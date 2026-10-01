# Simulación P4 frente a P7 — construcción y ejecución

- Fecha: 2026-09-23
- Agente: Codex
- Alcance: `Simulation_LTSpice_rev21/P4_P7_grueso/`

## Cambio

Se construyeron los 14 esquemas T01–T07 de P4 con relé y P7 sin relé, el include común, el ejecutor/evaluador, los resultados CSV/Markdown y el acta. Se usaron `UniversalOpamp2`, parámetros derivados para las compensaciones y modelos de diodo indicados en `PLAN_SIMULACION.md`. No se eligió ni recomendó diseño.

## Evidencia

- `Simulation_LTSpice_rev21/P4_P7_grueso/ACTA_RESULTADOS_P4_P7.md`
- `Simulation_LTSpice_rev21/P4_P7_grueso/resultados/resultados.csv`
- `Simulation_LTSpice_rev21/P4_P7_grueso/resultados/resumen.md`
- Logs de LTspice junto a cada uno de los 14 `.asc`.

## Pruebas

`python ejecutar_todo.py` terminó con código 0: 14 simulaciones, 0 errores y 0 advertencias. Los criterios resultaron:

- P4: pasan C6 y C7; fallan C1–C5, C8 y C9.
- P7: pasan C1, C2, C3 y C6; fallan C4, C5 y C7–C9.
- T04 no tiene discrepancias mayores del 30 % frente a las seis referencias manuales.

## Pendientes y límites

- T07 quedó parcial: ejecuta 200 corridas AC, pero no aplica todas las tolerancias/parásitas y usa un proxy AC para el error a 2 µs en lugar de repetir T03 transitorio. No sirve todavía para decidir ajustables ni atribuir un peor caso único.
- Auditar los fallos eléctricos documentados en el acta, especialmente la impedancia P4 ×1, el realce de las respuestas y la excursión de entradas por encima de ±5.5 V.
- `STATE.md` y `DECISIONS.md` no se tocaron por instrucción expresa del encargo; corresponde al auditor actualizar el estado compartido.
