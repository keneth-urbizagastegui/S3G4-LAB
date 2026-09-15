# 02 — Plan de mejoras del firmware (paquete de construcción para Antigravity)

> **Lee primero `00_LEEME.md`** (reglas de trabajo y lo que NO puedes tocar).
> Una fase por encargo. Cada fase termina en **compila → flashea → mide → /review** (ver `04`).

Alcance: **solo software** (el pinout del acta §2.1 queda congelado) y **solo video, sin audio**.
La UI la genera EEZ Studio y **reemplaza `spotify_ui.c`**.

---

## Arquitectura objetivo

```
                 ┌──────────────── Núcleo 0 ────────────────┐   ┌────────────── Núcleo 1 ──────────────┐
 FT6236 (INT) ──►│ gui_task: lv_timer_handler + EEZ ui_tick │   │ player_task                          │
                 │   actions.c ──► player_cmd_send() ───────┼──►│  cola de comandos (xQueue)           │
                 │   vars.c   ◄── player_get_status() ◄─────┼───┤  reloj PTS + descarte                │
                 │   flush_cb ──► lcd_bus_lock() ───┐       │   │  avi_demux → jpeg bloques 16 líneas  │
                 └──────────────────────────────────┼───────┘   │     └─► lcd_bus_lock() → blit DMA    │
                                                    ▼           └──────────────────────────────────────┘
                                          lcd_bus (mutex + región de video)
```

Reglas de la arquitectura:
1. **Solo `gui_task` llama a LVGL.** Nunca, en ningún fichero, se llama a `lv_*` desde `player_task`.
2. **UI → reproductor:** únicamente a través de `player_cmd_send()` (cola). Se eliminan las banderas
   `bool` globales.
3. **Reproductor → UI:** una estructura `player_status_t` copiada bajo `portENTER_CRITICAL`, que la UI
   lee cada 100–250 ms.
4. **El panel tiene un único dueño cada vez**, protegido por `lcd_bus_lock()`. LVGL y el video no
   dibujan nunca los mismos píxeles: el video se pinta en un **rectángulo de video** que LVGL deja
   libre (ver `03` §2).

---

## FASE 0 — Instrumentación (antes de optimizar nada)

**Objetivo:** tener cifras de verdad. Sin esta fase no se puede aceptar ninguna de las siguientes.

1. Crear `main/perf.h` / `perf.c`:
   ```c
   typedef struct {
       uint32_t frames_decoded;   // chunks decodificados OK
       uint32_t frames_presented; // blits completados (o flush de LVGL del canvas, en la fase actual)
       uint32_t frames_dropped;   // descartados por retraso (fase 2)
       uint32_t oversize_frames;  // chunks > búfer
       uint32_t t_read_us_max, t_read_us_sum;
       uint32_t t_decode_us_max, t_decode_us_sum;
       uint32_t t_blit_us_max, t_blit_us_sum;
       int32_t  late_us_max;      // retraso máximo frente al PTS
   } perf_window_t;
   void perf_begin(void); void perf_mark_read(uint32_t us); /* ... */
   void perf_report_if_due(void); // cada 2 s
   ```
2. Una **única línea de log parseable** cada 2 s, con este formato exacto (el script de `04` depende
   de él):
   ```
   PERF,t_ms=12034,dec_fps=29.9,pres_fps=24.1,drop=0,over=0,rd_avg=5.3,rd_max=9.8,dec_avg=27.4,dec_max=34.0,blit_avg=19.2,blit_max=22.1,late_max=41.0,heap_int=123456,heap_psram=5123456
   ```
   Los decimales con punto y **sin espacios**. Los FPS **se calculan** a partir del contador y del
   tiempo real de la ventana, **nunca se escriben a mano**.
3. En la versión actual (antes de la fase 1), contar `frames_presented` en `lvgl_disp_flush_cb`
   **solo cuando el área incluye la última línea del canvas** (`area->y2 == 319` en pantalla completa).
4. **Inventario de los AVI de la microSD** (nadie sabe a cuántos fps se convirtieron). Al abrir cada
   fichero, una línea:
   ```
   MEDIA,file=/sdcard/harry.avi,size=12345678,w=480,h=320,us_per_frame=50000,fps_milli=20000,frames=4020,idx1=1,chunk_avg=11234,chunk_max=28765,jpeg_sof=baseline,subsampling=420
   ```
   `chunk_avg/max` se calculan **recorriendo `idx1`** (tamaños de las entradas `00dc`), sin decodificar.
   `subsampling` se lee del marcador SOF0 del primer fotograma (factores H/V de la componente Y). Todo
   medido del fichero; nada supuesto. Si un AVI no cumple 480×320 o no es 4:2:0, **anótalo**.
   La autoprueba recorre **los `.avi` que encuentre en `/sdcard`** (en F0 todavía con `g_playlist` si
   hace falta, pero registrando también los que no están en la lista).
5. Medir **la línea base** con el firmware actual y los videos de la microSD: guardar en
   `plan_antigravity/mediciones/F0_baseline.csv`.

**Aceptación F0:** existe el CSV de la línea base con ≥ 60 s por video y la columna `pres_fps` rellena.
Si `pres_fps` sale ≈ `dec_fps`, **anótalo**: contradice C2 de la revisión y el auditor debe saberlo.

---

## FASE 1 — Concurrencia correcta y comandos por cola

1. `main/player.h` (API nueva; `avi_player.*` pasa a ser el demuxer interno):
   ```c
   typedef enum { PCMD_OPEN, PCMD_PLAY, PCMD_PAUSE, PCMD_TOGGLE, PCMD_STOP,
                  PCMD_SEEK_MS, PCMD_SEEK_REL_MS, PCMD_NEXT, PCMD_PREV,
                  PCMD_SET_REPEAT, PCMD_SET_SHUFFLE, PCMD_SET_VIDEO_RECT } player_cmd_type_t;
   typedef struct { player_cmd_type_t type; int32_t arg; char path[128];
                    struct { int16_t x, y, w, h; } rect; } player_cmd_t;

   typedef enum { PST_IDLE, PST_PLAYING, PST_PAUSED, PST_ENDED, PST_ERROR, PST_NO_MEDIA } player_state_t;
   typedef enum { REPEAT_OFF, REPEAT_ALL, REPEAT_ONE } repeat_mode_t;
   typedef struct {
       player_state_t state; repeat_mode_t repeat; bool shuffle;
       int32_t track_index; int32_t track_count;
       uint32_t pos_ms, dur_ms;          // milisegundos, no segundos enteros (A3)
       uint16_t width, height; uint32_t fps_milli; // 29970 = 29.97 fps
       float pres_fps, dec_fps; uint32_t dropped;
       char title[64]; char subtitle[64];
       uint32_t err_code;
   } player_status_t;

   esp_err_t player_start(void);                       // crea la tarea en el núcleo 1
   bool player_cmd_send(const player_cmd_t *c);        // no bloqueante (timeout 0); devuelve false si la cola está llena
   void player_get_status(player_status_t *out);       // copia bajo spinlock
   ```
2. Borrar `s_need_track_switch`, `s_need_seek`, `s_video_frame_ready` y las llamadas a
   `spotify_ui_*` desde `video_engine_task`.
3. La cola tiene profundidad 8. Si llegan **varios `SEEK`** seguidos (arrastrar la barra), el
   reproductor **se queda con el último** (vaciar la cola de SEEK antes de ejecutar).
4. `gui_task` en el núcleo 0: `lv_timer_handler()` + `ui_tick()` de EEZ. `app_main` solo inicializa
   y termina (o se queda como vigilante), no hace de bucle de GUI con esperas mágicas.
5. Duración con precisión: `dur_ms = total_frames * us_per_frame / 1000` en 64 bits (A3).

**Aceptación F1:**
- `grep -R "lv_" main/player*.c main/avi*.c` **no devuelve nada** (compruébalo leyendo los ficheros
  enteros; ver regla de grep en `00`).
- 20 cambios de pista seguidos y 50 saltos arrastrando la barra sin pánico ni UI desincronizada
  (título == pista reproducida, comprobado en el log).

---

## FASE 2 — Reloj de reproducción, cadencia y descarte

1. `CONFIG_FREERTOS_HZ=1000` en `sdkconfig.defaults`.
2. Reloj PTS basado en `esp_timer_get_time()`:
   ```c
   // al empezar o reanudar: t0 = now_us - pos_us
   int64_t due_us = t0 + (int64_t)frame_idx * us_per_frame;
   int64_t late = now_us - due_us;
   if (late > (int64_t)us_per_frame) {            // más de 1 fotograma tarde
       avi_skip_chunk();                           // leer cabecera y saltar SIN decodificar (MJPEG intra = gratis)
       perf.frames_dropped++; frame_idx++; continue;
   }
   if (late < -2000) {                             // más de 2 ms adelantado → esperar con precisión
       int64_t wait = -late;
       if (wait > 3000) vTaskDelay(pdMS_TO_TICKS((wait - 2000) / 1000));
       while (esp_timer_get_time() < due_us) taskYIELD(); // afinado final < 2 ms
   }
   ```
   (El `taskYIELD` en espera activa de ≤ 2 ms es aceptable en el núcleo 1. **Si el WDT de la tarea
   ociosa del CPU1 se queja, anótalo** y cambia a `esp_timer` con notificación.)
3. Los fotogramas descartados **siguen avanzando `pos_ms`**: la barra de progreso no se detiene.
4. Pausa: guardar `pos_us`; al reanudar se recalcula `t0`. Fin de video: aplicar `repeat` y `shuffle`.

**Aceptación F2:** desviación de `pos_ms` frente al reloj de pared **< 100 ms tras 3 min**, y
`late_max` estable (sin crecer con el tiempo).

---

## FASE 3 — Blit directo con decodificación por bloques (la mejora grande)

**Idea:** la tarea de video escribe en el panel sin LVGL, decodificando 16 líneas cada vez y
transmitiéndolas por DMA mientras decodifica las siguientes.

1. Nuevo `main/lcd_bus.c/.h`:
   ```c
   void lcd_bus_init(void);                         // envuelve el panel_io actual de ili9488_8080.c
   void lcd_bus_lock(void); void lcd_bus_unlock(void);   // mutex recursivo
   void lcd_bus_set_video_rect(int16_t x, int16_t y, int16_t w, int16_t h); // lo fija la UI (vía PCMD_SET_VIDEO_RECT)
   esp_err_t lcd_bus_begin_region(uint16_t x1, uint16_t y1, uint16_t x2, uint16_t y2); // CASET/PASET + primer RAMWR
   esp_err_t lcd_bus_push_strip(const uint8_t *px, size_t len, bool first); // tx_color(first?0x2C:-1)
   ```
   - `ili9488_8080_draw_bitmap()` y el flush de LVGL pasan por `lcd_bus_lock()`.
   - La espera del semáforo `on_color_trans_done` se sustituye por **una cola de 2 elementos**:
     se permite **un bloque en vuelo y uno preparado** (el patrón *ping-pong* del driver sí tiene
     sentido aquí, porque el productor es uno solo).
2. Decodificador en modo bloque:
   ```c
   cfg.output_type = JPEG_PIXEL_FORMAT_RGB565_LE;  // el swap lo hace el hardware (swizzle), no tocar
   cfg.block_enable = true;
   jpeg_dec_parse_header(dec, &io, &hdr);
   jpeg_dec_get_outbuf_len(dec, &blk_len);        // 8 o 16 líneas × 480 × 2
   jpeg_dec_get_process_count(dec, &n_blocks);    // no suponer 20: SE CUENTA
   // 2 búferes alineados a 16 B EN MEMORIA INTERNA DMA: heap_caps_aligned_alloc(16, blk_len, MALLOC_CAP_DMA|MALLOC_CAP_INTERNAL)
   for (int b = 0; b < n_blocks; b++) {
       io.outbuf = strip[b & 1];
       jpeg_dec_process(dec, &io);                 // io.out_size = bytes de este bloque
       blit_strip_clipped(io.outbuf, io.out_size, line_y, &video_rect); // recorta a la región visible
       line_y += io.out_size / (2 * width);
   }
   ```
   **Verificar contra `managed_components/espressif__esp_new_jpeg/include/esp_jpeg_dec.h`** (líneas
   49–62 y 113–150) antes de escribir: si el comportamiento de `out_size` o de los búferes en modo
   bloque no coincide con lo descrito aquí, **anota la discrepancia y sigue la cabecera**.
3. **Recorte a la región de video.** Cuando la OSD está visible, la región es
   `y ∈ [40, 235]` (ver `03` §2): las filas 0–39 y 236–319 del fotograma se **decodifican pero no se
   envían**. Sin OSD, la región es la pantalla completa. Las barras de la OSD son **opacas**, así que
   no hace falta mezclar alfa con el video (decisión de diseño documentada en `03`).
4. Las pantallas LVGL a pantalla completa (Biblioteca, Ajustes, Cola) ponen `video_rect = {0,0,0,0}`
   → **el reproductor pausa el blit** (sigue en pausa o se detiene según la acción).
5. Superposiciones pequeñas sobre el video (gesto de brillo, «+10 s», bloqueo): la UI declara
   rectángulos de **exclusión** (máximo 2) mediante `PCMD_SET_VIDEO_RECT` con `arg` = índice de
   exclusión. El blit salta esas columnas y filas. Si complica demasiado, la alternativa aceptada es
   **pausar el blit 600 ms mientras se muestra el gesto**. Anota cuál implementas.
6. Eliminar los búferes de fotograma en PSRAM de 480×320 y 240×160 (M5) y el canvas de LVGL.
7. Tarea `player_task`: stack de 8 KB (ya no hay búferes locales grandes; **medir el
   `uxTaskGetStackHighWaterMark`** y dejar margen ≥ 2 KB; **se mide, no se supone**).

**Aceptación F3:** `pres_fps ≥ 28,5` de media y `drop ≤ 1 %` en los 4 videos a 30 FPS, con la OSD
oculta, durante 60 s cada uno. Con la OSD visible, `pres_fps ≥ 28`. **Si no se llega, entrega las
cifras igual.** Un fallo medido es un resultado válido.

---

## FASE 4 — E/S de la SD y robustez

1. Lectura secuencial **sin `fseek`** salvo tras un SEEK (A5). Usar `read()` sobre el descriptor
   (`fileno`) o `setvbuf(f, NULL, _IOFBF, 32*1024)`, lo que **mida** mejor (anota ambos `rd_avg`).
2. Búfer JPEG creciente: empieza en 48 KB y hace `heap_caps_realloc` hasta 128 KB si llega un chunk
   mayor. Por encima de 128 KB se descarta el fotograma y se incrementa `oversize_frames` (A6).
3. `idx1`: leer el tamaño real del chunk `idx1` (buscando la etiqueta en la cola del fichero con una
   ventana inicial de 64 KB y ampliando **según `idx_size`**), sin tope fijo de 256 KB (A4).
4. Recuperación de la SD (A1): si `fread` devuelve un error de E/S o `fopen` falla dos veces seguidas →
   `sdcard_spi_deinit()` → `state = PST_NO_MEDIA` → reintento de montaje cada 1 s. Probar
   **extrayendo la tarjeta en plena reproducción** 5 veces.
5. Frecuencia de la SD: **probar** 20, 26 y 40 MHz (`s_host.max_freq_khz`) y quedarse con la mayor que
   supere 10 montajes y 5 min de reproducción sin error. Si solo pasa 20 MHz, se queda en 20 MHz.
   Anota los resultados.

**Aceptación F4:** 5 de 5 extracciones y reinserciones recuperadas sin reiniciar; `rd_max < 15 ms`.

---

## FASE 5 — Biblioteca dinámica y conversor unificado

1. `main/media_library.c`: escanear `/sdcard/videos/*.avi` (y `/sdcard/*.avi` por compatibilidad),
   ordenar alfabéticamente y **contar**, sin constante `PLAYLIST_SIZE`.
2. Por cada `nombre.avi`, leer los ficheros auxiliares opcionales:
   - `nombre.json` → `{"title":"…","subtitle":"…"}` (parsear con el componente `json`/cJSON de IDF).
   - `nombre.jpg` → miniatura **144×81** en JPEG 4:2:0, que se decodifica a RGB565 y se guarda en
     PSRAM como `lv_image_dsc_t`.
   - Si falta el JSON, el título es el nombre del fichero sin extensión. Si falta la miniatura, se
     usa un marcador de posición.
3. Persistir en NVS: último video, posición (cada 5 s y al pausar), brillo, `repeat`, `shuffle`,
   tiempo de ocultación de la OSD y si se muestran las estadísticas. «Continuar donde lo dejaste» al
   abrir el mismo video.
4. **Un único conversor** `TFT_8Bit_Capacitive/convert_videos.py`, que sustituye a los dos actuales
   (se conservan los viejos en `legacy/`). Parámetros por CLI, sin lista fija de videos:
   ```
   python convert_videos.py --src Videos --dst D:\videos --fps 30 --q 8 --fit crop
   ```
   Por cada `.mp4` genera `.avi` + `.jpg` (144×81) + `.json`. Comando de video:
   ```
   ffmpeg -y -i IN -vf "scale=480:320:force_original_aspect_ratio=increase,crop=480:320,fps=30" \
     -c:v mjpeg -pix_fmt yuvj420p -q:v 8 -an OUT.avi
   ffmpeg -y -ss 5 -i IN -frames:v 1 -vf "scale=144:81:force_original_aspect_ratio=increase,crop=144:81" -q:v 4 OUT.jpg
   ```
   Al terminar imprime, **medido del fichero de salida**, el tamaño medio y máximo de chunk con un
   parseo de `idx1` en Python, y avisa si el máximo supera 128 KB.
5. Resolver la contradicción A2: el conversor nuevo manda. **Actualiza el acta §5.1 solo después de
   medir.**

**Aceptación F5:** meter un 5.º video en la SD (sin recompilar) y que aparezca con su miniatura y su
título.

---

## FASE 6 — Integración de la UI de EEZ Studio

Detalle de pantallas y widgets en `03_especificacion_ui_eez.md`. Pasos de firmware:
1. EEZ genera en `test_video_player/main/ui/` (ruta de salida en *Settings → Build* del proyecto EEZ).
   Añadir `ui/*.c` a `SRCS` o crear `components/ui`.
2. **`flowSupport: false`**: acciones y variables **nativas**. Implementar `main/ui_glue/actions.c` y
   `vars.c` con los nombres **exactos** de `03` §5. `spotify_ui.c/.h` pasan a `legacy/`.
3. Mapa de acciones → `player_cmd_send()`; variables ← `player_get_status()` en caché (una copia por
   `ui_tick`, no una por variable).
4. Fuentes: habilitar en `sdkconfig.defaults` `CONFIG_LV_FONT_MONTSERRAT_12=y`, `_14=y` y `_20=y`.
5. `LV_USE_CLIB_MALLOC=y` (M3). Refresco de LVGL `CONFIG_LV_DEF_REFR_PERIOD=16` (LVGL ya no dibuja
   video, así que es barato).
6. Táctil: **el INT del FT6236 NO está conectado** (confirmado por Keneth el 15/09/2026). Se mantiene
   el sondeo I2C, pero **fuera del mutex de LVGL**: una tarea de 10 ms en el núcleo 0 lee el FT6236 y
   deja el último punto en una estructura protegida; `lvgl_touch_read_cb` solo copia esa estructura.
7. Gestos (`03` §4) en `main/ui_glue/gestures.c`, sobre un objeto transparente que cubre la región de
   video.

**Aceptación F6:** las 8 pantallas navegables; todos los criterios de F3 siguen cumpliéndose con la UI
nueva.

---

## FASE 7 — `sdkconfig.defaults` completo

Añadir (y verificar que acaban en `sdkconfig` tras `idf.py fullclean build`):
```
CONFIG_SPIRAM_SPEED_80M=y
CONFIG_FREERTOS_HZ=1000
CONFIG_ESP_DEFAULT_CPU_FREQ_MHZ_240=y
CONFIG_COMPILER_OPTIMIZATION_PERF=y
CONFIG_LV_COLOR_DEPTH_16=y
CONFIG_LV_USE_CLIB_MALLOC=y
CONFIG_LV_DEF_REFR_PERIOD=16
CONFIG_LV_FONT_MONTSERRAT_12=y
CONFIG_LV_FONT_MONTSERRAT_14=y
CONFIG_LV_FONT_MONTSERRAT_20=y
CONFIG_LV_DRAW_SW_SUPPORT_RGB888=n
CONFIG_LV_DRAW_SW_SUPPORT_XRGB8888=n
CONFIG_LV_DRAW_SW_SUPPORT_L8=n
CONFIG_LV_DRAW_SW_SUPPORT_AL88=n
CONFIG_LV_DRAW_SW_SUPPORT_I1=n
CONFIG_SPIRAM_MEMTEST=n
```
Deja `ARGB8888` activo si EEZ exporta imágenes con alfa en ese formato. **Compruébalo en `images.c`
generado antes de desactivarlo.**
Si `SPIRAM_SPEED_80M` da errores de arranque en esta placa WeAct, **anótalo** y vuelve a 40 M.

---

## Orden y dependencias

`F0 → F1 → F2 → F3 → F4 → F5 → F6`, y F7 se aplica en paralelo desde F2.
F3 es la única que puede fracasar por límites físicos: por eso F0 y F2 van antes, para poder
distinguir un fallo de diseño de un fallo de silicio.

---

## ADENDA (15/09/2026): estado real y lo que se suma a F5

Estado de las versiones: `vp-v0.1` F1 · `vp-v0.2` F2 · `vp-v0.3` F3 · **`vp-v0.4` F4** (0 descartes, 30 fps
en pantalla con y sin OSD, lector adelantado en el núcleo 0, SD a 20 MHz, PSRAM a 80 MHz).

**F5 arrastra de F4** (detalle en `informes/FASE_4.md`, «Cierre de F4»):
1. Firmware normal sin `CONFIG_APP_PERF_AUTOTEST` (hoy colado en `sdkconfig`), verificado en el log de arranque.
2. Prueba de extracción de la SD **manual y sin ventana de tiempo** con el firmware normal, supervisada por el
   auditor desde el puerto serie. SDPULL del autotest: 120 s y sin falsos positivos.
3. Métricas: lectura real del lector (`reader_rd_avg/max`, ocupación de la cola), la del consumidor renombrada
   a `q_wait_ms`, y revisión de `title_wait_ms_max`.

**F5 incorpora la sincronización con TE** (cable del pin 22 de JP1 al GPIO 7): ver `05_sincronizacion_TE.md`.
Se hace en un encargo propio **antes** de la biblioteca dinámica, porque cambia el camino de envío al panel.
Orden sugerido: F5a = pendientes de F4 + TE · F5b = biblioteca dinámica y conversor (FASE 5 original).
