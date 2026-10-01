# 11 — F6a iteración 4: lógica de pantallas, capas y botones (17/09/2026)

> Rama `video-player/fase-6`, desde `1ecbabf`. Antes de F6b. Viene de la prueba de Keneth con el dedo
> y de la revisión del auditor sobre `main/ui_glue/actions.c`, `main/main.c` y `main/player.c`.
> **Aprobado por Keneth en la it3:** aspecto de la barra (salvo L6), controles de golpe, reproducir,
> anterior/siguiente, ±10 s, aleatorio y repetir (salvo L4), EEZ con Checks = 0. **No lo rompas.**
>
> Recordatorio: en la it3 se revirtió un re-anclaje PTS a 60 ms que anulaba los descartes
> (`informes/FASE_6a.md` §6). Umbrales y métricas intocables.

## Modelo de navegación (lo que debe quedar)

```
             ┌──────────── tocar tarjeta ─────────────┐
             │   (si hay posición guardada:            │
             │    hoja «Continuar / Desde el principio»)│
             ▼                                          │
  scr_player ──── ‹ atrás (PAUSA y guarda posición) ──▶ scr_library
      │  ▲                                              │  ▲
      │  └──── fin de video con repetir OFF ────────────┘  │
      │                                                    │
      └── cola (F6a: aviso «Próximamente»; F6b: scr_queue)  └── ajustes (aviso en F6a)
  Capas de scr_player: osd_top + osd_bottom (auto-ocultar), ovl_lock, toast.
  Capa de scr_library: hoja «reanudar», toast.
```
Reglas:
- **El video solo se pinta en el panel si la pantalla activa es `scr_player`.** Nada fuera de
  `scr_player` puede fijar un `video_rect` distinto de `{0,0,0,0}`.
- **Al salir de `scr_player` el video se pausa** (y se guarda la posición). Al volver con la misma
  tarjeta, se reanuda donde estaba.
- Un único punto de verdad para la vista: `ui_glue_set_view_mode()`. `action_open_library`,
  `action_play_index` y `ui_glue_init` lo usan; nadie más llama a `loadScreen`/`lv_screen_load` ni a
  `lcd_bus_set_video_rect` directamente.

## Defectos

### L1 — La biblioteca «vuelve al video» a los 3 s (CAUSA ENCONTRADA)
`action_open_library` pone la vista en biblioteca pero **no pausa el video** ni desactiva el auto-ocultar
de la OSD. A los 3 s, `ui_glue_tick` llama a `ui_glue_set_osd_visible(false)`, que manda
`PCMD_SET_VIDEO_RECT {0,0,480,320}` y `lcd_bus_set_video_rect(0,0,480,320)`: **el video vuelve a
pintarse encima de la biblioteca**, aunque la pantalla activa sea `scr_library`.
Arreglo: auto-ocultar y `ui_glue_set_osd_visible` solo actúan con la vista en `scr_player`; al abrir
la biblioteca, `PCMD_PAUSE` + guardar posición. Criterio: quedarse 60 s en la biblioteca sin que
aparezca video (log `VIEW` cada cambio) y confirmación de Keneth.

### L2 — «atrás» y «cola» hacen lo mismo (decisión de diseño)
- `btn_back` → biblioteca (pausa, L1).
- `btn_queue` → en F6a **aviso «Próximamente»**; en F6b abre `scr_queue`. Ya no lleva a la biblioteca.

### L3 — Continuar o empezar desde el principio (nuevo, tablero `BibliotecaReanudar`)
Al tocar una tarjeta **con posición guardada entre 5 s y duración − 10 s**, se abre la hoja inferior de
`referencia/png/BibliotecaReanudar.png` (medidas en `referencia/widgets/BibliotecaReanudar.md`):
«Continuar en m:ss» (posición − 2 s) y «Desde el principio» (posición 0 y se borra la guardada); la X o
tocar fuera la cierra. Sin posición guardada, la tarjeta reproduce directamente desde 0.
La tarjeta del video **actual** (pausado por L1) reanuda sin preguntar.

### L4 — Repetir uno enseña ~1 s del siguiente video
En `player_handle_eof` con `REPEAT_ONE` se llama a `avi_player_restart()` pero el lector adelantado
(3 huecos en PSRAM) y/o la política de fin pueden estar sirviendo fotogramas de otra pista. Encuentra
la causa con log (`EOF,track=…,repeat=…,next_frame_from=…`) y haz que al reiniciar se **vacíen los
huecos del lector**. Criterio: 5 repeticiones seguidas de un video sin ningún fotograma ajeno (log).

### L5 — Barra de progreso de tarjetas vistas enteras
Al terminar un video se escribe `pos=0` en NVS, pero **`media_item_t.resume_ms` en RAM no se actualiza**
y la tarjeta sigue mostrando la posición vieja. Además, una posición guardada a menos de 10 s del final
debe tratarse como «visto» (= 0). Actualiza el valor en RAM en cada guardado (`media_library_set_resume`)
y refresca la tarjeta.

### L6 — Botones activos con círculo rojo
Repetir y aleatorio activos muestran **fondo circular rojo**: es el estado CHECKED del tema de LVGL.
Diseño (`EstadosOSD.png`): **sin fondo**, solo el icono en `#F2B33D`. Quita `bg` en CHECKED del estilo
`st_icon_btn` en el proyecto EEZ (no en `screens.c` a mano). PRESSED: fondo `#1F2228` radio 22.

### L7 — Tildes y caracteres especiales
Las fuentes Montserrat que trae LVGL solo tienen ASCII: «Próximamente», «mantén», «—», «·», «…» y el
emoji 🔒 salen mal. Convierte en EEZ Montserrat 12, 14 y 20 con el rango **0x20–0x7E, 0xA0–0xFF,
0x2014, 0x2022, 0x2026** (y los símbolos que uses). Quita el emoji: el candado es la imagen `lock_big`.
Criterio: foto de Keneth con «Próximamente» y «Mantén pulsado» bien escritos; `library_summary` con «·».

### L8 — Bloqueo poco intuitivo → hacerlo como el tablero `Bloqueo`
Hoy es una etiqueta genérica creada en código. Debe ser `ovl_lock` del proyecto EEZ (03 §3.7):
tarjeta 200×116 en 140,104, `lock_big` dentro de un círculo `#15171C`, **`arc_unlock` que se llena
durante la pulsación de 1 s** (feedback visible), «Pantalla bloqueada» / «Mantén pulsado para
desbloquear». Comportamiento: al bloquear, la tarjeta se ve 2 s y se oculta (queda el video limpio);
cualquier toque la vuelve a mostrar; si se suelta antes de 1 s, el arco vuelve a 0.

### L9 — Manejadores de tarjeta duplicados
`fix_card_events` y `action_library_populate` registran `action_play_index` en la tarjeta **y** en cada
hijo, a veces dos veces: un toque puede enviar varios `PCMD_OPEN`. Un solo manejador en la tarjeta y
los hijos con `EVENT_BUBBLE` sin `CLICKABLE`. Criterio: un toque = un `PCMD_OPEN` (log).

### L10 — Código generado editado a mano
`main/ui/screens.c` y `ui.c` llevan cambios manuales (guardas `startWidgetIndex >= 0`, caché
`s_screens`). Se pierden al pulsar «Build» en EEZ. Crea las tarjetas en `ui_glue` sin el user widget
indexado (o usa la API de EEZ para instancias dinámicas) y deja `main/ui` **idéntico** a lo que genera
EEZ. Criterio: regenerar desde EEZ no produce diff en `main/ui` y el firmware sigue funcionando.

### L11 — UINAV con resultados fijos
`play`, `prev`, `rew`, `fwd`, `next` y `seek` imprimen `PASS` sin comprobar nada. Cada uno debe verificar
su efecto (`state`, `track_index`, `pos_ms` antes/después). Añade: L1 (60 s en biblioteca sin video),
L2 (cola → toast), L3 (hoja y sus dos botones), L8 (bloqueo con pulsación corta no desbloquea; larga sí).

### L12 — Línea vertical que se desplaza (D7, diagnóstico obligatorio)
Keneth ve una **línea vertical que recorre la pantalla de lado a lado**. Con el panel en orientación
nativa (`MADCTL 0x48`), el barrido del panel avanza **de izquierda a derecha** en la vista apaisada, así
que esto es el aspecto de un **corte (tearing) residual** que se desplaza porque 30 fps y 44,6 Hz no están
enganchados. Hipótesis a comprobar con datos, sin tocar la secuencia de inicio del panel:
1. Los volcados de LVGL (etiquetas de posición y fps cada 250 ms, chip, OSD) usan el bus **fuera** de la
   espera de TE y retrasan el envío del video. ¿Aparece la línea con la OSD **oculta**? (Keneth)
2. El envío del fotograma empieza tarde respecto a TE (`te_wait` + tiempo hasta el primer byte).
   Mide `te_to_first_byte_ms` y `frame_blit_ms` por fotograma.
3. Compara con `vp-v0.6` en el mismo video (Keneth, a simple vista).
Entrega el diagnóstico con cifras. Cualquier cambio de sincronía se propone y lo aprueba el auditor.

## Criterios de cierre de la it4
- L1–L11 hechos con su prueba; L12 con diagnóstico.
- `perf_capture --phase F6a --timeout 600` en ÉXITO, umbrales intactos. Nuevo `F6a_run9`.
- UINAV sin `PASS` fijos, todo verificado.
- Informe `informes/FASE_6a.md` actualizado (sección it4) y firmware normal flasheado.

## Reglas
COM16 (a veces COM17; nunca COM8). Entorno: `$env:IDF_PATH="C:\esp\v6.0.1\esp-idf";
$env:IDF_TOOLS_PATH="C:\Users\Keneth\.espressif"; . $env:IDF_PATH\export.ps1`. Rutas con espacio
entre comillas. Prohibido: desactivar perros guardianes, relajar umbrales, redefinir métricas (incluido
el re-anclaje PTS), tocar la secuencia de inicio del panel, dejar la autoprueba en el firmware normal,
editar `main/ui` a mano. Commit tras cada defecto. No termines mientras una medición siga en marcha.
**Minimiza las ventanas:** agrupa compilar + flashear + medir en un solo comando de PowerShell y no
abras un proceso por cada lectura del puerto.

## Anexo L12 (Keneth, 17/09/2026): la línea aparece también con la OSD OCULTA
La hipótesis 1 pierde peso, pero no se descarta del todo: con la OSD oculta sigue actualizándose
`bar_mini_progress` (y=317, cada 250 ms). Prioriza la hipótesis 2 (inicio del envío respecto a TE y
duración del envío frente al periodo de 22,4 ms) y prueba el modo `tear_diag` con la barra fina
desactivada para separar ambas causas.
