# Cómo retomar el estudio de referencias del DMM (7 oct 2026, Claude Opus 5.5)

Lo deja la sesión del 6–7 oct, que se quedó sin contexto. Para empezar el chat nuevo basta con: «retomemos, lee ai-context/journal/2026-10-07-claude-retomar-referencias-dmm.md».

## Dónde estamos

- **Orden de la rev 2.1 (Keneth, DECISIONS 6 oct):** DMM → AWG → mapa de pines (separando lo analógico de lo digital del STM32) → rieles → resto de esquemas. CH1–CH3 cerrados y dibujados; se dejan como están.
- **DMM, decisiones del 7 oct (DECISIONS):**
  - divisor de 10 MΩ con tomas y 74HC4051;
  - amplificador de deriva cero externo;
  - aguantar la red 10 s (RD-10);
  - rangos DC/AC de 200 mV, 2 V, 20 V y 50 V; Ω de 200 Ω a 20 MΩ; 200 mA y 2 A.
- **Sección H (borrador, EN PAUSA):** `S3G4_LAB_rev2.1/01_diseno/dmm_rev21.html` y la hoja `00_requisitos/especificaciones_dmm.html`, publicadas. Se escribieron antes de estudiar las referencias: **se revisan en la síntesis** y después se encarga S11 a Codex.
- **Plan:** `S3G4_LAB_rev2.1/06_plan/PLAN_REFERENCIAS_DMM.md` (método, referencias, orden y la evaluación de los enlaces 95152/57000/57006 de EEWorld).

## Referencias hechas (7 de 9)

Todas en `S3G4_LAB_rev2.1/02_referencias/`, publicadas (enlaces en `ARTEFACTOS.md`), con scripts `herramientas/calc_dmm_*.py`, `draw_dmm_*.py` y `build_dmm_*.py`, y diario propio:

| # | Referencia | Página | Propuestas |
|---|---|---|---|
| R1 | TI TIDA-01012 | `dmm_tida01012.html` | P17–P22 |
| R2 | HydraMeter 0.4 | `dmm_hydrameter.html` | P23–P27 |
| R6 | TI TIDA-00879 | `dmm_tida00879.html` | P28–P29 |
| R7 | EEVblog 121GW | `dmm_121gw.html` | P30–P32 |
| R3 | Micro-DMM | `dmm_microdmm.html` | P33–P34 |
| R8 | Martin (STM32F373) | `dmm_martin.html` | — (refuerza P17, P19, P21, P27, P29) |
| R4 | EEWorld 77845 (ficha corta) | `dmm_eeworld77845.html` | — (confirma P20, P26) |

## Propuestas acumuladas (NINGUNA aplicada; se deciden en la síntesis)

- **P17** Patas bajas conmutadas: 10 MΩ fijo arriba y patas a COM con el 74HC4051. La toma tiene el mismo fondo en todos los rangos y los clamps solo ven µA. Confirmada por los TIDA y por el 121GW. A estudiar: rango de 200 mV (÷1.1 con 9 MΩ de fuente) y amplificador de entrada CMOS de pA en lugar del OPA2188.
- **P18** Compensación con la misma τ en todas las patas, con C0G fijos y sin trimmer (el TIDA-01012 los quitó), dejando margen para Ceq. Resistencia de amortiguación en serie con el condensador de arriba (121GW: 30 kΩ con 6 pF).
- **P19** Fuerza y sentido con un conmutador doble (derivadores conmutados y R_ref de ohmios).
- **P20** Filtro del ADC5 calculado por la carga de muestreo (método del TIDA-01012, §2.4.1.3.1).
- **P21** Firmware: DC por media; alterna por √(Xrms² − Xdc² − Xnoise²); calibración de 3 puntos; filtro exponencial; más NPLC y autocero por el mux.
- **P22** Riel propio del DMM apagable (buck + LDO con EN, o conmutador de carga). Cierra RF-18.
- **P23** Protección escalonada en V/Ω: resistencias de alta tensión en serie y descargador tras el primer tramo, con retorno al borne COM. Contar la capacidad de MOV/TVS en la compensación.
- **P24** Ohmios con camino de corriente protegido aparte y medida de tensión en el borne (Kelvin); quizá limitar la tensión del DUT.
- **P25** Medir la corriente de la fuente de ohmios sin divisores (op-amp + transistor, V→I referida a masa). **Corrige un error de la sección H:** el divisor ÷4 de X6 roba corriente al DUT.
- **P26** Calibración por tabla de varios puntos con interpolación por rango.
- **P27** Derivador de 4 terminales con punto estrella del lado del borne COM y diodos de potencia en antiparalelo.
- **P28** Resistencia de entrada de alta tensión específica (tipo Vishay CRHV1206); buscar el equivalente en LCSC.
- **P29** Constantes de calibración en memoria no volátil, editables desde S3G4-UI (el TIDA-00879 las compila).
- **P30** PTC de alta tensión (1–2 kΩ en frío) en la fuente de ohmios y diodo. Cierra el pendiente «PTC» de la sección H.
- **P31** Fusible HRC cerámico con poder de corte declarado y puente de diodos (DF10S, con los terminales de continua unidos) como sujeción del derivador.
- **P32** Aviso de fusible abierto: el borne A medido antes del fusible a través de ≈ 10 MΩ.
- **P33** Cable abierto en tensión (RD-09) con resistencias definidas, cuando la lectura lleva ≥ 5 ms bajo un umbral. Variante B, sin piezas: lectura breve en el rango de 20 MΩ (≤ 0.49 µA). Variante A, como el puente de Mann: brazo de 10 MΩ de la toma de P17 a VREF (≤ 0.12 µA).
- **P34** En ohmios, si aparece tensión externa, desconectar la fuente y la R_ref, avisar y pasar a tensión (la PTC solo aguanta unos ms).

## Riesgos para la síntesis

- **Resolución:** en H, una cuenta vale ≈ 1/12 de LSB del ADC5 de 12 bits (todo depende del sobremuestreo). En el TIDA-01012, una cuenta son 2.3 LSB de un ADC de 18 bits; en el TIDA-00879 es un ΣΔ de 24 bits. Hay que justificar las 20 000 cuentas o rebajarlas.
- COM a media alimentación (TIDA, HydraMeter): no aplicable, porque nuestro COM es la masa común (RD-05).
- Lazos de masa (Micro-DMM): con masa común, si el S3G4 está conectado por USB a un PC enchufado y se mide un equipo enchufado a la red, COM queda unido a la tierra del PC. El Micro-DMM aísla todo por eso. Decir en la síntesis cómo se avisa al usuario. Martin aísla solo los datos del USB: al cargar, un conmutador une las masas (mismo compromiso).
- Límite inferior (EEWorld 77845): ≈ 1 % con el SAR de 12 bits de un F103, sin referencia propia ni autocero. Martin, con un ΣΔ de 16 bits y 25 000 muestras por lectura, aún calibra offsets del 3.5 % del fondo en su rango más bajo.

## Siguiente, en orden

1. ~~R3 Micro-DMM~~: hecho el 7 oct (diario `2026-10-07-claude-dmm-microdmm.md`).
2. ~~R8 Martin + R4 EEWorld 77845~~: hechos el 7 oct, sin propuestas nuevas (diario `2026-10-07-claude-dmm-martin-eeworld.md`).
3. **R5 Analog Devices** «7.5-Digit Accuracy» partes 1 y 2 (`research_and_tests/Analog_/`): teoría de errores, para revisar el presupuesto de la sección H §8.
4. **R9 Agilent 34401A**: `research_and_tests/Agilent_34401A/34401A_Service_Guide.pdf` (167 p). Teoría de funcionamiento en pp. 99–115 y esquemas en pp. 150–165. Front-end profesional: protección, divisor, fuente de ohmios, autocero y alterna.
5. **Síntesis:** comparación de todas las referencias, lista P17–P32+ para que decida Keneth, revisión de la sección H y encargo S11.
6. Pendiente de Keneth: si quiere la ficha del 95152 de EEWorld, tiene que bajarlo él (pide cuenta).

## Método y herramientas (para no redescubrirlas)

- Python: `C:/Users/Keneth/AppData/Local/Programs/Python/Python312/python.exe`, con pymupdf.
- PDF: renderizar por zonas con PyMuPDF (`get_pixmap(dpi, clip)`); el texto con `get_text()`.
- KiCad: `"/c/Program Files/KiCad/10.0/bin/kicad-cli.exe" sch export netlist|pdf`.
- Plantilla de página: `herramientas/build_dmm_tida01012.py` exporta `css, EXTRA, sec, fig, tg`. Al importarla regenera también la página del TIDA-01012, sin cambios.
- Dibujos: `herramientas/sch.py`; comprobar con `chk_dmm.py <modulo> <funciones>` (0 solapes) y ver con `render_svg.py <modulo> <funciones>` → `view_<f>.png`.
- Cada referencia: calc + draw + build → publicar (icono «meter») → `ARTEFACTOS.md`, `herramientas/LEEME.md`, la fila del PLAN → STATE + diario → commit + push → `node tools/ai-context/context.mjs sync`.
- `research_and_tests/` está en `.gitignore`: las descargas no se suben.
- Webs con JavaScript (EEWorld): navegador integrado, `get_page_text` / `javascript_tool`. Los archivos de EEWorld piden cuenta: no iniciar sesión.
- Descargas: pedir permiso a Keneth. Keysight: la URL `/us/` devuelve la web impresa en PDF; vale la `/mu/`. eevblog: download.php da 502; usar web.archive.org con `2024id_`.

## Git

`main` al día con origin; último commit de la sesión: `1bc86ca` (121GW) y el de este diario. La rama `respaldo-antes-sin-step` (local) guarda el historial anterior con el STEP de 49 MB: no subirla, y borrarla cuando Keneth confirme.
