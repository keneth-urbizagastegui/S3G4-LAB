# Plan de simulación — Atenuador grueso de la rev 2.1: P4 (con relé) frente a P7 (sin relé)

- Autor del plan: Claude Code, 2026-09-23. Constructor: Codex. Auditor: Claude Code.
- Decisión que alimenta: elegir entre P4 y P7 para el atenuador grueso de los tres canales. **La simulación no decide: mide.** Decide Keneth después de la auditoría.
- Fuentes de los valores: `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html` (P1, P2, P4), `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html` (§4 ruido kT/C, §5 P7) y `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` (secciones B y C). **Si algo de este plan contradice esas fuentes, no lo resuelvas: anótalo en la lista de dudas del acta.**

---

## 1. Qué hay que responder

Siete preguntas, cada una con su ensayo. Todos los ensayos se hacen **para los dos diseños**, con el mismo tramo posterior, para que la comparación sea justa.

| Ensayo | Pregunta |
|---|---|
| T01 | ¿La impedancia de entrada es 1 MΩ y la capacidad de entrada igual en todas las posiciones? (una sonda ×10 sólo se compensa si lo es) |
| T02 | ¿La respuesta en frecuencia es plana y cuánto se pierde a 1.5 MHz? |
| T03 | ¿El divisor queda compensado? Respuesta a un escalón |
| T04 | ¿Cuánto ruido referido a la entrada hay en 5 mV/div, 200 mV/div y 500 mV/div? |
| T05 | ¿Qué pasa con señales grandes en las escalas gruesas? (la «rodilla» de P7) |
| T06 | ¿Sobrevive a 50 V continuos y a 250 Vrms (353 Vpk) de la red? ¿Qué potencia y tensión ven las piezas? |
| T07 | ¿Cuánto empeoran T02–T04 con las tolerancias y parásitas reales? (decide si hacen falta ajustables) |

## 2. Los dos diseños

Hasta el nodo seleccionado cada diseño es distinto; desde el buffer en adelante, el tramo es **común** (§3).

### 2.1 P4 — con relé (P1 + P2 + P4)

```
BNC ──┬── [Rt = 990 kΩ ∥ Ct = 10 pF] ──┬── TAP100 ──[Rb = 10.0 kΩ ∥ Cb]── GND        (÷100, siempre conectado)
      │                                 └──────────────── NC ─┐
      └── [R_S = 100 kΩ ∥ C_S = 1.0 nF] ── X1 ──────────── NO ─┤ K1 (SPDT) ── SEL
                                                                │
SEL: R_BIAS 10 MΩ a GND · clamps BAV199 a ±5 V · TVS bidireccional · CPAR_SEL a GND ── buffer (§3)
```

- Rt se construye en la placa con 3 × 330 kΩ y Ct con 3 × 30 pF en serie; **en simulación puede ser un solo elemento** salvo en T06, donde hay que informar la tensión y la potencia **por resistencia física** (dividir entre 3).
- **Cb se deriva, no se copia**: `Cb = Ct·Rt/Rb − (parásitas del nodo TAP100 con el relé en ÷100)`. Las parásitas de ese nodo en esa posición son `CPAR_TAP + CPAR_SEL + CIN_BUF` más lo que acople el contacto abierto (ver §4). Hazlo con `.param`.
- K1 es un conmutador controlado por tensión (`SW`) para cada contacto, complementarios: `Ron = 0.1 Ω`, `Roff = 1 GΩ`, y en paralelo con cada contacto abierto un condensador `COFF_RELE`. Posición «reposo» = ÷100.
- Rama ×1 en dos variantes: **P2-base** (una resistencia de 100 kΩ en 0805 y C_S de 1 nF / 100 V) y **P2-AT** (dos de 49.9 kΩ en 1206 en serie y C_S de 1 nF / 630 V). En simulación el valor total es el mismo; la diferencia sólo cuenta en T06 al repartir tensión y potencia.

### 2.2 P7 — sin relé (estilo WAVE2 revisión E)

```
BNC ──┬── [RtF = 1.00 MΩ ∥ CtF = 10 pF] ── FINO ──[RbF = 1.00 MΩ ∥ CbF]── GND
      │     FINO: clamps BAV199 a ±5 V · TVS · CPAR_FINO ── buffer A (§3) ── Y0 ┐
      │                                                                          ├─ 74HC4053 ── COM ── tramo común
      └── [RtG = 1.99 MΩ ∥ CtG = 10 pF] ── GRUESO ──[RbG = 10.0 kΩ ∥ CbG]── GND │
            GRUESO: CPAR_GRUESO ── buffer B (§3) ────────────────────────── Y1 ┘
```

- Rama fina ÷2 y rama gruesa ÷200 (relación 100 entre ellas). Zin = 2 MΩ ∥ 2 MΩ = 1 MΩ.
- `CbF = CtF·RtF/RbF − CPAR_FINO − CIN_BUF` y `CbG = CtG·RtG/RbG − CPAR_GRUESO − CIN_BUF`, derivados con `.param`.
- RtF se construye con 3 resistencias y RtG con 3 (3 × 665 kΩ en la placa; en simulación usa 1.99 MΩ exacto y anota la diferencia con la serie E96 como duda si la ves relevante).
- 74HC4053: conmutador con `RON_4053 = 100 Ω`; entre la entrada no seleccionada y la salida, `COFF_4053`; en la salida, `CS_4053` a masa.
- La rama gruesa no lleva clamps: con 353 V su nodo no pasa de ~1.8 V. Compruébalo en T06.

## 3. Tramo común (igual en los dos diseños)

```
buffer (seguidor FET) ── escalera 997.7 Ω con 6 tomas ── 74HCT4051 ── etapa 1 ── etapa 2 ── SAL ── [filtro ideal 1 polo 1.5 MHz] ── SAL_F
```

- **Amplificadores:** `UniversalOpamp2` de LTspice con `GBW = 100 MHz`, `Slew = 50 V/µs`, `Avol = 1e5` (100 dB), `En = 7 nV/√Hz`, `In = 5 fA/√Hz`, alimentación ±5 V, salida hasta los raíles. Añade `CIN_BUF` a masa en la entrada no inversora del buffer. **Todos los amplificadores con los mismos parámetros**, definidos una sola vez.
- **Escalera** (valores del DSO112): 499, 249, 150, 49.9, 24.9 y 24.9 Ω desde la salida del buffer a masa. Tomas: 1/1, 1/2, 1/4, 1/10, 1/20, 1/40.
- **74HCT4051:** `RON_4051 = 100 Ω` en serie y `CS_4051` a masa en la salida común.
- **Ganancia fija:** P4 = ×50 (×5 con 4 kΩ / 1 kΩ y después ×10 con 9 kΩ / 1 kΩ). P7 = ×100 (dos etapas de ×10 con 9 kΩ / 1 kΩ). No inversoras.
- **Filtro de 1 polo en 1.5 MHz:** fuente dependiente con Laplace, ideal. Sólo sirve para integrar el ruido con la banda del instrumento (T04). **T02 mide en SAL, antes del filtro.**
- Acoplo AC/DC fuera de estas simulaciones: posición DC. R_BIAS sólo existe en P4 (en P7 cada rama tiene su camino de continua por Rb).

### Escalas que hay que usar

8 divisiones = 2.0 V en el ADC (0.25 V/div). Comprueba tú la ganancia total de cada una y anota cualquier incoherencia.

| Escala | P4: grueso · toma · fija | P7: rama · toma · fija |
|---|---|---|
| 5 mV/div | ×1 · 1/1 · ×50 | fina ÷2 · 1/1 · ×100 |
| 200 mV/div | ×1 · 1/40 · ×50 | fina ÷2 · 1/40 · ×100 |
| 500 mV/div | ÷100 · 1/1 · ×50 | gruesa ÷200 · 1/1 · ×100 |
| 5 V/div | ÷100 · 1/10 · ×50 | gruesa ÷200 · 1/10 · ×100 |

## 4. Parámetros comunes (un solo fichero `comun/rev21_comun.inc`)

| Parámetro | Nominal | Barrido en T07 | Qué representa |
|---|---|---|---|
| `CBNC` | 3 pF | 2–5 pF | conector y pista de entrada |
| `CIN_BUF` | 3 pF | 2–6 pF | entrada del buffer |
| `CPAR_SEL`, `CPAR_FINO`, `CPAR_GRUESO`, `CPAR_TAP` | 5 pF | 3–8 pF | clamps, TVS y pista de cada nodo |
| `COFF_RELE` | 1 pF | 0.5–2 pF | contacto abierto del relé |
| `COFF_4053` / `CS_4053` | 5 pF / 5 pF | 2–10 pF | 74HC4053 |
| `RON_4053`, `RON_4051` | 100 Ω | 50–200 Ω | resistencia en conducción |
| `CS_4051` | 20 pF | 10–40 pF | salida común del 4051 |
| Tolerancia de R | 0 | ±1 % | Monte Carlo o extremos |
| Tolerancia de C | 0 | ±5 % (C0G) | Monte Carlo o extremos |

Modelos de diodo (aproximados; úsalos tal cual y dilo en el acta):

```
.model DBAV199 D(IS=1e-12 N=1.9 RS=1.5 CJO=1.5p M=0.3 VJ=0.6 BV=85 IBV=1n)
.model DTVS5   D(IS=1e-12 N=1.0 RS=0.5 CJO=3p BV=6.0 IBV=1m)     ; dos en antiserie = TVS bidireccional
```

Raíles de ±5 V ideales, **con una resistencia de fuente de 1 Ω** para poder medir la corriente que les inyectan los clamps.

## 5. Ensayos y medidas

Cada ensayo es un `.asc` por diseño: `P4_rele/T0x_nombre.asc` y `P7_sin_rele/T0x_nombre.asc`. Cada `.asc` lleva:
- un comentario al principio con qué mide, la posición del grueso, la toma y la fuente usadas;
- sus `.meas` con **nombres que incluyan el estado** (diseño, escala o posición, fuente). Ejemplo: `p7_g500_zin100`;
- los criterios de §6 escritos como comentario.

### T01 — Impedancia y capacidad de entrada
AC de 10 Hz a 10 MHz con fuente ideal. Medir |Zin| = |V(BNC)/I(fuente)| a 100 Hz y la capacidad equivalente a 1 MHz (`Cin = Im(1/Zin)/(2πf)`), **en cada posición** (P4: ×1 y ÷100; P7: fina y gruesa seleccionada).

### T02 — Respuesta en frecuencia
AC con la fuente de 50 Ω. Para cada escala de §3: ganancia en SAL respecto a su valor a 100 Hz; desviación máxima de 10 Hz a 100 kHz; pérdida a 1.5 MHz; pico máximo; frecuencia de −3 dB. Informar también la ganancia a 100 Hz frente a la nominal.

### T03 — Escalón (compensación)
Transitorio con cuadrada de 1 kHz y flancos de 10 ns, fuente de 50 Ω, en 5 mV/div y 500 mV/div (amplitud que llene 6 divisiones). Medir en SAL el error del tramo inicial frente al valor asentado: a 2 µs, 20 µs y 200 µs del flanco, en %.

### T04 — Ruido
`.noise` en SAL_F con la fuente de entrada, de 10 Hz a 50 MHz. Integrar `V(onoise)` en ese rango (`.meas ... INTEG`), dividir por la ganancia de T02 a 100 Hz y dar el **ruido referido a la entrada en µV rms** y en **% de una división** para 5 mV/div, 200 mV/div y 500 mV/div.

Valores de referencia de mi cálculo a mano, para contrastar:

| Diseño | 5 mV/div | 200 mV/div | 500 mV/div |
|---|---|---|---|
| P4 | ≈ 15 µV | ≈ 0.43 mV | ≈ 1.5 mV |
| P7 | ≈ 42 µV | ≈ 0.86 mV | ≈ 3.1 mV |

Si tu resultado difiere más de un 30 %, **no lo ajustes**: dilo y explica de dónde sale la diferencia (qué fuente de ruido domina; `.noise` permite ver la contribución de cada elemento).

### T05 — Señales grandes en las escalas gruesas
Transitorio, senoidal de 1 kHz, escala de 5 V/div. Amplitudes de pico: 5, 11, 20 y 40 V. Tres fuentes:
1. 50 Ω.
2. 10 kΩ.
3. **Sonda ×10**: 9 MΩ en serie con un condensador `Cp` en paralelo, `Cp = Cin_total/9` con el Cin de T01 **de esa posición** (derívalo). La amplitud «en la punta» es 10× la de la BNC: usa 50, 112, 200 y 400 V en la punta.

Medir: corriente de entrada de pico, impedancia de entrada efectiva (`Vpk/Ipk`), distorsión en SAL con `.four` (THD en %) y error de amplitud respecto a la ganancia nominal. **En P7 es aquí donde tiene que aparecer la rodilla de ±11.2 V; en P4 no debería aparecer.**

### T06 — Supervivencia
Dos situaciones, **en cada posición del grueso**:
- **50 V continuos** en la BNC (DC).
- **250 Vrms a 50 Hz** (353 Vpk), 5 ciclos de transitorio; informar los valores del último ciclo.

Medir, pieza a pieza: tensión de pico y potencia media en cada resistencia **física** (repartiendo Rt, RtF y RtG entre 3; la rama ×1 de P4 en sus dos variantes); corriente de pico y media en cada clamp y en la TVS; corriente inyectada en cada raíl; tensión máxima en la entrada de cada amplificador; y, en P4, la tensión entre los terminales del contacto abierto del relé.

Referencia de potencia de los encapsulados: 0805 = 0.125 W y 150 V; 1206 = 0.25 W y 200 V. **Criterio de potencia con reducción: ≤ 60 % de la nominal en continuo** (ver §6). Para los 10 s de red, informa potencia y energía y **no juzgues** la sobrecarga de corta duración: lo decide el auditor.

### T07 — Robustez
Barrido `.step` (o Monte Carlo con ≥ 200 corridas) de los parámetros de §4 **y** de las tolerancias. Repetir T02 (desviación a 100 kHz y pérdida a 1.5 MHz), T03 (error a 2 µs) y la ganancia de continua. Dar el peor caso y **qué parámetro lo produce**. Sirve para decidir si hacen falta ajustables: P4 tiene un divisor ajustable por canal y P7 dos.

## 6. Criterios de aceptación

Fallar es un resultado válido. Informar el valor medido siempre, pase o no.

| # | Criterio | Ensayo |
|---|---|---|
| C1 | \|Zin\| a 100 Hz = 1.00 MΩ ± 2 % en todas las posiciones | T01 |
| C2 | Cin entre 10 y 30 pF, y diferencia entre posiciones ≤ 2 pF | T01 |
| C3 | Ganancia a 100 Hz dentro de ±1 % de la nominal (sin calibrar) | T02 |
| C4 | Desviación ≤ 1 % de 10 Hz a 100 kHz; pérdida a 1.5 MHz ≤ 0.5 dB; pico ≤ 0.2 dB | T02 |
| C5 | Error de escalón ≤ 1 % a 2 µs en nominal | T03 |
| C6 | Ruido referido a la entrada ≤ 1 % de división en las tres escalas | T04 |
| C7 | Con 50 Ω y 40 V en 5 V/div: THD ≤ 0.5 % y Zin efectiva ≥ 900 kΩ | T05 |
| C8 | 50 V continuos: potencia ≤ 60 % de la nominal y tensión ≤ la nominal en toda resistencia; ninguna entrada de amplificador más de 0.5 V fuera de sus raíles | T06 |
| C9 | 250 Vrms: ningún clamp por encima de 100 mA de pico; entradas de amplificador como en C8; potencia y energía informadas | T06 |
| — | T07 no tiene criterio: es información para decidir los ajustables | T07 |

## 7. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/`:

1. `comun/rev21_comun.inc` — parámetros, modelos y el tramo común como subcircuito si lo prefieres.
2. `P4_rele/T01…T07*.asc` y `P7_sin_rele/T01…T07*.asc`, que se abran y se vean bien en la interfaz de LTspice.
3. `ejecutar_todo.py` — lanza LTspice en lote sobre cada `.asc`, lee los `.meas` de cada `.log`, evalúa los criterios de §6 y escribe `resultados/resultados.csv` y `resultados/resumen.md`. **Sale con código ≠ 0 si alguna simulación da error**, no si un criterio falla. Los umbrales de los criterios en una única tabla dentro del script, con el número de criterio.
4. `ACTA_RESULTADOS_P4_P7.md` — con el formato de las actas de `Simulation_LTSpice/` (ver `Simulation_LTSpice/Oscilloscope/ACTA_RESULTADOS_CANAL_OSCILOSCOPIO.md`):
   - tabla resumen por ensayo y diseño;
   - los valores de cada criterio;
   - lo que enseña cada ensayo;
   - **lista de dudas y contradicciones encontradas, sin resolver**;
   - con qué código salió `ejecutar_todo.py` y cuántas simulaciones dieron error o advertencia.
5. Un diario en `ai-context/journal/` según `AGENTS.md`. **No edites `STATE.md` ni `DECISIONS.md`**: los actualiza el auditor.

## 8. Lo que NO es tuyo

- No elegir entre P4 y P7, ni recomendar uno en el acta. Medir y describir.
- No cambiar valores del diseño para que pase un criterio. Si algo falla, se informa. Si crees que un valor está mal, va a la lista de dudas.
- No tocar nada fuera de `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/` salvo tu diario. En particular, ni `Simulation_LTSpice/`, ni `docs/`, ni firmware.
- No descargar modelos de internet: `UniversalOpamp2` y los diodos de §4.

## 9. Cómo voy a auditar

Para que sepas qué se va a mirar:
1. Que cada valor de los `.asc` coincide con §2–§4, y que los derivados (Cb, CbF, CbG, Cp) se calculan con `.param` y no están escritos a mano.
2. Que ejecuto `ejecutar_todo.py` yo mismo y obtengo lo mismo que el acta.
3. Toda suma o producto que aparezca en un comentario o etiqueta.
4. Que cada medida dice en qué estado se tomó, y que el estado del circuito coincide con el nombre.
5. Los resultados contra mis cálculos a mano (§5 T04 y las cifras de `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html` §5).
6. Que no hay ficheros tocados fuera de la carpeta.
