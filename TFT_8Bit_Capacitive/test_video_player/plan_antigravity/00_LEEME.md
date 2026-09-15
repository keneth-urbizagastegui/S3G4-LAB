# Paquete de trabajo — Reproductor de video S3G4 (ESP32-S3 + ILI9488 + LVGL 9.5 + EEZ Studio)

**Para:** Antigravity (constructor) · **De:** Claude (planificación y auditoría) · **Fecha:** 15/09/2026

## Documentos, en orden de lectura
1. `01_revision_y_opinion.md`: qué está bien, qué está mal y por qué (hallazgos C1–C6, A1–A6, M1–M8).
2. `02_plan_mejoras_firmware.md`: fases F0–F7 con código y criterios de aceptación.
3. `03_especificacion_ui_eez.md`: pantallas, widgets con coordenadas, estilos, acciones y variables.
4. `04_protocolo_loop_engineering.md`: compilar → flashear → medir → `/review` → informe.
5. Canvas del diseño visual: `diseno_ui/` (fuente, un `.dc.html` por pantalla) y la versión publicada
   https://claude.ai/artifact/A9vP5kNZF5qfsbwkqVzYRQ

## Decisiones ya tomadas (no se reabren)
- **Solo software.** El pinout del acta §2.1 queda congelado.
- **Solo video, sin audio.** No se reserva nada en la UI salvo lo indicado en `03` §4.
- **EEZ Studio reemplaza `spotify_ui.c`**, con acciones y variables nativas (sin *flow*).
- Formato MJPEG/AVI 4:2:0 y el decodificador `esp_new_jpeg` se mantienen.
- Se retira la marca «Spotify» del producto.

## Datos del banco (confirmados por Keneth el 15/09/2026)
- ESP32-S3 del reproductor: **UART COM17**. Nunca COM8.
- INT del táctil FT6236: **no conectado** → sondeo I2C.
- Los AVI están en la microSD, en el zócalo de la pantalla. **Se desconocen sus fps**: F0 los mide.
- Ramas y versiones: `04` §10.

## Un encargo = una fase
No mezcles fases. Empieza por **F0**. Si vas justo de tiempo, **entrega lo que tengas y avisa**.

## Reglas de trabajo (obligatorias)
1. **Las contradicciones se anotan, no se resuelven.** Si el plan, el acta, el código, una cabecera de
   IDF/LVGL o la placa se contradicen, escríbelo en «CONTRADICCIONES» del informe y sigue con la opción
   más conservadora.
2. **Los números se cuentan, no se escriben.** Nada de totales fijos: número de videos, bloques JPEG,
   FPS, tamaños de índice. Se derivan de los datos. (El umbral de un criterio sí es fijo: lo pone el
   plan.)
3. **El entregable se ejecuta y dice con qué código sale.** Fallar es un resultado válido si el fallo
   es real y está medido.
4. **Sin grep ni búsqueda por patrón** con tus herramientas: el espacio de «S3G4 LAB» rompe el
   analizador y el trabajo se cuelga en bucle. Lee los ficheros enteros.
5. Ruta de `node` si alguna herramienta lo necesita (no está en el PATH):
   `C:\Users\Keneth\scoop\apps\fnm\current\node-versions\v24.16.0\installation\node.exe`

## Lo que NO puedes tocar
- Nada fuera de `TFT_8Bit_Capacitive\test_video_player\` salvo `TFT_8Bit_Capacitive\convert_videos.py`
  (F5), y el acta **solo** para actualizar cifras medidas al final.
- La secuencia de inicialización del ILI9488 (`ili9488_8080_init`, registros F7…29) ni `MADCTL`.
- El reloj del bus i80 (16 MHz) salvo para convertirlo en opción de Kconfig con el mismo valor por
  defecto.
- `managed_components/` (versiones en `dependencies.lock`).
- Los umbrales de aceptación de `04` §5.
- Otros ESP32-S3 del banco: **no flashees un COM que no hayas identificado** (`04` §2).

## Estructura que debe quedar
```
test_video_player/
  main/
    main.c                 (solo inicializa)
    player.c/.h            (tarea, cola, reloj PTS)
    avi_demux.c/.h         (antes avi_player)
    lcd_bus.c/.h           (mutex, región de video, strips DMA)
    ili9488_8080.c/.h      (driver; draw_bitmap pasa por lcd_bus)
    ft6236_i2c.c/.h        sdcard_spi.c/.h   media_library.c/.h   settings_nvs.c/.h   perf.c/.h
    ui/                    (generado por EEZ, no editar a mano)
    ui_glue/actions.c vars.c gestures.c
    Kconfig.projbuild
  legacy/                  (spotify_ui.*, s3v_player.*, lz4.*, tjpgd*)
  tools/perf_capture.py
  sdkconfig.defaults  sdkconfig.perf.defaults
  plan_antigravity/mediciones/  plan_antigravity/informes/
```
