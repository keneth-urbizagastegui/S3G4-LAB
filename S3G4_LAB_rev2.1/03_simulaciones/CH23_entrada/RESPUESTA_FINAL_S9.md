# Respuesta final — S9

Ficheros creados: `comun/ch23_comun_s9.inc`, `comun/lm6172_s9_ruido_hoja.lib`, `comun/lm6172_s9_sin_ruido_interno.lib`; `ejecutar_s9.py`, `preparar_s9.py`, `k0_s9.py`, `informar_s9.py`, `verificar_s9.py`; decks y registros en `S9/`; CSV/JSON en `resultados/`, calibración A y CSV B vacío con nota de no evaluación; `ACTA_S9.md` y `ai-context/journal/2026-10-04-codex-s9.md`.

Código **0**; **14451 ejecuciones nativas de referencia**, **4313/4313 casos lógicos**, **6074.026 s** de sesiones finalizadas de campaña (sin huellas iniciales ni sesiones interrumpidas), 10 trabajadores, semilla 2026100371. Histórico: 14462 intentos terminados registrados, 17 fallidos de depuración; suma de tiempos de procesos paralelos 58811.348 s, no tiempo de pared. Interrupciones en console/diario. Código 0 significa ejecución completa, no aprobación eléctrica. Cambios protegidos: [].

La ejecución completa original devolvió código 1 tras 5989.700 s: detectó modificaciones externas de STATE.md y DECISIONS.md, conservadas con huellas antes/después en `S9/campaign/guard_concurrencia_2026-10-04/`. CH1 y modelos permanecieron idénticos. El código actual corresponde a reanudación y revisión de una nueva ventana sin modificar esos archivos; se reutilizan los mismos resultados.

Auditoría Codex: código 0, 14409 decks y 4313 casos verificados; 0 errores. Auditoría externa de Claude pendiente.

Filtro A: RFILT1 = 2370 Ω, RFILT2 = 1100 Ω, E96. El preflight B usó los mismos valores; la campaña B se detuvo en K0.

K0: orden +IN −IN V+ V− OUT confirmado en `LM6172/NS`. Hoja TI SNOS792E, pp.4/7/8: alimentación recomendada 5.5–36 V, diferencial absoluto ±10 V, entrada absoluta ±10 mA, offset máximo 3 mV, polarización máxima 2.5 µA a 25 °C; a ±5 V, salida típica +3.4/−3.3 V con 1 kΩ, ruido 11 nV/√Hz y 1 pA/√Hz, consumo típico 2.2 mA/amplificador. El modelo a ±4.9 V da offset 2.986 mV, polarización 1.219/1.200 µA, seguidor 181.984 MHz frente a 130 MHz de la hoja y consumo 1.698 mA/amplificador. ×10: 9.9971, −3 dB en 15.263 MHz. El ruido nativo de 6.587/51.496 nV/√Hz a 100 kHz/1 MHz no representa el ruido de entrada de la hoja; la copia propia blanca valida 11.03684 nV/√Hz en ambos puntos. Por el punto 3 del encargo, B queda detenida: sus pruebas previas son diagnóstico, excluido de las fracciones. Detalles de condiciones, máximos, estabilidad y margen en ACTA_S9.md.

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

K1 por escala (ganancia DC con signo):

| variant | scale_V_div | minus3_Hz | peak_db | atten_1p73m_db | atten_2p47m_db | gain_dc_signed |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0.005 | 1001224 | 1.741841e-05 | 13.66414 | 25.22757 | -49.47979 |
| A | 0.01 | 1001154 | 1.742267e-05 | 13.66599 | 25.23134 | -24.73182 |
| A | 0.02 | 1001182 | 1.742512e-05 | 13.66523 | 25.22979 | -12.38334 |
| A | 0.05 | 1001212 | 1.742671e-05 | 13.66443 | 25.22818 | -4.944453 |
| A | 0.1 | 1001221 | 1.742726e-05 | 13.66423 | 25.22779 | -2.469752 |
| A | 0.2 | 1001225 | 1.742753e-05 | 13.66415 | 25.22763 | -1.234874 |
| A | 0.5 | 1000877 | 1.77126e-05 | 13.66728 | 25.23071 | -0.4951413 |
| A | 1 | 1000807 | 1.771166e-05 | 13.66913 | 25.23448 | -0.2474899 |
| A | 2 | 1000836 | 1.77115e-05 | 13.66837 | 25.23294 | -0.1239194 |
| A | 5 | 1000866 | 1.77115e-05 | 13.66758 | 25.23133 | -0.04947884 |
| A | 10 | 1000874 | 1.771152e-05 | 13.66738 | 25.23093 | -0.02471467 |
| A | 20 | 1000878 | 1.771154e-05 | 13.66729 | 25.23077 | -0.01235731 |

Monte Carlo, mínimo/máximo y P2.5/P97.5:

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

Muestreo de 2.5 ciclos:

| state | RSW | freq_Hz | sfdr_db | residual_rms_LSB | error_max_LSB |
| --- | --- | --- | --- | --- | --- |
| P | 400 | 497656.2 | 153.8594 | 0.0001506834 | 14.47569 |
| P | 400 | 998697.9 | 146.1172 | 0.0002186559 | 26.7422 |
| P | 825 | 497656.2 | 149.0517 | 0.0001830419 | 25.75063 |
| P | 825 | 998697.9 | 143.6919 | 0.0002703957 | 48.81478 |
| P | 1500 | 497656.2 | 137.9519 | 0.0006120771 | 45.48061 |
| P | 1500 | 998697.9 | 130.3536 | 0.0009896744 | 86.15443 |
| Z | 400 | 497656.2 | 160.6662 | 2.565111e-05 | 17.29647 |
| Z | 400 | 998697.9 | 164.6892 | 1.929581e-05 | 27.86504 |
| Z | 825 | 497656.2 | 152.2095 | 8.378655e-05 | 28.65665 |
| Z | 825 | 998697.9 | 156.5544 | 6.018064e-05 | 50.15272 |
| Z | 1500 | 497656.2 | 126.5938 | 0.001427137 | 50.56032 |
| Z | 1500 | 998697.9 | 130.4146 | 0.001031391 | 88.5408 |
| R | 400 | 497656.2 | 149.4057 | 0.0003620737 | 17.29554 |
| R | 400 | 998697.9 | 149.1618 | 0.0003269721 | 27.86379 |
| R | 825 | 497656.2 | 148.8873 | 0.0004086782 | 28.65496 |
| R | 825 | 998697.9 | 142.6447 | 0.0004886712 | 50.1516 |
| R | 1500 | 497656.2 | 125.5414 | 0.002070631 | 50.55507 |
| R | 1500 | 998697.9 | 128.1789 | 0.001849853 | 88.53668 |

K3: AFE y suma en cuadratura con ADC de 0.40/0.61 mV rms; porcentajes de división:

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

Protecciones en extremos:

| variant | stage | differential_V | input_max_mA |
| --- | --- | --- | --- |
| A | OPA810 | 0.9197348 | 7.741847e-09 |
| A | U103A | 0.6870306 | 4.409585 |
| A | U103B | 0.6806466 | 3.913113 |
| A | U105A | 0.03656514 | 0.0003956648 |
| A | U105B | 0.02529511 | 0.000392071 |
| A | OPA836 | 0.6243244 | 0.03189061 |

| variant | adc_min_V | adc_max_V | mux_supply_max_V | bav99_max_mA |
| --- | --- | --- | --- | --- |
| A | 0.006878396 | 3.288983 | 9.954115 | 4.409344 |

Consumo y diferencias:

| dato | A | B |
| --- | --- | --- |
| Ruido peor nominal (%div) | 0.2338878 | Detenida por K0 |
| Offset nominal 5mV/div (V) | -0.01902655 | Detenida por K0 |
| Consumo de canal simulado (mW) | 62.72426 | Detenida por K0 |
| Corriente riel+ simulada (mA) | 6.000448 | Detenida por K0 |
| Corriente por riel según hojas (mA) | 7.7 | 12.5 |
| Diferencial U103/U105 máximo (V) | 0.6870306 | Detenida por K0 |

C8: 1.331497…1.414448 µs frente a 1 µs; exceso de 0.3314974…0.4144477 µs. Acortar la cola del filtro o la salida de saturación movería el resultado; no se simularon remedios. Rieles fuente de K6, en V: [(4.8, 4.8), (4.8, 5), (5, 4.8), (5, 5)].

Criterios incumplidos: S9-C8 recuperaciones nominales sin BAV199: faltan 100.000 puntos porcentuales hasta 100 %. Valores, distancia y dependencias sin simular remedios en ACTA_S9.md.

Dudas: modelo LM6172 antiguo sobreestima el ancho de banda y subestima consumo a ±5 V; ruido blanco de hoja sin curva 1/f; offset propio del macro sumado al Monte Carlo como S7b (diagnóstico B excluido); base S7b frente a S7c; U105 sin 470 Ω/BAV99 en la base pese al texto S9; GBW/Ib/temperatura no dispersados; R_SW y reset del ADC supuestos. C6/C7/C8 son casos, no fracciones de placas. No se elige variante ni remedio. Detalles, advertencias y concurrencia en acta y diario.
