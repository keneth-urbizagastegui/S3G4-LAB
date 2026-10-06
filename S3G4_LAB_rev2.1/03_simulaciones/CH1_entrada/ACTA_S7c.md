# Acta S7c — rango del trimmer con la opción A (tolerancias estrechas)

- Ejecutó y redactó: Claude Code, 4 oct 2026, a petición de Keneth (opción A de `AUDITORIA_CLAUDE_S7b.md`).
- **Método:** Monte Carlo analítico de 20 000 placas con la **misma fórmula** que usó Codex en S7b (`realization()` de `ejecutar_s7b.py`, línea 129: igualdad de constantes de tiempo del ÷100 de S2b). No hace falta LTspice: el trimmer se calcula, no se simula. Script `S7c/s7c_trimmer.py`; resultados en `S7c/s7c_resultados.json`, `s7c_centrado.json` y `s7c_final.json`.
- Varían igual que en S7b: R ±1 %, divisor ±0.1 %, R_BIAS ±1 %, rieles ±2 %, pistas ±50 %, C_off del relé y capacidades de los conmutadores ±5 %.
- **Esta vez ejecutó Claude**, que también es el auditor. Conviene que Codex o Keneth revisen el script, que es corto.

## 1. Validación frente a S7b

Con las tolerancias de S7b (Ct y Cb al ±5 %), el script da que el trimmer basta en el **81.2 %** de las placas, frente al **83.2 %** de Codex con 500 placas. La diferencia está dentro de la dispersión estadística de 500 placas (±1.7 %). Los percentiles necesarios también coinciden: 1.47 / 4.03 / 6.96 pF frente a 1.52 / 4.06 / 7.11 pF.

## 2. Resultados

| Escenario | Trimmer necesario p2.5 / p50 / p97.5 | Placas dentro de 2–6 pF |
|---|---|---|
| S7b (Ct ±5 %, Cb ±5 %) | 1.47 / 4.03 / 6.96 pF | 81.2 % |
| Ct ±2 %, Cb = 1 nF ±1 % + 68 pF ±2 % (Ct2 fijo de 16 pF) | 2.47 / 3.19 / 3.95 pF | 100 % (descentrado) |
| Ct ±1 %, Cb ±1 % | 2.65 / 3.19 / 3.75 pF | 100 % |
| **Elegido: Ct1 20 pF ±2 %, Ct2 fijo 15 pF ±2 %, Cb = 1 nF ±1 % + 68 pF ±5 %** | **3.47 / 4.19 / 4.95 pF** | **100 %** |
| Alternativa: Ct2 16 pF y Cb = 1 nF + 91 pF ±5 % | 3.32 / 4.10 / 4.91 pF | 100 % |

- La dispersión baja de ±2.7 pF a **±0.74 pF**, y la mediana queda en el centro del rango del trimmer (4.0 pF).
- **El hueco DNP no hace falta** con estas tolerancias: no lo usó ninguna placa. Se recomienda dejar uno en paralelo con Ct2 como seguro frente a una desviación **sistemática** de las capacidades de pista en el primer prototipo, que este Monte Carlo trata como aleatoria.
- **Por qué Ct2 = 15 pF:** no hay 16 pF ±2 % a ≥ 200 V en LCSC. Con 15 pF hace falta 1 pF más de trimmer, y el 68 pF de Cb lo compensa.

## 3. Piezas (LCSC, 4 oct 2026)

| Posición | Pieza | LCSC | Nota |
|---|---|---|---|
| Ct1 (C1A) | 20 pF ±2 % C0G 250 V, 0603, Murata GQM1875C2E200GB12D | C3845779 (2 573 ud) | Ve ≤ 50 V con 100 V en la entrada: ≤ 20 % |
| Ct2 fijo (C1B) | 15 pF ±2 % C0G 250 V, 0805, Murata GQM2195C2E150GB12D | C3836120 (355 ud) | Stock justo para prototipo; la versión 0603 C464956 tiene 120 ud |
| Cb (C2) | 1 nF ±1 % C0G 50 V, 0603, FH 0603CG102F500NT | C507408 (42 101 ud) | Ve ≈ 0.5 V |
| Cb (C2') | 68 pF ±5 % C0G 0603 | por elegir (genérico) | Su tolerancia pesa poco: ±5 % de 68 pF es el 0.3 % de Cb |
| Trimmer | SEHWA STC3MA06-T1, 2–6 pF, 100 V | C22468120 | Sin cambios |
| DNP | 0603 en paralelo con Ct2 | — | Sin montar; seguro para el primer prototipo |

## 4. Criterio

S7b-C5 (trimmer suficiente en ≥ 95 % de las placas): **pasa con el 100 %**. El resto de criterios de S7b no cambia: C_t y C_b sólo afectan a la compensación del ÷100, que el trimmer deja ajustada.
