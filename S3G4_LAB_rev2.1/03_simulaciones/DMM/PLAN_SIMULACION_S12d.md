# Plan de simulación S12d — DMM, bloque 2: cierre con el OPA4192

- Autor: Claude Code (auditor), 8 oct 2026. Ejecuta: Codex (gpt-6.1-sol, esfuerzo low). Audita: Claude (Opus, medio).
- **Lee antes:**
  - `PLAN_SIMULACION_S12c.md`, que sigue vigente salvo lo que cambia aquí;
  - `AUDITORIA_CLAUDE_S12c.md`;
  - en `ai-context/DECISIONS.md`, la entrada del 8 oct «OPA4192 con buffer en X2, y criterio de no complicar».
- **Criterio de Keneth:** que funcione con margen. Es una confirmación corta, no otra campaña completa. Si un resultado es marginal, clasifícalo (físico, modelo o criterio) en el acta, pero no busques decimales.

## 1. Cambios en el circuito respecto a S12c

1. **OPA4192** (modelo de TI `OPAx192.LIB`, el mismo de la familia):
   - buffer de X0;
   - buffer de X2 (÷100);
   - amplificador A (ganancia 91 k/10 k con el TMUX4053);
   - la cuarta sección, como seguidor a masa (no se usa).
2. **10 kΩ en serie delante de cada buffer** (X0 y X2), en lugar de los 100 Ω de X0.
3. **Condensadores:** 330 pF C0G de ≥ 100 V y 3 nF de ≥ 25 V.

## 2. Pruebas: solo E2, E3, E5 y E8 (las demás pasaron en S12c y no cambian)

| # | Qué | Criterio |
|---|---|---|
| E2 | Offset tras calibrar a 23 °C, a 18 y 28 °C, en los 4 rangos, con la **fuga de hoja del 74HC4051 en ON** (±0.4 µA a 25 °C) a la salida de los buffers y 0.6 nA en las entradas de los buffers | ≤ 4 cuentas |
| E3 | Error tras la espera del firmware (3 ms en X2 y 0.1 ms en X0) en los 4 rangos, de 0 a ±50 V DC y con 50 Vrms. Corriente por la pinza de cada buffer | Error ≤ 1 cuenta; pinza ≤ 50 µA continuos y ≤ 5 mA en la ESD; 50 mV de tolerancia sobre el riel |
| E5 | Margen de fase de A, con la CD(ON) del TMUX repartida | ≥ 40° |
| E8 | Entradas de los buffers con 50 V, la red y la ESD (modelo de protección de S11.4) | Pinza ≤ 5 mA |

## 3. Entregables

- `comun/dmm_bloque2d.inc`, `ejecutar_s12d.py` y `resultados/s12d_*.csv`;
- `ACTA_S12d.md`, con E2/E3/E5/E8 y la **lista de piezas final del bloque 2**;
- tu diario.

No cambies piezas. No toques los archivos anteriores, `01_diseno/`, `models/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.
