# 01 — Revisión del reproductor de video y opinión técnica

**Revisado:** `test_video_player/main/*`, `sdkconfig`, `sdkconfig.defaults`, `convert_videos.py`,
`ACTA_DE_PROYECTO_REPRODUCTOR_VIDEO_SPOTIFY_ESP32S3.md` y `video_player/video_player.eez-project`.
**Fecha:** 15/09/2026 · **Auditor:** Claude · **Constructor previsto:** Antigravity

---

## 1. Opinión en una frase

La elección del formato es **correcta y es lo más valioso del trabajo**: MJPEG en AVI, submuestreo 4:2:0,
`esp_new_jpeg` con SIMD y el bus i80 del periférico LCD_CAM. **Lo que no está resuelto es la ruta del
fotograma hasta el panel**, que pasa por LVGL. Además, la cifra de «30 FPS reales» del acta **mide
fotogramas decodificados, no fotogramas mostrados**. Hoy no hay forma de saber cuántos llegan de verdad
a la pantalla, y ahí es donde se va la fluidez.

## 2. Lo que está bien (conservar)

| Decisión | Por qué es buena |
|---|---|
| MJPEG intra-frame en AVI | Cada fotograma es independiente: el salto (*seek*) y el descarte son gratuitos. Ideal para la SD por SPI. |
| `esp_new_jpeg` con salida RGB565 | Usa las instrucciones SIMD del S3. Es el decodificador por software más rápido disponible. |
| `swap_color_bytes = 1` en el i80 | En IDF 6.0.1 el intercambio se hace **por hardware** (`lcd_ll_enable_swizzle`), así que no cuesta CPU. Verificado en `esp_lcd_panel_io_i80.c:859`. |
| `COLMOD 0x55` (16 bits) | En modo paralelo el ILI9488 sí admite RGB565. Eso ahorra un 33 % de bus frente a los 18 bits que exige el modo SPI. |
| Tabla `idx1` en PSRAM | Permite saltar en O(1). |
| Tarea de video fija en el núcleo 1 y GUI en el núcleo 0 | Es el reparto correcto. |
| Registro de anomalías con RCA en el acta | Es buena práctica y conviene mantenerla. |

## 3. Hallazgos, ordenados por gravedad

### C — Críticos (afectan a la fluidez o a la estabilidad)

**C1. El video pasa por LVGL: tres copias por fotograma y el render bloqueado por el bus.**
Ruta actual en pantalla completa:
`JPEG → RGB565 en PSRAM (480×320) → lv_canvas → LVGL compone la zona invalidada en un búfer
parcial de 40 líneas → flush → ili9488_8080_draw_bitmap() → tx_color + espera del semáforo`.
- La pantalla completa invalidada son **8 flush de 40 líneas**, cada uno con `set_window` y una espera
  bloqueante (`xSemaphoreTake(..., portMAX_DELAY)` en `ili9488_8080.c`).
- LVGL copia 153 600 píxeles **desde PSRAM** (a 40 MHz, ver C5) en cada fotograma.
- El `lv_timer_handler` del núcleo 0 queda ocupado todo ese tiempo, y el táctil y la OSD se quedan
  esperando detrás.

**Consecuencia:** el cuello de botella real no es la SD (5,5 ms) ni el bus i80 (unos 19 ms para
307 KB a 16 MHz), sino la suma de la composición de LVGL y los flush bloqueantes, que **nadie mide**.

**C2. La métrica de FPS no mide lo que dice.** `s_latest_fps` (`main.c`) cuenta las veces que
`avi_player_read_next_frame()` devuelve OK. El núcleo 0 solo recoge **el último** aviso de
`s_video_frame_ready`, de modo que si LVGL tarda más de 33 ms, los fotogramas se pierden **en
silencio** y el contador sigue marcando 30. Hacen falta dos contadores: decodificados y
**presentados** (contados dentro del callback de flush o del blit directo), más uno de descartados.

**C3. El doble búfer «ping-pong» no evita el tearing: tiene una carrera.**
`spotify_ui_commit_frame()` intercambia los índices en el núcleo 1 **sin sincronizarse con LVGL**.
Secuencia que falla:
1. LVGL (núcleo 0) está componiendo el canvas con `buf[read = 1]`.
2. El núcleo 1 termina el fotograma y hace `read = 0`, `write = 1`.
3. El núcleo 1 empieza a decodificar el siguiente fotograma **sobre `buf[1]`**, que LVGL sigue leyendo.

→ Se mezclan dos fotogramas: es el mismo tearing que el acta da por resuelto. Con dos búferes y dos
productores/consumidores asíncronos hacen falta **tres búferes** o un traspaso explícito. La solución
del plan (blit directo) **elimina el problema de raíz**.

**C4. Llamadas a LVGL desde el núcleo 1 sin mutex.** En `video_engine_task`, dentro de la rama de
cambio de pista, se llama a `spotify_ui_set_play_state(PLAYBACK_STATE_PLAYING)`, que invoca
`lv_label_set_text()` **sin tomar `s_lvgl_mutex`**. LVGL no es seguro entre hilos (`CONFIG_LV_OS_NONE`).
Es un fallo intermitente de corrupción de memoria. Además, `spotify_ui_set_track()` en fin de video
**se salta** si el mutex no llega en 20 ms, y entonces la UI muestra la pista equivocada.

**C5. PSRAM a 40 MHz.** El `sdkconfig` tiene `CONFIG_SPIRAM_SPEED_40M=y`. El módulo N16R8 (Octal)
admite **80 MHz**, y todos los búferes de fotograma viven en PSRAM.

**C6. La cadencia depende de un tick de 10 ms.** Con `CONFIG_FREERTOS_HZ=100`,
`vTaskDelay(pdMS_TO_TICKS(delay_us/1000))` redondea a múltiplos de 10 ms. Con 33,3 ms por fotograma
se alternan esperas de 20 y 30 ms: hay **judder** aunque el promedio salga bien. Además, el retardo se
calcula respecto al inicio de la decodificación de *ese* fotograma, no respecto a un reloj de
reproducción, así que el error se acumula y **nunca se descarta un fotograma** que llega tarde.

### A — Altos (funcionalidad incorrecta)

**A1. La recuperación en caliente de la SD que documenta el acta (§Anomalía 4) no puede funcionar.**
`s_is_mounted` nunca vuelve a `false` si se extrae la tarjeta: nadie llama a `sdcard_spi_deinit()` al
fallar la lectura. El bucle hace `sdcard_is_mounted() == true` → `avi_player_open()` falla →
reintenta indefinidamente sin volver a montar. **Contradicción acta ↔ código: la dejo anotada, no la
resuelvo.**

**A2. Receta de conversión contradictoria.** El acta §5.1 dice `-r 30 -q:v 8 … crop` y 4:2:0
explícito. `convert_videos.py` usa `-r 20 -q:v 9`, `pad` (bandas negras) y **no fuerza** `-pix_fmt
yuvj420p`. El nombre de los ficheros coincide, así que no se sabe con cuál se generaron los AVI que
hay en la SD. La cadencia de 20 frente a 30 FPS cambia todas las cifras del acta.

**A3. Duración y tiempo transcurrido en enteros.** `fps = 1000000 / us_per_frame` redondea hacia
abajo: un video a 29,97 da 29, y la duración mostrada se desvía unos 7 s por cada 3 minutos.

**A4. `idx1` solo se busca en los últimos 256 KB.** Un video de 3:20 a 30 FPS tiene unas 6000
entradas de 16 B (96 KB) y cabe. Uno de más de 8 minutos **pierde la tabla en silencio** y el salto
cae en la aproximación por bytes. El tope debe calcularse a partir del tamaño del chunk.

**A5. `fseek` en cada fotograma aunque la lectura sea secuencial.** Con tabla de índices,
`read_next_frame` hace `fseek(s_index_table[current])` siempre. En FATFS sobre SPI, un `fseek` hacia
delante dentro del mismo clúster es barato, pero repetirlo 30 veces por segundo sin necesidad añade
latencia y variación. Solo debe hacerse tras un salto.

**A6. Fotogramas mayores de 36 KB se descartan con `ESP_ERR_NO_MEM`** y el bucle espera 10 ms, lo que
se ve como un tirón. Con `-q:v 8` casi nunca ocurre, pero en escenas con mucho detalle sí. Hay que
**crecer** el búfer (con tope) en lugar de saltar el fotograma.

### M — Medios (deuda y mantenimiento)

- **M1.** `g_playlist[4]` fijo en el código. Hay que escanear `/sdcard` y leer los metadatos de un
  fichero auxiliar.
- **M2.** Código muerto que no compila pero confunde: `s3v_player.*`, `lz4.*`, `tjpgd*` (fuera de
  `CMakeLists.txt`). Hay que moverlo a `legacy/`.
- **M3.** `LV_MEM_SIZE = 64 KB` con `LV_USE_BUILTIN_MALLOC`. La UI nueva (biblioteca, cola y ajustes)
  no cabe. Hay que usar `LV_USE_CLIB_MALLOC` (que va a PSRAM con `SPIRAM_USE_MALLOC`).
- **M4.** `sdkconfig.defaults` no fija nada de LVGL ni de rendimiento: un `fullclean` pierde la
  configuración.
- **M5.** Se reservan 4 búferes de fotograma en PSRAM (2 de 240×160 y 2 de 480×320, unos 0,85 MB).
  Con blit directo sobra casi todo.
- **M6.** Táctil por sondeo I2C dentro del mutex de LVGL cada ciclo. `FT6236 INT` (GPIO 7) está
  cableado según el acta y sin usar.
- **M7.** Nombres y marca «Spotify» en código y UI. Conviene quitarlos del producto: no es nuestra
  marca.
- **M8.** El proyecto EEZ en blanco está configurado a **800×480** y `colorFormat: BGR`. Hay que
  ponerlo a **480×320**. El formato de color se decide en `03_especificacion_ui_eez.md` §1.

## 4. Presupuesto de tiempo por fotograma (estimado y pendiente de medir)

| Etapa | Hoy (estimado) | Con el plan (objetivo) |
|---|---|---|
| Lectura SD de unos 11 KB | 5,5 ms (medido en el acta) | 4–5 ms (sin `fseek`, búfer alineado) |
| Decodificación JPEG 480×320 | 26–31 ms (acta) | 18–24 ms (PSRAM a 80 M, salida directa a DMA) |
| Composición LVGL | **no medido** (estimado 6–12 ms) | **0 ms** (blit directo) |
| Bus i80 de 307 KB a 16 MHz | ~19 ms, bloqueante y serializado con LVGL | ~19 ms **solapado** con la decodificación (bloques) |
| **Total núcleo 1** | > 33 ms en escenas pesadas | ≤ 33 ms con descarte si se retrasa |

La clave del plan es **solapar decodificación y transferencia**: decodificar 16 líneas, lanzar su DMA
y decodificar las 16 siguientes mientras el bus transmite. Así el tiempo total pasa de *suma* a
*máximo* de ambos.

## 5. Riesgo que conviene conocer

El bus i80 va a **16 MHz**, y según el acta (§5.2) el mínimo de la hoja de datos es 66 ns
(unos 15,1 MHz). Funciona en el banco, pero **está fuera de especificación** y el pin RD va a 3,3 V,
así que no se puede leer la GRAM de vuelta para comprobarla. El plan mantiene 16 MHz, pero añade una
prueba de patrón visual y deja el reloj como parámetro de Kconfig para poder bajar a 12 MHz si aparecen
píxeles corruptos con calor o con cables largos.

## 6. Veredicto

- **Formato y decodificador:** aprobados.
- **Ruta de presentación:** hay que rehacerla (C1, C3).
- **Concurrencia:** hay que corregirla antes de añadir UI (C4).
- **Acta:** las cifras de FPS y el apartado de recuperación en caliente **no están respaldadas por el
  código**. Hay que actualizarlas cuando se mida con los contadores nuevos, no antes.
