# Respuesta final S3

Campaña: código **0**, **245 casos únicos**, **1036.014 s**, diez trabajadores. Incluye 168 repeticiones de E15 para corregir sólo su estímulo (+2div con offset), en 270.377s; 413 intentos en estas fases finales. Smoke: código 0, 52 ejecuciones, 268.312 s (previo a la última corrección del estímulo E15). Dos fallos nativos de compatibilidad SWI1 activan el reemplazo permitido sólo en E15; 243 simulaciones utilizables. Reejecución con `S3G4_MODELS`: código 0, 700.741 s; **14 CSV idénticos byte a byte**.

Creados: `comun/ch1_comun_s3.inc`, `ejecutar_s3.py`, `repetir_e15_s3.py`, `verificar_reproduccion_s3.py`, `generar_respuesta_s3.py`, `S3/` (decks y logs), `resultados/s3_*.csv`, JSON de ejecución y reproducción, `resultados/s3_resumen.md`, `ACTA_S3.md`, este resumen y el diario de Codex. Ningún archivo protegido cambió.

U103 aislado (1kΩ∥10pF): U103A ×4.999745, −3dB 85.201MHz, pico 1.93e-15dB; U103B ×10.011555, −3dB 32.481MHz, pico 0dB; tomas calculadas y comprobadas: 1.000000000, 0.499849654, 0.250275634, 0.099929839, 0.049914804, 0.024957402. SWI1 activo bajo; RON(−2/0/+2V)=71.66/69.13/75.04Ω.

| Criterio | Valor medido y límite | Resultado |
|---|---|---|
| S3-C1 | Loss S3 max 0.0220343922 dB / 0.5 | PASA |
| S3-C2 | Peak S3 1.78462966e-05 dB / 0.5; step 0.000172600053% / 5 | PASA |
| S3-C3 | DC error max 0.956278543% (informativo) | Informado |
| S3-C4 | Noise 1Hz–3.15MHz 0.644338186% div / 0.45 | FALLA |
| S3-C5 | THD 0.00696637201% / 1; SR fraction 0.0292243815 / 0.5 | PASA |
| S3-C6 | Recovery max finite 551.21675 us / 1; not recovered 0 (window 988.98us) | FALLA |
| S3-C7 | Diff A 0.0591696756, B 0.614658174 / 4V; U101 4.36202684/7V, I 2.18627024/10mA, rail excess 0.919680478/0.5V; AD rail excess -4.00447792V | FALLA por tensión OPA810; interpretación S2b pendiente |
| S3-C8 | Settle 0.0932545715 us / 10; glitch 5.28057427e-06 div; not recovered 0 | PASA, aproximación E15 |

| Escala/div | Pérdida S3 a2MHz dB | BNC dB | Pico S3 dB | Ruido %div | Recuperación +/− µs |
|---|---|---|---|---|---|
| 5mV | 0.01886 | 0.02433 | 0.000018 | 0.6443 | 0.0343/0.0348 |
| 10mV | 0.02203 | 0.02750 | 0.000018 | 0.6100 | 0.0368/0.0370 |
| 20mV | 0.02085 | 0.02632 | 0.000018 | 0.5978 | 0.0360/0.0360 |
| 50mV | 0.01953 | 0.02499 | 0.000018 | 0.5942 | 0.0350/0.0350 |
| 100mV | 0.01916 | 0.02462 | 0.000018 | 0.5936 | 0.0378/0.0378 |
| 200mV | 0.01901 | 0.02448 | 0.000018 | 0.5930 | 551.2167/551.2167 |
| 0.5V | 0.01886 | 0.02537 | 0.000018 | 0.6432 | 0.0348/0.0348 |
| 1V | 0.02203 | 0.02855 | 0.000018 | 0.6094 | 0.0373/0.0373 |
| 2V | 0.02085 | 0.02736 | 0.000018 | 0.5974 | 0.0338/0.0338 |
| 5V | 0.01953 | 0.02604 | 0.000018 | 0.5938 | 0.0278/0.0278 |
| 10V | 0.01916 | 0.02567 | 0.000018 | 0.5932 | 0.0240/0.0240 |
| 20V | 0.01901 | 0.02553 | 0.000018 | 0.5927 | 0.0203/0.0203 |

C4 falla en las 12 escalas: máximo **0.644338%**, exceso de 0.194338 puntos frente a 0.45%. C6: **551.216750 µs** frente a 1 µs (exceso 550.216750 µs), en 200 mV/div con ambas polaridades. C5: THD máxima 0.006966%, dV/dt 12.566V/µs (límite0.5×430).

E14: diferencial pico **U103A 0.059170 V / U103B 0.614658 V**, ambas por debajo de ±4 V. U101: 4.362027 V/7 V; 2.186270 mA/10 mA; excursión máxima 0.919680 V más allá del riel, frente a 0.5 V del criterio estricto (exceso 0.419680 V). La auditoría S2b admite la excursión con corriente limitada; se conserva la contradicción.

Reposo por amplificador, corrientes en sus pines +5V/−5V (mA): **OPA810 1.900076/-1.900000**; **AD8039A 1.035592/-1.035495**; **AD8039B 1.036391/-1.034698**; no se suman como si fueran dos consumos independientes.

Dudas: macro AD8039 con16.18nV/√Hz a100kHz frente a8 de la hoja (no corregido); SWI1 sin convergencia al conmutar, por lo que E15 usa100Ω y capacidades de hoja, sin inyección de carga real; los30ns/20ns del contrato no están declarados así en la hoja; excepción de corriente del OPA810 y consumo real pendientes de auditoría/placa. El límite40V evita forzar saturación en las escalas más altas. Modelos, entregables anteriores, STATE y DECISIONS permanecen intactos.
