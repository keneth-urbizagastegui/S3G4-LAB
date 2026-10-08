# ACTA S11.2 — DMM, bloque 1 O2

Agente: Codex. Fecha: 2026-10-07, America/Lima. Simulación, sin prueba de hardware. Contrato: [PLAN_SIMULACION_S11_2.md](PLAN_SIMULACION_S11_2.md). **Resultado: no aprobado.** R_LIM=700 Ω es un valor diagnóstico, no una solución garantizada. No se añadieron protecciones ni se cambió la topología física propuesta.

## Q0: fuentes y modelo antes de campaña

Fuentes locales, páginas PDF contadas desde 1:

- BSS126 Infineon rev.2.1: p1, 600 V, ±20 V de puerta, 0.5 W a25°C, Tj150°C; los21mA son corriente admisible, **no IDSS máximo**. P2: IDSS mínimo7mA, sin típico ni máximo; VGS(th) −2.7/−2/−1.6V a8µA; Ron320Ω típico/700Ω máximo a3mA y VGS0; RthJA250K/W. P3: capacidades y diodo de cuerpo. P4: SOA y Zth. P5–6: curvas típicas y deriva térmica. El límite contractual de unión es120°C.
- GBU808, Diodes DS21227 rev.8, p2: IFSM200A e I²t166A²s para8.3ms, 800V y VF1V a4A. Contradice175A/127A²s del rediseño: ambas referencias se conservan; aquí los umbrales C8 son100A/83A²s derivados de la hoja local.
- Littelfuse216, p1: ventanas IEC de apertura; p2: 3.15A,250Vac,1500A de corte, Rfría0.0368Ω e I²t de fusión6.7A²s nominales, curva promedio. Se mantiene Rfusible0.04Ω contractual, anotando la diferencia.

No se encontró modelo BSS126 del fabricante en los modelos locales. [Q0_BSS126_MODELO_S11_2.md](comun/Q0_BSS126_MODELO_S11_2.md) documenta el modelo de ingeniería nivel1, ajuste exacto del umbral a8µA, IDSS, Ron, capacidades, diodo y aproximaciones térmicas. 12 comprobaciones LTspice a25°C verifican IDSS7/21mA, I(Vth)=8.00173µA y Ron≈700Ω. **21mA sólo es sensibilidad supuesta: no acota IDSS.** No se ajustan simultáneamente fuga, avalancha, todas las curvas ni autocalentamiento.

La aproximación Shockley exige R≤700.374Ω para mantener1.3mA con IDSS7mA/Vp1.6V; corregir el umbral a8µA da724.880Ω. IDSS sin cota superior exige R≥1125Ω para limitar2.4mA con Vp2.7V. No hay intersección en este modelo ni garantía de hoja para una R válida. Se ensaya **700Ω**, registrado en el diario antes de continuar; no se declara elección de diseño aceptada.

## Ejecución y trazabilidad

El ejecutor [ejecutar_s11_2.py](ejecutar_s11_2.py) usa10 trabajadores, LTspice local `-b`,300s por proceso, `--smoke`, `--resume` y `S3G4_MODELS`. Las firmas incluyen deck, ejecutor, nuevo BSS126 y modelos principales. Cada `.meas` identifica el estado realmente simulado. [S11_2_REPRODUCCION.md](S11_2_REPRODUCCION.md) explica dependencias de S11.1 usadas sólo para lectura y reproducción.

Q3 previo convergió antes de campaña:1 caso,30.732s LTspice,31.425s pared. Q0:12/12,2.721s pared. Smoke inicial:5/6,308.949s, Q7 timeout; smoke corregido final:5/5 de Q3/Q5/Q4/Q1/Q6,41.419s. Q7 conserva la integración directa11s y el límite300s.

La campaña inicial se detuvo para corregir dos defectos de instrumentación: `.save I(*)` no guardaba corrientes jerárquicas; el interruptor ideal de fusible sin histéresis producía reaperturas numéricas. Se guardan explícitamente26 corrientes y se usa histéresis2mA²s con umbral6.7k, sin alterar piezas ni solver. Q3 corregido terminó antes de relanzar. Los intentos preliminares no se mezclan con resultados finales; permanecen en `resultados/s11_2_attempts.jsonl`.

**Campaña final:**498 casos,486 `ok`,12 Q7 `timeout`,5 casos reutilizados de firma actual; tiempo de pared2563.108s (**42min43s**),10 trabajadores. Cobertura: Q3=72, Q5=162, Q4=150, Q1=30, Q6=72, Q7=12. El ejecutor retorna1 por los timeout, sin ocultarlos. Hay559 intentos registrados de todas las fases del ejecutor:546 `ok` y13 `timeout`; incluyen66 intentos previos a la campaña final y493 nuevas ejecuciones de ésta. Los procesos interrumpidos durante la corrección no cuentan como casos concluidos.

La tabla de resultados definitiva es `resultados/s11_2_campaign_audited.csv`; las tablas derivadas son `s11_2_bss126_extremes.csv`, `s11_2_borne_a.csv` y `s11_2_esd.csv`. Los `.cir`, `.log` y `.json` quedan en `S11_2/`. Los raw se procesan y eliminan por defecto; `--keep-raw` permite conservarlos. Auditoría complementaria:53/53 `ok`,156.407s de pared, con decks idénticos; diferencias de pico e I²t del puente exactamente0. Q0 añade12 ejecuciones y2.721s. El conjunto principal de campaña, Q0 y auditoría suma563 casos/ejecuciones de comprobación, con5 casos de campaña reutilizados; incluyendo los66 intentos preliminares del ejecutor son624 ejecuciones registradas (559+12+53), aparte de diagnósticos y procesos interrumpidos. Los tiempos de fases reutilizadas no se suman como ejecución nueva.

## Criterios C1–C8

| Criterio | Resultado | Evidencia y límite |
|---|---|---|
| C1 | Falla; además faltan garantías | BSS126 Pmedia hasta0.262652W y Tj estimada135.659°C frente0.16W y120°C a70°C. ESD supera600V/20V absolutos. Falta hoja BZT52C5V6 y ratings de pulso de resistencias/derivador. |
| C2 | Falla | Q3 inyección+5.831mA y−3.260mA frente carga3mA; Q4+5.884mA. ESD8kV da span11.174V frente11V. |
| C3 | Falla | ESD da pin hasta0.932V más allá del riel y clamp HC hasta432mA frente10mA de margen. |
| C4 | Falla | Red con relé siempre cerrado: potencia/unión excedidas; corriente hasta2.569mA. No se demuestra supervivencia10s. |
| C5 | Sólo información | BAV199 típico3pA/máximo5nA por diodo a75V/25°C; no máximo garantizado a4V ni fuga completa N1/N2 de todas las piezas. |
| C6 | Falla | A100µA:3.374–3.577V disponibles, peor caso126mV bajo3.5V. A1mA:1.271–1.523V. |
| C7 | No certificado | Los12 Q7 agotan300s; no hay recuperación auditada de los11s completos con el modelo final. |
| C8 | Falla por pico | GBU808 hasta423.592A frente100A. I²t hasta10.930A²s, inferior a83A²s en el modelo con apertura. |

## Q3: BSS126 en los extremos

El camino de tensión conserva tres R_PROT33kΩ. Por resistencia: Q3 llega a106.655V/0.170301W y Q4 a108.255V/0.172441W; si se adopta1206 genérico0.25W, rebasa50%=0.125W. No existe MPN/hoja que permita certificar ese supuesto ni los pulsos. R_LIM alcanza1.801V/4.560mW en Q4. En ESD alcanza1592V y0.902mJ en10µs, mientras cada R_PROT alcanza2463V y0.855mJ. La potencia promediada sólo sobre10µs no se compara con potencia continua como si fuese un rating de pulso. Estas piezas tampoco quedan aprobadas por falta de hoja/pulso.

72 casos:0/25/70°C, IDSS7/21mA, Vth−1.6/−2.7V, rieles±2%/nominal, fases0/90°. Relé cerrado todo el tiempo. Se integra1s y extrapolan los últimos5 ciclos a10s, según S11.1 §3b. Dispersión periódica máxima≈0.994%, sin cambio de régimen evidente; extrapolar no modela degradación ni autocalentamiento eléctrico.

Máximos de seis casos por fila. Las potencias y temperaturas máximas de cada FET pueden proceder de casos distintos; no sumar máximos como si fueran simultáneos.

| TA °C | IDSS25 mA | Vth25 V | Ilim mA | P FET1/2 W | Tj FET1/2 °C |
|---:|---:|---:|---:|---:|---:|
|0|7|−1.6|1.306832|0.130677 /0.134156|32.669 /33.538|
|0|7|−2.7|1.934119|0.192839 /0.198073|48.210 /49.517|
|0|21*|−1.6|1.613661|0.161119 /0.165518|40.280 /41.377|
|0|21*|−2.7|2.545326|0.253081 /0.260170|63.270 /65.039|
|25|7|−1.6|1.333607|0.133365 /0.136912|58.341 /59.228|
|25|7|−2.7|1.908183|0.190325 /0.195477|72.581 /73.869|
|25|21*|−1.6|1.673616|0.167097 /0.171657|66.774 /67.912|
|25|21*|−2.7|2.560698|0.254638 /0.261642|88.659 /90.410|
|70|7|−1.6|1.364165|0.136445 /0.140084|104.111 /105.020|
|70|7|−2.7|1.843660|0.183998 /0.188974|115.999 /117.243|
|70|21*|−1.6|1.766321|0.176330 /0.181158|114.083 /115.287|
|70|21*|−2.7|2.568752|0.255513 /0.262652|133.878 /135.659|

*21mA no es máximo de hoja. VDS máximo Q3=322.806V, por debajo de480V de margen; esta comprobación no cubre ESD. En el peor FET2, E1s=0.262500J, extrapolación9s=2.363869J, total10s=2.626370J. Tj=70+250×2.626370/10=135.659°C,15.659°C por encima de120°C. La potencia es1.642 veces0.16W. La corriente excede2.4mA en0.169mA. Incluso IDSS7mA/Vth−2.7V a70°C supera0.16W: la limitación no depende sólo de la sensibilidad21mA.

Comprobación manual del peor caso: Vpk·I/π≈0.265955W por FET frente0.255154/0.262652W simulados. La unión se estima por potencia media y RthJA250K/W de la huella mínima; no verifica el rizado térmico ni realimenta el MOS. La corriente prospectiva que cortaría el relé alcanza2.569mA. El relé no abre en Q3: no confundirla con una prueba de corte230Vac. Su rating de conmutación125Vac sigue siendo una duda.

## Q4: apagado

150 casos, incluidos ambos estados del diodo de cuerpo del interruptor de carga y seis casos adicionales de modo tensión con relé abierto. Cada estado de cuerpo tiene75 casos: span máximo7.937V en body0 y7.771V en body1; ambos llegan a inyección positiva5.884mA y negativa≈3.264mA, superiores a3mA. Corrientes zéner hasta4.766mA/1.928mA; Tj estimada máxima135.652°C. El BAV199 de bloqueo se conserva en la topología. El span por sí solo no demuestra seguridad de los pines apagados.

## Q5: borne A con apertura del fusible

162 casos: red0.5/1/2Ω, k1/2/3, fases0/30/60/90/120/150°, rieles±2%/nominal. El fusible integra su corriente total: abre a6.7k A²s, no a la I²t de un único diodo. Puente con dos VF y Rs0.015Ω por diodo como supuesto de ingeniería ajustado a1V/4A. No hay curva real de corriente de corte ni limitación de pico del arco.

| Red Ω | k | Pico GBU A | I²t por diodo A²s | E derivador J | Pico entrada B V |
|---:|---:|---:|---:|---:|---:|
|0.5|1|423.592|3.6435|0.10182|5.49894|
|0.5|2|423.592|7.2869|0.17262|5.49894|
|0.5|3|423.592|10.9303|0.23737|5.49894|
|1|1|216.340|3.3864|0.12116|5.49832|
|1|2|216.340|6.7723|0.23363|5.49832|
|1|3|216.340|10.1575|0.32590|5.49832|
|2|1|103.484|2.9155|0.18392|5.33473|
|2|2|103.484|5.8209|0.28925|5.33473|
|2|3|103.484|8.7050|0.38002|5.33473|

Todas las redes fallan100A de C8;0.5Ω y1Ω superan incluso200A absoluto de la hoja local. Todas pasan83A²s en este modelo. El máximo423.592A es4.236 veces el margen; si se usaran175A/127A²s del rediseño, tampoco aprobaría.

La aproximación manual de pico da423.730/216.470/103.609A, coherente con LTspice. I²t6.7/I² da aperturas rápidas, algunas menores que1ms y fuera del tramo visible de la curva promedio. El modelo coincide con ventanas IEC a275/400/1000% pero no a150%: allí predice0.300s cuando la hoja exige≥3600s. Se restringe al cortocircuito de Q5. k1–3 es sensibilidad de arco, no tolerancia certificada. El rating250Vac frente230Vac supera el margen80%200Vac de C1, aunque no el absoluto. El criterio literal de50% de I²t también contradice que el fusible deba fundir al100% del umbral; se anota sin reinterpretarlo.

El máximo de energía del derivador es0.380J; falta su MPN/curva de pulso para aprobarlo. Tras R_B=10kΩ la entrada B alcanza5.499V. La carga de pin B mantiene el proxy de clamp de S11.1: no es un macromodelo completo de su amplificador.

La auditoría recupera53 marcas que faltaban por redondeo en q=6.7k; las162 aperturas quedan identificadas por estado eléctrico, sin sustituir los esfuerzos de campaña. Corriente máxima después de apertura más1µs:0.651nA. Intervalos completos sobre fases y rieles:

| Red Ω | k1 apertura µs | k2 apertura µs | k3 apertura µs |
|---:|---:|---:|---:|
|0.5|20.307–769.081|40.615–968.840|60.929–1110.262|
|1|72.374–1176.227|144.856–2232.276|217.555–2698.403|
|2|273.374–2912.545|552.780–3572.838|845.398–4013.857|

## Q6: ESD sin TVS

72 casos, ambas polaridades y modos ohmios/tensión/A. Se usa la descarga contractual simplificada150pF/330Ω, y300Ω adicionales en aire; energías iniciales1.2mJ a4kV y4.8mJ a8kV. Duración10µs y paso máximo1ns. No equivale a una pistola IEC calibrada RLC del banco CH1 S2b. No se añade TVS.

Máximos sobre polaridades, esquinas y rieles:

| ESD | Modo V/Ω | VDS FET V | VGS FET V | Energía FET | Clamp HC A | Exceso pin sobre riel V |
|---|---|---:|---:|---:|---:|---:|
|±4kV contacto|ohmios|1861.487|826.705|0.491mJ|0.27061|0.77061|
|±4kV contacto|tensión, relé abierto|1496.412|53.125|3.60µJ|0.31537|0.81537|
|±8kV aire|ohmios|2897.871|1592.008|1.505mJ|0.37270|0.87270|
|±8kV aire|tensión, relé abierto|2486.765|122.016|11.29µJ|0.43199|0.93199|

En ohmios4kV faltan1381.487V de margen VDS y810.705V de margen VGS frente480V/16V. En8kV faltan2417.871V y1576.008V:6.04 y99.50 veces el límite de margen. También se superan los absolutos600V/20V. El modelo no tiene ruptura destructiva de puerta ni fallo: esos picos son diagnóstico de invalidez, **no formas de onda de una pieza físicamente intacta**. No hay energía de avalancha garantizada para aprobar0.491/1.505mJ.

El clamp HC máximo432mA es43.2 veces10mA de margen. La I²t BAV máxima1.434×10⁻⁶A²s queda bajo8×10⁻⁶A²s de margen, pero eso no salva MOS ni IC. El pico terminal BAV llega4.299A, incluyendo desplazamiento capacitivo; la hoja da4A/1µs, sin garantizar el pulso de nanosegundos ni permitir equiparar corriente terminal a conducción directa. No se aprueba BAV sólo por I²t. En modo A el span queda≤9.996V y no hay esfuerzo significativo del par O2; las magnitudes por polaridad quedan en el CSV ESD. El span global alcanza11.174V en8kV positivo/ohmios.

## Q1 y C5: funcionamiento y fuga

30 casos:24 de cumplimiento y6 de fuga. A100µA,3.374266–3.576939V; incluso nominal da aproximadamente3.472–3.479V, por debajo de3.5V. A1mA,1.270904–1.523384V. La cuenta original del rediseño no representa los dos Ron700Ω, R_LIM700Ω y caída del BAV199 de bloqueo de este modelo. No se cambia ninguna pieza para remediarlo.

BAV199 p3: típico3pA y máximo5nA por diodo a75V/25°C; a150°C, típico3nA/máximo80nA. Dos diodos N2 suman6pA típicos/10nA máximos en esas condiciones; tres incluyendo bloqueo,9pA/15nA. No hay máximo garantizado a4V. Los dos N2 equivaldrían30/6ppm típicos a0.2/1µA y50000/10000ppm máximos a75V, sin trasladar esas cifras como garantía a4V. El barrido de fuga añadida del modelo da11.053–12.062ppm a0.2µA y1.516–1.718ppm a1µA; no es una cota de toda N1/N2.

4051 p9: OFF±100nA por canal/±400nA conjunto y ON±400nA a25°C, sin típico especificado. Retirar canal6 de N2 no elimina las fugas de los canales de medida restantes. BSS126 especifica IGSS a20V e Ioff a600V, no una fuga conjunta típica/máxima a0–4V. C5 permanece informativo, sin aprobar ni suspender el objetivo típico20pA de prototipo.

## Dudas y alcance

**Q7:** los12 procesos finales agotaron300s. La extracción encontró una ventana vacía (`zero-size array to reduction operation maximum which has no identity`); no se conserva ni publica un valor0 ficticio de recuperación. Una lectura independiente de los dos últimos raw mientras aún corrían observó prefijos hasta8.041797s y7.975390s, anteriores a retirar la red en10s. Esto no permite afirmar C7. El raw completo11s del smoke inicial pertenece a la versión previa de instrumentación, dio timeout y no se incorpora a la campaña final. No se cambian ajustes ni se reduce la exposición para obtener una respuesta.

1. No existe IDSS máximo garantizado ni R_LIM que cierre el intervalo con la información/modelo disponibles. Los extremos21mA y deriva térmica son supuestos, no esquinas garantizadas.
2. Falta hoja local BZT52C5V6: el sumidero5.6V/5mA, Rs40Ω/C100pF es supuesto. Faltan MPN y ratings de pulso de resistencias y derivador.
3. GBU808:175A/127A²s del rediseño contradicen200A/166A²s de hoja local. El rating I²t de8.3ms no garantiza todo pulso más corto ni su repetición. El modelo de arco no tiene datos de corte reales.
4. Tj se estima con potencia media, sin realimentación eléctrica, rizado térmico ni validación de huella real. La simulación no prueba10s físicos de supervivencia ni recuperación tras daño/calor.
5. Relé125Vac, fusible250Vac con margen80%, y sacrificio del fusible frente C1 son contradicciones abiertas. No se resuelven cambiando interpretación o piezas.
6. ESD simplificada y MOS fuera de absolutos: O2 sin TVS no queda validado. La entrada B usa proxy de protección, no amplificador completo.
7. Q7 y su plazo de300s limitan la evidencia de recuperación; no se reajusta solver, duración o tolerancias para conseguir un aprobado.

No se descargó nada. S11.1, `01_diseno`, `models`, `STATE.md` y `DECISIONS.md` se mantuvieron fuera de las ediciones; sus hashes agrupados (14 fuentes S11.1,6 archivos de diseño,94 de modelos y ambos archivos de memoria) coinciden con la captura18:44. Diario: [2026-10-07-codex-s11-2.md](../../../ai-context/journal/2026-10-07-codex-s11-2.md). La revisión externa de modelos/cálculos y cualquier prueba física quedan pendientes; no se inventa aprobación.
