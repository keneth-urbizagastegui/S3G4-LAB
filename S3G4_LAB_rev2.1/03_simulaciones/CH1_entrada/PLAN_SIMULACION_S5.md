# Plan de simulación S5 — filtro anti-alias de CH1

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S5.md`.
- Continúa S4. **Lee antes:**
  - `PLAN_SIMULACION_S4.md`, `ACTA_S4.md` y `AUDITORIA_CLAUDE_S4.md`;
  - las entradas del 3 oct de `ai-context/DECISIONS.md`;
  - la §6 de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (E17);
  - el §6 de `S3G4_LAB_rev2.1/01_diseno/canal_rapido_ch1.html` (alias, Bessel y Butterworth).

## 1. Decisiones que fija este plan

- **S4 cerrado** (Keneth, 3 oct): OPA836 con C_F = 1 pF, VMID M1 (divisor 10.0 k / 5.23 k + 1 µF por canal), R_IN = R_F = 10.0 kΩ, R_OFF = 8.06 kΩ, R_ADC = 68 Ω y C_ADC = 470 pF.
- **Filtro (Keneth, 3 oct): una etapa nueva U105 con un AD8039 doble** (el mismo de U103, C96525), a ±5 V, **entre U103B y S4**. Son dos secciones Sallen-Key de ganancia unidad (4.º orden activo).
- **Polos fijos que el filtro tiene que contar:** el RC del ADC (68 Ω · 470 pF, 4.98 MHz) y S4 (−3 dB en 10.8 MHz con C_F). Con ellos, el canal es de 6.º orden. Las pérdidas de S1–S3 a 2 MHz son de 0.02 dB.

## 2. Los tres candidatos

Cálculo previo de Claude (scipy, ideal): prototipos de 4.º orden escalados para que **la cadena completa**, con los dos polos fijos, quede a −3 dB en 2.0 MHz.

| Candidato | Biquad 1 (f0, Q) | Biquad 2 (f0, Q) | A 3.25 MHz | A 4.5 MHz | Sobreimpulso | Subida 10–90 % |
|---|---|---|---|---|---|---|
| **BE**, Bessel | 3.70 MHz, 0.806 | 3.30 MHz, 0.522 | 8.4 dB | 16.0 dB | 0.3 % | 173 ns |
| **TR**, intermedio (Butterworth-Thomson, m = 0.5) | 2.83 MHz, 0.987 | 2.68 MHz, 0.531 | 10.9 dB | 21.4 dB | 2.9 % | 182 ns |
| **BU**, Butterworth | 2.11 MHz, 1.307 | 2.11 MHz, 0.541 | 17.1 dB | 29.7 dB | 9.4 % | 196 ns |

**Repite este cálculo tú**, en Python y desde los prototipos (`scipy.signal.besselap(norm='mag')`, `buttap`; para TR, media geométrica de módulos y media aritmética de ángulos de los polos de Butterworth y Bessel), antes de sintetizar.

### 2.1 Síntesis de cada sección Sallen-Key de ganancia unidad

- R1 = R2 = R; C1 (realimentación, a la salida) y C2 (a masa).
- Q = ½ · √(C1/C2) y f0 = 1 / (2π · R · √(C1 · C2)).
- R entre 499 Ω y 2.49 kΩ, en serie E96. C en serie E12, C0G.
- Elige C2 de un valor E12 razonable (por ejemplo, 100–220 pF), redondea C1 al E12 más cercano y ajusta R (E96) para recuperar f0. Informa de f0 y Q reales tras redondear.
- Orden de las secciones: la de Q bajo primero (mejor margen dinámico).

## 3. Circuito

```
U103B ─► [SK 1 · U105A] ─► [SK 2 · U105B] ─► S4 (OPA836, C_F 1 pF, M1) ─► 68 Ω ─► pin ADC + 470 pF
```

- Cadena delante: la de S4 (`comun/ch1_comun_s4.inc`, sin cambios). Pistas: 1 pF en cada entrada no inversora de U105.
- `.noise` con `AD8038_ltspice_ruido_hoja.sub`; lo demás, con el original.

## 4. Pruebas

| # | Qué | Casos |
|---|---|---|
| G0 | Síntesis | Tabla de componentes por candidato; f0 y Q reales; comprobación de cada sección aislada (AC) |
| G1 | Respuesta en frecuencia de BNC a pin del ADC | 3 candidatos × 12 escalas; de 1 kHz a 200 MHz, ≥ 100 puntos por década: −3 dB, atenuación a 3.25, 4.5 y 6.5 MHz, máximo de \|H\| por encima de 4.5 MHz (rebote del Sallen-Key), pico en la banda de paso y variación del retardo de grupo de 0 a 2 MHz |
| G2 | Escalón | 3 candidatos, 5 mV/div y 0.5 V/div: escalón de 1 div con 2 ns de subida y cuadrada de 100 kHz de 4 div: sobreimpulso, subida 10–90 % y asentamiento a 1 % |
| G3 | Tolerancias, Monte Carlo | 3 candidatos, 5 mV/div; 200 casos con R ±1 % y C ±5 % (uniforme, semilla fija): distribución del −3 dB, del pico y de la atenuación a 4.5 MHz |
| G4 | Gran señal | 3 candidatos, 5 mV/div: seno de 1 y 2 MHz con 8 div pp en el ADC, offset 0: THD |
| G5 | Ruido | 3 candidatos, 12 escalas, de 1 Hz a 3.15 MHz en el pin del ADC (antes de los 5 pF) |
| G6 | Sobrecarga | 3 candidatos, 5 mV/div: pulsos de ±2 y ±4.5 V en la BNC (como B4 de S3b): recuperación; diferencial y corriente de entrada de U105A/B |

## 5. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S5-C1 | −3 dB de la cadena completa en **2.0 MHz ± 10 %** en las 12 escalas (nominal) | G1 |
| S5-C2 | En el Monte Carlo, ≥ 95 % de los casos dentro de 2.0 MHz ± 10 % | G3 |
| S5-C3 | Pico en la banda de paso ≤ 0.5 dB (nominal) | G1 |
| S5-C4 | Sin rebote: por encima de 4.5 MHz, \|H\| nunca supera a \|H(4.5 MHz)\| hasta 200 MHz | G1 |
| S5-C5 | Subida 10–90 % de **175 ns ± 20 %** | G2 |
| S5-C6 | THD ≤ 1 % | G4 |
| S5-C7 | Ruido ≤ 0.45 % de división en las 12 escalas | G5 |
| S5-C8 | Recuperación ≤ 1 µs; diferencial de U105 ≤ 2 V | G6 |
| — | Informar sin criterio, para que elija Keneth: atenuación a 3.25 / 4.5 / 6.5 MHz, sobreimpulso, retardo de grupo y consumo | G1, G2 |

Fallar es un resultado válido; informa siempre el valor medido. **No elijas candidato.**

## 6. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, sin tocar S1…S4:

1. `comun/ch1_comun_s5.inc`, que incluye `ch1_comun_s4.inc` y añade U105 parametrizado por candidato.
2. `S5/` con los `.cir`; `sintesis_s5.py` con el cálculo de §2.
3. `ejecutar_s5.py`, paralelo (10 trabajadores), con `--smoke` y `S3G4_MODELS`. **Guarda los registros fuera de la carpeta vigilada** o exclúyelos de la comprobación de ficheros protegidos (en la reejecución de S4 eso dio un falso código 1).
4. `resultados/s5_*.csv` (con orden de columnas fijo) y `resultados/s5_resumen.md`.
5. `ACTA_S5.md`, con:
   - la tabla de componentes;
   - los criterios por candidato;
   - una tabla comparativa para elegir;
   - dudas;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`. **Escríbelo pronto y ve completándolo**: en S4 te quedaste sin cupo antes de escribirlo.

## 7. Lo que NO es tuyo

- No cambies S1–S4 ni los polos fijos. No añadas protecciones.
- No elijas candidato ni el filtro de CH2/CH3.
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 8. Cómo voy a auditar

1. Reejecución en ruta corta, comparando valores (y bytes si el orden de columnas es fijo).
2. La síntesis contra mi tabla de §2.
3. Que el −3 dB y la atenuación se miden de la BNC al pin del ADC, con S4 y el RC incluidos.
4. El rebote del Sallen-Key a alta frecuencia con el modelo real del AD8039.
5. La semilla y el reparto del Monte Carlo.
