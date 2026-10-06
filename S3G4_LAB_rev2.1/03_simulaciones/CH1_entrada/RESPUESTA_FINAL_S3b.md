# Respuesta final S3b

Creado: `comun/ch1_comun_s3b.inc`, `ejecutar_s3b.py`, `S3b/` (.cir y .log), `resultados/s3b_*` (CSV, JSON, resumen y registros), `ACTA_S3b.md`, este resumen y `ai-context/journal/2026-10-03-1619-codex-s3b.md`. Auxiliares: `generar_respuesta_s3b.py` y `verificar_reproduccion_s3b.py`.

Campaña completa: **código 0, 162 simulaciones, 449.605 s**, diez trabajadores; 0 errores y 0 advertencias. Controles previos: código 0, 6 simulaciones, 16.017 s. Smoke: código 0, 66 simulaciones, 198.970 s. El código informa ejecución; las fallas eléctricas son resultados válidos.

B0 (U103A aislada):

| variante | ganancia_DC | corte_MHz | pico_dB |
| --- | --- | --- | --- |
| A | 4.999440 | 32.189 | 8.362 |
| B | 4.999119 | 24.164 | 8.349 |
| C | 4.999510 | 63.750 | 2.264 |
| D | 4.999245 | 48.549 | 2.238 |

Control de ruido sin protección: original: **0.644338 % div**, sheet: **0.396130 % div**.

Criterios S3b-C1…C6:

| variante | C1 | C2 | C3 | C4 | C5 | C6 |
| --- | --- | --- | --- | --- | --- | --- |
| A | PASA | CONDICIONAL | PASA | FALLA | PASA | PASA |
| B | PASA | CONDICIONAL | PASA | FALLA | PASA | PASA |
| C | PASA | PASA | PASA | FALLA | FALLA | PASA |
| D | PASA | PASA | PASA | FALLA | FALLA | PASA |

Pasan todo: **ninguna variante**. No se elige variante.

Fallas cuantificadas (C4 exige también B0):

| variante | pico_B1_dB | exceso_C4_B0_dB | recuperacion_us | exceso_C5_us |
| --- | --- | --- | --- | --- |
| A | 6.351324 | 7.862275 | 0.276770 | 0.000000 |
| B | 6.876054 | 7.849011 | 0.359135 | 0.000000 |
| C | 0.000018 | 1.763649 | 1.108423 | 0.108423 |
| D | 0.000018 | 1.738001 | 1.155029 | 0.155029 |

B3: máximos sobre ambas escalas y todo el barrido; ruido máximo en las 12 escalas:

| variante | dif_U103A_V | dif_U103B_V | I_4051_mA | I_Dp_mA | I_Dn_mA | I_OPA810_mA | ruido_max_pct_div |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.293351 | 3.547736 | 4.921832 | 4.589206 | 4.921544 | 9.777950 | 0.414363 |
| B | 0.275697 | 3.531148 | 2.934984 | 2.768895 | 2.934738 | 7.803576 | 0.437762 |
| C | 0.843716 | 3.558081 | 4.206455 | 3.882732 | 4.206208 | 9.066798 | 0.408975 |
| D | 0.816934 | 3.545812 | 2.517299 | 2.371519 | 2.517089 | 7.388841 | 0.423489 |

B6: offset **añadido frente a S3**, en divisiones:

| variante | 5mV_25C_div | 5mV_70C_div | 200mV_25C_div | 200mV_70C_div |
| --- | --- | --- | --- | --- |
| A | -9.3336366e-07 | -1.1195266e-05 | -2.347615e-08 | -2.8789803e-07 |
| B | -1.8936423e-06 | -1.952973e-05 | -4.7439636e-08 | -4.959241e-07 |
| C | -7.0868438e-07 | -8.3574259e-07 | -1.7685038e-08 | -2.086072e-08 |
| D | -1.507759e-06 | -1.7780781e-06 | -3.7625741e-08 | -4.4382066e-08 |

Dudas: C2 de A/B es condicional por falta de hoja local BAT54S Vishay; el modelo declara Iave=300 mA. El AD8038 no modela Ib real ni deriva, y los pares de diodos no modelan desajuste; el pequeño B6 no garantiza offset de placa. B0 usa la carga aislada de S3 (1 kΩ ∥ 10 pF); B1 conserva la cadena real, por eso se informan por separado. Se mantienen las contradicciones documentales y los valores derivados de S2b; sin compensaciones nuevas, selección de variante, descargas ni ensayos físicos. Archivos protegidos comprobados: 21318; cambios: [].

Reejecución en ruta corta con S3G4_MODELS: código 0, 162 simulaciones, 549.250 s; **10/10 CSV idénticos byte a byte**.
