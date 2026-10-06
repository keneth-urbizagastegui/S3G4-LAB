# Plan de simulación S3b — protección de la diferencial de U103A

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S3b.md`.
- Continúa S3. **Lee antes:** `PLAN_SIMULACION_S3.md`, `ACTA_S3.md`, `AUDITORIA_CLAUDE_S3.md` (sobre todo §3, §4 y §5) y las entradas del 3 oct de `ai-context/DECISIONS.md`.

## 1. Qué cambia respecto a S3

1. **Protección de U103A** (decisión de Keneth, 3 oct, opción (a) de la auditoría): una resistencia **R_SER** entre el común del 4051 (nodo `COMMON`, con sus 3 pF de pista) y la entrada no inversora de U103A, y un **par de diodos en antiparalelo entre las dos entradas** de U103A.
   - El par sale de un doble en serie en SOT-23 (pines 1 y 2 unidos a un nodo, pin 3 al otro): un diodo de IN+ a IN− y el otro de IN− a IN+.
   - El resto del circuito es el de S3, sin cambios: `comun/ch1_comun_s3.inc` (inclúyelo, no lo copies).
2. **Variantes**, 2 × 2:

   | Variante | R_SER | Diodos | Modelo |
   |---|---|---|---|
   | A | 470 Ω | BAT54S (Schottky) | `BAT54` de la librería estándar de LTspice (`standard.dio`, Vishay: Is 0.1 µA, Cjo 12 pF) |
   | B | 1.00 kΩ | BAT54S | ídem |
   | C | 470 Ω | BAV199 (silicio, baja fuga, ya en la lista de piezas) | `.MODEL BAV199` de `comun/ch1_comun_s2b.inc` |
   | D | 1.00 kΩ | BAV199 | ídem |

   Keneth eligió Schottky. BAV199 entra como comparación porque ya está en la lista de piezas, tiene modelo de fabricante y casi no tiene capacidad ni fuga. Elige Keneth con los resultados.
3. **Ruido con el modelo corregido:** `.noise` usa `Simulation_LTSpice/models/AD8039/AD8038_ltspice_ruido_hoja.sub` (8 nV/√Hz, como la hoja; ver `models/LEEME.md`). El resto de análisis, el original `AD8038_ltspice.sub`. Como control, repite E12 de 5 mV/div de S3 sin protección con los dos modelos: deben salir 0.396 % (corregido) y 0.644 % (original).
4. **E14 en dos partes,** para no repetir los fallos de S3:
   - **barrido estático** para los límites. El transitorio con ±40 V no converge con `SWI1`;
   - **transitorio sólo hasta ±4.5 V**, por debajo de la conducción de los BAV199 de entrada. La recuperación tras conducir los BAV199 (≈ 0.6 ms) está **aceptada por Keneth** (DECISIONS 3 oct) y no se vuelve a medir.

## 2. Pruebas

Todas con el 4051 de Nexperia (`hc_tnomi`) y las cuatro variantes, salvo donde se indica.

| # | Qué | Casos |
|---|---|---|
| B0 | Etapa U103A aislada con R_SER y diodos, como la comprobación aislada de S3 | AC: ganancia en continua, −3 dB y pico. Por variante |
| B1 | Respuesta en frecuencia (E11) | 12 escalas, CPL = DC; de 1 Hz a 100 MHz |
| B2 | Ruido (E12), modelo corregido | 12 escalas, fuente de 50 Ω, integral de 1 Hz a 3.15 MHz (y a 10 MHz, sin criterio). Más los dos controles de §1.3 |
| B3 | Límites en saturación, `.dc` | BNC de −40 a +40 V en pasos ≤ 50 mV, en 5 mV/div (×1, toma 1) y 10 mV/div (×1, toma 1/2) |
| B4 | Recuperación, transitorio | 5 mV/div; pulsos de ±0.2 V (10 × FS), ±2 V y ±4.5 V, de 10 µs, flancos de 10 ns; paso ≤ 1 ns en los flancos y en los 5 µs siguientes |
| B5 | Gran señal (E13) | 5 mV/div y 0.5 V/div; seno de 2 MHz con 2 Vpp en la salida |
| B6 | Offset en continua que añaden los diodos | `.op` con la BNC a 0 V, a 25 °C y a 70 °C, en 5 mV/div y 200 mV/div; frente a S3 sin protección. En divisiones |

Medidas de B3, por variante y escala:
- diferencial de entrada pico de U103A y de U103B;
- corriente pico de cada diodo;
- corriente por el interruptor del 4051 (`VIA` o equivalente en el nodo `COMMON`);
- corriente de salida del OPA810;
- tensión de IN+ de U103A frente a los rieles.

## 3. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S3b-C1 | Diferencial de U103A ≤ **2.0 V** (50 % del máximo absoluto de ±4 V, hoja p. 5) en todo el barrido; U103B ≤ 4 V (informar el margen) | B3 |
| S3b-C2 | Corriente por el interruptor del 4051 ≤ **12.5 mA** (50 % de los ±25 mA de I_SW, hoja `74HC_HCT4051.pdf` p. 5); corriente de cada diodo ≤ 50 % de su I_F continua de hoja; corriente de salida del OPA810 informada frente a su hoja | B3 |
| S3b-C3 | Ruido ≤ **0.45 %** de división en las 12 escalas, con el modelo corregido | B2 |
| S3b-C4 | Pérdida a 2 MHz ≤ 0.5 dB y pico ≤ 0.5 dB en las 12 escalas | B0, B1 |
| S3b-C5 | Recuperación a ±0.1 div ≤ 1 µs tras cada pulso | B4 |
| S3b-C6 | THD ≤ 1 % a 2 Vpp y 2 MHz | B5 |
| — | Offset añadido por los diodos a 25 y 70 °C, en divisiones; comparación con S3 | B6 |

Fallar es un resultado válido; informar siempre el valor medido. **No elijas variante.** Da la tabla con las cuatro y di cuáles pasan todo.

## 4. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, **sin modificar los entregables de S1…S3**:

1. `comun/ch1_comun_s3b.inc`, que **incluye** `ch1_comun_s3.inc` y añade R_SER y los diodos como parámetros de variante.
2. `S3b/` con los `.cir` generados.
3. `ejecutar_s3b.py`, paralelo (10 trabajadores) desde el principio, con `--smoke` y `S3G4_MODELS`.
4. `resultados/s3b_*.csv` y `resultados/s3b_resumen.md`.
5. `ACTA_S3b.md`, con:
   - criterios S3b-C1…C6 por variante;
   - tabla por escala y variante: pérdida a 2 MHz, pico y ruido;
   - el barrido B3 con sus picos;
   - **dudas y contradicciones sin resolver**;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`.

## 5. Lo que NO es tuyo

- No cambies valores fuera de R_SER y de los diodos de §1. No añadas otras protecciones ni compensaciones.
- No elijas variante ni diseñes S4.
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 6. Cómo voy a auditar

1. Reejecución en una copia con ruta corta y `S3G4_MODELS`, y comparación de los CSV byte a byte.
2. La orientación de los diodos (uno en cada sentido entre IN+ e IN−) y que R_SER está entre `COMMON` y IN+.
3. Que `.noise` usa el modelo corregido y que los controles dan 0.396 % y 0.644 %.
4. Que B3 cubre el barrido completo y que la diferencial se mide en los pines del amplificador, no antes de R_SER.
5. Que B4 no sobrepasa ±4.5 V y que la recuperación se mide desde el final del pulso.
