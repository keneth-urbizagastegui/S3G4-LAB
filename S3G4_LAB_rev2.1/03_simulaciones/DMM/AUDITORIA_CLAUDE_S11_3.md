# Auditoría de S11.3 (DMM, bloque 1, cierre con O4)

- Auditor: Claude Code, 7 oct 2026. Ejecutó: Codex. Contrato: `PLAN_SIMULACION_S11_3.md`, derivado de S11.1 y S11.2.
- Copia de trabajo: `C:\s113\a\b\DMM`. Hacen falta dos niveles de carpeta, porque `ejecutar_s11_2.py` usa `HERE.parents[2]`. No he tocado ningún archivo de Codex. Mis scripts están en `DMM/chequeo_claude/s11_3/`:
  - `comparar_smoke.py`;
  - `recalcular_raw.py`, con un lector `.raw` propio;
  - `inyeccion_rx.py`;
  - `forma_pico_x1.py`;
  - `diodo_schottky.py`.
- **Veredicto: el bloque NO se cierra todavía, pero le falta poco.** De los seis fallos del acta, dos y medio son artefactos o criterios mal aplicados. Los reales se arreglan cambiando una pieza o un valor cada uno (§8).

## 1. Reejecución y recálculo

- `ejecutar_s11_3.py --smoke --keep-raw`: 11/11 casos `ok` en 273.5 s; Codex tardó 274.4 s.
- `comparar_smoke.py` cruza 1664 valores de los 7 casos que coinciden. Los otros 4 casos son R1 que añadió la selección de smoke actual. Solo hay 7 valores con una diferencia relativa > 10⁻⁶, y todos son `d2n_E_sim_J`, del orden de 10⁻¹¹ a 10⁻⁴ J. Es ruido de signo en una energía despreciable y no afecta a ningún criterio.
- Recálculo desde el `.raw`:

| Caso | Magnitud | Claude | Codex |
|---|---|---|---|
| R3, 60 Vrms, apagado + diodo de cuerpo, riel +2 %, fuente off | P media de Rohm1 (últimos 5 ciclos) | 0.504827 W | 0.504827 W |
| | P media de la TVS / V(n1) pico | 0.233 W / 14.71 V | ≤ 0.266 W (en otro estado) |
| R6, +8 kV aire, modo V, RX0/RX2 = 100 Ω | V pico de Cc1 / Cc2 / Cc3 | 2014.75 V los tres | 2014.753 V |
| R6, −4 kV contacto, ídem | V pico de Cc1 | 1010.69 V | 1010.689 V |
| R1, diodo a 100 µA, riel −2 % / nominal / +2 % | tensión con la fuente al ≥ 99 % | 3.0466 / 3.1449 / 3.2420 V | 3.046638–3.241967 V |

Los números coinciden. Las diferencias de §3 y §6 vienen de la interpretación, no de la extracción.

## 2. C1, Cc1 (100 pF C0G, 630 V) en ESD: **físico**, pero el criterio está mal aplicado

- **Mecanismo.** En modo tensión no hay nada que limite V/Ω: el relé está abierto y la única carga son Rprot (99 kΩ) y el divisor (9 MΩ). Los 150 pF de la pistola se reparten con unos 33 pF de la compensación, y V(vin) llega a **3805 V a 4 kV y 7375 V a 8 kV**. Las tres Cc están en serie y se reparten esa tensión a partes iguales, unos 1011 V cada una. No es un artefacto.
- **Duración.** No es un pico de nanosegundos. Cc1 pasa **9.65 µs por encima de 630 V**, es decir, toda la ventana de 10 µs. Por cálculo: vin se descarga a través de unos 98 kΩ con unos 180 pF, τ ≈ 18 µs, y cada Cc pierde su carga por los 3 MΩ, τ ≈ 300 µs. El esfuerzo dura entre decenas y cientos de µs.
- **Criterio.** El 80 % de la tensión continua (504 V) no corresponde a un evento único de microsegundos. La referencia correcta es la tensión de prueba dieléctrica del fabricante (DWV, típicamente 120–150 % de Vr durante 1–5 s en MLCC de alta tensión). Para 630 V eso da unos 945 V, y **1011 V por contacto también la supera**. Por tanto el fallo por contacto es real con cualquiera de los dos criterios. El de aire (2015 V) es informativo.
- **Cambio mínimo:** cambiar el rating de las tres Cc a **100 pF C0G de 2 kV en 1206** (existen en catálogo; el MPN está por elegir). 1011 V quedan al 51 % de Vr, por debajo del 80 % incluso con el criterio estricto. Los 2015 V del aire quedan alrededor de Vr y por debajo de la DWV.
- **Lo que no midió nadie.** Con la misma ESD, cada Rprot de 33 kΩ en 1206 y cada Rdiv de 3 MΩ en 1206 aguantan **≈ 1268 V por contacto y ≈ 2458 V por aire**. Una 1206 de capa gruesa suele tener entre 200 V de tensión límite de elemento y 400 V de sobrecarga. Además, los contactos abiertos del relé ven unos 3.8 kV, frente a 1000 Vrms de dieléctrico. C1 pide evaluar cada pieza y estas faltan en el acta: hay que pedir **Rdiv y Rprot de alta tensión o antipulso**, con rating de pulso de hoja, o aceptar que la descarga salte en el relé o en la PCB. Lo marco como pendiente, no como aprobado.

## 3. C1, Rohm (2 × 1.1 kΩ, 2512) a 0.505 W: **físico, al filo del criterio**

- Codex supuso **1 W** (2512 estándar a 70 °C), así que el límite del 50 % es 0.5 W y el resultado sale al 101 %. Con la TVS sujetando N1 a ±14.7 V, cada resistencia ve aproximadamente (60·√2·sen − 14.7)/2.2 kΩ, y la cifra es coherente. Diez segundos bastan para llegar al régimen térmico de una 2512, así que es real.
- Lo que la movería:
  - una temperatura ambiente por encima de 70 °C, que obliga a reducir la potencia admisible y empeora el resultado;
  - una 2512 de **1.5–2 W**, de familias de alta potencia o antipulso; hay que confirmarlo con el MPN.
- Subir R (por ejemplo, 2 × 1.2 kΩ da unos 0.46 W) empeora C6. No conviene.
- **Cambio mínimo:** el mismo valor en **2512 de 2 W antipulso**, que queda al 25 %. Además, la ESD en modo ohmios pone hasta 2943 V instantáneos sobre Rohm, y eso pide también una pieza antipulso.

## 4. C1, Rprot a 0.172 W: **físico**

- Codex supuso **1206 de 0.25 W**, así que el límite es 0.125 W y el resultado sale al 69 % del rating, que es el 138 % del criterio. A mano: (230 V)²/99 kΩ/3 = 0.178 W, y la pequeña diferencia se debe a la sujeción en X0. Con red de 230 Vrms durante 10 s en modo tensión, la cifra es real, y 10 s bastan para que la 1206 llegue a régimen.
- **Cambio mínimo:** el mismo valor (33 kΩ) en **1206 antipulso de ≥ 0.5 W** (hay series de unos 0.66 W) o en 2512 de 1 W, que quedan al 26 % y al 17 %. Una serie antipulso cubre también la tensión de ESD de §2.

## 5. C3, inyección en X0/X1 por ESD: **X0 físico, X1 artefacto**

Comprobación con los peores estados del CSV de Codex. «Sostenido» quiere decir el máximo del mínimo móvil sobre 20 ns:

| Pin, caso | Bruto | Sostenido ≥ 20 ns | Con el cambio |
|---|---|---|---|
| X0, −4 kV contacto, sin RX0 | 37.7 mA | 37.3 mA | **RX0 = 100 Ω: 4.24 mA** |
| X0, −8 kV aire, sin RX0 | 73.3 mA | 72.9 mA | RX0 = 100 Ω: 4.64 mA |
| X1, +4 kV contacto, RX1 = 100 Ω | 8.29 mA | 4.82 mA | — |
| X1, +8 kV aire, RX1 = 100 Ω | **11.83 mA** | **5.24 mA** | — |

- **X0 es físico.** Sin resistencia, el diodo interno (proxy de 0.5 V y 1 Ω) queda en paralelo con el BAV199 exterior y se lleva la corriente. Con **RX0 = 100 Ω** el contacto baja a 4.2 mA, el 21 % de ±20 mA. Esos 100 Ω en serie con 99 kΩ no afectan a la medida.
- **El 11.8 mA de X1 es un artefacto.** Es un pico de una sola muestra, de 1 ns de anchura, a t ≈ 3.7 µs, no en el frente de la ESD. Su valor no es monótono con RX1: 100 Ω da 11.8 mA, 150 Ω da 14.5 mA y 220 Ω da 5.0 mA. La corriente sostenida es de 5.2 mA en aire y 4.8 mA por contacto, por debajo de 10 mA. **RX1 = 100 Ω basta.**
- **RX2 no hace falta:** la corriente es de 0 mA en todos los casos.
- El exceso de 0.5 V sobre el riel es un criterio mal puesto. El máximo absoluto de −0.5 V/VCC + 0.5 V del HC4051 rige cuando no se limita la corriente; lo que hay que vigilar es la corriente de sujeción, y el proxy de 1 Ω lo supera por construcción.
- **Cambio mínimo: RX0 = 100 Ω**, que es una pieza más. RX1 se queda en 100 Ω y no se pone RX2.

## 6. C6, diodo a 100 µA, 3.05–3.24 V frente a los 3.55 V estimados: **físico, por el diodo de bloqueo**

Cadena de caídas en el barrido (riel nominal, DUT = 3.5 V, unos 44 µA):

| Tramo | rp | − Vhead (P43) | − BSS84 | − **Dblk BAV199** | − Rs 3.3 kΩ | − Rohm 2.2 kΩ |
|---|---|---|---|---|---|---|
| V | 4.898 | 4.398 | 4.398 | **3.737 (−0.66 V)** | 3.593 | 3.500 |

- A 100 µA el BAV199 de bloqueo cae unos 0.68 V (su modelo da N·Vt·ln(I/Is) ≈ 0.676 V), y la resistencia fija de 5.5 kΩ, 0.55 V. La tabla §3.3 del rediseño marca «con DBLK» solo para O1, y su valor para O4, 3.55 V, se obtuvo sin el diodo de bloqueo. Esa es la diferencia. El riel de ±2 % explica la dispersión de ±0.1 V.
- La fuga pesimista de la TVS (unos 1.5 µA a 3.6 V) no influye en la compliance de la fuente, solo en la corriente que llega al DUT.
- **Cambio mínimo:** sustituir Dblk por un **Schottky de señal** con VF ≤ 0.24 V a 0.1 mA, que es el máximo de hoja de un BAT54. Lo comprobé en LTspice (`diodo_schottky.py`) con un modelo genérico ajustado a ese VF, que es un supuesto y no un modelo de fabricante: **3.48 / 3.58 / 3.68 V** con riel de −2 %, nominal y +2 %. Con riel −2 % falta 17 mV. Si se quiere margen, también Rs de 3.3 → 2.7 kΩ, que suma unos 0.06 V, o revisar Vhead en P43, que está fuera de este bloque.
- La fuga del Schottky no importa: durante la medida conduce en directa, y en inversa solo ve unos pocos voltios, porque N2 está sujeto a los rieles.
- **A 1 mA no es un fallo:** 1 mA por 5.5 kΩ son 5.5 V, más de lo que da el riel. El plan pide solo «informar», y la cifra de 0.53–0.56 mA en silicio coincide con los 0.60 mA estimados.

## 7. C7, nueve timeouts de R7 en modo tensión: **falta de tiempo, no riesgo**

- Los nueve casos son 230 Vrms durante 12 s con paso de 50 µs. Al cortar, el `.raw` había llegado a 5.8–9.0 s, antes de retirar la tensión. El único estado de smoke que terminó tardó 261 s, al borde del límite de 300 s, y recuperó en 40 µs en X0 y 0.79 ms en N2.
- Las constantes de tiempo del modo tensión son de cientos de µs: 3 MΩ·100 pF, 100 kΩ·3 nF y el riel de 1 µF regulado. No hay ningún elemento térmico ni de memoria en el modelo, y nada da tiempos cercanos a 1 s.
- **No hay riesgo físico identificable.** Basta con relanzar esos nueve con un límite de 900 s, o con 1 s de fallo (régimen periódico) más 2 s de recuperación.

## 8. Resumen y cambios mínimos

| Fallo del acta | Clasificación | Cambio mínimo |
|---|---|---|
| Cc1 1011 V por contacto | Físico (supera también la DWV); el criterio del 80 % en continua no es el adecuado para un pulso | 3 × 100 pF C0G **2 kV** 1206 |
| Cc1 2015 V por aire | Informativo | — (con 2 kV queda por debajo de la DWV) |
| Rohm 0.505 W | Físico, al filo (101 %) | 2 × 1.1 kΩ 2512 **2 W antipulso** |
| Rprot 0.172 W | Físico (138 % del criterio) | 3 × 33 kΩ **1206 antipulso ≥ 0.5 W** (o 2512) |
| X0 73 / 37 mA | Físico | **RX0 = 100 Ω** |
| X1 11.8 mA | Artefacto (pico de 1 ns); sostenido 5.2 mA | Ninguno (RX1 = 100 Ω) |
| Exceso de 0.5 V del proxy | Criterio mal puesto | — |
| Diodo 3.05–3.24 V | Físico (Dblk ≈ 0.68 V) | Dblk → Schottky (VF ≤ 0.24 V a 0.1 mA): 3.48–3.68 V; opcional Rs 2.7 kΩ |
| C7, 9 timeouts | Tiempo de simulación | Relanzar con 900 s |
| Sin evaluar: Rdiv/Rprot ≈ 1.27 kV por contacto; relé abierto ≈ 3.8 kV | Pendiente de C1 | Rdiv/Rprot de alta tensión o antipulso con rating de pulso |

## 9. Qué falta para cerrar el bloque 1

1. Que Keneth acepte los cambios: Cc de 2 kV, Rohm de 2 W antipulso, Rprot antipulso, RX0 = 100 Ω y Dblk Schottky (más Rs = 2.7 kΩ si se quiere margen en el riel −2 %). No los doy por aprobados.
2. Una simulación corta de confirmación (S11.3b), no una campaña:
   - R6 por contacto con RX0;
   - R1 con el modelo de fabricante del Schottky elegido; el BAT54 o similar no está en `models/`, y descargarlo es decisión de Keneth;
   - los nueve R7 de tensión con un límite de 900 s.
3. Elegir MPN con rating de pulso para Rohm, Rprot, Rdiv, Cc y el derivador, y comprobar la tensión de pulso de Rdiv/Rprot y el aislamiento del relé abierto frente a unos 3.8 kV, o aceptar ese salto de forma explícita.
4. Siguen abiertas, como dice el acta: la fuga real (C5, en prototipo), la hoja del BZT52C5V6 y la ausencia de un modelo destructivo para R3b.
