# Plan: estudio a fondo de las referencias del DMM

- Autor: Claude Code, 7 oct 2026. Pedido de Keneth: «hacer lo mismo que en el osciloscopio: investigar a fondo nuestras referencias, minuciosamente, cómo funcionan y qué usaron; un archivo por referencia; buscar más en internet; nada de módulos; planificarlo con calma».
- Modelo a seguir: las anatomías del osciloscopio (`02_referencias/analisis_dso112.html`, `analisis_wave2.html`, `analisis_openscope.html`, `analisis_black_scope.html`) y su método (diario `ai-context/journal/2026-09-23-claude-analisis-dso112.md`).
- **La sección H (`01_diseno/dmm_rev21.html`) queda en pausa.** Se escribió antes de estudiar las referencias. Se revisará con lo que salga de aquí, antes de encargar la simulación S11.

## 1. Regla de los módulos

Diseñamos **nuestro propio front-end** del DMM con piezas sueltas y el ADC5 del G473, igual que el TIDA-01012 construye el suyo alrededor de un ADC.

Cuando una referencia use un módulo (placa Arduino o Feather, sensor Hall tipo ACS712, placa ADC aislada, módulo de radio), se documenta **qué función cumple y cómo se haría en discreto**, pero no se adopta. Los circuitos integrados (ADC, referencia, amplificador, ASIC de DMM) sí se estudian; adoptarlos es otra decisión.

## 2. Método por referencia (el mismo del osciloscopio)

1. **Inventario de fuentes:** qué archivos hay y qué versión es la buena. Una referencia con muchas variantes, como Micro-DMM, se reduce a la placa que manda.
2. **Esquemático leído por zonas:**
   - los PDF se renderizan con PyMuPDF a 250–330 ppp;
   - los `.kicad_sch` se exportan con `kicad-cli` a PDF o SVG;
   - de cada pieza se anotan el valor, el MPN y su función.
3. **Redibujo de los bloques clave** en SVG con `herramientas/sch.py`: entrada V, ohmios, corriente y ADC. Cada dibujo pasa el comprobador de solapes y se revisa a la vista.
4. **Cálculos propios** en `herramientas/calc_dmm_<ref>.py`:
   - relaciones del divisor;
   - corriente y potencia de la protección con 50 Vrms y con 230 Vrms;
   - corriente de prueba en ohmios;
   - caída en corriente (burden);
   - valor de una cuenta;
   - presupuesto de errores.

   Cada cifra lleva su fuente: página, figura o pieza.
5. **Firmware**, si existe: selección de rango, autocero, calibración, verdadero valor eficaz, cable abierto y continuidad.
6. **Manual o especificación**, contrastado con lo que de verdad hace el circuito.
7. **Página HTML**, generada con `herramientas/build_dmm_<ref>.py` y el CSS de las anatomías. Secciones fijas:
   - Lo que nos llevamos (tabla) · Qué se analizó y cómo · Arquitectura (bloques)
   - Entrada de tensión: divisor, protección y selección · Ohmios, diodo y continuidad · Corriente: derivador, fusible y protección
   - Rango y ganancia · ADC y referencia · Alterna y verdadero valor eficaz · Firmware · Alimentación
   - Seguridad: qué aguanta y qué no · Lo que no conviene copiar · Módulos que usa y su equivalente discreto
   - Propuestas para la rev 2.1 · Comparación con nuestra sección H · Correcciones a lo dicho antes
8. **Cierre de cada estudio:**
   - artefacto privado y su línea en `ARTEFACTOS.md`;
   - diario en `ai-context/journal/` y apunte en `STATE.md`;
   - sincronizar la memoria.

   **Ninguna propuesta se aplica sin que Keneth la acepte.**
9. **Numeración de propuestas:** sigue la global, de **P17 en adelante** (P1–P16 son del osciloscopio y del G473).

Archivos: `02_referencias/dmm_<referencia>.html`, uno por referencia.

## 3. Referencias

### En la carpeta `research_and_tests/` (las aportó Keneth)

| # | Referencia | Qué hay | Por qué importa | Módulos |
|---|---|---|---|---|
| R1 | **TI TIDA-01012** (`TIDA-01012/`) | Guía de diseño (75 p) y esquemático (6 p) | El más parecido a nuestra sección H: divisor de 10 MΩ con conmutadores detrás, driver diferencial THS4531 con VCM, OPA333 de deriva cero, REF3325 y verdadero valor eficaz por firmware. 4½ dígitos, 50 000 cuentas | Ninguno |
| R2 | **HydraMeter 0.4** (`HydraMeter_0.4/`) | KiCad (6 hojas: Volt, Ohm, Amp, PGA_ADC, Input, MCU), PDF, código de la placa analógica y del display, bitácora de hackaday | Todo en discreto y abierto: secciones V, Ω y A separadas, PGA + ADC, COM a media alimentación, derivador de 4 terminales, protecciones | La Raspberry Pi Pico como MCU (no afecta al front-end) |
| R3 | **Micro-DMM** (`Micro-DMM/`, 399 MB) | Unas 35 variantes de placa, firmware Arduino, LTspice/QSpice, *white paper* de cable abierto, hojas de datos | **Detección de cable abierto** (nuestro RD-09), ohmios bajos de precisión, ADS1115/ADS1256 | Sí: placas Arduino/Feather/XIAO, sensor Hall ACS712, placas ADC aisladas. Se estudia la placa **DMM_KiCAD_V4_next** más **OpenLead_Headless_V3** y el *white paper*; los módulos solo se documentan |
| R4 | **STM32 Digital Multimeter**, EEWorld 77845 (web) | Solo texto, diagrama de bloques y fotos. **No hay esquemático** (los archivos son un vídeo y un `.axf`) | Usa el ADC interno de un STM32F1, como nosotros: LM324 como atenuador, amplificador y seguidor; CD4052 para el rango; MAX4080 y relés para los derivadores; MOSFET para el divisor de ohmios; calibración por ajuste lineal. ≈ 1 % medido | No se sabe sin esquemático. Ficha corta, salvo que aparezca el proyecto original en OSHWHub |
| R5 | **Analog Devices, «7.5-Digit Accuracy», partes 1 y 2** (`Analog_/`) | Dos artículos (7 + 8 p) | No es un diseño: es la **teoría de errores** de un DMM de precisión (referencia, ADC, divisor, ruido, temperatura). Sirve para revisar nuestro presupuesto de la sección H §8 | — |

### Propuestas nuevas, encontradas en internet

| # | Referencia | Qué hay | Por qué importa | Módulos |
|---|---|---|---|---|
| R6 | **TI TIDA-00879** (ti.com/tool/TIDA-00879) | Guía TIDUBM4, esquemático TIDRMI4, BOM, Gerber | DMM de 4½ dígitos (60 000 cuentas) con el **ADC integrado del MCU** (MSP430F6736, ΣΔ de 24 bits) y front-end discreto; verdadero valor eficaz por firmware. Es el caso «ADC del micro + front-end propio» | Ninguno |
| R7 | **EEVblog 121GW** (eevblog.com/product/121gw) | Esquemático completo publicado y manual | La **protección de un DMM de verdad**: fusible HRC, TVS, PTC, MOV y puente de diodos; red de rangos y fuente de ohmios con PTC. Usa un ASIC de DMM (HY3131), que no adoptaremos | Ninguno (el BLE no se usa) |
| R8 | **Open Source Multimeter de Martin** (EmbedBlog; clonado en `research_and_tests/Martin_STM32_multimeter/`, rev 1.5 con STM32F373 y su ADC ΣΔ de 16 bits) | EAGLE (`hardware/v15.sch`), PNG del esquema, BOM, firmware y calibración | STM32F1 con su ADC interno, conmutación electrónica de rango, ±60 V / ±6 V, mA, componentes y RMS por unos 10 USD. Lo más cercano a nosotros en microcontrolador | Por verificar |

Descartadas de entrada: TIDA-010970 (ADC de 24 bits de alta gama, fuera de nuestro coste) y los manuales de servicio de DMM de banco (Keysight 34401A). Se pueden añadir si hacen falta para un detalle.

## 4. Orden y ritmo

Una referencia por sesión, con calma. Al terminar cada una, Keneth la revisa antes de pasar a la siguiente.

| Paso | Estudio | Por qué en este orden |
|---|---|---|
| 1 | R1 TIDA-01012 — **hecho el 7 oct** (`02_referencias/dmm_tida01012.html`, propuestas P17–P22) | Fija el vocabulario y es la base de la sección H |
| 2 | R2 HydraMeter — **hecho el 7 oct** (`02_referencias/dmm_hydrameter.html`, P23–P27) | Todo discreto y abierto: el contraste directo con R1 |
| 3 | R6 TIDA-00879 — **hecho el 7 oct** (`02_referencias/dmm_tida00879.html`, P28–P29) | ADC del micro con front-end propio, nuestro caso |
| 4 | R7 121GW — **hecho el 7 oct** (`02_referencias/dmm_121gw.html`, P30–P32) | Protección y seguridad, que aún es lo más flojo de nuestro diseño |
| 5 | R3 Micro-DMM — **hecho el 7 oct** (`02_referencias/dmm_microdmm.html`, P33–P34) | Cable abierto (RD-09) y ohmios bajos |
| 6 | R8 Martin + R4 EEWorld — **hechos el 7 oct** (`02_referencias/dmm_martin.html` y `dmm_eeworld77845.html`, ficha corta; sin propuestas nuevas) | Los dos con ADC de STM32: el límite inferior de lo que se logra |
| 7 | R5 Analog Devices — **hecho el 7 oct** (`02_referencias/dmm_adi_errores.html`, P35–P37) | Teoría para cerrar el presupuesto de errores |
| 8 | **Síntesis** | Comparación de todas las referencias con la sección H, lista de propuestas P17+ para que decida Keneth y revisión de la sección H. Después, el encargo S11 |

## 5. Lo que necesito de Keneth antes de empezar

1. **Permiso para descargar** a `research_and_tests/`:
   - TIDA-00879: guía, esquemático y BOM de ti.com, unos 2 MB en PDF;
   - el esquemático del 121GW, PDF de eevblog.com;
   - el repositorio de Martin, cuando se localice.
2. Si se incluyen las tres referencias nuevas (R6–R8) o solo las cinco de la carpeta.
3. Si vale el orden de la tabla.

## 6. Riesgos conocidos

- **Micro-DMM** es enorme y está muy ramificado: hay que elegir bien la placa que manda o se pierde el tiempo.
- **R4 (EEWorld)** no tiene esquemático: puede quedar en una ficha corta.
- Las cifras de cada referencia salen de su documentación. Si el esquemático contradice al texto, manda el esquemático y se dice, como pasó con el DSO112.
- La sección H puede cambiar bastante tras la síntesis. Es lo esperado: es la razón de hacer este estudio.

## 7. Enlaces de EEWorld que añadió Keneth el 7 oct (evaluados)

Los archivos de EEWorld solo se bajan con una cuenta iniciada. Claude no crea cuentas ni inicia sesión: si hacen falta, los baja Keneth.

| Enlace | Qué es | Valor para nuestro DMM | Propuesta |
|---|---|---|---|
| [95152](https://en.eeworld.com.cn/Reference_Designs/detail/95152) | Proyecto de estudiante: resistencia por divisor con 1 kΩ, inductancia por oscilador LC con LM393, frecuencia con LM393 y tensión pico a pico con rectificador de media onda de precisión; reconoce la forma de onda por el factor de cresta. Sobre una Raspberry Pi Pico (módulo). Esquema en PDF, Altium/PADS y BOM, pero detrás de la cuenta | Bajo: no tiene rangos de tensión DC ni corriente, el ohmímetro es de un solo rango y la propia página admite errores de más de 100 mV en alterna por encima de 10 kHz | Ficha corta (R10), solo si Keneth baja el PDF del esquema; si no, descartar |
| [57000](https://en.eeworld.com.cn/Reference_Designs/detail/57000) | El Open Source Multimeter de Martin (STM32F1 → F3) | Es **R8**, ya clonado de GitHub (`research_and_tests/Martin_STM32_multimeter/`) | Nada nuevo: se estudia como R8 |
| [57006](https://en.eeworld.com.cn/Reference_Designs/detail/57006) | Manual de servicio del **Agilent 34401A** (34401-90013), DMM de banco de 6½ dígitos, con los esquemas en el apéndice | Alto como **escuela de front-end profesional**: protección de entrada, divisor de alta tensión, fuente de corriente de ohmios, autocero, conmutación de rangos y convertidor de alterna. Su ADC multipendiente es propio y no se copia | Añadir como **R9**, antes de la síntesis. El manual es público en keysight.com; bajarlo de ahí con permiso de Keneth |

Orden actualizado: … 6 · R8 Martin + R4 EEWorld 77845 · 7 · R5 Analog Devices · **7b · R9 Agilent 34401A** · 8 · Síntesis.

**7b hecho el 7 oct** (`02_referencias/dmm_34401a.html`, P38–P42). Las nueve referencias están estudiadas.

**Paso 8, síntesis, publicada el 7 oct** (`01_diseno/dmm_sintesis.html`): arquitectura recomendada, veredicto P17–P42, especificación en dos niveles (sin linealizar y tras calibrar) y siete decisiones D1–D7 para Keneth. Con sus respuestas: revisar la sección H y su hoja, y escribir el encargo S11. Las medidas en banco de P36/P37 pasan al prototipo (DECISIONS, 7 oct).

**Paso 9, revisión de la sección H, hecha el 7 oct:** Keneth aceptó D1–D7, con D1 sin huella del ADS1115. `01_diseno/dmm_rev21.html` y `00_requisitos/especificaciones_dmm.html` revisadas y republicadas. Queda pendiente la propuesta P43 (fuente de corriente de ohmios, D8). Después, el encargo S11.
