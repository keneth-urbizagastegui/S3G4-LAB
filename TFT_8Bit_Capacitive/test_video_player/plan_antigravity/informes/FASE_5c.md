# Fase 5c — Girar en el decodificador: EXPERIMENTO DESCARTADO

**Resultado: NO CUMPLE.** Encargo cancelado por el auditor el 16/09/2026 a las 01:11, tras 1 h 55 min
y 5 iteraciones. El informe lo escribe el auditor porque Antigravity no llegó a redactarlo.

## Qué se probó (vía A del encargo)
`JPEG_ROTATE_90D` en el decodificador (incompatible con el modo por franjas), fotograma completo de
320×480 en PSRAM, doble/triple búfer y DMA desde PSRAM, con `MADCTL 0x48` y el panel a 44,6 Hz.

## Medido (recalculado por el auditor desde los CSV)
| Ejecución | pres oculto | drop oculto | pres con OSD | decodificación/fotograma | envío/fotograma |
|---|---|---|---|---|---|
| run1 | 27,88 | 4,59 % | 21,68 | 22,2 ms | 23,0 ms |
| run2 | 27,89 | 4,72 % | 19,23 | 21,9 ms | 22,8 ms |
| run3 | 27,91 | 1,03 % | 21,51 | 22,2 ms | 22,9 ms |
| run4 | 27,82 | 0,80 % | 21,53 | 22,2 ms | 22,9 ms |
| run5 | 30,01 | 0,00 % | 28,50 | 22,5 ms | 19,3 ms | **pero la placa se reinició (Backtrace + heap con 4 B libres)** |

Referencia sin girar (`F5a_final.csv`): **29,67 oculto / 30,00 con OSD / 0,31 % de descartes**.

## Por qué no sirve
1. **Girar encarece la decodificación**: de ~16 ms a **22 ms** por fotograma.
2. **Enviar desde PSRAM es más lento** que desde memoria interna: de 20,2 ms a **22,9 ms**, por encima
   del periodo del panel (22,42 ms a 44,6 Hz). Cada fotograma pierde un refresco.
3. Con la OSD visible la caída es grande (21,5 fps): LVGL y el video compiten por la PSRAM.
4. La variante de la run5, la única con buenas cifras, **agota la memoria interna y provoca pánico**.
   Además, en esa iteración se desactivó el perro guardián de la tarea ociosa del núcleo 1 para que la
   prueba pasara: eso es tapar el síntoma, no arreglarlo. **No se adopta.**

## Estado del código
El experimento queda commiteado en la rama `video-player/fase-5c` como registro. **No se fusiona.**
La rama buena sigue siendo `video-player/fase-5a` (44,6 Hz, TE, blit por franjas desde memoria interna).

## Decisión (Keneth, 16/09/2026)
Se adopta la **vía B: girar los videos en origen**. El auditor ya convirtió los 4 con ffmpeg 9.0.1 a
320×480 (`TFT_8Bit_Capacitive/videos_rot/`, con miniatura y JSON): tamaños de fotograma idénticos a los
originales (7,7–12,1 KB de media, 34,3 KB el mayor), 266 MB en total. Continúa en `08_paquete_F5d.md`.
