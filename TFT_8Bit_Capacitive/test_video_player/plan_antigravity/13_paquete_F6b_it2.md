# 13 — F6b iteración 2: capas sin detener el video, lógica de uso y textos (17/09/2026)

> Rama `video-player/fase-6b` (desde `92c53d7`). Viene de la prueba de Keneth con el dedo sobre la it1
> y de la revisión del auditor. **Lo aprobado en vp-v0.7 y lo que Keneth confirmó que funciona no se
> rompe:** fin de video sin repetir retira «Reproduciendo»; brillo por ajuste; gestos detectados; cola
> abre y reproduce al tocar.

## 0. Causa de fondo de «solo se puede hacer una cosa a la vez» (Keneth, punto 10)

El video se pinta **directo al panel** (no pasa por LVGL). Para que una capa de LVGL no quede tapada por
el video, el código actual **apaga el dibujo del video** (`lcd_bus_set_video_rect(0,0,0,0)`) mientras la
capa está visible: `actions.c` líneas ~1083–1143 (pausas), ~1513 (bloqueo), ~2035 y otras. Resultado: la
imagen se congela o se pone negra con cada capa (bloqueo, estadísticas, gestos).

### Solución obligatoria: composición de capas opacas en el camino del video (autorizada por el auditor)
Se autoriza tocar `avi_player.c` / `lcd_bus.c` **solo para esto**, sin cambiar TE, ventana única,
re-anclaje PTS ni la secuencia del panel:
1. `lcd_bus` mantiene una lista de **hasta 4 rectángulos de capa** (`lcd_overlay_rect_t`, en coordenadas
   apaisadas) y un **búfer de capa** 480×320 RGB565 en PSRAM donde el `flush` de LVGL copia los píxeles
   que caen dentro de esos rectángulos (en lugar de descartarlos como hoy).
2. Al montar cada franja del video (tras decodificar y antes de enviar), para las filas nativas que
   cruzan un rectángulo, se **sobrescriben** con `memcpy` los píxeles de la capa en esas columnas. La
   ventana y el envío siguen siendo **uno por fotograma**.
3. Las capas son **opacas** (sin transparencia). El «oscurecido» de fondo del diseño no se hace.
4. Con el video **en pausa**, al cambiar una capa se reenvía el último fotograma compuesto (o solo las
   franjas afectadas) para que la capa aparezca.
5. **Nada** vuelve a poner `video_rect = 0` salvo pantallas completas (biblioteca, ajustes, sin videos).
6. Criterios: con `ovl_stats` visible y con `ovl_lock` visible, **pres ≥ 29 fps y descartes ≤ 1 %**
   (nuevo escenario `scn=overlay` en el autotest); `frame_blit_ms` no sube más de 1 ms; log
   `OVL,rects=<n>,px=<n>` por segundo.
Si tras medir no se cumple, **para y reporta** con cifras; no busques atajos.

## 1. Cola (`scr_queue`) — Keneth: «revisa la lógica»
- **Desplazar vs. tocar:** hoy no se puede desplazar; cualquier toque reproduce. `queue_list` debe ser
  desplazable (es una de las dos zonas permitidas) y las filas deben usar `LV_EVENT_SHORT_CLICKED`
  (no `PRESSED`), para que un arrastre desplace y no reproduzca. Filas de 48 px mínimo.
- **El video no se ve:** la mitad izquierda es negra. Con la composición (§0) el video sigue visible
  a la izquierda y la hoja de la cola es una capa opaca a la derecha (medidas del tablero `Cola`).
- **Marquesina parada en pausa:** la marquesina es una animación de LVGL y no puede depender del estado
  del reproductor ni del refresco de 250 ms. Debe moverse siempre que el texto no quepa.
- La fila actual se resalta y se desplaza a la vista al abrir. Cerrar (X o tocar el video) no pausa.

## 2. Ajustes (`scr_settings`)
- **Textos cortados** («Almacenamiento», subtítulos) y **caracteres que no se ven** (el de «salto de
  botones» y otros): ver §6 (regla de textos) y §7 (fuentes).
- **Textos no centrados** (p. ej. «Ver rendimiento»): los botones centran su etiqueta.
- **«Ver rendimiento»** abre `ovl_stats` sobre el reproductor: hoy aparece sobre el video **pausado**,
  sin datos, y desaparece al pulsar reproducir. Lógica pedida: al pulsar, volver al reproductor
  **reanudando si estaba reproduciendo antes de entrar en ajustes**, y mostrar `ovl_stats` como capa
  (§0) que se cierra con un toque sobre ella; los datos se actualizan aunque el video esté en pausa (con
  0 fps).
- **Brillo:** límite **20–100 %** (por debajo de 20 % no se ve nada). El deslizador, el gesto y NVS usan
  el mismo límite; un valor guardado < 20 se corrige a 20 al arrancar.
- Entrar en ajustes desde el reproductor pausa; **al volver, se reanuda si estaba reproduciendo**.

## 3. Gestos
- **Doble toque:** aparece `ovl_seek_hint` en el lado tocado con «+10 s», **y también un recuadro vacío
  en el otro lado**. Solo debe existir el del lado tocado (una sola capa reutilizada, o la otra oculta).
- **El video se para** al hacer un gesto: se arregla con §0; el salto se aplica sin pausar.
- Las pistas de brillo y salto duran 600 ms y no muestran la OSD.

## 4. Estadísticas (`ovl_stats`)
- Keneth: abrirla con **pulsación larga sobre el chip de fps no funciona**. Debe funcionar (y el chip
  debe estar visible para poder pulsarlo: si `stats=0`, la única vía es Ajustes).
- Capa opaca (§0) con fondo `#15171C` **en todo su recuadro** (hoy el fondo sólido solo está detrás del
  texto), cerrar con un toque sobre ella.

## 5. Bloqueo (`ovl_lock`)
- Funciona, pero **detiene el video y se pone negro** (línea ~1513) y el texto tiene un recuadro sólido
  propio. Con §0: la tarjeta de 200×116 es la capa; el video sigue. Los textos sin fondo propio.

## 6. Regla general de textos (Keneth, punto 10)
- Todo texto visible debe **caber** en su espacio o **desplazarse** (marquesina, `LV_LABEL_LONG_SCROLL_CIRCULAR`)
  si no cabe. Nunca cortado ni con «…» salvo en tarjetas de la biblioteca.
- Centrado donde el diseño lo centra (botones, títulos de hoja, avisos).
- **Prueba automática `TEXTFIT`**: al terminar el autotest, recorrer todos los `lv_label` de las 5 pantallas
  y capas, calcular el ancho del texto con `lv_text_get_size` y comparar con el ancho disponible; imprimir
  `TEXTFIT,offenders=<n>` y cada infractor (`TEXTFIT_BAD,id=…,text_w=…,box_w=…`). Criterio: 0 sin
  marquesina activa.
- La columna de pestañas de Ajustes: «Almacenamiento» debe caber (ajusta relleno o usa 12 px, sin
  cambiar el ancho de 150 px del tablero).

## 7. Proyecto EEZ: 55 errores «Font not found»
El proyecto referencia fuentes `montserrat_12/14/20` (en minúscula) que **no existen en el proyecto**: se
generaron fuera de EEZ. Por eso el simulador muestra «□» en «A continuación», «Reproducción», «mínima».
**Importa en EEZ** (pestaña Fonts) Montserrat 12, 14 y 20 con el rango de caracteres de `11` §L7 y usa
esas fuentes en los estilos. Criterio: **Checks = 0** y el simulador de EEZ muestra las tildes.
El `main/ui` debe salir de EEZ, no de `tools/generate_f6b_eez.py`: si ese script escribe el proyecto,
el código C sigue saliendo del «Build» de EEZ. Deja el script documentado o retíralo.

## 8. Repetir uno — «funciona pero no es óptimo»
Objetivo: bucle **sin costura**: sin negro, sin pausa visible, barra de progreso salta a 0 en el mismo
refresco. Mide y reporta `LOOP,gap_ms=<n>` (del último fotograma presentado al primero del reinicio) en 5
bucles; objetivo ≤ 2 periodos de fotograma (≤ 67 ms). Si hay reapertura del fichero, evítala
(`avi_player_restart` debe reutilizar el índice y el lector).

## 9. Revisión de uso (anticiparse al usuario)
Implementa y prueba estas reglas en toda la interfaz:
1. **Una capa a la vez** sobre el reproductor (cola, estadísticas, bloqueo, pistas de gesto, aviso). Abrir
   una cierra la anterior; el temporizador de ocultar la OSD se congela mientras hay una capa abierta.
2. **Toque fuera de una capa la cierra** (salvo el bloqueo). El mismo toque no hace nada más.
3. **Pantallas completas** (biblioteca, ajustes, sin videos) pausan; **volver** reanuda si se estaba
   reproduciendo antes (la biblioteca solo reanuda al tocar la tarjeta actual, como ya está).
4. **Pulsar un control mantiene la OSD visible** 3 s más (el temporizador se reinicia en cada toque).
5. **Un toque = una acción**: registra cada evento con `UIEV,obj=…,code=…` y comprueba que ningún toque
   dispara dos acciones.
6. Ningún gesto dispara botones ni al revés (zonas y orden de prioridad documentados).
7. Estado coherente tras reinicio: repetir, aleatorio, brillo, salto y ajustes se aplican al arrancar.

## 10. Pruebas y cierre
- UINAV ampliada: gestos (sin capa fantasma del otro lado), cola (arrastre no reproduce; toque sí),
  estadísticas por pulsación larga, bloqueo sin congelar video (`pres_fps` > 25 durante el bloqueo),
  ajustes → «Ver rendimiento» → vuelve reproduciendo, brillo no baja de 20 %, `LOOP,gap_ms`.
- `TEXTFIT,offenders=0`, `SCROLL,offenders=0`, 50 cambios aleatorios, escenario `scn=overlay`.
- `perf_capture --phase F6b --timeout 900` en **ÉXITO**, mismos umbrales. Ficheros en
  `plan_antigravity/mediciones/` (no en la raíz).
- `informes/FASE_6b.md`: tabla de §0–§9 con estado y prueba. Capturas del simulador junto a los PNG.
- Firmware normal flasheado al final.

## Reglas
COM16 (a veces COM17; nunca COM8). Entorno PowerShell:
`$env:IDF_PATH="C:\esp\v6.0.1\esp-idf"; $env:IDF_TOOLS_PATH="C:\Users\Keneth\.espressif"; . $env:IDF_PATH\export.ps1`.
Prohibido: desactivar perros guardianes, relajar umbrales, redefinir métricas, tocar TE/ventana única/
re-anclaje PTS/secuencia del panel (la composición de §0 es la única excepción autorizada), dejar la
autoprueba en el firmware normal, editar `main/ui` a mano, `PASS` sin comprobar. Commit tras cada
sección. **No termines tu turno mientras una medición siga en marcha: espera su resultado** (en las dos
iteraciones anteriores terminaste antes). Agrupa compilar+flashear+medir en un solo comando.
