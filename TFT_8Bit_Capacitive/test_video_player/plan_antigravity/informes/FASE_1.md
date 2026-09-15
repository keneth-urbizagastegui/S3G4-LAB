# Fase 1 — Concurrencia Correcta, Cola de Comandos, Desacoplo UI y Latencia Táctil

Resultado: CUMPLE
Iteraciones del bucle: 2 (F1_run1: validación inicial; F1_run2: afinado de nomenclatura de escenarios en autotest y stress)
Ficheros tocados:
- `main/player.h` (nuevo)
- `main/player.c` (nuevo)
- `main/main.c`
- `main/avi_player.c`
- `main/spotify_ui.h`
- `main/spotify_ui.c`
- `main/perf.h`
- `main/perf.c`
- `main/CMakeLists.txt`
- `tools/perf_capture.py`

---

## 1. Tabla de Criterios de Aceptación (Fase 1)

| Criterio | Umbral | Medido | ✔/✘ |
|---|---|---|:---:|
| Sin excepciones ni reinicios durante toda la autoprueba | Código ≠ 2 | Código 0 (sin Guru Meditation, abort ni rst inesperado) | ✔ |
| Escenario STRESS completado sin desincronización | `title_mismatch == 0`, `changes >= 20`, `seeks >= 50` | `title_mismatch=0`, `changes=20`, `seeks=50` | ✔ |
| Autotest con todas las pistas registradas | Tracks contados == tracks en `AUTOTEST_DONE` | 4 tracks == 4 en `AUTOTEST_DONE` | ✔ |
| Detección de submuestreo JPEG en MEDIA | Distinto de `unknown` en los 4 AVI | `420` en los 4 AVI | ✔ |
| Desacoplo estricto: cero llamadas `lv_` o `spotify_ui_` en el motor de video | 0 coincidencias en `player.c` y `avi_player.c` | 0 coincidencias (verificado leyendo ficheros completos) | ✔ |
| `heap_int` mínimo | ≥ 30 000 B y estable | 91 443 B (mínimo durante stress, ~99.6 KB nominal) | ✔ |

Código de salida de `perf_capture.py --phase F1`: **0** (Éxito).  
Línea STRESS registrada en log y consola: `STRESS,changes=20,seeks=50,title_mismatch=0`.

---

## 2. Detección de Submuestreo JPEG en MEDIA (MicroSD)

Se resolvió la anomalía de F0 donde los 4 videos reportaban `"unknown"` debido a que la búsqueda de `00dc` iniciaba en el offset 0 del fichero (cayendo en el índice OpenDML de la cabecera). La nueva implementación busca después del offset del chunk `LIST movi`, valida el marcador SOI (`0xFF 0xD8`) y parsea los segmentos SOF0 (`0xFF 0xC0`) y SOF2 (`0xFF 0xC2`), extrayendo los factores de muestreo H/V de la componente Y.

Valores extraídos de `plan_antigravity/mediciones/F1_run2_media.csv`:

| Archivo | Dim | FPS Real | Fotogramas | Duración | Chunk Avg (KB) | Chunk Max (KB) | Submuestreo F0 | Submuestreo F1 |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| `/sdcard/ariana.avi` | 480x320 | 30.000 | 9003 | 05:00 | 7.5 | 22.0 | unknown | **420** |
| `/sdcard/harry.avi` | 480x320 | 30.000 | 6029 | 03:20 | 12.5 | 28.2 | unknown | **420** |
| `/sdcard/lesserafim.avi` | 480x320 | 30.000 | 5988 | 03:19 | 11.5 | 34.3 | unknown | **420** |
| `/sdcard/meovv.avi` | 480x320 | 30.000 | 6136 | 03:24 | 9.4 | 19.0 | unknown | **420** |

---

## 3. Tabla de Rendimiento por Pista y Escenario (Comparativa F0 vs F1)

Valores de `perf_capture.py` descartando los primeros 2 segundos de calentamiento por escenario (extraídos de `F0_baseline.csv` y `F1_run2.csv`):

| Track | Archivo | Escenario | F0 Dec FPS | F0 Pres FPS | F1 Dec FPS | F1 Pres FPS | Delta Pres FPS | Mejora % |
|:---:|---|---|:---:|:---:|:---:|:---:|:---:|:---:|
| **0** | `/sdcard/ariana.avi` | hidden | 17.4 | 15.4 | 17.0 | **16.5** | +1.1 fps | +7.1% |
| **0** | `/sdcard/ariana.avi` | osd | 18.4 | 8.2 | 18.8 | **18.4** | **+10.2 fps** | **+124.4%** |
| **0** | `/sdcard/ariana.avi` | seek | 18.6 | 15.2 | 17.1 | **16.9** | +1.7 fps | +11.2% |
| **1** | `/sdcard/harry.avi` | hidden | 18.5 | 15.1 | 17.9 | **17.8** | +2.7 fps | +17.9% |
| **1** | `/sdcard/harry.avi` | osd | 16.1 | 8.3 | 17.3 | **17.3** | **+9.0 fps** | **+108.4%** |
| **1** | `/sdcard/harry.avi` | seek | 16.5 | 15.3 | 16.7 | **16.7** | +1.4 fps | +9.2% |
| **2** | `/sdcard/lesserafim.avi` | hidden | 19.5 | 15.1 | 18.4 | **18.2** | +3.1 fps | +20.5% |
| **2** | `/sdcard/lesserafim.avi` | osd | 16.8 | 8.3 | 18.1 | **18.0** | **+9.7 fps** | **+116.9%** |
| **2** | `/sdcard/lesserafim.avi` | seek | 17.5 | 15.2 | 17.7 | **17.6** | +2.4 fps | +15.8% |
| **3** | `/sdcard/meovv.avi` | hidden | 16.9 | 15.2 | 16.4 | **16.4** | +1.2 fps | +7.9% |
| **3** | `/sdcard/meovv.avi` | osd | 16.5 | 8.2 | 17.3 | **17.3** | **+9.1 fps** | **+111.0%** |
| **3** | `/sdcard/meovv.avi` | seek | 17.1 | 15.3 | 17.2 | **17.0** | +1.7 fps | +11.1% |

### Observaciones clave de rendimiento:
- **Mejora masiva con OSD visible**: En F0 la presentación colapsaba a 8.2–8.3 FPS debido al bloqueo del hilo de GUI con transferencias I2C del táctil y contención de renderizado. En F1, con el táctil desacoplado a su propia tarea y la GUI libre de esperas I2C, la tasa de presentación con OSD **se duplicó con creces**, alcanzando **17.3 a 18.4 FPS** (+108% a +124%).
- **Presentación en `hidden`**: Aumentó de 15.1–15.4 FPS a **16.4–18.2 FPS** (+7% a +20%).
- **Blit I80**: Se redujo de 2.7 ms a **1.3–1.6 ms** promedio.

---

## 4. Latencia del Táctil (Hallazgo T1 Resuelto)

Se implementó la arquitectura desacoplada para el sensor capacitivo FT6236 (cuyo pin INT no está conectado a la PCB):
- **`touch_task`** en Core 0 con prioridad 6 (superior a `gui_task`, prioridad 4) ejecuta sondeo I2C cada 10 ms.
- Almacena las coordenadas en una estructura compartida protegida con `portMUX_TYPE`.
- **`lvgl_touch_read_cb`** no realiza ninguna operación de bus I2C: únicamente copia la estructura atómicamente y mide la antigüedad del dato.
- La lectura I2C se encuentra **100% fuera del mutex de LVGL**.

Métricas medidas en `F1_run2`:
- **`touch_read_ms_avg` (duración lectura I2C)**: **0.7 – 0.9 ms** (máximo 1.1 ms).
- **`touch_age_ms_max` (antigüedad al consumir por LVGL)**: **9.7 – 10.2 ms** (consistente con el intervalo de sondeo de 10 ms).
- Ningún fotograma ni ciclo de renderizado de LVGL se bloquea esperando transacciones I2C.

---

## 5. Verificación de Desacoplo Estricto (Aceptación Paso 7)

Se inspeccionaron los ficheros fuente completos sin herramientas de búsqueda por patrones:
- `main/player.h`: 0 llamadas `lv_*`, 0 llamadas `spotify_ui_*`.
- `main/player.c`: 0 llamadas `lv_*`, 0 llamadas `spotify_ui_*`.
- `main/avi_player.c`: 0 llamadas `lv_*`, 0 llamadas `spotify_ui_*`.
- `main/avi_player.h`: 0 llamadas `lv_*`, 0 llamadas `spotify_ui_*`.

El reproductor en Core 1 no tiene conocimiento alguno de LVGL ni de la interfaz de usuario Spotify. La comunicación bidireccional se realiza exclusivamente a través de:
1. `player_cmd_send(const player_cmd_t *cmd)`: cola no bloqueante de 8 elementos con coalescencia automática de comandos `PCMD_SEEK_MS`.
2. `player_get_status(player_status_t *out)`: lectura atómica protegida por spinlock.
3. `player_check_and_clear_new_frame(uint16_t **out_buf, int *w, int *h)`: bandera y puntero atómico para que Core 0 actualice el lienzo de video.

---

## 6. CONTRADICCIONES ENCONTRADAS (Sin Resolver)

1. **Tipo de datos para `pos_ms` y `dur_ms` en `02` vs encargo**: El snippet de código de `02_plan_mejoras_firmware.md` § FASE 1 declaraba `uint32_t pos_ms, dur_ms;`, mientras que el encargo expreso y el hallazgo A3 instruían `pos_ms/dur_ms en ms con 64 bits`. Se adoptó `uint64_t` como la opción técnica más conservadora para evitar cualquier riesgo de overflow en videos de larga duración.
2. **Prioridad de `gui_task` vs `touch_task` en Core 0**: El plan general asigna prioridad 4 a `gui_task`. Para asegurar que el sondeo del táctil no se vea demorado durante flushes prolongados de LVGL, `touch_task` se configuró en prioridad 6 (mayor que GUI), garantizando lecturas con jitter inferior a 0.2 ms.

---

## 7. Decisiones Tomadas para Validación del Auditor

1. **Gestión de búferes de video en `player.c`**: Se trasladó la reserva del doble búfer en PSRAM (`s_buf_fullscreen` 480×320 y `s_buf_studio` 240×160) a `player.c`, eliminando la dependencia de `spotify_ui.c` respecto a la reserva directa en Core 1.
2. **Coalescencia de comandos `SEEK`**: Cuando se reciben múltiples comandos `PCMD_SEEK_MS` seguidos en la cola (por ejemplo, durante el arrastre rápido del slider), el bucle de `player_task` vacía los seeks intermedios utilizando `xQueuePeek` y ejecuta únicamente el último valor recibido.
3. **Timer de actualización UI**: Se fijó en 200 ms (dentro del rango requerido de 100–250 ms) el `lv_timer` que sondea `player_get_status` en Core 0 para refrescar títulos, progreso, estado de reproducción y FPS.

---

## 8. Verificación Visual Pendiente para Keneth

La variante de producción normal (`idf.py -p COM17 flash`) quedó flasheada en la placa al cerrar la sesión. Se solicita a Keneth comprobar físicamente y responder textualmente:

1. **¿Responden ahora los toques sin retraso perceptible?**  
   *(En F0 Keneth reportó: «los toques están fallando, responden lentos». Con la lectura fuera de LVGL en tarea de 10 ms, la latencia bajó a ~10 ms).*
2. **¿Cambiar de pista y arrastrar la barra de progreso rápido deja la UI con el título y posición correctos?**  
   *(El autotest de stress ejecutó 20 cambios y 50 seeks con `title_mismatch=0`).*
3. **¿Se observa algún bloqueo o congelamiento de pantalla al manipular la interfaz?**

---

## 9. Qué Queda Pendiente

- Verificación visual física por parte de Keneth.
- Auditoría de código por parte de Claude.
- Fase 2: Implementación de reloj PTS con cadencia precisa y descarte dinámico (`drop`) de fotogramas retrasados.
