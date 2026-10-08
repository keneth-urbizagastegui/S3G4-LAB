# Auditoría de Claude — S12b (bloque 2 del DMM con el buffer OPA2192 antes del mux)

8 oct 2026. Claude Code (Opus, esfuerzo medio). He auditado `ACTA_S12b.md`, `ejecutar_s12b.py`, `comun/dmm_bloque2b.inc` y `resultados/s12b_*` frente a `PLAN_SIMULACION_S12b.md` y a las decisiones del 8 oct. No he modificado ningún archivo de Codex, ni STATE, DECISIONS, modelos u hojas.

- Copia de trabajo: `C:\s12b\S3G4_LAB_rev2.1\03_simulaciones\DMM` (sólo `.py`, `comun/` y `gdt_seguimiento/`, con `S3G4_MODELS` apuntando a los modelos del proyecto). Los decks derivados están en `C:\s12b\e3` y `C:\s12b\e5`.
- Scripts en `chequeo_claude/s12b/`:
  - `recalcular_raw.py`: E3, X2 a ±50 V y +20 V, desde el `.raw` de Codex;
  - `e3_umbral_x1.py`: el mismo deck de E3 (X2) con Vin = 48…52 V;
  - `e5_variantes.py`: el deck de E5 de Codex (×1, Ron 400 Ω) con variantes de la entrada no inversora, de la capacidad del TMUX y de una Cf;
  - `e8_descomponer.py` y `e8_todos.py`: la corriente de entrada de los buffers, separada en pinza (resistiva) y capacitiva, en los 148 casos de protección.

## 1. Reproducción

- `--smoke` desde cero (0 reutilizados, 67.9 s): **11/11 válidos**. Todas las métricas numéricas coinciden con `resultados/s12b_smoke.csv` de Codex; sólo cambian la firma (ruta distinta) y el tiempo.
- **E3, X2/+50 V/0 pC**, recalculado desde el `.raw`: Vout final 0.4993632 V frente a 0.4995005 V esperados (1 cuenta = 99.9 µV en la salida) → **−1.3740 cuentas** al final y **−1.6561** a 1.5 ms. Coincide con el acta. A −50 V: +1.3443 y +1.4144.
- **E5:** el deck de Codex da 38.459° con su método. Coincide.
- **E8, peor caso** (−8 kV, GDT 420 V, τ 100 ns, u884): pico de |I(Vib0)| de **22.032 mA a t = 100.5 ns**. Coincide.

## 2. Clasificación de los fallos

| Ensayo | Clase | Lo que es en realidad |
|---|---|---|
| E2 | **Criterio mal puesto.** El margen es real y no viene del redondeo | El 83 % es la fuga supuesta de 0.85 nA en la entrada del buffer × 99.1 kΩ |
| E3 | **Físico.** Es un error estático, no de asiento; la magnitud la pone el modelo | Con 50 V, X1 = 5.045 V supera el modo común del OPA2192 |
| E5 | **Sobre todo del modelo**, más 0.4° de rejilla. Hay una causa física pequeña | Los 10 pF de CD(ON) del TMUX van enteros detrás de Ron. Pesa además la impedancia nula de la fuente |
| E8 | **Criterio mal aplicado** | Los 22 mA son corriente capacitiva de 3 ns. La de pinza es ≤ 3.86 mA en todos los casos |
| E6 | Pendiente de especificación, no es un fallo | — |

### E2 — 4.19 cuentas frente a 4

Lo he recompuesto a mano desde `dc_budget()`. En 200 mV la cuenta es de 10 µV, el factor de deriva es 2^0.5 − 1 = 0.414 (de 23 a 28 °C) y la resistencia de fuente de X0 es 99.1 kΩ (R_PROT 99 kΩ + 100 Ω).

| Componente | Cuentas |
|---|---:|
| **Fuga de 0.85 nA en la entrada del buffer × 99.1 kΩ × 0.414** | **3.489** |
| Deriva de Vos, 2 × 0.5 µV/°C × 5 °C (buffer + A) | 0.500 |
| Fuga del TMUX, 0.3 nA × 91 kΩ / 10.1 × 0.414 | 0.112 |
| Ib de 20 pA × 99.2 kΩ × 0.414 | 0.082 |
| 1 nA del Yn + 0.85 nA en COM, sobre ≈ 71 Ω | 0.005 |
| **Total** | **4.189** |

- Sí, es la fuga supuesta en la entrada del buffer por los 99 kΩ. Con el buffer, **la fuga en COM ya no importa**: ve 71 Ω en lugar de 99 kΩ.
- No es redondeo: sobra un 4.7 %. La fuga tolerable es **0.80 nA a 23 °C** en la entrada de X0, frente a los 0.94 nA del rango de 20 V.
- El criterio está mal puesto. El «0.85 nA en COM y X0» de la decisión venía de S12, donde COM veía R_PROT. Ahora el nodo que importa es la entrada del buffer X0. Allí la fuga física es Ib del OPA2192 (±20 pA máx. a 25 °C, hoja p8), más la inversa de la BAV199 (pA) y la del PCB. Eso queda muy por debajo de 0.8 nA.
- **Cambio mínimo (sin piezas):** reescribir el requisito como «fuga total en el nodo X0, entrada del buffer, **≤ 0.6 nA a 23 °C**, medida en el prototipo». Con 0.6 nA salen 3.16 cuentas, con margen. La fuga en COM deja de ser requisito.

### E3 — cuatro fallos, máximo 1.66 cuentas

- Los cuatro son **X2, rango de 50 V, a ±50 V**, con 0 y con 5 pC. El resto de los 28 casos dentro de rango cumple; el peor de ellos es −0.41 cuentas en X0/200 mV.
- **No es un asiento.** El error ya está en X2: −1.3586 cuentas. Sólo 0.28 cuentas son cola de asiento a 1.5 ms (−1.656 frente a −1.374), y eso cumple.
- Mecanismo, desde el `.raw`: con +50 V, X1p = 5.045 V. El buffer X1 está saturado (salida 4.896 V) y su entrada no inversora toma **1.50 nA**. Sobre la impedancia de la toma, ≈ 0.91 MΩ, eso son 1.36 mV, que llegan a X2 como 0.135 mV = 1.36 cuentas. Con 20 V la corriente es de 15 pA y el error de −0.02 cuentas.
- Umbral, con `e3_umbral_x1.py` (el mismo deck, cambiando sólo Vin):

| Vin | X1p | I entrada buffer X1 | Error final | Error a 1.5 ms |
|---:|---:|---:|---:|---:|
| ±48 V | ±4.843 V | 0.03 / −0.02 nA | −0.045 / +0.016 | −0.230 / +0.065 |
| 49 V | 4.944 V | 0.51 nA | −0.474 | −0.754 |
| 49.5 V | 4.995 V | 1.00 nA | −0.922 | −1.202 |
| 50 V | 5.045 V | 1.50 nA | −1.374 | −1.656 |
| 52 V | 5.247 V | 5.08 nA | −4.928 | −5.145 |

- **Es físico:** 5.045 V supera el modo común recomendado, que llega hasta V+ + 0.1 V = 5.0 V (hoja p8). El modelo de TI empieza a tomar corriente hacia 4.85 V. La magnitud real (diodos ESD con 0.1–0.15 V de sobretensión) es del modelo y no está garantizada. Es el mismo problema de X1 = 5.04 V que señaló la auditoría de S12; el buffer lo ha pasado del mux al OPA.
- **Cambio mínimo:** **fondo del rango de 50 V ≤ 48 V** (X1 ≤ 4.84 V). Es una decisión de Keneth que ya estaba abierta, y no cambia piezas. Comprobado: con ±48 V, ≤ 0.23 cuentas a 1.5 ms. La alternativa sin tocar el fondo sería otra relación de la toma (1.01 MΩ → ≈ 0.96 MΩ), pero eso es una pieza y obliga a repetir E1/E2.
- Si el rango de 50 V es de alterna (70.7 Vpk), X1 llegaría a 7.1 V y esto no basta. Sigue sin confirmarse si el rango es eficaz o de pico.
- Al margen, no es fallo: en los rangos de 20/50 V, X0 está sujeto por la BAV199 y **la entrada del buffer X0 toma 0.43 mA continuos** (I(Vib0) final con +50 V). Está por debajo de los 10 mA absolutos y el canal no está seleccionado, así que vale. Pero esa corriente va al carril +4.9 V, que tiene que poder absorberla, y queda fuera del modo común de la hoja.

### E5 — 38.46° frente a 40°

E5 se mide en ×1 con Ron = 400 Ω, que es el máximo de la hoja a 25 °C con ±5 V. A 85 °C son 520 Ω (TMUX4053, p10). Resultados de `e5_variantes.py`:

| Variante | PM, método de Codex | PM interpolado |
|---|---:|---:|
| Deck de Codex | 38.46° | 38.86° |
| Buffer sustituido por una fuente ideal | 38.72° | 38.97° |
| Entrada + de A desde X0, sin buffer (como en S12) | 40.51° | 40.98° |
| R serie de 100–1000 Ω entre el buffer y el mux | 37.9–39.4° | 38.7–39.9° |
| Ron 520 Ω (85 °C) | 35.12° | 36.35° |
| **CD(ON) repartida 5 pF + 5 pF a cada lado de Ron, Ron 400 Ω** | 42.47° | **43.60°** |
| Repartida, con Ron 520 Ω | 41.79° | 42.01° |
| Repartida, con Ron 520 Ω y Cf 5 pF de out a inv | 44.62° | 44.63° |
| Ctm 10 pF entera y Cf 5 pF (Ron 400 Ω) | 40.89° | 41.02° |

- **Por qué bajó de 40.46° a 38.46°:** no es la carga del buffer. Con una fuente ideal sale igual (38.97°). Lo que cambió es que la entrada + de A, antes colgada de 99 kΩ, ahora la mueve una fuente de impedancia casi nula. Con alta impedancia, la capacidad de entrada de A arrastraba la entrada + con la inversora y le daba ≈ 2° de más. Es un efecto físico, pero pequeño.
- **Método:** Codex toma la fase en el primer punto por debajo de |T| = 1, con 100 puntos por década y sin interpolar. Eso resta ≈ 0.4° (38.46° frente a 38.86°). Es un artefacto menor.
- **Lo que de verdad lo fija** es el polo de Ron × la capacidad en inv. El `.inc` pone los 10 pF de CD(ON) (el típico de la hoja con ±5 V, p11) **enteros en el nodo inv, detrás de Ron**. Eso es pesimista: la capacidad de un interruptor cerrado se reparte a sus dos lados, y la mitad del lado de la salida no pesa. Con el reparto 5 + 5 pF salen 43.6° con 400 Ω y 42.0° con 520 Ω.
- **Cambio mínimo:** ninguno obligatorio. Repetir E5 con CD(ON) repartida en π y la fase interpolada; el criterio de 40° se cumple con margen de 2–3.6°. Como reserva barata, una huella DNP de 5 pF entre out e inv da +2.6° (44.6° a 85 °C). Ojo: en ×10, 5 pF sobre los 91 kΩ ponen un polo en 350 kHz, que da ≈ −0.16 % a 20 kHz y lo absorbe la calibración. Sigue en pie el escalón en el prototipo (decisión del 8 oct).

### E8 — 22 mA en la entrada del buffer frente a 5 mA

- He separado la corriente del peor caso con la pinza del propio deck (`ICOPA`: Vfwd 0.5 V, Ron 1 Ω). Lo que no pasa por la pinza es capacitivo (Cin 6.4 pF y 1.6 pF diferencial).
  - **Los 22.03 mA son 100 % capacitivos.** En el pico, la corriente de pinza es 0. Supera 5 mA durante **3.2 ns** y 10 mA durante 1.6 ns, con una carga despreciable.
  - La corriente de pinza llega a **2.97 mA** en X0 y 3.80 mA en X1. Dura decenas de µs (73 nC en X0) y nunca pasa de 5 mA.
- En los **148 casos** (296 canal-caso), con `e8_todos.py`: la pinza da como máximo **3.86 mA** con ESD y **2.64 mA** con la red de 253 Vrms. **Ningún caso supera 5 mA de pinza.** Los 48 «fallos» son todos picos capacitivos de ≤ 7.1 ns.
- **La hoja del OPA2192** (SBOS620E): ±10 mA de corriente en los pines de entrada (p6, máximos absolutos) y tensión de modo común de V− − 0.5 a V+ + 0.5 V. La ESD es de 4 kV HBM y 750 V CDM en el OPA2192, pero sólo para manipulación fuera del circuito. La sección 8.3.7 dice que los diodos ESD no están pensados para activarse dentro del circuito y pide resistencias limitadoras y TVS. El ±10 mA es la corriente de conducción por esos diodos; el desplazamiento de unos ns por la capacidad de la entrada no es la magnitud que limita.
- **Clase:** criterio mal aplicado. Con la corriente de pinza, E8 cumple: 3.86 mA, el 39 % del máximo absoluto. Reservas:
  - la IV de la pinza (0.5 V, 1 Ω) es un supuesto. Si el diodo real conduce antes que la BAV199, se lleva más parte;
  - el modelo ESD de 150 pF/330 Ω no reproduce el arco en aire.
- **¿Una R serie en la entrada del buffer?** No hace falta para cumplir. Subir los 100 Ω de X0/X1 a 1 kΩ dividiría por ≈ 10 la parte de la pinza del buffer frente a la BAV199. Cuesta 4 nV/√Hz, 5 µV con 5 nA de Ib a 125 °C, y una τ de 8 ns con Cin, que no afecta a E1/E5. Lo dejo como **opcional y robusto frente a la IV desconocida**. Pertenece a la frontera del bloque 1, así que lo decide Keneth.

### E6 — especificación de la 3.3 kΩ antipulso

Lo que tiene que aguantar cada Rc (acta, comprobado en `s12b_impulsos.csv`) en un disparo de 8 kV: **1111 V de pico**, > 400 V durante ≤ 2.05 ns, > 1000 V durante 0.25 ns, y **2.49 µJ** disipados. Con 4 kV: 840 V y 2.13 µJ. Con la red, 0.015 V. Especificación propuesta:

- tensión de impulso ≥ 1.5 kV (≥ 1.35 × 1111 V, por el modelo de pistola sin arco), con pulso de 1.2/50 µs o con ESD ≥ 2 kV según AEC-Q200-002 o IEC 61000-4-2;
- ΔR ≤ 1 % tras 10 descargas de cada polaridad. La Rc sólo amortigua la compensación, así que basta un 1 %; no hace falta 0.1 %;
- energía de un pulso único ≥ 25 µJ (10 × 2.5 µJ) para pulsos ≤ 1 µs, leída en la curva del fabricante;
- 1206, para ganar línea de fuga. La tensión de trabajo en continua no se aplica (≈ 0 V);
- el MPN queda pendiente: no invento ratings. La pieza tiene que tener curva de pulso publicada (familias antisurge o «pulse proof»).

### La duda de la comprobación fina de ±50 V: 2.15 mA frente al pico grueso de 10.31 mA

- Son el mismo caso (E3, +50 V, X0, 0 pC) y la misma magnitud: el **pico de la corriente de la entrada inversora del buffer X0** durante el transitorio de conmutación.
- Con un paso máximo de 1 µs salen 10.31 mA; con 100 ns, **2.15 mA**. El pico de 10.31 mA es un **artefacto de integración**: el paso grueso fuerza una derivada brusca sobre la capacidad de entrada. La comprobación fina no tiene que confirmarlo; lo desmiente. El valor válido es 2.15 mA, por debajo de 5 mA.
- Además, la corriente de la entrada inversora de un seguidor saturado es en buena parte un efecto del modelo de TI: la hoja da un rango diferencial hasta el carril sin diodos entre entradas.
- Lo que sí es real y continuo es la corriente de la entrada no inversora con X0 sujeto: 0.43 mA (ver E3).

## 3. Cambios mínimos

| # | Cambio | Tipo | Comprobado |
|---|---|---|---|
| 1 | **Rango de 50 V con fondo ≤ ±48 V** | Decisión de Keneth, sin piezas | Sí: ≤ 0.23 cuentas |
| 2 | **E2:** «fuga en la entrada del buffer X0 ≤ 0.6 nA a 23 °C, en el prototipo»; se retira el requisito de COM | Criterio | Cálculo: 3.16 cuentas |
| 3 | **E5:** CD(ON) repartida en π y fase interpolada en la repetición; huella DNP de 5 pF entre out e inv | Modelo + huella | Sí: 42.0–43.6°, y 44.6° con Cf |
| 4 | **E8:** criterio sobre la corriente de pinza (conducción), no sobre el desplazamiento de ns | Criterio | Sí: ≤ 3.86 mA en 148 casos |
| 5 | **E6:** especificación de la Rc del apartado anterior; elegir el MPN | Compra | — |
| 6 | Opcional: 100 Ω → 1 kΩ delante de cada buffer | Frontera del bloque 1 | No simulado |

## 4. Veredicto

**Sí, el bloque 2 se puede cerrar en simulación, con condiciones.** Ningún fallo exige cambiar piezas del bloque 2. Las condiciones:

1. Keneth fija el fondo del rango de 50 V en ≤ 48 V (o acepta otra relación de la toma y repite E1/E2), y aclara si el rango es de continua o de alterna.
2. Se aceptan los criterios reescritos de E2 (≤ 0.6 nA en X0) y de E8 (corriente de pinza). Las dos fugas y la ESD se miden en el prototipo.
3. Se repite E5, sólo los cuatro casos de lazo, con CD(ON) repartida y la fase interpolada. Basta una comprobación pequeña; no hace falta otra campaña.
4. Se elige la Rc antipulso con la especificación del apartado E6.

Sigue sin probarse: la dispersión real del OPA (GBW, Cin, Ib), la IV de las pinzas, el arco IEC en aire y los efectos del PCB. Ninguno de los resultados demuestra la fabricación ni el cumplimiento IEC.
