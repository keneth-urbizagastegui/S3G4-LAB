# Resultados S2 — protección P4b

Código 0; 119 simulaciones; 0 con error; 0 con advertencia. 61.264s (1.021min), 10 trabajadores.

| criterion | buffer | value | status |
| --- | --- | --- | --- |
| S2-C1 | AD8065 | Zin 0.999012–1.000280 MΩ; Cin 26.918921–28.402606 pF; Δ 1.483685 pF; gain 0.418790%; flat 0.265726%; peak 0.004267dB; fc 8.805817Hz | PASA |
| S2-C1 | OPA810 | Zin 0.999093–1.000499 MΩ; Cin 26.919057–29.758938 pF; Δ 2.839881 pF; gain 0.536898%; flat 0.693691%; peak 0.008052dB; fc 8.790226Hz | FALLA |
| S2-C2 | AD8065 | worst req_v=99.0119; 1.320158 × derated limit; CEQ rating unspecified | FALLA |
| S2-C2 | OPA810 | worst req_v=99.0122; 1.320162 × derated limit; CEQ rating unspecified | FALLA |
| S2-C3 | AD8065 | VIN beyond rail 2.12908 V (<0.5); |IIN| 0.00337735 A; |differential| 4.00243 V | FALLA |
| S2-C3 | OPA810 | VIN beyond rail 1.68821 V (<0.5); |IIN| 0.00257305 A; |differential| 3.05475 V | FALLA |
| S2-C4 | AD8065 | |rails| 4.975072–4.977858 V | PASA |
| S2-C4 | OPA810 | |rails| 4.975668–4.980100 V | PASA |
| S2-C5 | OPA810 | OFF_LOAD_ONLY: bleed0 0.449344 V; bleed1 0.17016 V; bleed2 0.00310446 V | PASA |
| S2-C6 | AD8065 | BAV |I|=23.9688 A vs 4 A/1us; TVS |I|=5.81724e-12 A vs generic 38.8 A; input ∫|VI|=1.20347e-10 J; no rated transient energy | FALLA |
| S2-C6 | OPA810 | BAV |I|=23.9745 A vs 4 A/1us; TVS |I|=0.000169414 A vs generic 38.8 A; input ∫|VI|=6.71763e-11 J; no rated transient energy | FALLA |
| S2-C7 | AD8065 | |offset BNC|=0.403697 mV | PASA |
| S2-C7 | OPA810 | |offset BNC|=0.076053 mV | PASA |
| S2-C8 | OPA810 | THD=0.000004%; |BAV I|=0.002707 µA | PASA |

## Recuperación E8

| buffer | stimulus | recovery_one_div_s | recovery_tenth_div_s | final_output_v |
| --- | --- | --- | --- | --- |
| AD8065 | 40 | 0.0010157051976801747 | 0.001558405197680174 | -0.0003997076703426342 |
| AD8065 | -40 | 0.000992912345539415 | 0.001247112345539415 | -0.0003997076703425834 |
| OPA810 | 40 | 0.0010027272293450335 | 0.001311927229345033 | 7.520762877464926e-05 |
| OPA810 | -40 | 0.001007045060670243 | 0.0013550450606702427 | 7.539645196229984e-05 |

## Derivados contractuales

| CJ_POL_pF | C_SEL_EST_pF | CEQ_pF | CS_pF | CB_pF |
| --- | --- | --- | --- | --- |
| 1.0838258570379375 | 11.167651714075873 | 11.167651714075873 | 1419.6043801679232 | 1086.040148285924 |

Archivos protegidos: 19839; cambios: []. Manifest y detalle por estado en `s2_ejecucion.json` y CSV.

## Lo que enseña cada prueba

### OPA810

E5: tensiones pico y potencia media máximas, sin cambiar valores.

| part | voltage_V | voltage_limit_V | power_W | power_limit_W |
| --- | --- | --- | --- | --- |
| rt1 | 49.5046026503 | 100 | 0.00446394380936 | 0.125 |
| rt2 | 49.5046026503 | 100 | 0.00446394380936 | 0.125 |
| rb | 0.991884580703 | 75 | 8.94395474034e-05 | 0.0625 |
| rs1 | 47.1279051871 | 100 | 0.0445098085637 | 0.125 |
| rs2 | 47.1279051871 | 100 | 0.0445098085637 | 0.125 |
| req | 99.0121615402 | 75 | 0.000980334854753 | 0.0625 |
| rbias | 5.80186420546 | 75 | 3.30117066346e-06 | 0.0625 |
| rprot | 0.00243057378484 | 75 | 2.74227826635e-10 | 0.0625 |

| part | voltage_V | derated_limit_V |
| --- | --- | --- |
| ct1 | 49.5046026503 | 80.0 |
| ct2fixed | 49.5046026503 | 80.0 |
| ct2trim | 49.5046026503 | 80.0 |
| cb | 0.991884580703 | 40.0 |
| cs | 94.2558103743 | 80.0 |
| cac | 5.74801699384 | 40.0 |
| ceq | 99.0121615402 | SIN DEFINIR |

BAV corriente terminal continua/seno máxima: 0.00128322009 A. Contactos abiertos: 98.0213727 V.

E6: referencia de carga apagada frente al macro no validado a cero alimentación.

| variant | bleed | rail_abs_V | vp_min_V | vn_max_V |
| --- | --- | --- | --- | --- |
| off_load_only | 0 | 0.44934439065 | -1.30132092889e-06 | 1.30132093111e-06 |
| off_load_only | 1 | 0.170160293927 | -1.09895197417e-08 | 1.09895197418e-08 |
| off_load_only | 2 | 0.00310445961699 | -9.5091199307e-11 | 9.5091199307e-11 |
| real | 0 | 0.497504450225 | -0.497504093095 | 0.497504450225 |
| real | 1 | 0.497360882682 | -0.49736051532 | 0.497360882682 |
| real | 2 | 0.190315429168 | -0.189980882422 | 0.190315429168 |

E7: valores del circuito 150pF/330Ω, sin equipararlo a ensayo IEC certificado.

| POS | power | bleed | variant | stimulus | gun_peak_A | rise_ns | bav_peak_A | tvs_peak_A | pin_peak_V | pin_current_A | rail_peak_V | rs_energy_J | input_energy_J |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 0 | 0 | off_load_only | 8kv | 24.2400641683 | 0.00033507519761065917 | 8.85528636929 | 7.73745860984e-13 | 1.09956983795 | 1.1113072268e-18 | 0.076380362113 | 8.3943626663e-08 | 1.98584848952e-24 |
| 100 | 0 | 0 | real | 8kv | 24.2400658224 | 0.00033507519761065917 | 8.90263543712 | 0.000169413671535 | 0.59072736881 | 0.000281250122385 | 0.494747215978 | 8.39436584044e-08 | 6.3857345158e-13 |
| 100 | 0 | 1 | off_load_only | 8kv | 24.2400641683 | 0.00033507519761065917 | 8.85528304023 | 7.73715588081e-13 | 1.09956986171 | 1.1113072268e-18 | 0.0763680748013 | 8.39436266634e-08 | 1.98582596271e-24 |
| 100 | 0 | 1 | real | 8kv | 24.2400658203 | 0.00033507519761065917 | 8.90264290483 | 0.000168393149157 | 0.590793618204 | 0.000281273669975 | 0.494591884088 | 8.39436583978e-08 | 6.38591587249e-13 |
| 100 | 0 | 2 | off_load_only | 8kv | 24.2400641683 | 0.00033507519761065917 | 8.85528291583 | 7.70701181615e-13 | 1.09956621429 | 1.10453096322e-18 | 0.0751618376075 | 8.39436266964e-08 | 1.98348566301e-24 |
| 100 | 0 | 2 | real | 8kv | 24.2400642596 | 0.00033507519761065917 | 8.87488132203 | 1.21255041859e-09 | 0.877462372719 | 0.000385913460826 | 0.190353019668 | 8.39436389328e-08 | 1.34340234494e-12 |
| 100 | 1 | 0 | real | 4kv | 12.1200316666 | 0.00033507519766359876 | 3.6433175633 | 5.71611778936e-12 | 5.925002666 | 0.00193882961166 | 4.98115365019 | 2.09857361638e-08 | 4.34486915559e-11 |
| 100 | 1 | 0 | real | 8kv | 24.2400633331 | 0.00033507519761065917 | 8.19074881518 | 5.71977619975e-12 | 5.97086995607 | 0.00211865239562 | 4.98481206058 | 8.39433108982e-08 | 4.40065882951e-11 |
| 100 | 1 | 0 | real | -4kv | 12.1200316664 | 0.00033507519766359876 | 3.64367354733 | 5.71760529547e-12 | 5.92649279012 | 0.00193917841219 | 4.98264119915 | 2.09857360208e-08 | 4.34566884518e-11 |
| 100 | 1 | 0 | real | -8kv | 24.240063333 | 0.00033507519761065917 | 8.18581213151 | 5.7212672358e-12 | 5.97238719117 | 0.00211906832928 | 4.9862996347 | 8.39433105142e-08 | 4.40235258046e-11 |
| 1 | 1 | 0 | real | 4kv | 12.1200157317 | 0.00033507519765036385 | 11.9650411071 | 5.76497714527e-12 | 6.33078677389 | 0.00233937572257 | 5.03001300611 | 2.59678046296e-06 | 5.43209654306e-11 |
| 1 | 1 | 0 | real | 8kv | 24.240031458 | 0.0003350751975974243 | 23.9648239723 | 5.81807822504e-12 | 6.71849607392 | 0.0025724843758 | 5.08311408588 | 1.040415136162e-05 | 6.70257881295e-11 |
| 1 | 1 | 0 | real | -4kv | 12.1200157197 | 0.00033507519765036385 | 11.9650964669 | 5.76653159946e-12 | 6.33220973158 | 0.00233992700101 | 5.03156766469 | 2.59677795716e-06 | 5.44076239293e-11 |
| 1 | 1 | 0 | real | -8kv | 24.240031446 | 0.0003350751975974243 | 23.964602767 | 5.81964827568e-12 | 6.72006824678 | 0.0025730492786 | 5.08468235673 | 1.040414632694e-05 | 6.71757121072e-11 |

E9: fugas/offset y deriva del modelo, referidos a BNC.

| POS | CPL | connection | offset25_bnc_mV | offset85_bnc_mV | drift_bnc_uV_C |
| --- | --- | --- | --- | --- | --- |
| 100 | AC | 50ohm | 5.600761492657166 | 7.4174557179096805 | 30.278237087541903 |
| 100 | AC | air | 5.600761492657166 | 7.4174557179096805 | 30.278237087541903 |
| 100 | DC | 50ohm | 7.617842932853623 | 9.434535175769554 | 30.27820404859885 |
| 100 | DC | air | 7.617823109931869 | 9.434515334933081 | 30.278203750020218 |
| 1 | AC | 50ohm | 0.056046469873381105 | 0.07422601533309223 | 0.30299242432851853 |
| 1 | AC | air | 0.05604646987277512 | 0.07422601533258724 | 0.302992424330202 |
| 1 | DC | 50ohm | 0.07605335322440994 | 0.0942327180921222 | 0.3029894144618712 |
| 1 | DC | air | 0.07407242212667209 | 0.09225000237608603 | 0.3029596708235658 |

E10: CTIP=11.8694754pF fijo, fundamental 0.396035833Vpk; THD por remuestreo 3.58097295e-06%, por .four 0.0%.

### AD8065

E5: tensiones pico y potencia media máximas, sin cambiar valores.

| part | voltage_V | voltage_limit_V | power_W | power_limit_W |
| --- | --- | --- | --- | --- |
| rt1 | 49.5045978149 | 100 | 0.00446394390676 | 0.125 |
| rt2 | 49.5045978149 | 100 | 0.00446394390676 | 0.125 |
| rb | 0.991884580703 | 75 | 8.94395474034e-05 | 0.0625 |
| rs1 | 47.1284701283 | 100 | 0.044510875684 | 0.125 |
| rs2 | 47.1284701283 | 100 | 0.044510875684 | 0.125 |
| req | 99.0118606407 | 75 | 0.000980334854753 | 0.0625 |
| rbias | 5.74325626622 | 75 | 3.29849925395e-06 | 0.0625 |
| rprot | 0.000314483887866 | 75 | 9.89001156371e-11 | 0.0625 |

| part | voltage_V | derated_limit_V |
| --- | --- | --- |
| ct1 | 49.5045978149 | 80.0 |
| ct2fixed | 49.5045978149 | 80.0 |
| ct2trim | 49.5045978149 | 80.0 |
| cb | 0.991884580703 | 40.0 |
| cs | 94.2569402565 | 80.0 |
| cac | 5.74582407433 | 40.0 |
| ceq | 99.0118606407 | SIN DEFINIR |

BAV corriente terminal continua/seno máxima: 0.000944444849 A. Contactos abiertos: 98.0210573 V.

E7: valores del circuito 150pF/330Ω, sin equipararlo a ensayo IEC certificado.

| POS | power | bleed | variant | stimulus | gun_peak_A | rise_ns | bav_peak_A | tvs_peak_A | pin_peak_V | pin_current_A | rail_peak_V | rs_energy_J | input_energy_J |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 100 | 1 | 0 | real | 8kv | 24.2416609882 | 9.534169767069902e-07 | 8.14863515188 | 5.71752847139e-12 | 5.96741647973 | 0.00285596052447 | 4.98256433222 | 8.3943296331e-08 | 5.29603945018e-11 |
| 100 | 1 | 0 | real | -8kv | 24.2416596199 | 1.244524677684197e-06 | 8.14034761952 | 5.71900981182e-12 | 6.35760811162 | 0.00285736991845 | 4.98404405354 | 8.39432966294e-08 | 8.00799519146e-11 |
| 1 | 1 | 0 | real | 8kv | 24.2416582395 | 1.5179394221102578e-06 | 23.9688205836 | 5.81573526945e-12 | 6.67027585057 | 0.00337666304428 | 5.08077113028 | 1.04041569443e-05 | 8.45301000942e-11 |
| 1 | 1 | 0 | real | -8kv | 24.2416582573 | 1.5179394221102578e-06 | 23.9659799328 | 5.81724251995e-12 | 7.15735135604 | 0.0033773534873 | 5.08227618346 | 1.040415258604e-05 | 1.2034749197e-10 |

E9: fugas/offset y deriva del modelo, referidos a BNC.

| POS | CPL | connection | offset25_bnc_mV | offset85_bnc_mV | drift_bnc_uV_C |
| --- | --- | --- | --- | --- | --- |
| 100 | AC | 50ohm | -37.38142111046879 | -37.39059479678117 | -0.15289477187305223 |
| 100 | AC | air | -37.38142111046879 | -37.39059479678117 | -0.15289477187305223 |
| 100 | DC | 50ohm | -40.3679919786053 | -40.37258599446085 | -0.07656693092571165 |
| 100 | DC | air | -40.367962636418724 | -40.37255671515239 | -0.07656797889448361 |
| 1 | AC | 50ohm | -0.3740735424707553 | -0.3741653429757775 | -0.0015300084170368367 |
| 1 | AC | air | -0.3740735424687354 | -0.3741653429727476 | -0.0015300084002036946 |
| 1 | DC | 50ohm | -0.4036966061782784 | -0.40374314304289816 | -0.000775614410328808 |
| 1 | DC | air | -0.4007647383045977 | -0.40081757096842563 | -0.000880544397132025 |

E0 contrasta el nominal real con S1b en s2_s1b_comparacion.csv. E8 se informa en la tabla de recuperación, incluyendo ambas polaridades y segunda fuente. s2_segunda_fuente.csv conserva las diferencias por estado.

## Método, fuentes y dudas sin resolver

Ejecutor Codex; contrato PLAN_SIMULACION_S2, planes S1/S1b, actas y auditorías
leídas completas; DECISIONS 2/3 oct; revisión de entrada §4/§6 y documento vivo
C.6/G.3/G.5/G.6. Sólo S2, este ejecutor, resultados s2_* y diario se escriben.
No ensayos físicos, descargas, modificaciones del diseño ni selección de piezas.

OPA810: hoja local SBOS799E, agosto 2024, p.4: entrada entre VEE−0.5 y VCC+0.5,
corriente continua ±10mA, diferencial ≤min(7V, tensión total de alimentación).
AD8065: hoja local Rev.L, p.9: mismo límite relativo a rieles, diferencial 1.8V;
p.21 admite protección con corriente limitada a 30mA, lo que no equivale a
autorizar cualquier tensión ni una energía ESD. BAV199 Nexperia 1 abril 2023,
p.2: 160mA con un diodo cargado, 140mA con ambos; IFSM 4A/1us, VR75V.
Se informa tanto la corriente terminal total (incluye desplazamiento) como sus
extremos firmados: IFSM es de conducción directa y no valida un pico capacitivo.
La BV=113.3V del modelo no sustituye VR=75V de la hoja. No hay modelo térmico.

1. CIN_BUF=5pF explícita de S1b se conserva por contrato. OPA810 añade 2.5pF
de modo común y 0.5pF diferencial; AD8065 añade 1.1pF por pin y 4pF diferencial
en su modelo (distinto de 6.6pF en hoja). Por tanto la estimación contractual
C_SEL_EST no cuenta toda la capacidad real y E0 no tiene por qué pasar. No se
restan capacidades ni se reajusta CB/CEQ para forzar aceptación.
2. C_EQ no tiene tensión nominal en C.6 ni en el contrato: se informa su tensión,
sin inventar una selección comercial. Los demás ratings usan §3/C.6; C1≥100V
se evalúa conservadoramente a 100V. R/C no están elegidas por MPN: pulse rating,
derating térmico y tensión transitoria todavía requieren hoja de pieza concreta.
3. Las cargas resistivas son 5/42mA y 5/39mA (derivadas, sin redondeo). El buffer
real añade su consumo al equivalente agregado: posible doble conteo en G.3.
El regulador es de entrega unilateral (diodo ideal y 0.5Ω); el interruptor abierto
conserva desacoplo y 1MΩ del contrato y el buffer real. Los modelos de buffers
no garantizan corriente correcta con alimentación ausente; E6 no certifica
ausencia de alimentación parásita en silicio. Se añade OFF_LOAD_ONLY: sin macro
del amplificador, sólo 1MΩ de carga por riel, y entrada observada sin protección
interna. C5 se evalúa sobre esa carga contractual; los resultados REAL se dejan
en el CSV, incluso si invierten la polaridad de los rieles. OFF_LOAD_ONLY no
permite juzgar C3 ni corriente de entrada del buffer. Purga10k/100Ω no se elige.
4. La TVS es genérica, Rs=(10.3−6.67)/(38.8−0.001). BV a 1mA y Rs no obligan
a la ecuación Shockley a cruzar exactamente 10.3V a 38.8A. No se elige SMAJ.
5. ESD: 150pF inicialmente cargados, 330Ω, switch con Ron0.01Ω y mando de
0.5ns a 100ns. Paso global ≤0.1ns; se verifica el .raw en los primeros 200ns.
Sin inductancia ni modelo de arco: la subida medida no es el pulso normativo
IEC. ±8kV se descarga por contacto como pide E7, aunque el requisito es aire.
No demuestra conformidad IEC ni ±100V sin daño. Se informa corriente/energía
y excursión de entrada; no existe energía admisible en hoja para declarar
supervivencia si se exceden los máximos. Los modelos no simulan destrucción.
6. E5 DC usa equilibrio, con fuente ideal rígida, no un escalón de conexión.
En AC se mide el último ciclo de 8ms (100Vpk/1kHz), potencia media y tensión
pico de cada R/C. E6 añade CPL AC además de DC. E7 usa CPL DC; sin alimentación
POS100 forzado. No se hacen extrapolaciones al banco o a hardware conectado.
7. E8: pulso a cada polaridad de 40V, 1ms, flancos10ns, POS1/DC; último instante
fuera de ±5mV/±0.5mV, conservando offset absoluto (no resta del valor final).
Si no se asienta antes de 20ms se indica censura, sin tiempo ficticio. AD8065
declara explícitamente no modelar overload recovery ni distortion: sus tiempos
son observaciones del modelo y no comparación válida del silicio.
8. E9 referencia offset a BNC con ganancia nominal calculada; incluye Vos, fugas
del modelo y bias. Al aire en AC/DC se resuelve equilibrio, sin contaminación
de PCB ni absorción dieléctrica. La deriva es diferencia 85−25°C, no garantía.
9. E10 usa 9MΩ∥CTIP y cable80pF. CTIP se calcula por igualdad de constantes de
tiempo resistivas, con la Cin de POS100/DC medida en E0 a 1MHz; queda fijo.
Es compensación capacitiva nominal de la sonda de S1b, sin ajustar el DUT.
THD con 7 armónicos (2…7/fundamental) en último ciclo, remuestreo32768 puntos;
.four 1k 7 conserva un control independiente en el log. La corriente máxima
de BAV incluye componente capacitiva: también se informa el signo y el pulso.

CSV en orden determinista, pool de10 por defecto, threads=1 por LTspice.
.cir/.log se conservan, .raw regenerables se analizan antes de eliminarlos.
Hash de entregables S1/S1b, modelos, chequeo, STATE/DECISIONS al inicio/final.
Código distinto de cero sólo por errores de simulación/medida; fallos eléctricos
son resultados válidos. El modo smoke usa carpeta y prefijos separados.

Verificación posterior: 12 CSV reproducidos byte a byte; 119 estados, 5068
medidas y 19839 archivos protegidos comprobados. Evidencia:
`../S2/verificacion_entrega.json`; detalles y alcance en `../ACTA_S2.md`.
