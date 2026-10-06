# Plan de simulación S4 — etapa final a 3.3 V con offset (P8)

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S4.md`.
- Continúa S3b. **Lee antes:**
  - `PLAN_SIMULACION_S3b.md`, `ACTA_S3b.md` y `AUDITORIA_CLAUDE_S3b.md` (sobre todo §5: la cadena final protegida);
  - las entradas del 3 oct de `ai-context/DECISIONS.md`;
  - la §6 de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (E16);
  - los bloques ⑦ y ⑨ de `S3G4_LAB_rev2.1/01_diseno/canal_rapido_ch1.html`;
  - P14 y P15 de `S3G4_LAB_rev2.1/02_referencias/g473_analogico.html`.

## 0. Antes de lanzar (hecho por Claude, 3 oct)

1. **Modelo:** `Simulation_LTSpice/models/OPA836/opa836_a.lib` (TI SLOM218, Rev. A 2020), `.subckt OPA836 IN+ IN- OUT VCC VEE Vnot_pd`. Son **seis nodos**: el último es la pata de encendido (a VDDA = encendido). Hoja: `datasheet - componentes/opa836.pdf` (SLOS712J).
2. **Comprobación** (`chequeo_claude/s4/`):
   - seguidor a 3.3 V: −3 dB en 66 MHz;
   - ruido: 4.74 nV/√Hz a 100 kHz y a 1 MHz (hoja: 4.6). **No hace falta corregirlo**;
   - S4 con los valores de §2: ganancia −1.000, centro 1.235 V con V_DAC = 1.25 V, offset de +1.303 V / −1.214 V (recortado en 0 V). El pin del ADC va de 0.004 a 3.29 V en todo el barrido de ±5 V;
   - **pico de +1.5 dB hacia 11 MHz**, por la capacidad del nodo sumador con las resistencias de 10 kΩ. Con **C_F = 1 pF en paralelo con R_F** desaparece: −3 dB en 10.8 MHz y −0.08 a −0.10 dB a 2 MHz. Se simulan las dos variantes (§2.3);
   - **el modelo no incluye los diodos internos entre las entradas** que describe la hoja (p. 26): la diferencial llega a 1.49 V con 16 µA. Hay que añadirlos (§2.3).

## 1. Decisiones de Keneth (3 oct) que fija este plan

- **P8 adoptado:** una etapa final por canal, alimentada desde **VDDA = 3.3 V** (la del ADC). No puede sacar más de 3.3 V (P14).
- **Offset desde el DAC del G473 con buffer:** un canal por osciloscopio (DAC1 en PA4/PA5, DAC2 en PA6). Salida de 0.2 V a VREF+ − 0.2 V = 2.3 V; carga ≥ 5 kΩ y ≤ 50 pF (DS12712 T.69).
- **Amplificador: OPA836** (TI, C111589, SOT-23-6): 205 MHz, 560 V/µs, 4.6 nV/√Hz, 0.95 mA, salida rail-to-rail, con pata de apagado.

## 2. Circuito (CH1)

**Sumadora inversora con la entrada no inversora en VMID:**

```
           R_IN 10.0 k                R_F 10.0 k
U103B ──────/\/\──────┬──────────────/\/\────────┐
                      │   ┌────────┐             │
DAC ─────/\/\─────────┤   │        │             │
        R_OFF 8.06 k  └───┤−       │             │
                          │ OPA836 ├──┬──────────┴── R_ADC 68 Ω ──┬── pin ADC (PA0)
                  VMID ───┤+       │  │                           │
                          └────────┘  │                         C_ADC 470 pF
                         VDDA 3.3 V / GND                         │
                                                                  GND
```

- V_ADC = (1 + R_F/R_IN + R_F/R_OFF) · VMID − (R_F/R_IN) · V_in − (R_F/R_OFF) · V_DAC = **3.241 · VMID − V_in − 1.241 · V_DAC**.
- **Signo:** la cadena entera queda invertida (×−50.55). El firmware lo deshace. Es una decisión de diseño, no un fallo.
- **VMID** sale de VREF+ (REF3325, 2.5 V; P9, ratiométrico) con un divisor 10.0 kΩ / 5.23 kΩ: **0.8585 V** (el ideal es 0.8643 V). El centro de la pantalla con V_DAC = 1.25 V queda en 1.2313 V (−0.075 div); lo corrige la calibración. **Calcula todo con .param desde los valores**, sin escribir resultados a mano.
- **Rango de offset:** V_DAC de 0.2 a 2.3 V da ±5.21 div. Cumple RF-14 (±5 div) con un margen de 0.21 div para corregir offsets propios.
- **Ganancia de ruido:** 1 + R_F/(R_IN ∥ R_OFF) = 3.24. Con el OPA836, unos 63 MHz de −3 dB.
- **Carga:** R_ADC 68 Ω + C_ADC 470 pF (bloque ⑨), y detrás 5 pF del condensador de muestreo, estático. El retroceso de carga del muestreo (*kickback*) va en S6.
- **Alimentación:** VDDA = 3.3 V ideal con 100 nF + 1 µF; GND. Pata PD del OPA836 a VDDA (encendido).

### 2.1 La cadena delante

Para las pruebas integradas, la cadena de S3b con la protección final (variante G de la auditoría de S3b):

- `comun/ch1_comun_s3b.inc` sin cambios;
- **470 Ω + BAV99 en U103A y U103B**. El modelo y el subcircuito están en `chequeo_claude/s3b/y_b3_g_*.cir`: `BAV99HY` de Rohm (librería estándar de LTspice) y `PROTECT_BAV99`. Cópialos a `comun/ch1_comun_s4.inc`, citando la fuente, sin cambiar valores;
- `.noise` con `AD8039/AD8038_ltspice_ruido_hoja.sub`; el resto, con `AD8038_ltspice.sub`.

### 2.2 Dos variantes de VMID

En saturación, los diodos internos entre las entradas del OPA836 (hoja, p. 26) conducen. La corriente del nodo sumador va entonces a VMID. Esta tabla es la estimación de Claude de la diferencial **sin** diodos; Codex debe medirla con el modelo:

| V_in | V_DAC | Diferencial sin diodos |
|---|---|---|
| +3.9 V | 0.2 / 1.25 / 2.3 V | 0.44 / 0.84 / **1.24 V** |
| −3.9 V | 0.2 / 1.25 / 2.3 V | **−0.98** / −0.58 / −0.18 V |

El máximo absoluto es **1 V de diferencial y 0.85 mA de corriente de entrada** (hoja, p. 8).

| Variante | VMID |
|---|---|
| **M1** | Un divisor por canal (10.0 k / 5.23 k) con 1 µF en VMID |
| **M2** | Un divisor común con un seguidor (otro OPA836) que alimenta los tres VMID a través de 49.9 Ω, con 1 µF + 100 nF en cada VMID |

Para M2, simula tres etapas S4 (CH1, CH2 y CH3) colgando del mismo VMID, con CH2 y CH3 en reposo (V_in = 0, V_DAC = 1.25 V).

### 2.3 Compensación y diodos internos

- **C_F**, en paralelo con R_F: variantes **C0 = sin C_F** y **C1 = 1 pF C0G** (§0). Se cruzan con M1 y M2 en las pruebas donde importan: F2, F3, F5 y F6 con C0 y C1; F1, F4 y F7 sólo con C1. Mantén los 1 pF de pista en el nodo sumador.
- **Diodos entre IN+ e IN−:** el macromodelo no los trae y la hoja dice que existen. Ponlos en el envoltorio del OPA836, uno en cada sentido, con `.model DESD_OPA836 D(Is=1e-15 N=1 Rs=10)`. Es una **suposición de modelado**, no una pieza: dila en el acta. Para F1 y F4, repite también sin ellos e informa la diferencia.

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| F0 | S4 aislada, transferencia en continua | V_in de −1.25 a +1.25 V en pasos de 0.05 V × V_DAC ∈ {0.2, 0.725, 1.25, 1.775, 2.3 V}; M1 |
| F1 | Límites del pin y de la entrada del OPA836, `.dc` | V_in de −5 a +5 V en pasos ≤ 20 mV × V_DAC ∈ {0.2, 1.25, 2.3}; M1 y M2 |
| F2 | Respuesta en frecuencia | S4 aislada (M1) e integrada desde la BNC a 5 mV/div y 0.5 V/div; de 1 Hz a 100 MHz, ≥ 50 puntos por década |
| F3 | Recuperación | S4 aislada: escalón de V_in a ±3.9 V de 10 µs. Integrada: 5 mV/div con pulsos de ±2 y ±4.5 V en la BNC (como B4 de S3b). M1 y M2 |
| F4 | Interferencia entre canales por VMID | M2: CH1 con V_in = ±3.9 V sostenido; CH2 y CH3 en reposo; mide el cambio de VMID y el de la salida de CH2/CH3 |
| F5 | Gran señal | Integrada, 5 mV/div: seno de 2 MHz con 8 div pp (2 Vpp en el ADC), con offset de 0 y de ±2 div |
| F6 | Ruido | Integrada, `.noise` desde la BNC en las 12 escalas; integral de 1 Hz a 3.15 MHz en el pin del ADC (antes de los 5 pF) |
| F7 | Secuencia de encendido | (a) `.op` con VDDA = 0 y ±5 V presentes, V_in = ±3.9 V, V_DAC = 0; (b) VDDA en rampa de 0 a 3.3 V en 1 ms con V_in = ±1 V y V_DAC siguiendo a VREF+ |

## 4. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S4-C1 | Ganancia −1 ± 1 %; no linealidad ≤ 0.05 % de 2.5 V en F0; rango de offset ≥ ±5 div en el ADC | F0 |
| S4-C2 | **Pin del ADC entre 0 y VDDA** (P14) en todo F1 y F7; informar el mínimo y el máximo | F1, F7 |
| S4-C3 | Entradas del OPA836: corriente ≤ **0.43 mA** (50 % de los 0.85 mA de la hoja) y tensión dentro de VS ± 0.7 V; diferencial informada frente a 1 V | F1, F7 |
| S4-C4 | S4 aislada: pérdida a 2 MHz ≤ 0.1 dB (sin contar el RC del ADC) y pico ≤ 0.5 dB; integrada: pico ≤ 0.5 dB e informar la pérdida total de BNC al pin | F2 |
| S4-C5 | Recuperación a ±0.1 div ≤ 1 µs | F3 |
| S4-C6 | M2: cambio en la salida de CH2/CH3 ≤ 0.1 div con CH1 saturado. M1: informar el cambio de VMID durante y después | F4 |
| S4-C7 | THD ≤ 1 % en el pin del ADC | F5 |
| S4-C8 | Ruido total de CH1 ≤ 0.45 % de división en las 12 escalas, con S4 incluida | F6 |
| — | Consumo del OPA836 (y del seguidor en M2); corriente que VMID pide a VREF+ | todas |

Fallar es un resultado válido; informa siempre el valor medido. **No elijas variante de VMID ni de C_F.**

## 5. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, sin tocar S1…S3b:

1. `comun/ch1_comun_s4.inc`, que incluye `ch1_comun_s3b.inc` y añade la protección final de U103 y la etapa S4.
2. `S4/` con los `.cir`.
3. `ejecutar_s4.py`, paralelo (10 trabajadores), con `--smoke` y `S3G4_MODELS`.
4. `resultados/s4_*.csv` y `resultados/s4_resumen.md`.
5. `ACTA_S4.md`, con:
   - criterios por variante;
   - la ecuación de transferencia medida (ganancia, centro y rango de offset);
   - los extremos del pin del ADC;
   - dudas y contradicciones;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`.

## 6. Lo que NO es tuyo

- No cambies valores (R_IN, R_F, R_OFF, divisor de VMID, R_ADC, C_ADC ni la cadena delante). No añadas protecciones ni filtros, salvo C_F y los diodos de modelado de §2.3.
- No diseñes el filtro anti-alias (S5) ni el muestreo del ADC (S6).
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 7. Cómo voy a auditar

1. Reejecución en ruta corta con `S3G4_MODELS`, CSV byte a byte.
2. Orden de nodos del OPA836 y que su pata PD está activa.
3. La ecuación de F0 contra la de §2, calculada desde los valores.
4. Que F1 y F7 cubren V_DAC en los extremos, que es donde la diferencial es peor, y que el pin del ADC se mide en el pin, no a la salida del OPA836.
5. Que F4 usa tres etapas reales sobre el mismo VMID.
