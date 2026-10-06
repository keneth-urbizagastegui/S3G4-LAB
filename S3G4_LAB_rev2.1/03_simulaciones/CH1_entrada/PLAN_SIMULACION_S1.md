# Plan de simulación S1 — entrada pasiva P4b de CH1

- Autor: Claude Code (auditor), 2 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S1.md`.

## 1. Contexto y fuentes

- Revisión y propuesta: `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (§4 valores, §6 plan S0–S8). Esta es la etapa **S1, pruebas E1–E4**.
- Decisiones del 2 oct en `ai-context/DECISIONS.md`:
  - P1: grueso ×1 / ÷100;
  - entrada sin la red conectada directamente; ±100 V sin daño;
  - simulaciones por Codex.
- Patrón de trabajo: `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/` (include común, `ejecutar_todo.py`, `resultados/`, acta) y su auditoría `AUDITORIA_CLAUDE_P4_P7.md`. Lee la auditoría: dos de sus fallos los causaron reglas de contabilidad de parásitas, que aquí van en §3.
- Chequeo previo de Claude, sólo de referencia: `chequeo_claude/p4b_zin.cir`. **No lo modifiques ni lo reutilices como entregable.**

## 2. Circuito P4b (un canal, grueso ÷100)

Nodos con estos nombres en todos los ficheros:

```
BNC ─┬─ Rt1 ∥ Ct1 ─ M ─ Rt2 ∥ Ct2 ─┬─ TAP ─ Rb ∥ Cb ─ GND        (divisor siempre conectado)
     │                              └─ K1a contacto de reposo
     └─ RS1 ─ RSM ─ RS2 (∥ CS entre BNC y X1) ─┬─ X1               (rama ×1)
                                              ├─ K1a contacto de trabajo (×1)
                                              └─ K1b contacto de reposo → EQ ─ R_EQ ∥ C_EQ ─ GND
K1a común → SEL
SEL: BAV199 (ánodo-cátodo) a VP y VN; capacidad parásita CSEL_PAR a GND
SW1 polo A: común = B; tiro DC → SEL; tiro AC → T2 (C_AC de SEL a T2); tiro GND → GND
B: R_BIAS a GND; R_PROT de B a BI; CIN_BUF de BI a GND; buffer ideal de ganancia 1 con entrada en BI
```

- Relé: reposo = ÷100 (K1a en TAP y K1b cerrado); trabajo = ×1 (K1a en X1 y K1b abierto). Parámetro `POS` = 1 o 100.
- Acoplo: parámetro `CPL` = DC, AC o GND.
- Rieles VP = +5 V y VN = −5 V, ideales con 1 Ω de fuente (como `RAILS` de `rev21_comun.inc`).
- Buffer: fuente controlada de ganancia 1 o `UniversalOpamp2` con GBW de 100 MHz y Rin = 1 TΩ. En S1 no se prueban amplificadores.

## 3. Valores y reglas

Todos como `.param`. Los derivados se calculan, no se escriben a mano.

| Parámetro | Valor | Nota |
|---|---|---|
| RT1 (×2) | 549 kΩ | Rt total 1.098 MΩ |
| CT1 (×2) | 20 pF nominal; barrer también 12 pF | Ct efectivo de 10 pF o 6 pF |
| RB | 11.0 kΩ | |
| RS1, RS2 | 49.9 kΩ cada una | RS = 99.8 kΩ |
| RBIAS, REQ | 10 MΩ | REQ = RBIAS |
| RPROT | 1 kΩ | |
| CAC | 1.8 nF | |
| CBNC | 3 pF | conector y pista |
| CX1 | 2 pF | pista y pads de X1 |
| COFF_RELE | 1 pF | entre contactos abiertos de K1a y de K1b; RON_RELE 0.1 Ω |
| CSEL_PAR | 3 pF | conmutador, pista y pads de SEL, sin los diodos |
| COFF_SW | 0.5 pF | entre el común y cada tiro abierto de SW1 |
| CIN_BUF | 5 pF | en BI |
| BAV199 | `DBAV199` de `../P4_P7_grueso/comun/rev21_comun.inc` (CJO = 1.5 pF) | genérico; el de Nexperia llega en S2 |
| C_SEL_EST | derivado: 2 · CJO + CSEL_PAR + CIN_BUF + COFF_SW | estimación de diseño de la capacidad de SEL |
| CEQ | derivado: = C_SEL_EST | pieza de la réplica |
| CX1_TOT | derivado: CX1 + COFF_RELE + C_SEL_EST | lo que ve X1 en ×1 |
| CS | derivado: RBIAS · CX1_TOT / RS | compensación de la rama ×1 |
| CB | derivado: (CT1/2 + COFF_RELE) · 2·RT1 / (RB ∥ RBIAS) − (C_SEL_EST + CTAP) | compensación del ÷100; CTAP = 2 pF |

Reglas de contabilidad (lecciones de P4/P7):

1. La capacidad del contacto abierto que une SEL con X1 en ÷100 es **capacidad de arriba**: X1 es la BNC en alta frecuencia a través de CS. Por eso suma a Ct en la fórmula de CB.
2. La capacidad de los diodos va **sólo** en su CJO. No la vuelvas a sumar en ningún `CPAR`.
3. CIN_BUF va explícita en BI, detrás de RPROT.

## 4. Pruebas

### E1 — Zin y Cin
- AC de 10 Hz a 10 MHz con fuente ideal; corriente medida con una fuente de 0 V en serie.
- Casos: POS ∈ {1, 100} × CPL ∈ {DC, AC, GND} × CT1 ∈ {20 pF, 12 pF}.
- Medidas:
  - |Zin| a 100 Hz;
  - Cin = −Im(I/V)/(2π·f) a 1 MHz.

### E2 — Respuesta BNC → salida del buffer
- AC de 1 Hz a 20 MHz, con POS ∈ {1, 100} y CPL ∈ {DC, AC}.
- Medidas:
  - ganancia a 1 kHz frente a la nominal, que se calcula: ×1 → RBIAS/(RS+RBIAS); ÷100 → (RB∥RBIAS)/(2·RT1 + RB∥RBIAS);
  - desviación máxima de 10 Hz a 2 MHz respecto a 1 kHz (en DC);
  - pico máximo;
  - frecuencia de −3 dB baja (en AC).

### E3 — Sonda ×10 compensada una sola vez
- Modelo de sonda: 9 MΩ ∥ 10 pF en la punta, cable de 80 pF concentrado y condensador de compensación CCOMP a masa en el extremo de la BNC.
- Fuente: cuadrada de 1 kHz, ±1 V, 5 ns de subida, 50 Ω.
- Procedimiento:
  1. En POS = 100, barrer CCOMP y elegir el valor que minimiza el error del escalón.
  2. **Sin tocarlo**, medir en POS = 1.
- Medidas, referidas a la **altura del escalón** (no al nivel asentado de la cuadrada; ver la auditoría P4/P7, C5):
  - sobreimpulso;
  - error a 2 µs, 20 µs y 200 µs.

### E4 — Tolerancias y sensibilidad
1. Monte Carlo de ≥ 200 corridas sobre E1, E2 (desviaciones a 100 kHz, 1 MHz y 2 MHz) y E3 (sobreimpulso en POS = 1 con el CCOMP del caso nominal). Distribuciones uniformes:
   - RT1 y RB: 0.1 %.
   - RS, RBIAS y REQ: 1 %.
   - CT1, CB, CS y CEQ: 2 %.
   - CAC: 5 %.
   - COFF_RELE: 0.5–1.5 pF.
   - CSEL_PAR: 1.5–4.5 pF.
   - CIN_BUF: 3–7 pF.
   - CJO: ±30 %.
   - CX1: 1–3 pF.
   - CBNC: 2–4 pF.
2. Sensibilidad de uno en uno: cada parámetro en sus dos extremos con el resto nominal. Tabla de cuánto mueve ΔCin y la desviación a 1 MHz.

## 5. Criterios de aceptación

Fallar es un resultado válido. Informar siempre el valor medido.

| # | Criterio | Prueba |
|---|---|---|
| S1-C1 | \|Zin\| a 100 Hz = 1.00 MΩ ± 2 % en POS 1 y 100, con CPL en DC y en AC | E1 |
| S1-C2 | Cin entre 10 y 30 pF y \|Cin(×1) − Cin(÷100)\| ≤ 2 pF, con CPL = DC | E1 |
| S1-C3 | Ganancia a 1 kHz dentro de ±0.5 % de la nominal calculada | E2 |
| S1-C4 | En DC: desviación ≤ ±1 % de 10 Hz a 2 MHz y pico ≤ 0.1 dB. En AC: −3 dB por debajo de 10 Hz | E2 |
| S1-C5 | Con CCOMP fijado en ÷100: sobreimpulso y error a 2 µs ≤ 2 % del escalón en las dos posiciones | E3 |
| — | E4 sin criterio: decide si C_EQ y/o Cb llevan ajustable. Con CPL = GND, E1 sólo se informa | E4 |

## 6. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`:

1. `comun/ch1_comun.inc` — parámetros de §3, modelos y el subcircuito `FRONT_P4B` con parámetros POS, CPL y CT1.
2. `S1/E1_zin.cir`, `S1/E2_respuesta.cir`, `S1/E3_sonda.cir`, `S1/E4_mc.cir` (y los que necesites). Son netlists de texto para LTspice en lote; no hace falta dibujo.
3. `ejecutar_s1.py`, que:
   - corre todo en lote y lee los `.meas`;
   - evalúa §5 con los umbrales en una sola tabla del script, con el número de criterio;
   - escribe `resultados/s1_resultados.csv` y `resultados/s1_resumen.md`;
   - sale con código ≠ 0 sólo si una simulación da error, no si un criterio falla.
4. `ACTA_S1.md`, con:
   - tabla de criterios por caso (valor y pasa/falla);
   - lo que enseña cada prueba;
   - resultados de E4 con el parámetro dominante;
   - **lista de dudas y contradicciones, sin resolver**;
   - código de salida y número de simulaciones con error o advertencia.
5. Tu diario en `ai-context/journal/` según `AGENTS.md`.

## 7. Lo que NO es tuyo

- No cambies valores de §3 para que algo pase. Si crees que uno está mal, va a la lista de dudas con tu razón.
- No elijas ajustables ni recomiendes cambios de diseño en el acta: mide y describe.
- No toques nada fuera de `CH1_entrada/` salvo tu diario; en particular, ni `chequeo_claude/`, ni `P4_P7_grueso/` (sólo lectura), ni los documentos de `01_diseno/`.
- No edites `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 8. Cómo voy a auditar

1. Valores frente a §3 y derivados calculados con `.param`.
2. Ejecuto `ejecutar_s1.py` yo mismo y comparo fila por fila.
3. El estado del circuito en cada medida coincide con su nombre (POS, CPL, CT1).
4. Las reglas de §3 (Coff arriba, CJO una sola vez, CIN_BUF explícita).
5. E1 y E2 nominales frente a mi chequeo (999.1 kΩ; 27.7 pF con CT1 = 20 pF; planitud de −0.3 %). Mi chequeo no lleva diodos ni SW1, así que se esperan diferencias pequeñas, que tienen que estar explicadas.
6. Que no hay ficheros tocados fuera de la carpeta.
