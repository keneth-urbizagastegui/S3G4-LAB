# 12 — F6b: completar la interfaz del diseño (17/09/2026)

> Rama nueva **`video-player/fase-6b`** desde la etiqueta **`vp-v0.7`** (F6a aprobada por Keneth).
> Objetivo: que **todo lo diseñado** exista y funcione en la placa: todas las pantallas, capas, estados y
> funciones. La línea vertical (L12) **no** entra aquí: se ataca cuando la UI esté completa.
>
> Contrato: `03_especificacion_ui_eez.md` (objetos, nombres, variables, acciones, §8 scroll, §11
> marquesina) + `diseno_ui/referencia/` (PNG 480×320, `widgets/*.md` y `LEEME.md` con el mapa de
> controles, iconos y el formato del aviso). Si algo no está dibujado, **pregunta en el informe**, no
> lo inventes.

## Lo que ya funciona (vp-v0.7) — no romper
Reproductor con sus 9 botones y las 2 barras, biblioteca con miniaturas y hoja «Continuar / Desde el
principio», atrás = pausa + biblioteca, repetir/aleatorio sin círculo, tildes, controles de golpe,
video a 30 fps con descartes ≤ 0,2 %. Ajustes de la biblioteca muestra «Próximamente» (se sustituye
por la pantalla real en B2).

## Parte A — Observaciones de Keneth sobre vp-v0.7 (primero)

| # | Observación | Qué hacer |
|---|---|---|
| A1 | **Bloqueo:** no aparece ninguna tarjeta con candado; al mantener pulsado se desbloquea, aparecen los controles y **hay un glitch que los hace desaparecer**. | `ovl_lock` visible según `referencia/png/Bloqueo.png` (tarjeta 200×116, `lock_big`, `arc_unlock` que se llena en 1 s, dos textos). Al bloquear se ve 2 s y se oculta; cualquier toque la muestra de nuevo. **Causa probable del glitch:** el mismo toque largo que desbloquea llega después al contenedor del video (`action_toggle_osd`) y oculta la OSD, o el auto-ocultar arranca con un `s_last_touch_time` viejo. Tras desbloquear: OSD visible y el toque en curso **se consume** hasta soltar. Demuéstralo con log. |
| A2 | **Cola:** el botón de tres líneas con play (arriba a la derecha) no hace nada visible. | Abre `scr_queue` real (B1). |
| A3 | **Fin de video sin repetir:** vuelve a la biblioteca, pero la tarjeta sigue con el chip **«Reproduciendo»**. | El chip solo en el video **cargado y no terminado**. Al terminar: sin chip y sin barra (visto). Añade un chip «Visto» opcional **solo si está en el diseño**; si no, nada. |
| A4 | **Repetir uno** funciona mejor pero puede mejorar. | Transición sin parpadeo: al llegar al final, volver al fotograma 0 sin mostrar la biblioteca ni una pantalla negra y sin saltos de la barra de progreso. Registra `EOF` y el primer fotograma presentado tras reiniciar (retardo en ms). Objetivo: < 100 ms y ningún fotograma ajeno. |

## Parte B — Pantallas y capas que faltan (del diseño)

| # | Objeto EEZ | Tablero de referencia | Notas |
|---|---|---|---|
| B1 | `scr_queue` | `Cola` | Lista con desplazamiento (`queue_list`, única zona desplazable aparte de `lib_grid`), fila actual resaltada con **marquesina**, pie con `btn_q_repeat`, `btn_q_shuffle`, `lbl_q_mode`; `btn_queue_close` vuelve al reproductor **sin pausar**. Tocar una fila = reproducir ese video. Orden = el de la reproducción (aleatorio incluido). |
| B2 | `scr_settings` con 4 pestañas | `Ajustes`, `AjustesReproduccion`, `AjustesAlmacenamiento`, `AjustesAcercaDe` | Desde `btn_settings` (reproductor, **pausa** como atrás), `btn_lib_settings` y `btn_settings_alt`. Volver regresa a la pantalla de origen. **Cada ajuste tiene efecto real y se guarda en NVS** (tabla de `06` §4): brillo, ocultar OSD tras N s (0 = nunca), mostrar fps, barra fina, repetir, aleatorio, continuar donde lo dejé, salto 5/10/30 s (el icono ±10 muestra el valor). Almacenamiento: datos reales de la microSD y `btn_rescan` con `Escaneo`. Acerca de: versión `vp-v0.8`, hardware, fps actuales. |
| B3 | Brillo | `Ajustes` + `Gestos` | Averigua si el pin de retroiluminación admite PWM (LEDC). **Si no, dilo y deja el deslizador desactivado** con una nota; no cambies el hardware. |
| B4 | `ovl_brightness` y `ovl_seek_hint` (gestos) | `Gestos` | Arrastre vertical en la mitad izquierda = brillo (si B3 es posible); doble toque en tercio izquierdo/derecho = ∓/± salto, acumulable, con la pista 600 ms. Los gestos **no** deben disparar botones ni `action_toggle_osd`. |
| B5 | `ovl_stats` | `Estadisticas` | Desde Acerca de o un toque largo en `chip_fps`: métricas en vivo (pres/dec fps, descartes, TE Hz, lectura SD, heap). Actualización ≤ 2 Hz. |
| B6 | Marquesina | 03 §11 | Solo en `lbl_title` del reproductor y en la fila actual de la cola. Con un título largo, `pres_fps` con OSD sigue ≥ 28,0. |
| B7 | Estados de la biblioteca | `BibliotecaLlena`, `BibliotecaAviso`, `Escaneo` | Chip «Sin girar» y meta «Sin girar: puede verse corte» (480×320), tarjeta no compatible a opa 115 con motivo en `#E5484D`, marco rojo y aviso al tocarla, barra de desplazamiento, `library_summary` «N videos · M no compatibles · X GB libres», `bar_scan` y tarjeta sin miniatura durante el escaneo. |
| B8 | `scr_no_media` en sus 3 variantes | `SinMedios`, `SinMediosIncompatibles`, `ErrorSD` | Textos e iconos exactos; `btn_retry` = reescanear; `btn_settings_alt` = ajustes. Prueba con tarjeta sin videos (o carpeta vacía simulada por log) y error de montaje simulado. |
| B9 | Estados de la barra | `EstadosOSD` | `btn_next` desactivado (40 %) en el último video con repetir en off; PRESSED con fondo `#1F2228`. |
| B10 | Aviso del vigilante | `PlayerAviso` | «No se pudo reproducir» al fallar un video, 3 s, y vuelta a la biblioteca. |

## Parte C — Pruebas y medición
- `perf_capture --phase F6b --timeout 900` (añade la fase copiando F6a; **mismos umbrales**).
- UINAV **sin resultados fijos**, ampliada a: cola (abrir, tocar fila, cerrar sin pausar), ajustes
  (cada pestaña, cada ajuste cambia NVS y su efecto), gestos, estadísticas, bloqueo (tarjeta visible,
  toque corto no desbloquea, largo sí, **OSD sigue visible 1 s después de soltar**), fin de video sin
  repetir (chip retirado), `btn_next` desactivado.
- **50 cambios de pantalla aleatorios** (`scn=uinav`) sin cuelgues y `heap_int` estable (± 5 KB).
- **Prueba de scroll** (07): arrastre sintético en `scr_player`, `scr_settings`, `ovl_stats`, `ovl_lock`
  → `SCROLL,offenders=0`. Solo `lib_grid` y `queue_list` se desplazan.
- `UI,screens=…,widgets=…,fonts=…,images=…` **contado de verdad** del proyecto generado (hoy está escrito a
  mano en `main.c`: cámbialo).
- Capturas del simulador de EEZ de cada pantalla junto a su PNG de `referencia/png/` en el informe.

## Reglas
- COM16 (a veces COM17; nunca COM8). Entorno PowerShell:
  `$env:IDF_PATH="C:\esp\v6.0.1\esp-idf"; $env:IDF_TOOLS_PATH="C:\Users\Keneth\.espressif"; . $env:IDF_PATH\export.ps1`.
  Autotest en `build_perf` (`04` §receta). Rutas con espacio entre comillas.
- **Prohibido:** desactivar perros guardianes, relajar umbrales, redefinir métricas (incluido el
  re-anclaje PTS de 100 ms y la etiqueta `init`), tocar la secuencia de inicio del panel o la
  sincronía de video, dejar la autoprueba en el firmware normal, **editar `main/ui` a mano** (todo cambio
  de UI en el proyecto EEZ y regenerado), escribir `PASS` sin comprobar.
- Solo `gui_task` llama a `lv_*`. Una sola función cambia de pantalla (`ui_glue_set_view_mode`).
- Commit tras cada punto (A1…B10). No termines mientras una medición siga en marcha. Agrupa
  compilar+flashear+medir en un solo comando.
- Al final: `informes/FASE_6b.md` con tabla A1–A4 y B1–B10 (estado, prueba, captura) y el firmware
  normal flasheado.
