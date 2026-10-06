# Auditoría de Claude — S7 de CH1 (canal completo, contrato original)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) de 21:16 a ~22:35: código 0, 694 simulaciones (690 casos), 37.9 min.
- **S7 verifica el contrato original (±5 V, C_S derivado de 1.169 nF).** Las decisiones de Keneth tomadas durante la ejecución (R1: C_S 1.2 nF; R2: ±4.9 V; criterio de tolerancias) las verifica **S7b**, lanzado a las 22:41.

## Veredicto

**El canal completo funciona en simulación.** Pasan 8 de 9 criterios. C8 falla sólo por el recorte del offset en −4.85 div, ya aceptado por Keneth.

| Medida | Resultado |
|---|---|
| −3 dB (12 escalas) | 2.006–2.007 MHz |
| Atenuación a 4.5 MHz | 21.70–21.72 dB |
| Subida 10–90 % | 182 ns (175 ns ± 20 %) |
| Ruido | 0.25–0.32 % de división |
| Monte Carlo (−3 dB en ± 10 %) | 100 % en 5 mV/div y 96 % en 0.5 V/div; pico máximo de 0.66 dB (11 de 300 casos > 0.5 dB, en 0.5 V/div) |
| Límites con ±40 V | diferencial máxima 0.88 V (OPA810), 0.69 V (U103A), 0.68 V (U103B), 0.04 V (U105), 0.62 V (OPA836); pin del ADC de 0.007 a 3.29 V |
| Recuperación | ≤ 0.70 µs |
| Muestreo (J7) | SFDR ≥ 107 dB (suelo numérico), residuo ≤ 0.006 LSB rms |
| Ganancia en continua | −49.50 en 5 mV/div (−1.0 % frente a −50): de −0.4 a −1 % según la escala; la corrige la calibración (`resultados/s7_tabla_calibracion.csv`, con signo) |
| Consumo por canal (modelos) | 6.0 mA en +5 V, 6.1 mA en −5 V y 1.0 mA en VDDA. **Con el OPA810 a su hoja (3.7 mA en vez de 1.9) serían ≈ 7.8 mA por riel** (REVISION R3) |

## Comprobaciones puntuales de Claude

- `comun/ch1_comun_s7.inc`:
  - filtro TR reescalado (1.11 k, 56 / 47 pF; 499 Ω, 220 / 56 pF);
  - 470 Ω + BAV99 en U103A y U103B;
  - C_F = 1 pF y VMID M1;
  - **sin la carga ficticia** de U103B (línea 54).
- Tabla de calibración por escala con signo −1.
- La dispersión del Monte Carlo en 0.5 V/div (1.74–2.23 MHz) viene de las tolerancias de la compensación del ÷100 sin ajustar el trimmer. S7b lo modela con el ajuste del trimmer.

## Reproducción

Codex no hizo reproducción propia en S7. **Reproducción de muestra de Claude (4 oct, 03:00):** `ejecutar_s7.py --quick` en una copia con ruta corta (`Temp\claudeepro_s7`): J1 en 5 mV y 0.5 V/div y J9 dan **valores idénticos bit a bit** (−3 dB 2 007 085.87 / 2 006 817.48 Hz, ganancia −49.4983 / −0.495327, 21.70 dB a 4.5 MHz, pin 1.23097 V). Sólo cambian el sufijo de los identificadores y el orden de las filas. No se reejecutó la campaña completa.

## Dudas que Codex conservó (de acuerdo)

- C_S y C_EQ derivados (1.169 nF y 8.67 pF) frente a los resúmenes: resuelto por R1 (1.2 nF), en S7b.
- G.3 cuenta un amplificador de filtro y S5 fija dos: actualizar G.3 (REVISION R3).
- Los diodos del OPA836 son supuestos; BAV99HY es de Rohm, mientras que la pieza elegida es de Nexperia.
- El ADC no tiene ruido, cuantización, jitter ni desajuste en el modelo.
