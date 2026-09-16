# 06 — Paquete de trabajo F5b: biblioteca dinámica, metadatos y persistencia

> Encargo listo para enviar a Antigravity **tal cual** (con `--print-timeout 120m`), en cuanto F5a esté
> cerrada y etiquetada. Rama: `video-player/fase-5b` desde `vp-v0.5` (**ya etiquetada el 16/09/2026**).
> Sustituye a la «FASE 5» original de `02`, ya con las decisiones tomadas hasta el 15/09/2026.

## Contexto que el constructor no debe volver a averiguar

- Desde F5d los 4 AVI de la microSD están **girados en origen: 320×480**, 30 fps, 4:2:0, con `idx1`, cada
  uno con su `.jpg` y su `.json` (7,7–12,1 KB de media por fotograma, 34,3 KB el mayor). **Es el formato
  recomendado**: sin él vuelve el corte diagonal. Ver `informes/FASE_5d.md`.
- El panel trabaja en orientación nativa (`MADCTL 0x48`) y la vista pequeña ya gira sola los ficheros
  320×480 (`ensure_studio_decoder`). **No toques la ruta de presentación ni la recuperación de la SD.**
- La microSD va a **20 MHz** (26 y 40 MHz no montan, F4). El lector adelantado vive en el núcleo 0 con
  3 huecos en PSRAM; `q_wait_max` 0,1 ms.
- El escaneo actual (`media_scan_sdcard` en `avi_player.c`) ya lista los `.avi` de `/sdcard` y publica
  la línea `MEDIA`. **F5b lo extiende, no lo reescribe.**
- La UI actual (`spotify_ui.c`) es provisional: **no inviertas tiempo en ella**, se sustituye en F6.
  Lo de F5b que la UI necesita se expone por `player_status_t` y por la API de la biblioteca.

## Entregables

### 1. `main/media_library.c/.h` (nuevo, saca la biblioteca de `avi_player.c`)
```c
typedef struct {
    char path[128];        // /sdcard/videos/harry.avi
    char title[64];        // del .json, o el nombre sin extensión
    char subtitle[64];     // del .json ("artista"), o ""
    uint32_t dur_ms;       // de la cabecera AVI (frames * us_per_frame), NO del .json
    uint32_t frames;
    uint16_t w, h;
    uint32_t fps_milli;
    uint32_t chunk_max;    // recorriendo idx1 (ya se hace en la línea MEDIA)
    bool has_thumb;        // existe <nombre>.jpg
    void *thumb_dsc;       // lv_image_dsc_t* en PSRAM, NULL si no hay; lo rellena la UI en F6
    uint32_t resume_ms;    // posición guardada en NVS, 0 si ninguna
} media_item_t;

esp_err_t media_library_scan(void);     // escanea y ordena; devuelve ESP_OK aunque haya 0 videos
int  media_library_count(void);         // CONTADO, sin constantes
const media_item_t *media_library_get(int index);
int  media_library_index_of(const char *path);
```
- Busca en **`/sdcard/videos/` y, si no existe, en `/sdcard/`** (compatibilidad con la tarjeta actual).
- Orden alfabético por nombre de fichero, estable.
- Por cada `nombre.avi`, lee si existen: `nombre.json` y `nombre.jpg` (ver §3).
- **Progreso del escaneo** para la pantalla de `03` §10.3: callback
  `media_library_set_progress_cb(void (*cb)(int done, int total))`, llamado desde la tarea de escaneo;
  la UI solo lee. Nunca llamar a `lv_*` desde aquí.
- El escaneo **no decodifica video**: nada de generar miniaturas al vuelo (`03` §10.5).

### 2. Metadatos `nombre.json` (parseo con el componente `json` de IDF, cJSON)
```json
{ "title": "Dance No More", "subtitle": "Harry Styles" }
```
- Claves desconocidas se ignoran. Si falta el fichero o está mal formado: `title` = nombre sin
  extensión, `subtitle` = "", y **una línea de log**, no un fallo.
- Tamaño máximo aceptado: 2 KB por fichero. Por encima, se ignora con aviso.

### 3. Miniaturas `nombre.jpg`
- 144×81, JPEG 4:2:0 (las genera el conversor, §5).
- Se decodifican **una vez** al escanear, a RGB565 en PSRAM (144×81×2 = 23 328 B por video).
- **Tope de memoria: 24 miniaturas** (unos 560 KB). A partir de ahí, las tarjetas usan el marcador de
  posición de `03` §10.5. El tope es una constante de Kconfig `APP_THUMB_CACHE_MAX` (default 24).
- Si el `.jpg` no es 144×81, se ignora y se usa el marcador (no se reescala).

### 4. Persistencia en NVS (`main/settings_nvs.c/.h`)
Espacio de nombres `s3g4vid`. Claves y tipos exactos:
| Clave | Tipo | Default | Uso |
|---|---|---|---|
| `bright` | u8 (10–100) | 70 | brillo |
| `osd_ms` | u16 | 3000 | ocultar OSD (0 = nunca) |
| `stats` | u8 (0/1) | 0 | mostrar chip de fps |
| `miniprog` | u8 (0/1) | 1 | barra fina de progreso |
| `repeat` | u8 (0/1/2) | 1 | off / todo / uno |
| `shuffle` | u8 (0/1) | 0 | aleatorio |
| `resume` | u8 (0/1) | 1 | continuar donde lo dejé |
| `seekstep` | u8 (5/10/30) | 10 | salto de ⟲ ⟳ en segundos |
| `last_path` | str | "" | último video |
| `pos_<hash>` | u32 | — | posición en ms por video; `<hash>` = FNV-1a de 32 bits del nombre de fichero, en hexadecimal |
- **Escritura:** posición cada 5 s de reproducción y al pausar, cambiar de pista o apagar. Nunca por
  fotograma (NVS tiene ciclos de escritura limitados).
- **Poda:** al escanear, borrar las claves `pos_*` cuyo video ya no está. Contar las borradas y
  registrarlo.
- «Continuar donde lo dejé» solo si la posición guardada está entre **5 s y duración − 10 s**.

### 5. Conversor unificado `TFT_8Bit_Capacitive/convert_videos.py`
Ya escrito por el auditor (ver ese fichero). **Antigravity no lo reescribe**: solo lo usa si necesita
generar material de prueba, y reporta cualquier fallo. Sustituye a `convert_to_s3v.py` y al antiguo
`convert_videos.py`, que pasan a `legacy/`.

### 6. Limpieza (M1, M2, M5 de `01`)
- `legacy/`: `s3v_player.*`, `lz4.*`, `tjpgd*`, y el `spotify_ui.*` solo cuando F6 lo reemplace.
- `g_playlist` desaparece: toda la reproducción se dirige por índice de `media_library`.
- `PLAYLIST_SIZE` no puede quedar en ningún fichero.

## Criterios de aceptación (perf_capture `--phase F5b`)
- Se mantienen **todos** los de F5a (fps, descartes, TE, drift, STRESS, TAP).
- `LIB,count=<n>,with_json=<a>,with_thumb=<b>,scan_ms=<t>` en el log: `n` coincide con los `.avi` de la
  tarjeta **contados por el script** al listar el directorio.
- Meter un **5.º video** sin recompilar y que aparezca tras «Volver a escanear», con su título del JSON
  y su miniatura. Prueba manual de Keneth, documentada paso a paso.
- Reiniciar la placa y comprobar que vuelve al mismo video y posición (±2 s) con `resume=1`.
- `scan_ms` < 3000 ms con 5 videos y sus miniaturas.
- Memoria: `heap_int` mínimo ≥ 30 000 B y PSRAM libre ≥ 6 MB tras el escaneo.

## Lo que NO se toca en F5b
La ruta de presentación (F3/F5a), el reloj PTS, el driver del panel, la UI actual, `perf_capture.py`
más allá de añadir la comprobación de `LIB`, y nada fuera de `test_video_player` salvo el conversor.

---

## 7. Validación de compatibilidad: «Formato no compatible» (pedido por Keneth, 15/09/2026)

Hoy, si se copia un `.avi` que el reproductor no puede reproducir, falla sin explicar por qué. Como el
escaneo ya lee la cabecera de cada fichero, la biblioteca debe **decirlo en pantalla** y **no intentar
reproducirlo**.

### 7.1 Reglas de compatibilidad (todas se comprueban leyendo el fichero, sin decodificar)
| # | Requisito | De dónde sale | Motivo mostrado si falla |
|---|---|---|---|
| 1 | El vídeo es **MJPEG** | `strf`/`biCompression` del AVI (`MJPG`, `mjpg`, `jpeg`, `dmb1`) o el primer chunk empieza por `FF D8` | «No es MJPEG» |
| 2 | **480 × 320** exactos | `avih` | «Resolución 1280×720» (la real) |
| 3 | Submuestreo **4:2:0** | SOF0/SOF2 del primer fotograma (ya corregido en F1) | «Color 4:2:2 o 4:4:4» |
| 4 | **fps entre 24 y 31** | `us_per_frame` de `avih` | «60 fps» (los reales) |
| 5 | **chunk máximo ≤ 128 KB** | recorriendo `idx1` | «Fotogramas de 210 KB» |
| 6 | Tiene **`idx1`** | cola del fichero | «Sin índice: no se puede saltar» (**aviso, no bloqueo**: se reproduce sin saltos) |

- `media_item_t` gana: `bool compatible;` y `char incompat[48];` (el motivo, ya redactado para mostrar).
- La línea `MEDIA` gana `compat=1|0,reason=<texto sin comas>`.
- **Nada de rechazar por el nombre ni por la extensión**: se juzga por el contenido.

### 7.2 En la interfaz (coordinado con `03`)
- La tarjeta de un video incompatible se muestra **atenuada al 45 %**, con la miniatura de relleno, el
  título en `c_muted` y, en lugar de la duración, el motivo en `c_danger` a 11 px (por ejemplo
  «Resolución 1280×720»).
- Al tocarla **no reproduce**: muestra 3 s un aviso sobre la propia tarjeta con el motivo completo y la
  frase «Conviértelo con convert_videos.py».
- Los incompatibles **no entran en la cola** ni en «siguiente/anterior», y no cuentan en
  `library_summary`, que dirá «4 videos · 1 no compatible».
- Si **todos** son incompatibles: la pantalla `scr_no_media` en estado «sin videos» con el subtítulo
  «Hay N archivos, ninguno compatible. Conviértelos con convert_videos.py».

### 7.3 Criterio de aceptación añadido a F5b
- Copiar a la tarjeta **tres ficheros trampa** y comprobar que el escaneo los marca sin colgarse y sin
  reiniciar: (a) un AVI con códec no MJPEG, (b) un MJPEG de otra resolución, (c) un fichero `.avi` que
  en realidad sea texto o esté truncado.
- `LIB,count=<n>,compatible=<c>,incompatible=<i>` en el log, con `n = c + i` **contado**.
- El resto de criterios de F5b se mantienen; el tiempo de escaneo sigue por debajo de 3 s.
- Los tres ficheros trampa los genera el propio encargo con Python (no hace falta ffmpeg) y se dejan en
  `plan_antigravity/mediciones/ficheros_trampa/` para poder repetir la prueba.
