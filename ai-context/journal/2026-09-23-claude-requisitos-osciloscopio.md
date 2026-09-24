# Requisitos funcionales del osciloscopio

- Fecha: 2026-09-23, noche.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: con los siete artefactos, buscar «el punto intermedio del triángulo» (prestaciones, precio y energía) y establecer los requisitos funcionales del osciloscopio mediante preguntas que crucen la información.
- Los siete artefactos:
  - El esbozo de hardware de la rev 2.0.
  - El documento vivo de la rev 2.1.
  - Las anatomías del DSO112, el WAVE2, el OpenScope MZ y black_scope.
  - La revisión analógica del G473.

## Método

Cuatro rondas de preguntas de opción múltiple. Cada pregunta citaba la evidencia de los artefactos y de la simulación P4/P7 (DSO112, OpenScope y WAVE2 como referencia de banda; D-02 para las velocidades; el G473 para disparo y RAM; la rev 2.0 para batería y RE-01). Cada opción llevaba su consecuencia.

## Respuestas de Keneth

- **Banda:** unos 2 MHz sólo en CH1; CH2 y CH3 a 1 MHz.
- **Sonda ×10:** lineal hasta ±400 V en la punta.
- **Autonomía:** ≥ 4 h.
- **Coste:** «es relativo; la prioridad es buscar componentes con alta disponibilidad y baratos, o clones que tengan las mismas cualidades». Se concretó en la ronda 4: LCSC y JLCPCB, con equivalentes cuya hoja de datos cumpla.
- **Disparo:** flanco en CH1–CH3.
- **Memoria:** 8 k por canal.
- **Funciones a la vez:** las tres (osciloscopio, AWG y DMM).
- **Precisión:** ±1 % con autocalibración.
- **Adquisición:** normal, única, roll, detección de picos y promedio. La alta resolución es para el DMM: ADC5 a 16 bits por sobremuestreo.
- **Base de tiempos:** de 1 µs/div a 50 s/div.
- **Análisis:** todo lo propuesto (medidas automáticas y cursores, FFT, Bode con el AWG, matemáticas y XY).
- **Offset:** ±5 divisiones.
- **Entrada:** 1 MΩ ±2 % y ≤ 2 pF de diferencia entre escalas.
- **Acoplo AC:** ≤ 10 Hz.
- **Energía:** apagado por hardware por canal y por función.

## Cambio

- Nuevo `docs/requisitos_osciloscopio.html` (https://claude.ai/artifact/X1DWGzQBZB2zT57mXPD4sG), generado con `docs/rediseno_afe_gen/build_requisitos.py`. Lleva RF-01…RF-19, sus consecuencias en el diseño, cómo se comprobará cada uno y lo que queda abierto.
- `DECISIONS.md`: nueva entrada con los requisitos acordados y la consecuencia derivada (el grueso es P4).
- `STATE.md` actualizado.
- `docs/rediseno_afe_rev21.html`, versión 8 del artifact: un aviso bajo la entradilla con los requisitos y P4.
- `index.json`: la página de requisitos, el acta de Codex y la auditoría.

## Consecuencias principales

- P7 no cumple RF-07: **el grueso es P4, con un relé por canal.**
- P4 tiene que corregirse para RF-08.
- CH1 necesita su propia cadena y su filtro anti-alias (RF-03, sección D).
- El disparo se hace con el AWD1 de cada ADC más P12, sin hardware nuevo.
- RF-10 ocupa 48 KiB de los 128 KiB de RAM.
- RF-16 a RF-18 obligan a un presupuesto de energía con apagado por bloques (sección G).

## Pendientes

1. Cuestionario de requisitos del DMM y del AWG.
2. Decidir si RE-01 (120 USD) sigue como tope o sólo como referencia.
3. Correcciones de P4 y nueva simulación; orden del filtro anti-alias de CH1; P13.
