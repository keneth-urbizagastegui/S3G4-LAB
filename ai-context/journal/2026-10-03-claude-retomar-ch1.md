# 2026-10-03 — Claude Code: cómo retomar el canal rápido CH1 (rev 2.1)

Resumen para la siguiente sesión. El detalle está en `2026-10-02-claude-ramas-y-canal-rapido.md`.

## Dónde estamos

- Plan de CH1 por etapas S0–S8: `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` §6. El estado actualizado está en `canal_rapido_ch1.html` §7, con las etapas marcadas sobre el esbozo de §3.
- **Cerradas:** S0, S1, S1b, S2 y S2b. **Siguiente: S3** (ganancia). Luego S4 (etapa final a 3.3 V con offset), S5 (filtro; Keneth elige el tipo con los resultados), S6 (ADC), S7 (canal completo) y S8 (esquema en KiCad).
- Decisiones del 2–3 oct en `ai-context/DECISIONS.md`:
  - disparo sin entrada externa;
  - sin la red conectada directamente: ±100 V y ESD ±8 kV aire / ±4 kV contacto;
  - P1 = ÷100 con 6 tomas;
  - CH2/CH3 a 1 MHz;
  - trimmer SEHWA 2–6 pF con Cb seleccionado en prueba;
  - piezas de 200 V;
  - OPA810 fuente única.

## Tareas abiertas para S3

1. Elegir U103 (×5 y ×10): GBW ≥ 100 MHz en CH1 (≥ 50 en CH2/CH3), SR ≥ 30 V/µs, ±5 V, ≤ 10 nV/√Hz, ≤ 3–4 mA. El ruido de C.5 en CH1 da 0.41 % a 5 y 500 mV/div (objetivo 0.35 %); remedios posibles: R_PROT de 470 Ω (revisar E5/E7) y red de ganancia de 499 Ω.
2. Pedir a Keneth el modelo SPICE y la hoja del candidato elegido.
3. Escribir `PLAN_SIMULACION_S3.md` y `ENCARGO_CODEX_S3.md` con el patrón de S2b: paralelo, `--smoke`, `S3G4_MODELS`, criterios de E11–E15 de `revision_entrada_ch1.html` §6. C3 de protección se juzga por **corriente ≤ 10 mA**, no por tensión.

## Cómo trabajamos con Codex (lecciones de S1–S2b)

- **CLI de la aplicación:** `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe` (0.160.0). Cambia de carpeta cuando se actualiza; búscalo en `…\OpenAI\Codex\bin\*\codex.exe`. El del PATH (0.154.0) rechaza `gpt-6.1-sol`.
- `-m gpt-6.1-sol -c model_reasoning_effort=medium`. **Lanzar con `Start-Process`** (proceso independiente), con el prompt por stdin desde un fichero y `-o` para la respuesta final, más un Monitor que vigile ese fichero. Las tareas en segundo plano de Claude Code se cortan a la hora.
- Exigir **ejecución paralela (10 trabajadores) desde el principio**: la secuencial de S1b iba a tardar 5–6 h.
- **Auditar reejecutando en una copia con ruta corta** (`…\Temp\claude\<algo>`) y `S3G4_MODELS`. La ruta del scratchpad supera los 260 caracteres de Windows y LTspice falla al abrir su `.db`.
- Trampas de modelos en `Simulation_LTSpice/models/LEEME.md`: el orden de nodos del OPA810 y el `.ENDS` suelto de BAV199.txt.

## Primera búsqueda de U103 (3 oct, sin decidir)

| Pieza | LCSC · stock · precio | GBW · SR | Ruido | Consumo | Nota |
|---|---|---|---|---|---|
| **LM6172** (TI, doble) | C180430 · 11 167 · 2.09 USD | 100 MHz · 3000 V/µs | 12 nV/√Hz | 2.3 mA/canal | La del DSO112; ±15 V; bipolar (1.2 µA de Ib, sin importancia tras el buffer). Ruido por encima del objetivo de 10 nV/√Hz → C.5 empeora en CH1 |
| LMH6643 (TI, doble) | C44880 · 6273 · 1.08 USD | 130 MHz · 130 V/µs | 17 nV/√Hz | 2.7 mA/canal | Barato, pero ruidoso |
| AD8056 (ADI, doble) | C17348 · 103 · 9.88 USD | 300 MHz · 1400 V/µs | 6 nV/√Hz | 6 mA/canal | Muy bueno, poco stock |
| AD8065 (ADI) | C9648 · 4953 · 5.60 USD | 145 MHz | 7 nV/√Hz | 6.6 mA | **Cuidado:** diferencial máxima de 1.8 V; en saturación de la etapa ×5 la diferencial puede llegar a ~4 V |
| OPA2810, OPA2365 | — | 70 / 50 MHz | — | — | No llegan a los 100 MHz de CH1 |

Pendiente para S3: comprobar en la hoja de cada candidato la **diferencial máxima de entrada** (las etapas de ganancia saturan con sobrecarga) y el ruido real; decidir con Keneth.
