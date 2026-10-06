# Plan de simulación S9 — CH2/CH3 a 1 MHz, con la AD8039 y el LM6172 como variante

- Autor: Claude Code (auditor), 4 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S9.md`.
- Continúa S7b. **Lee antes:** en `../CH1_entrada/`: `PLAN_SIMULACION_S7b.md`, `ACTA_S7b.md`, `ACTA_S7c.md`, `REVISION_CLAUDE_CH1.md`, `PLAN_SIMULACION_S6.md` y `ACTA_S6.md`; en `ai-context/DECISIONS.md`, las entradas del 2 oct («CH1 a 2 MHz y CH2/CH3 a 1 MHz»), del 3 oct (criterio de tolerancias) y del 4 oct (variante LM6172).

## 1. Qué es CH2/CH3 y qué cambia respecto a CH1 (S7b)

CH2 y CH3 son **iguales a CH1** desde la BNC hasta la etapa final: entrada, ÷100, rama ×1, protecciones, OPA810, escalera, 74HC4051, VCHECK, 470 Ω + BAV99, rieles de ±4.90 V, OPA836, VMID, DAC y red del pin (68 Ω + 470 pF). La base es `../CH1_entrada/comun/ch1_comun_s7b.inc`, **incluida tal cual (sólo lectura)**. Cambian tres cosas:

1. **Filtro anti-alias (U105) a 1.0 MHz a −3 dB de la cadena entera (BNC → pin).** Mismos condensadores que CH1 (56 / 47 pF y 220 / 56 pF). Punto de partida: RFILT1 ≈ 2.49 kΩ y RFILT2 ≈ 1.10 kΩ (sección D del documento vivo). Es sólo un punto de partida: el filtro de CH1 compensaba los polos del resto de la cadena, y a 1 MHz esos polos quedan relativamente más lejos, así que el factor de escala no es exactamente el del cociente de frecuencias. Elige los valores **E96** con el barrido de K1.
2. **Muestreo con un solo ADC (ADC3 o ADC4) a 3.47 MSa/s:** f_ADC = 52 MHz, **2.5 ciclos de muestreo (48.1 ns)** y 12.5 de conversión: 15 ciclos = 288.5 ns por muestra. Sin entrelazado. La red del pin no cambia.
3. **Dos variantes de amplificador para U103 (ganancia ×5 / ×10) y U105 (filtro):**
   - **Variante A:** AD8039, como CH1 (modelo `AD8038_ltspice.sub`; `AD8038_ltspice_ruido_hoja.sub` para ruido, como en S7).
   - **Variante B:** **LM6172** (TI, C180430), dual, ±15 V, 12 nV/√Hz. **Ojo: a ±5 V su hoja da 70 MHz de ancho de banda unitario** (100 MHz sólo a ±15 V), y por eso se descartó en CH1 (DECISIONS 3 oct). En CH2/CH3 el mínimo es 50 MHz (C.4). Diferencial de entrada ±10 V según la nota de Claude del 3 oct (`ai-context/journal/2026-10-03-claude-s3-u103.md`); verifícalo en la hoja. Estimación de Claude a mano: ≈ 0.35 % de división de ruido en 5 mV/div a 1 MHz (0.50 % a 2 MHz en CH1 × √(1.57/3.15)). Modelo de fabricante de TI en `Simulation_LTSpice/models/LM6172/` y hoja de datos en `datasheet - componentes/` (las deja Keneth; **no descargues nada**). Usa un envoltorio con el orden de pines del símbolo (`In+ In− V+ V− OUT`), como hace `models/LEEME.md`, y **comprueba el orden de pines de la cabecera del fichero de TI** con una prueba de seguidor en continua antes de usarlo.
   - Las dos variantes llevan **los mismos valores de resistencias y condensadores**, incluido el 470 Ω + BAV99 en IN+ de cada etapa. Los valores del filtro se eligen en A y se aplican en B. Si con esos valores B queda fuera de 1.0 MHz ± 10 % en nominal, reoptimiza B por separado **e informa de los dos juegos**; no elijas tú cuál se queda.

OPA810 (U101) y OPA836 (U106) no cambian en ninguna variante.

Pregunta abierta que **no** es de S9: el disparo de CH2/CH3 (PE9/PE15 no llegan a ningún comparador). Se resuelve en el mapa de pines (PLAN, paso 8).

## 2. Datos de la hoja del LM6172 que hay que citar

Extrae de la hoja (con página y tabla) y ponlos en el acta antes de simular: alimentación mínima y máxima, máximo absoluto de tensión de alimentación y de **tensión diferencial de entrada**, corriente de entrada máxima, offset máximo, corriente de polarización máxima, excursión de salida a ±5 V, ruido de tensión y de corriente, consumo por amplificador, estabilidad a ganancia 1 y carga capacitiva. Compara cada dato con el macromodelo (seguidor, ganancia ×10, consumo y ruido en continua) e informa de las diferencias, como se hizo con el AD8038 y el OPA810.

Comprueba también la regla de Keneth: **≤ 80 % de la tensión máxima** (9.8 V de rieles, 10.0 V en el peor extremo) y ≤ 50 % de corriente en las protecciones.

## 3. Pruebas (cada una en las dos variantes, salvo que se diga)

| # | Qué | Casos |
|---|---|---|
| K0 | Validación del modelo LM6172 | Seguidor en continua (orden de pines), ×10 en alterna, consumo, ruido a 100 kHz y 1 MHz, frente a la hoja (§2) |
| K1 | Barrido del filtro y respuesta nominal | Barre RFILT1 y RFILT2 (E96, con el cociente de partida fijo y luego ajuste fino) en 5 mV/div y 0.5 V/div; con los valores elegidos, las **12 escalas**: −3 dB, pico, retardo de grupo de 10 kHz a 1 MHz, atenuación a **1.73 MHz (Nyquist)** y **2.47 MHz (3.47 − 1 MHz, primer alias de la banda)**, rebote por encima de 2.47 MHz y ganancia en continua por escala, con signo |
| K2 | Escalón | Subida 10–90 % y sobreimpulso en las 12 escalas |
| K3 | Ruido | 12 escalas, BNC a masa, hasta 10 MHz, en % de división; con y sin el ruido del ADC (0.40–0.61 mV rms, como S7) |
| K4 | Muestreo de 2.5 ciclos con un ADC | El modelo de S6 (P, Z y R; R_SW ∈ {400, 825, 1500 Ω}) con t_s = 48.1 ns y 288.5 ns por muestra; seno a fondo de escala de 0.5 y 1 MHz coherente con 3.47 MSa/s (N = 1024, M impar). Sólo variante A: la red del pin y el OPA836 son los mismos en B |
| K5 | Monte Carlo | 500 casos por escala, semilla fija, el reparto de S7b §2 (incluidos los rieles ±2 % y VREF+). Offsets uniformes dentro del máximo de la hoja: AD8039 ±3 mV y **LM6172 con el máximo de su hoja, citado**. 5 mV/div, 50 mV/div, 0.5 V/div y 5 V/div: −3 dB, pico, atenuación a 2.47 MHz, ganancia y offset en continua antes de calibrar; ruido en 5 mV/div y 0.5 V/div con un subconjunto de 100 casos. **El trimmer no se repite** (la entrada es la de CH1; S7c) |
| K6 | Protecciones y recuperación | Repite J5/K3 de S7b (±40 V en continua en 5 escalas, rieles en 4.80 y 5.00 V) y E5b (±100 V, POS 1 y 100), y la recuperación J6/K4. En B, los diferenciales de U103/U105 frente al máximo de la hoja del LM6172 y las corrientes por los BAV99 |
| K7 | Offset compensable | En el Monte Carlo: ¿el DAC (0.2–2.3 V) compensa el offset de cada placa y deja ±4.5 div de posición? En B cuenta la corriente de polarización del LM6172 por las resistencias de ganancia y del filtro |
| K8 | Consumo | Por amplificador y por canal en cada variante, frente a REVISION_CLAUDE_CH1 R3 (7.7 mA por riel con AD8039) |

## 4. Criterios de aceptación (funcionales; ≥ 95 % de las placas; cada variante por separado)

| # | Criterio | Prueba |
|---|---|---|
| S9-C1 | −3 dB en **1.0 MHz ± 15 %** | K1, K5 |
| S9-C2 | Pico en la banda de paso ≤ **1 dB** | K1, K5 |
| S9-C3 | Atenuación a **2.47 MHz ≥ 20 dB** | K1, K5 |
| S9-C4 | Ruido ≤ **0.5 % de división** en las 12 escalas (AFE solo) | K3, K5 |
| S9-C5 | Ganancia en continua dentro de **±5 %** de la nominal antes de calibrar | K1, K5 |
| S9-C6 | Muestreo de 2.5 ciclos: SFDR ≥ 60 dB y error no lineal ≤ 0.5 LSB rms con R_SW = 825 Ω (informa los otros dos) | K4 |
| S9-C7 | Protecciones dentro de márgenes con los rieles en sus extremos: los de S7b-C6 y, en B, diferencial de U103/U105 ≤ 80 % del máximo absoluto del LM6172 y corriente de entrada ≤ 50 % de su máximo | K6 |
| S9-C8 | Recuperación ≤ 1 µs (sin conducción de los BAV199) | K6 |
| S9-C9 | Offset compensable con ±4.5 div de posición restante | K7 |
| — | Subida, sobreimpulso, atenuación a 1.73 MHz, retardo de grupo y consumo: informar | K1, K2, K8 |

Fallar es un resultado válido; informa siempre el valor medido y la fracción de placas. Si una variante falla, di cuánto falta y qué la movería, **sin simular remedios**.

## 5. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/CH23_entrada/`:

1. `comun/ch23_comun_s9.inc` (incluye `../../CH1_entrada/comun/ch1_comun_s7b.inc` y define los subcircuitos del canal con el filtro parametrizado y el amplificador seleccionable por parámetro); el envoltorio del LM6172.
2. `S9/`, `ejecutar_s9.py`: 10 trabajadores, `--smoke`, **`--resume`** (salta los casos con CSV completo), `S3G4_MODELS`, columnas fijas, registros fuera de la comprobación de ficheros protegidos. En el Monte Carlo en continua, **puntos `.op` con tiempo límite y un reintento**, no barridos `.dc` (en S7b se colgaron).
3. `resultados/s9_*.csv`, `resultados/s9_tabla_calibracion_A.csv` y `_B.csv` (escala, relé, toma, ganancia medida, nominal, signo).
4. `ACTA_S9.md` con la tabla de criterios **lado a lado A | B** y una tabla de diferencias (ruido, offset, consumo, márgenes de protección).
5. Tu diario en `ai-context/journal/`, abierto al empezar.

## 6. Lo que NO es tuyo

No cambies valores fuera del §1. No elijas variante ni remedios. No modifiques `../CH1_entrada/` (ni su `comun/`), `Simulation_LTSpice/models/` (salvo leerlo), `STATE.md` ni `DECISIONS.md`. No descargues nada: si falta el modelo o la hoja del LM6172, haz toda la variante A, deja B preparada y dilo.

## 7. Cómo voy a auditar

1. Reejecución de `--smoke` comparando CSV.
2. Que la cadena de CH2/CH3 es la de S7b salvo el §1 (diff de netlists generadas).
3. El orden de pines del LM6172 y K0 frente a la hoja.
4. Que el estímulo de cada `.meas` llega al caso que dice (escala, variante, caso de Monte Carlo).
5. La temporización de K4 (48.1 ns / 288.5 ns) y la coherencia del seno.
6. Reparto y semilla del Monte Carlo y offsets dentro de los máximos citados.
