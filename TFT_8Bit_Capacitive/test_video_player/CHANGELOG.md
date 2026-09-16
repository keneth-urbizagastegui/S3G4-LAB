# Registro de versiones — Reproductor de video S3G4

Una entrada por etiqueta, con las cifras **medidas** de esa versión (no estimadas). Detalle por fase en
`plan_antigravity/informes/` y datos en bruto en `plan_antigravity/mediciones/`.

Leyenda: **presentados** = fotogramas que llegan de verdad al panel · **descartes** = fotogramas que el
reloj de reproducción salta por llegar tarde, sobre el total · ambos con la pantalla completa.

---

## `vp-v0.4` — E/S de la microSD y lector adelantado · 15/09/2026
- **Presentados: 30,01 fps** sin controles · **30,02** con controles · **descartes 0,00 %** (0 de 2100).
- Lector de la tarjeta en el núcleo 0 con 3 huecos en PSRAM: el hilo de video ya no espera (0,1 ms).
- Frecuencia de la microSD fijada en 20 MHz: a 26 y 40 MHz no monta (0 de 10 intentos, error 0x108).
- PSRAM a 80 MHz. Búfer JPEG que crece hasta 128 KB. Índice `idx1` sin tope fijo.
- **Pendiente:** la prueba de extracción en caliente nunca llegó a ejecutarse.

## `vp-v0.3` — El video se pinta directo en el panel · 15/09/2026
- **Presentados: ~29,5 fps** sin controles · **~29,4** con controles (antes 13 y 7).
- Decodificación por franjas de 16 líneas: mientras el bus envía una, la CPU decodifica la siguiente.
- LVGL deja de tocar la zona del video; su repintado se recorta alrededor.
- **Descartes 1,53 %**, por encima del 1 % permitido: causa localizada en picos de lectura de 25 ms.

## `vp-v0.2` — Reloj de reproducción y cadencia · 15/09/2026
- Tick del sistema a 1 ms y reloj basado en la marca de tiempo del video, con descarte de tardíos.
- El video pasa a ir **a velocidad natural**, confirmado en la placa.
- **Pero solo 13 de cada 30 fotogramas llegaban a la pantalla**: el cuello de botella era LVGL.
- Corregido el toque en pantalla completa (el lienzo no era pulsable).

## `vp-v0.1` — Concurrencia y respuesta táctil · 15/09/2026
- Cola de comandos entre interfaz y reproductor; ninguna llamada a LVGL fuera de su tarea.
- Táctil en tarea propia: lectura de 0,7–0,9 ms y como mucho 10 ms de antigüedad (antes iba a remolque
  del dibujado del video).
- 20 cambios de pista y 50 saltos seguidos sin desincronizar el título.

## `vp-v0.0` — Instrumentación y línea base · 15/09/2026
- Se separa por primera vez **decodificados** de **presentados**: el acta decía 30 fps y en pantalla
  llegaban **15,1–15,4** (8,2 con la barra visible).
- Inventario de los AVI de la tarjeta: los 4 están a 30 fps, 480×320, 4:2:0, con 7,7–12,8 KB por
  fotograma.

## `vp-v0.0-base` — Punto de partida · 15/09/2026
- Código tal como lo entregó Antigravity, más el plan de trabajo y la revisión.

---

## En curso (sin etiquetar)

- **F5a** — sincronía con el pin TE del panel (GPIO 7, cableado por Keneth) y refresco bajado a 44,6 Hz:
  **29,67 fps y 0,31 % de descartes**. El corte diagonal persiste: se diagnosticó, con fotografía, que
  es por **orientación** (escribimos perpendicular al barrido).
- **F5c** — girar dentro del chip: **descartado**, 27,8 fps y una variante que agotaba la memoria.
- **F5d** — girar el video en origen: los 4 videos ya están convertidos a 320×480 y copiados en la
  tarjeta; falta el cambio de orientación en el firmware.
