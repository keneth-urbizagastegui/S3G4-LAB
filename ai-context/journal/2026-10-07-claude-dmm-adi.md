# R5 Analog Devices: método de presupuesto de errores (7 oct 2026, Claude Opus 5.5)

Referencia 8 de 9 del estudio del DMM. Sesión retomada tras el corte por límite de uso; antes se cerraron los pendientes de R8/R4 (commit 595f048).

## Cambio

- Página nueva `S3G4_LAB_rev2.1/02_referencias/dmm_adi_errores.html` → https://claude.ai/artifact/LsJG4aZhYxcP8A2SGfAiZN.
- Scripts `herramientas/calc_dmm_adi.py` (reproduce las cifras de ADI y rehace el presupuesto de H) y `build_dmm_adi.py`. Sin redibujos: no es un circuito.
- Actualizados `ARTEFACTOS.md`, `herramientas/LEEME.md`, la fila 7 del plan, STATE y el diario de retomada.

## Evidencia

- Artículos de D. Guo y O. Liu (ADI, 2024), partes 1 (7 p) y 2 (8 p), en `research_and_tests/Analog_/`.
- Se reproducen todas sus cifras:
  - offset 0.20 ppm/°C, que da ≈ 1 ppm a 24 h; ganancia 0.54 ppm/°C, que da 0.56 ppm a 24 h;
  - con ±5 °C, 1.35 y 2.72 ppm;
  - deriva a un año: factor de Arrhenius de 1.81, 3.1 ppm del LT5400 y 13.5 ppm de la ADR1001.
- La ecuación (1) de la parte 1 está impresa con el signo cambiado: con ella sale 0.55.
- **DS12712 Rev 5, tabla 63** (p. 138), ADC diferencial: INL de 2.1 LSB típica y 3.2 máx. (4.1 en otras condiciones, tablas 64–65); DNL de 1.6 máx.; ENOB de 10.9. Con un LSB diferencial de 1.221 mV y una cuenta de 100 µV, la INL son 26 / 39 / 50 cuentas.
- **ti.com:** REF33, 30 ppm/°C máx. y 0.15 % inicial (la deriva a largo plazo no está en la página); OPA2188, Vos de 25 µV máx. e Ib de 850 pA máx.

## Resultado

- Ganancia (23 ± 5 °C, patrón del 0.05 % supuesto): 579 ppm en 2 V y 630 ppm en 200 mV y 20 V. Cabe en el 0.1 % y deja ≈ 780 ppm para la deriva anual. No hace falta una red apareada.
- Offset: 26–28 cuentas típicas y 39–41 máximas, según el rango. El ruido con ×1024 queda en 0.23 cuentas: manda la INL.
- Especificación honesta con el ADC5 tal cual: ±(0.1 % + 30) típica y ±(0.1 % + 40) en el peor caso a 25 °C.

## Propuestas (sin aplicar)

- **P35** Presupuesto con el método de ADI.
- **P36** Medir la INL del ADC5 y elegir: +40 cuentas, linealización o ΣΔ externo.
- **P37** Los cuatro ensayos de ADI: ruido, INL, coeficiente de temperatura y estabilidad.

## Correcciones registradas

- **H §8:** la INL no es «≈ 0.06 % del fondo cubierto por 10 cuentas».
- **H §2:** 160 pA es la Ib típica del OPA2188; la máxima es de 850 pA.

## Pruebas

- `calc_dmm_adi.py` reproduce las cifras de ADI.
- La página tiene 9 secciones, sin desbordamiento.

## Pendientes

- R9 Agilent 34401A; luego la síntesis.
- La medida de la INL del ADC5 (P36) se puede hacer ya en la placa del G473 si Keneth lo decide.
- Falta la deriva a largo plazo de la REF3325 (hoja completa).
