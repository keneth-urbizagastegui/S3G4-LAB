# Respuesta final — S7

Creados: `comun/ch1_comun_s7.inc`, `ejecutar_s7.py`, `verificar_s7.py`, decks y registros en `S7/`, CSV y resumen `resultados/s7_*`, tabla de calibración, `ACTA_S7.md` y diario propio en `ai-context/journal/2026-10-03-codex-s7-integracion.md`.

Código **0**; **694 simulaciones** para 690 casos, 2275.5 s (37.93 min), 10 trabajadores. 692 ejecuciones válidas; inicializaciones previas fallidas/interrumpidas: 2. 12404 archivos protegidos; cambios: 0. Código 0 expresa ejecución completa, no aceptación del circuito.

| Criterio | Resultado |
| --- | --- |
| S7-C1 | PASA |
| S7-C2 | PASA |
| S7-C3 | PASA |
| S7-C4 | PASA |
| S7-C5 | PASA |
| S7-C6 | PASA |
| S7-C7 | PASA |
| S7-C8 | FALLA |
| S7-C9 | PASA |

| V/div | −3 dB (MHz) | G DC (V/V) | Subida (ns) | Ruido (% div) | A 4.5 MHz (dB) |
| --- | --- | --- | --- | --- | --- |
| 0.005 | 2.007086 | -49.49820594 | 182.063 | 0.3217 | 21.7018 |
| 0.01 | 2.006447 | -24.74102802 | 182.114 | 0.27708 | 21.7143 |
| 0.02 | 2.006709 | -12.38795134 | 182.094 | 0.26156 | 21.7092 |
| 0.05 | 2.006982 | -4.94629362 | 182.071 | 0.25491 | 21.7039 |
| 0.1 | 2.00705 | -2.47067194 | 182.066 | 0.25319 | 21.7026 |
| 0.2 | 2.007078 | -1.23533393 | 182.064 | 0.25242 | 21.7021 |
| 0.5 | 2.006817 | -0.49532558 | 182.087 | 0.32182 | 21.7028 |
| 1.0 | 2.006179 | -0.24758199 | 182.142 | 0.27712 | 21.7154 |
| 2.0 | 2.006441 | -0.12396549 | 182.12 | 0.26157 | 21.7102 |
| 5.0 | 2.006714 | -0.04949726 | 182.097 | 0.25491 | 21.7049 |
| 10.0 | 2.006782 | -0.02472387 | 182.092 | 0.25319 | 21.7036 |
| 20.0 | 2.00681 | -0.01236191 | 182.091 | 0.25242 | 21.7032 |

Monte Carlo: 300 casos por escala, semilla 202610037, tolerancias independientes, sin reajuste.

| escala_V_div | min_MHz | max_MHz | dentro_pct |
| --- | --- | --- | --- |
| 0.005 | 1.87423 | 2.16699 | 100.0 |
| 0.5 | 1.73756 | 2.23295 | 96.0 |

Picos de Monte Carlo: [(0.005, 0.0036590551314025447, 0), (0.5, 0.6614483210831158, 11)] (escala V/div, máximo dB, casos >0.5 dB). El criterio C2 sólo fija la fracción de cortes dentro de banda; el rendimiento observado no es una garantía estadística de producción. Distribuciones completas de pico, rechazo a 4.5 MHz y ganancia: `s7_montecarlo_resumen.csv`.

J5, barridos −40…+40 V en las cinco escalas pedidas:

| Etapa | Diferencial máx. (V) | I entrada máx. (mA) | I salida máx. (mA) |
| --- | --- | --- | --- |
| OPA810 | 0.876671 | 0.0 | 9.238751 |
| U103A | 0.687027 | 4.409278 |  |
| U103B | 0.680641 | 3.912743 |  |
| U105A | 0.035793 | 0.000396 |  |
| U105B | 0.02558 | 0.000392 |  |
| OPA836 | 0.624339 | 0.031905 |  |

Pin del ADC: 0.006878…3.288984 V. U103: corrientes incluyen la protección BAV99. Extremos por escala: `s7_limits.csv`.

Consumo por etapa y canal (corrientes absorbidas):

| Etapa | I +5 reposo (mA) | I −5 reposo (mA) | I VDDA reposo (mA) | Reposo (mW) | Seno 2 MHz (mW) |
| --- | --- | --- | --- | --- | --- |
| OPA810 | 1.900076 | 1.9 | 0.0 | 18.9123 | 18.96755 |
| U103A | 1.03569 | 1.035391 | 0.0 | 10.3074 | 10.31283 |
| U103B | 1.036286 | 1.034795 | 0.0 | 10.3074 | 10.93227 |
| U105A | 1.03554 | 1.035541 | 0.0 | 10.3074 | 11.32942 |
| U105B | 0.992914 | 1.07951 | 0.0 | 10.31415 | 10.98923 |
| OPA836 | 0.0 | 0.0 | 1.004037 | 3.31332 | 3.31959 |
| 4051 | 1e-06 | 1e-06 | 0.0 | 1e-05 | 1e-05 |
| VMID | 0.0 | 0.0 | 0.0 | 0.40758 | 0.40758 |
| DAC | 0.0 | 0.0 | 0.0 | 0.05898 | 0.05898 |
| TOTAL_CHANNEL | 6.000507 | 6.085237 | 1.004037 | 63.92855 | 66.31747 |

G.3 aplicado al recuento real de CH1 supondría 207.87 mW sólo en amplificadores. Corrientes por cada riel: `s7_consumption.csv`.

J6: recuperación máxima 0.697757 µs; ningún caso de conducción directa de BAV199 en los pulsos prescritos.
J7: SFDR mínimo 107.449 dB; THD máxima 0.0004855 %; residuo máximo 0.0056064 LSB rms.

Dudas conservadas: FRONT_S2B deriva C_S=1.1691 nF y C_EQ=8.66765 pF, distintos de los resúmenes; G.3 cuenta un amplificador de filtro y S5 fija dos. C8 es lineal en su rango útil y recorta en el extremo inferior: se conserva el fallo literal de linealidad en los 9 puntos, junto con la aceptación previa del recorte en S4. Diodos del OPA836 supuestos, BAV99HY de Rohm para una pieza Nexperia y ADC sin ruido, cuantización, jitter ni desajuste: resultados de simulación, pendientes de auditoría y placa. No se cambian valores ni se eligen remedios.

Pendiente: S7b para la decisión concurrente de ±4.90 V y C_S=1.2 nF, con tolerancias ampliadas y criterio funcional. S7 verifica el contrato original; no certifica esa nueva revisión. Smoke completó 42/42 simulaciones, pero su código fue 1 por las modificaciones externas de STATE/DECISIONS.
