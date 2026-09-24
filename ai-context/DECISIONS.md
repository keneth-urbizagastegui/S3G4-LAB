# Decisiones y límites compartidos

## 2026-09-18 — Memoria común entre herramientas

Solicitado explícitamente por Keneth en esta tarea. Los archivos `ai-context/` son la fuente duradera; context-mode proporciona búsqueda selectiva y procesamiento de salidas. Cada cliente conecta al MCP `s3g4-context` del proyecto y usa la misma raíz física para evitar bases distintas por directorio de arranque. Se conserva el plugin general instalado.

No se intenta convertir todos los historiales privados en una conversación única. Se comparten decisiones, estado, evidencia y pendientes que se registren aquí. La captura automática de cada plataforma tiene diferencias y no sustituye esta memoria.

## 2026-09-22 — Rediseño del front-end analógico (rev 2.1)

Motivo declarado por Keneth: el coste de construcción del AFE de la rev. 2.0 es demasiado alto, y el consumo de los relés no encaja en un equipo a batería. Fuente: mensajes del usuario en la sesión del 22 sep 2026. Reemplaza, para el front-end, a la arquitectura de la rev. 2.0, que pasa a ser una referencia más.

Decididas por el usuario:

- **Tres canales**, no cuatro.
- **Acoplo AC/DC/GND mediante conmutador deslizante mecánico**, uno por canal. Quedan descartados relés y PhotoMOS para la función de acoplo, por coste y por consumo a batería.
- **Fondo de escala de entrada ±40 V** (11 escalas, de 5 mV/div a 10 V/div). Primero se fijó en ±20 V; Keneth lo cambió el 23 sep («si, cambia D-05 a ±40 V y regístralo») para que quepan la fuente de banco de 30 V, los rieles de 24 V y el USB-PD de 20 V con su rizado. La escala de 5 V/div no cambia; sólo se añade la de 10 V/div, con las mismas piezas. Sigue por debajo de los 50 Vpk declarados en D-06.
- **Arquitectura de referencia: el JYE Tech DSO112** — atenuador grueso conmutado en la entrada y escalera fina de ganancia después del buffer. Fuente: `research_and_tests/DSO112/schematic_112g.pdf`, cuya tabla de rangos está reproducida en el diario del 22 sep.

Documento vivo con el desarrollo y las decisiones numeradas D-01…D-09: `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html`. D-09 (escalera que atenúa + ganancia fija ×50) sigue como propuesta.

### 2026-09-23 — D-06 acordado

Keneth aceptó la recomendación en la sesión del 23 sep («si, registralo»). Reemplaza la versión anterior de D-06 (supervivencia ±50 V continuos y 250 Vrms en todas las escalas), que estaba como propuesta.

- **Máxima entrada declarada del osciloscopio: 50 Vpk** en todas las escalas, como DSO112, DSO150 y DSO138 mini.
- **Supervivencia a 250 Vrms ≤ 10 s en el rango ÷20**, que es el estado de arranque. Sale del divisor de la sección B sin coste adicional.
- **La rama ×1** (escalas de 5 a 100 mV/div desde que D-05 pasó a ±40 V) aguanta 50 Vpk de forma continua y **no** la red. Riesgo aceptado.
- **Un relé por canal para el grueso ×1/÷20**; el firmware lo lleva a ÷20 al arrancar, al apagar y al detectar saturación.
- **La protección fuerte contra la red se traslada al puerto del DMM (600 V).**
- Motivo: ningún instrumento comparable protege el osciloscopio contra la red; el riesgo real con la red es la pinza de masa, que ninguna protección de entrada evita; el DMM es la función que el estudiante sí apuntará a la red. Evidencia en `journal/2026-09-22-claude-rediseno-afe-rev21.md`.

Queda por decidir: relé latching o monoestable (ver sección C.2 del documento vivo). Con latching no existe un «reposo» en ÷20; corregido en el documento.

### 2026-09-23 — Requisitos funcionales del osciloscopio acordados

Keneth los fijó respondiendo al cuestionario del 23 sep (cuatro rondas de preguntas cruzadas con los siete artefactos). La lista completa, con origen y consecuencias, está en `S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html`. Se suman a D-01…D-06.

- **RF-03** Ancho de banda: CH1 ≈ 2 MHz; CH2 y CH3 ≈ 1 MHz.
- **RF-05** Acoplo AC con corte ≤ 10 Hz (el conmutador es D-04).
- **RF-07** Con sonda ×10, lineal hasta ±400 V en la punta.
- **RF-08** Entrada de 1 MΩ ±2 %, 10–30 pF y ≤ 2 pF de diferencia entre escalas.
- **RF-09** Disparo por flanco en CH1–CH3, con nivel, posición e histéresis; modos auto, normal y único.
- **RF-10** 8 k muestras por canal. **RF-11** De 1 µs/div a 50 s/div, con sin(x)/x y roll.
- **RF-12** Adquisición normal, única, roll, detección de picos y promedio.
- **RF-13** Medidas automáticas, cursores, FFT, Bode con el AWG, matemáticas y XY.
- **RF-14** Offset de ±5 divisiones. **RF-15** ±1 % en continua con autocalibración.
- **RF-16** Osciloscopio, AWG y DMM a la vez. **RF-17** ≥ 4 h con las tres funciones y el WiFi. **RF-18** Apagado por hardware por canal y por función.
- **RF-19** Coste relativo, sin tope nuevo. Se priorizan disponibilidad y precio en LCSC, con montaje en JLCPCB. Se aceptan equivalentes cuya hoja cumpla las cifras clave. El tope RE-01 de 120 USD no se discutió.
- **DMM:** 16 bits con el ADC5 por sobremuestreo.

**Consecuencia derivada, no votada aparte:** P7 (grueso sin relé) no cumple RF-07 (4.4 % de THD con 200–400 V en la punta, según la simulación auditada). El grueso sigue con **P4, un relé por canal**. Si RF-07 cambiara, habría que revisarla. P4 aún no cumple RF-08 y debe corregirse. Evidencia: `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md`.

### 2026-09-23 — Requisitos del DMM y del AWG acordados

Keneth los fijó en dos rondas de preguntas para cada instrumento. Lista completa y consecuencias en `S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html`.

- **DMM:**
  - **RD-01** Tensión DC y AC (verdadero valor eficaz), corriente DC y AC, resistencia, diodo y continuidad.
  - **RD-02** Tres bornes, como el NI ELVIS II: V/Ω, COM y A.
  - **RD-03** 20 000 cuentas (4½ dígitos), con el ADC5 en diferencial y sobremuestreo.
  - **RD-04** CAT II 600 V.
  - **RD-05** Sin aislamiento galvánico, con enclavamiento por firmware: sin rangos de red con el USB o el osciloscopio activos. Riesgo residual aceptado.
  - **RD-06** Hasta 2 A con un único derivador y fusible cerámico de 600 V.
  - **RD-07** Alterna de 40 Hz a 20 kHz en tensión y en corriente (confirmado por Keneth).
  - **RD-08** Prueba de diodo hasta ~3.5 V.
  - **RD-09** Autorango, relativo, mín/máx, retención, registro en el tiempo y detección de cable abierto.
- **AWG:**
  - **RG-01** Dos canales.
  - **RG-02** De 1 Hz a 1 MHz en todas las formas, por DDS.
  - **RG-03** ±5 V en vacío, con dos rangos.
  - **RG-04** Salida de 50 Ω y ±50 mA; soporta un cortocircuito indefinido y ±15 V aplicados desde fuera.
  - **RG-05** Seno, cuadrada, triángulo, rampa y continua; el resto se añade por firmware.
  - **RG-06** Arbitraria de 4096 puntos por canal.
  - **RG-07** Sin fuentes de continua aparte: el AWG en continua cubre ese uso.
  - **RG-08** Sincronización interna con el osciloscopio, sin conector.

Estos requisitos concretan el DMM de D-06 y los requisitos RF-13 y RF-16 del osciloscopio. No reemplazan ninguna decisión anterior. Los cuatro bornes del DMM de la rev 2.0 pasan a ser tres (RD-02).

### 2026-09-23 (noche) — Seguridad del DMM, rieles y relés

Keneth decidió en la sesión de la sección G (rieles), después de preguntar si era más seguro usar osciloscopio + AWG y el DMM por separado.

- **El DMM sólo mide baja tensión:** 60 V en continua o 30 Vrms, CAT I, como el NI ELVIS II. No mide la red y comparte la masa con el osciloscopio, el AWG y el USB.
  - Revisa D-06: la parte «la protección fuerte contra la red va en el puerto del DMM (600 V)» queda sin efecto. El resto de D-06 sigue: 50 Vpk declarados y supervivencia del osciloscopio a 250 Vrms ≤ 10 s en ÷20.
  - Sustituye a RD-04 (CAT II 600 V), RD-05 (sin aislar con enclavamiento) y RD-10. RD-06 pasa a un fusible rápido normal.
  - Motivo: sin aislamiento, un COM en la fase deja con tensión el metal de las BNC y del USB-C aunque no haya nada conectado. Aislar costaba ~4–8 USD y sacaba al DMM del ADC5.
- **AWG con convertidor propio de ±6.5 V.** Compartiendo la bomba del LM27762, su salida caía a −4.95 V con 100 mA en el AWG y el LDO de −5.0 V del AFE dejaba de regular.
- **Batería 1S de 5000 mAh.** Da 6.0 h en el peor caso de RF-17 y 8.1 h en uso típico (sección G, `S3G4_LAB_rev2.1/herramientas/calc_rieles.py`).
- **Relés del grueso monoestables con economizador.** Cierra lo que quedaba pendiente en D-06 y revisa D-03 (latching) en el documento vivo. Sin alimentación vuelven solos a ÷20. Gastan 72 mW por relé mientras están en ×1.

Fuente: respuestas de Keneth del 23 sep (noche). Detalle en `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` §G y `ai-context/journal/2026-09-23-claude-seccion-g-rieles.md`.

### 2026-09-24 — Reorganización: el trabajo de la rev 2.1 pasa a `S3G4_LAB_rev2.1/`

Decisión de Keneth: crear la carpeta dentro del proyecto, sin espacios, y **mover** (una sola copia) sólo lo de la rev 2.1. La rev 2.0 y las referencias se enlazan. Respaldo con commit local en Git, sin push.

| Antes | Ahora |
|---|---|
| `docs/rediseno_afe_rev21.html` | `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` |
| `docs/requisitos_osciloscopio.html`, `docs/requisitos_dmm_awg.html` | `S3G4_LAB_rev2.1/00_requisitos/` |
| `docs/analisis_{dso112,wave2,openscope,black_scope}.html`, `docs/g473_analogico.html` | `S3G4_LAB_rev2.1/02_referencias/` |
| `docs/rediseno_afe_gen/` | `S3G4_LAB_rev2.1/herramientas/` |
| `Simulation_LTSpice_rev21/` | `S3G4_LAB_rev2.1/03_simulaciones/` |

- Los diarios anteriores al 24 sep conservan las rutas viejas: son historia. Esta tabla las traduce.
- Las entradas anteriores de este archivo, STATE, SOURCES, el índice y los scripts ya usan las rutas nuevas.
- Índice de la carpeta: `S3G4_LAB_rev2.1/LEEME.md`. Plan: `06_plan/PLAN.md`. Enlaces: `ARTEFACTOS.md`.

## Reglas ya documentadas en el proyecto

- **Protocolo:** `comm_testbench/shared/` contiene las definiciones normativas compartidas. Fuente: `comm_testbench/README.md`.
- **Cliente:** vectores de prueba normativos en `client_app_testbench/shared/vectors/`; separación de capas y verificación estricta. Fuentes: `client_app_testbench/README.md`, `client_app_testbench/app/package.json` y especificación S3G4-UI.
- **Hardware:** antes de cambiar pines del rev. 2, consultar el mapa firmado y ejecutar el verificador indicado allí. El acta contiene decisiones y correcciones; no extrapolar sus cifras al firmware heredado. Fuentes: `docs/MAPA_PINES_FIRMADO.md`, `docs/ACTA_VERIFICACION_MAPA_PINES.md`.

Una nueva decisión debe indicar fecha, motivo, fuente/autoridad y qué decisión anterior reemplaza. Una idea propuesta queda como propuesta hasta que exista evidencia de aceptación.
