# 2026-09-30 — Claude Code — Coherencia del osciloscopio en el documento vivo

## Encargo

Keneth pidió revisar todo antes de empezar el esquemático de la rev 2.1 en KiCad y corregir las contradicciones, empezando por las del osciloscopio. El DMM, el AWG, los rieles y los archivos de plan quedan para la siguiente parte.

## Cambios (documento vivo `S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html`, artifact versión 11)

1. **Relé del grueso:** en C.2 (dibujo y nota), C.6 y C.7 todavía decía latching. Ahora dice monoestable con economizador (D-03, cerrado el 23 sep por la noche). La nota «latching o monoestable» se conserva como historia, con su cierre al final. También se cambió `herramientas/draw_c.py`.
2. **Líneas de control:** con monoestable hay 1 línea por relé. Quedan 12 líneas en 2 × 74HCT595, o 15 si el economizador necesita línea propia (sin definir).
3. **RF-08 en C.2:** se añade un aviso. La topología dibujada da 0.909 MΩ y ≈ 8 pF de diferencia entre escalas (auditoría P4/P7). La corrección prevista (R_BIAS delante del relé, segundo polo y por tanto DPDT, resistencia en serie antes del buffer) contradice el párrafo «Basta un relé SPDT»; se deja señalada, sin rediseñar.
4. **Ancho de banda de CH1:** C.4 solo comprobaba 1.5 MHz. Ahora incluye CH1 a 2 MHz (RF-03): −0.37 dB con amplificadores de 100 MHz de GBW y −1.0 dB con los de 50 MHz. Para CH1, el mínimo de GBW pasa a 100 MHz (también en C.6). El ruido crece ×1.15.
5. **Secciones pendientes:**
   - D decía 3.0 / 1.6 MHz de la rev 2.0; ahora sigue RF-03 y D-02, con Nyquist 3.25 y 1.73 MHz.
   - E y F se alinean con `06_plan/PLAN.md` (P6, P15, P9 y P13).
6. **B.5:** el conmutador ve hasta ±6 V (D-07), no ±2 V.
7. **B.1:** «a batería y aislado» contradecía G.7. Con el USB conectado a un PC, la masa del equipo es la tierra del PC.
8. **Preguntas ya respondidas:** la pregunta D-05 de la sección A (respondida por D-06) y el «siguiente paso» de B (hecho en B.8) quedan marcados como historia.
9. `ai-context/DECISIONS.md`: a la línea «Queda por decidir: latching o monoestable» se le añade su cierre.
10. `S3G4_LAB_rev2.1/ARTEFACTOS.md`: el documento vivo pasa a la versión 11.

## Evidencia y pruebas

- Pérdidas a 2 MHz calculadas con 1/√(1 + (f/fp)²) sobre los polos de C.4. El mismo cálculo a 1.5 MHz reproduce las cifras del documento (−0.21 dB y −0.57 dB).
- La versión publicada solo difería de la local en el envoltorio de publicación (diff), así que no se perdió contenido.

## Hoja de especificaciones (mismo día)

Keneth pidió ver cómo quedarían las especificaciones del osciloscopio en formato de fabricante. Se creó `S3G4_LAB_rev2.1/00_requisitos/especificaciones_osciloscopio.html` (artifact https://claude.ai/artifact/YMa7uusboCbYFR8hos2wGa), con el formato de la hoja del NI ELVIS II.

- Cada cifra lleva su origen: requisito (R), calculado (C), simulado (S) o pendiente (!). No hay ninguna medida.
- Cifras derivadas:
  - tiempo de subida 0.35/BW: 175 y 350 ns;
  - muestreo mínimo 16.4 Sa/s (8192 muestras en 500 s);
  - registro de 8 k: 1.26 y 2.36 ms;
  - resolución por código 0.61 mV ÷ ganancia de la escala, de 12.2 µV a 24.4 mV.
- Las 10 divisiones horizontales salen de `DIV_X = 10` en la S3G4-UI.
- Quedan sin especificar: diafonía, THD, ENOB, precisión de la base de tiempos (falta elegir el cristal), dimensiones y temperatura.

## Coherencia del DMM (mismo día)

Requisitos de `00_requisitos/requisitos_dmm_awg.html` (artifact versión 4). Las correcciones se hicieron en `herramientas/build_requisitos_dmm_awg.py` y la página se regeneró; antes se comprobó que el generador reproducía la página idéntica.

1. **RD-04 decía «60 V DC o 30 Vrms, como el ELVIS II».** La hoja del ELVIS II (`research_and_tests/NI ELVIS II Series.pdf`, p. 6) dice **60 VDC / 20 Vrms**, CAT I. El valor acordado (30 Vrms) no se cambia. Se atribuye a los umbrales de tensión no peligrosa de IEC 61010-1 (30 Vrms, 42.4 Vpk, 60 V DC); citado de memoria, la norma no está en la carpeta. Se corrigió también en la sección G del documento vivo (versión 12) y en `DECISIONS.md`.
2. **Rangos propuestos con 200 V y 600 V,** de cuando el DMM iba a medir la red. Ahora son 200 mV, 2 V, 20 V y 60 V en continua, y 200 mV, 2 V, 20 V y 30 Vrms en alterna. Los del ELVIS se añaden como referencia.
3. **RD-03 decía «sobremuestreo por hardware»,** pero el G473 solo llega a ×256 (RM §21.4.29). Con ×256 y 10.9 bits efectivos no caben las ±19 999 cuentas. Ahora: ×256 por hardware y ×4 en firmware, ×1024 en total, como hace el firmware del banco.
4. **RD-08 pedía sujeción antes de PB14 para un diodo de hasta 3.5 V.** La sujeción recortaría la lectura, porque VREF+ es 2.5 V. Se añade un divisor de ≈ ÷2.
5. **Entradas sustituidas, anotadas en `DECISIONS.md` y `STATE.md`:** DMM a 600 V, RD-04 CAT II, RD-05 con enclavamiento, RD-06 con fusible de 600 V, y el relé que «el firmware lleva a ÷20».

**Revisión de Keneth (mismo día):** el acuerdo era medir como el TIDA-01012, hasta 50 V en continua y en alterna, con los tres bornes y 2 A. A la pregunta de si son eficaces o de pico, eligió 50 Vrms.
- RD-04, los rangos propuestos, el documento vivo (D-06, sección G y G.7), `PLAN.md`, `DECISIONS.md` (entrada del 30 sep) y `STATE.md` pasan a 50 V DC / 50 Vrms.
- Se añade la consecuencia: ≈ 71 Vpk, por encima de los 50 Vpk del osciloscopio y del umbral de 30 Vrms de IEC 61010-1, lo que obliga a avisar en el panel y en el manual.

Queda para la parte del AWG: las consecuencias RG-03 («subir los rieles o aceptar ±4.5 V») y RG-01/RG-04 («por calcular») ya las resolvió la sección G con el convertidor de ±6.5 V.

## Coherencia del AWG (mismo día)

Correcciones en `herramientas/build_requisitos_dmm_awg.py`; página regenerada (artifact versión 6).

1. **RG-03:** la consecuencia decía «subir los rieles o aceptar ±4.5 V; se decide en G». La sección G ya lo resolvió con un convertidor propio de ±6.5 V, que deja 1.5 V de margen. Se añade el límite de uso |offset| + amplitud/2 ≤ 5 V, que faltaba: RG-03 permite 10 Vpp y ±5 V de offset a la vez.
2. **RG-01/RG-04:** el consumo figuraba «por calcular», pero G.3 ya lo calcula: 0.68 W con los dos canales sobre 50 Ω y 6.0 h con todo activo.
3. **RG-04, cifras añadidas:**
   - Con +15 V externos, ≈ 156 mA y 1.2 W en la resistencia de 50 Ω.
   - En cortocircuito, la salida pediría 100 mA de pico, así que los 50 mA exigen limitar la corriente. G.5 ya dimensiona el convertidor con ese límite.
   - Con el AWG apagado, la sujeción no puede descargar en un riel sin alimentar (G.6).
4. **RG-02, decisión de Keneth:** seno de 1 Hz a 1 MHz; cuadrada, triángulo y rampa con ≈ 175 ns de subida, útiles hasta 100–200 kHz. Motivo: 15 muestras por periodo a 1 MHz y un filtro de 2 MHz.
5. **RG-07, abierto por Keneth «hasta que definamos los rieles»:** a través de 50 Ω, a 50 mA caen 2.5 V. Se marca como en conflicto con RG-04.

## Coherencia de los rieles (mismo día)

`calc_rieles.py` reproduce las cifras de G.3–G.5. Por ejemplo, BUS5 = 42 + 39 × 1.3 + 56.7 + 43.2 = 193 mA. Cambios en el documento vivo (versión 14) y en `06_plan/PLAN.md`:

1. **Recuento de amplificadores.** C.7 decía 9 amplificadores y ≈ 270 mW; G.3 cuenta 13 (más el filtro de CH1 y las 3 etapas finales de P8) a 3.9 mA, ≈ 0.6 W. Anotado en los dos sitios, y en G.3 se aclara que P8 no está decidido.
2. **Inyección de las sujeciones.** C.7 decía que solo el riel negativo no absorbe corriente; en realidad es cualquiera de los dos LDO del LM27762, según la polaridad. Con el AFE encendido, los 13 mA quedan cubiertos por la carga normal (42 y 39 mA). Con el AFE apagado se aplica G.6. Añadido en G.5.
3. **Sujeción del AWG con ±15 V (abierto).** A sus rieles de ±6.5 V entrarían ≈ 156 mA por canal (312 mA las dos), frente a 10 mA de carga en reposo, y su convertidor no absorbe corriente. Tiene que ir a masa (TVS o Zener) o resolverse de otra forma. Anotado en G.5 y en el plan.
4. **G.5 y RG-04.** G.5 dimensiona el convertidor del AWG para 100 mA por riel, lo que supone limitar la corriente a 50 mA por canal; se hace explícito.
5. **Apagado del DMM (RF-18).** En G.6 faltaba la fila del DMM: comparte el LM27762 con el AFE. Queda por decidir si lleva un interruptor de carga propio (≈ 18 mW).

## Archivos desactualizados y commit (mismo día)

- `S3G4_LAB_rev2.1/06_plan/PLAN.md`:
  - fecha al 30 sep, con lo hecho hoy;
  - pasos 3, 6, 7 y 9 alineados con las correcciones;
  - KiCad: stackup, contorno, DRC, jerarquía y Konnect;
  - nuevas decisiones abiertas: RG-07 e interruptor del DMM.
- `S3G4_LAB_rev2.1/04_esquematicos/LEEME.md`: el proyecto KiCad ya existe, aunque vacío.
- `S3G4_LAB_rev2.1/LEEME.md`: su tabla ya no dice que la carpeta de esquemas está vacía, y añade la hoja de especificaciones.
- Commit local en la rama `ai/prueba-konnect`, sin push.

## Pendiente (no tocado; decisiones de Keneth o trabajo de diseño)

- **P8 sin decidir:** G.3 cuenta 10 amplificadores y la etapa final a 3.3 V (P8), mientras C.7 dice 9 amplificadores y ≈ 270 mW.
- **Corrección de P4 para RF-08** (paso 2 del plan) y el diseño de la sección D.
- **Referencias históricas:** el análisis del DSO112 sigue mostrando P4 como «Decidir»; no se regenera.
- **Siguiente parte:** contradicciones del DMM, del AWG y de los rieles, y archivos desactualizados (`04_esquematicos/LEEME.md`, `06_plan/PLAN.md`).
