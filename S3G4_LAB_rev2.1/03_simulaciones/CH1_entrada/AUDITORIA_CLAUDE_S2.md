# Auditoría de Claude — S2, protección y abusos de la entrada P4b de CH1

- Fecha: 2026-10-03.
- Auditor: Claude Code (Opus 5.5).
- Objeto: trabajo de Codex (CLI 0.160.0, `gpt-6.1-sol`, `medium`, sesión `01a10080-663f-7c31-965a-c27fc44ed3d0`). Entregó `comun/ch1_comun_s2.inc`, `S2/`, `ejecutar_s2.py` (paralelo), `ACTA_S2.md`, 12 CSV y su diario.
- Contrato: `PLAN_SIMULACION_S2.md` §8.

## Veredicto

1. **Reproducible.** Mi reejecución sale con código 0, 119 simulaciones sin errores, en 54 s, y **los 12 CSV son idénticos byte a byte**. Mis dos primeros intentos fallaron por mi entorno, no por el entregable:
   - el script busca los modelos en `../../../Simulation_LTSpice/models`, que en una copia hay que reproducir;
   - la ruta del scratchpad supera los 260 caracteres de Windows y LTspice no puede abrir su `.db`.
2. **Modelos bien conectados:** el envoltorio del OPA810 respeta su orden `IN+ IN- OUT VCC VEE` y el del AD8065 el suyo; el BAV199 es el de Nexperia, sin el `.ENDS` suelto. Los rieles no absorben corriente y llevan las cargas de G.3.
3. **De los cuatro fallos con OPA810, dos son reales y baratos de arreglar, uno es mi plan y otro depende de cómo se mida la ESD:**

| Criterio | Medido | Causa | Juicio |
|---|---|---|---|
| C1 ΔCin 2.84 pF | Codex mantuvo la CIN_BUF de 5 pF del contrato **y** la capacidad propia del macromodelo (lo dice el include) | **Plan (mío):** no dije que el modelo real sustituye a CIN_BUF; la capacidad se cuenta dos veces | No es del diseño. Además C_EQ se selecciona en prueba. En S2b: CIN_BUF = 0 con modelo real |
| C2 R_EQ 99 V; C_S 94 V | En ÷100, X1 queda a 100 V · 10 M/10.1 M = 99 V sobre R_EQ y C_EQ. En ×1, C_S ve 94 V | **Real** | R_EQ en **1206** (200 V → 49.5 %) o 2 × 4.99 MΩ en 0805. **C_EQ y C_S ≥ 200 V** (C0G de 250 V en 0805/1206) |
| C3 entrada 1.69 V sobre el riel | Sólo durante la **ESD** (E7). En continuo (E5) la corriente por R_PROT es de µA | Transitorio de ns, con 2.6 mA, frente a 10 mA continuos de máximo | Ver el punto de ESD |
| C6 BAV199 24 A | Pico con ±8 kV en contacto, comparado con 4 A de tp = 1 µs | **Métrica inadecuada:** un pulso de ~50 ns no se compara con el pico de 1 µs. Ver abajo | Revisar con I²t |

## ESD: la métrica correcta

- El BAV199 no declara rating de ESD. Lo que sí declara es IFSM = 4 A con tp = 1 µs, es decir **I²t ≈ 16 µA²s**.
- La red ESD de S2 (150 pF / 330 Ω) descarga con τ ≈ 50 ns. Con I₀ = 24 A, **I²t ≈ I₀²·τ/2 ≈ 14.5 µA²s a 8 kV en contacto** (0.9 del rating) y **≈ 3.6 µA²s a 4 kV** (4.4 veces por debajo).
- **El nivel acordado es ±4 kV en contacto y ±8 kV en aire** (DECISIONS, 2 oct). La descarga en aire es más lenta y con menos corriente. S2 probó 8 kV *en contacto*, que es más duro que lo pedido.
- **La red de S2 no tiene inductancia:** su flanco es de 0.3 ps, frente a los 0.7–1 ns de la IEC 61000-4-2. El pico (24 A) es del orden del real (30 A a 8 kV en contacto), pero la forma no.
- Conclusión provisional: **con BAV199 es plausible cumplir 4 kV en contacto**; 8 kV en contacto queda al límite y 8 kV en aire falta modelarlo. Hace falta S2b con una red IEC realista y el I²t como métrica.

## Segunda fuente: el AD8065 no es intercambiable

- **Máximo absoluto de tensión diferencial de entrada: 1.8 V** (hoja, tabla 4).
- En E5 (±100 V en ×1, continuo) su entrada diferencial llega a **3.1 V**: la entrada queda sujeta a ~5.7 V y la salida satura más abajo. En ESD llega a 4.0 V.
- El OPA810 aguanta ±7 V diferenciales y en E5 se queda en 0.88 V.
- **El AD8065 no sirve como segunda fuente directa.** Haría falta limitar la diferencial (diodos antiparalelo entre entradas, que en un seguidor añaden capacidad y fuga) o buscar otro equivalente.

## Lo demás

- **C4 rieles** (4.976–4.980 V), **C7 offset** (0.076 mV con OPA810; 0.40 mV con AD8065) y **C8 sonda a ±400 V** (THD 4·10⁻⁶ %, diodos a 2.7 nA): pasan con margen.
- **C5 canal apagado:** pasa con las tres variantes (0.45 / 0.17 / 0.003 V). Codex avisa de que los macromodelos sin alimentación no son válidos, así que se informa con la carga equivalente. **Hay que confirmarlo en placa.**
- **E8, recuperación de ~1–1.3 ms** tras ±40 V en ×1. Es inherente: después de sujetar, la rama ×1 se recupera con τ = R_S·C_S = R_BIAS·C_X1 ≈ 150 µs, y llegar a ±0.5 mV desde la sujeción lleva ~9 τ. Sólo baja reduciendo la capacidad de X1 o R_BIAS. El DSO112 tarda menos porque su nodo tiene sólo ~2.7 pF. No hay requisito; queda como característica para la hoja de especificaciones.
- **TVS de riel:** apenas conduce (pA–µA). No es decisiva con esta carga de riel.

## Dudas de Codex

| Duda | Juicio |
|---|---|
| Tensión nominal de C_EQ sin especificar | Correcto: queda **≥ 200 V** (ve 99 V en ÷100) |
| Capacidad explícita sumada a la del buffer | Correcto: error del plan; en S2b CIN_BUF = 0 con el modelo real |
| Modelos sin alimentación no válidos | Correcto: el canal apagado se valida en placa |
| Validación física de la ESD | Correcto: simulación y ensayo IEC no son lo mismo |
| El AD8065 no modela recuperación ni distorsión | Correcto: E8 del AD8065 es orientativo |

## Propuestas (deciden Keneth y la siguiente simulación)

1. **Piezas:** R_EQ en 1206 (o 2 × 4.99 MΩ); C_EQ y C_S de C0G ≥ 200 V.
2. **Segunda fuente del buffer:** descartar el AD8065 como reemplazo directo y buscar otro equivalente con ≥ ±7 V de diferencial, o aceptar el OPA810 como fuente única (RF-19).
3. **S2b**, encargo corto:
   - ESD con red IEC 61000-4-2 realista (flanco de ~0.8 ns, primer pico de 15 A/30 A a 4/8 kV) y una aproximación de descarga en aire;
   - I²t de los BAV199 frente a su rating;
   - repetir C1 con CIN_BUF = 0;
   - repetir C2 con R_EQ, C_EQ y C_S de 200 V.
