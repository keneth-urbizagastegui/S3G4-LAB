# Análisis exhaustivo del DSO112

- Fecha: 2026-09-23, hora local.
- Agente: Claude Code (Opus 5.5).
- Pedido de Keneth: «hagamos un análisis exhaustivo de todo lo que podamos aprender del DSO112, porque es el mejor con el OpenScope; genera información que podamos usar».

## Cambio

- Nuevo `docs/analisis_dso112.html`, publicado como artifact privado: https://claude.ai/artifact/1Q3Ajh4q39Pdic6AV6w1LR. Reutiliza el CSS del documento vivo. Contiene tabla de lecciones, dos esquemas redibujados (entrada y ganancia), análisis por bloques, firmware, energía, protocolo, funciones, propuestas P1–P6, comparativa con OpenScope y correcciones.
- Nueva carpeta `docs/rediseno_afe_gen/` con los generadores de dibujos del rediseño y del análisis (antes sólo estaban en el scratchpad de la sesión), y su `LEEME.md`.
- Instalado `pymupdf` en el Python del usuario: permite renderizar PDF y SVG. Antes no había forma de ver los esquemáticos ni de revisar visualmente nuestros dibujos.
- No se tocó firmware, `.ioc`, PCB, Altium ni los netlists. **Ninguna propuesta se ha aplicado al documento vivo.**

## Método y evidencia

- Esquemático `research_and_tests/DSO112/schematic_112g.pdf` renderizado a 250–330 ppp y leído por zonas. Tiene 2 hojas aunque el cajetín dice «de 3»: la hoja 3 falta.
- Firmware: `113-11201-211.hex` es el programa del ATmega64 (56 774 B, 0x0000–0xDDC5). `113-11205-024.hex` es **su bootloader** (8 KB en 0xE000), no el firmware del ATmega48, que no está en la carpeta. Desensamblado de los bucles de captura.
- Manual `dso112a-user-manual.pdf` leído por secciones.
- Contraste con DSO150 (`research_and_tests/105-15006-00A.pdf`) y DSO138 mini (`research_and_tests/dso138-mini-schematic-analog-j.pdf`), también renderizados.
- Los dos esquemas redibujados pasan el comprobador geométrico con 0 solapes y se revisaron visualmente (PNG vía PyMuPDF). La página HTML completa no se revisó visualmente.

## Hallazgos principales (valores del esquemático)

- **La topología de entrada es nuestra D-05.** Divisor ÷100 siempre conectado (R37 910 k + R38 82 k sobre R40 10 k) y rama ×1 (R31 100 kΩ ∥ C22 270 pF). Un relé TQ2 (RLY2A) elige el nodo que va al buffer.
- **El relé es monoestable de una bobina**: los pines 5 y 6 y el segundo polo RLY2B no se conectan. En reposo queda en 1/100. La bobina va desde VRAW por L1 (100 µH) y Q7, gobernada por SENSEL3. No se ve diodo de rueda libre.
- **Acoplo:** C21 (0.1 µF, 100 V) en serie, cortocircuitada por el PhotoMOS CPC1017N (RLY1). CPLSEL = 0 → DC. La posición GND no existe en hardware: se hace con la entrada I/O0 del 4051, que va a masa.
- **Protección de la rama ×1:** R31 (0.44 mA con 50 V) + unión puerta-drenador del J309 hacia AV+ + D1 (1N4148) hacia AV−. No hay TVS.
- **Compensación del ÷100:** con los valores nominales (C23 3 pF arriba; C24 ≤ 25 pF + C25 150 pF + C64 15 pF abajo, ≤ 190 pF, cuando harían falta ≈ 298 pF) no cuadra. Sin explicación visible.
- **Buffer discreto:** J309 + Q4, con fuentes de corriente Q5 (≈ 5.4 mA) y Q6. Un lazo lento U7B (τ ≈ 1 s con 10 MΩ · 0.1 µF) compara la continua de salida con la de entrada y ajusta la corriente del JFET mediante Q6. Consigue offset cero sin eliminar la componente continua de la señal.
- **Escalera de 997.7 Ω** (499, 249, 150, 49.9, 24.9, 24.9 Ω), con tomas 1…1/40. **74HC4051 con 8 entradas: I/O0 masa, I/O3 VCHECK** (AREF 2.56 V · 75/10 075 = 19.1 mV) y seis tomas. Resultado: 12 escalas de 5 mV a 20 V/div. Los 2 mV/div del DSO112A deben ser ampliación digital (deducido).
- **Ganancia fija:** U6A 1 + 1430/75 = ×20.07 y U6B ×1.99 (DC) → ≈ ×39.95. Con 5 mV/div quedan 0.2 V/div en el ADC y 25.6 códigos por división.
- **Offset:** VPOS_PWM → R53 510 k / C38 0.1 µ → U7D → U7A inversor (R48 100 k ∥ C34 0.1 µ) → R42 100 Ω / C26 0.1 µF → rama de masa de U6B. Con los valores nominales, C26 dentro de la red de ganancia produce un escalón de +5.5 % por encima de ~16 kHz (×1.99 → ×2.10).
- **ADC TLC5510** de 8 bits, 0.6–2.6 V por autopolarización. Reloj ADCLK desde OC1B. Salidas de 5 V hacia el micro de 3.3 V a través de resistencias de 1 kΩ. R19 100 Ω / C13 100 pF: no es filtro anti-alias.
- **Disparo:** nivel TLVL_PWM (OC0) → R7 100 k / C1 0.1 µ → AIN0; señal por R16 1 k / C12 150 pF → PF3, hacia la entrada negativa del comparador del ATmega64 a través del multiplexor del ADC. **Frecuencímetro:** R73 ∥ C57 → C5 10 µF → polarización a 1.65 V → T1; CNT_EN unido a ICP1.
- **Captura por software** (firmware, 0x0CF7C): se sincroniza con el flanco de ADCLK y ejecuta `IN r24,PINC / ST X+ / NOP`, 4 ciclos por muestra a 20 MHz, es decir 5 MSa/s. El bucle con disparo (0x0D00C) vigila ACSR.ACI y trabaja en búfer circular a 8 ciclos por muestra, 2.5 MSa/s: de ahí sale el «2.5 MSPS en tiempo real» del manual. Anuncia 2 MHz de banda con un Nyquist de 1.25 MHz y sin filtro anti-alias. El ATmega64 corre a 20 MHz con 3.3 V, fuera de especificación.
- **Energía:**
  - Carga con LTC4054 a 500 mA; selección USB/batería con D3 y Q8 (P-MOS).
  - Interruptor suave con Q9 + Q10: el botón enciende, PWREN mantiene, PWRSW lee el botón. Autoapagado.
  - Rieles: AX5511 elevador a +7.59 V → L5 → 78L05 → AV+ 5 V; MC34063 inversor a −7.13 V → L2 → 79L05 → AV− −5 V; MIC5255 → 3.3 V.
  - Los LM6172 van a ±7 V; JFET, 4051 y TL084 a ±5 V.
  - Vigilancia con divisores de 0.125 hacia el ATmega48. Consumo < 300 mA con 3.7 V.
- **Sistema:**
  - El ATmega48 es el coprocesador de táctil, energía y señal de prueba, unido por UART.
  - CP2102 para USB y AT24C1024 para 24 presets y una forma de onda.
  - J5 hace de salida de la señal de prueba y de entrada de disparo externo.
  - J8–J11 son conectores de integración.
  - Protocolo serie: 0xFE de sincronía, relleno de bytes, little endian, «modo USB Scope», tramas de bloque o de una muestra, tensiones en unidades VBU de 20 µV.

## Propuestas nuevas (ninguna aplicada, pendientes de Keneth)

- **P1 · Grueso ÷100 en vez de ÷20**, con la escalera del DSO112 de 6 tomas.
  - Da 12 escalas, de 5 mV a 20 V/div, y libera dos entradas del 4051.
  - El nodo protegido queda en ±0.4 V con ±40 V y en 3.5 V con 353 V, así que los clamps no llegan a conducir.
  - Valores: arriba 3 × 330 kΩ y 3 × 30 pF; abajo 10.0 kΩ y ≈ 990 pF.
  - La rama ×1 vuelve a cubrir 5–200 mV/div. Tocaría D-09 y las tablas C.1, C.3 y C.6; D-05 (±40 V) no cambia.
- **P2 · Rama ×1 con 100 kΩ ∥ 1 nF** en lugar de 10 kΩ ∥ 10 nF (la misma τ = 100 µs).
  - La corriente con 50 V baja a 0.44 mA; el aviso de C.7 para la sección G (13 mA hacia los rieles) desaparece.
  - Opción: dos 1206 de 49.9 kΩ y C_S ≥ 630 V; la rama ×1 sobreviviría también a 250 Vrms. Hay que verificar piezas y la separación entre contactos del relé (≥ 400 V).
- **P3 · Entradas de masa y VCHECK** para autocero y comprobación de ganancia. Depende de P1. VCHECK ≈ 20 mV desde la referencia de 2.5 V.
- **P4 · Relé monoestable con reposo en el divisor**, como el DSO112, o latching. Con diodo de rueda libre en los dos casos.
- **P5 · RC de 1 kΩ / 150 pF antes del COMP**, o la histéresis del COMP. El frecuencímetro sale del COMP hacia un temporizador.
- **P6 · Offset por PWM filtrado** inyectado en la rama de masa de la última etapa, sin condensador dentro de la red de ganancia.

## Correcciones a afirmaciones anteriores (diario del 22 sep y mensajes)

1. «La compensación del ÷100 del DSO112 cuadra al 1 %»: falso. Había tomado C22 como condensador de abajo, y C22 es de la rama ×1.
2. «El TQ2 es latching de dos bobinas»: falso. Es monoestable de una bobina.
3. «El segundo polo pone a masa la rama no usada»: falso en el DSO112, donde RLY2B no se usa. El DSO150 usa los dos polos para desconectar ambos extremos del divisor que no está en uso.
4. «El DSO112 deja la rama ×1 sin proteger»: falso. La protegen R31, la unión del JFET y D1.
5. «Los 200 kHz del DSO138 mini y del DSO150 son el precio de su resistencia de 100 kΩ»: sólo es cierto en el DSO150. Allí R2 100 k es la mitad superior de un divisor ×1.11 sin compensar, con C2 de 1 pF, y el polo queda en ~200 kHz. En el DSO138 mini, R1 lleva 220 pF en paralelo.

Ninguna corrección afecta a D-05 ni a D-06.

## Pendientes

1. Que Keneth decida sobre P1 (÷100) y P4 (monoestable o latching). P2 no depende de nada y puede aplicarse cuando lo acepte.
2. Si se adopta P1: rehacer C.1, C.3 y C.6 y actualizar D-09.
3. Verificar en JLCPCB las piezas de alta tensión de la opción de P2.
4. Lo que no se pudo resolver: la hoja 3 del esquemático, el mecanismo exacto del conector J5 (R76 0 Ω y TS_CAP) y la discrepancia de compensación del ÷100.
5. Siguen abiertos los pendientes del diario del 23 sep (sección C) y del 22 sep.
