# Acta S11.3 — DMM bloque 1 O4

7 de octubre de 2026 · Codex · simulación de cierre según PLAN_SIMULACION_S11_3.md y entorno ENCARGO_CODEX_S11_1.md.

**Bloque no aprobado.** Hay fallos de margen y de corriente/compliance; nueve casos de recuperación en tensión no completaron la integración. Esta acta describe simulación, no ensayos físicos ni certificación de supervivencia.

## Archivos y reproducción

- `comun/dmm_bloque1_o4.inc`: O4 derivado de S11.2; dos resistencias de 1.1 kΩ, Rs de 3.3 kΩ, TVS continuo heredado de S11.1, sujeción N2 a ambos rieles según contrato actual. Sin BSS126 ni protecciones nuevas. R_X1 permanece en 100 Ω; R_X0/R_X2 se ensayan sin resistencia (1 µΩ numérico) y en 100/100 Ω.
- `ejecutar_s11_3.py`: reutiliza los ejecutores/modelos reducidos anteriores en lectura; diez trabajadores, límite 300 s/caso, `--smoke`, `--resume`, S3G4_MODELS. Nombres de cada `.meas` incluyen estados reales. Las firmas de reanudación incluyen dependencias; cambios posteriores invalidan conservadoramente firmas anteriores.
- `analizar_s11_3.py`: consolida los casos esperados y genera los CSV de esfuerzos, criterios, fugas, diodo, borne A y ESD.
- `S11_3/`: decks, logs y JSON por estado. `resultados/s11_3_attempts.jsonl`: historial de intentos.
- **Resultado definitivo:** `resultados/s11_3_campaign_audited.csv` y `resultados/s11_3_hallazgos.json`. El CSV inicial `s11_3_campaign.csv` conserva errores de extracción de R1 y no es el resultado definitivo. Los CSV `s11_3_r1_*corrected.csv` documentan sus sustituciones.

Desde el directorio DMM, con rutas del entorno entrecomilladas: ejecutar `python ejecutar_s11_3.py --smoke`, después `python ejecutar_s11_3.py --resume`, y `python analizar_s11_3.py`. No se descargó ningún modelo. Los cambios de generación/extracción no alteraron solver ni tolerancias.

Fuentes leídas: contrato S11.3 completo y referencias exigidas, planes/actas S11.1 y S11.2, ENCARGO_CODEX_S11_1, auditorías Claude S11.1/S11.2, REDISENO_BLOQUE1, dmm_rev21 (§3, §5, §7), método CH1 S2b, decisiones del 7 de octubre y LEEME de modelos. Se usan las hojas locales ya auditadas; no se repite Q0. El método ESD sigue el RC de S11.2 y no equivale al RLC calibrado de S2b.

## Número de simulaciones y tiempo

| Prueba | Estados | Válidos | Timeout |
|---|---:|---:|---:|
| R3 | 144 | 144 | 0 |
| R6 | 216 | 216 | 0 |
| R2 | 18 | 18 | 0 |
| R5 | 162 | 162 | 0 |
| R1 | 54 | 54 | 0 |
| R7 | 18 | 9 | 9 |
| R3b | 18 | 18 | 0 |
| **Total definitivo** | **630** | **621** | **9** |

Campaña inicial: **1422.777 s (23 min 42.777 s)**, 629 llamadas nuevas y un caso reutilizado. Corrección R1: 143.690 s (49 nuevas, cinco reutilizadas); corrección final de corriente DUT: 124.257 s (12 nuevas). Smoke válido inicial: 274.353 s; smokes adicionales R1: 7.278 s y 4.607 s. Estos tiempos de fases no incluyen lectura, programación y redacción.

Historial completo: **717 invocaciones LTspice**: 661 terminadas correctamente, 12 timeout, ocho errores de sintaxis y 36 errores del extractor. Los 12 timeout incluyen tres del smoke preliminar excluido; nueve corresponden a R7 de campaña. Los ocho errores de sintaxis incluyen dos decks preliminares y seis nombres `.meas` de R1 con `+`. Los 36 errores del extractor eran división por cero en tensión con fuente apagada. Se corrigieron y repitieron sólo los casos afectados. Tres preflights R3 convergieron; el primero tardó 1.923 s de LTspice / 1.991 s de pared.

Cobertura: R3 ±60 V DC y 60 Vrms con fases 0/90°, cuatro fuentes, rieles ±2 % y estados alimentado/apagado/body; R2 230 Vrms con relé abierto; R6 ±4 kV contacto y ±8 kV aire en tres modos, dos variantes RX y estados de riel/alimentación; R5 red de 0.5/1/2 Ω, arco k=1/2/3, seis fases y tres rieles; R1 diodo/fuga y tensión ±50 V DC/50 Vrms a 60 Hz y 20 kHz; R7 retira tensión a 10 s e integra hasta 12 s; R3b aplica 230 Vrms en ohmios durante 100 ms. Orden ejecutado: R3, R6, R2, R5, R1, R7, R3b.

## Criterios C1–C8

| Criterio | Resultado | Evidencia y límite |
|---|---|---|
| C1, márgenes de piezas | **No cumple / ratings incompletos** | Cc1 de 630 V alcanza 1010.689 V en contacto y 2014.753 V en aire, frente a 504 V al 80 %. Cada Rohm alcanza 0.504827 W medios a 60 Vrms, frente a 0.5 W si se toma la referencia de 1 W. Rprot alcanza 0.172459 W frente a 0.125 W si el 1206 es de 0.25 W. Faltan MPN y curvas de pulso. |
| C2, separación de rieles <11 V | **Cumple en modelo** | Máximos: R2 10.184528 V; R3 10.497647 V; R6 10.673145 V. Zener y tolerancias limitan la garantía física. |
| C3, entradas e inyección | **No cumple** | Sin RX0/RX2: X0 73.267 mA, X1 13.479 mA. Con 100/100 Ω: X0 4.644 mA pero X1 11.832 mA en aire. OPA máximo 0.634 mA <5 mA. La sujeción proxy supera además ±0.5 V por su resistencia de 1 Ω. |
| C4, ohmios con 60 V | **No certificado** | Los 144 casos completan; Rohm 0.504827 W supera ligeramente el margen de 0.5 W. TVS 0.266059 W. No hay modelo térmico/destructivo ni especificación de pulso de las resistencias. |
| C5, fugas | **Informativo** | Modelo TVS: 147.061 nA con fuente 200 nA y 410.146 nA con fuente 1 µA. Ley lineal derivada del máximo a 12 V, no fuga típica garantizada a 4 V. Requiere comprobación física. |
| C6, diodo/compliance | **No cumple** | No hay región de corriente ≥99 % de 1 mA. A 100 µA, compliance de fuente 3.046638–3.241967 V, inferior a 3.5 V. Corriente real del DUT se informa separadamente abajo. |
| C7, recuperación | **Parcial, sin cierre** | Nueve R7 ohmios completan 12 s: X0 ≤28.213 ms, N2 ≤13.301 ms tras retirada. Nueve R7 tensión llegan a timeout antes de 10 s. Un smoke de tensión completo es evidencia suplementaria, no cobertura de los nueve estados. |
| C8, puente/fusible | **Cumple en modelo** | I²t máxima por diodo GBU808 10.930299 A²s <83 A²s (50 % de 166). Pico 423.592 A; no se compara directamente con IFSM de 8.3 ms. Fusible y arco son aproximaciones, no certificación de interrupción. |

No se equiparan ratings continuos con ratings de pulso: la tensión ESD del relé no se aprueba usando su ensayo dieléctrico de 1000 Vrms/1 min. La tensión nominal 250 Vac del fusible tampoco da margen 80 % a 230 Vac (200 Vac); su carácter sacrificial entra en conflicto con un criterio universal de energía al 50 %.

## Pieza más cargada en cada prueba

Clasificación por **energía absorbida máxima**, no por fracción de rating. Rohm1/Rohm2 son equivalentes cuando se indica empate. Los CSV de esfuerzos conservan también picos y estados.

| Prueba | Pieza | Energía y ventana | Observación |
|---|---|---|---|
| R1 | Rprot1 | 0.000690361 J / aproximadamente 100 ms | Máximo entre casos normales; no es el cuello de botella del diodo. |
| R2 | Rprot1 | 1.724569 J equivalente a 10 s | 0.172441 J simulados +1.552128 J extrapolados; potencia periódica 0.172459 W. |
| R3 | Rohm1, empate Rohm2 | 5.048259 J equivalente a 10 s | 0.504816 J simulados +4.543442 J extrapolados. |
| R5 | Rshunt 0.1 Ω | 0.380015 J /20 ms | Falta especificación de pulso de su MPN. |
| R6 | Rohm2, equivalente Rohm1 | 0.001615553 J /10 µs | Cc1 por tensión y HC por inyección son límites más graves. Rohm alcanza 2942.723 V instantáneos. |
| R7 | Rohm1, equivalente Rohm2 | 5.045783 J /12 s | Integración directa: 10 s de fallo y 2 s de recuperación, sin extrapolar. Sólo casos completos. |
| R3b | Rohm1, empate Rohm2 | 1.068445 J /100 ms | 10.684452 W medios; véase límite destructivo abajo. |

La discrepancia máxima absoluta entre extracción de energía raw y `.meas` es 3.40655e-5 J; se conservan tiempos observados e intervalos de integración. No se presenta igualdad exacta ni se oculta el pequeño sobrepaso de endpoint del raw.

## Diodo a 1 mA y a 100 µA

| Ajuste | Corriente fuente con DUT a 0.65 V | Corriente real del DUT a 0.65 V | Tensión disponible con fuente ≥99 % |
|---|---|---|---|
| 1 mA | 0.528467–0.563568 mA | **0.527647–0.562716 mA** | No existe región que mantenga ≥0.99 mA. |
| 100 µA | Aproximadamente 99.999998 µA | **99.572808 µA** | **3.046638–3.241967 V**, déficit peor de 0.453362 V respecto a 3.5 V. |

A DUT=3.5 V, el ajuste 100 µA entrega al DUT sólo 26.405451–57.879940 µA. Si se exige ≥99 % en el DUT, el umbral es 1.727688–1.729292 V en este modelo: la fuga TVS pesimista y el divisor consumen parte de la corriente. Ese umbral no debe confundirse con la compliance de la fuente ni asumirse como fuga típica real. El cálculo previo de 3.55 V/unos 0.6 mA omite la caída del BAV199 de bloqueo; la resistencia fija total de 5.5 kΩ consume ya 0.55 V a 100 µA.

## ESD, fugas y borne A

Con 100/100 Ω, contacto a 4 kV: X0 ≤4.239 mA y X1 ≤8.294 mA; aire a 8 kV: X1 11.832 mA. X2 sin resistencia presenta inyección de sólo 6.232e-12 A en el proxy; la variante conjunta no justifica exigir RX2 ni permite atribuir sus efectos por separado. **No se adopta RX0/RX2 como decisión de diseño.**

La sujeción HC proxy tiene 1 Ω y no una curva I/V certificada: sin RX, excesos de pin respecto al riel de 0.573267 V y 0.513479 V. El modelo reducido no demuestra ausencia de latch-up ni comportamiento real de pines de control apagados. Pico externo BAV máximo 0.718105 A; cota conservadora Ipk²·10 µs=5.156745e-6 A²s frente a 8e-6 A²s derivados como margen de 4 A/1 µs. Incluye desplazamiento y no certifica un pulso IEC.

Fuga BAV simulada máxima: aproximadamente 0.726 pA con 200 nA y 2.028 pA con 1 µA. La hoja local BAV199 indica 3 pA típicos/5 nA máximos a 75 V, 25 °C; SMAJ12CA máximo 5 µA a 12 V. HC4051 especifica fuga OFF ±100 nA por canal/±400 nA agregado y ON ±400 nA; el canal 6 se retira de N2. Estas condiciones de hoja no garantizan por sí mismas el error a baja corriente del circuito.

| Red | I²t GBU por diodo k=1 /2 /3 (A²s) | Pico puente (A) |
|---|---|---:|
| 0.5 Ω | 3.643516 /7.286925 /10.930299 | 423.592 |
| 1 Ω | 3.386368 /6.772315 /10.157467 | 216.340 |
| 2 Ω | 2.915479 /5.820949 /8.704982 | 103.484 |

Shunt, energías máximas k=1/2/3: 0.5 Ω: 0.101821/0.172616/0.237374 J; 1 Ω: 0.121163/0.233633/0.325896 J; 2 Ω: 0.183920/0.289250/0.380015 J. Bin máximo 5.498943 V y exceso proxy 0.500962 V. En 109/162 casos se identifica tiempo exacto de apertura (20.307 µs–4.013857 ms); en 53, el umbral del extractor no la identifica por redondeo. En los 162 casos, |Ifuse| final ≤0.636323 nA y q≈6.7·k apoyan apertura al terminar 20 ms. No se usan los 109 tiempos como envolvente completa de los 162.

## Recuperación y R3b

R7 ohmios: los nueve estados integran 12 s completos; desviación final en 100 ms X0 ≤1.96056e-8 V, N2 ≤1.32123e-9 V. El umbral de recuperación es el proxy heredado de 100 µV (un count de 2 V/20000); no certifica el rango de 200 mV con count de 10 µV. R7 tensión: los prefijos raw llegan a 5.791739–8.966673 s, antes de retirar a 10 s; no hay recuperación evaluable ni extrapolación legítima. El smoke tensión alimentado/riel -2 % sí completó: X0 39.572 µs y N2 790.055 µs, pero es un único estado suplementario.

**R3b: red de 230 Vrms en ohmios.** Los 18 estados completan 100 ms. Cada Rohm disipa hasta 1.068445 J, 10.684452 W medios y 21.914220 W de pico; tensión por resistencia hasta 155.259919 V. TVS acumula 0.125271 J, equivalente a 1.252713 W medios. Las resistencias son las primeras candidatas a exceder su capacidad térmica; el TVS también queda comprometido respecto a su rating continuo.

El primer exceso de potencia instantánea de 1 W en Rohm ocurre en t=0 con fase 90° y en t≈0.668262 ms con fase 0°. **Estos son tiempos de exceso, no tiempos de rotura.** No existe modelo de destrucción ni MPN con curva de pulso/impedancia térmica para demostrar qué pieza rompe primero o cuándo. Tampoco puede garantizarse una rotura durante los 100 ms. Se documenta el esfuerzo sin inventar un fallo físico ni reclamar supervivencia de red en ohmios.

## Lista final del bloque 1 ensayado

Lista de topología simulada, **no BOM aprobada para compra**:

| Elemento | Cantidad / valor |
|---|---|
| Relé de entrada | TQ2SA-5V-Z, un contacto NO usado; Ron=0.1 Ω, Coff=1 pF en modelo |
| Rohm | 2×1.10 kΩ 2512 en serie; referencia 1 W, MPN/pulso pendiente |
| TVS | 1×SMAJ12CA |
| Rs | 1×3.3 kΩ |
| Fuente ohmios | 1×BSS84 y un diodo de bloqueo BAV199 |
| Sujeción BAV199 | Pares en X0, X1, N2 y X5: ocho uniones/cuatro encapsulados; bloqueo añade una unión/un encapsulado. Total cinco encapsulados, nueve uniones usadas. |
| Sumideros de riel | 2×BZT52C5V6; parámetros asumidos, hoja local ausente |
| Rprot | 3×33 kΩ 1206 |
| Divisor | 3×3 MΩ 1206 +900 kΩ +100 kΩ |
| Compensación | 3×3.3 kΩ con 3×100 pF C0G 630 V; 330 pF sobre 900 kΩ y 3 nF sobre 100 kΩ (ratings de estos últimos pendientes) |
| R_X1 | 100 Ω, sin cambio |
| R_X0/R_X2 | Referencia sin resistencia, ensayo 100/100 Ω; selección pendiente, ninguna variante aprobada |
| Fusible A | Littelfuse 0216, 3.15 A, 250 Vac, HRC 1500 A, I²t fusión 6.7 A²s; modelo frío 40 mΩ |
| Puente A | GBU808 |
| Shunt | 0.100 Ω 2512, referencia de diseño 2 W; MPN/pulso pendiente |
| RB / Rwarn | 10 kΩ /10 MΩ |
| Riel local | 2×1 µF, alimentación ±4.9 V y variantes ±2 %/apagado/body; load switch sin MPN seleccionado |
| Interfaces | HC4051, OPA2188 seguidor y TLV2372 fuente con modelos reducidos heredados; circuitos detallados de ganancia/P43 fuera de este bloque |

Los límites provienen de hojas locales auditadas: SMAJ pp2–3 (400 W pulso 10/1000, 1 W a TL=75 °C); BAV199 pp2–3; HC4051 pp5/9/10; OPA2188 pp4–6; BSS84 p2; TQ p6; GBU p2; fusible pp1–2. Un rating de encapsulado genérico no sustituye un MPN de resistencia.

## Contradicciones, dudas y trazabilidad

1. DECISIONS del 7 de octubre prescribe sujeción N2 a COM; el contrato actual prescribe ambos rieles. Se ejecuta el contrato, sin editar decisiones.
2. La referencia ELVIS cita 60 VDC/20 Vrms; S11.3 exige 60 Vrms. Se ensaya 60 Vrms.
3. La compliance del rediseño no incluye el BAV de bloqueo. Se informa la corriente real del DUT además de la corriente de fuente.
4. Hoja local GBU808: 200 A/166 A²s; catálogo del rediseño: 175 A/127 A²s. Se usa la hoja local; incluso 50 % de 127 supera la I²t simulada, sin resolver las condiciones de pulso.
5. Fusible: modelo 40 mΩ frente a 36.8 mΩ de hoja; 6.7 A²s nominal y arco k=1–3 son supuestos. No hay curva de corte real para estos casos ni garantía de extrapolar el rating GBU a pulsos menores de 8.3 ms.
6. Faltan MPN/curvas de pulso de resistencias y shunt, rating de varios capacitores, hoja BZT y caracterización de sujeción/inyección del modelo reducido. No se simula destrucción, calentamiento acumulado ni latch-up.
7. C5 usa fuga TVS lineal pesimista desde el máximo a 12 V. Necesita medición de prototipo; no representa un acuerdo ni una garantía típica a 4 V.
8. C7 queda abierto por nueve timeout y por el umbral proxy de count; R3b queda sin tiempo de rotura demostrable. No se alteró solver para forzar resultados.
9. No se modificó firmware ni banco/hardware. No hay evidencia de conexión o repetición física hoy.

Control de archivos protegidos: captura inicial de hashes alrededor de 19:50, no al instante de abrir sesión. Comparación final: S11.1/S11.2 (6575 archivos), models (94) y STATE/DECISIONS (dos) conservan exactamente su agregado. El agregado de los siete archivos de 01_diseno cambió entre capturas; `dmm_bloque1.html` registra modificación a las 20:01:37. Ninguna operación de esta sesión escribió en 01_diseno; no se atribuye autoría ni se revierte ese cambio. Se conserva la incertidumbre de concurrencia.

No se cambia STATE.md ni DECISIONS.md por prohibición explícita del encargo. El diario propio registra cierre y la sincronización local indexa las fuentes sin descargar contenido.
