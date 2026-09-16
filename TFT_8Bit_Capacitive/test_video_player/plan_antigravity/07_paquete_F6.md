# 07 — Paquete de trabajo F6: interfaz de EEZ Studio integrada

> Encargo listo para enviar a Antigravity (con `--print-timeout 120m`) cuando F5b esté cerrada.
> Rama: `video-player/fase-6` desde `vp-v0.6`. **Es la fase más larga: puede necesitar 2 encargos**
> (F6a = proyecto EEZ + integración mínima; F6b = acciones, variables y gestos completos).

## Lo que ya está hecho y NO hay que inventar
- **`03_especificacion_ui_eez.md` es el contrato**: cada objeto con nombre exacto, posición, tamaño,
  estilo, variable y acción. §1 ajustes del proyecto · §2 tokens y estilos · §3 pantallas · §4 gestos ·
  §5 acciones y variables · §8 **regla de scroll** · §10 pantallas nuevas · §11 marquesina.
- **Canvas visual** (16 tableros, incluidos «Estados de componentes» y «Tokens»):
  https://claude.ai/artifact/A9vP5kNZF5qfsbwkqVzYRQ · fuentes en `diseno_ui/`.
- **Iconos PNG ya generados** en `diseno_ui/iconos/` (blancos con alfa, para teñir con
  `image_recolor`): `rew10, fwd10, lock, queue, sdcard` a 24×24; `sdcard_big`,
  `sdcard_error_big` a 48×48; `film` a 34×34 (marcador de miniatura). Se regeneran con
  `python diseno_ui/iconos/generar_iconos.py`. **No los rehagas a mano.**
- Todo lo demás (reproducción, biblioteca, NVS) existe ya: F6 **solo cambia la capa de UI**.

## Orden de trabajo
1. **Proyecto EEZ** `video_player/video_player.eez-project`: aplicar §1 (480×320, sin flow, salida a
   `../main/ui`), crear los estilos de §2 y las imágenes de `diseno_ui/iconos/`.
2. **Pantallas** en este orden, comprobando cada una en el simulador de EEZ antes de pasar a la
   siguiente: `scr_player` (con sus capas) → `scr_library` → `scr_settings` (4 pestañas) →
   `scr_queue` → `scr_no_media`.
3. **Integración**: `ui_glue/actions.c`, `vars.c`, `gestures.c` según §5. Una sola copia de
   `player_status_t` por `ui_tick`, punteros a texto ya formateado (nada de `snprintf` por getter).
4. **Retirada** de `spotify_ui.*` a `legacy/` y borrado de sus llamadas.

## Reglas que han fallado antes y aquí importan más
- **Solo `gui_task` llama a `lv_*`.** La UI nueva multiplica las oportunidades de romper esto.
- **`lcd_bus` sigue mandando**: el video se pinta directo (F3/F5a). Las pantallas que no son el
  reproductor ponen `video_rect = {0,0,0,0}` y el blit se pausa. El flush de LVGL sigue recortando la
  región de video.
- **Scroll**: §8. Solo `lib_grid` y `queue_list`; en todo lo demás, desmarcar SCROLLABLE y scrollbar OFF.
  Keneth lo ha pedido expresamente: el rebote de la UI vieja es el defecto que más le molesta.
- **Marquesina** solo en los dos sitios de §11.
- Memoria: `CONFIG_LV_USE_CLIB_MALLOC=y` para que LVGL use PSRAM (`02` F6.5). Vigilar `heap_int`: con
  las franjas DMA ronda los 72 KB libres.

## Criterios de aceptación (perf_capture `--phase F6`)
- **Se mantienen todos los de F5a/F5b con la UI nueva cargada**: pres_fps hidden ≥ 28,5 y osd ≥ 28,0,
  drop hidden ≤ 1 %, TE, drift, STRESS, TAP. Es el criterio que de verdad importa: la UI no puede
  costar fps.
- `UI,screens=<n>,widgets=<n>,fonts=<n>,images=<n>` en el arranque, todo contado del proyecto generado.
- Navegación completa sin cuelgues: 50 cambios de pantalla aleatorios en el autotest
  (`scn=uinav`), `heap_int` estable al final (± 5 KB respecto al inicio).
- **Con un título largo** y la marquesina activa, `pres_fps` osd sigue ≥ 28,0.
- **Prueba de scroll** en el autotest: arrastrar (toque sintético) en `scr_player`, `scr_settings` y
  `ovl_stats` no debe cambiar `lv_obj_get_scroll_y()`; imprimir `SCROLL,offenders=<n>` y exigir 0.

## Verificación visual de Keneth al cerrar F6
1. ¿Se parece a los tableros del canvas? (posiciones, tamaños, colores)
2. ¿Algo se desplaza al arrastrar donde no debería?
3. ¿Los toques caen donde se ve el botón, en las 4 esquinas de la pantalla?
4. ¿Los colores son correctos (piel, cielo azul)? Si no, cambiar el formato de color de §1 y **anotarlo**.
5. ¿El video sigue igual de fluido con la interfaz nueva?

---

## Actualización tras F5d (16/09/2026): el panel ya no va en horizontal

Desde F5d el panel trabaja en su **orientación nativa (320×480, `MADCTL 0x48`)** y los videos vienen
**girados en origen**. Es lo que eliminó el corte diagonal, y **no se cambia**. Consecuencias para F6:

- **LVGL rota por software** (`lv_display_set_rotation(..., LV_DISPLAY_ROTATION_90)`), así que las
  pantallas de EEZ **se siguen diseñando en 480×320 horizontal**, como dicta `03`. No hay que girar nada
  en el proyecto EEZ.
- **Defecto observado por Keneth con la UI vieja:** al tocar en pantalla completa, los controles aparecen
  **dibujándose a franjas**, con un corte visible mientras se completan. Pasa porque LVGL repinta la OSD
  por bloques y, con la rotación, esos bloques caen perpendiculares a la pantalla. En F6 hay que
  evitarlo:
  1. La OSD se muestra **en un solo flush por barra**: búfer de dibujo de LVGL suficiente para una
     barra entera (480×84 px en horizontal), o `LV_DISPLAY_RENDER_MODE_PARTIAL` con un tamaño que la
     cubra.
  2. El flush de LVGL también **espera TE** (con `lcd_bus_wait_te`, igual que el video) antes de
     enviar, para que la barra aparezca de golpe en un refresco.
  3. Criterio visual: al tocar en pantalla completa, los controles aparecen **enteros, sin barrido ni
     corte**. Se añade a la verificación de Keneth.
- La **ventana única por fotograma** y la **recuperación de la microSD** de F5d se mantienen tal cual.
