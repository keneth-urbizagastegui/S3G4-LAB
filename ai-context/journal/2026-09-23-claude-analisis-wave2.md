# Análisis del WAVE2 y corrección del modelo de ruido del divisor

- Fecha: 2026-09-23, tarde, hora local.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «haz la revisión del WAVE2», sobre `research_and_tests/Wave2`, con el mismo método que la del DSO112.

## Archivos nuevos aportados por Keneth (23 sep, 13:52–13:59)

Keneth creó la carpeta `research_and_tests/Wave2/` y movió a ella los PDF del WAVE2 que antes estaban en la raíz de `research_and_tests/`. Material nuevo:

- `wave2-main-board-schematic.pdf` (placa principal 105-15800-00G, noviembre de 2018).
- `wave2-main-board-schematic-version-j.pdf` (placa principal 00J, julio de 2019).
- `113-15801-092/113-15801-092.hex` (firmware del STM32F103).
- `Wave2_SerialInterface.pdf` (protocolo) y `WAVE2_HowToUpgradeFirmware.pdf` (actualización de firmware).
- Copia de `105-15800-00M.pdf` (placa principal 00M, noviembre de 2020), que sigue también en la raíz.

Ninguno se ha modificado.

## Cambio

- Nuevo `docs/analisis_wave2.html`, publicado en https://claude.ai/artifact/LgEYV3M8LjE8RqbTvAQMcE. Incluye dos redibujos propios (el grueso sin relé de la revisión E y la salida del generador). Pasaron el comprobador con 0 solapes y se revisaron a la vista con PyMuPDF.
- **Corrección del modelo de ruido**, aplicada con notas visibles de corrección:
  - `docs/rediseno_afe_rev21.html`, versión 7: razón de D-05, aviso de B.8 y tabla y párrafo de C.5.
  - `docs/analisis_dso112.html`, versión 2: tabla de P1.
- Especificaciones oficiales del WAVE2 obtenidas de la web del fabricante, porque los documentos locales no traen tabla de especificaciones: https://jyetech.com/wave2-2-channel-portable-oscilloscope/
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists. Ninguna propuesta aplicada.

## Corrección importante: el ruido de un divisor compensado

Hasta hoy calculé el ruido térmico de las resistencias del divisor como ruido blanco hasta 1.5 MHz. Es incorrecto. Los condensadores de compensación lo cortocircuitan por encima de la esquina R·C (≈ 17 kHz en nuestro ÷20), así que el total queda acotado por √(kT/C) de la capacidad del nodo. Lo verifiqué integrando R ∥ C con el polo del sistema.

| Divisor | R nodo | C nodo | Antes | Real |
|---|---|---|---|---|
| ÷20 de la sección B | 47.4 kΩ | 200 pF | 864 µV | **91 µV** |
| ÷100 de P1 | 9.9 kΩ | 1000 pF | 1965 µV | **202 µV** |
| WAVE2 E, rama A ÷7.67 | 235 kΩ | 28 pF | 734 µV | **93 µV** |
| WAVE2 A, ÷20.6 fijo | 48.5 kΩ | 26 pF | 896 µV | **250 µV** |

Todo referido a la entrada, con 1.5 MHz de banda.

- **Qué cambia:** «el ÷20 fijo deja la escala de 5 mV/div en el 17 %» era falso. El divisor sólo aporta el 1.8 %. Lo que pesa es que multiplica ×20 el ruido de los amplificadores y obliga a una ganancia ×1000: en total ≈ 0.32 mV rms, **≈ 6 %** de división, frente a ≈ 0.3 % con la rama ×1.
- **Tabla C.5 corregida:** 200 mV/div ≈ 0.25 % y 500 mV/div a 10 V/div ≈ 0.2 %; todas las escalas quedan entre 0.2 y 0.3 %. P1 con 500 mV/div: ≈ 0.3 %.
- **Qué no cambia:** D-05 y D-06 siguen justificadas.
- **Afecta a las cifras del diario del 22 sep** (864 µV, 197 µV para ÷2, etc.). Ese diario no se ha editado; esta nota lo corrige.

## Hallazgos del WAVE2

- **Especificaciones oficiales:** 2 canales, **200 kHz**, 1 MSa/s en tiempo real, 5 mV a 20 V/div, 50 Vpk, 1 MΩ / 25 pF, 1024 puntos. Generador de 2 canales. El protocolo lista hasta 2.5 MSa/s; no está verificado cómo se consigue.
- **Arquitectura:**
  - STM32F103CB: ADC de los dos canales en PA0 y PA1; TFT de 8 bits; microSD por SPI; USB nativo en las placas 00G y 00J; EEPROM; EXT en PB9 y TRIGOUT en PB10; entrega su reloj por MCO al otro micro.
  - STM32F100: táctil, botones y codificador; controla la placa analógica por un 74HC595 (9 líneas); genera con sus dos DAC; señal de prueba y energía.
- **Placa analógica, revisión E (oct 2018), grueso sin relé:**
  - Rama A: 1.8 M ∥ 3 p / 270 k ∥ 25 p ajustable, ÷7.67, con U1D ×7.67.
  - Rama B: 2.0 M ∥ 6 p ajustable / 20 k ∥ 510 p, ÷101, con seguidor U1C.
  - Un 74HC4053 conmuta las salidas ya bufferizadas; un chip sirve a los dos canales.
  - Después: ×2, escalera de 601 Ω con las tomas 1…1/40 del DSO112, 74HC4051, ×8 y +1.67 V fijos.
  - Todo con TL084. Zin 1.02 MΩ. Sin clamps: ninguna rama deja pasar más que microamperios.
- **Placa analógica, revisión A (oct 2019), simplificada:**
  - Un solo divisor fijo ÷20.6 (1 M ∥ 1 p / 51 k ∥ 25 p ajustable), buffer y escalera de 1019 Ω (1/5, 1/20, 1/100).
  - Etapas de ×4.92 y ×4; 74HC4051 con una entrada a masa; etapa final ×4.11 y +1.67 V.
  - **Sólo 6 ganancias de hardware, separadas ×5.** Coinciden con la Tabla 5 del protocolo: 3.93 / 0.98 / 0.20 / 0.039 / 0.0096 / 0.0020 frente a 4 / 1 / 0.2 / 0.04 / 0.01 / 0.002. Las otras seis escalas salen por software.
  - **20 mV por división en el ADC** (≈ 25 códigos): la posición vertical es digital.
- **Generador:** DAC del F100 → R 470 Ω + C 20 nF a un GPIO (filtro de 16.9 kHz que se conecta o no) → TL082 ×2 → 100 Ω. El offset lo fija un GPIO a través de 10 kΩ, así que sólo tiene dos niveles. Rango: 0–20 kHz, 0–3 Vpk, cuatro formas de onda, fase entre canales.
- **Alimentación y masas:**
  - Elevador AX5511 y MC34063 inversor (−7 V).
  - **Cada riel de cada canal con su propia bobina de 100 µH + 10 µF.**
  - **AGND1 y AGND2 unidas por resistencias de 0 Ω.**
  - **Un BL8060-3.3 sólo para VDDA.**
  - Módulos de interruptor (JYE117) y cargador LTC4054 (JYE118).
- **Evolución de la placa principal:**
  - 00G → 00J: añade EEPROM y diodos ESD en las líneas del táctil.
  - 00J → 00M: integra el cargador en la placa y pasa de USB nativo a CH340N.
- **Firmware** `113-15801-092.hex`:
  - 98 816 B, STM32F103CB, biblioteca Standard Peripheral, perro guardián IWDG.
  - Busca un ATSHA204A (antíclonado, no aparece en los esquemáticos), con activación por PID.
  - Otros textos: «1.65V for Ext. Trigger».
- **Actualización:** se usa el bootloader de fábrica del STM32 con BOOT0 y BOOT1 y la aplicación de ST, por UART.
- **Protocolo:** modo texto («nombre = valor», «?», pasos ++/--) y modo binario.

## Propuestas nuevas (ninguna aplicada)

- **P7 · Grueso sin relé, estilo WAVE2 E.**
  - Rama fina ÷2 (1 M / 1 M, 10 p / 10 p) y rama gruesa ÷200 (1.99 M / 10 k), cada una con su buffer FET. Un 74HC4053 para los tres canales. Escalera del DSO112 y ganancia fija ×100.
  - Ruido: 42 µV (0.8 %) a 5 mV/div y 3.1 mV (0.6 %) a 500 mV/div, frente a 0.3 % y 0.3 % con relé.
  - Sobrevive a la red en **todas** las escalas (0.35 mA, 0.12 W).
  - Coste: un amplificador más por canal (~30 mW), 2 ajustables por canal.
  - Limitación: en escalas gruesas, por encima de ±11.2 V en la BNC la rama fina recorta y la entrada efectiva baja a 820 kΩ con 20 V y a 735 kΩ con 40 V; con sonda ×10 hay deformación por encima de ±112 V en la punta.
  - Recomendado simularlo en LTspice antes de decidir entre P7 y P4.
- **Offset digital para la sección E.** Opción a estudiar. Si 8 divisiones ocupan 1.0 V hay 205 códigos por división y ±6 divisiones de margen; con 0.5 V, 102 códigos y ±16 divisiones, sin circuito de offset.
- **Adoptar** para las secciones F y G: filtro LC por riel y por canal, masas por canal con 0 Ω y regulador aparte para VDDA.
- **Estudiar:** disparo externo y TRIGOUT, filtro de reconstrucción conmutado por GPIO para el AWG, y reprogramación del STM32 desde el ESP32 por el bootloader de fábrica (comprobar BOOT0 y NRST en el mapa firmado).

## Pruebas

Todo es análisis documental y cálculo; no hay hardware. Los dibujos se verificaron con el comprobador geométrico y a la vista, pero la página HTML completa no se revisó a la vista. No se desensambló el código ARM del firmware, sólo cadenas y cabecera, así que el método de disparo interno del WAVE2 no está verificado.

## Pendientes

1. Keneth decide entre P4 (relé) y P7 (sin relé). Antes conviene simular P7.
2. Decidir sobre P1 (÷100); P7 lo incluye en su planteamiento (÷200 en la rama gruesa).
3. Siguen abiertos los pendientes de los diarios del 22 y 23 sep.
