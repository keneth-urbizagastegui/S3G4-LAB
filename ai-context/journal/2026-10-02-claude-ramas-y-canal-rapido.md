# 2026-10-01/02 — Claude Code: unión de ramas y guía del canal rápido CH1

## Cambios

- **Git (1 oct, pedido de Keneth):** todas las ramas unidas en `main` y subidas a GitHub (`2194561..c52fd3a`).
  - `origin/main` por avance directo; `ai/prueba-konnect` (contenía `rev2.1`), `video-player/fase-6b`, `fase-4` y `fase-5d` sin conflictos.
  - `video-player/fase-5c` (giro en el decodificador, NO CUMPLE): se conservó el código de `main` y entraron sólo sus 16 mediciones; `FASE_5c.md` ya estaba en `main`, idéntico.
  - Borradas las 13 ramas locales con `git branch -d`. Respaldo local: tag `respaldo/main-antes-de-unir` (no subido).
- **Guía de estudio del canal rápido:** `S3G4_LAB_rev2.1/01_diseno/canal_rapido_ch1.html`, anotada en `S3G4_LAB_rev2.1/LEEME.md`.
  - Recorrido de la señal con un ejemplo (±1 V a 500 mV/div → códigos 1229–2867).
  - Qué especificaciones fija el AFE y cuáles el G473; la ecuación de escala G = 0.25 V / (V/div) = grueso × toma × 50.
  - Alias con f_s/BW = 3.25: a 4.5 MHz, un Butterworth de 5.º orden atenúa 35 dB y un Bessel de 5.º orden 18 dB (scipy).
  - Base de tiempos: f_s = min(6.5 M, 8192 / (10 · s/div)).
- **Comparación con el DSO112A y disparo externo (2 oct):** respondida en el chat, sin cambiar documentos. Recomendación: sin BNC de disparo externo; disparo interno desde el AWG y desde cualquiera de los 3 canales. Es una propuesta y no está aceptada.

## Hallazgos

- C_AC = 1.5 nF (B.8) da 10.6 Hz con 10.05 MΩ; RF-05 pide ≤ 10 Hz. Con 1.8 nF da 8.8 Hz. Pendiente de confirmar en la corrección de P4 (PLAN, paso 2).
- La hoja de especificaciones ya decía «Disparo externo: no»; RF-09 sólo nombra CH1–CH3 como fuentes.

## Pendiente de Keneth

- P1 (÷20), P8 (etapa final única a 3.3 V), P13 (HCLK 104 MHz con ADC síncrono) y el tipo de filtro de CH1 (Bessel, Butterworth o simular ambos).
- Disparo externo: aceptar o rechazar la recomendación; disparo interno desde el AWG como fuente nueva de RF-09.

## Pruebas

Ninguna electrónica. Cifras calculadas con Python/scipy; la página se revisó en el navegador del panel.

## Continuación (2 oct, tarde): revisión de la entrada de CH1

- **Decisiones registradas en DECISIONS.md:** disparo sin entrada externa, con el AWG como fuente interna (aceptado); entrada sin la red conectada directamente (Keneth), con las cifras de «seguridad mejor» como propuesta sin aceptar.
- **Revisión** en `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html`: 13 hallazgos (R1–R13), comparación con DSO112, WAVE2, OpenScope y black_scope, y estado de cada requisito.
- **Propuesta P4b:** réplica de la carga de SEL en el segundo polo del relé (R_EQ = R_BIAS, C_EQ ≈ C_SEL). Sustituye a «R_BIAS delante del relé», que dejaba el buffer sin polarización en modo AC.
- **Simulación rápida** (LTspice 26.0.2, ideal): `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/chequeo_claude/p4b_zin.cir`. Resultados: Zin = 999.1 kΩ en ×1 y en ÷100; Cin = 27.65 / 27.73 pF; planitud de −0.26 % / −0.29 % hasta 2 MHz. Con C_SEL desviada ±3 pF, ΔCin llega a ±3 pF, así que hay que conocer C_SEL a ±2 pF o ajustar C_EQ.
- **Correcciones en `canal_rapido_ch1.html`:** el RC de 68 Ω / 470 pF resta −0.65 dB a 2 MHz (total sin filtro −1.0 dB, no −0.37); muestreo de 67 ns (3.5 ciclos), no 48 ns; TVS fuera del nodo; sin la red.
- **Plan S0–S8** en el documento y en `06_plan/PLAN.md`, paso 2.
- **Hallazgos con datos reales:** 74HCT4051 con una sola fuente en LCSC (C87239, 2796 ud) → 74HC4051 C9386, porque lo gobierna un 74HCT595 a 5 V; la hoja del SS23H37 no declara rigidez dieléctrica, así que el acoplo se queda detrás de la sujeción (D-07).
- **Pendiente de Keneth:** P1, cifras de seguridad y quién ejecuta las simulaciones.

## Cierre (2 oct): decisiones y encargo S1

- Keneth eligió las opciones recomendadas: **P1 = ÷100 con 6 tomas**, **±100 V sin daño y ESD ±8 kV aire / ±4 kV contacto**, y **Codex ejecuta las simulaciones** con auditoría de Claude. Registrado en DECISIONS.md.
- Encargo y contrato de la etapa S1 (E1–E4, entrada pasiva P4b): `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/ENCARGO_CODEX_S1.md` y `PLAN_SIMULACION_S1.md`. No se ha lanzado todavía.
- Por reescribir en el documento vivo: tablas C.1, C.3 y C.6 a ÷100 con 6 tomas, y R_S de C.2.

## Comprobación del entorno de Codex (2 oct)

- Codex CLI 0.154.0, sesión de ChatGPT activa, `danger-full-access`. **El modelo por defecto `gpt-6.1-sol` no se admite con cuenta de ChatGPT (error 400)**; con `-m gpt-5.6-sol` todo funciona. Anotado en `ENCARGO_CODEX_S1.md`.
- Probado desde el propio Codex, todo OK: Python 3.12.10 + NumPy 2.4.6 + SciPy 1.17.1; LTspice en lote con `.cir` e include; MCP s3g4-context, pcbparts y ltspice; `kicad-cli` 10.0.6; `pcb-inspector`; `ltspice-mcp`; skills de kicad-happy (kicad, spice, bom, emc, datasheets, distribuidores).
- **Falta en Codex:** Konnect (MCP de KiCad por IPC). En Claude sólo está en `04_esquematicos/kicad/.mcp.json`. No hace falta hasta el esquema (S8).

## Comprobación del entorno de agy (2 oct)

- agy 1.2.15, sesión activa; prueba hecha desde el propio agy con Gemini 3.1 Pro (High).
- **Tiene:** MCP s3g4-context, context-mode, `kicad-cli` 10.0.6, `pcb-inspector`, Python con NumPy/SciPy y LTspice en lote (repitió zin100 = 119.99 dB = 999.1 kΩ del chequeo P4b).
- **Le falta:** MCP ltspice, MCP pcbparts, skills kicad-happy y Konnect. `agy mcp list` dice «No MCP servers configured»: s3g4-context le llega por `.agents/mcp_config.json` del proyecto.
- Modelos de agy: Gemini 3.8/3.7/3.6 Flash (low/medium/high), Gemini 3.1 Pro (low/high), Claude Sonnet 4.6, Claude Opus 4.6 y GPT-OSS 120B. Por defecto: Gemini 3.8 Flash (Medium).
- **Completado el mismo día (Keneth confirmó):** `agy mcp add ltspice ltspice-mcp`, `agy mcp add pcbparts https://pcbparts.dev/mcp` y `agy plugin install` de kicad-happy 2.2.1 desde la caché de Claude. Prueba repetida desde agy: ltspice, pcbparts, s3g4-context y las 11 skills de kicad-happy, todo OK. Konnect sigue sólo en Claude.
- `.ltspice-mcp/` y `ltspice-mcp.toml` en la raíz los creó el MCP de LTspice de Claude durante el chequeo P4b (18:14). Añadidos a `.gitignore`.
- **S1 lanzado (2 oct, noche)** con Codex de la aplicación (0.159.0-alpha, `…\OpenAI\Codex\bin\be3fd7e5c1969ff6\codex.exe`), `gpt-6.1-sol`, esfuerzo `low` (elección de Keneth). El CLI del PATH (0.154.0) es el que rechazaba `gpt-6.1-sol`. Sesión 01a0ff12-386a-7b23-a2be-1160ccfdbc80.
- **Documento vivo (2 oct, noche), a petición de Keneth:** reescritas C.1 (12 escalas con ÷100 y 6 tomas), C.3 (escalera 499/249/150/49.9/24.9/24.9 Ω, más GND y VCHECK) y C.6 (piezas de P4b, 74HC4051, sin TVS en el nodo y con TVS de riel). Revisadas también las filas D-03, D-06, D-07 y D-09. El dibujo de C.3 queda marcado como pendiente de regenerar con `draw_c.py`. Aún dicen ÷20: B.5, B.8, C.2, C.4, C.5, G.6, G.7, A.3, la nota del DSO150 y 6 rótulos dentro de SVG.

## Auditoría de S1 (2 oct, noche)

- Entrega de Codex: código 0, 494 simulaciones, 0 errores ni advertencias. Valores y reglas de §3 correctos. C1–C4 pasan en el nominal: Zin 0.9991 MΩ, ΔCin 0.54 pF, planitud ±0.17 %, corte AC 8.7–8.8 Hz.
- **C5 fallaba por un error del plan (mío):** la sonda 9 MΩ ∥ 10 pF con 80 pF de cable no es compensable frente a 27 pF de entrada. Con sonda compensable y paso de 2 ns: ÷100 +0.11 %, ×1 +0.55 % → cumple. El paso de 200 ns del entregable da un pico falso del 2.8 %.
- E4: Zin y planitud ×1 robustas. Planitud ÷100 fuera de ±1 % en 159/200 (manda la Coff del relé) → hace falta un ajuste por canal; un trimmer de 2–6 pF sobre Ct sólo da ±3.5 %. ΔCin > 2 pF en 47/200 (manda la Cin del buffer) → C_EQ «seleccionado en prueba».
- Reproducido por Claude: CSV idéntico byte a byte.
- Auditoría: `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S1.md`. Siguiente: S1b (E3 corregido, CJ polarizada en C_SEL_EST, trimmer simulado) y decisión de Keneth sobre el trimmer.
- **Decisión de Keneth:** un trimmer por canal para ÷100 y C_EQ seleccionado en prueba (DECISIONS.md, 2 oct). Encargo **S1b** preparado, sin lanzar: `CH1_entrada/PLAN_SIMULACION_S1b.md` y `ENCARGO_CODEX_S1b.md`. Cubre C_SEL_EST con CJ polarizada y las dos COFF_SW, sonda compensable con paso ≤ 2 ns, trimmer de 2–6 / 3–10 / 5–20 pF sobre Ct2 con ajuste simulado, campaña de producción (criterios) y campaña de diseño (informativa, con selección E24 de C_EQ).
- **S1b lanzado (2 oct, noche)** con Codex de la aplicación, `gpt-6.1-sol`, esfuerzo `medium` (Keneth).
- **Documento vivo (2 oct, noche):** reescritas C.2 (P4b: réplica de carga, R_S 2×49.9 k ∥ 1.5 nF, ±100 V, trimmer, C_EQ en prueba; dibujo marcado como pendiente), C.4 (presupuesto con R_PROT, Ron real del 4051 y RC del ADC: CH1 −0.97 dB sin filtro; CH2/CH3 −0.2 dB) y C.5 (ruido con ÷100 y 6 tomas, contando R_PROT y las resistencias de ganancia: 0.25–0.36 % de división en CH2/CH3 y 0.29–0.41 % en CH1). **Aviso:** CH1 a 5 y 500 mV/div supera el 0.35 % de la prueba E12; posibles remedios R_PROT 470 Ω y red de ganancia de 499 Ω, a decidir en S3.
- **Corrección de Keneth:** CH2/CH3 a 1 MHz (no 1.5 MHz). C.4: CH2/CH3 −0.08 dB sin filtro (−0.25 dB con 50 MHz de GBW). C.5: CH2/CH3 0.21–0.29 % de división. Actualizados la sección D pendiente del documento vivo, el PLAN (paso 3) y DECISIONS.
- **Documento vivo (2 oct, noche):** actualizadas B.5 (cadena P4b, sin TVS en el nodo, TVS en los rieles, R_PROT, ±100 V), B.8 (divisor ÷100: 2 × 549 kΩ + 11.0 kΩ, Rt + Rb = 1.11 MΩ, Cb ≈ 1.08 nF con la Coff arriba, trimmer, Cin ≈ 27 pF, C_AC 1.8 nF, BOM de la entrada) y G (G.5 corriente de sujeción de 2.8 mA con 100 V; G.6 relé a ÷100 y condición de seguridad con descarga activa del riel, ~45 µA con el canal apagado; G.7 ±100 V sin la red). La fila D-05 pasa a ÷100 y 12 escalas. Los ÷20 que quedan son menciones históricas.
- **Dibujos de C.2 y C.3 regenerados** con `herramientas/draw_c.py` (copia anterior en el scratchpad de la sesión). C.2: entrada P4b (divisor ÷100 con C_TRIM, rama ×1 2 × 49.9 k ∥ 1.5 nF, K101A/K101B con réplica R_EQ ∥ C_EQ, BAV199 a los rieles). C.3: escalera de 6 tomas, X6 a masa, X7 VCHECK y 74HC4051. `chk_c.py`: 0 solapes en los dos. Insertados en el documento vivo, con la cabecera actualizada a 2 oct.
- **S1b cortado (20:42)** por el límite de una hora de las tareas en segundo plano de Claude Code, después de pasar la prueba de humo (2 casos por campaña; los 9 criterios pasan en esa muestra, que no es concluyente). **Reanudada la misma sesión** (`codex exec resume 01a0ff52-374c-76b0-a7e6-3795bc2eecff`) como proceso independiente (PID 17640), para las campañas completas. Salida en el scratchpad: `codex_s1b_resume.err/.log` y `codex_s1b_final.txt`.
- **S1b (21:50):** parada la ejecución secuencial (caso 36/200, ~1 caso/min, ~5–6 h) por decisión de Keneth; reanudada la sesión (PID 4108) con la orden de paralelizar `ejecutar_s1b.py` (10 trabajos), comprobar con --smoke que el CSV no cambia y relanzar las campañas completas.
- **S1b terminado por Codex (22:45):** A 200 casos × 3 rangos, B 200 casos; código 0; 9375 simulaciones sin errores ni advertencias; 34 min con 10 trabajadores; los nueve criterios pasan. El trimmer de 2–6 pF basta, pero usa 2.55–5.95 pF (0.05 pF de margen arriba) y en la campaña B toca tope en 29/200.
- **El PC se reinició a las 23:36** (3 oct, madrugada): se perdieron la sesión de Claude, los vigilantes y la reejecución independiente de S1b, que iba por la campaña B. Los entregables de Codex están intactos (22:42–22:45). Relanzada la reejecución (PID 4612). **El CLI de Codex de la aplicación se actualizó a 0.160.0** y cambió de carpeta (`…\OpenAI\Codex\bin\8aaf1547b825b104\codex.exe`); la ruta antigua de los encargos ya no existe.
- **Auditoría de S1b (3 oct):** reproducido por Claude tras el reinicio: los 14 CSV son idénticos byte a byte. Los nueve criterios pasan. El trimmer R1 de 2–6 pF (SEHWA C22468120, 4501 ud) cumple en producción por sólo 0.05 pF de margen y toca tope en 29/200 casos de diseño. Propuesta: R1 con **Cb seleccionado en prueba** para centrarlo; R2 (3–10 pF) sólo tiene 16 ud en LCSC. `AUDITORIA_CLAUDE_S1b.md`. Corregida la ruta del CLI de Codex en los encargos.
- **3 oct:** Keneth acepta el trimmer SEHWA 2–6 pF (C22468120) con Cb seleccionado en prueba (DECISIONS.md). Candidatos de buffer FET en LCSC: OPA810 (C2833513, 70 MHz, 2 pA, 6.3 nV/√Hz, 3.7 mA, 3287 ud, 3.08 USD, SOT-23-5); AD8065 (C9648, 145 MHz, 6 pA, 7 nV/√Hz, 6.6 mA, 4953 ud, 5.60 USD, misma patilla SOT-23-5); ADA4817-1 (C207502, 410 MHz, 14 mA, 9.87 USD); OPA1656 (C1849431, 53 MHz, 24 V/µs, 1.44 USD). Ningún equivalente chino con ≥ 50 MHz y pA entre los de más stock. La Cin de cada uno queda por confirmar en su hoja.
- **3 oct:** decidido OPA810 como buffer con AD8065 de segunda fuente (DECISIONS.md). Keneth descargó los modelos (OPA810 de TI, AD8065 de ADI, BAV199 de Nexperia) y las hojas. Comprobados en LTspice (`chequeo_claude/modelos_s2.cir`): seguidores a −3 dB en 122/138 MHz, planos a 2 MHz; BAV199 real con CJ(5 V) = 1.08 pF frente a 0.77 pF del genérico (+0.6 pF en C_SEL; C_EQ en prueba lo absorbe). Trampas anotadas en `Simulation_LTSpice/models/LEEME.md`: orden de pines del OPA810 y `.ENDS` suelto en BAV199.txt. Cin del OPA810: 2–2.5 pF de modo común.
- **Encargo S2 preparado (3 oct), sin lanzar:** `CH1_entrada/PLAN_SIMULACION_S2.md` y `ENCARGO_CODEX_S2.md`. Pruebas: E0 con modelos reales; E5 ±100/±50 V y seno de 100 Vpk; E6 canal apagado con tres variantes de descarga; E7 ESD de ±4/±8 kV; E8 recuperación; E9 fugas a 25/85 °C; E10 sonda ±400 V; y la segunda fuente con AD8065. El riel se modela sin capacidad de absorber corriente, con una TVS tipo SMAJ6.0A. Ocho criterios. Aviso: C_S de 100 V puede ver ~95 V con 100 V en ×1.
- **S2 lanzado (3 oct)** con Codex 0.160.0 (`…\8aaf1547b825b104\codex.exe`), `gpt-6.1-sol`, esfuerzo medium, como proceso independiente (PID 11976). Salida: `codex_s2.err` y `codex_s2_final.txt` en el scratchpad.
- **Auditoría de S2 (3 oct):** reproducido byte a byte (12 CSV). Mis dos primeros intentos fallaron por mi entorno: estructura de carpetas para los modelos y MAX_PATH en el scratchpad. De los fallos con OPA810: **C2 real** (R_EQ ve 99 V en ÷100 y C_S 94 V → R_EQ 1206, C_EQ y C_S ≥ 200 V); **C1 por mi plan** (CIN_BUF contada dos veces con el modelo real); **C3/C6 por la métrica de ESD** (pico frente a 4 A de 1 µs; con I²t, 4 kV en contacto tiene 4.4× de margen y 8 kV en contacto queda al límite; la red ESD de S2 no tiene inductancia, flanco de 0.3 ps). **El AD8065 no es segunda fuente directa:** 3.1 V diferenciales en E5 frente a 1.8 V de máximo. E8: recuperación de ~1 ms, inherente a τ = R_BIAS·C_X1. `AUDITORIA_CLAUDE_S2.md`.
- **3 oct:** Keneth acepta R_EQ en 1206, C_EQ y C_S ≥ 200 V, descartar el AD8065 y preparar S2b (DECISIONS.md). **Segunda fuente:** en LCSC sólo hay FET de ±5 V y ≥ 45 MHz de TI y ADI. Los CMOS de 100 MHz (OPA354, COS8052) son de 5.5 V como máximo. Candidatos por verificar en hoja (diferencial y Cin): **OPA828** (C1850247, JFET, 45 MHz, 1 pA, 4 nV/√Hz, 150 V/µs, 5.5 mA, ±4–18 V, 5191 ud, SOIC-8) y **OPA1656** (C1849431, doble, 53 MHz, 24 V/µs, 3.9 mA, 8456 ud, 1.44 USD). OPA2810 es el mismo dado del OPA810. **S2b preparado, sin lanzar:** `CH1_entrada/PLAN_SIMULACION_S2b.md` y `ENCARGO_CODEX_S2b.md` (generador IEC verificado sobre 2 Ω, métrica I²t, CIN_BUF = 0, límites de 200 V, ruta de modelos configurable).
- **3 oct:** Keneth descargó el modelo y la hoja del **OPA828** (`Simulation_LTSpice/models/OPA828/OPAx828.LIB`, `.SUBCKT OPAx828 IN+ IN- VCC VEE OUT`). Su hoja da una diferencial máxima igual a toda la alimentación (sin diodos entre entradas), así que no tiene el problema del AD8065. **S2b lanzado** con Codex 0.160.0, `gpt-6.1-sol`, medium, como proceso independiente (PID 5284).
- **Auditoría de S2b (3 oct):** reproducido byte a byte (14 CSV) con `S3G4_MODELS` desde otra ruta. Generador ESD verificado sobre 2 Ω en los cuatro puntos IEC a 4 y 8 kV. **I²t de los BAV199 con OPA810:** 3.41 µA²s a ±4 kV en contacto y 6.97 µA²s a +8 kV en aire (criterio 8, rating 16) → **el nivel acordado se cumple sin protección extra**; 8 kV en contacto da 13.7 (no exigido). **C3 pasa con el criterio correcto** (corriente por los diodos ESD ≤ 10 mA según las dos hojas; mi plan pedía tensión); en ESD llegan 5.7–6.2 mA. ΔCin 0.39 pF. R_EQ en 1206 queda al 99 % de su límite reducido. **OPA828:** eléctricamente válido, pero Cin del canal 31 pF (> 30 pF de RF-08) y error de ganancia 0.54 % → opciones: Ct de 2 × 12 pF para ambos, variante de piezas, u OPA810 como fuente única. `AUDITORIA_CLAUDE_S2b.md`.
- **3 oct:** actualizados los esbozos de `canal_rapido_ch1.html` (cadena con ÷100, etapas S1–S6 marcadas sobre los bloques, ejemplo a 500 mV/div con toma 1/1, tabla de 12 escalas, plan S0–S8 con su estado) y de `revision_entrada_ch1.html` (C_TRIM, R_EQ 1206, C_EQ/C_S 200 V, OPA810, recuadro de estado S1–S2b).
