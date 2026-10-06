# ACTA S3b — Protección diferencial de U103A

Código 0; 6 simulaciones; 16.017 s; diez trabajadores; errores 0; advertencias 0.

**Comprobación parcial, sin aceptación.**

## Criterios por variante

| variant | criterion | status | value |
| --- | --- | --- | --- |


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

|  |
|  |


## B3: Barrido estático y márgenes

| variant | scale_V_div | u103a_differential_peak_V | u103b_differential_peak_V | u103b_margin_V | switch_current_peak_A | diode_p_current_peak_A | diode_n_current_peak_A | opa810_current_peak_A | inplus_min_V | inplus_max_V | inplus_rail_margin_V |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |


## B4: Recuperación desde final de pulso

| variant | amplitude_V | polarity | BNC_plateau_V | recovery_s | terminal_error_V | max_step_pulse_and_5us_s |
| --- | --- | --- | --- | --- | --- | --- |


## B5: Gran señal

| variant | scale_V_div | output_pp_V | thd_pct | max_dvdt_V_us |
| --- | --- | --- | --- | --- |


## B6: Offset OP frente a S3

| variant | scale_V_div | temp_C | output_offset_V | baseline_offset_V | added_offset_div |
| --- | --- | --- | --- | --- | --- |


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
