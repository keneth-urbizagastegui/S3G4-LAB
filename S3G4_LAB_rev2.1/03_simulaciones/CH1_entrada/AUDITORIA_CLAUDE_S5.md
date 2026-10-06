# Auditoría de Claude — S5 de CH1 (filtro anti-alias, U105 = AD8039 doble)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) desde las 19:00: código 0, 708 simulaciones, y su reproducción dio 13/13 CSV idénticos.
- **Mi reejecución** en `…\Temp\claude\s5a` con `S3G4_MODELS`: código 0, 708 simulaciones, 578 s, **13/13 CSV idénticos byte a byte**.
- Comprobaciones propias en `chequeo_claude/s5/`.

## Veredicto

Los tres candidatos funcionan en lo esencial: −3 dB dentro de 2.0 MHz ± 10 %, sin pico, sin rebote hasta 200 MHz, THD y ruido correctos. Sus pegas:

| | BE (Bessel) | TR (intermedio) | BU (Butterworth) |
|---|---|---|---|
| Atenuación a 4.5 MHz | 17.5 dB | 22.6 dB | 30.9 dB |
| Sobreimpulso con cuadrada | 0.0 % | 3.2 % | 8.8 % |
| Fallos | Monte Carlo: sólo 67.5 % dentro de ±10 % (S5-C2) | ninguno | recuperación de 1.08 µs (S5-C8, > 1 µs) |

**Recomendación: TR, con las resistencias reescaladas (§2).** Es el único que pasa todo, y queda a mitad de camino entre rechazo de alias y forma de onda.

## 1. Por qué los tres cortan por debajo de 2.0 MHz

| | −3 dB ideal con mis valores sin redondear | Ideal con los valores E de Codex | Cadena simulada |
|---|---|---|---|
| BE | 2.00 MHz | 1.89 MHz | 1.82 MHz |
| TR | 2.00 MHz | 2.07 MHz | 1.95 MHz |
| BU | 2.00 MHz | 2.02 MHz | 1.92 MHz |

- **Redondeo:** en BE, la sección 1 quedó con C1 = C2 = 82 pF, es decir Q = 0.500 en vez de 0.522. Por eso cae a 1.89 MHz ya en el cálculo ideal.
- **Cadena real:** los tres pierden otro 4–6 % frente al cálculo ideal. Lo explican el macromodelo del AD8039 en Sallen-Key, el 1 pF de pista en cada entrada y la carga ficticia 1 kΩ ∥ 10 pF en la salida de U103B, que viene de S3 (§3).
- En BE, el corte nominal en 1.82 MHz deja poco margen al −10 %. Por eso falla el Monte Carlo.

## 2. Reescalado (comprobación de Claude con los decks de G1 de Codex, 5 mV/div)

| Candidato | R1 / R2 | −3 dB | A 4.5 MHz |
|---|---|---|---|
| TR original | 1150 / 511 Ω | 1.954 MHz | 22.6 dB |
| **TR reescalado** | **1.11 kΩ / 499 Ω** (E96) | **2.011 MHz** | **21.7 dB** |
| BE reescalado | 523 / 511 Ω | 2.008 MHz | 14.7 dB |

Con TR reescalado, los condensadores no cambian (sección 1: 56 / 47 pF; sección 2: 220 / 56 pF) y no aparece pico. Falta repetir con él el Monte Carlo, el escalón y la recuperación. Lo hará S7 (integración), salvo que Keneth prefiera un S5b corto.

## 3. Hallazgo heredado: la carga ficticia de U103B

`ch1_comun_s3.inc` puso en la salida de U103B una carga de 1 kΩ ∥ 10 pF, como sustituto de S4 mientras S4 no existía. Siguió en S4 y S5, aunque ahora la carga real es la primera sección del filtro. Su efecto es pequeño (parte de la pérdida del §1), pero **en S7 hay que quitarla**. Codex la anotó como duda.

## 4. Lo demás que comprobé

- Síntesis: los f0 y Q de Codex coinciden con mi tabla del plan, salvo el redondeo de BE.
- S5-C4 (rebote): ningún candidato vuelve a subir por encima de \|H(4.5 MHz)\| hasta 200 MHz con el modelo real del AD8039.
- Codex escribió su diario desde el principio, como se pidió.

## 5. Para Keneth

1. Elegir candidato. Recomendado: **TR reescalado (1.11 kΩ / 499 Ω)**.
2. Verificación del reescalado: un S5b corto o dejarlo para S7.
