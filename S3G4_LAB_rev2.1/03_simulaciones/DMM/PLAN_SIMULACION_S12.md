# Plan de simulación S12 — DMM, bloque 2: frontal de tensión

- Autor: Claude Code (auditor), 8 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Lee antes, enteros:**
  - `ESTUDIO_BLOQUE2.md`, sobre todo §0, §5 y §8, su tabla de confirmaciones C1–C9 y los decks de `estudio_bloque2/`;
  - `01_diseno/dmm_bloque1.html`, que fija la frontera de entrada;
  - en `ai-context/DECISIONS.md`, las entradas del 7 y el 8 oct del DMM.
- Reutiliza el modelo reducido y el ejecutor de S11.4 para la parte de protección.

## 1. Circuito (decisión del 8 oct)

Desde los nodos X0, X1 y X2 (bloque 1: R_PROT de 99 kΩ con BAV199 y 100 Ω en X0 y X1) hasta la salida del amplificador A.

1. **Divisor de 10 MΩ:**
   - arriba, 6 × 1.5 MΩ de película delgada al 0.1 % y 25 ppm/°C (`C728673.pdf`) – toma ÷10 – 910 kΩ – toma ÷100 – 100 kΩ;
   - compensación: 3 parejas de (100 pF C0G de 2 kV + 3.3 kΩ), una sobre cada par de 1.5 MΩ; 330 pF sobre 910 kΩ; 3.0 nF sobre 100 kΩ. Ajusta la τ a los valores nuevos con el cálculo del estudio §2 y dilo.
2. **Mux:** 74HCT4051 a ±4.9 V (modelo Nexperia `SWI1`, solo para transitorio). X3 = COM para el autocero.
3. **Amplificador A: OPA2192** (modelo de TI en `Simulation_LTSpice/models/OPA2192/`, hoja `opa2192.pdf`) a ±4.9 V. Compara con el OPA2188 solo en C5.
4. **Ganancia:** divisor fijo de 91 kΩ / 10 kΩ (0.1 %, 25 ppm/°C) desde la salida hasta COM. Un SPDT TMUX4053 (`tmux4053.pdf`; Ron y fuga de su hoja, en modelo paramétrico si no hay SPICE) lleva IN− a la salida (×1) o a la toma (×10.1).
5. **Carga de salida:** la entrada del driver del bloque 5, modelada con 10 kΩ ∥ 10 pF a VCM = 1.25 V (supuesto, márcalo).

## 2. Pruebas

La tabla C1–C9 del §8 del estudio, **con el OPA2192 como amplificador** y con el TMUX4053 y el 74HCT4051. En C7 (divisor con la red y la ESD) usa el modelo de protección de S11.4.

## 3. Criterios (≥ 95 % de las placas)

| # | Criterio |
|---|---|
| E1 | Alterna: residuo tras la corrección del firmware (cero fijo y 3 puntos: 100 Hz, 1 kHz y 20 kHz) **≤ 0.5 %** de 40 Hz a 20 kHz en los 4 rangos de tensión, con un ruido de calibración del 0.05 % (informa también con el 0.1 %) |
| E2 | Continua tras calibrar a 23 °C, a 18 y 28 °C: ganancia **≤ 500 ppm** y offset **≤ 4 cuentas**, con 1 nA de fuga. Informa de la fuga máxima que cumple en cada rango |
| E3 | Autocero: asiento a media cuenta dentro de la espera del firmware (3 ms en X1, 1.5 ms en X2 y 0.1 ms en X0) |
| E4 | Modo común: con 0 a 4.5 V en X0, en ×1 y ×10, la salida **nunca da un valor válido engañoso**, y la recuperación de 4.0 V → 0.1 V es ≤ 1 ms |
| E5 | Ganancia ×1 ↔ ×10: margen de fase **> 45°** y recuperación a media cuenta en 200 mV ≤ 1 ms |
| E6 | Divisor con la red y la ESD: cada pieza ≤ 80 % de su tensión de trabajo de la hoja en régimen, y el pulso ≤ su sobrecarga de la hoja |
| E7 | Ruido **< 1 cuenta rms** en 100 ms en 200 mV y en 20 V |
| — | Informar: C(v) del 4051 (C3), la sensibilidad a la capacidad parásita (C2) y el consumo del bloque |

Fallar es un resultado válido: informa del valor y de lo que lo movería, sin cambiar piezas.

## 4. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque2.inc`;
- `S12/` y `ejecutar_s12.py`: 10 trabajadores, `--smoke`, `--resume`, `S3G4_MODELS` y 900 s por caso;
- `resultados/s12_*.csv`;
- `ACTA_S12.md`, con la tabla E1–E7 y la lista de piezas del bloque 2;
- tu diario en `ai-context/journal/`.

## 5. Lo que NO es tuyo

No cambies piezas ni topología. No toques los archivos de S11.x, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
