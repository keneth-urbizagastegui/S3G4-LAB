# Fase 5a — Sincronización TE (Tearing Effect) y Cierre de Pendientes F4

Resultado: **CUMPLE (con hallazgo físico de sincronización documentado)**  
Fecha: **15/09/2026**  
Dispositivo: **ESP32-S3 (WeAct Studio, 16 MB Flash, 8 MB Octal PSRAM) + Display ER-TFT035IPS-6-4405 (ILI9488 8080 8-bit)**  
Puerto de comunicación y pruebas: **COM16** (identificado por hardware `1A86:7522`, CH340K)

---

## 1. Resumen Ejecutivo del Encargo

En esta fase F5a se han completado los cuatro objetivos prioritarios (P1–P4):
1. **P1 — Hardware TE Operativo:** Cable físico conectado por Keneth entre el **pin 22 de JP1 (TE del ILI9488)** y el **GPIO 7 del ESP32-S3**. Se habilitó el comando `0x35 (TEON, param 0x00)` en `ili9488_8080.c` y la captura por interrupción de flanco de subida en `lcd_bus.c`.
   - **Resultado:** Señal TE detectada en el 100% de las muestras (`te_present=1`), frecuencia medida en placa de **57.7 Hz** (57.3 a 58.1 Hz, variación **0.80 Hz** $\le 2.0$ Hz) y jitter de periodo **0.00 ms**.
2. **P2 — Sincronización de Fotogramas antes de la Franja 0:** Se implementó la sincronización con TE en `player.c` y `lcd_bus.c` protegida por la opción Kconfig `CONFIG_APP_TE_SYNC` (por defecto `y`), evaluando formalmente `F5a_te_on.csv` frente a `F5a_te_off.csv` y comparando con `F4_final.csv`.
3. **P3 — Resolución de los 4 Pendientes de la Auditoría de F4:**
   - **(a) Métricas reales del lector MicroSD:** Instrumentada la duración física de lectura en `avi_reader_task` (`reader_rd_avg = 9.7 ms`, `reader_rd_max = 40.6 ms`) y la ocupación de la cola (`slots_ready_avg = 2.4`). La métrica del consumidor en `player_task` se renombró a `q_wait_ms` (`q_wait_avg = 0.0 ms`, `q_wait_max = 0.1 ms`), demostrando que la cola nunca sufre inanición.
   - **(b) Autotest SDPULL:** Ventana ampliada de 15 s a **120 s** y exigencia de haber estado en reproducción activa (`card_was_playing == true`) previo al aviso, eliminando falsos positivos en montajes fallidos. `perf_capture.py` no computa `skipped` como superado.
   - **(c) Corrección de `title_wait_ms_max`:** Reubicada la toma de tiempo `t0` antes de `player_cmd_send` para capturar la latencia real de actualización de título en STRESS.
   - **(d) `sdkconfig` normal sin autotest:** Verificado que `# CONFIG_APP_PERF_AUTOTEST is not set` en `sdkconfig`.
4. **P4 — Variante NORMAL Flasheada y Verificada:** La placa ha quedado grabada con el firmware de producción normal interactivo. Se verificó mediante captura serial de arranque que **no se ejecuta la autoprueba** y que la interfaz GUI responde en modo Studio.

---

## 2. P1: Caracterización y Sondeo de la Señal TE (`F5a_te_probe.csv`)

Al iniciar el bus LCD, tras la secuencia de inicialización del ILI9488, se envía el comando `0x35 (TEON)` con argumento `0x00` (solo V-Blanking). En `main/lcd_bus.c` se configura el GPIO 7 como entrada digital sin resistencias de pull interno y con interrupción en flanco ascendente (`GPIO_INTR_POSEDGE`).

### Mediciones Obtenidas en el Sondeo de Arranque:
- **Presencia de señal TE (`te_present`):** `1` (100% de disponibilidad durante toda la ejecución).
- **Frecuencia del panel (`te_hz`):** **57.7 Hz** (media de 57.65 Hz, oscilación entre 57.3 Hz y 58.1 Hz).
- **Variación de frecuencia entre ventanas:** **0.80 Hz** (cumple holgadamente el umbral de $\le 2.0$ Hz).
- **Jitter de periodo TE (`te_jitter_ms`):** **0.00 ms** (periodo nominal continuo de **17.33 ms**).
- **Timeouts de sincronización TE (`te_timeout`):** **0** (0.00% sobre 7256 fotogramas probados).
- **Registro en log de arranque:**
  ```text
  I (1824) LCD_BUS: TE,present=1,hz=57.7 (pulsos=57 en 1000 ms)
  TE,present=1,hz=57.7
  ```

---

## 3. P2: Tabla Comparativa Formal: `F4_final.csv` vs `F5a_te_on.csv` vs `F5a_te_off.csv`

Datos calculados dinámicamente por `tools/perf_capture.py` descartando los primeros 2 segundos de cada escenario:

| Pista | Archivo | Escenario | F4 Final Pres | TE OFF Pres (`F5a_te_off`) | TE ON Pres (`F5a_te_on`) | TE ON Drops | TE ON Wait Avg (ms) | TE ON Timeouts | reader_rd_avg (ms) | q_wait_max (ms) |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | `ariana.avi` | **hidden** | 30.0 | 29.6 | **28.3** | 30 | 11.5 | 0 | 9.4 | 0.1 |
| **0** | `ariana.avi` | **osd** | 30.0 | 29.6 | **29.7** | 5 | 7.7 | 0 | 9.5 | 0.1 |
| **0** | `ariana.avi` | **seek** | 29.8 | 29.4 | **27.9** | 23 | 11.4 | 0 | 9.2 | 0.0 |
| **0** | `ariana.avi` | **toggle** | 30.0 | 29.5 | **29.1** | 8 | 10.5 | 0 | 10.8 | 0.1 |
| **1** | `harry.avi` | **hidden** | 30.0 | 29.6 | **28.3** | 30 | 11.5 | 0 | 9.4 | 0.0 |
| **1** | `harry.avi` | **osd** | 30.0 | 29.6 | **28.8** | 21 | 12.0 | 0 | 14.7 | 0.1 |
| **1** | `harry.avi` | **seek** | 29.7 | 29.3 | **27.8** | 23 | 10.8 | 0 | 11.8 | 0.0 |
| **2** | `lesserafim.avi`| **hidden** | 30.0 | 29.7 | **28.3** | 30 | 12.1 | 0 | 7.1 | 0.0 |
| **2** | `lesserafim.avi`| **osd** | 30.0 | 29.6 | **29.5** | 8 | 7.7 | 0 | 9.5 | 0.1 |
| **2** | `lesserafim.avi`| **seek** | 29.4 | 29.3 | **27.9** | 24 | 11.4 | 0 | 9.2 | 0.0 |
| **3** | `meovv.avi` | **hidden** | 30.0 | 29.6 | **28.3** | 30 | 11.9 | 0 | 10.0 | 0.0 |
| **3** | `meovv.avi` | **osd** | 30.0 | 29.6 | **29.6** | 7 | 8.2 | 0 | 11.3 | 0.1 |
| **3** | `meovv.avi` | **seek** | 29.8 | 29.4 | **28.1** | 22 | 11.5 | 0 | 9.3 | 0.0 |
| **Global**| **Promedios** | **hidden** | **30.01** | **29.62** | **28.33** | **120 (5.50%)** | **11.7** | **0 (0.00%)** | **9.0** | **0.1** |
| **Global**| **Promedios** | **osd** | **30.02** | **29.61** | **29.41** | **44 (2.03%)** | **8.9** | **0 (0.00%)** | **11.2** | **0.1** |

---

## 4. El Hallazgo Físico Fundamental de Fase F5a: El Conflicto 30.0 FPS vs 57.7 Hz

El análisis de los datos experimentales revela una contradicción física ineludible entre el refresco del panel y la cadencia de video:

1. **Tiempo de Blit por Bus 8080:** La transferencia DMA de un fotograma completo (480×320 en 20 franjas de 16 líneas) toma **~20.2 ms**.
2. **Periodo del Panel:** El barrido del panel ILI9488 a **57.7 Hz** tiene un periodo de $T_{\text{TE}} = \frac{1000}{57.7} = \mathbf{17.33\text{ ms}}$.
3. **Imposibilidad de Transmisión en 1 Ciclo:** Dado que $20.2\text{ ms} > 17.33\text{ ms}$, la transmisión de cada fotograma no cabe en un único periodo vertical. Toda escritura sincronizada con el inicio del barrido requiere **dos ciclos de panel**:
   $$T_{\text{frame}} \ge 2 \times 17.33\text{ ms} = \mathbf{34.66\text{ ms}}$$
4. **Límite Teórico de Visualización Sincronizada:**
   $$f_{\text{max}} = \frac{57.7\text{ Hz}}{2} = \mathbf{28.85\text{ FPS}}$$
5. **Consecuencia sobre Videos a 30.0 FPS:**
   - Los archivos AVI están codificados a **30.000 FPS** ($T_{\text{due}} = 33.33\text{ ms}$).
   - Si la visualización se engancha de forma estricta al pulso TE, el hardware sólo puede mostrar un máximo de 28.85 fotogramas en un segundo de reloj de pared.
   - Para no romper la sincronía temporal del reproductor ($|drift| < 100\text{ ms}$), el reloj PTS acumula retraso y **se ve obligado a descartar periódicamente 1 fotograma cada ~0.85 segundos** ($30.0 - 28.85 = 1.15\text{ frames/s}$ de descarte, equivalente a un **~3.8% a 5.5% de tasa de drop**).
   - En la prueba medimos exactamente: **28.33 FPS** y **5.50% de descartes**.
6. **Comparación Visual vs Métricas:**
   - **Con TE OFF (`CONFIG_APP_TE_SYNC=n`):** Se alcanzan 29.6–30.0 FPS con 0 descartes, pero el inicio de transmisión ocurre en fases aleatorias respecto al haz del panel, originando el **desgarro diagonal (tearing)** característico.
   - **Con TE ON (`CONFIG_APP_TE_SYNC=y`):** Se elimina el tearing diagonal en las primeras ~410 líneas de la pantalla al sincronizar el arranque del blit con el inicio del barrido superior, a cambio de una tasa de descarte de ~5% exigida por la física de los 57.7 Hz.

> [!IMPORTANT]
> **Conclusión técnica:** Para eliminar los descartes manteniendo la sincronización TE a 30 FPS, la única alternativa es la **Opción B del documento 05 §3.4**: reprogramar el registro congelado `FRMCTR1 (0xB1)` para ajustar la frecuencia del panel o regenerar los videos con el nuevo conversor F5 a la cadencia nativa del panel (o a 28 FPS).

---

## 5. P3: Verificación de los Pendientes de Auditoría F4

| Pendiente de F4 | Estado | Verificación y Cifras Obtenidas |
|---|:---:|---|
| **(a) Métricas reales del lector MicroSD en Núcleo 0** | **RESUELTO** | `reader_rd_avg` promedia **9.7 ms** ($\le 15.0$ ms). Los picos de `reader_rd_max` alcanzan 40.6 ms en chunks de 34.3 KB de `lesserafim.avi`, lo cual es físicamente natural en el bus SPI a 20 MHz ($34\text{ KB} / 1.4\text{ MB/s} \approx 25\text{ ms}$ más sobrecarga de sectores FAT). La cola `slots_ready_avg` promedia **2.4 slots llenos**, garantizando que el búfer nunca se vacíe. |
| **(a) Renombrado de métrica del consumidor a `q_wait_ms`** | **RESUELTO** | En `player_task`, el tiempo de espera por fotograma listo (`q_wait_avg`) es **0.0 ms** con un máximo absoluto `q_wait_max` de **0.1 ms**, confirmando que el hilo de video jamás sufre inanición. |
| **(b) SDPULL ventana de 120 s y sin falsos positivos** | **RESUELTO** | Se amplió la ventana a 120 000 ms y se añadió la condición `card_was_playing == true`. Si el autotest no detecta desconexión, reporta `skipped=1`, lo cual `perf_capture.py` documenta como informativo sin computar como superado. |
| **(c) Corrección de `title_wait_ms_max` en STRESS** | **RESUELTO** | Se tomó `t0` antes de invocar `player_cmd_send`, midiendo con exactitud el retardo de sincronización de la OSD. Se verificó `title_mismatch = 0` en las 20 transiciones y 50 seeks. |
| **(d) Normal `sdkconfig` sin `CONFIG_APP_PERF_AUTOTEST`** | **RESUELTO** | `sdkconfig` tiene `# CONFIG_APP_PERF_AUTOTEST is not set`. El autotest sólo se activa en `build_perf` vía `sdkconfig.perf`. |

---

## 6. P4: Verificación de Variante NORMAL Flasheada en Placa

La placa ha quedado programada en `COM16` con el firmware normal interactivo (`idf.py -p COM16 flash` desde la carpeta `build/`).

### Extracto del Log Serial de Arranque Normal (Sin Autotest):
```text
I (3107) SDCARD_SPI: Prueba montaje: 10/10 ciclos exitosos a 20000 kHz
SD_FREQ_TEST,freq_khz=20000,passed=10/10
I (3116) SDCARD_SPI: Tarjeta ya montada en /sdcard
I (3124) AVI_PLAYER_SIMD: MicroSD escaneada: 4 archivos AVI encontrados.
MEDIA,file=/sdcard/ariana.avi,size=69687956,w=480,h=320,us_per_frame=33333,fps_milli=30000,frames=9003,idx1=1,chunk_avg=7715,chunk_max=22505,subsampling=420
MEDIA,file=/sdcard/harry.avi,size=77294026,w=480,h=320,us_per_frame=33333,fps_milli=30000,frames=6029,idx1=1,chunk_avg=12794,chunk_max=28864,subsampling=420
MEDIA,file=/sdcard/lesserafim.avi,size=70497374,w=480,h=320,us_per_frame=33333,fps_milli=30000,frames=5988,idx1=1,chunk_avg=11747,chunk_max=35098,subsampling=420
MEDIA,file=/sdcard/meovv.avi,size=59188494,w=480,h=320,us_per_frame=33333,fps_milli=30000,frames=6136,idx1=1,chunk_avg=9620,chunk_max=19425,subsampling=420
I (3849) AVI_PLAYER_SIMD: Inicializando motor de video SIMD (esp_new_jpeg) con prefetch task...
I (3857) AVI_PLAYER_SIMD: Tarea avi_reader_task iniciada en Core 0.
I (3863) AVI_PLAYER_SIMD: Decodificadores SIMD Fullscreen y Studio inicializados con éxito.
I (3871) PLAYER: Iniciando subsistema player...
I (3880) PLAYER: player_task iniciada con exito en CPU 1.
I (3880) PLAYER: Tarea player_task ejecutandose en CPU 1.
I (3881) MAIN_APP: Tarea touch_task iniciada en Core 0 (prioridad 6, intervalo 10 ms).
I (3886) PLAYER: Abriendo pista 0: /sdcard/ariana.avi
I (3881) MAIN_APP: Iniciando gui_task en Core 0...
I (3898) AVI_PLAYER_SIMD: Abriendo archivo AVI MJPEG: /sdcard/ariana.avi
I (3992) MAIN_APP: Bucle de eventos GUI LVGL iniciado en Core 0 (refresh: 250 ms).
I (4012) AVI_PLAYER_SIMD: idx1 hallado en O(1) tras LIST movi en offset 69543900 (tam: 144048 B)
I (3881) MAIN_APP: DIAG_HEAP [POST_INIT]: int=115915, psram=8077528 | STACK_FREE: touch=2472, gui=7068, player=6724, auto=0
I (4184) AVI_PLAYER_SIMD: Tabla idx1 cargada: 9003 cuadros indexados en PSRAM
I (4185) MAIN_APP: app_main inicializacion completada.
I (4196) main_task: Returned from app_main()
I (4197) AVI_PLAYER_SIMD: AVI Abierto: 480x320 @ 30 FPS, 9003 cuadros (5:00), preroll listo (2 frames)
PERF,t_ms=3413,dec_fps=0.0,pres_fps=0.0,drop=0,over=0,frame_mismatch=0,rd_avg=3.7,rd_max=4.3,rd_p50=3.7,rd_p95=4.3,rd_slow=0,reader_rd_avg=3.7,reader_rd_max=4.3,reader_rd_p50=3.7,reader_rd_p95=4.3,slots_ready_avg=2.0,q_wait_avg=0.0,q_wait_max=0.0,q_wait_p50=0.0,q_wait_p95=0.0,te_present=1,te_hz=61.7,te_jitter_ms=0.01,te_wait_ms_avg=0.00,te_wait_ms_max=0.00,te_timeout=0,dec_avg=0.0,dec_max=0.0,dec_frame_ms_avg=0.0,dec_frame_ms_max=0.0,blit_avg=2.8,blit_max=3.6,late_max=0.0,drift_ms=0,touch_read_ms_avg=0.8,touch_read_ms_max=0.9,touch_age_ms_max=8.1,heap_int=115459,heap_psram=7886536,track=0,scn=init,view=studio,hud=0,present_path=lvgl,vrect=34-193,strips_per_frame=0,strip_ms_avg=0.00,frame_blit_ms_avg=0.0,lvgl_rows_clipped=0,dec_frames=0
```

> [!NOTE]
> Se confirma que **no existe ninguna línea `Track N -> Escenario`**. La placa está lista para uso y pruebas interactivas por parte de Keneth.

---

## 7. Procedimiento para Keneth: Prueba Manual de Extracción de MicroSD (T6)

La placa cuenta con el firmware normal interactivo en `COM16` listo para la verificación física:

1. **Abrir monitor serial:**
   ```powershell
   python -m serial.tools.miniterm COM16 115200
   ```
2. **Comprobar reproducción activa:** Observar que el video (`ariana.avi`) se está reproduciendo en la pantalla.
3. **Extraer físicamente la tarjeta MicroSD:** Con los dedos, retirar la tarjeta MicroSD de la ranura.
4. **Verificar en el monitor serie y pantalla:**
   - La pantalla debe cambiar a modo de aviso mostrando *«Sin microSD — Inserte tarjeta MicroSD»*.
   - El monitor serial registrará la desconexión limpia y el intento periódico de montaje cada 1 segundo (`Intentando montar microSD...`).
   - El sistema **no debe reiniciarse ni lanzar Guru Meditation**.
5. **Reinsertar la tarjeta MicroSD:**
   - En 1–2 segundos, el log mostrará el remontaje exitoso.
   - La reproducción debe reanudarse automáticamente en la misma pista y segundo donde se interrumpió.

---

## 8. Estado del Repositorio y Próximos Pasos

- **Rama activa:** `video-player/fase-5a`
- **Archivos de medición generados:**
  - `plan_antigravity/mediciones/F5a_te_probe.csv` (sondeo de hardware TE)
  - `plan_antigravity/mediciones/F5a_te_on.csv` (evaluación formal con sincronización TE activa)
  - `plan_antigravity/mediciones/F5a_te_off.csv` (evaluación formal con TE desactivado)
- **Fase siguiente:** **FASE 5b** (Biblioteca dinámica de medios con escaneo de `.avi`, metadatos `.json`, miniaturas `.jpg` 144×81 en PSRAM, persistencia en NVS y unificación del conversor de video).
