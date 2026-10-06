# ACTA S6 — ADC entrelazado CH1

Código 0; 25 simulaciones; 177.251s; diez trabajadores. Errores 0; advertencias 0.

RSW deducida=824.80451339ohm; ventana=67.3076923077ns; período=307.692307692ns; desfase=153.846153846ns.

| criterion | status | value |
| --- | --- | --- |
| S6-C1 | PARCIAL | 3.56886885e-06 LSB <= 0.5 |
| S6-C2 | PARCIAL | 86.5551451 LSB <= 0.5 |
| S6-C3 | PARCIAL | 0.000909576433 LSB rms <= 0.5; SFDR min 106.171978 dB >= 66 |
| S6-C4 | PARCIAL | 0.0425709045 dB <= 0.1 |
| S6-C5 | PARCIAL | 77.930008 deg >= 45 |

## Continua y seno nominal

| test | freq_Hz | level_V | adc | error_max_mV | error_rms_mV | error_max_LSB | error_rms_LSB | residual_rms_mV | residual_max_mV | gain_delta_db | phase_delta_deg |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 0.0 | 0.25 | 1 | 2.420292577465233e-07 | 2.4202924994026796e-07 | 3.9654073589190377e-07 | 3.96540723102135e-07 |  |  |  |  |
| H1 | 0.0 | 0.25 | 2 | 2.420293132576745e-07 | 2.420292924409931e-07 | 3.9654082684137393e-07 | 3.965407927353231e-07 |  |  |  |  |
| H1 | 0.0 | 1.25 | 1 | 1.210148203867334e-06 | 1.210148203867334e-06 | 1.98270681721624e-06 | 1.98270681721624e-06 |  |  |  |  |
| H1 | 0.0 | 1.25 | 2 | 1.2101484259119388e-06 | 1.2101483010118534e-06 | 1.9827071810141207e-06 | 1.9827069763778207e-06 |  |  |  |  |
| H1 | 0.0 | 2.25 | 1 | 2.1782646797419147e-06 | 2.1782646519863417e-06 | 3.568868851289153e-06 | 3.5688688058144222e-06 |  |  |  |  |
| H1 | 0.0 | 2.25 | 2 | 2.1782646797419147e-06 | 2.178264360552804e-06 | 3.568868851289153e-06 | 3.5688683283297145e-06 |  |  |  |  |
| H2 | 1999511.71875 | 1.25 | 1 | 52.82906806480625 | 37.355808666415825 | 86.55514511737856 | 61.203756919055685 | 0.0001670131118540086 | 0.0008561742292911845 | -0.04257074311514379 | -3.0216451474808346 |
| H2 | 1999511.71875 | 1.25 | 2 | 52.82867645968481 | 37.35580707990095 | 86.5545035115476 | 61.20375431970972 | 0.0001810976091462298 | 0.0009277272346175369 | -0.042570904507508334 | -3.0216449480406244 |
| H3 | 1999511.71875 | 1.25 | 1 | 52.82789652665376 | 37.35491140978552 | 86.55322566926952 | 61.2022868537926 | 0.0005533676539501232 | 0.0015183586269396088 | -0.042570985933947925 | -3.0216456879380535 |
| H3 | 1999511.71875 | 1.25 | 2 | 52.82694141486299 | 37.35490306696192 | 86.55166081411153 | 61.2022731849104 | 0.0005551613969736446 | 0.0015549763376643266 | -0.042570894017682714 | -3.0216450470404905 |

## FFT nominal, con y sin carga

| test | freq_Hz | sequence | sfdr_db | thd_pct | interleave_dbc | fundamental_pp_V | mean_V |
| --- | --- | --- | --- | --- | --- | --- | --- |
| H2 | 1999511.71875 | loaded | 145.52915482306497 | 8.653480944386316e-06 | -160.39844673625166 | 1.9902174417865168 | 1.2500000449486182 |
| H2 | 1999511.71875 | reference | 146.4466452533702 | 5.104635100506051e-06 | -197.0050019869997 | 1.9999957333082667 | 1.250000006608317 |
| H3 | 1999511.71875 | loaded | 106.17197837741949 | 0.0005394671329941186 | -161.91611916278362 | 1.9901691894221538 | 1.2499743565645676 |
| H3 | 1999511.71875 | reference | 106.06693634244705 | 0.0005461381107024301 | -187.64430169725955 | 1.9999472706301562 | 1.2499743192823276 |

## Sensibilidad completa

| test | RSW_Ohm | state | freq_Hz | level_V | adc | error_max_mV | error_rms_mV | residual_rms_mV | gain_delta_db | phase_delta_deg | block_rms_delta_mV |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| H1 | 825 | P | 0.0 | 0.25 | 1 | 2.420292577465233e-07 | 2.4202924994026796e-07 |  |  |  | 1.5612510870200958e-14 |
| H1 | 825 | P | 0.0 | 0.25 | 2 | 2.420293132576745e-07 | 2.420292924409931e-07 |  |  |  | 1.3877788221404763e-14 |
| H1 | 825 | P | 0.0 | 1.25 | 1 | 1.210148203867334e-06 | 1.210148203867334e-06 |  |  |  | 0.0 |
| H1 | 825 | P | 0.0 | 1.25 | 2 | 1.2101484259119388e-06 | 1.2101483010118534e-06 |  |  |  | 1.9428903158414908e-13 |
| H1 | 825 | P | 0.0 | 2.25 | 1 | 2.1782646797419147e-06 | 2.1782646519863417e-06 |  |  |  | 0.0 |
| H1 | 825 | P | 0.0 | 2.25 | 2 | 2.1782646797419147e-06 | 2.178264360552804e-06 |  |  |  | 8.32667305691995e-14 |
| H1 | 825 | R | 0.0 | 0.25 | 1 | 3.8821991849847803 | 3.881804565776418 |  |  |  | 8.15618724473062e-05 |
| H1 | 825 | R | 0.0 | 0.25 | 2 | 3.882743128898636 | 3.8818530837713925 |  |  |  | 6.695707523542496e-05 |
| H1 | 825 | R | 0.0 | 1.25 | 1 | 2.1571570066862833 | 2.1566096383696145 |  |  |  | 6.59147558895734e-05 |
| H1 | 825 | R | 0.0 | 1.25 | 2 | 2.1570336786647104 | 2.156629433809795 |  |  |  | 4.9252894935691155e-05 |
| H1 | 825 | R | 0.0 | 2.25 | 1 | 0.4314433663110684 | 0.43134185743110476 |  |  |  | 1.3525587094125394e-05 |
| H1 | 825 | R | 0.0 | 2.25 | 2 | 0.431471828921115 | 0.43133261184770344 |  |  |  | 3.252533126998306e-06 |
| H1 | 825 | Z | 0.0 | 0.25 | 1 | 0.43140895665050305 | 0.43140411668734985 |  |  |  | 9.353047614288519e-07 |
| H1 | 825 | Z | 0.0 | 0.25 | 2 | 0.4314090611480803 | 0.4314056954341386 |  |  |  | 1.863181434331486e-06 |
| H1 | 825 | Z | 0.0 | 1.25 | 1 | 2.1570767195944196 | 2.1570754908626024 |  |  |  | 1.1083378416432144e-06 |
| H1 | 825 | Z | 0.0 | 1.25 | 2 | 2.1570767296890114 | 2.1570756559531596 |  |  |  | 7.92793247283291e-07 |
| H1 | 825 | Z | 0.0 | 2.25 | 1 | 3.882679596296068 | 3.8826786226364063 |  |  |  | 2.5218837088059054e-07 |
| H1 | 825 | Z | 0.0 | 2.25 | 2 | 3.8826794881199334 | 3.882678057713088 |  |  |  | 1.2809952217897325e-06 |
| H2 | 825 | P | 1999511.71875 | 1.25 | 1 | 52.82906806480625 | 37.355808666415825 | 0.0001670131118540086 | -0.04257074311514379 | -3.0216451474808346 | 2.3869671218756938e-05 |
| H2 | 825 | P | 1999511.71875 | 1.25 | 2 | 52.82867645968481 | 37.35580707990095 | 0.0001810976091462298 | -0.042570904507508334 | -3.0216449480406244 | 1.2168033733384043e-06 |
| H2 | 825 | R | 1999511.71875 | 1.25 | 1 | 56.05034885366877 | 38.16968629564187 | 0.00019336449138040673 | -0.03154332624142603 | -3.0868766321430816 | 0.006594223195439952 |
| H2 | 825 | R | 1999511.71875 | 1.25 | 2 | 56.04996758597491 | 38.16969043691874 | 0.00016960401213415957 | -0.03154329569139436 | -3.0868770695621683 | 0.025315624298805073 |
| H2 | 825 | Z | 1999511.71875 | 1.25 | 1 | 56.05054599403747 | 38.169530938354605 | 7.151667683710197e-06 | -0.03154617806768087 | -3.0868613688578166 | 0.006588924994208045 |
| H2 | 825 | Z | 1999511.71875 | 1.25 | 2 | 56.050176182790736 | 38.169531000681566 | 7.096017915221046e-06 | -0.03154617872766384 | -3.086861374659595 | 0.02531440479348196 |
| H3 | 825 | P | 1999511.71875 | 1.25 | 1 | 52.82789652665376 | 37.35491140978552 | 0.0005533676539501232 | -0.042570985933947925 | -3.0216456879380535 | 5.055959567679125e-06 |
| H3 | 825 | P | 1999511.71875 | 1.25 | 2 | 52.82694141486299 | 37.35490306696192 | 0.0005551613969736446 | -0.042570894017682714 | -3.0216450470404905 | 8.237083619355712e-06 |

## Lazo

| section | crossover_Hz | phase_margin_deg | loop_current_ratio_abs | tian_crossover_Hz | tian_phase_margin_deg | tian_voltage_pm_delta_deg |
| --- | --- | --- | --- | --- | --- | --- |
| OPA836 | 12395991.618321132 | 113.04138005516013 | 3.7089835828449207 | 12792918.996230997 | 77.93000804614915 | -35.11137200901098 |
| U105A1 | 224096333.66809586 | 71.58855722325195 | 5.847170567507337 | 220314975.99023387 | 60.68146091418258 | -10.907096309069374 |
| U105B2 | 223688650.86950982 | 73.09243777222471 | 5.594622328108782 | 217965365.41905653 | 61.730320640743045 | -11.362117131481668 |

Protegidos=12264; cambios=[].

## Circuito, modelo y límites

Fuentes: PLAN/ENCARGO S6 completos; PLAN/ACTA/AUDITORIA S5 completos;
AUDITORIA S4 completa; DECISIONS del 3 oct; revisión de entrada §6 E18;
g473_analogico §§2–3; canal_rapido bloque ⑨; modelos/LEEME; fuentes
ch1_comun_s4.inc, ch1_comun_s5.inc y ejecutar_s5.py. No se han descargado
modelos ni modificado las fuentes anteriores. No es prueba física.

S4 cerrado: RIN/RF 10k, ROFF8.06k, CF1p, CSUM1p, OPA836 a3.3V,
PD aVDDA; DESD_OPA836 de S4, M1 10k/5.23k+1u por copia; DAC1.25V;
68ohm/470p hasta pin. Los 5p estáticos de S4 se identifican ahora como
Cpad=5p supuesto (pad+pista), y cada ADC tiene Cs=5p conmutado aparte.
H1/H2 parten de fuente ideal en entrada S4. H3 usa únicamente el TR
reescalado contractual, dos AD8038 de LTspice representan AD8039 a±5V,
incluyendo pista1p por entrada. No se añade la cadena S1–S3 ni su carga
sustituta, porque H3 empieza en entrada del filtro y no es S7.

RSW estimado de límite RC de tabla62, no un parámetro publicado ni medido:
(2.5/60MHz)/(5p*ln(2^13))-100ohm. Barrido400/825/1500ohm contractual.
Switch muestreo Ron=RSW, Roff1e15, umbral0.5V; sin inyección de carga,
clock feedthrough, ruido, cuantización ni mismatch entre ADC. Reset ideal
Ron1m durante conversión en Z/R, a0/2.5V. P conserva su propio Cs;
ambos resets apagados en P. El estado inicial DC se establece por Roff;
se descartan256 muestras combinadas antes de analizar. H1 tiene32
muestras por ADC; H2/H3 512 por ADC. Bloques RMS permiten revisar régimen.
Flancos20ps son regularización numérica; umbral exactamente en apertura
y cierre contractuales. Muestreo como límite izquierdo en el umbral
descendente: extrapolación de dos puntos de tracking anteriores al cierre.
Z/R tiene constante de reset5fs: interpolar atravesando el reset falsea la
muestra. El CSV conserva último tiempo/clock de tracking y cruce real
para auditar el límite izquierdo; referencia interpolada al mismo instante.

Referencia: misma S4, M1, ideal source y, en H3, filtro completo, en
paralelo, con68/470p+Cpad y sin switches/Cs. Error=Cs-referencia al mismo
instante, no Cs-pin cargado. LSB=2.5/4096V. H0 DC y AC calculan offset y
amplitud de fuente para niveles deseados y2Vpp en la referencia sin carga;
se informa amplitud/centro real, no se altera ninguna pieza para centrar.
Esto es calibración del estímulo ideal, no compensación del error ADC.

Coherencia:1024 muestras, M impar más cercano a0.5/1/2MHz, frecuencia
M*6.5MHz/1024. Por ello '2MHz' no es exactamente2MHz: se informa la
frecuencia real. FFT rectangular sin ventana ni cuantización; SFDR excluye
DC y fundamental y busca todo el resto hasta Nyquist. THD armónicos2–9,
plegados por alias y con bins únicos; espurio fs/2-fin explícito. El umbral
66dB viene del contrato, mientras documento G473 cita66.9dB single y63.2dB
multi; SFDR determinista no certifica el SNR real del ADC.

Descomposición por ADC: LS sobre error=a*v[n]+b*v[n-2]+c, usando referencia
sin carga. Dos muestras anteriores se simulan antes de la FFT; no wrap
artificial. Parte lineal H=1+a+b*exp(-j*2*pi*f*2/fs); ganancia20log|H| y
faseangle(H). Residuo=error-modelo LS. Se incluyen muestras y bins para
recalcularlo, sin ocultar error absoluto bajo una calibración.

H4: OPA836 inyección Middlebrook en entrada inversora, fuente DC0
entre retorno y entrada; U105 en SALIDA del amplificador, para incluir
las dos rutas de feedback (negativa unidad y positiva C1 Sallen-Key).
Ensayo independiente de corriente con tensión AC0, manteniendo puntoDC
y todas las cargas. Romper sólo IN- de SK deja un lazo positivo cerrado
con polos RHP y un margen ambiguo; no se usa esa primera prueba.
Tv=-Vret/Vinj; Ti=-Iprobe/(Iprobe+Itest), Itest=1A AC, orientación probe
retorno→entrada e Itest masa→entrada. Retorno general Tian/Middlebrook
T=(Tv*Ti-1)/(Tv+Ti+2); fase desenrollada desde0°, todos los cruces
descendentes0dB; PM=180°+fase(T). Se informa también la aproximación Tv
y su diferencia. No se declara PM de sistema periódico con switches:
carga H4 es la fija68ohm+470p+Cpad exigida. U105A conserva secciónB yS4
como carga; U105B conservaS4; fuente ideal en entradaTR. No hay fuenteAC
de señal concurrente. PuntoDC obtenido por macro real, diodos deS4 presentes.

Contradicciones conservadas: guía dice68ohm<=100ohm pero eso sólo compara
resistencia externa estática, no prueba seguimiento durante67ns; S6 lo
mide. E18 exigíaerror absoluto<=0.5LSB; C3/C4 distinguen linealidad y
ganancia, sin sustituir C2. RSW/estado previo/Cpad son suposiciones, no
caracterización de silicio. VREF/DAC ideales no incluyen sus ruido/drift.
No se decide remedio ni se diseñaS7. R_ADC, C_ADC y ciclos de muestreo
podrían mover el error; no se han simulado valores alternativos.

## Reejecución

python ejecutar_s6.py --smoke
python ejecutar_s6.py
En copia de CH1_entrada: S3G4_MODELS=ruta_original_de_modelos.
Diez trabajadores desdeH0, columnasCSV explícitas, filas ordenadas;
.cir/.log conservados enS6 y excluidos de huellas operativas; raw
exitosos eliminados por ser regenerables. HashesS1–S5/modelos/STATE/
DECISIONS antes/después. Código0 significa ejecución completa.
