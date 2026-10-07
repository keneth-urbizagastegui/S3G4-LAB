# Auditoría de S11.1 (DMM, bloque 1: bornes y protección)

- Auditor: Claude Code, 7 oct 2026. Ejecutó: Codex. Contrato: `PLAN_SIMULACION_S11_1.md` (§3b, §3c y §7).
- Copia de trabajo: `C:\s11a`. No se ha tocado nada de Codex dentro de `DMM/`. Los scripts de la auditoría están en `DMM/chequeo_claude/` (`comparar_smoke.py`, `auditar_raw.py`, `extrapolar_nunca.py` y `extraer_hojas.py`). El lector `.raw` es propio y no usa `leer_raw_s11_1.py`.
- **Veredicto: el bloque NO se aprueba**, como dice el acta. Los fallos C1, C2 y C3 son físicos. El acta, además, se queda corta en tres puntos: no marca como fallo la TVS (potencia de pulso) ni la PTC (Imax), y C4 no es «orientativo», sino que no se cumple.

## 1. Reejecución

- La copia de `C:\s11a` es idéntica, byte a byte, a `ejecutar_s11_1.py`, `leer_raw_s11_1.py` y los dos `.inc`. Los modelos (OPA2188 y 74HC4051) se copiaron a `C:\s11a\models`, y la ruta se pasó con `S3G4_MODELS`.
- Resultado de `ejecutar_s11_1.py --smoke --keep-raw`: 14/14 casos `ok` en 71 s.
- `comparar_smoke.py`: en los 14 casos se compararon 3974 valores numéricos con `resultados/s11_1_smoke_mixta.csv` y con las mismas filas de `s11_1_campana_mixta.csv`. **Diferencia máxima: 0.** Ningún valor difiere más de 1e-3.
- Recálculo independiente desde el `.raw` con `auditar_raw.py`:

| Caso | Magnitud | Claude (.raw) | Codex |
|---|---|---|---|
| P3, R_S = 100 Ω, apertura a 20 ms, fase 0, 40 Ω | E de la TVS hasta 1 s | 1.8589 J | 1.85903 J (máx. del grupo) |
| P3, R_S = 330 Ω, ídem | E de la TVS / span máx. | 1.8590 J / 20.54 V | 1.85911 J / — |
| P3, R_S = 100 Ω, **nunca** (deck propio: `Brc` = 1) | E de la PTC / E de la TVS / disparo | 50.411 J / 3.2715 J / 35.67 ms | 50.4106 / 3.2715 J (`energias.csv`) / 35.67 ms (máx.) |
| P3 nunca | Extrapolación de 1 a 10 s (PTC / TVS) | 20.065 / 0.643 J | 20.065 / 0.643 J (rechazada) |
| P5, 0.5 Ω, R_S = 100 Ω, fase 0 | Pico de DF08S / I²t hasta 8.3 ms | 386.21 A / 603.68 A²s | 386.213 A / 603.676 A²s |

Todo coincide.

## 2. Netlists frente al plan (§1, §3b y §3c)

- **Valores.** Coinciden con el §1:
  - 3 × 33 kΩ y 3 × 3 MΩ – 900 kΩ – 100 kΩ;
  - 3.3 kΩ + 100 pF, 330 pF y 3 nF;
  - relé con Ron 0.1 Ω, Coff 1 pF y suelta a +3 ms;
  - fusible de 40 mΩ, derivador de 0.100 Ω y 10 MΩ hasta X5;
  - 1 µF por riel y 3 mA de carga total;
  - R_S ∈ {100, 330} Ω y PTC de 40 y 60 Ω.
- **Red.** La fuente es `325.269·sin(2π·60·t + fase)`, es decir, 230 Vrms a 60 Hz. ✔
  - En V/Ω, Rgrid vale 1 µΩ (red ideal, caso pesimista).
  - En el borne A, Rgrid vale 0.5, 1 y 2 Ω.
- **Modelo reducido.** Las páginas citadas se han comprobado:
  - OPA2188, p. 4: ±0.5 V y ±10 mA. ✔
  - 74HC4051, p. 5: VCC de 11 V, ±20 mA de sujeción y ±25 mA de canal. ✔
  - BSS84, p. 2: −50 V, ±20 V, −130 mA, −1.2 A y 300 mW. ✔
  - Las capacidades (OPA p. 5, HC p. 10) y la TLV2372 no se han comprobado una por una.
- **Reparo del modelo reducido.** Las protecciones internas se modelan como diodo ideal con Vfwd = 0.5 V y Ron = 1 Ω. Ese diodo es más «duro» que el BAV199, cuyo modelo tiene IS = 0.8 fA, así que **les roba la corriente a los BAV199 externos** (en P3, I(D2p) ≈ 0 e I(D2n) ≈ 1.3 mA). El reparto entre la protección interna y el BAV199 depende del modelo. Que haya inyección no depende de él (ver §6a).
- **Carga de los rieles en el modelo reducido.** Es solo resistencia entre rp y rn, 3 mA a 9.8 V. Los reguladores no absorben corriente: `REGSUP` es de un solo sentido, como un LDO real.

## 3. P3: estado del relé y de la fuente

Caso de R_S = 100 Ω con apertura a 20 ms:
- **Antes de la apertura**, |V(vin, ptin)| máx. = 0.77 V. Equivale a 7.7 A × 0.1 Ω: el relé está **cerrado** desde t = 0. ✔
- **A partir de t = 23 ms** (20 ms + 3 ms de suelta), I_PTC < 1.3e-7 A y la tensión en los contactos llega a 329.6 V: el relé **se abre**. ✔
- **Fuente.** I(Vsense)(0) = 1.000 mA, que es el estado declarado. Después, I(Vsense) se vuelve negativa (−5.8 mA a 1 ms): es el diodo de cuerpo del BSS84 conduciendo hacia el riel.

## 4. Energías

- Se integran sobre el tiempo simulado real, de 0 a 1 s. La parte extrapolada (de 1 a 10 s) va en columnas separadas. ✔
- **Desviación declarada:** no se corta en el disparo, sino que se simula siempre 1 s. Es aceptable y más conservador.
- **Artefacto en la validación de la extrapolación.**
  - Para el caso «nunca», Codex exige R_PTC ≥ 0.99 MΩ. El propio modelo autorregula en torno a R_PTC ≈ 21 kΩ (θ = 1.25, 10 mA rms).
  - Por eso **las 0/18 extrapolaciones válidas son un criterio inalcanzable**, no una falta de convergencia.
- **Mi extrapolación** (últimos 5 ciclos, dispersión del 5–9 %, así que solo es estimación):

| Pieza | Simulada 0–1 s | Extrapolada 1–10 s | Total en 10 s |
|---|---|---|---|
| TVS | 3.27 J | 0.64 J | 3.91 J (0.071 W medios, frente a 1 W continuo de la p. 2) |
| PTC | 50.4 J | 20.1 J | 70.5 J |

## 5. Modelo de la PTC frente a `ptctl.pdf`

Datos de la hoja (p. 1, fila PTCTL4MR500SBE):
- 50 Ω ± 20 % y 600 Vrms;
- Int = 50 mA a 70 °C e It = 140 mA a 25 °C;
- t máx. = **1.0 s a 1 A**;
- **Imax = 1.0 A a Vmax**.

La hoja no trae curva R(T), curva de disparo ni masa térmica.

Modelo de Codex:
- dθ/dt = P/Ecrit − θ/τ;
- G = R·0.14², con lo que el umbral asintótico queda en 140 mA;
- Ecrit se elige para que 1 A dispare exactamente en 1 s. Lo he comprobado: θ(1 s) = 51.02·(1 − e^(−1/50.52)) = 1.000.

Valoración:
- **Es aceptable como cota lenta del disparo**, porque toma el t máx. de la hoja y eso es pesimista para la TVS.
- τ = 50.5 s, R_caliente (exponencial hasta 1 MΩ) y el enfriamiento son supuestos sin fuente. Lo correcto es tratarlos así.
- **Lo que el acta no evalúa:** la corriente real en la PTC es de **7.7 A de pico (≈ 5.4 A rms)** con 40 Ω, frente a **Imax = 1.0 A** (p. 1). No hay otro dato de corriente máxima en la hoja.
- Por tanto, con la información disponible, **la PTC está fuera de su hoja en C1**. Es físico y no depende del modelo térmico: I ≈ 325/(40 + R_TVS) mientras la PTC está fría.

## 6. Fallos del acta: ¿físicos o artefactos?

### (a) Rieles a 24 V en P3: físico

**Por dónde entra la corriente** (R_S = 100 Ω, fase 0, 40 Ω):
- La TVS fija N1 en 14.5–16.7 V (16.69 V de pico).
- Medio ciclo positivo: N1 → R_S → N2 → **diodo de cuerpo del BSS84** (drenador N2, fuente al riel a través de Vsense y Vhead) → rp.
  - Pico de I(R_S): 65.5 mA en este caso; 118.6 mA de máximo en la campaña.
  - Corriente por el diodo de cuerpo: unos 131 mA de pico.
  - El BAV199 de N2 no conduce, porque IS = 1 nA del diodo de cuerpo frente a 0.8 fA del BAV199.
- Medio ciclo negativo: casi todo va por la sujeción interna del 4051 en N2 (`Xh6`) hacia rn.

**Carga supuesta:** 3 mA en total, como resistencias entre rp y rn (unos 3.27 kΩ). El regulador no absorbe corriente.

**Resultado:**
- rp llega a 16.46 V y rn a −15.77 V; el span es de **24.12 V** a 17 ms (Codex: 24.20 V de máximo).
- En el último segundo del caso «nunca», con la PTC ya disparada, rp sigue llegando a 14.5 V y rn queda en −10.2 V.

**Por qué es físico:** inyectar más de 60 mA frente a 3 mA de consumo en un riel que no absorbe corriente lo bombea, y ni un LDO ni un interruptor de carga reales lo evitan. Los 24 V exactos sí son del modelo: un 4051 o un OPA reales conducirían o se averiarían antes de llegar ahí. Lo que no cambia es que **C2 falla por un factor de 20 a 40** y que el 4051 queda por encima de sus 11 V (p. 5).

**P4 (DMM apagado) sí cumple el span:** 9.08 V < 11 V.

### (b) Fuga de la TVS del 74 %: artefacto en la magnitud, fallo real

- **Modelo usado:** `I = V·TVLEAK/12` con TVLEAK = 5 µA. Toma la fuga **máxima** de la hoja a VRWM = 12 V (p. 3: IR ≤ 5 µA; la nota 10 solo la duplica en VRWM ≤ 10 V) y la aplica como **resistencia lineal de 2.4 MΩ**.
- **A 0–4 V:** da 0 a 1.67 µA (1.78 µA medidos a 4.26 V). La hoja no da fuga por debajo de VRWM; un valor típico real a 4 V está en nA o menos. **Los 735 000 y 410 000 ppm son un artefacto pesimista.**
- **Aun así, el fallo es real.** El límite de C5 equivale a 0.2 nA de fuga total en N1 + N2 (1000 ppm de 0.2 µA, o 200 ppm de 1 µA).
  - Ninguna TVS de 400 W lo garantiza.
  - El propio modelo del BAV199 da 2.2 nA a unos 4 V. La hoja (p. 3) da 3 pA típicos y 5 nA máximos a 75 V.
- Conclusión: C5 no se puede cumplir con una garantía de hoja. Haría falta medir, o tener en cuenta la fuga en el diseño. No simulo remedios.

### (c) DF08S a 386 A y 604 A²s: el cálculo es correcto; la magnitud viene de no abrir el fusible

Cálculo a mano:
- Rth = 0.5 Ω (red) + 0.04 Ω (fusible) = 0.54 Ω.
- Diodo del modelo: n·VT = 0.0517 V, IS = 7.45e-10 A y Rs = 0.02 Ω. A 386 A cae 0.0517·ln(386/7.45e-10) + 386·0.02 = 1.39 + 7.72 = 9.11 V. Con dos diodos en serie, la rama cae **18.2 V** (V(shunt) en el `.raw`: 18.24 V).
- Por el derivador pasan 18.2/0.1 = 182 A.
- Corriente total: (325.3 − 18.2)/0.54 = **568.6 A** (`.raw`: 568.6 A).
- Por el puente: 568.6 − 182 = 386 A.
- I²t de medio seno: 386²·8.33 ms/2 ≈ 621 A²s (`.raw`: 604 A²s hasta 8.3 ms).

Valoración:
- **La aritmética de Codex es correcta.**
- **Rs = 20 mΩ por diodo es un supuesto.** Si el DF08S real tiene más resistencia a 100 A, una parte mayor de la corriente va al derivador. Aun así, la corriente seguiría estando muy por encima de 50 A.
- **El factor 58× es un artefacto del supuesto «el fusible no abre en 10 ms»** (§1.3 del plan). Con 569 A presuntos, un fusible de 3.15 A funde en menos de 1 ms. Hasta 0.5 ms y hasta 1 ms (fase 0):

| Hasta | I²t total | I²t en el DF08S |
|---|---|---|
| 0.5 ms | 1.8 A²s | 0.39 A²s |
| 1 ms | 14.4 A²s | **4.9 A²s** (frente a 10.4 A²s; el criterio del 50 % es 5.2 A²s) |

- Con fase 90° (cierre en el pico), el DF08S ve 386 A desde el primer instante.
- **Es probable que siga siendo un fallo real**, pero el margen depende de la I²t de fusión y de arco del fusible, que no está en el proyecto. No se certifica ni en un sentido ni en otro.

### (d) Relé abriendo con 230 Vac: físico

Corriente que corta realmente, medida en el `.raw`:
- **Apertura ordenada a 20 ms (real a 23 ms):** 4.62 A instantáneos con 222.7 V en la red (4.77 A con R_S = 330 Ω). Los máximos de la hoja (C46047, p. 6) son 125 Vac, 2 A y 62.5 VA. Es unas **16 veces la potencia de corte**, con 230 V en lugar de 125 V. Fallo físico.
- **Apertura a 100 ms (real a 103 ms):** la PTC ya ha disparado y corta 0.138 A (unos 32 VA). Corriente y potencia están dentro de hoja; solo la **tensión** de 230 V supera los 125 Vac. Es un fallo menor, pero también contra la hoja.
- Abierto, el relé soporta 329.6 V de pico frente a 1000 Vrms entre contactos abiertos (p. 6). ✔

### (e) BSS84 con VDS de 24 V: no es un fallo

- VDS = V(n2) − V(msource) llega a −23.7 V (−24.3 V de máximo en la campaña) frente a VDSS = −50 V (p. 2): un 49 %, dentro del 80 % de C1.
- Es una consecuencia del bombeo de los rieles (§6a), no un fallo propio.
- El dato que se acerca al límite es la **corriente del diodo de cuerpo**: unos 131 mA de pico en pulsos de milisegundos, frente a ID = −130 mA continuos e IDM = −1.2 A en pulsos (p. 2). La disipación es de unos 0.1 W frente a 300 mW. **Queda al límite, sin fallo claro.**
- El límite de «0.065 A» que usa el acta no sale de ninguna hoja que haya encontrado.

### Fallos que el acta no marca

- **TVS en C1.** La potencia de pico es de 128.4 W en medios senos de unos 8 ms. La Fig. 3 de la hoja (p. 4) permite unos 150–200 W a 8–10 ms, **no repetitivos**. Se repite en 4 o 5 semiciclos (40 Ω) y hasta unos 9 (60 Ω, disparo a 78 ms).
  - Frente al 50 % que pide C1 (unos 80–100 W), **falla**.
  - Frente al máximo absoluto queda al límite y además se repite.
  - Es físico: la corriente la fija la PTC fría y la tensión la fija la TVS.
- **PTC en C1:** ver §5 (7.7 A frente a Imax = 1 A).

## 7. Máximos citados, comprobados con su página

| Pieza | Valor del acta | Página | ¿Correcto? |
|---|---|---|---|
| PTCTL4MR500SBE | 50 Ω ± 20 %, 600 V, 50/140 mA, 1 s a 1 A, Imax 1 A | p. 1 | ✔ (Imax citado, pero no aplicado en C1) |
| SMAJ12CA | 400 W, 1 W a TL = 75 °C, 13.3–14.7 V, 19.9 V a 20.1 A, 5 µA a 12 V | pp. 2–3 | ✔. Falta citar la Fig. 3 de la p. 4 (pulsos de ms) |
| BAV199 | 75/85 V, 140 mA, 250 mW, 4 A/1 µs, 1 A/1 ms, 5 nA | pp. 2–3 | ✔ (además, IFSM = 0.5 A durante 1 s; IR típica de 3 pA) |
| DF08S | 800 V, 1 A, 50 A en 8.3 ms, 10.4 A²s, 1.1 V a 1 A | p. 2 | ✔ |
| BSS84 | −50 V, ±20 V, −130 mA, −1.2 A, 300 mW | p. 2 | ✔ |
| TQ2SA (C46047) | 125 Vac / 220 Vdc, 2 A, 1000 Vrms, suelta ≤ 4 ms | p. 6 | ✔ (y 62.5 VA en AC) |
| OPA2188 | 40 V, entradas ±0.5 V y ±10 mA | p. 4 | ✔ |
| 74HC4051 | VCC 11 V, ±20/±25 mA | p. 5 | ✔ |

## 8. Tabla de criterios

| Criterio | Codex | Claude | Motivo |
|---|---|---|---|
| C1 | FALLA | **FALLA** (y más amplio) | Relé al cortar 4.6 A a 230 V (físico). TVS a 128 W repetidos frente a la Fig. 3 (no lo marca el acta). PTC a 7.7 A frente a Imax de 1 A (no lo marca el acta). DF08S: probable fallo, aunque los 58× son un artefacto de no abrir el fusible |
| C2 | FALLA | **FALLA (física)** | 65–131 mA inyectados frente a 3 mA de carga; span de 24 V. Sigue con la PTC disparada |
| C3 | FALLA | **FALLA (física)** | 4051 a más de 11 V y sujeción interna a más de 20 mA (el reparto depende del modelo). El VDS del BSS84 **no** es fallo |
| C4 | ORIENTATIVO | **NO CUMPLE** | Aunque la PTC dispare, C1 (PTC y TVS) y C2/C3 fallan durante los 10 s sin firmware. No depende del modelo térmico |
| C5 | FALLA MODELO | **FALLA** (magnitud exagerada) | Fuga lineal desde el máximo a 12 V. El límite equivale a 0.2 nA, que nada en N1/N2 garantiza |
| C6 | PASA, no certificado | PASA, no certificado (no reverificado) | 3.90 V ≥ 3.5 V; solo 1 de 6 casos completos con R_S = 330 Ω |
| C7 | NO CERTIFICADO | NO CERTIFICADO | P7 no parte del estado tras 10 s |

## 9. Pendientes que no son de Codex

- I²t de fusión y de arco del fusible de 3.15 A, para cerrar (c).
- Una cifra de fuga real de la SMAJ12CA a 4 V (medida).
- Confirmar con Vishay si Imax = 1 A se aplica a 230 V.
- La cobertura de P1 es incompleta: 33 casos agotaron el tiempo y 1 tuvo fallo numérico. Eso limita C5 y C6.
