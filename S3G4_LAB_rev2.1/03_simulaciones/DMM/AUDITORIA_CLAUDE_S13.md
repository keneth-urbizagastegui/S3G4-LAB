# Auditoría Claude — S13 (bloque 3: ohmios, diodo y continuidad)

8 oct 2026 · Claude (auditoría corta, esfuerzo medio) · Objeto: ACTA_S13.md, ejecutar_s13.py, analizar_s13.py y resultados/s13_*. Criterio de Keneth (DECISIONS, 8 oct): que funcione con margen; los fallos marginales se clasifican y no se persiguen.

No se modificó ningún archivo de Codex, ni STATE, DECISIONS, modelos u hojas. No se descargó nada. Scripts en `chequeo_claude/s13/`.

## 1. Reproducción del smoke

Copia en `C:\s13\a\b\DMM` (la profundidad hace falta porque `ejecutar_s11_2.py` usa `HERE.parents[2]`) con `S3G4_MODELS` apuntando a los modelos del proyecto. `--smoke`: 10/10 casos correctos en 171 s (Codex: 182 s).

`comparar_smoke.py`: 852 valores numéricos y **diferencia relativa máxima 0**. Los resultados son idénticos a los de Codex, salvo los tiempos de ejecución.

## 2. Comprobación desde el .raw (`verificar_raw_s13.py`)

| Caso | Recalculado desde el .raw | Codex | Coincide |
|---|---|---|---|
| C2 0040 (2 kΩ, 1 mA, el peor) | I0 = 1.0121 mA (+0.80 %); compliancia calibrada 2.29 V; V_x 2.024 V; margen **0.266 V** | 0.266 V (resumen calibrado) | Sí |
| C3 0431 (900 pF, 40 Ω) | cierre 30.558 µs; apertura 0.227 µs; 2 transiciones de COMP; PB14 0.202 V con el corto y 2.44 V abierto | 30.558 µs / 0.227 µs / 2 | Sí |
| C1 0376 (60 Vrms, el peor R1) | Vin ±84.85 V (59.99 Vrms); R1 0.4837 W por pieza (0.4835 W en los últimos 5 ciclos); pico 23.38 V; N1 14.71 V; BAT54 14.59 V inversos | 0.4837 W / 23.38 V / 14.589 V | Sí |

La potencia de R1 se promedia sobre todo el transitorio, no sólo sobre la ventana de 5 ciclos que menciona el acta. La diferencia es de 0.0002 W y no tiene importancia. Las tres piezas de 510 Ω trabajan al 24 % de 2 W.

## 3. C2: compliancia «97/100»

**Las dos cifras de 97/100 del acta cuentan los mismos tres fallos.** El `margin_V` de la campaña, que da el 97 de `s13_summary.json`, exige el 99 % de la corriente **nominal**. Las placas 0012, 0033 y 0036 nunca la alcanzan porque su error inicial es de −1.05 %, −1.19 % y −1.14 %. Su compliancia sale 0 y su margen −2.0 V. No es una pérdida de regulación sino el mismo error inicial contado dos veces.

Con el criterio correcto (`s13_compliance_summary.csv`, que usa la corriente propia de cada placa), los fallos son otras tres placas:

| Placa | Margen | Falta para 0.3 V | Riel | Vos A / B |
|---|---|---|---|---|
| 0040 | 0.266 V | 34 mV | 4.81 V | −3.8 / +4.2 mV |
| 0044 | 0.295 V | 4 mV | 4.84 V | +3.7 / +3.0 mV |
| 0083 | 0.296 V | 4 mV | 4.81 V | −4.4 / +1.5 mV |

**Causa** (`regresion_c2.py`, R² = 0.998): un riel cerca de 4.8 V, un Vos alto y la Ron del mux de fuerza. **El modelo de SWI1 añade 117.4–117.8 Ω a todas las placas** por encima de la Ron muestreada, lo que cuesta 118 mV de margen. Con la Ron que pretendía el Monte Carlo, el margen mínimo sería **0.384 V y no fallaría ninguna placa**.

**Error inicial ±1 %:** lo explica casi por completo el Vos del TLV2372 (R² = 1.000; el Vos de B pesa 0.48 % σ). Es error de ganancia de V_set, que el §3.3 del estudio ya prevé calibrar por rango.

**Dictamen:** son márgenes de criterio, no fallos funcionales. Cada criterio pasa por separado 97/100 (≥ 95 %). La unión de ambos da 94/100 placas «limpias», pero los 3 errores iniciales desaparecen con la calibración y las 3 compliancias se deben a 4–34 mV sobre un margen de diseño de 0.3 V. Además, ese margen está penalizado por el modelo. Una placa con 0.27 V de margen sigue midiendo 2 kΩ a fondo de escala.

## 4. C5: fugas a 1 nA

La tolerancia que se reparte a la fuga es el 25 % de lo que sobra tras la ganancia: 350 ppm en 2 MΩ y 2350 ppm en 20 MΩ. Los datos de `s13_leak_summary.csv`, en términos de **error en la lectura de ohmios** (deriva de 18 a 28 °C después de calibrar a 23 °C) y comparados con la tolerancia total del rango, son estos:

| Fuga a 23 °C (fuerza + borne) | 2 MΩ (tolerancia ≈ 0.2 %) | 20 MΩ (tolerancia ≈ 1 %) |
|---|---|---|
| 0.1 + 0.1 nA | 0.008 % | 0.085 % |
| 1 + 0.1 nA | 0.046 % (109 % del reparto) | 0.47 % |
| 1 + 1 nA | 0.084 % (199 %) | 0.85 % |
| 10 nA en una rama | 0.43–0.85 % | 4.3–8.6 % |

- **1 nA en una rama: marginal de criterio, de acuerdo con Codex.** Supera el reparto del 25 %, pero queda muy por dentro de la tolerancia total del rango.
- **1 + 1 nA: límite en 20 MΩ.** Consume el 85 % de la tolerancia por la inversión del divisor de 10.01 MΩ. Sigue siendo de criterio, pero sin holgura.
- **10 nA: fallo real**, que coincide con lo que dice Codex.

**Condición para el prototipo:** medir la fuga total del nodo de fuerza más el borne a 23 °C y a unos 28 °C. Una forma de hacerlo es leer una resistencia patrón de 1.5–2 MΩ y otra de unos 15 MΩ mientras se calienta la placa. Se acepta si la fuga total es ≤ 1 nA, o si la deriva de la lectura es ≤ 0.1 % en 2 MΩ y ≤ 0.5 % en 20 MΩ. Con más de unos 2 nA, o si la fuga de fuerza supera 0.8 nA (criterio que ya fija el estudio), se aplica el plan B ya previsto (TMUX1208). No hace falta cambiar nada antes.

## 5. «SWI1 dio una Ron superior a la del estudio»

**Afecta a la compliancia, no a la exactitud.**

- **Compliancia:** el mux de fuerza está en el camino de la corriente. Los 118 Ω de más restan 118 mV a 1 mA y son la única razón de los 3 fallos calibrados (§3). En 20 kΩ–20 MΩ la caída es de 12 mV o menos y no importa.
- **Exactitud:** la Ron queda dentro del lazo, porque la corriente se fija con V_set sobre R_k. La regresión le da un peso de 0.000 % en el error inicial. La lectura usa el mux de sentido, que trabaja a alta impedancia.

En consecuencia, la penalización del modelo va en el sentido pesimista. La Ron de hoja del 74HCT4051 cerca del riel tampoco es de 60 Ω, así que la cifra real hay que medirla.

## 6. Veredicto

**El bloque 3 se cierra en simulación**, con fallos sólo de criterio o de modelo. Los criterios C1 en continua, C2, C3, C4, C6 y el diodo se cumplen. C5 y el pulso de C1 quedan condicionados a medidas y ratings, como el acta ya declara.

Matiz al acta: el «97/100 de compliancia» de la tabla debería describirse como los 3 errores iniciales, porque así se calcula el 97 de `s13_summary.json`. La cifra de compliancia calibrada es otro 97/100, debido al modelo de Ron.

**Condiciones para el prototipo** (medir, no rediseñar):

1. **Compliancia a 1 mA:** con 2 kΩ en el borne y el riel en su mínimo real, la corriente se mantiene ≥ 99 % hasta V_borne ≥ V_x + 0.25 V (unos 2.27 V). Medir de paso la Ron real del 4051 de fuerza.
2. **Calibración de corriente por rango:** el error inicial tras calibrar debe ser ≤ 0.1 %. Antes de calibrar se espera hasta ±1.2 %, por el Vos.
3. **Fugas:** total ≤ 1 nA a 23 °C, o deriva de la lectura entre 23 y 28 °C ≤ 0.1 % en 2 MΩ y ≤ 0.5 % en 20 MΩ. Si no se cumple, plan B (TMUX1208).
4. **Pendientes que Codex ya señala y siguen abiertos:** P41 (umbral de continuidad ≤ 7.6 mV de residuo); curva de impulso del HoCR2512 de 510 Ω y del GDT; Vth del BSS138; secuencia EN/INH; deriva de 399 ppm en peor caso lineal frente a 300 ppm (un problema de método RSS frente a lineal, que no se persigue).
