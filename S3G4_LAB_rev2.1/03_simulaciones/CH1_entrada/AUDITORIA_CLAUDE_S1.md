# Auditoría de Claude — S1, entrada pasiva P4b de CH1

- Fecha: 2026-10-02, noche.
- Auditor: Claude Code (Opus 5.5).
- Objeto: trabajo de Codex (CLI de la aplicación 0.159.0-alpha, `gpt-6.1-sol`, esfuerzo `low`, sesión `01a0ff12-386a-7b23-a2be-1160ccfdbc80`). Entregó `comun/ch1_comun.inc`, `S1/E1…E4`, `ejecutar_s1.py`, `ACTA_S1.md`, `RESPUESTA_FINAL_S1.md`, `resultados/` y su diario.
- Contrato: `PLAN_SIMULACION_S1.md` §8. Comprobaciones propias en `chequeo_claude/e3_auditoria/`.

## Veredicto

1. **Trabajo reproducible:** mi ejecución de `ejecutar_s1.py` sobre una copia limpia (sin `.raw`) sale con código 0 y da un `s1_resultados.csv` **idéntico byte a byte** al de Codex (2868 filas).
2. **Valores y reglas de §3, correctos.** Están todos los parámetros. Los derivados (C_SEL_EST, CEQ, CX1_TOT, CS, CB) se calculan con `.param`. La Coff de K1a cuenta como capacidad de arriba en CB. La capacidad de los diodos va sólo en su CJO. CIN_BUF va explícita detrás de RPROT. Las piezas de compensación quedan fijas en su valor nominal durante el Monte Carlo, con su propia tolerancia: así se pedía.
3. **Nominal: C1–C4 pasan.** Zin = 0.9991 MΩ en las dos posiciones. Cin = 26.71 / 27.25 pF (Δ 0.54 pF). Planitud entre −0.17 % y +0.06 %. Corte AC en 8.73 / 8.80 Hz, que coincide con mi cálculo (8.75 / 8.83 Hz). Con mi chequeo (999.1 kΩ; Δ 0.08 pF), la diferencia de ΔCin la explica la duda 1 de Codex: la capacidad real de los BAV199 polarizados es menor que su CJO.
4. **C5 fallaba por mi plan, no por el diseño.** La sonda del contrato (9 MΩ ∥ 10 pF, cable de 80 pF) no se puede compensar: 9 MΩ · 10 pF = 90 µs, frente a 1 MΩ · (27 + 80) pF = 107 µs en la entrada. Añadir CCOMP sólo empeora, y por eso el óptimo salió en 0 pF. Con una sonda compensable (C de punta = (Cin÷100 + Ccable)/9, CCOMP = 0) y paso de 2 ns:

   | CT1 | Posición | Sobreimpulso | Error a 2 µs | a 20 µs | a 200 µs |
   |---|---|---|---|---|---|
   | 20 pF | ÷100 (compensada aquí) | +0.11 % | +0.10 % | +0.06 % | +0.01 % |
   | 20 pF | ×1 (sin retocar) | +0.55 % | +0.54 % | +0.45 % | +0.07 % |
   | 12 pF | ÷100 | +0.13 % | +0.11 % | +0.06 % | +0.01 % |
   | 12 pF | ×1 | +0.57 % | +0.56 % | +0.46 % | +0.07 % |

   **S1-C5 se cumple con margen** (≤ 2 %) en el nominal.
5. **Hallazgo sobre el paso temporal:** con el paso máximo de 200 ns del entregable, la sonda compensada da un pico falso del 2.8 % en ×1 que desaparece con 2 ns. La comprobación de convergencia de Codex (200 frente a 50 ns) sólo se hizo con la sonda sin compensar, donde no aparece. **Para E3 hace falta un paso de ≤ 5 ns.**

## E4 — tolerancias (Monte Carlo de 200 casos y sensibilidad)

| Medida (CT1 = 20 pF) | Mediana | Rango | Fuera de criterio | Lo que manda |
|---|---|---|---|---|
| Zin, todas las posiciones | 0.999 MΩ | 0.9975–1.0009 MΩ | 0/200 | — |
| Planitud ×1 a 1 MHz | −0.02 % | −0.20 / +0.16 % | 0/200 | — |
| Planitud ÷100 a 1 MHz | −0.46 % | −6.7 / +6.1 % | 159/200 (±1 %) | Coff del relé (±4.4 % con 0.5–1.5 pF), luego Cb (±2 % por cada 2 %) y Ct (±0.9 %) |
| ΔCin | 1.25 pF | 0.01–4.14 pF | 47/200 (> 2 pF) | Cin del buffer (+1.96 pF en su extremo de 3 pF) y CSEL_PAR (+1.47 pF) |

Con CT1 = 12 pF, la planitud en ÷100 empeora (174/200 fuera) y ΔCin no cambia.

Mi lectura, que decide Keneth:
- **La planitud de ÷100 necesita un ajuste por canal.** Con sólo la dispersión de producción (Cb y Ct al 2 %, la Coff de un relé a otro) ya se pasa de ±1 %. Es lo mismo que hace el DSO112 con su C24. Un trimmer de 2–6 pF en paralelo con uno de los dos condensadores de Ct sólo da **−3.6 / +3.3 %** de rango (Ct + Coff de 11.48 a 12.30 pF). **No alcanza el peor caso del MC (±6.7 %).** Ese MC trata la Coff como desconocida entre 0.5 y 1.5 pF; la dispersión real de un relé a otro será menor. S1b tiene que dimensionarlo: o un trimmer de más rango, o medir la Coff del HFD27 y fijar su valor nominal, de modo que el trimmer sólo cubra Cb, Ct y la dispersión de producción.
- **ΔCin es sobre todo incertidumbre de diseño.** La Cin del buffer elegido y las parásitas del layout son iguales en todas las placas. Basta medir el prototipo y fijar C_EQ con un C0G (pads con «seleccionar en prueba»), sin trimmer. Además hay que corregir C_SEL_EST para que use la capacidad de los diodos polarizados (duda 1).
- **El MC de E3 (sobreimpulso de hasta 9.8 %) no vale:** usó la sonda incompensable y el paso de 200 ns. Se repite en S1b.

## Dudas de Codex

| # | Duda | Juicio del auditor |
|---|---|---|
| 1 | C_SEL_EST usa CJO a 0 V; los diodos están polarizados en inversa | **Tiene razón.** En S1b, C_SEL_EST usa CJ(−5 V) = CJO/(1 + 5/VJ)^M ≈ 0.77 pF por diodo |
| 2 | Mi chequeo simplificado no lleva todos los elementos del contrato | Correcto; las diferencias quedan explicadas en el punto 3 |
| 3 | C_SEL_EST cuenta una sola COFF_SW y hay dos tiros abiertos | Correcto y menor (0.5 pF). En S1b se cuentan los dos |
| 4 | El plan no fija la Ron de SW1 ni las fugas | Bien resuelto (0.1 Ω y abierto ideal). Las fugas son de S2 (E9) |
| 5 | E3 no fija rango de CCOMP, objetivo ni referencia; no se logra C5 | **Error mío del plan** (punto 4). En S1b, sonda compensable y paso ≤ 5 ns |
| 6 | E2/E4 no detallan barridos ni correlaciones | Bien resuelto; las correlaciones están documentadas |
| 7 | E4 «decide ajustables» y §7 prohíbe recomendarlos | Redacción mía ambigua: Codex mide y el auditor decide, que es lo que hizo |

## Qué sigue

1. **S1b** (encargo corto a Codex):
   - E3 con sonda compensable (C de punta ajustable o CCOMP en un rango con solución) y paso ≤ 5 ns;
   - repetir el MC de E3;
   - C_SEL_EST con CJ polarizada y las dos COFF_SW;
   - añadir el trimmer de Ct y simular el ajuste en cada caso del MC: el residuo de planitud en ÷100 tiene que quedar ≤ ±1 %;
   - informar la ΔCin residual con C_EQ elegida a partir del nominal medido.
2. Decisión de Keneth: un trimmer por canal para la compensación de ÷100, y C_EQ «seleccionado en prueba».
3. Después, S2 (protección), que necesita los modelos de fabricante (BAV199 de Nexperia y amplificadores).
