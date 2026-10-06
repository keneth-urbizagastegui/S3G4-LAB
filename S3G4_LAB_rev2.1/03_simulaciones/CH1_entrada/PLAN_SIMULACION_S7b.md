# Plan de simulación S7b — CH1 con ±4.9 V, C_S = 1.2 nF y tolerancias reales

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S7b.md`.
- Continúa S7. **Lee antes:** `PLAN_SIMULACION_S7.md`, `ACTA_S7.md`, `REVISION_CLAUDE_CH1.md` y, en `ai-context/DECISIONS.md`, la entrada del 3 oct «Revisión de CH1: C_S, rieles del AFE y criterio de diseño con tolerancias».

## 1. Qué cambia respecto a S7

1. **Rieles del AFE a ±4.90 V** (opción A de R2): en `RAILS_S2B` y en todo lo que cuelga de ±5 V, incluido el 74HC4051. VDDA = 3.3 V y VREF+ = 2.5 V no cambian.
2. **C_S = 1.20 nF** (fijo, ya no derivado) y **C_EQ = 8.7 pF** (seleccionado en prueba; nominal 8.67 pF).
3. **Criterio permanente de Keneth: «que funcione, no la perfección».** Se juzga con tolerancias reales y se acepta si cumple en **≥ 95 % de las placas**, con criterios funcionales.

## 2. Monte Carlo ampliado (500 casos por escala, semilla fija)

| Qué varía | Cómo |
|---|---|
| Resistencias | ±1 % uniforme (divisor 549 k / 11 k: ±0.1 %) |
| Condensadores C0G | ±5 % (Ct, C_S, C_EQ, C_AC, filtro, C_F, C_ADC) |
| Cb | ±5 %, y luego **ajuste del trimmer** (§2.1) |
| Rieles | +4.90 V y −4.90 V, ±2 % cada uno, independientes |
| VREF+ | 2.5 V ±0.2 % |
| Offset de entrada de cada amplificador | fuente en serie con IN+, uniforme dentro del máximo de la hoja: OPA810 ±715 µV, AD8039 ±3 mV, OPA836 ±(máximo de su hoja, citado) |
| C de pista (1 pF y 3 pF) | ±50 % |

No hace falta variar el GBW de los macromodelos. Dilo como limitación.

### 2.1 Ajuste del trimmer en cada caso

En placa, el trimmer SEHWA (2–6 pF) se ajusta una vez por canal con la sonda ×10 (S1b). En cada caso de Monte Carlo, calcula el valor del trimmer que iguala las constantes de tiempo de arriba y de abajo del ÷100, con las mismas fórmulas de `ch1_comun_s2b.inc`. **Recórtalo a 2–6 pF** e informa del porcentaje de placas en que el rango del trimmer basta.

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| K1 | Nominal con ±4.9 V y C_S = 1.2 nF | Repite J1, J2, J4 y J8 de S7 en las 12 escalas |
| K2 | Monte Carlo del §2 | 5 mV/div, 50 mV/div, 0.5 V/div y 5 V/div: −3 dB, pico, atenuación a 4.5 MHz, ganancia y offset en continua (antes de calibrar), y ruido en 5 mV/div y 0.5 V/div con un subconjunto de 100 casos |
| K3 | Protecciones con ±4.9 V | Repite J5 (`.dc` de ±40 V en 5 escalas) con los rieles en el **peor extremo de cada lado** (4.80 y 5.00 V); repite E5b de S2b (±100 V en continua, POS 1 y 100) y comprueba el 4051 (tensión de interruptor dentro de VEE…VCC) |
| K4 | Recuperación y offset | J6 y J8 de S7 con ±4.9 V nominal |
| K5 | Rango de offset frente a los offsets reales | En el Monte Carlo: ¿el DAC (0.2–2.3 V) compensa el offset en continua de cada placa **y** deja aún ±4.5 div de posición vertical? |

## 4. Criterios de aceptación (funcionales; ≥ 95 % de las placas)

| # | Criterio | Prueba |
|---|---|---|
| S7b-C1 | −3 dB en **2.0 MHz ± 15 %** | K1, K2 |
| S7b-C2 | Pico en la banda de paso ≤ **1 dB** | K1, K2 |
| S7b-C3 | Ruido ≤ **0.5 % de división** | K1, K2 |
| S7b-C4 | Ganancia en continua dentro de **±5 %** de la nominal antes de calibrar (lo demás lo corrige la calibración) | K2 |
| S7b-C5 | El trimmer basta (2–6 pF) en ≥ 95 % de las placas | K2 |
| S7b-C6 | Protecciones dentro de márgenes con los rieles en sus extremos: OPA810 \|I\| ≤ 10 mA; diferenciales de U103/U105 ≤ 2 V; corriente de entrada del OPA836 ≤ 0.43 mA; pin del ADC entre 0 y VDDA; señal del 4051 dentro de VEE…VCC; 4051 con VCC − VEE ≤ 10.0 V | K3 |
| S7b-C7 | Recuperación ≤ 1 µs (sin conducción de los BAV199) | K4 |
| S7b-C8 | Offset compensable con ±4.5 div de posición restante | K5 |
| — | Subida, atenuación a 4.5 MHz y consumo: informar | K1 |

Fallar es un resultado válido; informa siempre el valor medido y la fracción de placas.

## 5. Entregables

`comun/ch1_comun_s7b.inc`, `S7b/`, `ejecutar_s7b.py` (10 trabajadores, `--smoke`, `S3G4_MODELS`, columnas fijas, registros fuera de la comprobación), `resultados/s7b_*.csv`, `resultados/s7b_tabla_calibracion.csv`, `ACTA_S7b.md` y tu diario, abierto al empezar.

## 6. Lo que NO es tuyo

No cambies valores fuera del §1. No elijas remedios. No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 7. Cómo voy a auditar

1. Reejecución, comparando CSV.
2. Rieles a ±4.9 V en todo el AFE, C_S = 1.2 nF y C_EQ = 8.7 pF.
3. Reparto y semilla del Monte Carlo, y las fuentes de offset dentro de los máximos de las hojas.
4. La fórmula del ajuste del trimmer y su recorte.
5. Que K3 usa los rieles en sus extremos.
