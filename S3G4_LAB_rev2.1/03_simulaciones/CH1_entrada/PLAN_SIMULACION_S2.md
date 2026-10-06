# Plan de simulación S2 — protección y abusos de la entrada P4b de CH1

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S2.md`.
- Continúa S1 y S1b. **Lee antes:**
  - `PLAN_SIMULACION_S1.md` y `PLAN_SIMULACION_S1b.md`: circuito, nombres y reglas, vigentes salvo lo que cambia aquí;
  - `ACTA_S1b.md`;
  - `AUDITORIA_CLAUDE_S1.md` y `AUDITORIA_CLAUDE_S1b.md`;
  - `ai-context/DECISIONS.md`, entradas del 2 y 3 oct (nivel de seguridad, trimmer, buffer).

## 1. Qué se comprueba

Que la entrada P4b de CH1 cumple el nivel de seguridad acordado el 2 oct, ya con **modelos de fabricante**:
- 50 Vpk declarados;
- **±100 V sin daño en cualquier escala, también con el equipo apagado**;
- **ESD de ±8 kV en aire y ±4 kV en contacto** en el vivo de la BNC.

Además: fugas y deriva en continua, recuperación de sobrecarga y sonda ×10 a ±400 V en la punta (RF-07). Son las pruebas E5–E10 de `01_diseno/revision_entrada_ch1.html` §6, más una prueba E0 de puesta a punto.

## 2. Circuito y modelos

Parte de `comun/ch1_comun_s1b.inc`: P4b con el trimmer R1 (2–6 pF) a mitad de recorrido, CT1 = 20 pF. Crea `comun/ch1_comun_s2.inc` sin tocar los anteriores, con estos cambios:

| Elemento | En S2 | Fuente |
|---|---|---|
| Diodos de sujeción | **Modelo BAV199 de Nexperia** (`Simulation_LTSpice/models/BAV199.txt`; copiar sólo el `.MODEL`, el fichero trae un `.ENDS` suelto) | DECISIONS 3 oct |
| C_SEL_EST | con la CJ polarizada **del modelo real**: CJO/(1 + 5/VJ)^M con CJO = 1.9002 pF, VJ = 1.2722, M = 0.35193 (≈ 1.08 pF por diodo). CEQ, CS y CB se recalculan con `.param` | chequeo `chequeo_claude/modelos_s2.cir` |
| Buffer | **OPA810** (`Simulation_LTSpice/models/OPA810/opa810_a.lib`), seguidor a ±5 V. Su subcircuito es `OPA810 IN+ IN- OUT VCC VEE`: **ojo al orden de nodos** (ver `Simulation_LTSpice/models/LEEME.md`). R_PROT 1 kΩ delante de IN+, como en S1 | DECISIONS 3 oct |
| Buffer, segunda fuente | **AD8065** (`Simulation_LTSpice/models/ad8065.cir`, `AD8065 IN+ IN- V+ V- OUT`) en las pruebas marcadas «2.ª fuente» | DECISIONS 3 oct |
| Carga del buffer | Escalera de 997.7 Ω a masa (la de C.3), tomada en 1/1 | documento vivo C.3 |
| Rieles ±5 V | **Modelo que no absorbe corriente**: fuente de 5.0 V → 0.5 Ω → diodo ideal (sólo entrega) → nodo del riel con 10 µF + 100 nF, carga resistiva equivalente a la del AFE (+5 V: 42 mA → 119 Ω; −5 V: 39 mA → 128 Ω) y **TVS de riel**. El −5 V es el espejo. Es la limitación real del LM27762 (G.5) | documento vivo G.5 |
| TVS de riel | Genérica de 6.0 V de standoff tipo SMAJ6.0A: BV = 6.67 V a 1 mA, ~10.3 V a 38.8 A (RS ≈ 0.094 Ω). Unidireccional, riel a masa | por elegir |
| Riel de un canal apagado | El regulador queda separado por un interruptor de carga abierto. Queda el desacoplo local (1 µF + 100 nF) y la carga de los amplificadores sin alimentar (1 MΩ), con tres variantes de descarga: **ninguna**, **purga de 10 kΩ** y **descarga activa de 100 Ω** | revisión R12, G.6 |
| Relé sin alimentación | POS = 100 forzado (monoestable en reposo) | D-03 |

Los valores de diseño de §3 de S1/S1b no cambian, salvo los derivados que dependen de C_SEL_EST.

## 3. Límites de las piezas (para los criterios)

Si la hoja de una pieza contradice esta tabla, usa la hoja y anótalo en dudas.

| Pieza | Límite | Criterio (reducción) |
|---|---|---|
| R1A, R1B, R_S1, R_S2 (1206) | 0.25 W, 200 V | ≤ 50 % de potencia (125 mW) y ≤ 50 % de tensión (100 V) en continuo |
| R2 (0805), R_EQ, R_BIAS, R_PROT (0805) | 0.125 W, 150 V | ≤ 50 % |
| C_S | 100 V (C.6) | ≤ 80 % de su tensión: **comprobar**, con 100 V en ×1 puede ver casi 95 V |
| C1A, C1B (≥ 100 V), C_TRIM (100 V), C2 (50 V), C_AC (50 V), C_EQ | según C.6 | ≤ 80 % |
| BAV199 | IF ≤ 160 mA continua; IFSM 4 A (1 µs); VR 75 V | continua ≤ 50 %; pico de ESD informado frente a IFSM |
| OPA810, entrada | Leer de `datasheet - componentes/opa810.pdf` (máximos absolutos: tensión y corriente de entrada) | dentro del máximo absoluto con margen |
| AD8065, entrada | Leer de `AD8065_8066 (1).pdf` | ídem |
| Contactos abiertos del HFD27 | informar la tensión entre contactos | — |

## 4. Pruebas

| # | Qué | Casos | Medidas |
|---|---|---|---|
| E0 | Puesta a punto con modelos reales: E1/E2 nominal (Zin, Cin, ΔCin, planitud a 2 MHz, corte AC) con OPA810 y BAV199 reales | POS {1, 100} × CPL {DC, AC} | Comparar con S1b; la diferencia de ΔCin la explica la CJ real |
| E5 | Sobretensión, equipo encendido | ±100 V y ±50 V en continua; seno de 1 kHz y 100 Vpk; POS {1, 100}; CPL {DC, AC} | Potencia y tensión de cada R y C de §3; corriente de cada BAV199; tensión y corriente en la entrada del buffer; corriente inyectada y tensión de cada riel; tensión entre contactos abiertos del relé |
| E6 | Canal apagado | ±100 V en continua; POS = 100 forzado; las tres variantes de descarga | Tensión del riel apagado; corrientes de E5 |
| E7 | ESD IEC 61000-4-2 | Red de 150 pF / 330 Ω cargada a +4, −4, +8 y −8 kV, descargada en la BNC (contacto). Paso ≤ 0.1 ns los primeros 200 ns. POS {1, 100}; equipo encendido. Equipo apagado sólo a +8 kV | Pico de corriente en cada BAV199 y en cada TVS de riel; pico de tensión y de corriente en la entrada del buffer; pico de tensión de los rieles; energía en R_S |
| E8 | Recuperación de sobrecarga | POS = 1, CPL = DC: ráfaga de ±40 V (fondo de escala del equipo) durante 1 ms sobre 0 V | Tiempo desde el final de la ráfaga hasta que la salida del buffer vuelve a ±1 div y a ±0.1 div de 5 mV/div (±5 mV y ±0.5 mV) |
| E9 | Fugas y deriva en continua | POS {1, 100}; CPL {DC, AC}; BNC con fuente de 50 Ω a 0 V y BNC al aire; `.temp` 25 y 85 °C | Offset en la salida del buffer referido a la BNC |
| E10 | Sonda ×10 a ±400 V (RF-07) | Sonda compensable de S1b (CTIP fijado en ÷100); seno de 1 kHz y 400 Vpk en la punta; POS = 100 | THD de la salida del buffer (7 armónicos); corriente máxima de los BAV199 |
| 2.ª fuente | Repetir E0, E5 (sólo ±100 V en continua), E7 (±8 kV), E8 y E9 con AD8065 | — | Las mismas |

## 5. Criterios de aceptación

Fallar es un resultado válido; informar siempre el valor medido.

| # | Criterio | Prueba |
|---|---|---|
| S2-C1 | E0: S1b-C1…C4 siguen pasando con modelos reales; ΔCin ≤ 2 pF con C_EQ recalculado | E0 |
| S2-C2 | Con ±100 V, toda R y C de §3 dentro de su criterio, en todas las posiciones | E5 |
| S2-C3 | Entrada del buffer dentro de su máximo absoluto (tensión y corriente), con margen | E5, E6, E7 |
| S2-C4 | Rieles encendidos: tensión dentro de ±5 % (4.75–5.25 V) en E5 | E5 |
| S2-C5 | Canal apagado: el riel no sube de 0.5 V con al menos una de las variantes de descarga; informar las tres | E6 |
| S2-C6 | ESD: pico de corriente en los BAV199 y en la TVS informado frente a su hoja; entrada del buffer dentro del máximo durante el pulso o con energía acotada (informar las dos cosas) | E7 |
| S2-C7 | Offset ≤ 0.5 mV con fuente de 50 Ω a 25 °C (0.1 div a 5 mV/div) en ×1 | E9 |
| S2-C8 | Sonda a ±400 V: THD ≤ 0.1 % y corriente de los BAV199 < 1 µA | E10 |
| — | E8 sin criterio: informar los tiempos; objetivo orientativo ≤ 10 µs hasta ±1 div | E8 |
| — | 2.ª fuente: informar las diferencias con el OPA810 | — |

## 6. Entregables

Todo dentro de `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, **sin modificar los entregables de S1 ni de S1b**:

1. `comun/ch1_comun_s2.inc`.
2. `S2/` con los `.cir` y los generados.
3. `ejecutar_s2.py`, **paralelo desde el principio** (10 trabajadores, como `ejecutar_s1b.py`):
   - CSV en orden determinista;
   - modo `--smoke`;
   - umbrales en una sola tabla del script;
   - sale con código ≠ 0 sólo si una simulación da error.
4. `resultados/s2_*.csv` y `resultados/s2_resumen.md`.
5. `ACTA_S2.md`, con:
   - tabla de criterios;
   - lo que enseña cada prueba;
   - la segunda fuente;
   - **dudas y contradicciones sin resolver**;
   - paralelización, tiempo y código de salida.
6. Tu diario en `ai-context/journal/`.

## 7. Lo que NO es tuyo

- No cambies valores de diseño para que algo pase, salvo los derivados que este plan manda recalcular. Si una pieza se queda corta (por ejemplo, C_S de 100 V), **se informa**; no se cambia.
- No elijas la TVS de riel ni el interruptor de carga: mide con los modelos de §2 e informa.
- No modifiques `Simulation_LTSpice/models/` (sólo lectura), ni los entregables de S1 o S1b, ni `chequeo_claude/`. Ni `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 8. Cómo voy a auditar

1. Reejecuto `ejecutar_s2.py` en una copia limpia y comparo los CSV byte a byte.
2. El orden de nodos del OPA810 y del AD8065 en los envoltorios, y que el BAV199 es el de Nexperia.
3. C_SEL_EST, CEQ, CS y CB con la CJ real, con `.param`.
4. El modelo de riel: que no absorbe corriente y que sus cargas son las de G.3.
5. E0 frente a S1b, y los límites de §3 frente a las hojas.
6. El paso temporal de E7 y la forma de onda de la red ESD (pico y tiempo de subida informados).
