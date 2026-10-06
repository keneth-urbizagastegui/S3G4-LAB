# Plan de simulación S2b — ESD realista, piezas de 200 V y capacidad del buffer

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S2b.md`.
- Continúa S2. **Lee antes:** `PLAN_SIMULACION_S2.md` (vigente salvo lo que cambia aquí), `ACTA_S2.md`, `AUDITORIA_CLAUDE_S2.md` y las entradas del 3 oct de `ai-context/DECISIONS.md`.

## 1. Qué cambia respecto a S2

1. **Capacidad del buffer sin doble cuenta** (error del plan de S2). Con macromodelo real, **CIN_BUF = 0** en el circuito: el modelo ya trae su capacidad. En la estimación de diseño, `C_SEL_EST` usa la capacidad de modo común de la hoja en su lugar: **2.5 pF para el OPA810** (el valor mayor de los dos que da la hoja, 2 y 2.5 pF). CEQ, CS y CB se recalculan con `.param`.
2. **Piezas de 200 V** (DECISIONS 3 oct): R_EQ en 1206 (0.25 W, 200 V); C_EQ y C_S de C0G de 200 V. Los valores no cambian; cambian los límites de §3 de S2 para esas tres piezas.
3. **ESD con un generador IEC 61000-4-2 realista**, en vez de 150 pF / 330 Ω sin inductancia (flanco de 0.3 ps en S2). Ver §2.
4. **Métrica de ESD para los BAV199: I²t**, no el pico. El BAV199 declara IFSM = 4 A con tp = 1 µs en onda cuadrada, es decir **I²t_lím = 16 µA²s** por diodo.
5. El buffer es el OPA810. **El AD8065 queda fuera** (DECISIONS 3 oct). Si en `Simulation_LTSpice/models/` aparece el modelo de una nueva segunda fuente (OPA828 de TI), repite con ella E0, E5 (±100 V en continua), E7 y E9, y compara su tensión diferencial de entrada con la de su hoja. Si no está, sáltalo y dilo.
   - **Modelo disponible (3 oct):** `Simulation_LTSpice/models/OPA828/OPAx828.LIB`, `.SUBCKT OPAx828 IN+ IN- VCC VEE OUT`. Hoja: `datasheet - componentes/opa828.pdf`. Diferencial máxima = (V+) − (V−), sin diodos entre entradas; entrada en modo común de (V−) − 0.5 a (V+) + 0.5 V; ±10 mA. Para la segunda fuente, la capacidad de modo común de C_SEL_EST es la de su hoja.

## 2. Generador de ESD

Construye un generador de descarga en contacto que, **descargado sobre 2 Ω** (el blanco de calibración de la norma), cumpla la tabla de la IEC 61000-4-2 en las dos tensiones:

| Nivel | Primer pico | Tiempo de subida | I a 30 ns | I a 60 ns |
|---|---|---|---|---|
| 4 kV | 15 A ±15 % | 0.8 ns ±25 % | 8 A ±30 % | 4 A ±30 % |
| 8 kV | 30 A ±15 % | 0.8 ns ±25 % | 16 A ±30 % | 8 A ±30 % |

- Vale cualquier red RLC de la literatura (por ejemplo, de dos ramas: el cuerpo de 150 pF / 330 Ω más una rama rápida de pocos pF con su inductancia).
- **Primero verifica el generador sobre 2 Ω e informa los cuatro puntos**; después descárgalo sobre la BNC.
- **Descarga en aire de 8 kV:** no tiene forma normalizada. Aproxímala con el mismo generador a 8 kV más una resistencia de arco en serie de 300 Ω e informa la forma resultante. Es orientativo y va sin criterio propio, salvo que lo pida §4.

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| E0b | E1/E2 nominal con CIN_BUF = 0 y C_SEL_EST corregida | POS {1, 100} × CPL {DC, AC} |
| E5b | Como E5 de S2 con los límites nuevos de §1.2 | ±100 V en continua y seno de 100 Vpk; POS {1, 100}; CPL {DC, AC} |
| E7a | Verificación del generador sobre 2 Ω | 4 kV y 8 kV, contacto |
| E7b | ESD en la BNC, equipo encendido | ±4 kV y ±8 kV en contacto, +8 kV en aire; POS {1, 100}; paso ≤ 0.05 ns los primeros 100 ns |
| E7c | ESD en la BNC, equipo apagado | ±4 kV en contacto, +8 kV en aire; POS = 100; las tres variantes de descarga del riel |

Medidas de E7b/E7c:
- I²t y pico de corriente de **cada** BAV199;
- corriente y tensión pico en la entrada del OPA810;
- tensión diferencial de entrada del OPA810;
- pico de tensión de los rieles;
- energía en R_S1, R_S2, R1A y R1B;
- tensión pico sobre C_S y sobre los contactos del relé.

## 4. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S2b-C1 | ΔCin ≤ 2 pF y el resto de S1b-C1…C4 pasan | E0b |
| S2b-C2 | Con ±100 V, toda R y C dentro de su criterio con los límites nuevos (R ≤ 50 %, C ≤ 80 %) | E5b |
| S2b-C3 | En continuo (E5b): entrada del OPA810 dentro de VS ± 0.5 V **y** \|I\| ≤ 10 mA; diferencial ≤ ±7 V | E5b |
| S2b-C4 | El generador cumple los cuatro puntos de §2 sobre 2 Ω, a 4 y a 8 kV | E7a |
| S2b-C5 | **±4 kV en contacto:** I²t de cada BAV199 ≤ 50 % de 16 µA²s; corriente pico en la entrada del OPA810 ≤ 10 mA; diferencial ≤ ±7 V | E7b, E7c |
| — | ±8 kV en contacto y 8 kV en aire: informar las mismas medidas frente a los mismos límites (el nivel acordado es 4 kV en contacto y 8 kV en aire) | E7b, E7c |

Fallar es un resultado válido; informar siempre el valor medido.

## 5. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, **sin modificar los entregables de S1, S1b ni S2**:

1. `comun/ch1_comun_s2b.inc`.
2. `S2b/`.
3. `ejecutar_s2b.py`, paralelo (10 trabajadores) con `--smoke`. **Ojo a la ruta:** que los modelos se encuentren también si la carpeta se copia a otro sitio. Por ejemplo, admite una variable de entorno `S3G4_MODELS` con la ruta de los modelos, y si no está, usa la ruta relativa actual.
4. `resultados/s2b_*.csv` y `resultados/s2b_resumen.md`.
5. `ACTA_S2b.md`, con:
   - criterios;
   - la verificación del generador;
   - **dudas y contradicciones sin resolver**;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`.

## 6. Lo que NO es tuyo

- No cambies valores de diseño para que algo pase. Si algo falla, se informa.
- No elijas protecciones nuevas (TVS, ferritas, resistencias de ESD): si C5 falla, informa cuánto falta.
- No modifiques `Simulation_LTSpice/models/`, ni los entregables anteriores, ni `chequeo_claude/`, ni `STATE.md`, ni `DECISIONS.md`. No descargues nada.

## 7. Cómo voy a auditar

1. Reejecución en una copia limpia con `S3G4_MODELS` y comparación de los CSV byte a byte.
2. Que CIN_BUF = 0 con el modelo real y que C_SEL_EST usa 2.5 pF.
3. La verificación del generador sobre 2 Ω, frente a la tabla de §2.
4. El cálculo de I²t (integral de i² sobre todo el pulso) y que se informa **por diodo**.
5. El paso temporal de E7b/E7c.
