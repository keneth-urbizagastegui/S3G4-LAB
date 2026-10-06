# Plan de simulación S1b — trimmer, sonda corregida y C_EQ en prueba

- Autor: Claude Code (auditor), 2 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S1b.md`.
- Continúa S1. **Lee antes:** `PLAN_SIMULACION_S1.md` (circuito, nombres y reglas, que siguen vigentes salvo lo que cambia aquí), `ACTA_S1.md` y `AUDITORIA_CLAUDE_S1.md`. La auditoría explica por qué existe S1b.

## 1. Qué cambia respecto a S1

1. **Decisión de Keneth (DECISIONS.md, 2 oct):**
   - **un trimmer por canal** para la compensación de ÷100;
   - **C_EQ seleccionado en prueba**: C0G fijo elegido al medir el prototipo, sin trimmer.
2. **C_SEL_EST corregida** (dudas 1 y 3 de S1):
   - los diodos con su capacidad polarizada `CJ_POL = CJO / (1 + 5/VJ)^M` (VJ y M del modelo DBAV199: 0.6 V y 0.3);
   - las **dos** COFF_SW abiertas.

   Queda: `C_SEL_EST = 2·CJ_POL + CSEL_PAR + CIN_BUF + 2·COFF_SW`. CEQ, CX1_TOT, CS y CB se recalculan a partir de ella, siempre con `.param`.
3. **Sonda de E3 corregida** (error del plan de S1). Modelo: punta de 9 MΩ ∥ CTIP, cable de 80 pF concentrado y sin CCOMP. CTIP es el ajuste de compensación de la sonda; se elige en ÷100 y se conserva en ×1.
4. **Paso temporal:** en E3, paso máximo ≤ 2 ns al menos durante los 5 µs que siguen al flanco medido. Con 200 ns aparecía un pico falso del 2.8 % (auditoría, punto 5). La convergencia se comprueba con el caso **compensado**: 2 ns frente a 1 ns.
5. **Dos campañas de tolerancias** en vez de una:
   - **A, producción:** lo que varía de una placa a otra. Es la que dimensiona el trimmer y decide los criterios.
   - **B, incertidumbre de diseño:** los rangos amplios de S1. Muestra qué hay que medir en el prototipo; es sólo informativa.

## 2. El trimmer

Va en paralelo con **una** de las dos capacidades de la rama superior (Ct2), que se parte en una parte fija `CT2F` y el trimmer `CTRIM`:

```
Ct2_total = CT2F + CTRIM,  con  CT2F = CT1 − CTRIM_MED   (derivado: con el trimmer a mitad de recorrido, Ct2_total = CT1)
```

- Rangos a comparar (mínimo–máximo): **R1 = 2–6 pF** (SEHWA, C22468120, ya usado en la rev 2.0), **R2 = 3–10 pF** y **R3 = 5–20 pF**.
- CTRIM_MED es la mitad del rango. Si CT2F sale negativo o por debajo de 1 pF con algún rango, informar y saltar ese rango.
- CT1 = 20 pF (nominal). El caso 12 pF de S1 ya no se simula.
- Con CTRIM = CTRIM_MED, el circuito nominal es igual al de S1 salvo por la corrección de C_SEL_EST. **Comprobarlo.**
- **Ajuste simulado:** en cada caso del MC, en POS = 100 y CPL = DC, buscar el CTRIM dentro del rango que minimiza la mayor desviación de planitud entre 10 kHz y 2 MHz respecto a 1 kHz. Es lo que haría un técnico con una cuadrada de calibración. Vale la búsqueda en rejilla de 0.05 pF o por bisección. Informar el CTRIM elegido y si quedó contra un tope del rango.

## 3. Tolerancias

| Parámetro | Campaña A, producción | Campaña B, diseño (como en S1) |
|---|---|---|
| RT1, RB | 0.1 % | 0.1 % |
| RS, RBIAS, REQ | 1 % | 1 % |
| CT1, CT2F, CB, CS, CEQ | 2 % | 2 % |
| CTRIM (en el valor ajustado) | ±0.1 pF de resolución | ±0.1 pF |
| CAC | 5 % | 5 % |
| COFF_RELE | 1 pF ± 20 % | 0.5–1.5 pF |
| CSEL_PAR | 3 pF ± 0.3 pF | 1.5–4.5 pF |
| CIN_BUF | 5 pF ± 10 % | 3–7 pF |
| CJO | ± 20 % | ± 30 % |
| CX1 | 2 pF ± 0.2 pF | 1–3 pF |
| CBNC | 3 pF ± 0.3 pF | 2–4 pF |
| COFF_SW | 0.5 pF ± 20 % | 0.5 pF ± 20 % |

Distribuciones uniformes, ≥ 200 casos por campaña, semilla fija.

**Las cifras de producción de la columna A son supuestos del auditor, no datos de hoja.** El HFD27 no declara su Coff, y lo mismo pasa con la dispersión de unidad a unidad de las parásitas de layout. Si te parecen incoherentes, ponlo en dudas, pero úsalas.

En la campaña B, además, **emular la selección en prueba de C_EQ**:
1. En cada caso, calcular el C_EQ que anula ΔCin (bisección en E1).
2. Redondearlo al valor E24 de C0G más cercano (…, 9.1, 10, 11, 12, 13, 15, 16, 18, 20 pF).
3. Informar la ΔCin residual con ese valor.

En la campaña A, C_EQ es el valor nominal derivado y no se selecciona.

## 4. Pruebas

| Prueba | Qué | Dónde |
|---|---|---|
| E1b | Zin y Cin nominales, POS {1, 100} × CPL {DC, AC, GND}, con C_SEL_EST corregida y CTRIM a mitad de recorrido | nominal |
| E2b | Respuesta BNC → buffer nominal, como E2 de S1 | nominal |
| E3b | Sonda compensable (§1.3), paso ≤ 2 ns. En ÷100, elegir CTIP que minimiza el error del escalón y, sin tocarlo, medir en ×1. Sobreimpulso y error a 2, 20 y 200 µs, referidos a la altura del escalón. Convergencia de 2 frente a 1 ns en el caso compensado | nominal y cada caso de A |
| E4A | Campaña A: ajuste del trimmer (§2) con cada rango R1–R3; luego E1, planitud de ÷100 y ×1, y E3b | 200 casos |
| E4B | Campaña B: igual que E4A sólo con el rango más pequeño que haya cumplido S1b-C6, más la selección de C_EQ | 200 casos |

## 5. Criterios de aceptación

Fallar es un resultado válido; informar siempre el valor medido.

| # | Criterio | Prueba |
|---|---|---|
| S1b-C1…C4 | Los de S1 (C1–C4), en nominal y con CT1 = 20 pF | E1b, E2b |
| S1b-C5 | Nominal: sobreimpulso y error a 2 µs ≤ 2 % del escalón en ×1 y en ÷100, con CTIP fijado en ÷100; convergencia: cambio ≤ 0.05 puntos entre 2 y 1 ns | E3b |
| S1b-C6 | Campaña A, por rango: **en los 200 casos** el trimmer alcanza planitud de ÷100 dentro de ±1 % de 10 kHz a 2 MHz **sin tocar tope**. Informar el rango más pequeño que lo cumple | E4A |
| S1b-C7 | Campaña A: \|ΔCin\| ≤ 2 pF en los 200 casos, con C_EQ nominal fijo | E4A |
| S1b-C8 | Campaña A (con el rango de C6): en ×1, con CTIP fijado en ÷100 en ese mismo caso, sobreimpulso y error a 2 µs ≤ 2 % | E4A |
| S1b-C9 | Campaña A: \|Zin − 1 MΩ\| ≤ 2 % y planitud ×1 ±1 % en todos los casos | E4A |
| — | Campaña B: sin criterio. Informar planitud tras el ajuste, casos contra tope, ΔCin antes y después de seleccionar C_EQ, y el reparto de los valores E24 elegidos | E4B |

## 6. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, **sin modificar los entregables de S1**:

1. `comun/ch1_comun_s1b.inc`: copia evolucionada del include, con la C_SEL_EST corregida y el trimmer (parámetro CTRIM y RANGO). El de S1 no se toca.
2. `S1b/` con los `.cir` de E1b, E2b, E3b, E4A y E4B, y los generados.
3. `ejecutar_s1b.py`:
   - corre todo y aplica los criterios desde una única tabla;
   - escribe `resultados/s1b_*.csv` y `resultados/s1b_resumen.md`;
   - sale con código ≠ 0 sólo si una simulación da error.
4. `ACTA_S1b.md`, con:
   - tabla de criterios;
   - el rango de trimmer mínimo que cumple C6, con el reparto del CTRIM elegido;
   - casos contra tope;
   - lo que enseña cada prueba;
   - la campaña B;
   - **dudas y contradicciones sin resolver**;
   - código de salida.
5. Tu diario en `ai-context/journal/`.

## 7. Lo que NO es tuyo

- No cambies valores de diseño para que algo pase, salvo los derivados que este plan manda recalcular. No elijas el rango del trimmer en el acta: informa cuál cumple.
- No toques los entregables de S1, ni `chequeo_claude/`, ni nada fuera de `CH1_entrada/` salvo tu diario. Ni `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 8. Cómo voy a auditar

1. Reejecuto `ejecutar_s1b.py` en una copia limpia y comparo el CSV byte a byte.
2. C_SEL_EST, CT2F y los derivados frente a §1–§2, con `.param`.
3. Que con CTRIM a mitad de recorrido el nominal reproduce S1 salvo la corrección explicada.
4. E3b nominal frente a mi comprobación: con la sonda compensable y 2 ns, ÷100 +0.11 % y ×1 +0.55 % con la C_SEL_EST antigua. La nueva debe moverlo poco y en el sentido de reducir ΔCin.
5. El paso temporal real de E3b y la convergencia en el caso compensado.
6. Que el ajuste del trimmer opera en POS = 100 y que los casos contra tope se informan, no se descartan.
