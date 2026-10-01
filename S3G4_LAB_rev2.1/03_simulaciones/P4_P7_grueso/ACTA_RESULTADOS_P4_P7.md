# Acta de resultados — atenuador grueso P4 frente a P7 (rev. 2.1)

- Fecha: 2026-09-23
- Constructor y ejecutor: Codex
- Simulador: LTspice 26.0.2, modo lote `-b`
- Orden ejecutado: T01–T07 para P4 y P7 (14 esquemas)
- Resultado de `python ejecutar_todo.py`: **código 0**
- Simulaciones con error: **0**; advertencias: **0**
- Modelos de diodo: aproximaciones `DBAV199` y `DTVS5` entregadas en el plan. No son modelos de fabricante.

Esta acta mide y describe. No elige ni recomienda P4 o P7.

## Resumen por ensayo

| Ensayo | P4 con relé | P7 sin relé | Qué enseña |
|---|---|---|---|
| T01 | 0.9089/0.9991 MΩ y 21.832/13.878 pF (×1/÷100) | 0.9998 MΩ y 18.609 pF en ambas selecciones | P4 cambia de impedancia y capacidad al conmutar; P7 las conserva en este modelo. |
| T02 | Error de ganancia peor −1.190 %; planitud peor 9.419 %; pérdida peor a 1.5 MHz 0.142 dB; pico 0.794 dB | Error peor −0.199 %; planitud peor 14.881 %; pérdida 1.429 dB; pico 3.203 dB | Las escalas gruesas P4 y finas P7 muestran realce/variación fuera de C4. |
| T03 | Error a 2 µs: 0.366 % (5 mV/div), 15.826 % (500 mV/div) | 22.276 % y 0.091 % | La compensación nominal no satisface simultáneamente las dos trayectorias en ninguno de los diseños. |
| T04 | 15.54 µV, 468.44 µV, 1533.04 µV | 44.52 µV, 906.04 µV, 3573.66 µV | Ambos quedan por debajo de 1 % de división; no hay discrepancias mayores del 30 % frente a la referencia. |
| T05 | Con 50 Ω/40 V: 0.0000 % THD, 999.01 kΩ | Con 50 Ω/40 V: 0.0154 % THD, 738.57 kΩ | En P7 la rodilla se manifiesta principalmente como caída de impedancia; con sonda ×10 también aparece THD ≈4.35 % a 200/400 V en punta. |
| T06 | En red: clamp 3.48 mA peor; entrada hasta ±6.09 V | Clamp fino 0.342 mA; entrada fina hasta ±5.966 V, gruesa ±1.768 V | Las corrientes de clamp cumplen 100 mA, pero las entradas exceden ±5.5 V con este modelo y fallan C8/C9. |
| T07 | 200 corridas AC: `g100` 0.49989115–0.49989165; proxy 9.5756 % | `g100` 0.49986859–0.49986909; proxy 44.507–44.570 % | Resultado informativo limitado; véase la duda D5. |

## T02 — detalle por escala

| Diseño | Escala | Ganancia 100 Hz | Error | Planitud 10 Hz–100 kHz | Pérdida 1.5 MHz | Pico | f−3 dB |
|---|---:|---:|---:|---:|---:|---:|---:|
| P4 | 5 mV/div | 49.4889 | −1.022 % | 0.197 % | 0.141 dB | 0.000 dB | 8.035 MHz |
| P4 | 200 mV/div | 1.23512 | −1.190 % | 0.197 % | 0.142 dB | 0.000 dB | 7.947 MHz |
| P4 | 500 mV/div | 0.499891 | −0.022 % | 9.419 % | −0.677 dB | 0.794 dB | 9.538 MHz |
| P4 | 5 V/div | 0.0499542 | −0.092 % | 9.419 % | −0.672 dB | 0.794 dB | 9.257 MHz |
| P7 | 5 mV/div | 49.9855 | −0.029 % | 14.881 % | 1.429 dB | 0.000 dB | 4.690 MHz |
| P7 | 200 mV/div | 1.24752 | −0.199 % | 14.841 % | 1.428 dB | 0.000 dB | 4.651 MHz |
| P7 | 500 mV/div | 0.499869 | −0.026 % | 0.083 % | −0.482 dB | 3.203 dB | 29.517 MHz |
| P7 | 5 V/div | 0.0499519 | −0.096 % | 0.083 % | −0.477 dB | 3.075 dB | 26.192 MHz |

Una pérdida negativa significa ganancia respecto a 100 Hz. El criterio de pico recoge ese realce.

## T03 — error de escalón

| Diseño | Escala | 2 µs | 20 µs | 200 µs |
|---|---:|---:|---:|---:|
| P4 | 5 mV/div | 0.366 % | 0.305 % | 0.045 % |
| P4 | 500 mV/div | 15.826 % | 2.580 % | 0.0002 % |
| P7 | 5 mV/div | 22.276 % | 4.671 % | 0.000 % |
| P7 | 500 mV/div | 0.091 % | 0.019 % | 0.000 % |

## T04 — ruido y contraste con el cálculo manual

| Diseño | Escala | Simulado referido a entrada | % división | Referencia | Diferencia |
|---|---:|---:|---:|---:|---:|
| P4 | 5 mV/div | 15.54 µV rms | 0.311 % | 15 µV | +3.6 % |
| P4 | 200 mV/div | 0.468 mV rms | 0.234 % | 0.43 mV | +8.9 % |
| P4 | 500 mV/div | 1.533 mV rms | 0.307 % | 1.5 mV | +2.2 % |
| P7 | 5 mV/div | 44.52 µV rms | 0.890 % | 42 µV | +6.0 % |
| P7 | 200 mV/div | 0.906 mV rms | 0.453 % | 0.86 mV | +5.4 % |
| P7 | 500 mV/div | 3.574 mV rms | 0.715 % | 3.1 mV | +15.3 % |

**Discrepancias mayores del 30 %: ninguna.** Por ello no se hizo un ajuste ni se atribuyó una fuente dominante para corregir cifras.

## T05 — señales grandes y rodilla

| Diseño/fuente | Pico nominal BNC | Pico BNC medido | Zin efectiva | THD SAL | Pico SAL |
|---|---:|---:|---:|---:|---:|
| P4, 50 Ω | 11 V | 10.999 V | 999.01 kΩ | 0.0000 % | 0.550 V |
| P4, 50 Ω | 40 V | 39.998 V | 999.01 kΩ | 0.0000 % | 1.999 V |
| P7, 50 Ω | 11 V | 10.999 V | 999.00 kΩ | 0.0083 % | 0.549 V |
| P7, 50 Ω | 20 V | 19.999 V | 825.82 kΩ | 0.0170 % | 0.999 V |
| P7, 50 Ω | 40 V | 39.997 V | 738.57 kΩ | 0.0154 % | 1.998 V |
| P7, sonda ×10 | 112 V punta | 11.201 V | 999.62 kΩ | 0.0991 % | 0.560 V |
| P7, sonda ×10 | 200 V punta | 17.432 V | 858.91 kΩ | 4.3716 % | 0.871 V |
| P7, sonda ×10 | 400 V punta | 31.323 V | 764.27 kΩ | 4.3457 % | 1.565 V |

Las 12 combinaciones por diseño están en `resultados/resultados.csv` y en los logs. La rodilla P7 aparece alrededor del punto previsto como aumento de corriente por la rama fina protegida, aunque la salida seleccionada sea la rama gruesa.

## T06 — supervivencia, potencia y energía

En 50 V continuos, la potencia por cada resistencia superior fue como máximo 0.83 mW en P4 y 0.65/0.41 mW en RtF/RtG de P7. La rama P2-base de P4 llegó a 19.38 mW; su variante P2-AT reparte aproximadamente 9.69 mW y 22.01 V por cada 1206. Estas potencias están bajo el 60 % nominal, pero el criterio completo falla por la excursión de entrada de amplificador.

Para 250 Vrms, último ciclo:

| Diseño/posición | Elemento físico | V pico | P media | Energía extrapolada a 10 s |
|---|---|---:|---:|---:|
| P4 ×1 | cada Rt 330 kΩ | 116.67 V | 20.625 mW | 0.206 J |
| P4 ×1 | Rs P2-base 100 kΩ | 347.46 V | 598.0 mW | 5.980 J |
| P4 ×1 | cada Rs P2-AT 49.9 kΩ | 173.73 V | 299.0 mW | 2.990 J |
| P4 ÷100 | cada Rt 330 kΩ | 116.67 V | 20.625 mW | 0.206 J |
| P7 | cada RtF (tres piezas) | 115.86 V | 19.952 mW | 0.200 J |
| P7 | cada RtG (tres piezas) | 117.26 V | 10.365 mW | 0.104 J |

Según el contrato, estas sobrecargas de 10 s se informan y no se juzgan. El contacto abierto P4 ve aproximadamente 350 V pico en reposo ÷100. La rama gruesa P7 llega a 1.768 V pico; la comprobación solicitada de que permanece en torno a 1.8 V se reproduce.

## Criterios C1–C9

| Criterio | P4: valor medido | P4 | P7: valor medido | P7 |
|---|---|---|---|---|
| C1 | 0.9089/0.9991 MΩ | FALLA | 0.9998/0.9998 MΩ | PASA |
| C2 | 21.832/13.878 pF; Δ 7.954 pF | FALLA | 18.609/18.609 pF; Δ 0 | PASA |
| C3 | error peor −1.190 % | FALLA | error peor −0.199 % | PASA |
| C4 | 9.419 %; 0.142 dB; pico 0.794 dB | FALLA | 14.881 %; 1.429 dB; pico 3.203 dB | FALLA |
| C5 | error peor 15.826 % | FALLA | error peor 22.276 % | FALLA |
| C6 | peor 0.311 % división | PASA | peor 0.890 % división | PASA |
| C7 | 0.0000 % THD; 999.01 kΩ | PASA | 0.0154 % THD; 738.57 kΩ | FALLA |
| C8 | potencia/tensión resistiva DC conformes; entrada 5.98 V | FALLA | potencias/tensiones conformes; entrada 5.86 V | FALLA |
| C9 | clamp 3.48 mA; entrada 6.09 V | FALLA | clamp 0.342 mA; entrada 5.97 V | FALLA |

## Dudas, contradicciones y limitaciones sin resolver

1. **P4 ×1 no presenta 1 MΩ.** La rama de 100 kΩ, el `R_BIAS` de 10 MΩ y la rama ÷100 quedan simultáneamente conectadas a la BNC y el modelo da 0.9089 MΩ. Se informa; no se cambió ningún valor.
2. **La igualdad de capacidad P4 no se reproduce.** Se midieron 21.832 pF y 13.878 pF pese a calcular `Cb` con la expresión del plan. No se retocó `Cb`.
3. **T02 muestra realce en las ramas compensadas.** Por eso hay pérdidas negativas a 1.5 MHz y picos de 0.794 dB (P4) y 3.203 dB (P7). Se conserva el resultado sin ajustar compensación.
4. **Serie física P7.** El esquema usa 1.99 MΩ exactos como ordena el plan; tres resistencias de 665 kΩ suman 1.995 MΩ (diferencia +0.251 %).
5. **T07 es parcial.** Se ejecutaron 200 corridas y se registraron extremos AC, pero el esquema actual sólo hace variar de forma efectiva fuente/CBNC; `WC` no se aplica a todos los condensadores y `WR` no se aplica a todos los resistores. Además `step2us_proxy` es un indicador AC, no una repetición transitoria de T03. Por tanto T07 no permite todavía decidir ajustables ni atribuir el peor caso a un único parámetro. Falta completar esa parte del contrato.
6. **Fuente de sonda.** El plan enumera 11 V en BNC y 112 V en punta; el caso de sonda se implementó literalmente con 112 V en punta (11.2 V ideal antes de carga), de modo que no es idéntico al caso de 11 V de las otras fuentes.
7. **Criterio de entrada de amplificador.** Los clamps entregados permiten aproximadamente ±5.9…6.1 V con raíles ±5 V; el límite C8/C9 es ±5.5 V. El fallo procede del modelo/umbral indicado, no de una convergencia de LTspice.

## Evidencia reproducible

- Medidas primitivas y evaluaciones: `resultados/resultados.csv`.
- Resumen generado: `resultados/resumen.md`.
- Cada `.log` queda junto a su `.asc`.
- El script retorna distinto de cero ante un error de LTspice o una medida fallida, pero no por criterios fallidos.
