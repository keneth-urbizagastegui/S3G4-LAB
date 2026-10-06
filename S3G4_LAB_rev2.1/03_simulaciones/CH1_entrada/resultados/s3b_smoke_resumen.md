# ACTA S3b — Protección diferencial de U103A

Código 0; 66 simulaciones; 198.970 s; diez trabajadores; errores 0; advertencias 0.

**Comprobación parcial, sin aceptación.**

## Criterios por variante

| variant | criterion | status | value |
| --- | --- | --- | --- |
| A | S3b-C1 | PARCIAL | A=0.293351027 V; B=3.54773599 V; margen B=0.452264015 V |
| A | S3b-C2 | PARCIAL | 4051=4.92183205 mA; diodo=4.92154377 mA |
| A | S3b-C3 | PARCIAL | 0.414362776 % div; exceso=0 puntos |
| A | S3b-C4 | PARCIAL | perdida=-0.0564674017 dB; pico=8.36227488 dB |
| A | S3b-C5 | PARCIAL | 0.209778228 us; sin recuperar=0 |
| A | S3b-C6 | PARCIAL | THD=0.00696880359 % |
| B | S3b-C1 | PARCIAL | A=0.27569716 V; B=3.53114849 V; margen B=0.468851512 V |
| B | S3b-C2 | PARCIAL | 4051=2.93498421 mA; diodo=2.93473764 mA |
| B | S3b-C3 | PARCIAL | 0.437762372 % div; exceso=0 puntos |
| B | S3b-C4 | PARCIAL | perdida=-0.10888775 dB; pico=8.34901146 dB |
| B | S3b-C5 | PARCIAL | 0.273889195 us; sin recuperar=0 |
| B | S3b-C6 | PARCIAL | THD=0.0069713798 % |
| C | S3b-C1 | PARCIAL | A=0.843716057 V; B=3.55808053 V; margen B=0.441919466 V |
| C | S3b-C2 | PARCIAL | 4051=4.20645493 mA; diodo=4.20620817 mA |
| C | S3b-C3 | PARCIAL | 0.40897479 % div; exceso=0 puntos |
| C | S3b-C4 | PARCIAL | perdida=0.00761783682 dB; pico=2.26364871 dB |
| C | S3b-C5 | PARCIAL | 0.0389307967 us; sin recuperar=0 |
| C | S3b-C6 | PARCIAL | THD=0.00696660508 % |
| D | S3b-C1 | PARCIAL | A=0.81693407 V; B=3.54581219 V; margen B=0.454187808 V |
| D | S3b-C2 | PARCIAL | 4051=2.51729876 mA; diodo=2.51708861 mA |
| D | S3b-C3 | PARCIAL | 0.423488991 % div; exceso=0 puntos |
| D | S3b-C4 | PARCIAL | perdida=0.00135053348 dB; pico=2.23800053 dB |
| D | S3b-C5 | PARCIAL | 0.058273699 us; sin recuperar=0 |
| D | S3b-C6 | PARCIAL | THD=0.00696683892 % |

## B0 y controles previos

| variant | gain_dc | minus3_Hz | peak_db | loss_2m_db |
| --- | --- | --- | --- | --- |
| A | 4.9994399002305325 | 32188525.934162885 | 8.362274876563157 | -0.07012093101245019 |
| B | 4.999119267339638 | 24164396.555408146 | 8.349011457770875 | -0.12507944520366396 |
| C | 4.99951024473808 | 63749811.20987373 | 2.263648708221728 | -0.009578955476671504 |
| D | 4.999245297085557 | 48548974.21639818 | 2.238000527893525 | -0.016415504927390676 |

| noise_model | noise_315m_uV | noise_315m_pct_div | noise_10m_pct_div |
| --- | --- | --- | --- |
| original | 32.216909315093915 | 0.6443381863018783 | 1.149459410737834 |
| sheet | 19.80647642774755 | 0.39612952855495104 | 0.7048881882269603 |

## Por escala y variante

| variant | scale_V_div | POS | tap | s3_gain_dc | s3_loss_2m_db | s3_peak_db | bnc_loss_2m_db | bnc_peak_db | noise_315m_uV | noise_315m_pct_div | noise_10m_pct_div |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.005 | 1 | 0 | 50.058225173931326 | -0.05646740170275716 | 6.351323578749085 | -0.051000665268815 | 6.089563585591458 | 20.718138776684093 | 0.41436277553368184 | 0.8082597483322209 |
| A | 0.5 | 100 | 0 | 50.05822517400261 | -0.05646740171448801 | 6.351323578490829 | -0.049952314984737345 | 6.0885791959231605 | 2064.793524014416 | 0.4129587048028832 | 0.8054754198245062 |
| B | 0.005 | 1 | 0 | 50.0550371508126 | -0.10888775011951161 | 6.876053547126071 | -0.10342101431277198 | 6.721549436740769 | 21.888118597844485 | 0.4377623719568897 | 0.9678091442320202 |
| B | 0.5 | 100 | 0 | 50.05503715088387 | -0.10888775013070591 | 6.876053546667596 | -0.10237266403307549 | 6.72053793982469 | 2182.026187898519 | 0.4364052375797038 | 0.9651417694812996 |
| C | 0.005 | 1 | 0 | 50.05897108345057 | 0.007617836815923631 | 1.7846534609948827e-05 | 0.013084546222654987 | 1.7283477930359653e-05 | 20.44873951644427 | 0.40897479032888545 | 0.7309845817805799 |
| C | 0.5 | 100 | 0 | 50.05897108352222 | 0.007617836820067502 | 1.7846534608020177e-05 | 0.014132896496639945 | 1.7791430291650624e-05 | 2037.7951605545984 | 0.4075590321109197 | 0.7281011187174928 |
| D | 0.005 | 1 | 0 | 50.05631824060413 | 0.00135053347551338 | 1.784676746562373e-05 | 0.006817242019067228 | 1.7283478040292766e-05 | 21.17444954268361 | 0.4234889908536722 | 0.7635192837338183 |
| D | 0.5 | 100 | 0 | 50.05631824067576 | 0.0013505334802013768 | 1.7846767463695085e-05 | 0.007865592291704897 | 1.7791432177871286e-05 | 2110.522036665737 | 0.4221044073331474 | 0.760695705252495 |

## B3: Barrido estático y márgenes

| variant | scale_V_div | u103a_differential_peak_V | u103b_differential_peak_V | u103b_margin_V | switch_current_peak_A | diode_p_current_peak_A | diode_n_current_peak_A | opa810_current_peak_A | inplus_min_V | inplus_max_V | inplus_rail_margin_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | 0.005 | 0.2933510267084023 | 3.5477359854355828 | 0.4522640145644172 | 0.004921832050659449 | 0.0045892057379069975 | 0.004921543774794741 | 0.009777950263508646 | -2.0577233203695613 | 1.9883947453464303 | 2.9422766796304387 |
| A | 0.01 | 0.2536892499494494 | 3.5175195033067714 | 0.48248049669322857 | 0.0014190107967237697 | 0.001415001075858692 | 0.0014187969219895185 | 0.005595374075964468 | -1.3137458240117432 | 1.3129044837695785 | 3.6862541759882568 |
| B | 0.005 | 0.2756971596072306 | 3.531148488312105 | 0.4688515116878951 | 0.002934984210668784 | 0.0027688951165175907 | 0.0029347376398615806 | 0.0078035760131384985 | -1.640681887328159 | 1.6054779902206626 | 3.3593181126718408 |
| B | 0.01 | 0.2418459486686666 | 3.5124237851184126 | 0.4875762148815874 | 0.0009330001351251502 | 0.0009314309895585898 | 0.0009327972374785059 | 0.005355595736149221 | -1.2039999461733595 | 1.2036838153753726 | 3.7960000538266403 |
| C | 0.005 | 0.8437160570375077 | 3.558080533508414 | 0.4419194664915862 | 0.004206454925698455 | 0.003882732423622702 | 0.004206208171742525 | 0.009066797971904331 | -2.4675280497928043 | 2.3983714643017175 | 2.5324719502071957 |
| C | 0.01 | 0.7656122122475197 | 3.534318862336911 | 0.46568113766308894 | 0.0008990915057986713 | 0.0008970079201336316 | 0.0008989189686450241 | 0.005338534630652485 | -1.725360848288764 | 1.7248774467653007 | 3.274639151711236 |
| D | 0.005 | 0.8169340699068683 | 3.545812192113049 | 0.4541878078869508 | 0.002517298763370642 | 0.0023715191591886777 | 0.0025170886057475296 | 0.007388841177583571 | -2.1015650031434876 | 2.0692582108257795 | 2.8984349968565124 |
| D | 0.01 | 0.7472673231008853 | 3.5321792328435575 | 0.4678207671564425 | 0.000598433446551547 | 0.0005976869624980258 | 0.0005982687801880731 | 0.005190324107719825 | -1.646653139574295 | 1.646494372878278 | 3.353346860425705 |

## B4: Recuperación desde final de pulso

| variant | amplitude_V | polarity | BNC_plateau_V | recovery_s | terminal_error_V | max_step_pulse_and_5us_s |
| --- | --- | --- | --- | --- | --- | --- |
| A | 0.2 | negative | -0.2 | 2.0977822827949662e-07 | -0.00017064272575992518 | 5.000000000010964e-10 |
| A | 0.2 | positive | 0.2 | 2.0967913720822092e-07 | 0.0001706427223430963 | 5.000000000010964e-10 |
| B | 0.2 | negative | -0.2 | 2.7359194557321697e-07 | -0.00017063267055700227 | 5.000000000010964e-10 |
| B | 0.2 | positive | 0.2 | 2.7388919532433645e-07 | 0.00017063267488643319 | 5.000000000010964e-10 |
| C | 0.2 | negative | -0.2 | 3.893079673188313e-08 | -0.0001706452214600149 | 5.000000000010964e-10 |
| C | 0.2 | positive | 0.2 | 3.872400498803046e-08 | 0.0001706452239309121 | 5.000000000010964e-10 |
| D | 0.2 | negative | -0.2 | 5.827369903391809e-08 | -0.00017063722042309727 | 5.000000000010964e-10 |
| D | 0.2 | positive | 0.2 | 5.79577159699325e-08 | 0.000170636954335827 | 5.000000000010964e-10 |

## B5: Gran señal

| variant | scale_V_div | output_pp_V | thd_pct | max_dvdt_V_us |
| --- | --- | --- | --- | --- |
| A | 0.005 | 1.99999345395929 | 0.006968803585071988 | 12.566441717429253 |
| A | 0.5 | 1.9999934765449683 | 0.006968682595972862 | 12.566445870885415 |
| B | 0.005 | 1.999993491737342 | 0.006971379796829598 | 12.566475750673874 |
| B | 0.5 | 1.999993514077511 | 0.006971249525669537 | 12.566479067767158 |
| C | 0.005 | 1.9999933829242293 | 0.0069666050833273 | 12.566477561667533 |
| C | 0.5 | 1.9999934057332256 | 0.00696648035158498 | 12.566476870610623 |
| D | 0.005 | 1.999993389252021 | 0.00696683892012926 | 12.566445449889551 |
| D | 0.5 | 1.9999934119781912 | 0.006966701560710862 | 12.566457398442635 |

## B6: Offset OP frente a S3

| variant | scale_V_div | temp_C | output_offset_V | baseline_offset_V | added_offset_div |
| --- | --- | --- | --- | --- | --- |
| A | 0.005 | 25 | 0.003769565411624221 | 0.0037697987525384057 | -9.333636567382397e-07 |
| A | 0.005 | 70 | 0.004442837755342847 | 0.004445636571875623 | -1.1195266131101833e-05 |
| A | 0.2 | 25 | 9.406872230564842e-05 | 9.407459134319519e-05 | -2.347615018707819e-08 |
| A | 0.2 | 70 | 0.00011089445972440153 | 0.00011096643423181113 | -2.878980296384102e-07 |
| B | 0.005 | 25 | 0.003769325341952734 | 0.0037697987525384057 | -1.8936423426870602e-06 |
| B | 0.005 | 70 | 0.004440754139272937 | 0.004445636571875623 | -1.9529730410743074e-05 |
| B | 0.2 | 25 | 9.406273143430883e-05 | 9.407459134319519e-05 | -4.7439635545451584e-08 |
| B | 0.2 | 70 | 0.00011084245320787017 | 0.00011096643423181113 | -4.959240957638734e-07 |
| C | 0.005 | 25 | 0.0037696215814437602 | 0.0037697987525384057 | -7.086843785818892e-07 |
| C | 0.005 | 70 | 0.004445427636229218 | 0.004445636571875623 | -8.357425856191092e-07 |
| C | 0.2 | 25 | 9.407017008379023e-05 | 9.407459134319519e-05 | -1.768503761983382e-08 |
| C | 0.2 | 70 | 0.0001109612190518266 | 0.00011096643423181113 | -2.0860719938129227e-08 |
| D | 0.005 | 25 | 0.003769421812782441 | 0.0037697987525384057 | -1.50775902385894e-06 |
| D | 0.005 | 70 | 0.00444519205235744 | 0.004445636571875623 | -1.7780780727297274e-06 |
| D | 0.2 | 25 | 9.406518490797888e-05 | 9.407459134319519e-05 | -3.762574086525099e-08 |
| D | 0.2 | 70 | 0.00011095533871538216 | 0.00011096643423181113 | -4.4382065715912675e-08 |
| NONE | 0.005 | 25 | 0.0037697987525384057 |  |  |
| NONE | 0.005 | 70 | 0.004445636571875623 |  |  |
| NONE | 0.2 | 25 | 9.407459134319519e-05 |  |  |
| NONE | 0.2 | 70 | 0.00011096643423181113 |  |  |

Archivos protegidos: 21318; cambios detectados: [].


## Método y dudas sin resolver

Fuentes completas leídas: encargo y contrato S3b; plan, acta y auditoría S3;
plan/acta/auditoría S2b; decisiones del 3 oct; revisión de entrada §6 E11–E15
y documento vivo C.3–C.6. No se modifican entregables previos ni modelos.
El ejecutor importa S3 sin escribirlo y reutiliza su lista de conexiones;
ch1_comun_s3b.inc incluye ch1_comun_s3.inc, que incluye S2b. Sólo se inserta
R_SER y dos diodos en sentidos opuestos entre IPA e IMA. CPCB sigue en COMMON.
VIA mide la corriente total que sale del común del 4051; VOUT101 mide toda la
corriente de salida del OPA810, incluida la escalera. Los sensores son fuentes
ideales de 0 V. U103A/B se miden en sus pines IPA/IMA, IPB/IMB.
Ocho SWI1 hc_tnomi reales, sin proxy. Modelos originales en AC/DC/TRAN/OP;
sólo NOISE usa AD8038_ltspice_ruido_hoja.sub. B0 es U103A aislada con
1 kohm paralelo 10 pF de carga como comprobación S3; su barrido llega a 1 GHz
para localizar -3 dB; el pico contractual se comprueba también en B1 a 100 MHz.
B1 informa función S3 OUT/BI y completa OUT/BNC; C4 mantiene el criterio S3
(pérdida de la parte añadida), sin ocultar la pérdida BNC. Rsource=50 ohm
en B1/B2/B5/B6; enlace ideal BNC en B3/B4 para imponer exactamente el estímulo.
Ruido inoise referido a Vsrc, integración del cuadrado de 1 Hz a 3.15/10 MHz
con interpolación del extremo, mismo método que S3. B3 -40 a +40 V, 50 mV;
extremos y número de puntos verificados; .meas y raw contrastados.
B4 flancos 10 ns, ancho 10 us, amplitud máxima 4.5 V; paso global máximo
0.5 ns comprobado en raw. Recuperación desde el FINAL del flanco descendente
a +/-25 mV del punto inicial; se busca última violación, no primer cruce;
30 us de registro, sin redefinir el objetivo por la cola. B5 amplitud del
estímulo calculada desde AC de la misma variante para 2 Vpp; armónicos 2–9,
20 ciclos coherentes y 65536 puntos interpolados, método inmutable de S3.
B6 .op real: extraído del raw, sin inventar una .meas TRAN con otro estado.
Offset añadido = (OUT protegido - OUT S3 sin protección) / 0.25 V por división.

1. No hay hoja local de BAT54S Vishay. El modelo contractual BAT54 de standard.dio
declara Iave=300 mA; el chequeo numérico C2 de A/B usa su mitad, 150 mA,
pero su estatus es CONDICIONAL hasta verificar IF continuo de la pieza dual
en su hoja. La hoja local onsemi BAT54T1G da 200 mA (mitad 100 mA), otra pieza
y otro encapsulado: NO se atribuye ese rating a BAT54S. Sin descargas.
BAV199 Nexperia p2 IF=160 mA con un diodo, 140 mA con ambos: se usa 70 mA,
conservador. 4051 p5 ISW=25 mA, criterio mitad 12.5 mA. Nota de esa página:
caída Y→Z >0.4 V puede sacar corriente de VCC; se informa como limitación
del criterio de corriente sin rediseñar la red. OPA810 p6 a +/-5 V: 52 mA
mín./75 mA típ. de drive lineal con VO=2.65 V, 100 mA típ. en cortocircuito;
son condiciones diferentes de B3, no un máximo absoluto ni garantía a saturación.
2. AD8038 simplificado no representa Ib real de 400 nA ni su deriva; B6 muestra
la contribución del par simétrico y de la resistencia en ESTE modelo, no
predice offset absoluto de placa. No se inyecta Ib artificial fuera del contrato.
BAT54 y BAV199 con mismo modelo en ambos sentidos tampoco incluyen mismatch.
3. BAV199 TT=1.023 us de fabricante; su recuperación puede dominar B4 aunque
proteja bien en DC. El modelo no simula destrucción ni temperatura de unión.
4. S3 conserva CS/CEQ derivados de S2b, no los valores resumidos 1.5 nF/12 pF;
no se retoca ningún valor. Documento vivo aún tiene candidatos/red/ruido antiguos;
mandan decisiones 3 oct y contratos S3/S3b. No se resuelven contradicciones.
5. Se respeta la recuperación aceptada de aproximadamente 0.6 ms tras conducción
de BAV199 de entrada: no se repite ese ensayo. Rieles ideales de S3 no validan
riel real ni prueba física. Sin selección de variante ni diseño S4.
CSV deterministas ordenados, .cir y .log retenidos; raw regenerable eliminado.
