# DMM bloque 2: frontal de tensión (estudio previo)

- Autor: Claude Code (ingeniero), 8 oct 2026. **Propone; no decide.** Elige Keneth.
- Alcance: de los nodos X0, X1, X2 (y X3 = COM) hasta la salida del amplificador A: divisor de 10 MΩ y su compensación, 74HC4051 de señal, OPA2188 A con ×1/×10 y autocero. El driver y el ADC5 son del bloque 5; la corriente, del 4; la fuente de ohmios, del 3 (aquí solo importa su tensión en vacío en X0).
- Fronteras del bloque 1 (cerrado): R_PROT 3 × 33 kΩ → BAV199 → 100 Ω → X0; divisor 3 × 3 MΩ ∥ (100 pF + 3.3 kΩ), 900 kΩ ∥ 330 pF, 100 kΩ ∥ 3.0 nF; 100 Ω y BAV199 en X1; nada en X2.
- Especificación (D5): DCV ±(0.1 % + 40) garantizado / ±(0.1 % + 10) calibrado; ACV 40 Hz–20 kHz ±(1 % + 40) / (1 % + 20); 23 ± 5 °C, un año, calibración por software al fabricar.
- Qué es esto: simulaciones pequeñas en LTspice (modelo TI del OPA2188, modelo Nexperia del BAV199), un modelo lineal en Python validado contra LTspice, y búsquedas en LCSC. **No hay hardware, no se descargó nada.** Las hojas de datos usadas son las del repositorio (`datasheet - componentes/opa2188.pdf`, `74HC_HCT4051.pdf`). Todo lo que depende de una pieza cuya hoja no tengo (TMUX4051, TMUX4053, OPA2192) lo marco **por confirmar**.
- Decks, scripts y salidas: `DMM/estudio_bloque2/` (`decks_ltspice/`, `scripts/`, `resultados/`). Cómo repetirlo: al final.

---

## 0. Lo esencial y tabla de decisiones

Seis hallazgos que cambian cosas respecto a la sección H:

1. **La planitud en alterna se corrige por firmware sin problema, con condiciones.** Con las capacidades reales del 4051 y del OPA2188 la caída a 20 kHz es −14.9 % en X0, −12.3 % en X1 y −5.0 % en X2 (H suponía −10 % en X0). En un Monte Carlo (C0G ±5 %, parásitas ±30 %, Ron ±30 %, ruido de calibración 0.05 %) el residuo tras la corrección de un cero y un polo (P39) queda en **p95 = 0.10 % (X0), 0.19 % (X1) y 0.18–0.22 % (X2)**, máximo 0.14 / 0.30 / 0.75 %. No hace falta cambiar hardware para cumplir < 0.5 %. Las condiciones: patrón de calibración con planitud relativa ≤ 0.05–0.1 % entre 1 kHz y 20 kHz (con 0.2 % el p95 pasa a 0.9 %), y una estrategia de ajuste que no deje el cero y el polo libres cuando la compensación está bien afinada (§3.3).
2. **El divisor de 9 MΩ en 1206 de 0.1 % no existe, pero no hace falta.** Seis resistencias de 1.5 MΩ de película delgada (0.1 %, 25 ppm/°C, Yageo `RT1206BRD071M5L`, C728673) dan **la misma deriva de relación que H** (225 ppm ÷10, 248 ppm ÷100 en el peor caso con ±5 °C), cuestan 0.50 USD y reparten mejor los pulsos (167 V por pieza con 1 kV, frente a 333 V con tres). La alternativa barata, 3 × 3.01 MΩ de película gruesa al 1 % (100 ppm/°C), gasta 562–585 ppm en el peor caso: cabe en el 0.1 % pero deja solo ≈ 590 ppm para el envejecimiento, y no conozco su coeficiente de tensión.
3. **El asiento del autocero es 2.8 ms en ÷10 y 1.4 ms en ÷100, no 0.8 ni 1 ms.** El divisor compensado tiene una constante de 300 µs: tras volver de X3 (0 V) la toma cae un 10 % por reparto de carga y tarda ≈ 9 constantes en volver a media cuenta. P38 debe esperar ≥ 3 ms en X1, ≥ 1.5 ms en X2 y ≈ 0.1 ms en X0.
4. **Con las puntas al aire en ohmios, X0 llega a ≈ 4.0 V** y el OPA2188 solo admite 3.4 V (V+ − 1.5 V). El modelo de TI se queda en 3.40 V en ×1 y satura a +4.78 V en ×10 (200 Ω); la lectura sale fuera de escala y se ve como OL. Hay tres salidas baratas (§4).
5. **La llave de ganancia en la rama de masa (H) sí mete su resistencia y su fuga en la señal.** Con Ron = 100 Ω la ganancia ×10 sale 9.991 (−0.09 %) y se mueve con la temperatura; y su fuga entra por Rf = 900 kΩ: **9 cuentas por nA en los rangos de 2 V, 20 V y 50 V**. Con la llave en el nudo inversor (escalera fija, un SPDT) la Ron no entra en la ganancia y la fuga solo pesa en 200 mV (§5).
6. **El presupuesto de fugas de H (≈ 1 nA) es el justo.** Con el 74HC4051 sin buffer, 1 nA de fuga son 10 cuentas en 200 mV y 9 en 20 V, y su deriva con +5 °C (+41 %) gasta 3–4 cuentas. La hoja solo garantiza ±100 nA por canal. Si el prototipo no demuestra < 0.7 nA, el plan B natural es un buffer RRIO (OPA2192) antes del mux en X0 y X1, que además arregla la planitud, el asiento y la fuga de golpe (§3.5, §6).

### Tabla de decisiones para Keneth

| # | Tema | Opciones (coste diferencial, número que cumple o no) | Recomendación |
|---|---|---|---|
| 1 | Resistencias del divisor | **A** H: 3 × 3 MΩ 0.1 % 1206: no existe. **B** 3 × 3.01 MΩ 1206 película gruesa 1 % (GiantOhm C49656332, 0.005 USD c/u) + 910 kΩ y 100 kΩ delgadas: 562 / 585 ppm; total 20 V = 807 ppm, margen 590 ppm; ≈ 0.15 USD. **C** 6 × 1.5 MΩ película delgada 0.1 % 25 ppm (C728673) + 910 kΩ (C870935) + 100 kΩ (C728669): 225 / 248 ppm; total 621 ppm, margen 784 ppm; ≈ 0.64 USD. **D** 9 × 1 MΩ (SIE `CRF1206Q1004BN` C55205340, 48 458 en stock): igual que C, ≈ 0.57 USD, más superficie | **C** (o D si el stock de C se queda corto). Las seis piezas van por parejas bajo los tres 100 pF existentes |
| 2 | Planitud en alterna | **A** H tal cual + P39: residuo p95 0.10–0.22 %, 0 USD. **B** retoque a 270 pF / 2.7 nF: 0 USD, la corrección baja de −12 % a ±5 %, sin mejorar el residuo. **C** mux con menos capacidad (TMUX4051 C5449352, +0.16 a +0.26 USD): X0 −4.7 % en vez de −14.9 % (por confirmar la hoja). **D** buffers OPA2192 antes del mux en X0 y X1 (+1.09 USD): X0 −1.3 %, la toma ÷10 con carga fija | **A** con la estrategia de ajuste de §3.3 y el patrón de §3.4. Guardar **D** como plan B (es la misma que resuelve fugas y asiento) |
| 3 | Modo común con puntas al aire | **A** H: OPA2188, OL por saturación (modelo: 3.40 V en ×1, 4.78 V en ×10), 0 USD. **B** centinela: leer X1 (÷10) antes de tocar X0 en ohmios, 0 USD, un canal más por lectura. **C** A = OPA2192 (C110074, 1.09 USD, −0.09 USD respecto al OPA2188): entrada hasta los rieles, Ib 5 pA. **D** sujeción de X0 a 2.9 V: toca el bloque 1; descartada | **C**, y **B** como red de seguridad mientras no se pruebe la pieza real. En todo caso el driver (bloque 5) tiene que aguantar la salida de A saturada |
| 4 | Ganancia ×1/×10 y asiento | **A** H: llave en Rg (4051 o similar): ×10 = 9.991, +900 µV/nA de fuga en ×1. **B** escalera fija 91 kΩ / 10 kΩ y un SPDT en el nudo inversor (TMUX4053, C5377936, 0.53 USD): Ron fuera de la ganancia; fuga 9 µV/nA solo en 200 mV. **C** dos amplificadores (quad OPA4188/OPA4192, 3.2 USD): descartada por precio. Asiento: P38 = 3 ms (X1), 1.5 ms (X2), 0.1 ms (X0) | **B** y P38 con los tiempos nuevos |
| 5 | Fugas e Ib | **A** 74HC4051 sin buffer: tolera 0.7–0.8 nA (200 mV y 20 V), 7 nA (2 V y 50 V) a 25 °C para ≤ 3 cuentas de deriva; la hoja garantiza ±100 nA. **B** TMUX4051 (fuga por confirmar). **C** buffers (opción 2D): la fuga se ve a través de ≈ 100 Ω; tolerancia > 100 nA. Ib: OPA2188 máx. 850 pA = 8 cuentas estáticas y 2.9 de deriva en 200 mV; OPA2192 (5 pA): < 0.1 | Medir la fuga en el prototipo (D4). Si < 0.7 nA a 25 °C, **A**; si no, **C**. Usar **74HCT4051** (C87239, 0.32 USD) si el control es un GPIO de 3.3 V (§6) |

Costes por opción completa (aproximados, en USD por unidad, sobre lo que H dejaba sin precio): mínima = divisor C (+0.62) + OPA2192 (−0.09) + SPDT TMUX4053 y escalera 91 kΩ/10 kΩ (+0.66) + HCT4051 (+0.11) ≈ **+1.3 USD**; robusta = mínima + OPA2192 de buffers (+1.09) ≈ **+2.4 USD**.

---

## 1. Base de cálculo y validación

### 1.1 Capacidades que cargan cada nodo

| Nodo | Elemento | Valor | Origen |
|---|---|---|---|
| Antes de los 100 Ω (X0) | BAV199 | 4 pF (2 × CJO 1.9 pF) | modelo Nexperia |
| | pata Yn del 74HC4051 | 5 pF | hoja Nexperia |
| | pista y pads | 3 pF | **supuesto** |
| Común (tras Ron + 100 Ω) | pata común Z | 25 pF | hoja Nexperia |
| | pista hasta la entrada de A | 3 pF | **supuesto** |
| | OPA2188, modo común | 9.5 pF por entrada; diferencial 6 pF | hoja y modelo TI |
| Total X0 | | 12 + 37.5 = **49.5 pF** | R = 99 kΩ + 100 Ω → polo en 32.4 kHz |

La sección H usa ≈ 40 pF (polo 40 kHz, −10 %). Con las cifras de hoja salen 49.5 pF y −14.9 %.

### 1.2 Validación del modelo lineal (Python) contra LTspice

`scripts/red.py` resuelve el divisor, las cargas y la ruta X0 por análisis nodal. Se comparó con LTspice usando el OPA2188 de TI (`decks_ltspice/x0_ac.cir`, `div_ac.cir`).

| Ruta / frecuencia | Python | LTspice con OPA2188 |
|---|---|---|
| X0, 20 kHz | −14.88 % | −14.83 % (−1.3949 dB) |
| X0, 10 kHz | −4.44 % | −4.42 % |
| X1, 20 kHz | −12.30 % | −12.31 % |
| X1, 1 kHz | −9.94 % | −10.0 % |
| X2, 20 kHz | −4.98 % | −4.98 % |

El amplificador casi no aporta: ×1 pierde 0.003 % a 20 kHz; ×10 (Rf/Rg = 9 k/1 k) pierde 0.44 % (−0.038 dB, polo de GBW/10 = 200 kHz), que se absorbe en la calibración por rango (`amp_ac.cir`).

---

## 2. Tema 1: resistencias del divisor

### 2.1 Qué hay en LCSC (película de 1206 salvo indicación; stock del 8 oct)

| Valor | Pieza | LCSC | Tipo / TC / tolerancia | Tensión | Stock | USD |
|---|---|---|---|---|---|---|
| 3 MΩ | FOJAN `FRH1206D3004TS` | C55348300 | gruesa, TC no declarado, 0.5 % | 200 V | 4 950 | 0.011 |
| 3 MΩ | FOJAN `FRC1206F3004TS` | C2930337 | gruesa, 100 ppm/°C, 1 % | 200 V | 237 202 | 0.007 |
| 3.01 MΩ | GiantOhm `GR1206F3M01T5G00` | C49656332 | gruesa, 100 ppm/°C, 1 % | 200 V | 11 000 | 0.005 |
| 1.5 MΩ | Yageo `RT1206BRD071M5L` | C728673 | **delgada, 25 ppm/°C, 0.1 %** | — | 1 402 | 0.084 |
| 2 MΩ | Viking `ARG06BTC2004` | C2828885 | delgada, 25 ppm/°C, 0.1 % | 200 V | 1 423 | 0.058 |
| 1 MΩ | SIE `CRF1206Q1004BN` | C55205340 | delgada, 25 ppm/°C, 0.1 % | 200 V | 48 458 | 0.049 |
| 1 MΩ | Viking `ARG06BTC1004` | C2984499 | delgada, 25 ppm/°C, 0.1 % | 200 V | 18 900 | 0.061 |
| 910 kΩ | Yageo `RT1206BRD07910KL` | C870935 | delgada, 25 ppm/°C, 0.1 % | 200 V | 3 576 | 0.057 |
| 100 kΩ | Yageo `RT1206BRD07100KL` | C728669 | delgada, 25 ppm/°C, 0.1 % | 200 V | 49 670 | 0.075 |

No hay 3 MΩ de película delgada en 1206 (ni 1.8 MΩ al 0.1 %). Redes de resistencias: la única de ≥ 100 kΩ al 0.1 % con 25 ppm (Vishay `ACASA1003S1003P1AT`, 4 × 100 kΩ) tiene 30 unidades y llega a 100 kΩ, no a megaohmios. No encontré MELF de alto valor en la base. Una sola pieza de 9.1 MΩ (FOJAN 0805 0.1 %, 150 V) está descartada: con la red vería 325 V.

El 910 kΩ y el 1.5 MΩ no son los valores de H (900 kΩ, 3 MΩ). Da igual: la relación se calibra al fabricar y la ganancia nominal se corre menos de un 1 %.

### 2.2 Deriva de la relación con ±5 °C

La tolerancia inicial se calibra. Lo que importa es el **coeficiente relativo** entre la parte alta y la baja. Sensibilidad de la relación: ÷10 = 0.9 × (TC_baja − TC_alta); ÷100 ≈ TC_R3 − media ponderada. Peor caso = cada grupo en su límite (signos enumerados); σ = uniformes independientes (la parte alta de n piezas promedia √n). `scripts/calc_b2.py`.

| Opción | ÷10 peor / σ | ÷100 peor / σ | Total 20 V peor* | Margen para envejecimiento* | USD |
|---|---|---|---|---|---|
| H (si existiera): 3 × 3 MΩ, 25 ppm | 225 / 70 ppm | 248 / 81 | 621 ppm | 784 ppm | — |
| B: 3 × 3.01 MΩ gruesa 1 %, 100 ppm; R2, R3 delgadas | 562 / 161 | 585 / 166 | 807 ppm | 591 ppm | 0.15 |
| B': todo película gruesa de 100 ppm | 900 / 279 | 990 / 324 | 1 070 ppm | 0 | 0.03 |
| **C**: 6 × 1.5 MΩ delgada 25 ppm | 225 / 65 | 248 / 76 | 621 ppm | 784 ppm | 0.64 |
| **D**: 9 × 1 MΩ delgada 25 ppm | 225 / 63 | 248 / 75 | 621 ppm | 784 ppm | 0.57 |

\* Suma cuadrática con REF3325 (150 ppm), driver (250), patrón de calibración (500, supuesto de H) y el divisor de cada fila. «Margen» = √(1000² − total²), lo que queda del 0.1 % para la deriva de un año del resto (REF, ganancia del ADC5, envejecimiento de las resistencias). H deja ≈ 780 ppm.

Conclusión: la deriva de **temperatura** de C y D es la de H. La opción B cabe en el 0.1 % pero consume la mitad del margen, y todo-grueso (B') no cabe.

### 2.3 Lo que no está en los datos de LCSC

- **Coeficiente de tensión (VCR).** No consta en el listado. Película delgada: despreciable (< 1 ppm/V, conocimiento general, a confirmar en la hoja de Yageo). Película gruesa de alto valor: suele ser decenas de ppm/V. Con 20 ppm/V (supuesto), cada 3 MΩ a 50 V de entrada ve 15 V → 300 ppm de variación de R, ≈ 270 ppm en la relación; la calibración multipunto absorbe una parte (un residuo en arco de ≈ ¼, ≈ 70 ppm). Con 100 ppm/V sería inaceptable. Es un riesgo de la opción B que C y D no tienen.
- **Envejecimiento a un año.** Supuesto de ingeniería, no de hoja: ≲ 100 ppm para película delgada con 1 mW de disipación, varios cientos de ppm para película gruesa. Lo comprueba el ensayo de estabilidad (P37).
- **Fugas superficiales.** Un nodo de 900 kΩ con 10 nA de fuga de placa pesa 9 mV; la guarda y el barniz son del layout (bloque de montaje), no del esquema.

### 2.4 Tensión, potencia y pulso con las opciones C y D

| Piezas arriba | Vpk con 230 Vrms | V por pieza con un pulso de 1 kV (reparto capacitivo igual) | Potencia por pieza (230 Vrms) |
|---|---|---|---|
| 3 | 108 V | 333 V | 1.8 mW |
| 6 | 54 V | **167 V** | 0.9 mW |
| 9 | 36 V | 111 V | 0.6 mW |

Con seis piezas un pulso de 1 kV (el impulso de cebado del GDT) deja a cada 1206 por debajo de su tensión de trabajo de 200 V; con tres, el pico de 333 V solo cabe en la tensión de sobrecarga (típicamente 400 V). La condición de «antipulso ≥ 1.5 kV» que pedía el bloque 1 para el 3 MΩ desaparece: cada pieza es de 1.5 MΩ y solo ve una fracción. La compensación no cambia: cada pareja de 1.5 MΩ en serie lleva los 100 pF + 3.3 kΩ que el bloque 1 ya puso en cada 3 MΩ.

---

## 3. Tema 2: planitud en alterna de 40 Hz a 20 kHz

### 3.1 Respuesta sin corregir, por rango (modelo lineal con las capacidades de §1.1)

| f | X0 (200 mV y 2 V) | X1 (20 V) | X2 (50 V) |
|---|---|---|---|
| 40 Hz | −0.00 % | −0.08 % | −0.03 % |
| 100 Hz | −0.00 % | −0.51 % | −0.18 % |
| 300 Hz | −0.00 % | −3.4 % | −1.2 % |
| 1 kHz | −0.05 % | −9.9 % | −3.9 % |
| 3 kHz | −0.42 % | −11.9 % | −4.8 % |
| 10 kHz | −4.4 % | −12.2 % | −4.9 % |
| 20 kHz | **−14.9 %** | **−12.3 %** | **−5.0 %** |

Dos comportamientos distintos:
- **X0** es un polo simple en 32 kHz (R_PROT + 49.5 pF). La corrección es la inversa de ese polo.
- **X1 y X2** son un escalón con el codo en ≈ 530 Hz (constante del divisor, 300 µs), **dentro de la banda de alterna**. El divisor mantiene su compensación para la capacidad sin carga; el mux y el amplificador añaden 50 pF a la toma ÷10, y los 330 pF quedan descompensados: ∆ = 13 % en alta frecuencia. El 1 kHz de la calibración ya está en la subida.

### 3.2 Capacidad no lineal del 4051

Se simuló (`x0_tran.cir`) el camino X0 con 2 Vpk (fondo de 2 V), el BAV199 real y capacidades que varían con la tensión, C(v) = C0 (1 + b·v) en la pata Y y en el común. b = 0.1/V significa ±20 % sobre ±2 V.

| b | THD a 20 kHz | RMS a 20 kHz | THD a 1 kHz | RMS a 1 kHz |
|---|---|---|---|---|
| 0 | 0 % | 1.21635 V | 0 % | 1.41349 V |
| 0.05 | 1.0 % | +0.003 % | 0.09 % | −0.00004 % |
| 0.1 | 2.1 % | **+0.012 %** | 0.18 % | −0.0002 % |
| 0.2 | 4.2 % | **+0.049 %** | 0.37 % | −0.0007 % |

La no linealidad produce distorsión (armónicos), pero el valor eficaz casi no se mueve porque el efecto es simétrico: ≤ 0.05 % aun con ±40 %. El BAV199 compensa en parte: sus dos diodos varían en sentidos opuestos. Para el TRMS del DMM no es un problema. Para un voltímetro que midiera solo la fundamental, sí (el pico sube/baja ±1.5 %).

### 3.3 Monte Carlo del residuo tras la corrección por firmware

Condiciones (`scripts/mc2.py`, `mc3.py`, N = 800 unidades por caso): C0G de 100 pF (tres en serie) y de C2, C3 con ±5 %; resistencias ±0.1 %; R_PROT ±1 %; cada capacidad parásita ±30 %; Ron ±30 %; OPA2188 ±15 %; **ruido en cada punto de calibración 0.05 %** (σ). Referencia de continua conocida. Modelo del firmware: |(1 + jf/f_cero)/(1 + jf/f_polo)|. Se evalúa el error máximo en 33 frecuencias de 40 Hz a 20 kHz.

Residuo (máximo en banda por unidad; se da p95 y el peor de las 800):

| Ruta | Hardware | Calibración y ajuste | p95 | Máx. |
|---|---|---|---|---|
| X0 | H (74HC4051 + OPA2188) | 1 y 20 kHz, polo libre | **0.10 %** | 0.14 % |
| X1 | H (330 pF / 3.0 nF) | 1 y 20 kHz, cero y polo libres | 0.19 % | 0.30 % |
| X1 | H | 1 y 20 kHz, cero fijo, polo libre | 0.19 % | 0.35 % |
| X1 | H | 100 Hz, 1 y 20 kHz, cero y polo libres | 0.19 % | 0.34 % |
| X2 | H | 1 y 20 kHz, cero y polo libres | 0.18 % | 0.75 % |
| X2 | H | 1 y 20 kHz, cero fijo | 0.22 % | 0.42 % |
| X2 | H | 100 Hz, 1 y 20 kHz, cero y polo libres | 0.17 % | 0.30 % |
| X1 | retoque 270 pF / 2.7 nF | 1 y 20 kHz, cero y polo libres | 0.19 % | 0.82 % |
| X1 | retoque | 1 y 20 kHz, cero fijo | 0.12 % | 0.17 % |
| X2 | retoque | 1 y 20 kHz, cero y polo libres | **1.34 %** | 2.26 % |
| X2 | retoque | 1 y 20 kHz, cero fijo | 0.54 % | 0.64 % |
| X2 | retoque | 100 Hz, 1 y 20 kHz, cero y polo libres | 0.34 % | 0.51 % |

La dispersión que corrige el firmware, sin corregir a 20 kHz (2.5–97.5 %): X0 −18.6…−11.2 %; X1 −16.6…−7.4 %; X2 −10.8…+0.9 %.

Lectura:
- **H tal cual cumple** < 0.5 % en p95 en las tres rutas, con cualquier modo de ajuste.
- Cuando la compensación está **bien afinada** (retoque), el desvío en alta frecuencia casi se anula y el par cero/polo queda mal condicionado: con ambos libres, X2 sube a 1.3 %. Con el cero fijo en el valor de diseño y solo el polo libre baja a 0.5 %; con tres puntos (100 Hz, 1 kHz, 20 kHz) a 0.34 %. Por eso el retoque **no mejora el residuo**; solo reduce el tamaño de la corrección.
- Recomendación de firmware para P39: cero fijo (viene de R_alta·C_alta, ±3 %), polo y ganancia por rango, tres puntos de calibración. Cuesta una frecuencia más en la calibración de fábrica.

Sensibilidad al patrón (X1 retoque, ajuste libre):

| Ruido relativo en cada punto de calibración | p95 | Máx. |
|---|---|---|
| 0 % | 0.06 % | 0.13 % |
| 0.05 % | 0.20 % | 0.55 % |
| 0.1 % | 0.39 % | 1.05 % |
| 0.2 % | 0.89 % | 2.05 % |

Para que el residuo quede < 0.5 % hace falta que el patrón de 1 y 20 kHz sea plano entre sí a ≈ 0.05–0.1 %. Un generador de funciones corriente (1 %) no vale; un multímetro de 6½ dígitos o un calibrador sí (comprobar su hoja a 20 kHz).

### 3.4 Qué mueve el 20 kHz después de calibrar

Sensibilidad de la lectura a 20 kHz a una capacidad extra en el nodo (sin recalibrar):

| Camino | Por pF |
|---|---|
| X0, H (74HC4051 + OPA2188, 49.5 pF) | −0.47 % |
| X0, con TMUX4051 (≈ 25.5 pF, por confirmar) | −0.35 % |
| X0, con buffer (12–13 pF) | −0.19 % |
| X1 (÷10, con la carga de §1.1) | −0.23 % |
| X2 (÷100) | −0.31 % |

Humedad, residuos de flux o la deriva térmica de la capacidad del 4051 (junturas de silicio; el coeficiente no está en la hoja) mueven el 20 kHz de X0 unos 0.1–0.5 % por ±0.2–1 pF. Está dentro del 1 % del ACV, pero ocupa parte del residuo. Con el buffer (0.19 %/pF) o con un mux de menos capacidad (0.35 %/pF) ese consumo baja a la mitad o a un tercio.

### 3.5 Opciones de hardware para X0 (si se quiere menos corrección)

| Opción | C total en X0 | Caída a 20 kHz | USD |
|---|---|---|---|
| **A** H (74HC4051, OPA2188) | 49.5 pF | −14.9 % | 0 |
| **B** TMUX4051 (`Con` = 3 pF según LCSC; supuesto Z = 3, Yn = 3) | ≈ 25.5 pF | −4.7 % | +0.16…0.26 |
| **B2** TMUX4051 con Con = 11 pF (versión SOT-23, DYY) | ≈ 33.5 pF | −7.7 % | +0.2 |
| **C** buffer OPA2192 antes del mux (Cin ≈ 6 pF, supuesto) | 13 pF | −1.3 % | +1.09 |

R_PROT no se puede bajar (protección); un condensador en paralelo con R_PROT no ayuda (el nodo no tiene camino de continua hacia abajo, solo añade un cero y baja la ganancia de alta frecuencia). La opción C también cambia el divisor: la toma ÷10 pasa a tener siempre la misma carga (BAV199 + buffer, ≈ 13 pF), con lo que la compensación se puede afinar de una vez (óptimo con buffer en X0 y X1: C2 = 313 pF y C3 = 2.77 nF; con piezas estándar el desvío queda en ±4 %, que se corrige igual).

### 3.6 Retoque gratuito de C2 y C3

Para anular el escalón con las capacidades de §1.1 los óptimos son C2 = 269 pF y C3 = 2.73 nF. Los valores estándar **270 pF y 2.7 nF** dejan −0.1 % (÷10) y +0.9 % (÷100) con las cargas nominales. Con C0G ±5 % el desvío es −3.6…+7.1 % (÷10) y −3.4…+8.3 % (÷100); con ±1 % en C2 y C3, −2.6…+5.2 % (÷10). Piezas con ±1 % en LCSC: 270 pF CCTC `TCC0402COG271F500AT` (C50767321, 0.002 USD, 6 430 en stock) y 2.7 nF Murata `GRM1885C1H272FA01D` (C1625600, 0.072 USD, 1 875 en stock, 0603, 50 V). La tensión no es problema: la toma está sujeta a ±5 V por el BAV199.

No es necesario: H tal cual ya cumple. Es una mejora para reducir el tamaño de la corrección y es independiente de las demás. **Mi recomendación:** montar con 330 pF / 3.0 nF (como en bloque 1), medir en el prototipo el desvío real a 20 kHz, y pasar a 270 pF / 2.7 nF solo si la capacidad medida es la estimada (≈ 50 pF). Los dos valores caben en la misma huella (0603 o 0805).

---

## 4. Tema 3: modo común del OPA2188 en ohmios con las puntas al aire

### 4.1 Qué llega a X0

Con la fuente de ohmios sin carga, X0 queda a la **compliancia de la fuente**: ≈ 4.0 V (REDISENO_BLOQUE1 usa 4.1 V; 4.9 V − 0.5 V del sensor − 0.2 V del PNP − la caída del BAT54 a corriente casi nula). Por R_PROT no pasa corriente, así que X0 = ese valor, y la sujeción de BAV199 a +4.9 V no conduce (queda 0.9 V en inversa). Esto ocurre en 200 Ω … 2 MΩ. En 20 MΩ (0.2 µA) la fuente cae al divisor de 10 MΩ: 2.0 V, dentro del rango.

La hoja del OPA2188 da para el modo común «(V−) a (V+) − 1.5 V»: con V+ = 4.9 V, **3.4 V**. Hay 0.6 V de exceso.

### 4.2 Qué hace el modelo de TI (`cm_dc.cir`, rieles ±4.9 V, R_PROT 99 kΩ en serie)

| V en X0 | Salida en ×1 | Salida en ×10 |
|---|---|---|
| 2.0 V | 2.000 V | 4.78 V (satura desde 0.48 V) |
| 3.0 V | 3.000 V | 4.78 V |
| 3.4 V | 3.400 V | 4.78 V |
| 4.0 V | **3.400 V** (clavada) | 4.78 V |
| 4.5 V | 3.400 V | 4.78 V |

La corriente de polarización sube a 6 nA con 4 V (en vez de 0.17 nA a 3 V), irrelevante porque la lectura ya es OL. La hoja lista «No Phase Reversal»: no hay inversión de fase. **El modelo es una sujeción simple, no el silicio.** Lo que no sé es cómo se recupera la pieza real al volver de 4 V a 0.1 V (la hoja da 1 µs de recuperación de sobrecarga de salida, no de modo común).

### 4.3 Opciones

| Opción | Qué hace | Coste | Número |
|---|---|---|---|
| **A** H sin cambios | A satura y la lectura sale fuera de escala → OL | 0 | ×1: 3.40 V; ×10: +4.78 V. Falta que el driver de 3.3 V (bloque 5) aguante 4.78 V en la entrada: lo que sale con PD13 = 1.25 V + v/2 = 3.6 V |
| **B** Centinela por X1 | En ohmios, antes de leer X0, el firmware lee X1 (÷10): si V/Ω ÷ 10 > 0.21 V, declara OL sin tocar X0 | 0 | +1 lectura por medida de ohmios. Con 4.0 V, X1 da 0.40 V |
| **C** A = OPA2192 (C110074, SOIC-8, 35 409 en stock) | Entrada hasta los rieles (RRIO) y Ib de 5 pA | −0.09 USD (1.09 frente a 1.18) | Vos 5 µV típ., deriva 0.2 µV/°C; GBW 10 MHz. Cubre el modo común y baja Ib de 8 a < 0.1 cuentas (§7) |
| **D** Sujeción a ≈ 2.9 V en X0 | Diodo de X0 a un riel de 2.5 V | 0 | Cambia el bloque 1 (cerrado) y mete corriente en VREF: descartada |

Notas sobre C:
- LCSC etiqueta el OPA2192 como «cero deriva», pero su deriva de 0.2 µV/°C indica que no es de chopper. Para el DMM da igual: el autocero (X3) resta el offset y su deriva en cada lectura.
- **No tengo su hoja ni su modelo SPICE en el repositorio.** El máximo de Ib, la curva Vos–Vcm, la capacidad de entrada y si tiene cruce de pares de entrada hay que leerlos en la hoja de TI. Si el cruce cae en el rango de uso (≈ V+ − 1.4 V = 3.5 V, fuera de los ±2 V normales), no importa en 2 V, pero sí en la zona de vacío.
- Si A pasa a OPA2192, su gemelo B (derivador, bloque 4) viene en el mismo encapsulado. El bloque 4 decide si lo deja como OPA2188 en otro encapsulado (el OPA2188 ya no se compartiría) o si usa también el OPA2192 (deriva de 1 µV con 5 °C, 1 cuenta de 10 µA en 200 mA).

**Mi recomendación:** C como pieza de A y B (centinela) como red de seguridad en el firmware mientras la OPA2192 real no se pruebe con puntas al aire. En todo caso, el bloque 5 debe dejar el driver tolerante a una entrada de +4.8 V.

---

## 5. Tema 4: ganancia ×1/×10 y asiento del autocero

### 5.1 Dónde poner la llave

Simulado con el OPA2188 (`scripts/gen_gain.py`): Ron = 100 Ω; fuga de 1 nA; la entrada A a 1 V (×1) o 0.2 V (×10).

| Montaje | Ganancia ×10 | Efecto de 1 nA de fuga de la llave | Dónde pesa |
|---|---|---|---|
| **H**: llave en serie con Rg (rama de masa); Rf = 900 kΩ, Rg = 100 kΩ | **9.991** (Ron entra: −0.09 %) | +900 µV a la salida en ×1 (= 9 cuentas) | **2 V, 20 V, 50 V** (los rangos en ×1). En ×10 la llave cerrada no sufre |
| **S**: escalera Rf/Rg fija en la salida; SPDT en el nudo inversor (COM → ×1 salida de A / ×10 toma de la escalera) | **10.000** (Ron solo ve Ib) | +901 µV a la salida en ×10 con 900 kΩ / 100 kΩ (9 cuentas); **+91 µV con 90 kΩ / 10 kΩ** (0.9 cuenta); 0 en ×1 | solo **200 mV** (y 200 mA del bloque 4) |

Cuentas «por nA» tomadas en la salida de A: en el montaje H un nA de fuga en ×1 son 0.9 mV a la salida, es decir 9 cuentas en cualquiera de los tres rangos que van en ×1. Detalle de la tempco de Ron en H: el CMOS sube ≈ 0.3–0.5 %/°C; con ±5 °C y Rg = 100 kΩ son ≈ 15–20 ppm; con Rg = 10 kΩ serían 180 ppm, que gastan casi todo el término de ganancia (250 ppm). Por eso H necesita Rg grande y la fuga se paga cara. El montaje S desacopla las dos cosas.

Con S:
- La escalera de 91 kΩ + 10 kΩ (E24; ganancia 10.1, calibrada) cuesta ≈ 0.13 USD y carga la salida de A con 20 µA a 2 V (despreciable).
- El SPDT es una sección de un **TMUX4053** (TI, ±12 V / 5–24 V, tres SPDT; LCSC C5377936 TSSOP-16 0.53 USD, 2 379 unidades; o C22388988 SOT-23-THIN-16 0.44 USD, 3 839 unidades). Las otras dos secciones sirven al bloque 4. **Por confirmar** su fuga y su inyección de carga en la hoja (en LCSC: Con 5 pF, 6 pC en la versión DYY).
- Deriva de la ganancia: Rf y Rg de película delgada 25 ppm, peor caso 0.9 × 50 ppm × 5 °C = 225 ppm (H pone 250).
- Al conmutar ×1↔×10 solo se cambia de rango, no en cada lectura; el nudo inversor se estabiliza en microsegundos.

### 5.2 Asiento del autocero (P38)

Simulado (`gen_settle.py`, decks `st_*.cir`): tras leer X3 (COM a 0 V), la llave conecta la toma con 37.5 pF en COM; se mide cuánto tarda la tensión de COM en llegar a **media cuenta** de su valor final (5 µV en X0 de 200 mV, 50 µV en X1 y X2). La inyección de carga del 4051 no está en su hoja: se probó con 0 y con 5 pC (supuesto; el TMUX4051 dice 2 pC en LCSC).

| Ruta | Caída inicial | Constante | Tiempo a media cuenta, H (330 pF / 3.0 nF) | Con 5 pC | Con 270 pF / 2.7 nF |
|---|---|---|---|---|---|
| X0 (200 mV) | −18 % (de 0.2 V a 0.164 V) | ≈ 5 µs | **0.05 ms** | 0.04 ms | — |
| X1 (÷10, 20 V → 2 V) | −10 % | ≈ 300 µs | **2.84 ms** | 2.81 ms | 2.50 ms |
| X2 (÷100, 50 V → 0.5 V) | −0.9 % | ≈ 300 µs | **1.47 ms** | 1.36 ms | 1.35 ms |

(La caída de X1 y X2 se lee a 0.5 µs de cerrar la llave.) El tiempo es el mismo con inyección de carga o sin ella: lo manda la constante del divisor compensado, que es la de la compensación (300 µs, la misma en la toma ÷10 y en la ÷100). H calcula 0.8 ms y fija ≈ 1 ms; con 1 ms quedarían ≈ 100 cuentas sin asentar en X1 (10.8 mV en la toma de un 0.1 mV por cuenta) y ≈ 2 en X2. La constante efectiva medida es 340 µs en ÷10 y ≈ 300 µs en ÷100.

Recomendación para P38: **esperar ≥ 3 ms (X1), ≥ 1.5 ms (X2), ≥ 0.1 ms (X0)** tras cada conmutación del mux. Con integración de 100 ms (6 ciclos de 60 Hz) la espera es del 3 %. Si el autocero se hace en cada lectura, el tiempo de espera se paga dos veces (al entrar en X3 y al volver): se puede ir a un autocero cada 1–2 s y fijar la toma entre medias. Con **buffers antes del mux** (§3.5/§6) el asiento pasa a microsegundos: la llave conmuta salidas de baja impedancia y el divisor ve siempre la misma carga.

---

## 6. Tema 5: fugas e Ib

### 6.1 Cuentas por nA de corriente de fuga o de polarización

La corriente que sale del nodo de señal produce un error igual a I × la resistencia de fuente que ve el nodo.

| Rango | Ruta | R vista | Cuenta | Cuentas por nA |
|---|---|---|---|---|
| 200 mV | X0, A ×10 | 99.1 kΩ | 10 µV | **9.9** |
| 2 V | X0, A ×1 | 99.1 kΩ | 100 µV | 1.0 |
| 20 V | X1 (÷10), A ×1 | 900 kΩ | 1 mV | **9.0** |
| 50 V | X2 (÷100), A ×1 | 99 kΩ | 10 mV | 1.0 |

La fuga del 4051 (y del BAV199) se duplica cada 10 °C: **+41 % con +5 °C y −29 % con −5 °C**. La Ib del OPA2188 sube de 160 pA a 25 °C a 18 nA a 105 °C (hoja): se duplica cada 11.8 °C, +34 % con +5 °C.

### 6.2 Fuga tolerable a 25 °C para que su deriva (+5 °C) cueste ≤ 3 cuentas

| Rango | Fuga máxima a 25 °C (≤ 3 cuentas) | (≤ 2 cuentas) |
|---|---|---|
| 200 mV | **0.73 nA** | 0.49 nA |
| 2 V | 7.3 nA | 4.9 nA |
| 20 V | **0.80 nA** | 0.54 nA |
| 50 V | 7.3 nA | 4.9 nA |

Es el criterio de H («≈ 1 nA», D4), con un poco menos de margen: 3 cuentas es la deriva de fuga que H admite (≈ 4 en su tabla de §8). Aviso sobre ese presupuesto: la especificación calibrada es ±(0.1 % + 10) y H ya gasta ≈ 10 cuentas en la INL del ADC5 tras la linealización; en suma cuadrática, 4 cuentas de deriva más Ib suben el total a ≈ 11. Cabe «≈ 10» solo si la INL real queda en 9 o menos. Si no, el término de cuentas no se garantiza ±10 y hay que vigilar la deriva de la fuga.

Lo que dice la hoja del 74HC4051: **±100 nA por canal y ±0.4 µA en todos los canales** a 25 °C con 10 V de excursión (`74HC_HCT4051.pdf`). No hay un valor típico garantizado. Con ese máximo el error sería 990 cuentas en 200 mV. Lo típico es de pA a nA (medible en el prototipo). Conclusión: **no se puede garantizar por hoja; hay que medirlo**, como ya dice D4.

### 6.3 Ib del amplificador

Con 99 kΩ en X0 y 900 kΩ en X1:

| Rango | OPA2188 típ. 160 pA: estático / deriva | OPA2188 máx. 850 pA: estático / deriva | OPA2192 (5 pA típ., LCSC): estático / deriva |
|---|---|---|---|
| 200 mV | 1.6 / 0.5 cuentas | 8.4 / **2.9** | 0.05 / 0.02 |
| 2 V | 0.2 / 0.05 | 0.8 / 0.3 | 0.00 |
| 20 V | 1.4 / 0.5 | 7.6 / **2.6** | 0.04 / 0.015 |
| 50 V | 0.2 / 0.05 | 0.8 / 0.3 | 0.00 |

El estático se calibra; la deriva es la que cuenta. Con el máximo garantizado la deriva de Ib sola (2.9) consume el presupuesto de ≈ 3 cuentas; por eso H necesitaba la fuga en ≈ 1 nA **y** una Ib típica. Con el OPA2192 desaparece (máximo por confirmar).

### 6.4 Opciones

| Opción | Efecto | Coste |
|---|---|---|
| **A** 74HC4051 sin buffer | tolera 0.7–0.8 nA en 200 mV y 20 V | 0.31 USD (C5645) |
| **B** TMUX4051 (C5449352, TI) | inyección de carga 2 pC, `Con` 3 pF; fuga **por confirmar** | 0.47 USD |
| **C** OPA2192 de buffer en X0 y X1 antes del mux | la fuga se ve a través de la impedancia de salida del buffer (< 1 Ω) más Ron: > 100 nA tolerables. Ib 5 pA. X0 −1.3 % en alterna; asiento de microsegundos. Entrada RRIO | +1.09 USD (un OPA2192 para dos buffers) |

Con la opción C, la fuga de los canales sin seleccionar sigue entrando en COM, pero COM está alimentado por la salida de un buffer: un nA × 100 Ω = 0.1 µV. En X2 (sin buffer, 99 kΩ) pesa 1 cuenta por nA, tolerable hasta 7 nA.

### 6.5 Hallazgo de nivel lógico del 4051

La hoja del 74HC4051 da V_IH mínimo = 3.15 V con VCC = 4.5 V y 4.2 V con VCC = 6 V: con VCC = 4.9 V el mínimo es **≈ 3.4 V**, y un GPIO de 3.3 V no lo garantiza. Si el control no pasa por un 74HCT595 alimentado a 4.9 V, hay que usar el **74HCT4051** (V_IH = 2.0 V; C87239, 0.32 USD, 2 796 unidades; misma Ron y capacidad). Además VCC − VEE = 9.8 V frente a un máximo recomendado de 10 V (absoluto 11 V): poco margen si el riel sube a ±5.1 V.

---

## 7. Hallazgos que no son de este bloque

1. **Bloque 3 / 1: corriente real de la fuente de ohmios.** El camino de ohmios del bloque 1 lleva en serie 2 × 1.1 kΩ + R_S 2.7 kΩ = 4.9 kΩ (más el BAT54). Con una compliancia de 4.0–4.1 V, 1 mA es inalcanzable: a 1 mA caerían 4.9 V solo en esas resistencias. REDISENO_BLOQUE1 §3.3 lo recoge solo para la prueba de diodo (O4: «n.a.» a 1 mA, 0.60 mA con un diodo de silicio); no encuentro que se haya trasladado a los rangos de 200 Ω y 2 kΩ de H §6 (1 mA) ni a la tensión disponible en V_x. Si la fuente de P43 se queda sin compliancia, la corriente real cae y la lectura de ohmios ya no corresponde a la corriente calibrada. Hay que verificarlo en el bloque 3 con el esquema real (¿la fuerza pasa por las resistencias de protección, o la medida es por cuatro hilos?).
2. **Bloque 5.** A en ×10 con las puntas al aire en 200 Ω satura a +4.78 V; el driver de 3.3 V tiene que tolerarlo (resistencia en serie y sujeción) o el firmware usar el centinela.
3. **Control del mux.** HC o HCT (§6.5).
4. **Sección H.** (a) «6 µV de offset como máximo»: la hoja da 6 µV típico y 25 µV máximo (0.03 µV/°C típico, 0.085 máximo); no cambia nada porque el autocero lo resta. (b) «0.8 ms» de asiento y «≈ 1 ms» de espera: son 2.8 ms (§5.2). (c) La llave de ganancia «colocada de forma que su resistencia no entre en la ganancia» no se cumple en la rama de masa (§5.1).

---

## 8. Qué tendría que confirmar la campaña de Codex

Todo con el criterio de ≥ 95 % de placas y los decks de `estudio_bloque2/` como punto de partida.

| # | Qué | Cómo | Criterio |
|---|---|---|---|
| C1 | Planitud en alterna con el OPA2188 de TI en las tres rutas, ×1 y ×10, con el 74HC4051 como carga y las capacidades de §1.1 | Repetir el Monte Carlo de §3.3 con la red completa en LTspice (no el modelo lineal), 40 Hz–20 kHz, para 330 pF/3.0 nF y 270 pF/2.7 nF; con ruido de calibración 0.05 % y 0.1 %; ajuste de cero fijo y 3 puntos | Residuo p95 < 0.5 % |
| C2 | Sensibilidad a la capacidad parásita | Barrer la carga del nodo X1 ±20 pF, X0 ±10 pF | Residuo y correccion máxima |
| C3 | Qué capacidad en función de la tensión implica el modelo HC4051 de NXP (solo transitorio) | Escalón de corriente en COM, medir C(v) entre ±2 V; compararla con el b = 0.1–0.2 de §3.2 | THD y RMS a 20 kHz |
| C4 | Asiento del autocero con el modelo HC4051, sin y con buffer | X3 → X0, X1, X2 con el sistema completo y OPA2188 (no solo los pasivos) | Tiempo a media cuenta de cada rango |
| C5 | Modo común con puntas al aire | Barrido 0–4.5 V en ×1 y ×10 y salto 4.0 V → 0.1 V con el OPA2188; repetir con el modelo del OPA2192 (**lo tiene que descargar Keneth**) | Tiempo de recuperación a media cuenta; la salida nunca engaña con un valor válido |
| C6 | Montaje de ganancia S (escalera fija + SPDT) | Transitorio ×1 ↔ ×10 y estabilidad con el OPA2188 y con Ron de 100 Ω en el nudo inversor; modelo del TMUX4053 si existe, si no Ron y fuga paramétricas | Recuperación a media cuenta de 200 mV; margen de fase > 45° |
| C7 | Divisor con 6 × 1.5 MΩ en la campaña del bloque 1 (S11.4) | ESD y red 230/253 Vrms con las seis piezas y las tres parejas con 100 pF + 3.3 kΩ | V por pieza ≤ 80 % de 200 V en régimen; pulso ≤ tensión de sobrecarga |
| C8 | Presupuesto de continua con el divisor nuevo | Monte Carlo del §8 de H con R de película delgada, Ib máx. y fuga de 0.1–10 nA (barrido) y T ±5 °C | Cuentas y ppm ≤ garantizado; fuga máxima que cumple |
| C9 | Ruido | Densidad de ruido y valor eficaz en 200 mV con 99 kΩ en serie (≈ 40 nV/√Hz) y en 20 V con 900 kΩ (≈ 120 nV/√Hz) | < 1 cuenta en 100 ms |

En el prototipo (no en simulación):
1. Medir la fuga del 74HC4051 (o TMUX4051) en X0 y X1 a 23 °C y a +5 °C; **decide entre la opción 5A y 5C**.
2. Medir la capacidad real de cada toma con un barrido a 20 kHz en bornes abiertos.
3. Medir el patrón de calibración: planitud de 1 a 20 kHz con el multímetro o el calibrador disponible (≤ 0.05–0.1 %).
4. Tensión en X0 con las puntas al aire y comportamiento real del OPA2188 u OPA2192.

---

## 9. Límites del estudio

- Las capacidades de pista y pads (3 pF), la inyección de carga del 4051 (5 pC), la capacidad no lineal (b) y el VCR/envejecimiento de las resistencias son **supuestos**, marcados donde aparecen.
- No he leído hojas de TMUX4051, TMUX4053 ni OPA2192 (no están en el repositorio y no se descarga nada). De ellas solo uso lo que LCSC publica.
- El modelo de TI del OPA2188 incluye un limitador de modo común, pero no necesariamente el comportamiento del silicio fuera de rango.
- El 74HC4051 de NXP solo sirve para transitorios; no incluye fuga ni capacidad no lineal fiables.
- El Monte Carlo usa el modelo lineal validado (error < 0.1 punto frente a LTspice en el nominal); las simulaciones de LTspice son del caso nominal y del caso no lineal.
- Nada de esto cambia STATE.md, DECISIONS.md, 01_diseno, modelos ni hojas.

## 10. Cómo repetir

Desde `DMM/estudio_bloque2/scripts/` (Python 3 con numpy y scipy; LTspice en `C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe`; los scripts que lanzan LTspice escriben ahí sus decks y logs, conviene copiarlos primero a una carpeta de trabajo, p. ej. `C:\b2`):

- `python red.py` → respuesta nominal; `python mc3.py` → Monte Carlo de §3.3; `python mc2.py 300` → sensibilidades; `python retune.py` y `python tier2.py` → retoque de C2/C3 y buffers; `python x0_opt.py` → opciones de X0.
- `python calc_b2.py` → deriva de la relación, fugas, Ib y tensión por pieza (§2, §6).
- `python gen_settle.py` → asiento (§5.2); `python gen_gain.py` → llave de ganancia (§5.1).
- Decks sueltos (`decks_ltspice/`): `LTspice.exe -b x0_ac.cir` (ruta X0 con OPA2188), `div_ac.cir` (divisor, `.step sel`), `amp_ac.cir` (solo el amplificador), `x0_tran.cir` (capacidad no lineal; `b` y `f` se cambian en `.param`), `cm_dc.cir` (modo común). Los `.meas` salen en el `.log`.
- Las salidas de la corrida de esta sesión están en `resultados/`.
