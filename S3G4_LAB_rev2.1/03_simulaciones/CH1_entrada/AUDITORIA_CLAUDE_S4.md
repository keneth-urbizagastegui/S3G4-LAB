# Auditoría de Claude — S4 de CH1 (etapa final a 3.3 V con offset, OPA836)

- Auditor: Claude Code, 3 oct 2026. Ejecutó Codex (gpt-6.1-sol, medium) de 17:15 a 18:34.
- **Codex se detuvo por el límite de uso de la cuenta de ChatGPT**, después de terminar la campaña: 199 simulaciones, código 0, sin errores, `ACTA_S4.md` y `resultados/s4_*`. Faltan su respuesta final, su diario y su reproducción.
- Comprobaciones propias en `chequeo_claude/s4/`.

## Veredicto

**S4 cumple con C_F = 1 pF, siempre que se respete una regla de secuencia de encendido.**

| Criterio | Acta | Auditoría |
|---|---|---|
| S4-C1 ganancia, linealidad y offset | FALLA | **Pasa.** Ganancia −0.999997. La no linealidad que da el acta (3–7 % en la zona «lineal», 53 % en el barrido completo) es un error de cálculo: con 21 puntos por ajuste de V_DAC, el residuo es < 1 µV en toda la zona de 0.2 a 3.1 V (`chequeo_claude/s4/s4_lineal.cir`). Offset de **+5.21 / −4.85 div**: abajo lo limita la salida, que no baja de unos 20 mV (§3) |
| S4-C2 pin del ADC entre 0 y VDDA | FALLA | **Pasa en funcionamiento (F1):** 0.004–3.29 V con ±5 V a la entrada. **Falla sólo en F7**, con ±5 V presentes y VDDA apagado o subiendo: hasta ±0.49 V en el pin. Se evita con secuencia (§2) |
| S4-C3 entradas del OPA836 | FALLA | **Pasa en F1:** con los diodos de modelado, diferencial ≤ 0.69 V y corriente ≤ 0.28 mA (límite 0.43 mA). Sin diodos, la diferencial llega a 1.52 V con 16 µA: el modelo de TI no los trae. El «exceso de VS ± 0.7 V» sólo aparece en F7 |
| S4-C4 respuesta en frecuencia | C0 falla, C1 pasa | **C1 (C_F = 1 pF) pasa:** S4 sola pierde 0.08 dB a 2 MHz y no tiene pico. C0 tiene +1.5 dB de pico. De la BNC al pin del ADC, 0.76 dB a 2 MHz, de los que 0.65 dB son el RC del ADC (previsto en C.4) |
| S4-C5 recuperación | Pasa | **Pasa:** ≤ 0.23 µs |
| S4-C6 interferencia por VMID | M1 informado, M2 pasa | **Pasan las dos.** M2: 1·10⁻⁷ div en CH2. M1: VMID se mueve ≤ 1.7 mV (≈ 0.02 div en la propia salida) y no afecta a los otros canales, porque cada uno tiene su divisor |
| S4-C7 THD | FALLA | **Pasa:** 0.006 % con offset 0. El 10 % aparece con offset de −2 div **más** 8 div de señal, que lleva la traza 6 div por debajo del centro y la recorta contra 0 V. **El caso estaba mal planteado en el plan**; con offset +2 div la THD también es 0.006 % |
| S4-C8 ruido total de CH1 | Pasa | **Pasa:** 0.38 % en las 12 escalas, con S4 incluida |

## 1. Lo que comprobé

- Ecuación medida: V_ADC = 2.7856 − 0.999997·V_in − 1.2407·V_DAC. Coincide con la de diseño (§2 del plan: 3.241·VMID − V_in − 1.241·V_DAC; centro de 1.2347 V frente a 1.2313 V de cálculo; la diferencia es la corriente de polarización del OPA836 en el divisor).
- Revisé que los extremos de F1 y F7 se miden en el pin del ADC y con V_DAC en sus extremos.
- Releí las corrientes del CSV: son ≤ 0.28 mA en todos los casos de F1 y F7. Una primera lectura mía de varios mA era un error al recortar el exponente.

## 2. Secuencia de encendido (F7): regla de diseño

Si los ±5 V del AFE están presentes mientras VDDA = 0, U103B empuja el pin del ADC a ±0.49 V a través de R_IN y R_F, con el G473 sin alimentar. Eso es inyección en un pin sin tensión (P14). **No hace falta otra pieza:** basta con que el AFE no pueda encenderse antes que VDDA. La propuesta para la sección G:

- **EN+ y EN− del LM27762 con resistencia a masa y gobernados por el G473.** El AFE sólo se enciende cuando el microcontrolador ya tiene VDDA.
- Al apagar, primero EN del AFE y después el LDO de 3.3 V.
- El ±5 V del AFE no puede llegar por otro camino (por ejemplo, desde el DMM con su propio riel).

## 3. Rango de offset: −4.85 div en vez de −5

Con V_DAC = 2.3 V, el centro de la traza debería quedar en −0.07 V, pero la salida rail-to-rail del OPA836 no baja de unos 20 mV. Con offset de −5 div, el centro de la traza ya está en el borde inferior de la pantalla, así que la mitad de la señal queda fuera de todos modos. **Propuesta: aceptarlo** y documentar RF-14 como ±5 div por arriba y −4.85 div por abajo. Otra opción es subir el centro unos 40 mV moviendo VMID, a cambio de perder 0.16 div por arriba.

## 4. Variante de VMID

- **M1** (un divisor de 10.0 k / 5.23 k con 1 µF por canal): suficiente. VMID se mueve ≤ 1.7 mV durante una saturación y no toca a los otros canales.
- **M2** (seguidor común con otro OPA836): también cumple, pero añade un amplificador (≈ 2.2 USD y 1 mA).
- **Recomendación: M1.**

## 5. Reproducción

Reejecución de Claude en `…\Temp\claude\s4a` con `S3G4_MODELS`: `--controls` (14 simulaciones) y la campaña completa (199 simulaciones, 0 errores, 1053 s).

- **Mismos valores en las 199:** la mayor diferencia relativa entre los 14 CSV es de 4·10⁻¹⁴ (ruido en el último dígito).
- **No son idénticos byte a byte por dos motivos ajenos a los resultados:**
  - el orden de columnas de 9 CSV: la campaña de Codex se escribió en dos tandas (`--resume`), y la mía de una vez;
  - el estado PARCIAL en vez de FALLA/PASA en `s4_criterios.csv`: mi registro estaba dentro de la carpeta copiada y el script lo detectó como fichero protegido modificado, por lo que salió con código 1.
- Codex no llegó a hacer su propia reproducción: se quedó sin cupo.

## 6. Pendientes para Keneth

1. C_F = 1 pF C0G en paralelo con R_F (recomendado).
2. VMID: M1 (recomendado) o M2.
3. Regla de secuencia del §2 en la sección G.
4. Aceptar el offset de −4.85 div (§3).
