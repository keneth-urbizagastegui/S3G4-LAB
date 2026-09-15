# Fase 0 — Instrumentación, Autotest y Línea Base de Rendimiento

Resultado: CUMPLE
Iteraciones del bucle: 1
Ficheros tocados:
- `main/perf.c`
- `main/spotify_ui.h`
- `main/spotify_ui.c`
- `main/main.c`
- `tools/perf_capture.py`

---

## 1. Tabla de Criterios de Aceptación (Fase 0)

| Criterio | Umbral | Medido | ✔/✘ |
|---|---|---|:---:|
| Líneas PERF en todos los videos | tracks contados == tracks en `AUTOTEST_DONE` | 4 tracks == 4 en `AUTOTEST_DONE` | ✔ |
| Sin excepciones ni reinicios durante autotest | Código ≠ 2 | Código 0 (sin abort/Guru Meditation/rst) | ✔ |
| `heap_int` mínimo | ≥ 30 000 B y estable | 94 111 B (mínimo, estable ~94.1 KB) | ✔ |

Código de salida de `perf_capture.py`: **0** (Éxito).
Iteraciones requeridas: **1** (F0_baseline).

---

## 2. Tabla MEDIA por AVI (MicroSD)

Valores extraídos de `plan_antigravity/mediciones/F0_baseline_media.csv`:

| Archivo | Dimensiones (w x h) | FPS Real (`fps_milli/1000`) | Fotogramas (`frames`) | Duración (mm:ss) | `chunk_avg` (KB) | `chunk_max` (KB) | Submuestreo (`subsampling`) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/sdcard/ariana.avi` | 480x320 | 30.000 | 9003 | 05:00 | 7.5 | 22.0 | unknown |
| `/sdcard/harry.avi` | 480x320 | 30.000 | 6029 | 03:20 | 12.5 | 28.2 | unknown |
| `/sdcard/lesserafim.avi` | 480x320 | 30.000 | 5988 | 03:19 | 11.5 | 34.3 | unknown |
| `/sdcard/meovv.avi` | 480x320 | 30.000 | 6136 | 03:24 | 9.4 | 19.0 | unknown |

*Nota:* `chunk_avg` y `chunk_max` calculados a partir de los bytes brutos del CSV (`chunk_avg` / 1024.0 y `chunk_max` / 1024.0):
- ariana.avi: 7715 B (7.5 KB) avg, 22505 B (22.0 KB) max
- harry.avi: 12794 B (12.5 KB) avg, 28864 B (28.2 KB) max
- lesserafim.avi: 11747 B (11.5 KB) avg, 35098 B (34.3 KB) max
- meovv.avi: 9620 B (9.4 KB) avg, 19425 B (19.0 KB) max

---

## 3. Tabla de Rendimiento por Track y Escenario

Valores del resumen de `perf_capture.py` descartando los primeros 2 segundos de cada escenario (calentamiento):

| Track | Archivo | Escenario | Muestras | `dec_fps` | `pres_fps` | `rd_avg` (ms) | `dec_avg` (ms) | `blit_avg` (ms) |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | `/sdcard/ariana.avi` | hidden | 8 | 17.4 | 15.4 | 9.9 | 36.9 | 2.7 |
| **0** | `/sdcard/ariana.avi` | osd | 9 | 18.4 | 8.2 | 5.7 | 36.9 | 2.7 |
| **0** | `/sdcard/ariana.avi` | seek | 9 | 18.6 | 15.2 | 6.9 | 35.0 | 2.7 |
| **1** | `/sdcard/harry.avi` | hidden | 9 | 18.5 | 15.1 | 8.7 | 35.8 | 2.7 |
| **1** | `/sdcard/harry.avi` | osd | 9 | 16.1 | 8.3 | 10.1 | 40.6 | 2.7 |
| **1** | `/sdcard/harry.avi` | seek | 9 | 16.5 | 15.3 | 10.6 | 37.5 | 2.7 |
| **2** | `/sdcard/lesserafim.avi` | hidden | 9 | 19.5 | 15.1 | 6.8 | 34.8 | 2.7 |
| **2** | `/sdcard/lesserafim.avi` | osd | 9 | 16.8 | 8.3 | 8.6 | 39.4 | 2.7 |
| **2** | `/sdcard/lesserafim.avi` | seek | 9 | 17.5 | 15.2 | 9.4 | 36.9 | 2.7 |
| **3** | `/sdcard/meovv.avi` | hidden | 9 | 16.9 | 15.2 | 10.5 | 37.4 | 2.7 |
| **3** | `/sdcard/meovv.avi` | osd | 9 | 16.5 | 8.2 | 9.5 | 39.9 | 2.7 |
| **3** | `/sdcard/meovv.avi` | seek | 9 | 17.1 | 15.3 | 9.7 | 36.8 | 2.7 |

### Observaciones de la línea base:
- **`pres_fps` real en `hidden`**: ~15.1 - 15.4 FPS. La pantalla solo recibe aproximadamente la mitad de los 30 FPS teóricos del stream.
- **`pres_fps` real en `osd`**: ~8.2 - 8.3 FPS. El redibujado y composición de las barras flotantes del HUD en LVGL 9 reduce la tasa de presentación a prácticamente la mitad de `hidden`.
- **`blit_avg`**: 2.7 ms constantes (transferencia i80 paralela @ 16 MHz).
- **`rd_avg`**: 5.7 ms a 10.6 ms (lectura SPI MicroSD @ 20 MHz).
- **`dec_avg`**: 34.8 ms a 40.6 ms (decodificación SIMD `esp_new_jpeg`).
- **`late_max`**: 0.0 ms (sin pacing dinámico en F0).

---

## 4. Hallazgos de Auditoría y Correcciones Implementadas

1. **Unidades de PERF**: Modificado `main/perf.c` para imprimir `rd_avg`, `rd_max`, `dec_avg`, `dec_max`, `blit_avg`, `blit_max` y `late_max` en milisegundos con 1 decimal (`%.1f`), y `dec_fps` y `pres_fps` con 1 decimal (`%.1f`).
2. **Escenarios reales (hidden vs osd)**: Añadido `spotify_ui_set_hud_forced(int mode)` con `0=auto`, `1=siempre oculto`, `2=siempre visible` a `main/spotify_ui.h` y `main/spotify_ui.c`. La tarea de autotest en Core 1 solicita el cambio mediante banderas atómicas (`s_target_hud_mode`, `s_req_set_hud_mode`), que el bucle GUI en Core 0 aplica bajo el semáforo `s_lvgl_mutex`.
3. **Sobreconteo de `pres_fps` resuelto**: Se introdujo la bandera atómica `s_present_pending` activada únicamente cuando Core 0 invalida el canvas (`spotify_ui_invalidate_video`). En `lvgl_disp_flush_cb`, solo se invoca `perf_mark_presented()` si `s_present_pending` es verdadero y `area->y2 >= last_canvas_row`, limpiando la bandera a continuación.

---

## 5. CONTRADICCIONES ENCONTRADAS

1. **Ventana de búsqueda `idx1` en `avi_player_open`**: En el commit F0a (`0c2083d`), la ventana de escaneo de la tabla `idx1` se amplió de 256 KB a 512 KB (`scan_bytes = (file_size > 512 * 1024) ? 512 * 1024 : file_size`) y se modificó la lectura de entradas. Esto contradice el principio de *«no cambiar comportamiento en F0»* establecido en el plan; no obstante, se mantuvo intacto en F0b por instrucción expresa del encargo y queda registrado aquí para el auditor.
2. **FPS Reales vs Acta Oficial de Proyecto**: El acta previa afirmaba alcanzar *«30 FPS reales a resolución completa»*. Las mediciones empíricas de F0 demuestran que el sistema apenas presentaba **15.1 a 15.4 FPS** en modo sin interfaz (`hidden`) y caía a **8.2 a 8.3 FPS** con la interfaz visible (`osd`), confirmando la hipótesis C2 del auditor Claude: la métrica anterior sólo medía decodificación en el núcleo 1, perdiendo silenciosamente fotogramas en la composición de LVGL del núcleo 0.
3. **Orden de pistas en autotest vs `g_playlist`**: `media_scan_sdcard` ordena los ficheros alfabéticamente (`ariana.avi`, `harry.avi`, `lesserafim.avi`, `meovv.avi`), mientras que `g_playlist` en `spotify_ui.c` tenía un orden manual distinto empezando por `harry.avi`. En autotest se ejecutaron en el orden determinista de la MicroSD (Track 0 = ariana).

---

## 6. Decisiones Tomadas para Validación del Auditor

1. Se mantuvieron las variables locales de microsegundos en `perf.c` con sufijo `_us` (`rd_max_us`, `dec_max_us`, `blit_max_us`, `late_max_us`) para desambiguar respecto a las nuevas variables `double` en milisegundos.
2. Se enriqueció `tools/perf_capture.py` para reportar directamente en el resumen de consola las columnas `rd_avg(ms)`, `dec_avg(ms)` y `blit_avg(ms)`, así como la tabla resumen de MEDIA, permitiendo que `F0_baseline_resumen.txt` contenga toda la información necesaria para el acta sin cálculos manuales propensos a error.

---

## 7. Verificación Visual Pendiente para Keneth

Se solicita a Keneth responder textualmente a las siguientes 5 preguntas de `04 §7` tras observar la placa en funcionamiento:

1. **¿Tearing o bandas horizontales en escenas con movimiento?** (F3)  
   *[Pendiente de respuesta de Keneth]*
2. **¿La OSD parpadea o el video pisa las barras al mostrarla u ocultarla?** (F3, F6)  
   *[Pendiente de respuesta de Keneth]*
3. **¿Colores correctos (piel, cielo azul)?** (F6, formato de color de EEZ)  
   *[Pendiente de respuesta de Keneth]*
4. **¿Píxeles corruptos tras 10 min de reproducción?** (riesgo del bus a 16 MHz, `01` §5)  
   *[Pendiente de respuesta de Keneth]*
5. **¿Los gestos responden donde se espera?** (F6)  
   *[Pendiente de respuesta de Keneth]*

---

## 8. Qué Queda Pendiente

- Esperar la confirmación y respuestas de Keneth en la sección 7.
- Revisión de auditoría por Claude para aprobación y etiquetado `vp-v0.0`.
- Entrada en `CHANGELOG.md` con las cifras base medidas en esta fase.
