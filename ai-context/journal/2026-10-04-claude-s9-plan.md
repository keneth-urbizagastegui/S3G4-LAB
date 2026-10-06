# 2026-10-04 — Claude Code: plan de S9 (CH2/CH3 a 1 MHz) con el LM6172 como variante

## Cambio

- Propuesta de S9 a Keneth: CH2/CH3 iguales a CH1 salvo el filtro (1 MHz) y el muestreo (un ADC, 3.47 MSa/s, 2.5 ciclos = 48.1 ns). Alias de la banda en 2.47 MHz.
- Revisión de precios (pcbparts, LCSC a 10 uds): OPA810 2.61, AD8039 4.07, OPA836 1.90 USD; ≈ 12.7 USD de amplificadores por canal. Los dobles baratos de 5.5 V no sirven con ±4.9 V y la regla del 80 %. Candidatos para U103/U105: LM6172 (2.09 USD, 12 nV/√Hz), OPA2810 (3.01 USD), LMH6643 (1.08 USD, 17 nV/√Hz).
- Keneth: «quiero seguir tu recomendacion y probar el lm6172». Registrado en DECISIONS (4 oct) como variante a evaluar, no adoptada.
- **Corrección propia:** en el chat dije «LM6172, 100 MHz». A ±5 V da 70 MHz (descartado para CH1 el 3 oct por eso). Para CH2/CH3 basta (≥ 50 MHz). Anotado en el plan y en DECISIONS.
- Escritos `S3G4_LAB_rev2.1/03_simulaciones/CH23_entrada/PLAN_SIMULACION_S9.md` y `ENCARGO_CODEX_S9.md` (K0–K8, criterios S9-C1…C9, A | B lado a lado, `--resume`, `.op` con tiempo límite).

## Evidencia y pruebas

Ninguna simulación. Precios de pcbparts el 4 oct. Estimación de ruido del LM6172 a 1 MHz ≈ 0.35 % de división (escalado del cálculo del 3 oct).

## Pendientes

- Conseguir el modelo PSpice de TI del LM6172 (`Simulation_LTSpice/models/LM6172/`) y su hoja (`datasheet - componentes/`). No están en el proyecto ni en la biblioteca de LTspice.
- Lanzar Codex con el encargo y auditar.
- Disparo de CH2/CH3 (PE9/PE15): fuera de S9, al mapa de pines.

## Más tarde (misma sesión)

- Modelo PSpice y hoja del LM6172 descargados por Keneth (`Simulation_LTSpice/models/LM6172/lm6172.lib`, macromodelo antiguo de National; `datasheet - componentes/lm6172.pdf`). **Codex S9 lanzado a las 09:30** (gpt-6.1-sol, medium; registro en el scratchpad de la sesión).
- Consulta de Keneth: ¿hay algo más barato que la AD8039 en CH1 sin romper lo validado? Respuesta: no. La única que se acerca es la ADA4851-2 (C141960, 3.34 USD frente a 4.64 USD), con ruido en el límite, Ib de 4 µA y otro encapsulado. CH1 no cambia.
- **S8 preparado** (Keneth: hoja plana, sin jerarquía; la jerarquía estilo OpenScope al final; dibujo con Konnect en otra sesión; solo la cadena de CH1). Paquete en `S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/`: `CH1_PIEZAS_Y_REDES.md` (piezas, pines y redes desde DECISIONS, `ch1_comun_s7b.inc` y el documento vivo) y `ENCARGO_KONNECT_S8.md`. Pinouts verificados contra la hoja: OPA810, OPA836 (PD alto = encendido), AD8039, 74HC4051 y BAV199. Sin hoja: HFD27/005-S, BAV99 y SS23H37L6 (está C883267.pdf, sin revisar).
- Contradicción anotada: S7/S7b simularon VCHECK con 1 kΩ a masa, no con el divisor 12.4 k / 100 Ω del documento.
- Abiertos para el esquema: driver y economizador del relé, cuerpo del BNC (AGND o chasis), tensión de C_AC, desacoplo y pull-ups del polo B (propuestas sin acordar).
- Keneth decide: cuerpo del BNC a AGND; acepta desacoplo (C116–C126) y pull-ups (R133, R134). Paquete de S8 actualizado y registrado en DECISIONS (4 oct).
- Keneth elige: economizador de dos tensiones (RELAY_COM, arranque a 5 V y mantenimiento a ~3.0 V desde 3.3 V; Q101 2N7002, D104 1N4148W, R135/R136), C_AC 1.8 nF C0G 50 V y el 74HC165 en el STM32. Paquete de S8 y DECISIONS actualizados. Pendiente: hoja del HFD27 (mantenimiento a 3.0 V, pinout).
- Evaluadas las hojas del HFD27 (C23911) y del TQ2 (C46047): el HFD27 pide un mantenimiento ≥ 60 % (p. 22, nota 4) y el economizador le da 56 %. Keneth elige el TQ2SA-5V-Z (C22686, SMD). Paquete de S8 y DECISIONS actualizados. Pendiente: lista de piezas del documento vivo (aún dice HFD27) y la huella SA (p. 11).
- Documento vivo v17 publicado (TQ2SA-5V-Z en D-03, C.2, C.6, C.7 y BOM). BOM de CH1 con precios: S3G4_LAB_rev2.1/04_esquematicos/S8_CH1/bom_ch1.py → CH1_BOM_precios.csv: 75 piezas montadas, ≈ 19.4 USD por canal a precio de 1 unidad de LCSC; amplificadores 75 %; 18 referencias extendidas conocidas. Corrección: el recuento de 61 piezas dado antes en el chat estaba mal; son 75.
- Códigos LCSC asignados a todos los pasivos (bom_ch1.py, 55 líneas): 19.6 USD por canal, 30 referencias extendidas (≈ 90 USD de cargo por pedido en JLCPCB). Hallazgo: 1.11 kΩ (R123/R124, filtro de CH1) no es E96 y no hay stock ni al 0.1 %; propuesto 1.10 kΩ (C22764), pendiente de Keneth. Pull-ups y resistencias de puerta pasan de 0402 a 0603.
- Keneth aprueba las 7 parejas serie/paralelo (DECISIONS 4 oct): CH1 con 88 piezas, 24 referencias extendidas y 19.6 USD por canal; 1.11 kΩ = 1.1 kΩ + 10 Ω. Paquete de S8 (§2.10, R101…R149) y bom_ch1.py actualizados; comprobado que R101–R149 aparecen una vez cada una.

## Revisión de coherencia de documentos (4 oct, noche)

Pedido de Keneth: actualizar el documento vivo con las parejas y revisar todos los documentos.
- **Documento vivo (v18):** D-09 cerrada (P1); A.3 y preguntas de A resueltas; avisos de valores históricos en los dibujos de B.7, C.2 y C.3; B.8 al día (códigos, C1A/C1B, C_AC 0603, R_BIAS 0603, D101); C_S 1.2 nF en C.2; parejas en C.3, C.6, D y E; C.7 (buffer resuelto); S9 en curso en D y F; G.1 y G.3 con el TQ2; P8 adoptada; rieles ±4.9 V; sección Σ rehecha (lista de CH1 por bloques y resumen de coste).
- **canal_rapido_ch1.html:** 32 correcciones (12 escalas hasta 20 V/div, ÷100, ruido de S7b, OPA810, red de ganancia real, etapa final inversora con OPA836, filtro elegido, TQ2, estado S1–S7c auditado, S8 preparado, decisiones resueltas).
- **revision_entrada_ch1.html:** aviso de documento histórico con lo que cambió después.
- **Requisitos (v5):** `build_requisitos.py` corregido (antes reproducía la página idéntica): RF-04, RF-06, consecuencias de RF-03/06/08/14/15, energía, verificación y abiertos.
- **Especificaciones (v2):** 21 cambios y tabla de escalas recalculada con ÷100 y 6 tomas.
- **PLAN.md, LEEME.md (raíz, simulaciones, esquemas, informes), ARTEFACTOS.md, SOURCES.md, index.json** (añadidas tres HTML) y dos notas en el resumen inicial de DECISIONS (escalas y D-09).
- Pendiente detectado: D-07 sigue sin aceptación registrada; la tabla de consumo G.3/G.4 sigue sin rehacer.
- S9: la puerta K0 de Codex detuvo la variante B (modelo National ≈ 150 MHz frente a 70 MHz de la hoja a ±5 V). Keneth: seguir la hoja. Escrito ENCARGO_CODEX_S9_B.md (copia ajustada lm6172_hoja.lib, K0 repetido y campaña B); se lanza cuando Codex acabe A. A hasta las 11:06: K1, K3 y K4 completos; Monte Carlo en frecuencia, 2000/2000 dentro (sin auditar).
- SW101 verificado con el plano C883267 (común a 6 mm; T1/T2/T3 a 0/10/14 mm); Keneth: orden AC – GND – DC (DECISIONS). Tabla de pines añadida a CH1_PIEZAS_Y_REDES §2.3. S8 listo para Konnect; quedan sin hoja el 2N7002 y el BAV99 (pinouts habituales).
- 15:35: la campaña A de S9 terminó a las 12:48 (acta y resultados escritos), pero Codex se colgó antes de su respuesta final; Claude lo cerró (PID 10392). Resultado A (sin auditar): C1–C7 y C9 pasan (C9 96.8–97.6 %); C8 falla: recuperación de 1.33–1.41 µs frente a 1 µs, criterio copiado de CH1 sin escalar (a 1 MHz cabe esperar el doble que los 0.71 µs de CH1); pendiente de Keneth. El código 1 de la campaña vino de ediciones de Claude en STATE/DECISIONS. Lanzado Codex S9-B (PID 15260) con ENCARGO_CODEX_S9_B.md.
- Auditoría de S8 (sesión de Konnect, rama ai/s8-ch1-esquema): netlist reproducida idéntica, ERC con las mismas 12 violaciones (todas por hojas que faltan), comprobación pin a pin propia de CI, relé, conmutador, diodos y parejas: correcta. kicad-happy: 5 errores y 8 avisos, todos por rieles y líneas de control sin hoja. Corregidas en la fuente C125/C126 (25 V) y C107 (8.2 pF de partida). Queda: valor de C125/C126 en la hoja, DNP de C103, símbolos y huellas propios, legibilidad (todo por etiquetas). AUDITORIA_CLAUDE_S8.md.
- S8 (cont.): pinouts de 2N7002, BAV99 y 1N4148W verificados con C8545/C2500/C81598. Símbolos (TQ2SA-5V-Z, SS23H37L6) y huellas (relé SMD, conmutador, BNC, trimmer) generados con lib/gen/gen_ch1_parts.py a partir de los planos y de las huellas EasyEDA (trimmer sin plano: rotor NO VERIFICADO). Keneth guardó C103 DNP y C125/C126 a 25 V; verificar_s8 = 0. Commits 487b0d0 y encargo ENCARGO_KONNECT_S8b.md para redibujar con cables (pedido de Keneth); unir con main después.
- Hoja SEHWA (C22468120): huella del trimmer rehecha con su land pattern (1.40 x 1.30, centros a ±1.95, cuerpo 3.2 x 4.5); la hoja no identifica el rotor. Criterio S9-C8 de CH2/CH3: ≤ 2 µs (DECISIONS). Commit de la librería; S8b listo para lanzar.
- 20:38: S9-B se cortó a las 18:28 por pérdida de red (sin informe). Hecho de B (sin auditar): C1–C3 2000/2000 (0.94–1.10 MHz, ≥ 24.2 dB), C4 0.27–0.30 %, C5 pasa; C9 53–57 % por doble contabilización del offset (modelo +2.986 mV + MC ±3 mV). Relanzado Codex (PID 11660) con --resume y la corrección del offset (total ±3 mV) para las cohortes OP de B, además de lo pendiente (5 V/div, K6, K2, K8, acta).
