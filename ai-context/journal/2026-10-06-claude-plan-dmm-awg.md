# Orden DMM → AWG → pines y documentos al día (6 oct 2026, noche, Claude Opus 5.5)

- Keneth propuso hacer primero el DMM y el AWG, y después el mapa de pines con la conexión al STM32 separando lo analógico de lo digital. Claude estuvo de acuerdo y propuso una salvaguarda: una lista de reserva de pines y periféricos del G473 mientras se diseñan.
- Keneth: D-07 queda aceptada y RE-01 en espera. Registrado en DECISIONS.
- Documentos actualizados: PLAN.md (reescrito), rediseno_afe_rev21.html (D-07, CH2/CH3 en F y en el filtro, meta), los LEEME de la rev 2.1, de 05_informes y de 03_simulaciones.
- Error propio corregido: había puesto 1.03 MHz / 25.6 dB (que son del LM6172) como cifras de CH2/CH3. Con la AD8039, s9_k1.csv da 1.001 MHz y 25.23 dB. Corregido en el documento vivo y en CH23_PIEZAS_Y_REDES.md.
- Siguiente: diseño del DMM.
