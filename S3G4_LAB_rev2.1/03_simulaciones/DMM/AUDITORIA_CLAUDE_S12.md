# Auditoría de S12 (DMM, bloque 2: frontal de tensión)

- Auditor: Claude Code, 8 oct 2026. Ejecutó: Codex. Contrato: `PLAN_SIMULACION_S12.md`. Acta: `ACTA_S12.md`.
- Copia de trabajo: `C:\s12a\r\s\DMM`, con dos niveles de carpeta por `HERE.parents[2]` y `S3G4_MODELS` apuntando a los modelos del proyecto. Mis decks derivados están en `C:\s12a\e3`, `e3s`, `e3u`, `e5` y `e5r`.
- No he tocado ningún archivo de Codex, ni `STATE.md`, `DECISIONS.md`, modelos u hojas. No he descargado nada.
- Mis scripts, en `DMM/chequeo_claude/s12/`:
  - `leer_raw.py`: lector `.raw` propio;
  - `comparar_smoke.py`: compara mi smoke con el de Codex, columna a columna;
  - `recalcular_raw.py`: E3 (X0, 200 mV) y E6 (GDT solo, −4 kV) desde el `.raw`;
  - `duracion_e6.py`: duración, energía y Vin de pico del pulso en una 1.5 MΩ;
  - `e3_inyeccion.py`, `e3_inyeccion_base.py`, `e3_umbral.py` y `e3_pinza_schottky.py`: punto de trabajo de E3 con variantes que aíslan los canales;
  - `e5_cff.py` y `e5_ron.py`: margen de fase frente a Cff, RTMUX, C en IN− y carga.

## 1. Reejecución y recálculo

- `--smoke` en la copia: **10/10 en 165 s**, frente a los 163.5 s de Codex. Las 10 filas coinciden con `s12_smoke.csv` en todas las columnas numéricas (la peor diferencia relativa es 0; solo cambian el tiempo y la firma).
- **E3, X0 en 200 mV**, desde el `.raw`: final 2.019978 V, es decir −0.221 cuentas (1 cuenta = 101 µV en la salida ×10.1). El asiento a media cuenta tarda **22.50 µs** desde 1 ms. Coincide con el acta.
- **E6, GDT solo a −4 kV**, desde el `.raw`: 175.455 V en cada una de las seis 1.5 MΩ, el mismo valor en todas (el reparto lo fijan los 100 pF). Coincide con `r1a_v`. El pulso pasa de 50 V solo durante **85 ps** y la energía en la resistencia es de 0.13 nJ.

Los resultados de Codex se reproducen. Los cuatro fallos son tres cosas distintas:

| Fallo | Clase | Mecanismo |
|---|---|---|
| E2, 200 mV | Supuesto/criterio: margen nulo, no es un defecto | 1 nA supuesto que se duplica cada 10 °C, sobre los 99 kΩ de R_PROT |
| E3, X1/X2 | **Físico: el circuito trabaja fuera de la hoja.** La magnitud es del modelo, el mecanismo no | Canales apagados del 4051 por encima de su VCC |
| E5, ×1 en el corner | Real en el límite de la hoja; el remedio no es un pF | Polo Ron × C de IN− sobre un OPA que solo tiene ≈ 50° |
| E6, 558 V | Criterio mal puesto (ns frente a 5 s) y un dato que falta en la hoja | Reparto capacitivo durante la demora del GDT, con el MOV en serie |

## 2. E2, 200 mV: 4.008 cuentas, margen nulo

Composición, con los números de Codex (`s12_campaign.csv`, `s12_dc_budget.csv`):

- Offset SPICE en la salida: −1.0213 mV a 23 °C, −1.4261 mV a 28 °C (fuga 1.414 nA) y −0.7381 mV a 18 °C (0.707 nA). La deriva a 28 °C es −0.405 mV en la salida, **40.08 µV en la entrada = 4.008 cuentas**; a 18 °C es de 2.80 cuentas. Toda sale de **Δfuga × R de fuente**: 0.414 nA × ≈ 99 kΩ (R_PROT 99 kΩ + 100 Ω + Ron). Vos e Ib del modelo apenas cuentan.
- El presupuesto (4.552 cuentas) suma lo mismo con la R completa (99.17 kΩ: 4.108 cuentas) y 0.444 cuentas de reservas: 2.5 µV de deriva de Vos (0.25), 20 pA de Ib con la misma ley (0.08) y 0.3 nA del TMUX vistos a través de 91 kΩ/10.1 (0.11).
- El autocero no lo cancela: X3 pone COM a masa con impedancia nula, así que no ve la caída de la fuga sobre R_PROT.

**Clase: supuesto con margen nulo.** El «1 nA a 23 °C, ×2 cada 10 °C» es una elección del contrato, no un dato. La hoja del 74HC4051 da ±0.4 µA máx. en todos los canales a 25 °C, sin valor típico (`74HC_HCT4051.pdf` p. 9). El caso nominal supera el criterio en un 0.2 %, y el presupuesto en un 14 %. No hay que cambiar ninguna pieza: queda un requisito de medida.

**Cambio mínimo:** sustituir «1 nA» por el límite que sale del cálculo, **≤ 0.85 nA de fuga agregada en COM a 23 °C** para 200 mV y 20 V (el estudio daba 0.7 nA con 3 cuentas), y medirlo en el prototipo (D4). Si no se cumple, el estudio ya tiene la salida: los buffers C, o recalibrar el offset con la entrada en corto a la temperatura de uso.

## 3. E3, X1/X2: no es un asiento, es un error estático por inyección del canal X0 apagado

«Colas incorrectas» significa que la salida se asienta pronto, pero en un valor equivocado: a 8 ms, 2.7925 V en lugar de 2.0180 V en X1 y 4.8786 V en lugar de 0.4995 V en X2. Lo he comprobado con `.op` del mismo deck, con el canal ya conmutado (`e3_inyeccion.py`):

| Caso | Vout | V(x0) | Lo que entra por el canal X0 |
|---|---|---|---|
| X1, 20 V, base | 2.79254 V | 5.289 V | 148 µA por Rx0 |
| X1, con el Y de X0 a 0 V | **2.01791 V** (bien) | 5.599 | 0 |
| X2, 50 V, base | 4.87854 V | 5.476 | 441 µA |
| X2, X0 aislado | 0.49443 V (−5.07 mV, 507 cuentas) | 5.638 | 0; ahora X1 = 4.994 V |
| X2, X0 y X1 aislados | **0.49950 V** (bien) | | |

El `.op` repite el valor final del transitorio, así que no es un problema de asiento, ni del estímulo, ni del orden de los flancos. En los rangos de 20 V y 50 V, la pinza BAV199 del bloque 1 sujeta X0 a vp + Vf ≈ **5.3–5.6 V**, por encima de los 4.9 V de VCC del 4051. En el rango de 50 V, la propia toma ÷10 deja X1 = 50 × 0.1009 = **5.04 V**. Los canales apagados que pasan de VCC vuelcan corriente al común.

El umbral es nítido (`e3_umbral.py`, X2 con X0 aislado): sin error hasta Vin = 48 V (X1 = 4.843 V) y 507 cuentas a 50 V (X1 = 4.994 V).

**Clase: físico en su causa, del modelo en su tamaño.** El aviso del estudio sobre SWI1 no lo explica: no es la capacidad ni el transitorio. Lo que pasa es que la hoja (condiciones recomendadas) limita la tensión del canal a VEE…VCC, y el circuito la supera en un uso normal. Que una pieza real inyecte 148–441 µA con 0.4–0.6 V de exceso no está demostrado: el SWI1 conduce de golpe en VCC, y en el silicio la corriente iría sobre todo por el diodo de la pieza hacia VCC. Pero no se puede aprobar un frontal que deja canales apagados fuera de la hoja, y la inyección en el común de los mux CMOS es un efecto conocido.

Consecuencias:
- E1 y E2 de 20 V y 50 V se hicieron con el mux pasivo y no ven este efecto. Sus resultados no valen para el aparato real hasta que se arregle E3.
- Los 7677/43834 de «error final» que da el acta son del modelo; lo que es seguro es que el estado es ilegal.

**Cambio mínimo**, dos partes:

1. **X0** (rangos de 20 V y 50 V): las pinzas de X0 tienen que ir a un carril por debajo de VCC. Con una Schottky genérica (supuesto tipo BAT54, sin ficha local) a ±4.3 V, X0 queda en 4.50–4.52 V y el rango de 20 V sale bien: 2.017917 V frente a 2.017982 V; los −65 µV son el offset que también hay con X0 aislado (`e3_pinza_schottky.py`). Otra opción, sin carril nuevo: llevar X0 a masa con una sección libre del TMUX4053 en los rangos de ≥ 20 V. Por esa sección pasaría la misma corriente que hoy va a vp por la pinza.
2. **X1 en 50 V:** no tiene arreglo con pinzas, porque al pinzar x1p también se mueve X2 (con la pinza a ±4.0/4.3 V, X2 da −97/−69 mV). Hay tres salidas: limitar el fondo del rango de 50 V a ≤ 48 V (X1 ≤ 4.84 V), subir el VCC del mux por encima de la toma (el HCT4051 admite VCC − VEE ≤ 10 V, lo que no basta), o cambiar la relación ÷10. Es una decisión de Keneth.

**Comprobación pequeña:** repetir E3 de X1/X2 con el remedio elegido y con Vin igual al fondo de escala real, incluido el pico si el rango de 50 V es de alterna.

## 4. E5: 40.46° en ×1 con RTMUX = 400 Ω

En mi extracción, que interpola en el cruce, salen 41.00° con 400 Ω y 49.92° con 60 Ω; Codex da 40.46°/49.11°. La diferencia de ≈ 0.6–0.8° es de método, no cambia nada.

Barrido (`e5_ron.py`, ×1, carga de 10 pF):

| RTMUX | Ctm 5 pF | 10 pF | 15 pF |
|---|---|---|---|
| 60 Ω | 50.4° | 49.9° | 49.5° |
| 150 Ω | 48.9° | 47.2° | 45.7° |
| 200 Ω | 48.1° | 45.9° | 43.9° |
| 300 Ω | 46.6° | 43.3° | 40.5° |
| 400 Ω | 45.2° | 41.0° | 37.6° |

Qué fija el margen:
- **Base:** el OPA2192 como seguidor con 10 kΩ ∥ 10 pF solo tiene ≈ 50° (cruce a 8.7 MHz).
- **Polo de la ruta:** el polo (RTMUX + 1 Ω) × C de IN− resta ≈ 9° con 400 Ω y 10 pF. Esos 10 pF son CD(ON) = 10 pF típ. de la hoja (`tmux4053.pdf` p. 11), más la entrada del OPA.
- **Ron:** 400 Ω es el máximo a 25 °C con ±5 V (p. 10); el típico es de 60 Ω. A ±4.9 V será algo mayor.
- **Carga del driver:** con 47 pF el margen sube unos 3° (44.1° con 400 Ω). La carga supuesta no es lo que lo fija.

**Un pF de compensación no basta** (`e5_cff.py`). Un Cff de out a IN− de 1/2/3.3/4.7 pF sube el ×1 a 400 Ω solo hasta 41.4/41.8/42.4/42.9°: el condensador tiene que ganarle a ≈ 16 pF de IN−. Uno grande (≥ 22 pF) estropea el ×10.1, porque con 91 kΩ pone un cero cerca de 80 kHz. En ×10.1 el margen ya es de 64°, y con Cff sube.

**Clase: real, pero solo en el corner de hoja.** Pasa con Ron típica (49°) y el transitorio de cambio de ganancia cumple (11.45 µs). El criterio > 45° falla con RTMUX > ≈ 210 Ω (Ctm 10 pF).

**Cambio mínimo**, a elegir por Keneth:
- **(a)** Exigir en la llave ×1 una Ron máx. ≤ 200 Ω a ±4.9 V con CD(ON) ≤ 10 pF, por ejemplo con otra SPDT de baja Ron; hay que confirmarlo en su hoja.
- **(b)** Aceptar ≥ 40° en el corner de Ron máx. y ≥ 45° en el típico, comprobando con un escalón pequeño en ×1 que el sobreimpulso es razonable y que no oscila con carga de 10–50 pF.

Poner dos secciones del TMUX en paralelo no basta: 200 Ω con ≈ 15 pF dan 43.9°.

## 5. E6: 558 V en una 1.5 MΩ

**Estímulo:** ESD de +8 kV, alimentado, toma X0, relé abierto, GDC 780 V, **cadena vigente GDT + 14D431K en serie** (Dm1/Dm2 de vin a ga, GDT de ga a masa) y cebado con **τ = 100 ns**. El MOV está en serie, y por eso empeora frente al «GDT solo» del contrato S11.4: suma su tensión de codo (≈ 430–710 V) a la de cebado del GDT. Lo de Codex es correcto: el contrato pedía el GDT solo (177.86 V) y la cadena aprobada da más.

Desde el `.raw` (`duracion_e6.py`):

| Caso | Vin de pico | Pico por 1.5 MΩ | > 400 V | > 200 V | Energía por pieza |
|---|---|---|---|---|---|
| GDT + MOV, τ 100 ns | 3349 V | **558.1 V** | **0.5 ns** | 2.6 ns | 48 nJ |
| GDT + MOV, τ 1 ns | 1729 V | 288.1 V | 0 | 0.1 ns | 51 nJ |
| GDT solo (S11.4), τ 1 ns | 1053 V | 175.5 V | 0 | 0 | 0.13 nJ |

Mecanismo: durante la demora del GDT, Vin sube hasta 3.35 kV y las tres parejas de 100 pF reparten esa tensión a partes iguales. Cada 1.5 MΩ ve ≈ Vin/6, y cada 3.3 kΩ ve la pareja entera (**1115 V**). El pico es proporcional a la τ supuesta, que es un supuesto de modelo, no un dato de hoja: la hoja del GDT solo da 1000 V a 100 V/µs.

**Comparación con la hoja: criterio mal puesto.** El 400 V de `C728673.pdf` es la *Short Time Overload* (IEC 60115-1 4.13): 2.5 × la tensión nominal **durante 5 s**, con un requisito de ±(0.5 % + 0.05 Ω). La hoja no da ninguna cifra de ESD ni de impulso. Comparar un pico de 0.5 ns con un ensayo de 5 s no tiene sentido en ninguno de los dos sentidos: ni prueba el daño ni lo descarta. Además, pasar el ensayo permite una deriva del 0.5 %, cinco veces la tolerancia.

**Cambio mínimo:**
- Rehacer el criterio de pulso para las tres familias expuestas (1.5 MΩ, 3.3 kΩ y C0G): tensión de impulso o ESD de una hoja que la dé, o un ensayo de ESD en el prototipo midiendo la deriva de la relación del divisor (≤ 0.05 %).
- La pieza más expuesta es la **3.3 kΩ (1115 V)**: elegirla antipulso (película gruesa *anti-surge* con curva de impulso en su hoja).
- Si se mantiene «pico ≤ 400 V» como regla prudente, hace falta Vin de pico ≤ 2.4 kV, es decir, que el GDT cebe en ≲ 50 ns con el MOV en serie. Eso solo se puede confirmar con medida, no con este modelo.

## 6. Otros puntos

- E1 «cumple», pero en pequeña señal y con el mux pasivo. En 20/50 V no vale hasta cerrar E3. Si el rango de 50 V es de alterna, el pico de x1p (70.7 × 0.1009 = 7.1 V) lo cortaría la BAV199 y distorsionaría X2: hay que confirmar si los rangos son de valor eficaz o de pico.
- Los transitorios usan `SWI1` (HC) y no `SWI1T` (HCT). Con un control de 0/4.9 V no cambia nada; es una nota.
- El consumo de X1/X2 (11.4/13.3 mW) es el del estado ilegal; Codex ya lo marca.
- C3 (0.89 pF frente a los 25 pF de hoja): bien señalado como no representativo.

## 7. Veredicto

S12 está bien ejecutado y es reproducible, pero el bloque 2 **no se puede cerrar todavía**. Falta esto, por orden:

1. **E3 (bloqueante, de diseño):** sacar los canales apagados del 4051 de fuera de VEE…VCC. Para X0, pinza a un carril de ±≈ 4.3 V o puesta a masa en los rangos ≥ 20 V. Para X1 en 50 V, decisión de Keneth: fondo ≤ 48 V, otra relación u otro mux. Después, repetir E3, y E1/E2 en 20/50 V con el mux de transitorio.
2. **E5:** decidir entre una llave ×1 con Ron máx. ≤ 200 Ω o el criterio de corner a ≥ 40° con un ensayo de escalón.
3. **E6:** sustituir el criterio de 400 V/5 s por uno de impulso, elegir una 3.3 kΩ antipulso y prever un ensayo de ESD con medida de la deriva de la relación. El valor de 558 V depende de la τ supuesta del GDT.
4. **E2:** reescribir el requisito como fuga en COM ≤ 0.85 nA a 23 °C y medirla en el prototipo (D4). No pide cambiar piezas.
