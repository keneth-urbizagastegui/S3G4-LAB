# Análisis exhaustivo del OpenScope MZ

- Fecha: 2026-09-23, noche, hora local.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «haz la revisión del OpenScope completa y exhaustiva», antes de simular P4 o P7.

## Cambio

- Nuevo `docs/analisis_openscope.html`, publicado en https://claude.ai/artifact/8KbSKL4sWnYoQzPJgKsRwf. Lleva un redibujo propio del canal analógico, verificado con el comprobador y revisado a la vista.
- `docs/analisis_dso112.html`, versión 3: se completó la columna del OpenScope en la comparativa (ancho de banda, protección y disparo).
- Generadores copiados en `docs/rediseno_afe_gen/`: `draw_openscope.py`, `build_openscope.py` y `chk_o.py`.
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists. Ninguna propuesta aplicada.

## Fuentes y método

- `research_and_tests/openscope-mz/openscope-mz-sch-revg.pdf`, revisión G, 12 hojas. Su texto no se puede extraer y **nunca se había leído**; se renderizó con PyMuPDF.
- El firmware es un clon del repositorio de Digilent (C/C++, Arduino/PIC32). Se leyeron `AnalogIn.c`, `Trigger.c`, `AWG.c`, `DCInstruments.c`, `FeedBack.c`, `LA.c`, `Config.cpp`, `WiFi.cpp`, `OpenScope.h` y `MfgTest.cpp`.
- Aplicación `research_and_tests/waveforms-live`, versión 1.4.10 (Ionic 2 / Angular 2).
- Adaptador de terceros: `OpenScopeMZ-Adapter_Schema.pdf` y `openscope-Adapter.zip`.
- Especificaciones del manual de referencia publicado en Farnell (https://www.farnell.com/datasheets/2339652.pdf), procesado en memoria sin guardarlo en disco. digilent.com devuelve 403 a las descargas automáticas.

## Hallazgos

- **Especificaciones:**
  - Osciloscopio: 2 canales, 12 bits, 6.25 MSa/s, 2 MHz a −3 dB, 1 MΩ, ±20 V, 32 640 muestras.
  - Generador: 10 bits, 1 Hz–1 MHz, 3 Vpp ±1.5 V, 10 mA.
  - Fuentes DC ±4 V / 50 mA; analizador lógico de 10 canales a 10 MSa/s; WiFi 802.11g; USB.
  - Alimentación **sólo por USB**, sin batería.
- **Canal analógico (hojas 4 y 5):**
  - IC5A (LMV116 a ±5 V): inversor con R31 de 1 MΩ hacia su tierra virtual y R30 de 200 kΩ ∥ 0.3 pF, ganancia −0.2. Zin = 1 MΩ.
  - IC6A (LMV116 **a 3.3 V**): sumador inversor referido a VREF1V5 = 1.5 V. Recibe la señal por R32 3.6 kΩ (puenteada por 33 pF), VREF3V0 por 3.41 kΩ y el offset por R2Sx.
  - **Un TS3A5017** (dos multiplexores 4:1 de 3.3 V) elige la realimentación, **en la tierra virtual**: 18 kΩ, 4.53 kΩ ∥ 22 pF, 2.26 kΩ ∥ 51 pF y 1.33 kΩ ∥ 91 pF. Salen las ganancias 1, 1/4, 1/8 y 3/40 (R_f = 5·G·3.6 kΩ − 10 Ω) y, por los condensadores, **polos de filtro anti-alias en 1.60, 1.38 y 1.32 MHz**.
  - La otra mitad del TS3A5017 elige la resistencia del offset (10 k / 2.4 k / 1.37 k / 1.02 k), así que el offset escala con la ganancia.
  - La salida va por R35 68 Ω / C31 470 pF **a dos pines del ADC** (entrelazado); rango de 0–3 V.
  - **Sin acoplo AC en hardware.**
- **Ruido:** R31 y R30 dan 315 nV/√Hz referidos a la entrada, **≈ 0.56 mV rms con 2 MHz**. Es el 11 % de una división a 5 mV/div y el 0.19 % a 300 mV/div, su escala nativa. El canal sólo atenúa. **Conclusión: no cambia la decisión entre P4 y P7.**
- **Protección:** no tiene protección dedicada, pero R31 de 1 MΩ hacia la tierra virtual limita la corriente a 0.35 mA con 353 V. El límite real es la tensión que aguanta la resistencia.
- **Referencias (hoja 12):** un LM4040 de 3.000 V es la VREF+ del ADC. De él salen VREF3V0 (buffer) y VREF1V5 (divisor al 0.1 % + buffer): **diseño ratiométrico**. Regulador NCP1117 de 3.3 V y bomba de carga LM2660 para −5 V.
- **Realimentación (hoja 11):** divisores del 0.1 % llevan al ADC 3.3 V, ±5 V, VREF3V0, VREF1V5, la salida del generador y las dos fuentes DC.
- **Autocalibración (firmware):**
  1. Fuentes DC a ±3 V, medidas por la realimentación.
  2. Generador: offset, y después los **1024 códigos de la escalera R-2R**, que se ordenan en una tabla de corrección.
  3. Osciloscopio, por cada una de las 4 ganancias: fuente DC a +V y −V con un **cable del usuario** hacia la entrada (con detección de cable no conectado), barrido del PWM de offset y cero. Modelo Vin = A·código + B·PWM + C.
  - Las medidas usan el sobremuestreo por hardware del ADC. Se guarda como archivo en un FAT de la flash interna, y en microSD si la hay. La aplicación tiene una página de calibración guiada.
- **Generador (hoja 6):** escalera R-2R de 10 bits en el puerto H, DMA hasta 10 MSa/s, búfer de hasta 25 000 muestras, dos RC de reconstrucción y un MCP6H91 inversor a ±5 V con offset por PWM (OC7).
- **Fuentes DC (hoja 7):** PWM → dos RC 1 kΩ / 4.7 µF → MCP6H82 inversor ×4.
- **Captura y disparo:**
  - Dos ADC dedicados por canal, con disparo por temporizador y comparación desfasada, y dos DMA. Pasa a un solo ADC por debajo de ~2 kSa/s.
  - **Disparo con los dos comparadores digitales del ADC** (uno arma, otro dispara), es decir histéresis; después refina el punto recorriendo el búfer.
  - PWM de offset a 303 kHz, 330 pasos, con **500 ms** de asentamiento.
  - Analizador lógico por DMA desde el puerto E.
- **Protocolo:** JSON por objetos (device, osc, awg, dc, la, trigger, file, log, gpio, mode, test), con binario en transferencia fragmentada, por HTTP en el puerto 80 (WiFi) o por serie USB (FT232RQ). La prueba de fabricación usa el mismo JSON.
- **Adaptador de terceros** (C. Feyer, 2021): añade BNC, acoplo AC/DC (100 nF + 27 MΩ con puente), disparo por BNC, adaptadores de nivel a 5 V, ±12 V y un amplificador para el generador.

## Propuestas nuevas (continúan P1–P7; ninguna aplicada)

- **P8 · Etapa final única por canal**, estilo IC6A. Un sumador inversor alimentado como el ADC que haga ganancia fija, anti-alias de primer orden, desplazamiento a mitad de escala y offset a la vez, y proteja el ADC. Hay que verificar si un filtro de primer orden basta para CH2 y CH3 a 3.47 MSa/s (sección D). **Decidir.**
- **P9 · Referencia única y ratiométrica:** la referencia del ADC genera la mitad de escala con un divisor al 0.1 % y un buffer. **Adoptar** en la sección F.
- **P10 · Autocalibración encadenada:**
  - Red de realimentación al 0.1 % hacia canales lentos del ADC (salida del AWG, rieles y referencias).
  - El AWG en modo DC como fuente, con un cable del usuario y detección.
  - P3 (masa y VCHECK) para la parte interna.
  - Modelo A·código + B·offset + C por escala, guardado en flash, con pantalla guiada en la S3G4-UI.
  - Requiere pines de ADC libres: revisar el mapa firmado. **Adoptar.**
- **P11 · Disparo con los analog watchdog del G4** (dos umbrales) como alternativa o complemento del COMP + DAC del mapa firmado. **Estudiar** en firmware.

## Corrección

- En la revisión de la carpeta del 22 sep dije que el OpenScope «no tiene protección». Matiz: no tiene protección dedicada, pero su megaohmio hacia la tierra virtual limita la corriente; lo que falla es el aislamiento de una sola resistencia.

## Pruebas

Análisis documental y cálculo; no hay hardware. El dibujo pasó el comprobador y se revisó a la vista; la página completa no se revisó a la vista. La hoja 8–9 (puertos del PIC32) sólo se miró en miniatura.

## Pendientes

1. Decidir P4 o P7 después de simular; el OpenScope no cambia esa elección.
2. Decidir P1, P4, P7 y P8; adoptar formalmente P9 y P10 cuando Keneth lo confirme.
3. Para P10: comprobar pines libres de ADC en `docs/MAPA_PINES_FIRMADO.md`.
