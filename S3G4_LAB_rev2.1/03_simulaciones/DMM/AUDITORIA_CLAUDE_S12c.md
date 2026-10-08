# Auditoría de Claude — S12c (bloque 2 sin toma ÷10)

8 oct 2026. Claude Code (Opus, esfuerzo medio). Material auditado: `PLAN_SIMULACION_S12c.md`, `ACTA_S12c.md`, `ejecutar_s12c.py`, `comun/dmm_bloque2c.inc`, `resultados/s12c_*`. Hojas consultadas: `opa2192.pdf` (SBOS620E, pp. 8–11 y 26) y `74HC_HCT4051.pdf` (pp. 9–12). No se modificó nada de Codex ni STATE/DECISIONS/modelos.

Comprobaciones propias (`chequeo_claude/s12c/`, ejecutadas en `C:\s12c` con LTspice -b y el modelo TI `OPAx192.LIB`):

- `e3_pinza_x0.py`: buffer X0 con BAV199 y 99 kΩ, barrido DC del borne de 0 a 50 V. Se varían la R serie (100 Ω, 1 kΩ, 10 kΩ) y la Schottky a los rieles.
- `e2e3_buffer_x2.py`: divisor S12c reducido, con y sin buffer OPA192 en X2. Mide la fuga del mux (1.85 nA a 23 °C y 2.616 nA a 28 °C) y una carga de 7.8 pC inyectada en el nodo del mux.

Recalculé desde `s12c_campaign.csv`, `s12c_dc_budget.csv`, `s12c_capacitores.csv` y `s12c_verificacion_extra.csv`.

## Resumen

| Fallo | Clase | Mecanismo | Cambio mínimo propuesto |
|---|---|---|---|
| E2, 20 V: 8.04 cuentas | **Físico** (con un supuesto de fuga optimista) | La fuga del mux sobre los ≈ 99 kΩ de Thévenin de X2 aporta 7.59 cuentas de deriva entre 23 y 28 °C; el resto suma ≈ 0.45 cuentas | **(a) Buffer en X2**: un OPA4192 para el buffer de X0, el buffer de X2 y A |
| E3, 1.81 cuentas a 1.5 ms | **Criterio de espera** (el asiento es físico) | Carga inyectada por el 4051 en X2 (≈ 7.5 pC en el modelo) que decae con τ = 100 k·3 nF ≈ 300 µs. **No guarda relación con X0**: en ese caso X0 está a 0 V | Esperar 3 ms en X2 (20 V y 50 V). Con el buffer en X2 basta con 1.5 ms |
| E3, entrada del buffer de X0 a 5.45–5.52 V | **Físico**, pero el criterio está mal planteado | La pinza interna del OPA192 conduce antes que la BAV199 y se lleva casi toda la corriente (145 µA a 20 V y 421 µA a 50 V) | **Rx0: de 100 Ω a 10 kΩ** (19–23 µA). No hacen falta Schottky ni encapsulados separados |
| E3: 9 refinamientos inconclusos | **Artefacto / criterio** | Cinco son el mismo asiento de 1.5 ms y ya cumplen a 3 ms. Cuatro son excesos de 0.6–3.1 mV sobre ±4.9 V en la salida del buffer, que su propio riel limita | Tolerancia de riel de ±4.9 V + 50 mV para salidas de AO; no hace falta repetir los casos |
| E6, 330 pF a 47.68 V | Especificación | Pico de ESD de 8 kV en aire; 32.5 V de pico continuos con 253 Vrms | C0G de **≥ 100 V** para 330 pF; 3 nF ≥ 25 V (50 V habitual) |

## E2 — 20 V: 8.04 cuentas

Datos (`s12c_dc_budget.csv`): con 1.85 nA de fuga agregada en X2, la parte fija suma 0.444 cuentas y el total, 8.044. La fuga máxima tolerable es de 0.866 nA.

Simulación propia (`e2e3_buffer_x2.py`, sin buffer; 1 cuenta = 1 mV en el borne = 9.99 µV en X2):

- 1.85 nA dan −183 µV, es decir, −18.33 cuentas, que la calibración elimina.
- A 28 °C la fuga es de 2.616 nA y da −25.93 cuentas. **La deriva es de 7.59 cuentas.**
- 7.59 + 0.44 ≈ 8.04: la fuga del 4051 pone el 94 % del error, y la Thévenin (100 k ∥ 9.91 M = 99.0 kΩ) lo convierte directamente en tensión. La ganancia ×10.1 no lo agrava, porque el error se refiere al borne igual que la señal. Lo que pesa es la impedancia de X2.

**Hecho decisivo de la hoja** (74HC_HCT4051, p. 9): I_S(OFF) es de ±0.1 µA por canal e I_S(ON) de ±0.4 µA como máximo a 25 °C, y de ±1 µA y ±4 µA en temperatura (pp. 10–12). El «1 nA por ruta» es un **supuesto típico, unas 100 veces por debajo del máximo garantizado**. Con la fuga máxima, el rango de 20 V sin buffer fallaría por cientos de cuentas.

Opciones:

- **(a) Buffer en X2.** La simulación da una deriva de **0.0054 cuentas**: la fuga va a la salida del buffer y sólo ve los 70 Ω de Ron. Presupuesto estimado:
  - 0.44 cuentas fijas;
  - 0.25 por la deriva de Vos del buffer nuevo (0.5 µV/°C × 5 °C);
  - ≈ 0.08 por su Ib (20 pA en 99 k, con la ley ×2 cada 10 °C).
  - Total ≈ **0.8 cuentas**. Incluso con la fuga máxima de hoja (0.4 µA × 70 Ω, ×0.41 de deriva), son unas 1.2 cuentas más y el total queda ≈ 2 < 4.

  Coste: un OPA4192 en lugar del OPA2192 (≈ +1 mA de consumo, una huella SOIC-14). También elimina el asiento de E3 (ver abajo) y la sensibilidad a la capacidad del mux, que con ±20 pF movía el decaimiento a 20 kHz de −1.55 % a −2.82 %. Condición: X2 vale ≤ 0.5 V en rango y 3.25 V de pico con 253 Vrms; bajo ESD llega a 5.2 V (el pico del 3 nF). Hay que poner ≥ 10 kΩ en serie ante la entrada del buffer de X2, por la misma razón que en X0. El canal libre del cuádruple se cablea como seguidor a masa.
- **(b) Fuga medida ≤ 0.6–0.8 nA.** Es selección por ensayo, placa por placa y a 28 °C, de una pieza garantizada a 100 nA. El margen es nulo con 0.8 nA (0.866 de límite) y la fuga del PCB entra en el mismo presupuesto. **No es fabricable** con el criterio de ≥ 95 % de placas sin una criba; sólo sirve como respaldo.
- **(c) Otro mux de fuga baja.** Necesitaría una fuga **máxima garantizada** de ≤ 0.5 nA agregados a 28 °C con ±4.9 V, y no tengo hoja local de ninguno para comprobarlo. Además, el buffer de X0 sigue haciendo falta, y la deriva de 200 mV con 0.6 nA ya va justa (0.804 nA de límite). Es más caro de calificar que (a).

**Recomendación: (a).** Con (a), el límite de 0.6 nA en X0 también deja de mandar en 200 mV: la fuga del mux pasa a la salida del buffer de X0. Sólo quedan la Ib del buffer, la BAV199 y el PCB en x0p, y conviene recalcular ese presupuesto.

## E3 — asiento de 20 V y entrada del buffer de X0

### Asiento de 1.81 cuentas a 1.5 ms

`s12c_campaign.csv` (E3, X2 ×10.1) da los errores a 1.5 ms y a 3 ms:

| Borne | 1.5 ms | 3 ms | Final |
|---|---:|---:|---:|
| −20 V | −1.28 | −0.08 | −0.07 |
| 0 V | −1.85 | −0.11 | −0.10 |
| +20 V | −2.20 | −0.14 | −0.12 |

- La diferencia entre ±20 V (X0 saturado a 5.45 V) y 0 V (X0 a 0 V) es de **±0.03 cuentas** y sigue el signo de la entrada: es ganancia, no acoplo. **El error de asiento no procede de X0**. El modelo usa además dos instancias independientes, así que no puede mostrar acoplo dentro del encapsulado (ver más abajo).
- Mecanismo: en el caso refinado, X2 llega a un pico de 2.49 mV con el borne a 0 V (`s12c_verificacion_extra.csv`). Es la carga de conmutación del modelo NXP: ≈ 2.5 mV × 3.03 nF ≈ 7.5 pC, que decae con τ ≈ 300 µs. Entre 1.5 y 3 ms el transitorio cae unas 145 veces, lo que equivale a τ = 0.30 ms. Mi deck reproduce el caso: con 7.8 pC obtengo −1.817 cuentas a 1.5 ms y −0.013 a 3 ms.
- Clase: el asiento es físico y **el fallo lo pone la espera de 1.5 ms heredada de X1**. La hoja del 4051 no especifica la carga inyectada. Una espera de 3 ms cubre 148 veces más carga que la del modelo, y 2.5 ms bastarían con 20 veces de margen. **Propuesta: 3 ms tras seleccionar X2**, en los rangos de 20 V y de 50 V (en 50 V el peor caso a 1.5 ms es de 0.21 cuentas). Es una decisión de firmware que debe tomar Keneth.
- Con el buffer en X2, la carga va a la salida del buffer. La simulación da **−0.124 cuentas constantes (su Vos) desde 0.1 ms**, así que basta con 1.5 ms.

### Entrada del buffer de X0 a 5.45–5.52 V

Datos: `bi0` vale 5.4515 V a ±20 V, 5.5027 V a ±50 V y 5.5244 V con 50 Vrms. Simulación propia (`e3_pinza_x0.py`):

| Rx0 / pinza | I entrada buffer a 20 V | a 50 V | V(bi0) a 50 V |
|---|---:|---:|---:|
| 100 Ω (actual) | **145 µA** | **421 µA** | 5.502 V |
| 1 kΩ | 109 µA | 160 µA | 5.455 V |
| 10 kΩ | 18.8 µA | 22.7 µA | 5.403 V |
| 100 Ω + Schottky a rieles | 1.9 nA | 2.2 nA | 5.109 V |

- **Mecanismo:** con 100 Ω, la pinza interna del OPA192 conduce antes que la BAV199 externa, cuya IS es de 8×10⁻¹⁹ A. El buffer se lleva el 99 % de los (20 − 5.45)/99 k = 147 µA. La BAV199 apenas protege. Es corriente de entrada al riel a través de las celdas ESD de un dado que también aloja A.
- **Acoplo en el doble:** la hoja da 150 dB de diafonía en DC (p. 9), pero en régimen lineal. Para 5 V de excursión supondría 0.16 µV ante A, ≈ 0.016 cuentas en 20 V, despreciable. La hoja no especifica la precisión del otro canal mientras uno inyecta 0.1–0.4 mA por su ESD, y el modelo no puede simularlo. **Sin evidencia de error; lo indeterminado es la inyección, no la saturación de la salida.**
- **Criterio:** que un buffer **no seleccionado** salga del modo común (V+ + 0.1 V = 5.0 V) no es un error de medida. El OPAx192 tiene protección contra inversión de fase (p. 26), y la máxima absoluta se respeta si la corriente queda limitada (±10 mA). El criterio útil es «corriente de entrada ≤ 50 µA» con el canal sin seleccionar, no el ±4.9 V literal.
- **Remedios:**
  - **Rx0 = 10 kΩ** reduce la inyección 19 veces (≤ 23 µA, < 0.25 % de los 10 mA) y hace que conduzca la BAV199. Coste: 10 k × 20 pA = 0.2 µV (≈ 0.02 cuentas en 200 mV, y además se calibra), 12.9 nV/√Hz de ruido térmico (despreciable con 100 ms) y 10 k × 6.4 pF = 64 ns.
  - La Schottky deja la inyección en nA, pero su fuga inversa (típica de decenas de nA a 5 V en un BAT54) **arruina el presupuesto de ≤ 0.6 nA en X0**. Rechazada.
  - Separar encapsulados no elimina la inyección al riel compartido y choca con la opción (a), en la que los cuatro canales comparten encapsulado. Con 10 kΩ deja de ser necesario.
- **Comprobación en banco**, cuando haya placa: medir el offset de 20 V con X0 forzado de 0 a 50 V.

### Los nueve refinamientos inconclusos

- **Cinco «excesos de una cuenta»:** son los casos de X2 ×10.1 a 1.5 ms de la tabla anterior; todos quedan ≤ 0.14 cuentas a 3 ms. Con la espera de 3 ms, su refinamiento es irrelevante.
- **Cuatro excesos de 0.6–3.1 mV:** afectan a la salida del buffer, que no puede superar su propio riel en silicio. Son un artefacto del modelo ESD_OUT y del paso de integración. El 74HCT4051 admite V_I hasta V_CC + 0.5 V. Se clasifican como **criterio**: hay que aplicar una tolerancia (≥ 50 mV) a las salidas de AO alimentadas por los mismos rieles.

## E6 — 330 pF

Picos (`s12c_capacitores.csv`), en el orden aire 8 kV / contacto 4 kV / red 253 Vrms:

| Condensador | Aire 8 kV | Contacto 4 kV | Red 253 Vrms |
|---|---:|---:|---:|
| 330 pF | 47.68 V | 44.79 V | 32.53 V (régimen continuo) |
| 3 nF | 5.20 V | 4.88 V | 3.57 V |
| 100 pF | 157.2 V | 147.6 V | 107.2 V |

**Exigir C0G de ≥ 100 V nominales para 330 pF**:

- deja ×2.1 sobre el pico de ESD y ×3 sobre la red continua;
- 50 V quedarían a ×1.05 de la ESD, sin margen frente a la tolerancia de la cadena GDT+MOV;
- es la tensión estándar del C0G en 1206 y no tiene coste apreciable.

3 nF: C0G de ≥ 25 V (50 V habitual). Los 100 pF siguen siendo los de 2 kV ya elegidos. La 3.3 kΩ (1.112 kV, 2.32 µJ) queda cubierta por la especificación ya decidida (≥ 1.5 kV, ≥ 25 µJ, ΔR ≤ 1 %). Sigue pendiente la calificación de su MPN.

## Otras observaciones

- La ganancia real es ×10.1 (91 k/10 k); Codex lo declara bien y la calibración lo absorbe.
- E1, E4, E5, E7 y E8 no presentan fallos. Las cifras que revisé (los picos de bi0 y los presupuestos) coinciden con el acta.
- La limitación de que el modelo no aleatoriza el silicio sigue en pie, como en S12b.

## Veredicto: qué falta para cerrar el bloque 2

El bloque 2 **no se puede cerrar todavía**, pero sólo faltan cambios pequeños y bien acotados:

1. **Decidir el buffer en X2** con un OPA4192 (buffer de X0, buffer de X2, A y un canal libre a masa). Si Keneth la acepta, entra un nuevo parámetro de diseño (D-xx). Es la única vía robusta con el máximo de fuga de hoja del 4051. Después hay que recalcular E2: X0 a 200 mV sin el término del mux, y X2.
2. **Rx0 = 10 kΩ**, y ≥ 10 kΩ ante el buffer de X2. El criterio de E3 pasa de «±4.9 V» a «corriente de entrada ≤ 50 µA» con el canal sin seleccionar.
3. **Espera de X2:** 3 ms sin buffer en X2, o 1.5 ms con él. Es decisión de firmware.
4. **330 pF C0G ≥ 100 V** y 3 nF ≥ 25 V en la lista de piezas.
5. Una **S12d corta** que confirme E2, E3 y E5 con el buffer de X2 (estabilidad con la carga del mux) y repase E8.

Fuera de la simulación siguen pendientes los MPN de 3.3 kΩ, 91 k/10 k y C0G, las curvas de impulso del RT1206 y, en banco, la fuga real y el offset de 20 V con X0 forzado.
