# Resultados S2 — protección P4b

Código 0; 21 simulaciones; 0 con error; 0 con advertencia. 35.789s (0.596min), 10 trabajadores.

**SMOKE: validación del ejecutor, no aceptación.**

| criterion | buffer | value | status |
| --- | --- | --- | --- |
| S2-C1 | AD8065 | Zin 0.999012–1.000280 MΩ; Cin 26.918921–28.402606 pF; Δ 1.483685 pF; gain 0.418790%; flat 0.265726%; peak 0.004267dB; fc 8.805817Hz | SMOKE/INCOMPLETO |
| S2-C1 | OPA810 | Zin 0.999093–1.000499 MΩ; Cin 26.919057–29.758938 pF; Δ 2.839881 pF; gain 0.536898%; flat 0.693691%; peak 0.008052dB; fc 8.790226Hz | SMOKE/INCOMPLETO |
| S2-C2 | AD8065 | worst cs_v=94.2569; 1.178212 × derated limit; CEQ rating unspecified | SMOKE/INCOMPLETO |
| S2-C2 | OPA810 | worst cs_v=94.2558; 1.178198 × derated limit; CEQ rating unspecified | SMOKE/INCOMPLETO |
| S2-C3 | AD8065 | VIN beyond rail 1.63549 V (<0.5); |IIN| 0.00337666 A; |differential| 4.00243 V | SMOKE/INCOMPLETO |
| S2-C3 | OPA810 | VIN beyond rail 1.32294 V (<0.5); |IIN| 0.00233938 A; |differential| 2.65653 V | SMOKE/INCOMPLETO |
| S2-C4 | AD8065 | |rails| 4.975072–4.977388 V | SMOKE/INCOMPLETO |
| S2-C4 | OPA810 | |rails| 4.976186–4.979629 V | SMOKE/INCOMPLETO |
| S2-C5 | OPA810 | OFF_LOAD_ONLY: bleed0 0.448341 V | SMOKE/INCOMPLETO |
| S2-C6 | AD8065 | BAV |I|=23.9688 A vs 4 A/1us; TVS |I|=5.81574e-12 A vs generic 38.8 A; input ∫|VI|=8.45301e-11 J; no rated transient energy | SMOKE/INCOMPLETO |
| S2-C6 | OPA810 | BAV |I|=11.965 A vs 4 A/1us; TVS |I|=5.76498e-12 A vs generic 38.8 A; input ∫|VI|=5.4321e-11 J; no rated transient energy | SMOKE/INCOMPLETO |
| S2-C7 | AD8065 | |offset BNC|=0.403697 mV | SMOKE/INCOMPLETO |
| S2-C7 | OPA810 | |offset BNC|=0.076053 mV | SMOKE/INCOMPLETO |
| S2-C8 | OPA810 | THD=0.000004%; |BAV I|=0.002707 µA | SMOKE/INCOMPLETO |

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

Archivos protegidos: 19839; cambios: []. Manifest y detalle por estado en `s2_smoke_ejecucion.json` y CSV.

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
