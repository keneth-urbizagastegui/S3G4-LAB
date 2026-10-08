# Auditoría de S11.2 (DMM, bloque 1 rediseñado: O2 y borne A con GBU808)

- Auditor: Claude Code, 7 oct 2026. Ejecutó: Codex. Contrato: `PLAN_SIMULACION_S11_2.md` (§6), derivado de `PLAN_SIMULACION_S11_1.md` y `REDISENO_BLOQUE1.md` §2.3.
- Copia de trabajo: `C:\s112`. No se ha tocado ningún archivo de Codex. Scripts propios en `DMM/chequeo_claude/s11_2/`: `comparar_smoke.py`, `recalcular_raw.py` (lector `.raw` propio) y `verificar_rlim_tj.py`.
- **Veredicto: el bloque NO se aprueba**, como dice el acta. Pero la clasificación cambia:
  - **físicos:** ESD sobre el par O2 (C1/C4), C3 (por el divisor, no por O2), la ventana de R_LIM y, por poco, la Tj a 70 °C;
  - **criterio mal puesto:** C8 por pico y C2 en Q3/Q4 (inyección frente a carga, cuando ya hay sumidero zéner);
  - **C6 a 1 mA** no es un fallo (el plan dice «informar»); a 100 µA sí falla, por 0.13 V, y la causa principal es el diodo de bloqueo.

## 1. Reejecución

- `ejecutar_s11_2.py --smoke --keep-raw --only Q3 Q5 Q4 Q1 Q6` en `C:\s112` (con `S3G4_MODELS` apuntando a los modelos del proyecto): 5/5 `ok` en 41.4 s. Codex dio 41.4 s.
- `comparar_smoke.py` frente a `resultados/s11_2_smoke.csv`: 894 valores numéricos comparados. **Diferencia máxima: 0.**
- Recálculo independiente desde el `.raw` (`recalcular_raw.py`):

| Caso | Magnitud | Claude (.raw) | Codex |
|---|---|---|---|
| Q3, 0 °C, IDSS 7 mA, V_th −1.6 V, fase 0, 1 s | ¿Relé cerrado? \|V(vin)−V(ptin)\| máx. | 1.3·10⁻⁴ V (cerrado los 1 s integrados) | — |
| | I_lim / P media FET1 / FET2 | 1.3068 mA / 0.130677 / 0.134135 W | 1.30683 mA / 0.130677 / 0.134135 W |
| | Tj (método de Codex) FET1 / FET2 | 32.669 / 33.534 °C | 32.669 / 33.534 °C |
| | V_pk·I/π (a mano) | 0.1353 W | — |
| Q5, 0.5 Ω, k = 1, fase 0 | ¿Abre por la hoja? I²t del fusible al abrir | 6.7003 A²s a 769.06 µs; 6.5·10⁻¹⁰ A después | 769.08 µs |
| | Pico / I²t por diodo del GBU808 | 107.50 A / 2.5722 A²s | 107.4995 A / 2.5722 A²s |
| Q6, −4 kV contacto, ohmios | V_DS1 / V_DS2 / V_GS | 1459.4 / 1830.2 / 826.7 V | 1459.4 / — / 826.7 V |
| Q1, 1 mA, V_th −1.6, riel −2 % | Tensión disponible | 1.2709 V | 1.270904 V |

Todo coincide. El relé no se abre en Q3 y el fusible abre en Q5 cuando su I²t llega a 6.7 A²s (§6, puntos 3 y 4).

## 2. Modelo del BSS126 frente a la hoja (Infineon rev. 2.1)

| Dato | Hoja (página) | Modelo `bss126_s11_2.inc` | ¿Bien? |
|---|---|---|---|
| V_DS / V_GS / P_tot / Tj | 600 V, ±20 V, 0.50 W, 150 °C (p1) | BV 600 V; **sin ruptura de puerta** | sí; la puerta, no |
| **ESD HBM** | **Clase 0 (< 250 V)** (p1) | no modelado | falta, y es clave en Q6 |
| I_D,pulse / I_S,pulse | 85 mA / 64 mA (p1, p3) | sin límite | falta |
| R_thJA | 250 K/W, huella mínima (p2) | lo usa Codex fuera del modelo | ver C1 |
| I_DSS | ≥ 7 mA a V_GS 0, V_DS 25 V; **sin típico ni máximo** (p2) | 7 mA; 21 mA como sensibilidad | sí |
| V_GS(th) | −2.7 / −2.0 / −1.6 V a 8 µA, V_DS 3 V (p2) | ajuste exacto a 8 µA | sí |
| Bandas H6906 | J…N, 0.2 V de ancho por bobina, sin poder pedirse (p2) | no se usan | ver R_LIM |
| R_DS(on) | 320 típ. / **700 máx.** a V_GS 0, 3 mA (p2) | **700 Ω en todos los casos** | conservador para C6 |
| C_iss / C_oss / C_rss | 21 / 2.4 / 1.0 pF típ. (p3) | Cgs 20 + Cgd 1; Cds 1.4 + Cgd 1 | sí |
| V_SD | 0.81 típ. / 1.2 máx. a 16 mA (p3) | Is 2n, N 2, Rs 1 → 0.83 V | sí |
| Zth | curva p4, fig. 4 | no la usa nadie | ver C1 |
| Deriva térmica | curvas típicas p5–p6 | −3.7 mV/K y Ron·e^{0.0055ΔT} | supuesto, no garantía |

- **Artefacto:** la R_on (≈ 565 Ω de `Rd`) está en serie con el diodo de cuerpo y con el de avalancha. Con amperios de ESD, la caída en `Rd` infla V_DS: en el caso −4 kV, 1459 V ≈ 2.58 A × 565 Ω. Un MOSFET real modula la conductividad de la deriva con esa corriente, aunque a esa corriente se destruye antes (85 mA de pulso).
- La Ley de Shockley entre los dos puntos garantizados (I_DSS y 8 µA) es una aproximación: la hoja **no** garantiza puntos intermedios.

## 3. R_LIM: ¿hay alguna selección garantizable?

`verificar_rlim_tj.py`, a 25 °C:
- **Cota alta.** Sin I_DSS máximo, la cota sale de la hoja sin modelo. Si I·R_LIM > |V_th|máx = 2.7 V, el FET limitador queda por debajo del umbral (8 µA a V_DS 3 V). Por tanto, I_lim ≤ 2.7 V / R_LIM, y ≤ 2.4 mA exige **R_LIM ≥ 1125 Ω**. Es el mismo número de Codex: la condición «I_DSS → ∞» es exactamente esa cota.
- **Cota baja.** Con I_DSS 7 mA y V_th −1.6 V, ≥ 1.3 mA exige **R_LIM ≤ 724.9 Ω** con Shockley. Con 1125 Ω, el peor bajo da 0.93 mA.
- **Confirmado: no hay intersección** (725 frente a 1125 Ω). Y la cota baja ni siquiera es de hoja: depende de Shockley.
- **Qué lo movería:**
  - Elegir R_LIM por banda de bobina (H6906). Banda J: R ≤ 725 Ω da como máximo 2.48 mA (un 3 % por encima de 2.4). Banda N: R ≤ 997 Ω da 2.41 mA. Casi cierra, pero exige montar la R según la etiqueta de la bobina.
  - Un techo de 2.4 mA más alto, si el criterio de potencia se cambia por Zth (ver C1).
- **A 70 °C** el techo baja: 50 % de P_tot(70 °C) = 0.16 W → 1.55 mA. Con Zth y Tj ≤ 120 °C → 2.25 mA. La ventana a 70 °C queda en 1.3–1.55 mA.

## 4. Criterios C1–C8

| # | Codex | Claude | Motivo |
|---|---|---|---|
| C1 (Tj) | FALLA, 135.66 °C | **FALLA, física pero menor** (≈ 120–133 °C) | Ver C1 abajo. Sólo falla con I_DSS 21 mA (supuesto). Con 7 mA / −2.7 V a 70 °C, Tj ≈ 111 °C |
| C1 (P 50 %) | FALLA, 0.263 W frente a 0.16 W | **FALLA según el criterio**; dudoso como criterio | 50 % de P_tot en DC para un evento de 10 s. Con Zth(10 s), el 50 % es 0.258 W: queda un 2 % por encima |
| C1 (ESD) | FALLA | **FALLA física** | V_GS 827 / 1592 V frente a ±20 V; HBM clase 0. Ver ESD |
| C2 | FALLA, 5.88 mA y 11.17 V | **Q3/Q4: criterio mal puesto. ESD: física y marginal** | Ver C2 |
| C3 | FALLA, 432 mA | **FALLA física, pero no de O2** | Entra por la compensación del divisor, no por el limitador. Ver C3 |
| C4 | FALLA | **FALLA** | Por ESD y R_LIM. La Tj de 10 s queda en el límite, no muy por encima |
| C5 | Informativo | Informativo | De acuerdo |
| C6 | FALLA (1 mA: 1.27–1.52 V) | **A 1 mA no es fallo** (el plan dice «informar»). **A 100 µA falla** (3.374–3.577 V; nominal 3.47 V) | Ver C6 |
| C7 | No certificado | **No certificado** | 12/12 timeouts. Sin dato, ni a favor ni en contra |
| C8 | FALLA, pico 423.6 A frente a 100 A | **Criterio mal puesto en el pico; I²t pasa (6.6 % de 166 A²s)** | Ver C8 |

### C1. Tj de 135.66 °C

- **Cálculo de Codex:** Tj = 70 + 250 × E₁₀/10, con la R_thJA **en estado estacionario** (huella mínima, p2) aplicada a 10 s.
- **La parte de la hoja que aplica es la fig. 4 de la p4 (Zth).** El pulso único a 10 s se lee en **≈ 155 K/W** (140–170 según la lectura); la curva llega a 250 K/W cerca de 100 s.
- **Codex omite el rizado.** La potencia llega en semiondas: 0.525 W durante 8.3 ms, con Zth(8.3 ms) ≈ 60 K/W, lo que suma ≈ 16 K.
- **Resultado:** Tj ≈ 70 + 0.263·155 + 0.263·60 ≈ **126.5 °C** (120–133 °C con la incertidumbre de lectura), frente a 120 °C. Sigue fallando, pero por 0–13 K y no por 15.7 K.
- **Sólo falla con el supuesto I_DSS = 21 mA.** Con 7 mA y −2.7 V a 70 °C: P = 0.189 W → ≈ 111 °C.
- **Mecanismo:** P ≈ V_pk·I_lim/π = 325·I_lim/π por FET; el FET que bloquea se lleva toda la semionda.
- **Qué lo movería:** a 70 °C, Tj ≤ 120 °C exige P ≤ 0.233 W, es decir, I_lim ≤ 2.25 mA. También una R_th real menor (cobre en la huella; los 250 K/W son de huella mínima).

### C2. Inyección de 5.9 mA y span de 11.17 V

- **Camino:** el peor caso de Q4 suma +5.884 mA = 2.569 mA (limitador por D2p) + ≈ 3.28 mA por el **camino de tensión**. Son 325 V / 99 kΩ por R_PROT → x0 → D0p → rp.
  - Ese camino está siempre conectado a V/Ω, con el relé cerrado o abierto.
  - Los −3.26 mA del negativo son el mismo camino de R_PROT; el limitador va a COM por D2n.
- **Es físico, pero el criterio «≤ carga del riel» es de S11.1, cuando no había sumidero.** Ahora están los zéner (I_Z máx. 4.77 mA, ≈ 27 mW de pico frente a cientos de mW).
- **La magnitud que importa cumple:** span máx. 10.68 V en Q3 y 7.94 V en Q4, frente a 11 V. → **Criterio mal puesto en Q3/Q4.** Hay una salvedad: el zéner es supuesto, porque falta la hoja del BZT52C5V6.
- **ESD a 8 kV (11.174 V): físico y marginal.**
  - La carga es Q = 150 pF × 8 kV = 1.2 µC, que entra en 1 µF → ΔV = 1.2 V (rp llega a 6.13 V). Coincide con el CSV.
  - **Qué lo movería:** ≥ 1.15 µF efectivos en rp. Con un 1 µF −20 % el exceso crece (≈ 1.5 V). Un zéner real a cientos de mA tiene menos de los 40 Ω supuestos y recortaría antes.

### C3. Sujeción del 4051 a 432 mA

- **No viene del limitador.** En ohmios N2 ya no va al 4051 (canal 6 retirado). El pico máximo es `xh1` (canal **x1, toma del divisor**) en **modo tensión, relé abierto, −8 kV**.
- **Camino:** la compensación del divisor, 3 × (3.3 kΩ + 100 pF) en paralelo con los 3 × 3 MΩ. Para un frente de ns, los condensadores son cortos.
  - I ≈ 8000 / (630 + 9900) ≈ 0.76 A hacia x1, repartida entre el BAV199 D1n y el diodo interno del 4051 (≈ 57 %).
  - En mi caso a −4 kV en ohmios: I(Rc1) = 0.319 A (≈ 4000/10.2 k) y `xh1` = 268 mA.
  - El camino de R_PROT (99 kΩ) sólo da ≈ 80 mA a 8 kV (`xh0` = 73 mA). La ESD por el par O2 va a D2p/D2n y no a un pin.
- **Físico.** El reparto BAV/4051 depende del modelo `PINHC`. El camino existía en S11.1 y no lo crea O2.
- **Qué lo movería:** para ≤ 10 mA en el pin, la corriente hacia x1 tiene que bajar ~40–75 veces, o el reparto tiene que cambiar. Ejemplos: R en serie entre x1 y el pin del 4051 (con 1 V de exceso, ≈ 100 Ω da 10 mA), o una R_c mayor en la compensación.

### C6. Diodo a 1 mA: 1.27–1.52 V frente a los 3.0–3.3 V estimados

Cadena de caídas medida en el `.raw` a 0.99 mA (riel 4.80 V):

| Tramo | Caída |
|---|---|
| Cabeza de la fuente P43 (rp − msource, supuesto del modelo) | 0.500 V |
| BSS84 | 0.090 V |
| **D_blk (BAV199 de bloqueo, nuevo en S11.2)** | **0.770 V** |
| R_S 47 Ω | 0.047 V |
| FET2 + **R_LIM 700 Ω** + FET1 | 0.788 + **0.693** + 0.641 = **2.122 V** |
| **Disponible** | **1.271 V** |

- **Causa:** el rediseño (§2.3, línea 154) suponía «R del par ≤ 700 Ω» en total. El modelo tiene R_LIM 700 Ω **más dos FET** de 640–790 Ω cada uno: R_on de 700 Ω (el **máximo** de hoja, usado en todos los casos) y, en uno de ellos, V_GS −0.69 V. Eso suma ≈ 2.1 kΩ, no 700 Ω. Además, no contaba el diodo de bloqueo (0.77 V).
- **Qué lo movería:**
  - con R_on típica (320 Ω), +0.76 V → ≈ 2.0–2.3 V;
  - sin la caída del BAV199 de bloqueo, otros +0.5–0.7 V con un diodo de menor VF;
  - aun así, no llega a 3 V con R_LIM ≈ 700 Ω.
- **A 100 µA, el fallo es real pero pequeño:** 4.80 − 0.5 − ~0.09 − 0.67 (D_blk) − 0.21 (2.1 kΩ) ≈ 3.37 V. **La causa dominante es D_blk.** Con un diodo de 0.3 V pasaría con margen; la R_on típica sólo aporta +0.08 V.

### C8. GBU808 a 423.6 A frente a 100 A

- **Hoja (Diodes DS21227, p2):**
  - I_FSM 200 A, «8.3 ms single half sine wave, superimposed on rated load, non-repetitive»;
  - **I²t 166 A²s «for fusing (t = 8.3 ms)»** (= 200² × 8.3 ms / 2);
  - no hay dato por debajo de 8.3 ms.
- **Comparar el 50 % de una I_FSM de 8.3 ms con un pico de < 1 ms no es el criterio correcto.** El I_FSM es la amplitud de una semionda de 8.3 ms. Para pulsos más cortos, la capacidad de pico **sube** (a I²t constante, I_pk ∝ 1/√t). La magnitud que se coordina con un fusible es la **I²t**.
- **Por I²t:**
  - peor caso 10.93 A²s por diodo (0.5 Ω, k = 3), el **6.6 %** de 166 A²s;
  - 423.6 A con 10.9 A²s equivale a una semionda de ≈ 120 µs;
  - con un escalado prudente de la I²t a 1 ms (∝ √t, que no está en la hoja) queda ≈ 58 A²s → 50 % = 29 A²s, que también pasa.
- **Salvedad:** la hoja no garantiza nada por debajo de 8.3 ms, y el pico de 424 A es 2.1 veces la I_FSM. Es un supuesto razonable, no una garantía.
  - El modelo de fusible no limita el pico (fusible no limitador; abre a 20 µs–4 ms). El pico lo fija la red: 325 V / (0.5 Ω + 2 V_F + R_s). La I²t del fusible no lo cambia.
- **Veredicto: criterio mal puesto en el pico; por I²t, el puente pasa con holgura.**

### ESD: V_DS 2898 V, V_GS 1592 V

- **Camino (ohmios, relé cerrado):** pistola → vin → ptin → FET1 → (Cgs₁‖Cgs₂‖R_LIM entre s1 y s2) → FET2 → n1 → R_S → D2p/D2n → riel/COM.
- **Mecanismo:**
  - Nada fija ptin por debajo de 600 V, así que el FET limitador entra en avalancha. El otro conduce por el cuerpo o realzado.
  - La corriente ya no está limitada: (V_ESD − 600) / (R_ESD + R_d + R_LIM + …) ≈ 2.3–4.2 A.
  - Esa corriente cruza R_LIM, que **es** la V_GS de ambos FET (puertas cruzadas): V_GS = I·R_LIM = 2.27 A × 700 Ω = **1592 V**.
  - En el primer frente (t = 100 ns, en mi caso −4 kV), I_RLIM ≈ 0: la corriente pasa por las Cgs (40 pF). Luego las carga hasta 827 V.
- **¿Físico?** Sí, en lo cualitativo:
  - basta I_RLIM > 20 V / 700 Ω = **29 mA** para romper la puerta;
  - el pulso de drenaje es de 85 mA (p1) y el de cuerpo de 64 mA (p3);
  - la pieza es **HBM clase 0 (< 250 V)** (p1).
- **La magnitud de V_DS (1459–2898 V) es artefacto:** 600 V de avalancha + I × R_d (565–724 Ω) sin modulación ni destrucción. Los 1592 V de puerta son un número de modelo sin ruptura: la pieza real se rompe a decenas de voltios.
- **En modo tensión** (relé abierto, 2487 V por los 1 pF de Coff): la energía es pequeña (11 µJ) y el contacto abierto del relé descargaría antes.
- **Qué lo movería:** la corriente por el par tiene que bajar de amperios a ≤ 29 mA (V_GS) y ≤ 64–85 mA (pulso), unas 100 veces. Eso exige que ptin quede fijado por debajo de ≈ 480 V antes del par, y además una sujeción de V_GS ≤ 16 V en paralelo con R_LIM. Las dos cosas son piezas nuevas que el plan prohíbe aquí: **sin TVS, O2 no sobrevive a la ESD**, y esto no depende del modelo.

## 5. Resumen de fallos físicos y qué los movería

| Fallo | Número | Mecanismo | Qué lo movería |
|---|---|---|---|
| ESD sobre O2 | V_GS 827 V (4 kV) / 1592 V (8 kV) | Avalancha sin sujeción previa; I·R_LIM es la V_GS | Corriente en el par ≤ 29 mA → sujeción < 480 V antes del par + sujeción de puerta |
| C3 (4051, x1) | 432 mA frente a 10 mA | Compensación 3 × (3.3 k + 100 p) del divisor | R en serie con el pin x1 (~100 Ω) o R_c mayor; no depende de O2 |
| R_LIM | 725 Ω frente a 1125 Ω, sin solape | V_th −1.6…−2.7 e I_DSS sin máximo | R_LIM por banda de bobina (casi cierra) o un techo de corriente mayor |
| Tj a 70 °C | ≈ 126 °C (120–133) frente a 120 °C, sólo con I_DSS 21 mA | P = 325·I/π; Zth(10 s) ≈ 155 K/W más rizado | I_lim ≤ 2.25 mA a 70 °C, o cobre en la huella |
| C6 a 100 µA | 3.37 V frente a 3.5 V | D_blk 0.67 V + cabeza 0.5 V + 2.1 kΩ | Diodo de bloqueo de menor V_F (+0.4 V) |
| Span por ESD | 11.17 V frente a 11 V | 1.2 µC en 1 µF | ≥ 1.15 µF efectivos en rp |

**No son fallos físicos:** C8 por pico (debe juzgarse por I²t: pasa, con el 6.6 %), C2 en Q3/Q4 (el span cumple gracias al zéner) y C6 a 1 mA (es informativo). **C7 sigue sin evidencia.**
