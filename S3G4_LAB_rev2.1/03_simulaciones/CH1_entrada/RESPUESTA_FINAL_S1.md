# Entrega S1 — entrada pasiva P4b

`ejecutar_s1.py`: **código de salida 0**, 494 simulaciones, **0 errores y 0 advertencias**. Nominalmente pasan S1-C1…S1-C4; falla S1-C5. No se cambiaron valores para obtener aceptación ni se eligieron ajustables.

Ficheros creados: `comun/ch1_comun.inc`; `S1/E1_zin.cir`, `E2_respuesta.cir`, `E3_sonda.cir`, `E4_mc.cir`; `ejecutar_s1.py`; `ACTA_S1.md`; netlists y logs de cada caso en `S1/generados/`; y en `resultados/`, `s1_resultados.csv`, `s1_resumen.md`, `s1_criterios.csv`, `s1_sonda_barrido.csv`, `s1_mc_parametros.csv`, `s1_sensibilidad.csv`, `s1_mc_rangos.csv`, `s1_convergencia.csv`, `s1_ejecucion.json` y copia de la primera campaña `s1_resultados_primera.csv`. Se añade el diario autorizado en `ai-context/journal/`.

✓ pasa; ✗ falla; — no aplica. C3 muestra el error de ganancia a 1 kHz; C4 en DC muestra intervalo de desviación y pico, y en AC la frecuencia baja −3 dB. C5 muestra sobreimpulso/error a 2 µs, ambos respecto a la altura del escalón. Las ganancias y cifras completas están en el acta y los CSV.

| CT1 pF | POS | CPL | S1-C1 MΩ | S1-C2 Cin/Δ pF | S1-C3 error % | S1-C4 | S1-C5 sobre/error2 % |
|---|---|---|---|---|---|---|---|
|20|1|DC|0.999128 ✓|26.707/0.540 ✓|+0.014289 ✓|[−0.172,+0.023]%; 0.0020 dB ✓|0.000/−13.842 ✗|
|20|1|AC|1.000288 ✓|—|−0.294629 ✓|8.728 Hz ✓|—|
|20|100|DC|0.999119 ✓|27.248/0.540 ✓|+0.000234 ✓|[−0.153,+0.041]%; 0.0035 dB ✓|0.000/−14.224 ✗|
|20|100|AC|0.999120 ✓|—|−0.307578 ✓|8.803 Hz ✓|—|
|12|1|DC|0.999167 ✓|22.747/0.540 ✓|+0.014289 ✓|[−0.172,+0.023]%; 0.0020 dB ✓|0.000/−10.918 ✗|
|12|1|AC|1.000348 ✓|—|−0.294629 ✓|8.728 Hz ✓|—|
|12|100|DC|0.999159 ✓|23.287/0.540 ✓|+0.000146 ✓|[−0.128,+0.063]%; 0.0055 dB ✓|0.000/−11.315 ✗|
|12|100|AC|0.999159 ✓|—|−0.307639 ✓|8.803 Hz ✓|—|

CCOMP óptimo ensayado: **0 pF**, fijado en ÷100 y conservado en ×1 para ambas CT1. Los casos GND de E1 sólo se informan en el acta, conforme al contrato.

Las dos campañas producen CSV idénticos byte por byte: **2868 filas, 0 diferencias**. Evidencia adicional: `resultados/s1_verificacion.json`. Diario: `ai-context/journal/2026-10-02-1925-codex-s1-ch1.md`.

E4, 200 muestras reproducibles:

- Peor **ΔCin = 4.141176 pF**, muestra `mc_059`, CT1 = 12 pF, DC. En sensibilidad individual domina **CIN_BUF**: su extremo de 3 pF produce ΔCin = 2.501160 pF, desplazamiento de +1.960860 pF frente al nominal.
- Peor **desviación a 1 MHz = −8.677442 %**, muestra `mc_095`, POS100, CT1 = 12 pF, DC. En sensibilidad individual domina **COFF_RELE**: su extremo de 0.5 pF produce −6.980300 %, desplazamiento de −6.997415 puntos porcentuales frente al nominal.
- Los peores casos Monte Carlo combinan múltiples variaciones: no se atribuyen a una sola pieza. Los parámetros anteriores son los dominantes del ensayo de uno en uno. La tabla completa está en `s1_sensibilidad.csv` y el acta.

Dudas registradas, sin resolver:

1. C_SEL_EST usa CJO a cero voltios; los diodos del circuito están polarizados inversamente y tienen menor capacidad efectiva.
2. Los valores aproximados y el chequeo simplificado de la revisión no incluyen exactamente las fórmulas y todos los elementos exigidos por S1.
3. C_SEL_EST cuenta una COFF_SW; la topología tiene dos tiros abiertos, uno acoplado de vuelta a SEL a través de CAC.
4. No se especifican Ron de SW1 ni fugas resistivas; el banco explicita 0.1 Ω cerrado y 1e18 Ω abierto.
5. E3 no define rango de CCOMP, objetivo de minimización, referencia temporal ni CPL. Se documentaron esas convenciones; la sonda contractual no logra S1-C5 con ninguna CCOMP positiva ensayada.
6. E2/E4 no detallan el barrido de CT1 ni correlaciones de tolerancias; se cubrieron ambas CT1 y se documentaron las correlaciones utilizadas.
7. E4 pide decidir ajustables, pero §7 lo prohíbe. Se entregan medidas y se deja la decisión abierta.
