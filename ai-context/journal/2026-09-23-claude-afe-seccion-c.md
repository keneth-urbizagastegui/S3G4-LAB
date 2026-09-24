# D-06 acordado y sección C del AFE rev 2.1

- Fecha: 2026-09-23, madrugada, hora local.
- Agente: Claude Code (Opus 5.5).
- Pedido: registrar D-06 tras la aceptación de Keneth («si, registralo y vamos con la seccion C») y desarrollar la sección C, sensibilidad y ancho de banda.

## Cambio

- `docs/rediseno_afe_rev21.html`, republicado como versión 5 del artifact https://claude.ai/artifact/YLrJwmm5Cz6w864dUYsrBT. Copia previa en el scratchpad de la sesión (`rediseno_afe_rev21.bak.html`).
  - Tabla de decisiones: D-03 y D-05 revisadas (un relé por canal para el grueso; divisor ÷20 permanente más rama ×1 conmutada), **D-06 acordada**, D-07 con el orden nuevo de la cadena (sigue como propuesta), D-08 añadida (arquitectura DSO112, cerrada) y **D-09 añadida como propuesta** (la escalera atenúa y la ganancia es fija).
  - Sección C nueva, de C.1 a C.7, con dos esquemas.
  - La TVS y los BAV199 se trasladan de `NET_TAP` a `NET_SEL`, detrás del relé. Son las mismas piezas; el dibujo B.7 queda superado en ese punto.
  - El BOM pasa a numerarse «Σ» y las pendientes «…».
- `ai-context/DECISIONS.md`: sustituido el apartado «Abierto, sin acuerdo» por «D-06 acordado», con el texto de la decisión y a qué reemplaza.
- `ai-context/STATE.md`: actualizado el frente de rediseño.
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists de la rev 2.0.

## Contenido técnico de la sección C (propuesta, pendiente de validar por Keneth)

- Supuesto a confirmar en la sección F: 8 divisiones = 2.0 V en el ADC (0.25 V/div).
- 10 escalas 1-2-5, de 5 mV/div a 5 V/div. Ganancia = grueso (×1 o ÷20) · toma (1/1…1/50) · fija (×50). ×1 hasta 200 mV/div; ÷20 desde 500 mV/div.
- Ocho tomas exactas, 1, 1/2, 1/4, 1/5, 1/10, 1/20, 1/40 y 1/50, con un 74HCT4051 por canal. Cadena de 1 kΩ con valores E96 de 499, 249, 49.9, 100, 49.9, 24.9, 4.99 y 20.0 Ω; error de relación ≤ 0.23 %.
- Rama ×1: R_S 10 kΩ 1206 en paralelo con C_S 10 nF C0G 100 V. τ = 100 µs, del orden de R_BIAS·C_in; relación 0.999 en continua y 0.9988 en alta frecuencia; no necesita ajuste. Con 50 V continuos: 4.4 mA hacia los clamps y 0.2 W en R_S. Con 250 Vrms en ×1 se quema R_S; es el riesgo aceptado en D-06.
- Basta un relé SPDT. Poner a masa la rama no usada dejaría R_S de la BNC a masa y bajaría Zin a 10 kΩ. La capacidad del contacto abierto queda en paralelo con C1A–C1C y la absorbe el ajuste de C2.
- Ganancia fija ×5.02 (4.02 k / 1.00 k) y ×10.09 (9.09 k / 1.00 k), ×50.65 en total; el resto va a calibración.
- Presupuesto de ancho de banda a 1.5 MHz con GBW de 100 MHz: ≈ −0.2 dB. Con 50 MHz, ≈ −0.6 dB. Slew rate pedido ≥ 30 V/µs.
- Ruido referido a la entrada con amplificadores de ~7 nV/√Hz: ~0.3 % de división en las 10 escalas, frente al 17 % que daba la escala de 5 mV/div con el divisor ÷20 fijo.

## Corrección propia

Al recomendar D-06 escribí «relé latching, en reposo = ÷20». Un latching no tiene posición de reposo. Corregido en C.2 del documento, con las dos opciones: latching con disciplina de firmware, o monoestable con ÷20 en el contacto de reposo (~100–140 mW por canal mientras se usan las escalas finas).

## Evidencia y pruebas

Cálculo y dibujo solamente. Los dos esquemas nuevos pasan el comprobador geométrico (`chk_c.py`, derivado de `docs/esbozo_hardware_gen/check.py`) con 0 solapes de texto y 0 textos sobre cables. No hubo revisión visual en navegador. No se consultaron precios ni hojas de datos de amplificadores ni relés: los candidatos (LM6172, OPA2810, AD8066) están **por comparar**, no verificados.

## Cambio posterior: D-05 pasa a ±40 V

Tras comparar con las referencias (DSO150 y DSO112 muestran hasta 50 V; DSO138 mini y OpenScope MZ se quedan en ±20 V), Keneth aceptó subir el fondo de escala a ±40 V. También revisamos un texto que pegó defendiendo ±20 V: la relación 16:1 y las 512 cuentas por división no distinguen entre ±20 y ±40 V, y su propia lista de señales (24 V, USB-PD 20 V) apuntaba a ±40 V.

- 11 escalas, de 5 mV/div a 10 V/div. Frontera ×1/÷20 entre 100 y 200 mV/div.
- Tomas 1, 1/2, 1/4, 1/5, 1/10, 1/20, 1/50, 1/100; sale la de 1/40. Siguen siendo 8, con el mismo 74HCT4051.
- Cadena E96: 499, 249, 49.9, 100, 49.9, **30.1, 10.0, 10.0 Ω**. Error de relación ≤ 0.41 % (peor toma, 1/20); lo corrige la calibración.
- Con ±40 V el nodo protegido llega a ±2 V. La sección B no cambia.
- Ruido: 0.2–0.5 % de división; la peor escala es 200 mV/div, la primera que pasa por el divisor.
- Documento republicado como versión 6. La sección C se regeneró sobre la copia previa (`rediseno_afe_rev21.bak.html`) y los dibujos vuelven a dar 0 solapes.

## Pendientes

1. Relé latching o monoestable, y modelo concreto con ≥ 500 Vrms entre contactos abiertos.
2. Elegir buffer (amplificador FET o J309 discreto) y amplificador doble; buscar precios en JLCPCB.
3. Sección G: los clamps pueden inyectar hasta 13 mA en los rieles de ±5 V con 50 V en ×1 en los tres canales, y los 9 amplificadores suman ≈ 270 mW.
4. U102 con VCC − VEE = 10 V, en el límite del 74HCT4051: confirmar en su hoja de datos.
5. Protección de 600 V del puerto DMM (D-06), con Micro-DMM como referencia.
6. Secciones D, E, F y G. Siguen abiertos los pendientes del diario del 22 sep (sección A y hallazgos de netlist de la rev 2.0).
