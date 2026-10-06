# Plan de la rev 2.1 — lo que haremos

Estado a 4 oct 2026. El estado compartido y oficial está en `ai-context/STATE.md`; esta lista lo ordena para trabajar.

## Hecho

- Anatomías de cinco referencias (DSO112, WAVE2, OpenScope MZ, black_scope) y revisión analógica del G473.
- Requisitos funcionales:
  - Osciloscopio: RF-01…RF-19.
  - DMM: RD-01…RD-10. Sólo baja tensión, sin medir la red: 50 V en continua y 50 Vrms en alterna, como el TIDA-01012 (30 sep).
  - AWG: RG-01…RG-08. RG-02 revisado el 30 sep: seno a 1 MHz y el resto de formas hasta 100–200 kHz.
- Simulación P4/P7 construida por Codex y auditada. Por RF-07, el grueso es P4, con relé.
- Sección G (rieles): arquitectura y presupuesto. Con 5000 mAh, 6.0 h en el peor caso.
- Entorno KiCad 10.0.6 + IA montado y probado; proyecto `s3g4` vacío en `04_esquematicos/kicad/` (30 sep).
- **Revisión de coherencia (30 sep)** del osciloscopio, el DMM, el AWG y los rieles, en el documento vivo, los requisitos y la memoria compartida. Hoja de especificaciones preliminar del osciloscopio: `00_requisitos/especificaciones_osciloscopio.html`.

## Siguiente, en este orden

1. **Rieles (sección G.8):** elegir en LCSC (RF-19):
   - un cargador que no deje subir VSYS de ~4.4 V;
   - el boost de 5.3 V y el buck de 3.3 V;
   - el convertidor de ±6.5 V del AWG;
   - el driver de la retroiluminación y los interruptores de carga;
   - con el convertidor del AWG, decidir RG-07 (fuente de continua frente a la salida de 50 Ω) y dónde va la sujeción de su salida: con ±15 V externos, sus rieles de ±6.5 V no pueden absorber 312 mA (G.5);
   - un interruptor de carga para el DMM, o aceptar que no se apaga aparte del AFE (RF-18, G.6).
2. **Entrada de CH1 (P4b) y plan de simulación por etapas** — revisión del 2 oct en `01_diseno/revision_entrada_ch1.html`:
   - 13 hallazgos (R1–R13). Los graves: P1 sin decidir y documentos con ÷20 frente a la simulación con ÷100; RF-08 (0.909 MΩ y 8 pF de diferencia); la corrección «R_BIAS delante del relé» rompía el modo AC; C_AC de 1.5 nF da 10.6 Hz; TVS con fuga en el nodo sujetado; entrada del buffer por encima de su máximo.
   - Propuesta **P4b**: réplica de la carga de SEL (R_EQ ∥ C_EQ) en el segundo polo del relé, Rt + Rb = 1.11 MΩ, R_S = 2 × 49.9 kΩ ∥ 1.5 nF, C_AC 1.8 nF, R_PROT 1 kΩ, BAV199 a los rieles con la TVS en el riel. Comprobación rápida: 999.1 kΩ y 27.7 pF en las dos posiciones (`03_simulaciones/CH1_entrada/chequeo_claude/`).
   - Plan S0–S8: preparación, entrada pasiva (E1–E4), protección y abusos (E5–E10), ganancia (E11–E15), etapa final (E16), filtro (E17), ADC (E18), canal completo (E19) y paso al esquema.
   - Acordado el 2 oct: P1 = ÷100 con 6 tomas; ±100 V sin daño y ESD ±8/±4 kV; simula Codex y audita Claude. Encargo de S1 en `03_simulaciones/CH1_entrada/ENCARGO_CODEX_S1.md`.
   - S1 hecho y auditado el 2 oct (`AUDITORIA_CLAUDE_S1.md`): C1–C5 cumplen en el nominal. Acordado: un trimmer por canal para ÷100 y C_EQ seleccionado en prueba. S1b hecho y auditado el 3 oct (`AUDITORIA_CLAUDE_S1b.md`): trimmer SEHWA 2–6 pF con Cb seleccionado en prueba; buffer OPA810 con AD8065 de segunda fuente. S2 y S2b hechos y auditados el 3 oct: con OPA810 la entrada cumple RF-05/07/08 y el nivel de seguridad (±100 V; ESD ±4 kV contacto / ±8 kV aire con BAV199); R_EQ 1206, C_EQ y C_S ≥ 200 V; OPA810 fuente única y OPA828 alternativa documentada. S3–S7c hechos y auditados el 3–4 oct (`03_simulaciones/CH1_entrada/AUDITORIA_CLAUDE_S3*.md` … `AUDITORIA_CLAUDE_S7b.md`, `ACTA_S7c.md`; revisión completa en `REVISION_CLAUDE_CH1.md`):
     - U103 = AD8039 con redes de 249 Ω y 470 Ω + BAV99 en las dos etapas;
     - filtro U105 = AD8039 doble, intermedio reescalado;
     - etapa final OPA836 a 3.3 V con offset por DAC;
     - rieles del AFE a ±4.9 V; C_S 1.2 nF; Ct ±2 % y Cb 1 nF ±1 % + 68 pF.
     **CH1 cerrado en simulación:** 2.0 MHz, 21.7 dB a 4.5 MHz y ruido de 0.3 %, en ≥ 95 % de las placas con tolerancias reales (criterio de Keneth).
   - **S8 preparado (4 oct):** hoja plana de CH1 en `04_esquematicos/S8_CH1/` (`CH1_PIEZAS_Y_REDES.md`, `ENCARGO_KONNECT_S8.md`, `bom_ch1.py`). Se dibuja con Konnect desde una sesión abierta en `04_esquematicos/kicad/`, en la rama `ai/s8-ch1-esquema`. Decisiones del 4 oct para el esquema: cuerpo del BNC a AGND; desacoplo y pull-ups; relé **TQ2SA-5V-Z** con economizador de dos tensiones (2N7002 + 1N4148W por canal, `RELAY_COM` y `RELAY_KICK` comunes); C_AC de 50 V; 74HC165 en el STM32; valores E96 con parejas serie/paralelo de piezas basic. CH1 sale en ≈ 19.6 USD por canal (88 piezas, 24 referencias extendidas).
   - **S9 en curso (4 oct):** CH2/CH3 a 1 MHz con la AD8039 y el LM6172 como variante (`03_simulaciones/CH23_entrada/`); lo ejecuta Codex y lo audita Claude.
3. **Sección D, filtro anti-alias** (*CH1 hecho el 4 oct; CH2/CH3 en S9, en curso*): CH1 a 2 MHz, de orden alto (RF-03, Nyquist 3.25 MHz); CH2 y CH3 ≈ 1 MHz a −3 dB (Nyquist 1.73 MHz; Keneth, 2 oct). En CH1, amplificadores de GBW ≥ 100 MHz (C.4).
4. **Sección E, offset** (*hecho el 4 oct: DAC del G473 con buffer y OPA836*): ±5 divisiones (RF-14), con PWM o DAC en sample-and-hold (P6, P15).
5. **Sección F:** driver del ADC con R_AIN ≤ 100 Ω, REF3325 (P9) y reloj del ADC (P13). *CH1 hecho (S6): 68 Ω + 470 pF; CH2/CH3 con 2.5 ciclos de muestreo en S9.*
6. **DMM:**
   - 50 V en continua y 50 Vrms en alterna (como el TIDA-01012), 2 A, 4½ dígitos y tres bornes: V/Ω, COM y A.
   - Entrada V/Ω y su protección para 71 Vpk continuos; aviso de tensión peligrosa en el panel y el manual.
   - Prueba de diodo de 3.5 V, con divisor antes de PB14.
   - Protección frente a errores (RD-10).
7. **AWG:** etapa de salida de ±5 V con 50 mA y límite de corriente, filtro de reconstrucción de 2 MHz y protección de ±15 V con la sujeción a masa.
8. **Mapa de pines para 3 canales (D-02),** con disparo de CH2 y CH3 por watchdog (P11, P12): PE9/PE15 no llegan a ningún comparador. Reservar PA4–PA6 para el offset (DAC). El bus de control del AFE (74HCT595 × 2 con 13 líneas, incluida `RELAY_KICK`, y el 74HC165 del acoplo) cuelga del STM32: SCK, dato, latch, dato de vuelta y carga.
9. **Esquemas de la rev 2.1** en `04_esquematicos/kicad/` (KiCad 10, rama `ai/*`):
   - Antes de dibujar: stackup de 4 capas, contorno de la placa y clases de red del AFE con sus reglas DRC (las escribe Keneth en `s3g4.kicad_dru`).
   - Primero, hojas planas por bloque (Keneth, 4 oct: CH1 en S8); la jerarquía, al estilo del OpenScope, se arma al final. Lo que ya está cerrado (CH1 y la parte digital: G473, ESP32-S3, TFT, USB) puede dibujarse antes de que terminen los pasos 1–8.
   - Konnect sólo aparece en sesiones de Claude abiertas en `04_esquematicos/kicad/`.
   - Más adelante: remoto en GitHub con KiBot.

## Decisiones abiertas (de Keneth)

- ¿Sigue el tope RE-01 de 120 USD?
- P13 (CPU a 104 MHz con el ADC síncrono). *P8 se adoptó el 3 oct.*
- D-07 (orden de la cadena) sigue marcada como propuesta en el documento vivo, aunque todas las simulaciones de CH1 la usan.
- CH2/CH3: AD8039 o LM6172 en U103/U105 (se decide con el acta de S9).
- TVS de riel y circuito común del economizador (P-MOSFET de arranque y Schottky): por elegir.
- ¿Cuánto debe aguantar el DMM si se conecta a la red por error (RD-10)?
- RG-07: el AWG como fuente de continua a través de 50 Ω (se decide con los rieles del AWG).
- ¿Interruptor de carga propio para el DMM (RF-18)?
- Propuestas P1–P16: todas siguen sin aplicar salvo lo que recogen D-xx, RF, RD y RG.
