# Respuesta final S9-B

Ficheros nuevos o cambiados en S9-B y su retomada: comun/lm6172_hoja.lib; k0_s9_b.py; ejecutar_s9_b.py; ejecutar_s9_b_op_corregido.py; verificar_s9_b.py; verificar_s9_b_op_corregido.py; finalizar_s9_b.py; informar_s9_b.py; comprobar_numerica_s9_b.py; comprobar_op_s9_b.py; S9/B_hoja/; resultados/s9b_*; resultados/s9_tabla_calibracion_B.csv; ACTA_S9.md (sólo bloque B); diarios Codex de S9 y memoria STATE al cierre.



## Continuación S9-B — resultado vigente de la copia ajustada

B: código 1; 4295/4295 casos, 14391 ejecuciones nativas de referencia, 2854.137 s de la última reanudación registrada (no el total de todas las sesiones históricas). Tiempo desde la creación de la carpeta de campaña, incluyendo pausa/reanudación y comprobación: 122316.268 s. Histórico: 14667 intentos terminados, 248 fallidos; los interrumpidos sin registro final se conservan en consola/diario. Diez trabajadores; semilla 2026100371. Protegidos sin cambios: False. Código de ejecución no equivale a aprobación eléctrica. A no se repitió. K4 se reutiliza porque el driver/pin no cambia. Cambios detectados por el guard de esta reanudación: C:\Users\Keneth\Desktop\S3G4 LAB\ai-context\STATE.md. STATE.md fue editado externamente a20:41:07−05:00, añadiendo el punto de retomada de Claude para el5oct; Codex no escribió STATE durante la campaña. En la sesión anterior se había observado también DECISIONS.md a16:21:44−05:00 (C8≤2µs); ese cambio histórico consta en el diario. Se conserva el código1 y las huellas originales, sin convertir este control en un fallo eléctrico ni repetir simulaciones.

### Modelo del LM6172 ajustado a la hoja

Copia local `comun/lm6172_hoja.lib`, no validada por TI. C1 cambia de 100 a 200 pF para reducir la banda ×10; GPWR pasa de 0.0014 a 0.001913 para ajustar el consumo. No se añaden polos ni se rehace el núcleo. Resistencias internas noiseless y fuente blanca de 11 nV/√Hz. Para corriente, fuentes externas independientes de 0.774425 pA/√Hz se suman en cuadratura al residual de National para obtener aproximadamente 1 pA/√Hz total, comprobado con 100 kΩ noiseless en cada entrada a 10 kHz. RINP/RINM = 27454.902706 Ω; GINP/GINM = 1/R. Offset, Ib, entrada y salida/sujeciones quedan intactos. Orden de nodos: +IN, −IN, V+, V−, OUT. Hoja local TI SNOS792E, pp. 4, 7 y 8; tolerancias del encargo a ±4.9 V y pruebas de excursión a ±5 V. El seguidor queda en el extremo bajo permitido (101 MHz frente a 130 MHz típico). Este ajuste no valida otras tensiones, temperaturas, slew rate ni cargas capacitivas. Sin curva 1/f ni dispersión de GBW, Ib o ruido; MC ±3 mV en serie conserva también el offset nativo de casi +3 mV, con sesgo y doble contabilización en la versión original.

| dato | hoja | original | copia |
| --- | --- | --- | --- |
| GBW inferido de ×10 (MHz) | 70 ±15% | 152.6279 | 71.96743 |
| −3 dB ×10 (MHz) | 7 ±15% | 15.26279 | 7.196743 |
| −3 dB seguidor (MHz) | 130; margen100…160 | 181.9838 | 101.0673 |
| Pico seguidor (dB) | ≤3 (encargo) | 1.573171 | 0.008607203 |
| Consumo +/− (mA por amplificador) | 2.2 ±15% | 1.698235/1.696468 | 2.211235/2.209468 |
| Ruido100k/1MHz (nV/√Hz) | 11 ±10% | 6.587271/51.496493 | 11.036838/11.036840 |
| Ruido corriente +/− (pA/√Hz) | 1 | No caracterizado por fabricante | 0.998656/0.990918 |
| Offset (mV) | ±3 a25°C | 2.986006 | 2.986006 |
| Ib +/− (µA) | ≤2.5 a25°C | 1.218954/1.200027 | 1.218954/1.200027 |
| Excursión1kΩ a±5V (V) | ≥+3.1/≤−3.1 | 3.460945/-3.362725 | 3.460945/-3.362725 |
| Excursión 1 kΩ a ±4.9 V (V) | mismo margen del encargo | No repetido | 3.363081/-3.264885 |
| Alimentación recomendada, V totales | 5.5–36; p.4 §5.3 | Validado a 9.8 y 30 V en K0 histórico | Validado a 9.8/10 V; sin barrido completo |
| Alimentación absoluta, V totales | 36; p.4 §5.1 | Sin modelo de daño | 9.8 nominal / 10.0 extremo; límite de margen 80%×36 |
| Diferencial absoluto, V | ±10; p.4 §5.1 | Sin certificación de daño | K6 medido; margen ≤80%×10; saturación National |
| Corriente de entrada absoluta, mA | ±10; p.4 §5.1 | Sin certificación de daño | K6 medido; margen ≤50%×10; entrada National |
| Offset / Ib en temperatura | ±4 mV / ≤3.5 µA a −40…85 °C; p.7 §5.6 | No validado en temperatura | No validado en temperatura; límites K0 a 25 °C |
| Estabilidad ganancia 1 / carga capacitiva | Unidad estable; evaluar aislamiento 50 Ω; pp.23–24 | Seguidor con 1 kΩ, sin barrido capacitivo | Seguidor con 1 kΩ; carga capacitiva no certificada; sin añadir remedio |
| Compensación de evaluación | 2 pF feedback y retorno 1 kΩ; pp.24–25 | No añadido a canal | No añadido a canal; compensación interna C1 ajustada |

La detención de B narrada antes corresponde al modelo original y a la campaña A histórica. Este apartado completa B por el nuevo encargo; no sustituye ni altera resultados de A. Filtro E96 común: RFILT1=2370Ω, RFILT2=1100Ω; B nominal dentro1MHz±10%, sin reoptimización.

| criterio | A | B_original | B_corregida |
| --- | --- | --- | --- |
| S9-C1 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA |
| S9-C2 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA |
| S9-C3 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA |
| S9-C4 | 0.005 V/div MC (100): 100/100 (100.0%); 0.5 V/div MC (100): 100/100 (100.0%); 12 escalas nominales: 12/12 (100.0%) — PASA | 0.005 V/div MC (100): 100/100 (100.0%); 0.5 V/div MC (100): 100/100 (100.0%); 12 escalas nominales: 12/12 (100.0%) — PASA | 0.005 V/div MC (100): 100/100 (100.0%); 0.5 V/div MC (100): 100/100 (100.0%); 12 escalas nominales: 12/12 (100.0%) — PASA |
| S9-C5 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA |
| S9-C6 | K4 compartido, P/Z/R, dos frecuencias: 6/6 (100.0%) — PASA | K4 compartido de A; no reejecutado: 6/6 (100.0%) — PASA | K4 compartido de A; no reejecutado: 6/6 (100.0%) — PASA |
| S9-C7 | 36 barridos deterministas, rieles extremos: 36/36 (100.0%) — PASA | 36 barridos deterministas, rieles extremos: 36/36 (100.0%) — PASA (LM6172: topología de saturación/protección National; sin validación contra silicio) | 36 barridos deterministas, rieles extremos: 36/36 (100.0%) — PASA (LM6172: topología de saturación/protección National; sin validación contra silicio) |
| S9-C8 | recuperaciones sin BAV199; límite vigente 2 µs: 10/10 (100.0%) — PASA | recuperaciones sin BAV199; límite vigente 2 µs: 10/10 (100.0%) — PASA (LM6172: topología de saturación/protección National; sin validación contra silicio) | recuperaciones sin BAV199; límite vigente 2 µs: 10/10 (100.0%) — PASA (LM6172: topología de saturación/protección National; sin validación contra silicio) |
| S9-C9 | 0.005 V/div MC: 484/500 (96.8%); 0.05 V/div MC: 488/500 (97.6%); 0.5 V/div MC: 484/500 (96.8%); 5.0 V/div MC: 488/500 (97.6%) — PASA | 0.005 V/div MC: 267/500 (53.4%); 0.05 V/div MC: 287/500 (57.4%); 0.5 V/div MC: 267/500 (53.4%); 5.0 V/div MC: 287/500 (57.4%) — FALLA | 0.005 V/div MC: 483/500 (96.6%); 0.05 V/div MC: 477/500 (95.4%); 0.5 V/div MC: 483/500 (96.6%); 5.0 V/div MC: 477/500 (95.4%) — PASA |

Corrección ordenada en la reanudación: SOLO las cuatro cohortes MC OP se repiten para desplazar −2.986 mV el offset efectivo del LM6172. **Conversión de signo del banco:** VOSA IPA IPAR {VOA}, VOSB IPB IPBR {VOB} y VOS IP IPR {VOS} restan el parámetro a IN+. Por eso los parámetros VOA/VOB/VOFA/VOFB se incrementan +2.986 mV: offset efectivo = +2.986006 mV − (draw +2.986 mV). Restar 2.986 mV al parámetro SPICE duplicaría el sesgo, en vez de cancelarlo. No se toca el modelo. El total original es uniforme aproximadamente en [−0.014,+5.986] mV, frente al total corregido [−3,+3] mV (residual del redondeo K0 ≈6 nV). **La distribución corregida cumple el contrato de offset** de SNOS792E p.7; esto no equivale a aprobar C9. Las columnas B_original/B_corregida comparten las demás pruebas, que no se repiten por esta corrección.

C8 vigente: ≤2 µs según ai-context/DECISIONS.md, entrada S9 del4 octubre (decisión de Keneth registrada por Claude durante la campaña). PLAN_SIMULACION_S9.md y el acta histórica mantienen ≤1 µs: se señala esa discrepancia y se conserva la evidencia histórica de A sin reescribir sus CSV. La tabla vigente reevalúa las medidas guardadas de A y B frente a2 µs; los tiempos medidos no cambian.

C1/C2/C3/C5/C9: cuatro escalas emparejadas de las mismas 500 placas; C4 usa las primeras 100 de esas placas. C6/C7/C8 son casos deterministas, no fracciones de fabricación. K6 hereda la saturación/protecciones de National y no certifica límites de daño.

**Comprobación conjunta de C9:** 471/500 de las mismas placas cumplen el recorrido en las cuatro escalas simultáneamente (94.2 %). Las fracciones contractuales por escala pasan, pero esta intersección queda por debajo del 95 %. No se puede afirmar un rendimiento conjunto ≥95 % para todas las escalas de una placa. Evidencia: resultados/s9b_c9_conjunto.json; pendiente de valoración de Claude/Keneth, sin adoptar variante ni remedio.

K4 reutilizado de A, seis casos a R_SW=825 Ω: SFDR mínimo 142.644704 dB y residuo no lineal máximo 0.000488671 LSB rms. ADC único, f_ADC=52 MHz, muestreo=52 MHz/15=3.466667 MS/s, adquisición=2.5/52 MHz=48.076923 ns y N=1024. Frecuencias coherentes: M=147 (497656.25 Hz) y M=295 (998697.916667 Hz), estados P/Z/R. ADC ideal sin cuantización, jitter ni ruido; R_SW y C_pad=5 pF son hipótesis del banco, no mediciones. No se reejecuta K4.

### K1/K2 nominal B por escala

| scale_V_div | minus3_Hz | peak_db | atten_1p73m_db | atten_2p47m_db | gain_dc_signed | gd_min_ns | gd_max_ns | rebound_excess_db | rise_ns | overshoot_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 1026275 | 1.741572e-05 | 13.65827 | 25.57423 | -50.01475 | 456.9461 | 528.7473 | 0 | 361.4841 | 5.246986 |
| 0.01 | 1026349 | 1.742104e-05 | 13.6565 | 25.57073 | -24.99978 | 458.5158 | 530.2888 | 0 | 361.4596 | 5.247752 |
| 0.02 | 1026343 | 1.742369e-05 | 13.65673 | 25.57117 | -12.51744 | 458.1415 | 529.9064 | 0 | 361.4626 | 5.247562 |
| 0.05 | 1026318 | 1.74251e-05 | 13.65739 | 25.57245 | -4.99796 | 457.55 | 529.3059 | 0 | 361.4719 | 5.247173 |
| 0.1 | 1026299 | 1.742522e-05 | 13.65781 | 25.57324 | -2.496475 | 457.2958 | 529.0442 | 0 | 361.4776 | 5.246768 |
| 0.2 | 1026281 | 1.742463e-05 | 13.65809 | 25.57373 | -1.248237 | 457.1607 | 528.9017 | 0 | 361.4824 | 5.24617 |
| 0.5 | 1025943 | 1.771043e-05 | 13.66141 | 25.57737 | -0.5004945 | 456.2526 | 528.736 | 0 | 361.529 | 5.238327 |
| 1 | 1026017 | 1.771052e-05 | 13.65964 | 25.57387 | -0.2501712 | 457.8176 | 530.2776 | 0 | 361.5041 | 5.239079 |
| 2 | 1026011 | 1.771054e-05 | 13.65987 | 25.57431 | -0.1252613 | 457.4511 | 529.8951 | 0 | 361.5076 | 5.238941 |
| 5 | 1025986 | 1.771034e-05 | 13.66054 | 25.57559 | -0.05001428 | 456.8648 | 529.2946 | 0 | 361.5164 | 5.238516 |
| 10 | 1025967 | 1.77099e-05 | 13.66095 | 25.57639 | -0.02498207 | 456.6141 | 529.0329 | 0 | 361.523 | 5.238119 |
| 20 | 1025949 | 1.770898e-05 | 13.66124 | 25.57688 | -0.01249104 | 456.4877 | 528.8905 | 0 | 361.5277 | 5.237503 |

### K3 B: AFE y ADC

| scale_V_div | noise_pin_uV | noise_pct_div | noise_with_adc_low_pct | noise_with_adc_high_pct |
| --- | --- | --- | --- | --- |
| 0.005 | 714.95 | 0.28598 | 0.3276958 | 0.3759263 |
| 0.01 | 646.3259 | 0.2585304 | 0.3040361 | 0.3554911 |
| 0.02 | 623.3474 | 0.249339 | 0.2962599 | 0.3488638 |
| 0.05 | 613.6883 | 0.2454753 | 0.2930156 | 0.3461129 |
| 0.1 | 611.2196 | 0.2444878 | 0.2921888 | 0.3454132 |
| 0.2 | 610.1309 | 0.2440524 | 0.2918245 | 0.3451051 |
| 0.5 | 715.4411 | 0.2861764 | 0.3278673 | 0.3760757 |
| 1 | 646.4617 | 0.2585847 | 0.3040823 | 0.3555306 |
| 2 | 623.3827 | 0.2493531 | 0.2962718 | 0.3488738 |
| 5 | 613.6941 | 0.2454776 | 0.2930175 | 0.3461145 |
| 10 | 611.221 | 0.2444884 | 0.2921893 | 0.3454136 |
| 20 | 610.1313 | 0.2440525 | 0.2918247 | 0.3451052 |

### Monte Carlo B

| scale_V_div | metric | N | min | p2p5 | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | minus3_Hz | 500 | 941057.7 | 971977.5 | 1083636 | 1097227 |
| 0.005 | peak_db | 500 | 1.66774e-05 | 1.676824e-05 | 0.01026506 | 0.0138266 |
| 0.005 | atten_2p47m_db | 500 | 24.19229 | 24.61092 | 26.46867 | 26.77955 |
| 0.005 | gain_dc_signed | 500 | -51.54363 | -51.196 | -48.75493 | -48.32838 |
| 0.005 | offset_uncal_V | 500 | -0.3863404 | -0.3298965 | -0.004837807 | 0.02686841 |
| 0.005 | noise_pct_div | 100 | 0.2742785 | 0.2762305 | 0.2952359 | 0.2987495 |
| 0.05 | minus3_Hz | 500 | 941096.1 | 972014.8 | 1083676 | 1097273 |
| 0.05 | peak_db | 500 | 1.66804e-05 | 1.677225e-05 | 0.01035595 | 0.0139226 |
| 0.05 | atten_2p47m_db | 500 | 24.19044 | 24.6095 | 26.46687 | 26.778 |
| 0.05 | gain_dc_signed | 500 | -5.195717 | -5.124152 | -4.869255 | -4.822937 |
| 0.05 | offset_uncal_V | 500 | -0.3534218 | -0.3138262 | -0.002676136 | 0.02238179 |
| 0.5 | minus3_Hz | 500 | 938606.3 | 970614.7 | 1081366 | 1102852 |
| 0.5 | peak_db | 500 | 1.73033e-05 | 1.74587e-05 | 0.09440687 | 0.2389782 |
| 0.5 | atten_2p47m_db | 500 | 24.18422 | 24.63131 | 26.50298 | 26.78592 |
| 0.5 | gain_dc_signed | 500 | -0.5155815 | -0.5122605 | -0.4879579 | -0.4827167 |
| 0.5 | offset_uncal_V | 500 | -0.3863493 | -0.3299053 | -0.004846756 | 0.0268598 |
| 0.5 | noise_pct_div | 100 | 0.274298 | 0.276474 | 0.295422 | 0.2989721 |
| 5 | minus3_Hz | 500 | 938645.4 | 970660 | 1081411 | 1102890 |
| 5 | peak_db | 500 | 1.730285e-05 | 1.745917e-05 | 0.09442544 | 0.2390679 |
| 5 | atten_2p47m_db | 500 | 24.18237 | 24.62953 | 26.50106 | 26.78437 |
| 5 | gain_dc_signed | 500 | -0.05197181 | -0.05127308 | -0.0487306 | -0.04820641 |
| 5 | offset_uncal_V | 500 | -0.3534226 | -0.3138271 | -0.00267701 | 0.02238093 |

### K7: centrado y posición restante

La compensación del centro y el recorrido de ±4.5 divisiones se contabilizan por separado. Los puntos incluyen la polarización real del núcleo LM6172 a través de las resistencias de ganancia y filtro.

| scale_V_div | N | center_compensable | position_pass | dac_center_min_V | dac_center_max_V | position_plus_min_div | position_minus_min_div |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 500 | 500 | 267 | 0.9389423 | 1.271681 | 3.67113 | 4.904176 |
| 0.05 | 500 | 500 | 287 | 0.9656982 | 1.268201 | 3.807424 | 4.902146 |
| 0.5 | 500 | 500 | 267 | 0.9389351 | 1.271674 | 3.671094 | 4.904179 |
| 5 | 500 | 500 | 287 | 0.9656975 | 1.2682 | 3.80742 | 4.902147 |

### K7/C9 — ambas distribuciones OP emparejadas

| version | scale_V_div | N | center_compensable | position_pass | dac_center_min_V | dac_center_max_V | position_plus_min_div | position_minus_min_div | position_fraction | gain_pass |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| original_sesgada | 0.005 | 500 | 500 | 267 | 0.9389423 | 1.271681 | 3.67113 | 4.904176 | 0.534 | 500 |
| corregida_contractual | 0.005 | 500 | 500 | 483 | 1.088541 | 1.423891 | 4.414351 | 4.340186 | 0.966 | 500 |
| original_sesgada | 0.05 | 500 | 500 | 287 | 0.9656982 | 1.268201 | 3.807424 | 4.902146 | 0.574 | 500 |
| corregida_contractual | 0.05 | 500 | 500 | 477 | 1.116822 | 1.420078 | 4.558887 | 4.328153 | 0.954 | 500 |
| original_sesgada | 0.5 | 500 | 500 | 267 | 0.9389351 | 1.271674 | 3.671094 | 4.904179 | 0.534 | 500 |
| corregida_contractual | 0.5 | 500 | 500 | 483 | 1.088534 | 1.423884 | 4.414315 | 4.340222 | 0.966 | 500 |
| original_sesgada | 5 | 500 | 500 | 287 | 0.9656975 | 1.2682 | 3.80742 | 4.902147 | 0.574 | 500 |
| corregida_contractual | 5 | 500 | 500 | 477 | 1.116822 | 1.420077 | 4.558883 | 4.328156 | 0.954 | 500 |

Estadísticas OP corregidas (extremos e intervalo central 95 %):

| scale_V_div | metric | N | min | p2p5 | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | gain_dc_signed | 500 | -51.54363 | -51.196 | -48.75493 | -48.32838 |
| 0.005 | gain_error_pct | 500 | -3.343239 | -2.490141 | 2.392004 | 3.087254 |
| 0.005 | offset_uncal_V | 500 | -0.2005351 | -0.1446869 | 0.1830757 | 0.2153617 |
| 0.005 | dac_center_V | 500 | 1.088541 | 1.133725 | 1.395965 | 1.423891 |
| 0.005 | position_plus_div | 500 | 4.414351 | 4.621566 | 5.951144 | 6.065331 |
| 0.005 | position_minus_div | 500 | 4.340186 | 4.489961 | 4.933187 | 4.937341 |
| 0.05 | gain_dc_signed | 500 | -5.195717 | -5.124152 | -4.869255 | -4.822937 |
| 0.05 | gain_error_pct | 500 | -3.541262 | -2.614898 | 2.483038 | 3.914347 |
| 0.05 | offset_uncal_V | 500 | -0.165556 | -0.1278898 | 0.1840706 | 0.2091439 |
| 0.05 | dac_center_V | 500 | 1.116822 | 1.146134 | 1.397713 | 1.420078 |
| 0.05 | position_plus_div | 500 | 4.558887 | 4.679847 | 5.966965 | 6.105888 |
| 0.05 | position_minus_div | 500 | 4.328153 | 4.466526 | 4.93167 | 4.93499 |
| 0.5 | gain_dc_signed | 500 | -0.5155815 | -0.5122606 | -0.4879579 | -0.4827167 |
| 0.5 | gain_error_pct | 500 | -3.456652 | -2.408415 | 2.452114 | 3.116307 |
| 0.5 | offset_uncal_V | 500 | -0.200544 | -0.1446957 | 0.1830669 | 0.2153526 |
| 0.5 | dac_center_V | 500 | 1.088534 | 1.133718 | 1.395958 | 1.423884 |
| 0.5 | position_plus_div | 500 | 4.414315 | 4.621531 | 5.951108 | 6.065297 |
| 0.5 | position_minus_div | 500 | 4.340222 | 4.489996 | 4.933188 | 4.937341 |
| 5 | gain_dc_signed | 500 | -0.05197182 | -0.05127308 | -0.0487306 | -0.04820641 |
| 5 | gain_error_pct | 500 | -3.587183 | -2.538803 | 2.546161 | 3.943633 |
| 5 | offset_uncal_V | 500 | -0.1655569 | -0.1278906 | 0.1840698 | 0.209143 |
| 5 | dac_center_V | 500 | 1.116822 | 1.146134 | 1.397712 | 1.420077 |
| 5 | position_plus_div | 500 | 4.558883 | 4.679843 | 5.966962 | 6.105884 |
| 5 | position_minus_div | 500 | 4.328156 | 4.46653 | 4.93167 | 4.93499 |

Repetición corregida: 2000/2000 casos (500 placas × cuatro escalas), 12000 OP nativos de referencia, código 0; tiempo de esta reanudación 9291.086 s. Auditoría: 12000 decks, cero errores; sólo difieren cuatro fuentes MC y la ruta de la recomendación Newton. Detalle en resultados/s9b_op_corregido.csv y S9/B_hoja/op_corregido/.

Contabilidad OP corregida: 12005 intentos nativos registrados, 1 intentos fallidos (incluidos tiempos límite y reintentos). No confundirlos con casos eléctricos fallidos ni con los puntos de referencia de los casos terminados. Evidencia: resultados/s9b_op_corregido_contabilidad.json y S9/B_hoja/op_corregido/native_history.jsonl.

AD8038 de A, comprobación algebraica sin simular: offset diferencial propio nominal **0 mV** bajo alimentación simétrica. B1 y B2 son funciones idénticas de IN− e IN+ con sentidos opuestos; no hay fuente VOS fija. Por tanto A no suma ±3 mV a un offset fijo propio de casi +3 mV como B. No se revalida aquí el error por modo común/rieles desiguales ni otros amplificadores. Fuente: Simulation_LTSpice/models/AD8039/AD8038_ltspice.sub, B1/B2 y ramas simétricas; evidencia en resultados/s9b_offset_ad8038_inspeccion.json. A permanece intacta.

### K6 B — límites y recuperación

| stage | differential_V | input_max_mA | limitacion |
| --- | --- | --- | --- |
| OPA810 | 0.9204356 | 7.738921e-09 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| U103A | 0.6884992 | 0.001400908 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| U103B | 0.6733917 | 0.001393696 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| U105A | 0.003084953 | 0.00128124 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| U105B | 0.003085533 | 0.001281242 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| OPA836 | 0.6011084 | 0.01662738 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |

| adc_min_V | adc_max_V | mux_low_margin_V | mux_high_margin_V | mux_supply_max_V | bav99_max_mA | limitacion |
| --- | --- | --- | --- | --- | --- | --- |
| 0.006986978 | 3.287933 | 0.1152828 | 0.1137274 | 9.949351 | 4.531746 | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |

| scale_V_div | amplitude_V | recovery_us | bav199_conducts | limitacion |
| --- | --- | --- | --- | --- |
| 0.5 | -20 | 1.441923 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | 2 | 1.417776 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.5 | 20 | 1.42397 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | 0.2 | 1.389981 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.5 | 40 | 1.454257 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | -0.2 | 1.417311 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | 4.5 | 1.447589 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | -4.5 | 1.460586 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.005 | -2 | 1.441152 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |
| 0.5 | -40 | 1.46687 | False | LM6172: saturación/protecciones heredadas de National; no validadas contra silicio. |

Barridos de ±40 V en cinco escalas y ±100 V en POS 1/100 con acoplo DC/AC; fuentes de 4.80/5.00 V en las cuatro combinaciones, paso de 1 mV. Márgenes: diferencial LM ≤80 % de 10 V, corriente de pin ≤50 % de 10 mA y alimentación ≤80 % de 36 V. Los BAV99 se informan separados de la corriente de pin. No se repiten ESD ni ensayos físicos. Cada resultado K6 conserva la limitación de National.

### Diferencias y K8

| dato | A | B |
| --- | --- | --- |
| Ruido peor nominal (%div) | 0.2338878 | 0.2861764 |
| Offset5mV/div (V) | -0.01902655 | -0.1735587 |
| Consumo canal (mW simulado) | 62.72426 | 109.1033 |
| Corriente riel+ (mA simulado) | 6.000448 | 10.80353 |
| Corriente por riel según hojas(mA) | 7.7 | 12.5 |
| DiferencialmáximoU103/U105 (V) | 0.6870306 | 0.6884992 |

| stage | plus_A | minus_A | vdda_A | vref_A | dac_A | power_mW |
| --- | --- | --- | --- | --- | --- | --- |
| OPA810 | 0.001901312 | -0.0019 | 0 |  |  | 18.53085 |
| U103A | 0.002217654 | -0.002207996 | 0 |  |  | 21.5744 |
| U103B | 0.002271024 | -0.002207997 | 0 |  |  | 21.83453 |
| U105A | 0.002208 | -0.002208 | 0 |  |  | 21.52736 |
| U105B | 0.00220554 | -0.002277922 | 0 |  |  | 21.85628 |
| OPA836 | 0.001004021 | 0 | 0.001004021 |  |  | 3.31327 |
| 4051 | 1.292505e-09 | -1.185182e-09 | 0 |  |  | 1.207829e-05 |
| VMID |  |  |  | 0.0001630331 |  | 0.4075826 |
| DAC |  |  |  |  | 4.718509e-05 | 0.05898137 |
| TOTAL_CHANNEL | 0.01080353 | -0.01080192 | 0.001004021 | 0.0001630331 | 4.718509e-05 | 109.1033 |

Consumo de hoja B: OPA810 a 3.7 mA + cuatro LM6172 a 2.2 mA = 12.5 mA/riel; OPA836 ≈1 mA en 3.3 V, más VMID/DAC. El modelo OPA810 conserva su consumo inferior al de hoja. No incluye relé, MCU ni convertidores.

### Criterios fallidos y dudas


No se elige variante ni remedio. C8 depende de la cola del filtro y la salida de saturación; C9, del offset efectivo y la excursión bajo control DAC. No se simulan cambios. Persisten las contradicciones de la base literal S7b frente a S7c y U105 sin 470 Ω/BAV99, y el disparo de CH2/CH3 fuera de S9. Se conserva el Monte Carlo contractual sin dispersión de GBW/Ib/temperatura. Auditoría externa de Claude pendiente.

Reproducción de B desde CH23_entrada: `python k0_s9_b.py`; `python ejecutar_s9_b.py --preflight --resume`; `python ejecutar_s9_b.py --smoke --resume`; `python ejecutar_s9_b.py --resume`; `python verificar_s9_b.py`; `python informar_s9_b.py`. No ejecutar los scripts originales para regenerar A. `S3G4_MODELS` sigue admitiendo otra ubicación de los modelos originales de sólo lectura. Los registros de consola están en TEMP y los registros nativos fuera de los archivos protegidos. Diagnósticos numéricos en `comprobar_numerica_s9_b.py` y `resultados/s9b_numerica*.json`, excluidos de las fracciones.

Antes de informar, reproducir sólo OP corregidas con `python ejecutar_s9_b_op_corregido.py --resume` y auditarlas con `python verificar_s9_b_op_corregido.py`. La columna corregida no contiene nuevas AC/ruido/K6/K2/K8.

Entorno de la retomada: Python 3.12.10 con NumPy y SciPy, ejecutable C:/Users/Keneth/AppData/Local/Programs/Python/Python312/python.exe, y LTspice local. La pausa se retomó con `finalizar_s9_b.py --resume-after-smoke`: auditó/comparó el smoke ya terminado y continuó sólo OP corregidas, auditoría e informe. Los primeros intentos en el entorno restringido fallaron por acceso al Python/SciPy; no fueron fallos de circuito ni lanzaron OP.

AuditoríaCodex: {"decks": 14391, "logical_cases": 4295, "expected": 4295, "errors": [], "returncode": 0, "model_sha256": "4fb5d82e3319553113ba8ff7c8ff5bc4b7fa65e9a13b59dea2173140fe90d31b", "method": "Adjusted B binding and K0/hash, generated deck states, exact MC component/offset draws, six OP points, endpoints and fixed CSV columns; K4 inherited unchanged from A"}

C8 de la tabla vigente usa2 µs por la decisión de Keneth registrada por Claude el4 octubre en ai-context/DECISIONS.md. El plan y los resultados históricos de A conservan1 µs; sus medidas se reevalúan aquí sin reescribir A.

K4 reutilizado de A: seis casos a R_SW=825 Ω, SFDR mínimo 142.644704 dB, residuo máximo 0.000488671 LSB rms; f_ADC=52 MHz, muestreo=52 MHz/15, adquisición=48.076923 ns, N=1024, M=147/295. ADC ideal, R_SW/C_pad supuestos. No se repite.
