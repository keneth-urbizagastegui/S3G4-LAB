# Acta S9 — CH2/CH3, 1 MHz

Codex, 4 octubre 2026. Campaña A cerrada; B detenida por K0. No se adopta variante ni remedio. Sin pruebas físicas, descargas o cambios de CH1/modelos/STATE/DECISIONS.

## K0: datos de la hoja local antes de la campaña

Fuente: `datasheet - componentes/lm6172.pdf`, TI SNOS792E, diciembre 2024. Páginas del PDF y numeración impresa coinciden.

| Dato | Hoja y condición | Fuente |
| --- | --- | --- |
| Alimentación recomendada | 5.5–36 V totales | p.4, §5.3 |
| Máximo absoluto de alimentación | 36 V totales | p.4, §5.1 |
| Diferencial de entrada absoluto | ±10 V | p.4, §5.1 |
| Corriente de entrada absoluta | ±10 mA | p.4, §5.1 |
| Offset máximo | ±3 mV a 25 °C; ±4 mV a −40…85 °C | p.7, §5.6, ±5 V |
| Polarización máxima | 2.5 µA a 25 °C; 3.5 µA a −40…85 °C; típica 1.4 µA | p.7, §5.6 |
| Salida con 1 kΩ | +3.4/−3.3 V típicos; garantizada +3.1/−3.1 V a 25 °C; ±3 V en temperatura | p.7, §5.6 |
| Salida con 100 Ω | +2.9/−2.7 V típicos; +2.5/−2.4 V garantizados a 25 °C | p.7, §5.6 |
| Ruido de tensión/corriente | 11 nV/√Hz y 1 pA/√Hz a 10 kHz, ±5 V | p.8, §5.6 |
| Ruido a ±15 V | 12 nV/√Hz, 1 pA/√Hz a 10 kHz | p.6, §5.5 |
| Consumo | 4.4 mA típicos, 6 mA máx. a 25 °C, 7 mA máx. en temperatura, por dual a ±5 V; por amplificador la mitad | p.7, §5.6; p.27, §7.3.2 |
| Ancho unitario | 70 MHz a ±5 V; a ±15 V, 80 MHz SOIC/100 MHz PDIP | pp.5/7, §§5.5/5.6 |
| Seguidor −3 dB | 130 MHz a ±5 V | p.7, §5.6 |
| Estabilidad | Ganancia unidad estable; carga capacitiva puede oscilar; recomienda 50 Ω de aislamiento como evaluación inicial; no se añade | p.23, §6.1; p.24, §7.1.3 |
| Compensación | Recomienda 2 pF de realimentación en evaluación y 1 kΩ de retorno en buffer; no se añade | pp.24–25, §§7.1.2/7.1.4 |

Cabecera National: `.SUBCKT LM6172/NS 3 2 4 5 6`: **+IN −IN V+ V− OUT**. No son números de patilla del encapsulado. Seguidor en ±0.1 V: 0.102983/−0.097011 V; offset de 2.986 mV y ganancia ≈0.999974. Polarización: 1.219/1.200 µA. A ±4.9 V: consumo 1.698/1.696 mA; a ±15 V: 2.304/2.303 mA. Salida en saturación a ±5 V con 1 kΩ: +3.461/−3.363 V. ×10: 9.9971 y −3 dB en 15.263 MHz. Seguidor: −3 dB en 181.984 MHz y pico 1.573 dB; cruce unitario inferido A=H/(1−H), con carga 1 kΩ: 112.851 MHz. **El modelo antiguo no reproduce el ancho ni el consumo de la hoja actual a ±5 V**. Por la condición expresa del punto 3 del encargo, **B se detiene en K0**. Inicialmente se continuó B como comparación con limitaciones; esa interpretación se corrigió antes de la campaña completa. Las pruebas B ya ejecutadas quedan como diagnóstico histórico, excluidas de las fracciones y de la aprobación. No hay certificación de límites de daño por un macromodelo.

El modelo no tiene un ruido de entrada caracterizado como el de la hoja. Aunque LTspice genera ruido de sus componentes, el seguidor da 6.587 nV/√Hz a 100 kHz y 51.496 nV/√Hz a 1 MHz: no representa la especificación. Para K3, copia propia `comun/lm6172_s9_ruido_hoja.lib`: resistencias internas `noiseless`, resto del núcleo intacto; fuentes blancas independientes de 11 nV/√Hz y 1 pA/√Hz por entrada. Los diodos/transistores mantienen su ruido residual (<0.004 nV/√Hz a 1 MHz en el seguidor). Validación de copia: 11.03684 nV/√Hz a 100 kHz y 1 MHz, incluyendo carga de 1 kΩ. Es aproximación blanca: la hoja especifica a 10 kHz; no se inventa una curva 1/f ni una dependencia con temperatura. La copia sólo se usa en `.noise`.

Regla de margen: rieles nominales 9.8 V y extremo 10.0 V totales, ambos inferiores a 0.8×36 = 28.8 V; diferencial admisible bajo el criterio: 8 V; corriente admisible: 5 mA. K6 los comprueba, además de los límites heredados del OPA810/OPA836/4051/ADC.

## Contradicciones conservadas

- El plan cita 12 nV/√Hz del LM6172, pero la tabla de ±5 V dice 11; K3 usa la tabla aplicable, sin descargar ni sustituir hoja.
- La base S7b literal mantiene Ct2 fijo de 16 pF y Cb derivado, mientras S7c adoptó 15 pF y 1 nF+68 pF. El contrato prohíbe cambiar la entrada y ordena incluir S7b tal cual y su reparto; no se incorpora silenciosamente S7c a la topología. Se hereda la realización de entrada y su ajuste ya calculado de S7b, sin campaña ni aceptación nueva de trimmer. El porcentaje de placas S9 se refiere a esta base contractual.
- 4.9 V ±2 % da 4.802…4.998 V por fuente; K6 manda extremos redondeados 4.80/5.00 V. C_EQ de base es 8.67 pF, frente al redondeo 8.7 pF del texto.
- U105 en S7b **no lleva** 470 Ω+BAV99; §1 de S9 dice que los lleva cada etapa, pero a la vez ordena la base literal y sólo permite filtro/amplificador/muestreo. Se conserva la topología de S7b, se miden todos los diferenciales y no se añade protección como remedio.
- Offset MC: fuentes en serie uniformes ±3 mV (LM6172 p.7 máximo a 25 °C), ±3 mV AD8039, ±715 µV OPA810 y ±400 µV OPA836 (S7b). Se conserva también el offset del macromodelo, como S7b: el LM6172 ya modela casi +3 mV. Hay posible doble contabilización y sesgo de su distribución efectiva. No se modifica el modelo nativo para corregirla. No se dispersan GBW, Ib ni temperatura porque el reparto contractual S7b no lo hace; límite frente a la regla general de DECISIONS.

## Resultados

Resultados finales en la sección Campaña cerrada. Registros K0/preflight y diagnósticos históricos conservados en S9.

Diagnóstico numérico histórico de B (no campaña): gmin=1e−12, Gear/Alternate, itl4=1000. El valor 1e−16 sugerido por National produjo pasos patológicos en el mux. K0 con 0/±0.1 V comprobó cambio ≤0.814 pA en Ib y ≤40.020 pV en salida entre ambos gmin (`s9_k0_gmin.json`). Ensayos Normal/Trap y Normal/Gear agotaron 90 s. Con abstol=1e−10, los diagnósticos −0.2/−40 V terminaron en 24.912/28.438 s; recuperación 1.358298/1.412050 µs. El cambio de recuperación de −0.2 V frente a abstol=1e−12 fue 1.010 ns. No se añadieron cshunt, parásitas ni componentes. B queda detenida por K0; estas pruebas no la califican.

## Puerta K0 y recomendaciones iniciales

El runner de campaña filtra B por la condición del punto 3 del encargo. El preflight y los registros B previos permanecen identificados por variante; no entran en las tablas de campaña ni en sus estadísticas. El CSV de calibración B quedará sin filas con una nota de no evaluación. No se elige una variante de diseño.

Para las tomas nominales sin bias S7b histórico, se genera una copia propia de .nodeset de toma 0 con permutación de los nodos iniciales de la rama SWI1 y del decodificador hacia la toma real. Es sólo una recomendación a Newton: el circuito conserva CODE, fuentes y valores reales. Se guarda la copia en S9, sin tocar CH1. Las doce escalas K1/K3 ya se ejecutaron correctamente. AMP_S9_SELECT se compila en el generador hacia exactamente un amplificador real; LTspice 26 rechazó .if en la jerarquía del subcircuito. No hay una segunda instancia inactiva cargando la red.


## Campaña cerrada

Código **0**; **14451 ejecuciones nativas de referencia**, **4313/4313 casos lógicos**, **6074.026 s** de sesiones finalizadas de campaña (sin huellas iniciales ni sesiones interrumpidas), 10 trabajadores, semilla 2026100371. Histórico: 14462 intentos terminados registrados, 17 fallidos de depuración; suma de tiempos de procesos paralelos 58811.348 s, no tiempo de pared. Interrupciones en console/diario. Código 0 significa ejecución completa, no aprobación eléctrica. Cambios protegidos: [].

La ejecución completa original devolvió código 1 tras 5989.700 s: detectó modificaciones externas de STATE.md y DECISIONS.md, conservadas con huellas antes/después en `S9/campaign/guard_concurrencia_2026-10-04/`. CH1 y modelos permanecieron idénticos. El código actual corresponde a reanudación y revisión de una nueva ventana sin modificar esos archivos; se reutilizan los mismos resultados.

Auditoría Codex: código 0, 14409 decks y 4313 casos verificados; 0 errores. Auditoría externa de Claude pendiente.

| criterio | A | B |
| --- | --- | --- |
| S9-C1 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C2 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C3 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C4 | 0.005 V/div MC (100): 100/100 (100.0%); 0.5 V/div MC (100): 100/100 (100.0%); 12 escalas nominales: 12/12 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C5 | 0.005 V/div MC: 500/500 (100.0%); 0.05 V/div MC: 500/500 (100.0%); 0.5 V/div MC: 500/500 (100.0%); 5.0 V/div MC: 500/500 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C6 | K4 compartido, P/Z/R, dos frecuencias: 6/6 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C7 | 36 barridos deterministas, rieles extremos: 36/36 (100.0%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C8 | recuperaciones nominales sin BAV199: 0/10 (0.0%) — FALLA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |
| S9-C9 | 0.005 V/div MC: 484/500 (96.8%); 0.05 V/div MC: 488/500 (97.6%); 0.5 V/div MC: 484/500 (96.8%); 5.0 V/div MC: 488/500 (97.6%) — PASA | NO EVALUADA: detenida por K0 (modelo incompatible con hoja) |

Concurrencia: las nuevas entradas de memoria sobre S8 (relé, economizador, C_AC, parejas serie/paralelo y orden AC–GND–DC) no se incorporan al modelo S9, cuyo contrato exige S7b literal. Las fracciones describen ese circuito contractual y su reparto de tolerancias; no certifican las nuevas realizaciones físicas de S8. Los seis escalones con fallo inicial por límite de iteraciones terminaron en el único reintento, con la recomendación nominal propia y itl4=1000; sus errores iniciales están en registros e historial.

B se detiene por K0: el modelo antiguo no concuerda en ancho ni consumo con la hoja suministrada. Sus ensayos previos son diagnósticos y quedan fuera de esta campaña. C1/C2/C3/C5/C9: cuatro cohortes de las mismas 500 placas de A, no 2000 placas independientes. C4: primeras 100 placas en dos escalas, nominal en las 12. C6/C7/C8 son fracciones de casos deterministas y no estiman una fracción poblacional. Detalle por escala en `s9_criterios.csv`.

## K1 nominal por escala

| variant | scale_V_div | minus3_Hz | peak_db | atten_1p73m_db | atten_2p47m_db | gain_dc_signed | gd_min_ns | gd_max_ns | rebound_excess_db | rise_ns | overshoot_pct | noise_pct_div |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.005 | 1001224 | 1.741841e-05 | 13.66414 | 25.22757 | -49.47979 | 436.5238 | 494.7786 | 0 | 367.6458 | 4.374252 | 0.2336542 |
| A | 0.01 | 1001154 | 1.742267e-05 | 13.66599 | 25.23134 | -24.73182 | 438.3514 | 496.5611 | 0 | 367.6729 | 4.373371 | 0.2005073 |
| A | 0.02 | 1001182 | 1.742512e-05 | 13.66523 | 25.22979 | -12.38334 | 437.9251 | 496.1165 | 0 | 367.6634 | 4.37349 | 0.1890778 |
| A | 0.05 | 1001212 | 1.742671e-05 | 13.66443 | 25.22818 | -4.944453 | 437.237 | 495.4199 | 0 | 367.6529 | 4.373699 | 0.1842431 |
| A | 0.1 | 1001221 | 1.742726e-05 | 13.66423 | 25.22779 | -2.469752 | 436.9342 | 495.1167 | 0 | 367.6502 | 4.373776 | 0.1830085 |
| A | 0.2 | 1001225 | 1.742753e-05 | 13.66415 | 25.22763 | -1.234874 | 436.7653 | 494.952 | 0 | 367.6487 | 4.373845 | 0.1824648 |
| A | 0.5 | 1000877 | 1.77126e-05 | 13.66728 | 25.23071 | -0.4951413 | 435.8773 | 494.7673 | 0 | 367.694 | 4.365613 | 0.2338878 |
| A | 1 | 1000807 | 1.771166e-05 | 13.66913 | 25.23448 | -0.2474899 | 437.6946 | 496.5498 | 0 | 367.7208 | 4.364727 | 0.2005753 |
| A | 2 | 1000836 | 1.77115e-05 | 13.66837 | 25.23294 | -0.1239194 | 437.2657 | 496.1052 | 0 | 367.7116 | 4.364881 | 0.1890959 |
| A | 5 | 1000866 | 1.77115e-05 | 13.66758 | 25.23133 | -0.04947884 | 436.5777 | 495.4086 | 0 | 367.7009 | 4.365072 | 0.1842461 |
| A | 10 | 1000874 | 1.771152e-05 | 13.66738 | 25.23093 | -0.02471467 | 436.2765 | 495.1054 | 0 | 367.6978 | 4.36515 | 0.1830092 |
| A | 20 | 1000878 | 1.771154e-05 | 13.66729 | 25.23077 | -0.01235731 | 436.1115 | 494.9407 | 0 | 367.6971 | 4.365244 | 0.182465 |

## Monte Carlo

| variant | scale_V_div | metric | N | min | p2p5 | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.005 | minus3_Hz | 500 | 916034.9 | 946698 | 1058728 | 1071758 |
| A | 0.005 | peak_db | 500 | 1.667979e-05 | 1.677064e-05 | 0.01023691 | 0.01379254 |
| A | 0.005 | atten_2p47m_db | 500 | 23.85616 | 24.27655 | 26.11417 | 26.42334 |
| A | 0.005 | gain_dc_signed | 500 | -50.98914 | -50.64586 | -48.2369 | -47.81634 |
| A | 0.005 | offset_uncal_V | 500 | -0.2304555 | -0.1746012 | 0.1481236 | 0.1810312 |
| A | 0.005 | noise_pct_div | 100 | 0.2243225 | 0.2258602 | 0.2410118 | 0.2436932 |
| A | 0.05 | minus3_Hz | 500 | 916022.8 | 946689 | 1058712 | 1071748 |
| A | 0.05 | peak_db | 500 | 1.668178e-05 | 1.677276e-05 | 0.01032669 | 0.01387785 |
| A | 0.05 | atten_2p47m_db | 500 | 23.85668 | 24.27758 | 26.11475 | 26.42424 |
| A | 0.05 | gain_dc_signed | 500 | -5.139773 | -5.06924 | -4.81744 | -4.771595 |
| A | 0.05 | offset_uncal_V | 500 | -0.2044576 | -0.1640492 | 0.142788 | 0.1672714 |
| A | 0.5 | minus3_Hz | 500 | 913505.4 | 945282.3 | 1056523 | 1078945 |
| A | 0.5 | peak_db | 500 | 1.730554e-05 | 1.746094e-05 | 0.09354797 | 0.2370698 |
| A | 0.5 | atten_2p47m_db | 500 | 23.84809 | 24.3015 | 26.14517 | 26.42972 |
| A | 0.5 | gain_dc_signed | 500 | -0.5100352 | -0.5067556 | -0.4827662 | -0.4776024 |
| A | 0.5 | offset_uncal_V | 500 | -0.2304644 | -0.1746104 | 0.148115 | 0.1810219 |
| A | 0.5 | noise_pct_div | 100 | 0.2243442 | 0.2261499 | 0.2412294 | 0.2439586 |
| A | 5 | minus3_Hz | 500 | 913493.4 | 945270 | 1056512 | 1078926 |
| A | 5 | peak_db | 500 | 1.730408e-05 | 1.745952e-05 | 0.09359017 | 0.2370937 |
| A | 5 | atten_2p47m_db | 500 | 23.84861 | 24.30212 | 26.14564 | 26.43061 |
| A | 5 | gain_dc_signed | 500 | -0.05141223 | -0.05072269 | -0.04821205 | -0.0476952 |
| A | 5 | offset_uncal_V | 500 | -0.2044584 | -0.1640501 | 0.1427871 | 0.1672706 |

## K3: AFE y ADC

Ruido integrado de 1 Hz a 10 MHz. Se suma en cuadratura el ruido independiente del ADC de 0.40 y 0.61 mV rms. Las tres columnas de porcentaje se refieren a una división; C4 se evalúa sólo con el AFE.

| variant | scale_V_div | noise_pin_uV | noise_pct_div | noise_with_adc_low_pct | noise_with_adc_high_pct |
| --- | --- | --- | --- | --- | --- |
| A | 0.005 | 584.1356 | 0.2336542 | 0.283186 | 0.3378318 |
| A | 0.01 | 501.2682 | 0.2005073 | 0.2565213 | 0.3158151 |
| A | 0.02 | 472.6946 | 0.1890778 | 0.2476902 | 0.308685 |
| A | 0.05 | 460.6077 | 0.1842431 | 0.2440195 | 0.3057475 |
| A | 0.1 | 457.5211 | 0.1830085 | 0.2430887 | 0.3050051 |
| A | 0.2 | 456.1619 | 0.1824648 | 0.2426796 | 0.3046792 |
| A | 0.5 | 584.7196 | 0.2338878 | 0.2833788 | 0.3379934 |
| A | 1 | 501.4383 | 0.2005753 | 0.2565745 | 0.3158583 |
| A | 2 | 472.7398 | 0.1890959 | 0.247704 | 0.3086961 |
| A | 5 | 460.6151 | 0.1842461 | 0.2440217 | 0.3057493 |
| A | 10 | 457.523 | 0.1830092 | 0.2430892 | 0.3050055 |
| A | 20 | 456.1624 | 0.182465 | 0.2426797 | 0.3046793 |

## Muestreo, un ADC

f_ADC=52MHz, f_s=52MHz/15=3466666.66667Sa/s; t_s=2.5/52MHz=48.0769230769ns; período=288.461538462ns. N=1024, M impar más cercano a0.5/1MHz. R_SW inferida de S6, no medida: (2.5/60MHz)/(5pF×ln(2¹³))−100Ω=824.80451339Ω. C_pad5pF supuesto; C_S5pF, resetideal0/2.5V, flancos20ps. Se descartan256 muestras; se mide el límite izquierdo de cierre, sin mezclar reset. Referencia sin carga de la misma S4 en paralelo. LS error=a*v[n]+b*v[n−1]+c; sin entrelazado. FFT rectangular, sin cuantización/jitter/ruido del ADC.

| state | RSW | freq_Hz | M | sfdr_db | reference_sfdr_db | residual_rms_LSB | error_max_LSB | error_rms_LSB | gain_delta_db | phase_delta_deg | fundamental_pp_V | closing_time_error_ps |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P | 400 | 497656.2 | 147 | 153.8594 | 181.9269 | 0.0001506834 | 14.47569 | 10.23589 | -0.009267936 | -0.5027934 | 1.997867 | 5.421011e-08 |
| P | 400 | 998697.9 | 295 | 146.1172 | 160.4375 | 0.0002186559 | 26.7422 | 18.90935 | -0.03036017 | -0.915167 | 1.993021 | 0.03972097 |
| P | 825 | 497656.2 | 147 | 149.0517 | 190.2646 | 0.0001830419 | 25.75063 | 18.20847 | -0.01123072 | -0.8980565 | 1.997416 | 5.421011e-08 |
| P | 825 | 998697.9 | 295 | 143.6919 | 164.8895 | 0.0002703957 | 48.81478 | 34.5172 | -0.03713503 | -1.693164 | 1.991467 | 0.0391861 |
| P | 1500 | 497656.2 | 147 | 137.9519 | 202.6057 | 0.0006120771 | 45.48061 | 32.1585 | -0.02056707 | -1.58657 | 1.99527 | 5.421011e-08 |
| P | 1500 | 998697.9 | 295 | 130.3536 | 173.275 | 0.0009896744 | 86.15443 | 60.9204 | -0.06845745 | -2.991208 | 1.984299 | 5.421011e-08 |
| Z | 400 | 497656.2 | 147 | 160.6662 | 189.3183 | 2.565111e-05 | 17.29647 | 9.990723 | -0.02377165 | -0.3814934 | 1.994534 | 1.084202e-07 |
| Z | 400 | 998697.9 | 295 | 164.6892 | 177.813 | 1.929581e-05 | 27.86504 | 16.73754 | -0.02479054 | -0.7653371 | 1.9943 | 1.084202e-07 |
| Z | 825 | 497656.2 | 147 | 152.2095 | 188.9896 | 8.378655e-05 | 28.65665 | 16.98966 | -0.0280487 | -0.7573525 | 1.993552 | 1.084202e-07 |
| Z | 825 | 998697.9 | 295 | 156.5544 | 177.5598 | 6.018064e-05 | 50.15272 | 31.59338 | -0.03067083 | -1.51943 | 1.99295 | 1.084202e-07 |
| Z | 1500 | 497656.2 | 147 | 126.5938 | 189.9655 | 0.001427137 | 50.56032 | 29.99326 | -0.05007136 | -1.339356 | 1.988504 | 1.084202e-07 |
| Z | 1500 | 998697.9 | 295 | 130.4146 | 177.7964 | 0.001031391 | 88.5408 | 55.80977 | -0.05707903 | -2.686572 | 1.9869 | 1.084202e-07 |
| R | 400 | 497656.2 | 147 | 149.4057 | 173.7449 | 0.0003620737 | 17.29554 | 9.989935 | -0.0237664 | -0.3814984 | 1.994535 | 0.05484242 |
| R | 400 | 998697.9 | 295 | 149.1618 | 155.7467 | 0.0003269721 | 27.86379 | 16.73721 | -0.02478532 | -0.765347 | 1.994301 | 0.0405187 |
| R | 825 | 497656.2 | 147 | 148.8873 | 177.1733 | 0.0004086782 | 28.65496 | 16.98907 | -0.02804251 | -0.7573578 | 1.993553 | 1.084202e-07 |
| R | 825 | 998697.9 | 295 | 142.6447 | 159.6385 | 0.0004886712 | 50.1516 | 31.59322 | -0.03066524 | -1.51944 | 1.992951 | 0.02567189 |
| R | 1500 | 497656.2 | 147 | 125.5414 | 185.6821 | 0.002070631 | 50.55507 | 29.99151 | -0.05005241 | -1.33937 | 1.988508 | 1.084202e-07 |
| R | 1500 | 998697.9 | 295 | 128.1789 | 173.6459 | 0.001849853 | 88.53668 | 55.80929 | -0.05706021 | -2.686604 | 1.986904 | 0.02109668 |

Fondo de escala heredado de S6/S7: ±4 divisiones, 0.25 V/div; referencia sin carga de 2 Vpp centrada en 1.25 V. Es distinto del rango eléctrico total ADC de 0…2.5 V. Fuente: PLAN_SIMULACION_S3.md, Las 12 escalas; PLAN_SIMULACION_S7.md, J7; auditoría S6, amplitud 1 V. La amplitud y el centro de la fuente se calculan con AC y OP de la etapa real.

LSB heredado de S6: 2.5/4096 = 0.6103515625 mV (12 bits). Medio LSB = 0.30517578125 mV; el factor ln(2¹³) corresponde al asentamiento a medio LSB, no a un ADC de 13 bits.

## Protecciones en extremos

| variant | stage | differential_V | input_max_mA |
| --- | --- | --- | --- |
| A | OPA810 | 0.9197348 | 7.741847e-09 |
| A | U103A | 0.6870306 | 4.409585 |
| A | U103B | 0.6806466 | 3.913113 |
| A | U105A | 0.03656514 | 0.0003956648 |
| A | U105B | 0.02529511 | 0.000392071 |
| A | OPA836 | 0.6243244 | 0.03189061 |

| variant | adc_min_V | adc_max_V | mux_low_margin_V | mux_high_margin_V | mux_supply_max_V | bav99_max_mA |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0.006878396 | 3.288983 | 0.115322 | 0.1137649 | 9.954115 | 4.409344 |

Rieles fuente (positivo, magnitud del negativo), en V: [(4.8, 4.8), (4.8, 5), (5, 4.8), (5, 5)]. Barridos continuos de cero hasta ±40 V y ±100 V, con paso de 1 mV y posterior fusión de polaridades; E5b cubre las posiciones de acoplamiento DC y AC. Las sondas de corriente usan fuentes de 0 V. Los diagnósticos B miden la corriente real del pin a través de RINA/RINB, separada de la corriente de los BAV99 externos. No se ejecutaron ESD, apagado ni pruebas físicas.

## Recuperación

| variant | scale_V_div | amplitude_V | recovery_us | bav199_conducts | bav199_forward_max_V |
| --- | --- | --- | --- | --- | --- |
| A | 0.005 | 0.2 | 1.331497 | False | -4.677729 |
| A | 0.005 | 2 | 1.342698 | False | -2.892531 |
| A | 0.005 | 4.5 | 1.376531 | False | -0.4157484 |
| A | 0.005 | -0.2 | 1.362077 | False | -4.679136 |
| A | 0.005 | -2 | 1.371689 | False | -2.893935 |
| A | 0.005 | -4.5 | 1.39547 | False | -0.417069 |
| A | 0.5 | 20 | 1.371571 | False | -4.677613 |
| A | 0.5 | 40 | 1.401285 | False | -4.47875 |
| A | 0.5 | -20 | 1.390504 | False | -4.67902 |
| A | 0.5 | -40 | 1.414448 | False | -4.480157 |

## Distancia a los criterios incumplidos

- S9-C8, recuperaciones nominales sin BAV199: 0.000 %, faltan 100.000 puntos porcentuales para 100 % (casos deterministas). Recuperación medida 1.3315…1.41445 µs frente a 1 µs. El resultado se movería al acortar la cola del filtro y/o la salida de saturación; no se cambia el ancho contractual ni se simula un remedio.

## Diferencias y consumo

| dato | A | B |
| --- | --- | --- |
| Ruido peor nominal (%div) | 0.2338878 | Detenida por K0 |
| Offset nominal 5mV/div (V) | -0.01902655 | Detenida por K0 |
| Consumo de canal simulado (mW) | 62.72426 | Detenida por K0 |
| Corriente riel+ simulada (mA) | 6.000448 | Detenida por K0 |
| Corriente por riel según hojas (mA) | 7.7 | 12.5 |
| Diferencial U103/U105 máximo (V) | 0.6870306 | Detenida por K0 |

| variant | stage | plus_A | minus_A | vdda_A | vref_A | dac_A | power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | OPA810 | 0.001900076 | -0.0019 | 0 |  |  | 18.53383 |
| A | U103A | 0.001035675 | -0.001035376 | 0 |  |  | 10.10098 |
| A | U103B | 0.001036271 | -0.00103478 | 0 |  |  | 10.10098 |
| A | U105A | 0.001035525 | -0.001035526 | 0 |  |  | 10.10098 |
| A | U105B | 0.0009928991 | -0.001079495 | 0 |  |  | 10.10759 |
| A | OPA836 | 0.001004037 | 0 | 0.001004037 |  |  | 3.313321 |
| A | 4051 | 1.293134e-09 | -1.185758e-09 | 0 |  |  | 1.209004e-05 |
| A | VMID |  |  |  | 0.0001630331 |  | 0.4075826 |
| A | DAC |  |  |  |  | 4.718511e-05 | 0.05898139 |
| A | TOTAL_CHANNEL | 0.006000448 | -0.006085177 | 0.001004037 | 0.0001630331 | 4.718511e-05 | 62.72426 |

Consumo por hojas: OPA810 3.7 mA, AD8039 1 mA/amplificador (revisión R3); LM6172 4.4 mA/dual a ±5 V, 2.2 mA/amplificador (p.7). Por riel: A 7.7 mA, B 12.5 mA; OPA836 ≈1 mA a 3.3 V, más VMID/DAC. Los modelos dan menos corriente que las hojas; no se corrige G.3 ni se certifica autonomía. No incluye relé, MCU, pérdidas de convertidores ni cargas de otros canales; las cargas 42/39 mA de RAILS heredadas no se suman al canal. B sólo tiene estimación por hoja, tras su detención K0.

Las corrientes de las fuentes se conservan con signo; para consumo del riel negativo se usa su magnitud. La potencia se calcula con la tensión y la corriente firmadas de cada fuente.

## Método y reproducibilidad

LTspice 26.0.2, modelos locales, diez trabajadores. El reparto S7b §2 conserva uniformes independientes por componente: resistencias ±1 % (divisor ±0.1 %), C0G ±5 %, pistas de 1/3 pF ±50 %, rieles ±2 % independientes y VREF ±0.2 %. Offsets en serie con IN+: OPA810 ±715 µV, AD8039 ±3 mV y OPA836 ±400 µV. LM6172 ±3 mV sólo en los diagnósticos B previos. El offset propio de cada modelo permanece. No se dispersan GBW, polarización, temperatura ni ruido intrínseco.

La realización física se conserva al cambiar escala. Los resistores del filtro reutilizan el mismo factor de tolerancia, reescalado al E96 elegido. Componentes y factores en `s9_mc_components.csv`. K3 pone la BNC a masa con fuente ideal de 0 Ω e integra el ruido en el pin de 1 Hz a 10 MHz. El ruido ADC de 0.40/0.61 mV rms se añade en cuadratura.

Ganancia DC: tres puntos `.op` independientes, entrada −0.01/0/+0.01 división, DAC a 1.25 V. Posición: entrada cero, DAC a 0.2/2.3 V y 1.24 V para medir la pendiente local junto al punto de 1.25 V. Son seis puntos por caso. Los extremos reales incluyen saturación. Centro ADC 1.25 V; ±4.5 divisiones exige 0.125…2.375 V. La continua Monte Carlo no usa `.dc`.

Límites de tiempo: 60 s por OP, 120 s en AC/ruido, 600 s en protecciones y 900 s en transitorios; un reintento por caso. `.loadbias` recomienda condiciones iniciales y Newton resuelve de nuevo el circuito. Se usa la solución propia de placa/escala cuando existe; las recomendaciones S7b y su permutación de rama están documentadas arriba. El reintento A aumenta itl4 y usa su bias nominal propio, conservando estímulo y tolerancias. Los ensayos numéricos B permanecen como diagnóstico histórico.

CSV con columnas fijas y orden por ID; JSON durables por caso. `--resume` exige CSV completo, cabecera declarada y registro JSON. La tabla `s9_nominal.csv` se identifica como agregado, con los cuatro casos fuente por escala en `s9_nominal_sources.csv`. Calibración A usa ganancia DC con signo; B tiene CSV vacío y nota de no evaluación.

Fuentes/modelos protegidos por SHA256; artefactos previos por tamaño/mtime. Logs, raw, bases de datos y bytecode quedan fuera del guard. La concurrencia externa se conserva con huellas y metadatos originales; no se editan STATE ni DECISIONS. El auditor indexa los decks una sola vez y comprueba los seis estados OP, parámetros Monte Carlo, nombres de medidas, extremos de protección, fuente coherente, un ADC, apertura y cabeceras.

Reproducción desde CH23_entrada: `python preparar_s9.py`; `python k0_s9.py`; `python ejecutar_s9.py --preflight --optimize`; `python ejecutar_s9.py --smoke`; `python ejecutar_s9.py`; `python verificar_s9.py`; `python informar_s9.py`. Reanudación: `python ejecutar_s9.py --resume`. `S3G4_MODELS` admite otra ruta de la biblioteca local de sólo lectura. B se filtra por su resultado K0.

<!-- S9_B_CODEX_BEGIN -->

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

<!-- S9_B_CODEX_END -->
