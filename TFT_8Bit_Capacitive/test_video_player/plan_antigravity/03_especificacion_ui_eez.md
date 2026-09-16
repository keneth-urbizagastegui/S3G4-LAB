# 03 — Especificación de la UI para EEZ Studio (LVGL 9.5, 480×320 horizontal)

> Diseño visual de referencia: el canvas publicado (enlace en `00_LEEME.md`). **Si este documento y el
> canvas no coinciden, manda este documento** (tiene coordenadas exactas) y hay que anotar la
> diferencia.
> Proyecto EEZ: `test_video_player/video_player/video_player.eez-project` (hoy en blanco).

---

## 1. Ajustes del proyecto EEZ (*Settings → General / Build*)

| Campo | Valor | Motivo |
|---|---|---|
| Project type | LVGL | ya lo está |
| LVGL version | 9.5.0 | ya lo está |
| **Display width / height** | **480 / 320** | hoy está a 800×480 (M8) |
| Flow support | **desactivado** | acciones y variables nativas en C (`02` F6) |
| Color format | Por defecto de LVGL con 16 bits. Probar primero **RGB**; si en el panel los azules salen rojos, cambiar a BGR **y anotarlo** | hoy dice BGR sin justificar; el driver ya aplica `MADCTL 0x28` (BGR) y el swap por hardware |
| Build → destination folder | `../main/ui` | integración de `02` F6 |
| Fuentes | Montserrat 12, 14 y 20 **integradas en LVGL** (no importar TTF) | cero Flash extra |

## 2. Sistema visual (tokens)

Dirección: **«cine oscuro»**. Negro con un toque frío, un solo acento ámbar y barras opacas, para que
el video pueda pintarse por blit directo sin mezclar alfa (`02` F3).

| Token (estilo EEZ) | Hex | Uso |
|---|---|---|
| `c_bg` | `#0B0C0F` | fondo de pantallas y barras de la OSD |
| `c_surface` | `#15171C` | tarjetas, paneles, lista |
| `c_surface_hi` | `#1F2228` | botones secundarios pulsados, pistas de slider |
| `c_line` | `#2A2D34` | separadores de 1 px |
| `c_text` | `#EDEDEA` | texto principal, iconos |
| `c_muted` | `#8E929B` | texto secundario, tiempos |
| `c_accent` | `#F2B33D` | reproducir, progreso, selección, foco |
| `c_on_accent` | `#1A1204` | icono sobre el ámbar |
| `c_danger` | `#E5484D` | errores |

Tipografía: `montserrat_20` para títulos de pantalla, `montserrat_14` para títulos de elemento y
etiquetas, y `montserrat_12` para metadatos, tiempos y estadísticas.
Radios: 6 en tarjetas y miniaturas, 8 en paneles, `LV_RADIUS_CIRCLE` en botones circulares.
**Zona táctil mínima: 44×44 px.** Iconos de 20–24 px. Usar símbolos `LV_SYMBOL_*` cuando existan;
para ⟲10 / ⟳10, bloqueo y cola, imágenes PNG de 24×24 blancas con alfa (se tiñen con
`image_recolor` a `c_text`).

### Estilos EEZ que hay que crear (*Styles*)
`st_screen` (bg `c_bg`, pad 0, sin borde) · `st_bar` (bg `c_bg`, borde inferior o superior 1 px
`c_line`) · `st_icon_btn` (bg transparente; pulsado: `c_surface_hi`; radio circular) ·
`st_play_btn` (bg `c_accent`; pulsado: opacidad 80 %; radio circular) · `st_card` (bg `c_surface`,
radio 8) · `st_seek` (MAIN `c_line` h 4 · INDICATOR `c_accent` · KNOB `c_accent` pad 4; pulsado:
KNOB pad 7) · `st_chip` (bg `c_surface`, radio 10, texto `c_accent` 12) · `st_list_item`
(bg transparente, pulsado `c_surface_hi`, borde inferior 1 px `c_line`).

## 3. Pantallas y árbol de widgets

Coordenadas absolutas `x, y, w, h` en px. Los nombres de objeto son **exactos**: `actions.c`/`vars.c`
dependen de ellos.

### 3.1 `scr_player` — Reproductor con la OSD visible *(artboard «Reproductor»)*
Región de video del blit con la OSD visible: **`x0 y40 w480 h196`** (filas 40–235).
Sin OSD: `0,0,480,320`.

| Objeto | Tipo | x,y,w,h | Estilo / contenido | Evento → acción |
|---|---|---|---|---|
| `player_touch` | obj transparente | 0,40,480,196 | sin fondo; CLICKABLE | `CLICKED` → `action_toggle_osd`; gestos (§4) |
| `osd_top` | container | 0,0,480,40 | `st_bar` borde inferior | — |
| `btn_back` | button | 0,0,44,40 | `st_icon_btn`, `LV_SYMBOL_LEFT` | `action_open_library` |
| `lbl_title` | label | 48,5,300,18 | 14 `c_text`, `LONG_DOT` | var `title` |
| `lbl_subtitle` | label | 48,22,300,14 | 12 `c_muted` | var `subtitle` («02 / 04 · 30 fps») |
| `chip_fps` | container+label | 370,10,62,20 | `st_chip` | var `fps_text`; oculto si `show_stats=false` |
| `btn_queue` | button | 436,0,44,40 | `st_icon_btn`, icono cola | `action_open_queue` |
| `osd_bottom` | container | 0,236,480,84 | `st_bar` borde superior | — |
| `lbl_pos` | label | 8,244,48,14 | 12 `c_muted`, alineado a la derecha | var `pos_text` («1:24») |
| `sld_seek` | slider | 64,248,352,4 | `st_seek`, rango 0–1000, `ext_click_area` 14 | `PRESSED` → `action_seek_begin` · `VALUE_CHANGED` → `action_seek_preview` · `RELEASED` → `action_seek_commit` |
| `lbl_dur` | label | 424,244,48,14 | 12 `c_muted`, alineado a la izquierda | var `dur_text` |
| `btn_lock` | button | 8,272,44,44 | `st_icon_btn`, icono candado | `action_lock` |
| `btn_repeat` | button | 56,272,44,44 | `st_icon_btn`; `CHECKED` → icono `c_accent` | `action_cycle_repeat`; var `repeat_mode` (0/1/2; en 2 se muestra un «1» de 12 px) |
| `btn_prev` | button | 122,272,44,44 | `LV_SYMBOL_PREV` | `action_prev` |
| `btn_rew` | button | 170,272,44,44 | icono ⟲10 | `action_rew10` |
| `btn_play` | button | 218,272,44,44 | `st_play_btn`; `LV_SYMBOL_PAUSE`/`PLAY` | `action_toggle_play`; var `is_playing` |
| `btn_fwd` | button | 266,272,44,44 | icono ⟳10 | `action_fwd10` |
| `btn_next` | button | 314,272,44,44 | `LV_SYMBOL_NEXT` | `action_next` |
| `btn_shuffle` | button | 380,272,44,44 | `LV_SYMBOL_SHUFFLE`; `CHECKED` en ámbar | `action_toggle_shuffle`; var `shuffle` |
| `btn_settings` | button | 428,272,44,44 | `LV_SYMBOL_SETTINGS` | `action_open_settings` |

Comportamiento: la OSD **se oculta** tras `osd_timeout_ms` (por defecto 3000) sin tocar la pantalla,
**solo si está reproduciendo**. Al ocultarla: `osd_top` y `osd_bottom` pasan a HIDDEN →
`PCMD_SET_VIDEO_RECT {0,0,480,320}`. Al mostrarla, primero `PCMD_SET_VIDEO_RECT {0,40,480,196}` y
**después** se quita HIDDEN. El orden importa: evita que el video pise la barra durante un fotograma.
Mientras se arrastra `sld_seek`, la OSD no se oculta y `lbl_pos` muestra la posición de vista previa.
En pausa, la OSD siempre está visible.

### 3.2 `scr_player` · capa de gestos *(artboard «Gestos»)*
Superposiciones hijas de `scr_player`, ocultas por defecto y declaradas como **rectángulos de
exclusión** del blit (`02` F3 paso 5).

| Objeto | Tipo | x,y,w,h | Contenido |
|---|---|---|---|
| `ovl_brightness` | container | 16,70,40,180 | `st_card` con opacidad 100 %; `bar` vertical `bar_brightness` 12,28,16,124 (ámbar); icono sol arriba; `lbl_bri` 12 abajo («70 %») |
| `ovl_seek_hint` | container | 316,116,100,88 | `st_card` radio 44; icono ⟳ + `lbl_seek_hint` 14 («+10 s»). La versión izquierda va en x 64 |
| `bar_mini_progress` | bar | 0,317,480,3 | se ve con la OSD oculta **si** `show_mini_progress`; indicador `c_accent`, fondo `c_line` |

### 3.3 `scr_library` — Biblioteca *(artboard «Biblioteca»)*
| Objeto | Tipo | x,y,w,h | Contenido / evento |
|---|---|---|---|
| `lib_header` | container | 0,0,480,44 | `st_bar` |
| `lbl_lib_title` | label | 16,12,200,24 | 20 `c_text` «Biblioteca» |
| `lbl_lib_count` | label | 220,16,200,16 | 12 `c_muted`, alineado a la derecha; var `library_summary` («4 videos · microSD 29,7 GB libres») |
| `btn_lib_settings` | button | 428,0,44,44 | `LV_SYMBOL_SETTINGS` → `action_open_settings` |
| `lib_grid` | container scroll V | 0,44,480,276 | flex ROW_WRAP, pad 12, gap 12 |
| `card_video` ×N | **user widget** `uw_video_card` | 144×124 | se crea **por código** en `action_library_populate` (N se cuenta al escanear la SD) |

`uw_video_card` (144×124): `img_thumb` 0,0,144,80 radio 6 · `badge_now` 6,6,auto,18 (`st_chip`,
«Reproduciendo», visible si es el actual) · `bar_resume` 0,78,144,3 (visible si hay posición guardada) ·
`lbl_card_title` 0,88,144,18 (14, `LONG_DOT`) · `lbl_card_meta` 0,106,144,14 (12 `c_muted`, «3:21»).
`CLICKED` → `action_play_index` (índice en `user_data`).

### 3.4 `scr_queue` — Cola *(artboard «Cola»)*
Se abre sobre el último fotograma, con el video en pausa de blit.
| Objeto | Tipo | x,y,w,h | Contenido |
|---|---|---|---|
| `queue_scrim` | obj | 0,0,220,320 | bg negro con opacidad 60 %; `CLICKED` → `action_close_queue` |
| `queue_sheet` | container | 220,0,260,320 | bg `c_surface`, borde izquierdo 1 px `c_line` |
| `lbl_queue_title` | label | 236,12,120,20 | 14 «A continuación» |
| `btn_queue_close` | button | 436,0,44,44 | `LV_SYMBOL_CLOSE` |
| `queue_list` | container scroll V | 220,44,260,232 | flex COLUMN |
| `row_queue` ×N | user widget `uw_queue_row` | 260×56 | `img` 12,10,64,36 · `lbl` 86,10,140,18 (14) · `lbl_meta` 86,30,140,14 (12) · `icon_now` 234,20 (ámbar si es la actual) → `action_play_index` |
| `queue_footer` | container | 220,276,260,44 | borde superior `c_line`; `btn_q_repeat` 232,276,44,44 · `btn_q_shuffle` 280,276,44,44 · `lbl_q_mode` 332,290,140,16 (12 `c_muted`, «Repetir todo») |

### 3.5 `scr_settings` — Ajustes *(artboard «Ajustes»)*
Navegación izquierda (0,0,150,320, bg `c_bg`, borde derecho `c_line`) con `btn_back_settings`
0,0,44,44 y 4 elementos de 150×48 desde y = 52: **Pantalla · Reproducción · Almacenamiento ·
Acerca de**. El seleccionado lleva texto `c_accent` y fondo `c_surface`.
Panel derecho `settings_panel` 150,0,330,320, pad 16, con una página por sección (tabview oculto o
4 contenedores alternados por `action_settings_tab`):
- **Pantalla:** `sld_brightness` (fila 48: etiqueta «Brillo» + slider 10–100 + valor) · `dd_osd_timeout`
  («2 s / 3 s / 5 s / Nunca») · `sw_show_stats` («Mostrar FPS en la OSD») · `sw_mini_progress`.
- **Reproducción:** `dd_repeat` («Desactivado / Repetir todo / Repetir uno») · `sw_shuffle` ·
  `sw_resume` («Continuar donde lo dejé») · `dd_seek_step` («5 s / 10 s / 30 s»).
- **Almacenamiento:** `lbl_sd_info` (tipo, capacidad y libre) · `lbl_sd_speed` («SPI 20 MHz») ·
  `btn_rescan` («Volver a escanear») → `action_rescan`.
- **Acerca de:** firmware, IDF, LVGL, panel y botón `btn_open_stats` → `action_open_stats`.
Cada control escribe con su acción `action_set_*` y se persiste en NVS (`02` F5.3).

### 3.6 `ovl_stats` — Estadísticas *(artboard «Estadísticas»)*
Panel hijo de `scr_player`, 12,52,212,172, `st_card` con opacidad 100 % (rectángulo de exclusión).
Título «Rendimiento» (14) + botón cerrar 44×44 en la esquina, y 7 filas de 12 px en dos columnas
(etiqueta `c_muted` a la izquierda, valor `c_text` a la derecha): **Presentados** (`pres_fps`) ·
**Decodificados** (`dec_fps`) · **Descartados** (`dropped`) · **Lectura SD** (`rd_avg / rd_max ms`) ·
**Decodificación** (`dec_avg / dec_max ms`) · **Envío al panel** (`blit_avg ms`) · **Archivo**
(«480×320 · MJPEG · 11,2 KB/f»).
Todos los valores salen de `perf` (`02` F0). **Ninguno escrito a mano.**

### 3.7 `ovl_lock` — Bloqueo *(artboard «Bloqueo»)*
Capa 0,0,480,320 transparente que se traga todos los toques. Visible: círculo 64×64 en 208,112
(bg `c_surface`, icono candado) + `arc_unlock` 200,104,80,80 (ámbar, progreso 0–100 con pulsación
larga de 1000 ms) + `lbl_lock` 140,196,200,18 centrado, 14 «Pantalla bloqueada» + `lbl_lock_hint`
12 `c_muted` «Mantén pulsado para desbloquear». Los elementos se ocultan a los 2 s y reaparecen al
tocar. Rectángulo de exclusión del blit: 140,104,200,116 **solo mientras están visibles**.

### 3.8 `scr_no_media` — Sin microSD o sin videos *(artboard «Sin medios»)*
Centrado: icono SD 48×48 (`c_muted`) · título 20 «No hay videos» · texto 12 `c_muted`
«Copia archivos .avi en /videos de la microSD» · `btn_retry` 180,220,120,44 (`st_card`, texto
`c_accent` «Reintentar») → `action_rescan`. Variante de error con título «No se pudo leer la
microSD» y `err_code` en 12.

## 4. Gestos sobre `player_touch` (`main/ui_glue/gestures.c`)

| Gesto | Zona | Efecto |
|---|---|---|
| Toque | cualquiera | mostrar u ocultar la OSD |
| Doble toque (< 300 ms) | tercio izquierdo / derecho | −/+ `seek_step` (10 s por defecto), muestra `ovl_seek_hint` 600 ms; se acumula (+20, +30…) |
| Doble toque | tercio central | reproducir o pausar |
| Arrastre vertical | mitad izquierda | brillo (`ovl_brightness`), 1 % cada 2 px |
| Arrastre horizontal | toda la zona, con OSD visible | *scrub* con vista previa en `lbl_pos`; al soltar → `SEEK_MS` |
| Pulsación larga (1 s) | sobre `ovl_lock` | desbloquear |

(Mitad derecha vertical: reservada para el volumen cuando haya audio. **No implementar ahora.**)

## 5. Contrato de acciones y variables nativas

**Acciones** (`actions.h` generado por EEZ; se implementan en `ui_glue/actions.c`):
`action_toggle_play, action_prev, action_next, action_rew10, action_fwd10, action_seek_begin,
action_seek_preview, action_seek_commit, action_cycle_repeat, action_toggle_shuffle, action_lock,
action_toggle_osd, action_open_library, action_open_queue, action_close_queue, action_open_settings,
action_settings_tab, action_open_stats, action_play_index, action_rescan, action_library_populate,
action_set_brightness, action_set_osd_timeout, action_set_show_stats, action_set_mini_progress,
action_set_repeat, action_set_shuffle, action_set_resume, action_set_seek_step`

**Variables nativas** (getters en `ui_glue/vars.c`, leídas de una caché de `player_status_t` +
`perf` refrescada 1 vez por `ui_tick`):
`title (string), subtitle (string), pos_text (string), dur_text (string), seek_value (int 0-1000),
is_playing (bool), repeat_mode (int), shuffle (bool), fps_text (string), show_stats (bool),
library_summary (string), brightness (int), stats_pres_fps (string), stats_dec_fps (string),
stats_dropped (string), stats_read (string), stats_decode (string), stats_blit (string),
stats_file (string)`

Regla: una variable de texto **no crea un `snprintf` en cada llamada al getter**. Se formatea al
refrescar la caché y el getter devuelve el puntero.

## 6. Qué entrega Antigravity en EEZ

1. El proyecto `video_player.eez-project` con los ajustes de §1, los estilos de §2, las 3 pantallas
   (`scr_player`, `scr_library`, `scr_settings`), `scr_no_media`, las superposiciones de §3.2, 3.4,
   3.6 y 3.7 como hijas de `scr_player`, y los *user widgets* `uw_video_card` y `uw_queue_row`.
2. Las imágenes de iconos (⟲10, ⟳10, candado, cola, tarjeta SD) en PNG de 24×24 y 48×48, blancas con
   alfa.
3. Una captura del simulador de EEZ de cada pantalla, guardada en
   `plan_antigravity/mediciones/eez_*.png`, para compararla con el canvas.
4. Una lista de **cualquier diferencia** con este documento o con el canvas, sin «arreglarla» por su
   cuenta.

---

## 7. Hojas de sistema del canvas (añadidas el 15/09/2026)

El canvas incluye ahora, además de las pantallas, dos tableros que no son pantallas del dispositivo:

- **«Estados de componentes»**: cada control con sus estados reales — botón de icono (normal, pulsado,
  activo, desactivado), botón principal (reproducir/pausa/pulsado), chips, barra de progreso (normal y
  arrastrando, con el knob de 12 → 18 px), interruptor, filas de lista y tarjeta de video (normal y
  actual). **Cada estado de esta hoja es un estilo de EEZ** con su parte (MAIN / INDICATOR / KNOB) y su
  estado (DEFAULT / PRESSED / CHECKED / DISABLED). Constrúyelos una vez y reutilízalos.
- **«Tokens»**: los 8 colores con su hex, la escala tipográfica (20/14/12 de Montserrat, las tres
  integradas en LVGL), los radios, la zona táctil mínima de 44 × 44 y el recordatorio de que las barras
  son opacas porque el video se pinta directo entre ellas.

También se añadieron dos pantallas: **«Reproductor · sin controles»** (video a pantalla completa con la
barra mínima de progreso de 3 px abajo) y **«Ajustes · Reproducción»** (repetir, aleatorio, continuar
donde lo dejé y salto de ±10 s).

---

## 8. Regla de desplazamiento (scroll): SOLO DOS SITIOS

En LVGL 9 **todo objeto nace con `LV_OBJ_FLAG_SCROLLABLE` activo**, con rebote elástico e inercia. Eso
provoca que paneles y barras «se muevan» al arrastrar, que es el defecto que Keneth señala de la UI
actual (15/09/2026). Regla del proyecto:

**Solo pueden desplazarse dos objetos, y solo en vertical:**
| Objeto | Cuándo aparece el desplazamiento |
|---|---|
| `lib_grid` (Biblioteca) | con **más de 6 videos** (2 filas de 3 caben enteras: 44 + 2×124 + 12 = 304 ≤ 320) |
| `queue_list` (Cola) | con **más de 4 videos** (4 filas de 56 = 224 ≤ 232 de alto útil) |

En esos dos: `LV_SCROLL_SNAP_NONE`, dirección `LV_DIR_VER`, `scrollbar_mode = LV_SCROLLBAR_MODE_AUTO`
(barra de 4 px, `c_line`, sin fondo), y **sin rebote elástico**: `lv_obj_set_scroll_dir(obj, LV_DIR_VER)`
más `lv_obj_clear_flag(obj, LV_OBJ_FLAG_SCROLL_ELASTIC | LV_OBJ_FLAG_SCROLL_MOMENTUM)` si el gesto de
inercia estorba al arrastre horizontal de la barra de progreso.

**En TODO lo demás** — `scr_player`, `osd_top`, `osd_bottom`, `player_touch`, las superposiciones de
gestos, `ovl_stats`, `ovl_lock`, `queue_sheet`, `settings_panel`, la navegación de ajustes,
`scr_no_media` y cada `uw_video_card` / `uw_queue_row` — hay que quitarlo explícitamente:
```c
lv_obj_remove_flag(obj, LV_OBJ_FLAG_SCROLLABLE);
lv_obj_set_scrollbar_mode(obj, LV_SCROLLBAR_MODE_OFF);
```
En EEZ: desmarcar **SCROLLABLE** en las propiedades del widget y poner *Scrollbar mode* en **OFF**.
Ninguna pantalla del diseño necesita desplazarse: todas caben en 480×320 por construcción, y las
pestañas de ajustes tienen 4 filas de 56 px (224 px) dentro de 320.

**Comprobación de F6:** arrastrar el dedo en cualquier zona que no sea la biblioteca, la cola o la barra
de progreso **no debe mover nada**. Se añade a la verificación visual de Keneth.

## 9. Lo que todavía NO está diseñado (pendiente antes de F6)

1. **Iconos PNG 24×24** (⟲10, ⟳10, candado, cola, tarjeta SD) y el de 48×48 de «sin medios». Hoy en el
   canvas son SVG de referencia; EEZ necesita PNG blancos con alfa para teñirlos.
2. **Pestañas «Almacenamiento» y «Acerca de»** de ajustes: definidas por texto en §3.5, sin tablero.
3. **Estado de escaneo** al arrancar o tras pulsar «Volver a escanear» (mientras se leen las miniaturas).
4. **Variante de error** de `scr_no_media` («No se pudo leer la microSD» + código), descrita en §3.8.
5. **Miniatura de marcador de posición** para los videos sin `.jpg`.
6. **Comportamiento del título largo**: marquesina o corte con puntos suspensivos (hoy `LONG_DOT`).
7. El propio **proyecto EEZ**, que es trabajo de F6.

---

## 10. Pantallas añadidas el 15/09/2026 (resuelven los puntos 2, 3, 4 y 5 del §9)

Mismas reglas de §2 y §8: nada desplazable salvo `lib_grid` y `queue_list`.

### 10.1 `scr_settings` · pestaña **Almacenamiento** *(artboard «Ajustes · Almacenamiento»)*
Panel derecho `settings_panel` (150,0,330,320, pad 16):
| Objeto | Tipo | x,y,w,h (relativo al panel) | Contenido |
|---|---|---|---|
| `card_sd` | container | 0,0,298,88 | `st_card`; icono SD 32×32 en 12,28 (`c_muted`) |
| `lbl_sd_name` | label | 56,12,150,16 | 14; var `sd_name` («microSD SDHC 32 GB») |
| `lbl_sd_fs` | label | 206,12,80,16 | 12 `c_muted`, derecha; var `sd_fs` («FAT32») |
| `bar_sd_usage` | bar | 56,36,230,6 | radio 3; MAIN `c_line`, INDICATOR `c_accent`; rango 0–1000; var `sd_used_permil` |
| `lbl_sd_free` | label | 56,50,230,14 | 12 `c_muted`; var `sd_free_text` («6,4 GB usados · 23,3 GB libres») |
| `row_bus` | container | 0,96,298,48 | borde inferior 1 px `c_line`; etiqueta «Velocidad del bus» (13) + `lbl_sd_speed` a la derecha (13 `c_muted`, «SPI · 20 MHz», var `sd_speed_text`) |
| `row_count` | container | 0,144,298,48 | igual; «Videos encontrados» + `lbl_sd_count` (var `library_count_text`) |
| `btn_rescan` | button | 0,208,140,44 | `st_card`, texto `c_accent` 13 + icono ⟳ 16 px; → `action_rescan` |

**Los valores salen de `sdmmc_card_t` y de `f_getfree`, contados en el momento**: nada fijo en el código.
Si `f_getfree` falla, `sd_free_text` = «Espacio no disponible» y la barra a 0.

### 10.2 `scr_settings` · pestaña **Acerca de** *(artboard «Ajustes · Acerca de»)*
| Objeto | x,y,w,h | Contenido |
|---|---|---|
| `lbl_about_name` | 0,0,298,26 | 20 «S3G4 Video» |
| `lbl_about_sub` | 0,26,298,14 | 12 `c_muted` «Reproductor de video embebido» |
| filas 40 px con borde inferior `c_line`, etiqueta 12 `c_muted` a la izquierda y valor 12 a la derecha | 0,54 en adelante | **Firmware** (`APP_VERSION` de CMake, no escrito a mano) · **ESP-IDF** (`IDF_VER`) · **LVGL** (`LVGL_VERSION_*`) · **Panel** («ILI9488 · 8080 8 bits · 16 MHz», derivado de la config) · **Sincronía** («TE en GPIO 7 · <te_hz medido> Hz» o «TE ausente») |
| `btn_open_stats` | 0,258,140,44 | `st_card`, texto `c_accent` «Ver rendimiento» → `action_open_stats` |

### 10.3 `scr_library` · estado **escaneando** *(artboard «Biblioteca · escaneando»)*
No es una pantalla nueva: es `scr_library` durante el escaneo.
- `lbl_lib_count` (44 alto de cabecera) pasa a `c_accent`: «Escaneando microSD… `<n>` de `<total>`», ambos contados.
- `bar_scan` 0,44,480,3: MAIN `c_line`, INDICATOR `c_accent`, rango 0–1000. Visible solo mientras se escanea.
- `btn_lib_settings` se deshabilita (opacidad 40 %) mientras dura.
- Las tarjetas aparecen **según se leen**, en orden. La que se está leyendo muestra un `lv_spinner` de
  22 px (arco `c_accent` sobre `c_line`) centrado en la miniatura, título «Leyendo…» en `c_muted` y como
  metadato el nombre del fichero.
- Al terminar: se oculta `bar_scan` y `lbl_lib_count` vuelve a `c_muted` con el resumen.

### 10.4 `scr_no_media` · variante **error** *(artboard «Error de microSD»)*
Misma pantalla que «Sin videos», con otro contenido (una sola pantalla, dos estados):
| Objeto | Estado «sin videos» | Estado «error» |
|---|---|---|
| `img_nomedia` 48×48 | icono SD, `c_muted` | icono SD con «!», **`c_danger`** |
| `lbl_nomedia_title` 20 | «No hay videos» | «No se pudo leer la microSD» |
| `lbl_nomedia_sub` 12 `c_muted` | «Copia archivos .avi en /videos de la microSD» | «Sácala, límpiala y vuelve a insertarla» |
| `chip_err` (`st_chip`, 11, `c_muted`) | oculto | «Error 0x<err_code> · <texto>» con el código **real** de `player_status_t.err_code` |
| `btn_retry` 120×44 | «Reintentar» | «Reintentar» |
| `btn_settings_alt` 120×44 (borde 1 px `c_line`, texto `c_muted`) | oculto | «Ver ajustes» → `action_open_settings` |
| `lbl_retry_hint` 11 `c_muted` abajo (y 288) | oculto | «Reintentando cada segundo…» mientras `state == PST_NO_MEDIA` |

### 10.5 Miniatura de relleno (punto 5)
Cuando un `.avi` no trae `.jpg`: `img_thumb` se sustituye por un contenedor 144×80, radio 6, fondo
`c_surface`, con un icono de claqueta/película de 34 px centrado en `#4A4E57`, y `lbl_card_meta` empieza
por «Sin miniatura · ». **No se genera la miniatura decodificando el video en el arranque**: alargaría el
escaneo. El conversor (`02` F5) es quien debe crear los `.jpg`.

## 11. Títulos largos: marquesina (punto 6, decidido por Keneth)

- **Marquesina** (`LV_LABEL_LONG_SCROLL_CIRCULAR`) **solo en dos sitios**, donde el título es el
  protagonista y hay uno solo en pantalla:
  - `lbl_title` del reproductor (OSD superior).
  - `lbl` de la fila **actual** de la cola (`uw_queue_row` con `is_current`).
- Velocidad: `lv_obj_set_style_anim_duration` calculada para ~**40 px/s**; pausa de 1 s al inicio y al
  final del ciclo (comportamiento por defecto de LVGL con `anim_speed`).
- **En todo lo demás sigue el corte con puntos suspensivos** (`LV_LABEL_LONG_DOT`): tarjetas de la
  biblioteca, filas no actuales de la cola, subtítulos y ajustes. Motivo: varias marquesinas a la vez
  obligan a LVGL a repintar sin parar sobre la zona del video y se comen el presupuesto de los 33 ms.
- La marquesina **se detiene** cuando su pantalla no está visible (LVGL ya lo hace al ocultar el objeto:
  no crear timers propios).
- Comprobación en F6: con la OSD visible y un título largo, `pres_fps` debe seguir ≥ 28,0.

## 12. Estado del diseño

Resueltos los puntos 2, 3, 4, 5 y 6 del §9. **Queda solo el punto 1**: los iconos PNG de 24×24 (⟲10,
⟳10, candado, cola, tarjeta SD) y el de 48×48 de «sin medios» / «error», que genera Antigravity en F6 a
partir de los dibujos del canvas: blancos, con alfa, y teñidos con `image_recolor`.
