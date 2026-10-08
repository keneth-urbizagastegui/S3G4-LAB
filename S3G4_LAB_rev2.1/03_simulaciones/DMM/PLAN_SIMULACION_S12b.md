# Plan de simulación S12b — DMM, bloque 2: confirmación con el buffer antes del mux

- Autor: Claude Code (auditor), 8 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Lee antes:**
  - `PLAN_SIMULACION_S12.md`, que sigue vigente salvo lo que cambia aquí;
  - `ACTA_S12.md` y `AUDITORIA_CLAUDE_S12.md`;
  - en `ai-context/DECISIONS.md`, la entrada del 8 oct «buffer antes del mux».
- Reutiliza `ejecutar_s12.py` y `comun/dmm_bloque2.inc`.

## 1. Cambios en el circuito

1. **Buffer:** un OPA2192 doble (modelo de TI) a ±4.9 V como seguidor en X0 y en X1, entre el bloque 1 y el 74HCT4051.
   - X0 → buffer A → canal 0 del mux.
   - Toma ÷10 (tras sus 100 Ω) → buffer B → canal 1.
   - X2 (÷100) va directo al canal 2. Comprueba que nunca pasa de ±4.9 V; con 50 V, ≈ 0.5 V.
   - La protección de las entradas del buffer sigue siendo la del bloque 1: R_PROT con BAV199 en X0, y los 100 Ω con la sujeción de la toma. **Mide la corriente por las entradas del OPA2192 frente a su máximo absoluto de la hoja** con 50 V, con la red de 230 Vrms (modelo de protección de S11.4) y con la ESD.
2. **Las 3 × 3.3 kΩ de la compensación,** marcadas como antipulso. Criterio de impulso en E6 (abajo).
3. Lo demás, igual que en S12: divisor de 6 × 1.5 MΩ, 74HCT4051, OPA2192 A, y 91 k/10 k con el TMUX4053.

## 2. Pruebas y criterios

Repite E1–E7 de S12 con el circuito nuevo, con estos cambios:

| # | Cambio |
|---|---|
| E1 | Los cuatro rangos con el buffer. Informa además de la caída sin corregir a 20 kHz en X0 (el estudio estimaba −1.3 %) |
| E2 | Fuga del mux de 1 nA y fuga en COM y en la entrada del buffer de 0.85 nA, a 18 y 28 °C. Informa de la fuga máxima tolerable |
| E3 | **Lo principal:** canales no seleccionados siempre dentro de ±4.9 V de 0 a ±50 V en los cuatro rangos; error ≤ 1 cuenta tras el asiento (3 / 1.5 / 0.1 ms) |
| E5 | Criterio **≥ 40°** en el peor caso (decisión de Keneth) |
| E6 | **Criterio de impulso:** informa de la tensión de pico, la duración por encima de la tensión de trabajo y la energía en cada pieza del divisor y en cada 3.3 kΩ con la ESD (contacto y aire) y con GDT + 14D431K. Sin aprobar ni suspender por la sobrecarga de 5 s |
| E8 | **Nuevo:** entradas del OPA2192 buffer: corriente ≤ 50 % de su máximo absoluto en los casos de 50 V, la red y la ESD |

## 3. Entregables

- `comun/dmm_bloque2b.inc`, `ejecutar_s12b.py` y `resultados/s12b_*.csv`;
- `ACTA_S12b.md`, con la tabla E1–E8 y la lista de piezas final del bloque 2;
- tu diario.

No cambies piezas. No toques los archivos de S11.x/S12, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
