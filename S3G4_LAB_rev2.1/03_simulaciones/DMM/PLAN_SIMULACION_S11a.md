# Plan de simulación S11a — DMM: cadena de medida, fuente de ohmios P43 y dinámica

- Autor: Claude Code (auditor), 7 oct 2026. Ejecuta: Codex. Audita: Claude.
- Contrato de `ENCARGO_CODEX_S11a.md`.
- Primera simulación del DMM. **Lee antes, enteros:**
  - `S3G4_LAB_rev2.1/01_diseno/dmm_rev21.html` (sección H), que es la fuente de todos los valores;
  - `00_requisitos/especificaciones_dmm.html` y `00_requisitos/requisitos_dmm_awg.html` (RD-01…RD-10);
  - en `ai-context/DECISIONS.md`, las entradas del 7 oct (arquitectura del DMM, criterio de diseño, D1–D7 y D8);
  - para el método: `../CH1_entrada/PLAN_SIMULACION_S6.md` (modelo del ADC) y `../CH23_entrada/PLAN_SIMULACION_S9.md`.
- Cifras de diseño y estimaciones de Claude: `S3G4_LAB_rev2.1/herramientas/calc_dmm_h.py` y `calc_dmm_s11.py`.

## 0. Para qué sirve y qué queda fuera

Keneth no caracteriza la parte analógica en banco antes de fabricar (DECISIONS, 7 oct). S11 tiene que dejar el margen para que, al fabricar, **baste con calibrar por software**. Por eso casi todos los criterios se miden **tras calibrar a 23 °C**, a 18 y a 28 °C.

Fuera de S11a:
- **La INL del ADC5** es del chip y se linealiza al fabricar (D1). Aquí el ADC es ideal salvo su carga de muestreo.
- **La escalera de P42** (H §6 solo la esboza), la red durante 10 s en V/Ω y las ESD van a **S11b**, cuando Claude fije su circuito. En S11a, P42 se sustituye por un 1N4007 (modelo de LTspice) en serie con una fuente de 0.2 V, de modo que la caída total sea ≈ 0.8 V, como supone `calc_dmm_h.py`.
- **El fusible** no tiene pieza elegida.

## 1. Circuito (valores de la sección H; no cambies nada salvo lo que se barre)

Rieles del DMM:
- ±4.90 V detrás de su interruptor de carga (P22, ideal en S11a);
- 3.30 V analógico para el driver;
- VREF+ = 2.500 V de la REF3325, que también da IREF y VCM.

COM es el punto estrella (P27).

1. **Entrada de tensión.**
   - V/Ω → R_PROT, 3 × 33.0 kΩ (1206, 1 %) → nodo X0, con un BAV199 a ±4.9 V.
   - Divisor entre V/Ω y COM, siempre conectado: 3 × 3.00 MΩ – toma ÷10 – 900 kΩ – toma ÷100 – 100 kΩ (0.1 %, 25 ppm/°C).
   - La toma ÷10 lleva su BAV199 a ±4.9 V.
   - Compensación (P18), en C0G: sobre cada 3 MΩ, 100 pF de 630 V con 3.3 kΩ de amortiguación en serie; 330 pF sobre 900 kΩ; 3.0 nF sobre 100 kΩ (τ ≈ 300 µs, `calc_dmm_s11.py`).
2. **Mux de señal:** 74HC4051 a ±4.9 V, modelo Nexperia `SWI1` (8 instancias con Z común; ver `models/LEEME.md`).
   - X0 = nodo tras R_PROT; X1 = toma ÷10; X2 = toma ÷100; X3 = COM.
   - X4 = salida de B.
   - X5 = borne A antes del fusible, a través de 10.0 MΩ.
   - X6 al aire.
   - X7 = VREF ÷2 (10.0 kΩ / 10.0 kΩ al 0.1 % desde VREF+, con 100 nF).
3. **Amplificador A:** media OPA2188 a ±4.9 V, no inversor.
   - R_F = 9.09 kΩ y R_G = 1.00 kΩ (0.1 %, 25 ppm/°C), siempre de la salida a COM.
   - Dos canales `SWI1` complementarios llevan IN− a la salida (×1) o a la toma R_F/R_G (×10.09). La resistencia del conmutador no entra en la ganancia.
4. **Amplificador B:** la otra mitad, no inversor ×10.09 con las mismas R_F/R_G.
   - IN+ va al hilo Kelvin del lado alto del derivador; R_G, al hilo Kelvin del lado de COM.
   - La salida va a X4.
5. **Corriente:** A → fusible (40 mΩ, sin apertura) → derivador de 0.100 Ω (1 %) → COM.
   - DF10S (sustituto: 4 × 1N4007) en paralelo con el derivador, con + y − unidos.
   - El retorno de COM se modela con 2 mΩ por tramo de pista hasta el punto estrella. Por él vuelven la corriente del divisor, la de la fuente de ohmios y ≈ 3 mA de alimentación del DMM.
6. **Driver diferencial a 3.30 V:**
   - U1 es un seguidor. Su IN+ toma el punto medio de 10.0 kΩ desde la salida de A y 10.0 kΩ desde VREF+, así que PD13 = VREF/2 + v/2.
   - U2 es un inversor ×−1 (10.0 kΩ / 10.0 kΩ) desde la salida de U1, con IN+ en VCM = VREF/2 (10.0 kΩ / 10.0 kΩ desde VREF+, 100 nF). Así PD14 = VCM − v/2.
   - Todas las resistencias son del 0.1 % y 25 ppm/°C.
   - Cada salida va al pin con R_ISO en serie y C_FLT a masa (P20), que se barren en K6.
   - **Dos variantes de amplificador:** **A = TLV2372** (la misma pieza que P43) y **B = OPA365** (modelo en `models/`). La pieza está abierta en H: informa de las dos y no elijas.
7. **ADC5:** diferencial PD13–PD14, ideal salvo el muestreo de S6 §2.
   - Por pin: C_pad = 5 pF, el interruptor R_SW ∈ {400, **825**, 1500} Ω y C_S = 5 pF.
   - Estados previos P, Z y R, como en S6.
   - f_ADC = 50 MHz y t_s = **92.5 ciclos** (1.85 µs); se barre {24.5, 47.5, 92.5}. Una conversión cada 5 µs (200 kSa/s).
   - ±2 V diferenciales = ±19 999 cuentas: **1 cuenta = 100 µV en el ADC**.
8. **Fuente de ohmios P43** (aceptada, D8):
   - **IREF:** TLV2372 A, con IN+ en VREF+ y un elemento de paso N cuyo emisor (o fuente) va a IN− y a R1 = 24.9 kΩ a COM. El colector (o drenador) toma IREF del riel +4.9 V a través de R2 = 4.99 kΩ (0.1 %, 25 ppm/°C). V_set = VREF·R2/R1 ≈ 501 mV bajo el riel.
   - **TLV2372 B:** IN+ en el nodo de R2. IN− va al lado bajo de R_rango por el 74HC4051 de **sentido**. La salida mueve el elemento de paso P, cuyo emisor (o fuente) va al lado bajo de R_rango por el 74HC4051 de **fuerza**.
   - **R_rango**, desde el riel: 50.0 Ω, 500 Ω, 5.00 kΩ, 50.0 kΩ, 500 kΩ y 2.49 MΩ (0.1 %, 25 ppm/°C). Rangos de 200 Ω a 20 MΩ: 10 mA … 0.2 µA.
   - **Elementos de paso, dos variantes:** **A = bipolares** (2N3904 / 2N3906 de LTspice, por MMBT3904 / MMBT3906) y **B = MOSFET** (2N7002 / BSS84 de LTspice). Motivo: la corriente de base no llega a Rx. Con β = 100 se pierde ≈ 1 %, con una deriva de ≈ 300 ppm con ±5 °C (`calc_dmm_s11.py`). Informa de las dos y no elijas.
   - El colector (o drenador) del elemento P → P42 provisional (§0) → V/Ω.
   - Con la fuente apagada, la salida de B lleva el elemento P a corte (en S11a basta con IREF = 0 y B en el riel).
9. **Continuidad:** la salida de A → divisor ÷2 (2 × 10.0 kΩ) → BAV199 a 0 / 3.3 V → PB14.
   - COMP7 ideal, con el umbral del DAC2 en 0.250 V (50 Ω con 10 mA) y 20 mV de histéresis (supuesto).

## 2. Modelos y hojas

- **En el proyecto:** `74HC4051/` (Nexperia, **solo para transitorio**: en continua, corre un transitorio hasta régimen y dilo), `BAV199.txt`, `OPA365.lib`, y las hojas `74HC_HCT4051.pdf`, `BAV199.pdf`, `datasheet/stm32g473.pdf` (DS12712) y `datasheet/rm0440…pdf`.
- **Los pone Keneth antes del lanzamiento** en `Simulation_LTSpice/models/<pieza>/` y `datasheet - componentes/`:
  - modelos de TI de OPA2188, TLV2372 y REF3325;
  - hojas de OPA2188, TLV2372, REF3325, MMBT3904, MMBT3906, 2N7002, BSS84, 1N4007W y DF10S.
  - **No descargues nada.**
- **Si falta un modelo**, usa el sustituto de LTspice y márcalo en cada resultado:
  - OPA2188 → `LTC2057`, con Vos e Ib inyectados a los valores de la hoja (o de H §④ si falta la hoja);
  - REF3325 → fuente ideal de 2.500 V con la tolerancia y el coeficiente de temperatura de la hoja;
  - TLV2372 → no tiene sustituto: haz la variante B del driver y deja P43 preparada.
- **Ojo con las fugas:** el modelo del 4051 no da su fuga en corte. Se inyecta como fuentes de corriente (K3).

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| K0 | Modelos frente a hojas | OPA2188: Vos, deriva, Ib, GBW, ruido, modo común (¿V+ − 1.5 V?) e **inversión de fase** (lo que diga la hoja). TLV2372: Vos, Ib, salida a ±4.9 V y estabilidad con carga capacitiva. REF3325: tolerancia y coeficiente de temperatura. β (hFE) de 2N3904/2N3906 a 10 mA … 0.2 µA frente a MMBT3904/3906. Fuga de puerta de 2N7002/BSS84. Tabla con página y tabla de cada dato. Comprueba los ejemplos de H: 12 V en 20 V (PD13 = 1.85 V, PD14 = 0.65 V), 150 mA (v = 1.5 V) y 4.7 kΩ (V_x = 0.470 V) |
| K1 | Cadena nominal | Todos los rangos y funciones a 23 °C. v en el ADC a −FS, −50 %, 0, +10 %, +50 % y +FS. Tabla de calibración: ganancia, offset y no linealidad residual tras un ajuste de 2 puntos. Corriente de cada rango de ohmios y tensión disponible |
| K2 | Monte Carlo y temperatura | 500 placas, semilla fija. Se calibra cada placa a 23 °C (2 puntos por rango) y se evalúa a 18 y a 28 °C en 10, 50 y 100 % del rango (y −100 % en continua). Funciones: DCV (4 rangos), DCI (2) y Ω (6, variantes A y B). Reparto: resistencias del 0.1 % uniformes ±0.1 % y ±25 ppm/°C; del 1 %, ±1 % y ±100 ppm/°C; C0G ±5 % y ±30 ppm/°C; REF3325 y amplificadores con los máximos de la hoja (uniformes); rieles ±2 %; β uniforme en el rango de la hoja; fuga del 4051 de 1 nA por canal con signo al azar y ×2 cada 10 °C |
| K3 | Fuga del 74HC4051 | Barre 0.1, 1, 3 y 10 nA por canal (en el mux de señal, el de ganancia y los dos de P43). Pon cada caso en cuentas y en ppm tras calibrar, a 18 y 28 °C. **Fuga máxima tolerable** por rango para S11-C2 y S11-C4 (decide D4) |
| K4 | Asiento del autocero (P38) | Transitorio con el modelo `SWI1`: X3 → X0, X1, X2 y X4, con la entrada a fondo y a 10 %. Tiempo hasta quedar a 1 cuenta del final, inyección de carga incluida |
| K5 | Alterna | `.ac` de 10 Hz a 100 kHz en los 4 rangos de ACV y los 2 de ACI, con las capacidades parásitas (4051, BAV199, entrada del OPA2188, 2 pF de pista). **Riesgo previsto por Claude:** R_PROT con ≈ 40 pF en X0 da un polo en ≈ 40 kHz, −10 % a 20 kHz en 200 mV y 2 V. Ajusta en cada placa la corrección P39 (un cero y un polo) a 1 y 20 kHz, a 23 °C. Residuo de 40 Hz a 20 kHz a 18, 23 y 28 °C, con 200 placas. Informa también de cuánto varía la capacidad de X0 con la tensión de la señal |
| K6 | Driver y muestreo (P20) | Rejilla R_ISO ∈ {100, 330, 1000, 3300} Ω con C_FLT para 50 kHz (E12 C0G: 33 n, 10 n, 3.3 n y 1 nF), en las variantes A y B. Por punto: error del muestreo en continua de −2 a +2 V en pasos de 0.25 V (lineal y no lineal), con P, Z y R, R_SW × 3 y t_s × 3. Estabilidad: escalón de 0.1 V con sobreimpulso y margen de fase. Respuesta a 20 kHz |
| K7 | Fuente de ohmios (P43) en detalle | Por rango y variante: regulación de carga (I con Rx = 0 frente a Rx = fondo); tensión disponible y margen con los rieles a −2 %; tensión en vacío; tiempo de asiento al conectar Rx. **Riesgo previsto:** en vacío, de 2 kΩ a 2 MΩ, la entrada del OPA2188 queda en su límite de modo común. Mira la salida de A en ×1 con IN+ de 3.0 a 3.6 V. Diodo a 1 mA con modelos de LED rojo (1.8 V), verde (2.2 V), azul (3.0 V) y blanco (3.2 V), frente a ~3.5 V de RD-08 |
| K8 | Ruido | Referido a la entrada en 200 mV, 2 V y 200 mA (y 200 Ω), en cuentas rms. En continua, con una integración de 1 ciclo de 60 Hz (ENBW 30 Hz); en alterna, de 40 Hz a 100 kHz |
| K9 | Firmware, en Python | Rechazo de la red con 1 ciclo de 60 Hz y con 100 ms, a 50 y 60 Hz ± 0.5 Hz. TRMS con muestras a 200 kSa/s y ventanas de 100 ms no coherentes: senos de 40 Hz a 20 kHz al 10 y 100 % del rango y factor de cresta 3, con la cuantización y el ruido de K8 |
| K10 | Corriente y punto estrella | Offset y ruido de 200 mA con el retorno del §1.5. Error en cuentas por las corrientes de retorno en cada función. Sobrecorriente en A sin apertura del fusible (±12 V entre A y COM durante 10 ms): sujeción del DF10S y entrada de B. Autocalentamiento del derivador a 2 A, en papel, con un coeficiente supuesto de ±50 ppm/°C (no hay pieza elegida) |
| K11 | Sobrecarga y recuperación | 50 V en 200 mV (X0, sujeción BAV199), 50 V en 2 V y −50 V. Salida de A sin inversión de fase y tiempo hasta 1 cuenta tras retirar la sobrecarga. Corriente por cada BAV199 frente a su hoja. Las tensiones en PB14, PD13 y PD14 frente a los máximos absolutos del G473 (DS12712) |
| K12 | Continuidad | Contacto de 0, 40, 50, 60 y 100 Ω desde vacío: tiempo hasta que PB14 cruza 0.25 V y ausencia de rebotes. PB14 con la entrada de −50 a +50 V |
| K13 | Consumo | Por riel y por bloque, con la fuente de ohmios en cada rango |

## 4. Criterios de aceptación (funcionales; ≥ 95 % de las placas; cada variante por separado)

| # | Criterio | Prueba |
|---|---|---|
| S11-C1 | DCV: ganancia tras calibrar a 23 °C, a 18 y 28 °C, **≤ 500 ppm** en cada rango (la cadena analógica; el patrón y la ganancia del ADC van aparte, `calc_dmm_adi.py`) | K2 |
| S11-C2 | DCV: offset tras autocero y calibración, a 18 y 28 °C, **≤ 4 cuentas** en cada rango con 1 nA de fuga | K2, K3 |
| S11-C3 | DCI: ganancia **≤ 500 ppm** sin el autocalentamiento del derivador (se informa aparte) y offset **≤ 4 cuentas** en 200 mA | K2, K10 |
| S11-C4 | Ω: lectura tras calibrar, a 18 y 28 °C, **≤ 500 ppm** de 200 Ω a 2 MΩ y **≤ 0.3 %** en 20 MΩ | K2, K3, K7 |
| S11-C5 | Ω: tensión disponible − V_x a fondo **≥ 0.2 V** en cada rango con los rieles a −2 %, y regulación de carga **≤ 100 ppm** | K7 |
| S11-C6 | Alterna: residuo tras P39, de 40 Hz a 20 kHz, **≤ 0.5 %** en cada rango a 18, 23 y 28 °C | K5 |
| S11-C7 | Autocero: **≤ 1 ms** hasta 1 cuenta en cada toma | K4 |
| S11-C8 | Muestreo: parte no lineal **≤ 1 cuenta** (100 µV) con t_s = 92.5 ciclos y R_SW = 825 Ω en algún punto de la rejilla. Sobreimpulso **≤ 10 %** en ese punto. Informa de la rejilla entera | K6 |
| S11-C9 | Ruido en continua **≤ 1 cuenta rms** en 200 mV, 2 V y 200 mA | K8 |
| S11-C10 | OPA2188 fuera de su modo común o en sobrecarga: salida saturada en el sentido correcto y recuperación **≤ 1 ms** | K7, K11 |
| S11-C11 | Rechazo de la red **≥ 40 dB** a 60 ± 0.5 Hz, con 1 ciclo y con 100 ms (a 50 Hz, informar) | K9 |
| S11-C12 | TRMS: error del algoritmo **≤ 0.1 %** de la lectura de 40 Hz a 20 kHz, del 10 al 100 % del rango y con factor de cresta 3 | K9 |
| S11-C13 | Continuidad: PB14 cruza el umbral **< 1 ms** tras el contacto con ≤ 50 Ω y no lo cruza con ≥ 60 Ω. PB14 dentro de sus máximos con ±50 V | K12 |
| S11-C14 | Sobrecarga: corrientes por los BAV199 y por los pines **≤ 50 %** del máximo de la hoja | K10, K11 |
| — | Informar sin criterio: corrientes de ohmios, tensión en vacío, LED, el autocalentamiento y el error del punto estrella, consumo y la variación de la capacidad de X0 | K1, K7, K10, K13 |

Fallar es un resultado válido; informa siempre del valor y de la fracción de placas. Si algo falla, di cuánto falta y qué variable lo movería, **sin simular remedios**. Las variantes se informan **lado a lado** (elemento de paso A | B y driver A | B), y **no eliges ninguna**.

## 5. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:

1. `comun/dmm_comun_s11.inc`: subcircuitos del DMM con los valores del §1 parametrizados y las variantes elegibles por parámetro. Los envoltorios de los modelos llevan el orden de pines comprobado con un seguidor en continua.
2. `S11/` y `ejecutar_s11.py`:
   - 10 trabajadores, `--smoke` y **`--resume`**, que salta los casos con su CSV completo;
   - `S3G4_MODELS`, columnas fijas y los registros fuera de la carpeta vigilada;
   - Monte Carlo con puntos `.op`, tiempo límite y un reintento.
3. `resultados/s11_*.csv` y `resultados/s11_tabla_calibracion.csv` (función, rango, variante, ganancia, offset y no linealidad residual).
4. `ACTA_S11a.md`, con la tabla de criterios (variantes lado a lado), la fuga tolerable por rango y una lista de lo que se apoya en sustitutos o supuestos.
5. Tu diario en `ai-context/journal/`, abierto al empezar.

## 6. Lo que NO es tuyo

- No cambies valores fuera de lo que se barre.
- No elijas variante ni remedios, y no diseñes P42 (es S11b).
- No modifiques `../CH1_entrada/`, `../CH23_entrada/`, `Simulation_LTSpice/models/` (solo lectura), `STATE.md` ni `DECISIONS.md`.
- No descargues nada.

## 7. Cómo voy a auditar

1. Reejecución de `--smoke` en una ruta corta, comparando los CSV.
2. Netlists frente al §1 (valores, orden de pines de los envoltorios, variantes).
3. Que cada `.meas` lleva en su nombre el estado real: función, rango, variante, placa, temperatura y estado previo del ADC.
4. Que la calibración se hace a 23 °C y la evaluación a 18/28 °C con los coeficientes de esa placa.
5. Que la fuga y la Ib se inyectan donde dice K3, con su dependencia de la temperatura.
6. La temporización del muestreo (t_s, periodo de 5 µs) y los estados P, Z y R.
7. K0 frente a las hojas, dato por dato.
