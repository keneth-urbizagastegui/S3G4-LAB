# Plan de simulación S13 — DMM, bloque 3: ohmios, diodo y continuidad

- Autor: Claude Code (auditor), 8 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Contrato:** `ESTUDIO_BLOQUE3.md`, §9 (criterios C1–C6 con margen) y la tabla de decisiones del §0, con las decisiones de Keneth del 8 oct en `ai-context/DECISIONS.md`:
  - c1;
  - BSS84 + BSS138 con 1 kΩ + 1 nF;
  - 1.19 µA y 0.30 µA en 2 MΩ y 20 MΩ;
  - diodo por X2 ×10.1;
  - continuidad a 1 mA con un Schottky;
  - fuga medida en el prototipo;
  - sin P33.
- **Lee antes:** el estudio entero, sus decks en `estudio_bloque3/` (punto de partida), `PLAN_SIMULACION_S11_4.md` y `ACTA_S11_4.md` (para C1), y `ACTA_S12d.md` (el bloque 2 que lee V_x).
- **Criterio de Keneth:** que funcione con margen y sin complicar. Es una campaña de confirmación. Los fallos marginales de modelo o de criterio se clasifican en el acta y no se persiguen.

## 1. Circuito

El del estudio con las decisiones de arriba:
- **cadena de ohmios:** relé TQ2SA → R1 = 3 × 510 Ω (HoCR2512) → N1 (SMAJ12CA a COM, **inyección de la fuente aquí**) → R_S 2.7 kΩ → N2 con las sujeciones (2 × BAV199, 2 × BZT52C5V6);
- **fuente P43:** TLV2372 doble, BSS138 en la referencia, BSS84 de paso, BAT54 de bloqueo, R_rango y 2 × 74HCT4051 (fuerza y sentido), con la compensación de 1 kΩ + 1 nF;
- **lectura de V_x:** por X0 (buffer OPA4192, bloque 2); **el diodo**, por X2 ×10.1;
- **continuidad:** A → ÷2 → un Schottky a COM → PB14; COMP7 ideal con el umbral del DAC2 e histéresis HYST = 1.

Modelos: los del repositorio (TLV2372, OPAx192, BSS84, BAT54, 74HC4051 `SWI1`). El BSS138 es genérico de LTspice, ajustado a la hoja si está, o marcado como supuesto.

## 2. Pruebas y criterios

Los **C1–C6 del §9 del estudio**, tal como están escritos, con P33 fuera (no se prueba). C4 se hace con la INL de la hoja (2.1 / 3.2 LSB), porque la medida aún no existe.

## 3. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque3.inc` y `ejecutar_s13.py` (10 trabajadores, `--smoke`, `--resume`, 900 s por caso);
- `resultados/s13_*.csv`;
- `ACTA_S13.md`, con la tabla C1–C6 y la lista de piezas del bloque 3;
- tu diario.

No cambies piezas ni topología. No toques los archivos anteriores, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
