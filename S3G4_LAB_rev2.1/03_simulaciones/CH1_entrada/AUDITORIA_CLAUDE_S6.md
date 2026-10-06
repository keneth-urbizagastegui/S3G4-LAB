# Auditoría de Claude — S6 de CH1 (muestreo entrelazado del G473)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) desde las 20:18: código 0, 67 simulaciones, y su reproducción dio 11/11 CSV idénticos.
- Reejecución de Claude: §4.

## Veredicto

**El driver (S4 + 68 Ω + 470 pF) ataca bien al ADC entrelazado.** El único criterio que falla, S6-C2 (E18: error ≤ 0.5 LSB con seno de 2 MHz a fondo de escala), **estaba mal planteado en mi plan**: mide un retraso fijo de 4 ns propio del ADC como si fuera error.

| Criterio | Codex | Auditoría |
|---|---|---|
| S6-C1 continua | 3.6·10⁻⁶ LSB | **Pasa** |
| S6-C2 E18 tal cual | 86.6 LSB, falla | **Criterio mal definido** (§1). Lo que mide es un retraso de 4.2 ns |
| S6-C3 no lineal | residuo 0.0009 LSB rms; SFDR ≥ 106 dB | **Pasa** |
| S6-C4 ganancia a 2 MHz | −0.043 dB | **Pasa** |
| S6-C5 margen de fase | OPA836 77.9° a 12.8 MHz; U105A/B 61–62° | **Pasa** |

## 1. Por qué E18 falla y por qué no importa

El error que da Codex contra el pin sin carga, en el mismo instante, sigue exactamente la constante de tiempo interna del ADC (R_SW · C_S). La muestra en C_S sigue al pin con ese retraso:

| R_SW | Error pico a 2 MHz (1 V de amplitud) | Retraso equivalente = error / (2π · 2 MHz · 1 V) | R_SW · 5 pF |
|---|---|---|---|
| 400 Ω | 26.65 mV | 2.12 ns | 2.0 ns |
| 825 Ω | 52.83 mV | 4.20 ns | 4.1 ns |
| 1500 Ω | 93.91 mV | 7.47 ns | 7.5 ns |

La descomposición de Codex lo confirma: la parte lineal es un desfase de −3.02° con −0.043 dB, y lo que queda es del orden de 10⁻³ LSB. Por tanto:

- es un **retraso puro**, igual en ADC1 y ADC2 (el espurio de entrelazado en f_s/2 − f_in está a −160 dBc), así que no deforma la señal: desplaza la traza unos 4 ns en el tiempo;
- **no depende del circuito externo**: lo pone el interruptor interno del ADC, y lo tendría cualquier driver;
- el firmware puede compensarlo en el disparo si hiciera falta. 4 ns son el 2.6 % de un intervalo de muestreo (154 ns).

**Criterio corregido** para S7 y para el acta final: error no lineal ≤ 0.5 LSB (S6-C3) y ganancia a 2 MHz ≤ 0.1 dB (S6-C4). Ambos pasan con mucho margen. El retraso se informa aparte.

## 2. Sensibilidad al estado del condensador de muestreo

- Con el estado P (C_S conserva su muestra anterior, el caso realista), el error en continua es despreciable.
- Si el G473 descargara C_S a 0 V (Z) o la cargara a VREF+ (R) antes de cada muestreo, el error en continua llega a **5.26 mV (8.6 LSB)**. Es proporcional a V (Z) o a 2.5 V − V (R), es decir, un error de ganancia y offset fijo que absorbe la calibración P10.
- **Conviene medirlo en placa:** una rampa lenta comparada con un multímetro dirá cuál de los tres estados es el real.

## 3. Supuestos que quedan abiertos (anotados por Codex)

- R_SW = 825 Ω es una deducción a partir de la tabla 62; la hoja no la da.
- C_pad = 5 pF: pad más pista.
- No se modelan el ruido ni la cuantización del ADC, ni el desajuste ni el jitter entre ADC1 y ADC2. El desajuste de ganancia y offset entre los dos ADC sí aparecerá en placa: se corrige con la calibración por ADC.
- Los SFDR de más de 100 dB son el suelo numérico de la simulación, no una cifra del silicio. El SNR real del ADC es de 63–67 dB (tabla 63).

## 4. Reproducción

Reejecución de Claude en `…\Temp\claude\s6a` con `S3G4_MODELS`: código 0, 67 simulaciones, 457 s; **11/11 CSV idénticos byte a byte**.

## 5. Para Keneth

Nada que decidir en S6. Siguiente: **S7**, la integración de todo el canal (BNC → PA0):
- filtro TR reescalado con su Monte Carlo, escalón y recuperación;
- sin la carga ficticia de U103B;
- las 12 escalas;
- consumo por etapa.
