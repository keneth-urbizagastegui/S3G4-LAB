# Auditoría de Claude — S3b de CH1 (protección de la diferencial de U103A)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) desde las 16:01: código 0, 162 simulaciones, y su reejecución en ruta corta dio 10/10 CSV idénticos.
- Comprobaciones propias en `chequeo_claude/s3b/`. Son los decks de Codex con una sola sustitución y medidas añadidas.

## Veredicto

**Ninguna de las cuatro variantes del plan pasa todo, pero el diodo BAV99 sí:**

- **BAT54S (A, B): descartado.** Sus 12 pF entre las entradas crean un camino de realimentación positiva. U103A sola tiene +8.4 dB de pico y la cadena completa +6.4 a +6.9 dB.
- **BAV199 (C, D): casi.** Protege bien y la cadena completa no tiene pico. Pero:
  - es un diodo lento (TT = 1.02 µs en el modelo de Nexperia): la recuperación de ±4.5 V tarda 1.07–1.16 µs, por encima de 1 µs;
  - U103A sola tiene +2.2 dB de pico hacia 29–38 MHz. En la cadena no se ve porque U103B corta en ~32 MHz, pero indica poco margen de estabilidad en U103A.
- **BAV99 (variantes E y F, añadidas por Claude): pasan todo lo medido.** Es el mismo par en serie en SOT-23, pero rápido (4 ns) y con 0.64 pF. LCSC **C2500**, Nexperia BAV99,215, pieza *basic*, más de 1.1 millones en stock, 0.012 USD.

## 1. Lo que confirmo de Codex

- La variante C de control, reejecutada por mí, da lo mismo que su acta: diferencial de 0.844 V; recuperación de 1.07–1.10 µs frente a 1.108 µs (yo mido desde el final del flanco de bajada, 10 ns después). B0: +2.26 dB a 38 MHz.
- Los diodos están bien orientados (uno en cada sentido entre IN+ e IN−) y R_SER va entre `COMMON` e IN+.
- El ruido usa el modelo corregido; los controles dan 0.644 % y 0.396 %, como se pedía.
- El pico de 0 dB de C y D en B1 frente a +2.2 dB en B0 no es un error de medida. Lo comprobé hasta 1 GHz: en la cadena, U103B tapa el pico de U103A.

## 2. BAV99 (modelo `BAV99HY` de Rohm, `standard.dio` de LTspice)

E = 470 Ω + BAV99; F = 1 kΩ + BAV99. Mismos circuitos que C y D, cambiando sólo el diodo.

| Medida | Criterio | E (470 Ω) | F (1 kΩ) | C (BAV199, control) |
|---|---|---|---|---|
| B0: pico de U103A sola | ≤ 0.5 dB | **+0.33 dB** (35 MHz) | **+0.26 dB** (26 MHz) | +2.26 dB |
| B1: pico de la cadena (5 mV y 0.5 V/div, hasta 1 GHz) | ≤ 0.5 dB | 0 dB | 0 dB | 0 dB |
| B1: pérdida a 2 MHz | ≤ 0.5 dB | 0.020–0.022 dB | 0.019–0.022 dB | 0.012–0.014 dB |
| B2: ruido a 5 mV/div | ≤ 0.45 % | **0.409 %** | 0.423 % | 0.409 % |
| B2: ruido a 0.5 V/div | ≤ 0.45 % | **0.407 %** | 0.422 % | 0.408 % |
| B3: diferencial de U103A (±40 V) | ≤ 2 V | **0.69 V** | 0.66 V | 0.84 V |
| B3: diferencial de U103B | ≤ 4 V | 3.56 V | 3.55 V | 3.56 V |
| B3: corriente por el 4051 | ≤ 12.5 mA | 4.4 mA | 2.6 mA | 4.2 mA |
| B3: corriente del OPA810 | informar | 9.3 mA | 7.5 mA | 9.1 mA |
| B4: recuperación de ±2 y ±4.5 V | ≤ 1 µs | **42–50 ns** | 47–55 ns | 1.07–1.10 µs |

No repetí B5 (THD) ni B6 (offset) con el BAV99. Con señal normal, los diodos tienen casi 0 V entre sus terminales: ni distorsionan ni fugan apreciablemente. A 0 V de polarización, la fuga es del orden de pA; la hoja da 0.5 µA a 80 V. Lo confirma la integración S7.

## 3. Recomendación

**Variante E: R_SER = 470 Ω y BAV99 (C2500).**
- Frente a F tiene menos ruido (0.41 % frente a 0.42 %) y más ancho de banda en U103A. Sus corrientes en sobrecarga (4.4 mA en el 4051 y 9.3 mA en el OPA810) siguen muy por debajo de los límites.
- F sólo es mejor en corriente, y no hace falta.

## 4. Lo que queda abierto

- **U103B: 3.56 V de diferencial frente a ±4 V**, con un 11 % de margen. Depende de la excursión real de la salida de U103A. Opciones: aceptarlo, o poner la misma protección en U103B (+1 resistencia y +1 BAV99, con algo más de ruido). **Lo decide Keneth.**
- El AD8038 de LTspice no modela la corriente de polarización real (400 nA) ni la deriva. La resistencia de 470 Ω añade ≈ 0.19 mV de offset en la entrada de U103A, unos 0.04 div a la salida. Lo absorbe el autocero (P3).

## 5. Decisión de Keneth y comprobación de U103B (3 oct, tarde)

Keneth confirma la variante E en U103A y pide **la misma protección en U103B**: 470 Ω entre la salida de U103A y IN+ de U103B, y un BAV99 en antiparalelo entre sus entradas. Lo comprobé con la variante G (`chequeo_claude/s3b/y_*.cir`, igual que E más la protección de U103B):

| Medida | Criterio | G (U103A y U103B protegidos) |
|---|---|---|
| ×10 aislada: pico | ≤ 0.5 dB | 0 dB |
| Cadena: pico hasta 1 GHz (5 mV y 0.5 V/div) | ≤ 0.5 dB | 0 dB |
| Cadena: pérdida a 2 MHz | ≤ 0.5 dB | 0.013–0.015 dB |
| Ruido a 5 mV/div y 0.5 V/div | ≤ 0.45 % | 0.409 % y 0.408 % |
| Diferencial de U103A / U103B (±40 V) | ≤ 2 V | 0.69 V / **0.68 V** (antes 3.56 V) |
| Corriente por el 4051 / OPA810 | ≤ 12.5 mA / informar | 4.4 mA / 9.3 mA |
| Recuperación de ±2 y ±4.5 V | ≤ 1 µs | 41–49 ns |

**Configuración final de la cadena de ganancia de CH1:** U103A y U103B = AD8039, cada uno con 470 Ω en serie en IN+ y un BAV99 (C2500) en antiparalelo entre IN+ e IN−. Redes 1.00 k / 249 Ω y 2.26 k / 249 Ω. Sin repetir: THD y offset con BAV99 (se miden en S7).
