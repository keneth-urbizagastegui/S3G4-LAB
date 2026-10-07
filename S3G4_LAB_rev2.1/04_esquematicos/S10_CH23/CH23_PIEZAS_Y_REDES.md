# CH2 y CH3 — piezas y redes para el esquema (S10)

- Autor: Claude Code, 6 oct 2026. Fuente de verdad para dibujar CH2 y CH3 en KiCad.
- **CH2 y CH3 son CH1 con el filtro a 1 MHz.** Todo lo demás es idéntico: entrada, ÷100, relé, sujeción, acoplo, OPA810, escalera, 74HC4051, ganancia ×50 con AD8039, OPA836, VMID, red del pin, desacoplo, pull-ups y driver del relé. Fuentes:
  - `ai-context/DECISIONS.md`, entradas del 4 oct (S9) y del 6 oct (AD8039 en CH2/CH3);
  - `03_simulaciones/CH23_entrada/ACTA_S9.md` y `RESPUESTA_FINAL_S9_B.md` (filtro E96 común: RFILT1 = 2370 Ω y RFILT2 = 1100 Ω, con los condensadores de CH1);
  - la tabla de CH1, `../S8_CH1/CH1_PIEZAS_Y_REDES.md`, y su hoja verificada (S8b, `verificar_s8.py` con código 0).
- Por eso esta tabla **no repite** las 89 piezas: da las reglas para pasar de CH1 a CH2/CH3 y los cambios. `verificar_ch23.py` aplica las mismas reglas a la netlist de CH1 (`../S8_CH1/s8_ch1.net`) y compara.

## 1. Organización (Keneth, 6 oct)

- **Una hoja por canal:** `ch2.kicad_sch` y `ch3.kicad_sch`, colgadas de la raíz `s3g4.kicad_sch` como hojas jerárquicas con nombre `CH2` y `CH3`. CH1 sigue dibujado en la raíz; se moverá a su propia hoja cuando se arme la jerarquía completa.
- Las hojas **no llevan pines jerárquicos**: todo lo que entra o sale va por etiquetas globales o símbolos `power:`, como en CH1.
- **Referencias por centenas:** CH2 = 2xx y CH3 = 3xx (CH1 = 1xx). Los relés quedan K101, K201 y K301; DECISIONS los llamaba K101…K103.

## 2. Reglas de copia

| De CH1 | A CH2 | A CH3 |
|---|---|---|
| Referencia `X1nn` (R123, K101, U105…) | `X2nn` (R223, K201, U205…) | `X3nn` |
| Red local `CH1_*` (CH1_TAP, CH1_F1_MID…) | `CH2_*` | `CH3_*` |
| Etiqueta global `CH1_ADC`, `CH1_OFFSET_DAC`, `CH1_SENSEL_A/B/C`, `CH1_K_CTRL`, `CH1_CPL_A/B` | `CH2_…` | `CH3_…` |
| Rieles y masas: `+AFE_4V9`, `-AFE_4V9`, `VDDA`, `VREF_2V5`, `+3V3`, `AGND`, `GND` | iguales (compartidos) | iguales |
| `RELAY_COM` (nodo común de las bobinas) | igual (compartido) | igual |
| Símbolo, huella, campo `LCSC`, `MPN` y `Nota` de cada pieza | iguales | iguales |

## 3. Cambios: filtro anti-alias a 1 MHz (U205/U305)

Mismos condensadores que CH1 (C109 56 pF, C110 47 pF, C111 220 pF, C112 56 pF). Cambian las resistencias, con piezas *basic* de JLCPCB (0603 1 %):

| CH1 | Valor en CH1 | CH2 / CH3 | Valor nuevo | LCSC | Red (sin cambios) |
|---|---|---|---|---|---|
| R123 + R148 | 1.1 kΩ + 10 Ω (1.11 kΩ) | R223 + R248 / R323 + R348 | **2.2 kΩ + 150 Ω (2.35 kΩ)** | C4190 + C22808 | `G2_OUT` – `F1_A` – `F1_MID` |
| R124 + R149 | 1.1 kΩ + 10 Ω | R224 + R249 / R324 + R349 | **2.2 kΩ + 150 Ω** | C4190 + C22808 | `F1_MID` – `F1_B` – `F1_INP` |
| R125 ∥ R138 | 1 kΩ ∥ 1 kΩ (499 Ω) | R225 / R325 | **1.1 kΩ**, una sola pieza | C22764 | `F1_OUT` – `F2_MID` |
| R126 ∥ R139 | 1 kΩ ∥ 1 kΩ | R226 / R326 | **1.1 kΩ**, una sola pieza | C22764 | `F2_MID` – `F2_INP` |
| R138, R139 | — | **no existen** (R238, R239, R338 y R339 no se dibujan) | | | |

- **RFILT1 = 2.35 kΩ frente a 2.37 kΩ simulado (−0.84 %).** El 2.37 kΩ y el 180 Ω no son *basic* (pcbparts, 6 oct). El error es mayor que el ≤ 0.35 % de las parejas de CH1, pero el −3 dB solo sube ≈ 0.8 % (de 1.001 a ≈ 1.01 MHz con la AD8039, K1 de S9), dentro del 1 MHz ± 10 % de S9-C1 y del ±1 % del Monte Carlo. **No se vuelve a simular.**
- RFILT2 = 1.1 kΩ es exacto: no hace falta pareja.
- **Cuenta por canal: 87 piezas** (89 de CH1 menos R_38 y R_39).

## 4. Textos de la hoja

- Rótulos de bloque como en CH1, con las referencias renumeradas. Bloque 7: «Filtro anti-alias U205 a 1 MHz (dos Sallen-Key)». Bloque 8: «Etapa final U206, VMID y red del pin (CH2_ADC → ADC3, pin por fijar)»; en CH3, U306 y ADC4.
- Nota «ABIERTO», además de las de CH1 que siguen vigentes:
  - **Pin del ADC** (ADC3 para CH2 y ADC4 para CH3, D-02) y **canal del DAC de offset**: se fijan en el mapa de pines (PLAN, paso 8).
  - **Disparo de CH2/CH3** (PE9/PE15 no llegan a ningún comparador): fuera de esta hoja, mapa de pines.
- Cajetín: título «CH2 — canal lento (AFE rev 2.1)» / «CH3 — canal lento (AFE rev 2.1)», empresa «S3G4 LAB», revisión «S10», comentario «Fuente: S10_CH23/CH23_PIEZAS_Y_REDES.md». Si Konnect no puede, lo rellena Keneth en KiCad, como en S8b.
