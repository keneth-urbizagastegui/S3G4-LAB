# 16 — Revisión completa antes de seguir construyendo (17/09/2026)

> Rama `video-player/fase-6b`. Revisión del auditor con la placa y el registro serie
> (`mediciones/F6b_fallo_capas.log`), más las fotos de Keneth. **Nada de esto es una suposición: cada
> punto lleva su evidencia.** Constructor: Codex (`14_contrato_codex.md`).

## C1 — CRÍTICO: la placa se REINICIA al abrir cualquier capa
Keneth: «no puedo ver la cola, se pone una pantalla gris; lo mismo al bloquear, al pulsar Ver
rendimiento y con los gestos». No es una pantalla gris: **es un reinicio**. Registro:

```
I (56934) UI_ACTIONS: Action: open_queue -> abriendo cola
VIEW,mode=queue,track=0
assert failed: lcd_bus_set_overlay_rect lcd_bus.c:133 (s_overlay_rows != NULL)
Backtrace: ...
Rebooting...
```

Causa: `s_overlay_rows` reserva **480 filas × 168 B ≈ 80 KB de RAM interna**
(`lcd_overlay_row_cache_t` = 31 tramos × 4 B + 40 B de máscara + 2 B). Con ~120 KB libres y
fragmentados, la reserva falla y el `assert` reinicia la placa. Que en la autoprueba saliera bien fue
suerte: allí la reserva sí cabía.

Arreglo pedido:
1. **Reducir la estructura a lo imprescindible**: como mucho **4 tramos por fila** y sin máscara de
   320 bits (≈ 18 B por fila), y **solo para las filas del rectángulo de la capa**, no para las 480.
   Con 4 capas de 200×120 eso son unos pocos KB.
2. **Prohibido `assert` por un fallo de reserva** en la ruta de interfaz: si no hay memoria, se
   registra un aviso y se cae al camino lento (comparar píxel a píxel) o se dibuja la capa sin
   composición. **La placa nunca puede reiniciarse por abrir una capa.**
3. Criterio: abrir cola, bloqueo, estadísticas y los dos gestos, **20 veces cada uno**, sin un solo
   reinicio (log sin `Rebooting`), con `heap_int` ≥ 30 000 B al final.

## C2 — Miniaturas con ruido de colores en la biblioteca
Foto de Keneth: dos tarjetas («ICONIC BY MISTAKE» y «HANDS UP») muestran ruido de colores en lugar de
la miniatura; otras salen en negro. Sospechas: el búfer de decodificación de miniaturas se comparte con
el de las franjas de video o con el de capas, o se libera antes de tiempo. Encuentra la causa y
corrígela; criterio: las 6 miniaturas correctas tras reiniciar y tras volver del reproductor.

## C3 — Textos: sigue sin cumplirse la regla (fotos)
Siguen cortados o mal encajados: **«Almacenamiento»** (pestaña), **«Volver a escanear»** (botón),
**«Reproduciendo»** (chip de la tarjeta), **«Guarda la posición de cada vid…»** (subtítulo de
«Continuar donde lo dejé»), **«microSD SDHC 29.0 GB»** (se corta la B). Regla, otra vez: todo texto
**cabe** en su marco (ajustando ancho, relleno o bajando un escalón la fuente) o no se muestra; la
marquesina **solo** en el título del reproductor y en la fila actual de la cola; centrado donde el
diseño lo centra y con 8 px de margen. Comprueba pantalla por pantalla contra
`diseno_ui/referencia/widgets/*.md` y deja `TEXTFIT,offenders=0` de verdad.

## C4 — «Salto de los botones ⊓⊓»: cuadros en lugar de símbolos
Los iconos ⟲/⟳ de ese ajuste se dibujan como caracteres que la fuente no tiene. Usa las imágenes PNG
`rew10`/`fwd10` de `diseno_ui/iconos/`, o quita los símbolos del texto.

## C5 — Almacenamiento muestra «Espacio no disponible»
Debe mostrar el **espacio libre real** de la microSD (`esp_vfs_fat` / `f_getfree`) junto al total, como
en el tablero `AjustesAlmacenamiento`. Si no se puede calcular, el texto debe decir por qué.

## C6 — EEZ Studio vuelve a marcar 55 errores «Font not found»
Foto de Keneth. El proyecto referencia `montserrat_12/14/20` en los estilos y esas fuentes no existen
dentro del proyecto (las generamos aparte y se sustituyen en tiempo de ejecución, commit 23a0438).
Funciona en la placa pero deja el proyecto sucio y el simulador muestra «□». Arréglalo de forma limpia:
o los estilos apuntan a las fuentes integradas que EEZ sí conoce, o se añaden entradas de fuente al
proyecto que generen los `.c` de `main/ui_fonts`. Criterio: **Checks = 0** en EEZ Studio (lo confirma
Keneth) y las tildes siguen bien en la placa.

## Orden de trabajo
C1 primero (bloquea todo lo demás), luego C2, C3, C4, C5 y C6. Un commit por punto.

## Reglas
Herramientas: `powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/banco.ps1 -Accion
ui|build`. **Codex no flashea ni mide**: lo hace el auditor. Prohibido editar `main/ui` a mano,
relajar umbrales, redefinir métricas, tocar TE / la ventana única / el re-anclaje PTS, y dar por bueno
algo sin comprobarlo. Si un punto no se puede cumplir, parar y reportar con cifras.
