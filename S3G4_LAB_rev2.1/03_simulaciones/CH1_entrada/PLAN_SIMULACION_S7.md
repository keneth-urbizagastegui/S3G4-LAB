# Plan de simulación S7 — canal CH1 completo, de la BNC a PA0 (E19)

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S7.md`.
- **Lee antes:**
  - las auditorías `AUDITORIA_CLAUDE_S1.md` … `AUDITORIA_CLAUDE_S6.md`;
  - las entradas del 3 oct de `ai-context/DECISIONS.md`;
  - la §6 de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (E19).
- Es la integración: **no se diseña nada nuevo**. Se junta lo decidido y se verifica de punta a punta.

## 1. El canal, tal como está decidido

| Bloque | Contenido | Fuente |
|---|---|---|
| Entrada P4b | `FRONT_S2B` sin cambios (divisor 2 × 549 k + 11 k, Ct, trimmer en el centro, Cb, R_S ∥ C_S, relé, réplica R_EQ ∥ C_EQ, BAV199, C_AC, R_BIAS, R_PROT 1 kΩ) | `comun/ch1_comun_s2b.inc` |
| Buffer | OPA810 seguidor | S2b |
| Escalera y 4051 | RL1…RL6 y 8 × `SWI1` de Nexperia (`hc_tnomi`) | `comun/ch1_comun_s3.inc` |
| Ganancia | AD8039: 1.00 k / 249 Ω y 2.26 k / 249 Ω; **470 Ω + BAV99 (BAV99HY) en IN+ de U103A y de U103B** | S3, S3b; `chequeo_claude/s3b/y_*_g_*.cir` |
| **Sin carga ficticia** | **Quita el 1 kΩ ∥ 10 pF de la salida de U103B** (sustituto de S4 desde S3) | AUDITORIA_S5 §3 |
| Filtro U105 | AD8039, **TR reescalado**: sección 1 (Q bajo, primera), R = 1.11 kΩ, C1 = 56 pF, C2 = 47 pF; sección 2, R = 499 Ω, C1 = 220 pF, C2 = 56 pF; 1 pF de pista en cada IN+ | DECISIONS 3 oct |
| S4 | OPA836 a VDDA = 3.3 V; R_IN = R_F = 10.0 kΩ, **C_F = 1 pF**, R_OFF = 8.06 kΩ; VMID M1 (10.0 k / 5.23 k desde VREF+ = 2.5 V, 1 µF); PD a VDDA; diodos `DESD_OPA836` entre las entradas | S4 |
| Pin del ADC | 68 Ω + 470 pF; C_pad 5 pF; en las pruebas de muestreo, el modelo de S6 (R_SW = 825 Ω, C_S = 5 pF, ADC1/ADC2 entrelazados, estado P) | S6 |
| Rieles | ±5 V con `RAILS_S2B` (POWER = 1); VDDA = 3.3 V y VREF+ = 2.5 V ideales; V_DAC = 1.25 V salvo en J8 | — |

- `.noise` con `AD8038_ltspice_ruido_hoja.sub`; lo demás, con los modelos originales.
- Escribe `comun/ch1_comun_s7.inc` con todo esto. Los valores van como `.param`, para que la tabla del §1 salga del fichero.

## 2. Pruebas

| # | Qué | Casos |
|---|---|---|
| J1 | Respuesta en frecuencia BNC → pin | 12 escalas; de 1 Hz a 200 MHz. −3 dB, pérdida a 1 MHz, atenuación a 3.25 / 4.5 / 6.5 MHz, pico, rebote por encima de 4.5 MHz, retardo de grupo de 10 kHz a 2 MHz y **ganancia en continua por escala** (tabla para la calibración, con signo) |
| J2 | Escalón y cuadrada | 12 escalas: escalón de 1 div (2 ns de subida) y cuadrada de 100 kHz de 6 div: subida 10–90 %, sobreimpulso y asentamiento a 0.5 % |
| J3 | Monte Carlo | 5 mV/div y 0.5 V/div; 300 casos (semilla fija): R ±1 % (divisor ±0.1 %), C del filtro ±5 %, resto de C ±5 %. Distribución del −3 dB, del pico, de la atenuación a 4.5 MHz y de la ganancia en continua |
| J4 | Ruido | 12 escalas; integral de 1 Hz a 3.15 MHz en el pin, referida a la BNC |
| J5 | Límites en saturación (`.dc`) | BNC de −40 a +40 V en 5 mV, 10 mV, 200 mV, 0.5 V y 20 V/div: entradas de OPA810, U103A, U103B, U105A, U105B y OPA836 (tensión, diferencial y corriente) y pin del ADC |
| J6 | Recuperación | 5 mV/div: pulsos de ±0.2, ±2 y ±4.5 V; 0.5 V/div: ±20 y ±40 V; 10 µs; recuperación a ±0.1 div |
| J7 | Gran señal muestreada | 5 mV/div y 0.5 V/div; seno coherente de ≈ 1 y ≈ 2 MHz con 8 div pp en el ADC; 1024 muestras con el modelo de S6: SFDR, THD y error no lineal |
| J8 | Offset | 5 mV/div, entrada 0: V_DAC de 0.2 a 2.3 V en 9 pasos; posición de la traza en div |
| J9 | Consumo | Reposo y seno de 2 MHz a fondo de escala: corriente de cada amplificador por riel, del 4051, de los divisores de VMID (desde VREF+) y del DAC. Total por riel y por canal |

## 3. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S7-C1 | −3 dB en **2.0 MHz ± 10 %** en las 12 escalas; pico ≤ 0.5 dB; sin rebote | J1 |
| S7-C2 | Monte Carlo: ≥ 95 % de los casos dentro de 2.0 MHz ± 10 % | J3 |
| S7-C3 | Subida 10–90 % de **175 ns ± 20 %** | J2 |
| S7-C4 | Ruido ≤ 0.45 % de división en las 12 escalas | J4 |
| S7-C5 | Ningún límite de §2 de las auditorías superado: OPA810 \|I\| ≤ 10 mA (S2b); diferencial de U103A/B y U105A/B ≤ 2 V; corriente de entrada del OPA836 ≤ 0.43 mA; pin entre 0 y VDDA | J5 |
| S7-C6 | Recuperación ≤ 1 µs siempre que no conduzcan los BAV199 de entrada; informa aparte los casos en que conducen (aceptados ≈ 0.6 ms) | J6 |
| S7-C7 | SFDR ≥ 60 dB y error no lineal ≤ 0.5 LSB rms en la secuencia muestreada | J7 |
| S7-C8 | Offset de +5 / −4.8 div o más, con una relación lineal con V_DAC | J8 |
| S7-C9 | Ganancia en continua de cada escala dentro de ±3 % de la nominal (0.25 V/div); infórmala con signo para la calibración | J1 |
| — | Consumo por etapa y por canal, comparado con G.3 del documento vivo (3.9 mA por amplificador supuestos) | J9 |

Fallar es un resultado válido; informa siempre el valor medido.

## 4. Entregables

1. `comun/ch1_comun_s7.inc`, `S7/`, `ejecutar_s7.py` (10 trabajadores, `--smoke`, `S3G4_MODELS`, orden de columnas fijo, registros fuera de la comprobación de ficheros protegidos).
2. `resultados/s7_*.csv`, `resultados/s7_resumen.md` y **`resultados/s7_tabla_calibracion.csv`** (escala, relé, toma, ganancia medida, ganancia nominal, signo).
3. `ACTA_S7.md`, el **acta final de CH1**:
   - la lista de piezas del canal con sus valores;
   - criterios;
   - tablas por escala;
   - consumo;
   - dudas;
   - tiempo y código de salida.
4. Tu diario en `ai-context/journal/`, abierto al empezar.

## 5. Lo que NO es tuyo

- No cambies valores. Si algo falla, di cuánto falta.
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 6. Cómo voy a auditar

1. Reejecución en ruta corta y comparación de los CSV.
2. Que el canal del §1 es el decidido: el filtro reescalado, sin la carga ficticia, con las protecciones de U103 y con C_F.
3. Que el −3 dB se mide de la BNC al pin y que la tabla de ganancias tiene signo.
4. J5 con los extremos en todas las escalas pedidas.
5. El consumo frente al recuento de G.3.
