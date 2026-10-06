# Plan de simulación S3 — buffer, escalera, 74HC4051 y ganancia ×5 · ×10

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S3.md`.
- Continúa S2b. **Lee antes:** `PLAN_SIMULACION_S2b.md`, `ACTA_S2b.md`, `AUDITORIA_CLAUDE_S2b.md`, las entradas del 3 oct de `ai-context/DECISIONS.md`, la §6 de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (E11–E15) y las secciones C.3, C.4, C.5 y C.6 de `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html`.

## 0. Antes de lanzar (hecho por Claude, 3 oct)

1. Modelos y hojas en el proyecto:
   - **AD8039:** `Simulation_LTSpice/models/AD8039/AD8038_ltspice.sub`, `.subckt AD8038 1 2 3 4 5` = IN+ IN− V+ V− OUT. Lo extrajo Claude de `ADI.lib` de LTspice (el AD8039 es el doble del AD8038). Es un modelo nativo de LTspice, simplificado: **no modela diodos entre entradas ni la corriente de polarización real**. Hoja: `datasheet - componentes/AD8038_8039.pdf`.
   - **74HC4051:** paquete de Nexperia en `Simulation_LTSpice/models/74HC4051/` (`hc_tnomi.cir`, con variantes `hc_tfast` y `hc_tslow`). Hoja: `datasheet - componentes/74HC_HCT4051.pdf`.
2. Comprobación de Claude en `chequeo_claude/s3_*.cir` (±5 V, carga 1 kΩ ∥ 10 pF):
   - seguidor a −3 dB en 361 MHz; con 4.02 k / 1 k (×5.02), 94 MHz; con 9.09 k / 1 k (×10.09), 48 MHz. Pérdida a 2 MHz < 0.02 dB;
   - **pico:** la ×5.02 con 4.02 k / 1 k, 1 pF en la entrada inversora y 10 pF de carga da **+3.7 dB**; con R_G = 249 Ω, 0 dB. Por eso cambia la red (decisión de Keneth, 3 oct; §1);
   - saturación: con 4.9 V en la entrada no inversora de la ×5, la diferencial llega a **4.28 V**, por encima de los ±4 V de la hoja. Se mide en E14 con la cadena real antes de decidir protección (decisión de Keneth, 3 oct);
   - corriente de reposo del modelo: 2.07 mA por el riel positivo (incluye la carga de la red);
   - interruptor `SWI1` de Nexperia con VCC = +5 V y VEE = −5 V: **conduce con el control a nivel bajo**. RON = 69 Ω en 0 V, 72–75 Ω en ±2 V, 97–125 Ω en ±4 V y 178 Ω como máximo en ±4.5 V.

## 1. Qué se simula

La cadena de CH1 desde la BNC hasta la salida de U103B, en las 12 escalas:

```
BNC → FRONT_S2B (S2b, sin cambios) → U101 OPA810 seguidor → escalera RL1…RL6 → U102 74HC4051 → U103A ×5.02 → U103B ×10.09 → carga
```

- **Entrada:** `FRONT_S2B` y `BUFFER_OPA810` de `comun/ch1_comun_s2b.inc`, sin tocar valores. U101 como seguidor (salida a IM).
- **Escalera:** RL1…RL6 = 499, 249, 150, 49.9, 24.9 y 24.9 Ω desde la salida de U101 a masa. Tomas 1, 1/2, 1/4, 1/10, 1/20 y 1/40. **Calcula las tomas desde los valores** (con .param o Python) e informa la relación real de cada una; no escribas 1/2, 1/4… a mano.
- **U102 74HC4051** con el modelo de Nexperia:
  - **ocho instancias de `SWI1`** (`hc_tnomi.cir`; nodos: control, Y, Z, VEE, VCC, GND) con los Z unidos en el común. Así cada canal apagado pone su capacidad sobre el común y se ve la inyección de carga real;
  - VCC = +5 V, VEE = −5 V. **El control conduce a nivel bajo:** genera los ocho controles con un decodificador comportamental de las tres líneas de dirección (0 V = cerrado, 5 V = abierto). Para E15, con un tiempo de conmutación de 30 ns y rotura antes de cierre de 20 ns, tomados de la hoja (`74HC_HCT4051.pdf`, columna de 4.5 V / −4.5 V); cita la página;
  - 8 entradas: las 6 tomas, GND (Y6) y VCHECK (Y7). VCHECK queda a masa a través de 1 kΩ en S3: su valor es P3, sin decidir;
  - variantes de proceso: `hc_tnomi` en toda la campaña; E11 a 5 mV/div y E15 también con `hc_tslow` (peor RON). Si los tres ficheros no pueden incluirse a la vez por nombres repetidos, usa uno por simulación;
  - si el modelo no converge en algún análisis (Nexperia lo declara para transitorio), sustitúyelo **sólo en ese análisis** por un interruptor comportamental con RON = 100 Ω y las capacidades de la hoja, y dilo en el acta.
- **U103A, U103B:** AD8039 (`AD8038` del modelo) a ±5 V, no inversores, **R_F1/R_G1 = 1.00 kΩ / 249 Ω y R_F2/R_G2 = 2.26 kΩ / 249 Ω** (decisión de Keneth, 3 oct, para quitar el pico; antes 4.02 k / 1 k y 9.09 k / 1 k). Ganancia ideal ×5.016 · ×10.08 = ×50.55; calcúlala desde los valores.
- **Parásitas:** 3 pF en el común del 4051 (pista) y 1 pF en cada entrada inversora.
- **Carga de U103B:** 1 kΩ ∥ 10 pF a masa (sustituto de S4, todavía sin diseñar).
- **Rieles:** `RAILS_S2B` con POWER = 1, o fuentes ideales de ±5 V con 10 µF + 100 nF. Mide la corriente de cada amplificador por su pin de alimentación.

### Las 12 escalas

| Escala | POS (relé) | Toma |
|---|---|---|
| 5, 10, 20, 50, 100, 200 mV/div | 1 | 1, 1/2, 1/4, 1/10, 1/20, 1/40 |
| 0.5, 1, 2, 5, 10, 20 V/div | 100 | 1, 1/2, 1/4, 1/10, 1/20, 1/40 |

Fondo de escala (FS) = ±4 div. A la salida de U103B, 1 div = 0.25 V.

## 2. Pruebas

| # | Qué | Casos |
|---|---|---|
| E11 | Respuesta en frecuencia por escala | 12 escalas × CPL {DC}, `hc_tnomi`; AC de 1 Hz a 100 MHz, ≥ 50 puntos por década. Además CPL = AC en 5 mV/div y 0.5 V/div, y `hc_tslow` en 5 mV/div y 200 mV/div |
| E11b | Escalón pequeño | 12 escalas, `hc_tnomi`; escalón de 1 div con 2 ns de subida |
| E12 | Ruido referido a la BNC | 12 escalas, CPL = DC, fuente de 50 Ω; `.noise` de 1 Hz a 10 MHz |
| E13 | Gran señal | 5 mV/div y 0.5 V/div; seno de 2 MHz con 2 Vpp en la salida de U103B (8 div) y, aparte, con 4 Vpp |
| E14 | Saturación y recuperación | 12 escalas; ver §2.1 |
| E15 | Conmutación del 4051 | ver §2.3 |

### 2.1 E14, saturación

- Pulso en la BNC de amplitud **min(10 × FS, 40 V)**, positivo y negativo, de 10 µs, con flancos de 10 ns. 10 × FS es ±40 div: ±200 mV a 5 mV/div; en las escalas altas manda el límite de 40 V (RF-07, que ya pasó S2b).
- Mide desde el final del pulso:
  - el tiempo hasta que la salida de U103B entra y se queda en ±0.1 div (25 mV) de su valor final;
  - aparte, el mismo tiempo con ±0.5 div.
- Durante el pulso, en U103A y en U103B:
  - **tensión diferencial de entrada** (pico) y **corriente de cada entrada** (pico);
  - tensión en la entrada no inversora frente a los rieles.
- En U101, la misma comprobación que en S2b (corriente de entrada y diferencial).

### 2.2 Límites del AD8039 (hoja `AD8038_8039.pdf`, Rev. G)

| Magnitud | Valor de la hoja | Página |
|---|---|---|
| Diferencial de entrada máxima (absoluta) | **±4 V** | p. 5, Table 3 |
| Modo común de entrada (absoluto) | ±VS | p. 5, Table 3 |
| Corriente de entrada máxima | no especificada: informa la que dé el modelo, sin criterio | — |
| Excursión de salida a ±5 V | ±4 V con RL = 2 kΩ, saturada | p. 3 |
| Recuperación de sobrecarga | 50 ns (G = +2, 1 V) | p. 3 |
| Ruido | 8 nV/√Hz y 600 fA/√Hz a 100 kHz | p. 3 |
| Reposo | 1.0 mA típ., 1.5 mA máx. por amplificador | p. 3 |

El modelo no limita la diferencial: E14 informa la tensión que aparece, y S3-C7 la juzga contra ±4 V.

### 2.3 E15, conmutación del 4051

- Entrada en continua tal que, en la escala de llegada, la salida quede en +2 div. Cambia la toma **con el relé quieto**:
  - 1 → 1/2, 1/2 → 1/4, 1/20 → 1/40 (tomas vecinas);
  - 1 → 1/40 y 1/40 → 1 (salto máximo);
  - toma 1 → GND (autocero) → toma 1.
- Las tres líneas de dirección cambian juntas (el 74HCT595 las suelta a la vez), y aparte con 10 ns de desfase entre ellas, en el orden que dé el peor código intermedio.
- Mide en la salida de U103B: pico del glitch (en div), tiempo hasta ±0.1 div del valor final y si algún amplificador satura durante la transición.
- POS = 1 y POS = 100.

## 3. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S3-C1 | En las 12 escalas, pérdida de S3 a 2 MHz ≤ 0.5 dB respecto de su ganancia en continua. «S3» es la función de U101 a la salida de U103B (V(salida)/V(entrada de U101)); informa también la de la BNC a la salida | E11 |
| S3-C2 | Sin picos: \|H\| no supera la ganancia en continua en más de 0.5 dB en ninguna frecuencia hasta 100 MHz; en E11b, sobreimpulso ≤ 5 % | E11, E11b |
| S3-C3 | Error de ganancia en continua por escala **informado** (va a la calibración, P10), frente a la ganancia ideal calculada con los valores de §1 (toma × ×50.55 × grueso) | E11 |
| S3-C4 | Ruido referido a la BNC, integrado de 1 Hz a **3.15 MHz** (ancho de banda de ruido de un canal de 2 MHz), **≤ 0.45 % de división** en las 12 escalas. Informa también la integral de 1 Hz a 10 MHz, sin criterio | E12 |
| S3-C5 | 2 Vpp a 2 MHz: THD ≤ 1 % (hasta el 9.º armónico) y sin limitación de slew rate (dV/dt de la salida ≤ 50 % del SR del modelo). Con 4 Vpp, informar | E13 |
| S3-C6 | Recuperación a ±0.1 div en ≤ 1 µs en las 12 escalas y polaridades | E14 |
| S3-C7 | En saturación, todas las entradas de U103A, U103B y U101 dentro de los límites de §2.2 y de S2b (diferencial, modo común y corriente) | E14 |
| S3-C8 | Asentamiento tras cambio de toma ≤ 10 µs a ±0.1 div; glitch informado | E15 |
| — | Corriente de reposo de cada AD8039 y del OPA810, y su valor durante E13 (para G.3 y RF-17) | todas |

E12 se relajó de 0.35 % a 0.45 % el 3 oct (decisión de Keneth al elegir el AD8039): la estimación de C.5 con el AD8039 y R_PROT de 1 kΩ era 0.42 % con la red de 1 kΩ y es ≈ 0.40 % con la de 249 Ω. La mitad la ponen el buffer y R_PROT, que no se tocan.

Fallar es un resultado válido; informar siempre el valor medido.

## 4. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, **sin modificar los entregables de S1, S1b, S2 ni S2b**:

1. `comun/ch1_comun_s3.inc`, que **incluye** `ch1_comun_s2b.inc` (no lo copia) y añade escalera, 4051, U103 y carga.
2. `S3/` con los `.cir` generados.
3. `ejecutar_s3.py`, paralelo (10 trabajadores) desde el principio, con `--smoke`, y con la variable de entorno `S3G4_MODELS` para la ruta de los modelos (si no está, ruta relativa).
4. `resultados/s3_*.csv` y `resultados/s3_resumen.md`.
5. `ACTA_S3.md`, con:
   - criterios S3-C1…C8;
   - tabla por escala: ganancia en continua, error frente a la ideal, −3 dB, pérdida a 2 MHz, pico, ruido (µV y % de división);
   - el modelo del 4051 que usaste y de dónde salen sus valores;
   - **dudas y contradicciones sin resolver**;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`.

## 5. Lo que NO es tuyo

- No cambies valores de diseño para que algo pase (escalera, red de ganancia, R_PROT, amplificadores). Si algo falla, informa cuánto falta.
- No elijas otro amplificador ni añadas compensaciones, diodos o resistencias de protección.
- No diseñes S4 (offset, etapa final) ni el filtro.
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 6. Cómo voy a auditar

1. Reejecución en una copia con ruta corta y `S3G4_MODELS`, y comparación de los CSV byte a byte.
2. El orden de nodos del envoltorio del AD8039 y del OPA810.
3. Que las tomas y las ganancias ideales salen de los valores, no de constantes escritas a mano.
4. El ruido: que es `inoise` referido a la BNC y que la integral usa el intervalo pedido. Lo comparo con la estimación de C.5 (0.42 % a 5 y 500 mV/div).
5. E14: que el pulso llega al nivel pedido en cada escala y que la recuperación se mide desde el final del pulso.
6. E15: que el peor código intermedio está cubierto.
