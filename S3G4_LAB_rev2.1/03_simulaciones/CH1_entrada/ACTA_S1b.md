# ACTA S1b — entrada pasiva P4b de CH1

Código de salida: 0. Simulaciones: 9375; error: 0; advertencia: 0. Semilla: 20261003. Casos por campaña: 200.

Pool: 10 trabajadores. Tiempo total: 2047.451 s (34.124 min). Casos fallidos: 0.

Verificación de paralelización: smoke de 1 y 10 trabajadores, 14 CSV idénticos byte a byte; 104 simulaciones por variante, sin errores ni advertencias. Tiempos: 96.586 s secuencial y 61.975 s paralelo. Evidencia: `S1b/paralelizacion_verificacion.json` y directorios smoke.

| criterion | RANGO | value | status |
| --- | --- | --- | --- |
| S1b-C1 | nominal | 0.999128…1.000287 MΩ | PASA |
| S1b-C2 | nominal | Cin=26.292419…26.691674 pF; Δ=0.399255 pF | PASA |
| S1b-C3 | nominal | Error máximo 0.324191 % | PASA |
| S1b-C4 | nominal | Planitud 0.239715 %; pico 0.001353 dB; corte 8.802472 Hz | PASA |
| S1b-C5 | nominal | Sobre 0.017252 %; |e2| 0.338975 %; convergencia 0.000000 pp | PASA |
| S1b-C6 | 1 | Máx 0.376486 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C6 | 2 | Máx 0.375144 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C6 | 3 | Máx 0.382238 %; fuera 0/200; topes 0/200 | PASA |
| S1b-C7 | A todos | |ΔCin| máx 1.414737 pF | PASA |
| S1b-C8 | 1 | Sobre máx 0.505098 %; |e2| máx 1.500587 % | PASA |
| S1b-C9 | A todos | Error Zin máx 0.256254 %; planitud ×1 máx 0.293357 % | PASA |

Rango mínimo que cumple C6: R1. Esto no selecciona una pieza comercial.

## Trimmer: recorrido y reparto

| RANGO | cases | stops | outside | trim_min_pF | trim_median_pF | trim_max_pF | worst_flat_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 200 | 0 | 0 | 2.55 | 4.05 | 5.95 | 0.3764856892516599 |
| 2 | 200 | 0 | 0 | 5.0 | 6.550000000000001 | 8.4 | 0.3751443504008911 |
| 3 | 200 | 0 | 0 | 11.0 | 12.600000000000001 | 14.3 | 0.3822379589964231 |

| RANGO | low_pF | high_pF | count |
| --- | --- | --- | --- |
| 1 | 2.0 | 2.5 | 0 |
| 1 | 2.5 | 3.0 | 14 |
| 1 | 3.0 | 3.5 | 29 |
| 1 | 3.5 | 4.0 | 50 |
| 1 | 4.0 | 4.5 | 46 |
| 1 | 4.5 | 5.0 | 38 |
| 1 | 5.0 | 5.5 | 19 |
| 1 | 5.5 | 6.0 | 4 |
| 2 | 3.0 | 3.875 | 0 |
| 2 | 3.875 | 4.75 | 0 |
| 2 | 4.75 | 5.625 | 19 |
| 2 | 5.625 | 6.5 | 75 |
| 2 | 6.5 | 7.375 | 77 |
| 2 | 7.375 | 8.25 | 28 |
| 2 | 8.25 | 9.125 | 1 |
| 2 | 9.125 | 10.0 | 0 |
| 3 | 5.0 | 6.875 | 0 |
| 3 | 6.875 | 8.75 | 0 |
| 3 | 8.75 | 10.625 | 0 |
| 3 | 10.625 | 12.5 | 94 |
| 3 | 12.5 | 14.375 | 106 |
| 3 | 14.375 | 16.25 | 0 |
| 3 | 16.25 | 18.125 | 0 |
| 3 | 18.125 | 20.0 | 0 |

## E3b nominal y convergencia

| POS | step_height_v | overshoot_pct | error_2us_pct | error_20us_pct | error_200us_pct |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.1978931950156 | 0.0 | -0.3389751986404172 | -0.29738057448291877 | -0.07759005911643069 |
| 100 | 0.001980291156476 | 0.017252493699358513 | -0.011190331597211521 | 0.014129891661889878 | 0.004169767396579401 |

| POS | shift_overshoot_pct | shift_objective_pct | shift_error_2us_pct | shift_error_20us_pct | shift_error_200us_pct |
| --- | --- | --- | --- | --- | --- |
| 1 | 0.0 | -4.069897401315359e-07 | 3.56151716063291e-07 | 3.081965529450059e-07 | 3.8050829556657284e-08 |
| 100 | -1.2462813721303423e-07 | -1.2454400919251207e-07 | -3.499486050245748e-08 | -1.997181042334012e-07 | 2.524877949078297e-09 |

## Campaña B

|ΔCin| antes: 0.012508…3.474681 pF; mediana 1.087545. Después de E24: 0.000542…0.962840 pF; mediana 0.263917.

Topes: 29/200. Planitud ÷100 máxima tras ajuste: 2.644086 %; tras E24: 2.648992 %. Sólo informativa.

| CEQ_E24_pF | count |
| --- | --- |
| 7.5 | 4 |
| 8.2 | 14 |
| 9.1 | 28 |
| 10.0 | 41 |
| 11.0 | 41 |
| 12.0 | 46 |
| 13.0 | 24 |
| 15.0 | 2 |

## Qué enseña cada prueba

E1b/E2b miden Zin, Cin, ganancia, planitud y corte AC con la estimación SEL corregida; GND sólo se informa en el CSV. E3b comprueba la sonda compensada y la convergencia real del caso compensado. E4A cuantifica el recorrido y los fallos de producción supuesta sin ocultar topes. E4B separa el ajuste del trimmer de la selección E24 de CEQ.

## Métodos y alcance

Contrato: PLAN_SIMULACION_S1b.md y PLAN_SIMULACION_S1.md; leídos ACTA_S1,
AUDITORIA_CLAUDE_S1, auditoría P4/P7 y revisión de entrada CH1 (§4 y §6).
Modelos: DBAV199 genérico, buffer ideal, rieles ±5 V con 1 Ω. No prueba física,
certificación de seguridad ni amplificador real. Ninguna pieza de diseño cambiada.

AC: 240 puntos/década; E1 10 Hz–10 MHz y E2 1 Hz–20 MHz. Cin a 1 MHz,
Zin a 100 Hz. Planitud nominal C4/C9 10 Hz–2 MHz; ajuste/C6 10 kHz–2 MHz,
normalizados a 1 kHz. Las medidas incluyen 100 kHz, 1 MHz y 2 MHz.
La corriente de Vsense retorna a la fuente: −Im(I/V)/(2πf) da Cin positiva.

Búsqueda del trimmer: red RC nodal de la misma topología, diodos linealizados
a 5 V, bisección de la suma de desviaciones extrema positiva/negativa; rejilla
de 0.05 pF. LTspice verifica el punto candidato, ambos vecinos y ambos topes,
y camina por la rejilla hasta mínimo local. La búsqueda usa POS100/CPLDC real.
Los CSV de búsqueda conservan todas esas .meas; los criterios sólo usan .meas.
La incertidumbre ±0.1 pF se aplica después del ajuste como error uniforme,
compartido para la misma muestra en los tres rangos, limitado al recorrido físico.
Se registran tanto ajuste solicitado como valor efectivo; un tope en cualquiera
cuenta. Los casos contra tope no se descartan. CT2F varía al 2 %, CTRIM no al 2 %.

Sonda: 9 MΩ ∥ CTIP, cable 80 pF, sin CCOMP; fuente ±1 V, 1 kHz, 5 ns y 50 Ω.
CTIP minimiza error máximo de 0.1 a 200 µs después del flanco en POS100.
Se busca primero mediante la solución modal RC de la rampa de 5 ns (contactos
cerrados ideales sólo en ese acelerador, circuito LTspice completo con 0.1 Ω), luego
se verifica y refina en LTspice a 0.002 pF con el candidato y ambos vecinos.
CTIP es idéntico en los dos POS de cada caso y rango. La altura es 2·Vref de
una copia DC con los mismos parámetros, incluyendo los diodos no lineales.
Errores a 2,20,200 µs desde el final del flanco; sobreimpulso entre 0 y 400 µs.
Pasos máximos reales ≤2 ns durante los 5 µs después del final del flanco,
forzados por puntos de quiebre PWL de una fuente numérica aislada del circuito.
Fuera de esa ventana, máximo 100 ns. Se leen los tiempos de cada .raw antes de
eliminarlo y se verifica la ventana; resultados en s1b_ejecucion.json. Se usa
Gear con solver Alternate; no hay timeout del proceso LTspice. Los contactos
cerrados conservan 0.1 Ω, sin alterar ningún componente por razones numéricas.
Se contrasta el nominal de ventana con paso global de 2 ns; convergencia contra
1 ns global en el mismo caso compensado. No se modifica el circuito por ello.
MC usa el primer flanco desde equilibrio negativo (DC de LTspice). Se comprueba
en el nominal frente al segundo flanco a 1.5 ms de una cuadrada periódica.

Mismas 200 muestras A en cada rango; B usa otras 200, semilla fija. Piezas
RT1/RT2, RS1/RS2 y CT1/CT2F independientes; CJO compartido entre ambos diodos;
parásitas de cada clase comunes entre contactos. Capacidades de compensación
calculadas con nominales y luego su propia tolerancia; no se recalculan con
parásitas de cada muestra. La selección CEQ de B mantiene el factor de tolerancia
de la pieza: bisección LTspice de la diferencia firmada Cin1−Cin100 a 1 MHz,
15 iteraciones, 1–30 pF nominales, luego E24 más próximo por distancia absoluta.
Trimmer B ajustado con CEQ inicial; se informa también planitud después de E24.
E1 cubre DC, AC y GND en cada caso A/B; GND sólo se informa. E3 de B se mide
antes y después de seleccionar CEQ, ajustando CTIP en POS100 en cada estado.

Simulaciones independientes en procesos LTspice con rutas únicas, mediante
ThreadPoolExecutor de 10 trabajadores por defecto (configurable con --workers).
Cada instancia lleva .options threads=1 para evitar paralelismo anidado;
es una opción del ejecutor, sin cambiar el circuito. Fuente ADI:
https://ez.analog.com/design-tools-and-calculators/ltspice/f/q-a/592257/option-to-limit-the-maximum-number-of-threads
Casos y rangos A comparten el pool; las búsquedas dentro de cada caso son
secuenciales. B espera la elección del rango C6. Un fallo se registra y los
otros casos continúan; no se presentan campañas incompletas como aprobadas.
CSV ordenados por campaña/rango/caso, nunca por orden de finalización. Los .cir
y .log quedan; .raw, .op.raw y .db regenerables se eliminan después de leer el log.
La tabla CRITERIA del ejecutor concentra todos los umbrales. El código de salida
señala errores de simulación/medida, no criterios eléctricos fallidos.

## Dudas y contradicciones sin resolver

1. Dispersión A de Coff/layout supuesta por el auditor, sin caracterización
   de unidades HFD27 o PCB; el MC no demuestra capacidad de producción real.
2. C_SEL_EST cuenta dos COFF_SW. Una de ellas vuelve a SEL a través de CAC,
   no directamente a masa; el circuito explícito se conserva sin corregir el plan.
3. C9 no fija banda de planitud; se usa la banda completa de E2 (10 Hz–2 MHz).
   También se informa 10 kHz–2 MHz. Zin se comprueba tanto en DC como en AC.
4. El contrato no define objetivo/precisión de CTIP, correlaciones ni la aplicación
   de ±0.1 pF. Las elecciones del banco están descritas, no son decisiones de pieza.
5. «En los 200 casos» es una muestra de Monte Carlo, no todos los extremos
   posibles ni una garantía de fabricación. C6 no elige comercialmente un trimmer.
6. Modelo de diodo genérico y buffer ideal: los modelos de fabricante y las
   protecciones de ±100 V/ESD pertenecen a S2, fuera de este encargo.
7. La selección CEQ de B puede mover ligeramente la planitud tras el ajuste
   del trimmer; se informa ambos estados sin reajustar otra pieza por conveniencia.

No se modifica S1, chequeo_claude, STATE.md ni DECISIONS.md.

## Verificación de la entrega completa

Comprobación independiente del manifiesto y los archivos: 6 006 filas con claves
únicas; A contiene 200 casos en cada rango y B contiene 200 antes y 200 después
de seleccionar CEQ, con DC/AC/GND en ambos POS. Los resultados MC están
ordenados por campaña/rango/caso. Las 9 375 simulaciones tienen .cir y .log
únicos y confirman un hilo interno de LTspice. Se contrastaron los nombres de
131 499 medidas con POS/CPL/RANGO de su instancia real. Las 1 003 ventanas
finas verificadas cumplen el límite; paso máximo observado 1.066639 ns.
Los hashes de 993 archivos protegidos permanecieron iguales.

Evidencia: `S1b/verificacion_campana_completa.json`, ligada por SHA-256 a
`resultados/s1b_ejecucion.json`. Campaña completa: 2 047.451 s (34.124 min),
10 trabajadores, código 0, cero errores, advertencias o casos fallidos.
