# Referencia visual del diseño — para construir en EEZ Studio al pie de la letra

Generado por `../exportar_referencia.py` (Chrome sin ventana). **No se edita a mano**: si cambia un
tablero, se vuelve a ejecutar el script.

| Carpeta | Contenido |
|---|---|
| `png/<Tablero>.png` | Captura a **480×320**, píxel a píxel igual que el panel. Es la imagen contra la que se compara. |
| `png/<Tablero>@2x.png` | Igual, a 960×640, para ver detalles finos (iconos, radios). |
| `widgets/<Tablero>.md` | Tabla por elemento: x, y, ancho, alto, fondo, color, borde, radio, opacidad, fuente, alineación y texto. |
| `widgets.json` | Las mismas tablas en JSON. |

`Componentes` y `Tokens` no son pantallas; su contenido ya está en `03_especificacion_ui_eez.md`.

## Reglas de traducción a LVGL/EEZ

1. **Coordenadas.** Las tablas dan posiciones **absolutas en pantalla**. En EEZ, un hijo va relativo a su
   contenedor: resta la x/y del padre (el padre es la fila anterior con menos puntos `·`).
2. **Fuentes.** Montserrat. `14px 600` → `ui_font_montserrat_14` (o la más cercana que exista); `11px`
   → 12. `20px 700` → 20. El peso 600/700 se aproxima con la misma fuente si no hay negrita convertida.
3. **«grupo» 44×44 con un «icono» dentro** = **botón de icono**: `lv_button` 44×44, **sin estilo del tema**
   (`bg_opa 0`, `shadow_width 0`, `border_width 0`, `pad 0`), con el icono **centrado**
   (`LV_ALIGN_CENTER`). Color del icono = columna «texto/icono color».
4. **«caja» con radio igual a la mitad del alto** = forma redondeada (play, pulgar del deslizador, chip).
5. **`degradado (imagen)`** = marcador de miniatura o fondo de video del maquetado. En la placa es la
   miniatura real (144×80) o la imagen de relleno; no hay que reproducir el degradado.
6. **Opacidad** `85%` → `LV_OPA_80`/`bg_opa 217`. Colores `#RRGGBB @NN%` → color y `bg_opa`.
7. **Iconos.** Los que tienen PNG en `../iconos/` se usan como imagen. El resto son símbolos de la fuente
   Montserrat de LVGL (vienen incluidos, no hace falta convertir nada):

| En el tablero | Nombre en EEZ | Icono | Acción |
|---|---|---|---|
| Main #4 (‹ arriba izq.) | `btn_back` | `LV_SYMBOL_LEFT` | ir a `scr_library` |
| Main #6 / #7 | `lbl_title` / `lbl_subtitle` | — | título (marquesina en F6b) y «NN / MM · artista» |
| Main #8 | `chip_fps` | — | texto `pres_fps`; oculto si `stats=0` |
| Main #9 (arriba der.) | `btn_queue` | `iconos/queue.png` | F6a: `scr_library` · F6b: `scr_queue` |
| Main #12 / #16 | `lbl_pos` / `lbl_dur` | — | posición y duración |
| Main #13–#15 | `sld_seek` | pista #2A2D34, relleno y pulgar #F2B33D | saltar |
| Main #17 | `btn_lock` | `iconos/lock.png` | `ovl_lock`; se desbloquea manteniendo 1 s |
| Main #19 | `btn_repeat` | `LV_SYMBOL_LOOP` (acento si está activo) | off → todo → uno |
| Main #21 | `btn_prev` | `LV_SYMBOL_PREV` | video anterior |
| Main #23 | `btn_rew` | `iconos/rew10.png` | −`seekstep` s |
| Main #25 / #26 | `btn_play` | círculo #F2B33D 44×44 · `LV_SYMBOL_PAUSE`/`PLAY` en #1A1204 | reproducir/pausar |
| Main #27 | `btn_fwd` | `iconos/fwd10.png` | +`seekstep` s |
| Main #29 | `btn_next` | `LV_SYMBOL_NEXT` | video siguiente |
| Main #31 | `btn_shuffle` | `LV_SYMBOL_SHUFFLE` (#8E929B apagado, acento encendido) | aleatorio |
| Main #33 | `btn_settings` | `LV_SYMBOL_SETTINGS` | F6a: aviso «Próximamente» · F6b: `scr_settings` |
| Main #3 / #11 | `osd_top` / `osd_bottom` | fondo #0B0C0F, borde 1 px #2A2D34 | se ocultan juntos |
| Biblioteca #2 / #3 | `lbl_lib_title` / `lbl_lib_count` | — | «N videos · microSD X GB libres» |
| Biblioteca #4 | `btn_lib_settings` | `LV_SYMBOL_SETTINGS` | F6a: aviso · F6b: ajustes |
| Biblioteca #6 | `lib_grid` | rejilla de 3 columnas 144 px, hueco 12 px | **única zona con desplazamiento** |
| Biblioteca (tarjeta) | `card_video` → `img_thumb` 144×80, `lbl_card_title`, `lbl_card_meta` | — | tocar = reproducir |
| Biblioteca #7 | chip «Reproduciendo» | fondo #15171C, texto #F2B33D | solo en la tarjeta actual |
| Biblioteca #8 / #9 | barra de progreso de la tarjeta | 144×3 | posición guardada |

Las demás pantallas (Ajustes, Cola, Bloqueo, Estadísticas, SinMedios, Escaneo, ErrorSD) usan los
nombres de `03_especificacion_ui_eez.md`; la tabla de medidas es la de su fichero en `widgets/`.

## Cómo se acepta
Por cada pantalla construida: la captura del simulador de EEZ (o una foto de la placa) **al lado** de
`png/<Tablero>.png`, en el informe de la fase. Diferencias admitidas: el contenido (miniaturas, títulos
reales) y el suavizado de las fuentes. **No admitidas:** posiciones, tamaños, colores, fondos de botón
que el diseño no tiene, iconos descentrados.
