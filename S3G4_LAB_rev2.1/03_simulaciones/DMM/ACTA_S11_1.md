# Acta S11.1 — DMM bloque 1

7 octubre 2026 · Codex · segunda reanudación, contrato PLAN_SIMULACION_S11_1.md §3b–§3c.

**Bloque no aprobado.** La finalización numérica no acredita supervivencia. No se cambiaron piezas ni se simularon remedios.

## Ejecución

Preflight P3: 1/1 ok en 38.044 s. Smoke inicial: 14/14 ok en 67.573 s; smoke tras corregir la carga externa apagada: 14/14 ok en 42.689 s; último smoke de estados con resume: 14/14 ok en 0.033 s, todos conservados por firma. Campaña final con resume: 570 casos, 536 ok, 1969.332 s de pared, diez trabajadores y límite 300 s/caso. `S3G4_MODELS`, `--resume`; prioridad P3, P2, P4, P5, P1, P6, P7. No se reintentaron los casos fallidos con otros ajustes.

El primer tramo de campaña se detuvo a los aproximadamente 2102 s para corregir Riqother en P4. El segundo se detuvo tras aproximadamente 1006 s adicionales al detectar que P1 diodo/fuga abría el relé a los 3 ms. P1 diodo/fuga ahora mantiene el relé cerrado, con nuevas firmas; los intentos con DUT desconectado quedan excluidos de C5/C6. Se conservan por firma exacta los ok no afectados, y se repiten las pruebas corregidas. Como resume solo conserva ok, cuatro P1 de tensión agotados previamente a 300 s se repiten sin cambiar ajustes. Tiempo aproximado de campaña acumulado: 5077.332 s, más preflight y smoke. Código de salida final: 1.

Revisión raw: 34 P1 ok terminan entre 0.10 y 8.72 µs después del stop solicitado. El lector anterior confundía igualdad exacta con cobertura y daba raw_complete=False. `s11_1_campana_auditada.csv` corrige cobertura (último punto ≥ stop), conserva raw_endpoint_exact y no modifica ninguna medida. Las medidas finales de LTspice corresponden al tiempo solicitado; las energías auditadas integran el intervalo observado real, incluido ese pequeño excedente, identificado por raw_overrun_s. No hubo resimulación por esta corrección.

| Prueba | Casos | Estado |
|---|---:|---|
| P3 | 216 | {'ok': 216} |
| P2 | 18 | {'ok': 18} |
| P4 | 72 | {'ok': 72} |
| P5 | 42 | {'ok': 42} |
| P1 | 108 | {'ok': 74, 'timeout': 33, 'numerical_failure': 1} |
| P6 | 96 | {'ok': 96} |
| P7 | 18 | {'ok': 18} |

## P0 y modelos

Tabla completa: `resultados/s11_1_p0.csv`. Páginas de los PDF locales, sin descargas.

| Pieza | Hoja/página | Límites relevantes |
|---|---|---|
| PTCTL4MR500SBE | ptctl.pdf p.1 | 50 Ω ±20 %; 600 Vrms/DC; mantenimiento 50 mA a 70 °C; disparo 140 mA a 25 °C; máximo 1 s a 1 A; Imax 1 A |
| SMAJ12CA | SMAJ12CA.pdf pp.2–3 | 400 W no repetitivo, 1 W continuo a TL=75 °C; 12 V standoff; 13.3–14.7 V a 1 mA; 19.9 V a 20.1 A; 5 µA máx a 12 V |
| BAV199 | BAV199.pdf pp.2–3 | 75 V DC/85 V repetitivo; 140 mA; 250 mW; 4 A/1 µs, 1 A/1 ms; fuga 5 nA a 75 V/25 °C |
| DF08S | DF08S.pdf p.2 | 800 V, 1 A, 50 A/8.3 ms media senoide; I²t 10.4 A²s solo t<8.3 ms; VF 1.1 V a 1 A por diodo |
| BSS84 | BSS84.pdf p.2 | VDS −50 V, VGS ±20 V, ID −130 mA, IDM −1.2 A, 300 mW; Ciss/Coss/Crss 24.6/4.7/2.8 pF típicos |
| TQ2SA | C46047.pdf p.6 | Conmutación 125 Vac/220 Vdc, 2 A; aislamiento abierto 1000 Vrms/1 min; suelta máx 4 ms sin diodo |
| OPA2188 | opa2188.pdf pp.4–6 | 40 V alimentación; entrada riel ±0.5 V y ±10 mA; 9.5 pF común, 6 pF diferencial; 415 µA/canal típico |
| TLV2372 | tlv2372.pdf pp.8,11,13 | 16.5 V alimentación; entrada riel ±0.2 V y ±10 mA; 8 pF común; 550 µA/canal a 5 V, 750 µA a 15 V |
| 74HC4051 | 74HC_HCT4051.pdf pp.1,5,9–10 | Límite contractual span 11 V; clamp ±20 mA, canal ±25 mA; Ron 60 Ω típico a 9 V; consumo 16 µA máx a 10 V/25 °C; Yn 5 pF, Z 25 pF |

No hay fuga garantizada de TVS/BAV199 a 4 V ni curvas térmicas de la PTC. Faltan MPN y ratings de resistencias, capacitores, fusible y derivador: un encapsulado no certifica energía de pulso. El límite contractual span del 4051 no debe confundirse con su tabla VCC referida a GND; también se informa su rango recomendado de 10 V.

Modelo PTC: θ normalizada, dθ/dt=P/Ecrit−θ/τ; G=Rcold·0.14², Ecrit=−G/ln(1−0.14²), τ=50.518759 s. R=Rcold hasta θ=1 y crecimiento exponencial a 1 MΩ entre θ=1 y 1.4. Para 40/60 Ω: Ecrit=39.606707/59.410060 J y G=0.784/1.176 W. θ=1 se llama disparo. El punto 1 A/1 s se reproduce, pero el umbral asintótico de 140 mA, Rcaliente y enfriamiento son supuestos; no se identificó masa térmica física ni temperatura. C4 es orientativo.

P2–P7 usan `comun/dmm_reducido_s11_1.inc`: protección y capacidad de entradas, canal seleccionado resistivo y consumo equivalente. Los límites de corriente se evalúan, no recortan la corriente. Ron de los diodos internos=1 Ω es aproximado, sin curva IV publicada; TLV usa 550 µA/canal a 9.8 V como aproximación. Encendido, la suma de resistencias de consumo equivale a 3 mA a 9.8 V, sin doble cuenta. Apagado, el generador elimina la carga residual externa Riqother y mantiene solo las resistencias equivalentes de IC (1.946 mA a 9.8 V); su comportamiento apagado/inversamente alimentado no está validado. P43 se conserva como fuente abstracta con cumplimiento, terminales de sentido TLV en ms/msource; no representa el lazo completo ni sus referencias. BSS84 conserva capacitancias y diodo intrínseco: su hoja no especifica diodos de puerta a rieles y no se inventan. P1 conserva la implementación completa previa del OPA/4051 y BSS84; el lazo P43 anterior también era abstracto, no un macromodelo TLV2372 completo.

## Criterios (100 Ω | 330 Ω)

| Criterio | R_S = 100 Ω | R_S = 330 Ω |
|---|---|---|
| S11.1-C1 | FALLA: DF08S I²t >5.2 A²s (50 % de 10.4); también supera 50 A. Conmutación de relé a 230 Vac sobre 125 Vac. Márgenes R/C/fusible/derivador no verificables. | FALLA: DF08S I²t >5.2 A²s (50 % de 10.4); también supera 50 A. Conmutación de relé a 230 Vac sobre 125 Vac. Márgenes R/C/fusible/derivador no verificables. |
| S11.1-C2 | FALLA: span 24.2002 V; inyección externa pico 0.005383 A y clamp interno por pin máx 0.062835 A vs 0.003 A. No se suman máximos de instantes distintos. | FALLA: span 20.7141 V; inyección externa pico 0.00114245 A y clamp interno por pin máx 0.0256875 A vs 0.003 A. No se suman máximos de instantes distintos. |
| S11.1-C3 | FALLA: span máx P1–P6 24.2002 V; exceso máximo de pines observados 13.0858 V; VDS BSS84 24.3004 V; corriente de paso en red 0.118607 A (límite continuo C3 0.065 A). Picos internos derivados de IV simplificada en CSV por pin, sin certificar curva de hoja. | FALLA: span máx P1–P6 22.8067 V; exceso máximo de pines observados 13.0858 V; VDS BSS84 20.6659 V; corriente de paso en red 0.0361234 A (límite continuo C3 0.065 A). Picos internos derivados de IV simplificada en CSV por pin, sin certificar curva de hoja. |
| S11.1-C4 | ORIENTATIVO / NO CERTIFICADO: disparo máximo observado 0.0779018 s; faltan curva térmica y 10 s simulados/estado caliente validado. | ORIENTATIVO / NO CERTIFICADO: disparo máximo observado 0.0779019 s; faltan curva térmica y 10 s simulados/estado caliente validado. |
| S11.1-C5 | FALLA MODELO: fuga modelada TVS+BAV N2 735230 ppm a 0.2 µA (lím.1000; 4/6 completos), 409827 ppm a 1 µA (lím.200; 4/6 completos); sin garantía de fuga a 4 V. | FALLA MODELO: fuga modelada TVS+BAV N2 735230 ppm a 0.2 µA (lím.1000; 5/6 completos), 409827 ppm a 1 µA (lím.200; 4/6 completos); sin garantía de fuga a 4 V. |
| S11.1-C6 | PASA TENSIÓN EN CASOS COMPLETOS / NO CERTIFICADO: tensión mínima 4.11264 V (lím.3.5 V), corriente fuente mínima 0.000995085 A, solicitada 1 mA; 4/6 completos. Fuente abstracta y corriente no exactamente 1 mA; no garantiza C6 a 1 mA exacto. | PASA TENSIÓN EN CASOS COMPLETOS / NO CERTIFICADO: tensión mínima 3.90401 V (lím.3.5 V), corriente fuente mínima 0.000994942 A, solicitada 1 mA; 1/6 completos. Fuente abstracta y corriente no exactamente 1 mA; no garantiza C6 a 1 mA exacto. |
| S11.1-C7 | NO CERTIFICADO: recuperación auxiliar máx 0.999663 s; P7 retira red a 1 s y observa hasta 2 s; no parte del estado tras 10 s ni del enfriamiento de hoja. | NO CERTIFICADO: recuperación auxiliar máx 0.999653 s; P7 retira red a 1 s y observa hasta 2 s; no parte del estado tras 10 s ni del enfriamiento de hoja. |

## P5 — DF08S por diodo

Peor caso entre fase cero/pico, riel nominal/±2 % y los cuatro diodos. Pico e I²t pueden corresponder a casos distintos. Fusible cerrado durante 10 ms; su apertura no se simula. Valores de modelo, ajustado a 1 A: la extrapolación IV a cientos de amperios no está validada. Comparación con máximos de hoja, sin confundirlos con el criterio más estricto del 50 %. No se extrapola energía en este ensayo.

| Z red Ω | R_S Ω | Pico A / 50 A | I²t hasta 8.3 ms A²s / 10.4 | I²t 10 ms A²s (informativo) | E derivador simulada J | Pico entrada B V |
|---:|---:|---:|---:|---:|---:|---:|
| 0.5 | 100 | 386.213 / 7.72426× | 603.676 / 58.0458× | 603.676 | 19.5787 | 18.2365 |
| 0.5 | 330 | 386.213 / 7.72426× | 603.676 / 58.0458× | 603.676 | 19.5787 | 18.2365 |
| 1 | 100 | 196.709 / 3.93417× | 153.149 / 14.7259× | 153.149 | 6.81903 | 10.587 |
| 1 | 330 | 196.709 / 3.93417× | 153.149 / 14.7259× | 153.149 | 6.81903 | 10.587 |
| 2 | 100 | 92.7964 / 1.85593× | 32.5599 / 3.13076× | 32.5599 | 2.57721 | 6.35327 |
| 2 | 330 | 92.7964 / 1.85593× | 32.5599 / 3.13076× | 32.5599 | 2.57721 | 6.35327 |

I²t del derivador en 10 ms = E_simulada/0.100 Ω; valores en `s11_1_df08s.csv`. Su hoja y rating de pulso no están disponibles, por lo que no se certifica el margen del derivador.


| P5 fusible abierto | Pico X5 V | Mínimo X5 V | Pico corriente por Rwarn A |
|---:|---:|---:|---:|
| R_S=100 Ω | 5.49652 | -5.49652 | 3.19969e-05 |
| R_S=330 Ω | 5.49652 | -5.49652 | 3.19969e-05 |

## Rieles con DMM apagado

| Diodo cuerpo | R_S Ω | Máximo rp V | Mínimo rn V | Máximo span V / 11 V |
|---|---:|---:|---:|---:|
| 0 | 100 | 9.58338 | -7.77668 | 9.08276 / 11 |
| 0 | 330 | 9.58339 | -7.77668 | 9.08277 / 11 |
| 1 | 100 | 5.38257 | -5.37917 | 6.24358 / 11 |
| 1 | 330 | 5.38257 | -5.37917 | 6.24358 / 11 |

## P3 — disparo y energía de TVS

| R_S Ω | PTC Ω | Apertura ordenada s | Casos ok | Disparo mín/máx s | E TVS semiciclo máx J | E TVS simulada máx J | E TVS extrapolada válida máx J | Extrapolaciones válidas |
|---:|---:|---|---:|---|---:|---:|---:|---:|
| 100 | 40 | 0.02 | 18 | sin dato / sin dato | 0.646129 | 1.85903 | 7.63952e-05 | 18/18 |
| 100 | 40 | 0.1 | 18 | 0.0338135 / 0.0356673 | 0.646129 | 3.05719 | 7.63951e-05 | 18/18 |
| 100 | 40 | nunca | 18 | 0.0338135 / 0.0356673 | 0.646129 | 3.27853 | sin dato | 0/18 |
| 100 | 60 | 0.02 | 18 | sin dato / sin dato | 0.418066 | 1.2022 | 7.63952e-05 | 18/18 |
| 100 | 60 | 0.1 | 18 | 0.0758957 / 0.0779018 | 0.418066 | 4.19008 | 7.6395e-05 | 18/18 |
| 100 | 60 | nunca | 18 | 0.0758957 / 0.0779018 | 0.418066 | 4.68552 | sin dato | 0/18 |
| 330 | 40 | 0.02 | 18 | sin dato / sin dato | 0.646158 | 1.85911 | 7.63805e-05 | 18/18 |
| 330 | 40 | 0.1 | 18 | 0.0338135 / 0.0356673 | 0.646158 | 3.05764 | 7.63805e-05 | 18/18 |
| 330 | 40 | nunca | 18 | 0.0338135 / 0.0356673 | 0.646158 | 3.28286 | sin dato | 0/18 |
| 330 | 60 | 0.02 | 18 | sin dato / sin dato | 0.418096 | 1.20228 | 7.63805e-05 | 18/18 |
| 330 | 60 | 0.1 | 18 | 0.0758958 / 0.0779019 | 0.418096 | 4.19048 | 7.63805e-05 | 18/18 |
| 330 | 60 | nunca | 18 | 0.0758958 / 0.0779019 | 0.418096 | 4.69011 | sin dato | 0/18 |

| R_S Ω | Corriente PTC pico A | Corriente R_S pico A | BAV199 N2 pico por diodo A | TVS pico W |
|---:|---:|---:|---:|---:|
| 100 | 7.69598 | 0.118607 | 0.0149721 | 128.378 |
| 330 | 7.69546 | 0.0361234 | 0.0041511 | 128.381 |

## Energía simulada y extrapolada

`s11_1_energias.csv` separa para cada caso/pieza el tiempo real y la energía integrada, la estimación de los segundos restantes y el total. Una extrapolación rechazada se conserva en columna separada, sin promoverla a resultado. Los extremos de tablas no se suman entre sí: pueden pertenecer a casos diferentes.

LTspice corrió como máximo 1 s en red y 10 µs en ESD (paso 1 ns). Desviación pendiente respecto de §3b: el ejecutor no corta dinámicamente al primer θ=1; sigue hasta 1 s, por lo que puede incluir calentamiento/enfriamiento y no debe describirse como tramo terminado exactamente al disparo. Python extrapola desde los últimos cinco ciclos solo si el raw terminó, la variación de potencia es <5 %, deriva de riel <10 mV y, con relé sin abrir, RPTC final ≥0.99 MΩ. No se ejecutó un régimen caliente separado: si esa condición no se alcanza se rechaza la extrapolación, y no hay validación de supervivencia durante 10 s.

| Prueba | R_S Ω | Pieza de mayor energía simulada registrada | Energía J |
|---|---:|---|---:|
| P3 | 100 | ptc | 74.0423 |
| P3 | 330 | ptc | 74.0397 |
| P2 | 100 | rprot1 | 0.170647 |
| P2 | 330 | rprot1 | 0.170647 |
| P4 | 100 | rprot1 | 0.172465 |
| P4 | 330 | rprot2 | 0.172465 |
| P5 | 100 | rshunt | 19.5787 |
| P5 | 330 | rshunt | 19.5787 |
| P1 | 100 | rprot1 | 0.000343586 |
| P1 | 330 | rprot1 | 0.000343586 |
| P6 | 100 | rprot1 | 0.000854545 |
| P6 | 330 | rprot1 | 0.000854546 |
| P7 | 100 | ptc | 74.0439 |
| P7 | 330 | ptc | 74.0413 |

Esta clasificación no es el menor margen frente a hoja: no hay límites de energía de todas las piezas. El CSV por caso identifica la pieza más cargada entre las registradas; excluye disipación interna de integrados, fusible y diodos DF08S.

## Dudas, desviaciones y pendientes

- PTC y TVS sin dato garantizado de fuga a 4 V; modelo térmico no físico único. C4 no certificable.
- Relé contractual suelta 3 ms; hoja máximo 4 ms sin diodo. Conmutación a 230 Vac no respaldada por el rating 125 Vac. No se ajustaron estos valores para ocultar la contradicción.
- El modelo reducido no caracteriza latch-up, avería, alimentación inversa, transferencia ni lazo TLV. El total de inyección de las medidas heredadas solo suma BAV externos. `s11_1_pines_reducidos.csv` deduce picos por pin HC/OPA de Vexceso y su IV lineal; estos picos no se suman entre sí ni sustituyen una medida simultánea por riel. No certifica C3 aunque el transitorio termine.
- ESD es la red simple 150 pF/330 Ω del contrato (8 kV con 300 Ω de arco adicionales); no es el generador RLC calibrado sobre 2 Ω de S2b. Los picos orientan y no certifican IEC.
- P7 no satisface la exposición previa de 10 s ni enfriamiento de hoja; sus tiempos auxiliares no son C7.
- No hay elección de R_S ni remedios. Claude revisa aparte el borne A. No se tocaron STATE.md, DECISIONS.md, diseño, modelos del fabricante ni otros canales.

## Archivos y trazabilidad

`ejecutar_s11_1.py`, `leer_raw_s11_1.py`, `resumir_s11_1.py`, `comun/dmm_bloque1.inc`, `comun/dmm_reducido_s11_1.inc`; decks/logs/JSON en `S11_1/`; CSV/JSON y logs `segundo_*` en `resultados/`; diario `ai-context/journal/2026-10-07-codex-s11-1.md`. Los raw se eliminan tras extraer integrales para limitar disco; `--keep-raw` permite conservarlos. Firmas actuales del deck, include y bibliotecas; no se recuperan resultados legado.
