# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_hydrameter.html (anatomia del HydraMeter 0.4).
Cifras: calc_dmm_hydrameter.py. Dibujos: draw_dmm_hydrameter.py. Plantilla y CSS: build_dmm_tida01012.py."""
import io, draw_dmm_hydrameter as D, calc_dmm_hydrameter as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_hydrameter.html"
v = K.volt

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El HydraMeter es un multímetro abierto de John Duffy, diseñado en KiCad y documentado en hackaday. Todo su front-end es discreto: secciones separadas de tensión, corriente y ohmios, un PGA con multiplexor y un ADC ΣΔ de 16 bits. Su autor dice que <b>no está pensado para medir la red</b> y que es una prueba de concepto. Aun así enseña tres cosas que el TIDA-01012 no tenía: <b>protección escalonada de verdad</b>, <b>ohmios con medida Kelvin en el borne</b> y <b>derivadores de cuatro terminales</b>.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el HydraMeter</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Protección escalonada en V/Ω</td><td>Resistencias de inserción en serie, MOV de 230 Vrms y GDT de 75 V hacia el borne COM, y un MOV de 3.3 V en la toma (§3)</td><td>Cada etapa baja la falla un escalón; la corriente de falla vuelve por el borne, no por pistas finas. Base para RD-10 (P23)</td><td>{tg(OK,'Adoptar la idea')}</td></tr>
      <tr><td>Patas bajas conmutadas con 1 MΩ arriba</td><td>Como el TIDA, pero la resistencia de arriba es 1 MΩ: la entrada es 10 MΩ solo en el rango bajo y 1.1 MΩ en los demás (§3)</td><td>Mantener 10 MΩ arriba, como el TIDA</td><td>{tg(CRIT,'Evitar')}</td></tr>
      <tr><td>Compensación que no cuadra</td><td>Con los valores nominales, el rango ÷1.11 perdería ≈ {abs(v['÷1.11']['err_ac'])*100:.0f} % por encima de ≈ {v['÷1.11']['f_c']:.0f} Hz, sin contar la capacidad del MOV de la toma (§3)</td><td>Las capacidades de MOV, TVS y GDT entran en el divisor y hay que contarlas. En la toma, mejor diodos de baja capacidad</td><td>{tg(WARN,'Tener en cuenta')}</td></tr>
      <tr><td>Ohmios con medida Kelvin en el borne</td><td>La corriente sale por su propio camino protegido (diodo, fusible, 1 kΩ de 1 W) y la tensión se mide en el borne con la entrada de tensión (§5)</td><td>La protección no entra en la medida. Confirma la idea de nuestra sección H (P24)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Medir la corriente de la fuente sin cargar el nodo</td><td>Amplificador y P-MOS que convierten la caída en la R de rango en una corriente hacia 1 kΩ referido a COM (§5)</td><td>Sustituye a los divisores ÷4 de nuestra sección H, que roban corriente al nodo de medida (P25)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Limitar la tensión del DUT</td><td>Un N-MOS en seguidor de fuente mantiene el DUT por debajo de ≈ 1.5 V en los rangos altos, para seguir en el rango de 10 MΩ (§5)</td><td>Útil si nuestra entrada en ohmios tiene un tope de tensión (P24)</td><td>{tg(OPEN,'Estudiar')}</td></tr>
      <tr><td>Derivador de 4 terminales y punto estrella</td><td>10 mΩ en 2512 de 4 pines; COM sale del pin de sentido del lado del borne; diodos en antiparalelo en cada derivador (§4)</td><td>Directo a nuestro derivador de 0.1 Ω (P27)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Calibración por tablas de varios puntos</td><td>Pares (código, valor real) por rango, de 3 a 15 puntos, con interpolación lineal (§7)</td><td>Corrige también la no linealidad del ADC, nuestro punto débil (P26)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>COM a 1.65 V y comunicación aislada</td><td>Instrumento flotante con batería; el enlace sale por un aislador digital y un DC-DC aislado (§8)</td><td>No aplicable: nuestro COM es la masa común (RD-05)</td><td>{tg(CRIT,'No aplicable')}</td></tr>
      <tr><td>Módulos</td><td>Raspberry Pi Pico, radios, dos DC-DC aislados en módulo, y el PGA y el ADC en placas «breakout» (§11)</td><td>Nada de esto entra: tenemos el G473 y ±4.9 V referidos a masa</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><b>Proyecto KiCad 8</b> <code>research_and_tests/HydraMeter_0.4/MMTR_AFE_00_04_TORELEASE/</code> (7 hojas, versión 0.4 de diciembre de 2024). Exporté la netlist con <code>kicad-cli</code> 10 y la leí pieza a pieza: valor, número de pieza y red de cada pin. El PDF que trae el proyecto son imágenes sin texto.</li>
    <li><b>Bitácora del autor</b> «Schematic and Operation» (hackaday, log 223270, sep. 2023). Explica la intención de cada bloque, pero es <b>anterior</b> a la v0.4: allí la entrada tenía diez resistencias y un relé de estado sólido en ohmios; en la v0.4 son cuatro y el relé ya no está. <b>Manda la netlist.</b></li>
    <li><b>Firmware</b> de la placa analógica <code>Code/HackBoard_V02_10_shbrd_cal/</code>: configuración del ADC, autorango, cálculo de ohmios, alterna y tablas de calibración.</li>
    <li><b>README</b>: la placa fabricada es la v0.3 y necesitó muchos retoques a mano; los cambios de la v0.4 están <b>sin probar</b>.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_hydrameter.py</code>; tres redibujos en <code>draw_dmm_hydrameter.py</code> (0 solapes con <code>chk_dmm.py</code>, revisados a la vista).</li>
  </ul>
"""))

S.append(sec("arquitectura", "2", "Arquitectura", """
  <pre class="mermaid">flowchart LR
  VP["Borne V/Ω"] --> VAFE["Entrada de tensión<br/>1 MΩ + MOV + GDT + patas (NL7WB66)"]
  VP -. "interruptor del panel" .- OHM["Fuente de ohmios<br/>9.5 V aislados, 4 R de rango"]
  OHM --> ISENSE["LMC7101 + P-MOS<br/>corriente de la fuente"]
  AJ["Borne A"] --> AAFE["F1 16 A + 10 mΩ (4 terminales)"]
  MJ["Borne mA/µA"] --> MAFE["F2 500 mA + 100 Ω / 0.33 Ω"]
  VAFE --> PGA["MCP6S28<br/>mux 8 + PGA ×1…×32"]
  AAFE --> PGA
  MAFE --> PGA
  ISENSE --> PGA
  PGA --> ADC["MCP3461R · ΣΔ 16 bits<br/>diferencial frente a COM"]
  ADC -->|SPI| MCU["Raspberry Pi Pico"]
  MCU -->|"74HC595 ×3, 74HCS165 ×2"| VAFE
  MCU -->|"aislador + RS-422"| DISP["Pantalla aparte"]</pre>
  <p>Hay tres secciones de entrada separadas, cada una con su protección, y todas terminan en el mismo PGA. Las referencias de tensión son COM (1.65 V), A0V/A3V3 (analógico) y D0V/D3V3 (digital). El borne COM no se une directamente a la red COM: pasa por el derivador de 10 A (§4).</p>
"""))

rows = "".join(
    f"<tr><td>{n}</td><td class='n'>{x['Zin']/1e6:.2f} MΩ</td><td class='n'>±{x['fs']:.1f} V</td>"
    f"<td class='n'>{x['tau_b']*1e6:.0f} µs</td><td class='n'>{x['err_ac']*100:+.1f} % desde ≈ {x['f_c']:.0f} Hz</td></tr>"
    for n, x in v.items())
S.append(sec("tension", "3", "Entrada de tensión: protección escalonada", f"""
{fig(D.tension(), "Redibujo de la hoja Volt_AFE (v0.4). Los descargadores se dibujan con el símbolo de un diodo bidireccional.")}
  <h3>Cuatro escalones de protección</h3>
  <p>La resistencia de entrada no es una pieza, sino cuatro de inserción (THT verticales, para tener más distancia de aislamiento), con un descargador después de cada tramo. El autor lo explica con una falla de 10 kV de ejemplo:</p>
  <ol class="tight">
    <li><b>R1 + R2 (200 kΩ) y RT1</b>, un MOV de 230 Vrms (TDK B72205S0231K311) hacia el <b>borne COM</b>. Sujeta N1 a unos 400 V; por R1 + R2 pasan ≈ {K.I_N1_10kV*1e3:.0f} mA durante el pulso.</li>
    <li><b>R3 (400 kΩ) y RT2</b>, un GDT de 75 V (Bourns 2045-07-BLF), también al borne COM: unos {K.I_N2*1e3:.1f} mA.</li>
    <li><b>R4 (400 kΩ) y RT3</b>, un MOV de 3.3 V en 0603 hacia COM: unos {K.I_VOUT*1e6:.0f} µA.</li>
    <li><b>R11 (1 kΩ)</b> y los diodos internos del PGA.</li>
  </ol>
  <p>Con la red (230 Vrms) el MOV de 230 V apenas conduce y la cadena de 1 MΩ deja pasar {K.I_RED*1e3:.2f} mA de pico, que RT3 absorbe. Cada resistencia disipa milivatios ({K.P_R_RED*1e3:.0f} mW en las de 100 kΩ, {K.P_R4_RED*1e3:.0f} mW en las de 400 kΩ): la entrada aguantaría la red de forma continua. El detalle importante es <b>adónde vuelve la corriente de falla</b>: RT1 y RT2 van al borne COM, no a la red COM, para que los picos no recorran pistas finas.</p>
  <h3>Rangos: patas bajas conmutadas, como el TIDA</h3>
  <p>Debajo de la toma, R12 (9.1 MΩ) está siempre, y un NL7WB66 (dos conmutadores de 3.3 V) añade R13 (100 kΩ) o R14 (6.8 kΩ) hacia COM. La toma va al PGA por R11 y se limita a ±1.5 V respecto a COM.</p>
  <div class="tw"><table>
    <thead><tr><th>División</th><th>Z de entrada</th><th>Fondo</th><th>τ de la pata</th><th>Error de la división capacitiva</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="meta">Cálculo propio con los valores de la netlist. El firmware calibra las impedancias reales en 1.104 MΩ y 1.011 MΩ, que cuadran con 1.10 y 1.01 MΩ.</p>
  <p>Como arriba hay solo 1 MΩ, <b>la impedancia de entrada cae a ≈ 1.1 MΩ</b> en cuanto se pasa de ±1.7 V. El autor lo sabe y dejó escrita una versión con 10 MΩ constantes que no llegó a probar. Para nosotros, RF/RD piden 10 MΩ: aquí el TIDA hace mejor el trabajo.</p>
  <h3>La compensación no cuadra con los valores nominales</h3>
  <p>Arriba hay dos tramos con constantes de tiempo distintas: R1 + R2 con C54 dan {K.TAU_TOP1*1e6:.0f} µs y R3 + R4 con C55 dan {K.TAU_TOP2*1e6:.0f} µs. Debajo, R12 con C73 dan 300 µs y las patas de 100 kΩ y 6.8 kΩ, 181 y 184 µs. Además, el MOV RT1 añade unos 70 pF en N1 (cifra del autor). Calculando la división capacitiva con todo eso, <b>los rangos ÷11.1 y ÷148 quedan bien</b> (+1.1 % y +0.3 %), pero <b>el ÷1.11 perdería ≈ {abs(v['÷1.11']['err_ac'])*100:.0f} % por encima de ≈ {v['÷1.11']['f_c']:.0f} Hz</b>. Y eso sin contar el MOV de 3.3 V de la toma, cuya capacidad (en un 0603, de cientos de pF; <b>NO VERIFICADO</b>) lo empeoraría. O hay algo que no aparece en el esquema, o ese rango no mide bien la alterna por encima de unos cientos de hercios. La lección para nosotros: <b>las capacidades de los descargadores son parte del divisor</b>.</p>
"""))

c = K.corr
S.append(sec("corriente", "4", "Corriente: tres derivadores, cuatro terminales", f"""
{fig(D.corriente(), "Redibujo de la hoja Amp_AFE. El hilo grueso J30–J34 (README: 18 AWG) une el fusible F1 con el derivador R15.")}
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Resistencia medida</th><th>Fondo (tabla de calibración)</th><th>Caída</th><th>Tras el PGA</th><th>Fusible</th></tr></thead>
    <tbody>
      <tr><td>A</td><td>R15 = 10 mΩ</td><td class="n">±3 A calibrados (≈ 10 A previstos)</td><td class="n">{c['A']['V']*1e3:.0f} mV</td><td class="n">{c['A']['V_adc']:.2f} V (×8)</td><td>F1, 16 A</td></tr>
      <tr><td>mA</td><td>R16 + R15 = 0.34 Ω</td><td class="n">±0.5 A</td><td class="n">{c['mA']['V']*1e3:.0f} mV</td><td class="n">{c['mA']['V_adc']:.2f} V (×5)</td><td>F2, 500 mA</td></tr>
      <tr><td>µA</td><td>R17 + R16 + R15 = 100.3 Ω</td><td class="n">±1.4 mA</td><td class="n">{c['µA']['V']*1e3:.0f} mV</td><td class="n">{c['µA']['V_adc']:.2f} V (×8)</td><td>F2, 500 mA</td></tr>
    </tbody>
  </table></div>
  <ul class="tight">
    <li><b>Cuatro terminales.</b> R15 es una 2512 de 4 pines: dos llevan la corriente y dos miden. <b>COM nace en el pin de sentido del lado del borne</b>, de modo que es un punto estrella: en uso normal casi no circula corriente entre COM y el borne, y una corriente de falla de la entrada de tensión vuelve directa al borne.</li>
    <li><b>Diodos en antiparalelo</b> (1N4007) sobre cada derivador: si se aplica tensión, sujetan la caída hasta que abre el fusible.</li>
    <li><b>Un interruptor del panel</b> (J5–J6) puentea R17 en el rango de mA. El firmware se entera leyendo los interruptores por los 74HCS165.</li>
    <li>Las tres medidas llegan al PGA por 2 kΩ y un MOV de 3.3 V, igual que la tensión.</li>
    <li>Con 16 A, R15 disiparía {K.P_R15_16A:.1f} W; la potencia de esa 2512 está <b>NO VERIFICADA</b>. El fusible parece grande para el derivador.</li>
  </ul>
"""))

S.append(sec("ohmios", "5", "Ohmios y diodo: Kelvin en el borne", f"""
{fig(D.ohmios(), "Redibujo simplificado de la hoja Ohm_AFE (v0.4). En la v0.4 ya no está el relé de estado sólido de la bitácora; Q20, Q21 y su red quedan sin montar según el README.")}
  <p>El autor quería pocas piezas, una prueba de diodo de al menos 3.6 V (para LED blancos y azules), un solo borne para V y Ω, algo de protección y más de seis décadas de resistencia. Lo resolvió así:</p>
  <ul class="tight">
    <li><b>Riel propio de ≈ 9.5 V referido a COM</b>, hecho con un DC-DC aislado (B0309S-1WR3) que se enciende solo en ohmios. Así la corriente de prueba vuelve a COM sin pasar por el amplificador que genera COM.</li>
    <li><b>Cuatro resistencias de rango</b> (510 Ω, 10 kΩ, 100 kΩ, 1 MΩ), cada una con un P-MOS que la conecta al riel. Corriente en cortocircuito: {', '.join(f'{i*1e3:.3g} mA' for i in K.I_CORTO)}. Rangos del firmware: {', '.join(K.FW_RANGOS)}.</li>
    <li><b>Medida de la corriente sin cargar el nodo.</b> U4 (LMC7101) fija en R30 (3.3 kΩ) la misma caída que hay en la R de rango; esa corriente pasa por un P-MOS (Q6) y cae en R31 (1 kΩ) referida a COM. La salida es la caída dividida por {K.G_SENSE:.1f}: hasta {K.V_SHUNT_MAX:.1f} V de caída caben en ±1.5 V. Ningún divisor toca el nodo de la R de rango, así que toda la corriente va al DUT.</li>
    <li><b>Seguidor de fuente (Q1).</b> En los rangos altos su puerta se fija a ≈ {K.V_GATE_LOWV:.1f} V (LowV_EN) y el DUT queda por debajo de ≈ 1.5 V: la entrada de tensión sigue en ÷1.11, con 10 MΩ. Además consume la tensión sobrante para que el amplificador de corriente no se sature cuando el DUT es mucho menor que la R de rango.</li>
    <li><b>Protección propia</b> del camino de corriente: D1 en serie (bloquea tensiones positivas), F3 de 63 mA, R25 de 1 kΩ y 1 W, D6 y un MOV de 18 V a COM. La conexión al borne la cierra <b>un interruptor del panel</b> (J7–J8).</li>
    <li><b>Kelvin en el borne.</b> La tensión del DUT se mide en el borne V/Ω con la entrada de tensión. D1, F3 y R25 llevan la misma corriente que el DUT pero quedan fuera de la medida: su caída no importa.</li>
  </ul>
  <p>Límites: la fuga de D1, D6 y del MOV de 18 V pasa por la R de rango pero no por el DUT, y en el rango de 1 MΩ la corriente de prueba es de solo 8 µA (la fuga está <b>NO VERIFICADA</b>). La corrección por la entrada de tensión en paralelo está escrita en el firmware pero comentada («TODO: cal's off!»). No hay modo de continuidad con zumbador.</p>
  <p><b>Diodo:</b> modo con el rango ÷11.1 y la puerta de Q1 al riel; la tensión en vacío llega a unos 8 V, de sobra para un LED azul.</p>
"""))

S.append(sec("adc", "6", "PGA y ADC", f"""
  <ul class="tight">
    <li><b>MCP6S28</b>: multiplexor de 8 entradas y PGA de ×1 a ×32, con su referencia en COM. Entradas: tensión, mA, µA, A, corriente de ohmios y tres para módulos.</li>
    <li><b>MCP3461R</b>: ΣΔ de 16 bits con referencia interna de 2.4 V, entrada diferencial. Mide la salida del PGA contra COM (CH0 − CH1); también puede leer directamente cuatro entradas sin pasar por el PGA. Un LSB son {K.LSB*1e6:.0f} µV.</li>
    <li>El reloj del ADC sale de un pin PWM de la Pico y el firmware elige el sobremuestreo (de 32 a 98 304) según la velocidad pedida. El autor quiere usarlo también como «modo osciloscopio» lento (12 bits a 1 MSa/s).</li>
    <li>El PGA y el ADC van en placas pequeñas enchufables para poder cambiarlos: es parte de la idea de modularidad del autor.</li>
  </ul>
"""))

S.append(sec("firmware", "7", "Firmware", """
  <ul class="tight">
    <li><b>Calibración por tablas</b> (<code>calibration.h</code>): pares (código del ADC, valor real) medidos con un instrumento de referencia. Son 15 puntos en µA, 7 en mA, 6 en A, de 3 a 5 por rango de tensión y 3–4 por rango de ohmios. Entre puntos se interpola: así se corrige también la no linealidad.</li>
    <li><b>Continua:</b> filtro exponencial con α = 0.05.</li>
    <li><b>Alterna:</b> resta una media muy lenta (α = 0.0007), eleva al cuadrado, suma bloques de 16 muestras y promedia en ventana; la salida es √(media) × 2. Ese factor 2 no está explicado en el código.</li>
    <li><b>Autorango de tensión:</b> sobre un valor eficaz filtrado de los códigos; baja de rango por debajo de 800 y sube por encima de 20 000, con al menos 200 ms entre cambios.</li>
    <li><b>Ohmios:</b> R = V / I, con V de la entrada de tensión e I de la tabla de calibración de la fuente. Autorango: sube si la lectura de corriente pasa de 12 500 o si la tensión supera 1.55 V; baja por debajo de 500.</li>
  </ul>
"""))

S.append(sec("alimentacion", "8", "Alimentación y aislamiento", """
  <ul class="tight">
    <li><b>Batería</b> con un P-MOS de encendido suave: el botón lo enciende y el MCU tiene medio segundo para sostener Battery_EN; si no, se apaga. Sirve también de autoapagado real.</li>
    <li>LDO de 5 V (AP2210) a VSYS para la Pico, que hace el 3.3 V digital. El 3.3 V analógico sale de otro LDO (AP7375) tras un choque de modo común entre las masas digital y analógica.</li>
    <li><b>COM</b> = A3V3/2 con un divisor de 100 kΩ y un LMR321 con 50 Ω de salida.</li>
    <li><b>Comunicación aislada</b> hacia la pantalla o el PC: DC-DC aislado de 5 V (RFM-0505S), aislador digital STISO621 y RS-422 (SP491E), con opción de LVDS. Tres 74HC595 y dos 74HCS165 manejan conmutadores e interruptores del panel.</li>
  </ul>
"""))

S.append(sec("seguridad", "9", "Seguridad: qué aguanta y qué no", """
  <ul class="tight">
    <li><b>Tensión:</b> la entrada aguantaría la red de forma continua (1 MΩ, mW por resistencia, descargadores). Es lo más sólido del diseño.</li>
    <li><b>Ohmios:</b> R25 de 1 kΩ limita, pero con la red pasarían ≈ 0.3 A de pico hasta que abra F3 (63 mA); el autor lo reconoce.</li>
    <li><b>Corriente:</b> fusibles de 16 A y 500 mA sin poder de corte declarado en el esquema, y diodos 1N4007 como sujeción.</li>
    <li>El autor avisa: «no está pensado para medir nada fuera de baja tensión DC».</li>
  </ul>
"""))

S.append(sec("no-copiar", "10", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>1 MΩ arriba: la entrada baja a ≈ 1.1 MΩ en los rangos altos.</li>
    <li>Un MOV de 3.3 V en la toma: su capacidad y su fuga entran en el divisor. Mejor diodos de baja fuga y baja capacidad (BAV199) con resistencia serie.</li>
    <li>Rangos e interruptores mecánicos: mA/µA y la conexión de ohmios dependen del usuario.</li>
    <li>COM a media alimentación y comunicación aislada: no encajan con nuestra masa común.</li>
    <li>1N4007 como diodos de sujeción y de protección de señal: lentos y con mucha capacidad.</li>
    <li>El factor ×2 sin explicar en la alterna y la corrección de ohmios desactivada.</li>
  </ul>
"""))

S.append(sec("modulos", "11", "Módulos y su equivalente discreto", """
  <div class="tw"><table>
    <thead><tr><th>Módulo</th><th>Función</th><th>En la rev 2.1</th></tr></thead>
    <tbody>
      <tr><td>Raspberry Pi Pico</td><td>MCU</td><td>STM32G473 en nuestra placa</td></tr>
      <tr><td>RFM69HCW, NRF24L01</td><td>Radio hacia la pantalla</td><td>No hace falta: ESP32-S3 y TFT en la misma placa</td></tr>
      <tr><td>B0309S-1WR3</td><td>9.5 V aislados para ohmios</td><td>No hace falta aislar: COM = masa. La fuente sale de +4.9 V (prueba de diodo hasta ≈ 3.5 V, RD-08)</td></tr>
      <tr><td>RFM-0505S + STISO621 + SP491E</td><td>Comunicación aislada</td><td>No aplicable (RD-05)</td></tr>
      <tr><td>MCP6S28 y MCP3461R en placa enchufable</td><td>PGA y ADC</td><td>ADC5 del G473 y nuestro amplificador</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("comparacion", "12", "Comparación con el TIDA-01012 y con la sección H", """
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>HydraMeter</th><th>TIDA-01012</th><th>Sección H</th></tr></thead>
    <tbody>
      <tr><td>Entrada de tensión</td><td>1 MΩ + patas conmutadas</td><td>10 MΩ + patas conmutadas</td><td>Tomas fijas de una cadena de 10 MΩ</td></tr>
      <tr><td>Protección</td><td>Escalonada: THT, MOV, GDT, MOV</td><td>Ninguna</td><td>R_PROT de 3 × 33 kΩ y BAV199</td></tr>
      <tr><td>Ohmios</td><td>4 R de rango, Kelvin en el borne, corriente medida con V→I</td><td>No tiene</td><td>Razón con R_ref, «fuerza y sentido» con divisores ÷4</td></tr>
      <tr><td>Corriente</td><td>3 derivadores y 3 bornes, 4 terminales</td><td>2 derivadores, fuerza y sentido</td><td>1 derivador de 0.1 Ω</td></tr>
      <tr><td>ADC</td><td>ΣΔ 16 bits + PGA</td><td>SAR 18 bits</td><td>ADC5 de 12 bits con sobremuestreo</td></tr>
      <tr><td>Calibración</td><td>Tablas de 3 a 15 puntos</td><td>3 puntos y regresión</td><td>Ganancia y offset por rango</td></tr>
      <tr><td>COM</td><td>1.65 V, flotante, aislado</td><td>1.35 V, flotante</td><td>Masa común</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "13", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P22 (TIDA-01012). <b>Ninguna está aplicada</b>; se deciden en la síntesis.</p>
  <h3>P23 · Protección escalonada en V/Ω {tg(OK,'Adoptar la idea')}</h3>
  <p>Varias resistencias de alta tensión en serie (THT o 1206 de alta tensión) con un descargador tras el primer tramo (MOV de 230–275 Vrms o GDT) que devuelva la corriente al borne COM, y diodos de baja fuga en la toma. Con P17 la toma ya está a µA; esta propuesta cubre los picos (ESD y transitorios) y el caso de la red durante 10 s (RD-10). Hay que contar la capacidad de cada descargador en la compensación.</p>
  <h3>P24 · Ohmios con camino de corriente protegido aparte y medida en el borne {tg(OK,'Adoptar')}</h3>
  <p>Confirma la sección H: la fuente sale por su propio camino (PTC o resistencia de potencia, diodo y fusible) y la tensión se mide en el borne con la entrada de tensión. Se estudia además limitar la tensión del DUT (seguidor de fuente) para no salir del rango de 10 MΩ.</p>
  <h3>P25 · Medir la corriente de la fuente sin divisores {tg(OK,'Adoptar')}</h3>
  <p>Un amplificador y un transistor que convierten la caída en la R de rango en una corriente hacia una resistencia referida a masa. Sustituye a las entradas X5/X6 (÷4) de la sección H, que roban corriente al nodo de la fuente: en el rango de 20 MΩ, con 0.3 µA de prueba, cualquier divisor de cientos de kΩ en ese nodo arruina la medida.</p>
  <h3>P26 · Calibración por tabla de varios puntos {tg(OK,'Adoptar')}</h3>
  <p>Por rango, 3–7 puntos medidos con un multímetro de referencia e interpolación lineal. Complementa la calibración de tres puntos del TIDA (P21) y ataca la no linealidad del ADC5.</p>
  <h3>P27 · Derivador de 4 terminales con punto estrella y diodos en antiparalelo {tg(OK,'Adoptar')}</h3>
  <p>El 0.1 Ω en 2512 con huella Kelvin (o un derivador de 4 pines), la red de medida del DMM tomada del pin de sentido del lado del borne COM, y dos diodos de potencia en antiparalelo sobre el derivador hasta que abra el fusible.</p>
"""))

S.append(sec("correcciones", "14", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>En el plan dije que el único módulo era la Pico. Hay más: dos radios, dos DC-DC aislados en módulo, y el PGA y el ADC en placas enchufables.</li>
    <li>En nuestra sección H, las entradas X5/X6 miden lo alto y lo bajo de R_ref con divisores ÷4. El del lado del borne (X6) <b>roba corriente al DUT</b>: es un error de diseño que el HydraMeter evita con el convertidor V→I. Queda como P25.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("arquitectura", "2 · Arquitectura"),
    ("tension", "3 · Tensión y protección"), ("corriente", "4 · Corriente"), ("ohmios", "5 · Ohmios y diodo"),
    ("adc", "6 · PGA y ADC"), ("firmware", "7 · Firmware"), ("alimentacion", "8 · Alimentación"),
    ("seguridad", "9 · Seguridad"), ("no-copiar", "10 · Lo que no conviene copiar"), ("modulos", "11 · Módulos"),
    ("comparacion", "12 · Comparación"), ("propuestas", "13 · Propuestas P23–P27"), ("correcciones", "14 · Correcciones")])

HTML = (
 '<title>Anatomía del HydraMeter</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 2 de 9</p>\n  <h1>Anatomía del HydraMeter</h1>\n'
 '  <p class="lede">Un multímetro abierto con todo el front-end discreto: entrada de tensión con protección escalonada, ohmios con medida Kelvin en el borne y derivadores de cuatro terminales, alrededor de un PGA y un ADC ΣΔ de 16 bits.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes locales en <code>research_and_tests/HydraMeter_0.4/</code>. '
 'Proyecto: <a href="https://hackaday.io/project/176607-hydrameter">hackaday.io/project/176607-hydrameter</a>. Cifras: <code>herramientas/calc_dmm_hydrameter.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
