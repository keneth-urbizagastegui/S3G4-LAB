# Revisión completa del canal CH1 — componentes, lógica, teoría y matemáticas

- Autor: Claude Code, 3 oct 2026, a petición de Keneth, mientras corre S7.
- Alcance: la cadena de CH1 de la BNC a PA0, tal como queda tras S0–S6 y las decisiones del 3 oct (`ai-context/DECISIONS.md`).
- **Todas las cifras de §2 salen de un script, no de memoria:** `chequeo_claude/revision/revision_ch1.py` (salida en `revision_ch1_salida.txt`). Los valores de las hojas se comprobaron en `datasheet/` y `datasheet - componentes/`.
- Esta revisión no sustituye a S7, que verifica el canal completo en simulación.

## 0. Resumen

**La arquitectura es correcta y las cuentas cierran.** Las escalas dan 0.25 V/div con un error de −0.2 a −0.6 % (lo corrige la calibración). El ancho de banda queda en 2.0 MHz con el filtro decidido y el ruido total en ≈ 0.45 % de división. Ningún componente trabaja fuera de su hoja en uso normal, con dos excepciones de margen y una incoherencia de documentación:

| # | Prioridad | Hallazgo | Propuesta |
|---|---|---|---|
| R1 | **Alta** | **C_S y C_EQ de la lista de piezas (C.6) no son los simulados.** Desde S2b, las simulaciones calculan C_S = **1.17 nF** y C_EQ = **8.7 pF**; C.6 dice 1.5 nF y ≈ 12 pF (cifras de S1, cuando la capacidad del buffer se contaba dos veces) | C_S = **1.2 nF** C0G ≥ 200 V (E12; error de planitud de la rama ×1 del 0.03 %); C_EQ ≈ **8.2–9.1 pF** C0G ≥ 200 V, seleccionado en prueba |
| R2 | Media | **74HC4051 sin margen de alimentación:** VCC − VEE = 10.0 V nominal, y el máximo recomendado es 10.0 V (hoja p. 6). El LM27762 tiene la referencia al ±1.5 %: con ±5.08 V serían 10.16 V (el máximo absoluto es 11 V) | Ajustar el LM27762 a **±4.90 V** (9.8 V; peor caso 9.95 V), o aceptar el exceso dentro del máximo absoluto. Con ±4.9 V, la salida del OPA810 sigue dentro de los rieles del 4051. Hay que repasar S2b (sujeción a ±4.9 V) |
| R3 | Media | **Consumo:** el macromodelo del OPA810 da 1.9 mA; la hoja, **3.7 mA** típicos (4.6 máx.). Por canal: **7.7 mA por riel de ±5 V** y 1.0 mA en 3.3 V. G.3 suponía 3.9 mA por amplificador (39 mA para 10 amplificadores) | Rehacer G.3 con 3 × 7.7 = **23 mA por riel** (si CH2/CH3 son iguales) y 3 mA en 3.3 V: ≈ 0.24 W en vez de ≈ 0.6 W |
| R4 | Media | **VCHECK (P3) sin valores**, y el autocero (Y6 = GND) **no ve los offsets de antes del 4051**: OPA810 hasta 715 µV × 50 = 36 mV en el ADC (0.14 div en 5 mV/div) | VCHECK = divisor desde VREF+ de **12.4 kΩ / 100 Ω 0.1 %** → 19.97 mV → ≈ 1.0 V en el ADC (4 div). El offset de la entrada se calibra con el conmutador de acoplo en GND (D-04): ahí queda a masa la entrada del buffer |
| R5 | Media | **El documento vivo está desfasado:** no hay secciones D (filtro), E (offset) ni F (driver del ADC), y C.6 no tiene U105, OPA836, la red de S4, VMID ni C_F | Escribir D, E y F con S4–S7 cuando se audite S7 |
| R6 | Baja | Supuestos sin verificar en placa: R_SW del ADC (≈ 825 Ω deducida), estado previo de su condensador de muestreo, inyección de carga real del 4051, economizador del relé | Medirlos en el primer prototipo (§5) |

## 1. Piezas de CH1

| Bloque | Pieza | Valor | Función | Comprobado |
|---|---|---|---|---|
| Entrada | J101 Kinghelm C2837587 | BNC 500 Vrms | Conector | A.1 |
| | SW101 SS23H37L6 | AC / DC / GND | Acoplo; GND pone a masa la entrada del buffer | A.2 |
| Grueso | K101 HFD27/005-S (C23911) | DPDT monoestable, reposo en ÷100 | Elige ×1 o ÷100; el 2.º polo conecta la réplica | S1–S2b |
| Divisor ÷100 | R1A, R1B | 2 × 549 kΩ 0.1 % 1206 | Rama superior; 49.5 V cada una con 100 V | §2.1 |
| | C1A, C1B + trimmer | 2 × 20 pF C0G + SEHWA 2–6 pF | Compensación arriba (10 pF efectivos) | S1b |
| | R2 · C2 | 11.0 kΩ 0.1 % · ≈ 1.09 nF C0G | Rama inferior; Cb seleccionado en prueba | §2.1 |
| Rama ×1 | R_S | 2 × 49.9 kΩ 1206 | Limita a 0.95 mA con 100 V; 45 mW cada una | §2.1 |
| | C_S | **1.2 nF** C0G ≥ 200 V (R1) | Compensa R_S frente a R_BIAS · C_X1 | §2.1 |
| Réplica | R_EQ · C_EQ | 10 MΩ 1206 · **≈ 8.2–9.1 pF** ≥ 200 V (R1) | Misma Zin y Cin en las dos posiciones | S1b |
| Sujeción | D101 BAV199 (C40919) | a ±5 V | Protege SEL; I²t de ESD al 21–44 % | S2b |
| Acoplo | C_AC · R_BIAS | 1.8 nF C0G · 10 MΩ | Corte AC de 8.84 Hz | §2.1 |
| | R_PROT | 1 kΩ | Limita la corriente de entrada del buffer | S2b |
| Buffer | U101 OPA810 (C2833513) | seguidor, ±5 V | Alta impedancia; 3.7 mA | S2b |
| Escalera | RL1…RL6 | 499, 249, 150, 49.9, 24.9, 24.9 Ω | Tomas 1 … 1/40 | §2.2 |
| Selector | U102 74HC4051 (C9386) | ±5 V (**R2**) | 6 tomas + GND + VCHECK | S3 |
| Ganancia | U103 AD8039 (C96525) | 1.00 k / 249 Ω y 2.26 k / 249 Ω | ×5.016 · ×10.08 | S3 |
| Protección | R_SA, R_SB · D_A, D_B | 470 Ω · BAV99 (C2500) | Diferencial ≤ 0.69 V en sobrecarga | S3b |
| Filtro | U105 AD8039 | TR: 1.11 kΩ, 56 / 47 pF; 499 Ω, 220 / 56 pF | Anti-alias de 4.º orden activo | S5 |
| Etapa final | U106 OPA836 (C111589) | R_IN = R_F = 10 kΩ, C_F = 1 pF, R_OFF = 8.06 kΩ | Desplaza a 0–2.5 V, offset, protege el ADC | S4 |
| VMID | divisor | 10.0 k / 5.23 k + 1 µF, desde VREF+ | 0.8585 V | S4 |
| Pin | R_ADC · C_ADC | 68 Ω · 470 pF C0G | Depósito para el muestreo; último polo | S6 |
| Control | 74HCT595 × 2 | 3 líneas del 4051 + relé por canal | Desde el G473 a 3.3 V | C.6 |

## 2. Matemáticas recalculadas

### 2.1 Entrada

- **÷100:** R_bot efectiva = 11 k ∥ 10 M = 10.988 kΩ → relación **1/100.93**.
- **×1:** R_BIAS / (R_S + R_BIAS) = **0.99012** (−0.99 %).
- **Zin = 999.27 kΩ en las dos posiciones** (RF-08). En ÷100, el divisor en paralelo con R_S + R_EQ; en ×1, con R_S + R_BIAS.
- **Compensación de ÷100:** τ arriba = τ abajo = **12.078 µs** con Cb = 1088.5 pF. Cuadra con «≈ 1.08 nF».
- **Rama ×1:** C_S = R_BIAS · (C_X1 + C_off + C_SEL) / R_S = 10 M × 11.67 pF / 99.8 k = **1.169 nF**. Con 1.2 nF, la relación en alta frecuencia es 0.99037 frente a 0.99012 en continua (0.03 %). **Con 1.5 nF sería del 0.22 %** (R1).
- **Corte AC:** 1 / (2π · 10 MΩ · 1.8 nF) = **8.84 Hz**.
- **Esfuerzos con 100 V en ×1:** 0.946 mA hacia las sujeciones; 44.6 mW por R_S. En ÷100, 49.5 V por cada 549 kΩ. Todo dentro de 1206 y 200 V.
- **Offset por I_B del OPA810:** 2 pA × 10 MΩ = 20 µV.

### 2.2 Escalera y ganancia

- **Tomas reales:** 1, 0.49985, 0.25028, 0.09993, 0.04992 y 0.02496. Errores de −0.17 a +0.11 %; total 997.7 Ω; peor impedancia de toma 249 Ω.
- **Ganancia:** ideal ×5.0161 · ×10.0763 = **×50.543**. Con A_OL = 70 dB (hoja del AD8039), **×50.303** (−0.48 %).

### 2.3 Escalas: 0.25 V/div en el ADC

| Escala | Grueso | Toma | V/div en el ADC | Error |
|---|---|---|---|---|
| 5 / 10 / 20 / 50 / 100 / 200 mV | ×1 (0.99012) | 1 … 1/40 | −0.2486 … −0.2493 V | −0.28 … −0.56 % |
| 0.5 / 1 / 2 / 5 / 10 / 20 V | ÷100.93 | 1 … 1/40 | −0.2488 … −0.2495 V | −0.21 … −0.49 % |

El signo negativo es S4 (inversora): lo deshace el firmware. Todos los errores son fijos y menores que la tolerancia de las resistencias. Los absorbe la tabla de calibración por escala (P10), que S7 entrega medida (`resultados/s7_tabla_calibracion.csv`).

### 2.4 Filtro y ancho de banda

- Sección 1: f0 = 2.795 MHz, Q = 0.546. Sección 2: f0 = 2.874 MHz, Q = 0.991. Polo del RC: 4.98 MHz. Polo de S4: ≈ 10.8 MHz.
- Ideal: −3 dB en 2.13 MHz y 20.4 dB a 4.5 MHz. **Simulado en la cadena (Claude): 2.011 MHz y 21.7 dB.** La cadena real pierde un 5–6 %, como se vio en S5.
- Slew rate necesario: 2π · 2 MHz · 1 V = **12.6 V/µs**. Tienen 200 (OPA810), 425 (AD8039) y 560 V/µs (OPA836).

### 2.5 Etapa final (S4)

- V_ADC = 3.2407 · VMID − V_in − 1.2407 · V_DAC, con VMID = 0.8585 V. Centro en **1.2313 V** (simulado: 1.2347 V).
- **Offset:** de **+5.21 a −5.21 div** de cálculo; la salida no baja de ≈ 0.02 V, así que el mínimo real es −4.85 div (aceptado).
- **Carga del DAC:** 8.06 kΩ (la hoja pide ≥ 5 kΩ). **VREF+:** los tres divisores piden 0.49 mA (REF3325: ±5 mA).
- **Ganancia de ruido:** 3.24. **Polo de C_F:** 15.9 MHz.
- **Offset por I_B del OPA836:** 650 nA en el divisor dan 2.2 mV en VMID → 7.2 mV en el ADC (0.03 div), calibrable.

### 2.6 ADC y ruido

- **1 LSB = 0.610 mV**; **409.6 códigos por división**. La pantalla (±4 div) va de 0.25 a 2.25 V: **códigos 410–3686**.
- **Ruido del ADC:** 0.40–0.61 mV rms = 0.16–0.24 % div (SNR de 66.9–63.2 dB).
- **Ruido total:** AFE 0.38 % ⊕ ADC → **0.41–0.45 % de división**, unos 1.8 códigos rms en el peor caso. En pantalla, menos de un píxel.

### 2.7 Consumo por canal (hoja)

| Riel | Piezas | Corriente |
|---|---|---|
| ±5 V | OPA810 3.7 mA + 4 × AD8039 (U103, U105) a 1.0 mA | **7.7 mA por riel** |
| 3.3 V | OPA836 1.0 mA | 1.0 mA |
| VREF+ | divisor de VMID | 0.16 mA |

Tres canales iguales: ±5 V × 23 mA ≈ **231 mW**, más 10 mW en 3.3 V. G.3 contaba ≈ 0.6 W (R3).

## 3. Teoría: por qué funciona y qué supuestos tiene

1. **Grueso con relé y réplica de carga.** La impedancia y la capacidad de entrada no cambian entre ×1 y ÷100 (RF-08), así que una sonda ×10 se compensa una sola vez (S1, S1b).
2. **Atenuar y después ganancia fija.** Las 12 escalas tienen el mismo ancho de banda y el mismo filtro (DSO112). El precio es el ruido en las escalas de toma 1: 0.38 % frente a 0.2 % en las demás.
3. **Protección en capas.** El divisor y R_S limitan la corriente; los BAV199 sujetan SEL; R_PROT protege el buffer; 470 Ω + BAV99 protegen U103A/B; S4 a 3.3 V protege el ADC; el orden de encendido protege el G473 apagado (S4). **Supuesto:** los rieles absorben la corriente de sujeción porque hay carga (G.5).
4. **Filtro anti-alias de 6.º orden en total.** Con f_s/BW = 3.25 no hay forma de tener a la vez rechazo de alias y forma de onda perfecta. TR es el compromiso: 21.7 dB y ≈ 3 % de sobreimpulso. El alias a 4.5 MHz queda en el ≈ 8 % de su amplitud.
5. **Muestreo.** El depósito de 470 pF con 68 Ω carga la muestra sin error no lineal (S6). El retraso interno de 4 ns del ADC es igual en ADC1 y ADC2.
6. **Calibración (P10).** Una ganancia y un offset por escala y por ADC. Los errores fijos de §2.3 (−0.2 a −0.6 %), el −0.95 % por A_OL y los offsets (§2.5, R4) entran en ella. **Supuesto:** las derivas térmicas son pequeñas. AD8039: 4.5 µV/°C × 50 = 0.23 mV/°C en el ADC; OPA810: 10 µV/°C × 50 = 0.5 mV/°C, ≈ 0.002 div/°C en 5 mV/div.

## 4. Lógica de control y firmware

| Función | Cómo funciona | Estado / riesgo |
|---|---|---|
| Cambio de escala | El G473 escribe 16 bits en 2 × 74HCT595: por canal, 3 líneas del 4051 y 1 del relé. Las líneas cambian a la vez al subir RCLK | OK. Con 3 canales × 4 = 12 líneas; el economizador del relé puede pedir 3 más (C.6) |
| Relé | Monoestable: reposo en ÷100 (seguro sin alimentación). Esperar ≈ 7 ms de asentamiento y descartar esas muestras | Falta diseñar el economizador (D-03) |
| 4051 | Rotura antes de cierre en la hoja; asentamiento simulado < 0.1 µs (S3, sin inyección de carga) | Inyección real sin medir (R6) |
| Autocero | Y6 = GND mide los offsets **desde el 4051** (U103, U105, S4, ADC) | No ve el OPA810 ni la entrada (R4) |
| Offset de entrada | Con el acoplo en GND, la entrada del buffer va a masa: se mide el offset completo | El firmware debe leer la posición del conmutador (74HC165, A.3) |
| VCHECK | Y7: tensión conocida desde VREF+ | Valores propuestos en R4 |
| Signo | S4 invierte: el firmware multiplica por −1 | Documentar en el firmware |
| Offset vertical | DAC1/DAC2 con buffer (PA4, PA5, PA6) → R_OFF 8.06 kΩ | **Reservar PA4–PA6** en el mapa de pines de la rev 2.1 |
| Sobrecarga | Si el ADC satura (código 0 o 4095) en una escala ×1, pasar a ÷100. Con los BAV199 conduciendo, la recuperación tarda ≈ 0.6 ms (aceptado) | Regla de firmware |
| Encendido | EN+ y EN− del LM27762 con resistencia a masa; el G473 enciende el AFE cuando tiene VDDA; al apagar, primero el AFE (S4) | Regla de la sección G |
| Entrelazado | ADC1/ADC2 sobre PA0, 3.5 ciclos de muestreo y 8 de desfase; reloj síncrono (P13) recomendado | Calibrar la ganancia y el offset de cada ADC por separado |

## 5. Qué medir en el primer prototipo

1. El estado del condensador de muestreo del ADC (rampa lenta frente a un multímetro): decide entre los casos P, Z y R de S6.
2. Glitch y asentamiento del 4051 al cambiar de toma.
3. VCC − VEE real del 4051 con el LM27762 montado (R2).
4. Consumo por riel frente a §2.7.
5. Ajuste del trimmer y selección de Cb, C_S y C_EQ con la sonda ×10 (S1b).

## 6. Siguiente

- Auditar S7: verifica el filtro reescalado, el Monte Carlo y el canal completo sin la carga ficticia.
- Decidir R1 y R2.
- Escribir las secciones D, E y F del documento vivo (R5) y actualizar C.6 y G.3 (R1, R3).
- Después, S8: el esquema en KiCad.
