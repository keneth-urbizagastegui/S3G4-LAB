# 17 — F6b iteración 16: acabado visual y lógica de uso (18/09/2026)

> Rama `video-player/fase-6b`, desde `91859d8` (medición it15 en ÉXITO). Constructor: Codex.
> Origen: prueba de Keneth con la placa y fotos, más la auditoría del código por el auditor.
> **Ninguna corrección puede romper lo ya verde en it15**: `TEXTFIT=0`, `SCROLL=0`, `GLYPHS=0`,
> 0 reinicios, capas a 30,06 fps con 0 % de descartes, `LOOP` 36 ms, `heap_int` ≥ 100 KB.

## D1 — Esquinas blancas en TODAS las capas (crítico visual)
Foto del gesto de retroceso: alrededor del círculo redondeado se ven las **esquinas del rectángulo en
blanco** en vez de dejar ver el vídeo. Pasa en la pista de gesto, en estadísticas y en las demás capas.
Causa probable: el área del rectángulo de capa que **no** pinta la tarjeta redondeada queda con el
fondo por defecto de LVGL (blanco) en vez del color clave `LCD_OVERLAY_COLOR_KEY` (0x07E0), así que la
composición la considera opaca. Revisa `fill_overlay_rect_with_color_key()` y el contenedor de cada
capa: fuera de la tarjeta, cada píxel debe quedar **exactamente** en el color clave, incluidas las
esquinas redondeadas y cualquier suavizado del borde. Si el antialias del radio genera píxeles
intermedios que no son ni clave ni tarjeta, desactiva el suavizado en esas capas o pinta la esquina con
el color clave. Criterio: ninguna esquina clara en ninguna capa; el vídeo se ve hasta el borde curvo.

## D2 — El cuadro del bloqueo sale cortado — CAUSA YA LOCALIZADA
La tarjeta se agrandó a `(140, 96, 200, 132)` (`actions.c:483-486`), pero el rectángulo de composición
sigue con la geometría antigua: `lcd_bus_set_overlay_rect(0, 140, 104, 200, 116, true)` en
**`actions.c:439` y `actions.c:1767`**. Los 8 px de arriba y los de abajo quedan fuera del rectángulo y
no se componen: de ahí el recorte. Haz que el rectángulo se derive del tamaño real de la tarjeta (leer
posición y tamaño del objeto) en vez de repetir las cifras a mano, y **revisa igual los otros cuatro**
(`actions.c:228`, `:609`, `:1302`, `:2347`) por si alguno arrastra el mismo desfase — en especial la
tarjeta de «Sin girar…», que también agrandaste a 144×140.

## D3 — Chip «Reproduciendo» de la biblioteca: ni cabe ni está centrado
Foto: el texto se sale de su recuadro amarillo y queda pegado al borde. Debe **caber** (ancho ≥ texto +
8 px de relleno) y estar **centrado** vertical y horizontalmente en el chip.

## D4 — Chip de FPS: ni cabe ni está centrado
Mismo defecto con «29.8 fps» / «30.2 fps»: el texto toca los bordes y roza el botón de la cola. Dale
relleno y centrado, y comprueba que no se solapa con el botón contiguo con el valor más largo posible
(«100.0 fps»).

## D5 — «Archivo» en Rendimiento: marquesina permitida
Esa fila muestra el nombre del vídeo y se corta («hate that i made you l…»). Es un título largo:
**añádelo a la lista de marquesinas permitidas** (horizontal), junto al título del reproductor y la fila
actual de la cola, y actualiza la prueba `TEXTFIT` para que no lo cuente como infractor. Sigue sin
permitirse desplazamiento vertical.

## D6 — Al abrir Rendimiento el vídeo se queda en blanco hasta pulsar play
Con el vídeo en pausa, abrir la capa deja el área del vídeo en blanco. Ya existe
`avi_player_reblit_current_frame()` y se llama en otras rutas (`actions.c:570, 1523, 1559, 1572, 2365`);
falta en la de estadísticas. Regla: **toda** apertura, cierre o cambio de capa con el vídeo en pausa
debe reenviar el último fotograma compuesto. Criterio: abrir y cerrar las cinco capas en pausa, 10 veces
cada una, sin que aparezca blanco ni negro.

## D7 — Botón «Volver a escanear»: el icono se monta sobre el texto
Foto de Ajustes → Almacenamiento. Coloca icono y etiqueta sin solaparse (icono a la izquierda con su
separación, texto centrado en el espacio restante) y comprueba que el conjunto cabe en el botón.

## D8 — Los desplegables no parecen desplegables
«Ocultar controles tras», «Repetir» y «Salto de los botones» son cuadros blancos sin ninguna pista de
que se pueden desplegar. Añade el icono de chevron (`ui_image_chevron_down`, ya está en el proyecto) a
la derecha de cada uno, dentro del recuadro, sin que pise el texto.

## Hallazgos del auditor (revisión del código y de la lógica)
- **A1 — Rendimiento en pausa muestra todo a 0.0.** Foto 6: presentados, decodificados, lectura SD y
  decodificación a `0.0` mientras «Envío al panel» sigue marcando `1.4 ms (45 Hz)`. Parece una avería.
  Conserva los **últimos valores válidos** y marca el estado («en pausa»), en vez de ceros.
- **A2 — Geometría duplicada a mano.** El desfase de D2 existe porque las medidas de cada tarjeta están
  escritas dos veces (en el objeto LVGL y en la llamada al rectángulo de composición). Deriva siempre el
  rectángulo del objeto; es la raíz del fallo, no solo un síntoma.
- **A3 — Revisión pedida por Keneth:** repasa el resto de la interfaz con estos mismos criterios (textos
  que caben y centrados, iconos que no pisan, capas con su rectángulo correcto, nada en blanco al
  cambiar de capa) y **reporta lo que encuentres antes de tocarlo** si supone cambiar el diseño.

## Reglas
Un commit por punto. Herramientas: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File
tools/banco.ps1 -Accion ui|build`. **Codex no flashea ni mide.** Prohibido editar `main/ui` a mano,
relajar umbrales, redefinir métricas, tocar TE / la ventana única / el re-anclaje PTS, y dar por bueno
lo no comprobado. Comprueba siempre con `git diff` que `main/ui/screens.c` refleja lo que tocas en el
proyecto EEZ. Si algo no se puede cumplir, para y reporta con cifras.
