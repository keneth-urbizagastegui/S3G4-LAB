# Plan de la rev 2.1 — lo que haremos

Estado a 30 sep 2026. El estado compartido y oficial está en `ai-context/STATE.md`; esta lista lo ordena para trabajar.

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
2. **Corregir P4 para RF-08:**
   - R_BIAS delante del relé.
   - Rt + Rb para que el paralelo dé 1 MΩ.
   - Capacidad igualada con el segundo polo del relé (pasa a DPDT).
   - Resistencia serie antes del buffer.
   - Sujeción segura con el canal apagado.

   Luego, un nuevo encargo de simulación con T07 completo.
3. **Sección D, filtro anti-alias:** CH1 a 2 MHz, de orden alto (RF-03, Nyquist 3.25 MHz); CH2 y CH3 ≥ 1 MHz con techo de 1.5 MHz (Nyquist 1.73 MHz). En CH1, amplificadores de GBW ≥ 100 MHz (C.4).
4. **Sección E, offset:** ±5 divisiones (RF-14), con PWM o DAC en sample-and-hold (P6, P15).
5. **Sección F:** driver del ADC con R_AIN ≤ 100 Ω, REF3325 (P9) y reloj del ADC (P13).
6. **DMM:**
   - 50 V en continua y 50 Vrms en alterna (como el TIDA-01012), 2 A, 4½ dígitos y tres bornes: V/Ω, COM y A.
   - Entrada V/Ω y su protección para 71 Vpk continuos; aviso de tensión peligrosa en el panel y el manual.
   - Prueba de diodo de 3.5 V, con divisor antes de PB14.
   - Protección frente a errores (RD-10).
7. **AWG:** etapa de salida de ±5 V con 50 mA y límite de corriente, filtro de reconstrucción de 2 MHz y protección de ±15 V con la sujeción a masa.
8. **Mapa de pines para 3 canales (D-02),** con disparo de CH2 y CH3 por watchdog (P11, P12).
9. **Esquemas de la rev 2.1** en `04_esquematicos/kicad/` (KiCad 10, rama `ai/*`):
   - Antes de dibujar: stackup de 4 capas, contorno de la placa y clases de red del AFE con sus reglas DRC (las escribe Keneth en `s3g4.kicad_dru`).
   - Jerarquía de hojas. Lo que ya está cerrado (entrada A/B y la parte digital: G473, ESP32-S3, TFT, USB) puede dibujarse antes de que terminen los pasos 1–8.
   - Konnect sólo aparece en sesiones de Claude abiertas en `04_esquematicos/kicad/`.
   - Más adelante: remoto en GitHub con KiBot.

## Decisiones abiertas (de Keneth)

- ¿Sigue el tope RE-01 de 120 USD?
- ¿Grueso ÷20 o ÷100 (P1)?
- P8 (etapa final única) y P13 (CPU a 104 MHz con el ADC síncrono). G.3 ya cuenta con P8.
- ¿Cuánto debe aguantar el DMM si se conecta a la red por error (RD-10)?
- RG-07: el AWG como fuente de continua a través de 50 Ω (se decide con los rieles del AWG).
- ¿Interruptor de carga propio para el DMM (RF-18)?
- Propuestas P1–P16: todas siguen sin aplicar salvo lo que recogen D-xx, RF, RD y RG.
