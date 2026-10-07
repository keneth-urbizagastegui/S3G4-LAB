# Rediseño del bloque 1 del DMM: ohmios con la red y borne A

- Autor: Claude Code (ingeniero), 7 oct 2026. **Propone; no decide.** Elige Keneth.
- Parte de `AUDITORIA_CLAUDE_S11_1.md` (fallos 1–3) y del mensaje del coordinador (topología tipo 121GW, diodo tipo ELVIS II y dato de 60 V).
- Todo lo calculado está en `DMM/rediseno_bloque1/` (`scripts/`, `decks/`, `resultados/`). Se simuló en `C:\s11r` con LTspice. No se ha tocado nada de Codex, `STATE.md`, `DECISIONS.md`, `01_diseno`, modelos ni hojas.
- Restricciones que **no** se han cambiado: 50 V DC / 50 Vrms de medida, 230 Vrms 10 s sin daño (V/Ω y A, 60 Hz), rieles ±4.9 V con un máximo de 11 V entre ellos, relé TQ2SA (125 Vac, 2 A, 62.5 VA, suelta ≤ 4 ms), fuente de ohmios ≤ 1 mA (0.2 µA en 20 MΩ) con compliancia de 4.1 V, regla 80 % de tensión y 50 % de potencia, energía o corriente.

## 0. Resumen y recomendación

**Ohmios.** Con una PTC en serie, la corriente de los primeros ciclos la fija la resistencia en frío y la tensión la fija el recorte de la TVS. Eso no se arregla subiendo la PTC de 50 Ω a 200 Ω: la PTC de 200 Ω sigue llevando 1.55 A de pico (1.08 A rms, 235 W) y la prueba de diodo cae a 2.8 V. Sacar la protección de la fuente de los rieles hacia COM y bloquear el diodo de cuerpo **sí arregla los rieles** (0 mA al riel, 9.80 V entre rieles), pero no la PTC, la TVS ni el relé.

**Recomendación (O2): limitador de corriente bidireccional de deplexión en lugar de la PTC.**
- Dos MOSFET de deplexión de 600 V (candidato BSS126, C3288820, 0.13 USD) en serie y opuestos, con una resistencia de fuente que fija el límite en unos 2 mA, más una R_S pequeña y los BAV199.
- La corriente con la red es ≤ 2 mA **en cualquier fase y sin depender de un modelo térmico ni del firmware**: la energía y las corrientes salen de V·I y no de cuánto tarde en dispararse una PTC.
- Resultados con la red (ILIM = 2 mA):
  - pico de potencia por FET 0.65 W, media 0.20 W por FET (con 0.5 W de SOT-23, 41 %);
  - tensión de pico en el FET 324 V (54 % de 600 V);
  - corriente al riel 2 mA (la carga toma 3 mA) y 9.80 V entre rieles;
  - el relé corta 2 mA y sobrevive 10 s sin abrir nunca (C4);
  - sin TVS ni PTC, así que desaparece la fuga de la TVS en el nodo de 4 V;
  - cuesta unos 0.45 USD.
- Prueba de diodo: **4.0 V a 100 µA** (LED) y silicio a 1 mA, con **3.0–3.3 V** disponibles a 1 mA (no llega a 3.5 V salvo que la R del par sea ≤ 450 Ω).
- **Incierto:** la hoja del BSS126 (IDSS, R_on, dispersión) no está en el proyecto. El modelo es conductual y el límite es un parámetro. Hay que verificarlo con la hoja y con el modelo de Infineon antes de cerrar.

**Alternativas, para que elijas:**
- **O1 (PTC 200 Ω + COM + bloqueo):** arregla rieles, pero PTC a 1.1 Arms (235 W), TVS a 13.5 W de media hasta el disparo y diodo a 2.8 V. No lo recomiendo.
- **O3 (tipo 121GW, 2.2 kΩ):** corrientes pequeñas (0.145 A de pico), pero la PTC de LCSC más resistiva cuesta 13.5 USD cada una y el disparo en 10 s no está garantizado: con una energía de disparo de 20/50/100 J, la PTC tarda 1.7/4.2/8.5 s y la resistencia en serie recibe 17/44/88 J. Sin hoja de la PTC no se puede cerrar. No lo recomiendo con estas piezas.
- **O4 (dato, 60 V sin red):** solo resistencias, TVS y R_S a rieles: 0.15 USD, todo con margen a 60 V DC/60 Vrms. **No sobrevive a 230 V.** No se recomienda ni se desaconseja: es decisión de Keneth (RD-10 en ohmios).

**Borne A.** El DF08S solo aguanta si el fusible es rápido y de baja I²t. Con los fusibles 5×20 de 3.15 A de LCSC (I²t de fusión de 4.3 a 8.5 A²s para los rápidos; 43 A²s el temporizado) el DF08S queda al 40–115 % de su I²t con 0.5 Ω de red. **Propuesta: GBU808 (C42406072, 0.20 USD, 175 A / 127 A²s) con un fusible rápido de ≤ 8.5 A²s** (HOLLY 50CF-032H C356446, 4.27 A²s, o Littelfuse 0216 C95689, 6.7 A²s). Eso deja el puente por debajo del 12 % de su I²t. Quitar el puente deja al derivador de 0.1 Ω con 0.4–2.6 J y 51 V en la entrada de B: no lo recomiendo salvo que el derivador tenga energía de pulso garantizada.

## 1. Método y qué es dato

- **Red:** 230 Vrms (325.269 V de pico), 60 Hz, con 1 mΩ de impedancia. Se simulan 5 ciclos (83 ms) para los parámetros por ciclo y 1 s para el disparo de la PTC. El caso de fase 0 y el de fase 90° dan lo mismo (el circuito es casi resistivo).
- **Circuito común:**
  - relé cerrado con R_on = 0.1 Ω y C_off = 1 pF, como en S11.1;
  - fuente P43 abstracta (fuente de 1 mA, compliancia 4.1 V);
  - BSS84 con su diodo de cuerpo (modelo de Codex, IS = 1 nA);
  - protección reducida de los pines del 4051 y del TLV2372 (Codex);
  - rieles ±4.9 V con 1 µF y 3 mA entre ellos; el regulador solo entrega.
  - Se reutilizó el modelo del BAV199 y la TVS (rodilla central 14.0 V, 19.9 V a 20.1 A, hoja p. 3).
- **Referencia de validación:** con la PTC de 50 Ω y R_S = 100 Ω, la tensión de diodo a 1 mA sale 3.95 V, frente a los 3.90 V del acta de Codex.
- **PTC de ohmios:** no hay hoja de la PTCEL67R501 ni de la PTCEL67R152. Se simuló con R en frío fija (200 Ω, 250 Ω, 570 Ω) y con un modelo térmico sin refrigeración (θ = E/E_disparo; al llegar a 1 pasa a 35 kΩ). La **energía de disparo (20 y 100 J) y los 35 kΩ en caliente son supuestos míos**. Como referencia, la hoja de la PTCTL (p. 1) da 1 s a 1 A (~50 J en 50 Ω).
- **Limitador de deplexión:** modelo conductual I = I_LIM·tanh(V/(I_LIM·R_on)), con R_on de la pareja = 700 Ω (450 y 1000 Ω para la sensibilidad del diodo). No sale de una hoja.
- **Relé al abrir:** se informa la corriente de pico (peor fase) y la corriente 1 ms después de un cruce por cero (si el firmware sincroniza con ±0.3 ms).
- **LCSC:** precios y existencias de la herramienta `pcbparts` (no se descargó nada). Los valores de I²t de fusión de los fusibles son los de la ficha del catálogo, **no** una hoja leída.

## 2. Ohmios: topologías

Cuatro topologías: O1, O2, O3 y la referencia O0.

### 2.1 O0 (referencia, para ver qué se arregla)

PTC 200 Ω → TVS SMAJ12CA a COM (N1) → R_S 330 Ω → N2 con BAV199 a ±4.9 V, como en S11.1 pero con la PTC de 200 Ω.
- I_PTC = 1.55 A de pico, 1.08 A rms.
- Por R_S pasan 25 mA y **todo va a los rieles**: rp = 12.9 V, rn = −11.9 V, **18.6 V entre rieles**.
- Con un Zener de 5.6 V a COM en cada riel el span baja a 10.6 V, pero el Zener disipa los 25 mA a 5.6 V.

### 2.2 O1: PTC de 200 Ω, protección a COM y diodo de cuerpo bloqueado

```
V/Ω ─relé─ PTC 200 Ω ─ N1 ─ R_S 330 Ω ─ N2c ──── DBLK (BAV199, ánodo n2s) ──── n2s ─ BSS84 / 4051 ch6
                        │                  │
                     TVS12CA a COM    BAV199 de COM a N2c (sujeta lo negativo a −0.7 V)
```
- Lo positivo lo bloquea DBLK (ve 14 V, de 85 V); lo negativo se sujeta a COM. **No entra corriente a los rieles** (0.00 mA al riel, **9.80 V entre rieles**).
- Cuesta más energía en la TVS y la PTC que en el diseño original.

### 2.3 O2: limitador bidireccional de deplexión (recomendada)

```
V/Ω ─relé─ [FET1 D→S ─ R ─ S←FET2]  ─ N1 ─ R_S 47 Ω ─ N2 ──┬── BAV199 a rp          (rieles ±4.9 V)
          (gates cruzadas: G1 a S2, G2 a S1)                 ├── BAV199 de COM a N2   (negativo a COM)
                                                              └── n2s: BSS84 / 4051
                  + Zener 5.6 V (BZT52C5V6) de rp a COM y de COM a rn, solo como sumidero
```
- **Elemento limitador:** dos depletion MOSFET de 600 V con un solo R que fija el límite. La corriente de la fuente de 1 mA pasa sin saturar; con la red satura.
- **Sin TVS ni PTC.** Lo negativo se sujeta a COM (no al riel), así que el nodo de 4 V ve BAV199 a 0.9 V y 4 V de inversa y no a 8.9 V.
- El límite lo fija la pareja FET + resistencia, y el modelo lo trata como parámetro.

### 2.4 O3: tipo 121GW (PTC + resistencia, 2.2 kΩ), con diodo tipo ELVIS

- Fuente: `02_referencias/dmm_121gw.html` §5 (PTC4 1.2 kΩ + R17 1 kΩ = 2.2 kΩ, de la que "la PTC disipa ≈ 24 W en el primer instante").
- Piezas de LCSC:
  - la PTC más resistiva con stock es la **PTCEL67R152UBE, 570 Ω, 800 V, 32 mA de mantenimiento (C22414522, 13.5 USD, 50 uds.)**; hacen falta 2 en serie (1140 Ω, 27 USD) y una R de 1 kΩ;
  - TVS SMAJ12CA a COM en N1 y R_S 3.3 kΩ a rieles en N2, con Zener de sumidero.
- Prueba de diodo como el ELVIS II: silicio a 1 mA (lo que dé la compliancia), LED a 100 µA.

### 2.5 O4 (dato): 60 V sin supervivencia a la red

R fija de 2.2 kΩ (2 × 1.1 kΩ en 2512), TVS a COM, R_S 3.3 kΩ a rieles y Zener de sumidero. Sin PTC. Se desconecta el efecto de RD-10 en ohmios.

## 3. Resultados de ohmios

### 3.1 Con la red de 230 Vrms (peor fase; detalle por caso en `resultados/campana*.json`)

| Magnitud | O0 (ref.) | O1 | O2 (ILIM 2 mA) | O3 (2 PTC 570 + 1 kΩ) |
|---|---|---|---|---|
| Corriente de pico / rms (A) | 1.55 / 1.08 | 1.55 / 1.09 | 0.002 / 0.002 | 0.145 / 0.102 |
| Potencia media en la PTC (frío) | 235 W | 236 W | no hay PTC | 11.8 W (6 W cada una) |
| Energía en la PTC por ciclo | 3.9 J | 3.9 J | no hay PTC | 0.20 J |
| Potencia pico / media en la TVS | 22.3 / 13.7 W | 22.4 / 13.5 W | no hay TVS | 2.0 / 1.23 W |
| Potencia en el elemento limitador | n.a. | n.a. | 0.65 W pico; 6.8 mJ por ciclo (0.41 W de media entre los 2 FET) | R de 1 kΩ: 10.3 W |
| Potencia en R_S (pico / media) | 0.2 / 0.02 W | 0.55 / 0.26 W (R_S 330) | 0.0002 W | 0.027 / 0.024 W |
| Corriente al riel positivo | 25 mA | 0 | 2 mA | 2.9 mA (diodo de cuerpo) |
| Corriente al riel negativo | 23 mA (sujeción del 4051) | 0 | 0 (se sujeta a COM) | 1.6 mA (sujeción del 4051) |
| Tensión rp / rn / entre rieles | 12.9 / −11.9 / **18.6 V** | 4.9 / −4.9 / **9.80 V** | 4.9 / −4.9 / **9.80 V** | 4.9 / −4.9 / **9.80 V** |
| Corriente que corta el relé (pico, peor fase) | 1.55 A | 1.55 A | 2 mA | 0.145 A (23 VA rms) |
| Corriente 1 ms tras un cruce por cero | 0.54 A | 0.53 A | 2 mA | 0.050 A |

Notas:
- **Rieles:** el span es la diferencia entre rp y rn. La carga de 3 mA se compensa con lo que entra; el riel solo sube si entra más de 3 mA. En O3, 2.9 mA es el 97 % de la carga: sin margen. El Zener lo absorbe (Zener p: sin conducción en la simulación).
- **O2 con otros límites** (con Zener de sumidero y R_S 47 Ω):

| I_LIM | Potencia pico en el FET | Media entre los 2 FET | Por FET (de 0.5 W) | Entre rieles |
|---|---|---|---|---|
| 1.5 mA | 0.49 W | 0.31 W | 0.15 W (31 %) | 9.80 V |
| 2 mA | 0.65 W | 0.41 W | 0.20 W (41 %) | 9.80 V |
| 3 mA | 0.97 W | 0.61 W | 0.31 W (61 %) | 9.80 V |
| 5 mA | 1.62 W | 1.0 W | 0.5 W (100 %) | 10.5 V (Zener 1.8 mA) |
| 10 mA (R_S 100 Ω, con Zener) | 3.2 W | n.a. | n.a. | 10.6 V |

  El FET de SOT-23 (0.5 W) **solo cumple el 50 % hasta ≈ 2.4 mA**. Con una IDSS de 7–21 mA la resistencia de fuente es **obligatoria** para bajar el límite a unos 2 mA.
- **Tensión sobre el elemento limitador de O2:** pico de 324.4 V (54 % de 600 V). Pasa el 80 %.

### 3.2 Disparo de la PTC con la energía de disparo supuesta (simulado 1 s, `th_*.cir`)

| Caso | Disparo | E en la TVS hasta el disparo | Corriente después del disparo (pico / rms) |
|---|---|---|---|
| O1, E = 20 J | 82 ms | 1.12 J | 20 mA / 7 mA |
| O1, E = 100 J | 0.41 s | 5.6 J | 46 mA / 18 mA (aún bajando) |
| O3, E = 20 J | 1.7 s (sale por P = 11.8 W) | 2.1 J | n.a. |
| O3, E = 50 J | 4.2 s | 5.2 J | n.a. |
| O3, E = 100 J | 8.5 s | 10.5 J | n.a. |

- Resistencia en serie de 1 kΩ en O3: 10.3 W hasta el disparo → 17 J / 44 J / 88 J para 20 / 50 / 100 J. Las resistencias de 2512 no están hechas para eso.
- Con la PTC caliente a 35 kΩ: el estado estable es de 6 mA rms (O1: TVS 0.04 W, PTC 1.4 W); el relé corta 3 mA.
- La TVS SMAJ12CA aguanta 400 W en 10/1000 µs y 1 W en continuo (p. 2); 13.5 W durante 0.4 s no está cubierto por ninguna cifra de la hoja que haya podido leer (la Fig. 3 de la p. 4 es una gráfica).

### 3.3 Prueba de diodo y compliancia (barrido en continua, `dc2_*.cir`)

Tensión máxima del DUT en que la fuente aún da el 99 % de la corriente:

| Opción | A 1 mA | A 100 µA | I con un diodo de silicio de 0.65 V |
|---|---|---|---|
| Original (PTC 50 Ω, R_S 100 Ω; referencia) | 3.95 V | 4.08 V | 1.0 mA |
| O1 (PTC 200 Ω, R_S 330 Ω, con DBLK) | **2.81 V** | 3.37 V | 1.0 mA |
| O2 (R pareja 450 / 700 / 1000 Ω) | 3.56 / **3.29** / 2.97 V | 4.05 / **4.03** / 4.00 V | 1.0 mA |
| O3 (2 PTC 570 + 1 kΩ, R_S 3.3 kΩ) | n.a. (5.4 kΩ × 1 mA) | **3.56 V** | **0.60 mA** |
| O4 (2.2 kΩ, R_S 3.3 kΩ) | n.a. | 3.55 V | 0.60 mA |

- RD-08 (≥ 3.5 V a 1 mA) solo lo cumple el original y O2 con R_pareja ≤ 450 Ω (poco probable).
- **Con el esquema del ELVIS II** (silicio a 1 mA, LED a 100 µA), O2, O3 y O4 dan ≥ 3.5 V a 100 µA para LED. En silicio, O3 entrega 0.60 mA (el diodo de 0.65 V cae 10 mV frente a 1 mA).
- **Relajar RD-08 a 3.0 V a 1 mA** cubre O2 (con R ≤ 700 Ω) y deja a O1 en 2.8 V. Con 3.0 V se cubren LED rojos, amarillos y verdes; los azules y blancos (≈ 3 V a 1 mA) quedan al borde. Con el esquema de 100 µA no hace falta relajar nada.

### 3.4 Fuga en el nodo de medida (C5: ≤ 0.2 nA, es decir, 1000 ppm de 0.2 µA)

Fugas de los modelos a 1, 2 y 4 V (`leak.py`):
- BAV199: ≈ 0.4–0.6 pA cada uno (modelo de NXP, con IS = 0.8 fA) → **2 pA entre los dos de un nodo, 10 ppm**.
- El 1 nA que sale en el total es el diodo de cuerpo del BSS84 del modelo de Codex (IS = 1 nA), **artefacto del modelo** y no una fuga del diseño.

Fugas con datos de hoja, que son lo que se puede garantizar (no se encontró un dato a 4 V):
- **BAV199:** 5 nA máx. y 3 pA típ. a 75 V, 25 °C; 80 nA máx. a 150 °C (p. 3). A 4–9 V no hay cifra garantizada. Escalando por √V, el máximo sería ~1.2 nA a 4 V y ~1.7 nA a 9 V (**no garantizado, solo orden de magnitud**).
- **SMAJ12CA:** 5 µA máx. a VRWM = 12 V (p. 3); el catálogo de LCSC dice 1 µA. A 4 V no hay dato.
- **74HC4051** (si hay un canal sobre N2 o sobre vin): ±0.1 µA por canal apagado y ±0.4 µA en total a 25 °C (p. 9). **Esto es 500 veces el límite de C5, y es independiente de la protección.**

| Elementos en el nodo de 4 V | O1 | O2 | O3 y O4 |
|---|---|---|---|
| TVS a COM (4 V) | sí | **no** | sí |
| BAV199 a COM (inversa 4 V) | sí | sí | no |
| BAV199 al riel positivo (inversa 0.9 V) | no | sí | sí |
| BAV199 al riel negativo (inversa 8.9 V) | no | no | sí |
| Canal del 4051 en n2s | sí | sí | sí |
| Fuga típica estimada (modelos) | ≈ pA + TVS | **≈ 1 pA** | ≈ pA + TVS |
| Fuga máxima extrapolada (sin garantía) | ≈ 1 nA + TVS | ≈ 1.8 nA | ≈ 3 nA + TVS |

Conclusión sobre la fuga:
- **Ninguna opción puede garantizar 0.2 nA con las hojas.** O2 es la que menos elementos pone en el nodo y evita la TVS, que es el elemento sin dato.
- **Propuesta de criterio para C5**, con el criterio de Keneth de «que funcione» (≥ 95 % de placas):
  - fuga típica ≤ 20 pA a 25 °C (10 ppm, 100× de margen);
  - fuga máxima extrapolada ≤ 0.2 nA solo a 25 °C;
  - se mide en el prototipo con 20 MΩ conocidos (así se calibra el offset de fuga, que es estable a temperatura constante);
  - se **quita el canal 6 del 4051 de N2** (±0.1 µA).
- El canal que mide vin (X0) tiene el mismo problema (±0.1 µA por canal): es de S11b, pero convendría decidirlo ya.

### 3.5 Relé

- **Relé que corta con la red.** La hoja (C46047, p. 6) da 125 Vac, 2 A y 62.5 VA; con 230 V la tensión **no cumple ninguna opción**.

| Opción | Corriente al cortar | VA a 230 V | Frente a 62.5 VA |
|---|---|---|---|
| O0 / O1 (antes de que dispare la PTC) | 1.55 A pico, 1.08 A rms | 250 VA | **4×** |
| O1 después del disparo | 6 mA rms (20–46 mA al inicio) | 1.4 VA | 2 % |
| O2 | 2 mA, en cualquier fase | 0.46 VA | 0.7 % |
| O3 antes del disparo | 0.145 A pico, 0.10 A rms | 23 VA | 37 % |
| O3 después del disparo | 6 mA | 1.4 VA | 2 % |

- Con corrientes por debajo de unos 10 mA el contacto no arrastra arco (criterio general de corriente mínima de arco de los contactos de plata, **sin dato de la hoja**).
- **Dos contactos en serie** (el TQ2SA es de dos polos; se usan los dos NO en serie) reparten 230 V en 115 V cada uno (92 % de 125 V, sigue sin pasar el 80 %). Es un paliativo y no una solución.
- **Firmware:** un relé que se abre después del disparo requiere saber cuándo disparó la PTC. Con la red aplicada, el nodo vin no cambia al disparar; solo se ve por la corriente. Con O2 el firmware no interviene.

### 3.6 Coste en LCSC (precios a una unidad, existencias de la herramienta)

| Opción | Piezas principales | Coste |
|---|---|---|
| O1 | PTCEL67R501 (C28219210, **35 uds.**, 2.89 USD), SMAJ12CA (C78399, 0.045 USD), 2 × BAV199, R de 330 Ω de 0.5 W | ≈ 3.1 USD |
| O2 | 2 × BSS126 (C3288820, 481 uds., 0.13 USD; o C2987085, 4242 uds., 0.17 USD), R de fuente, 2 × BAV199, 2 × BZT52C5V6 (C19077402, 0.017 USD) | ≈ 0.45 USD |
| O3 | 2 × PTCEL67R152UBE (C22414522, **50 uds.**, 13.5 USD cada una), 1 kΩ, SMAJ12CA, R_S 3.3 kΩ, BAV199 | ≈ 27.5 USD |
| O4 | 2 × 1.1 kΩ 2512, SMAJ12CA, R_S 3.3 kΩ, 2 × BAV199, Zener | ≈ 0.15 USD |
| Original (S11.1) | PTCTL4MR500 (C3760522, **32 uds.**, 1.99 USD), SMAJ12CA, R_S, 2 × BAV199 | ≈ 2.2 USD |

## 4. Comparación

| Criterio | O1 | O2 (recomendada) | O3 (121GW) | O4 (60 V) |
|---|---|---|---|---|
| Corriente/energía en el elemento limitador (≤ 50 %) | PTC 1.08 Arms; **Imax de la PTCEL desconocida (PTCTL: 1 A)** | FET 0.20 W de 0.5 W (41 %) | PTC 6 W cada una durante hasta 8 s | R 0.48 W cada una (48 % de 1 W) a 60 V |
| TVS (≤ 50 %) | 22 W pico; 13.5 W de media hasta el disparo (frente a 1 W continuo) | no hay TVS | 2.0 W pico; 1.2 W de media | 0.25 W DC |
| Tensión en la pieza más expuesta (≤ 80 %) | BAV199 de bloqueo: 14 V de 85 V | FET: 324 V de 600 V (54 %) | TVS: 14 V | TVS: 14 V |
| Corriente al riel / tensión entre rieles | 0 mA / 9.80 V | 2 mA / 9.80 V | 2.9 mA (97 % de la carga) / 9.80 V | 2.9 mA / 9.80 V |
| Relé corta | 1.55 A (250 VA) antes del disparo | 2 mA | 0.145 A (23 VA) | 21 mA a 60 V |
| C4 (sobrevivir 10 s sin abrir el relé) | **depende de t_disparo de la PTC** | **sí, por construcción** | depende de t_disparo (1.7–8.5 s) | n.a. (no sobrevive 230 V) |
| Diodo | 2.8 V a 1 mA / 3.37 V a 100 µA | 3.0–3.3 V a 1 mA / 4.0 V a 100 µA | 0.6 mA para Si / 3.56 V a 100 µA | igual que O3 |
| Fuga en el nodo (típica) | pA + TVS | ≈ 1 pA | pA + TVS | pA + TVS |
| Coste | ≈ 3.1 USD | ≈ 0.45 USD | ≈ 27.5 USD | ≈ 0.15 USD |
| Incertidumbre principal | PTCEL sin hoja | hoja y modelo del FET | PTCEL sin hoja; resistencias de pulso | ninguna a 60 V |

## 5. Borne A

### 5.1 Datos

- **Red 230 Vrms, 60 Hz.** Impedancia de red de 0.5, 1 y 2 Ω; fusible de 40 mΩ en serie; derivador de 0.1 Ω en paralelo con el puente (con + y − unidos, dos diodos en serie por sentido).
- **Fusible:** se supone un corto hasta que se alcanza la I²t de fusión del fusible; después se mantiene la corriente hasta I²t total = k × I²t de fusión (k = 1, 2, 3; el arco de un fusible rápido de 250 V suma de 1 a 2 veces la I²t de fusión, supuesto mío). **Es conservador**: un fusible real de alto poder de corte limita el pico (corriente de corte) y no deja que la corriente llegue a los 570 A de la red.
- **Puentes:**
  - **DF08S** (actual): 50 A en 8.3 ms, 10.4 A²s (hoja p. 2).
  - **GBU808** (C42406072, 0.20 USD): 175 A, I²t = 175² × 8.3 ms / 2 = **127 A²s** (la I²t es **derivada de la IFSM** de la ficha del catálogo, no un valor de hoja). Vf 1.1 V a 8 A.
  - **GBU1510** (C350460, 0.23 USD): 220 A → 200 A²s.
  - **GBU2510** (C840743, 0.45 USD): 300 A → 373 A²s.
- **Fusibles de LCSC** 5×20 de 3.15 A, cerámicos, 250 V (datos de la ficha del catálogo):

| Fusible | LCSC | I²t de fusión (A²s) | Poder de corte | Precio | Stock |
|---|---|---|---|---|---|
| HOLLY 50CF-032H | C356446 | **4.27** | 1.5 kA @250 VAC | 0.14 USD | 280 |
| Littelfuse 0216 3.15 MXP | C95689 | **6.7** | 1.5 kA | 0.20 USD | 809 |
| Conquer VBS UBM | C5175346 | 7.14 | 1.5 kA @250 VAC | 0.11 USD | 432 |
| Eaton BK/S501-3.15-R | C3156611 | 8.1 | 1.5 kA | 0.24 USD | 1000 |
| SETsafe SCF520F | C50386930 | 8.5 | 5 kA @250 VAC | 0.15 USD | 840 |
| Littelfuse 0215 (temporizado) | C142723 | 43.3 | 1.5 kA @250 VAC | 0.19 USD | 3844 |
| Hongda 52TC T (temporizado) | C47278823 | 469 | 35 A | 0.06 USD | 530 |

  Con 0.5 Ω la corriente de cortocircuito de la red es de 600 A, que es el 40 % de 1.5 kA.

### 5.2 Resultados (envolvente sobre la fase de cierre; `borneA.py`, `resultados/borneA.csv`)

Red de 0.5 Ω. Con 1 y 2 Ω las corrientes bajan (302 / 156 A de pico total) y las I²t del puente bajan un 10–30 %.

| Fusible (I²t) | Puente | Pico por el puente (A) | I²t del puente para k = 1 / 2 / 3 (A²s) | Límite del puente / 50 % | ¿Pasa? |
|---|---|---|---|---|---|
| HOLLY (4.27) | DF08S | 386 | 2.1 / 4.2 / 6.1 | 10.4 / 5.2 | k ≤ 2 sí; k = 3 no |
| Littelfuse (6.7) | DF08S | 386 | 3.3 / 6.4 / 9.5 | 10.4 / 5.2 | **no** (k ≥ 2) |
| SETsafe (8.5) | DF08S | 386 | 4.2 / 8.1 / 11.9 | 10.4 / 5.2 | **no** (k ≥ 2) |
| HOLLY (4.27) | GBU808 | 423 | 2.5 / 4.9 / 7.3 | 127 / 64 | sí (≤ 12 %) |
| Littelfuse (6.7) | GBU808 | 423 | 3.9 / 7.5 / 11.2 | 127 / 64 | sí (≤ 9 %) |
| SETsafe (8.5) | GBU808 | 423 | 4.9 / 9.4 / 14.2 | 127 / 64 | sí (≤ 12 %) |
| Temporizado (43.3) | DF08S | 386 | 20 / 40 / 60 | 10.4 / 5.2 | **no** |
| Temporizado (43.3) | GBU808 | 423 | 24 / 47 / 71 | 127 / 64 | k = 1 y 2 sí; k = 3 (56 %) no |
| Cualquiera | **sin puente** | n.a. | derivador: 0.46 / 0.90 / 1.31 J (HOLLY), 0.90 / 1.75 / 2.59 J (SETsafe) | | depende del derivador |

- El pico por el puente es el mismo para todos los fusibles porque la fusión ocurre en 20–50 µs a esa corriente. **La I²t de fusión, y no el pico, decide.**
- **Sin puente,** la tensión en el derivador llega a **51 V (0.5 Ω), 29 V (1 Ω) y 15 V (2 Ω)** y la energía en 0.1 Ω a 0.4–2.6 J. Un 2512 de 1 W no tiene energía de pulso garantizada en esos valores.
- **Con puente,** el derivador pasa a un máximo de 18 V (DF08S) o 15 V (GBU808) y 0.1–0.5 J.

### 5.3 Opciones

- **B1 (recomendada): GBU808 + fusible rápido de ≤ 8.5 A²s.** El puente queda al 12 % de su I²t, mucho más holgado que el DF08S con los mejores fusibles. Cuesta 0.10 USD más. La huella de la GBU es de agujero pasante (hay que revisarla en la placa).
- **B1′: mantener el DF08S con el HOLLY 50CF-032H (4.27 A²s).** Pasa solo si el arco aporta ≤ 1 vez la I²t de fusión (k ≤ 2): sin margen. No lo recomiendo.
- **B2: sin puente, solo protección en B (R + sujeción).** Hay que elegir el derivador por su energía de pulso (0.4–2.6 J) y poner una R_B en serie con la entrada de B.
- **Pendiente que afecta a las dos:** en el modelo del bloque 1, el canal del derivador entra al 4051 **sin resistencia en serie** (`Xh4 shunt rp rn`). Con 15–18 V en el derivador (puente) o 51 V (sin puente), la sujeción del 4051 llevaría cientos de mA. **Hace falta una R_B de ≥ 10 kΩ** (1 mA a 15 V; 4.6 mA a 51 V): el offset de 0.3 nA × 10 kΩ = 3 µV, sin importancia. Y como la corriente al riel no tiene sumidero, el Zener de sumidero de los rieles (§2.3) también sirve aquí.

## 6. Qué queda incierto

1. **PTCEL67R501 y PTCEL67R152:** no hay hoja en el proyecto. Faltan la Imax, la energía y el tiempo de disparo (decide O1 y O3), la tolerancia de R25 y la R en caliente (35 kΩ es un supuesto).
2. **Limitador de deplexión (O2):** falta la hoja del BSS126 (IDSS, V_p, R_on, dispersión y coeficiente de temperatura) y su modelo SPICE. El límite se tomó como parámetro. Con IDSS de 7–21 mA hay que bajar el límite con una resistencia, y la dispersión hace que el límite real caiga entre 1.3 y 4.5 mA (estimación mía): el mínimo debe superar 1 mA (la fuente) con margen, y el máximo debe seguir ≤ 2.4 mA para el 50 % de potencia del SOT-23.
3. **ESD (P6):** no se ha simulado. O2 quita la TVS, que era el elemento que absorbía el pulso de ±4 kV en N1; puede necesitar una TVS más (con su fuga) o un FET de más tamaño.
4. **Relé a 230 V:** la tensión supera los 125 Vac de la hoja en todos los casos. Con ≤ 10 mA no debería formar arco, pero eso no es dato de hoja. Se puede consultar al fabricante o poner los dos contactos en serie.
5. **Fuga:** ninguna cifra de la hoja la garantiza (§3.4), y el 4051 domina con ±100 nA por canal.
6. **Fusibles:** la I²t es la del catálogo (no se leyó una hoja) y falta el factor de arco k y la curva de corriente de corte. Mi simulación es conservadora.
7. **Puente:** R_s = 15–20 mΩ por diodo es un supuesto. La I²t de la GBU808 es derivada de la IFSM (para pulsos de menos de 1 ms la hoja no la garantiza).
8. **Temperatura:** no se ha barrido (la PTC, el límite del FET y las fugas dependen de ella).

## 7. Qué debería confirmar la campaña de Codex

1. **O2 con el modelo real del BSS126** (el de Infineon), con el caso peor: IDSS y V_p en los extremos y temperatura de 0 a 70 °C. Informar de: I_LIM mínima y máxima, V_DS, potencia por FET en 10 s (con la temperatura de la unión), tensión de diodo a 1 mA y a 100 µA, y la corriente que corta el relé.
2. **Red de 230 Vrms durante 10 s en O2**, con el relé sin abrir nunca (C4), con los rieles encendidos y apagados (P4). Los BAV199 deben conducir poco (el modelo de sujeción interna de Codex les roba la corriente: informar de la repartición).
3. **ESD a ±4 kV** con O2 (P6) y, si hace falta, con una TVS en N1.
4. **Fugas** con la hoja del 4051 (p. 9) y sin el canal 6 sobre N2.
5. **Borne A:** repetir P5 con el GBU808 y un fusible de 4.3–8.5 A²s (sin suponer que el fusible no abre), con R_B de 10 kΩ y sin canal directo del derivador.
6. **Relanzar S11.1 solo con O2** (no con O1 ni O3, salvo que Keneth los pida): P1 (fuga y diodo), P3 (red en ohmios, relé cerrado, sin abrir nunca), P4 y P6.

## 8. Decisiones que son de Keneth

1. **Forma de la prueba de diodo:** silicio a 1 mA y LED a 100 µA (como el ELVIS II) o relajar RD-08 a 3.0 V a 1 mA. O2 lo cumple en el primer caso.
2. **Criterio de fuga (C5):** pasar de «0.2 nA garantizados» a «fuga típica ≤ 20 pA y se mide en el prototipo».
3. **Relé a 230 V sobre una hoja de 125 Vac:** aceptar el riesgo, poner dos contactos en serie o consultar al fabricante.
4. **Dato (no recomendado ni desaconsejado): relajar RD-10 en ohmios a 60 V sin daño**, sin supervivencia a la red, como el ELVIS. Con O4 todo cumple los márgenes con 0.15 USD y sin PTC ni limitador:
   - a 60 V DC: 20.9 mA, R de 2.2 kΩ a 0.96 W (0.48 W cada una de 1.1 kΩ), TVS a 0.25 W, 9.80 V entre rieles;
   - a 60 Vrms: 21.7 mA rms, TVS 0.23 W, 9.80 V entre rieles, el relé corta 8 mA;
   - **con 230 V no sobrevive** (22 W en la resistencia).

## 9. Archivos (`DMM/rediseno_bloque1/`)

- `scripts/`:
  - `gen.py`: generador de decks y métricas;
  - `rdlib.py`: lector `.raw` y ejecución;
  - `run1.py`, `campana.py`, `campana2.py`: casos de red;
  - `dc_diodo2.py`: compliancia y diodo;
  - `leak.py`: fuga;
  - `borneA.py`: borne A.
- `decks/`: los `.cir` de LTspice (`c1_*` red, `th_*` disparo térmico, `dc2_*` diodo, `lk_*` fuga).
- `resultados/`: `campana1.json`, `campana2.json`, `dc_diodo2.json`, `leak.json`, `borneA.json`, `borneA.csv`, `o4_60Vrms.json`.
- Reejecución: copiar `scripts/` a una ruta corta (p. ej. `C:\s11r`) y ejecutar `python campana.py`, `campana2.py`, `dc_diodo2.py`, `leak.py` y `borneA.py`.
