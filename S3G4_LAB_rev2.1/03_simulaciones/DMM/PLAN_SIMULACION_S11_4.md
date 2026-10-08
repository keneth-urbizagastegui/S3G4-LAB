# Plan de simulación S11.4 — DMM, bloque 1: confirmación final

- Autor: Claude Code (auditor), 7 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Lee antes:**
  - `PLAN_SIMULACION_S11_3.md`, que sigue vigente salvo lo que cambia aquí;
  - `ACTA_S11_3.md` y `AUDITORIA_CLAUDE_S11_3.md`;
  - en `ai-context/DECISIONS.md`, las entradas del 7 oct «cambios tras la auditoría de S11.3» y «ESD con piezas de pulso y descargador de gas (A + B)».
- Reutiliza el ejecutor y el include de S11.3. **No repitas la campaña entera:** solo lo del §2.

## 1. Cambios en el circuito respecto a S11.3

1. **GDT** entre V/Ω y COM: hongjiacheng SMD4532-600NF (LCSC C47345384).
   - Modelo de comportamiento: no conduce hasta el cebado; al cebar, arco de unos 20 V. Se apaga por debajo de la corriente de mantenimiento.
   - Cebado en continua de 600 V ±30 % (420 a 780 V); cebado por impulso de 1 kV a 100 V/µs; 0.5 pF. Haz casos con el cebado mínimo y el máximo.
   - Son datos de la ficha de LCSC: si no hay hoja, márcalos como supuestos.
2. **Compensación:** 3 × 100 pF C0G de 2 kV (CCTC C7393967).
3. **R_PROT:** 3 × 33 kΩ en 1206 de 0.5 W (FOJAN C55348469; 200 V de trabajo según la ficha).
4. **Ohmios:**
   - 2 × 1.1 kΩ en 2512 de 2 W (Milliohm C5123622; 250 V de trabajo);
   - R_S de 2.7 kΩ;
   - diodo de bloqueo **BAT54** (modelo de LTspice, `standard.dio`) en lugar del BAV199.
5. **Mux:** RX0 = RX1 = 100 Ω; sin RX2.

## 2. Pruebas

| # | Qué |
|---|---|
| T1 | Diodo: tensión disponible a 100 µA y a 1 mA, con los rieles nominales y a −2 %; corriente real en un LED (3.0 y 3.2 V) y en un silicio |
| T2 | ESD por contacto a ±4 kV y en el aire a ±8 kV en V/Ω, en modo tensión y en modo ohmios, con el cebado mínimo y el máximo del GDT. Ventana de 50 µs |
| T3 | Red de 230 Vrms durante 10 s en modo tensión, con el cebado mínimo: **el GDT no debe cebar** (tensión en sus bornes y corriente) |
| T4 | 60 V DC y 60 Vrms en ohmios (repite el peor caso de R3 de S11.3) con las piezas nuevas |
| T5 | Los nueve casos R7 que agotaron el tiempo en S11.3, ahora con 900 s |

## 3. Criterios

| # | Criterio |
|---|---|
| D1 | Cada pieza ≤ 80 % de su tensión y ≤ 50 % de su potencia o energía, según su ficha u hoja. En la ESD, compara con la tensión de pulso o de sobrecarga de la ficha cuando la haya, y dilo |
| D2 | En T2, la tensión en el relé abierto ≤ 80 % de los 1500 V de pulso de su hoja (C46047, p. 6) y en cada 1206 ≤ su tensión de sobrecarga de la ficha |
| D3 | En T3, el GDT no ceba con el cebado mínimo (≤ 80 % de 420 V) |
| D4 | Corriente en X0/X1 ≤ 50 % del máximo del 74HC4051 en T2 por contacto |
| D5 | Diodo ≥ 3.5 V a 100 µA con los rieles a −2 % |
| D6 | Recuperación ≤ 1 s en T5 |
| D7 | Tensión entre rieles ≤ 11 V en T2–T4 |

Fallar es un resultado válido. Informa siempre del valor y de lo que lo movería, sin cambiar piezas.

## 4. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque1_final.inc`;
- `ejecutar_s11_4.py` (10 trabajadores, `--smoke`, `--resume`, 900 s por caso);
- `resultados/s11_4_*.csv`;
- `ACTA_S11_4.md`, con la tabla D1–D7 y la lista de piezas final del bloque 1;
- tu diario en `ai-context/journal/`.

## 5. Lo que NO es tuyo

No cambies piezas ni topología. No toques los archivos de S11.1–S11.3, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
