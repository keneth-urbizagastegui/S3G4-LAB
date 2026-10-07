# Estado compartido

Revisión documental inicial: 2026-09-18. Agente: Codex. No se han repetido ensayos electrónicos ni conectado placas durante esta revisión.

## Estado documentado, no nueva certificación

- `comm_testbench/README.md` y sus actas registran aceptación de etapas de transporte, control, trigger, calibración, Wavegen, SCPI y DMM. Para cifras y alcance consultar el acta concreta: varios ensayos usan datos sintéticos y no certifican el front-end analógico definitivo.
- `client_app_testbench/README.md` registra M-01 a M-08 aceptados; M-04 conserva una fase 4.3 parcial. M-09 tiene empaquetado Android conforme, con prueba en teléfono pendiente. M-10/campaña CP-UI-01 a CP-UI-12 figura pendiente. Confirmar contra actas y trabajo posterior antes de actualizar esos estados.
- Hardware rev. 2: existen `docs/MAPA_PINES_FIRMADO.md`, `docs/ACTA_VERIFICACION_MAPA_PINES.md` y `firmware/stm32_afe_rev2`. El mapa firmado documenta correcciones frente al firmware heredado. No reutilizar el pinout antiguo como autoridad para rev. 2.
- Los puertos COM, el SSID y las condiciones del banco que constan en guías son referencias históricas; descubrir el estado actual antes de ejecutar pruebas físicas.

## Trabajo de contexto compartido

- Solicitud vigente: que Codex, Claude Code y agy conozcan el mismo proyecto al abrir una sesión sobre esta carpeta, usando context-mode sin repetir manualmente el contexto.
- Se crea memoria canónica en `ai-context/`, instrucciones de arranque para las tres herramientas y un MCP local `s3g4-context` con almacenamiento en `.ai-runtime/`.
- La documentación ignorada por Git se consulta mediante una lista explícita. Sus archivos no se añaden automáticamente al control de versiones.
- Validación técnica terminada: 103 fuentes indexadas, 0 ausentes y 12 comprobaciones MCP correctas. Codex reconoce la conexión, Claude muestra Connected y el panel `/mcp` de agy 1.2.6 confirma el servidor activo. Ver `ai-context/VALIDATION.md` para evidencia y límites.
- **Artefactos (23 sep, Claude):** los 7 publicados desde `docs/` coinciden con sus archivos locales, sin contar el envoltorio de publicación: rev 2.1, DSO112, WAVE2, OpenScope, black_scope, G473 y el esbozo de hardware. Los agentes leen esos archivos y el índice; los enlaces de claude.ai son privados de Keneth. El esbozo (`docs/esbozo_hardware_s3g4.html`) no estaba en `index.json` y se añadió.
- Los clientes que ya estaban abiertos necesitan una nueva conexión MCP para recoger la configuración nueva. La actualización automática del índice funciona; el registro de decisiones al terminar depende de seguir `AGENTS.md`.

## Próximas tareas del producto identificadas

1. Confirmar/practicar la prueba de M-09 en teléfono y completar M-10 con evidencia, cuando el usuario retome ese frente.
2. Consultar el estado específico del front-end y esquemático rev. 2 antes de planificar su integración; la revisión de contexto no determina que esté terminado.
3. Mantener estado y decisiones al terminar cada trabajo para que otra IA pueda retomarlo.

No se ha elegido automáticamente uno de estos frentes como nueva tarea de ingeniería.

## Frente activo: integración del front-end rev. 2 (18 sep 2026, Claude Code)

- El usuario eligió este frente. Guía para Altium: `docs/esbozo_hardware_s3g4.html` (generador en `docs/esbozo_hardware_gen/`). Incluye diagrama de bloques, esquema por hoja y conexión top, todo generado desde `docs/netlist_hoja*.py`.
- Hay hallazgos abiertos en los netlists, sin corregir y pendientes de decisión del usuario: `R1004_HDR` une VDDA con VCC_P5; las bobinas de los relés van a GND_RELAY desde la salida de un driver que sólo hunde corriente; U1002 usa 8 canales de un TPL7407 de 7; los niveles de 3.3 V gobiernan CD405x a 5 V; el bus SR/I2C/RST no tiene pin del MCU. Detalle en `ai-context/journal/2026-09-18-claude-esbozo-hardware.md`.

## Rediseño del AFE rev. 2.1 en curso (22 sep 2026, Claude Code)

- El usuario abrió este frente porque el coste de construcción del AFE rev. 2.0 le resulta demasiado alto. Documento vivo: `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` (artifact https://claude.ai/artifact/YLrJwmm5Cz6w864dUYsrBT), que se modifica sección por sección. La rev. 2.0 pasa a ser **una referencia más**, no la línea base.
- Trabajo cerrado: sección A (conector BNC y conmutador de acoplo) y sección B (protección, divisor compensado ÷20 y lista de compra para JLCPCB), con la matemática verificada.
- **D-06 acordado el 23 sep:** osciloscopio a 50 Vpk declarados, supervivencia a 250 Vrms en el rango ÷20 (estado de arranque) y protección de red de 600 V en el puerto del DMM. *(Esa última parte se sustituyó esa misma noche: el DMM ya no mide la red.)*
- **D-05 cambiado el 23 sep a ±40 V de fondo de escala.**
- **Sección C (sensibilidad y ancho de banda) propuesta el 23 sep:** 11 escalas de 5 mV/div a 10 V/div, con ×1 hasta 100 mV/div; grueso ×1/÷20 con un relé por canal y rama ×1 compensada (10 kΩ ∥ 10 nF); escalera de 8 tomas (1 … 1/100) con 74HCT4051; ganancia fija ×50 en dos etapas; ≈ −0.2 dB a 1.5 MHz y entre 0.2 y 0.5 % de división de ruido en todas las escalas. Pendiente: relé latching o monoestable, elegir amplificadores y buscar precios en JLCPCB. Detalle en `ai-context/journal/2026-09-23-claude-afe-seccion-c.md`.
- **Análisis exhaustivo del DSO112 (23 sep):** `S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html` (artifact https://claude.ai/artifact/1Q3Ajh4q39Pdic6AV6w1LR). Confirma la topología de D-05 y D-09. Deja seis propuestas **sin aplicar**: P1 grueso ÷100, P2 rama ×1 con 100 kΩ ∥ 1 nF, P3 autocero y VCHECK, P4 relé monoestable o latching, P5 RC antes del COMP y P6 offset por PWM. Corrige cinco afirmaciones anteriores sobre el DSO112, el DSO150 y el DSO138. Detalle en `ai-context/journal/2026-09-23-claude-analisis-dso112.md`. Generadores en `S3G4_LAB_rev2.1/herramientas/`.
- **Análisis del WAVE2 (23 sep):** `S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html` (https://claude.ai/artifact/LgEYV3M8LjE8RqbTvAQMcE). Nueva propuesta **P7, grueso sin relé**, como alternativa a P4, pendiente de decidir y de simular. **Corregido el modelo de ruido del divisor (kT/C)** en el documento vivo y en el análisis del DSO112: el ÷20 aporta 91 µV, no 864 µV; D-05 y D-06 no cambian. Detalle en `ai-context/journal/2026-09-23-claude-analisis-wave2.md`.
- **Análisis del OpenScope MZ (23 sep):** `S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html` (https://claude.ai/artifact/8KbSKL4sWnYoQzPJgKsRwf). Su canal sólo atenúa (suelo de 0.56 mV rms): **no cambia la elección P4/P7**. Aporta P8 (etapa final única), P9 (referencia ratiométrica), P10 (autocalibración encadenada) y P11 (disparo por analog watchdog). Ninguna aplicada. Detalle en `ai-context/journal/2026-09-23-claude-analisis-openscope.md`.
- **Análisis de black_scope (23 sep):** `S3G4_LAB_rev2.1/02_referencias/analisis_black_scope.html` (https://claude.ai/artifact/EQGpdo9q4Fu2EkwqAgykAn). Usa nuestro G473 con sus OPAMP internos como PGA: confirma que el OPAMP interno no sirve de etapa final (203 kHz a ×64, muestreo de 59 ns frente a los 200 ns exigidos, offset común con DAC2 cargado 2000 veces por encima de lo permitido). Aporta **P12, disparo por hardware** (COMP/AWD → ETR de un temporizador). Detalle en `ai-context/journal/2026-09-23-claude-analisis-black-scope.md`.
- **Partes analógicas del G473 revisadas (23 sep):** `S3G4_LAB_rev2.1/02_referencias/g473_analogico.html` (https://claude.ai/artifact/8fBAS9Tis7h8yQh9qnSciB), sobre DS12712 Rev 5 y RM0440 Rev 9. Confirma las velocidades de D-02 (sólo en canales rápidos y con V_DDA ≥ 2.7 V). Deja **P13** (reloj del ADC síncrono: HCLK 104 MHz /2), **P14** (ningún pin analógico por encima de V_DDA: el G473 no admite inyección positiva), **P15** (DAC en sample-and-hold para continua) y **P16** (calibración con GCOMP y sobremuestreo), sin aplicar. **Abierto:** con D-02, CH2 y CH3 (PE9, PE15) no llegan a ningún comparador; opciones: watchdog, segundo pin o CH2 en PE7 (COMP4). El ruido propio del ADC (0.16–0.24 % de división con VREF+ = 2.5 V) es del orden del del AFE. Detalle en `ai-context/journal/2026-09-23-claude-g473-analogico.md`.
- **Requisitos funcionales del osciloscopio acordados (23 sep):** `S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html` (https://claude.ai/artifact/X1DWGzQBZB2zT57mXPD4sG), RF-01…RF-19, registrados en `DECISIONS.md`. Resumen: CH1 a 2 MHz y CH2/CH3 a 1 MHz; sonda ×10 lineal hasta ±400 V; 1 MΩ con la misma capacidad en todas las escalas; disparo por flanco en los tres canales; 8 k muestras; ±1 % con autocalibración; las tres funciones a la vez y ≥ 4 h. Consecuencia: **el grueso es P4, con relé; P7 queda archivado.** Pendiente: requisitos del DMM y del AWG. Detalle en `ai-context/journal/2026-09-23-claude-requisitos-osciloscopio.md`.
- **Reorganización (24 sep):** todo el trabajo de la rev 2.1 vive en `S3G4_LAB_rev2.1/`: requisitos, documento vivo, referencias, simulaciones, herramientas y plan. Se empieza por su `LEEME.md` y `06_plan/PLAN.md`.
  - Se movió sin copiar; la tabla de rutas está en `DECISIONS.md` (24 sep).
  - Las 8 páginas se volvieron a publicar en los mismos enlaces (`ARTEFACTOS.md`).
  - Respaldo: commit local en Git, sin push.
  Detalle en `ai-context/journal/2026-09-24-claude-reorganizacion-rev21.md`.
- **Sección G, rieles, en curso (23 sep, noche):** en `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html` (versión 9 del artifact).
  - Árbol: cargador con power path → VSYS; buck de 3.3 V para el ESP32-S3; boost de 5.3 V → LM27762 (±5.0 V para AFE y DMM) y LDO de 3.3 V para el G473; convertidor aparte de ±6.5 V para el AWG; retroiluminación desde VSYS con PWM.
  - Con 5000 mAh: **6.0 h en el peor caso de RF-17** (2.76 W) y 8.1 h en uso típico.
  - Decisiones nuevas en `DECISIONS.md`: DMM sólo en baja tensión con masa común (revisa D-06 y RD-04/05/10), AWG con su convertidor, 5000 mAh, relés monoestables con economizador.
  - Falta elegir las piezas en LCSC y confirmar el consumo real de los amplificadores.
  Detalle en `ai-context/journal/2026-09-23-claude-seccion-g-rieles.md`.
- **Requisitos del DMM y del AWG acordados (23 sep):** `S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html` (https://claude.ai/artifact/5TwLhVKhkoYHuPQXJq9y2n), RD-01…RD-10 y RG-01…RG-08, registrados en `DECISIONS.md`.
  - DMM: tres bornes como el ELVIS II, 4½ dígitos con el ADC5 sobremuestreado, CAT II 600 V sin aislamiento pero con enclavamiento *(sustituido esa noche por baja tensión con masa común; desde el 30 sep, 50 V DC / 50 Vrms como el TIDA-01012)*, 2 A, alterna de 40 Hz a 20 kHz y prueba de diodo de 3.5 V.
  - AWG: dos canales, 1 MHz por DDS *(desde el 30 sep, sólo el seno; el resto hasta 100–200 kHz)*, ±5 V en dos rangos, 50 Ω protegido hasta ±15 V y arbitraria de 4096 puntos.
  - Pendiente: rangos concretos del DMM, rieles del AWG y presupuesto de energía con todo activo.
  Detalle en `ai-context/journal/2026-09-23-claude-requisitos-dmm-awg.md`.
- **Simulación P4/P7 ejecutada y auditada (23 sep):** Codex la entregó con código 0 (14 ensayos). Mi reejecución es idéntica. Los fallos de compensación de P4 ÷100 y de P7 fina venían de mi plan, por la contabilidad de parásitas. Los fallos reales:
  - P4 da 0.909 MΩ y cambia 8 pF entre posiciones (incumple RF-08).
  - En ambos diseños, la entrada del buffer llega a 6.1 V: falta una resistencia serie.
  - P7 muestra rodilla, distorsión con sonda ×10 y fuga del 4053.
  - Para la red, la rama ×1 debe ser P2-AT.
  - T07 quedó parcial.
  Auditoría en `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md`; diario en `ai-context/journal/2026-09-23-claude-auditoria-p4p7.md`.
- **Simulación P4/P7 planificada (23 sep):** carpeta nueva `S3G4_LAB_rev2.1/03_simulaciones/` (separada de la rev 2.0). Plan en `S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/PLAN_SIMULACION.md` y encargo en `ENCARGO_CODEX.md`. Construye Codex con **gpt-5.6-sol**, esfuerzo medium (se pidió GPT-6-Sol, pero la cuenta de ChatGPT no lo admite y Keneth eligió gpt-5.6-sol); audita Claude. En ejecución desde las 17:14 del 23 sep; sin auditar.
- Evidencia nueva recogida de `research_and_tests` (DSO112, DSO150, DSO138 mini, DSO158/wave2, TI TIDA-01012, Micro-DMM, EMBO, black_scope) y correcciones a cifras de ruido que yo mismo había dado mal. Todo el detalle, con valores y designadores, en `ai-context/journal/2026-09-22-claude-rediseno-afe-rev21.md`.
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists de la rev. 2.0.


## Entorno KiCad 10 + IA para la rev 2.1 (30 sep 2026, Claude Code)

- Keneth migra el diseño de Altium a KiCad 10.0.6. Instalados y verificados: plugins del PCM (Interactive Html BOM, Fabrication Toolkit 5.3.0, KiKit 1.8.1 con backend), plugin kicad-happy 2.2.1, MCP de usuario pcbparts y ltspice, y Konnect 0.12.1 (MCP de proyecto, aprobado por Keneth; lectura de la placa por IPC probada, escritura sin probar) y pcb-inspector 0.1.0 (instalado desde la release de GitHub, no por nombre de PyPI; sin visión ni MCP).
- Esqueleto del proyecto en `S3G4_LAB_rev2.1/04_esquematicos/kicad/` (proyecto `s3g4` vacío, PCB de 2 capas por defecto, reglas para IA en su `AGENTS.md`). Todavía no hay diseño: ni contorno, ni stackup de 4 capas, ni reglas DRC. Trabajo en la rama `ai/prueba-konnect`. Detalle y pendientes en `ai-context/journal/2026-09-30-claude-entorno-kicad10-ia.md`.
- **Coherencia del osciloscopio (30 sep):** el documento vivo (versión 11) ya dice relé monoestable en toda la sección C. Además, C.2 avisa de que P4 aún no cumple RF-08, C.4 incluye CH1 a 2 MHz (GBW ≥ 100 MHz) y la sección D sigue RF-03. Faltan las contradicciones del DMM, del AWG y de los rieles. Detalle en `ai-context/journal/2026-09-30-claude-coherencia-osciloscopio.md`.
- **Límite del DMM (30 sep):** 50 V en continua y 50 Vrms en alterna, como el TIDA-01012 (decisión de Keneth). Siguen los tres bornes y los 2 A. Están corregidas las contradicciones del DMM: rangos, sobremuestreo ×256 + ×4 y divisor de la prueba de diodo. Detalle en `DECISIONS.md` (30 sep) y en `journal/2026-09-30-claude-coherencia-osciloscopio.md`.
- **Coherencia del AWG (30 sep):** RG-02 revisado por Keneth (seno a 1 MHz; cuadrada, triángulo y rampa hasta 100–200 kHz). RG-07 queda abierto hasta elegir los rieles del AWG, porque la fuente de ±5 V / ±50 mA no cabe con la salida de 50 Ω. Las consecuencias de RG-03 y RG-01/RG-04 ya apuntan a la sección G. Detalle en el diario `2026-09-30-claude-coherencia-osciloscopio.md`.
- **Coherencia de los rieles (30 sep):** el documento vivo (versión 14) cuadra con `calc_rieles.py`. Quedan anotados: 13 amplificadores en G.3 (con P8 sin decidir); la inyección de las sujeciones, que absorbe la carga normal mientras el AFE está encendido; la sujeción del AWG con ±15 V, que no puede ir a sus rieles de ±6.5 V (abierto); y la falta de un apagado propio del DMM (RF-18). Plan actualizado.
- **Display en KiCad (1 oct):** primera pieza de la librería del proyecto: símbolo `s3g4:ER-TFT035IPS-6-4405` (JP1, 40 pines, datasheet pp. 11-12) y huella con zócalo hembra 2x20, 4 separadores M2.5 x 11 mm y 3D apilado a 11 mm (datasheet p. 9, vista frontal). El montaje tipo DSO138 es idea de Keneth, no decisión cerrada. El STEP de 49 MB está versionado en `lib/3d/`. Rama `ai/footprint-tft035`. Detalle en `journal/2026-10-01-claude-footprint-display-tft035.md`.
- **1–2 oct (Claude):** todas las ramas unidas en `main` y subidas (tag local `respaldo/main-antes-de-unir`). Guía del canal rápido CH1 en `S3G4_LAB_rev2.1/01_diseno/canal_rapido_ch1.html`. Abiertos P1, P8, P13, el filtro de CH1 y el disparo externo (propuesta: no, con disparo interno desde el AWG). Detalle en `ai-context/journal/2026-10-02-claude-ramas-y-canal-rapido.md`.
- **2 oct (Claude):** registradas en DECISIONS dos decisiones de Keneth: disparo sin entrada externa (fuentes CH1–CH3 y el AWG interno) y entrada sin la red conectada directamente (revisa D-06/RF-06; cifras de seguridad pendientes). Revisión de la entrada de CH1 con 13 hallazgos y propuesta P4b en `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html`; plan de simulación S0–S8 en el mismo documento y en `06_plan/PLAN.md`, paso 2. Pendientes: P1 (recomendado ÷100), cifras de seguridad y quién ejecuta.
- **2 oct (Claude, cierre):** acordados P1 = ÷100 con 6 tomas, ±100 V sin daño con ESD ±8/±4 kV, y simulaciones por Codex. Encargo S1 listo en `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/ENCARGO_CODEX_S1.md`, sin lanzar.
- **2 oct (Claude, noche):** S1 ejecutado por Codex y auditado (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S1.md`): reproducible byte a byte; C1–C5 cumplen en el nominal (C5 con la sonda corregida); E4 pide un ajuste por canal para la planitud de ÷100 y C_EQ seleccionado en prueba. Pendiente de Keneth: el trimmer y el encargo S1b.
- **3 oct (Claude):** S1b auditado y reproducido (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S1b.md`): los 9 criterios pasan. Pendiente de Keneth: trimmer R1 (2–6 pF) con Cb seleccionado en prueba, o R2 sin stock. Siguiente: S2, que necesita los modelos de fabricante (BAV199 de Nexperia y el buffer FET).
- **3 oct (Claude):** S2 auditado (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S2.md`). Pendiente de Keneth: subir a 200 V R_EQ, C_EQ y C_S; descartar el AD8065 como segunda fuente directa; S2b con ESD IEC realista y métrica I²t.
- **3 oct (Claude):** S2b auditado: la entrada P4b de CH1 con OPA810 cumple en simulación RF-05/07/08 y el nivel de seguridad acordado (±100 V, ESD ±4 kV contacto / ±8 kV aire). Pendiente de Keneth: cómo encajar el OPA828 como segunda fuente (Cin 31 pF). Siguiente: S3.

## Punto de retomada de la rev 2.1 — CH1 (3 oct 2026, Claude)

- **Hecho y auditado:** S0, S1, S1b, S2 y S2b de la entrada P4b de CH1 (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_*.md`). Con el OPA810, la entrada cumple RF-05/07/08 y el nivel de seguridad acordado.
- **Piezas fijadas:**
  - divisor 2 × 549 kΩ 1206 + 11.0 kΩ, Ct 2 × 20 pF, trimmer SEHWA 2–6 pF (C22468120), Cb ≈ 1.08 nF seleccionado en prueba;
  - R_S 2 × 49.9 kΩ 1206 ∥ C_S 1.5 nF ≥ 200 V;
  - relé HFD27 DPDT con réplica R_EQ 10 MΩ 1206 ∥ C_EQ ≈ 12 pF ≥ 200 V (en prueba);
  - BAV199 Nexperia a ±5 V, TVS de riel, R_PROT 1 kΩ, C_AC 1.8 nF;
  - OPA810 como fuente única (OPA828, alternativa documentada);
  - escalera de 6 tomas con 74HC4051 (+ GND + VCHECK).
- **Siguiente:** S3 (buffer + escalera + ×5 · ×10 con amplificadores reales). Después S4–S8.
- **3 oct, tarde:** U103 = **AD8039** (C96525) y E12 relajado a ≤ 0.45 % de división (DECISIONS 3 oct). El LM6172 queda fuera: a ±5 V da 70 MHz. Plan y encargo de S3 escritos (`PLAN_SIMULACION_S3.md`, `ENCARGO_CODEX_S3.md`). Modelos del AD8039 y del 74HC4051 (Nexperia) comprobados. Red de U103 cambiada a R_G = 249 Ω por el pico en el modelo. La diferencial de U103A en saturación (posible > ±4 V) se mide en E14. Codex S3 ejecutado y **auditado** (`S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S3.md`). Reproducible byte a byte. Pasan pérdida, pico, THD, consumo y recuperación de los amplificadores. El ruido da 0.30–0.40 % con el ruido de la hoja (el modelo de LTspice del AD8039 da el doble). Los 551 µs de 200 mV/div son de la red de entrada. **Hallazgo:** la diferencial de U103A llega a 4.10 V (máx. ±4 V) con ≥ 4.9 V en la BNC a 5 mV/div. Keneth eligió la protección (a) y aceptó ≈ 0.6 ms tras conducir los BAV199 (DECISIONS 3 oct). S3b ejecutado y auditado (`AUDITORIA_CLAUDE_S3b.md`): BAT54S descartado por pico (+6–8 dB); BAV199 lento (1.1 µs); **BAV99 (C2500) con R_SER 470 Ω pasa todo** según la comprobación de Claude. **Keneth confirmó 470 Ω + BAV99 en U103A y en U103B** (comprobado: 0.68 V de diferencial, 0.41 %, sin pico) y la propuesta de jack de 9–12 V con power path para la sección G. Documento vivo actualizado (versión 15: C.4, C.5 y C.6 con S3/S3b). **S4 planificado** (`PLAN_SIMULACION_S4.md`, `ENCARGO_CODEX_S4.md`): P8 a 3.3 V, offset por el DAC del G473 y OPA836. Modelo del OPA836 descargado (con permiso de Keneth) y comprobado: ruido correcto; pico de +1.5 dB que se quita con C_F = 1 pF (variante); el modelo no trae los diodos de entrada (se añaden como suposición). Codex S4 terminó la campaña (199 simulaciones) y se quedó sin cupo de ChatGPT antes de su respuesta final. **Auditado por Claude** (`AUDITORIA_CLAUDE_S4.md`, mismos valores en la reejecución): cumple con C_F = 1 pF. La no linealidad y la THD que da el acta son errores de cálculo y del plan. **Regla nueva:** el AFE (EN del LM27762) sólo se enciende con VDDA presente. Keneth aceptó C_F = 1 pF, M1, la regla de secuencia y el offset de −4.85 div. S5 (filtro, U105 = AD8039 doble) ejecutado y **auditado** (`AUDITORIA_CLAUDE_S5.md`, 13/13 CSV idénticos). Bessel falla el Monte Carlo (corta en 1.82 MHz); Butterworth tarda 1.08 µs en recuperarse; el intermedio (TR) pasa todo. Claude recomienda TR reescalado (1.11 kΩ / 499 Ω: 2.011 MHz, 21.7 dB a 4.5 MHz). Hay que quitar en S7 la carga ficticia de 1 kΩ ∥ 10 pF de U103B. **Keneth eligió TR reescalado** (1.11 k / 499 Ω; verificación en S7). S6 (muestreo entrelazado del ADC) ejecutado y **auditado** (`AUDITORIA_CLAUDE_S6.md`, 11/11 CSV idénticos): el driver cumple (no lineal 0.0009 LSB, −0.043 dB, margen de fase de 78°). E18 «falla» porque mide el retraso interno R_SW·C_S ≈ 4 ns: criterio mal planteado, corregido. **S7 (canal completo) terminado y auditado** (`AUDITORIA_CLAUDE_S7.md`): 8/9 criterios (C8 = recorte del offset ya aceptado); 2.007 MHz, 0.25–0.32 % de ruido y protecciones dentro. Reproducción completa pendiente. **S7b terminado y auditado** (`AUDITORIA_CLAUDE_S7b.md`): 4 416 casos y Monte Carlo de 500 placas. Pasan en ≥ 95 % (casi todo al 100 %): ancho de banda, pico, ruido, ganancia, protecciones con rieles de 4.8/5.0 V, recuperación y offset (≈ 97 %). **Falla sólo el trimmer de 2–6 pF: basta en el 83 % de las placas.** **Keneth eligió A; S7c (Claude, `ACTA_S7c.md`) lo resuelve: 100 % de las placas en rango** con Ct1 20 pF ±2 %, Ct2 15 pF ±2 %, Cb 1 nF ±1 % + 68 pF y un hueco DNP. **CH1 queda cerrado en simulación.** Siguiente: documento vivo (C.6, D, E, F y G.3), reproducción de muestra de S7/S7b, y S8 (KiCad) o S9 (CH2/CH3) (±4.9 V, C_S 1.2 nF y Monte Carlo ampliado con rieles, VREF, offsets y trimmer; criterios funcionales en ≥ 95 % de placas). Revisión completa de CH1 hecha por Claude (`CH1_entrada/REVISION_CLAUDE_CH1.md`, cifras de `chequeo_claude/revision/revision_ch1.py`). Hallazgos:
  - **R1:** C_S debe ser 1.2 nF y C_EQ ≈ 8.7 pF, no 1.5 nF / 12 pF como dice C.6;
  - **R2:** el 74HC4051 queda sin margen en VCC − VEE = 10 V (propuesta: ±4.9 V);
  - **R3:** consumo de 23 mA por riel en tres canales, no 39;
  - **R4:** valores de VCHECK y offset de la entrada calibrado en GND;
  - **R5:** faltan las secciones D, E y F del documento vivo.
- **Keneth (3 oct, noche):** sí a R1 (C_S 1.2 nF, C_EQ ≈ 8.7 pF) y R2-A (rieles del AFE a ±4.90 V). **Criterio permanente: diseñar con tolerancias reales y márgenes**, aceptar si funciona en ≥ 95 % de placas (DECISIONS). S7 corre con ±5 V y los valores viejos de C_S/C_EQ, así que hará falta un **S7b** con ±4.9 V, C_S 1.2 nF, Monte Carlo ampliado (rieles, VREF, dispersión de los amplificadores) y criterios funcionales. S3b se había lanzado a las 16:01 (`PLAN_SIMULACION_S3b.md`): R_SER 470 Ω / 1 kΩ × BAT54S / BAV199, ruido con `AD8038_ltspice_ruido_hoja.sub`. Detalle en `journal/2026-10-03-claude-s3-u103.md`.
- **Cómo retomar:** `ai-context/journal/2026-10-03-claude-retomar-ch1.md` y luego `journal/2026-10-03-claude-s3-u103.md`.

## Punto de retomada — CH1 cerrado (4 oct 2026, Claude)

- **CH1 cerrado en simulación (S0–S7c), auditado.** La cadena final y sus piezas están en `ai-context/journal/2026-10-04-claude-retomar-s8-s9.md`. Documento vivo en la versión 16, con las secciones D, E y F nuevas.
- **Siguiente:** S8 (esquema de CH1 en KiCad) y S9 (CH2/CH3 a 1 MHz).
- **4 oct (Claude): S9 planificado** en `S3G4_LAB_rev2.1/03_simulaciones/CH23_entrada/` (`PLAN_SIMULACION_S9.md`, `ENCARGO_CODEX_S9.md`): CH2/CH3 = CH1 con el filtro a 1 MHz y un ADC a 3.47 MSa/s (2.5 ciclos); variante B con **LM6172** en U103/U105 por coste (DECISIONS 4 oct; no adoptada). **Bloqueo:** falta en el proyecto el modelo PSpice y la hoja del LM6172. Modelo y hoja del LM6172 ya en el proyecto; **Codex S9 lanzado el 4 oct a las 09:30**, pendiente de auditar.
- **4 oct (Claude): S8 preparado** en `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/` (`CH1_PIEZAS_Y_REDES.md`, `ENCARGO_KONNECT_S8.md`): hoja plana de CH1, dibujada con Konnect desde una sesión abierta en `04_esquematicos/kicad/`, en la rama `ai/s8-ch1-esquema`. **Dibujado el 4 oct** por una sesión de Konnect (`INFORME_S8.md`) y **auditado** por Claude (`AUDITORIA_CLAUDE_S8.md`): correcto pin a pin. Pendiente: C125/C126 a 25 V en la hoja, DNP de C103, símbolos y huellas propios y unir con `main`. Decisiones del 4 oct incluidas: cuerpo del BNC a AGND, desacoplo, pull-ups, economizador de dos tensiones, C_AC de 50 V, 74HC165 en el STM32 y **relé TQ2SA-5V-Z** (sustituye al HFD27). Valores E96 con parejas basic serie/paralelo (88 piezas, 24 referencias extendidas, ≈ 19.6 USD por canal; `bom_ch1.py`).
- **4 oct, noche (Claude): revisión de coherencia de todos los documentos vivos** con las decisiones del día y las simulaciones S1–S7c: documento vivo (versión 18), requisitos del osciloscopio (versión 5, regenerados con `build_requisitos.py`: RF-04 a 12 escalas hasta 20 V/div, RF-06 con ±100 V y ESD), hoja de especificaciones (versión 2), `canal_rapido_ch1.html`, aviso de histórico en `revision_entrada_ch1.html`, `PLAN.md`, los `LEEME.md`, `ARTEFACTOS.md`, `SOURCES.md` e `index.json`. Las actas, auditorías y diarios no se tocan (son registro).
- **Cómo retomar:** lee `ai-context/journal/2026-10-04-claude-retomar-s8-s9.md`.
- **Retomar el lunes 5 oct, 21:00:** `ai-context/journal/2026-10-05-claude-retomar-s8b-s9b.md` (Codex S9-B reanudado a las 20:38 del 4 oct; S8b listo para la sesión de Konnect; la rama `ai/s8-ch1-esquema` todavía sin unir).

## S9-B pausado por Keneth — 4 oct 2026, 21:35 (Codex)

- **Instrucción vigente:** parar después de acabar la corrida actual y dejar contexto para otra IA. No continuar automáticamente ni lanzar la continua corregida hasta que Keneth retome. Este punto supera las menciones anteriores de S9-B «en curso».
- **Campaña principal completa:** 4 295/4 295 casos, 14 391 ejecuciones nativas; auditoría estructural código 0 y cero errores. `CH23_entrada/S9/B_hoja/campaign/s9b_meta.json` conserva código 1 por cambio externo detectado en STATE, no por casos fallidos. No relanzar la campaña principal ni A.
- **Repetición corta ya iniciada también terminada:** 25/25 casos, 57 ejecuciones nativas, código 0, a las 21:34 Lima. Coordinador detenido; comprobación final sin procesos S9 activos. No se lanzó OP corregida.
- **Pendientes:** auditoría/comparación del smoke repetido; corregir la doble contabilización del offset LM6172 en sólo las cuatro cohortes de continua B; auditar, generar columna B/informe y comparar con AD8039. C9 original sesgado = 53.4/57.4/53.4/57.4 %, sin aceptación final ni elección de variante. C8 vigente ≤2 µs; actas históricas con 1 µs no gobiernan.
- **Retomada y evidencia detallada:** `ai-context/journal/2026-10-04-2135-codex-pausa-s9b.md` (rutas, hashes, procesos detenidos, límites y orden de continuación). El bloque B de ACTA sigue sin informe final. S8b permanece separado y pendiente.

## S9-B retomado y cerrado en simulación — 6 oct 2026, Codex

- **Estado vigente:** Keneth pidió retomar el encargo de Claude; supera la pausa anterior. Campaña OP corregida y coordinador terminados con código 0. No quedan corridas S9-B por lanzar. Auditoría externa de Claude pendiente.
- **Resultado corregido:** 2 000/2 000 casos (500 placas emparejadas × cuatro escalas), 12 000 puntos OP de referencia, auditoría de 12 000 decks con cero errores. Ganancia y centro compensable 500/500 por escala. C9 en 5 mV/div, 50 mV/div, 0.5 V/div y 5 V/div: **96.6 / 95.4 / 96.6 / 95.4 %**, cumple el mínimo por escala. **Las mismas placas que cumplen las cuatro a la vez son 471/500 (94.2 %)**: no afirmar rendimiento conjunto ≥95 %; pendiente de valorar por Claude/Keneth.
- **Trazabilidad:** sólo cuatro fuentes MC de offset cambian +2.986 mV en el parámetro SPICE (−2.986 mV efectivo); modelo intacto, SHA256 `4fb5d82e3319553113ba8ff7c8ff5bc4b7fa65e9a13b59dea2173140fe90d31b`. Guard de 26 403 archivos sin diferencias al cerrar. 12 005 intentos registrados, un timeout recuperado, ningún caso definitivamente fallido; los fallos C9 se incluyen. Smoke 25/25 auditado y reproducible a 1e-9.
- **Entrega:** `S3G4_LAB_rev2.1/03_simulaciones/CH23_entrada/RESPUESTA_FINAL_S9_B.md`, bloque B de `ACTA_S9.md`, `resultados/s9b_*`, tabla de calibración B de 12 escalas y `S9/B_hoja/op_corregido/`. C1–C9 pasan en el alcance por escala/determinista declarado; C8 vigente ≤2 µs, K4 reutilizado de A. Campaña B original conserva código 1 por cambio externo de STATE y C9 sesgado de 53–57 %; no reemplaza el resultado corregido. A/CH1 y modelos de fabricante preservados.
- **Límites y siguiente:** copia LM6172 no validada por TI, saturación/protecciones National y sin dispersión de GBW/Ib/temperatura. No se adopta variante ni remedio ni se ensaya hardware. Revisar el 94.2 % conjunto, base S7b/S7c y U105 sin 470 Ω/BAV99; después decisión de Keneth y cifras G.3/G.4. S8b sigue separado. Detalles: `ai-context/journal/2026-10-05-codex-retomada-s9b.md` (sesión del 5 al 6 oct). No relanzar A ni las campañas completas para auditar esta entrega.

## Auditoría de Claude: S9-B y S8b — 6 oct 2026

- **S9-B auditado** (sin repetir campañas). Signo del offset correcto: los parámetros corregidos son los originales +2.986 mV exactos, y con `VOS IP IPR` eso da un offset efectivo uniforme de ±3 mV. Recalculé el C9 desde `s9b_op_corregido.csv`: 483/477/483/477 por escala y 471/500 (94.2 %) conjunto, coincide. **El conjunto de A, que no estaba calculado, es 481/500 (96.2 %).** B no cumple el ≥ 95 % conjunto; sus fallos ahora son de recorrido negativo (mínimo 4.33 div), y en A de recorrido positivo. B consume 109 mW por canal frente a 63 mW de A, con más ruido (0.286 frente a 0.234 %div). **Decidido el 6 oct: AD8039 en CH2/CH3** (DECISIONS). Tabla G.3/G.4 rehecha el 6 oct: M1 = 2.52 W y 6.6 h (antes 2.76 W y 6.0 h); los relés cuestan ≈ 0.28 W de batería, no 0.16 W.
- **S8b auditado:** netlist reexportada idéntica; `verificar_s8.py` da código 0 (89 piezas, 56 redes); ERC 15 = 7 `power_pin_not_driven` (uno por riel, sobre `power:`) + 3 `pin_not_driven` + 5 `isolated_pin_label`. El detector da 0 solapes, pero no mira etiquetas contra textos: en la etapa final, CH1_VMID_LO y CH1_ROFF_MID se cruzan con textos de R131/R147/R128, y VREF_2V5 toca a R130. Es cosmético. Rama unida en `main` el 6 oct (db94b62, sin push). Pendiente: cajetín y ERC 15 (Keneth en KiCad). El STEP de 49 MB del display salió del historial sin subir y queda ignorado, en disco. Detalle: `ai-context/journal/2026-10-06-claude-auditoria-s9b-s8b.md`.

## S10 preparado: esquema de CH2/CH3 — 6 oct 2026, Claude

- Rama `ai/s10-ch23-esquema`. En `S3G4_LAB_rev2.1/04_esquematicos/S10_CH23/`:
  - `CH23_PIEZAS_Y_REDES.md`: reglas de copia desde CH1 y cambios del filtro;
  - `verificar_ch23.py`: deriva lo esperado de `s8_ch1.net`; probado con CH1 (0 diferencias) y con una copia sintética de CH2 (detecta los 8 cambios);
  - `ENCARGO_KONNECT_S10.md`.
- Decisiones de Keneth del 6 oct en DECISIONS: una hoja por canal, referencias 2xx/3xx y RFILT1 = 2.2 kΩ + 150 Ω.
- **Siguiente:** Keneth cierra KiCad, abre una sesión de Claude en `04_esquematicos/kicad` y pega «Lee y cumple ../S10_CH23/ENCARGO_KONNECT_S10.md». Después, auditoría de Claude.

## S10 ejecutado: CH2 y CH3 dibujados — 6 oct 2026, Claude (Konnect)

- Hojas `ch2.kicad_sch` y `ch3.kicad_sch` (87 piezas cada una) en la rama `ai/s10-ch23-esquema`, sin push. `verificar_ch23.py` código 0; ERC 31 (7 rieles + 9 pin_not_driven + 15 isolated_pin_label, sin otros tipos); 0 solapes de texto.
- **Pendiente de Keneth:** abrir y guardar ch2/ch3 en KiCad (ch2 trae una ruta de instancia obsoleta) y rellenar el cajetín; después auditoría de Claude. Detalle: `S10_CH23/INFORME_S10.md` y `ai-context/journal/2026-10-06-claude-s10-esquema-ch23.md`.

## Orden nuevo y documentos al día — 6 oct 2026 (noche), Claude

- Keneth: D-07 aceptada; RE-01 en espera (criterio: componentes baratos y circuitos mínimos); **siguiente, el DMM, después el AWG y luego el mapa de pines**, separando los recursos analógicos de los digitales del STM32. Los esquemas de CH1–CH3 se dejan como están. Todo en DECISIONS (6 oct).
- Actualizados: `06_plan/PLAN.md` (reescrito), el documento vivo (D-07 cerrada, S9 cerrado con la AD8039, K4), `LEEME.md` de la rev 2.1, `05_informes/LEEME.md` y `03_simulaciones/LEEME.md`.
- Corregido en S10: el −3 dB nominal de CH2/CH3 con la AD8039 es 1.001 MHz; en la tabla había puesto la cifra del LM6172.

## DMM empezado — 7 oct 2026, Claude

- Decisiones de Keneth (DECISIONS, 7 oct): divisor de 10 MΩ con tomas y 74HC4051 (sin relés); amplificador doble de deriva cero externo; aguantar la red unos segundos (RD-10); rangos aceptados.
- Borrador de arquitectura: `S3G4_LAB_rev2.1/01_diseno/dmm_arquitectura.md`, con bloques, rangos, la lista de reserva de recursos del G473 (ADC5 diferencial PD13/PD14, OPAMP5/COMP7 en PB14, DAC2_CH1) y lo abierto. Lo principal abierto: el riel de la pieza de deriva cero, porque las habituales son de 5.5 V como máximo.
- Siguiente: sección H del documento vivo con valores y la pieza elegida; luego la simulación S11 con Codex.
- **7 oct, sección H del DMM:** guía `01_diseno/dmm_rev21.html` y hoja `00_requisitos/especificaciones_dmm.html`, las dos publicadas (ARTEFACTOS). Propuesta de diseño:
  - divisor 9 M / 900 k / 100 k (0.1 %) con R_PROT de 3 × 33 kΩ;
  - un 74HC4051 de señal con 8 entradas (incluido el autocero);
  - OPA2188AIDR (C17271) a ±4.9 V: A con ×1/×10 y B con el derivador ×10;
  - driver diferencial RRIO a 3.3 V con VCM de 1.25 V hacia PD13/PD14 (±2 V = ±19 999 cuentas);
  - ohmios por razón con 4051 de fuerza y de sentido, R_ref de 301 Ω a 10 MΩ;
  - continuidad por PB14 y COMP7.

  Abiertos: la PTC, el fusible, la pieza del driver y el interruptor de carga. Siguiente: el encargo S11 para Codex.
- **7 oct, plan de referencias del DMM:** `S3G4_LAB_rev2.1/06_plan/PLAN_REFERENCIAS_DMM.md`.
  - Un estudio a fondo por referencia, con el método de las anatomías del osciloscopio.
  - Locales: TIDA-01012, HydraMeter 0.4, Micro-DMM, STM32 DMM de EEWorld 77845 (sin esquemático) y los artículos de Analog Devices de 7.5 dígitos.
  - Propuestas de internet: TIDA-00879, EEVblog 121GW y el multímetro STM32 de Martin.
  - Sin adoptar módulos. Propuestas numeradas desde P17.
  - **La sección H queda en pausa** hasta la síntesis; luego S11.
  - Pendiente de Keneth: permiso de descarga, incluir R6–R8 y el orden.
- **7 oct, referencias del DMM:**
  - Descargados: TIDA-00879 (guía, esquemático, BOM y layout, de ti.com); esquemático del 121GW (copia de archive.org, porque eevblog da 502) y su manual; repositorio de Martin (STM32F373).
  - **R1 TIDA-01012 hecho:** `02_referencias/dmm_tida01012.html` (artefacto BzuS4XnvR7xVfP3ZutR9No). Propuestas sin aplicar: P17 patas bajas conmutadas, P18 compensación con la misma τ, P19 fuerza y sentido, P20 filtro del ADC5 por carga de muestreo, P21 firmware de medida, P22 riel propio del DMM.
  - Siguiente: R2 HydraMeter.
- **7 oct, R2 HydraMeter hecho:** `02_referencias/dmm_hydrameter.html` (artefacto 5j4fYKqbpLK8TxGpkFgE7D).
  - Propuestas P23 protección escalonada, P24 ohmios con medida en el borne, P25 corriente de la fuente con conversión V→I (sin divisores), P26 calibración multipunto, P27 derivador de 4 terminales con punto estrella.
  - Hallazgo para la síntesis: los divisores ÷4 de X6 en la sección H roban corriente al DUT.
  - El manual de servicio del 34401A ya está en `research_and_tests/Agilent_34401A/` (167 p, esquemas en pp. 150–165). Ojo: la URL /us/ de Keysight devuelve su web en PDF; vale la /mu/.
  - Siguiente: R6 TIDA-00879.
- **7 oct, R6 TIDA-00879 hecho:** `02_referencias/dmm_tida00879.html` (artefacto XKxwSffsJUNX7j4EGX2iLx).
  - Es el antecesor del TIDA-01012: mismo front-end, con los ADC ΣΔ de 24 bits del MSP430F6736.
  - Hallazgos: R19 CRHV1206 de alta tensión; dos trimmers de 4.5–20 pF que el 01012 quitó; DC ±(0.03 % + 5) pero alterna solo hasta 1 kHz; calibración compilada en el código.
  - Propuestas P28 (resistencia de entrada de alta tensión) y P29 (calibración en memoria no volátil).
  - Siguiente: R7 EEVblog 121GW.
- **7 oct, R7 EEVblog 121GW hecho:** `02_referencias/dmm_121gw.html` (artefacto YcB94Hqks4aYz739W2KLwM). Lo que aporta:
  - Confirma P17: el HY3131 pone a masa las patas bajas bajo 10 MΩ.
  - Protección CAT III: PTC + R + S05K575 en serie; fusibles HRC de 400 mA (10 kA) y 11 A (20 kA); puente DF10S como sujeción; ×10 MAX4238 «Low Burden».
  - Propuestas P30 (PTC en la fuente de ohmios: cierra el pendiente de la sección H), P31 (fusible HRC cerámico + puente) y P32 (aviso de fusible abierto).
  - Siguiente: R3 Micro-DMM.
- **7 oct, R3 Micro-DMM hecho:** `02_referencias/dmm_microdmm.html` (artefacto VXTHBpRXxs9tDhqPwQFTb6).
  - El puente de Mann (cable abierto en tensión) funciona en SimplifiedOpenLeadVoltmeter, Feather Redux y OpenLead_Headless_V3. En la DMM_KiCAD_V4_next está dibujado al revés y no puede romperse.
  - La prueba depende de una bajada de ≈ 0.5 MΩ que no está en el esquema (probablemente la fuga del Schottky): umbrales por placa.
  - Su ohmímetro de divisor (5 V / 22 kΩ, referencia supuesta) da de −18 % a +44 % en 4.7 MΩ sin calibrar; confirma la razón y las R_ref por rango de la sección H.
  - Propuestas P33 (cable abierto con resistencias definidas; variante B = lectura breve en el rango de 20 MΩ, sin piezas) y P34 (en ohmios, detectar tensión externa y desconectar la fuente). Ninguna aplicada.
  - Corrige el matiz de RD-09: el Micro-DMM no inyecta una corriente definida.
  - Siguiente: R8 Martin + R4 EEWorld 77845. Detalle en `journal/2026-10-07-claude-dmm-microdmm.md`.
- **7 oct, R8 Martin y R4 EEWorld 77845 hechos:** `02_referencias/dmm_martin.html` (artefacto R3vvm1wXKejCDjdHz8xVFR) y `dmm_eeworld77845.html` (ficha corta, JMeU9V49kriNvnQjgBTxeg).
  - Martin, rev 1.5: STM32F373 con dos ΣΔ de 16 bits sincronizados; 1 MΩ con patas de 15/150 kΩ a COM; COM a VREF/2 = 0.9 V; derivadores de 50 + 5 mΩ en serie con toma elegida e INA199.
  - Cuantificados: cruce V→I del 2.6–2.8 % del fondo (IN− lejos del derivador), error del RMS (4.2 mV en vacío y +23 % con 10 mV en el rango de 60 mV) y calibración escrita por un firmware aparte. Las ganancias de corriente calibradas no cuadran con ninguna variante del INA199 (NO VERIFICADO).
  - EEWorld: STM32F103 con SAR de 12 bits, ≈ 1 % medido; sin esquema, no está en OSHWHub. El MAX4080 solo trabaja en el lado alto (4.5–76 V).
  - Sin propuestas nuevas: refuerzan P17, P19, P20, P21, P26, P27 y P29.
  - Siguiente: R5 Analog Devices. Detalle en `journal/2026-10-07-claude-dmm-martin-eeworld.md`.
- **7 oct, R5 Analog Devices hecho:** `02_referencias/dmm_adi_errores.html` (artefacto LsJG4aZhYxcP8A2SGfAiZN).
  - Método de presupuesto de errores de ADI (7½ dígitos): ganancia en % de lectura y offset en % de rango; la INL cuenta como offset; coeficiente × ΔT más deriva (√t, Arrhenius); suma cuadrática. Sus cifras se reproducen; la ecuación (1) del artículo tiene el signo cambiado.
  - **Hallazgo para la sección H:** la INL diferencial del ADC5 (DS12712, T.63: 2.1 típ. / 3.2 máx. LSB) son **26–39 cuentas** de 100 µV, no menos de 10 como dice §8. El 0.1 % de lectura se sostiene (579–630 ppm con 23 ± 5 °C y un patrón del 0.05 %, sin redes apareadas). Además, Ib del OPA2188 es de 850 pA máx. (H citaba 160 pA, la típica).
  - Propuestas P35 (presupuesto con el método de ADI), P36 (medir la INL del ADC5 y elegir: +40 cuentas, linealización o ΣΔ externo) y P37 (los cuatro ensayos de ADI en S11 y en el banco). Ninguna aplicada.
  - Siguiente: R9 Agilent 34401A. Detalle en `journal/2026-10-07-claude-dmm-adi.md`.
- **7 oct, R9 Agilent 34401A hecho:** `02_referencias/dmm_34401a.html` (artefacto Gd8rGXutjjVU3zHBf2p9LY), a partir del manual de servicio (esquemas pp. 157–160). **Las nueve referencias del DMM están estudiadas.**
  - Lo que aporta: autocero MC/MZ/PRE con precarga; compensación de alterna con un condensador programable (un DAC multiplicador mueve el pie de 5.6 pF, calibrado a 50 kHz); fuente de ohmios ratiométrica protegida a ±1000 V con un diodo y una escalera de transistores; descargador de gas en serie con varistor ∥ C en HI; dos fusibles (3 A rápido y 7 A de alto poder de corte); autoprueba con recursos internos; integración ligada a la frecuencia de red.
  - Propuestas P38 (autocero con tiempo de asiento o precarga), P39 (corrección de alterna por firmware), P40 (red de 60 Hz en Perú; 100 ms rechaza 50 y 60 Hz), P41 (autoprueba) y P42 (protección de la fuente de ohmios con semiconductores, alternativa a la PTC). Ninguna aplicada.
  - **Para la síntesis:** la fuga garantizada del 74HC4051 (±0.1 µA a 25 °C) son ~1000 cuentas en la toma ÷10; hay que medirla o cambiar de conmutador.
  - Siguiente: la síntesis. Detalle en `journal/2026-10-07-claude-dmm-34401a.md`.
- **7 oct, síntesis del DMM publicada:** `01_diseno/dmm_sintesis.html` (artefacto FzUFdinBfx7Yf3mbvAnsy4).
  - **Criterio de Keneth** (DECISIONS, 7 oct): no caracterizar lo analógico en banco antes de fabricar (la placa WeAct une VDDA/VREF a la alimentación digital). Simular con margen y calibrar por software al fabricar. Especificaciones holgadas pero profesionales, con bajo coste y pocos componentes.
  - **Conclusión:** la arquitectura de H se mantiene. Ocho correcciones: INL de 26–39 cuentas; la PTC de kΩ deja el rango de 200 Ω al 20 % de la ventana (nuevo, se sustituye por P42); el ÷4 de X6; la fuga del 4051; Ib del OPA2188; red de 60 Hz; asiento del autocero; compensación de alterna.
  - **Veredicto P17–P42:** 7 de hardware (céntimos), 11 de firmware, 2 ya en H, 3 opcionales, P17 descartada, P30 sustituida por P42 y P36 por decidir.
  - **Especificación en dos niveles:** sin linealizar, ±(0.1 % + 40) en continua; tras calibrar al fabricar, ±(0.1 % + 10). Huella sin montar de un ADS1115 (C37593, 1.22 USD) como respaldo.
  - **Pendiente de Keneth:** D1–D7 (INL, divisor con tomas, P42, 74HC4051, especificación, opcionales y riel propio). Después, revisión de H y encargo S11. Detalle en `journal/2026-10-07-claude-dmm-sintesis.md`.
- **7 oct, D1–D7 aceptadas y sección H revisada:** Keneth aceptó D1–D7 con un cambio: **sin huella del ADS1115**, solo el ADC5 y la linealización al fabricar (DECISIONS, 7 oct). Revisados y republicados `01_diseno/dmm_rev21.html` (versión 3, 4iveEdvtCBTvhQj9jHjsvY) y `00_requisitos/especificaciones_dmm.html` (versión 3, 9wuyJcNBxPcee2dNuThttm).
  - H aplica P42 (en lugar de la PTC), el fusible cerámico con DF10S y el aviso por X5, C0G fijos con corrección por firmware, el autocero con asiento, 60 Hz/100 ms y la especificación en dos niveles. Añade §10 (firmware y calibración) y §11 (S11 y lo abierto).
  - **Hallazgo nuevo** (`herramientas/calc_dmm_h.py`): en la razón de ohmios, la corriente también se mide con el ADC5, así que la INL entra en % de lectura: 0.62 % típ., 0.94 % máx. y 0.24 % aun linealizada. No cabe en ±(0.2 % + 10).
  - **Propuesta P43 (pendiente, D8):** fuente de corriente ratiométrica a VREF, como el 34401A. TLV2372 (C27204) + NPN + PNP, R_rango de 50 Ω a 2.49 MΩ, 10 mA … 0.2 µA, ≈ 3.4 V en vacío y diodo a 1 mA hasta ≈ 3.3 V. Ganancia de ohmios ≈ 630 ppm. En 20 MΩ se usa 0.2 µA y no 0.1 µA: con 0.1 µA, la curva aplanada por el divisor de 10 MΩ daba 1.5 veces la tolerancia garantizada. Sin ella, la razón con buffer (P25) da ≈ 0.6 %.
  - **Siguiente:** respuesta de Keneth a D8 y después el encargo S11. Detalle en `journal/2026-10-07-claude-revision-seccion-h.md`.
- **7 oct, D8 aceptada y encargo S11a escrito:** Keneth aceptó P43 (DECISIONS, D8). Encargo y plan en `S3G4_LAB_rev2.1/03_simulaciones/DMM/`: `ENCARGO_CODEX_S11a.md` y `PLAN_SIMULACION_S11a.md` (K0–K13, S11-C1…C14). **Sin lanzar.**
  - Al escribir el plan aparecieron riesgos de diseño (`herramientas/calc_dmm_s11.py`). S11 los mide; nada se ha cambiado sin datos:
    - **P42 con la fuente encendida:** con la red en V/Ω y en el rango de 200 Ω (10 mA), ≈ 1.65 W de pico por MMBTA92, el 472 % de un SOT-23 (47 % en 2 kΩ). H decía «nada que se caliente»: corregido. Depende de que P34 apague la fuente a tiempo.
    - **El circuito de la escalera P42 no está definido**, y su caída de ≈ 0.8 V no está justificada con un riel de 4.9 V. Pasa a S11b, después de que Claude lo diseñe. En S11a se modela con un 1N4007 + 0.2 V.
    - **PNP de paso:** su β deja ≈ 1 % fuera de Rx, con ≈ 300 ppm de deriva con ±5 °C. Variante B: 2N7002/BSS84.
    - **Tensión en vacío** de 2 kΩ a 2 MΩ, en el límite del modo común del OPA2188 (V+ − 1.5 V).
    - **Polo de R_PROT con ≈ 40 pF en X0:** −10 % a 20 kHz en 200 mV y 2 V; lo corrige P39.
  - Variantes del driver: TLV2372 | OPA365.
  - **Falta:** que Keneth deje los modelos de TI (OPA2188, TLV2372 y REF3325) y las hojas del §2 del plan; Claude puede bajarlos con su permiso. Después, lanzar Codex. CLI: `…\Codex\bin\5ea220ae823df3d7\codex.exe`, 0.160.1.
  - Detalle en `journal/2026-10-07-claude-encargo-s11a.md`.

## Punto de retomada — referencias del DMM (7 oct 2026, Claude)

- **Retomar con:** `ai-context/journal/2026-10-07-claude-retomar-referencias-dmm.md`. Contiene:
  - el estado: las 9 referencias hechas (TIDA-01012, HydraMeter, TIDA-00879, 121GW, Micro-DMM, Martin, EEWorld 77845, Analog Devices y 34401A);
  - las propuestas P17–P42 resumidas, sin aplicar;
  - los riesgos para la síntesis;
  - el orden siguiente: ~~respuestas a D1–D7~~, ~~revisión de la sección H~~, ~~D8~~ y ~~encargo S11a~~ (hechos el 7 oct) → modelos y hojas de TI → lanzar S11a → circuito de P42 y S11b;
  - las herramientas y las trampas conocidas.
- La sección H del DMM está revisada y P43 aceptada (7 oct). El encargo S11a está escrito y sin lanzar.
- **7 oct, DMM por bloques y opción B:** Keneth decidió avanzar por bloques (bornes y protección → tensión → ohmios → corriente → driver/ADC) y poner un relé (TQ2SA, como el osciloscopio) que conecta la fuente de ohmios solo en Ω/diodo/continuidad (DECISIONS). DF08S en el borne A. S11a aparcado sin lanzar. Hojas y modelos de TI ya en el proyecto (los bajó Keneth). Pendiente de Keneth: cómo se protege la fuente en modo ohmios con la red (10 mA + escalera P42, o 1 mA máx. + PTC de 250 V + TVS); después, plan del bloque 1.
- **7 oct, bloque 1 del DMM:** Keneth eligió B2. La fuente de ohmios da 1 mA como máximo, sin escalera P42. Camino: relé TQ2SA → PTC PTCTL4MR500SBE (35 Ω, 600 V) → TVS SMAJ12CA → R_S → BAV199. Con eso, ≈ 3.7–4.0 V para la prueba de diodo. Encargo `03_simulaciones/DMM/ENCARGO_CODEX_S11_1.md` y plan `PLAN_SIMULACION_S11_1.md` (P0–P7, C1–C7) escritos, **sin lanzar**. Faltan las hojas de la PTC y de la SMAJ12CA. La sección H se actualiza al cerrar el bloque.
- **7 oct, S11.1 terminado (Codex) — bloque 1 NO aprobado, sin auditar aún por Claude.** `03_simulaciones/DMM/ACTA_S11_1.md`.
  - **Borne A:** DF08S con 93–386 A de pico e I²t de 33–604 A²s (red de 2–0.5 Ω), frente a 50 A y 10.4 A²s.
  - **Ohmios con la red:** la PTC dispara a los 34–78 ms; la TVS SMAJ12CA recibe 0.42–0.65 J por semiciclo y hasta ≈ 4.7 J en total, demasiado para una SMA de 400 W.
  - **Rieles:** con el DMM encendido suben hasta 24 V entre ellos (límite 11 V); apagado, ≤ 9.1 V.
  - **Relé:** conmutar 230 Vac supera sus 125 Vac.
  - **Fuga del modelo de la TVS en N1:** inaceptable para 2–20 MΩ (falta un dato garantizado a 4 V).
  - Diodo: ≥ 4.1 V, pasa.
