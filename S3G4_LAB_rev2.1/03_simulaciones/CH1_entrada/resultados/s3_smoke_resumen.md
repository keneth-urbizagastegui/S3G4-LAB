# ACTA S3 — CH1 buffer, escalera, 4051 y AD8039

Código 0; 52 ejecuciones; 0 errores de campaña; 0 advertencias de campaña; 268.312s; diez trabajadores.

De esas ejecuciones, 2 son pruebas de compatibilidad SWI1 que no convergen y activan la sustitución permitida sólo en E15; sus fallos y registros parciales no cuentan como una simulación nativa válida. E15 y C8 son aproximados (RON100, sin inyección de carga real).

**SMOKE: parcial, sin aceptación.**

| criterion | value | status |
| --- | --- | --- |
| S3-C1 | Loss S3 max 0.0190101283 dB / 0.5 | PARCIAL |
| S3-C2 | Peak S3 1.78462966e-05 dB / 0.5; step 0.000172600053% / 5 | PARCIAL |
| S3-C3 | DC error max 0.954048406% (informativo) | PARCIAL |
| S3-C4 | Noise 1Hz–3.15MHz 0.644338186% div / 0.45 | PARCIAL |
| S3-C5 | THD 0.00696637201% / 1; SR fraction 0.0292243815 / 0.5 | PARCIAL |
| S3-C6 | Recovery max finite 551.21675 us / 1; not recovered 0 (window 988.98us) | PARCIAL |
| S3-C7 | Diff A 0.0591696756, B 0.610193566 / 4V; U101 4.36202684/7V, I 2.18627024/10mA, rail excess 0.919680478/0.5V; AD rail excess -4.00893791V | PARCIAL |
| S3-C8 | Settle 0.0810606431 us / 10; glitch 3.51714213e-11 div; not recovered 0 | PARCIAL |

## Comprobaciones aisladas anteriores a campaña

Ganancias calculadas: G1=5.01606425703, G2=10.0763052209, producto=50.5433944614.

| stage | gain_dc | ideal | minus3_Hz | peak_db | loss_2m_db |
| --- | --- | --- | --- | --- | --- |
| a | 4.999745221851348 | 5.016064257028113 | 85200534.21975593 | 1.928654933106574e-15 | 0.0011771818326452926 |
| b | 10.011555092849296 | 10.076305220883533 | 32481166.55054551 | 0.0 | 0.015794136645117317 |

| tap | resistance_to_ground_Ohm | total_Ohm | ratio | ideal_chain_gain |
| --- | --- | --- | --- | --- |
| 0 | 997.6999999999999 | 997.6999999999999 | 1.0 | 50.543394461379656 |
| 1 | 498.69999999999993 | 997.6999999999999 | 0.4998496542046707 | 25.26409824385089 |
| 2 | 249.70000000000002 | 997.6999999999999 | 0.25027563395810365 | 12.649780091216298 |
| 3 | 99.69999999999999 | 997.6999999999999 | 0.09992983862884634 | 5.050793252279795 |
| 4 | 49.8 | 997.6999999999999 | 0.04991480404931342 | 2.5228636305269188 |
| 5 | 24.9 | 997.6999999999999 | 0.02495740202465671 | 1.2614318152634594 |

| control | level | ron | off_gain |
| --- | --- | --- | --- |
| 0 | 0 | 69.1320757766 |  |
| 5 | 1 |  | 1.99999999574e-09 |
| 0 | 2 | 75.0356713488 |  |
| 0 | -2 | 71.6629126354 |  |

## Convergencia nativa de SWI1 con control30ns

| corner | native_converged | stall_time_s | collapsed_step_s |
| --- | --- | --- | --- |
| nomi | False | 1.0151585158976798e-06 | 7.254225211928691e-16 |
| slow | False | 1.0158188724994948e-06 | 4.259709633500563e-16 |

## Por escala nominal DC

| scale_V_div | POS | tap | gain_dc | ideal | error_pct | minus3_s3_Hz | minus3_bnc_Hz | loss_s3_2m_db | loss_bnc_2m_db | peak_s3_db | peak_bnc_db | noise_uV | noise_pct_div | noise_10m_uV | recovery_positive_us | recovery_negative_us |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 1 | 0 | 49.56663270154675 | 50.043955782668625 | -0.9538076550039243 | 28458815.28427667 | 25732520.371830072 | 0.018859201699349043 | 0.02432590685313691 | 1.784629657970336e-05 | 1.7283477666134454e-05 | 32.216909315093915 | 0.6443381863018783 | 57.47297053689171 | 0.03425000000002089 | 0.034750000000021986 |
| 0.2 | 1 | 5 | 1.237051372436179 | 1.2489671233722048 | -0.9540484063226162 | 28167098.11673764 | 25543241.43085815 | 0.01901012825859336 | 0.024476774270019652 | 1.784469110120399e-05 | 1.7281900492414528e-05 | 1186.0729070626091 | 0.5930364535313045 | 2119.4551905245867 | 551.2167499999999 | 551.2167499999999 |
| 0.5 | 100 | 0 | 0.49601032564833647 | 0.5007867347672896 | -0.9537810783212364 | 28458815.28094988 | 25727854.242126018 | 0.018859201705987767 | 0.025374257125418347 | 1.784629657777471e-05 | 1.7791426829722113e-05 | 3216.024547987918 | 0.6432049095975836 | 5734.95966173841 | 0.034750000000021986 | 0.034750000000021986 |
| 20.0 | 100 | 5 | 0.01237909901565222 | 0.012498335868202376 | -0.9540218298462633 | 28167098.116713926 | 25538610.51456396 | 0.019010128258616924 | 0.025525125505889912 | 1.7844691099275335e-05 | 1.7789826334846735e-05 | 118534.65728754204 | 0.5926732864377102 | 211748.34819997114 | 0.02025000000002238 | 0.02025000000002238 |

## E14: entradas y recuperación, ambas polaridades

| ix | polarity | pulse_requested_V | pulse_BNC_plateau_V | recovery_0p1_s | recovery_0p5_s | u103a_differential_peak_V | u103b_differential_peak_V | u101_differential_peak_V | u101_plus_current_peak_A | u103a_plus_current_peak_A | u103a_minus_current_peak_A | u103b_plus_current_peak_A | u103b_minus_current_peak_A | u103a_plus_rail_excess_V | u103b_plus_rail_excess_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | negative | -0.2 | -0.2 | 3.4750000000021987e-08 | 2.6750000000021386e-08 | 0.05913802116220035 | 0.6087052171351606 | 0.04594391885743393 | 4.9554307061838704e-05 | 3.917128983750957e-05 | 3.652307056843413e-05 | 0.00018449483125199933 | 8.004285234251265e-05 | -4.8020135703850295 | -4.010428356128369 |
| 0 | positive | 0.2 | 0.2 | 3.425000000002089e-08 | 2.6750000000021386e-08 | 0.05913218061523165 | 0.6094576248429786 | 0.045960122756030106 | 4.955421068546392e-05 | 3.918137309704007e-05 | 3.65300237808454e-05 | 0.0001844790328360934 | 8.003651113292683e-05 | -4.801862870409505 | -4.009674931762996 |
| 5 | negative | -8.0 | -8.0 | 0.0005512167499999999 | 0.00036331675 | 0.018545938485724056 | 0.24500762619454447 | 4.340558458940918 | 0.0021856180221387516 | 1.237596667750631e-05 | 1.1630385835413063e-05 | 5.83546112149699e-05 | 5.3979969692891826e-05 | -4.873351556446475 | -4.376187696167187 |
| 5 | positive | 8.0 | 8.0 | 0.0005512167499999999 | 0.00036331675 | 0.018541908679490515 | 0.24420938819163934 | 4.3620268351198845 | 0.002186270237194746 | 1.2315932717547659e-05 | 1.1629254521423182e-05 | 5.834875261148198e-05 | 5.398429180548633e-05 | -4.873672209238173 | -4.376986515722302 |
| 6 | negative | -20.0 | -20.0 | 3.4750000000021987e-08 | 2.7000000000021934e-08 | 0.05916967556852841 | 0.6094396215110847 | 0.045971534833512184 | 4.958284165053333e-05 | 3.9194896139137856e-05 | 3.65462840143609e-05 | 0.00018460712804244933 | 8.00506754520143e-05 | -4.801899531404882 | -4.0096927239627105 |
| 6 | positive | 20.0 | 20.0 | 3.4750000000021987e-08 | 2.6750000000021386e-08 | 0.059165395014700695 | 0.6101935663784976 | 0.04598768745854865 | 4.958275090295254e-05 | 3.9205082384680344e-05 | 3.654454786854179e-05 | 0.00018460856374237264 | 8.003411250769415e-05 | -4.8017490289560305 | -4.008937914005099 |
| 11 | negative | -40 | -40.0 | 2.025000000002238e-08 | 1.2250000000021779e-08 | 0.002897217666038486 | 0.022771930283452275 | 0.09319620994859398 | 9.943262474340903e-05 | 1.9379706633335386e-06 | 1.817274489899448e-06 | 9.184074852618164e-06 | 6.894120551560952e-06 | -4.9901127483228835 | -4.950559748800294 |
| 11 | positive | 40 | 40.0 | 2.025000000002238e-08 | 1.2250000000021779e-08 | 0.002897434651734908 | 0.02277254700308799 | 0.09324001375868357 | 9.943261951503315e-05 | 1.937974036745581e-06 | 1.817278318185025e-06 | 9.184034773558621e-06 | 6.894258580830757e-06 | -4.990108981223133 | -4.950540911779367 |

## Gran señal y corriente por pin

| ix | vpp | output_pp_V | thd_pct | max_dvdt_V_us | model_SR_V_us | u101p_signal | u101n_signal | u103ap_signal | u103an_signal | u103bp_signal | u103bn_signal |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | 2 | 1.9999933690801928 | 0.00696637201181924 | 12.566484040863001 | 430.0 | 0.00190404627462 | -0.00190397080721 | 0.00103598325266 | -0.00103568177913 | 0.00112382537363 | -0.00111855329804 |
| 0 | 4 | 3.999980621296251 | 0.023150609182341058 | 25.133831826262423 | 430.0 | 0.00190805468522 | -0.00190797921495 | 0.0010368490773 | -0.0010365475924 | 0.00135231456519 | -0.00134704221358 |
| 6 | 2 | 1.9999933919783404 | 0.006966258115298515 | 12.566462632208506 | 430.0 | 0.0019040463731 | -0.00190397071444 | 0.00103598363436 | -0.00103568139753 | 0.00112383206085 | -0.00111854663678 |
| 6 | 4 | 3.99998066638628 | 0.023150716535413292 | 25.13376167414388 | 430.0 | 0.00190805480469 | -0.0019079791283 | 0.00103684948845 | -0.00103654718139 | 0.00135232176959 | -0.00134703503996 |

## Reposo con BNC a cero

| ix | u101p_idle | u101n_idle | u103ap_idle | u103an_idle | u103bp_idle | u103bn_idle |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 0.00190007547455 | -0.00190000001 | 0.00103569450518 | -0.00103539304302 | 0.00103818217499 | -0.00103291033699 |
| 5 | 0.00190007548654 | -0.00190000001 | 0.00103554752743 | -0.0010355400045 | 0.00103560954635 | -0.00103547798866 |
| 6 | 0.00190007565094 | -0.00190000001 | 0.00103569485744 | -0.00103539269084 | 0.00103818834617 | -0.00103290418911 |
| 11 | 0.00190007566292 | -0.00190000001 | 0.00103554753622 | -0.00103553999571 | 0.00103560970008 | -0.00103547783495 |

Corrientes en A: positiva entra al pin desde VP/VN; el retorno negativo suele tener signo negativo. Medidas individuales, no total del riel.

## E15 peor caso por transición, POS y proceso

| POS | corner | transition | skew | order | codes_observed | glitch_div | transition_peak_div | settlement_s | saturation_4V_flag |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | nomi | 0to5 | 10ns | 201 | 0>4>5 | 6.306066779870889e-14 | 15.357395634198436 | 8.106064219951026e-08 | True |
| 1 | nomi | autozero | 0ns | 012 | 0>6>0 | 3.517142133091511e-11 | 2.015072491028987 | 5.253153121156263e-08 | False |
| 1 | slow | 0to5 | 10ns | 201 | 0>4>5 | 6.306066779870889e-14 | 15.357395634198436 | 8.106064219951026e-08 | True |
| 1 | slow | autozero | 0ns | 012 | 0>6>0 | 3.517142133091511e-11 | 2.015072491028987 | 5.253153121156263e-08 | False |
| 100 | nomi | 0to5 | 0ns | 012 | 0>5 | 7.949196856316121e-14 | 15.357395634216159 | 7.104530024626068e-08 | True |
| 100 | nomi | autozero | 0ns | 012 | 0>6>0 | 2.2382096176443156e-12 | 2.0151077268396556 | 5.253154043934623e-08 | False |
| 100 | slow | 0to5 | 0ns | 012 | 0>5 | 7.949196856316121e-14 | 15.357395634216159 | 7.104530024626068e-08 | True |
| 100 | slow | autozero | 0ns | 012 | 0>6>0 | 2.2382096176443156e-12 | 2.0151077268396556 | 5.253154043934623e-08 | False |

Protegidos 20560; cambios []. Todos los estados y ambas entradas/corrientes en CSV.

## Método, fuentes y dudas sin resolver

Se leyeron completos encargo, plan S3, contrato S2b, acta y auditoría S2b,
sus antecedentes S2/S1b/S1 y las decisiones del 3 oct. Fuentes rectoras:
revision_entrada_ch1.html §6 E11–E15; rediseno_afe_rev21.html C.3–C.6.
Se conserva la red y los valores de FRONT_S2B sin cambios, incluida su
CS derivada ≈1.169nF y CEQ≈8.668pF: no se sustituyen por 1.5nF/12pF de
las listas resumidas. CIN_BUF=0; CBUF_EST=2.5pF. S3 sólo añade carga aguas abajo.
Ideal BNC = toma calculada × ganancias calculadas × nominal_gain de S2,
incluida la carga RBIAS. Ganancia en continua por AC a 1Hz (DC coupling);
AC coupling se normaliza a 1kHz, no se llama ganancia DC. Rsource=50ohm;
E11 informa H respecto a BNC y respecto al pin de U101 después de R_PROT.
Caída positiva significa pérdida; negativa significa subida. Pico hasta 100MHz.
E11b es escalón BNC de 1div, 2ns; overshoot relativo a su delta final real.
E14 usa enlace ideal0V de SRC a BNC para imponer exactamente min(10FS,40V)
en el puerto; el resto usa fuente50ohm. Se guardan meseta y pico BNC reales.
Rieles ideales ±5V con 10uF+100nF: opción autorizada; no evalúa inyección en
rieles reales de G.3. Sensores de 0V separan ambos rieles y entradas de cada
amplificador; no se asigna consumo total del riel a una etapa.

U102: ocho SWI1 del fichero hc_tnomi.cir de Nexperia, nodo control/Y/Z/VEE/VCC/GND,
activo bajo, incluyendo las siete ramas apagadas. Sólo se incluye una esquina
por deck (nombres repetidos). hc_tslow en E11 y toda E15. Sin HC4051pck extra:
el contrato exige SWI1+3pF de pista. Sus parásitas son las del macro de transistor.
La hoja sólo publica capacitancias terminales (p10: Yn5pF, Z25pF), no una matriz
de capacidades ni una garantía de inyección. No se añaden otra vez al macro.
Nexperia declara el modelo para transitorio: que converja AC/noise no valida
su precisión experimental. Si converge, no se sustituye por Ron fijo.
En conmutación E15 SWI1 no converge: el control aislado30ns colapsa a pasos
<1fs sin alcanzar3us. El ejecutor comprueba ambas esquinas antes de campaña
y guarda su último tiempo/paso tras30s de diagnóstico. Sólo en las esquinas
que fallan E15 sustituye las ocho SWI1 por SW(Ron100ohm), Yn5pF y Z25pF
(distribuido25pF/8 en cada rama), p10. Las capacidades no especifican una
matriz de acoplamiento al control; el proxy NO reproduce inyección de carga.
Glitch y C8 son resultados de esta aproximación, pendientes de modelo/placa.
No se presenta un peor RON de proceso real en E15: ambos proxies usan100ohm.

E12 es V(inoise) de LTspice referido a Vsrc en la BNC con Rsource=50ohm,
no ruido de salida dividido por una ganancia constante. Se integra su densidad
al cuadrado mediante trapecios entre 1Hz y 3.15MHz y 10MHz; se interpola
explícitamente el punto de corte. Esta referencia incluye los 50ohm.
Diagnóstico adicional separado (S3/diagnostico_ruido_ad8039.cir y
diagnostico_ruido_opa810.cir, ambos ejecutados con código0): el AD8038
aislado con la red contractual×5 da inoise=1.61810882549e-8 V/raízHz
a100kHz, frente a8nV/raízHz de la hoja p3; OPA810 seguidor con la carga
de escalera da5.77019729804e-9 V/raízHz. La discrepancia de ruido del AD8038
queda abierta: NO se divide por2 ni se modifica el modelo para aprobar C4.
Los dos decks diagnósticos son anclados a la estructura original mediante
rutas relativas; la campaña principal sí soporta S3G4_MODELS en una copia.
E13 ajusta solamente el estímulo desde la AC medida para 2/4Vpp, no el diseño;
THD armónicos 2–9 sobre 20 períodos, rejilla uniforme65536 por interpolación
del raw ≤0.5ns; todos los armónicos se conservan. SR del macro = Isrc/Cout
de A2 =43uA/0.1pF, no se utiliza como sustituto el SR típico de la hoja.
E14: pulso de10us con flancos10ns, origen recuperación al FINAL del flanco
de bajada. Se busca la última violación respecto al offset final real, nunca
el primer cruce. Registro1ms; se informa ventana y recuperación censurada.
Paso <=1ns durante pulso y primeros5us tras su fin, verificado en raw;
después <=50ns. El objetivo es el punto DC inicial, no el último valor de cola.
Las corrientes de entrada AD8039 son del modelo simplificado: no representa
Ib400nA ni diodos diferenciales. No especifica límite de corriente la hoja.
La diferencial sí se juzga contra ±4V aunque el macro no se destruya.
AD8038_8039.pdf RevG p5 Table3; entrada común absoluta±VS; p3 reposo1mA
típ/1.5mA máx, salida±4V en RL2k, recuperación50ns en G2/1V no trasladable
a esta cadena. OPA810: ±7V diferencial, ±10mA; se informa también exceso de
VS±0.5V conservando la contradicción acta/auditoría S2b, sin resolverla.

E15: código binario comportamental a partir de las tres direcciones reales;
el código nuevo debe coincidir con el de20ns antes para cerrar. RC de control
tau=30ns/ln9 da flanco10–90%30ns; la separación al50% es20ns en cambio
simple. Se prueban las seis permutaciones de desfase10ns, incluyendo códigos
intermedios, no sólo el orden supuesto peor. El filtro limita pulsos de código
menores que BBM; no representa el decodificador físico ni su hazards exactos.
Se conserva el comportamiento del SWI1 detrás del control. Pico de glitch =
excursión fuera del intervalo entre salida inicial/final (div); se informa
además pico absoluto respecto a masa e indicio de saturación por etapa si
la salida ideal demandada supera4V y |diferencial|>50mV simultáneamente.
Esto reconoce el recorte del macro alrededor3.84V con nuestra carga, sin
confundirlo con el ±4V típico de hoja en RL2k. No es un límite de seguridad.
La entrada se calcula desde la ganancia DC medida en E11 para+2div en la toma
de llegada, y en autocero para
la toma de retorno: GND no puede producir+2div. Ambos eventos se miden.

Contradicción documental de tiempos: el plan atribuye30ns/20ns a la hoja;
74HC_HCT4051.pdf Rev12 p13–14 columna ±4.5V dice ton16–18ns típico y
toff18ns típico (máx51/42ns a25°C); NO declara BBM20ns. Se aplican30ns/20ns
como supuestos impuestos por contrato, no como citas verificadas de fabricante.
El documento vivo C.6 aún contiene la red4.02k/1k,9.09k/1k y candidatos
anteriores; manda decisión3oct y contrato S3:1k/249,2.26k/249,AD8039.
§6 de revisión conserva criterio ruido0.35%/10MHz; manda S3:0.45%/3.15MHz.
Resultados de modelo no prueban supervivencia, consumo real ni ESD en placa.
No se diseña S4 ni filtro, no se eligen protecciones ni se descargan ficheros.
No se modifican STATE/DECISIONS por prohibición específica del encargo.
CSV ordenados deterministas, .cir/.log retenidos, raw regenerable eliminado.
