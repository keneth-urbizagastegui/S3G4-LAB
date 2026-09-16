# 09 — F6a iteración 2: corrección tras la revisión en placa (16/09/2026)

> Rama `video-player/fase-6`. Lo medido en `F6a_run3` (0,35 % de descartes) **no basta**: Keneth probó
> la placa y la interfaz falla. Esta iteración NO añade nada de F6b: arregla lo que sigue.
> Registro del bloqueo: `mediciones/F6a_bloqueo_trampa.log`.

## Defectos observados por Keneth (con fotos) y verificados por el auditor

### D1 — El proyecto EEZ tiene 79 errores en «Checks» (BLOQUEANTE)
Al abrir `video_player/video_player.eez-project` en EEZ Studio salen 79 errores, todos de estilos:
- `"Use style": "default" not found` en casi todas las etiquetas, contenedores e imágenes.
- `Style "st_bar" / "st_icon_btn" / "st_chip" / "st_screen" is not for this widget type`.

Causa: el JSON se editó a mano con estilos que no declaran el tipo de widget correcto y referencias a
un estilo `default` que no existe. **Criterio: el panel Checks de EEZ Studio debe mostrar 0 errores.**
Cada estilo debe declararse para el tipo de widget donde se usa (o no usar `useStyle` y poner las
propiedades locales). Pide a Keneth que abra el proyecto y confirme el 0 antes de dar la fase por hecha;
el código de `main/ui` debe coincidir con lo que genera Studio al pulsar «Build».

### D2 — No se parece al diseño (BLOQUEANTE)
En la placa los botones son los botones LVGL por defecto: cuadrados azules grandes con el icono
desplazado a la esquina inferior derecha, título casi invisible y el chip de fps ilegible. Hay que
seguir `03_especificacion_ui_eez.md` y los tableros del canvas (`diseno_ui/`):
- Botones de icono **sin fondo** (`bg_opa 0`, sin sombra ni borde), icono **centrado**
  (`lv_obj_center` o `align center`), zona táctil ≥ 44 px.
- Solo el botón play/pausa lleva círculo relleno con el color de acento.
- Barras OSD semitransparentes oscuras con texto claro (`c_text` sobre `c_bar`), no azul claro.
- Quitar el tema por defecto de LVGL en los botones (`lv_obj_remove_style_all` o estilo propio).
Entrega fotos o capturas del simulador de las 3 pantallas junto a los tableros equivalentes.

### D3 — Navegación y botones que no hacen nada (BLOQUEANTE)
| Control | Esperado | Hoy |
|---|---|---|
| ‹ atrás (arriba izq.) | ir a `scr_library` | nada |
| cola (arriba der.) | en F6a: ir a `scr_library` (la cola llega en F6b) | nada |
| candado | bloquea; **mantener pulsado 1 s en cualquier sitio desbloquea** y lo indica | bloquea y no hay forma de salir |
| pantalla completa | alterna vista completa / con barras | nada |
| aleatorio | alterna `shuffle`, cambia el color del icono, se guarda en NVS | nada |
| ajustes | en F6a: aviso «Próximamente» (llega en F6b) | nada |
| tocar el video con la OSD oculta | mostrar la OSD | a veces no, y nunca estando bloqueado |
| tarjeta de la biblioteca | reproducir ese video | no se puede llegar a la biblioteca |
**Criterio:** una prueba por el puerto serie (`uinav`) que pulse cada botón por su id y compruebe el
efecto por log (pantalla activa, estado), más la confirmación de Keneth tocando cada uno.

### D4 — La OSD se sigue dibujando a franjas
Pendiente heredado de F5d (`07` §actualización): al mostrar u ocultar la OSD, dibujarla **en un solo
flush** sincronizado con TE (búfer de LVGL que cubra la barra entera, o invalidar la barra completa y
enviarla en una sola ventana). Criterio: Keneth la ve aparecer de golpe.

### D5 — Bloqueo permanente con un video que no se presenta (CRÍTICO)
Pasó con `trampa_codec.avi` (la versión antigua de la tarjeta: 480×320 con JPEG reales, `compat=1`):
1. Se reprodujo 2 s y terminó; con `repeat=0` el reproductor **se paró y dejó la pantalla gris**, sin
   interfaz para salir.
2. `last_path` quedó apuntando a ese fichero, así que **cada reinicio volvía al mismo punto muerto**.
   Hubo que borrar la NVS con esptool.
3. Además, en ese fichero `pres_fps=0,0` con `dec_fps=29,2`: el camino 480×320 «sin girar» decodifica
   pero no presenta.

Arreglos obligatorios:
- Al terminar un video con `repeat=0`: **volver a `scr_library`** (nunca pantalla vacía).
- Vigilante: si en 3 s de reproducción `pres_fps` es 0 o la apertura falla, parar, marcar el video como
  no reproducible en esta sesión, mostrar aviso y volver a la biblioteca.
- `last_path` y la posición **solo se guardan tras 5 s presentando de verdad**; al arrancar, si el video
  guardado no existe, no es compatible o falló, se ignora y se abre la biblioteca.
- Arreglar la presentación de los 480×320 (aviso «Sin girar» y se ve, aunque con corte).
- Criterio: con `trampa_codec` antigua en la tarjeta y `last_path` apuntándola, la placa arranca en la
  biblioteca. Prueba de 10 reinicios sin quedarse gris.

### D6 — Miniaturas descartadas por 144×80
Las 5 miniaturas se rechazan: el conversor las genera a 144×80 porque 4:2:0 necesita alto par. **El
error es de la especificación (144×81 es impar).** El nuevo tamaño oficial es **144×80**; acepta ese y
corrige `03` y `06` en consecuencia. Criterio: `with_thumb=5` y miniaturas visibles.

### D7 — «Ruido vertical» sobre el video (investigar, no bloquea)
Keneth ve líneas verticales finas que parecen cortes. Puede ser muaré de la cámara o algo real.
Diagnóstico pedido: flashear `vp-v0.6` y la rama actual, poner el mismo video y que Keneth compare a
simple vista (sin cámara). Si solo aparece con F6a, buscar la causa (p. ej. LVGL pintando encima de la
zona del video, o un cambio en la ventana de envío). Informa del resultado; no cambies el driver sin
aprobación.

## Lo que se mantiene
Criterios de rendimiento de F5 (≥ 29 fps presentados con y sin OSD, descartes ≤ 1 %), perros guardianes
activos, secuencia de inicio del panel congelada, `perf_capture --phase F6a` en ÉXITO, sin autoprueba en
el firmware normal. **Prohibido** relajar umbrales o redefinir métricas.

## Entrega
Commits en `video-player/fase-6`, `informes/FASE_6a.md` con una tabla D1–D7 (estado y prueba de cada
uno), el CSV nuevo en `mediciones/`, y el firmware normal flasheado en COM16 para que Keneth lo pruebe.

## Anexo (añadido durante la iteración): referencia visual exacta
`plan_antigravity/diseno_ui/referencia/`: PNG 480×320 de cada tablero, tabla de medidas por elemento y
`LEEME.md` con el nombre EEZ, el icono y la acción de cada control. **Úsalo para D2 y D3**; la
aceptación visual es captura/foto al lado del PNG.
