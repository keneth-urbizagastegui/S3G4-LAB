# ACTA S5 — filtro anti-alias de CH1

Código 0; 57 simulaciones; 346.855 s; diez trabajadores; errores 0; advertencias 0.

Casos finales verificados=57; reutilizados con deck idéntico=51; nuevas ejecuciones=6; intentos nativos acumulados=63.

**Ejecución parcial: sin aceptación de criterios.**

## Síntesis ideal

| candidate | scale_rad_s | minus3_Hz | overshoot_pct | rise_ns | atten_3p25m_db | atten_4p5m_db | atten_6p5m_db |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 14516445.717378018 | 2000000.0 | 0.2618098940081026 | 172.93244570096232 | 8.354360409894412 | 16.041332678413603 | 28.747274898236054 |
| TR | 14065779.756088406 | 2000000.0 | 2.8547066365342655 | 182.04233136364672 | 10.894804929008634 | 21.446575567176588 | 35.89937843952434 |
| BU | 13233398.881427823 | 2000000.0 | 9.412869355843224 | 196.42559682057455 | 17.12185434018911 | 29.675452659096177 | 44.81639226691079 |

## Componentes (C1 realimentación, C2 a masa; sección1 Q bajo)

| candidate | section | R1_Ohm | R2_Ohm | C1_pF | C2_pF | target_f0_Hz | target_Q | real_f0_Hz | real_Q | f0_error_pct | Q_error_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 1 | 590.0 | 590.0 | 82.0 | 82.0 | 3304217.0176753593 | 0.5219345816689801 | 3289684.6443136698 | 0.5 | -0.4398129203969092 | -4.202553814089171 |
| BE | 2 | 576.0 | 576.0 | 120.0 | 47.0 | 3704339.6321795685 | 0.8055382818416658 | 3679239.814197748 | 0.7989354619369612 | -0.6775787447721782 | -0.8196779785075936 |
| TR | 1 | 1150.0 | 1150.0 | 56.0 | 47.0 | 2677182.720783468 | 0.5307031978373262 | 2697611.155002705 | 0.5457768229098153 | 0.7630571518577156 | 2.8403117098061204 |
| TR | 2 | 511.0 | 511.0 | 220.0 | 56.0 | 2834647.9584893123 | 0.9870856812644104 | 2806040.1292498684 | 0.9910312089651149 | -1.0092198275898134 | 0.3997148145893803 |
| BU | 1 | 1470.0 | 1470.0 | 56.0 | 47.0 | 2106160.8458859967 | 0.541196100146197 | 2110376.0736415717 | 0.5457768229098153 | 0.2001379791960689 | 0.8464072010831103 |
| BU | 2 | 511.0 | 511.0 | 390.0 | 56.0 | 2106160.8458859967 | 1.3065629648763764 | 2107525.8708339017 | 1.319496657279369 | 0.06481104947759775 | 0.989901960386308 |

## Criterios por candidato

| candidate | criterion | status | value |
| --- | --- | --- | --- |
| BE | S5-C1 | PARCIAL | 1.82148..1.82221 MHz; 2/12 |
| BE | S5-C2 | PARCIAL | 2/3 = 66.6667% |
| BE | S5-C3 | PARCIAL | 0 dB |
| BE | S5-C4 | PARCIAL | exceso 0 dB; max alta -17.4918498 dB |
| BE | S5-C5 | PARCIAL | 188.125..188.184 ns |
| BE | S5-C6 | PARCIAL | 0.00272536968% |
| BE | S5-C7 | PARCIAL | 0.313453514% div; 2/12 |
| BE | S5-C8 | PARCIAL | rec 0.462649678 us; censurados 0; diferencial 0.0348504109 V |
| TR | S5-C1 | PARCIAL | 1.9506..1.95119 MHz; 2/12 |
| TR | S5-C2 | PARCIAL | 3/3 = 100% |
| TR | S5-C3 | PARCIAL | 0 dB |
| TR | S5-C4 | PARCIAL | exceso 0 dB; max alta -22.603662 dB |
| TR | S5-C5 | PARCIAL | 187.106..187.138 ns |
| TR | S5-C6 | PARCIAL | 0.0017235583% |
| TR | S5-C7 | PARCIAL | 0.318812074% div; 2/12 |
| TR | S5-C8 | PARCIAL | rec 0.706623228 us; censurados 0; diferencial 0.0437420747 V |
| BU | S5-C1 | PARCIAL | 1.91654..1.91685 MHz; 2/12 |
| BU | S5-C2 | PARCIAL | 3/3 = 100% |
| BU | S5-C3 | PARCIAL | 0 dB |
| BU | S5-C4 | PARCIAL | exceso 0 dB; max alta -30.9123474 dB |
| BU | S5-C5 | PARCIAL | 204.903..204.926 ns |
| BU | S5-C6 | PARCIAL | 0.00232576674% |
| BU | S5-C7 | PARCIAL | 0.316497733% div; 2/12 |
| BU | S5-C8 | PARCIAL | rec 1.08147861 us; censurados 0; diferencial 0.123698631 V |

## Comparativa (nominal5mV/div; ruido peor escala)

| candidate | minus3_MHz | atten_3p25m_db | atten_4p5m_db | atten_6p5m_db | overshoot_pct | square_overshoot_pct | rise_ns | gd_variation_ns | noise_max_pct_div | mc_within_pct | thd_max_pct | u105_idle_power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 1.822209010136647 | 9.503092100182585 | 17.48355142506528 | 30.256807202073965 | 0.0009022796245483633 | 0.0008989003850157218 | 188.12487097550155 | 16.059745592141326 | 0.31345351351753686 | 66.66666666666666 | 0.002725369675460312 | 20.71759080698 |
| TR | 1.951188722679016 | 11.809201379793267 | 22.593417325036558 | 37.14792051264003 | 3.204116951341507 | 3.2031840962729596 | 187.10619660651636 | 28.93602266878662 | 0.3188120743319457 | 100.0 | 0.0017235582952353696 | 20.71759081272 |
| BU | 1.916852512439587 | 18.379306704577665 | 30.90129199958564 | 46.08805598008768 | 8.831188766565056 | 8.830163913068368 | 204.90285034310733 | 100.51100446663094 | 0.3164977331816914 | 100.0 | 0.0023257667436076632 | 20.717590816459996 |

## Monte Carlo

| candidate | cases | seed | within_pct | minus3_Hz_min | minus3_Hz_p05 | minus3_Hz_mean | minus3_Hz_p95 | minus3_Hz_max | minus3_Hz_std | peak_db_min | peak_db_p05 | peak_db_mean | peak_db_p95 | peak_db_max | peak_db_std | atten_4p5m_db_min | atten_4p5m_db_p05 | atten_4p5m_db_mean | atten_4p5m_db_p95 | atten_4p5m_db_max | atten_4p5m_db_std |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 3 | 20261003 | 66.66666666666666 | 1771576.5037370392 | 1780656.5637441985 | 1840209.901859213 | 1884246.1986096338 | 1886676.0980319672 | 60667.271105712556 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 16.909116093191056 | 16.955053883268633 | 17.342047091256617 | 17.710527467347458 | 17.748531186611974 | 0.42033201610504806 |
| TR | 3 | 20261003 | 100.0 | 1895329.1625568059 | 1903885.543126272 | 1969402.2396321006 | 2026875.4261043721 | 2031984.5880880281 | 69048.56236687924 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 22.062226799337527 | 22.10243099273369 | 22.436298408009705 | 22.750586595583094 | 22.782399691392417 | 0.36090026729731745 |
| BU | 3 | 20261003 | 100.0 | 1879471.0427950239 | 1884606.2209095592 | 1929372.1992791754 | 1973122.7403859515 | 1977822.7311021264 | 49191.88837750717 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 30.415416088496418 | 30.45180356071599 | 30.737793057574006 | 30.994734127249313 | 31.018672273533443 | 0.3037615081470124 |

## G0 secciones aisladas reales

| candidate | section | fit_f0_Hz | fit_Q | minus3_Hz | isolated_peak_db | isolated_peak_Hz |
| --- | --- | --- | --- | --- | --- | --- |
| BE | 1 | 3158457.3465586095 | 0.5054049126020127 | 2027676.043830171 | -9.643274665532871e-16 | 1000.0 |
| BE | 2 | 3486936.520708187 | 0.7973662694367442 | 3861028.1145881973 | 0.1475991107066284 | 1513561.2484363015 |
| BU | 1 | 2019319.9721294227 | 0.5401691684083981 | 1425738.7163829587 | 0.0 | 1000.0 |
| BU | 2 | 2016520.997270766 | 1.3225099352353589 | 2814720.921907379 | 2.9524158888595524 | 1698243.6524618503 |
| TR | 1 | 2572200.4956566337 | 0.5416124524183344 | 1823224.4707977686 | 0.0 | 1000.0 |
| TR | 2 | 2679919.56653413 | 0.9939105615571596 | 3396344.92098537 | 1.1012882856054345 | 1862087.1366629854 |

## G1 todas las escalas

| candidate | scale_V_div | minus3_Hz | atten_3p25m_db | atten_4p5m_db | atten_6p5m_db | peak_db | high_max_db | high_max_Hz | rebound_excess_db | gd_variation_ns |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 0.005 | 1822209.0101366471 | 9.503092100182585 | 17.48355142506528 | 30.256807202073965 | 0.0 | -17.49184983177688 | 4501252.062061655 | 0.0 | 16.059745592141326 |
| BE | 0.5 | 1821476.9968811315 | 9.5054639336011 | 17.485921694300806 | 30.259173858227676 | 0.0 | -17.494220099188084 | 4501252.062061655 | 0.0 | 19.011762300743328 |
| BU | 0.005 | 1916852.512439587 | 18.379306704577665 | 30.90129199958564 | 46.08805598008768 | 0.0 | -30.912347402651086 | 4501252.062061655 | 0.0 | 100.51100446663094 |
| BU | 0.5 | 1916541.044343259 | 18.381678538104406 | 30.903662269041504 | 46.09042263670788 | 0.0 | -30.914717670282744 | 4501252.062061655 | 0.0 | 93.53589227526157 |
| TR | 0.005 | 1951188.7226790162 | 11.809201379793267 | 22.593417325036558 | 37.14792051264003 | 0.0 | -22.603662040922092 | 4501252.062061655 | 0.0 | 28.93602266878662 |
| TR | 0.5 | 1950603.2552281262 | 11.811573213196946 | 22.59578759431627 | 37.15028716894062 | 0.0 | -22.60603230837754 | 4501252.062061655 | 0.0 | 21.965582899914864 |

## G2 flancos y cuadrada

| candidate | scale_V_div | kind | overshoot_pct | rise_ns | settling_1pct_ns | square_fall_settling_ns | u105_idle_power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 0.005 | square | 0.0008989003850157218 | 188.1540005112178 | 420.22033963141604 | 418.49785317422794 | 20.72746767828 |
| BE | 0.005 | step | 0.0009022796245483633 | 188.12487097550155 | 420.587793587103 |  | 20.71759080698 |
| BE | 0.5 | square | 0.0013923758227285532 | 188.18403209577534 | 420.6591168074462 | 418.82376439904266 | 20.7274758418 |
| BE | 0.5 | step | 0.00139277575770258 | 188.15537347742034 | 420.35058585444176 |  | 20.71759067043 |
| BU | 0.005 | square | 8.830163913068368 | 204.91133383623907 | 887.0820110945607 | 884.8654736124965 | 20.727465726355 |
| BU | 0.005 | step | 8.831188766565056 | 204.90285034310733 | 887.150316524679 |  | 20.717590816459996 |
| BU | 0.5 | square | 8.820537117673988 | 204.92618070989772 | 887.6599114940899 | 885.700966382317 | 20.727473888074996 |
| BU | 0.5 | step | 8.821697887634006 | 204.91837201555606 | 887.8122224583192 |  | 20.717590679965 |
| TR | 0.005 | square | 3.2031840962729596 | 187.1195896259928 | 549.8779254595362 | 547.8660550136115 | 20.727466492654997 |
| TR | 0.005 | step | 3.204116951341507 | 187.10619660651636 | 549.9589024671434 |  | 20.71759081272 |
| TR | 0.5 | square | 3.194032789252166 | 187.13842392523634 | 550.1311714659176 | 547.2439885905534 | 20.727474655140004 |
| TR | 0.5 | step | 3.1948769982347525 | 187.12589519665192 | 549.8396546134226 |  | 20.717590676264997 |

## G4 gran señal

| candidate | freq_Hz | amplitude_V | fundamental_pp_V | amplitude_error_pct | thd_pct | adc_min | adc_max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BE | 1000000.0 | 0.022494188436549992 | 1.9999752952089476 | -0.0012352395526216142 | 0.002725369675460312 | 0.229084655767 | 2.23090865581 |
| BE | 2000000.0 | 0.030600794596966224 | 1.999710169600766 | -0.014491519961701282 | 0.0024322853746459932 | 0.193242156578 | 2.2307924691 |
| BU | 1000000.0 | 0.020953873886196694 | 1.999992358764605 | -0.00038206176975474904 | 0.0008609894048063741 | 0.230949092232 | 2.23514497876 |
| BU | 2000000.0 | 0.030910812365104196 | 1.9997929689299094 | -0.010351553504528432 | 0.0023257667436076632 | 0.230249531965 | 2.23220860967 |
| TR | 1000000.0 | 0.021784702396580022 | 1.9999908898227645 | -0.0004555088617741454 | 0.0017235582952353696 | 0.230953556938 | 2.23093292926 |
| TR | 2000000.0 | 0.02922407173328713 | 1.999849483437938 | -0.007525828103105425 | 0.0003860228344759969 | 0.231018981799 | 2.23087097488 |

## G5 ruido

| candidate | scale_V_div | noise_uV | noise_pct_div |
| --- | --- | --- | --- |
| BE | 0.005 | 783.6337837938422 | 0.31345351351753686 |
| BE | 0.5 | 781.5568716786174 | 0.31262274867144696 |
| BU | 0.005 | 791.2443329542284 | 0.3164977331816914 |
| BU | 0.5 | 789.1534203607528 | 0.31566136814430107 |
| TR | 0.005 | 797.0301858298642 | 0.3188120743319457 |
| TR | 0.5 | 794.9103297891871 | 0.31796413191567485 |

## G6 sobrecarga

| candidate | amplitude_V | recovery_us | terminal_error_V | a_differential_V | b_differential_V | a_vip_peak_A | a_vim_peak_A | b_vip_peak_A | b_vim_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | -2 | 0.4470043993576983 | 0.001698333329091195 | 0.03381571164938535 | 0.015294529608908425 | 5.626108915818008e-05 | 5.63716116665663e-05 | 4.590457349002798e-05 | 4.588583565476966e-05 |
| BE | -4.5 | 0.46264967764976334 | 0.00519008857037595 | 0.03485041085722784 | 0.015294942473614404 | 5.6203568831379186e-05 | 5.631765294394157e-05 | 4.585895540816035e-05 | 4.58399813305338e-05 |
| BE | 2 | 0.44354667285434113 | -0.00017400412045187608 | 0.03375213058346782 | 0.01526368262484512 | 5.615096560949352e-05 | 5.626077199523772e-05 | 4.5814864808371005e-05 | 4.5796210211772075e-05 |
| BE | 4.5 | 0.4582270394110342 | -0.0036638011096765677 | 0.03480753203611098 | 0.015264108915270524 | 5.609609790446144e-05 | 5.6204437611973506e-05 | 4.57691710339887e-05 | 4.5749750509932744e-05 |
| BU | -2 | 1.0637909736194708 | 0.00169757773108703 | 0.012867704872873587 | 0.12367273813756663 | 3.751211312721936e-05 | 3.752204627262609e-05 | 3.7018958161034825e-05 | 3.699937970860957e-05 |
| BU | -4.5 | 0.9287531470767987 | 0.005189795125720487 | 0.012867957492320059 | 0.12369863139882087 | 3.7512644848359866e-05 | 3.752273459329462e-05 | 3.701984617006557e-05 | 3.70003374409845e-05 |
| BU | 2 | 1.0814786136346834 | -0.00017036089885036354 | 0.01284731102276826 | 0.12116036633813332 | 3.7439403004323874e-05 | 3.744939667689546e-05 | 3.694778341415337e-05 | 3.69279324537361e-05 |
| BU | 4.5 | 0.9267511220958339 | -0.003660618911566438 | 0.012847348768898037 | 0.12118416623573314 | 3.744061068705331e-05 | 3.7449849493746404e-05 | 3.6948549074109475e-05 | 3.6928677907730964e-05 |
| TR | -2 | 0.5694019511535552 | 0.0016978168582997277 | 0.01629753204646789 | 0.0437167638785132 | 4.7891484053543985e-05 | 4.792290716901726e-05 | 4.248667244128847e-05 | 4.246663268146445e-05 |
| TR | -4.5 | 0.7066232279009845 | 0.00518959180087708 | 0.01629799093471762 | 0.04374207469005453 | 4.784491475479103e-05 | 4.787701076922691e-05 | 4.24877427479029e-05 | 4.246778871917249e-05 |
| TR | 2 | 0.570797953221302 | -0.00017008708510801718 | 0.016270802268056994 | 0.04071797549205147 | 4.779590970960037e-05 | 4.7830015162669576e-05 | 4.240472843387808e-05 | 4.238472361295517e-05 |
| TR | 4.5 | 0.6915547757593051 | -0.0036599003577377776 | 0.016270982278879575 | 0.04074117025839197 | 4.7750558845376376e-05 | 4.778230089919557e-05 | 4.2405894651626224e-05 | 4.238589292881613e-05 |

Protegidos=11439; cambios=[].

## Método y dudas

Fuentes leídas: encargo y plan S5; plan, acta y auditoría S4;
DECISIONS del 3 oct; revision_entrada_ch1 §6; canal_rapido_ch1 §6;
models/LEEME. S4.base/stage/mid_network y S3.chain/address se reutilizan
sin modificar sus fuentes. M1, C_F1pF, DAC1.25V, R_IN/R_F10k,
R_OFF8.06k, R_ADC68, C_ADC470p y C_SH5p conservados. U103 protegido
con 470ohm/BAV99; U105 NO lleva protecciones añadidas.
Cada .meas identifica grupo, candidato, escala/POS/tap, caso MC,
estímulo, polaridad y sección reales. Modelos originales salvo G5,
que usa AD8038_ltspice_ruido_hoja en U103 y U105. Modelo AD8038
es el modelo contractual de cada mitad AD8039, no prueba física.

Síntesis: besselap(norm=mag), buttap, TR con pares de polos en orden
Q creciente, media geométrica de módulos/arimética de ángulos.
Se escalan los cuatro polos para -3dB exactos a2MHz contando polos
ideales f_RC=1/(2pi*68*470p) y10.8MHz. No se altera ninguno de los
polos fijos. C2 se recorre en E12 entre47 y220p, C1 se redondea primero
al E12 más cercano y R al E96 más cercano entre499 y2490ohm. Se
minimiza error de Q, luego f0 y se favorece C2 mayor en empate.
Se informa f0/Q por pasivos, y ajuste biquad del AC aislado real con
1p de pista en IN+. No se retoca la síntesis después de la campaña.

G1/G3: 300puntos/década,1kHz..200MHz. H=V(ADC1)/V(BNC), normalizada
a1kHz (acoplo DC). Atenuaciones por interpolación log-frecuencia.
Pico se mide en1k..2MHz; máximo alta frecuencia en>4.5..200MHz.
Retardo de grupo por derivada de fase desenrollada: variación1k..2MHz;
0..1kHz no se simula, se informa esta limitación del barrido contractual.
C4 compara máximo alta frecuencia contra H(4.5MHz), sin ocultar rebote.
G3:200casos/candidato, semilla20261003, numpy default_rng, uniforme
independiente ±1% en cuatro R y±5% en cuatro C del filtro. Mismos
ocho factores por índice entre candidatos (comparación pareada).
Los polos fijos,1p de pista y S1-S4 no se aleatorizan. Distribuciones
de corte/pico/A4.5, componentes reales y factores recuperables en CSV.

G2: escalón1div positivo,2ns; cuadrada100kHz de4div pp,centrada
(±2div),2ns. Dos escalas5mV y0.5V/div. Normalización con signo de
la cadena inversora; subida al primer cruce10/90%; overshoot y última
violación de±1% respecto a meseta4..5us. Resolución<=1ns.
G6: BNC impuesta±2/±4.5V,10us,flancos10ns; recuperación desde final
de bajada11.02us hasta permanecer en±0.1div de la salida inicial;
ventana30us. Se conserva censura si no recupera. Diferencial y ambas
corrientes por U105A/B con sensores ideales0V,sin diodos añadidos.
G4: seno1/2MHz,offset0,DAC1.25; fuente calculada desde G1 para2Vpp
(8div) en pin ADC. THD armónicos2..9,ventana20..40us coherente,
131072puntos interpolados del raw<=0.5ns. Se informa amplitud real.
G5: integral ONOISE1Hz..3.15MHz en pin ADC,por trapecios de densidad
al cuadrado y extremo interpolado; porcentaje sobre0.25V/div.
C_SH5p estático permanece después del pin; no hay kickback S6.
Consumo U105 por sensores de ambos rieles en reposo; incluye macro,
no garantía del consumo real. Corrientes de entrada del AD8038
macro no representan toda la Ib de400nA ni daños por sobrecarga.

Contradicciones conservadas: E17 antiguo menciona Butterworth5º y
pérdidaS3 -0.97dB; contratoS5 exige tres filtros4º activos y usa
S4 real más RC sin cambiar S1-S4. Tablaideal omite la pequeña pérdida
S1-S3; cadena real la incluye. RLOAD1k/CLOAD10p heredados de S3/S4
eran sustitutos de carga; permanecen en U103B además del filtro,
por prohibición de cambiar la cadena. El poloS4 de10.8MHz es una
aproximación ideal para síntesis: la campaña conserva el macromodelo
completo,cargaADC y5p estáticos. Fuentes VREF yDAC ideales no
certifican ruidoREF3325/DAC. No se resuelven discrepancias acta/auditoría
S4 ni se elige candidato. Sin descargas,ni cambios deSTATE/DECISIONS.

## Reejecución

En CH1_entrada: python sintesis_s5.py; python ejecutar_s5.py --controls;
python ejecutar_s5.py --smoke; python ejecutar_s5.py.
En copia: fijar S3G4_MODELS a modelos originales (sólo lectura).
Diez trabajadores desdeG0. CSV con columnas fijas ordenadas y filas
porID; .cir/.log conservados, raw exitosos regenerables eliminados.
Registros bajoS5 (excluido) o fuera deCH1_entrada. HuellasSHA256
antes/después de fuentes/modelos/S1-S4/STATE/DECISIONS.
Código0=ejecución completa,sin implicar aprobación eléctrica.
