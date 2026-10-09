# ACTA S13 — DMM: ohmios, diodo y continuidad

8 oct 2026 · Codex · Contrato: PLAN_SIMULACION_S13.md; ESTUDIO_BLOQUE3.md íntegro, especialmente §9. Referencias: PLAN/ACTA S11.4, ACTA S12d y entorno ENCARGO_CODEX_S11_1.md.

## Alcance y reproducción

Confirmación de c1: relé TQ2SA → 3 × 510 Ω → N1 (SMAJ12CA, inyección aquí) → R_S 2.7 kΩ → sujeciones. P43: TLV2372, BSS138 de referencia/habilitación y BSS84 de paso, fuerza/sentido por dos 74HCT4051, compensación 1 kΩ + 1 nF; 2 MΩ con 420 kΩ y 20 MΩ con 1.7 MΩ. Diodo por X2 ×10.1, continuidad a 1 mA con un Schottky negativo en PB14. P33 excluida. No se cambiaron piezas ni archivos anteriores, 01_diseno, models, STATE o DECISIONS. No hubo descargas ni prueba física.

Desde la raíz (entrecomillar las rutas):

```powershell
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --preflight
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --smoke
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/ejecutar_s13.py" --resume
python -B "S3G4_LAB_rev2.1/03_simulaciones/DMM/analizar_s13.py"
```

10 trabajadores, 900 s/caso; S3G4_MODELS y S3G4_LTSPICE admitidos. LTspice por argumentos independientes, sin shell. Resume exige coincidencia de firma del deck/ejecutor/include/dependencias S11. Archivos por caso en S13: cir, log, raw y json. El nombre largo de cada .meas expresa las variables de estado y, en C1, el estado completo heredado. Los filenames son cortos por el límite de ruta Windows.

## Simulaciones y tiempo

502 estados únicos; 502 completos y 0 errores. Smoke: 10 casos, 182.413 s. Campaña: 502 casos, 10 reutilizados, 1252.115 s. Pared smoke+campaña: **1434.528 s (23.91 min)**. Nuevos lanzamientos en campaña: 492. No se suman al tiempo definitivo la lectura, programación ni los preflights/smokes de depuración interrumpidos: no se conservó un registro íntegro de sus tiempos y lanzamientos, por lo que no se inventa un total histórico.

Distribución: {"compliance": 100, "phase": 80, "startup": 15, "thermal": 15, "esd": 144, "fault60": 72, "continuity": 6, "leak": 54, "external": 12, "diode": 4}. C4 es cálculo numérico, no una simulación LTspice. C7 adicional responde a la prueba de diodo que aparece en §9 del estudio aunque el plan nombra C1–C6.

Completitud validada con el último tiempo del RAW; medidas de aceptación calculadas desde ese RAW. En 6 casos C3, el .meas FIND del borne exactamente al tiempo final falla por redondeo del último instante (320 µs); el RAW sí completa y conserva el valor final. Las medidas de cruce, apertura y rebotes se extraen de la traza, no de ese FIND. Se registra aparte en s13_measurement_notes.csv, sin presentarlo como fallo físico de continuidad ni como .meas exitoso.

## Tabla C1–C6

| Criterio | Resultado medido | Dictamen / alcance |
|---|---|---|
| C1, protección | R1 continua 0.4837 W/pieza, pico 23.38 V; rieles 10.5692 V; BAT54 inversa 14.589 V; BSS84 19.707 V | Cumple continuo; pulso condicionado al rating/curva del MPN. Modelo reducido de S11.4 |
| C2, P43 | Compliancia ≥0.3 V: 97/100; corriente inicial ±1 %: 97/100; PM mínimo 74.45°; peor asiento/límite 0.778 | Cumple rendimiento de compliancia ≥95 %, fase y asiento; 3 errores iniciales marginales. Deriva de pasivos no garantizada; Ron/capacidades condicionados al modelo |
| C3, continuidad | Cierre 30.558 µs; apertura 0.298 µs; máximo 2 transiciones | Cumple dinámica sin rebotes; umbral calibrado condicionado a P41 |
| C4, INL | Máximo garantizado 91.27 %, proxy calibrado 78.12 % | Cumple cálculo con INL de hoja; proxy 10 cuentas, no curva medida |
| C5, fugas | 4/18 combinaciones pasan la deriva de corriente; 2/18 al invertir el divisor | Condicionado al prototipo. Fallos a 1 nA marginales de criterio; 10 nA incompatibles |
| C6, P34 | ±20 mV, ±5 V y ±60 V; X2 ×10.1 y ×1 | Cumple lógica modelada, umbral 16 cuentas para ruido −3 y offset simulado; ADC ideal y fuente ordenada OFF. P33 excluida |

## C1: protección y esfuerzo

El generador, GDT y rieles son los de S11.4, sin rediseñar. Se retienen todos los estados T2 y T4 y se añade fuente a 1 mA en T4. El camino R1 se cambia exclusivamente al c1 contratado; R_S y las sujeciones permanecen intactos. Los valores del viejo audit de dos resistencias NO certifican las tres de c1: usar r1_1/r1_2/r1_3 del CSV. TVS, R_S, zéner y D2p/D2n mantienen sus claves de auditoría; máximos en resultados/s13_stress_summary.json.

Para continua/AC: potencia por R1 ≤1 W, tensión ≤200 V, TVS ≤0.5 W, corriente de sujeción continua ≤5 mA y separación de rieles ≤10.6 V. BAT54 ≤24 V inversos y BSS84 ≤40 V. TVS media continua: 0.3907 W; R_S: 0.02845 W; zéner: 0.01449 W. Sujeción continua pico: 4.8595 mA, frente al pico total de arranque 5.1319 mA. La ventana continua es el último intervalo de cinco ciclos de 60 Hz (también para DC); ambos valores se conservan en CSV. El pico de arranque no se presenta como corriente continua.

La ESD lleva R1 a 358.465 V/pieza, por encima de 200 V si se aplica literalmente el límite de trabajo del §9. **C1 queda condicionado/no demostrado en pulso**: clasificar como falta de criterio/rating de impulso, sin afirmar destrucción. La potencia media sobre 50 µs NO es potencia continua. Falta la curva de impulso del HoCR2512 de 510 Ω. El GDT mantiene los supuestos de S11.4: arco 20 V, mantenimiento 10 mA, encendido/extinción 1 ns y extrapolación de cebado a frentes ESD. No prueba el retraso del GDT real ni supervivencia de PCB.

P43 completo en ESD falló numéricamente en xb2:D17 (timestep 1.25e-19 s a ~100 ns). Se conserva para C1 el modelo reducido de exposición validado en S11.4: fuente abstracta, diodo de cuerpo y capacidades de BSS84, BAT54 real de biblioteca. C2 sí usa los macromodelos completos. Esto es una **limitación de modelo**, no prueba de daño real.

## C2: qué se barrió y qué no se garantiza

100 placas Monte Carlo uniformes, semilla 1308: riel 4.8–5.0 V; R_ref/R_set ±0.1 %; Vos de cada TLV2372 ±4.5 mV; Vth BSS84 −0.8…−2.0 V; Ron nominal 60–130 Ω; capacidades explícitas ×0.5…1.5. Compliancia se busca con corriente ≥99 % de la corriente inicial de esa placa por barrido 0–4.5 V, resolución 10 mV, y se resta V_x a fondo con esa misma corriente. El CSV de campaña conserva también el umbral estricto contra corriente nominal; para compliancia tras calibrar usar s13_compliance_summary.csv. El error inicial ±1 % se evalúa aparte: un offset de ganancia no debe confundirse con pérdida de regulación. El fondo de 2 kΩ es el exigente; 200 Ω tiene el mismo suministro y menor V_x. No son 100 placas fabricadas ni intervalo estadístico de rendimiento garantizado.

80 esquinas AC (16 por cada una de las cinco corrientes). Ruptura/inyección de lazo y extracción del primer cruce de unidad según el estudio; el resto de parámetros nominales. No se exploró una esquina simultánea de todos los Vos en AC. 15 transitorios con 300/600/900 pF de TVS; arranque medido desde borne inicialmente a 0 V con rieles establecidos. No se acredita aquí encendido frío ni secuencia real EN/INH. 15 puntos térmicos de SPICE (18/23/28 °C); máximos respecto a 23 °C por rango: 0.005, 0.005, 0.005, 0.013, 0.042 ppm.

**Ron de SWI1:** la biblioteca tiene una resistencia efectiva propia y no permite el mismo parámetro ideal de los decks de estudio. Se añade max(Ron−60,0) Ω y se publica force_ron_ohm en las filas DC. Por ello el barrido total no es exactamente 60–130 Ω y las capacidades internas SWI1 no varían con las capacidades explícitas. No se retoca la biblioteca ni se presenta este desajuste como dispersión del MPN: **limitación de modelo**.

El BSS138 usa un VDMOS genérico (Vth 1.3 V, Kp 1.3, capacidades explícitas) **supuesto**, no modelo garantizado del MPN. BSS84 y BAT54 conservan los modelos del estudio/biblioteca. Los BAV199 son del modelo local; TVS: avalancha lineal S11.4 y capacidad parametrizada; la fuga se inyecta en C5 en lugar de inventar extrapolación desde 12 V.

Deriva de pasivos/Vos del estudio: RSS de 125,177,20,4 ppm = 217.65 ppm respecto a 23 °C. Peor caso lineal (125+250+20+4) = **399 ppm**, supera 300 ppm. El SPICE no incorpora TC real de las resistencias, referencia ni deriva garantizada de Vos: su deriva NO certifica esa especificación. **Criterio/método:** 217 ppm es una estimación RSS; con los límites individuales no hay garantía determinista de 300 ppm. No se cambian piezas.

## C3 y C6: lectura y lógica

Lectura basada en el deck run_cont.py: R_PROT 99 kΩ, 10 kΩ, OPAx192 de buffer, mux 70 Ω/28 pF, A ×10.1 y divisor 2×10 kΩ hasta PB14; un BAT54 negativo. COMP ideal, histéresis total 9 mV (HYST=1 típica), umbral 252.5 mV. Cierra 20/40 Ω y abre, TVS 300/600/900 pF. Las ventanas comienzan con DC establecido; maxstep 0.2 µs. La lectura X2 usa el divisor 9.91 MΩ/100 kΩ y buffer OPAx192; para C6 se simulan las rutas X0 y X2 por separado, sin reconstruir toda la red TMUX4053, cuyo efecto DC se idealiza.

El ±16 mV sin calibrar equivale a ±3.168 Ω. Para ≤±1.5 Ω tras P41 el residuo debe ser ≤7.575 mV en PB14. No hay calibración física ni se garantiza deriva/ruido real del COMP/DAC. La histéresis de hoja 4–16 mV tampoco queda probada por su típico 9 mV. Pendiente de prototipo; no se marca P41 realizada.

P34 usa X2: 20 mV → 20.180 cuentas ideales. Un umbral literal de 20 mV puede perder ese caso con ruido −3 cuentas. La lectura positiva simulada resulta ligeramente menor por offset del OPAx192; el modelo de firmware calcula **16 cuentas** como umbral de aviso conservador: floor(menor señal simulada−3cuentas de ruido−0.5cuenta de redondeo). Esto puede avisar por debajo de 20 mV y no exige piezas; no se declara una modificación de firmware realizada. Para ±60 V, ×10.1 satura, lo que basta para avisar; ×1 permite leer ~±0.599 V sin saturación. X0 saturado no oculta la lectura independiente de X2. El estado ×1 a20 mV solo documenta lectura, no es la ruta de detección. resultados/s13_p34_summary.csv conserva cada estado. El ADC se idealiza en este modelo de lógica (cuentas de100 µV y ruido acotado); la INL local cerca de cero y la linealización real quedan pendientes. La fuente OFF se representa por BSS84 con puerta al riel y BAT54; el macromodelo TLV2372 deshabilitado no convergía en algunos DC extremos. La secuencia de habilitación real queda pendiente, sin modificar firmware.

## C4: presupuesto de INL

Barrido 10–100 % de cada rango, divisor de 10.01 MΩ, G=10.1 en 200 Ω y G=1 en el resto. INL diferencial: 5 V/4096 × 2.1/3.2 LSB =25.635/39.0625 cuentas de 100 µV. Ganancia de ohmios 600 ppm según el estudio; se descuenta de la tolerancia. Nivel calibrado: residuo supuesto de 10 cuentas; no se afirma que se haya medido o linealizado un ADC5.

| Rango Ω | Típica de hoja | Garantizada (≤100 %) | Proxy calibrado (≤85 %) |
|---|---|---|---|
| 200 | 59.06 % | 90.00 % | 77.04 % |
| 2000 | 59.66 % | 90.91 % | 77.82 % |
| 20000 | 59.68 % | 90.94 % | 77.84 % |
| 200000 | 59.89 % | 91.27 % | 78.12 % |
| 2e+06 | 52.24 % | 79.60 % | 68.14 % |
| 2e+07 | 34.29 % | 52.25 % | 16.96 % |

## C5: clasificación de fugas

3×3 combinaciones de 0.1/1/10 nA en fuerza y borne, dos rangos, 18/23/28 °C: 54 simulaciones. Ley de deriva ×2/10 °C, como el estudio. Se calibra a 23 °C y se compara deriva de corriente con 25 % de (tolerancia porcentual−600 ppm). Se conserva también la amplificación al invertir el divisor para convertir tensión a ohmios en s13_leak_summary.csv; no se oculta el efecto de la carga de 10.01 MΩ en 20 MΩ.

La suma de ambas fugas importa: no se comparan dos fugas de 1 nA como si fueran una sola. Los límites antiguos 0.85/1.14 nA del contrato corresponden a 1/0.2 µA; con 420 kΩ/1.7 MΩ las corrientes reales aumentan la tolerancia, pero no garantizan las fugas de hoja de los 4051. A 1 nA, falla marginal de criterio/prototipo; a 10 nA, error físico del supuesto inyectado. El modelo no demuestra que las piezas reales tengan 10 nA a baja tensión. No se propone ni aplica sustitución.

## Diodo (C7 adicional)

Silicio 0.65 V a 1 mA; LED 3.0/3.2 V y punto de compliancia 3.6 V a 100 µA, riel 4.8 V, lectura X2 ×10.1. DUT es tensión fija, como S11.4, no curva I/V de un LED seleccionado. Corriente medida en cada DUT y lectura en s13_campaign.csv. La corriente del DUT excluye la carga del divisor: no confundir I(R_k) con I_LED.

## Lista de piezas — contrato, no nueva selección

| Función | Pieza / valor | Cantidad / observación |
|---|---|---|
| Fuente y referencia | TLV2372IDR, C27204 | 1 dual |
| Paso | BSS84, C82079 (BSS84LT1G) | 1; modelo/hoja no garantizan ese MPN exacto |
| Referencia y habilitación | BSS138, C7420339 | 2; Vgs/Vth del MPN por confirmar |
| Fuerza/sentido | 74HCT4051, C87239 | 2; 5 canales usados +3 libres en cada uno |
| Rangos, 0.1 %,25 ppm/°C | 499 Ω;4.99 kΩ;49.9 kΩ;420 kΩ;1.7 MΩ | 5 valores; 1.7 MΩ =1.5 MΩ+200 kΩ; MPN de los dos últimos no definido por este encargo |
| Referencia, 0.1 % | 24.9 kΩ y4.99 kΩ | 2 |
| Referencia común | REF3325,2.5 V | Compartida; fuente ideal en estos decks |
| Compensación/control | 1 kΩ puerta;1 kΩ sentido;10 kΩ habilitación;1 nF C0G | 4 piezas; desacoplos según implementación, no definidos aquí |
| Bloqueo + PB14 | BAT54 (bloqueo y Schottky negativo) | 2 diodos |
| PB14 | 10 kΩ,1 % | 2, divisor ÷2 |
| Cadena c1 compartida con bloque1 | HoCR2512 510 Ω,2 W, C2912629 | 3; curva de impulso pendiente |
| Cadena compartida | TQ2SA,C46047; SMAJ12CA; R_S2.7 kΩ;2×BAV199;2×BZT52C5V6 | Piezas del contrato; sin sustitución |
| Lectura compartida, bloque2 | OPA4192;74HCT4051;TMUX4053;divisor6×1.5 MΩ+910 kΩ+100 kΩ | Ya definidos en S12d; no piezas nuevas de P43 |
| MCU compartido | STM32G473: COMP7/DAC2/PB14/ADC5 | Sin hardware nuevo para P34; P33 excluida |

## Dudas y pendientes

Fuga real y limpieza/guarda del prototipo; capacidad de TVS/cables y asiento real en 20 MΩ; curva ADC5/linealización; P41 y deriva COMP/DAC; BSS138/MPN; impulso de HoCR2512/GDT real; secuencia EN/INH y recuperación de alimentación. La tensión en vacío mayor que3.4 V permanece como contradicción documental del estudio: no se cambia 01_diseno. Las limitaciones de modelo/criterio se clasifican, sin perseguirlas ni cambiar piezas.

Diario: ai-context/journal/2026-10-08-codex-s13.md. STATE y DECISIONS se dejan intactos por instrucción expresa. La sincronización del contexto se ejecuta al cierre sobre las fuentes locales.
