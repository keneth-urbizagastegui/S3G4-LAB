# Fase 5b — Biblioteca dinámica, metadatos, posición guardada y compatibilidad

**Resultado: CUMPLE.** Código de Antigravity (commit `0fbfe36`), cortado por cuota antes de flashear.
**Medición, pruebas en placa e informe: auditor (16/09/2026).**

## Qué se hizo
- `media_library.c/.h`: escaneo de la microSD sin lista fija, orden alfabético, título y subtítulo del
  `.json`, miniatura `.jpg` en PSRAM (tope `APP_THUMB_CACHE_MAX=24`), validación de compatibilidad por
  contenido y línea `LIB`. `g_playlist` y `PLAYLIST_SIZE` eliminados.
- `settings_nvs.c/.h`: espacio `s3g4vid` con brillo, OSD, repetición, aleatorio, reanudar, salto, último
  video y posición por video (clave con hash del nombre), con poda de claves huérfanas.
- Componente cJSON de IDF. Código muerto (`lz4`, `s3v_player`, `tjpgd`) movido a `legacy/`.

## Medido (`F5b_run1.csv`, perf_capture `--phase F5b` → código 0)
| Criterio | Umbral | Medido | |
|---|---|---|---|
| pres oculto / con OSD | ≥ 28,5 / ≥ 28,0 | 29,29–30,04 / 29,45–30,02 | ✔ |
| **Descartes ocultos** | ≤ 1 % por pista y global | 0,64 / 0,63 / 0,00 / 0,00 % · **0,31 %** global | ✔ |
| TE, deriva, STRESS, TAP | los de F5a | OK (deriva 69 ms) | ✔ |
| `LIB` | count = compatibles + no compatibles | `count=4, compatible=4, with_json=4, with_thumb=4` | ✔ |
| Escaneo | < 3000 ms | **809 ms** | ✔ |
| Memoria | heap ≥ 30 KB · PSRAM ≥ 6 MB | 57 127 B · 7,89 MB | ✔ |

## Pruebas en placa (auditor)
- **Posición guardada** (`F5b_nvs_test.log`): reproducción de ~45 s y reinicio en caliente → reanudó en
  174,2 s cuando lo esperado era ~179 s. **Pierde hasta 5 s**, por el guardado cada 5 s. La
  especificación pedía ±2 s, lo cual es **incompatible con guardar cada 5 s** (error del paquete, no del
  código). Propuesta para F6: al reanudar, retroceder 2 s adrede (práctica habitual) y documentar ±5 s.
- **Tarjeta con ficheros nuevos** (`F5b_trampas_boot.log`): 8 ficheros, escaneo en 1176 ms, **sin colgarse**.
  - `quinto.avi` **aparece sin recompilar**, con su título y su miniatura. ✔
  - `trampa_roto.avi` → «Archivo truncado». ✔
  - `trampa_tamano.avi` → «Resolución 240x160». ✔
  - `trampa_codec.avi` → **aceptado**. La trampa estaba mal diseñada por el auditor: etiqueta XVID pero con
    fotogramas JPEG de verdad, y la regla admite el fichero si el primer fotograma es JPEG, así que el
    firmware acertó (ese fichero se puede reproducir). **Generador corregido**: la nueva trampa lleva datos
    que no son JPEG. Queda por repetir en la próxima vez que la tarjeta pase por el PC.

## Pendiente (pasa a F6)
- Presentación en la interfaz de los incompatibles (tarjeta atenuada con el motivo, aviso «sin girar»,
  pantalla de ninguno compatible): la UI actual es provisional y se sustituye en F6.
- Botón «Volver a escanear» (existe la función; falta la UI).
- Repetir la trampa de códec corregida.
