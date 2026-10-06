# Auditoría de Claude — S1b, trimmer, sonda corregida y C_EQ en prueba

- Fecha: 2026-10-03, madrugada.
- Auditor: Claude Code (Opus 5.5).
- Objeto: trabajo de Codex (CLI de la aplicación, `gpt-6.1-sol`, esfuerzo `medium`, sesión `01a0ff52-374c-76b0-a7e6-3795bc2eecff`, reanudada dos veces).
  - Primera reanudación: el límite de una hora de las tareas en segundo plano de Claude Code cortó la primera ejecución.
  - Segunda reanudación: Keneth paró la versión secuencial para paralelizarla.
- Entregó `comun/ch1_comun_s1b.inc`, `S1b/`, `ejecutar_s1b.py` (10 trabajadores), `ACTA_S1b.md`, 14 CSV y su diario `ai-context/journal/2026-10-02-2115-codex-s1b.md`.
- Contrato: `PLAN_SIMULACION_S1b.md` §8.

## Veredicto

1. **Reproducible.** Mi ejecución de `ejecutar_s1b.py` sobre una copia limpia sale con código 0 y da 9375 simulaciones sin errores ni advertencias. **Los 14 CSV son idénticos byte a byte** a los de Codex. Un primer intento se perdió por el reinicio del PC a las 23:36; el segundo terminó sin incidencias.
2. **Valores y derivados correctos (§1–§2):**
   - `CJ_POL = CJO/(1+5/VJ)^M` = 0.768 pF por diodo;
   - `C_SEL_EST` con las dos COFF_SW = 10.54 pF; CEQ igual; CS = 1.356 nF; CB = 1.087 nF;
   - `CT2F = CT1 − CTRIM_MED`;
   - el modelo del diodo usa los mismos VJ y M.
3. **Equivalencia con S1:** con el trimmer a mitad de recorrido en R1, R2 y R3, el nominal reproduce S1 con cambio relativo 0 (`s1b_equivalencia.csv`, `s1b_referencia_s1.csv`).
4. **Paso temporal y convergencia (lección de S1):** 1003 ventanas finas verificadas, con paso máximo observado de 1.07 ns. Convergencia de 2 frente a 1 ns **en el caso compensado**: cambio ≤ 4·10⁻⁷ puntos.
5. **Método del ajuste, aceptable:** un modelo nodal en Python propone el trimmer y LTspice verifica el candidato, sus vecinos y los dos topes. Los criterios salen sólo de `.meas` de LTspice.
6. **Los 9 criterios pasan:**

| # | Valor | |
|---|---|---|
| C1 | Zin 0.9991–1.0003 MΩ | ✓ |
| C2 | Cin 26.29–26.69 pF; ΔCin 0.40 pF (era 0.54 en S1) | ✓ |
| C3 | error de ganancia ≤ 0.32 % | ✓ |
| C4 | planitud 0.24 %; pico 0.001 dB; corte AC 8.80 Hz | ✓ |
| C5 | sonda: sobreimpulso 0.02 %; error a 2 µs 0.34 % | ✓ |
| C6 | trimmer: planitud ÷100 ≤ 0.38 % en 200/200 con R1, R2 y R3, sin topes | ✓ |
| C7 | \|ΔCin\| ≤ 1.41 pF en producción con C_EQ nominal fijo | ✓ |
| C8 | sonda en producción: sobreimpulso ≤ 0.51 %, error a 2 µs ≤ 1.50 % | ✓ |
| C9 | Zin ±0.26 %, planitud ×1 ±0.29 % en producción | ✓ |

## El trimmer: «R1 basta», pero sin margen

| Rango | Recorrido usado en A (producción) | Margen hasta los topes | En B (diseño) | Pieza LCSC |
|---|---|---|---|---|
| R1 2–6 pF | 2.55 – **5.95** pF (mediana 4.05) | 0.55 abajo / **0.05 pF arriba** | **29/200 contra tope** | SEHWA STC3MA06-T1, **C22468120**, 4501 ud, 0.49 USD, 100 V, tolerancia 0 / +50 % |
| R2 3–10 pF | 5.0 – 8.4 pF | 2.0 / 1.6 pF | no simulado | SEHWA STC3MB10-T1, C22468121, **16 ud** (no cumple RF-19) |
| R3 5–20 pF | 11.0 – 14.3 pF | 6.0 / 5.7 pF | no simulado | sin pieza equivalente con stock |

Lectura del auditor:
- En producción, R1 cumple **por 0.05 pF**, y la dispersión de producción de A son supuestos míos (el HFD27 no declara su Coff).
- En B (Coff entre 0.5 y 1.5 pF), R1 toca tope en el 15 % de los casos: con R1, **el nominal de diseño tiene que estar centrado de antemano**.
- La tolerancia 0 / +50 % de la SEHWA ayuda arriba: su máximo real está entre 6 y 9 pF. Abajo no da margen.

**Propuesta (decide Keneth):** quedarse con **R1, la SEHWA C22468120** (stock alto) y **centrarla en el prototipo**:
1. Medir en la primera placa la Coff real del HFD27 y la capacidad del nodo SEL.
2. Elegir **Cb «seleccionado en prueba»**, igual que C_EQ, para que el trimmer quede cerca de la mitad de su recorrido. Un paso de ~10 pF en Cb (1 %) mueve el punto de ajuste unos 0.1 pF de Ct.
3. Así R1 sólo cubre la dispersión de producción (A), donde ya da ±1.7 pF de recorrido útil frente a los ±1.7 pF que se usan.

Alternativa sin centrado: R2 (3–10 pF), con margen de sobra, pero hoy sin stock en LCSC.

## Campaña B (incertidumbre de diseño, informativa)

- ΔCin con C_EQ nominal: hasta 3.47 pF (mediana 1.09). Con C_EQ seleccionado en E24, **≤ 0.96 pF** (mediana 0.26). La selección en prueba funciona; los valores salen entre 7.5 y 15 pF, la mayoría entre 9.1 y 12 pF.
- Planitud de ÷100 tras el ajuste: hasta 2.64 %, por los 29 casos contra tope de R1. Lo resuelve el centrado con Cb en prueba.

## Dudas de Codex

| # | Duda | Juicio del auditor |
|---|---|---|
| 1 | Las tolerancias de A son supuestas | Correcto, y dicho en el plan. Se cierra midiendo el prototipo |
| 2 | Una COFF_SW vuelve a SEL a través de C_AC | Correcto y menor (0.5 pF). La estimación se queda así; C_EQ se selecciona en prueba de todos modos |
| 3 | C9 no fija banda | Bien resuelto: usó 10 Hz–2 MHz e informó también 10 kHz–2 MHz |
| 4 | Precisión de CTIP, correlaciones y ±0.1 pF no definidas | Bien resueltas y documentadas |
| 5 | 200 casos son una muestra, no una garantía | Correcto. Por eso el margen de 0.05 pF de R1 no basta sin centrado |
| 6 | Diodo genérico y buffer ideal | Correcto: es S2 |
| 7 | La selección de C_EQ mueve un poco la planitud tras el ajuste | Correcto y despreciable (2.644 → 2.649 %) |

## Incidencias de proceso

- El límite de una hora de las tareas en segundo plano de Claude Code corta los encargos largos. Los siguientes se lanzan como proceso independiente (`Start-Process`) con un vigilante.
- La ejecución secuencial iba a ~1 caso por minuto (5–6 h). Paralelizada con 10 trabajadores bajó a 34 min, con CSV idénticos al secuencial en la prueba de humo.
- Tras el reinicio, el CLI de Codex de la aplicación pasó a 0.160.0 en `C:\Users\Keneth\AppData\Local\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe`; la ruta anterior de los encargos ya no existe.

## Qué sigue

1. Decisión de Keneth: trimmer R1 (SEHWA C22468120) con **Cb seleccionado en prueba** para centrarlo, o R2 sin stock.
2. **S2 (protección y abusos: E5–E10)** necesita los modelos de fabricante: BAV199 de Nexperia y un buffer FET candidato. Hay que elegir el buffer en LCSC (Cin ≤ 5 pF, Ib ≤ 20 pA, GBW ≥ 50 MHz) y descargar su macromodelo.
