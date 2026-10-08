# Plan de simulación S12c — DMM, bloque 2: confirmación sin toma ÷10

- Autor: Claude Code (auditor), 8 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Lee antes:**
  - `PLAN_SIMULACION_S12b.md` (y S12), que siguen vigentes salvo lo que cambia aquí;
  - `ACTA_S12b.md` y `AUDITORIA_CLAUDE_S12b.md`;
  - en `ai-context/DECISIONS.md`, la entrada del 8 oct «sin toma ÷10».
- Reutiliza `ejecutar_s12b.py` y `comun/dmm_bloque2b.inc`.

## 1. Cambios en el circuito

1. **Divisor con una sola toma:**
   - 6 × 1.5 MΩ + 910 kΩ arriba y 100 kΩ abajo (toma ÷100 ≈ 100 k / 10.01 M);
   - la misma compensación (3 × [100 pF + 3.3 kΩ], 330 pF sobre 910 kΩ y 3.0 nF sobre 100 kΩ);
   - **sin la conexión de la toma ÷10, sin su sujeción BAV199 y sin sus 100 Ω.**
2. **Mux:** X0 a través del buffer OPA2192; X2 (÷100) directo; X3 = COM. X1 queda libre (a COM).
3. **Rangos:**

   | Rango | Entrada | Ganancia de A |
   |---|---|---|
   | 200 mV | X0 | ×10 |
   | 2 V | X0 | ×1 |
   | **20 V** | X2 | **×10** |
   | 50 V | X2 | ×1 |

   La prueba de diodo, por X0 (relé de ohmios cerrado; tensión ≤ 4 V).
4. **Buffer de X0:** usa media OPA2192. Si el circuito lo permite, el buffer de X0 y el amplificador A van en el **mismo OPA2192 doble**; si no, informa de por qué.
5. **E5:** reparte la capacidad CD(ON) del TMUX4053 a los dos lados de su Ron e interpola la fase (auditoría de S12b, §4).

## 2. Pruebas y criterios

E1–E8 de S12b con estos cambios:

| # | Cambio |
|---|---|
| E1 | Los 4 rangos, **incluido 50 Vrms en alterna** (71 Vpk), y el rango de 20 V con ×10 |
| E2 | Fuga ≤ 0.6 nA en X0 (decisión de Keneth); en X2, informa de la fuga tolerable en 20 V y en 50 V |
| E3 | Mux y buffer dentro de ±4.9 V (su modo común) de 0 a ±50 V DC y con 50 Vrms; error ≤ 1 cuenta tras el asiento |
| E5 | ≥ 40° con la CD(ON) repartida (solo los casos de lazo) |
| E6 | Criterio de impulso (≥ 1.5 kV, ≥ 25 µJ y ΔR ≤ 1 %). Informa |
| E8 | Corriente **de la pinza** (no la capacitiva) ≤ 50 % de los ±10 mA de la hoja del OPA2192 |

E4 y E7, igual que en S12b.

## 3. Entregables

- `comun/dmm_bloque2c.inc`, `ejecutar_s12c.py` y `resultados/s12c_*.csv`;
- `ACTA_S12c.md`, con la tabla E1–E8 y la lista de piezas final del bloque 2;
- tu diario.

No cambies piezas salvo lo indicado. No toques los archivos de S11.x/S12/S12b, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
