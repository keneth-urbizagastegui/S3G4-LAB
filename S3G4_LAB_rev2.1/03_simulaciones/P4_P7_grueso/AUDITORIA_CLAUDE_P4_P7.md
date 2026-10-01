# Auditoría de Claude — simulación P4 (con relé) frente a P7 (sin relé)

- Fecha: 2026-09-23, noche.
- Auditor: Claude Code (Opus 5.5).
- Objeto: trabajo de Codex (gpt-5.6-sol, esfuerzo medium, tarea `task-muenuphs-puqefo`, 1 h 5 min). Entregó `ACTA_RESULTADOS_P4_P7.md`, `ejecutar_todo.py`, `comun/rev21_comun.inc`, 14 `.asc` y `resultados/`.
- Contrato: `PLAN_SIMULACION.md` §9. Los diagnósticos propios están en `auditoria/` (netlists `.cir` e includes).

## Veredicto

1. **Trabajo reproducible:** mi ejecución de `ejecutar_todo.py` da el mismo `resultados.csv` fila por fila (2345 filas, 0 distintas). Código 0, 14 simulaciones, 0 errores y 0 advertencias, en 4 min 45 s.
2. **Entregables completos salvo dos puntos:**
   - T07 es parcial, como el propio acta reconoce.
   - Los `.asc` son netlists escritas como texto: se abren en LTspice, pero no hay esquema dibujado (§7.2 pedía que «se vean bien»).
3. **Dos familias de fallos salen de mi plan, no de los diseños:**
   - La compensación nominal de P4 ÷100.
   - La compensación nominal de P7 fina.

   Con la contabilidad de parásitas corregida, las dos respuestas quedan planas (diagnósticos A y B).
4. **El resto de fallos son propiedades reales de los diseños:**
   - En P4: impedancia y capacidad de entrada, error de ganancia en ×1 y excursión de la entrada del buffer.
   - En P7: rodilla, distorsión con sonda ×10, fuga del 74HC4053 y excursión de la entrada del buffer.

## Lista de §9

| # | Comprobación | Resultado |
|---|---|---|
| 1 | Valores de los `.asc` frente a §2–§4; derivados con `.param` | Coinciden. `CBN_P4`, `CBF_P7`, `CBG_P7` y `CPROBE` son `.param`. Hay dos desviaciones: `CBN_P4` resta `COFF_RELE` (ver C4/C5 P4), y `CPROBE` aproxima Cin con `(CBNC + CtF + CtG)/9` = 23 pF/9 en vez del Cin de T01 (18.6 pF). Esto último no afecta a 1 kHz |
| 2 | Reejecución de `ejecutar_todo.py` | Idéntica; ver veredicto |
| 3 | Sumas y productos de comentarios y actas | Correctos: 3 × 665 kΩ = 1.995 MΩ (+0.251 %); 19.38 mW / 2 = 9.69 mW; 44.02 V / 2 = 22.01 V; energía = P · 10 s |
| 4 | Estado en el nombre de cada medida y coincidencia con el circuito | Correcto: `p4_x1_*` con `POS=1`, `p4_d100_*` con `POS=100`, `p7_fina_*` con `POS=2`, `p7_gruesa_*` con `POS=200`. Tomas y ganancias de T02 según §3 |
| 5 | Resultados frente a mis cálculos | T04: entre +2.2 % y +15.3 % sobre mis referencias. T05 P7: 825.8 kΩ a 20 V y 738.6 kΩ a 40 V, frente a mis 820 y 735 kΩ. T06: nodo grueso de P7 a 1.77 V, frente a ~1.8 V |
| 6 | Ficheros fuera de la carpeta | Sólo su diario (`ai-context/journal/2026-09-23-codex-simulacion-p4-p7.md`). `STATE.md` y `DECISIONS.md` intactos |

## Causa de cada criterio fallido

| Criterio | Diseño | Medido | Causa | Origen |
|---|---|---|---|---|
| C1 | P4 | 0.909 MΩ en ×1 | (Rt + Rb) ∥ (R_S + R_BIAS) = 1 MΩ ∥ 10.1 MΩ | Diseño: topología |
| C2 | P4 | 21.8 / 13.9 pF | La rama ×1 añade la capacidad del nodo SEL sólo cuando está elegida | Diseño: topología |
| C3 | P4 | −1.19 % | R_S/(R_S + R_BIAS) = −0.99 %, más la toma 1/40 de la escalera (24.9/997.7 = −0.17 %) | Diseño; se corrige calibrando |
| C4, C5 | P4 ÷100 | +9.4 % de planitud; pico de 0.794 dB | `CBN_P4` resta `COFF_RELE`. El contacto abierto une SEL con X1, que por C_S (1 nF) es la BNC en alta frecuencia: es capacidad **de arriba** y había que sumarla a Ct | **Plan (mío)**: «más lo que acople el contacto abierto» era ambiguo. Corregido en el diagnóstico A: planitud 0.015 %, Cb = 1076 pF |
| C4, C5 | P7 fina | −14.9 % de planitud; −1.43 dB a 1.5 MHz | §4 define `CPAR_FINO` como «clamps, TVS y pista», y además los modelos de diodo llevan su CJO: la capacidad de los clamps se cuenta dos veces | **Plan (mío)**. Diagnóstico B, con CJO ≈ 0: planitud 0.017 %. Queda CbF = 2 pF, un margen frágil |
| C4 | P7 gruesa | +0.48 dB a 1.5 MHz; pico de +3.2 dB a 8.4 MHz | La capacidad del 4053 apagado (5 pF) mete en la salida la rama fina, que lleva una señal 100 veces mayor. Con COFF ≈ 0, el frente queda plano hasta 5 MHz (variantes v1/v2/v3) | Diseño P7 |
| C5 (métrica) | ambos | 15.8 % y 22.3 % | Codex mide contra el nivel asentado de una cuadrada simétrica, que es la mitad del escalón: da el doble que el error referido al escalón (7.9 % y 11 %) | Plan ambiguo. Falla igual |
| C7 | P7 | 738.6 kΩ; THD 0.015 % | Rodilla de la rama fina protegida. Con sonda ×10 da **4.4 % de THD** a 200–400 V en la punta | Diseño P7 |
| C8, C9 | ambos | entrada de 5.86–6.09 V | El BAV199 del plan cae ≈ 1.08 V a 3.5 mA, y `UniversalOpamp2` no tiene diodos de entrada. En la placa, los diodos internos del amplificador se llevarían la corriente | Diseño: falta una resistencia serie entre el nodo sujetado y el buffer |

## Juicio sobre los 10 s de red (§5 T06 lo deja al auditor)

- **P4 ÷100 (reposo):**
  - Cada 330 kΩ de Rt ve 116.7 V de pico y disipa 20.6 mW: bien.
  - El contacto abierto del relé ve ~350 V de pico: el relé tiene que aguantar ≥ 500 Vrms entre contactos, como ya pide la lista de la sección A.
- **P4 ×1 (error del usuario):**
  - **P2-base** (100 kΩ 0805): 598 mW, 4.8 veces su potencia, y 347 V con un límite de 150 V. No sobrevive: **descartar**.
  - **P2-AT** (2 × 49.9 kΩ 1206): 299 mW cada una (1.2 veces) y 174 V (límite 200 V) durante 10 s, 2.99 J. Es verosímil dentro de la sobrecarga de corta duración habitual en película gruesa, pero **hay que confirmarlo con la hoja de la pieza elegida**. **Adoptar P2-AT.**
  - El clamp conduce 3.5 mA: bien, siempre que el riel tenga una carga mayor que la corriente que se le inyecta.
- **P7:** bien en todas las posiciones. RtF y RtG ven ~116 V y disipan 10–20 mW; el clamp conduce 0.34 mA; el nodo grueso llega a 1.77 V.

## Consecuencia de los requisitos acordados hoy

Keneth fijó que con sonda ×10 se deben medir sin deformar **±400 V en la punta** (RF-07 en `S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html`). P7 no lo cumple: 4.4 % de THD, y la entrada efectiva cae a 739 kΩ. **P4 es el único diseño que cumple RF-07.** P7 queda archivado; sus hallazgos (fuga del 4053, CbF frágil) quedan aquí como referencia.

## Qué falta, sólo para P4

1. Corregir en el plan la contabilidad de parásitas: `COFF_RELE` arriba, y clamps en CPAR o en CJO, no en los dos.
2. RF-08 (1 MΩ ±2 % y ≤ 2 pF entre escalas):
   - Poner R_BIAS delante del relé (en X1) para que la impedancia no cambie con la posición.
   - Elegir Rt + Rb para que el paralelo dé 1 MΩ.
   - Igualar la capacidad con el segundo polo del relé.
   - Volver a simular T01–T03.
3. Resistencia serie entre el nodo sujetado y el buffer; volver a simular T06.
4. Completar T07 en P4: tolerancias y parásitas en todos los elementos, y T03 transitorio. Decide el ajustable.
5. Los `.raw` ocupan ~1.8 GB y se regeneran; se pueden borrar.
