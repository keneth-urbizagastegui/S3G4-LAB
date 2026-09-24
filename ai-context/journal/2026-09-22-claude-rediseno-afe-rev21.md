# Rediseño del front-end analógico (rev 2.1) y revisión de referencias

- Fecha: 2026-09-22, de 12:50 a 23:45 hora local.
- Agente: Claude Code (Opus 5).
- Pedido: reducir el coste de construcción del AFE de la rev 2.0, que el usuario considera demasiado alto. Trabajo por secciones, eligiendo cada componente con disponibilidad en JLCPCB y explicando la matemática, porque el usuario indicó que en la rev 2.0 «se perdió en las matemáticas y en por qué elegimos tal componente».

## Archivos nuevos aportados por el usuario en esta sesión

Ninguno fue modificado. Se registran como fuentes de consulta:

- `research_and_tests/DSO112/schematic_112g.pdf` — esquemático completo del JYE Tech DSO112 (doc. 105-11200-00G).
- `research_and_tests/DSO112/dso112a-user-manual.pdf`, `dso112a-quick-guide.pdf` — especificaciones declaradas.
- `research_and_tests/DSO112/113-11201-211/113-11201-211.hex`, `113-11205-024/113-11205-024.hex` — firmware binario del DSO112. **No analizado.**
- `datasheet - componentes/C2837587.pdf` (BNC Kinghelm), `C41416668.pdf` (BNC Samzo), `C725760.pdf` (conmutador SS23H38L5), `C883267.pdf` (conmutador SS23H37L6).

## Cambio

- `docs/rediseno_afe_rev21.html` — documento vivo del rediseño, creado y ampliado en esta sesión. Publicado también como artifact privado: https://claude.ai/artifact/YLrJwmm5Cz6w864dUYsrBT
  Contiene: reglas de trabajo, decisiones D-01…D-07, sección A (conector BNC y conmutador de acoplo), sección B (protección: tabla de amenazas, tres funciones de protección, orden de la cadena, esquemas B.7, cálculo del divisor B.8 y lista de compra para JLCPCB), y nota sobre el significado de «50 Vpk» del DSO150.
- No se tocó firmware, `.ioc`, PCB, el proyecto de Altium ni ningún `.py` de netlist.

## Evidencia recogida

Toda sale de los esquemáticos y manuales de la carpeta `research_and_tests`, no de foros.

### Cómo resuelven la protección de entrada cuatro instrumentos de JYE Tech

| | DSO138 mini | DSO150 | DSO112 | DSO158 / wave2 |
|---|---|---|---|---|
| Documento | 105-13801-00J | 105-15001-00F | 105-11200-00G | 105-15801-00E |
| Ancho de banda | 200 kHz | 200 kHz | 2 MHz | — |
| Zin | 1 MΩ / 20 pF | ~1 MΩ | 1 MΩ | ~2 MΩ |
| Máxima entrada declarada | 50 Vpk | 50 Vpk | 50 Vpk | — |
| Atenuador grueso | conmutadores mecánicos SW1–SW3 | relé DPDT RLY1A/B/C | relé TQ2 DPDT, ×1 / ÷100 | 74HC4053 (switch CMOS) |
| Acoplo AC/DC/GND | conmutador mecánico | conmutador mecánico SW1A/B | PhotoMOS CPC1017N | PhotoMOS CPC1017N ×2 |
| Escalera fina | 74HC4051 tras el buffer | 74HC4051: 300/150/91/30/15/15 Ω | 74HC4051: 499/249/150/75/49.9/24.9 Ω | 2× 74HC4051 |

Hallazgo principal: **ninguno de los cuatro lleva TVS, PTC, fusible, varistor ni componente alguno destinado a sobrevivir a la red eléctrica.** Su protección consiste en una resistencia serie de 100 kΩ (`R1` en el DSO138 mini, `R2` en el DSO150), declarar 50 Vpk y un aviso en el manual. La guía rápida del DSO112A dice literalmente: «Do not attempt to measure live power directly.»

Consecuencia medida: 100 kΩ contra ~8 pF de capacidad de entrada dan 199 kHz. **Los 200 kHz de ancho de banda del DSO138 mini y del DSO150 no son un límite del amplificador: son el precio de su resistencia de protección.** El DSO112, que declara 2 MHz, no puede permitírsela y deja la rama ×1 sin proteger.

### Tabla de rangos del DSO112, impresa en su propia hoja 2

12 escalas de 5 mV/div a 20 V/div, formadas por 2 posiciones de relé (1/1, 1/100) × 6 pasos de escalera (1/1, 1/2, 1/4, 1/10, 1/20, 1/40), atenuación total de 1/1 a 1/4000. **En la escala de 5 mV/div la atenuación total es 1/1: no hay divisor delante.**

Sus valores: `R37 910k + R38 82k / R40 10k` → Zin 1002 kΩ, relación 100.2. Compensación `C23 3 pF` arriba, `C22 270 pF + C24 25 pF` de ajuste abajo. Verificación: 3 pF × 992 kΩ = 2.98 µs frente a 295 pF × 10 kΩ = 2.95 µs. **Cuadra al 1 %**, lo que valida el modelo de divisor compensado que estamos usando.

### Otras referencias

- **TI TIDA-01012** (`research_and_tests/tidubv5b (1).pdf`), DMM 4½ dígitos: su documentación dice «minimal overvoltage and overcurrent protection mechanisms have been implemented in this TI Design». Sólo hay fusible rearmable en la rama de corriente.
- **Micro-DMM** (`research_and_tests/Micro-DMM/`): sección titulada «Minimal Protections». Protección completa = **500 kΩ en serie + dos diodos de sujeción**, probada con megóhmetro de 1000 V sin daño. Identifica el peligro real en la **vía de retorno**, no en la punta, y lo resuelve con aislador USB. La carpeta trae hojas de ADuM1200/1201, ISO1540, RFM-0505S, AMC0330R-Q1 y PhotoMOS AQW21.
- **EMBO** (`research_and_tests/EMBO/`): scope+AWG+DMM+LA sobre STM32, pero sus «esquemáticos» son placas Nucleo/BluePill. **No tiene front-end analógico.**
- **black_scope** (`research_and_tests/black_scope/`): osciloscopio sobre STM32G473VE en KiCad. BOM: LMV324, LMV358, 4× 8k2, diodos Schottky. Sin entrada de 1 MΩ ni protección.
- **Rigol DS1054Z** (50 MHz, 300 V CAT I), por ingeniería inversa publicada: relé Fujitsu FTR-B3, JFET MMBFJ309L, diodos **BAV199**, amplificadores AD851x. Coincide con las piezas que habíamos elegido de forma independiente.

## Verificaciones numéricas hechas

Sobre el divisor ÷20 de la sección B, todas dan correcto: Zin = 997.9 kΩ y relación 20.00; carga de R_BIAS 10 MΩ → relación 20.09, error de ganancia +0.47 %; compensación 10 pF × 948 kΩ = 190 pF × 49.9 kΩ; capacidad de entrada ≈ 12 pF; corte del acoplo AC en 10.6 Hz; corriente de falla con 353 V = 0.354 mA; 112 V por resistencia de la rama superior.

Ruido térmico referido a entrada, con ancho de banda de ruido 1.57 × f₃dB a 1.5 MHz: ÷20 → 864 µVrms (17.3 % de una división de 5 mV); ÷5 → 395 µV; ÷2 → 197 µV (3.9 %); sin divisor → limitado por el amplificador, ~0.3 % de división.

## Errores propios corregidos durante la sesión

1. Di 158 µV y «3.2 % de división» para la toma ÷2. Correcto: **197 µV, 3.9 %**. La causa fue usar √(1.5 MHz) en vez del ancho de banda de ruido real.
2. Di «79 µV, 1.6 %» para el camino ×1. **Esa cifra no tenía base.** En ×1 el ruido lo fija el amplificador.
3. Propuse un atenuador de dos tomas (÷2 y ÷20) conmutadas por un solo PhotoMOS por toma. **No se sostiene**: (a) los clamps de la toma ÷2 conducirían a fondo de escala y corromperían el rango ÷20; (b) la capacidad en OFF del conmutador acopla la toma no usada al buffer con un error del orden del 25 % para 5 pF. Es un error absorbible en la compensación, pero exige que la capacidad sea estable y conocida, y el remedio general es conmutación en T o de dos polos. Leo Bodnar lo describe en EEVblog como práctica habitual: «shorting undesired leakage paths to ground with SPSTs». Es también la razón probable de que el DSO112 y el DSO150 usen relés de **dos polos** para conmutar una sola cosa.
4. Afirmé sin demostrarlo que el cuerpo del BNC Kinghelm mide 12.5 mm frente a 29.5 mm del Samzo. Retirado: el 12.5 sólo aparece en el título del plano. Pendiente de comprobar en EasyEDA.

## Pruebas

No se ha conectado hardware, no se ha ejecutado firmware ni se ha repetido ningún ensayo de banco. Todo lo anterior es análisis documental y cálculo. No hubo revisión visual de los esquemas generados: el panel de navegador no abre archivos locales y no hay renderizador de PDF (`pdftoppm`) instalado, por lo que `research_and_tests/DSO183_Schematic.pdf` y `dso138-mini-schematic-main-i.pdf` **no han podido leerse**.

## Pendientes

1. **Decisión abierta y bloqueante: D-06, nivel de supervivencia de la entrada del osciloscopio.** El usuario pidió explícitamente conservar la protección frente a que un estudiante mida la red («quiero mantener ese posible error que pueda cometer el usuario»). La revisión posterior mostró que ningún producto comparable lo hace y que el coste recae en el ancho de banda. Está planteada la alternativa de declarar 50 Vpk, conservar la supervivencia a 250 Vrms que el rango ÷20 ya da sin coste, y trasladar la protección de red fuerte al puerto del DMM, donde cuesta ~1 USD. **Sin respuesta del usuario. No hay acuerdo.**
2. Cerrar la sección A: confirmar el BNC Kinghelm C2837587, verificar en EasyEDA el número de pines y posiciones del SS23H37L6, y decidir si el 74HC165 de lectura de acoplo cuelga del STM32 o del ESP32.
3. Sección C (sensibilidad y ancho de banda): depende del punto 1.
4. Secciones D (filtro antialias), E (offset por PWM), F (red de muestreo del ADC) y G (rieles) sin empezar.
5. Leer `research_and_tests/Micro-DMM/An Open-Lead Detection Voltmeter Circuit.pdf` y los documentos de NI ELVIS II para el bloque DMM.
6. Incorporar al documento vivo las correcciones de ruido y la tabla comparativa de esta sesión.
7. Siguen abiertos los siete hallazgos de netlist de la rev 2.0 registrados en `2026-09-18-claude-esbozo-hardware.md`. Ninguno se ha corregido.
