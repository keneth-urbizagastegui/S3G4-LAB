# Resumen final S6

Creado: `comun/ch1_comun_s6.inc`, `ejecutar_s6.py`, `analisis_s6.py`,
`verificar_s6.py`, los decks/registros de `S6/`, `resultados/s6_*`,
[ACTA_S6.md](ACTA_S6.md) y el diario `ai-context/journal/2026-10-03-codex-s6.md`.

**Código 0; 67 simulaciones; 455.122 s.** Smoke: 25, código 0, 177.251 s.
Reproducción: 67, código 0, 436.704 s; **11/11 CSV idénticos byte a byte**.
Precisión: 4 simulaciones adicionales; cambio de error pico ≤ 0.823 µV.
Sin cambios en circuito, modelos, S1–S5, STATE ni DECISIONS.

R_SW deducida: **824.8045 Ω**; barrido contractual 400/825/1500 Ω.
Temporización verificada en ambos ADC: ventana **67.3077 ns**, período
**307.6923 ns**, desfase **153.8462 ns**; 6.5 MSa/s combinados.

| Criterio | Resultado | Valor nominal |
| --- | --- | --- |
| S6-C1 | PASA | 0.00000357 LSB máximo en continua |
| S6-C2 | FALLA | 86.5551 LSB máximo; límite 0.5 |
| S6-C3 | PASA | Residuo ≤ 0.000910 LSB rms; SFDR ≥ 106.17 dB |
| S6-C4 | PASA | Cambio de ganancia −0.042571 dB |
| S6-C5 | PASA | Margen de fase 77.93° |

Errores con P y 825 Ω; continua: peor de 0.25/1.25/2.25 V.
El seno «2 MHz» es coherente: **1.999511719 MHz**, M=315, N=1024.

| Prueba | ADC | Máximo mV (LSB) | RMS mV (LSB) |
| --- | --- | --- | --- |
| Continua | 1 | 0.00000218 (0.00000357) | 0.00000218 (0.00000357) |
| Continua | 2 | 0.00000218 (0.00000357) | 0.00000218 (0.00000357) |
| Seno H2 | 1 | 52.8291 (86.5551) | 37.3558 (61.2038) |
| Seno H2 | 2 | 52.8287 (86.5545) | 37.3558 (61.2038) |

Parte lineal H2: **−0.042571 dB / −3.021645°** en ambos ADC.
Residuo no lineal máximo/rms: ADC1 **0.000856/0.000167 mV**;
ADC2 **0.000928/0.000181 mV**. H3, con filtro TR: errores máximo/rms
ADC1 **52.8279/37.3549 mV**, ADC2 **52.8269/37.3549 mV**;
residuos máximo/rms **0.001518/0.000553** y **0.001555/0.000555 mV**.

FFT de la secuencia combinada, sin ventana:

| Prueba/secuencia | SFDR dB | THD % | Espurio fs/2−fin dBc |
| --- | --- | --- | --- |
| H2 cargada | 145.53 | 0.00000865 | −160.40 |
| H2 sin carga | 146.45 | 0.00000510 | −197.01 |
| H3 cargada | 106.17 | 0.000539 | −161.92 |
| H3 sin carga | 106.07 | 0.000546 | −187.64 |

A 2 MHz, error máximo P: **26.65 / 52.83 / 93.91 mV** para
400/825/1500 Ω; Z/R: **29.39 / 56.05 / 98.29 mV** aproximadamente.
En continua Z/R alcanzan **5.257 mV**. Sensibilidad completa por ADC en CSV.

Lazo por dos inyecciones Tian/Middlebrook: OPA836 **77.93° a 12.793 MHz**;
U105A **60.68° a 220.315 MHz**, U105B **61.73° a 217.965 MHz**.

Dudas: R_SW, C_pad y memoria de C_S son supuestos; se omiten ruido,
cuantización, mismatch y jitter. Los SFDR muy altos dependen del suelo
numérico y no caracterizan silicio. C2 excede el límite en **52.524 mV**;
C3/C4 no lo sustituyen. R_ADC, C_ADC y ciclos de adquisición podrían
moverlo; no se eligió ni simuló remedio. Pendiente auditoría de Claude.
