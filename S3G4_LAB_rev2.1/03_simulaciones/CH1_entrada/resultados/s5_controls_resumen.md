# ACTA S5 — filtro anti-alias de CH1

Código 0; 6 simulaciones; 5.643 s; diez trabajadores; errores 0; advertencias 0.

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


## Comparativa (nominal5mV/div; ruido peor escala)

| candidate | minus3_MHz | atten_3p25m_db | atten_4p5m_db | atten_6p5m_db | overshoot_pct | square_overshoot_pct | rise_ns | gd_variation_ns | noise_max_pct_div | mc_within_pct | thd_max_pct | u105_idle_power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BE | nan | None | None | None | None | None | None | None | nan | None | nan | None |
| TR | nan | None | None | None | None | None | None | None | nan | None | nan | None |
| BU | nan | None | None | None | None | None | None | None | nan | None | nan | None |

## Monte Carlo

|  |
|  |


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


## G2 flancos y cuadrada

| candidate | scale_V_div | kind | overshoot_pct | rise_ns | settling_1pct_ns | square_fall_settling_ns | u105_idle_power_mW |
| --- | --- | --- | --- | --- | --- | --- | --- |


## G4 gran señal

| candidate | freq_Hz | amplitude_V | fundamental_pp_V | amplitude_error_pct | thd_pct | adc_min | adc_max |
| --- | --- | --- | --- | --- | --- | --- | --- |


## G5 ruido

| candidate | scale_V_div | noise_uV | noise_pct_div |
| --- | --- | --- | --- |


## G6 sobrecarga

| candidate | amplitude_V | recovery_us | terminal_error_V | a_differential_V | b_differential_V | a_vip_peak_A | a_vim_peak_A | b_vip_peak_A | b_vim_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


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
