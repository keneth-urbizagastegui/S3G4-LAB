# Respuesta final S5

Campaña: **código 0, 708 simulaciones, 624.939 s**, diez trabajadores. Reproducción: código 0, 708 simulaciones, 548.763 s; **13/13 CSV idénticos**. Smoke: código 0, 57 casos verificados; 346.855 s acumulados (63 intentos nativos, 51 casos reutilizados tras verificar el deck).

Creado: `sintesis_s5.py`, `ejecutar_s5.py`, `verificar_s5.py`, `comun/ch1_comun_s5.inc`, `S5/*.cir` y sus logs, `resultados/s5_*`, `ACTA_S5.md`, esta respuesta y `ai-context/journal/2026-10-03-codex-s5.md`.

Componentes: R1=R2; C1 realimenta desde la salida, C2 va a masa. Sección 1 de Q bajo. f0/Q calculados con pasivos redondeados; comprobaciones con modelo real en el acta.

| Candidato | Sección | R (Ω) | C1 (pF) | C2 (pF) | f0 (MHz) | Q |
| --- | --- | --- | --- | --- | --- | --- |
| BE | 1 | 590 | 82 | 82 | 3.290 | 0.500 |
| BE | 2 | 576 | 120 | 47 | 3.679 | 0.799 |
| TR | 1 | 1150 | 56 | 47 | 2.698 | 0.546 |
| TR | 2 | 511 | 220 | 56 | 2.806 | 0.991 |
| BU | 1 | 1470 | 56 | 47 | 2.110 | 0.546 |
| BU | 2 | 511 | 390 | 56 | 2.108 | 1.319 |

| Criterio | BE | TR | BU |
| --- | --- | --- | --- |
| S5-C1 | PASA | PASA | PASA |
| S5-C2 | FALLA | PASA | PASA |
| S5-C3 | PASA | PASA | PASA |
| S5-C4 | PASA | PASA | PASA |
| S5-C5 | PASA | PASA | PASA |
| S5-C6 | PASA | PASA | PASA |
| S5-C7 | PASA | PASA | PASA |
| S5-C8 | PASA | PASA | FALLA |

| Medida | BE | TR | BU |
| --- | --- | --- | --- |
| −3 dB (MHz) | 1.822 | 1.951 | 1.917 |
| A 3.25 MHz (dB) | 9.50 | 11.81 | 18.38 |
| A 4.5 MHz (dB) | 17.48 | 22.59 | 30.90 |
| A 6.5 MHz (dB) | 30.26 | 37.15 | 46.09 |
| Sobreimpulso cuadrada (%) | 0.0009 | 3.203 | 8.830 |
| Subida escalón (ns) | 188.12 | 187.11 | 204.90 |
| Ruido peor escala (% div) | 0.3135 | 0.3188 | 0.3165 |
| Monte Carlo dentro de 1.8–2.2 MHz | 135/200 (67.5 %) | 199/200 (99.5 %) | 200/200 (100.0 %) |
| Corte Monte Carlo mín.–máx. (MHz) | 1.687–1.952 | 1.798–2.082 | 1.812–1.993 |

Comparativa nominal a 5 mV/div; ruido es el máximo de las 12 escalas. BU falla C8 por rec 1.08147861 us; censurados 0; diferencial 0.123698631 V. BE falla C2; no se elige candidato.

Dudas conservadas: E17 antiguo pide Butterworth de 5.º orden, mientras el contrato S5 fija 4.º activo; permanecen RLOAD=1 kΩ/CLOAD=10 pF heredados en U103B; los polos ideales de síntesis no sustituyen S4 y el RC reales. El retardo de grupo se informa de 1 kHz a 2 MHz, frente al intervalo 0–2 MHz pedido. Macromodelos y referencias/DAC ideales no certifican placa ni todo su ruido. S1–S4, modelos, STATE y DECISIONS sin cambios.

