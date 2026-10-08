# S12c — confirmación del bloque 2 sin toma ÷10

8 oct 2026. Codex. Contrato: PLAN_SIMULACION_S12c.md; S12b/S12 siguen vigentes salvo sus cambios explícitos. Simulación local LTspice 26, Python/numpy/scipy. Sin hardware ni descargas. Campaña principal: **1215/1215 ejecuciones válidas**. La validez de ejecución no equivale a conformidad del diseño.

## Circuito y fuentes

Se mantienen 6×1.5 MΩ +910 kΩ +100 kΩ =10.01 MΩ, compensación 3×(100 pF +3.3 kΩ), 330 pF y3.0 nF. El nudo entre9 MΩ y910 kΩ queda interno: sin conexión al mux, BAV199,100 Ω ni buffer de X1. Canal X1 del mux a COM; X0 tras su buffer; X2 directo; X3=COM. Ganancia por91 kΩ/10 kΩ con TMUX4053; carga supuesta del bloque5:10 kΩ∥10 pF a1.25 V.

|Rango|Ruta|Ganancia real|Cuenta referida al borne|
|---|---|---:|---:|
|200 mV|X0|10.1|10 µV|
|2 V|X0|1|100 µV|
|20 V|X2|10.1|1 mV|
|50 V|X2|1|10 mV|

÷100 real=100k/10.01M=0.00999000999. El texto ×10 del contrato es la denominación:91k/10k da×10.1; no se cambian valores. Constantes: cada pareja3M×100pF=300 µs;910k×330pF=300.3 µs;100k×3nF=300 µs. Cero fijo de calibración530.516 Hz. La prueba de diodo se conecta a X0 según la decisión; no se recualifica aquí la fuente de ohmios ni su compliancia.

**Un OPA2192 doble puede alojar el buffer X0 y A:** comparten los mismos rieles y requieren dos canales. Los decks emplean dos instancias del modelo monocanal TI común aOPA192/2192/4192. No prueba el acoplo entre canales del encapsulado cuando X0 satura o inyecta corriente. El canal B del bloque4 queda fuera de este encapsulado/asignación de bloque2 y de esta calificación.

Fuentes locales leídas: AGENTS/START/STATE; planes S12c/S12b/S12; ENCARGO_CODEX_S11_1; ESTUDIO_BLOQUE2 completo y sus nueve decks; ACTA y AUDITORIA_CLAUDE deS12/S12b; decisiones DMM7/8oct incluida «sin toma÷10»; HTML bloque1; LEEME de modelos; ejecutores/includes S12b/S12/S11.4 y estudio GDT. Los límites deOPA2192, TMUX yRT1206 se contrastan con las referencias locales documentadas por esas actas/auditorías (SBOS620E pp6/8/9; SCDS445E pp10/11; YageoRTV16). MCPs3g4-context/context-mode no disponible: respaldo local `context.mjs search` y lecturas puntuales, sin pedir repetir contexto.

## Método, contradicciones y límites

- E1:200 placas virtuales por rango, semillas y tolerancias deS12b, TI completo con mux pasivo de hoja enAC. Ajuste de cero fijo y tres puntos100Hz/1kHz/20kHz, ruido relativo0.05%/0.1%, evaluación40Hz…20kHz. No es garantía del95% de fabricación: no se aleatorizan GBW/Ib/Vos/Cin de silicio. Se añaden16transitorios a fondo eficaz en cuatro frecuencias40/100/1000/20000Hz; incluyen50Vrms=70.7107Vpk con los ocho canalesNXP y ambosOPA. RMS/THD se calculan tras cuatro ciclos o≥3.9ms; es comprobación nominal de gran señal, no MonteCarlo transitorio ni barrido continuo de amplitud.
- E2:21plateaus de20ms entre−FS/+FS, muestras de los últimos2ms; calibración23°C y comparación18/28°C. Se heredan1nA por rutaYn y0.85nA enCOM (supuestos), y se cambia la inyección en entradaX0 a0.6nA segúnS12c. Ley térmica supuesta×2/10°C. Presupuesto10000TC independientes uniformes±25ppm/°C, reservaVosSOIC0.5µV/°C por canal,Ib20pA y fugaTMUX0.3nA típica. Se trata0.6nA como inyección externa y se reservaIb aparte, conservador frente a un límite total que ya lo incluya. Fuga máxima deX2 es **agregada** Yn+COM+PCB; no confundirla con fuga de un solo pin.20pA es condición de hoja a25°C, no máximo garantizado18…28°C;Ib5nA en toda temperatura impide certificar fabricación con este presupuesto.
- E3:48transitorios DC, cada rango en0/±FS/±20/±50V, con0/5pC, más8casos a50Vrms en40Hz/20kHz. Rampa inicial20µs y20ms de preacondicionamiento; autocero en21ms, cierre en21.002ms. Paso máximo1µs con breakpoints100ns en la conmutación, heredado deS12b. SWI1 se arranca conUIC (solo transitorio); se evita su puntoDC no convergente. ParaX2 se evalúa1.5ms según la espera por toma heredada; se informa también3ms para20V porque antes ese rango iba porX1 con3ms. **El contrato no aclara si la espera sigue a la toma nueva o al rango antiguo.** Las otras entradas se revisan durante todo el caso, incluido el arranque. La entrada del buffer se califica separadamente de su salida al mux y de la pinza: cumplir corrienteE8 no demuestra modo comúnE3.
- E4/E7 conservan el métodoS12b. OL definido como|Vout|>2.02V es supuesto de interfaz; no certifica el driver/ADC. Ruido integrado con sinc de100ms y√2 para autocero independiente; no incluye ADC, interferencia de red ni deriva bajo0.1Hz.
- E5:solo los cuatro casos de lazo emplean CD(ON)=10pF repartida5pF a cada lado deRon. Fase interpolada enlog|T| ylogf en el cruce unitario. Otros ensayos conservan la capacidad lumped10pF para comparación conS12b. Ron60/400Ω más1Ω del selector ideal;400Ω es el corner dehoja±5V/25°C, no garantía de±4.9V a toda temperatura. No se añadeCf.
- E6/E8:148estados de protección, cadena vigente GDT+14D431K con esquinasGDC420/780V yτ1/100ns; red230/253Vrms yESD±4/±8kV. Se elimina solo la ramaX1 de los decks derivados. El residualRiqother negativo deS12 sigue eliminado; presupuesto reducido4.116mA (incluye fronteras de protección/B, no consumo del bloque2 aislado). No se modificaS11.4. GDT+MOV prevalece sobre elGDTsolo del texto antiguo. El modelo150pF/330Ω aplicado a8kV «aire» no modela arco ni certificaIEC.
- E8 mide directamente la conducción de los diodos de la pinza reducidaX0 (Vf0.5V,Ron1Ω), guardando por separado la corriente total/capacitiva. En±50V conTI completo se separa su propia capacidad:IN+/IN− incluyen100Ω internos antes deESDP/ESDN,6.4pF aMID y1.6pF diferencial. No se aplica laIV dePINOPA al modeloTI (sus pinzas son interruptoresVSWITCH,Ron50Ω,Voff0.1/Von0.7V). La inferencia inicial con0.5V/1Ω produjo103.6mA imposibles frente a432µA de corriente total yqueda descartada. Se conserva como diagnóstico yse corrige el criterio mediante la separación delmodelo; comprobación con corrientes internas aparte. El pin inversor delseguidor queda unido a la salida. Criterio≤5mA,50% del absoluto±10mA, no aplicado al desplazamiento capacitivo. Ninguna de esasIV es medida de silicio ni modelo de daño.
- E6 informa tensiones, duración por encima de200V enRT1206 y energías resistivas por pieza; energía almacenada½CV² en capacitores. ≥1.5kV/≥25µJ/ΔR≤1% es especificación de compra/ensayo de las3.3kΩ, **no rating demostrado de unMPN**. Un resistor ideal no simulaΔR. La sobrecarga400V/5s no se usa para aprobar ni suspenderESD.
- ElHTML de bloque1 conserva divisor3×3M/900k, etiqueta630V y toma÷10; lo sustituyen las decisiones y contratos7/8oct. El centinela de diodo porX1 del estudio también queda superado: S12cmandaX0. No se editan documentos protegidos.

## Piezas finales del bloque2

|Cantidad|Pieza / valor|Referencia y condición|
|---|---|---|
|6|YageoRT1206BRD071M5L,1.5MΩ|C728673;0.1%,25ppm/°C;200V trabajo,0.25W; curva de impulso pendiente|
|1|YageoRT1206BRD07910KL,910kΩ|C870935; misma familia/tolerancia/TC|
|1|YageoRT1206BRD07100KL,100kΩ|C728669; misma familia/tolerancia/TC|
|3|CCTCTCC1206COG101J202FT,100pF,2kV|C7393967; ficha definitiva pendiente|
|3|3.3kΩ antipulso|MPN pendiente;≥1.5kV,≥25µJ,ΔR≤1% tras ensayo|
|1+1|C0G330pF/3.0nF|MPN/rating pendientes|
|1|Nexperia74HCT4051|C87239;X1/X3 aCOM,X0buffer,X2directo|
|1 doble|TIOPA2192|C110074; bufferX0+A,±4.9V|
|1 sección|TITMUX4053|C5377936; otras secciones del bloque4 fuera de alcance|
|1+1|91kΩ/10kΩ|0.1%,25ppm/°C;MPN pendientes;×10.1|

Frontera conservada:3×33kΩ deR_PROT,BAV199 y100Ω enX0, cadenaGDT+MOV. La sujeción,100Ω ybuffer deX1 se eliminan **solo enS12c**, como ordenado. No se sustituyen piezas ni se eligen remedios.

## Resultados

|Ensayo|Casos principales|Resultado|Conclusión|
|---|---:|---|---|
|E1|816|P95 conjunto del residuo:0.15067% con ruido0.05%;0.25053% con0.1%. Gran señal nominal:residuo máximo0.03288% en50Vrms;X2máx0.70635V.|Cumple≤0.5% dentro del modelo/muestreo descrito.|
|E2|12|Presupuesto offset:3.162/0.305/8.044/0.793cuentas en200mV/2V/20V/50V. SPICE:2.265/0.227/7.496/0.750. Deriva de gananciaP95máx234.6ppm a±5°C respecto de23°C.|20V no cumple≤4cuentas con fuga agregada1.85nA;los otros rangos cumplen el presupuesto.|
|E3|56|EntradaX0delbuffermáx5.5244V. Caso20V/X2/borne0/0pC refinado:1.8131cuentas a1.5ms,0.1081a3ms.|No cumple modo común±4.9V ni asiento≤1cuenta a1.5ms;otros excesos pequeños pendientes de convergencia.|
|E4|8|0puntos válidos engañosos;recuperaciónOPA2192máx15.52µs.|Cumple recuperación≤1ms y criterioOL supuesto.|
|E5|8|PMmín43.598°;ganancia×1 típica49.011°;×10.1/Ron400:64.148°. Conmutaciónmáx4.441µs.|Cumple≥40° y≤1ms.|
|E6|148|Red253Vrms:cada1.5Mmáx53.616V<160V. ESD8kV:RTmáx556.54V/40.77nJ;3.3kmáx1112.32V/2.321µJ.|Régimen cumple;calificación de impulso pendiente deMPN/curvas/ΔR real.|
|E7|2|Ruido con autocero:0.03595cuentas en200mV y0.02710en20V.|Cumple<1cuenta rms/100ms en el modelo.|
|E8|150|Conducciónmáx:±50V0.43227mA;4kV2.95156mA;8kV2.99773mA;red2.63934mA.|Cumple≤5mA en todos los estados modelados.|

### E3: comprobación numérica y espera

La malla principal1µs daba cinco excesos de una cuenta ycuatro excesos de riel delmux de0.6…3.1mV. No se presentan estos últimos como excesos físicos confirmados:la convergencia a100ns no terminó para ellos dentro de900s. Tampoco se les atribuye aprobación. Se conservan los decks/resultados principales ylos intentos finos separados.

Dos casos20V/X2×10.1/borne0 sí terminaron a100ns:

|Carga inyectada|Error a1.5ms,1µs|Error a1.5ms,100ns|Error a3ms,100ns|Asiento≤1cuenta|
|---|---:|---:|---:|---:|
|0pC|−1.84565|**−1.81309**|−0.10814|1.694ms|
|5pC|−2.37266|**−0.69256**|−0.10037|1.375ms|

El caso0pC confirma que **1.5ms no basta**;3ms sí cumple en ambos casos refinados. La diferencia del caso5pC impide trasladar todos los excesos principales a la realidad sin refinamiento. No se cambia la espera delfirmware ni se declara nueva decisión. El otro fallo independiente deE3 es la entrada no seleccionada delbufferX0 a5.524V, aunque su salida almux está sujeta cerca delriel. Los±50V TI deE8 verifican conducción real de los interruptores internos:0.432264mA;la separación capacitiva difiere≤5.66nA, validando ese método de auditoría.

### Fuga máxima tolerable

Presupuesto térmico/calibración deE2 (límite4cuentas, mismas reservas y ley térmica):

|Rango|Ruta|Fuga máxima nA|Alcance|
|---|---|---:|---|
|200mV|X0|0.8040|Inyección externa,Ib reservado aparte;decisión contractual≤0.6nA.|
|2V|X0|9.6014|Misma convención.|
|20V|X2|0.8656|AgregadoYn+COM+PCB;no por pin.|
|50V|X2|9.6567|AgregadoYn+COM+PCB.|

Por tanto, para compartirX2 entre20V/50V manda **≤0.866nA agregado**, condicionado a estos supuestos. No es límite garantizado de catálogo ni medición. El supuesto heredado1+0.85=1.85nA excede ese presupuesto en20V. Mantener0.6nA enX0 ofrece margen nominal hasta0.804nA en200mV.

### Impulsos por pieza y dudas materiales

`resultados/s12c_impulsos.csv` contiene1628filas (148estados×11resistores), con pico,energía yduraciones por encima de trabajo/400V/1000V por pieza. En cada1.5M, el peor8kV supera200V durante2.093ns;cada3.3k supera400V2.046ns y1000V0.254ns. Para4kV:RT420.24V/37.20nJ y3.3k839.99V/1.988µJ. Los valores≥1.5kV/≥25µJ cubren numéricamente el pulso calculado en3.3k, pero **no acreditan ningún MPN niΔR≤1%**.

Picos de capacitores en8kV:100pF157.17V (energía almacenada1.235µJ);330pF47.681V (0.375µJ);3nF5.197V (0.0405µJ). La retirada de la pinza intermedia eleva el estrés del330pF:su rating pendiente debe cubrirlo. No extrapolar aESD una prueba de sobrecarga400V/5s.

Pendientes:calificar fuga real18…28°C;resolver el alcance literal del modo común delbuffer no seleccionado y el acoplo delOPA2192doble;confirmar espera de20V por rango/toma;seleccionar y verificar losMPN ya pendientes;curvas de impulso deRT1206 y ensayoΔR. No se proponen ni aplican cambios de piezas. La campaña no validaIEC,PCB ni hardware.

Auxiliares:CD(COM) incremental del modeloNXP=0.8855…0.9000pF al barrer−2…+2V;no representa todas las capacidades de la hoja. C2,±20pF enX2, cambia el droop a20kHz de−1.552% a−2.823% (nominal−2.191%);enX0,±10pF apenas cambia−1.0203%. El modeloTI de un canal enreposo da≈1mA por riel:estimación deldoble≈2mA/19.6mW a±4.9V, sin carga/mux/protección. El presupuesto reducido4.116mA conserva las fronteras deS11.4 yB;**no es una medida del consumo completo del bloque2**. Consumo real pendiente dehardware. `s12c_capacitores.csv` añade740filas de picos y½CV² por capacitor/estado.

E4 comparativo:OPA2188 recupera12.85µs/19.25µs en×1/×10.1. Sus dos casos de recuperación requirieron condiciones iniciales coherentes para el punto de operación (.ic de salida,inversora ybuffer, liberadas durante el transitorio;sinUIC), solver normal/trap yreltol0.003. Dos intentos previos no convergieron yse conservan en el historial;OPA2188 no sustituye elOPA2192 final.

## Ejecución y reproducción

`ejecutar_s12c.py` carga la metodología deS12b/S12 en memoria, redirige todos los artefactos aS12c y sustituye exclusivamente el circuito/criterios del contrato.10trabajadores,900s/caso, grupos completos en ordenE3→E8→E2→E1→E6→E5→E4→E7; auxiliaresC2/C3/Q0 después. `--resume` exige firma de código,deck,includes ymodelos,estadook ydeckguardado idéntico. Nombres cortos porhash paraMAX_PATH; cada `.meas` conserva el estado real completo, incluyendo la ausenciaRx1,borne,modo,relé,riel,GDT,τ ytiempo de apertura. `status=ok` significa ejecución válida, no conformidad.

```powershell
Set-Location -LiteralPath 'C:\Users\Keneth\Desktop\S3G4 LAB'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12c.py' --smoke --workers 10
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s12c.py' --resume --workers 10
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/verificar_s12c.py'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/verificar_s12c_extra.py'
python 'S3G4_LAB_rev2.1/03_simulaciones/DMM/analizar_s12c.py'
```

VariablesS3G4_MODELS/S3G4_LTSPICE heredadas; rutas locales entrecomilladas. Sin descargas. STATE/DECISIONS yfuentes anteriores quedan protegidos. ManifiestoSHA256 inicial de167fuentes enresultados/s12c_protegidos_inicio.json. Diario propio:ai-context/journal/2026-10-08-codex-s12c.md.

### Registro final de ejecución

- Smoke definitivo:15/15 válidos en91.8916s;se reutilizan esos15en la campaña.
- Campaña:1215estados,1215válidos finales;10trabajadores,900s/caso. Distribución:E3=56,E8=150,E2=12,E1=816,E6=148,E5=8,E4=8,E7=2,C2=6,C3=7,Q0=2. Inicio12:44:37−05:00;ejecución inicial1490.3851s con1213válidos. Reparaciones/reanálisis:189.4263s,127.1958s y39.4896s;las dos primeras no resolvieron el arranque deOPA2188,la última sí. Total de fases de campaña1846.4968s (**30min46.5s**),sin sumar smoke/preparación.
- Comprobaciones adicionales:13estados distintos;4válidos (2E3+2E8),9límites900s enE3. Primer grupo10:900.3921s;segundo grupo3:900.2154s;se solaparon,ventana aproximada13:17:20…13:41:57−05:00. **No equivalen a13resultados válidos.** Códigos de salida1 de los verificadores señalan esos límites,separados del1215/1215principal.
- Total final:1228estados intentados,1219válidos y9inconclusos;1234lanzamientos desde el smoke definitivo,contando6reintentos de recuperación deE4. Los intentos preliminares de preparación figuran en el diario yno se mezclan con esta contabilidad.
- Integridad:167fuentes protegidas idénticas;1215firmas/decks exactos comprobados,y1215casos con nombres.meas coincidentes con estado real. Evidencia:`s12c_integridad_final.json`. El análisis combina solo refinamientos válidos;conserva resumen grueso,comparaciones e intentos fallidos en`s12c_resumen.json`.

Cierre documental08oct2026≈13:42−05:00. **S12c ejecutado y documentado;diseño no declarado conforme ni aprobado para fabricación.** No se cambiaSTATE/DECISIONS por prohibición expresa del encargo.
