# S7b — CH1, tolerancias reales

{"returncode": 0, "simulations": 128, "logical_cases": 80, "successful": 80, "seconds": 890.3135114999895, "workers": 10, "smoke": true, "preflight": false, "seed": 2026100371, "protected_changed": [], "protected_count": 13319}

| criterion | scope | N | pass_count | fraction | status |
| --- | --- | --- | --- | --- | --- |
| S7b-C1 | 0.005 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C2 | 0.005 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C1 | 0.005 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C2 | 0.005 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C1 | 0.05 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C2 | 0.05 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C1 | 0.5 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C2 | 0.5 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C1 | 0.5 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C2 | 0.5 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C1 | 5.0 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C2 | 5.0 V/div MC | 3 | 3 | 1.0 | PASA |
| S7b-C3 | 0.005 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C3 | 0.005 V/div MC | 2 | 2 | 1.0 | PASA |
| S7b-C3 | 0.5 V/div nominal | 1 | 1 | 1.0 | PASA |
| S7b-C3 | 0.5 V/div MC | 2 | 2 | 1.0 | PASA |
| S7b-C4 | 0.005 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C4 | 0.05 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C4 | 0.5 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C4 | 5.0 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C5 | placas únicas | 3 | 3 | 1.0 | PASA |
| S7b-C6 | casos deterministas K3; no estimador de placas | 12 | 12 | 1.0 | PASA |
| S7b-C7 | casos nominales K4; no estimador de placas | 10 | 10 | 1.0 | PASA |
| S7b-C8 | 0.005 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C8 | 0.05 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C8 | 0.5 V/div | 3 | 3 | 1.0 | PASA |
| S7b-C8 | 5.0 V/div | 3 | 3 | 1.0 | PASA |

## K1 por escala

| scale_V_div | minus3_Hz | peak_db | gain_dc_signed | rise_ns | noise_pct_div | atten_4p5m_db |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 2007647.063619549 | 1.741861881050446e-05 | -49.498204366691645 | 182.05827863774803 | 0.32164412915359325 | 21.699597410789288 |
| 0.5 | 2006843.2901978297 | 1.771334399799645e-05 | -0.49532556828858626 | 182.08563157364756 | 0.3218227877422076 | 21.70273684683138 |

## Monte Carlo

| scale_V_div | metric | N | min | p2p5 | median | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.005 | minus3_Hz | 3 | 1990612.1631355532 | 1990777.9799787016 | 1993928.4999985187 | 2082425.3100001046 | 2087083.0368422933 |
| 0.005 | peak_db | 3 | 0.004294234213305165 | 0.004390983460318128 | 0.006229219153564418 | 0.009141608036505705 | 0.009294891661923668 |
| 0.005 | atten_4p5m_db | 3 | 21.397059514881267 | 21.413744376356608 | 21.730756744388064 | 22.091204086206787 | 22.110174998934088 |
| 0.005 | gain_dc_signed | 3 | -49.05039609285033 | -49.0221966785049 | -48.48640780594175 | -48.186983262878705 | -48.1712240764017 |
| 0.005 | gain_error_pct | 3 | -3.657551847196605 | -3.6260334742426 | -3.0271843881164995 | -1.9556066429901997 | -1.8992078142993418 |
| 0.005 | offset_uncal_V | 3 | -0.10947119069404487 | -0.10394769088525313 | 0.0009988054817899883 | 0.04102552499286729 | 0.04313219444081873 |
| 0.005 | dac_center_V | 3 | 1.1601437570865272 | 1.1646770564959479 | 1.2508097452749407 | 1.2826197382040685 | 1.2842939483582332 |
| 0.005 | position_plus_div | 3 | 4.678943918317609 | 4.7042275117325785 | 5.1846157866170035 | 5.441437058133893 | 5.454953967161098 |
| 0.005 | position_minus_div | 3 | 4.90528387056861 | 4.905547261265958 | 4.910551684515561 | 4.926391019018303 | 4.927224668202658 |
| 0.005 | noise_pct_div | 2 | 0.31185404810008244 | 0.3119183343173393 | 0.3131397724452193 | 0.31436121057309924 | 0.3144254967903561 |
| 0.05 | minus3_Hz | 3 | 1990511.8374848964 | 1990674.4667067511 | 1993764.421921991 | 2082338.4586911767 | 2087000.2501000813 |
| 0.05 | peak_db | 3 | 0.004380393475195393 | 0.004477170979520901 | 0.006315943561705548 | 0.00922583050666379 | 0.009378982451135276 |
| 0.05 | atten_4p5m_db | 3 | 21.39902497914618 | 21.415694402179547 | 21.732413439813488 | 22.09453141353179 | 22.113590254253808 |
| 0.05 | gain_dc_signed | 3 | -4.9078390152749245 | -4.904534620424026 | -4.841751118256957 | -4.806160239353378 | -4.804287035200558 |
| 0.05 | gain_error_pct | 3 | -3.914259295988831 | -3.876795212932433 | -3.164977634860866 | -1.9093075915194757 | -1.8432196945015078 |
| 0.05 | offset_uncal_V | 3 | -0.09924711803375175 | -0.09354903413390477 | 0.014714559963187934 | 0.07137846667822435 | 0.07436077755796311 |
| 0.05 | dac_center_V | 3 | 1.1685358897627578 | 1.1732055600327862 | 1.2619292951633265 | 1.3067637538002854 | 1.309123462149599 |
| 0.05 | position_plus_div | 3 | 4.7198402089594005 | 4.745822138738583 | 5.239478804543042 | 5.562848824875254 | 5.579868299629581 |
| 0.05 | position_minus_div | 3 | 4.890102470742499 | 4.89091797103299 | 4.9064124765523145 | 4.924996890110785 | 4.925975017140178 |
| 0.5 | minus3_Hz | 3 | 1987095.957352022 | 1987307.6618462757 | 1991330.0472370945 | 2080466.5839936293 | 2085157.980665026 |
| 0.5 | peak_db | 3 | 4.492276967405743e-05 | 5.372672711531388e-05 | 0.0002210019184991864 | 0.0007018516164647311 | 0.000727159495305023 |
| 0.5 | atten_4p5m_db | 3 | 21.410234996849994 | 21.42666396393113 | 21.738814338472725 | 22.101573148129035 | 22.120665717058316 |
| 0.5 | gain_dc_signed | 3 | -0.49056489901256284 | -0.4902829787353235 | -0.4849264934677765 | -0.48189748506037894 | -0.4817380635652527 |
| 0.5 | gain_error_pct | 3 | -3.6523872869494545 | -3.6205029879242168 | -3.0147013064447004 | -1.9434042529352957 | -1.8870201974874323 |
| 0.5 | offset_uncal_V | 3 | -0.10947887562578895 | -0.10395537313272174 | 0.000991174235555281 | 0.041017289392941865 | 0.04312392703280432 |
| 0.5 | dac_center_V | 3 | 1.1601374491338212 | 1.1646707546030886 | 1.2508035585191677 | 1.282613184204634 | 1.2842873750301849 |
| 0.5 | position_plus_div | 3 | 4.6789131785906335 | 4.704196782742706 | 5.1845852616320744 | 5.441404115734191 | 5.454920897529039 |
| 0.5 | position_minus_div | 3 | 4.905286764982653 | 4.905550115330077 | 4.910553771931144 | 4.92639198718819 | 4.927225577464876 |
| 0.5 | noise_pct_div | 2 | 0.3120324914043843 | 0.31209752061634 | 0.3133330756434979 | 0.31456863067065577 | 0.31463365988261144 |
| 5.0 | minus3_Hz | 3 | 1986996.133498836 | 1987204.6554707142 | 1991166.5729364005 | 2080379.9464718206 | 2085075.387184211 |
| 5.0 | peak_db | 3 | 6.674631993027687e-05 | 7.600238049966913e-05 | 0.0002518675313181224 | 0.0007438508049358774 | 0.000769744661442075 |
| 5.0 | atten_4p5m_db | 3 | 21.41220050856532 | 21.428614037690803 | 21.740471091074983 | 22.104900534086376 | 22.124081031086977 |
| 5.0 | gain_dc_signed | 3 | -0.04908448735364142 | -0.04905145017450427 | -0.04842374377089842 | -0.04806436057411422 | -0.04804544566902032 |
| 5.0 | gain_error_pct | 3 | -3.9091086619593707 | -3.87127885177156 | -3.1525124582031605 | -1.8970996509914695 | -1.83102529271717 |
| 5.0 | offset_uncal_V | 3 | -0.09924788447730659 | -0.093549800433157 | 0.014713796405685153 | 0.07137764421829128 | 0.07435995199790213 |
| 5.0 | dac_center_V | 3 | 1.1685352606498576 | 1.173204931424205 | 1.261928676136808 | 1.306763099274649 | 1.3091228057555881 |
| 5.0 | position_plus_div | 3 | 4.719837143185163 | 4.745819073541556 | 5.239475750313021 | 5.562845535035531 | 5.579864997389347 |
| 5.0 | position_minus_div | 3 | 4.890103042792937 | 4.890918527224531 | 4.9064127314248145 | 4.924996994814422 | 4.925975113940191 |

## Recuperación

| scale_V_div | amplitude_V | recovery_us | bav199_conducts |
| --- | --- | --- | --- |
| 0.005 | 0.2 | 0.551688489360655 | False |
| 0.005 | 2 | 0.5625667919249963 | False |
| 0.005 | 4.5 | 0.568376914344862 | False |
| 0.005 | -0.2 | 0.549499672028484 | False |
| 0.005 | -2 | 0.5608172090459268 | False |
| 0.005 | -4.5 | 0.5670142763721917 | False |
| 0.5 | 20 | 0.5485943107224954 | False |
| 0.5 | 40 | 0.654947129951127 | False |
| 0.5 | -20 | 0.5485735781462273 | False |
| 0.5 | -40 | 0.6716356255901114 | False |

## Offset nominal

| scale_V_div | vdac_V | center_V | offset_div |
| --- | --- | --- | --- |
| 0.005 | 0.2 | 2.533697905117435 | 5.210904446321599 |
| 0.005 | 0.46249999999999997 | 2.20801637722232 | 3.908178334741139 |
| 0.005 | 0.7249999999999999 | 1.8823348493271979 | 2.6054522231606514 |
| 0.005 | 0.9874999999999998 | 1.5566533214320857 | 1.3027261115802027 |
| 0.005 | 1.2499999999999998 | 1.2309717935370283 | -2.6645352591003757e-14 |
| 0.005 | 1.5124999999999997 | 0.905290265641913 | -1.3027261115804882 |
| 0.005 | 1.7749999999999997 | 0.579608737746859 | -2.6054522231607042 |
| 0.005 | 2.0374999999999996 | 0.2539272098517436 | -3.908178334741166 |
| 0.005 | 2.3 | 0.02077284567231568 | -4.840795791458877 |
| 0.5 | 0.2 | 2.533689103520981 | 5.210904446321599 |
| 0.5 | 0.46249999999999997 | 2.208007575625872 | 3.908178334741164 |
| 0.5 | 0.7249999999999999 | 1.8823260477307278 | 2.6054522231605866 |
| 0.5 | 0.9874999999999998 | 1.5566445198356382 | 1.3027261115802284 |
| 0.5 | 1.2499999999999998 | 1.2309629919405742 | -2.7533531010703882e-14 |
| 0.5 | 1.5124999999999997 | 0.9052814640454557 | -1.3027261115805016 |
| 0.5 | 1.7749999999999997 | 0.5795999361504082 | -2.605452223160692 |
| 0.5 | 2.0374999999999996 | 0.25391840825529927 | -3.9081783347411276 |
| 0.5 | 2.3 | 0.02077240728150345 | -4.840762338636311 |

## Protecciones en extremos

| scale_V_div | POS | CPL | dc_limit_V | rail_plus_set_V | rail_minus_set_V | adc_min_V | adc_max_V | mux_low_margin_V | mux_high_margin_V | mux_supply_max_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 1 | 0 | 100.0 | 4.8 | 4.8 | 0.006917769358147539 | 3.288631941995905 | 0.14886557224541086 | 0.14566614768148867 | 9.555258479551721 |
| 0.005 | 1 | 0 | 100.0 | 4.8 | 5.0 | 0.0069177831605922785 | 3.288983863716602 | 0.1515807346371556 | 0.1459044534791456 | 9.754481436103289 |
| 0.005 | 1 | 0 | 100.0 | 5.0 | 4.8 | 0.0068783309270280465 | 3.28863183490808 | 0.14911152921050963 | 0.14852876699595186 | 9.754421940457604 |
| 0.005 | 1 | 0 | 100.0 | 5.0 | 5.0 | 0.006878339570614248 | 3.288983786288714 | 0.15181691816855025 | 0.14875746044744265 | 9.953644897460283 |
| 0.005 | 1 | 0 | 40.0 | 4.8 | 4.8 | 0.006917769358147539 | 3.288631941995905 | 0.14886557224541086 | 0.14566614768148867 | 9.555258479551721 |
| 0.005 | 1 | 0 | 40.0 | 4.8 | 5.0 | 0.0069177831605922785 | 3.288983863716602 | 0.1515807346371556 | 0.1459044534791456 | 9.754481436103289 |
| 0.005 | 1 | 0 | 40.0 | 5.0 | 4.8 | 0.0068783309270280465 | 3.28863183490808 | 0.14911152921050963 | 0.14852876699595186 | 9.754421940457604 |
| 0.005 | 1 | 0 | 40.0 | 5.0 | 5.0 | 0.006878339570614248 | 3.288983786288714 | 0.15181691816855025 | 0.14875746044744265 | 9.953644897460283 |
| 0.5 | 100 | 0 | 100.0 | 4.8 | 4.8 | 0.006917769357647762 | 3.288631941995943 | 3.783986815628436 | 3.7824638202792937 | 9.55525850920496 |
| 0.5 | 100 | 0 | 100.0 | 4.8 | 5.0 | 0.006917783159145726 | 3.28898386371684 | 3.982999072417305 | 3.782463935031104 | 9.754481469481245 |
| 0.5 | 100 | 0 | 100.0 | 5.0 | 4.8 | 0.006878330924661921 | 3.2886318349084322 | 3.7839869298770035 | 3.981416370790453 | 9.754421966263966 |
| 0.5 | 100 | 0 | 100.0 | 5.0 | 5.0 | 0.006878339567579182 | 3.288983786288772 | 3.982999186799852 | 3.981416485647368 | 9.953644927116464 |

## Consumo

| id | stage | kind | plus_A | minus_A | vdda_A | vref_A | dac_A | power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | 4051 | idle | 1.293133601307204e-09 | -1.1857577834789106e-09 | 0.0 |  |  | 1.2090037154406933e-05 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | DAC | idle |  |  |  |  | 4.71851090842823e-05 | 0.05898138635535287 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | OPA810 | idle | 0.0019000755456114002 | -0.0019000000097560174 | 0.0 |  |  | 18.533826655307482 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | OPA836 | idle | 0.0010040365431533424 | 0.0 | 0.0010040365431533424 |  |  | 3.31332059240603 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | TOTAL_CHANNEL | idle | 0.006000447664797286 | -0.006085176762614464 | 0.0010040365431533424 | 0.00016303305416298842 | 4.71851090842823e-05 | 62.72426436460947 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | U103A | idle | 0.0010356751058680184 | -0.0010353756094063462 | 0.0 |  |  | 10.100981861389396 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | U103B | idle | 0.0010362713820871107 | -0.0010347797160813455 | 0.0 |  |  | 10.10098288534403 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | U105A | idle | 0.0010355251270801889 | -0.00103552557209574 | 0.0 |  |  | 10.10098199509395 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | U105B | idle | 0.0009928992110169658 | -0.0010794946695172319 | 0.0 |  |  | 10.107594263268599 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_idle_a0_f0_dac1p25_zero_k1_rp4p9_rn4p9_cpldc | VMID | idle |  |  |  | 0.00016303305416298842 |  | 0.4075826354074711 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | 4051 | sine | 1.2945758010784847e-09 | -1.1734500947095992e-09 | 0.0 |  |  | 1.2034208583190927e-05 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | DAC | sine |  |  |  |  | 4.718501823204519e-05 | 0.058981272790056494 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | OPA810 | sine | 0.0019056722177327268 | -0.0019055964418392528 | 0.0 |  |  | 18.587965504891585 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | OPA836 | sine | 0.0010059366249945292 | 0.0 | 0.0010059366249945292 |  |  | 3.3195908624819466 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | TOTAL_CHANNEL | sine | 0.006239979015429872 | -0.006324694707645943 | 0.0010059366249945292 | 0.00016303305416291123 | 4.718501823204519e-05 | 65.06547452050762 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | U103A | sine | 0.0010362450052556588 | -0.0010359453301070675 | 0.0 |  |  | 10.106294189534136 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | U103B | sine | 0.0010990713381029023 | -0.0010975876159840501 | 0.0 |  |  | 10.713342984290026 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | U105A | sine | 0.0011382335123169638 | -0.0011382269888814895 | 0.0 |  |  | 11.102542448434036 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | U105B | sine | 0.0010607556474458194 | -0.0011473371573839887 | 0.0 |  |  | 10.769162588469976 |
| s7b_j9_s00_pos1_tap0_dc_mcnom_sine_a0p0284387055866_f2000000_dac1p25_bipolar_k1_rp4p9_rn4p9_cpldc | VMID | sine |  |  |  | 0.00016303305416291123 |  | 0.40758263540727807 |

## Método y dudas

- Cambios nominales únicos: AFE ±4.90 V; C_S fijo 1.20 nF; C_EQ nominal 8.67 pF (redondeado 8.7 pF en el contrato). Rieles regulados conservan 0.5 Ω, carga 5/42 mA y 5/39 mA, TVS y todos los valores previos. El 4051 usa los mismos ocho SWI1; niveles altos del decodificador siguen el riel real. No se simulan cambios dinámicos de toma.
- Monte Carlo: semilla 2026100371, 500 placas emparejadas en cuatro escalas; offsets independientes, pasivos independientes por instancia; uniformes, factores guardados. R ±1 %, divisor ±0.1 %; C ±5 %, pistas explícitas de 1/3 pF ±50 %. El trimmer no recibe tolerancia adicional: se ajusta y recorta a 2..6 pF. Réplica C_EQ recibe ±5 % tal como manda §2 aunque la selección en prueba podría reducirlo. CMID y condensadores internos/rieles no se dispersan: §2 especifica C0G y no asigna dispersión a esos otros modelos.
- Trimmer: Rtop=Rt1+Rt2; Rbp=Rb||Rbias; Csel=Cj(V+)+Cj(|V−|)+Csel_pista+2.5 pF+CswAC+CswGND; Ctop=Rbp*(Cb+Csel+Ctap)/Rtop−Coff; Ct2=Ct1*Ctop/(Ct1−Ctop); trimmer=Ct2−Ct2fixed. Cb no se reajusta por placa: el contrato pide dispersarlo ±5 % y ajustar el trimmer. La sonda ×10 motivó el ajuste en S1b; la igualdad de tau se calcula sin sustituir la transferencia BNC→PIN por la de punta de sonda.
- Offset OPA836 ±400 µV: hoja local opa836.pdf, SLOS712J, pp. 10/12, máximo a 25 °C; a −40..125 °C llega a 1080 µV (p.12). Fuentes adicionales en serie con IN+ para los seis amplificadores; no se suprime el offset propio del macromodelo (incertidumbre de doble contabilización de su típico). OPA810 ±715 µV y AD8039 ±3 mV según contrato.
- K2 DC: ganancia medida en tres puntos distintos de entrada (−0.01/0/+0.01 div) con DAC 1.25 V, mediante dos recorridos desde cero. DAC recorrido desde 1.25 hacia 0.2 y 2.3 V, paso 5 mV, entrada cero; se miden centros y extremos, sin sustituir DC por AC. La solución AC de la misma placa/escala se guarda con .savebias internal y se carga como recomendación .nodeset; no impone tensiones permanentes, componentes o tolerancias nuevos. Offset referido a centro ADC 1.25 V; DAC de centrado inferido con pendiente medida entre los dos primeros ajustes; posición restante comprobada con los extremos reales, incluido recorte. ±4.5 div exige llegar a 0.125 y 2.375 V. Esto juzga desplazamiento de traza en entrada cero, no amplitud de señal adicional a esa posición.
- Cada proceso tiene tiempo límite: 120 s AC/DC/ruido, 600 s K3 y 900 s transitorios. Popen sin pipes y taskkill /T /F al vencer, para evitar procesos o manejadores heredados colgados. Las cuatro ejecuciones nativas de cada K2DC se registran como hijas con su estado real en el nombre .meas. CSV y extras se ordenan por claves fijas.
- K1/J8 conserva definición relativa al centro nominal del S7. J2 conserva flancos y amplitudes S7; K4 conserva final de flanco a 11.02 µs y banda ±0.1 div. Conducción BAV199: polarización directa >0.4 V, no corriente capacitiva.
- K3: cuatro combinaciones de magnitud de riel 4.80/5.00 V, barridos iniciados en 0 y continuados con paso 1 mV a ambos extremos; J5 ±40 V en cinco escalas, E5b ±100 V en POS1/100, DC y AC. No incluye seno 100 Vpk ni ESD: S7b pide E5b en continua. Se guarda cada polaridad real en el nombre .meas. La señal del 4051 se comprueba en los ocho Y y Z, incluso la toma no seleccionada. La corriente OPA810 es del pin de entrada, no la corriente de carga de salida. Corrientes de U103 incluyen su red de protección, cota conservadora.
- C6 y C7 son barridos deterministas, no fracciones poblacionales de placas; se reporta la fracción de casos y se declara que no hay Monte Carlo de sobrecarga/recuperación. C1..C4/C8 se juzgan por escala, no sólo agregando placas. Las muestras de ruido son los primeros 100 casos de las mismas 500 placas. No se presenta 2000 realizaciones emparejadas como 2000 placas independientes.
- No se dispersan GBW, I_B, ganancia abierta, ruido intrínseco ni temperatura: el contrato S7b §2 no los exige, aunque la decisión permanente es más amplia. Ruido sólo AFE de 1 Hz a 3.15 MHz con AD8038_ltspice_ruido_hoja.sub; sin ruido, cuantización, jitter ni desajuste del ADC. SWI1 está declarado para transitorio por Nexperia; uso AC/DC conserva limitación histórica. OPA836 ESD es supuesto externo; BAV99HY Rohm representa BAV99 Nexperia. TVS genérica y absorción de rieles pendientes de placa.
- Contradicción: ±2 % de 4.90 implica 4.802..4.998, y dos rieles máximos suman 9.996 V en la fuente ideal, no 9.95 V. K3 exige extremos redondeados 4.80/5.00: suma de fuente 10.0 V, margen nulo en ese extremo; se informa tensión real tras resistencia/consumo.
- Consumo de macromodelo OPA810 ≈1.9 mA frente a 3.7 mA típico de hoja: reportar simulado no revisa G.3 ni certifica autonomía. Sin carga ficticia U103B. No se eligieron remedios ni se modificaron entregables previos, modelos, STATE, DECISIONS o chequeo_claude. No hay nueva evidencia física.
