# 15 — F6b iteración 3 (primer encargo a Codex): secciones 3–10 + observaciones de Keneth

> Rama `video-player/fase-6b`, desde `5a212fd`. Constructor: **Codex** (`gpt-5.6-terra`, esfuerzo
> `medium`). Contrato: `14_contrato_codex.md` (léelo entero: prohibiciones y obligaciones).
> Todo ocurre dentro de `TFT_8Bit_Capacitive/test_video_player`.
>
> **Hecho y verificado, no lo rompas:** composición de capas sobre el video (`d706559`: 29,9 fps y
> 0,41 % de descartes con capa, +0,48 ms por fotograma), cola (`ffe5350`) y ajustes (`a08a5a5`).
> El paquete `13_paquete_F6b_it2.md` sigue vigente: sus secciones 3–10 son parte de este encargo.

## Parte A — Observaciones nuevas de Keneth (17/09/2026, probando en la placa)

### A1 — Quitar el pie de la cola
En `scr_queue` aparecen los iconos de repetir y aleatorio con un texto de modo. **No hacen nada** y
confunden. Quítalos del proyecto EEZ (`btn_q_repeat`, `btn_q_shuffle`, `lbl_q_mode` y el contenedor
`queue_footer`) y borra su código (`update_queue_footer` y las llamadas). Los modos se cambian desde el
reproductor o desde Ajustes. La lista ocupa el alto que deja libre el pie.

### A2 — Brillo: mínimo real 25 %, escala mostrada 0–100 %
- El mínimo pasa de 20 % a **25 %** (por debajo no se ve nada).
- Lo que **ve el usuario** va de 0 a 100: `mostrado = (real − 25) × 100 / 75`, y a la inversa
  `real = 25 + mostrado × 75 / 100`. El deslizador de Ajustes, la barra del gesto y la etiqueta usan la
  escala mostrada; NVS guarda el valor **real**.
- Al arrancar, un valor guardado < 25 se corrige a 25.
- Criterio: el deslizador al mínimo muestra «0 %» y la pantalla sigue viéndose; al máximo, «100 %».

### A3 — Iconos de las capas con recuadro cuadrado (candado, saltos, brillo)
Causa: la composición de §0 copia **rectángulos opacos**, así que las esquinas redondeadas y lo que
debería quedar transparente se rellenan con el fondo que dibuja LVGL.
Solución pedida (autorizada en el camino del video, sin tocar TE ni la ventana única): **color clave**.
1. Antes de que LVGL dibuje una capa, rellena su zona del búfer de capa con un color clave que no
   aparezca en el diseño (por ejemplo `0x07E0`, verde puro; documenta cuál eliges).
2. Al componer cada franja, copia píxel a píxel **saltando** los que son del color clave, en lugar de
   `memcpy` de toda la fila. Así la esquina redondeada y el hueco alrededor del icono dejan ver el video.
3. Mide el coste: el criterio de §0 sigue valiendo (**≥ 29 fps, descartes ≤ 1 %, `frame_blit_ms` con
   capa ≤ +1,0 ms respecto a sin capa**). Si no se cumple, para y repórtalo con cifras.
4. Criterio visual (foto de Keneth): candado, ⟳/⟲ y brillo **sin recuadro cuadrado**; se ve el video
   alrededor del icono y de la tarjeta.

### A4 — Textos cortados o descuadrados (sigue sin resolverse)
Es la sección 6 de `13`. Repásala pantalla por pantalla, no solo en Ajustes: pestañas, etiquetas de
ajuste, cola, avisos, biblioteca y capas. Recuerda la prueba automática `TEXTFIT` con
`offenders=0` (ancho del texto frente al ancho disponible, marquesina donde no quepa, centrado donde el
diseño lo centra).

## Parte B — Secciones pendientes de `13_paquete_F6b_it2.md`
Ejecútalas en este orden, con un commit por sección:
- **3 · Gestos:** sin recuadro fantasma en el lado no tocado (ya usa una sola capa: compruébalo), el
  video no se detiene, pista de 600 ms.
- **4 · `ovl_stats`:** se abre con **pulsación larga sobre el chip de fps** (hoy no funciona) y desde
  Ajustes; fondo completo; se cierra con un toque.
- **5 · `ovl_lock`:** tarjeta del tablero `Bloqueo` sin fondo propio en los textos (con A3).
- **6 · Textos** (ver A4).
- **7 · Fuentes en EEZ:** **55 errores «Font not found»**. Las fuentes con tildes se generaron fuera de
  EEZ y el proyecto las referencia en minúscula (`montserrat_12/14/20`) sin tenerlas. Impórtalas en el
  proyecto y usa esas. Criterio: **Checks = 0** en EEZ Studio y el simulador muestra las tildes.
- **8 · Repetir uno sin costura:** `LOOP,gap_ms` ≤ 67 ms en 5 bucles, sin negro ni pausa visible.
- **9 · Reglas de uso:** una capa a la vez; tocar fuera cierra (salvo el bloqueo); el temporizador de
  ocultar la OSD se congela con una capa abierta; cada toque reinicia ese temporizador; un toque = una
  acción (`UIEV`); gestos y botones no se pisan; los ajustes se aplican al arrancar.
- **10 · Pruebas y cierre** (ver más abajo).

## Parte C — Fallos abiertos de la medición del auditor (`F6b_it2_auditor`)
- `UINAV`: `lock`, `lock_short_touch` y `seek` fallan **la primera vez** y pasan en el segundo intento.
  Arréglalo de verdad (esperas o consumo del toque), no subiendo tiempos de espera a ciegas.
- `te_hz`: una muestra aislada de **48,4 Hz** en el escenario `tap` (el resto 44,0–45,0) hace fallar el
  criterio de variación ≤ 2 Hz. Diagnostica por qué se mide mal con el video detenido y corrige **la
  medición**, no el umbral. Si concluyes que la muestra es válida, para y repórtalo.

## Parte D — Cierre
- `perf_capture --phase F6b --timeout 900` en **ÉXITO**, umbrales intactos, salida en
  `plan_antigravity/mediciones/F6b_run3` (no en la raíz).
- `UINAV` sin `PASS` fijos y ampliada a lo nuevo: cola sin pie, brillo (mínimo real 25 % y escala
  mostrada 0–100), estadísticas por pulsación larga, bloqueo sin congelar el video (`pres_fps` > 25
  durante el bloqueo), `TEXTFIT,offenders=0`, `SCROLL,offenders=0`, `LOOP,gap_ms`, 50 cambios de
  pantalla aleatorios con `heap_int` estable (± 5 KB).
- `informes/FASE_6b.md` actualizado: una fila por punto (A1–A4, secciones 3–10, Parte C) con estado,
  prueba y el dato que lo respalda.
- **Firmware normal flasheado** en COM16 al terminar.

## Recordatorio de lo prohibido (contrato §4)
Perros guardianes, umbrales, métricas (re-anclaje PTS de 100 ms, umbral de descarte, etiqueta `init`),
TE / ventana única / orientación del panel (la excepción autorizada es la composición de capas de §0 y
el color clave de A3), `main/ui` a mano, `PASS` sin comprobar, autoprueba en el firmware normal,
enmendar commits ajenos. Si algo no se cumple: **para y reporta con cifras**.
