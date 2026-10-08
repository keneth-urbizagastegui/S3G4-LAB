# Auditoría de Claude — S12d (cierre del bloque 2 del DMM)

8 oct 2026. Claude (Opus), auditoría corta. Criterio de Keneth (DECISIONS, 8 oct): «que funcione con margen», sin perseguir decimales; los fallos marginales se clasifican. Material: PLAN_SIMULACION_S12d, ACTA_S12d, `ejecutar_s12d.py`, `analizar_s12d.py`, `comun/dmm_bloque2d.inc`, `resultados/s12d_*`, diario de Codex y AUDITORIA_CLAUDE_S12c. No se modificó ningún archivo de Codex ni STATE/DECISIONS/modelos/hojas.

Scripts: `chequeo_claude/s12d/` (`comparar_smoke.py`, `rawlt.py`, `verificar_raw.py`).

## 1. Reproducción del smoke

Copia de los scripts en `C:\s12d\r\a\sim\DMM` (hace falta esa profundidad porque `ejecutar_s11_2.py` usa `HERE.parents[2]`), con `S3G4_MODELS` apuntando a `Simulation_LTSpice/models` del proyecto y LTspice local `-b`.

- `--smoke --workers 7`: 7/7 ok en 92.7 s (E2 1, E3 3, E5 2, E8 1).
- Con `comparar_smoke.py` frente a `s12d_smoke.csv` de Codex: mismos 7 identificadores y **diferencia relativa 0 en todas las columnas numéricas**, sin contar los tiempos. Reproducción exacta.

## 2. E2: qué hay en las 4.44 cuentas

`s12d_dc_budget.csv`, rango de 200 mV (1 cuenta = 10 µV en X0; en 20 V se obtiene lo mismo referido a X2):

| Término | Cuentas | Origen |
|---|---:|---|
| Fuga de entrada del buffer, 0.6 nA a 23 °C ×2/10 °C, sobre 109 kΩ | 2.71 | Deriva a 28 °C: 0.6·(√2−1) = 0.25 nA × 109 kΩ = 27 µV |
| Fuga ON del mux, ±0.4 µA a 25 °C ×2/10 °C, sobre ≈ 71 Ω | 1.02 | Deriva de la fuga ON, de hoja, sobre la Ron |
| Deriva de Vos (0.5 µV/°C × 5 °C, SOIC) | 0.50 | Típica de hoja, con signo de peor caso |
| Ib, 20 pA más | 0.09 | Reserva aparte |
| TMUX, fuga típica de 0.3 nA | 0.11 | Reserva aparte |
| **Suma lineal** | **4.44** | Frente al criterio de ≤ 4 |

El SPICE nominal (3.92) contiene los dos primeros términos y la cadena modelada. Las reservas se suman linealmente, todas con el signo más desfavorable. La calibración a 23 °C elimina el offset, así que solo cuenta la **deriva** entre 18 y 28 °C.

**¿Es razonable la cifra de 0.6 nA?** Según las hojas locales:
- OPA2192/4192 (opa2192.pdf, p. 8): Ib de ±5 pA típica y **±20 pA máxima a 25 °C**. En todo el margen de −40 a 125 °C llega a ±5 nA, un límite que en 18–28 °C no se alcanza.
- BAV199 (BAV199.pdf, p. 3): IR de **3 pA típica y 5 nA máxima a VR = 75 V y 25 °C**. En el nodo X0 el diodo de pinza solo soporta unos pocos voltios, de modo que la fuga real está en la zona de los pA. Los 5 nA son el límite de prueba a 75 V, no el punto de trabajo.
- Por tanto, 0.6 nA equivale a ≈ 30 veces la Ib máxima y a más de 100 veces la IR típica del BAV199. Es un valor de diseño que incluye, en la práctica, la **fuga superficial de la placa** (fundente o humedad sobre 109 kΩ). Esa es la única fuente que puede acercarse a 0.6 nA, y la hoja no la cubre. La ley de ×2/10 °C se aplica además a todo el término, cuando a la fuga superficial no le corresponde esa ley.
- La fuga ON de 0.4 µA es el máximo de hoja; la típica del mux está en la zona de los nA. Ese término (1.02 cuentas) también es conservador.

**Peso frente a la especificación (D5 y H §8).** El presupuesto de H §8 tras calibrar suma la INL ≈ 10 (linealizada), la deriva de fuga ≤ 4, la deriva de Ib < 1, el ruido 0.2 y los offsets < 1:
- En la especificación **garantizada ±(0.1 % + 40)**, 4.44 en lugar de 4 no cambia nada: el margen es de ≈ 25 cuentas.
- En la especificación **calibrada ±(0.1 % + 10)**, lo que manda es la INL (≈ 10 por sí sola). Con suma cuadrática, √(10² + 4.44² + 1²) ≈ 11.0, frente a ≈ 10.8 con 4 cuentas. La diferencia de 0.44 cuentas apenas mueve el total. Que la columna calibrada sea ajustada se debe a la INL del ADC5 (D1/P26), no al bloque 2.

**Clasificación:** el exceso es un **margen de criterio y presupuesto, no un riesgo real para la especificación**. Coincido con Codex en que no está demostrado «con margen» para ≥ 95 % de las placas. La causa es que el término dominante (2.71) es un supuesto sin respaldo de hoja, no que algo falle. Aun así, la cifra cumple ≤ 4 si la fuga real en X0 es ≤ 0.50 nA a 23 °C, que es lo que da el propio análisis de Codex.

## 3. E3, E5 y E8 comprobados en el .raw

`verificar_raw.py` lee los .raw de mi smoke sin pasar por los `.meas` de Codex:

- **E3 con 20 V en el rango de 20 V** (`e3_d4f8…`, ×10.1): a 21.1 ms y a 24 ms, V(out) = 2.01794 V y V(x2) = 0.1998 V. El valor nominal es 20 × 0.00999 × 10.1 = 2.01798 V, así que el error es ≈ −0.4 cuentas, como en el CSV (−0.41). Cumple.
- **E3 con −50 V en el rango de 200 mV** (`e3_2036…`, sobrecarga): máx|V(mux)| = 4.897 V, por debajo de 4.95 V. La conducción ESD en IN+ es de ≈ 20 pA en ambos buffers. El interruptor S4 de xbuf0 conduce 40 µA a partir de 1 ms; corresponde a IN− (realimentación con la salida saturada) y queda por debajo de 50 µA. Cumple, aunque esa cifra de 40 µA es la que da E3 su margen mínimo (20 %).
- **E5, ×1 con Ron de 400 Ω** (`e5_2e54…`): T = −V(inv)/V(test) da cruce en 8.153 MHz y **PM = 43.6°**, idéntico al acta. Cumple ≥ 40° con un margen escaso pero suficiente. Las otras configuraciones están entre 49° y 64°.
- **E8 con −4 kV ESD** (`e8_b199…`): máx|I(Dlo)| de xbpin0 = 83 µA; los demás diodos están por debajo de 10 pA. El criterio es ≤ 5 mA y el peor estado de la campaña es 0.461 mA. Cumple con mucho margen, dentro del modelo de IV reducido (Vf 0.5 V, 1 Ω), que es un supuesto declarado.

## 4. Veredicto

**El bloque 2 queda cerrado en simulación.** E3, E5 y E8 cumplen y se reproducen. E2 es marginal solo en el criterio: 3.92 en el nominal y 4.44 con la suma lineal de reservas conservadoras. Su efecto sobre D5 es despreciable porque la columna calibrada la fija la INL. No hace falta cambiar piezas ni volver a simular.

**Condiciones para el prototipo:**
1. **Fuga en X0 y en la entrada del buffer X2:** con la entrada en abierto o en 10 kΩ, medir la deriva de offset entre 18 y 28 °C en los rangos de 200 mV y 20 V. Debe ser ≤ 4 cuentas, lo que equivale a ≤ 0.5 nA a 23 °C. Si no se cumple, la primera medida es limpiar el fundente o aplicar guarda o anillo en X0, no cambiar piezas.
2. Placa limpia (sin restos de fundente) en los nodos de 109 kΩ.
3. Verificar en banco el PM de ×1 (43.6° en modelo): respuesta a un escalón sin sobreoscilación excesiva.

Tiempo de la auditoría: smoke de 93 s y análisis de pocos minutos.
