# Auditoría de Claude — S7b de CH1 (±4.9 V, C_S 1.2 nF, tolerancias reales)

- Auditor: Claude Code, 4 oct 2026.
- Ejecución:
  - Codex escribió el script el 3 oct y se quedó sin cupo.
  - Claude lanzó con ese script la prueba rápida, que se atascó por convergencia en K2DC.
  - Codex, reanudado a las 00:01, reparó la convergencia sin cambiar el circuito (barrido punto a punto, tiempo límite y reintentos) y ejecutó la campaña: código 0, **4 416 / 4 416 casos**, 10 496 ejecuciones, 115 min acumulados; 36 intentos fallidos, todos recuperados; 0 errores finales.

## Veredicto

**CH1 funciona en ≥ 95 % de las placas en todo, salvo el rango del trimmer**, que basta en el **83.2 %**. Es un problema de **ajuste en fabricación, no de prestaciones**: el canal sigue funcionando en las placas fuera de rango, pero con la compensación del ÷100 ligeramente desajustada (§2).

| Criterio (≥ 95 % de placas) | Resultado |
|---|---|
| C1: −3 dB en 2.0 MHz ± 15 % | **100 %** (p2.5–p97.5: 1.89–2.13 MHz) |
| C2: pico ≤ 1 dB | **100 %** (máx. 0.24 dB) |
| C3: ruido ≤ 0.5 % div | **100 %** (0.31–0.34 %) |
| C4: ganancia ±5 % antes de calibrar | **100 %** (−47.8 … −51.0 en 5 mV/div) |
| **C5: el trimmer de 2–6 pF basta** | **83.2 %** (necesario de 0.9 a 7.8 pF; p2.5–p97.5: 1.5–7.1 pF) |
| C6: protecciones con rieles de 4.80 / 5.00 V | **100 %** (diferencial máxima 0.92 V; pin del ADC de 0.007 a 3.29 V; 4051 con 9.95 V como máximo y señal 0.11 V dentro de sus rieles) |
| C7: recuperación ≤ 1 µs | **100 %** (≤ 0.67 µs) |
| C8: offset compensable con ±4.5 div restantes | **96.8–97.6 %** por escala; 96.2 % en las cuatro a la vez |

Con ±4.9 V y C_S = 1.2 nF, el canal nominal es igual que en S7: 2.007 MHz, 182 ns, 0.25–0.32 % y 21.7 dB a 4.5 MHz.

## 1. Comprobaciones de Claude

- Valores (`comun/ch1_comun_s7b.inc`): rieles ±4.9 V, C_S = 1.2 nF y C_EQ = 8.7 pF. El resto es igual que en S7.
- La reparación de la convergencia **no cambia el circuito**: reparte el barrido de V_DAC en puntos `.op` con tiempo límite y reintento. Por eso hay más de 8 000 decks `j1dc`.
- Semilla fija (2026100371); placas emparejadas en las cuatro escalas.
- **Reproducción de muestra de Claude (4 oct, 03:00):** `ejecutar_s7b.py --smoke` en una copia con ruta corta (`Temp\claudeepro_s7`), con K1, K3, K2 (placas de muestra), ruido, K2DC y consumo: **15/15 CSV con los mismos valores** que la prueba rápida de Codex (diferencia relativa máxima de 7·10⁻¹⁶). El código 1 sale de la comprobación de ficheros protegidos, no de la simulación. No se reejecutó la campaña de 2 h.

## 2. El trimmer: diagnóstico y propuestas

**Por qué se queda corto.** El trimmer está en paralelo con *una* de las dos mitades del condensador superior del ÷100 (C1B ∥ trimmer, en serie con C1A). Cada pF del trimmer mueve ≈ ¼ de pF la capacidad total de arriba, así que sus 4 pF de recorrido equivalen a ≈ 1 pF efectivo. Con condensadores al ±5 %, sobre todo **Cb ≈ 1.09 nF**, la necesidad se reparte entre 0.9 y 7.8 pF. **La mediana (4.06 pF) ya está en el centro**: mover el condensador fijo no ayuda.

**Qué hay en LCSC (4 oct):** SEHWA STC3MA06, 2–6 pF, 100 V, 0.49 USD, 4 501 ud (el actual); Knowles JZ300, 5.5–30 pF, 125 V, 4.44 USD, 123 ud; Knowles JZ060, 2–6 pF, 4.00 USD, 75 ud. No hay ninguno de 3–10 pF con stock.

| Opción | Qué es | Cobertura estimada | Coste |
|---|---|---|---|
| **A (recomendada)** | Condensadores del divisor más precisos: **Cb (1 nF + 68 pF) al ±1 %** y **C1A/C1B/C1B fijo al ±2 %** (C0G), **y** un hueco sin montar (DNP) de 0603 en paralelo con C1B para 0.5–2.2 pF de ajuste grueso en las pocas placas que se salgan | Cálculo simplificado de Claude: ≈ 92 % sólo con las tolerancias; con el hueco DNP, ≈ 100 % | Céntimos por pieza más un hueco |
| B | Trimmer Knowles JZ300 (5.5–30 pF) con C1B fijo más pequeño | ≈ 100 % | +4 USD por canal; stock bajo (123) |
| C | Trimmer en paralelo con **todo** el condensador de arriba (sensibilidad 1:1) | ≈ 100 % | Vería ≈ 99 V con 100 V de entrada, al 99 % de los 100 V del SEHWA: incumple el margen ≤ 80 % |
| D | Aceptar el 83 % y seleccionar Cb en prueba en las placas fuera de rango | 100 % con trabajo manual | Tiempo de montaje |

Con la opción A conviene un S7c corto: sólo el Monte Carlo del trimmer con las tolerancias nuevas, en minutos.

## 3. Para Keneth

1. Elegir la opción del trimmer (recomendada: **A**).
2. Reproducción de muestra pendiente (Claude).
3. Luego: actualizar el documento vivo (C.6 con C_S, C_EQ y las tolerancias; nuevas secciones D, E y F; G.3 con el consumo y los rieles de ±4.9 V) y pasar a CH2/CH3 (S9) o al esquema (S8).
