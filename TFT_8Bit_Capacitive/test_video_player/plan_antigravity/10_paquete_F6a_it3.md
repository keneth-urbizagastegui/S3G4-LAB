# 10 — F6a iteración 3: terminar y revisar lo de la it2 (16/09/2026)

> Rama `video-player/fase-6`. La it2 (09) se cortó por cuota a mitad. Commits que dejó: D6 f244d37, D5
> c30e4f8 y 2a96bca, D1 a924239, D2 0ad892b, D3 5a6d60f, D4 d9386b8, perf_capture fad7d31. Medición
> `mediciones/F6a_run4.*`. **Antes de escribir código nuevo, revisa todo eso contra este documento y
> contra `diseno_ui/referencia/`**: puede estar a medias.
>
> Un cambio sin commit que subía el umbral de descartes al 3 % para las pistas ≥ 5 fue **rechazado y
> revertido** (`mediciones/F6a_it2_umbral_relajado_RECHAZADO.diff`). No lo repitas.

## Lo que Keneth ve ahora en la placa (foto del 16/09/2026, firmware normal de HEAD)
- Barra superior: a la izquierda aparece **un icono de cola/ajustes en lugar de ‹ atrás**; título y
  subtítulo bien; chip de fps bien.
- Barra inferior: **solo se ve la barra de progreso** con un icono redondo raro a su izquierda; **no se
  ve ninguno de los 9 botones** (bloqueo, repetir, anterior, −10, play, +10, siguiente, aleatorio,
  ajustes). La barra de progreso sí funciona.
- **Los botones de arriba y de abajo a la izquierda no hacen nada.** Solo se reproducen videos.
- En EEZ Studio (simulador de edición) `scr_player` sí muestra los botones, pero todavía con el
  **botón de pantalla completa** (2.º por la izquierda) y **sin repetir**. **Checks: 19 errores**, todos
  `"Default value": not set` en variables globales (`title`, `subtitle`, `pos_text`…).

## Tareas, en este orden

### T1 — Proyecto EEZ con 0 errores y fiel al diseño
- Pon valor por defecto a **todas** las variables globales (`""`, `0`, `false`). Criterio: Checks = 0
  (Keneth lo confirma abriendo el proyecto).
- `scr_player`, `scr_library`, `scr_no_media` igual que `referencia/png/Main.png`, `Biblioteca.png`,
  `SinMedios.png` / `SinMediosIncompatibles.png` / `ErrorSD.png`, con las medidas de
  `referencia/widgets/*.md` y el mapa de `referencia/LEEME.md`.
- **Quitar el botón de pantalla completa; en x 56 va `btn_repeat`** (decisión de Keneth).
- Play: círculo **44×44** (no 56) en x 218, como el diseño.
- **Iconos: solo los 25 PNG de `diseno_ui/iconos/`** (ya regenerados desde el diseño: back, queue,
  settings, lock, repeat, repeat_one, shuffle, prev, next, play, pause, rew10, fwd10, …). Súbelos como
  bitmaps de EEZ y regenera `main/ui`. **Ningún `LV_SYMBOL_*`** en estas pantallas.
- El código de `main/ui` debe ser el que genera EEZ con «Build»; nada de editar `screens.c` a mano sin
  reflejarlo en el proyecto.

### T2 — Que la placa muestre lo mismo que EEZ (el fallo de la foto)
Averigua por qué en la placa faltan los botones de `osd_bottom` y sale otro icono en `btn_back`:
orden/offset de las imágenes, contenedor con altura o recorte incorrecto, estilo que los oculta,
`ui_glue` que los esconde, o el volcado de D4 que pinta solo una parte de la barra. **Prueba con
evidencia** (log con posiciones y banderas de cada botón tras crear la pantalla: `UIDUMP,id=…,x,y,w,h,
hidden,clickable`) y explica la causa en el informe.

### T3 — Que todos los botones funcionen en la placa (D3 completo)
Tabla de `09` §D3 con la corrección de `09` (sin pantalla completa, con repetir). Además: ‹ atrás y cola
→ `scr_library`; tarjeta → reproducir; ajustes → aviso «Próximamente» (formato de aviso en
`referencia/LEEME.md`); bloqueo y desbloqueo con 1 s.
**`uinav` debe cubrir los 12 controles** (back, queue, lock, unlock, repeat, prev, rew, play, fwd,
next, shuffle, settings) **más** tocar una tarjeta de la biblioteca, y **pulsar por coordenadas a
través de la ruta táctil real** (no llamando a la acción directamente), para que un botón tapado o sin
`CLICKABLE` falle la prueba. Hoy solo cubre 6.

### T4 — D4, D5, D7 y avisos
- D4: confirmar con el log que la OSD se envía en una ventana; Keneth lo verá.
- D5: repetir la prueba de 10 reinicios con `last_path` apuntando a `trampa_codec.avi`; debe arrancar
  en la biblioteca. Guardar el log.
- Avisos emergentes (`BibliotecaAviso`, `PlayerAviso`) y tarjetas no compatibles/«Sin girar»
  (`BibliotecaLlena`).
- D7 (ruido vertical): el diagnóstico de `09`. Si no te da tiempo, dilo en el informe; no lo inventes.

### T5 — Medición e informe
- `perf_capture --phase F6a` completa, umbrales intactos (≤ 1 % por pista, ≥ 29 fps). Nuevo `F6a_run5`.
- `informes/FASE_6a.md`: tabla D1–D7 + T1–T4 con estado y prueba, capturas/fotos junto a los PNG.
- Dejar **el firmware normal** (sin autotest) flasheado en COM16.

## Reglas (sin cambios)
COM16 (a veces COM17; nunca COM8). Entorno: `$env:IDF_PATH="C:\esp\v6.0.1\esp-idf";
$env:IDF_TOOLS_PATH="C:\Users\Keneth\.espressif"; . $env:IDF_PATH\export.ps1`. Rutas con espacio entre
comillas. Prohibido: desactivar perros guardianes, relajar umbrales, redefinir métricas, tocar la
secuencia de inicio del panel, dejar la autoprueba en el firmware normal. **Commit tras cada tarea** para
que un corte por cuota no pierda trabajo. **No termines tu turno esperando una tarea en segundo plano**:
espera a que acabe la medición antes de responder.
