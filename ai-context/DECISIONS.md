# Decisiones y límites compartidos

## 2026-09-18 — Memoria común entre herramientas

Solicitado explícitamente por Keneth en esta tarea. Los archivos `ai-context/` son la fuente duradera; context-mode proporciona búsqueda selectiva y procesamiento de salidas. Cada cliente conecta al MCP `s3g4-context` del proyecto y usa la misma raíz física para evitar bases distintas por directorio de arranque. Se conserva el plugin general instalado.

No se intenta convertir todos los historiales privados en una conversación única. Se comparten decisiones, estado, evidencia y pendientes que se registren aquí. La captura automática de cada plataforma tiene diferencias y no sustituye esta memoria.

## 2026-09-22 — Rediseño del front-end analógico (rev 2.1)

Motivo declarado por Keneth: el coste de construcción del AFE de la rev. 2.0 es demasiado alto, y el consumo de los relés no encaja en un equipo a batería. Fuente: mensajes del usuario en la sesión del 22 sep 2026. Reemplaza, para el front-end, a la arquitectura de la rev. 2.0, que pasa a ser una referencia más.

Decididas por el usuario:

- **Tres canales**, no cuatro.
- **Acoplo AC/DC/GND mediante conmutador deslizante mecánico**, uno por canal. Quedan descartados relés y PhotoMOS para la función de acoplo, por coste y por consumo a batería.
- **Fondo de escala de entrada ±40 V** (11 escalas, de 5 mV/div a 10 V/div; *desde P1, 2 oct: 12 escalas, de 5 mV/div a 20 V/div*). Primero se fijó en ±20 V; Keneth lo cambió el 23 sep («si, cambia D-05 a ±40 V y regístralo») para que quepan la fuente de banco de 30 V, los rieles de 24 V y el USB-PD de 20 V con su rizado. La escala de 5 V/div no cambia; sólo se añade la de 10 V/div, con las mismas piezas. Sigue por debajo de los 50 Vpk declarados en D-06.
- **Arquitectura de referencia: el JYE Tech DSO112** — atenuador grueso conmutado en la entrada y escalera fina de ganancia después del buffer. Fuente: `research_and_tests/DSO112/schematic_112g.pdf`, cuya tabla de rangos está reproducida en el diario del 22 sep.

Documento vivo con el desarrollo y las decisiones numeradas D-01…D-09: `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html`. D-09 (escalera que atenúa + ganancia fija ×50) *quedó aceptada con P1 el 2 oct (entrada de ese día)*; D-07 (orden de la cadena) sigue como propuesta, aunque todas las simulaciones de CH1 la usan.

### 2026-09-23 — D-06 acordado

Keneth aceptó la recomendación en la sesión del 23 sep («si, registralo»). Reemplaza la versión anterior de D-06 (supervivencia ±50 V continuos y 250 Vrms en todas las escalas), que estaba como propuesta.

- **Máxima entrada declarada del osciloscopio: 50 Vpk** en todas las escalas, como DSO112, DSO150 y DSO138 mini.
- **Supervivencia a 250 Vrms ≤ 10 s en el rango ÷20**, que es el estado de arranque. Sale del divisor de la sección B sin coste adicional.
- **La rama ×1** (escalas de 5 a 100 mV/div desde que D-05 pasó a ±40 V) aguanta 50 Vpk de forma continua y **no** la red. Riesgo aceptado.
- **Un relé por canal para el grueso ×1/÷20**; el firmware lo lleva a ÷20 al arrancar, al apagar y al detectar saturación. *(Desde el 23 sep por la noche es monoestable: sin alimentación vuelve solo a ÷20.)*
- **La protección fuerte contra la red se traslada al puerto del DMM (600 V).** *(Sustituido el 23 sep por la noche; ver «Seguridad del DMM, rieles y relés».)*
- Motivo: ningún instrumento comparable protege el osciloscopio contra la red; el riesgo real con la red es la pinza de masa, que ninguna protección de entrada evita; el DMM es la función que el estudiante sí apuntará a la red. Evidencia en `journal/2026-09-22-claude-rediseno-afe-rev21.md`.

Queda por decidir: relé latching o monoestable (ver sección C.2 del documento vivo). Con latching no existe un «reposo» en ÷20; corregido en el documento. *Cerrado el 23 sep (noche): monoestable con economizador; ver la entrada «Seguridad del DMM, rieles y relés».*

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
  - **RD-04** CAT II 600 V. *(Sustituido el 23 sep por la noche; ver «Seguridad del DMM, rieles y relés».)*
  - **RD-05** Sin aislamiento galvánico, con enclavamiento por firmware: sin rangos de red con el USB o el osciloscopio activos. Riesgo residual aceptado. *(Sustituido el 23 sep por la noche; ver «Seguridad del DMM, rieles y relés».)*
  - **RD-06** Hasta 2 A con un único derivador y fusible cerámico de 600 V. *(Sustituido el 23 sep por la noche; ver «Seguridad del DMM, rieles y relés».)*
  - **RD-07** Alterna de 40 Hz a 20 kHz en tensión y en corriente (confirmado por Keneth).
  - **RD-08** Prueba de diodo hasta ~3.5 V.
  - **RD-09** Autorango, relativo, mín/máx, retención, registro en el tiempo y detección de cable abierto.
- **AWG:**
  - **RG-01** Dos canales.
  - **RG-02** De 1 Hz a 1 MHz en todas las formas, por DDS. *(Revisado el 30 sep: ver la entrada de ese día.)*
  - **RG-03** ±5 V en vacío, con dos rangos.
  - **RG-04** Salida de 50 Ω y ±50 mA; soporta un cortocircuito indefinido y ±15 V aplicados desde fuera.
  - **RG-05** Seno, cuadrada, triángulo, rampa y continua; el resto se añade por firmware.
  - **RG-06** Arbitraria de 4096 puntos por canal.
  - **RG-07** Sin fuentes de continua aparte: el AWG en continua cubre ese uso. *(30 sep: en conflicto con la salida de 50 Ω; abierto.)*
  - **RG-08** Sincronización interna con el osciloscopio, sin conector.

Estos requisitos concretan el DMM de D-06 y los requisitos RF-13 y RF-16 del osciloscopio. No reemplazan ninguna decisión anterior. Los cuatro bornes del DMM de la rev 2.0 pasan a ser tres (RD-02).

### 2026-09-23 (noche) — Seguridad del DMM, rieles y relés

Keneth decidió en la sesión de la sección G (rieles), después de preguntar si era más seguro usar osciloscopio + AWG y el DMM por separado.

- **El DMM sólo mide baja tensión:** 60 V en continua o 30 Vrms, CAT I, como el NI ELVIS II. *(Corregido el 30 sep: el ELVIS II es 60 V DC / 20 Vrms. Sustituido ese día por 50 V DC / 50 Vrms, como el TIDA-01012; ver la entrada del 30 sep.)* No mide la red y comparte la masa con el osciloscopio, el AWG y el USB.
  - Revisa D-06: la parte «la protección fuerte contra la red va en el puerto del DMM (600 V)» queda sin efecto. El resto de D-06 sigue: 50 Vpk declarados y supervivencia del osciloscopio a 250 Vrms ≤ 10 s en ÷20.
  - Sustituye a RD-04 (CAT II 600 V), RD-05 (sin aislar con enclavamiento) y RD-10. RD-06 pasa a un fusible rápido normal.
  - Motivo: sin aislamiento, un COM en la fase deja con tensión el metal de las BNC y del USB-C aunque no haya nada conectado. Aislar costaba ~4–8 USD y sacaba al DMM del ADC5.
- **AWG con convertidor propio de ±6.5 V.** Compartiendo la bomba del LM27762, su salida caía a −4.95 V con 100 mA en el AWG y el LDO de −5.0 V del AFE dejaba de regular.
- **Batería 1S de 5000 mAh.** Da 6.0 h en el peor caso de RF-17 y 8.1 h en uso típico (sección G, `S3G4_LAB_rev2.1/herramientas/calc_rieles.py`).
- **Relés del grueso monoestables con economizador.** Cierra lo que quedaba pendiente en D-06 y revisa D-03 (latching) en el documento vivo. Sin alimentación vuelven solos a ÷20. Gastan 72 mW por relé mientras están en ×1.

Fuente: respuestas de Keneth del 23 sep (noche). Detalle en `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` §G y `ai-context/journal/2026-09-23-claude-seccion-g-rieles.md`.

### 2026-09-30 — Límite de tensión del DMM: como el TIDA-01012

Keneth, en la sesión de coherencia del DMM: «habíamos acordado medir solo tensiones bajas como TIDA-01012, que solo mide hasta 50 V DC como AC». A la pregunta de si en alterna son 50 V eficaces o de pico, eligió **50 Vrms, como el TIDA**.

- **RD-04 pasa a 50 V en continua y 50 Vrms en alterna (≈ 71 Vpk).** El TIDA-01012 tiene rangos de 50 mV, 500 mV, 5 V y 50 V (`research_and_tests/tidubv5b (1).pdf`, tabla 1, p. 4). Sustituye a «60 V DC / 30 Vrms, como el ELVIS II».
- **Sin cambios:** tres bornes (V/Ω, COM, A), 2 A como máximo, sin medir la red y con masa común (RD-02, RD-05, RD-06).
- **Consecuencia aceptada:** 71 Vpk supera los 50 Vpk declarados del osciloscopio y el umbral de 30 Vrms de IEC 61010-1. El borne V/Ω lleva tensión peligrosa y necesita aviso en el panel y en el manual. La entrada y su protección se dimensionan para 71 Vpk continuos.
- **Rangos propuestos:** 200 mV, 2 V, 20 V y 50 V en continua, y lo mismo en alterna con 50 Vrms.

### 2026-09-30 — AWG: frecuencia por forma de onda; RG-07 abierto

Keneth, en la sesión de coherencia del AWG:
- **RG-02 revisado:** el seno llega de 1 Hz a 1 MHz. La cuadrada, el triángulo y la rampa tienen un tiempo de subida de ≈ 175 ns (filtro de reconstrucción de 2 MHz) y son útiles con buena forma hasta 100–200 kHz. Motivo: con DDS a 15 MSa/s solo hay 15 muestras por periodo a 1 MHz.
- **RG-07 queda abierto «hasta que definamos los rieles».** El conflicto: a través de los 50 Ω de RG-04, con 50 mA caen 2.5 V, así que la fuente de ±5 V / ±50 mA no se cumple. Opciones planteadas: rebajar el requisito, compensar por firmware o añadir un modo de baja impedancia.

### 2026-10-02 — Disparo sin entrada externa; disparo interno desde el AWG

Keneth aceptó la recomendación de Claude en la sesión del 2 oct («sí, regístralo»).
- **No hay BNC ni borne de disparo externo.** Las fuentes de disparo son CH1, CH2 y CH3 (RF-09) y, **nueva, el AWG interno**: el firmware conoce el inicio de cada periodo y dispara desde ahí, sin hardware (también lo usa el Bode de RF-13).
- Motivo: con 3 canales, cualquiera puede hacer de entrada de disparo; el caso educativo típico («disparo con la salida del generador») lo cubre el AWG interno. El DSO112A y el WAVE2 lo tienen porque sólo tienen 1–2 canales.
- Amplía RF-09. Si algún día hace falta, queda la vía de un comparador libre del G473 con umbral desde un DAC, sin tocar el AFE.

### 2026-10-02 — Entrada del osciloscopio: sin la red conectada directamente

Keneth, sesión del 2 oct: «ya no vamos con valores de voltajes altos como de red conectados directos a nuestro dispositivo, sino como nuestras referencias, con una seguridad mejor».
- **Revisa D-06 y RF-06:** la supervivencia a 250 Vrms ≤ 10 s en ÷20 deja de ser requisito de diseño. Se mantienen los 50 Vpk declarados (como el DSO112A y el WAVE2), el relé monoestable con reposo en el grueso y la sonda ×10 lineal hasta ±400 V en la punta (RF-07).
- Consecuencias que dejan de aplicar: relé con ≥ 500 Vrms entre contactos abiertos (C.6), rama superior partida en tres para repartir 353 V (B.8), y el criterio «sobrevive a la red» de T06.
- **Cifras acordadas el mismo día** (Keneth eligió la opción recomendada): 50 Vpk declarados; **sin daño con ±100 V continuos en cualquier escala, también con el equipo apagado**; **ESD de ±8 kV en aire y ±4 kV en contacto** (IEC 61000-4-2) en el vivo de la BNC. Ver `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` §5.

### 2026-10-02 — P1: grueso ÷100 con escalera de 6 tomas; simulaciones de CH1 por Codex

Keneth, respondiendo a la revisión de la entrada de CH1 (opción recomendada):
- **P1 aceptado: grueso ×1 / ÷100** y escalera del DSO112 de 6 tomas (1, 1/2, 1/4, 1/10, 1/20, 1/40) con ganancia fija ×50. Salen 12 escalas, de 5 mV a 20 V/div. **Sustituye al ÷20 con 8 tomas** de D-09 y de las tablas C.1, C.3 y C.6 del documento vivo, que quedan por reescribir. D-05 (±40 V) no cambia.
- Las dos entradas libres del 4051 pasan a ser GND (autocero) y VCHECK (P3), al servicio de RF-15. El valor de VCHECK está por definir.
- La entrada de CH1 sigue la propuesta **P4b** de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html`, pendiente de que la simulación la confirme.
- **Ejecución de las simulaciones S1–S7: Codex**, con encargo escrito y auditoría de Claude (el mismo esquema que P4/P7).

### 2026-10-02 — Un trimmer por canal para la compensación de ÷100; C_EQ seleccionado en prueba

Keneth, tras la auditoría de S1 (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S1.md`): «sí, acepto un trimmer por canal».
- **Un trimmer por canal** en la rama superior del divisor ÷100. Motivo: la Coff del relé y las tolerancias de Cb y Ct hacen variar la planitud en ÷100 de una placa a otra más de ±1 %. Como el C24 del DSO112. Rango y posición los fija S1b.
- **C_EQ (réplica de carga) seleccionado en prueba**, sin trimmer: un C0G fijo elegido al medir el prototipo. Motivo: lo que domina ΔCin (la Cin del buffer y las parásitas del layout) es igual en todas las placas.
- Son 3 ajustes en total, uno por canal, en el procedimiento de calibración de fábrica.

### 2026-10-02 — Ancho de banda de diseño: CH1 a 2 MHz y CH2/CH3 a 1 MHz

Keneth, al revisar C.4 y C.5: «ch1 2mhz y ch2y3 a 1mhz». Concreta RF-03: los cálculos y el filtro de CH2 y CH3 se hacen a **1 MHz (−3 dB)**, no al margen de 1.5 MHz que usaban la sección C y el PLAN. CH1 sigue a 2 MHz.

### 2026-10-03 — Trimmer de 2–6 pF centrado con Cb seleccionado en prueba

Keneth, tras la auditoría de S1b (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S1b.md`): «acepto el trimmer 2-6 pF».
- **Trimmer SEHWA STC3MA06-T1, 2–6 pF, 100 V (LCSC C22468120)**, uno por canal, en paralelo con C1B. Con CT2F = 16 pF.
- Motivo: cumple los 9 criterios en producción (200/200), pero con sólo 0.05 pF de margen hasta el tope superior. El de 3–10 pF (C22468121) tiene 16 ud en LCSC.
- **Para centrarlo:** en el prototipo se mide la Coff real del HFD27 y la capacidad de SEL, y se elige **Cb seleccionado en prueba** (como C_EQ) para que el trimmer trabaje cerca de la mitad de su recorrido.

### 2026-10-03 — Buffer de entrada: OPA810, con AD8065 de segunda fuente

Keneth: «sí, OPA810 con AD8065 de segunda fuente».
- **U101 (buffer de cada canal): OPA810IDBVR** (TI, LCSC C2833513, SOT-23-5): FET, 70 MHz, 200 V/µs, 2 pA, 6.3 nV/√Hz, 3.7 mA, 4.75–27 V. Cin de modo común 2–2.5 pF ∥ 12 GΩ, diferencial 0.5 pF (hoja).
- **Segunda fuente: AD8065ARTZ** (ADI, C9648), mismo patillaje SOT-23-5: 145 MHz, 6 pA, 7 nV/√Hz, 6.6 mA. Entrada de 6.6 pF en total; como seguidor, la parte diferencial queda bootstrapped.
- Modelos en `Simulation_LTSpice/models/` (OPA810 de TI, AD8065 de ADI y BAV199 de Nexperia), comprobados como seguidor a ±5 V (`CH1_entrada/chequeo_claude/modelos_s2.cir`).

### 2026-10-03 — Piezas de 200 V en la réplica y en C_S; AD8065 descartado como segunda fuente

Keneth, tras la auditoría de S2 (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S2.md`): «sí a las tres».
- **R_EQ en 1206** (200 V; ve 99 V en ÷100 con 100 V de entrada). **C_EQ y C_S: C0G de ≥ 200 V** (ven 99 y 94 V).
- **El AD8065 deja de ser segunda fuente del buffer:** su diferencial de entrada máxima es 1.8 V y en sobrecarga en ×1 llega a 3.1 V. Se busca otra con ≥ ±7 V de diferencial (como el OPA810).
- Se encarga **S2b**: ESD con red IEC realista y métrica I²t, CIN_BUF sin contar dos veces y piezas de 200 V.

### 2026-10-03 — Buffer: OPA810 como fuente única; OPA828 como alternativa documentada

Keneth eligió la opción (c), tras la auditoría de S2b (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S2b.md`).
- **U101 = OPA810IDBVR (C2833513), fuente única**, con una sola huella SOT-23-5 y una sola lista de piezas. RF-19 lo admite porque no hay equivalente que encaje sin cambios: 3287 ud en LCSC bastan para prototipo y serie corta.
- **OPA828 (C1850247), alternativa documentada y validada en S2b:**
  - diferencial igual a toda la alimentación;
  - ESD e I²t correctos;
  - pero la Cin del canal sube a 31 pF (> 30 pF de RF-08) y el encapsulado es SOIC-8 o HVSSOP-8.
  - Si algún día hace falta, se cambian huella, Ct (2 × 12 pF), C_S, C_EQ y Cb.

### 2026-10-03 — U103 = AD8039; criterio de ruido E12 a ≤ 0.45 % de división

Keneth eligió la opción recomendada por Claude al preparar S3 (sesión del 3 oct; cálculo en `ai-context/journal/2026-10-03-claude-s3-u103.md`).
- **U103 = AD8039ARZ-REEL7 (C96525, 2574 ud, 4.64 USD), doble, en los tres canales:** 350 MHz, 425 V/µs, 8 nV/√Hz, 1 mA por amplificador (ahorra ≈ 120 mW frente a los 3 mA de G.3), Ib 400 nA. Pendiente de verificar en su hoja: diferencial máxima de entrada y GBW real a ×5 y ×10 con ±5 V.
- **E12 se relaja de 0.35 % a 0.45 % de división.** Con el AD8039 y R_PROT de 1 kΩ, CH1 da ≈ 0.42 % a 5 y 500 mV/div; la mitad la ponen el OPA810 y R_PROT. Se mantiene R_PROT = 1 kΩ y la red de 1 kΩ, así que S2b no se repite.
- Descartados: **LM6172**, porque a ±5 V su hoja da 70 MHz de ancho de banda unitario (no llega a 100); **AD8056**, que cumpliría 0.34 % con R_PROT de 470 Ω y red de 499 Ω, pero gasta 6 mA por amplificador, cuesta el doble y obliga a repetir S2b; **ADA4896-2**, por su Ib de 11 µA (≈ 0.5 V de offset en el ADC) y porque ±5 V es su máximo de alimentación; **LMH6643**, por sus 17 nV/√Hz.
- **Red de ganancia de U103 con R_G = 249 Ω** (decisión de Keneth, 3 oct, tras la comprobación del modelo): ×5 = 1.00 kΩ / 249 Ω y ×10 = 2.26 kΩ / 249 Ω (×50.55). Sustituye a 4.02 k / 1 k y 9.09 k / 1 k de C.6, que en el modelo del AD8039 daban +3.7 dB de pico en la ×5. Ruido de CH1 estimado ≈ 0.40 %.
- **Diferencial de entrada de U103A en saturación:** puede pasar de los ±4 V de la hoja (4.28 V en el modelo con 4.9 V en IN+). Keneth decide medirla primero en S3 (E14) y elegir la protección después.
- **Tras la auditoría de S3** (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S3.md`), Keneth decide:
  - **protección de U103A, opción (a):** resistencia serie en IN+ (470 Ω–1 kΩ) y diodos en antiparalelo entre sus entradas. Se elige con S3b, que compara BAT54S y BAV199;
  - **acepta ≈ 0.6 ms de recuperación** cuando, en la rama ×1, conducen los BAV199 de entrada (|V_BNC| > 5.6 V). El criterio de ≤ 1 µs queda sólo para la saturación de los amplificadores.
- **Tras S3b** (`AUDITORIA_CLAUDE_S3b.md`), Keneth confirma:
  - **protección de U103A y de U103B:** 470 Ω en serie en IN+ y **BAV99 (C2500, Nexperia)** en antiparalelo entre IN+ e IN−. El BAT54S queda descartado por su pico (+6–8 dB) y el BAV199 por lento (1.1 µs). Comprobación de Claude con los dos protegidos: diferencial ≤ 0.69 V, ruido 0.41 %, sin pico y recuperación < 50 ns;
  - **propuesta para la sección G** (sin piezas elegidas): jack de 9–12 V con cargador y power path para la batería, y USB sólo para datos y programación. Las tensiones internas no cambian (±5 V, 3.3 V, ±6.5 V del AWG): se generan desde la batería.
- **Etapa final de CH1 (S4), decisiones de Keneth del 3 oct:**
  - **P8 adoptado:** una etapa final por canal alimentada desde VDDA = 3.3 V (cumple P14);
  - **offset desde el DAC del G473 con buffer** (DAC1 en PA4/PA5 y DAC2 en PA6, un canal por osciloscopio): hay que reservar esos pines en el mapa de la rev 2.1;
  - **amplificador OPA836** (C111589).
  Topología propuesta por Claude y en simulación: sumadora inversora con la entrada no inversora en VMID (de VREF+), R_IN = R_F = 10 kΩ y R_OFF = 8.06 kΩ (`PLAN_SIMULACION_S4.md`). Queda abierto cómo se alimenta VMID: divisor por canal o seguidor común.
- **Tras la auditoría de S4** (`AUDITORIA_CLAUDE_S4.md`), Keneth decide:
  - **C_F = 1 pF C0G** en paralelo con R_F de la etapa final (quita un pico de +1.5 dB);
  - **VMID M1:** divisor de 10.0 kΩ / 5.23 kΩ desde VREF+ con 1 µF, uno por canal;
  - **regla de secuencia (sección G):** el AFE (EN+ y EN− del LM27762) tiene resistencia a masa y lo enciende el G473 cuando VDDA ya está presente; al apagar, primero el AFE. Sin ella, el pin del ADC recibe ±0.49 V con el G473 apagado;
  - **se acepta un offset de −4.85 div por abajo** (+5.21 por arriba); RF-14 se lee como ±5 div con ese límite inferior.
- **Filtro anti-alias de CH1 (S5), decisión de Keneth del 3 oct:** etapa U105 con un **AD8039 doble** (C96525) a ±5 V entre U103B y S4: dos Sallen-Key de ganancia unidad (4.º orden activo), que con el RC del ADC y S4 hacen 6.º orden. El candidato (Bessel, intermedio o Butterworth) lo elige Keneth con los resultados de S5.
- **Tras S5** (`AUDITORIA_CLAUDE_S5.md`), Keneth elige el **filtro intermedio (Butterworth-Thomson, m = 0.5) reescalado**: sección 1, R = 1.11 kΩ, C1 = 56 pF, C2 = 47 pF; sección 2, R = 499 Ω, C1 = 220 pF, C2 = 56 pF. Comprobación de Claude: −3 dB en 2.011 MHz y 21.7 dB a 4.5 MHz. El Monte Carlo, el escalón y la recuperación con estos valores se verifican en **S7**, donde también se quita la carga ficticia de 1 kΩ ∥ 10 pF de U103B.

### 2026-10-03 — Revisión de CH1: C_S, rieles del AFE y criterio de diseño con tolerancias

Keneth, tras `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/REVISION_CLAUDE_CH1.md`:
- **R1, sí:** **C_S = 1.2 nF** C0G ≥ 200 V y **C_EQ ≈ 8.7 pF** (8.2–9.1 pF C0G ≥ 200 V, seleccionado en prueba). Sustituyen a 1.5 nF y ≈ 12 pF de C.6, que venían de S1 con la capacidad del buffer contada dos veces.
- **R2, opción A:** los rieles del AFE (LM27762) pasan a **±4.90 V**, para que el 74HC4051 quede en 9.8 V (peor caso ≈ 9.95 V ≤ 10 V recomendados). Hay que repasar las sujeciones de S2b (BAV199 a ±4.9 V) y la integración con esos rieles.
- **Criterio de diseño (permanente):** «no quiero la perfección, quiero que funcione». Desde ahora, cada etapa se juzga con **tolerancias reales y márgenes**, no con el valor nominal:
  - Monte Carlo o peor caso con R ±1 %, C ±5 % (C0G) o ±10 % (X7R), rieles ±2 %, VREF ±0.2 % y la dispersión de hoja de los amplificadores (offset, I_B, GBW);
  - aceptar si cumple **en ≥ 95 % de las placas**, con criterios funcionales (por ejemplo, ancho de banda de 2 MHz ± 15 % y ruido ≤ 0.5 % de división), no con cifras ideales;
  - componentes con margen: tensión ≤ 80 % del nominal, potencia ≤ 50 %, corriente ≤ 50 % del máximo absoluto, y alimentaciones dentro de lo recomendado, no en el límite;
  - lo que se corrige por calibración (ganancia y offset) no cuenta como fallo; sí cuentan la estabilidad, la saturación, la protección y el ruido.

### 2026-10-04 — Trimmer del ÷100: opción A (tolerancias estrechas)

Keneth elige la opción A de `AUDITORIA_CLAUDE_S7b.md` (en S7b, el trimmer de 2–6 pF bastaba en el 83 % de las placas). Verificado en `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/ACTA_S7c.md` (Monte Carlo de 20 000 placas con la fórmula de S7b): **100 % de las placas en rango**, con el ajuste entre 3.5 y 4.9 pF.
- **Ct1 (C1A) = 20 pF ±2 % C0G 250 V** (C3845779).
- **Ct2 fijo (C1B) = 15 pF ±2 % C0G 250 V** (C3836120); antes 16 pF.
- **Cb = 1 nF ±1 % C0G** (C507408) **+ 68 pF ±5 % C0G**.
- Trimmer SEHWA de 2–6 pF sin cambios; **un hueco DNP 0603 en paralelo con Ct2** como seguro para el primer prototipo.

### 2026-10-04 — S9: CH2/CH3 iguales a CH1 salvo el filtro; LM6172 como variante a evaluar

Keneth, tras la propuesta de Claude: «quiero seguir tu recomendacion y probar el lm6172».
- Diseño base de CH2/CH3: copia de CH1 (OPA810, AD8039 en U103/U105, OPA836), con el filtro a 1 MHz y un solo ADC a 3.47 MSa/s (2.5 ciclos).
- **Variante B a evaluar en S9: LM6172 (C180430) en U103 y U105.** Motivo: la AD8039 es lo más caro del canal (≈ 4.07 USD frente a ≈ 2.09 USD, LCSC a 10 uds, 4 oct); ahorro estimado ≈ 8 USD por placa menos el cargo de pieza extendida. Los amplificadores baratos de 5.5 V quedan fuera por los rieles de ±4.9 V y la regla del 80 %. El descarte del LM6172 del 3 oct (70 MHz a ±5 V) era para CH1, que pide ≥ 100 MHz; CH2/CH3 piden ≥ 50 MHz.
- **No está adoptada:** se decide con el acta de S9 (ruido, protecciones, offset y consumo). Plan: `S3G4_LAB_rev2.1/03_simulaciones/CH23_entrada/PLAN_SIMULACION_S9.md`.
- El disparo de CH2/CH3 (PE9/PE15) queda fuera de S9; va al mapa de pines (PLAN, paso 8).
- **4 oct, modelo de la variante B:** la puerta K0 de Codex detuvo B porque el macromodelo de National no cuadra con la hoja de TI a ±5 V (≈ 150 MHz frente a 70 MHz; 1.7 frente a 2.2 mA). Keneth: «hay que seguir lo que dice el datasheet». B se simula con una copia propia ajustada a la hoja (`CH23_entrada/comun/lm6172_hoja.lib`; encargo `ENCARGO_CODEX_S9_B.md`). La saturación y las protecciones siguen saliendo de la topología de National, con esa limitación anotada.
- **4 oct, criterio de recuperación de CH2/CH3 (S9-C8): ≤ 2 µs** (Keneth: «lo que te parezca», sobre la propuesta de Claude). El ≤ 1 µs del plan se copió de CH1 sin escalar; el asentamiento del filtro escala con 1/BW (CH1: 0.71 µs a 2 MHz → ≈ 1.4 µs a 1 MHz). Con él, la variante A cumple (1.33–1.41 µs).

### 2026-10-06 — CH2/CH3: AD8039 en U103/U105; LM6172 descartado

Keneth, 6 oct, tras la auditoría de S9 hecha por Claude: «Elijo AD8039 para CH2/CH3».
- **Adoptada la variante A:** CH2/CH3 llevan AD8039 en U103 y U105, igual que CH1 (OPA810, AD8039, OPA836), con el filtro a 1 MHz. **Cierra la variante B de la entrada del 4 oct.**
- **Motivo** (acta `CH23_entrada/ACTA_S9.md` y auditoría `ai-context/journal/2026-10-06-claude-auditoria-s9b-s8b.md`): A cumple C1–C9. La C9 conjunta, con la misma placa en las cuatro escalas, da 481/500 (96.2 %). B, con el offset corregido, da 471/500 (94.2 %) y queda en 95.4 % en dos escalas. A además consume 63 mW por canal frente a 109 mW, y su peor ruido es 0.234 %div frente a 0.286 %div.
- Se renuncia al ahorro estimado de ≈ 8 USD por placa.
- Siguiente paso: rehacer la tabla de consumo G.3/G.4 con las cifras de A.

### 2026-10-07 — DMM: arquitectura (rangos, mux, amplificador de deriva cero y RD-10)

Keneth eligió las cuatro opciones recomendadas por Claude al empezar el DMM:
- **Cambio de rango en tensión:** divisor de 10 MΩ con tomas (÷1, ÷10, ÷100) y un **74HC4051** que elige la toma (sin relés). El mux solo ve tensiones divididas o la entrada ya sujetada. Una posición a COM da el autocero.
- **Amplificador:** **uno de deriva cero externo**, doble y barato, entre la toma y el ADC5 diferencial: buffer de alta impedancia para tensión y ganancia ×10/×100 para el derivador. Autocero por el mux para lo que quede.
- **RD-10:** **aguantar unos segundos** una conexión a la red (230 Vrms). Resistencias de alta tensión en el divisor, PTC y sujeción en la fuente de ohmios, y fusible en el borne A. No es una categoría de medida; el equipo sigue sin medir la red.
- **Rangos aceptados:**
  - DC y AC: 200 mV, 2 V, 20 V y 50 V;
  - Ω: de 200 Ω a 20 MΩ;
  - corriente: 200 mA y 2 A con un solo derivador de 0.1 Ω;
  - 20 000 cuentas, recortado a 50 V en el rango alto.
- Fuentes: `S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html` (RD-01…RD-10) y la referencia TI TIDA-01012 (`research_and_tests/tidubv5b (1).pdf`).

### 2026-10-06 — D-07 aceptada, RE-01 en espera y orden: DMM → AWG → mapa de pines

Keneth, 6 oct, tras cerrar CH1–CH3:
- **D-07 (orden de la cadena) aceptada:** «D-07 queda con lo que hicimos». Pasa de propuesta a cerrada en el documento vivo.
- **RE-01 (tope de 120 USD) en espera.** Criterio: que funcione con componentes baratos y con los circuitos reducidos al mínimo (la rev 2.1 ya recorta piezas frente a la rev 2.0). Se revisa con todos los bloques.
- **Orden de trabajo:** primero el DMM y el AWG, y después el mapa de pines. Con sus esquemas se reparte la conexión con el STM32, separando los recursos analógicos de los digitales. Sustituye al orden de PLAN del 4 oct (rieles primero, mapa de pines antes que los esquemas). Para no diseñar contra un recurso ocupado, durante el DMM y el AWG se lleva una lista de reserva de pines y periféricos del G473 (propuesta de Claude, 6 oct).
- Los esquemas de CH1–CH3 se dejan como están hasta tener más hojas.

### 2026-10-06 — S10: esquema de CH2/CH3, una hoja por canal y referencias por centenas

Keneth eligió las tres opciones recomendadas por Claude:
- **Una hoja jerárquica por canal:** `ch2.kicad_sch` y `ch3.kicad_sch`, colgadas de la raíz y sin pines jerárquicos (todo por etiquetas globales y `power:`). Adelanta para CH2/CH3 la jerarquía que S8 dejaba para el final; CH1 sigue en la raíz por ahora.
- **Referencias por centenas:** CH2 = 2xx y CH3 = 3xx. Los relés pasan a K101, K201 y K301 (antes K101…K103).
- **RFILT1 de 2.37 kΩ con pareja de piezas *basic*:** 2.2 kΩ + 150 Ω = 2.35 kΩ (−0.84 %). No hay 2.37 kΩ ni 180 Ω *basic* en 0603. El −3 dB sube ≈ 0.8 %, dentro de S9-C1, así que no se vuelve a simular. RFILT2 = 1.1 kΩ, una sola pieza.
- Fuente: `S3G4_LAB_rev2.1/04_esquematicos/S10_CH23/CH23_PIEZAS_Y_REDES.md`.

### 2026-10-04 — S8: esquema de CH1, cuerpo del BNC, desacoplo y pull-ups

Keneth, al preparar S8: hoja plana sin jerarquía (la jerarquía, al estilo de OpenScope, se hará al final), dibujada con Konnect en una sesión abierta en `04_esquematicos/kicad/`, y solo la cadena de CH1. Después: «BNC a AGND, y acepto el desacoplo y los pull-ups».
- **Cuerpo del BNC a `AGND`.**
- **Desacoplo:** 100 nF X7R 16 V 0402 en cada pin de alimentación de U101, U102, U103, U105 y U106, más 10 µF X5R 16 V 0805 en +AFE y en −AFE por canal.
- **Pull-ups del polo B del acoplo:** 10 kΩ a +3V3 en `CH1_CPL_A` y `CH1_CPL_B`.
- Fuente de piezas y redes: `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/CH1_PIEZAS_Y_REDES.md`. Siguen abiertos: driver y economizador del relé, tensión de C_AC y a qué MCU va el 74HC165.

### 2026-10-04 — Driver y economizador del relé, C_AC y lectura del acoplo

Keneth eligió las tres opciones recomendadas por Claude:
- **Economizador de dos tensiones (cierra el «economizador» de D-03):** las bobinas de K101…K103 cuelgan de un nodo común `RELAY_COM`. Recibe 5 V por un P-MOSFET común de arranque (línea `RELAY_KICK` del 74HCT595, ~20 ms por cierre, la gestiona el firmware) o ≈ 3.0 V de mantenimiento desde 3.3 V por un Schottky. Por relé: 2N7002 (C8545) hacia `GND`, 1N4148W (C81598) en paralelo con la bobina, 100 Ω de puerta y 100 kΩ de puerta a masa. Bobina (dato de LCSC, sin hoja): 125 Ω, 200 mW a 5 V; mantenimiento ≈ 72 mW. **Pendiente: verificar en la hoja del HFD27 que 3.0 V lo mantienen cerrado.** El 74HCT595 pasa a 13 líneas de 16. Se descartan el RC en serie (~330 µF por relé, 120 mW) y el PWM (conmutación junto al AFE).
- **C_AC = 1.8 nF C0G 50 V, 0603.** S2/S2b: 5.75 V de peor caso (11.5 %).
- **El 74HC165 del acoplo cuelga del STM32**, en el bus de los 74HCT595 (+2 pines: dato de vuelta y carga). Cierra la duda de la sección A.

### 2026-10-04 — Relé del grueso: TQ2SA-5V-Z en lugar del HFD27/005-S

Keneth, tras la comparación de Claude con las dos hojas (`datasheet - componentes/C23911.pdf` y `C46047.pdf`): **K101…K103 = Panasonic TQ2SA-5V-Z (C22686)**, SMD, el mismo relé de la serie TQ2 que usa el DSO112. Sustituye al HFD27/005-S (C23911).
- Motivo: la hoja del HFD27 (p. 22, nota 4) exige un mantenimiento ≥ 60 % de la nominal, y el economizador de dos tensiones solo le daba ≈ 2.82 V (56 %; 54 % con el riel de 3.3 V al −3 %). El TQ2 no da un mínimo; en sus curvas de referencia (p. 7) la suelta queda en ≤ ~40 %, +~10 puntos a 70 °C. Con el mismo esquema recibe ≈ 2.88 V (58 %, ≈ 46 mW frente a 72 mW).
- Además: es un relé de señal (Ag + Au, de 10 µA a 10 mV), se monta en SMD en JLCPCB, va de −40 a 85 °C y ocupa 14 × 9 mm.
- **La bobina tiene polaridad:** pin 1 (+) a `RELAY_COM`, pin 10 (−) al 2N7002. Contactos: polo 1 con común en 3, NC en 2 y NO en 4; polo 2 con común en 8, NC en 9 y NO en 7 (p. 10).
- Pendiente: medir en el prototipo la tensión de suelta, y actualizar la lista de piezas del documento vivo (todavía dice HFD27). Las simulaciones no cambian: el relé se modeló genérico (Ron 0.1 Ω, Coff 1 pF) y la capacidad real de los contactos abiertos se mide para elegir Cb.

### 2026-10-04 — Valores E96 de CH1 con parejas serie/paralelo de piezas basic

Keneth: «sí, aplica las siete combinaciones», tras la evaluación de Claude con las 80 resistencias basic 0603 de JLCPCB. Objetivo: reproducir los valores simulados y auditados sin referencias extendidas (~3 USD por referencia y pedido) y obtener 1.11 kΩ, que no es E96 y no tiene stock.
- 499 Ω = 1 kΩ ∥ 1 kΩ (RL1, R125, R126) · 249 Ω = 270 Ω ∥ 3.3 kΩ (RL2, RG1, RG2) · 24.9 Ω = 49.9 Ω ∥ 49.9 Ω (RL5, RL6) · 2.26 kΩ = 2.2 kΩ + 68 Ω (RF2) · 8.06 kΩ = 7.5 kΩ + 560 Ω (R_OFF) · 5.23 kΩ = 5.1 kΩ + 120 Ω (VMID) · **1.11 kΩ = 1.1 kΩ + 10 Ω** (R123, R124; sustituye a la propuesta de 1.10 kΩ).
- Error ≤ 0.35 % frente al valor simulado, dentro del ±1 % del Monte Carlo de S7b: no se repite la simulación.
- CH1 pasa de 75 a 88 piezas y de 30 a 24 referencias extendidas (≈ 18 USD menos de cargo por pedido). Detalle: `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/CH1_PIEZAS_Y_REDES.md` §2.10 y `bom_ch1.py`.
- No se aplican en el divisor ÷100, la réplica ni VCHECK (alta impedancia o 0.1 %).

### 2026-10-04 — Orden del conmutador de acoplo: AC – GND – DC

Keneth eligió la opción recomendada por Claude: en el recorrido del SS23H37L6, **T1 = AC, T2 = GND, T3 = DC**. GND queda en el centro, como en los osciloscopios clásicos: al pasar de AC a DC se pasa por masa. Pines según el plano C883267 (filas de 4 a 0/6/10/14 mm, común a 6 mm; numeración propia 1–4 polo A y 5–8 polo B) en `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/CH1_PIEZAS_Y_REDES.md` §2.3. Al pasar a CH2/CH3 se aplicará el mismo criterio a sus valores (p. ej., los 2.37 kΩ del filtro de S9).

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
