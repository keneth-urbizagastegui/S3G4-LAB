# Referencia visual del diseño — para construir en EEZ Studio al pie de la letra

Generado por `../exportar_referencia.py` (Chrome sin ventana). **No se edita a mano**: si cambia un
tablero, se vuelve a ejecutar el script. Los tableros de estados salen de `../generar_tableros_estados.py`
y los iconos de `../iconos/generar_iconos.py`.

| Carpeta | Contenido |
|---|---|
| `png/<Tablero>.png` | Captura a **480×320**, píxel a píxel igual que el panel. Es la imagen contra la que se compara. |
| `png/<Tablero>@2x.png` | Igual, a 960×640, para ver detalles finos. |
| `png/_iconos.png` | Hoja de control de los 25 iconos (a 2×). |
| `widgets/<Tablero>.md` | Tabla por elemento: x, y, ancho, alto, fondo, color, borde, radio, opacidad, fuente, alineación y texto. |
| `widgets.json` | Las mismas tablas en JSON. |

`Componentes` y `Tokens` no son pantallas; su contenido está en `03_especificacion_ui_eez.md`.

## Pantallas y estados (19 tableros)

| Tablero | Pantalla EEZ | Qué muestra |
|---|---|---|
| Main | `scr_player` | OSD visible, reproduciendo, repetir todo |
| PlayerLimpio | `scr_player` | OSD oculta: solo el video y la barra fina `bar_mini_progress` |
| Gestos | `scr_player` | `ovl_brightness` (izq.) y `ovl_seek_hint` (der.; la versión izquierda va en x 64 con `seek_back`) |
| Estadisticas | `ovl_stats` | superposición de métricas |
| Bloqueo | `ovl_lock` | bloqueado, con anillo de «mantén pulsado» (widget `arc`, no icono) |
| **EstadosOSD** | `osd_bottom` | pausa (icono `play`), repetir off/uno, aleatorio activo, botón **pulsado** (fondo #1F2228 circular) y **desactivado** (40 %) |
| **PlayerAviso** | `scr_player` + aviso | los dos avisos emergentes (se muestran de uno en uno) |
| Biblioteca | `scr_library` | 4 videos, tarjeta en reproducción |
| **BibliotecaLlena** | `scr_library` | desplazada 40 px con barra de desplazamiento; tarjeta **no compatible** y tarjeta **«Sin girar»** |
| **BibliotecaAviso** | `scr_library` + aviso | al tocar una tarjeta no compatible: marco #E5484D en la miniatura y aviso con el motivo |
| Escaneo | `scr_library` | escaneando, con `bar_scan` y tarjeta sin miniatura |
| Cola | `scr_queue` | cola (F6b) |
| SinMedios | `scr_no_media` | no hay ningún `.avi` |
| **SinMediosIncompatibles** | `scr_no_media` | hay archivos pero ninguno compatible: icono en #E5484D, `btn_retry` y `btn_settings` |
| **BibliotecaReanudar** | `scr_library` + hoja | al tocar una tarjeta con posición guardada: «Continuar en m:ss» / «Desde el principio» |
| ErrorSD | `scr_no_media` (estado error) | no se puede leer la microSD |
| Ajustes, AjustesReproduccion, AjustesAlmacenamiento, AjustesAcercaDe | `scr_settings` | las 4 pestañas (F6b) |

## Reglas de traducción a LVGL/EEZ

1. **Coordenadas.** Las tablas dan posiciones **absolutas en pantalla**. En EEZ un hijo va relativo a su
   contenedor: resta la x/y del padre (el padre es la fila anterior con menos puntos `·`).
2. **Fuentes.** Montserrat. `14px 600` → 14; `13px` → 14; `11px`/`12px` → 12; `10px` → 12 (o 10 si se
   convierte); `20px 700` → 20.
3. **«grupo» 44×44 con un «icono» dentro = botón de icono**: `lv_button` 44×44 **sin estilo del tema**
   (`bg_opa 0`, `shadow_width 0`, `border_width 0`, `pad 0`), con la imagen **centrada**
   (`LV_ALIGN_CENTER`). Estados: PRESSED → `bg_color #1F2228`, `bg_opa 255`, `radius 22`;
   CHECKED → icono en `c_accent`; DISABLED → `opa 40 %`.
4. **Iconos: todos son PNG** de `../iconos/`, blancos con alfa. Se tiñen con `image_recolor` +
   `image_recolor_opa 255` al color de la columna «texto/icono color». **No usar `LV_SYMBOL_*`**: no se
   parecen al diseño (el engranaje de LVGL no es el icono de ajustes, por ejemplo).
5. **«caja» con radio igual a la mitad del alto** = forma redondeada (play, pulgar, chips).
6. **`degradado (imagen)`** = miniatura (144×80) o fondo de video del maquetado; en la placa es la imagen
   real. Sin miniatura: caja #15171C con el icono `film` en #8E929B centrado.
7. **Opacidad** `85%` → `opa 217`; `45%` → `opa 115`; `40%` → `opa 102`. `#RRGGBB @NN%` → color + `bg_opa`.

## Mapa de controles e iconos

| Tablero · fila | Nombre EEZ | Icono PNG (tamaño) · color | Acción |
|---|---|---|---|
| Main #4 | `btn_back` | `back` (20) · #EDEDEA | pausar y ir a `scr_library` |
| Main #6 / #7 | `lbl_title` / `lbl_subtitle` | — | título (marquesina en F6b) y «NN / MM · artista» |
| Main #8 | `chip_fps` | — | `pres_fps`; oculto si `stats=0` |
| Main #9 | `btn_queue` | `queue` (22) · #EDEDEA | F6a: aviso «Próximamente» · F6b: `scr_queue` |
| Main #12 / #16 | `lbl_pos` / `lbl_dur` | — | posición y duración |
| Main #13–#15 | `sld_seek` | pista #2A2D34, relleno y pulgar #F2B33D | saltar |
| Main #17 | `btn_lock` | `lock` (20) · #EDEDEA | `ovl_lock`; se desbloquea manteniendo 1 s |
| Main #19 | `btn_repeat` | `repeat` / `repeat_one` (20) · #8E929B off, #F2B33D todo/uno | off → todo → uno |
| Main #21 | `btn_prev` | `prev` (22) · #EDEDEA | video anterior |
| Main #23 | `btn_rew` | `rew10` (24) · #EDEDEA | −`seekstep` s |
| Main #25 / #26 | `btn_play` | círculo #F2B33D 44×44 · `pause` / `play` (20) en #1A1204 | reproducir/pausar |
| Main #27 | `btn_fwd` | `fwd10` (24) · #EDEDEA | +`seekstep` s |
| Main #29 | `btn_next` | `next` (22) · #EDEDEA; desactivado si es el último y repetir está en off | video siguiente |
| Main #31 | `btn_shuffle` | `shuffle` (20) · #8E929B off, #F2B33D on | aleatorio |
| Main #33 | `btn_settings` | `settings` (20) · #EDEDEA | F6a: aviso «Próximamente» · F6b: `scr_settings` |
| Main #3 / #11 | `osd_top` / `osd_bottom` | fondo #0B0C0F, borde 1 px #2A2D34 | se ocultan juntos |
| — | ~~botón de pantalla completa~~ | **no existe** | la vista sin controles se obtiene tocando el video |
| Gestos | `ovl_brightness` | `brightness` (20) | arrastre vertical en la mitad izquierda |
| Gestos | `ovl_seek_hint` | `seek_fwd` / `seek_back` (24) | doble toque en un tercio lateral |
| Bloqueo | `ovl_lock` | `lock_big` (26) | — |
| Biblioteca #2 / #3 | `lbl_lib_title` / `lbl_lib_count` | — | «N videos · M no compatibles · X GB libres» (sin «M …» si M = 0) |
| Biblioteca #4 | `btn_lib_settings` | `settings` (20) | F6a: aviso · F6b: ajustes |
| Biblioteca #6 | `lib_grid` | 3 columnas de 144 px, huecos de 12 px, filas cada 126 px | **única zona con desplazamiento** (barra 3 px #2A2D34 a la derecha) |
| Biblioteca (tarjeta) | `card_video` → `img_thumb` 144×80 radio 6, `lbl_card_title` 14, `lbl_card_meta` 12 | — | tocar = reproducir |
| Biblioteca #7 | chip «Reproduciendo» | fondo #15171C, texto #F2B33D | solo en la tarjeta actual |
| BibliotecaLlena | chip «Sin girar» | fondo #15171C, texto #8E929B; meta «Sin girar: puede verse corte» | fichero 480×320: se reproduce |
| BibliotecaLlena | tarjeta no compatible | toda la tarjeta a opa 115; título #8E929B; meta = motivo en #E5484D; miniatura de relleno | no reproduce: muestra el aviso |
| Escaneo / SinMedios | `img_nomedia` | `film` (34) · `sdcard_big` (48) | — |
| ErrorSD | icono | `sdcard_error_big` (48) · #E5484D | — |
| SinMediosIncompatibles | icono | `sdcard_big` (48) · #E5484D | `btn_retry` = reescanear · `btn_settings` = ajustes |
| AjustesAlmacenamiento | `card_sd` / `btn_rescan` | `sdcard` (32) / `rescan` (16) | reescanear |
| Ajustes | desplegables | `chevron_down` (14) · #8E929B | — |
| Cola | `btn_queue_close` | `close` (18) | cerrar la cola |

### Aviso emergente (`toast`, nuevo)
Contenedor de **300 px de ancho** (302 en la biblioteca), alto automático, `bg #15171C`, borde 1 px
#2A2D34, radio 8, relleno 10/12, icono `warning` (20) + título 14/600 #EDEDEA + texto 12 #8E929B.
Icono en **#E5484D** para errores y en **#F2B33D** para información («Próximamente»). Se muestra **3 s**,
de uno en uno, centrado en horizontal, **encima de `osd_bottom`** en el reproductor (y 150) y bajo la
tarjeta tocada en la biblioteca. Textos exactos:
| Caso | Título | Texto |
|---|---|---|
| Opción de F6b tocada en F6a | Próximamente | Esta opción llega en la próxima versión. |
| Tarjeta no compatible | No se puede reproducir | `<motivo>`. Se admiten 320×480 y 480×320. / Conviértelo con convert_videos.py |
| Vigilante de D5 | No se pudo reproducir | El video no muestra imagen. Volviendo a la biblioteca… |

## Cómo se acepta
Por cada pantalla construida: la captura del simulador de EEZ (o una foto de la placa) **al lado** de
`png/<Tablero>.png`, en el informe de la fase. Diferencias admitidas: el contenido (miniaturas, títulos
reales) y el suavizado de las fuentes. **No admitidas:** posiciones, tamaños, colores, fondos de botón
que el diseño no tiene, iconos descentrados o sustituidos por símbolos de LVGL.
