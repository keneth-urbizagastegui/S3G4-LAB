# Auditoría de Claude — S3 de CH1 (buffer, escalera, 74HC4051 y ganancia con AD8039)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) de 13:36 a ~15:10.
- Entregables auditados: `ACTA_S3.md`, `RESPUESTA_FINAL_S3.md`, `ejecutar_s3.py`, `comun/ch1_comun_s3.inc`, `resultados/s3_*.csv`.
- Comprobaciones propias en `chequeo_claude/s3_*.cir`, `chequeo_claude/s3_ruido/` y `chequeo_claude/s3_e14/`.

## Veredicto

**S3 cumple en lo que depende de U103 y del 4051, con una excepción real: la diferencial de entrada de U103A en sobrecarga grande a 5 mV/div.**

- Los fallos de C4 (ruido) y C6 (recuperación) que da el acta **no son de la cadena de ganancia**:
  - C4 viene del modelo de LTspice del AD8039, que da el doble de ruido que su hoja;
  - C6 es la recuperación de la red de entrada cuando conducen los BAV199.
- El fallo de C7 por la tensión de entrada del OPA810 tampoco cuenta: con el criterio acordado en S2b (corriente ≤ 10 mA), pasa.
- Mi prueba adicional encuentra **un fallo que E14 no podía ver**: la diferencial de U103A supera los ±4 V de la hoja (4.10 V) con ≥ 4.9 V en la BNC a 5 mV/div. Hace falta decidir una protección.

## 1. Reproducibilidad

- Copia en ruta corta (`…\Temp\claude\s3a`) con `S3G4_MODELS`: código 0, 245 simulaciones, 860 s.
- **Los 14 CSV son idénticos byte a byte** a los entregados. Coincide con la verificación propia de Codex (`resultados/s3_reproducibilidad.json`).
- El circuito sigue el plan:
  - `FRONT_S2B` sin cambios;
  - tomas calculadas desde los valores (1 / 0.4998 / 0.2503 / 0.0999 / 0.0499 / 0.0250);
  - red de 249 Ω;
  - 8 instancias de `SWI1` con control activo a nivel bajo;
  - nodos del AD8038 en el orden IN+ IN− V+ V− OUT.

## 2. Criterios

| # | Acta de Codex | Auditoría | Motivo |
|---|---|---|---|
| S3-C1 pérdida a 2 MHz ≤ 0.5 dB | 0.022 dB, pasa | **Pasa** | — |
| S3-C2 pico ≤ 0.5 dB, sobreimpulso ≤ 5 % | 0 dB, 0.0002 %, pasa | **Pasa** | La red de 249 Ω quitó el pico de +3.7 dB |
| S3-C3 error de ganancia (informado) | −0.95 % | **Informado** | Uniforme en las 12 escalas; es la ganancia finita en lazo abierto del AD8039 (aislado: ×4.9997 frente a 5.016 y ×10.012 frente a 10.076). Lo corrige la calibración (P10) |
| S3-C4 ruido ≤ 0.45 % | 0.59–0.64 %, falla | **Pasa: 0.30–0.40 %** | §3: el modelo da 16 nV/√Hz frente a 8 de la hoja |
| S3-C5 THD ≤ 1 %, slew | 0.007 %, pasa | **Pasa** | — |
| S3-C6 recuperación ≤ 1 µs | 551 µs en 200 mV/div, falla | **Pasa la recuperación de los amplificadores** (20–38 ns en todos los casos sin conducción de los BAV199) | §4: los 551 µs son de la red de entrada |
| S3-C7 entradas dentro de límites | Falla por tensión del OPA810 | **Pasa en E14**, pero **falla fuera de E14** | OPA810: 0.92 V por encima del riel con 2.19 mA ≤ 10 mA (criterio S2b). U103A: §5 |
| S3-C8 asentamiento ≤ 10 µs | 0.09 µs, pasa | **Asentamiento plausible; glitch no concluyente** | §6 |
| Consumo | OPA810 1.90 mA; AD8039 1.04 mA por amplificador | **Correcto** | Coincide con la hoja (1.0 mA típ.) |

## 3. Ruido: el modelo del AD8039 da el doble que su hoja

- Seguidor con el modelo `AD8038` de LTspice: **16.1 nV/√Hz de 10 kHz a 1 MHz**. La hoja (p. 3) da 8 nV/√Hz a 100 kHz. Codex lo detectó (16.18 nV/√Hz) y no lo corrigió, como mandaba el encargo.
- Copia de auditoría `chequeo_claude/s3_ruido/AD8038_en4.sub` (sólo cambia `en=8n` → `en=4n` en el OTA; el original no se toca). Como seguidor da **8.04 nV/√Hz a 100 kHz**.
- Repetí los 12 decks de E12 de Codex con esa copia, integrando con `.meas INTEG` de 1 Hz a 3.15 MHz. Control: el deck de 5 mV/div con el modelo original da 32.2 µV = **0.644 %**, igual que el acta.

| Escala | 5 mV | 10 mV | 20 mV | 50 mV | 100 mV | 200 mV |
|---|---|---|---|---|---|---|
| µV rms | 19.8 | 33.7 | 63.1 | 154 | 305 | 608 |
| % de división | **0.396** | 0.337 | 0.316 | 0.307 | 0.305 | 0.304 |

| Escala | 0.5 V | 1 V | 2 V | 5 V | 10 V | 20 V |
|---|---|---|---|---|---|---|
| mV rms | 1.97 | 3.36 | 6.31 | 15.4 | 30.5 | 60.8 |
| % de división | **0.395** | 0.336 | 0.315 | 0.307 | 0.305 | 0.304 |

Coincide con la estimación previa (≈ 0.40 %). **C4 pasa en las 12 escalas.** Hasta 10 MHz, sin criterio: 0.70 % a 5 mV/div.

## 4. Recuperación de 551 µs en 200 mV/div: es la red de entrada

- Con ±8 V (10 × FS) en la rama ×1, los BAV199 conducen y la entrada de U101 se queda en 5.92 V.
- Durante el pulso, C_S (1.5 nF) se carga con la diferencia. Al soltar, la entrada de U101 salta a −2.36 V y se descarga a través de ~100 kΩ (τ ≈ 150 µs). Hasta ±0.1 div son unos 550 µs.
- En las otras 22 combinaciones de escala y polaridad (sin conducción de los BAV199), la recuperación es de 20–38 ns.
- **Error del plan:** E14 pedía ≤ 1 µs pensando en la saturación de los amplificadores, pero 10 × FS en 200 mV/div ya hace conducir la protección.
- Propuesta (decide Keneth): mantener ≤ 1 µs para la saturación de los amplificadores y **documentar ≈ 0.6 ms** como recuperación tras conducir las sujeciones de la rama ×1. Esto sólo ocurre en ×1 por encima de ±5.6 V; el firmware puede pasar a ÷100 al detectar saturación.

## 5. Diferencial de U103A: el hallazgo que E14 no podía ver

- Por diseño, 10 × FS deja siempre ≈ 0.2 V en la entrada de U103A, en cualquier escala. Por eso E14 sólo midió 0.06 V de diferencial. Otro error de mi plan: la prueba no llegaba al caso que quería vigilar.
- Prueba propia (`chequeo_claude/s3_e14/sobrecarga_5mV_dc.cir`): barrido en continua de la BNC de −40 a +40 V en 5 mV/div (×1, toma 1), con el deck de Codex:
  - salida de U101 limitada a **±4.88 V** por los BAV199 y R_PROT;
  - U103A con IN+ = 4.88 V e IN− = 0.78 V: **diferencial de 4.10 V**, por encima de los ±4 V de la hoja (p. 5, máximo absoluto);
  - la supera desde **|V_BNC| ≥ 4.92 V**;
  - U103B: 3.53 V, dentro.
- Sólo afecta a 5 mV/div: en las demás escalas la toma o el ÷100 reducen la entrada. Pero es un caso normal de uso, porque basta conectar una señal de 5 V con la escala más sensible.
- El exceso es pequeño (0.1 V) y depende de la excursión real del OPA810 y del AD8039, pero es un máximo absoluto. **No se debe aceptar sin margen.**
- El modelo no tiene diodos entre entradas, así que una protección habrá que simularla explícitamente.

Opciones para Keneth (no decididas):
- **(a) Resistencia en serie en IN+ de U103A (470 Ω–1 kΩ) y un par de Schottky en antiparalelo entre las entradas** (BAT54S o similar). Limita la diferencial a ≈ 0.4 V con ≈ 3–7 mA. Añade 2.8–4 nV/√Hz en la entrada de U103A (ruido ≈ 0.42–0.45 %) y la capacidad del diodo. Es lo habitual.
- **(b) Bajar la tensión que llega a U103A:** sujeción a ±3.3 V en el común del 4051, con resistencia serie. Mismos costes de ruido y corriente que (a), pero sin depender de la diferencial interna.
- **(c) Aceptar y vigilar por firmware:** al detectar saturación en 5 mV/div, cambiar de escala. No protege durante el tiempo de reacción.

Recomiendo (a), con una simulación corta (S3b) que mida el ruido y la corriente.

## 6. E15 y el modelo del 4051

- `SWI1` de Nexperia no converge al conmutar con control de 30 ns (Codex lo diagnosticó con un deck aislado). Como permitía el plan, E15 usó un interruptor comportamental de 100 Ω con las capacidades de la hoja (Y 5 pF, Z 25 pF), **sin inyección de carga**.
- El asentamiento (0.09 µs) es plausible: la constante de tiempo es de decenas de ns. Pero el glitch de 5·10⁻⁶ div no significa nada sin inyección de carga. **C8: el asentamiento pasa y el glitch queda pendiente** de medir en placa, o con un modelo que converja.
- Codex señala bien que los 30 ns / 20 ns del plan no figuran así en la hoja. Son valores míos de partida. No cambian el resultado.

## 7. Lo que hizo bien Codex

- No tocó modelos ni entregables anteriores (comprobación SHA256 de 20 562 ficheros).
- Detectó y documentó la discrepancia de ruido del modelo y la no convergencia de `SWI1`.
- Anotó, sin resolverla, la contradicción del criterio de tensión del OPA810 frente al de S2b.

## 8. Pendientes

1. **Keneth:** protección de la diferencial de U103A, opción (a), (b) o (c).
2. **Keneth:** aceptar que tras conducir los BAV199 en ×1 la recuperación es de ≈ 0.6 ms (§4).
3. Actualizar el documento vivo:
   - C.5 con 0.30–0.40 %;
   - C.6 con U103 = AD8039 y la red de 249 Ω;
   - y la protección elegida.
4. Siguiente etapa: S4 (etapa final a 3.3 V con offset).
