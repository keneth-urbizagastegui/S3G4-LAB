# DMM bloque 3: ohmios, prueba de diodo y continuidad (estudio previo)

- Autor: Claude Code (ingeniero), 8 oct 2026. **Propone; no decide.** Elige Keneth.
- Alcance: la fuente de corriente P43 (TLV2372, elemento de paso, R_rango y los 2 × 74HCT4051 de fuerza y sentido), su paso por la cadena de ohmios del bloque 1 (relé → R1 → TVS → R_S → sujeciones → BAT54), la lectura de V_x por X0 (bloque 2, cerrado en S12d), la prueba de diodo, la continuidad con COMP7 y la detección de cable abierto (P33) y de tensión externa (P34).
- Fronteras: bloque 1 cerrado (60 V DC / 60 Vrms en ohmios, sin red); bloque 2 cerrado en S12d (X0 por R_PROT 99 kΩ + 10 kΩ, OPA4192 como seguidor, A con ×1 / ×10.1, divisor de 10.01 MΩ entre V/Ω y COM). Especificación D5: Ω de 200 Ω a 2 MΩ ±(0.2 % + 40) / ±(0.2 % + 10), 20 MΩ ±(1 % + 40) / ±(1 % + 10), diodo ≥ 3.5 V a 100 µA (LED) y silicio como el ELVIS II, continuidad < 1 ms con COMP7 contra el DAC2.
- Criterio de Keneth (8 oct, DECISIONS y memoria): que funcione con margen y sin complicar; se prefiere la solución simple que quita el problema de raíz; los fallos marginales de modelo o de criterio se documentan, sin rediseñar por ellos; lo que se calibra se separa de lo que deriva.
- Qué es esto: cuentas propias en Python (`scripts/calc_*.py`, mismo método que `herramientas/calc_dmm_h.py`), simulaciones pequeñas en LTspice (TLV2372 y OPAx192 de TI, BSS84 y BAT54 con los modelos del repositorio) y búsquedas en LCSC. **No hay hardware, no se descargó nada.** Hojas usadas, todas locales: BSS84 y 2N7002 (Diodes), TLV2372 (SLOS270F), 74HC4051/74HCT4051 (Nexperia, rev. 12), SMAJ12CA (Diodes DS19005), STM32G473 (DS12712 rev. 5) y el relé TQ2SA. Lo que no está en el repositorio (BSS138, TMUX1208, TVS de baja capacidad) lo marco **por confirmar**.
- Decks, scripts y salidas: `DMM/estudio_bloque3/` (`decks_ltspice/`, `scripts/`, `resultados/`). Cómo repetirlo: al final.

---

## 0. Lo esencial y tabla de decisiones

Hallazgos que cambian cosas respecto a la sección H y a la pendiente del 8 oct:

1. **El problema de los 4.9 kΩ es más grave que «no llega a 1 mA con 2 kΩ».** 1 mA por 4.9 kΩ son 4.9 V, más que el riel: ni en cortocircuito se llega. Con riel −2 %, resistencias +1 %, BAT54 de hoja y 110 Ω del 4051, la corriente máxima con la que el rango de 2 kΩ cabe (V_x = 2 V con 0.3 V de margen) es **0.52 mA**. LTspice lo confirma: a 0.5 mA el borne llega a 1.62 V y a 100 µA a 3.63 V (§2.1).
2. **Bajar la corriente (a) no cabe en D5.** A 0.5 mA el ADC trabaja al 50 % de la ventana en 200 Ω y 2 kΩ: la INL vale el doble en ohmios y harían falta **+75 / +17 cuentas** en lugar de +40 / +10 (error/tolerancia 182 % / 157 %). El LED a 100 µA queda en 3.53 V, a 0.03 V del mínimo.
3. **La raíz es que la corriente de medida atraviesa R_S (2.7 kΩ), que solo protege las sujeciones.** Si la fuente (tras el BAT54) se inyecta en **N1**, el nodo de la TVS, y no en N2, R_S queda como rama de falta y el camino de la fuente es solo R1. Con R1 = 3 × 510 Ω (1.53 kΩ) caben **1 mA** en 200 Ω y 2 kΩ, D5 completo (error/tolerancia 91 % / 78 %), LED 3.87 V y silicio a 1 mA con 2.29 V. Con R1 = 2.2 kΩ sin tocar valores (c2) caben 0.79 mA: +47 / +10 cuentas, casi D5.
4. **Repartir la resistencia de otra forma, solo con valores (b), empeora los rieles.** Con R1 = 3 × 330 Ω y R_S = 510 Ω se cumple D5, pero la corriente hacia las sujeciones con 60 V pasa de 2.6 mA a 13 mA: más de lo que consume el DMM, los rieles suben hasta el zéner y la separación entre ellos pasa de 9.8 V a ≈ 11–12 V, por encima de los 10.5 V del 74HCT4051 (§2.4). Descartada.
5. **Elemento de paso: BSS84, no PNP.** El PNP pierde 0.66 % (1/(β+1) con β = 150) y deriva 340 ppm entre 18 y 28 °C; el BSS84 no pierde nada (+1 ppm en SPICE) y cae 0.03 V en lugar de 0.2 V. El lazo necesita compensación: sin ella el margen de fase es 8° en el rango de 100 µA; con 1 kΩ en el sentido y 1 nF de la salida a la entrada inversora queda en 74–98° en los cinco rangos (§3.2).
6. **La etapa de referencia también va mejor con MOSFET (BSS138) que con NPN:** el NPN pone 199 ppm de deriva (β) que el MOSFET no tiene. La deriva de la corriente baja de 295 a 217 ppm y la ganancia de ohmios de 630 a 600 ppm (§3.3).
7. **La tensión en vacío del borne es ≈ 4.75 V, no 3.4–4.1 V,** en todos los rangos salvo 20 MΩ (2.0 V). Con la fuente saturada no cae V_set. Cabe en la entrada del OPA4192 y A satura (PB14 ≈ 2.4 V). La hoja de especificaciones dice «3.4 V máx.»: debe corregirse (§3.4).
8. **El asiento lo manda la capacidad de la TVS** (≈ 600 pF a 0 V, hoja Diodes Fig. 2): 0.03 / 0.13 / 1.1 / 9.4 / **39 ms** al 0.1 % en 1 mA / 100 µA / 10 µA / 1 µA / 0.2 µA (§3.6). El 20 MΩ necesita ≈ 50 ms de espera; es firmware, no hardware.
9. **Fugas:** la tolerancia del nodo de corriente es **0.85 nA en 2 MΩ y 1.1 nA en 20 MΩ** a 23 °C. La hoja del 74HCT4051 garantiza ±100 nA por canal y ±400 nA en total: no se puede garantizar. Como en el bloque 2: se mide en el prototipo y el plan B es un TMUX1208 en la fuerza (+0.55 USD) (§3.5).
10. **Diodo:** 1 mA para silicio y 100 µA para LED, y **se lee por X2 ×10.1** (la ruta del rango de 20 V, 1 mV por cuenta), no por X0: X0 ×1 no pasa de ≈ 2.4 V y un LED azul a 100 µA los supera. Corrige la decisión del 8 oct («se lee por X0») (§4).
11. **Continuidad:** a 1 mA, 50 Ω dan 50 mV; con A ×10.1 y el divisor ÷2 son 252 mV en PB14 (código DAC2 ≈ 414). El cruce llega en **15–27 µs** tras un corto y se asienta en 32 µs, con la TVS de 600 pF incluida (§5).
12. **P34 sin hardware y con mejora:** leer V_ext por X2 con la fuente apagada en cada medida (y restarla, como los ohmios compensados del 34401A). **P33 cierra el relé en modo tensión**, donde el bloque 1 pide sobrevivir a la red con el relé abierto: es una decisión para Keneth (§6).

### Tabla de decisiones para Keneth

| # | Tema | Opciones (cifras que cumplen o no) | Recomendación |
|---|---|---|---|
| 1 | **4.9 kΩ en serie** | **a** 0.5 mA, bloque 1 intacto: D5 pide +75/+17 cuentas en 200 Ω y 2 kΩ (182 %/157 %), LED 3.53 V. **c2** inyectar en N1, R1 = 2.2 kΩ sin tocar valores, 0.79 mA: +47/+10 (115 %/99 %), LED 3.80 V. **c1** inyectar en N1 y R1 = 3 × 510 Ω (1.53 kΩ), 1 mA: D5 entero (91 %/78 %), LED 3.87 V, esfuerzos a 60 V más bajos que hoy (R1 0.47 W por pieza, 24 %; TVS 0.37 W, 37 %), corriente de las sujeciones igual (2.6 mA). **b** valores (3 × 330 Ω + R_S 510 Ω): cumple D5 pero 13 mA a los rieles | **c1.** Quita el problema de raíz con un cambio de cableado y de valor de R1, ≈ +0.04 USD, y deja intacto lo que más costó cerrar (R_S, sujeciones y rieles). Exige que Codex repita las ESD y los 60 V de S11.4 con la nueva cadena (§9). Si Keneth no quiere reabrir el bloque 1: **a**, con D5 de 200 Ω y 2 kΩ en ±(0.2 % + 80) / ±(0.2 % + 20) documentado |
| 2 | Elemento de paso | **A** BSS84 (C82079, 0.047 USD): sin corriente de base, 0.03 V; puerta con fuga ≤ 10 nA que no pasa por Rx. **B** MMBT3906: −0.66 % (β = 150), deriva ±170 ppm con ±5 °C, 0.2 V, a 0.2 µA la β cae | **A** |
| 3 | Etapa de referencia | **A** TLV2372 A + NPN (MMBT3904): +199 ppm de deriva por β. **B** TLV2372 A + BSS138 (0.026 USD): sin β; la puerta debe subir a VREF + Vgs ≈ 3.7–4.3 V y el TLV2372 llega a 4.75 V. **C** 2N7002: descartado, su Vth es 1.0–2.5 V a 250 µA (hoja local) y pediría hasta 5.0 V de puerta | **B** (comprobar Vgs en la hoja del MPN elegido) |
| 4 | Estabilidad del lazo | **A** sin compensar: 8° en 100 µA. **B** Rsn 1 kΩ en la línea de sentido y Cc 1 nF de la salida a la entrada inversora: 74–98° (esquinas en §3.2) | **B** (0.02 USD) |
| 5 | Corrientes de 2 MΩ y 20 MΩ | **A** H: 1.0 µA y 0.2 µA (83 % y 67 % de la ventana; error/tolerancia 95 % y 77 % garantizada). **B** llenar la ventana: ≈ 1.19 µA (R_k ≈ 420 kΩ) y ≈ 0.30 µA (R_k ≈ 1.7 MΩ = 1.5 MΩ + 200 kΩ): 80 % y 52 %, y la fuga tolerable sube a ≈ 1.0 y 1.7 nA. En vacío el 20 MΩ da 3.0 V en lugar de 2.0 V | **B** (mismas piezas, otro valor). Si no, **A** |
| 6 | Fuga de los 74HCT4051 (fuente) | **A** 74HCT4051 y medirla (tolerancia 0.85–1.1 nA, hoja ±100/±400 nA). **B** TMUX1208 (C494728, 0.60 USD cada uno, +0.55 USD) para fuerza y sentido, alimentado a +4.9 V y COM porque todos los nodos están entre 0 y +4.9 V (fuga por confirmar con la hoja de TI) | **A** y medir (D4). **B** si la fuga de fuerza supera 0.8 nA a 23 °C |
| 7 | Diodo | **A** silicio 1 mA + LED 100 µA, lectura por X2 ×10.1. **B** lectura por X0 (decisión del 8 oct): solo hasta ≈ 2.4 V | **A** |
| 8 | Continuidad | 1 mA con A ×10.1 y umbral de 50 Ω; sujeción de PB14 solo al lado negativo (un Schottky a COM) o ninguna (inyección −0.4 mA, hoja −5 mA) | 1 mA, un solo Schottky |
| 9 | P34, tensión externa | **A** leer V_ext por X2 con la fuente apagada antes de cada medida y restarla. **B** esperar lecturas negativas o saturadas con la fuente encendida | **A** (ya cabe en el ciclo del autocero; en 20 MΩ, solo al cambiar de rango por los 39 ms de asiento) |
| 10 | P33, cable abierto | **A** solo en ohmios (OL), sin avisar en tensión. **B** también en tensión, con relé cerrado ≤ 15 ms, solo si el borne está a menos de 5 mV y sin zumbido de red durante 50 ms. **C** como §10 de H, sin salvaguarda | **B** (la especificación lo lista); el riesgo residual es una red conectada justo en esos 15 ms, que destruye R1 pero no el resto |
| 11 | Asiento en ohmios | Firmware: esperar 0.05 / 0.2 / 1.5 / 12 / 50 ms en 1 mA / 100 µA / 10 µA / 1 µA / 0.2 µA (tiempo al 0.01 % del §3.6, redondeado hacia arriba) | Aceptar |

Coste de P43 completa ≈ 1.5 USD (§3.7). El cambio c1 cuesta ≈ +0.04 USD sobre las 2 × 1.1 kΩ del bloque 1.

---

## 1. Base de cálculo y validación

### 1.1 Constantes

| Magnitud | Valor | Origen |
|---|---|---|
| Riel | 4.9 V; peor caso 4.802 V (−2 %) | H §6, S11.4 |
| V_set | 2.5 V × 4.99 kΩ / 24.9 kΩ = 0.501 V bajo el riel | P43 aceptada (D8) |
| Ron del 74HCT4051 de fuerza | 110 Ω (cerca del riel) | hoja Nexperia, Fig. 8: típico 50–75 Ω a VCC − VEE = 9 V; se toma 110 Ω por dispersión (±30 %) y temperatura |
| BAT54 | V_F de hoja máxima: 0.24 V a 0.1 mA, 0.32 V a 1 mA | catálogo Nexperia, ver S11.4 |
| BSS84 | 0.03 V con Vgs de −7 a −9 V (R_DS(on) ≤ 10 Ω a −5 V) | hoja local |
| Divisor entre V/Ω y COM | 10.01 MΩ (6 × 1.5 MΩ + 910 kΩ + 100 kΩ), en paralelo con Rx | ACTA_S12d |
| Una cuenta | 100 µV en el ADC (±2 V = ±19999 cuentas) | H §1 |
| Ganancia de ohmios | 600–625 ppm (corriente 217–280, driver 250, patrón 500) | H §8, §3.3 de este estudio |

Compliancia = riel − V_set − I·Ron − V_DS − V_F(BAT54) − I·R_serie·1.01. V_x se lee en el borne por X0 (después del relé, de R1 y de R_S): ni el relé ni R1 ni R_S entran en el cociente V_x / I, solo en la compliancia.

### 1.2 Validación del modelo analítico con LTspice

`run_compl.py` busca la tensión máxima en el borne con ≥ 99 % de la corriente (TLV2372, BSS84 y BAT54 de modelo, riel 4.8 V). Las filas de la opción a salen de una pasada anterior del mismo script (`resultados/compliancia_spice_a_b.txt`); c1 está en `compliancia_spice_c.txt`:

| Caso | Analítico (conservador) | LTspice |
|---|---|---|
| c1, R_serie 1.53 kΩ, 1 mA | 2.29 V | 2.43 V |
| c1, R_serie 1.53 kΩ, 100 µA | 3.87 V | 3.96 V |
| R_serie 4.9 kΩ, 0.5 mA | 1.45 V | 1.62 V |
| R_serie 4.9 kΩ, 100 µA | 3.53 V | 3.63 V (S11.4: 3.606 V) |

El analítico sale 0.09–0.17 V por debajo porque usa el V_F máximo del BAT54 y el +1 % de las resistencias; el SPICE usa el modelo genérico (V_F ≈ 0.24 V a 1 mA). Todas las cifras de este estudio usan el analítico.

### 1.3 Cómo se pasa la INL a ohmios

Mismo método que `calc_dmm_h.py`: V_x(Rx) = I·(Rx ∥ 10.01 MΩ), así que una cuenta del ADC equivale a 100 µV / (G·I·(R_DIV/(Rx + R_DIV))²) ohmios. Se recorre del 10 al 100 % del rango; la tolerancia es (pct − ganancia de ohmios)·lectura + n·fondo/20000. INL del ADC5: 39 cuentas sin linealizar (nivel «garantizado», n = 40) y 10 linealizada (nivel «calibrado», n = 10). «Error/tolerancia» es el peor cociente: menos de 100 % cumple.

---

## 2. Tema 1: los 4.9 kΩ en serie

### 2.1 Cuánta corriente cabe

| R_serie | I máxima en el rango de 2 kΩ (margen 0.3 V) | V_ADC a fondo | Llenado de la ventana |
|---|---|---|---|
| 1.0 kΩ | 1.17 mA | 2.34 V | 117 % |
| 1.5 kΩ | 1.007 mA | 2.01 V | 101 % |
| 1.8 kΩ | 0.93 mA | 1.86 V | 93 % |
| 2.3 kΩ | 0.83 mA | 1.65 V | 83 % |
| 3.0 kΩ | 0.71 mA | 1.43 V | 71 % |
| 4.0 kΩ | 0.60 mA | 1.19 V | 60 % |
| 4.9 kΩ (bloque 1) | 0.52 mA | 1.04 V | 52 % |

En H el rango de 200 Ω daba 2 V a 10 mA; con el ×10.1 de A (bloque 2) bastan 0.99 mA, así que **el rango de 200 Ω usa la misma corriente que el de 2 kΩ** y las dos comparten R_k. Los 10 mA de H no caben con ningún R_serie realista: 10 mA × 0.3 kΩ ya son 3 V.

### 2.2 Opciones

Todas con riel −2 %, resistencias +1 % (`calc_opciones.py`):

| Opción | R_serie | I (200 Ω y 2 kΩ) | V_x a fondo en 2 kΩ / ventana | V_disponible | Margen | LED a 100 µA | Silicio | Cuentas ADC por Ω en 200 Ω | Dígitos que cubren la INL (garantizada / calibrada) | Error/tolerancia en 2 kΩ (garantizada / calibrada) |
|---|---|---|---|---|---|---|---|---|---|---|
| a · bloque 1 intacto | 4.9 kΩ | 0.50 mA | 1.00 V / 50 % | 1.44 V | +0.44 V | 3.53 V | 0.50 mA, 1.44 V | 51 | **75 / 17** | 182 % / 157 % |
| c2 · inyectar en N1, R1 = 2.2 kΩ | 2.2 kΩ | 0.79 mA | 1.58 V / 79 % | 2.12 V | +0.54 V | 3.80 V | 0.79 mA, 2.12 V | 80 | **47 / 10** | 115 % / 99 % |
| c1 · inyectar en N1, R1 = 3 × 510 Ω | 1.53 kΩ | 1.00 mA | 2.01 V / 100 % | 2.29 V | +0.28 V | 3.87 V | 1.00 mA, 2.29 V | 101 | **36 / 7** | 91 % / 78 % |
| b · valores: R1 = 3 × 330 Ω, R_S = 510 Ω | 1.5 kΩ | 1.00 mA | igual que c1 | 2.32 V | +0.31 V | 3.87 V | 1.00 mA | 101 | 36 / 7 | 91 % / 78 % |

Los rangos de 20 kΩ a 20 MΩ llevan en todas las opciones las corrientes de H (100 µA, 10 µA, 1 µA, 0.2 µA); solo cambia la tensión disponible: con a, 3.53 / 4.06 / 4.19 / 4.25 V; con c1, 3.87 / 4.09 / 4.19 / 4.25 V (todas con margen ≥ 1.5 V). D5 da 40 / 10. Solo c1 y b caben. La columna «Dígitos» es lo que haría falta aceptar para que el error de INL quepa en toda la escala; la opción a lo dobla.

Para la opción a, el aumento es físico y no se arregla recalibrando: la linealización deja 10 cuentas del ADC, que en un rango medio-lleno son 20 dígitos.

### 2.3 Cómo queda cada rango con la opción c1 (R_serie 1.53 kΩ, riel −2 %)

Con las corrientes de H para 100 µA y menos (`calc_b3.py`):

| Rango | R_k (0.1 %) | I | G | V_x a fondo | V_ADC a fondo | V_disponible | Margen | Cuentas ADC por Ω | Garantizada (peor, % del rango) | Calibrada |
|---|---|---|---|---|---|---|---|---|---|---|
| 200 Ω | 499 Ω | 1.004 mA | ×10.1 | 0.200 V | 2.02 V (101 %) | 2.29 V | +2.09 V | 101 | 90 % (10 %) | 78 % |
| 2 kΩ | 499 Ω | 1.004 mA | ×1 | 2.00 V | 2.00 V (100 %) | 2.29 V | +0.28 V | 10 | 91 % (10 %) | 78 % |
| 20 kΩ | 4.99 kΩ | 100.4 µA | ×1 | 1.996 V | 1.996 V (100 %) | 3.87 V | +1.87 V | 0.996 | 91 % (10 %) | 78 % |
| 200 kΩ | 49.9 kΩ | 10.04 µA | ×1 | 1.961 V | 1.961 V (98 %) | 4.09 V | +2.13 V | 0.0961 | 92 % (10 %) | 79 % |
| 2 MΩ | 499 kΩ | 1.004 µA | ×1 | 1.667 V | 1.667 V (83 %) | 4.19 V | +2.52 V | 0.00695 | 95 % (10 %) | 82 % |
| 20 MΩ | 2.499 MΩ | 0.2005 µA | ×1 | 1.334 V | 1.334 V (67 %) | 4.25 V | +2.91 V | 0.000223 | 77 % (100 %) | 25 % |
| 2 MΩ, ventana llena | ≈ 420 kΩ | ≈ 1.19 µA | ×1 | 1.984 V | 99 % | 4.18 V | +2.2 V | 0.00827 | 80 % (10 %) | 69 % |
| 20 MΩ, ventana llena | ≈ 1.7 MΩ | ≈ 0.295 µA | ×1 | 1.97 V | 99 % | 4.2 V | +2.2 V | 0.00033 | 52 % (100 %) | 17 % |

Una cuenta del ADC en 20 MΩ cerca del fondo vale ≈ 4.5 kΩ (el divisor de 10.01 MΩ aplana la curva): 3.0 kΩ con 0.3 µA. Es el único rango donde las cuentas del ADC y los dígitos de la pantalla (1 kΩ) no coinciden.

### 2.4 Qué pasa con 60 V en cada reparto (`calc_prot.py`)

Modelo estático: TVS lineal por tramos (VBR mínima 13.3 V y resistencia dinámica (19.9 − 14.7)/20.1 de la hoja), sujeción de N2 a ±(5.6 + 0.65) V con 30 Ω. Criterio de S11.4: ≤ 50 % de la potencia y ≤ 80 % de la tensión de cada pieza (2512: 2 W y 250 V; TVS: 1 W continuo a 75 °C; zéner: 375 mW supuesto).

| Cadena | R_serie del camino de medida | 60 V DC: R1 por pieza | TVS | R_S | Corriente a los rieles | 60 Vrms: R1 / TVS | V por pieza de R1 (pico) |
|---|---|---|---|---|---|---|---|
| Hoy: 2 × 1.1 kΩ + R_S 2.7 kΩ | 4.9 kΩ | 0.50 W (25 %) | 0.25 W | 0.018 W | 2.6 mA | 0.53 / 0.22 W | 36 V |
| **c1: R1 = 3 × 510 Ω, R_S 2.7 kΩ en rama aparte** | 1.53 kΩ | **0.47 W (24 %)** | 0.37 W (37 %) | 0.018 W | **2.6 mA** | 0.51 / 0.33 W | 16 V |
| c2: R1 = 2 × 1.1 kΩ, R_S rama aparte | 2.2 kΩ | 0.50 W | 0.25 W | 0.018 W | 2.6 mA | 0.53 / 0.22 W | 36 V |
| b: R1 = 3 × 330 Ω + R_S 510 Ω | 1.5 kΩ | 0.73 W (37 %) | 0.45 W (45 %) | 0.087 W | **13 mA** | 0.79 / 0.41 W | 24 V |
| b': R1 = 2 × 510 Ω + 470 Ω | 1.5 kΩ | 1.07 W (53 %, no cumple) | 0.42 W | 0.094 W | 13 mA | 1.15 / 0.38 W | 36 V |

La opción b mete 13 mA en las sujeciones con 60 V: más de lo que consume el DMM (≈ 3 mA con la fuente apagada), así que el riel positivo sube hasta el zéner (5.6 V + su resistencia dinámica a 13 mA, ≈ 6.1 V) y, con 60 Vrms, también el negativo. La separación pasa de 9.8 V a 11–12 V; el 74HCT4051 admite 10.5 V (hoja Nexperia). Ya hoy S11.4 mide 10.57 V entre rieles en el caso de 60 V con la fuente apagada: es un margen que no conviene empeorar. Con c1, R_S vale lo mismo y la corriente de las sujeciones también.

Lo que cambia c1 y no está validado: el BAT54 y el BSS84 quedan expuestos a la tensión del nodo N1 (clampeada por la TVS a 14–20 V) en lugar de a la de N2 (±6.3 V). El BAT54 aguanta 30 V inversos (24 V al 80 %) y el BSS84 50 V; con 60 V DC el BAT54 ve 10 V inversos. Las ESD vuelven a entrar por el relé con R1 de 1.53 kΩ en lugar de 2.2 kΩ: la corriente de pico por pulso sube un 44 %, repartida en tres piezas en lugar de dos. Todo eso se repite en S11.4 (§9, C1).

---

## 3. La fuente P43

### 3.1 Circuito propuesto

- **Referencia:** TLV2372 (un solo encapsulado doble, A y B). A compara VREF (2.5 V, REF3325) con el emisor/fuente de Q1 y R1 = 24.9 kΩ a COM: IREF = 100.4 µA. Q1 (BSS138) lleva IREF por R2 = 4.99 kΩ desde el riel: **el colector queda 0.501 V bajo el riel**.
- **Corriente:** R_k cuelga del riel. B compara el nodo de 0.501 V con el extremo inferior de la R_k elegida (línea de **sentido**: un 74HCT4051 y 1 kΩ en serie, sin corriente) y mueve la puerta de M1 (BSS84, 1 kΩ en serie). La corriente de la fuente de M1 llega a ese mismo extremo de R_k por el 74HCT4051 de **fuerza**, así que su Ron queda fuera del lazo. I = V_set / R_k y la **referencia se cancela** como en H.
- **Compensación:** 1 kΩ en serie con la línea de sentido y **1 nF** de la salida de B a su entrada inversora.
- **Salida:** el drenador de M1 va al BAT54 de bloqueo y de ahí a **N1** (opción c1) o a N2 (opción a).
- **Habilitación:** un BSS138 (GPIO de 3.3 V) lleva a COM la entrada no inversora de A a través de 10 kΩ desde VREF: V_set = 0, B lleva la puerta al riel y M1 queda cortado. Se refuerza con INH de ambos 74HCT4051.
- **Selección:** los dos 74HCT4051 comparten A, B, C e INH: **cuatro líneas**, más la habilitación: cinco en total (H preveía 2 × 3 + 1).
- **Nivel lógico:** el 74HCT4051 admite VIH ≥ 2.0 V con VCC = 4.9 V (hoja p. 11), así que un GPIO de 3.3 V basta; sus entradas de control se miden respecto a GND, no a VEE (hoja: «voltages are referenced to GND»). El BSS138 tiene Vth ≤ 1.5 V.

```
 +4.9 V ─┬─ R2 4.99k ── CN (riel − 0.501 V) ─────────────────────────► B (+)
         │      Q1 (BSS138): drenador en CN; fuente = E1 ── R1 24.9k ── COM
         │      A: (+) = VREF 2.5 V, (−) = E1, salida → puerta de Q1
         └─ R_k (499 Ω … 2.499 MΩ) ── S ─┬─ 4051 de sentido ── 1 kΩ ──► B (−)   [Cc 1 nF: salida de B → B (−)]
                                          └─ 4051 de fuerza ── F ── fuente de M1 (BSS84); puerta ← salida de B (1 kΩ)
                  drenador de M1 ── BAT54 ── N1 (TVS a COM) ── R1 (3 × 510 Ω) ── relé ── V/Ω
                                             └─ R_S 2.7 kΩ ── N2 (sujeciones BAV199 y zéner)    [rama de falta, opción c1]
```

Cinco valores de R_k para seis rangos (200 Ω y 2 kΩ comparten): 499 Ω, 4.99 kΩ, 49.9 kΩ, 499 kΩ y 2.499 MΩ (= 2 MΩ + 499 kΩ), todos 0.1 % y 25 ppm/°C. Quedan tres canales libres en cada 4051.

### 3.2 Elemento de paso y estabilidad (LTspice)

**PNP frente a BSS84** (`run_pnp.py`, β = 150, XTB = 1.5; resultado en `resultados/pnp_frente_a_mos.txt`):

| Rango | PNP: I a 23 °C | Deriva 18 → 28 °C | BSS84: I a 23 °C | Deriva |
|---|---|---|---|---|
| 1 mA | 990.18 µA | +353 ppm | 997.07 µA | +1 ppm |
| 100 µA | 99.041 µA | +342 ppm | 99.707 µA | +1 ppm |
| 10 µA | 9.9043 µA | +341 ppm | 9.9707 µA | +1 ppm |
| 1 µA | 0.99043 µA | +340 ppm | 0.99705 µA | +1 ppm |
| 0.2 µA | 0.19776 µA | +340 ppm | 0.19908 µA | +1 ppm |

El PNP resta 0.66 % de la corriente (la base sale por B, no llega a Rx) y deriva ≈ ±170 ppm con ±5 °C, lo que H estimaba en 300 ppm; la β real cae además a 0.2 µA (el modelo genérico no la modela). El BSS84 no tiene corriente de puerta que pase por Rx: su fuga de puerta (±10 nA a ±20 V, hoja) sale de B. Su IDSS (−100 nA a −25 V) solo importa con la fuente apagada, con el relé abierto en tensión y por tanto lejos de la medida.

**Margen de fase del lazo** (`run_comp.py`; lazo roto a la salida de B; BSS84 con Vth = −2.0 y −0.8 V):

| Compensación | 1 mA | 100 µA | 10 µA | 0.2 µA |
|---|---|---|---|---|
| Sin compensar | 46–47° | **8–9°** | 30° | 75–76° |
| Rsn 1 kΩ + Cc 1 nF | 95–98° | 74–80° | 76–78° | 74–75° |
| Rsn 10 kΩ + Cc 330 pF | 84–87° | 72–76° | 75–77° | 74° |

Sin compensar, el rango de 100 µA queda casi inestable. La causa probable (el modelo no la desglosa) es el polo del seguidor de fuente (1/gm ‖ R_k con 50–60 pF de la pata común del 4051 y del BSS84), que cae por debajo del cruce de 2 MHz del TLV2372. Con 1 kΩ + 1 nF la salida de B alimenta la entrada inversora directamente por encima de 160 kHz y el lazo se comporta como un seguidor (fc ≈ 2.3 MHz, margen > 70°). Se elige 1 kΩ y no 10 kΩ para que la fuga del 4051 de sentido pese 4 ppm por nA y no 40.

Esquinas del margen de fase con Rsn 1 kΩ + Cc 1 nF (`run_pm_esquinas.py`: Vth −0.8 / −2.0 V, Ron del 4051 60 / 130 Ω, capacidades ×0.6 / ×1.5 y riel 4.8 / 5.0 V, 16 combinaciones por rango): margen mínimo **92° (1 mA), 74° (100 µA), 74° (10 µA), 73° (1 µA) y 72° (0.2 µA)**, con cruce entre 2.1 y 2.6 MHz.

**Regulación de carga y de riel** (`run_reg.py`): con carga desde 0.1 Ω hasta la compliancia la corriente no varía (0 ppm; la ganancia de lazo es 109–111 dB). El riel de 4.8 a 5.0 V mueve la corriente +9 ppm. El modelo no tiene fugas parásitas: el residuo real son las fugas del §3.5.

### 3.3 Deriva con 23 ± 5 °C, tras calibrar (`calc_b3b.py`)

| Término | ppm |
|---|---|
| R_k (25 ppm/°C × 5 °C) | 125 |
| R2/R1 (dos resistencias de 25 ppm/°C, suma cuadrática; lineal 250) | 177 |
| Vos de B (2 µV/°C × 5 °C sobre 0.501 V) | 20 |
| Vos de A (2 µV/°C × 5 °C sobre 2.5 V) | 4 |
| NPN de la etapa 1 (β = 150, +0.6 %/°C) | 199 |
| **Total con NPN / con BSS138** | **295 / 217** |
| Ganancia de ohmios con BSS138 (con driver 250 y patrón 500 ppm) | **600** (H: 630) |

El Vos de los TLV2372 (hasta 4.5 mV) es un error de ganancia de V_set (0.9 % de 0.5 V) que se calibra con la corriente de cada rango; solo cuenta su deriva.

### 3.4 Tensión disponible y en vacío

Disponible: ver tablas del §2. **En vacío** (puntas al aire), la fuente satura y V_set no cuesta: el borne queda en ≈ riel − V_F(BAT54) = **4.75 V** (LTspice, riel 4.8 V), salvo en 20 MΩ, donde I·R_DIV = 2.0 V (3.0 V con 0.3 µA). La hoja dice «≈ 3.4 V máx.» y H supone ≈ 4.0 V para el OPA2188; con el OPA4192 de S12d no hay problema (entrada hasta los rieles; las sujeciones de X0 quedan a 0.05 V de conducir con riel +2 %: 4.95 V frente a 5.0 V). A satura y el driver del bloque 5 tiene que aceptarlo (ya lo exigía S12d). Debe corregirse la hoja de especificaciones.

### 3.5 Fugas frente a corrientes de 0.2 µA

Tolerancia: la deriva de una fuga (×(√2 − 1) = 0.41 de su valor a 23 °C con 18–28 °C, ley ×2/10 °C) debe ser ≤ 25 % de lo que sobra de la tolerancia tras la ganancia de ohmios:

| Rango | I | Fuga tolerable a 23 °C |
|---|---|---|
| 200 Ω y 2 kΩ | 1 mA | 846 nA |
| 20 kΩ | 100 µA | 85 nA |
| 200 kΩ | 10 µA | 8.5 nA |
| 2 MΩ | 1 µA | **0.85 nA** |
| 20 MΩ | 0.2 µA | **1.14 nA** (0.3 µA: ≈ 1.7 nA) |

Dónde entran:

| Camino | Qué hace | Valor de hoja | Efecto |
|---|---|---|---|
| Pata común del 4051 de fuerza hacia VEE | resta corriente a Rx, 1:1 | ±0.4 µA «all channels» y ON a 25 °C; ±1 y ±4 µA a 85 y 125 °C; medidas con la tensión completa de 9.8 V | **No garantizable**; típico no consta |
| Canales cerrados del 4051 de fuerza hacia la pata común | suman a Rx, con solo ≈ 0.5 V entre pines | ±0.1 µA por canal con 9.8 V | Mucho menor con 0.5 V, no hay cifra |
| 4051 de sentido | corriente × 1 kΩ en la entrada de B | mismas cifras | 4 ppm por nA: despreciable |
| TVS de N1 y BAV199 de N2 y de X0 | roban corriente en el borne | TVS 5 µA a 12 V (a 1–3 V sin dato); BAV199 5 nA a 75 V, 3 pA típica; extrapolado √V: ≈ 1.2–1.7 nA no garantizado | ≈ pA típicos; ver REDISENO_BLOQUE1 §3.4 |
| TLV2372 | corriente de polarización | 1 pA típica, 60 pA máx. | despreciable |

Conclusión: como en el bloque 2, **la hoja no deja garantizar el 20 MΩ y el 2 MΩ**; con valores típicos (pA–nA) caben. Criterio de prototipo: con un patrón de 20 MΩ y otro de 2 MΩ, la lectura no debe derivar más de 0.2 % (2 MΩ) y 0.3 % (20 MΩ) entre 18 y 28 °C. Si no se cumple, primero limpiar y poner guarda alrededor de N1 y de la pata común del 4051 de fuerza (el bloque 2 llega a lo mismo), después el plan B (TMUX1208 o 0.3 µA en el 20 MΩ, que sube la tolerancia 1.5×).

### 3.6 Arranque y asiento (`run_arranque.py`, TVS 600 pF, cadena c1)

La TVS bidireccional SMAJ12CA tiene ≈ 600 pF a 0 V (Fig. 2 de la hoja de Diodes, lectura a ojo). La corriente de la fuente la carga: τ = (Rx ∥ 10 MΩ) × ≈ 700 pF.

| Rango | Rx | I final | 1 % | 0.1 % | 0.01 % |
|---|---|---|---|---|---|
| 1 mA | 2 kΩ | 997.1 µA | 0.028 ms | 0.031 ms | 0.033 ms |
| 100 µA | 20 kΩ | 99.71 µA | 0.099 ms | 0.13 ms | 0.16 ms |
| 10 µA | 200 kΩ | 9.971 µA | 0.81 ms | 1.10 ms | 1.39 ms |
| 1 µA | 2 MΩ | 0.9971 µA | 6.9 ms | 9.4 ms | 11.8 ms |
| 0.2 µA | 20 MΩ | 0.1991 µA | 29 ms | 39 ms | **49 ms** |

Con Rx = 10 % del rango los tiempos son menores. En 20 MΩ conviene dejar la fuente encendida entre lecturas y no apagarla en cada una. En 20 MΩ con 0.3 µA el asiento es el mismo (τ no depende de I). Una TVS de menor capacidad (p. ej. 390 pF de las SMBJ12CA del catálogo) bajaría esos tiempos proporcionalmente, pero toca el bloque 1.

### 3.7 Piezas y coste

| Pieza | Cant. | LCSC | USD |
|---|---|---|---|
| TLV2372IDR (A y B) | 1 | C27204 | 0.35 |
| BSS84 (M1) | 1 | C82079 (onsemi BSS84LT1G; la hoja local es la de Diodes: comprobar Vth y IGSS del MPN) | 0.047 |
| BSS138 (Q1 y habilitación) | 2 | C7420339 (preferida) | 0.053 |
| 74HCT4051 (fuerza y sentido) | 2 | C87239 | 0.64 |
| R_k 0.1 %, 25 ppm: 499 Ω, 4.99 kΩ, 49.9 kΩ, 499 kΩ | 4 | C861432, C723532, C705780, C515607 | 0.16 |
| R_k de 2.499 MΩ = 2 MΩ + 499 kΩ | 2 | C2828885 (1206) + C515607 | 0.10 |
| R1 = 24.9 kΩ y R2 = 4.99 kΩ, 0.1 % | 2 | C136967, C723532 | 0.07 |
| 1 kΩ (Rg), 1 kΩ (Rsn), 10 kΩ, 1 nF C0G, desacoplos | ≈ 6 | genéricos | ≈ 0.10 |
| **Total P43** | | | **≈ 1.5** |
| Cambio c1: R1 = 3 × 510 Ω 2512 (en lugar de 2 × 1.1 kΩ) | 3 | C2912629 (0.083 c/u, 12.7 k en stock) | +0.04 |

Consumo: IREF 0.1 mA + TLV2372 ≈ 0.6 mA + corriente de medida ≤ 1 mA + 2 × 4051. H preveía hasta 10 mA de fuente: el máximo baja a 1 mA, útil para RF-17.

---

## 4. Prueba de diodo

- **Corrientes:** silicio 1 mA (R_k de 499 Ω, la del rango de 2 kΩ), LED 100 µA (R_k de 4.99 kΩ, la del rango de 20 kΩ). Son las del ELVIS II (decisión del 7 oct).
- **Tensión disponible** (riel −2 %): con c1, 3.87 V a 100 µA (SPICE 3.96 V) y 2.29 V a 1 mA; con a, 3.53 V (SPICE 3.63 V) y 0.5 mA con 1.44 V. RD-08 y D5 piden ≥ 3.5 V a 100 µA: c1 deja 0.37 V de margen y la opción a solo 0.03 V.
- **Lectura:** X0 ×1 no pasa de ≈ 2.4 V (ventana del ADC de ±2.5 V diferencial). Un LED azul o blanco a 100 µA da 2.6–3.3 V. La decisión del 8 oct dice «la prueba de diodo se lee por X0»; hay que leer por **X2 con ×10.1**, la ruta del rango de 20 V (V_ADC = V_x / 9.91, 1 mV por cuenta, como pide la hoja: 0 – 3.3 V, 1 mV). La carga del divisor es 0.35 µA a 3.5 V (0.35 % de 100 µA), calibrada. La exactitud es la de 20 V (±(0.1 % + 40 cuentas) = 40 mV garantizada, 10 mV calibrada), suficiente para un diodo.
- **Silicio a 1 mA** requiere c1. Con a serían 0.5 mA, donde un diodo de señal da unos 20–35 mV menos que a 1 mA; sirve igual para decidir sentido y tipo.
- **Fuente apagada y tensión externa:** igual que ohmios (P34).

---

## 5. Continuidad

- **Corriente y ganancia:** rango de 200 Ω, A en ×10.1. Con 1 mA, 50 Ω (el umbral de la hoja) dan 50 mV en el borne, 505 mV a la salida de A y **252 mV en PB14** tras el divisor ÷2 (código DAC2 ≈ 414 con VREF+ = 2.5 V). Con 0.5 mA (opción a): 25 mV, 126 mV en PB14, código ≈ 207.
- **Divisor ÷2:** 2 × 10 kΩ al 1 % (la razón solo mueve el umbral, que se calibra en P41); impedancia de salida 5 kΩ, con la que la fuga de entrada de PB14 es despreciable, y 20 kΩ de carga para A además del driver del bloque 5.
- **Incertidumbre del umbral:** COMP7 tiene offset −9 / +3 mV y la DAC interna ±5 LSB (15 MSPS) o ±12 LSB (1 MSPS) de error total sin ajustar: peor caso ≈ ±16 mV en PB14. Con 1 mA son **±3.2 Ω** (6 % del umbral) y con 0.5 mA ±6.3 Ω (13 %). P41 mide el umbral en la autoprueba y lo ajusta con el código del DAC; queda ruido y deriva de unos pocos mV. Histéresis HYST = 1 (9 mV típ., 4–16 mV): 1.8 Ω a 1 mA.
- **Fuente de 1 mA en vacío:** A satura a +4.85 V y PB14 queda en 2.4 V (LTspice 2.385 V), bajo VDDA = 3.3 V: no hace falta sujetar el lado positivo. Con tensión externa negativa A llega a −4.9 V y PB14 a −2.45 V: **el Schottky a COM solo sirve para este lado**. Sin él, la inyección sería ≈ −0.4 mA frente a los −5 mA de la hoja del G473 (con posible deterioro del ADC5 vecino).
- **Tiempo de respuesta** (`run_cont.py`, cadena completa con P43, R_PROT 99 kΩ + 10 kΩ, OPA4192 de buffer, mux Ron 70 Ω, A ×10.1, ÷2, TVS 600 pF):

| Caso | Abierto → corto | Cruza el umbral | Asiento al 2 % |
|---|---|---|---|
| c1, 1 mA | 20 Ω | **14.5 µs** | 32 µs |
| c1, 1 mA | 40 Ω | 26.6 µs | 32 µs |
| a, 0.5 mA | 20 Ω | 13.7 µs | 67 µs |
| a, 0.5 mA | 40 Ω | 61 µs | 67 µs |

 La mayor parte son la recuperación de A desde su saturación (≈ 15 µs en S12c) y la constante del filtro de X0 (≈ 1.7 µs). COMP7 añade 17–31 ns. Margen de 30× sobre 1 ms (la cadena de c1 incluye la TVS de 600 pF). La corriente mayor da más margen cerca del umbral: a 40 Ω y 0.5 mA el voltaje (101 mV) queda a 26 mV del umbral y el cruce tarda 61 µs.
- **Zumbador:** un anti-rebote mínimo en firmware (PWM del zumbador); no forma parte de la medición.

---

## 6. Cable abierto (P33) y tensión externa (P34)

### 6.1 P34: tensión externa en ohmios

Con la fuente apagada, el borne sin conexión a la fuente ve V_ext por el divisor (X2 ÷100.1) y por R_PROT (X0). **Propuesta, sin hardware:** en cada medida de ohmios, con el relé cerrado y el ADC en X2 ×10.1 (V_ADC = V_ext / 9.91):

1. Fuente apagada, leer X3 y X2. Si |V_ext| < 20 mV (≈ 2 mV en el ADC, 20 cuentas), seguir y **restar V_ext** del resultado (compensación de offset, como los ohmios compensados del 34401A: elimina también las fem térmicas del relé y los contactos).
2. Si |V_ext| ≥ 20 mV: no encender la fuente y mostrar «tensión externa X V». Con ×10.1 el ADC cubre ±19.8 V; por encima satura, y eso ya basta para avisar; para mostrar el valor se pasa a ×1 (60 V caen a 0.6 V en X2). Quedarse en vigilancia.
3. Con la fuente encendida, una lectura negativa o por encima de la tensión disponible del rango sin que Rx haya cambiado indica que V_ext cambió entre medias.

Coste: una lectura más por medida (≈ 17 ms con un ciclo de 60 Hz) y, en 20 MΩ, **los 39–49 ms de asiento por cada encendido**: allí conviene hacerlo solo al cambiar de rango o al ver una lectura anómala.

### 6.2 P33: cable abierto

El mecanismo de §10 de H (encender 0.2 µA y mirar si el borne llega a ≈ 2 V) **funciona igual** con la fuente nueva (2.0 V en 20 MΩ con puntas al aire, 3.0 V con 0.3 µA). Con la capacidad de la TVS y del borne (≈ 700 pF) la tensión sube a I/C = 0.29 V/ms: a los 3 ms hay 0.86 V con puntas al aire frente a < 20 mV con una resistencia de < 100 kΩ o con las puntas en corto. Basta una ventana de ≈ 10 ms (relé 3–4 ms de cierre según la hoja, 3 ms de fuente, lectura), como decía H.

**El conflicto:** P33 se pensó para el modo tensión, donde el relé está abierto, y en tensión el bloque 1 exige sobrevivir 230 Vrms durante 10 s con el relé abierto. La cadena de ohmios no aguanta la red. Cerrar el relé 10–15 ms en tensión, solo cuando el borne está en ≈ 0 V, es seguro salvo que alguien conecte la red a las puntas justo en esa ventana (325 V pico sobre 1.53 kΩ: ≈ 0.2 A de pico y ≈ 20 W de pico en cada 510 Ω durante unos ms, del orden del límite de pulso de un 2512 de 2 W, cuya curva no he leído: podría dañar R1, no la placa).

| Opción | Qué hace | Riesgo |
|---|---|---|
| A | P33 solo en ohmios (cable abierto = OL); en tensión, 0 V | Ninguno; pierde un aviso que la hoja lista |
| **B** | En tensión, solo si el borne está a menos de 5 mV durante 50 ms y sin zumbido de red; relé cerrado ≤ 15 ms, como mucho una vez cada 5 s | Red conectada justo en la ventana: baja, pero real |
| C | Sin salvaguarda | El relé repiqueteará con las puntas en corto |

---

## 7. Lo más simple que cumpla

| # | Simplificación | Efecto |
|---|---|---|
| S1 | 200 Ω y 2 kΩ comparten corriente (1 mA, R_k de 499 Ω) | 5 R_k y 5 canales en lugar de 6 |
| S2 | Etapa 1 con BSS138, elemento de paso con BSS84 | Sin β: −199 ppm de deriva y −0.66 % de pérdida, menos de 0.2 V de caída |
| S3 | Fuente de 10 mA descartada | Sin 1.6 W en la escalera P42 (ya superado por O4) y −9 mA de consumo |
| S4 | P34 con lectura de V_ext con la fuente apagada | Sin hardware, además compensa offsets |
| S5 | Cuatro líneas de selección comunes a los dos 4051, más la habilitación | 5 GPIO en lugar de 7 |
| S6 | 2.499 MΩ = 2 MΩ + 499 kΩ (dos piezas comunes de 0.1 %) | Sin un 2.49 MΩ que no encontré en LCSC |
| S7 | Sujeción de PB14 solo al lado negativo (un Schottky a COM) | −1 diodo |
| S8 | c1: inyectar en N1 | Quita 2.7 kΩ del camino sin tocar R_S ni las sujeciones; no añade piezas |
| S9 | Llenar la ventana en 2 MΩ y 20 MΩ con otros R_k | Mismas piezas, mejor error/tolerancia (80 % y 52 % en lugar de 95 % y 77 %) y 1.5× más tolerancia de fuga |

Descartado por no simplificar: quitar el 4051 de sentido (la Ron del 4051 con +0.3–0.4 %/°C supuestos, sin dato de hoja, daría 2200–4400 ppm de deriva con ±5 °C en R_k = 499 Ω y 220–440 ppm en 4.99 kΩ); una sola corriente con gran ganancia (la ventana del ADC no lo permite); la razón con el ADC (0.24 % con la INL linealizada, ya descartada en H §6); un Howland (resistencias de 0.1 % dan R_out ≈ 2.5 MΩ, que arruina el 0.2 µA).

---

## 8. Contradicciones y avisos

1. **«Tensión en vacío ≈ 3.4 V máx.»** (hoja de especificaciones): con la fuente saturada son ≈ 4.75 V (salvo 20 MΩ, 2.0 V). H y el bloque 2 suponían 4.0–4.1 V. No cambia nada, pero hay que corregir la hoja.
2. **«La prueba de diodo se lee por X0»** (DECISIONS 8 oct): X0 ×1 no llega a un LED azul. Leer por X2 ×10.1.
3. **«Lecturas por segundo ≈ 2–5»**: el asiento de ≈ 50 ms en 20 MΩ cabe en esos 200–500 ms por lectura, pero deja de ser despreciable; por eso P34 en 20 MΩ no apaga la fuente en cada ciclo.
4. **«Diodo ≥ 3.5 V a 100 µA»**: S11.4 dio 3.606 V con rail −2 %; nuestro analítico da 3.53 V (BAT54 de hoja máxima) y SPICE 3.63 V para la cadena actual. El margen real es de 0.03–0.13 V; con c1 pasa a 0.37 V.
5. **§9 de H** («≈ 9 líneas» de control del DMM): este bloque usa 5, no 7.
6. La **opción c1 cambia el bloque 1**, cerrado en S11.4: R1 de 2 × 1.1 kΩ a 3 × 510 Ω y el punto de inyección. No se editó 01_diseno ni los HTML; es propuesta.
7. Las corrientes de H para 200 Ω y 2 kΩ (10 mA y 1 mA) con la cadena del bloque 1 eran imposibles: el aviso de DECISIONS del 8 oct se queda corto.

---

## 9. Lo que confirmaría Codex (criterios con margen)

Con el criterio de Keneth: Monte Carlo o peor caso, ≥ 95 % de placas, márgenes realistas, y los fallos marginales de modelo o de criterio se clasifican sin rediseñar.

**C1 · S11.4 reducida con la cadena elegida (c1: R1 = 3 × 510 Ω, inyección en N1, R_S 2.7 kΩ sin cambios).** Repetir solo T2 (ESD ±4 kV contacto y ±8 kV aire, GDT 420/780 V) y T4 (60 V DC y 60 Vrms, fuente apagada y encendida a 1 mA):
- R1 ≤ 50 % de 2 W por pieza y ≤ 80 % de 250 V; TVS ≤ 0.5 W; R_S y zéner como hoy;
- corriente de las sujeciones ≤ 5 mA continuos (hoy 2.6 mA) y separación entre rieles ≤ 10.6 V (S11.4: 10.57 V);
- BAT54 con tensión inversa ≤ 24 V (80 % de 30 V) en ESD y BSS84 con |V_DS| ≤ 40 V;
- corriente de pico en R1 con pulsos: se pide la curva de impulso del MPN (HoCR2512 de 510 Ω) como ya se pide para el 1.1 kΩ.

**C2 · P43 completa en SPICE (TLV2372, BSS138, BSS84, 4051 con Ron y capacidades, BAT54), Monte Carlo:**
- V_set (R1, R2 al 0.1 %, Vos ±4.5 mV), Vth del BSS84 −0.8…−2.0 V, Ron del 4051 60–130 Ω, capacidades ±50 %, riel 4.8–5.0 V;
- compliancia ≥ V_x a fondo + 0.3 V en los rangos de 200 Ω y 2 kΩ en ≥ 95 % de las placas (hoy +0.28 V con c1 y +0.43 V en SPICE nominal);
- margen de fase ≥ 60° en los cinco rangos con la compensación elegida (esquinas de este estudio: ver §3.2);
- arranque al 0.1 % ≤ 1.5 × la tabla del §3.6;
- corriente inicial dentro de ±1 % del nominal (tolerancia de calibración) y deriva 18–28 °C ≤ 300 ppm.

**C3 · Continuidad:**
- cruce del umbral de 50 Ω en ≤ 100 µs con la TVS de 300–900 pF (hoy 15–27 µs), sin rebotes con histéresis HYST = 1;
- recuperación al abrir, ≤ 100 µs;
- umbral sin calibrar ±16 mV en PB14 (±3.2 Ω a 1 mA), ≤ ±1.5 Ω con la calibración de P41.

**C4 · INL a ohmios con la curva real:** repetir el §2 con la INL medida cuando exista; criterio: error/tolerancia ≤ 100 % garantizada y ≤ 85 % calibrada en los seis rangos (hoy 91–95 % y 78–82 %).

**C5 · Fugas del nodo de corriente:** barrer 0.1 / 1 / 10 nA en la pata común del 4051 de fuerza y 0.1 / 1 / 10 nA en el borne (TVS + BAV199): la deriva con 18–28 °C debe ser ≤ 25 % de la tolerancia sobrante (0.85 nA en 2 MΩ, 1.14 nA en 20 MΩ). Si con 1 nA falla, es **marginal de criterio** y se clasifica; no se cambia nada hasta medir el prototipo.

**C6 · Lógica de P34 y P33 (con un modelo de firmware o a mano):**
- V_ext ≥ 20 mV detectada en X2 ×10.1 con ruido ≤ 3 cuentas;
- tensión de ±5 V y de ±60 V DC con la fuente apagada: X2 y X0 no saturan A de forma que oculte la lectura;
- P33 (si se acepta B): relé cerrado ≤ 15 ms y V(t=3 ms) ≥ 0.3 V con puntas al aire frente a < 20 mV en corto.

**C7 · Diodo:** compliancia ≥ 3.5 V + 0.1 V a 100 µA con el LED real de la tabla de S11.4 (3.0 y 3.2 V), corriente ≥ 99 µA; silicio a 1 mA con 0.65 V.

Lo que queda **pendiente de prototipo**, no de simulación: la fuga del 4051 de fuerza a 23 ± 5 °C, el asiento real en 20 MΩ con cables, el offset del COMP7 y la DAC, y la capacidad real de la TVS.

---

## 10. Cómo repetirlo

Trabajo en `C:\b3\work` (ruta corta). Los modelos son los del repositorio (`Simulation_LTSpice\models`: TLV2372, OPA2192/OPAx192); BSS84 y BAT54 salen del `standard.mos` y `standard.dio` de LTspice.

```
cd "S3G4_LAB_rev2.1/03_simulaciones/DMM/estudio_bloque3/scripts"
python calc_b3.py            # compliancia, INL a ohmios, corriente máxima por R_serie
python calc_b3b.py           # dígitos necesarios, deriva, fugas tolerables, diodo, continuidad
python calc_opciones.py      # tabla a / c2 / c1
python calc_prot.py          # esfuerzos con 60 V
python run_compl.py          # compliancia en LTspice
python run_comp.py           # margen de fase con y sin compensar
python run_pm_esquinas.py    # esquinas del margen de fase (tarda ≈ 20 min)
python run_pnp.py            # PNP frente a BSS84
python run_arranque.py       # asiento por rango
python run_cont.py           # continuidad
python run_reg.py            # regulación de carga y de riel
```

Cada script lanza `LTspice.exe -b` sobre un deck generado por `gen_p43.py` y lee el `.raw` con `rawlt.py`. Los decks quedan en `decks_ltspice/` y las salidas en `resultados/`. No se modificó ningún archivo de Codex, `STATE.md`, `DECISIONS.md`, `01_diseno`, los modelos ni las hojas.
