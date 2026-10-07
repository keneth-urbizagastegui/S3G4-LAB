# Plan de la rev 2.1 — lo que haremos

Estado a 6 oct 2026. El estado compartido y oficial está en `ai-context/STATE.md`; esta lista lo ordena para trabajar.

**Criterio de Keneth (6 oct):** que funcione con componentes baratos y con los circuitos reducidos al mínimo. La rev 2.1 ya recorta piezas frente a la rev 2.0. El tope de 120 USD (RE-01) queda en espera: se revisa cuando estén todos los bloques.

## Hecho

- Anatomías de cinco referencias (DSO112, WAVE2, OpenScope MZ, black_scope) y revisión analógica del G473.
- Requisitos funcionales:
  - osciloscopio, RF-01…RF-19;
  - DMM, RD-01…RD-10: sólo baja tensión, 50 V en continua y 50 Vrms en alterna, como el TIDA-01012;
  - AWG, RG-01…RG-08.
- Simulación P4/P7 (grueso con relé, P4) y revisión de coherencia del 30 sep.
- **Osciloscopio, los tres canales cerrados en simulación** (secciones A–F del documento vivo):
  - **CH1 (S1–S7c, 2–4 oct):** 2.0 MHz, 21.7 dB a 4.5 MHz y ruido de 0.3 % de división, en ≥ 95 % de las placas. Entrada P4b, OPA810, escalera de 6 tomas con 74HC4051, ganancia ×50 con AD8039, filtro con AD8039, etapa final OPA836 con offset por DAC y red del pin de 68 Ω + 470 pF.
  - **CH2/CH3 (S9, 4–6 oct):** la misma cadena con el filtro a 1 MHz (RFILT1 2.37 kΩ, RFILT2 1.10 kΩ) y un ADC a 3.47 MSa/s. **AD8039 elegido** frente al LM6172 (DECISIONS 6 oct). C9 conjunto: 96.2 % frente a 94.2 %; 63 mW por canal frente a 109 mW.
  - **D-07 (orden de la cadena) aceptada** por Keneth el 6 oct.
- **Esquemas en KiCad** (unidos en `main` y subidos):
  - CH1 (S8/S8b): hoja raíz, cableado y verificado; `verificar_s8.py` sale con código 0.
  - CH2/CH3 (S10): hojas jerárquicas `ch2.kicad_sch` y `ch3.kicad_sch`, referencias 2xx/3xx y filtro con 2.2 kΩ + 150 Ω; `verificar_ch23.py` sale con código 0.
  - ERC: 31 avisos, todos de tipos conocidos (riel sin fuente hasta que exista la hoja de alimentación, S0–S2 del 4051 y globales sin pareja).
  - **Se dejan como están** hasta tener más hojas del proyecto (Keneth, 6 oct). Pendientes de entonces: cajetines, mover CH1 a su propia hoja y los textos apretados.
- **Consumo G.3/G.4 rehecho el 6 oct** con el AFE real: 2.52 W y 6.6 h en el peor caso (RF-17 ≥ 4 h).

## Siguiente, en este orden (Keneth, 6 oct)

1. **DMM** (RD-01…RD-10):
   - 50 V en continua, 50 Vrms en alterna y 2 A, 4½ dígitos, tres bornes (V/Ω, COM y A);
   - entrada V/Ω y su protección para 71 Vpk continuos, con aviso en el panel y el manual;
   - prueba de diodo de 3.5 V con divisor antes de PB14;
   - protección frente a errores (RD-10; abierto: cuánto aguanta si se conecta a la red);
   - interruptor de carga propio, o aceptar que se apaga con el AFE (RF-18, G.6).

   Mismo método que CH1: diseño en el documento vivo, simulación por Codex, auditoría de Claude y paso al esquema.
2. **AWG** (RG-01…RG-08):
   - etapa de salida de ±5 V con 50 mA y límite de corriente;
   - filtro de reconstrucción de 2 MHz;
   - protección de ±15 V con la sujeción a masa (G.5);
   - RG-07: fuente de continua frente a salida de 50 Ω, junto con su convertidor de ±6.5 V.
3. **Mapa de pines y conexión con el STM32G473 (D-02).** Con el DMM y el AWG diseñados, se reparten los recursos del G473 separando lo analógico de lo digital:
   - **Analógico:**
     - ADC: CH1 en PA0 con ADC1+2 entrelazados; CH2/CH3 en ADC3/ADC4; el DMM en el ADC5 diferencial (RD-03);
     - DAC de offset de los tres canales (PA4–PA6);
     - DAC3 y los OPAMP internos del AWG;
     - comparadores o watchdog para el disparo de CH2/CH3 (PE9/PE15 no llegan a ningún comparador; P11, P12);
     - VREF+.
   - **Digital:** bus del AFE (2 × 74HCT595 con 13 líneas, incluida `RELAY_KICK`, y el 74HC165 del acoplo: SCK, dato, latch, dato de vuelta y carga), enlace con el ESP32-S3, pantalla, USB y depuración.
   - Durante los pasos 1 y 2 se anota en una lista de reserva cada pin o periférico del G473 que el DMM y el AWG den por supuesto, para no diseñar contra un recurso ocupado.
4. **Rieles (G.8):** elegir en LCSC (RF-19):
   - el cargador que no deje subir VSYS de ~4.4 V;
   - el boost de 5.3 V y el buck de 3.3 V;
   - el convertidor de ±6.5 V del AWG;
   - el driver de la retroiluminación y los interruptores de carga;
   - el circuito común del economizador de los relés (P-MOSFET de arranque y Schottky), las TVS de riel y el ajuste del LM27762 a ±4.90 V.

   Propuesta abierta: tomar el mantenimiento de los relés del buck de 3.3 V en vez del LDO (≈ −0.11 W).
5. **Resto de esquemas** en `04_esquematicos/kicad/` (KiCad 10, rama `ai/*`, Konnect solo en sesiones abiertas en esa carpeta):
   - las hojas del MCU, el ESP32-S3, la TFT, el USB, la alimentación, el DMM y el AWG;
   - después, la jerarquía completa y la revisión de CH1–CH3;
   - antes de la PCB: stackup de 4 capas, contorno y clases de red del AFE con sus reglas DRC (las escribe Keneth en `s3g4.kicad_dru`);
   - más adelante: remoto en GitHub con KiBot.

## Decisiones abiertas (de Keneth)

- Tope RE-01 de 120 USD: **en espera** (6 oct). CH1 cuesta ≈ 19.6 USD por canal: el AFE ronda los 59 USD.
- P13 (CPU a 104 MHz con el ADC síncrono).
- TVS de riel y circuito común del economizador: por elegir (paso 4).
- ¿Cuánto debe aguantar el DMM si se conecta a la red por error (RD-10)?
- RG-07: el AWG como fuente de continua a través de 50 Ω.
- ¿Interruptor de carga propio para el DMM (RF-18)?
- Mantenimiento de los relés desde el buck de 3.3 V (propuesta de G.3, 6 oct).
- Propuestas P1–P16: todas siguen sin aplicar, salvo lo que recogen D-xx, RF, RD y RG.
