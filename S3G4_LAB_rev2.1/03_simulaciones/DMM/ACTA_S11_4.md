# Acta S11.4 — DMM, bloque 1: confirmación final

7 de octubre de 2026 · Codex · PLAN_SIMULACION_S11_4.md y entorno ENCARGO_CODEX_S11_1.md.

**El bloque no queda aprobado.** Los 223 estados completan, pero D1/D2 carecen de ratings de pulso verificables y D6 no se acredita en seis estados apagados. Los demás criterios cumplen en este modelo, con las limitaciones indicadas.

## Alcance y reproducción

Confirmación de los cambios ya elegidos, sin cambiar piezas ni topología por los resultados. No se repite S11.3 completo ni el borne A. No hay ensayo físico, conexión de placas ni certificación de supervivencia.

Desde DMM: `python -B "ejecutar_s11_4.py" --smoke --keep-raw`, después `python -B "ejecutar_s11_4.py" --resume`, y `python -B "analizar_s11_4.py"`. Diez trabajadores; 900 s por caso; `S3G4_MODELS` y `S3G4_LTSPICE` siguen admitidos. Rutas Windows pasadas como argumentos independientes a LTspice, sin shell. Cada `.meas` lleva borne, modo, relé, Rs, RX, alimentación/body, riel, corriente, toma, fase, cebado DC/impulso, estímulo, amplitud, duración y retirada reales.

Archivos: `comun/dmm_bloque1_final.inc`, `ejecutar_s11_4.py`, `analizar_s11_4.py`, `S11_4/` (decks/logs/JSON), `resultados/s11_4_*.csv` y `resultados/s11_4_findings.json`. `s11_4_campaign_audited.csv` sólo admite firmas vigentes. CSV de criterios, diodo, ESD y esfuerzos por pieza conservan estados y magnitudes.

Cobertura: T2=144 (dos signos, contacto4kV/aire8kV, dos modos, tres rieles, encendido/apagado/body y dos cebados DC); T1=16 (dos corrientes, dos rieles, barrido y DUT a0.65/3.0/3.2V); T3=18 (dos fases y nueve estados de riel/alimentación); T4=36 (fuente off, peor caso de R3, ±60VDC y60Vrms con fases0/90°, nueve estados); T5=9 (exactamente los estados tensión R7 que agotaron tiempo). Prioridad T2,T1,T3,T4,T5.

## Método del GDT y límites

SMD4532-600NF: DC600V±30% (420/780V), impulso1000V a100V/µs,0.5pF según contrato/ficha citada. No hay hoja local: datos tratados como supuestos de catálogo. El cebado dependiente de pendiente interpola linealmente DC→1000V hasta100V/µs y conserva1000V por encima; **esa extrapolación a los frentes ESD no está garantizada**. Los dos extremos DC comparten1000V de impulso: no se inventa tolerancia de impulso.

Arco:20V+I·1Ω; corriente de mantenimiento10mA; constante de cebado/extinción1ns. Estos tres parámetros son supuestos, no datos de hoja. Estado integrado con memoria: una vez cebado continúa hacia arco, se extingue por debajo del mantenimiento y puede volver a cebar si reaparece la tensión. No simula destrucción, calor, retraso estadístico ni limitaciones de PCB. Corriente `Bgdt` es arco; `Cgdt` aporta desplazamiento separado.

ESD hereda el generador RC de S11.3:150pF,330Ω contacto y630Ω aire, cierre a100ns;50µs, paso máximo1ns. Es una aproximación, **no el generador RLC calibrado de S2b ni una pistola IEC certificada**. Se mantiene el solver y tolerancias heredados. Se informa pico bruto de inyección y mínimo móvil20ns; D4 se evalúa con el bruto.

T3/T4:1s integrado y9s extrapolados a régimen con últimos cinco ciclos, según §3b heredado; CSV separa energía simulada/extrapolada/total10s. No se declara integración directa10s. T5 integra10s de fallo y2s después de retirarlo; umbral heredado100µV respecto a media de los últimos100ms, proxy de un count de2V/20000, no garantía del rango200mV.

BAT54: modelo exacto de `standard.dio`, biblioteca local UTF-16; etiqueta `mfg=Vishay`, mientras selección de catálogo es Nexperia C85084. No es un modelo verificado del MPN seleccionado. Vhead0.5V y fuente P43 son aproximaciones heredadas. DUT de silicio/LED representado por su tensión fija0.65/3.0/3.2V; corriente real a esa tensión, no una curva I/V de LED concreto.

## Simulaciones y tiempo

| Prueba | Estados | Válidos | Timeout |
|---|---:|---:|---:|
| T2 |144|144|0|
| T1 |16|16|0|
| T3 |18|18|0|
| T4 |36|36|0|
| T5 |9|9|0|
| Total |**223**|**223**|**0**|

Smoke definitivo:9/9,**287.202 s** (4min47.202s). Confirmación con `--resume`:223/223,**853.807 s** (14min13.807s),214 llamadas nuevas y9 estados reutilizados porfirma. Smoke+confirmación:**1141.009 s** (19min1.009s); tiempos de pared, excluyen lectura/programación/redacción. Dos preflights adicionales:4.458 y4.512 s. Historial:233 invocaciones completadas `ok` (223 definitivas+10 preliminares),más1 invocación interrumpida del smoke invalidado;234 lanzamientos totales. El smoke preliminar interrumpido no tiene resumen de pared completo y no se inventa su duración total.

Los ocho T5 nuevos tardaron391.598–526.794 s de LTspice porcaso; el T5 reutilizado tardó271.674 s enel smoke. Ninguno agotó900 s. `ok` significa integración/extracción completa, **no cumplimiento de todos los criterios**.

## D1–D7

| Criterio | Resultado | Valor / límite |
|---|---|---|
| D1, margen de cada pieza |**No certificado; supera tensión de trabajo en ESD**|Rohm543.070 V frente a200 V (80 % de250 V); Rprot366.030 V frente a160 V (80 % de200 V). Sin rating de pulso no se demuestra daño ni supervivencia. Potencia continua conocida: Rprot0.172168/0.25 W; Rohm0.505017/1 W; TVS0.258113/0.5 W. Faltan ratings de las demás piezas.|
| D2, relé y1206 en ESD |**Parcial / no certificado**|Relé abierto38.594 V≤1200 V (80 % de1500 V surge,p6);1206 hasta366.852 V, sobrecarga de MPN no disponible.|
| D3, GDT no ceba con red |**Cumple en modelo**|325.269119 V≤336 V; arco0 A;18/18 estados sin cebado.|
| D4, inyecciónX0/X1 contacto |**Cumple en modelo**|1.177005 mA máximo bruto≤10 mA (50 % de20 mA).|
| D5, diodo100µA/riel−2 % |**Cumple para la fuente en modelo**|3.606262 V≥3.5 V con fuente≥99 %; corriente DUT a3.5 V=98.084527 µA.|
| D6, recuperación |**No acreditado en la ventana**|X0≤27.943987 ms; N2 alimentado≤0.129069 ms. Seis N2 apagados siguen derivando hasta2 s: resultado censurado, no recuperación medida. Límite1 s.|
| D7, separación de rieles |**Cumple en modelo**|T2:9.996 V;T3:10.181227 V;T4:10.569051 V;máximo≤11 V.|

D1, D2 y D6 impiden aprobar el bloque completo con estas fuentes. Para D1/D2 faltan especificaciones de pulso/energía y sobrecarga verificables para cada MPN, y la respuesta real del GDT; no se cambiaron piezas. D6 conserva seis resultados censurados por deriva. D3 tiene sólo 10.731 V de margen al criterio: amplitud real de red, tolerancia del cebado y modelo importan. D5 depende de Vhead, VF/BSS84, riel y resistencia total; la fuga mueve la corriente DUT. D7 depende de capacitancia efectiva de riel y característica real de los zéner. D4 depende del frente, cebado y reparto de sujeciones, sin certificar latch-up.

## Diodo

| Ajuste / DUT | Riel −2 % | Riel nominal |
|---|---:|---:|
| 100 µA, tensión disponible con fuente ≥99 % |3.606262 V|3.704264 V|
| 1 mA, tensión disponible con fuente ≥99 % |No existe región|No existe región|
| Silicio 0.65 V, ajuste 100 µA, corriente DUT |99.572808 µA|99.572808 µA|
| LED 3.0 V, ajuste 100 µA, corriente DUT |98.359510 µA|98.359510 µA|
| LED 3.2 V, ajuste 100 µA, corriente DUT |98.256250 µA|98.256250 µA|
| Silicio 0.65 V, ajuste 1 mA, corriente DUT |0.695744 mA|0.715544 mA|
| LED 3.0 V, ajuste 1 mA, corriente DUT |0.222435 mA|0.241945 mA|
| LED 3.2 V, ajuste 1 mA, corriente DUT |0.182668 mA|0.202091 mA|

D5 tiene 106.262 mV de margen en el peor riel según la compliance de la **fuente**. A DUT=3.5 V llegan 98.084527–98.084573 µA con ajuste 100 µA. Exigir ≥99 % en el **DUT** daría sólo 1.731337–1.731464 V por la fuga TVS pesimista del modelo; no se oculta esa distinción ni se presume una fuga típica real. A 1 mA no se mantiene 0.99 mA: la resistencia total fija de 4.9 kΩ, Vhead, BAT54 y MOS consumen la tensión disponible. El contrato pide informar, no aprobar 1 mA a 3.5 V.

## ESD con mínimo y máximo del GDT

Cada fila recoge 18 estados por extremo del GDT (ambos signos, tres rieles y tres estados de alimentación/body); total 144. Ventana completa 50 µs.

| ESD / modo | V/Ω pico con GDC=420 V | V/Ω pico con GDC=780 V | Relé abierto máx. | Rprot individual máx. | Rohm individual máx. |
|---|---:|---:|---:|---:|---:|
| ±4 kV contacto / tensión |1067.171 V|1067.171 V|38.594 V|355.668 V|518.697 V|
| ±4 kV contacto / ohmios |1059.624 V|1059.624 V|Cerrado|351.694 V|522.377 V|
| ±8 kV aire / tensión |1064.252 V|1064.252 V|38.036 V|354.671 V|517.782 V|
| ±8 kV aire / ohmios |1101.016 V|1101.016 V|Cerrado|366.030 V|543.070 V|

Los extremos de **DC** casi coinciden porque el frente supera 100 V/µs y el modelo usa el mismo cebado por impulso de 1000 V. Esto no demuestra que la dispersión de un GDT físico en ESD sea nula. Todos los 144 casos ceban y se extinguen; máximo corriente de arco 23.643711 A y energía de arco 32.625713 µJ (contacto: ≤21.528123 A y16.536385 µJ). El estado llega al arco de ~20 V más su resistencia asumida; no permanece en conducción parcial.

Picos brutos de sujeción HC por contacto: X0≤0.283207 mA, X1≤1.177005 mA; ambos frente a10 mA. Por aire: X0≤0.303578 mA, X1≤1.324275 mA. No se necesita descartar picos para cumplir D4. Entre rieles en T2≤9.996 V. Rdiv superior≤366.852 V; Rc superior≤366.034 V. Cc1≤7.649045 V; los tres capacitores y sus estados se conservan en CSV de esfuerzos, sin usar el rating anterior630 V.

Aunque el relé esté abierto, Coff=1 pF transmite el frente a la rama de ohmios; por eso Rohm también recibe pico en modo tensión. No se confunde el esfuerzo de la resistencia con la tensión entre contactos. La baja tensión entre contactos durante este pulso depende de esa capacitancia y de la respuesta de 1 ns supuesta del GDT. Tampoco aprueba aislamiento contacto–bobina/PCB ni bornes.

Con la tensión de trabajo como referencia, el margen80 % sería160 V para Rprot y200 V para Rohm: los picos ESD los superan. Sin curvas/tensiones de pulso del MPN no se declara rotura, pero tampoco supervivencia ni D1/D2 completos. La referencia genérica400 V de sobrecarga1206 de la auditoría **no es una ficha de FOJAN, Rdiv o Rc**; 366.852 V sería inferior a400 V si se confirmase ese rating para cada una, y superior a320 V si además se exigiese80 %. No se adopta ese supuesto para aprobar.

## Red, 60V y recuperación

**T3, red en tensión.** GDT a 325.269119 V máximo, 77.445 % de420 V y margen10.730881 V respecto a336 V. Arco0 A y estado0 en los18 casos: no ceba durante el segundo integrado; se extrapola el mismo régimen a10 s. Su capacitancia0.5 pF sí conduce desplazamiento: pico sinusoidal calculado61.3118 nA, no un arco. Rprot≤108.170868 V y0.172168 W por pieza, frente a160 V y0.25 W. Entre rieles≤10.181227 V.

**T4, 60 V en ohmios con fuente apagada (peor R3).** Cada Rohm≤35.071482 V y0.505017 W media; frente a200 V y1 W (80 %/50 % de los ratings de trabajo citados). TVS≤0.258113 W media, frente a0.5 W (50 % de1 W de la hoja). Rs≤0.027962 W media, pero su MPN/rating sigue pendiente. Zéner≤0.014485 W media; hoja y tolerancias pendientes. Entre rieles≤10.569051 V. Son esfuerzos eléctricos del modelo, sin modelo térmico ni destructivo.

Ejemplo de separación de energías **en el mismo estado** peor de potencia: T3 Rprot1, apagado+body,riel−2 %,fase0:0.172151589 J integrado+1.549512014 J extrapolado=1.721663604 J a10 s. T4 Rohm1, mismo estado:0.505013970 J integrado+4.545149167 J extrapolado=5.050163136 J a10 s. La energía10s no se compara con un rating desconocido de pulso; la potencia periódica sí se compara con el rating continuo citado.

La comprobación independiente por V²/R en el raw del smoke ESD coincide con la energía Rprot1:1.138715213 nJ en50 µs. Máxima diferencia absoluta raw–`.meas` en T2–T4:3.39782 µJ en Rohm; se conserva la diferencia, no se fuerza igualdad ni se altera el solver.

**T5, recuperación.** Los nueve estados completan directamente 12 s (10 s de red, 2 s sin red), sin extrapolación. X0 recupera en 37.065–38.828 µs alimentado y 27.547–27.944 ms apagado. N2 alimentado: 119.053–129.069 µs y deriva final ≤0.792 pV. **Seis N2 apagados no tienen referencia estacionaria:** al final quedan en −45.367…−45.361 mV, con 1.407302–1.407976 mV de variación en los últimos 100 ms, frente al umbral 100 µV. El extractor heredado da 2.0 s porque la última muestra aún supera el umbral respecto a la media final; ese número es el extremo de observación, **no un tiempo de recuperación**. Se declara censura y D6 no acreditado, sin extrapolar sobre un régimen que sigue moviéndose.

El modelo reducido advierte expresamente que no es un modelo de recuperación/transferencia/fallo. El resultado identifica deriva de N2 con alimentación apagada y BAT54 nuevo; no demuestra destrucción ni atribuye por sí solo un mecanismo físico real. Lo que movería D6 es la referencia de reposo real apagado, la fuga/capacitancia efectivas del BAT54, el comportamiento del interruptor/rieles apagados y el modelo de recuperación completo. Queda pendiente medir o ampliar la observación. No se ensayan remedios ni se cambian piezas.

## Lista final del bloque 1 ensayado

| Elemento | Cantidad / valor / referencia |
|---|---|
| Bornes |2×Amass24.245.1 rojo C7437326 (V/Ω,A);1×24.245.2 negro C7437327 COM; dato1kV de decisiones, no modelados|
| GDT V/Ω–COM |1×hongjiacheng SMD4532-600NF C47345384,1812|
| Relé ohmios |1×TQ2SA-5V-Z C46047;un NO usado;Ron0.1Ω,Coff1pF|
| Rohm |2×1.1kΩ Milliohm HoCR2512,2512,2W,C5123622;250V trabajo de ficha citada|
| TVS N1–COM |1×SMAJ12CA C78399|
| Rs |1×2.7kΩ;MPN/rating pendientes|
| Fuente |BSS84 y1×BAT54 Nexperia C85084 de bloqueo|
| Sujeciones |4×BAV199 dobles:8uniones usadas enX0,X1,N2,X5;bloqueo ya es BAT54|
| Sumideros |2×BZT52C5V6;modelo aproximado, hoja local ausente|
| Rprot |3×33kΩ FOJAN FPS1206J333,1206,0.5W,C55348469;200V trabajo de ficha citada|
| Divisor |3×3MΩ1206+900kΩ+100kΩ;MPN de3MΩ con pulso pendiente para bloque2|
| Compensación superior |3×3.3kΩ en serie con3×100pF C0G2kV CCTC TCC1206COG101J202FT,1206,C7393967|
| Compensación inferior |330pF sobre900kΩ y3nF sobre100kΩ;MPN/ratings pendientes|
| Mux |74HC4051;RX0=RX1=100Ω;sin RX2;canal6 retirado deN2|
| Buffer/fuente |OPA2188 seguidor yTLV2372/P43 reducido;ganancia detallada fuera del bloque|
| Borne A heredado |Littelfuse0216,3.15A250Vac (C95689),GBU808 (C42406072),shunt0.1Ω2512 referencia2W,RB10kΩ,Rwarn10MΩ;no reensayado enS11.4|
| Rieles |±4.9V yvariantes±2%;2×1µF;load switch sinMPN,body cases0/1|

Es la lista del circuito evaluado, no una BOM con todos los ratings aprobados. La elección concreta de las resistencias del divisor se mantiene pendiente; no se cambió para aprobar.

## Fuentes, contradicciones y dudas

Leídos contrato S11.4 y toda su cadena de planes S11.1–S11.3, ENCARGO, actas/auditorías exigidas, REDISENO_BLOQUE1, decisiones7oct, dmm_rev21, método/actaS2b, AGENTS/START/STATE y LEEME de modelos. Fuentes locales heredadas: relé C46047p6 (1500V surge10×160µs entre contactos abiertos); HC4051p5 (20mA clamp),pp9–10(fuga/capacidad); SMAJpp2–3 (1W continuo,400W10/1000); BAV199pp2–3; BSS84p2; OPA2188pp4–6; GBU808p2; fusiblepp1–2.

1. No hay hojas locales para FOJAN/Milliohm/CCTC/GDT. No se convierte el dato genérico400V de sobrecarga1206 de la auditoría en rating garantizado de estos MPN. Tampoco se deriva una energía ESD admisible multiplicando potencia continua por50µs.
2. DC420/780V son tolerancias de cebado estático; el dato1000V a100V/µs no proporciona extremos ni retraso a pendientes ESD mucho mayores. El resultado del GDT es condicional al modelo; retardo, inductancia de conexión y dispersión reales pueden mover decisivamente los picos. Falta prueba en prototipo.
3. P23/dmm_rev21 descartaban GDT; decisión A+B del7oct y contrato actual lo añaden. Se sigue el contrato actual, sin editar diseño. La antigua decisión sujeción N2–COM discrepa del contrato heredado aambos rieles; se conservan ambos rieles.
4. ELVIS cita60VDC/20Vrms; contrato exige60Vrms. Se ejecuta60Vrms. No se declara supervivencia a230Vrms enohmios.
5. BAT54 de biblioteca Vishay≠MPN seleccionado Nexperia. Compliance de fuente≥99%≠corriente que alcanzaDUT: fugaTVS pesimista lineal desde5µA@12V y divisor consumen parte. Fuga real y exactitud se verifican enprototipo/bloques siguientes.
6. BZT yrieles reducidos no demuestran tolerancias físicas, latch-up ni destrucción. Ratings de capacitores inferiores, resistencias del divisor/Rc/Rs/RX yshunt faltan. Herencia GBU/fusible ybornes no son nueva validación enesta campaña.
7. El extractor heredado devuelve 0.5 para `.meas ...gdt_on: V(gstate)=.5 AT t`; es el valor del estado, no el tiempo. El CSV auditado lo renombra `gdt_on_state`; el tiempo de cebado es `gdt_ignition_s`, extraído del raw. Las corrientes de los LED se nombran por su DUT real, sin conservar etiquetas heredadas «a 0.65 V» que no les corresponden.
8. Primer preflight ysmoke preliminar contenían unGDT que conducía parcialmente sin llegaralarco. Se corrigió la ecuación de memoria; resultados preliminares se excluyen porfirma. La ramaT5 deese smoke se interrumpió alhaberse invalidado elmodelo. No se cambió solver paraforzarconvergencia.

No se escribió en S11.1–S11.3, 01_diseno, models, STATE ni DECISIONS. La ejecución usa `-B` para no escribir bytecode de dependencias. El MCP s3g4-context no estaba expuesto; búsqueda/sincronización mediante CLI local, sin descargas. Diario propio: `ai-context/journal/2026-10-07-codex-s11-4.md`. No se capturaron hashes iniciales de todos los archivos protegidos: no se presenta una certificación byte a byte de cambios concurrentes. El estado Git de archivos previamente rastreados permanece limpio.
