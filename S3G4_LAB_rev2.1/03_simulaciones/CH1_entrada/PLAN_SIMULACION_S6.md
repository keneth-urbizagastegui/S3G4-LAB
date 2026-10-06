# Plan de simulación S6 — ataque al ADC (muestreo entrelazado del G473)

- Autor: Claude Code (auditor), 3 oct 2026.
- Ejecuta: Codex. Audita: Claude.
- Contrato del encargo `ENCARGO_CODEX_S6.md`.
- Continúa S5. **Lee antes:**
  - `PLAN_SIMULACION_S5.md`, `ACTA_S5.md` y `AUDITORIA_CLAUDE_S5.md`;
  - `AUDITORIA_CLAUDE_S4.md`;
  - las entradas del 3 oct de `ai-context/DECISIONS.md`;
  - la §6 de `S3G4_LAB_rev2.1/01_diseno/revision_entrada_ch1.html` (E18);
  - los §2 y §3 de `S3G4_LAB_rev2.1/02_referencias/g473_analogico.html`;
  - el bloque ⑨ de `canal_rapido_ch1.html`.

## 1. Circuito fijo

- **S4** (cerrado): OPA836 a VDDA = 3.3 V, R_IN = R_F = 10.0 kΩ, R_OFF = 8.06 kΩ, **C_F = 1 pF**, VMID M1 (10.0 k / 5.23 k desde VREF+ = 2.5 V, con 1 µF), pata PD a VDDA; los diodos de modelado `DESD_OPA836` de S4 entre IN+ e IN−. R_ADC = 68 Ω y C_ADC = 470 pF C0G, hasta el pin PA0.
- Entrada de S4: fuente ideal (la salida del filtro U105; su impedancia no importa detrás de 10 kΩ). V_DAC = 1.25 V.
- **Filtro TR reescalado** (DECISIONS 3 oct): sólo para la prueba H3. Sección 1, R = 1.11 kΩ, C1 = 56 pF, C2 = 47 pF; sección 2, R = 499 Ω, C1 = 220 pF, C2 = 56 pF; AD8039 a ±5 V.

## 2. Modelo del ADC del G473 (DS12712 Rev 5, figura de la p. 147 y tabla 61)

- En el pin: **C_pad = 5 pF** a masa (capacidad del pad de la tabla 54 más la pista). Infórmalo como suposición.
- Por cada ADC (ADC1 y ADC2, el mismo pin): un interruptor de muestreo con **R_SW** en serie con **C_S = 5 pF** a VSSA.
- **R_SW** no viene en la hoja. Estimación de Claude a partir de la tabla 62 (R_AIN ≤ 100 Ω con 2.5 ciclos a 60 MHz y 12 bits): (R_AIN + R_SW) · C_S · ln(2¹³) ≤ 41.7 ns → R_SW ≈ 825 Ω. Repite el cálculo y **barre R_SW ∈ {400, 825, 1500 Ω}**.
- **Temporización** (RM0440 §21.4.12 y §21.4.30; D-02): f_ADC = 52 MHz; muestreo de 3.5 ciclos = **67.3 ns**; cada ADC convierte cada 16 ciclos = **307.7 ns**; ADC2 va desfasado 8 ciclos = **153.8 ns**. Resultado: 6.5 MSa/s en el pin.
- **Estado de C_S al abrir el muestreo** (no lo dice la hoja): tres casos.
  - **P (previo):** conserva la tensión de su propio muestreo anterior. Es el caso más probable.
  - **Z:** descargado a 0 V.
  - **R:** cargado a VREF+ = 2.5 V.
  Para Z y R, fuerza C_S a ese valor con un interruptor ideal durante la conversión (los 12.5 ciclos fuera de la ventana).
- **La muestra** es la tensión de C_S al cerrar la ventana.
- **Referencia sin carga:** simula en paralelo el mismo circuito **sin** interruptores ni C_S (con C_pad) y toma su tensión de pin en el mismo instante. **El error de muestreo es la diferencia entre las dos.** 1 LSB = 2.5 V / 4096 = 0.610 mV.

## 3. Pruebas

| # | Qué | Casos |
|---|---|---|
| H0 | Comprobaciones | R_SW deducida; temporización de los interruptores (gráfica o tabla de flancos de ADC1 y ADC2) |
| H1 | Continua | V_ADC de 0.25, 1.25 y 2.25 V; P, Z y R; R_SW × 3; ≥ 30 muestras ya en régimen: error de cada ADC |
| H2 | Seno a fondo de escala | 2 Vpp (8 div) centrado en 1.25 V a 0.5, 1 y 2 MHz, con la frecuencia ajustada para que el patrón no se repita (coherente con 6.5 MSa/s: N = 1024 muestras y M impar de ciclos); P, Z y R; R_SW × 3 |
| H3 | Cadena con el filtro TR | Seno de 2 MHz y 2 Vpp en el ADC, desde la entrada del filtro; P; R_SW = 825 Ω |
| H4 | Estabilidad | Ganancia de lazo del OPA836 (método de Middlebrook o de Tian en LTspice) con C_F = 1 pF y la carga 68 Ω + 470 pF + C_pad: margen de fase y frecuencia de cruce. Informa también el de cada sección de U105 |

Análisis de H2 y H3:
- error máximo y rms por muestra, en mV y en LSB, separado por ADC;
- **descomposición:** ajusta por mínimos cuadrados el error de cada muestra como a·v[n] + b·v[n−2] + c (v[n−2] es la muestra anterior del mismo ADC). Informa del residuo rms y máximo: es la parte no lineal. Convierte la parte lineal en cambio de ganancia (dB) y de fase (grados) a esa frecuencia;
- FFT de la secuencia de 1024 muestras (con y sin carga): SFDR, THD y el espurio del entrelazado en f_s/2 − f_in.

## 4. Criterios de aceptación

| # | Criterio | Prueba |
|---|---|---|
| S6-C1 | Continua: \|error\| ≤ 0.5 LSB (0.305 mV) en régimen, con P y R_SW = 825 Ω | H1 |
| S6-C2 | E18 tal cual: error ≤ 0.5 LSB con seno de 2 MHz a fondo de escala (P, 825 Ω). **Infórmalo aunque falle**, junto con la descomposición | H2 |
| S6-C3 | Parte no lineal (residuo de la descomposición) ≤ 0.5 LSB rms y SFDR de la secuencia ≥ 66 dB (el SNR típico del ADC, tabla 63) a 2 MHz | H2, H3 |
| S6-C4 | Parte lineal: cambio de ganancia a 2 MHz ≤ 0.1 dB | H2 |
| S6-C5 | Margen de fase del OPA836 ≥ 45° | H4 |
| — | Lo mismo con Z, R y las otras R_SW, sin criterio, para ver la sensibilidad | H1, H2 |

Fallar es un resultado válido; informa siempre el valor medido. **No cambies R_ADC, C_ADC ni nada del circuito**: si algo falla, di cuánto falta y qué variable lo movería (R_ADC, C_ADC, ciclos de muestreo), sin simular cambios.

## 5. Entregables

En `S3G4_LAB_rev2.1/03_simulaciones/CH1_entrada/`, sin tocar S1…S5:

1. `comun/ch1_comun_s6.inc`: S4 cerrada, el filtro TR reescalado y el modelo del ADC parametrizado (R_SW, estado previo).
2. `S6/` con los `.cir`; `analisis_s6.py` con la descomposición y las FFT.
3. `ejecutar_s6.py`, paralelo (10 trabajadores), con `--smoke` y `S3G4_MODELS`. Orden de columnas fijo y registros fuera de la comprobación de ficheros protegidos.
4. `resultados/s6_*.csv` y `resultados/s6_resumen.md`.
5. `ACTA_S6.md`, con:
   - criterios;
   - el modelo del ADC y de dónde sale cada número;
   - dudas;
   - tiempo y código de salida.
6. Tu diario en `ai-context/journal/`, abierto al principio y completado sobre la marcha.

## 6. Lo que NO es tuyo

- No cambies el circuito ni elijas remedios. No diseñes S7.
- No modifiques `Simulation_LTSpice/models/`, los entregables anteriores, `chequeo_claude/`, `STATE.md` ni `DECISIONS.md`. No descargues nada.

## 7. Cómo voy a auditar

1. Reejecución en ruta corta, CSV byte a byte.
2. Temporización de los interruptores: 67.3 ns, 307.7 ns y 153.8 ns.
3. Que la muestra se toma al cerrar la ventana y que la referencia sin carga es el mismo circuito en el mismo instante.
4. La descomposición lineal / no lineal y la coherencia de la FFT (sin ventana, frecuencia coherente).
5. El método de la ganancia de lazo.
