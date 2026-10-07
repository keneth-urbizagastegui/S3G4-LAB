# R8 Martin + R4 EEWorld 77845 (7 oct 2026, Claude Opus 5.5)

La sesión se cortó por límite de uso con el registro a medias. Al retomarla se cerraron los pendientes 1–5 de abajo: índices, plan, STATE, diario de retomada, commit y sincronización.

## Hecho

- `S3G4_LAB_rev2.1/02_referencias/dmm_martin.html` → https://claude.ai/artifact/R3vvm1wXKejCDjdHz8xVFR (referencia 6 de 9).
- `S3G4_LAB_rev2.1/02_referencias/dmm_eeworld77845.html` → https://claude.ai/artifact/JMeU9V49kriNvnQjgBTxeg (7 de 9, ficha corta).
- Scripts: `herramientas/calc_dmm_martin.py`, `draw_dmm_martin.py` (0 solapes), `build_dmm_martin.py` y `build_dmm_eeworld77845.py`.
- Martin, rev 1.5: STM32F373 con dos ΣΔ de 16 bits sincronizados; divisor de 1 MΩ con patas de 15/150 kΩ a COM; COM a VREF/2 = 0.9 V; derivadores de 50 + 5 mΩ en serie con un conmutador de toma y un INA199.
  - Las ganancias de tensión calibradas salen entre −3.1 % y −3.9 % de lo nominal, lo que confirma el fondo de ±0.9 V.
  - Las de corriente no cuadran con ninguna variante del INA199 (NO VERIFICADO).
  - Cruce V→I: 2.6–2.8 % del fondo con 60 V (Ron típico de 6 Ω).
  - Error del RMS: 4.2 mV con la entrada en cortocircuito en el rango de 60 mV, y +23 % con 10 mV.
- EEWorld 77845: sin esquema; no está en OSHWHub. STM32F103 con SAR de 12 bits, ≈ 1 % medido. El MAX4080 es solo de lado alto (modo común de 4.5 a 76 V).
- **Sin propuestas nuevas.** Refuerza P17, P19, P21, P27, P29, P20 y P26.

## Pendiente (siguiente sesión)

1. Añadir las dos filas a `S3G4_LAB_rev2.1/ARTEFACTOS.md` y las líneas a `herramientas/LEEME.md`.
2. Marcar los pasos de R8 y R4 como hechos en `06_plan/PLAN_REFERENCIAS_DMM.md`.
3. Poner al día `STATE.md` y el diario de retomada (7 de 9; lo siguiente es R5 Analog Devices).
4. Añadir a los riesgos del diario de retomada el aislamiento de Martin, que solo vale para datos (al cargar, un conmutador une las masas).
5. Hacer commit y push, y ejecutar `node tools/ai-context/context.mjs sync`.
