# Síntesis de las 9 referencias del DMM (7 oct 2026, Claude Opus 5.5)

Paso 8 de `S3G4_LAB_rev2.1/06_plan/PLAN_REFERENCIAS_DMM.md`.

## Pedido y criterio de Keneth

Keneth rechazó medir en banco la INL del ADC5 y la fuga del 74HC4051:
- su placa del G473 es una WeAct, con VDDA/VSSA unidos a la alimentación digital y VREF+ a VDDA;
- y la placa final llevará otro chip.

Pidió la síntesis con su criterio:
- estudiar y simular para dejar margen, y calibrar por software al fabricar;
- especificaciones algo holgadas pero profesionales;
- bajo coste y pocos componentes, sin sesgarse por el TIDA ni por el osciloscopio.

Registrado en `DECISIONS.md` (7 oct) y en la memoria `criterio-tolerancias-keneth` y `banco-hardware-s3g4`.

## Cambio

- Página nueva `S3G4_LAB_rev2.1/01_diseno/dmm_sintesis.html` → https://claude.ai/artifact/FzUFdinBfx7Yf3mbvAnsy4.
- Scripts `herramientas/calc_dmm_sintesis.py`, `draw_dmm_sintesis.py` (diagrama de bloques, 0 solapes) y `build_dmm_sintesis.py`. Reutilizan `calc_dmm_adi.py` y `calc_dmm_34401a.py`.
- Actualizados `ARTEFACTOS.md`, `herramientas/LEEME.md`, el plan (paso 8), STATE, `DECISIONS.md`, el diario de retomada y la memoria.

## Contenido y hallazgos

- La arquitectura de la sección H se mantiene. Coincide con lo que repiten los buenos diseños: entrada de 10 MΩ, conmutadores en baja tensión y en el lado de sentido, deriva cero con autocero, ADC con buffer, ohmios ratiométricos y valor eficaz por firmware.
- **Hallazgo nuevo** (calc_dmm_sintesis.py): la PTC «de pocos kΩ» de H §6, en serie con R_ref, deja el rango de 200 Ω en 1.96 mA y en el 20 % de la ventana, en lugar de 9.78 mA y el 98 %. Con P42 (≈ 1 V de caída) queda en 7.8 mA y el 78 %. La prueba de un LED de 3 V necesita una R_ref de 1 kΩ con P42 (0.9 mA).
- **Fuga del mux referida a la entrada:** ≈ 10 cuentas por nA en 200 mV y en 20 V, y ≈ 1 en 2 V y en 50 V. Con calibración de offset por rango, solo queda la deriva (+41 % con +5 °C). Tolerancia de ≈ 1 nA, a confirmar en S11.
- **Veredicto P17–P42:**
  - 7 de hardware (P18, P20, P22, P25, P27, P31, P42);
  - 11 de firmware o documento;
  - ya en H: P19, P24;
  - opcionales: P23 parcial, P28, P32;
  - P17 descartada (10 MΩ de fuente en 200 mV con 850 pA = 4 % del fondo);
  - P30 sustituida por P42;
  - P36 por decidir.
- **Especificación en dos niveles:**
  - sin linealizar: ±(0.1 % + 40) DCV, ±(1 % + 40) ACV, ±(0.2 % + 40) Ω, ±(0.5 % + 40) DCI;
  - tras calibrar: +10 (+20 en alterna).
  - Condiciones: un año, 23 ± 5 °C, 60 Hz, y 0.1 × la exactitud por °C fuera de 18–28 °C.
  - Anclas: 121GW y 34401A.
- **Respaldo:** huella sin montar de un ADS1115 (LCSC C37593, 1.22 USD, INL de 1 LSB).
- **Mux de fuga garantizada:** el MAX4051A cuesta 9.50 USD en LCSC (C1546586) frente a 0.21 USD del 74HC4051D (C9386). Se mantiene el 74HC4051 si S11 tolera ≥ 1 nA.
- **Lista de S11** (9 puntos) y procedimiento de calibración al fabricar (6 pasos).

## Pruebas

- La página tiene 11 secciones, 1 SVG y 9 enlaces a las referencias, sin desbordamiento a 296 px.
- El recuento de veredictos se calcula desde la tabla, con un `assert` de 26.

## Pendientes

- Respuestas de Keneth a D1–D7.
- Después: revisar la sección H y su hoja (sin aplicar nada antes de las respuestas) y escribir el encargo S11.
