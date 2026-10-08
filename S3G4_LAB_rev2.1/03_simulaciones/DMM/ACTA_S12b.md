# S12b — confirmación del frontal de tensión con buffers

8 oct 2026. Codex. Contrato `PLAN_SIMULACION_S12b.md`, con S12 vigente salvo sus cambios explícitos. LTspice26.0.2, Python3.12/numpy/scipy. Simulación local, sin hardware ni descargas. Campaña cerrada:1191/1191 ejecuciones válidas; esto no significa conformidad de los ocho ensayos. Auditoría independiente pendiente.

## Circuito y fuentes

Se conservan 6×1.5MΩ+910kΩ+100kΩ (10.01MΩ), compensación3×100pF/3.3kΩ,330pF/3nF,74HCT4051,OPA2192 A y91kΩ/10kΩ con TMUX4053. Se añade un OPA2192 dual como dos seguidores: X0 tras100Ω→buffer0→Y0; X1 tras100Ω→buffer1→Y1; X2 directo aY2. Alimentación±4.9V. Las3.3kΩ son antipulso; no se inventa MPN/rating.

Relaciones calculadas: X1/Vin=1.01/10.01=0.1008991; X2/Vin=0.1/10.01=0.00999001. τ de cada pareja alta=3MΩ×100pF=300µs;910kΩ×330pF=300.3µs;100kΩ×3nF=300µs. Cero fijo de compensación530.516Hz. No se retocan valores.

Fuentes leídas: planes S12/S12b, ESTUDIO_BLOQUE2 completo y sus nueve decks, ACTA_S12, AUDITORIA_CLAUDE_S12, decisiones DMM7/8oct incluida «buffer antes del mux», `01_diseno/dmm_bloque1.html`, ENCARGO_CODEX_S11_1, modelos/LEEME, ejecutores/includes S12 y S11.4 y estudio GDT local. OPA2192 SBOS620E p6: entradas±10mA absolutos, por lo que E8 exige≤5mA; tensión absoluta V−−0.5…V++0.5V y rango recomendado de modo común V−−0.1…V++0.1V (p8). El HBM de la pieza no certifica IEC en el borne. Hojas de resistencias/TMUX y límites de ruido/deriva: fuentes locales ya citadas por S12; no se descargan fichas.

## Método y límites

- E3:48transitorios (cuatro rangos,0/±FS/±20/±50V según duplicados eliminados,0/5pC). Rampa inicial0→Vin en20µs y20ms (>60τ) antes del autocero a21ms. Se comprueban los canales durante todo el transitorio; error absoluto respecto al valor nominal en los casos dentro de rango, después de0.1/3/1.5ms. Los casos fuera de rango solo califican los rieles. Paso máximo1µs, con breakpoints100ns entre20.9 y21.1ms por una fuente de tiempo desconectada del circuito físico. No es una nueva pieza. Se contrasta con nueve referencias100ns, conservadas en JSON; el smoke sensible coincide a37nV en el pico. Los resultados de1µs sin breakpoints se descartaron por cambiar el veredicto de rieles.
- E8/E6: cadena vigente GDT+14D431K en serie, esquinas DC420/780V yτ1/100ns, mismos estados de protección S11.4. ±4kV se etiqueta contacto y±8kV aire, pero ambos usan150pF/330Ω del modelo heredado: **no modela arco de aire ni certifica la forma de onda IEC**. Red230/253Vrms. E8 añade rampas0→±50V en20µs mantenidas3ms, con TI completo. Se sustituye el barrido DC extremo que no encontraba punto de operación, sin alterar piezas ni amplitudes.
- Exposición reducida de buffers en protección: pinza de entrada±0.5V respecto a rieles con Ron1Ω, Cin6.4pF y C diferencial1.6pF; IV supuesto, no se limita artificialmente la corriente. Transferencia con TI y alimentación aislada, para evitar doble contabilidad de rieles. Se miden entrada no inversora y entrada inversora. No es modelo de daño, dispersión ni alimentación parasitaria completa del silicio.
- Contradicción corregida solo en S12b: la rama Riqother heredada daba resistencia negativa al actualizar OPA a2mA, porque2mA+1.1mA+16µA exceden el total antiguo3mA. Se elimina el residual no físico; presupuesto reducido de ICs con buffers5.116mA a9.8V. No se escribe ningún archivo S12/S11.
- E2: calibración a23°C y comprobación18/28°C. Para evitar el punto de operación extremo se usan21plateaus de−FS a+FS, cada uno20ms (>60τ), con rampas20µs; se ajustan pendiente/cero sobre la media de los últimos2ms de cada plateau. Paso máximo5µs, integración gear; no se mezclan transiciones con las muestras de continua. Interpretación explícita del texto:1nA en cada Yn de las tres rutas,0.85nA agregada adicional en COM y0.85nA en cada entrada de buffer, todos a23°C, multiplicados por2^((T−23)/10). No son garantías de hoja ni fugas máximas de ocho canales. Presupuesto separado10000TC independientes uniformes±25ppm/°C; reserva de0.5µV/°C SOIC **para buffer y A**,Ib20pA yTMUX0.3nA típ., Rout buffer1Ω supuesto. Ib20pA es condición de tabla a25°C;5nA en toda temperatura impide certificar fabricación con este presupuesto.
- E1:200placas virtuales/rango con los mismos pasivos y semillas de S12; tolerancias y dispersión de parásitas de aquel método. TI no aleatoriza GBW/Ib/Vos/Cin. Mux pasivo de hoja en AC/ruido; SWI1 transitorio. Ajuste de cero fijo y tres puntos100Hz/1kHz/20kHz con ruido relativo0.05%/0.1%. p95 es de la población supuesta, no evidencia de95% de fabricación. No se ensaya AC de50Vrms (70.7Vpk), fuera de la comprobación E3 de±50V.
- E4/E5/E7 y C2/C3 conservan métodos S12. Carga de bloque5 **supuesta**10kΩ∥10pF a1.25V; OL en A como|Vout|>2.02V; TMUX paramétrico60/400Ω más1Ω ideal y10pF; integración rectangular100ms para ruido, cuadrando densidad y con√2 para autocero independiente. C2 conserva la perturbación en COM del mux, no es barrido geométrico del pad antes del buffer. C3 no sustituye los25pF de hoja.
- E6 informa pico y energía disipada por cada resistencia, y duración por encima de200V de trabajo para RT1206, con interpolación lineal de la señal y cruces de±rating. En3.3kΩ falta rating: duración de trabajo queda vacía y se dan umbrales200/400/1000V informativos. Energía de capacitores es máxima almacenada½CV², no daño/disipación. No se aprueba ni suspende ESD por400V/5s.

## Piezas finales del bloque2

| Cantidad | Pieza / valor | Referencia y condición |
|---|---|---|
|6|Yageo RT1206BRD071M5L,1.5MΩ|C728673,0.1%,25ppm/°C;200V trabajo,0.25W; rating ESD pendiente|
|1|Yageo RT1206BRD07910KL,910kΩ|C870935; misma familia|
|1|Yageo RT1206BRD07100KL,100kΩ|C728669; misma familia|
|3|C0G100pF,2kV|C7393967; ficha local definitiva pendiente|
|3|3.3kΩ antipulso|MPN, tensión de trabajo y curva de impulso pendientes|
|1+1|C0G330pF/3.0nF|MPN/rating pendientes|
|1|Nexperia74HCT4051|C87239; SWI1 para transitorio, equivalente de hoja para AC/ruido|
|1 dual nuevo|TIOPA2192, buffers X0/X1|C110074; ambos canales seguidores|
|1 canal adicional|TIOPA2192 A|C110074; comparte encapsulado con B del bloque4, fuera de alcance|
|1 sección|TITMUX4053|C5377936; otras secciones del bloque4 fuera de alcance|
|1+1|91kΩ/10kΩ|0.1%,25ppm/°C; MPN pendientes; ganancia10.1|

Frontera del bloque1: R_PROT3×33kΩ, BAV199 y100Ω enX0/X1, GDT+14D431K. Se preserva su topología y no se recualifica el bloque1 completo.

## Resultados y cierre

|Ensayo|Resultado principal|Dictamen bajo el método indicado|
|---|---|---|
|E1|p95 conjunto residual:0.180711% con ruido0.05%;0.248881% con ruido0.1%|Cumple población virtual; fabricación no garantizada|
|E2|Presupuesto peor4.188685cuentas frente a4; SPICE3.291474|No cumple el presupuesto conservador a0.85nA|
|E3|Canales no seleccionados≤4.896546V; peor error1.656123cuentas tras espera|Rieles cumplen; asentamiento absoluto falla en4/28 casos dentro de rango|
|E4|Recuperación OPA2192≤15.5184µs; cero puntos engañosos|Cumple el modelo|
|E5|Margen mínimo38.4594° con×1/Ron400Ω; conRon60Ω47.4035°|Falla mínimo40°; conmutación≤4.41288µs cumple|
|E6|RT1206≤556.098V;3.3kΩ≤1111.430V en8kV|Calificación de impulso pendiente; no aplicar400V/5s aESD|
|E7|Ruido con autocero0.0359458/0.00507913cuentas en200mV/20V|Cumple<1cuenta|
|E8|Corriente máxima22.031969mA;48/144 casos ESD superan5mA|Falla criterio del modelo; red y±50V confirmados cumplen|

E1 por rango200mV/2V/20V/50V, p95 residual con ruido0.05%:0.112642/0.095252/0.137191/0.180711%; con0.1%:0.193117/0.203479/0.207898/0.227235%. Caída nominal20kHz respecto100Hz enX0:−1.020290% con×1 y−0.979663% con×10.1. No implica respuesta plana sin calibración.

|E2: rango|Cambio de cero SPICE18/28°C, cuentas|Presupuesto conservador, cuentas|Fuga máxima por entrada de buffer a23°C, nA|
|---|---:|---:|---:|
|200mV|3.291474|4.188685|0.804034|
|2V|0.329149|0.407672|9.601409|
|20V|3.518493|3.662850|0.940429|
|50V|1.066151|1.117505|8.582176|

La fuga global tolerable es **0.804nA por entrada a23°C**, condicionada al resto del presupuesto y a duplicarse cada10°C. No es especificación garantizada del fabricante. Se incluye la fuga deYn2 no seleccionado cargandoX1 a través de89.91kΩ y la fuga del bufferX1 cargandoX2 a través de esa misma transferencia. TC p95 de ganancia:176.123/0/115.593/136.012ppm; cambio de ganancia SPICE:0.002036/0.002061/0.018899/0.091046ppm.

E3 falla enX2/50V a±50V, tanto0 como5pC: error final+50V≈−1.3740cuentas y−50V≈+1.3443cuentas; la espera1.5ms deja hasta1.656123cuentas. Confirmación100ns del caso+50V/X2/0pC:−1.654731cuentas tras espera y−1.373430 al final. Los casos que alcanzan una cuenta tardan como máximo1.034833ms. El riel contractual se evalúa en las otras dos rutas durante todo el caso y en la ruta futura hasta su cierre a21.002ms.

Incertidumbre numérica: nueve referencias100ns conservan el dictamen de rieles, con diferencia máxima0.020512V en picos y0.00596cuentas en espera. El pico de ruta seleccionadaX0=4.907789V del paso1µs/+50V/5pC baja a4.896918V a100ns. La corriente inversoraX0=10.312440mA del caso+50V/0pC baja a**2.147622mA** con100ns; picoX0=4.896866V. Se descartan esos picos gruesos para afirmar sobrecorriente o exceso del riel. Los CSV originales mantienen las métricas gruesas para trazabilidad; las comprobaciones finas están separadas y no sobrescriben la campaña.

E8: las dos rampas±50V conTI completo dan≤0.432268mA; las comprobaciones finas de conmutación±50V incluidas dan≤2.147622mA. Red230/253Vrms≤2.639346mA. ESD±4kV:16.548341mA máximo y24/72 fallos;±8kV:22.031969mA y24/72 fallos. Peor4kV:positivo, alimentado, cuerpo0, riel1.02, tap0, GDT780V/100ns; peor8kV:negativo, mismo estado salvoGDT420V. La corriente medida incluye desplazamiento capacitivo; la pinza reducida Ron1Ω no tiene IV validada. El resultado contractual es fallo, pero no demuestra daño físico ni identifica corriente de pinza de silicio real.

E5: márgenes×10.1=64.471286°/63.692371° paraRon60/400Ω. E4 usa umbral deOL supuesto2.02V; sin validación del driver siguiente. E7 RMS antes del√2 deautocero:0.0254175/0.00359149cuentas; voltaje integrado2.56717µV/0.359149µV.

### E6 — tensiones y energías por pieza

Máximos independientes por columna sobre los estados completos; no constituyen un único caso combinado. Duración por encima de200V para resistenciasRT1206; energía disipada por resistencia. El CSV `s12b_impulsos.csv` identifica las1628 observaciones pieza/caso.

|Pieza|4kV pico V|4kV >200V ns|4kV energía nJ|8kV pico V|8kV >200V ns|8kV energía nJ|
|---|---:|---:|---:|---:|---:|---:|
|r1a1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r1b1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r2a1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r2b1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r3a1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r3b1.5MΩ|420.241|1.601|46.257|556.098|2.092|51.079|
|r910k|5.305|0|1.265|5.312|0|1.271|
|r100k|0.583|0|0.139|0.583|0|0.139|
|rc13.3kΩ|839.989|36.314*|2131.245|1111.430|42.560*|2490.566|
|rc23.3kΩ|839.989|36.314*|2131.245|1111.430|42.560*|2490.566|
|rc33.3kΩ|839.989|36.314*|2131.245|1111.430|42.560*|2490.566|

*200V es umbral informativo paraRc, no rating confirmado. CadaRc supera400V durante≤1.572ns/2.046ns y1000V durante0/0.254ns en4/8kV. La duración sobre su rating real queda desconocida.

Régimen253Vrms/1s: cada1.5MΩ≤58.732V,1.141mJ, inferior a160V (80% de200V);910kΩ4.868V/24.032µJ;100kΩ0.535V/2.641µJ;cadaRc0.0151V/32.134nJ. En capacitores, para4/8kV: cada100pF≤160.471/170.233V y energía almacenada≤1.288/1.449µJ;330pF≤5.305/5.312V,4.643/4.655nJ;3nF≤0.583/0.583V,0.509/0.510nJ. No confundir energía almacenada con disipada ni aprobar impulso sin curva del fabricante.

### Comprobaciones auxiliares, ejecución y pendientes

C2: cambio±10pF enCOM/X0 deja caída20kHz entre−1.020375 y−1.020207%;±20pF/X1 entre−3.459399 y−3.459072%. C3: capacitancia incremental inferida deCOM0.8855…0.9000pF para−2…+2V, sin reemplazar los25pF de hoja; THD0.000154%/0.016163% a0.2/2V. Q0: cruce de unidad≈9.772MHz. El indicador heredado de consumo de transitorios llega29.959mW; el presupuesto explícito5.116mA×9.8V=50.137mW es el que incluye losIC de protección y buffers. Son fronteras distintas, no una demostración de consumo total del equipo.

Ejecutor:10trabajadores,900s por caso, prioridadE3→E8→E2→E1→E6→E5→E4→E7; luegoC2/C3/Q0. Reanudación verifica firma de fuentes y deck. Reauditoría solo reutiliza RAW cuando el deck guardado coincide exactamente con el deck actual; historial de firma conservado. Recuento: E1=800,E2=12,E3=48,E4=8,E5=8,E6=148,E7=2,E8=150,C2=6,C3=7,Q0=2; total1191.

Smoke final11/11:17.036s,10reutilizados. Campaña final1391.217s,198reutilizados inicialmente; fase previa válida1625.140s; reparación de dos±50V con señales guardadas11.103s; reauditoría final33.353s. Suma de estas fases3060.813s (**51min00.8s**); excluye desarrollo, intentos interrumpidos y auditorías anteriores. Todas las1191 fichas finales son válidas y tienen firma actual. Cuatro comprobaciones adicionales (tres transitorios100ns y nominalAC×10.1):170.300+156.127=326.427s. No son casos adicionales de la población principal. Se conservan errores/logs preliminares sin presentarlos como aprobaciones.

Comandos desdeDMM: `python ejecutar_s12b.py --smoke --workers 10`, `python ejecutar_s12b.py --resume --workers 10`, `python refrescar_s12b.py --collect`, `python analizar_s12b.py`; auxiliares `reparar_s12b_50v.py` y `verificar_s12b.py` (incluye `--only-zero-charge`). El límite900s está fijado en el ejecutor. Consultar `--help` para las opciones completas.

Dudas abiertas: dispersión realTI/GBW/Cin/Ib/Vos, fuga garantizada por temperatura, carga efectiva de bloque5 ydriver/OL, IV y capacidad de pinzas, encapsulado/compartición delOPA deA/B, condiciones de arcoIECaire, curvas de impulso yMPN deRc, ratings definitivos de capacitores y efectos delPCB. No se altera ninguna pieza para corregir E2/E3/E5/E8. No se declara cumplimientoIEC ni aceptación de fabricación. Auditoría independiente y prototipo pendientes.

Artefactos: `comun/dmm_bloque2b.inc`, `ejecutar_s12b.py`, auxiliaresS12b, `S12b/` con decks/logs/RAW/fichas y `resultados/s12b_*` conCSV/JSON. Se comprobó la integridadSHA256 de64 fuentes protegidas; STATE yDECISIONS se conservan por instrucción expresa.
