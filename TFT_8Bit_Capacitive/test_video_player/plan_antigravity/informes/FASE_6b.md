# Fase 6b — estado al 17/09/2026 (Antigravity sin cuota semanal)

Rama `video-player/fase-6b`. Antigravity agotó la cuota **semanal** (vuelve en ~5 días). Este informe lo
escribe el auditor con lo que hay en la rama y lo medido por él.

## Hecho

| Sección | Commit | Estado |
|---|---|---|
| 0 · Composición de capas opacas sobre el video | `d706559` | **Verificado por el auditor.** El video ya no se detiene al abrir una capa. |
| 1 · `scr_queue` | `ffe5350` | Código listo (video de fondo, lista desplazable, toque corto). **Sin probar con el dedo.** |
| 2 · `scr_settings` | `a08a5a5` (sobre `cc2d1a6` del auditor) | Código listo (reanudar al volver, brillo 20–100 %, «Ver rendimiento»). **Sin probar.** |

### Medición del auditor `F6b_it2_auditor` (17/09/2026)
| Criterio | Umbral | Medido |
|---|---|---|
| `pres_fps` con capa (`scn=overlay`) | ≥ 29,0 | **29,90** |
| Descartes con capa | ≤ 1 % | **0,41 %** |
| Coste de la capa en `frame_blit_ms` | ≤ +1,0 ms | **+0,48 ms** |
| Descartes con la OSD oculta | ≤ 1 % | **0,28 %** |
| `SCROLL,offenders` | 0 | **0** |
| `heap_int` mínimo | ≥ 30 000 B | **119 719 B** |

**El resultado global del script es FALLO** por dos motivos, ambos abiertos:
1. `UINAV`: `lock`, `lock_short_touch` y `seek` fallan la primera vez y pasan en el segundo intento
   (problema de tiempos en la prueba o de consumo del toque, no de la lógica de bloqueo).
2. `te_hz`: una muestra aislada de **48,4 Hz** en el escenario `tap` (el resto 44,0–45,0) dispara el
   criterio de variación ≤ 2 Hz. Sospecha: la medición de TE con el video detenido.

## Pendiente (paquete `13_paquete_F6b_it2.md`, secciones 3–10)
- 3 · Gestos: recuadro fantasma en el lado no tocado.
- 4 · `ovl_stats` por pulsación larga en el chip de fps; fondo completo.
- 5 · `ovl_lock` sin recuadro sólido propio (ya no congela el video, §0).
- 6 · Regla de textos + prueba `TEXTFIT`.
- 7 · Fuentes en el proyecto EEZ: **55 errores «Font not found»** (las fuentes con tildes se generaron
  fuera de EEZ y el proyecto las referencia en minúscula).
- 8 · Repetir uno sin costura (`LOOP,gap_ms`).
- 9 · Reglas de uso (una capa a la vez, toque fuera cierra, un toque = una acción…).
- 10 · Pruebas y cierre: UINAV ampliada, `TEXTFIT`, medición en ÉXITO, firmware normal.
- Observaciones de Keneth del 17/09 sobre la it1 que siguen sin verificar en placa: cola, ajustes
  (textos cortados y sin centrar), gestos, estadísticas y bloqueo.

## Estado de la placa
Firmware **normal** de `0928443` flasheado en COM16 por el auditor, para la prueba manual de Keneth.
