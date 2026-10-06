# ACTA S2b — entrada P4b

Código 0; 26 simulaciones; 0 errores; 0 advertencias; 18.544 s; 10 trabajadores.

**SMOKE: parcial, no aceptación.**

| criterion | buffer | value | status |
| --- | --- | --- | --- |
| S2b-C1 | OPA810 | Zin error 0.085388%; Cin 24.443517–24.832964 pF; delta 0.389447 pF; gain 0.187737%; flat 0.084306%; peak 0.001354 dB; fc 8.814669 Hz | PARCIAL |
| S2b-C1 | OPA828 | Zin error 0.092912%; Cin 30.879287–31.297180 pF; delta 0.417893 pF; gain 0.541745%; flat 0.343764%; peak 0.001303 dB; fc 8.783539 Hz | PARCIAL |
| S2b-C2 | OPA810 | ct2trim_v=49.5043; 0.618804 times derated limit (e5b_opa810_pos1_cpldc_pwr1_bleed0_sine100_t25_50ohm_real_contact) | PARCIAL |
| S2b-C2 | OPA828 | ct2trim_v=49.5041; 0.618801 times derated limit (e5b_opa828_pos1_cpldc_pwr1_bleed0_neg100_t25_50ohm_real_contact) | PARCIAL |
| S2b-C3 | OPA810 | rail excess 0.778812 V; input 0.000962578 mA; diff 0.886076 V / 7 V | PARCIAL |
| S2b-C3 | OPA828 | rail excess 0.544754 V; input 0.211425 mA; diff 4.04476 V / 9.95342 V | PARCIAL |
| S2b-C4 | GENERATOR | four points at 4 and 8 kV; see calibration CSV | PARCIAL |
| S2b-C5 | OPA810 | BAV max I2t 3.41301 microA2s / 8; input 5.67624 mA; diff 4.39916 V; OFF macro unvalidated | PARCIAL |
| S2b-C5 | OPA828 | BAV max I2t 3.58743 microA2s / 8; input 6.16921 mA; diff 4.08432 V; OFF macro unvalidated | PARCIAL |

## Generador sobre 2ohm; aire orientativo

| stimulus | mode | first_peak_A | rise_10_90_ns | i30_A | i60_A | i30_switch_A | i60_switch_A |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 4kv | contact | 14.985867865763495 | 0.805105078604813 | 7.926373584232879 | 4.046079137271234 | 7.93656834223981 | 4.051826649784338 |
| 8kv | air | 14.895349239352548 | 0.5079992794313816 | 9.910942413475432 | 7.169563179411343 | 9.914248955981298 | 7.171951760566067 |
| 8kv | contact | 29.97173573153648 | 0.8051050786041645 | 15.852747168465894 | 8.092158274542543 | 15.873136684479784 | 8.103653299568764 |

## Derivados por buffer

| buffer | CIN_BUF_pF | CBUF_EST_pF | CJ_POL_pF | C_SEL_EST_pF | CEQ_pF | CS_pF | CB_pF |
| --- | --- | --- | --- | --- | --- | --- | --- |
| OPA810 | 0 | 2.5 | 1.0838258570379375 | 8.667651714075875 | 8.667651714075875 | 1169.1033781639155 | 1088.540148285924 |
| OPA828 | 0 | 9.0 | 1.0838258570379375 | 15.167651714075877 | 15.167651714075877 | 1820.4059833743363 | 1082.040148285924 |

## I2t y estrés por estado

| buffer | test | POS | power | bleed | variant | stimulus | mode | DHP_I2t_uA2s | DLP_I2t_uA2s | DHP_peak_A | DLP_peak_A | input_peak_mA | differential_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| OPA810 | E7b | 1 | 1 | 0 | real | 4kv | contact | 3.4130140520382803 | 3.5268174519920043e-07 | 14.8598875399 | 0.0882072037982 | 5.6762354641999995 | 4.39915966424 |
| OPA828 | E7b | 1 | 1 | 0 | real | 4kv | contact | 3.587429859299947 | 3.532475921267301e-07 | 14.9246943913 | 0.0884024521253 | 6.1692084383 | 4.0843231772 |
| OPA810 | E7c | 100 | 0 | 2 | off_load_only | 4kv | contact | 0.10374150114337247 | 5.056866580852581e-09 | 6.05834082058 | 0.00467489134884 | 1.15916458832e-15 | 1.15907328155 |
| OPA810 | E7c | 100 | 0 | 2 | real | 4kv | contact | 0.10468658306435377 | 3.834350547134003e-09 | 6.06670946337 | 0.00410532169549 | 0.735580083653 | 0.861459312264 |
| OPA828 | E7c | 100 | 0 | 2 | off_load_only | 4kv | contact | 0.07853011282208165 | 4.318758117511724e-09 | 4.85028773001 | 0.00410171037171 | 1.08748442516e-15 | 1.08747145771 |
| OPA828 | E7c | 100 | 0 | 2 | real | 4kv | contact | 0.0802809720462105 | 2.0351673462292993e-09 | 4.87254519381 | 0.00277464278203 | 0.549761071118 | 0.0872330159311 |

µA²s en las columnas I2t significa 10⁻⁶ A²·s, no (µA)²·s. Límite por diodo: 50% de 4²·1µs = 8·10⁻⁶ A²·s.

## R/C en E5b

| buffer | part | voltage_V | voltage_limit_V | power_W | power_limit_W |
| --- | --- | --- | --- | --- | --- |
| OPA810 | rt1 | 49.5042963551 | 100.0 | 0.00446384650222 | 0.125 |
| OPA810 | rt2 | 49.5042963551 | 100.0 | 0.00446384650222 | 0.125 |
| OPA810 | rb | 0.991884580703 | 75.0 | 8.94395474034e-05 | 0.0625 |
| OPA810 | rs1 | 47.1279051871 | 100.0 | 0.0445098085637 | 0.125 |
| OPA810 | rs2 | 47.1279051871 | 100.0 | 0.0445098085637 | 0.125 |
| OPA810 | req | 0.933136824399 | 100.0 | 1.11960388033e-08 | 0.125 |
| OPA810 | rbias | 5.75654872955 | 75.0 | 3.30117066346e-06 | 0.0625 |
| OPA810 | rprot | 0.000962577659194 | 75.0 | 3.27126760031e-11 | 0.0625 |
| OPA810 | ct1 | 49.5042963551 | 80.0 |  |  |
| OPA810 | ct2fixed | 49.5042963551 | 80.0 |  |  |
| OPA810 | ct2trim | 49.5042963551 | 80.0 |  |  |
| OPA810 | cb | 0.991884580703 | 40.0 |  |  |
| OPA810 | cs | 94.2558103743 | 160.0 |  |  |
| OPA810 | cac | 5.73529543857e-08 | 40.0 |  |  |
| OPA810 | ceq | 0.933136824399 | 160.0 |  |  |
| OPA828 | rt1 | 49.5040577096 | 100.0 | 0.00446384650222 | 0.125 |
| OPA828 | rt2 | 49.5040577096 | 100.0 | 0.00446384650222 | 0.125 |
| OPA828 | rb | 0.991884580703 | 75.0 | 8.94395474034e-05 | 0.0625 |
| OPA828 | rs1 | 47.1338113119 | 100.0 | 0.0445209653063 | 0.125 |
| OPA828 | rs2 | 47.1338113119 | 100.0 | 0.0445209653063 | 0.125 |
| OPA828 | req | 5.73337168757e-11 | 100.0 | 3.28713532228e-28 | 0.125 |
| OPA828 | rbias | 5.73324846372 | 75.0 | 3.28701379467e-06 | 0.0625 |
| OPA828 | rprot | 0.211425265227 | 75.0 | 4.47006427762e-05 | 0.0625 |
| OPA828 | ct1 | 49.5040577096 | 80.0 |  |  |
| OPA828 | ct2fixed | 49.5040577096 | 80.0 |  |  |
| OPA828 | ct2trim | 49.5040577096 | 80.0 |  |  |
| OPA828 | cb | 0.991884580703 | 40.0 |  |  |
| OPA828 | cs | 94.2676226238 | 160.0 |  |  |
| OPA828 | cac | 2.11617579948e-05 | 40.0 |  |  |
| OPA828 | ceq | 5.73337168757e-11 | 160.0 |  |  |

## Cierre de integral 2 frente a 4ms

| diode | I2t_2ms | I2t_4ms | relative_change |
| --- | --- | --- | --- |


Protegidos: 20179 archivos; cambios: []. Segunda fuente: True. Los CSV completos conservan tensión/corriente de entrada, rieles, energía por resistencia, CS y contactos. E9 OPA828 en s2b_e9.csv.

## Método y dudas sin resolver

Contrato S2b y documentos rectoros S2/S1b/S1, actas, auditorías y decisiones
2/3 oct leídos; revisión de entrada §4/§6 y documento vivo C.6/G.3/G.5/G.6.
Sin descargas, ensayos físicos ni cambios a entregables anteriores o modelos.
El ejecutor importa las funciones de lectura/netlist de ejecutar_s2.py y sólo
configura sus objetos en memoria; requiere ese fichero en la copia de CH1_entrada.
S3G4_MODELS permite apuntar a modelos externos. Diez trabajadores; threads=1.

Generador pasivo de dos ramas RLC inicialmente cargadas al nivel indicado:
150pF/330ohm/1.8uH y 5pF/155ohm/180nH. Síntesis numérica propia de banco,
no selección de protección ni modelo certificado de una pistola comercial.
El switch cierra a 100ns; flanco de mando 1ps, la subida de corriente la fijan
los inductores. Contacto: 0.01ohm; aire: 300ohm en serie, orientativo.
E7a verifica realmente la suma de corriente sobre 2ohm antes de habilitar E7b/c.
Tiempo de subida 10–90%; I30/I60 desde el primer cruce del 10% del pico,
y CSV conserva también I30/I60 desde el cierre del switch. Primer pico en
los primeros 20ns; el máximo global también se conserva. Los cuatro puntos
no determinan de forma única la impedancia de salida o la energía del generador.

I2t por cada BAV199 = integral de la corriente terminal al cuadrado de 0 a 2ms,
incluida corriente capacitiva e inversa. El valor usado es el trapecio del raw;
.meas es control independiente. Tolerancia de contraste: 0.1% de la integral
o 1ppm del límite de C5 (8e-12 A2s), el mayor; evita errores relativos ficticios
en el diodo casi inactivo. Cierre de cola: 0.01% o ese mismo piso absoluto.
Se conserva cada discrepancia y la contribución de la segunda mitad en CSV.
La fuente PWL aislada introduce quiebres de 50ps en los primeros 100ns y 0.5ns
hasta 2us; el raw se comprueba, no se presume el paso de la directiva .tran.
Después se permite adaptación hasta 200ns; se informa una comprobación a 4ms.
Las energías Rt1/Rt2 representan R1A/R1B del contrato; Rs1/Rs2 son R_S1/R_S2.

OPA810: SBOS799E local, p4 máximo diferencial min(7V, alimentación total),
input ±10mA, riel ±0.5V; 2/2.5pF común, se usa 2.5pF para diseño.
OPA828: SBOS671D local, p4 diferencial igual al span de alimentación, sin
diodos entre entradas; riel ±0.5V y ±10mA. p5: 9pF común, 6pF diferencial,
modo común operativo limitado a VEE+2.5…VCC−3.5V. No es aceptación comercial
ni prueba de intercambiabilidad de encapsulado. CIN_BUF=0 en ambos circuitos.
CB/CS/CEQ derivados se recalculan para cada buffer como manda el contrato;
ningún valor se ajusta después de observar un fallo.

1. I2t 4A²·1us es un criterio encargado, no un rating IEC ni demostración de
supervivencia: IFSM está referido a conducción directa, aquí se incluye corriente
terminal capacitiva. El modelo no simula destrucción ni temperatura de unión.
La BV del modelo BAV199 no reemplaza VR=75V de la hoja.
2. E7c conserva el macro REAL a cero alimentación para informar corriente y
diferencial solicitadas, pero no está validado ahí. OFF_LOAD_ONLY añade el
equivalente contractual sin macro, con input sin protección interna: corriente
de entrada y diferencial de un amplificador ausente no certifican C5. Se
informan ambas variantes sin sustituir REAL para forzar aceptación.
3. C5 del plan fija ±7V diferencial también apagado; la hoja OPA810 exige el
menor de 7V y el span instantáneo. Se informa el exceso frente al span en CSV;
la tabla contractual OPA810 usa 7V, sin resolver la contradicción. La segunda
fuente se compara frente a su span instantáneo, incluso si el macro de riel
apagado invierte polaridad. Ninguno demuestra ausencia de alimentación parásita.
4. Los límites de R/C son genéricos de formato; faltan MPN y ratings de pulso.
Se cambian sólo ratings de R_EQ/C_EQ/C_S a 200V, no piezas para aprobar.
5. Rieles con fuente que sólo entrega, TVS genérica y cargas 42/39mA: el macro
añade consumo al equivalente agregado, posible doble cuenta heredada de S2.
No se elige TVS, purga ni interruptor. S2b no repite ±100V apagado de E6.
6. E5 DC es equilibrio, no transitorio de conectar 100V. El seno es 100Vpk/1kHz,
medido en el último ciclo 7–8ms. E7 utiliza CPL DC, como S2. Aire +8kV es
orientativo; el requisito acordado dice ±8kV aire, pero §3 sólo encarga +8kV.
7. Acoplo por una COFF_SW a través de CAC y capacidades diferenciales del macro
no equivale exactamente a la estimación C_SEL_EST. Se conserva la topología.
8. Los fallos eléctricos son resultados válidos. Código no cero indica error de
simulación/medida, calibración ausente/inválida o archivos protegidos cambiados.
CSV deterministas, .cir/.log retenidos, raw regenerable se elimina tras análisis.
