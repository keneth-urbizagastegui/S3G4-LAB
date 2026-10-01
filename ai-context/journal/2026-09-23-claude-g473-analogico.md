# Revisión de las partes analógicas del STM32G473 (datasheet y manual)

- Fecha: 2026-09-23, tarde (≈ 17:30–18:15 hora local).
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: revisar en `datasheet/` «el manual y el datasheet de todas las partes analógicas del STM32G473, con su propio artefacto».

## Cambio

- Nuevo `docs/g473_analogico.html`, publicado en https://claude.ai/artifact/8fBAS9Tis7h8yQh9qnSciB.
- Generadores nuevos en `docs/rediseno_afe_gen/`: `calc_g473.py` (cifras derivadas) y `build_g473.py`.
- No se tocó firmware, `.ioc`, PCB ni el mapa de pines. Ninguna propuesta aplicada.

## Fuentes

- `datasheet/stm32g473.pdf` = DS12712 Rev 5:
  - §3.18–3.22.
  - Tabla 12 (LQFP100), extraída con `find_tables` de PyMuPDF.
  - T.14, T.15, T.20, T.21, T.52–T.54 y T.60–T.77.
- `datasheet/rm0440-…(1).pdf` = RM0440 Rev 9:
  - Capítulos 21–25.
  - T.161, T.179, T.183, T.197, T.199, T.200, T.204.
  - Tablas de interconexión de temporizadores T.268 y T.292.
- Números de canal interno contrastados con `stm32g4xx_ll_adc.h` (CubeG4, en el clon de black_scope).
- No se revisaron los otros PDF de la carpeta: ESP32-S3, OPA313, LM27762 y REF3325. Del REF3325 y del OPA313 sólo se usó el resumen de la primera página.

## Hallazgos con cifra y fuente

- **f_ADC máxima (T.61):**
  - 60 MHz con un solo ADC.
  - **52 MHz con varios ADC si V_DDA ≥ 2.7 V**; 42 MHz por debajo.
  - Conversión = muestreo + 12.5 ciclos.
- **Canales rápidos (IN1–IN5) y lentos (T.62, 12 bits):**
  - Canal rápido: R_AIN ≤ 100 Ω con 2.5 ciclos.
  - Canal lento: no admite 2.5 ciclos; con 6.5 ciclos, R_AIN ≤ 100 Ω.
  - Velocidades a 52 MHz: 3.47 MSa/s en canal rápido y 2.74 en canal lento.
  - Entrelazado rápido: 6.5 MSa/s (SMPPLUS, 16 ciclos).
  - Entrelazado lento: ~5.2 MSa/s. Es cálculo propio con DELAY = 3 y disparo externo, **por verificar**.
- **Salida de OPAMP por el canal interno (T.75):** muestreo ≥ 200 ns, es decir ≥ 12.5 ciclos a 52 MHz, que dan 2.08 MSa/s.
- **Reloj del ADC (T.61, RM §21.4.3):**
  - Asíncrono (CKMODE = 00): latencia de disparo de 1.5–2.5 ciclos.
  - Síncrono: latencia fija, y el manual lo recomienda con disparo por temporizador.
  - Peor caso con fase aleatoria a 52 MHz (σ = 5.55 ns): SNR ≤ 29 dB a 1 MHz y 49 dB a 100 kHz.
- **Precisión:**
  - Un solo ADC: ENOB 10.6 y SNR 66.9 dB típicos, THD −73 dB (T.63).
  - Varios ADC: ENOB 10.7 (25 °C) a 10.1 (−40…125 °C) (T.66–T.68).
  - Con VREF+ = 2.5 V, el ruido del ADC es 0.40–0.61 mV rms, **0.16–0.24 % de una división de 0.25 V**. Es del orden del ruido del AFE de la sección C, y se suman en cuadratura.
- **Watchdogs (RM §21.4.28):** AWD1 de 12 bits con filtro; AWD2 y AWD3 de 8 bits. Sus salidas van a las ETR:
  - TIM1: ADC1 y ADC4.
  - TIM8: ADC2 y ADC3.
  - TIM20: ADC3 y ADC5.
  - TIM3: ADC2.
- **Ayudas del ADC:**
  - Sobremuestreo ×2–×256 hasta 16 bits.
  - Offsets por canal y GCOMP.
  - BULB y SMPTRIG.
  - ADCAL tras cada arranque.
- **DAC (T.69–T.72, RM T.183):**
  - DAC1 (PA4/PA5) y DAC2 (PA6): 1 MSa/s con buffer, C_L ≤ 50 pF, R_L ≥ 5 kΩ y salida de 0.2 V a VREF+ − 0.2 V. TUE ±30 LSB.
  - DAC3 y DAC4: sólo internos, 15 MSa/s, 64 ns a 1 LSB, 720 µA de VREF+.
  - Modo sample-and-hold con 0.1–1 µF.
- **OPAMP (T.75):**
  - GBW 7/13 MHz. Slew rate 2.5/6.5 V/µs en modo normal y 18/45 V/µs en alta velocidad.
  - Carga máxima 500 µA y 50 pF.
  - Ruido 250 nV/√Hz a 1 kHz y 90 nV/√Hz a 10 kHz.
  - PGA con R1 = 10 kΩ y R2 = (G − 1)·10 kΩ (±15 % en absoluto). Error de ganancia ±1 % hasta ×16 y ±2 % a ×32 y ×64.
  - Estimación propia del ruido 1/f entre 0.1 y 10 Hz: ≈ 17 µV rms, por verificar en el óhmetro.
- **COMP (T.74, RM T.199/T.200):**
  - Retardo 16.7 ns típico, 31 ns máximo. Offset de −9 a +3 mV.
  - Histéresis de 0 a 63 mV, sólo en el flanco de bajada.
  - Tablas de entradas INP e INM recogidas en la página.
- **VREFBUF (T.73, RM T.197):**
  - 2.048, 2.5 o 2.9 V con ±4 mV. Deriva ≤ VREFINT + 50 ppm/°C. PSRR de 40–55 dB.
  - Tras el reset, HIZ = 1: VREF+ queda como entrada.
  - **ENVR = 0 con HIZ = 0 lleva VREF+ a masa.** Con una referencia externa, el firmware no debe escribir nunca ese estado.
- **Pines (T.14, T.15, T.54):**
  - TT_xx: de −0.3 a 4.0 V.
  - **Sin inyección positiva posible.** La negativa admite −5 mA por pin y −25 mA en total, y degrada otros canales; el fabricante recomienda un Schottky a masa.
  - Fuga de ±100 a ±150 nA y 5 pF por pin.
  - El booster sólo hace falta con V_DDA < 2.4 V.
- **Consumo (T.21):** CPU a 170 MHz, 29.5 mA; a 104 MHz, ≈ 16.9 mA (interpolado). Bloques analógicos en una configuración supuesta: ≈ 6.8 mA típicos.

## Contraste con el mapa firmado y D-02

- Los tres canales de D-02 caen en canales rápidos.
- **Pendiente:** PE9 (ADC3_IN2) y PE15 (ADC4_IN2) no llegan a ningún comparador. Caminos para disparar CH2 y CH3:
  - Watchdog (P11/P12).
  - Un segundo pin, como la rev 2.0 con PD11/PD12.
  - Para CH2, mover el canal a **PE7** (ADC3_IN4 rápido + COMP4_INP; umbral desde DAC1_CH1).
- El umbral de CH1 (COMP3) debe salir de DAC1_CH1, porque DAC3 es el AWG. El mapa ya prevé DAC1 en modo interno.
- El mapa firmado es de la rev 2.0 (4 canales). Hay que revisarlo con D-02; esta revisión no lo modifica.

## Propuestas nuevas (continúan P1–P12; ninguna aplicada)

- **P13 · Reloj del ADC síncrono:** HCLK = 104 MHz con CKMODE = HCLK/2 da 52 MHz. Sin incertidumbre de disparo y con ≈ 12.6 mA menos de CPU. La alternativa es 170 MHz /4 = 42.5 MHz, que baja D-02 a 5.31 y 2.83 MSa/s. **Decidir** en la sección D.
- **P14 · Ningún pin analógico recibe más de V_DDA:** la última etapa se alimenta desde V_DDA (P8), o se añade una sujeción externa antes del RC anti-alias. **Adoptar** en la sección F.
- **P15 · Tensiones de continua con el DAC en sample-and-hold** (o sin buffer, más un buffer de bajo consumo). **Estudiar.**
- **P16 · Calibración P10 y DMM con las ayudas del ADC** (GCOMP, offsets, sobremuestreo, BULB). **Estudiar** en firmware.

## Pruebas

Lectura del fabricante y cálculo (`python calc_g473.py`); no hay hardware. Se comprobaron en el texto del PDF las tablas de comparadores, de rutas de OPAMP y de interconexión de temporizadores. La tabla de pines se extrajo automáticamente y se contrastó a mano en los pines que usa el mapa.

## Pendientes

1. Decidir P13 con la sección D, y resolver el disparo de CH2 y CH3 (PE7, segundo pin o watchdog).
2. Revisar el mapa firmado para la rev 2.1 (3 canales, D-02).
3. Verificar en banco el entrelazado sobre un canal lento y el ruido 1/f del OPAMP en el óhmetro.
