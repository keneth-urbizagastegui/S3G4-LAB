# 08 — Paquete de trabajo F5d: video girado en origen (elimina el tearing sin coste en fps)

> Encargo listo para enviar **tal cual** a Antigravity con `--print-timeout 120m`.
> Rama **ya creada**: `video-player/fase-5d`, desde `235a7e7` (final de F5a: 44,6 Hz, TE, blit por
> franjas desde memoria interna, 29,67 fps y 0,31 % de descartes).
> **No partas de `video-player/fase-5c`**: ese experimento está descartado (ver `informes/FASE_5c.md`).

## Por qué esta vía

- El tearing es **de orientación**, confirmado con foto: escribimos filas de 480 px que son columnas del
  barrido (`informes/FASE_5a.md`, sección del diagnóstico).
- Girar **en el chip** (F5c) cuesta 6 ms más de decodificación y 2,7 ms más de envío (PSRAM): 27,8 fps,
  o 30 fps con pánico por falta de memoria. Descartado.
- Girar **en el fichero** no cuesta nada en ejecución: el decodificador entrega filas de 320 px que ya
  son líneas nativas del panel, y el envío vuelve a ser el rápido por franjas desde memoria interna
  (20,2 ms, que cabe en los 22,42 ms del refresco).

## Material ya preparado por el auditor (no lo rehagas)

`TFT_8Bit_Capacitive/videos_rot/` con los 4 videos girados 90° (ffmpeg 9.0.1,
`scale=480:320:...,crop=480:320,fps=30,transpose=1`, MJPEG 4:2:0 `-q:v 8`), cada uno con su `.jpg`
(144×81) y su `.json`:

| Fichero | Tamaño | Fotogramas | Medio | Máximo |
|---|---|---|---|---|
| `harry_rot.avi` | 71,3 MB | 6029 | 12,1 KB | 27,6 KB |
| `ariana_rot.avi` | 68,2 MB | 9003 | 7,7 KB | 26,0 KB |
| `lesserafim_rot.avi` | 67,4 MB | 5988 | 11,5 KB | 34,3 KB |
| `meovv_rot.avi` | 59,3 MB | 6136 | 9,9 KB | 20,3 KB |

**YA ESTÁN COPIADOS EN LA MICROSD** (16/09/2026, con los nombres de siempre: harry.avi, ariana.avi,
lesserafim.avi, meovv.avi, cada uno con su .jpg y su .json). **Los originales sin girar ya no están y no
se restauran: no hay nada que comparar.** Decisión de Keneth: avanzar, no volver a medir lo ya descartado.

## Tareas

### T1 — Reconocer el video girado y elegir la orientación del panel
- La biblioteca acepta ficheros **320×480** además de 480×320. `media_item_t` (o el escaneo actual)
  marca `rotated = (w == 320 && h == 480)`.
- Con un fichero girado: `MADCTL` **sin el bit MV** (orientación nativa) y el blit escribe líneas de
  320 px consecutivas, **en el mismo sentido que el barrido**. Opción de Kconfig `APP_LCD_MADCTL_NATIVE`
  con el valor elegido; documenta el `0x28` anterior y prueba los candidatos hasta que la imagen se vea
  derecha y con los colores correctos (hoy se ven bien: no los estropees).
- Con un fichero 480×320 se mantiene el comportamiento actual. **Se puede cambiar de MADCTL al abrir
  cada video**; si eso provoca parpadeo al cambiar de pista, anótalo.
- **El modo por franjas (`block_enable = true`) se mantiene**: es lo que da los 20,2 ms.

### T2 — Táctil e interfaz en orientación nativa
- `lvgl_touch_read_cb` aplica hoy una transformación para paisaje (acta, anomalía 7). Revísala para la
  orientación nueva: tocar una esquina debe activar el botón que se ve en esa esquina.
- LVGL puede quedarse con el display en 320×480 y `lv_display_set_rotation(disp, LV_DISPLAY_ROTATION_90)`
  para que las pantallas sigan diseñadas en 480×320 (así lo espera `03`). La rotación por software solo
  afecta a lo que LVGL redibuja (barras de la OSD), no al video.
- El recorte del flush alrededor del rectángulo de video (F3) debe seguir funcionando.

### T3 — Medición
- Autotest con los **4 ficheros girados** que hay en la tarjeta. En `PERF`, cada registro lleva
  `rot=90` y `madctl=0x..`. **No hay versión sin girar: no se compara nada en la placa.**
- CSV: `F5d_run1.csv`. Compara con `F5a_final.csv` (`--compare`).
- **Criterios (fijos, no los toques):** pres_fps oculto ≥ 28,5 y con OSD ≥ 28,0; drop oculto ≤ 1 % por
  pista y global; te_present=1 con variación ≤ 2 Hz; te_timeout ≤ 1 %; present_path=direct;
  |drift| < 100; TAP 0→1; STRESS `title_mismatch=0` y pres > 20; `reader_rd_avg` < 15 ms;
  `q_wait_max` < 15 ms; `heap_int` ≥ 30 000 B.
- **Lo esperado** es igualar o mejorar F5a (29,67 / 30,00 / 0,31 %). Si no se alcanza, entrega las
  cifras: un fallo medido es un resultado válido.

### T4 — Conversor
`TFT_8Bit_Capacitive/convert_videos.py` (del auditor) gana `--rotate 0|90` (por defecto 90 cuando se
confirme esta vía), que añade `transpose=1` al filtro y deja constancia en el `.json`
(`"rotated": true`). **No reescribas el resto del script.**

### T5 — Documentación
- Actualiza el acta del proyecto y `06_paquete_F5b.md` §7: un video **480×320 sin girar ya no es el
  formato recomendado**, pero **se sigue reproduciendo** (sin la ventaja del tearing). El motivo de
  incompatibilidad solo se muestra si no cumple las otras reglas.
- Informe `informes/FASE_5d.md` con el formato de `04` §9, tabla de criterios **incluida la fila de
  descartes**, MADCTL elegido, qué cambió en el táctil, CONTRADICCIONES y verificación visual:
  (a) modo C de `tear_diag`: ¿sigue la diagonal? (b) ¿imagen derecha y colores correctos? (c) ¿el táctil
  responde donde se ve el botón en las 4 esquinas? (d) ¿fluidez igual o mejor?

## Entorno
PowerShell (si tu shell es bash: `powershell -NoProfile -Command` y `$env:MSYSTEM=$null`):
```
$env:IDF_PATH = "C:\esp\v6.0.1\esp-idf"; $env:IDF_TOOLS_PATH = "C:\Users\Keneth\.espressif"
. "C:\esp\v6.0.1\esp-idf\export.ps1"
idf.py build ; idf.py -B build_perf -D SDKCONFIG=sdkconfig.perf -D SDKCONFIG_DEFAULTS="sdkconfig.defaults;sdkconfig.perf.defaults" build
idf.py -B build_perf -p COM16 flash
python tools\perf_capture.py --port COM16 --out plan_antigravity\mediciones\F5d_run1.csv --phase F5a --compare plan_antigravity\mediciones\F5a_final.csv --timeout 1200
```
`ffmpeg` ya está instalado en
`C:\Users\Keneth\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe`
(puede no estar en el PATH de una terminal vieja).

## Límites
NO tocar: reloj i80 16 MHz, FRMCTR1 (44,6 Hz ya elegido), pinout, `managed_components`, umbrales, el
modo por franjas, `tear_diag` (debe seguir compilado y arrancando en OFF), nada fuera de
`test_video_player` salvo el conversor.
**Nunca desactives un perro guardián ni relajes un umbral para que pase una prueba** (ocurrió en F5c).
Si algo no cabe en el tiempo, entrega lo medido y dilo.
