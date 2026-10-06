# Resultados S1b — LTspice

Código de salida: 0. Simulaciones: 9375; error: 0; advertencia: 0. Semilla: 20261003. Casos por campaña: 200.

Pool: 10 trabajadores. Tiempo total: 2047.451 s (34.124 min). Casos fallidos: 0.

Verificación de paralelización: smoke de 1 y 10 trabajadores, 14 CSV idénticos byte a byte; 104 simulaciones por variante, sin errores ni advertencias. Tiempos: 96.586 s secuencial y 61.975 s paralelo. Evidencia: `S1b/paralelizacion_verificacion.json` y directorios smoke.

| criterion | RANGO | value | status |
| --- | --- | --- | --- |
| S1b-C1 | nominal | 0.999128…1.000287 MΩ | PASA |
| S1b-C2 | nominal | Cin=26.292419…26.691674 pF; Δ=0.399255 pF | PASA |
| S1b-C3 | nominal | Error máximo 0.324191 % | PASA |
| S1b-C4 | nominal | Planitud 0.239715 %; pico 0.001353 dB; corte 8.802472 Hz | PASA |
| S1b-C5 | nominal | Sobre 0.017252 %; |e2| 0.338975 %; convergencia 0.000000 pp | PASA |
| S1b-C6 | 1 | Máx 0.376486 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C6 | 2 | Máx 0.375144 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C6 | 3 | Máx 0.382238 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C7 | A todos | |ΔCin| máx 1.414737 pF | PASA |
| S1b-C8 | 1 | Sobre máx 0.505098 %; |e2| máx 1.500587 % | PASA |
| S1b-C9 | A todos | Error Zin máx 0.256254 %; planitud ×1 máx 0.293357 % | PASA |

Rango mínimo que cumple C6: R1. Esto no selecciona una pieza comercial.

## Trimmer: recorrido y reparto

| RANGO | cases | stops | outside | trim_min_pF | trim_median_pF | trim_max_pF | worst_flat_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 200 | 0 | 0 | 2.55 | 4.05 | 5.95 | 0.3764856892516599 |
| 2 | 200 | 0 | 0 | 5.0 | 6.550000000000001 | 8.4 | 0.3751443504008911 |
| 3 | 200 | 0 | 0 | 11.0 | 12.600000000000001 | 14.3 | 0.3822379589964231 |

| RANGO | low_pF | high_pF | count |
| --- | --- | --- | --- |
| 1 | 2.0 | 2.5 | 0 |
| 1 | 2.5 | 3.0 | 14 |
| 1 | 3.0 | 3.5 | 29 |
| 1 | 3.5 | 4.0 | 50 |
| 1 | 4.0 | 4.5 | 46 |
| 1 | 4.5 | 5.0 | 38 |
| 1 | 5.0 | 5.5 | 19 |
| 1 | 5.5 | 6.0 | 4 |
| 2 | 3.0 | 3.875 | 0 |
| 2 | 3.875 | 4.75 | 0 |
| 2 | 4.75 | 5.625 | 19 |
| 2 | 5.625 | 6.5 | 75 |
| 2 | 6.5 | 7.375 | 77 |
| 2 | 7.375 | 8.25 | 28 |
| 2 | 8.25 | 9.125 | 1 |
| 2 | 9.125 | 10.0 | 0 |
| 3 | 5.0 | 6.875 | 0 |
| 3 | 6.875 | 8.75 | 0 |
| 3 | 8.75 | 10.625 | 0 |
| 3 | 10.625 | 12.5 | 94 |
| 3 | 12.5 | 14.375 | 106 |
| 3 | 14.375 | 16.25 | 0 |
| 3 | 16.25 | 18.125 | 0 |
| 3 | 18.125 | 20.0 | 0 |

## E3b nominal y convergencia

| POS | step_height_v | overshoot_pct | error_2us_pct | error_20us_pct | error_200us_pct |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1978931950156 | 0.0 | -0.3389751986404172 | -0.29738057448291877 | -0.07759005911643069 |
| 100 | 0.001980291156476 | 0.017252493699358513 | -0.011190331597211521 | 0.014129891661889878 | 0.004169767396579401 |

| POS | shift_overshoot_pct | shift_objective_pct | shift_error_2us_pct | shift_error_20us_pct | shift_error_200us_pct |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | -4.069897401315359e-07 | 3.56151716063291e-07 | 3.081965529450059e-07 | 3.8050829556657284e-08 |
| 100 | -1.2462813721303423e-07 | -1.2454400919251207e-07 | -3.499486050245748e-08 | -1.997181042334012e-07 | 2.524877949078297e-09 |

## Campaña B

|ΔCin| antes: 0.012508…3.474681 pF; mediana 1.087545. Después de E24: 0.000542…0.962840 pF; mediana 0.263917.

Topes: 29/200. Planitud ÷100 máxima tras ajuste: 2.644086 %; tras E24: 2.648992 %. Sólo informativa.

| CEQ_E24_pF | count |
| --- | --- |
| 7.5 | 4 |
| 8.2 | 14 |
| 9.1 | 28 |
| 10.0 | 41 |
| 11.0 | 41 |
| 12.0 | 46 |
| 13.0 | 24 |
| 15.0 | 2 |

## Qué enseña cada prueba

E1b/E2b miden Zin, Cin, ganancia, planitud y corte AC con la estimación SEL corregida; GND sólo se informa en el CSV. E3b comprueba la sonda compensada y la convergencia real del caso compensado. E4A cuantifica el recorrido y los fallos de producción supuesta sin ocultar topes. E4B separa el ajuste del trimmer de la selección E24 de CEQ.
