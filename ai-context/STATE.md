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
- **D-06 acordado el 23 sep:** osciloscopio a 50 Vpk declarados, supervivencia a 250 Vrms en el rango ÷20 (estado de arranque) y protección de red de 600 V en el puerto del DMM.
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
  - DMM: tres bornes como el ELVIS II, 4½ dígitos con el ADC5 sobremuestreado, CAT II 600 V sin aislamiento pero con enclavamiento, 2 A, alterna de 40 Hz a 20 kHz y prueba de diodo de 3.5 V.
  - AWG: dos canales, 1 MHz por DDS, ±5 V en dos rangos, 50 Ω protegido hasta ±15 V y arbitraria de 4096 puntos.
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

