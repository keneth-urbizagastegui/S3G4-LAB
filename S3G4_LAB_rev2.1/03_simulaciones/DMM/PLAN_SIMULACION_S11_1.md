# Plan de simulación S11.1 — DMM, bloque 1: bornes y protección

- Autor: Claude Code (auditor), 7 oct 2026. Ejecuta: Codex. Audita: Claude.
- Contrato de `ENCARGO_CODEX_S11_1.md`. Sustituye a `PLAN_SIMULACION_S11a.md` (aparcado: Keneth decidió avanzar por bloques).
- **Lee antes:**
  - `ai-context/DECISIONS.md`, entradas del 7 oct: D1–D8, «se avanza por bloques» y «opción B2»;
  - `S3G4_LAB_rev2.1/01_diseno/dmm_rev21.html` §3 ①–②, §5 y §7. Donde no coincida con este plan, **manda este plan**: H se actualiza al cerrar el bloque;
  - para el método de protección: `../CH1_entrada/PLAN_SIMULACION_S2b.md` y su acta.

## 0. Qué decide este bloque

Que los tres bornes aguantan sin daño lo que pide RD-10 y que la protección no estropea la medida:
- 50 V DC / 50 Vrms en medida normal;
- **230 Vrms durante 10 s** en cualquier borne y en cualquier modo, también con el DMM apagado;
- ESD de ±4 kV por contacto y ±8 kV por aire.

La exactitud de cada función es de los bloques siguientes. Aquí solo se mide el error que **añade** la protección: fugas y caídas.

## 1. Circuito

COM es el punto estrella y la masa del equipo (RD-05). Los rieles del DMM son ±4.90 V detrás de su interruptor de carga (P22).

1. **Borne V/Ω, camino de tensión** (sin cambios respecto a H):
   - R_PROT, 3 × 33.0 kΩ en 1206 → nodo X0, con un BAV199 a ±4.9 V.
   - Divisor de 3 × 3.00 MΩ (1206) – toma ÷10 – 900 kΩ – toma ÷100 – 100 kΩ – COM. La toma ÷10 lleva su BAV199 a ±4.9 V.
   - Compensación en C0G: 100 pF / 630 V con 3.3 kΩ en serie sobre cada 3 MΩ; 330 pF sobre 900 kΩ; 3.0 nF sobre 100 kΩ.
   - X0, X1 y X2 terminan en el 74HC4051 (modelo `SWI1`, 8 instancias) y en la entrada de un OPA2188 (modelo de TI). Basta con el OPA2188 como seguidor.
2. **Borne V/Ω, camino de ohmios (opción B2, nuevo):**
   - V/Ω → **relé TQ2SA-5V-Z** (contacto NO; abierto salvo en Ω, diodo y continuidad).
   - → **PTC PTCTL4MR500SBE** (Vishay, C3760522, 600 V, 35 Ω mín. en frío, mantenimiento 50 mA, disparo 140 mA).
   - → nodo N1, con una **TVS SMAJ12CA** bidireccional a COM (C78399).
   - → **R_S**, que se barre en {100, **330**} Ω (1206).
   - → nodo N2, con un BAV199 a ±4.9 V.
   - → elemento de paso de la fuente P43 (en este bloque, el BSS84, con la fuente en 1 mA, 1 µA o apagada).
   - Modelos:
     - relé: genérico como en el osciloscopio (Ron 0.1 Ω, Coff 1 pF), con un retardo de suelta de 3 ms;
     - PTC: un modelo térmico simple (R(T) por tramos con la masa térmica que deduzcas de la curva de disparo de la hoja). Dilo y cítalo;
     - TVS: la curva de su hoja.
3. **Borne A:**
   - A → fusible cerámico de 3.15 A (resistencia de 40 mΩ; la apertura **no** se simula) → derivador de 0.100 Ω → COM.
   - **DF08S** en paralelo con el derivador, con + y − unidos. Modelo: 4 diodos ajustados a la hoja del DF08S.
   - Aviso de fusible (P32): 10.0 MΩ desde A, antes del fusible, hasta X5, con el BAV199 de X5 a ±4.9 V.
4. **Rieles:**
   - Encendido: ±4.9 V con 1 µF y la carga típica del DMM (≈ 3 mA).
   - **Apagado:** interruptor de carga abierto con 1 µF y sin carga. Dos casos: sin diodo de cuerpo hacia el riel principal, y con él (el riel principal cargado como en el osciloscopio).

## 2. Hojas y modelos

En el proyecto (los dejó Keneth): `opa2188.pdf` y su modelo, `BSS84.pdf`, `DF08S.pdf`, `BAV199.pdf`, `74HC_HCT4051.pdf`, `C46047.pdf` (TQ2SA) y `prod_2022_2421-078207-rectifier-diode-1n4007-smamic.pdf`.

**Faltan** las hojas de la PTCTL4MR500SBE y de la SMAJ12CA. Si no están al empezar:
- usa los datos de la ficha de LCSC citados en §1 y márcalo;
- deja la PTC y la TVS parametrizadas para repetir cuando lleguen las hojas.

No descargues nada.

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| P0 | Datos de las hojas | Tensión máxima, potencia o energía de pulso y corriente de cada pieza expuesta. Fuga de la TVS y de los BAV199 a 4 V. Tabla con página |
| P1 | Medida normal | ±50 V DC y 50 Vrms (60 Hz y 20 kHz) en V/Ω en cada toma: corrientes por los BAV199. En ohmios a 1 mA, la tensión disponible en V/Ω (el diodo hasta ≈ 4 V). **Error añadido**: fuga de la TVS y de los BAV199 en N1/N2 con la fuente en 1 µA y 0.2 µA (ppm) |
| P2 | Red en V/Ω, modo tensión | 230 Vrms, 10 s, relé abierto, rieles encendidos. Por pieza: tensión de pico, potencia media y energía. Corriente a cada riel |
| P3 | Red en V/Ω, modo ohmios | Relé cerrado al conectar la red, en el pico y en el cruce por cero. El firmware abre el relé a los 20 ms, a los 100 ms o nunca. PTC: tiempo hasta el disparo. TVS: energía por semiciclo y total. Corriente por R_S y el BAV199 de N2 hacia el riel. R_S × 2 |
| P4 | Red con el DMM apagado | P2 y P3 (relé abierto: la bobina sin alimentación) con los rieles apagados, en los dos casos del §1.4: ¿cuánto suben los rieles locales frente al máximo de VCC − VEE del 74HC4051 y del OPA2188? |
| P5 | Red en el borne A | 230 Vrms entre A y COM durante 10 ms (antes de que abra el fusible), con la impedancia de la red supuesta en 0.5 Ω. Corriente e I²t por el DF08S y el derivador frente a sus hojas. Tensión en la entrada de B. Por X5, con el fusible abierto y la red en A: corriente y tensión |
| P6 | ESD | Modelo IEC 61000-4-2 (150 pF / 330 Ω) a ±4 kV en V/Ω (modo tensión y modo ohmios) y en A. A ±8 kV, solo informar (aire). Tensiones en los pines de los circuitos integrados y corrientes por las sujeciones frente a sus hojas |
| P7 | Recuperación | Tras P2 y tras P3 (cuando la PTC se enfría según su hoja), ¿vuelven X0 y N2 a menos de 1 cuenta del régimen? Tiempo |

## 4. Criterios (con los valores nominales y en los extremos de los rieles, ±2 %)

| # | Criterio | Prueba |
|---|---|---|
| S11.1-C1 | Cada pieza expuesta: tensión ≤ **80 %** de su máximo y potencia (o energía de pulso) ≤ **50 %** de su máximo, en P2–P5 | P2–P5 |
| S11.1-C2 | Corriente hacia cada riel ≤ la que absorbe la carga del riel encendido. Con el DMM apagado, el riel local no supera el máximo de VCC − VEE del 74HC4051 | P2–P4 |
| S11.1-C3 | Pines de los circuitos integrados dentro de sus máximos absolutos, con corrientes ≤ 50 % de su máximo, en P1–P6 | P1–P6 |
| S11.1-C4 | Con la red en ohmios y el relé **sin abrir nunca**, todo sobrevive 10 s gracias a la PTC (es decir, sin depender del firmware) | P3 |
| S11.1-C5 | Error añadido por fugas en ohmios a 0.2 µA (20 MΩ) ≤ **0.1 %**, y a 1 µA (2 MΩ) ≤ **0.02 %** | P1 |
| S11.1-C6 | Tensión disponible para el diodo a 1 mA ≥ **3.5 V** (RD-08) | P1 |
| S11.1-C7 | Recuperación ≤ 1 s tras retirar la red (sin contar el enfriamiento de la PTC, que se informa) | P7 |

Fallar es un resultado válido: informa del valor y de lo que lo movería, **sin simular remedios**. Informa de R_S = 100 y 330 Ω lado a lado, sin elegir.

## 5. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/DMM/`:
- `comun/dmm_bloque1.inc`;
- `S11_1/` y `ejecutar_s11_1.py`, con 10 trabajadores, `--smoke`, `--resume` y `S3G4_MODELS`;
- `resultados/s11_1_*.csv`;
- `ACTA_S11_1.md`, con la tabla de criterios y la lista de supuestos (sobre todo el modelo térmico de la PTC);
- tu diario.

## 6. Lo que NO es tuyo

No cambies valores salvo R_S. No elijas piezas ni remedios. No toques `../CH1_entrada/`, `../CH23_entrada/`, `models/`, `01_diseno/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 7. Cómo voy a auditar

1. `--smoke` reejecutado en una ruta corta.
2. El modelo térmico de la PTC frente a la curva de su hoja.
3. Que en P3 el relé está realmente cerrado y la fuente en el estado que dice cada caso.
4. Energías integradas sobre el tiempo real (10 s, o hasta el disparo), no sobre un ciclo extrapolado sin decirlo.
5. Cada máximo citado con su página.
