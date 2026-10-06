# ACTA S4 — OPA836 a 3.3 V, offset y VMID

Código 0; 14 simulaciones; 51.269 s; diez trabajadores; errores 0; advertencias 0.

**Parcial: sin aceptación.**

## Criterios por variante

| variant | criterion | status | value | inherited |
| --- | --- | --- | --- | --- |


Valores derivados de resistencias: A_IN=1, A_OFF=1.24069478908, NG=3.24069478908, VMID ideal=0.858502954695 V, centro ideal=1.23127756534 V.

## ISOAC: Comprobación aislada AC

| cf | scope | gain_dc | minus3_Hz | adc_minus3_Hz | amp_minus3_Hz | amp_peak_db | amp_loss_2m_db |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C0 | follower | 0.9999992077266439 | 66253934.9190769 |  |  |  |  |
| C0 | iso |  |  | 5649671.985998263 | 19606006.474795558 | 1.50369680699552 | -0.09239692660717734 |
| C1 | iso |  |  | 4415340.387445749 | 10822354.918378957 | 0.0 | 0.0814283514514757 |

## ISODC: Comprobación aislada DC

| vdac_V | esd | adc_min_V | adc_max_V | diff_at_neg3p9_V | diff_at_pos3p9_V | ip1_current_peak_A | im1_current_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.2 | 0 | 0.0062719743198296875 | 3.291250708262074 | -0.926549062569995 | 0.4037193114693435 | 6.8250349637258875e-06 | 1.5889589709745364e-05 |
| 0.2 | 1 | 0.006918334455123211 | 3.289344168711776 | -0.6393275056040145 | 0.4036889547298692 | 9.369658411851542e-05 | 0.00010685102487503902 |
| 1.25 | 0 | 0.00484593423390343 | 3.290421567915402 | -0.5434290027911859 | 0.7865593744042851 | 8.708494351882811e-06 | 1.2023880948611609e-05 |
| 1.25 | 1 | 0.00682021259908178 | 3.289344168767669 | -0.5378109793832326 | 0.6244395919086783 | 7.906651360022381e-05 | 7.83948050337131e-05 |
| 2.3 | 0 | 0.004207359189615453 | 3.288638923598069 | -0.16123880497818288 | 1.169752927590385 | 1.0593202317555731e-05 | 1.1779633014152215e-05 |
| 2.3 | 1 | 0.006820212714943657 | 3.288633624593449 | -0.16123880058159845 | 0.6546972863485172 | 0.0001373312180239179 | 0.00013873889070608307 |

## F0: Transferencia y rango real

| vdac_V | linear_gain | linear_intercept_V | center_V | linear_nonlinearity_pct_fs | full_nonlinearity_pct_fs | full_equation_error_V |
| --- | --- | --- | --- | --- | --- | --- |


## F1: Extremos estáticos

| vmid | vdac_V | esd | adc_min_V | adc_max_V | ip1_min_V | ip1_max_V | im1_min_V | im1_max_V | diff1_peak_V | ip1_current_peak_A | im1_current_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## F7: Secuencia de encendido

| vmid | supply | ref_V | vin_V | vdac_V | adc_min_V | adc_max_V | adc_above_vdda_V | adc_below_zero_V | ip1_min_V | ip1_max_V | im1_min_V | im1_max_V | diff1_peak_V | ip1_current_peak_A | im1_current_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## F2: Respuesta en frecuencia

| vmid | cf | scope | scale_V_div | amp_loss_2m_db | amp_peak_db | adc_loss_2m_db | adc_peak_db | adc_minus3_Hz |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |


## F3: Recuperación

| vmid | cf | scope | vdac_V | amplitude_V | recovery_s | terminal_error_V | vmid_during_shift_V | vmid_after_shift_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |


## F4: Interferencia por VMID

| vdac_V | esd | vm1_shift_neg_V | vm1_shift_pos_V | adc2_shift_neg_V | adc2_shift_pos_V | crosstalk_peak_div |
| --- | --- | --- | --- | --- | --- | --- |


## F5: Gran señal

| vmid | cf | offset_div | vdac_V | fundamental_pp_V | actual_pp_V | mean_adc_V | thd_pct | adc_min_V | adc_max_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## F6: Ruido de canal completo en ADC

| vmid | cf | scale_V_div | noise_adc_uV | noise_pct_div |
| --- | --- | --- | --- | --- |


## Alimentación y demanda a VREF

| test | vmid | vdac_V | vin_V | supply | esd | iq1_min_A | iq1_max_A | iq2_mean_A | iq3_mean_A | buffer_iq_min_A | buffer_iq_max_A | vref_current_min_A | vref_current_max_A | dac_current_peak_A |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


Archivos protegidos=22075; cambios=[].


## Método y límites de interpretación

Fuentes: ENCARGO_CODEX_S4 y PLAN_SIMULACION_S4 completos; plan/acta/auditoría
S3b, plan/acta/auditoría S3; DECISIONS del 3 oct; revisión entrada §6 E16;
canal rápido bloques 7 y 9; G473 P14/P15; models/LEEME y OPA836 SLOS712J
pp.8 y 26. Sin descargas. Diez trabajadores incluso en controles.
S3b incluido sin cambios. BAV99HY y PROTECT_BAV99 copiados textualmente de
y_b3_g_s00_pos1_tap0_cpldc_nomi_bipolar_t25.cir; 470 ohm en ambos AD8039.
Se retiene RLOAD=1k y CLOAD=10p de S3b porque el contrato prohíbe cambiar
la cadena delante; era una carga sustituta de S4 en S3. Esta ambigüedad
se deja anotada: S4 se suma a ella, no se elimina silenciosamente.
OPA836 seis nodos, PD unido a VDDA. Sensores ideales de 0V miden corriente
TOTAL de cada entrada, incluyendo diodos diferenciales añadidos. DESD es
suposición contractual (Is=1e-15 N=1 Rs=10), no pieza ni validación física.
F1/F4 se repiten con el macro sin diodos para cuantificar la dependencia.
M2 siempre tiene tres S4 reales; entradas de CH2/3=0, DAC2/3=1.25 V.
Sólo NOISE usa AD8038_ltspice_ruido_hoja.sub; modelos intactos.
R_ADC68/C_ADC470p más C_SH5p estático. Sin filtro S5 ni kickback S6.

F0 incluye todas las 51 posiciones -1.25..1.25 por DAC; se informa la
no linealidad del barrido completo, incluida saturación, además de ajuste
lineal restringido al intervalo ideal 0.2..3.1V. C1 no oculta el recorte.
Rango de offset medido a Vin=0 respecto del centro a DAC1.25, no una
extrapolación ideal. F0 es M1-C1 por contrato; los demás C1 de la tabla
heredan esa prueba y NO certifican F0 de M2. F1/F7/F4 sólo C1; C0 hereda
C2/C3/C6 según el cruce definido en 2.3, no un transitorio C0 de arranque.
F2 aislada M1; M2 hereda esa respuesta aislada, pero su cadena se simula.
F2 separa O1 (antes del RC, cargada por él) y ADC1 (pin después del RC).
Frecuencias 200 puntos/década; pérdida positiva respecto de AC a1Hz;
pico hasta100MHz. Controles aislados hasta1GHz para localizar -3dB.
F1 -5..5V, 10mV, extrema por raw y .meas independientes.
F4 -3.9..3.9V sostenido con DAC extremos y nominal, variación respecto
de CH1=0 en el mismo circuito; sin redefinir la línea base por otro macro.
F3 flancos10ns, pulso10us, dt<=0.5ns, recuperación desde FINAL del flanco
de bajada hasta permanecer en +/-25mV del punto inicial; ventana30us.
Si no recupera se informa censura, no se toma el último valor como cero.
F5 seno2MHz, amplitud de fuente calculada desde F2 de la misma variante
para2Vpp en pin ADC; offset0,+/-2div, DAC calculado desde RF/ROFF.
THD armónicos2..9, 20ciclos coherentes, rejilla65536; se informa recorte.
F6 integra ONOISE en el PIN de1Hz a3.15MHz (no inoise/BNC), cuadrado
por trapecios con extremo interpolado; porcentaje respecto de0.25V/div.

F7(a) VDDA=0, +/-5 presentes, Vin=+/-3.9, DAC=0. Como el plan no fija
VREF apagada, se prueban VREF=0 y2.5V sin decidir su secuencia real.
F7(b) rampa VDDA0..3.3 en1ms; suposición explícita VREF sigue
VDDA*2.5/3.3; DAC sigue VREF en proporciones0.2/2.5,1.25/2.5,2.3/2.5.
La alimentación <2.5V está FUERA del rango recomendado del macro/hoja.
Resultados de arranque/apagado son diagnóstico del macro, no garantía
de silicio. Se comprueba ADC frente a VDDA instantánea, no sólo3.3V.
Consumo por sensor de alimentación por amplificador; RT es demanda de
VMID a VREF, no incluye ADC/DAC ni ruido real de REF3325/DAC idealizados.
Valores medios en barrido son medias de puntos, no consumo temporal.

Contradicciones no resueltas: E16 pide rizado sample-and-hold0.1LSB,
pero el contrato usa DAC con buffer continuo y no aporta modelo S/H;
no se certifica rizado. La ecuación positiva en la guía de CH1 es previa
a la sumadora inversora de este contrato. El rango ideal +/-5.21div no
asegura igual rango REAL con recorte contra masa. Ganancia de ruido3.24
no permite inferir63MHz de ancho de banda con resistencias10k y parásitas;
se mide. BAV99 de Nexperia se simula con modelo Rohm contractual.
Fuentes ideales no evalúan el power path, impedancia real ni REF/DAC
apagados. Sin selección M1/M2 o C0/C1, ni modificaciones a valores.
CSV ordenados/deterministas; decks y logs retenidos; raw regenerables
se eliminan después de análisis correcto. Error eléctrico es válido;
código0 sólo indica campaña completa, no aceptación.
