# S9-B — retomada y cierre del encargo de Claude

Fecha de sesión: 5 octubre 2026 (America/Lima). Agente: Codex.

## Autorización y alcance

Keneth pidió retomar la tarea S9-B encargada por Claude. Queda levantada la pausa de `2026-10-04-2135-codex-pausa-s9b.md` para completar las verificaciones pendientes, continua corregida e informe, sin elegir variante ni remedio. Se sigue `ENCARGO_CODEX_S9_B.md`, `PLAN_SIMULACION_S9.md` y las decisiones vigentes. No se repite A ni la campaña B original; no se toca CH1, modelos originales, firmware, esquemas ni banco físico.

## Comprobaciones previas

- MCP s3g4-context conectado, consultado con source S3G4/ y orden timeline; estado y encargo contrastados con archivos actuales.
- Sin procesos S9 activos al retomar. Continua corregida aún ausente.
- Campaña B original: 4 295/4 295 casos, 14 391 ejecuciones nativas, auditoría estructural previa sin errores; código 1 conservado por cambio externo histórico de STATE, no por simulaciones fallidas.
- Smoke ya terminado: 25/25 casos, 57 ejecuciones, código 0. Comparación preliminar de sus 25 filas con baseline: mismos IDs, cero diferencias a tolerancia absoluta/relativa 1e−9. Falta emitir el resultado persistente y auditar los decks en esta sesión.
- SHA256 de `comun/lm6172_hoja.lib` coincide con K0 y campaña: `4fb5d82e3319553113ba8ff7c8ff5bc4b7fa65e9a13b59dea2173140fe90d31b`.

## Cambio y método de retomada

Se añade `--resume-after-smoke` a `CH23_entrada/finalizar_s9_b.py`: comprueba metadatos/hash del smoke completo, audita y compara lo guardado, sin volver a simularlo ni repetir la campaña. Conserva las etapas previas de `resultados/s9b_cierre.json` y escribe nuevas consolas con sufijo UTC para no sobrescribir las históricas.

Después ejecuta únicamente `ejecutar_s9_b_op_corregido.py --resume` (cuatro cohortes × 500 placas, seis OP por placa), su auditor y `informar_s9_b.py`. Se conserva el macromodelo: sólo se compensa el offset nativo mediante las cuatro fuentes MC independientes. La fuente `VOS IP IPR` resta su parámetro en IN+; el desplazamiento de +2.986 mV en el parámetro equivale a −2.986 mV efectivos, según el método ya documentado. No se cambian rieles, pasivos, semilla ni los originales.

El criterio C8 vigente es ≤2 µs en DECISIONS; el plan histórico todavía dice 1 µs. No se acepta una variante automáticamente aunque cumpla.

El primer intento en el entorno restringido abortó al importar SciPy (`ModuleNotFoundError`), sin lanzar OP. Un intento de usar explícitamente el Python local dio acceso denegado; la ejecución fuera del sandbox fue autorizada por la revisión automática para el alcance ya pedido. Se usa `C:/Users/Keneth/AppData/Local/Programs/Python/Python312/python.exe` (3.12.10, numpy/scipy disponibles), sin instalar ni descargar dependencias. El cierre reiniciado auditó el smoke con código 0 y generó `resultados/s9b_smoke_repeticion.json` sin diferencias. Consola del coordinador: `%TEMP%/s9b_retomada_20261005_pipeline_retry.log`; las etapas conservan su ruta en `resultados/s9b_cierre.json`. El intento fallido también queda en esa contabilidad, sin confundirlo con fallo eléctrico.

Se refuerza `informar_s9_b.py` para rechazar OP corregidas con código de salida no cero o cambios protegidos y se corrige la descripción del tiempo de la campaña original: 2 854 s corresponde a su última reanudación registrada, no a todas las sesiones históricas. Los números de simulación y criterios no se alteran por esta aclaración.

El auditor de OP corregidas enumera ahora los decks una sola vez y comprueba los seis estados nominales distintos por placa; mantiene la comparación de bytes tras restaurar las cuatro fuentes. Se contrastó el índice con el método anterior en diez placas terminadas: mismos seis decks en todas. AST de los tres scripts modificados: correcto. El informe añade `s9b_op_corregido_contabilidad.json` para separar intentos nativos fallidos/repetidos de casos terminados y de simulaciones de referencia; no ocultar los tiempos límite recuperados por el reintento contractual.

## Evidencia, resultados y pendientes

La sesión continúa el 6 octubre, America/Lima. **Primer checkpoint completo**, a 2026-10-06T04:55:52Z (23:55 del 5 oct, Lima): 500/500 placas de 5 mV/div, ganancia y centro compensable 500/500, recorrido ±4.5 div **483/500 (96.6 %)**. Resultado preliminar de esa cohorte, no aceptación final ni elección de variante. La placa MC189 agotó un primer punto de 60 s y completó el reintento; su ganancia cumple y su recorrido no cumple C9. Ese fallo eléctrico se conserva dentro de las 17 placas que no pasan, separado del intento numérico recuperado.

**Segundo checkpoint completo**, confirmado a 2026-10-06T05:34:31Z (00:34, Lima): 500/500 placas de 50 mV/div; ganancia y centro compensable 500/500, recorrido ±4.5 div **477/500 (95.4 %)**. Ambas cohortes completas superan el mínimo del 95 %, pendiente de auditoría global. A 05:46:20Z hay 1 152/2 000 casos terminados, incluidos 152/500 de 0.5 V/div, sin otro intento nativo fallido ni caso definitivamente fallido. Las 12 escalas nominales originales también cumplen C1/C2/C3 y error de ganancia por comprobación de los resultados guardados, sin repetir simulaciones.

**Tercer checkpoint completo**, confirmado a 2026-10-06T06:13:57Z (01:13, Lima): 500/500 placas de 0.5 V/div; ganancia y centro compensable 500/500, recorrido ±4.5 div **483/500 (96.6 %)**. Hay 1 507/2 000 casos terminados, ya iniciada la última cohorte (5 V/div), sin otro fallo nativo ni caso definitivamente fallido. Estos son checkpoints; la auditoría global aún no se ejecutó.

Los resultados de la retomada se guardan separados en `CH23_entrada/S9/B_hoja/op_corregido/`. Los checkpoints anteriores describen el progreso histórico; el cierre vigente es el siguiente.

## Cierre — 6 octubre 2026, 02:00 America/Lima, Codex

- Campaña OP corregida terminada a las 01:52 Lima: **2 000/2 000 casos**, **12 000 puntos OP de referencia**, código 0, 9 291.086 s de esta reanudación, diez trabajadores y semilla 2026100371. Las cuatro cohortes de 500 placas son 5 mV/div, 50 mV/div, 0.5 V/div y 5 V/div. Ganancia y centro compensable: 500/500 en cada una.
- C9 por escala: **483/500 (96.6 %), 477/500 (95.4 %), 483/500 (96.6 %), 477/500 (95.4 %)**. Todas superan el mínimo por escala del 95 %. **Intersección de las mismas placas en las cuatro escalas: 471/500 (94.2 %)**; no afirmar rendimiento conjunto ≥95 %. Se añadió la comprobación derivada y su limitación al generador, al acta y a la respuesta final, con `resultados/s9b_c9_conjunto.json`. Requiere valoración de Claude/Keneth; no se eligió remedio.
- Auditoría OP corregida: 2 000 casos y **12 000 decks**, código 0, **cero errores**, seis estados distintos por caso y comparación de bytes contra el original tras restaurar cuatro fuentes y excluir la ruta loadbias. Guard antes/después: **26 403 archivos, cero diferencias**, incluidos resultados A, CH1 y modelos de fabricante. SHA256 del modelo permanece `4fb5d82e3319553113ba8ff7c8ff5bc4b7fa65e9a13b59dea2173140fe90d31b`.
- Contabilidad completa corregida: **12 005 intentos nativos registrados, uno fallido y recuperado** (MC189), ningún caso definitivamente fallido. Los cuatro intentos extra exitosos son puntos repetidos, no nuevas placas; no borrar ese historial ni excluir el fallo C9 de MC189. Evidencia: `resultados/s9b_op_corregido_contabilidad.json` y `S9/B_hoja/op_corregido/native_history.jsonl`.
- Smoke guardado auditado y comparado: 25/25, código 0, **cero diferencias** con tolerancias absoluta/relativa 1e-9. No se volvió a ejecutar. Original B permanece 4 295/4 295, auditoría código 0/cero errores; el metadato original conserva código 1 por modificación externa de STATE, no fallo eléctrico. No se repitieron A, K0, AC, ruido, K6 ni K4 por el cambio de offset.
- C1–C9 por los alcances de sus tablas pasan tras corregir OP y usar C8≤2 µs (decisión previa de Keneth). K4 son seis mediciones históricas compartidas de A. El generador terminó con código 0, y se regeneró sólo el informe al incorporar la intersección C9, también código 0. `ACTA_S9.md` tiene un único bloque B, las tablas hoja/original/copia y A/B_original/B_corregida, límites del modelo y consumos; `RESPUESTA_FINAL_S9_B.md` contiene la entrega. CSV nominal/calibración B contiene las 12 escalas. A histórico permanece intacto.
- Coordinador nativo terminado con código 0 (sesión 19479); no quedan etapas por lanzar. `Get-Process LTspice` no devolvió procesos visibles. La consulta CIM de líneas de comandos fue denegada por el sandbox: no se usa para afirmar el estado de procesos ajenos.
- No hubo simulaciones físicas, descargas, instalaciones, commits ni cambios de firmware/esquema/PCB. Modelo ajustado no validado por TI; saturación/protecciones heredadas de National, sin dispersión GBW/Ib/temperatura ni ruido 1/f. No certifica silicio ni daño. Persisten la base S7b frente a S7c y U105 sin 470 Ω/BAV99. No se adopta variante LM6172 ni se cambia DECISIONS.

**Pendientes de la siguiente IA:** auditoría externa de Claude del acta, scripts/CSV y de la interpretación del **94.2 % conjunto**; decisión de Keneth sobre variante/remedio y cifras de consumo para G.3/G.4. S8b sigue separado. Arranque: leer START/STATE, este diario y `CH23_entrada/RESPUESTA_FINAL_S9_B.md`; consultar las fuentes rectoras. No repetir campañas completas para esta revisión. Actualización de STATE y sincronización de memoria se hacen después de cerrar el guard y los informes.
