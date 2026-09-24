# Análisis exhaustivo de black_scope

- Fecha: 2026-09-23, tarde (≈ 17:00–18:00 hora local).
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «revisar `research_and_tests/black_scope` exhaustivamente como hemos hecho con los demás referentes, con su artefacto».

## Cambio

- Nuevo `docs/analisis_black_scope.html`, publicado en https://claude.ai/artifact/EQGpdo9q4Fu2EkwqAgykAn. Lleva un redibujo propio del canal 1 completo (divisor → LMV324 → OPAMP1 en PGA → ADC1, con la polarización común desde DAC2). El dibujo pasó el comprobador y se revisó a la vista.
- Generadores nuevos en `docs/rediseno_afe_gen/`:
  - `calc_black_scope.py`: todas las cifras derivadas.
  - `draw_black_scope.py`.
  - `build_black_scope.py`.
  - `chk_b.py`.
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists. Ninguna propuesta aplicada.

## Fuentes y método

- Clon de https://github.com/jgpeiro/black_scope. `black_scope_1` es el mismo clon con cambios locales en `wavegen.c/.h`.
- Esquemático KiCad 7.0.6 de una hoja: `hardware/black_scope/outputs/pdf/black_scope.pdf`, con texto extraíble; se renderizó la zona analógica.
- Netlist `black_scope.xml` (84 componentes, 137 redes) y BOM del 17 ago 2023.
- Firmware leído: `.ioc`, `adc.c`, `opamp.c`, `dac.c`, `stm32g4xx_it.c`, `Lib/Scope`, `Lib/Tasks`, `Lib/WaveGen` y `Lib/Ui`.
  - Versión Nuklear y versión LVGL.
  - Prototipo `test_nucleo_f401re`.
  - `firmware_15_sep.hex`: imagen de 512 KB, sin información nueva.
- Imágenes `capture engine.png` y `capture engine 2.png`.
- Las cifras del G473 se contrastaron con DS12712 Rev 5 y RM0440 Rev 9; ver `2026-09-23-claude-g473-analogico.md`.

## Hallazgos

- **Canal (×4):**
  - R5 8k2 en serie hasta un nodo con R11 2k7 a +3.3VA, R12 4k3 a masa y C23 100 pF. Después, un seguidor LMV324.
  - Función de transferencia: Vn = 0.16824·Vin + 1.6861 V. Zin = 9.86 kΩ hacia 2.03 V. Polo de 1.15 MHz.
  - Rango −10.0 … +9.6 V, que queda en +4.8 V si el LMV324 es el de TI (modo común hasta VCC − 0.8 V; dato típico, no está en el repo).
  - Con la entrada al aire lee +2.03 V.
  - Con resistencias del 0.5 %, el cero se desalinea ±8.25 mV en el nodo, que son ±49 mV en la entrada.
- **Salida del seguidor:** va a dos pines.
  - VINP de un OPAMP interno: PA7, PB0, PB14, PB13.
  - Un pin de ADC lento (ruta directa, sin usar): PB12, PB1, PD11, PD12.
- **PGA interno:** OPAMP1, 3, 5 y 6 en PGA con VINM0 como polarización.
  - Vout = G·(VINP − VB) + VB, con G de 2 a 64.
  - El ADC lo lee por el canal interno: VOPAMP1/ADC1, VOPAMP3/ADC3, VOPAMP6/ADC4, VOPAMP5/ADC5.
  - Ancho de banda GBW/G: 109–203 kHz a ×64.
  - Modo normal, sin alta velocidad: 3.2 Vpp limpio sólo hasta 249–647 kHz.
- **ADC:**
  - PCLK/4 = 42.5 MHz, síncrono. Muestreo de 2.5 ciclos = 58.8 ns.
  - DS12712 T.75 exige ≥ 200 ns para leer el OPAMP por el canal interno.
  - Con 12.5 ciclos, el máximo real sería 1.70 MSa/s; la interfaz ofrece 2.5 MSa/s.
- **Offset:** DAC2 con buffer alimenta los cuatro VINM0, con R25 10 kΩ y C22 100 nF.
  - C22 es 2000 veces la carga máxima con buffer (50 pF, T.69).
  - Un solo offset para cuatro canales: a ×64 el desalineo llega a ±528 mV en el ADC.
  - Cada canal inyecta en VB (VINP − VB)/10 kΩ: 82.5 µA a ×2 con el ADC a fondo.
- **Captura:** DMA circular de 512 muestras y ×4 ADC con TIM2.
  - Espera un búfer lleno antes de armar.
  - AWD1 arma y AWD2 (8 bits) dispara; la ISR arranca TIM3 en un solo pulso.
  - En la parada, TIM3_IRQHandler lee CNDTR; la posición del disparo se supone len/2 antes.
  - Dos juegos de búfer alternos.
  - **Sólo CH1 puede disparar.**
  - La versión Nuklear desborda el prescaler por debajo de 1.297 kSa/s; la versión LVGL lo corrige.
- **Generador:** DAC1 con TIM4/TIM6 y DMA, 512 puntos, a un LMV358 y 51 Ω.
  - Límite limpio: 1953 Hz (1 MSa/s).
  - A 10 kHz sale 10 376 Hz (+3.76 %) y el DAC actualiza a 5.3 MSa/s, fuera de especificación.
- **Protección:** sólo R5 (0603) frente a los diodos del LMV324.
  - 50 V: 0.26 W en R5.
  - 325 V: 12.6 W.
  - La corriente se inyecta en +3.3VA, que sale de un XC6206 que no absorbe corriente.
- **Ratiométrico:** VREF+ = +3.3VA a través de L2/C8, el mismo riel del divisor y del DAC2. Confirma P9.
- **Notas del autor en el esquemático:**
  - «Change OPAMP ADC and DAC IC with bigger BW», con OPA4322/OPA2322.
  - «Add capacitors to ADC channels» y «Fix ADC noise issues».
  - «Add pull-down / capacitor to DAC2-OUT1».
  - «Add battery measurement».
- **Hipótesis (sin medir) para el ruido del ADC:** el muestreo de 59 ns sobre el OPAMP y el buffer del DAC2 con 100 nF.

## Propuesta nueva (continúa P1–P11; no aplicada)

- **P12 · Cadena de disparo por hardware:**
  - La fuente es un COMP o un AWD, que entra por la ETR de un temporizador (RM0440 T.268 y T.292).
  - El temporizador cuenta en un solo pulso las muestras posteriores al disparo.
  - Al terminar, bloquea en modo puerta el temporizador de muestreo.
  - La posición del disparo sale exacta y no depende de la latencia. **Estudiar.**

## Pruebas

Análisis documental y cálculo (`python calc_black_scope.py`); no hay hardware. El comprobador del dibujo dio 0 incidencias. La página se revisó en texto en el navegador interno, no a la vista completa.

## Pendientes

1. P12 junto con P11, en el firmware de disparo.
2. Nada de black_scope cambia la elección P4/P7.
