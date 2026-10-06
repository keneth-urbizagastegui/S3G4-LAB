# S7b — CH1, tolerancias reales

{"returncode": 0, "simulations": 19, "logical_cases": 19, "successful": 19, "seconds": 84.47672050000983, "workers": 10, "smoke": false, "preflight": true, "seed": 2026100371, "protected_changed": [], "protected_count": 13319}

| criterion | scope | N | pass_count | fraction | status |
| --- | --- | --- | --- | --- | --- |
| S7b-C1 | 0.005 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C2 | 0.005 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C1 | 0.5 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C2 | 0.5 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C3 | 0.005 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C3 | 0.5 V/div | 1 | 1 | 1.0 | PASA |
| S7b-C4 | 0.005 V/div | 0 | 0 | 0 | FALLA |
| S7b-C4 | 0.05 V/div | 0 | 0 | 0 | FALLA |
| S7b-C4 | 0.5 V/div | 0 | 0 | 0 | FALLA |
| S7b-C4 | 5.0 V/div | 0 | 0 | 0 | FALLA |
| S7b-C5 | placas únicas | 0 | 0 | 0 | FALLA |
| S7b-C6 | casos deterministas K3; no estimador de placas | 0 | 0 | 0 | FALLA |
| S7b-C7 | casos nominales K4; no estimador de placas | 0 | 0 | 0 | FALLA |
| S7b-C8 | 0.005 V/div | 0 | 0 | 0 | FALLA |
| S7b-C8 | 0.05 V/div | 0 | 0 | 0 | FALLA |
| S7b-C8 | 0.5 V/div | 0 | 0 | 0 | FALLA |
| S7b-C8 | 5.0 V/div | 0 | 0 | 0 | FALLA |

## K1 por escala

| scale_V_div | minus3_Hz | peak_db | gain_dc_signed | rise_ns | noise_pct_div | atten_4p5m_db |
| --- | --- | --- | --- | --- | --- | --- |
| 0.005 | 2007647.063619549 | 1.741861881050446e-05 | -49.498204366691645 | 182.05827863774803 | 0.32164412915359325 | 21.699597410789288 |
| 0.5 | 2006843.2901978297 | 1.771334399799645e-05 | -0.49532556828858626 | 182.08563157364756 | 0.3218227877422076 | 21.70273684683138 |

## Monte Carlo

| scale_V_div | metric | N | min | p2p5 | median | p97p5 | max |
| --- | --- | --- | --- | --- | --- | --- | --- |


## Recuperación

| scale_V_div | amplitude_V | recovery_us | bav199_conducts |
| --- | --- | --- | --- |


## Offset nominal

| vdac_V | center_V | offset_div |
| --- | --- | --- |
| 0.2 | 2.533697905117435 | 5.210904446321599 |
| 0.46249999999999997 | 2.20801637722232 | 3.908178334741139 |
| 0.7249999999999999 | 1.8823348493271979 | 2.6054522231606514 |
| 0.9874999999999998 | 1.5566533214320857 | 1.3027261115802027 |
| 1.2499999999999998 | 1.2309717935370283 | -2.6645352591003757e-14 |
| 1.5124999999999997 | 0.905290265641913 | -1.3027261115804882 |
| 1.7749999999999997 | 0.579608737746859 | -2.6054522231607042 |
| 2.0374999999999996 | 0.2539272098517436 | -3.908178334741166 |
| 2.3 | 0.02077284567231568 | -4.840795791458877 |

## Protecciones en extremos

| scale_V_div | POS | CPL | dc_limit_V | rail_plus_set_V | rail_minus_set_V | adc_min_V | adc_max_V | mux_low_margin_V | mux_high_margin_V | mux_supply_max_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## Consumo

| id | stage | kind | plus_A | minus_A | vdda_A | vref_A | dac_A | power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |


## Método y dudas

- Cambios nominales únicos: AFE ±4.90 V; C_S fijo 1.20 nF; C_EQ nominal 8.67 pF (redondeado 8.7 pF en el contrato). Rieles regulados conservan 0.5 Ω, carga 5/42 mA y 5/39 mA, TVS y todos los valores previos. El 4051 usa los mismos ocho SWI1; niveles altos del decodificador siguen el riel real. No se simulan cambios dinámicos de toma.
- Monte Carlo: semilla 2026100371, 500 placas emparejadas en cuatro escalas; offsets independientes, pasivos independientes por instancia; uniformes, factores guardados. R ±1 %, divisor ±0.1 %; C ±5 %, pistas explícitas de 1/3 pF ±50 %. El trimmer no recibe tolerancia adicional: se ajusta y recorta a 2..6 pF. Réplica C_EQ recibe ±5 % tal como manda §2 aunque la selección en prueba podría reducirlo. CMID y condensadores internos/rieles no se dispersan: §2 especifica C0G y no asigna dispersión a esos otros modelos.
- Trimmer: Rtop=Rt1+Rt2; Rbp=Rb||Rbias; Csel=Cj(V+)+Cj(|V−|)+Csel_pista+2.5 pF+CswAC+CswGND; Ctop=Rbp*(Cb+Csel+Ctap)/Rtop−Coff; Ct2=Ct1*Ctop/(Ct1−Ctop); trimmer=Ct2−Ct2fixed. Cb no se reajusta por placa: el contrato pide dispersarlo ±5 % y ajustar el trimmer. La sonda ×10 motivó el ajuste en S1b; la igualdad de tau se calcula sin sustituir la transferencia BNC→PIN por la de punta de sonda.
- Offset OPA836 ±400 µV: hoja local opa836.pdf, SLOS712J, pp. 10/12, máximo a 25 °C; a −40..125 °C llega a 1080 µV (p.12). Fuentes adicionales en serie con IN+ para los seis amplificadores; no se suprime el offset propio del macromodelo (incertidumbre de doble contabilización de su típico). OPA810 ±715 µV y AD8039 ±3 mV según contrato.
- K2 DC: barrido simétrico ±0.01 div, tres puntos, en DAC 0.2/1.25/2.3 V; ganancia DC real medida en DAC 1.25, sin usar AC como sustituto. Offset referido a centro ADC 1.25 V; DAC de centrado inferido con pendiente medida entre los dos primeros ajustes; posición restante comprobada con los extremos reales, incluido recorte. ±4.5 div exige llegar a 0.125 y 2.375 V. Esto juzga desplazamiento de traza en entrada cero, no amplitud de señal adicional a esa posición.
- K1/J8 conserva definición relativa al centro nominal del S7. J2 conserva flancos y amplitudes S7; K4 conserva final de flanco a 11.02 µs y banda ±0.1 div. Conducción BAV199: polarización directa >0.4 V, no corriente capacitiva.
- K3: cuatro combinaciones de magnitud de riel 4.80/5.00 V, barridos iniciados en 0 y continuados con paso 1 mV a ambos extremos; J5 ±40 V en cinco escalas, E5b ±100 V en POS1/100, DC y AC. No incluye seno 100 Vpk ni ESD: S7b pide E5b en continua. Se guarda cada polaridad real en el nombre .meas. La señal del 4051 se comprueba en los ocho Y y Z, incluso la toma no seleccionada. La corriente OPA810 es del pin de entrada, no la corriente de carga de salida. Corrientes de U103 incluyen su red de protección, cota conservadora.
- C6 y C7 son barridos deterministas, no fracciones poblacionales de placas; se reporta la fracción de casos y se declara que no hay Monte Carlo de sobrecarga/recuperación. C1..C4/C8 se juzgan por escala, no sólo agregando placas. Las muestras de ruido son los primeros 100 casos de las mismas 500 placas. No se presenta 2000 realizaciones emparejadas como 2000 placas independientes.
- No se dispersan GBW, I_B, ganancia abierta, ruido intrínseco ni temperatura: el contrato S7b §2 no los exige, aunque la decisión permanente es más amplia. Ruido sólo AFE de 1 Hz a 3.15 MHz con AD8038_ltspice_ruido_hoja.sub; sin ruido, cuantización, jitter ni desajuste del ADC. SWI1 está declarado para transitorio por Nexperia; uso AC/DC conserva limitación histórica. OPA836 ESD es supuesto externo; BAV99HY Rohm representa BAV99 Nexperia. TVS genérica y absorción de rieles pendientes de placa.
- Contradicción: ±2 % de 4.90 implica 4.802..4.998, y dos rieles máximos suman 9.996 V en la fuente ideal, no 9.95 V. K3 exige extremos redondeados 4.80/5.00: suma de fuente 10.0 V, margen nulo en ese extremo; se informa tensión real tras resistencia/consumo.
- Consumo de macromodelo OPA810 ≈1.9 mA frente a 3.7 mA típico de hoja: reportar simulado no revisa G.3 ni certifica autonomía. Sin carga ficticia U103B. No se eligieron remedios ni se modificaron entregables previos, modelos, STATE, DECISIONS o chequeo_claude. No hay nueva evidencia física.
