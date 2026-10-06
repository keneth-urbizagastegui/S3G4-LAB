# ACTA S2b — entrada P4b

Código 0; 120 simulaciones; 0 errores; 0 advertencias; 69.206 s; 10 trabajadores.

| criterion | buffer | value | status |
| --- | --- | --- | --- |
| S2b-C1 | OPA810 | Zin error 0.085388%; Cin 24.443517–24.832964 pF; delta 0.389447 pF; gain 0.187737%; flat 0.084306%; peak 0.001354 dB; fc 8.814669 Hz | PASA |
| S2b-C1 | OPA828 | Zin error 0.092912%; Cin 30.879287–31.297180 pF; delta 0.417893 pF; gain 0.541745%; flat 0.343764%; peak 0.001303 dB; fc 8.783539 Hz | FALLA |
| S2b-C2 | OPA810 | req_v=99.0122; 0.990122 times derated limit (e5b_opa810_pos100_cplac_pwr1_bleed0_sine100_t25_50ohm_real_contact) | PASA |
| S2b-C2 | OPA828 | req_v=99.0119; 0.990119 times derated limit (e5b_opa828_pos100_cpldc_pwr1_bleed0_neg100_t25_50ohm_real_contact) | PASA |
| S2b-C3 | OPA810 | rail excess 0.838447 V; input 0.000962578 mA; diff 0.886076 V / 7 V | FALLA |
| S2b-C3 | OPA828 | rail excess 0.544754 V; input 0.211425 mA; diff 4.04476 V / 9.95342 V | FALLA |
| S2b-C4 | GENERATOR | four points at 4 and 8 kV; see calibration CSV | PASA |
| S2b-C5 | OPA810 | BAV max I2t 3.41302 microA2s / 8; input 5.6777 mA; diff 4.40066 V; OFF macro unvalidated | PASA |
| S2b-C5 | OPA828 | BAV max I2t 3.58749 microA2s / 8; input 6.17061 mA; diff 4.08432 V; OFF macro unvalidated | PASA |

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
| OPA810 | E7b | 100 | 1 | 0 | real | 4kv | contact | 0.0717714251918521 | 2.4422552353751193e-08 | 4.93169079533 | 0.00516170335387 | 4.74678894924 | 4.05023375682 |
| OPA810 | E7b | 100 | 1 | 0 | real | 8kv | air | 0.17469807854727676 | 2.6764651729543406e-08 | 5.02020965706 | 0.00550582771047 | 4.79053793586 | 4.12310099561 |
| OPA810 | E7b | 100 | 1 | 0 | real | 8kv | contact | 0.366948584920794 | 4.0921280375202326e-08 | 11.8129304002 | 0.00918219302462 | 5.252344985300001 | 4.21884919381 |
| OPA810 | E7b | 100 | 1 | 0 | real | -4kv | contact | 2.4431836501945432e-08 | 0.07176393962831795 | 0.0051615276154 | 4.93129938934 | 4.74789824496 | 4.05167231781 |
| OPA810 | E7b | 100 | 1 | 0 | real | -8kv | contact | 4.093039818434713e-08 | 0.3669454515034578 | 0.00918136265555 | 11.8127813906 | 5.25346908746 | 4.22037535334 |
| OPA810 | E7b | 1 | 1 | 0 | real | 4kv | contact | 3.4130140520382803 | 3.5268174519920043e-07 | 14.8598875399 | 0.0882072037982 | 5.6762354641999995 | 4.39915966424 |
| OPA810 | E7b | 1 | 1 | 0 | real | 4kv | contact | 3.4130140520382803 | 3.526817451992532e-07 | 14.8598875399 | 0.0882072037982 | 5.6762354641999995 | 4.39915966424 |
| OPA810 | E7b | 1 | 1 | 0 | real | 8kv | air | 6.964603876786193 | 4.86142171732264e-07 | 14.7524761891 | 0.119778813589 | 5.79825392296 | 4.50975992894 |
| OPA810 | E7b | 1 | 1 | 0 | real | 8kv | contact | 13.673702090624907 | 5.045711067483556e-07 | 29.7458103527 | 0.125244463073 | 5.91249396866 | 4.77118332631 |
| OPA810 | E7b | 1 | 1 | 0 | real | -4kv | contact | 3.528192872983975e-07 | 3.413015246364401 | 0.0882254450873 | 14.8598770885 | 5.67770412774 | 4.40066355258 |
| OPA810 | E7b | 1 | 1 | 0 | real | -8kv | contact | 5.047978590960172e-07 | 13.673700675722136 | 0.125260058648 | 29.745857112 | 5.91384349798 | 4.77271085925 |
| OPA828 | E7b | 100 | 1 | 0 | real | 4kv | contact | 0.052929221795050274 | 2.021619428668866e-08 | 3.48566492509 | 0.00426958396685 | 5.52715693997 | 4.0583794313 |
| OPA828 | E7b | 100 | 1 | 0 | real | 8kv | air | 0.13371350284448502 | 2.166748612285882e-08 | 3.66231384923 | 0.00450510788142 | 5.53609061555 | 4.06217011512 |
| OPA828 | E7b | 100 | 1 | 0 | real | 8kv | contact | 0.2736237903321876 | 3.501778778438249e-08 | 9.28476063313 | 0.00773310765067 | 5.92144355824 | 4.06051302442 |
| OPA828 | E7b | 100 | 1 | 0 | real | -4kv | contact | 2.0223115473561657e-08 | 0.052926849843992256 | 0.00426953930541 | 3.485001758 | 5.52846394554 | 3.05841327276 |
| OPA828 | E7b | 100 | 1 | 0 | real | -8kv | contact | 3.503869795744593e-08 | 0.2736099081971681 | 0.00772908036821 | 9.28438298677 | 5.92283846412 | 3.06117675891 |
| OPA828 | E7b | 1 | 1 | 0 | real | 4kv | contact | 3.587429859299947 | 3.532475921267301e-07 | 14.9246943913 | 0.0884024521253 | 6.1692084383 | 4.0843231772 |
| OPA828 | E7b | 1 | 1 | 0 | real | 8kv | air | 7.320702025389447 | 4.878234281659166e-07 | 14.812701555 | 0.119730573514 | 6.2662704964 | 4.08909454621 |
| OPA828 | E7b | 1 | 1 | 0 | real | 8kv | contact | 14.374942279534448 | 5.063823123994372e-07 | 29.8775456349 | 0.125227278037 | 6.87527838944 | 4.10544320924 |
| OPA828 | E7b | 1 | 1 | 0 | real | -4kv | contact | 3.5341245886543416e-07 | 3.587490975983156 | 0.0884095662708 | 14.9249888664 | 6.1706101575300005 | 3.08091331777 |
| OPA828 | E7b | 1 | 1 | 0 | real | -8kv | contact | 5.065852256319869e-07 | 14.375008309153737 | 0.125234261258 | 29.877730686 | 6.87665915264 | 3.14778109082 |
| OPA810 | E7c | 100 | 0 | 0 | off_load_only | 4kv | contact | 0.10372955534810048 | 5.056871240582964e-09 | 6.05834077802 | 0.00467489135009 | 1.1590587092e-15 | 1.15907330136 |
| OPA810 | E7c | 100 | 0 | 0 | real | 4kv | contact | 0.10603331984059663 | 2.2433300792524524e-09 | 6.07754432818 | 0.00247923616117 | 0.5083771443740001 | 0.375437225741 |
| OPA810 | E7c | 100 | 0 | 0 | off_load_only | 8kv | air | 0.2086645231078357 | 6.38869467347966e-09 | 6.18440660966 | 0.00590850559674 | 1.60819792948e-15 | 1.60821846328 |
| OPA810 | E7c | 100 | 0 | 0 | real | 8kv | air | 0.21151543376575838 | 2.8401503725148898e-09 | 6.21959992682 | 0.00343341157716 | 0.531434776913 | 0.448500319839 |
| OPA810 | E7c | 100 | 0 | 0 | off_load_only | -4kv | contact | 5.056323372558783e-09 | 0.10372712913839784 | 0.00467489135009 | 6.05818781077 | 1.15916458832e-15 | 1.15907363366 |
| OPA810 | E7c | 100 | 0 | 0 | real | -4kv | contact | 2.2434717825441408e-09 | 0.10603530662099732 | 0.00247923494754 | 6.07763824501 | 0.508385701334 | 0.373448665615 |
| OPA810 | E7c | 100 | 0 | 1 | off_load_only | 4kv | contact | 0.1037297915134231 | 5.056870987782128e-09 | 6.05834078904 | 0.00467489134884 | 1.15916458832e-15 | 1.1590733014 |
| OPA810 | E7c | 100 | 0 | 1 | real | 4kv | contact | 0.10603600337264545 | 2.242435911884456e-09 | 6.07772816658 | 0.00247805772894 | 0.508442682232 | 0.375457256541 |
| OPA810 | E7c | 100 | 0 | 1 | off_load_only | 8kv | air | 0.2086656050304243 | 6.3886913037290305e-09 | 6.18440660139 | 0.00590850559411 | 1.58437512784e-15 | 1.58430356117 |
| OPA810 | E7c | 100 | 0 | 1 | real | 8kv | air | 0.21151452673283 | 2.8389094221357493e-09 | 6.21959782278 | 0.00343103922557 | 0.5314891518839999 | 0.448620018681 |
| OPA810 | E7c | 100 | 0 | 1 | off_load_only | -4kv | contact | 5.0563226734187506e-09 | 0.10372736551486289 | 0.00467489134884 | 6.05818789502 | 1.1590587092e-15 | 1.15907363501 |
| OPA810 | E7c | 100 | 0 | 1 | real | -4kv | contact | 2.242632905457234e-09 | 0.10603440909304344 | 0.00247805651828 | 6.07761405943 | 0.508434876092 | 0.373454486413 |
| OPA810 | E7c | 100 | 0 | 2 | off_load_only | 4kv | contact | 0.10374150114337247 | 5.056866580852581e-09 | 6.05834082058 | 0.00467489134884 | 1.15916458832e-15 | 1.15907328155 |
| OPA810 | E7c | 100 | 0 | 2 | real | 4kv | contact | 0.10468658306435377 | 3.834350547134003e-09 | 6.06670946337 | 0.00410532169549 | 0.735580083653 | 0.861459312264 |
| OPA810 | E7c | 100 | 0 | 2 | off_load_only | 8kv | air | 0.20871783798212976 | 6.388678632291816e-09 | 6.18440662674 | 0.00590850559408 | 1.16001162126e-15 | 1.15999479473 |
| OPA810 | E7c | 100 | 0 | 2 | real | 8kv | air | 0.2098440000274145 | 4.870711816052803e-09 | 6.19925527086 | 0.00530015226541 | 0.768643300552 | 0.940860483268 |
| OPA810 | E7c | 100 | 0 | 2 | off_load_only | -4kv | contact | 5.056318260079549e-09 | 0.10373907512613478 | 0.00467489134884 | 6.05818792256 | 1.15916458832e-15 | 1.1590736148 |
| OPA810 | E7c | 100 | 0 | 2 | real | -4kv | contact | 3.8305374102562235e-09 | 0.1046831735639891 | 0.00410340770417 | 6.0660691277 | 0.7350637602719999 | 0.829738122253 |
| OPA828 | E7c | 100 | 0 | 0 | off_load_only | 4kv | contact | 0.0785182057716661 | 4.318763337466514e-09 | 4.85028673324 | 0.00410171037302 | 1.12835376486e-15 | 1.12832599028 |
| OPA828 | E7c | 100 | 0 | 0 | real | 4kv | contact | 0.08049941918132954 | 2.658322296330888e-08 | 4.87453901109 | 0.0172294371827 | 0.5124726647829999 | 0.0125973687218 |
| OPA828 | E7c | 100 | 0 | 0 | off_load_only | 8kv | air | 0.16093408039109336 | 5.4070421118884484e-09 | 4.90506096613 | 0.00513004822544 | 1.60459803945e-15 | 1.60453081624 |
| OPA828 | E7c | 100 | 0 | 0 | real | 8kv | air | 0.16313613214055686 | 3.599303159117091e-08 | 4.94868720261 | 0.0258864750117 | 0.5139511463419999 | 0.0233859662473 |
| OPA828 | E7c | 100 | 0 | 0 | off_load_only | -4kv | contact | 4.318122243617347e-09 | 0.0785192165900033 | 0.00410171037302 | 4.85036921046 | 1.12835376486e-15 | 1.12832599357 |
| OPA828 | E7c | 100 | 0 | 0 | real | -4kv | contact | 2.6582754747522777e-08 | 0.08049941863153688 | 0.0172294267731 | 4.87453901385 | 0.512472649906 | 0.0126216876358 |
| OPA828 | E7c | 100 | 0 | 1 | off_load_only | 4kv | contact | 0.07851836043576153 | 4.318762337850665e-09 | 4.85028782284 | 0.00410171037171 | 1.1195657980299999e-15 | 1.11957541687 |
| OPA828 | E7c | 100 | 0 | 1 | real | 4kv | contact | 0.08049899827112775 | 2.6141550621994937e-08 | 4.87463377 | 0.0170900348869 | 0.512660485383 | 0.0127259521998 |
| OPA828 | E7c | 100 | 0 | 1 | off_load_only | 8kv | air | 0.16093517369310884 | 5.407041730025363e-09 | 4.90505903884 | 0.00513004822307 | 1.58003408398e-15 | 1.57998880097 |
| OPA828 | E7c | 100 | 0 | 1 | real | 8kv | air | 0.1631344842508344 | 3.540708545884262e-08 | 4.94867410377 | 0.0256399706035 | 0.5140729263580001 | 0.0235937960462 |
| OPA828 | E7c | 100 | 0 | 1 | off_load_only | -4kv | contact | 4.318121915445746e-09 | 0.07851945664753895 | 0.00410171037171 | 4.85036920821 | 1.1195657980299999e-15 | 1.11957541689 |
| OPA828 | E7c | 100 | 0 | 1 | real | -4kv | contact | 2.614109065874542e-08 | 0.0804989978015646 | 0.0170900243294 | 4.87463377059 | 0.512660494184 | 0.0127502811054 |
| OPA828 | E7c | 100 | 0 | 2 | off_load_only | 4kv | contact | 0.07853011282208165 | 4.318758117511724e-09 | 4.85028773001 | 0.00410171037171 | 1.08748442516e-15 | 1.08747145771 |
| OPA828 | E7c | 100 | 0 | 2 | real | 4kv | contact | 0.0802809720462105 | 2.0351673462292993e-09 | 4.87254519381 | 0.00277464278203 | 0.549761071118 | 0.0872330159311 |
| OPA828 | E7c | 100 | 0 | 2 | off_load_only | 8kv | air | 0.16098769952976644 | 5.40702943735384e-09 | 4.90505906142 | 0.00513004822306 | 1.11617766624e-15 | 1.11602347694 |
| OPA828 | E7c | 100 | 0 | 2 | real | 8kv | air | 0.1628365097061845 | 2.627158309885545e-09 | 4.94495243242 | 0.00406873736061 | 0.550632591617 | 0.157190002309 |
| OPA828 | E7c | 100 | 0 | 2 | off_load_only | -4kv | contact | 4.3181176198892506e-09 | 0.07853120268685358 | 0.00410171037171 | 4.85036923249 | 1.08748442516e-15 | 1.08747762121 |
| OPA828 | E7c | 100 | 0 | 2 | real | -4kv | contact | 2.0351625244708185e-09 | 0.08028034035077537 | 0.00277462071094 | 4.87246812182 | 0.549757670496 | 0.0872327677333 |

µA²s en las columnas I2t significa 10⁻⁶ A²·s, no (µA)²·s. Límite por diodo: 50% de 4²·1µs = 8·10⁻⁶ A²·s.

## R/C en E5b

| buffer | part | voltage_V | voltage_limit_V | power_W | power_limit_W |
| --- | --- | --- | --- | --- | --- |
| OPA810 | rt1 | 49.5045997481 | 100.0 | 0.00446394380936 | 0.125 |
| OPA810 | rt2 | 49.5045997481 | 100.0 | 0.00446394380936 | 0.125 |
| OPA810 | rb | 0.991884580703 | 75.0 | 8.94395474034e-05 | 0.0625 |
| OPA810 | rs1 | 47.1279051871 | 100.0 | 0.0445098085637 | 0.125 |
| OPA810 | rs2 | 47.1279051871 | 100.0 | 0.0445098085637 | 0.125 |
| OPA810 | req | 99.0121530395 | 100.0 | 0.000980334854753 | 0.125 |
| OPA810 | rbias | 5.81598367877 | 75.0 | 3.30117066346e-06 | 0.0625 |
| OPA810 | rprot | 0.000962577659194 | 75.0 | 3.27126760031e-11 | 0.0625 |
| OPA810 | ct1 | 49.5045997481 | 80.0 |  |  |
| OPA810 | ct2fixed | 49.5045997481 | 80.0 |  |  |
| OPA810 | ct2trim | 49.5045997481 | 80.0 |  |  |
| OPA810 | cb | 0.991884580703 | 40.0 |  |  |
| OPA810 | cs | 94.2558103743 | 160.0 |  |  |
| OPA810 | cac | 5.74801699384 | 40.0 |  |  |
| OPA810 | ceq | 99.0121530395 | 160.0 |  |  |
| OPA828 | rt1 | 49.5045972909 | 100.0 | 0.00446394381227 | 0.125 |
| OPA828 | rt2 | 49.5045972909 | 100.0 | 0.00446394381227 | 0.125 |
| OPA828 | rb | 0.991884580703 | 75.0 | 8.94395474034e-05 | 0.0625 |
| OPA828 | rs1 | 47.1338113119 | 100.0 | 0.0445209653063 | 0.125 |
| OPA828 | rs2 | 47.1338113119 | 100.0 | 0.0445209653063 | 0.125 |
| OPA828 | req | 99.0118606407 | 100.0 | 0.000980334854753 | 0.125 |
| OPA828 | rbias | 5.73324846372 | 75.0 | 3.28701379467e-06 | 0.0625 |
| OPA828 | rprot | 0.211425265227 | 75.0 | 4.47006427762e-05 | 0.0625 |
| OPA828 | ct1 | 49.5045972909 | 80.0 |  |  |
| OPA828 | ct2fixed | 49.5045972909 | 80.0 |  |  |
| OPA828 | ct2trim | 49.5045972909 | 80.0 |  |  |
| OPA828 | cb | 0.991884580703 | 40.0 |  |  |
| OPA828 | cs | 94.2676226238 | 160.0 |  |  |
| OPA828 | cac | 5.74623484799 | 40.0 |  |  |
| OPA828 | ceq | 99.0118606407 | 160.0 |  |  |

## Cierre de integral 2 frente a 4ms

| diode | I2t_2ms | I2t_4ms | relative_change |
| --- | --- | --- | --- |
| dhp | 3.41300167039e-06 | 3.41300167039e-06 | 0.0 |
| dlp | 3.51697234886e-13 | 3.51697234886e-13 | 0.0 |

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

## Lectura de resultados y contradicciones medidas

OPA810: C3 falla por tensión en `e5b_opa810_pos1_cplac_pwr1_bleed0_sine100_t25_50ohm_real_contact`: 0.838447317 V más allá del riel frente a 0.5 V. No se convierte la corriente pequeña en permiso para superar el máximo de tensión.

OPA810, apagado: exceso máximo de |diferencial| frente al span instantáneo de alimentación = 0.606629385 V. El C5 contractual del OPA810 usa 7 V, pero su hoja pide min(7 V, span); esta discrepancia queda abierta y el macro sin alimentación no valida supervivencia.

E9 OPA810: offset referido a BNC, ×1/DC, 50 Ω y 25 °C = 0.0760533532 mV. Resto de estados y deriva en CSV; comparación por estado en s2b_segunda_fuente.csv.

OPA828: C3 falla por tensión en `e5b_opa828_pos1_cpldc_pwr1_bleed0_100_t25_50ohm_real_contact`: 0.544753841 V más allá del riel frente a 0.5 V. No se convierte la corriente pequeña en permiso para superar el máximo de tensión.

OPA828, apagado: exceso máximo de |diferencial| frente al span instantáneo de alimentación = -0.619971387 V. El C5 contractual del OPA810 usa 7 V, pero su hoja pide min(7 V, span); esta discrepancia queda abierta y el macro sin alimentación no valida supervivencia.

E9 OPA828: offset referido a BNC, ×1/DC, 50 Ω y 25 °C = 0.020896129 mV. Resto de estados y deriva en CSV; comparación por estado en s2b_segunda_fuente.csv.

I²t máximos por diodo sobre todos los estados ensayados (incluidas variantes apagadas); unidades 10⁻⁶ A²·s, límite reducido 8.

| buffer | level | DHP_I2t_micro_A2s | DLP_I2t_micro_A2s |
| --- | --- | --- | --- |
| OPA810 | ±4 kV contacto | 3.4130140520382803 | 3.413015246364401 |
| OPA810 | ±8 kV contacto | 13.673702090624907 | 13.673700675722136 |
| OPA810 | +8 kV aire | 6.964603876786193 | 4.86142171732264e-07 |
| OPA828 | ±4 kV contacto | 3.587429859299947 | 3.587490975983156 |
| OPA828 | ±8 kV contacto | 14.374942279534448 | 14.375008309153737 |
| OPA828 | +8 kV aire | 7.320702025389447 | 4.878234281659166e-07 |

±8 kV en contacto supera el límite reducido por diodo; +8 kV aire queda por debajo en esta aproximación. El nivel contractual C5 es ±4 kV contacto. OPA828 tiene diferencial dentro de su hoja en los estados simulados, pero falla el nominal por Cin >30 pF y error de ganancia >0.5%, y falla C3 por tensión. No se acepta como sustituto directo.

La auditoría de S2 atribuía la excursión de tensión sólo a ESD; E5b muestra un exceso también en continuo. Se conserva el hallazgo sin cambiar el diseño. C.6 del documento vivo aún dice C_S de 100 V y valores de partida: se aplican las decisiones del 3 oct y el contrato S2b, sin editar ese documento.
