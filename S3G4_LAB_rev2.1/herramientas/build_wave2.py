# -*- coding: utf-8 -*-
import io, draw_wave2 as W
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/analisis_wave2.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css and ".sx{" in css
EXTRA = """
.lesson td:first-child{font-weight:600}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:10px 0;font-size:14px}
.kv dt{color:var(--muted)} .kv dd{margin:0}
pre.mermaid{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:12px;overflow-x:auto}
.meta{color:var(--muted);font-size:13px}
.toc{columns:2 260px;column-gap:28px;margin:6px 0 0;padding-left:20px;font-size:14px}
.toc li{break-inside:avoid;margin:2px 0}
.toc a{color:var(--accent);text-decoration:none} .toc a:hover{text-decoration:underline}
"""
def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def fig(svg, cap):
    return f'  <figure><div class="sx">{svg}</div><figcaption>{cap}</figcaption></figure>\n'

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", """
  <p>El WAVE2 es el paso del DSO112 a dos canales, con generador, sobre dos STM32. Su ancho de banda es de 200 kHz, siete veces menos que el nuestro, y eso explica casi todas sus decisiones. Cada fila remite a su sección. <b>Nada de esto está decidido.</b></p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el WAVE2</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Grueso sin relé</td><td>Un divisor y un buffer por rama; un 74HC4053 conmuta las salidas ya bufferizadas (§2)</td><td>Alternativa real a P4, que llamo P7: algo más de ruido que con relé (0.8 % frente a 0.3 %), pero sin relé y a prueba de red en todas las escalas (§5)</td><td><span class="tag t-open">Decidir</span></td></tr>
      <tr><td>El ruido de un divisor está acotado por kT/C</td><td>Aparece al calcular su rama ÷7.67 (§4)</td><td><b>Corrige cifras nuestras</b>: el ÷20 aporta 91 µV, no 864 µV. Las decisiones siguen en pie</td><td><span class="tag t-crit">Corregido</span></td></tr>
      <tr><td>Divisor fijo único (revisión A)</td><td>÷20.6 permanente y sólo 6 ganancias de hardware; las demás, por software (§3)</td><td>Viable a 200 kHz; a 1.5 MHz exigiría ×1000 y multiplicaría ×20 el ruido de los amplificadores</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Posición vertical digital</td><td>Sin offset analógico: el ADC ve 20 mV por división y la pantalla es una ventana (§6)</td><td>Opción para la sección E: se ahorra el DAC/PWM de offset a cambio de resolución</td><td><span class="tag t-open">Decidir</span></td></tr>
      <tr><td>Rieles y masas por canal</td><td>L de 100 µH + 10 µF por riel y por canal; AGND1/AGND2 unidas por resistencias de 0 Ω (§9)</td><td>Con tres canales, para limitar la diafonía</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Regulador aparte para VDDA</td><td>Un BL8060 sólo para la referencia del ADC (§9)</td><td>Revisar en la sección G / F</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Generador con dos trucos de GPIO</td><td>Filtro de reconstrucción que conecta un pin; offset de dos niveles con otro pin (§7)</td><td>El primero sirve para nuestro AWG; el segundo se queda corto</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Disparo externo y salida de disparo</td><td>Entrada LVTTL hasta 15 V con umbral de 1.65 V, y TRIGOUT (§8)</td><td>Funciones baratas que no teníamos en la lista</td><td><span class="tag t-open">Decidir</span></td></tr>
      <tr><td>Actualización por el bootloader de fábrica</td><td>BOOT0/BOOT1 + UART, sin bootloader propio (§8)</td><td>Idea: que el ESP32 reprograme el STM32 por su bootloader de fábrica</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Protocolo con modo texto</td><td>Órdenes legibles «nombre = valor», consulta con «?» y pasos ++/-- (§10)</td><td>Ya tenemos SCPI: confirma la elección</td><td><span class="tag t-ok">Confirmado</span></td></tr>
    </tbody>
  </table></div>
""", ("t-open", "Con propuestas")))

S.append(sec("fuentes", "i", "Qué se analizó y cómo", """
  <dl class="kv">
    <dt>Carpeta</dt><dd><code>research_and_tests/Wave2/</code>, reorganizada por Keneth el 23 sep. Material nuevo: dos versiones de la placa principal, el firmware <code>113-15801-092.hex</code>, <code>Wave2_SerialInterface.pdf</code> y <code>WAVE2_HowToUpgradeFirmware.pdf</code>.</dd>
    <dt>Placa analógica</dt><dd>Dos revisiones: <b>105-15801-00E</b> (oct 2018) y <b>105-15803-00A</b> (oct 2019).</dd>
    <dt>Placa principal</dt><dd><b>00G</b> (nov 2018), <b>00J</b> (jul 2019) y <b>00M</b> (nov 2020, el <code>105-15800-00M.pdf</code> suelto). Más las placas 117 (interruptor), 118 (cargador) y 161 (interfaz).</dd>
    <dt>Método</dt><dd>El mismo que con el DSO112: esquemáticos renderizados con PyMuPDF y leídos por zonas, tablas del protocolo extraídas y firmware descodificado. Los esquemas de esta página son redibujos propios, revisados con el comprobador y a la vista.</dd>
    <dt>Especificaciones</dt><dd>Los documentos locales no traen tabla de especificaciones; las oficiales vienen de la web del fabricante (fuentes al pie).</dd>
  </dl>
  <ol class="toc">
    <li><a href="#que-es">Qué es y cómo está repartido</a></li><li><a href="#rev-e">Canal analógico, revisión E</a></li>
    <li><a href="#rev-a">Canal analógico, revisión A</a></li><li><a href="#ruido">El ruido de un divisor: corrección</a></li>
    <li><a href="#p7">¿Nos sirve el grueso sin relé?</a></li><li><a href="#offset">Offset vertical digital</a></li>
    <li><a href="#generador">Generador</a></li><li><a href="#sistema">Placa principal y sistema</a></li>
    <li><a href="#energia">Alimentación y masas</a></li><li><a href="#protocolo">Protocolo serie</a></li>
    <li><a href="#firmware">Firmware</a></li><li><a href="#evitar">Lo que no conviene copiar</a></li>
  </ol>
"""))

S.append(sec("que-es", "1", "Qué es y cómo está repartido", """
  <div class="tw"><table>
    <thead><tr><th>Dato</th><th>WAVE2</th><th>DSO112A</th><th>S3G4 rev 2.1</th></tr></thead>
    <tbody>
      <tr><td>Canales</td><td>2</td><td>1</td><td>3</td></tr>
      <tr><td>Ancho de banda</td><td><b>200 kHz</b></td><td>2 MHz</td><td>1.5 MHz</td></tr>
      <tr><td>Muestreo en tiempo real</td><td>1 MSa/s</td><td>2.5 MSa/s</td><td>6.5 / 3.47 MSa/s</td></tr>
      <tr><td>Escalas</td><td>5 mV – 20 V/div</td><td>5 mV – 20 V/div</td><td>5 mV – 10 V/div</td></tr>
      <tr><td>Máx. entrada · Zin</td><td>50 Vpk · 1 MΩ / 25 pF</td><td>50 Vpk · 1 MΩ</td><td>50 Vpk · 1 MΩ</td></tr>
      <tr><td>Generador</td><td>2 canales, 0–20 kHz, hasta 3 Vpk</td><td>sólo señal de prueba</td><td>AWG hasta 1 MHz</td></tr>
      <tr><td>Registro</td><td>1024 puntos</td><td>512 / 1024</td><td>—</td></tr>
    </tbody>
  </table></div>
  <p>Dos microcontroladores, con el mismo reparto que el DSO112 pero con más peso en el ayudante:</p>
  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  AN["Placa analógica<br/>2 canales"] -->|"CH1ADC · CH2ADC"| F103["STM32F103CB<br/>captura, pantalla,<br/>microSD, USB"]
  F100["STM32F100<br/>táctil, botones,<br/>energía, generador"] -->|"74HC595 por SPI de software"| AN
  F103 -->|"MCO: reloj de 8 MHz"| F100
  F103 ---|"UART"| F100
  F100 -->|"DAC ×2"| GEN["Salidas A y B<br/>TL082"]
  F103 --- LCD["TFT 2.4 pulgadas<br/>bus de 8 bits"]
  F103 --- SD["microSD por SPI"]
  F103 --- EXT["Disparo externo<br/>y TRIGOUT"]
</pre>
  <p>El F103 captura los dos canales con sus ADC internos, que reciben CH1ADC y CH2ADC por 100 Ω en PA0 y PA1. El F100 gobierna la placa analógica a través de un 74HC595: acoplo y selección de escala de los dos canales.</p>
"""))

S.append(sec("rev-e", "2", "Canal analógico, revisión E (2018): el grueso sin relé", fig(W.rev_e(),
  "Redibujo del canal 1 de la placa 105-15801-00E. El canal 2 es idéntico y usa la otra mitad del mismo 74HC4053.") + """
  <p>Es la pieza que motivó esta revisión. El DSO112 usa un relé porque su rama ×1 conecta la entrada directamente al buffer y hay que desconectarla cuando no se usa. El WAVE2 lo evita así:</p>
  <ul class="tight">
    <li><b>Dos divisores compensados, los dos siempre conectados.</b> Rama A: 1.8 MΩ / 270 kΩ, ÷7.67. Rama B: 2.0 MΩ / 20 kΩ, ÷101. En paralelo dan 1.02 MΩ.</li>
    <li><b>Cada rama tiene su propio buffer.</b> El de la rama A tiene ganancia ×7.67 (R35 1 kΩ / R36 150 Ω), así que la rama A queda en ×1 neto, pero su amplificador <b>nunca ve la tensión completa de la BNC</b>. El de la rama B es un seguidor.</li>
    <li><b>El 74HC4053 conmuta después de los buffers</b>, en baja impedancia. La capacidad del interruptor abierto, que era el problema de conmutar tomas de un divisor (el «fallo B» de nuestro análisis), aquí no importa.</li>
    <li><b>Protección:</b> ninguna rama deja pasar más que microamperios; no hay clamps.</li>
  </ul>
  <p>Detrás del 4053: U1A ×2 → escalera de <b>601 Ω</b> (300, 150, 91, 30, 15, 15 Ω) con las mismas seis tomas que el DSO112 (1…1/40) → 74HC4051 → U1B ×8 con un desplazamiento fijo de +1.67 V hacia la mitad del ADC. Salen <b>12 escalas de hardware</b>, como en el DSO112. Todo con un TL084 por canal (3 MHz de GBW), coherente con 200 kHz de banda. Cada canal lleva dos condensadores ajustables: C3 y C5.</p>
"""))

S.append(sec("rev-a", "3", "Canal analógico, revisión A (2019): simplificar", """
  <p>Un año después JYE rehízo la placa en la dirección contraria: menos piezas.</p>
  <div class="tw"><table>
    <thead><tr><th></th><th>Revisión E (2018)</th><th>Revisión A (2019)</th></tr></thead>
    <tbody>
      <tr><td>Entrada</td><td>dos divisores, dos buffers, 74HC4053</td><td><b>un divisor fijo ÷20.6</b> (1 MΩ ∥ 1 pF / 51 kΩ ∥ 25 pF ajustable)</td></tr>
      <tr><td>Tras el buffer</td><td>×2 y escalera de 6 tomas</td><td>escalera 1/5, 1/20, 1/100 (1019 Ω) y dos etapas de ×4.92 y ×4</td></tr>
      <tr><td>Selector</td><td>74HC4051 con 6 tomas</td><td>74HC4051 con 6 señales, <b>una entrada a masa</b> y una libre</td></tr>
      <tr><td>Etapa final</td><td>×8 + 1.67 V</td><td>×4.11 + 1.67 V</td></tr>
      <tr><td>Ganancias de hardware</td><td>12</td><td><b>6, separadas ×5</b></td></tr>
      <tr><td>Tensión por división en el ADC</td><td>80 mV (≈ 99 códigos), calculado desde el esquemático</td><td><b>20 mV (≈ 25 códigos)</b></td></tr>
      <tr><td>Ajustables por canal</td><td>2</td><td>1</td></tr>
    </tbody>
  </table></div>
  <p><b>Verificado contra el protocolo.</b> La Tabla 5 de <code>Wave2_SerialInterface.pdf</code> da la «ganancia analógica» de cada escala: 4, 2, 1, 0.4, 0.2, 0.1, 0.04, 0.02, 0.01, 0.004, 0.002 y 0.001. Las ganancias de la revisión A calculadas desde el esquemático son 3.93, 0.98, 0.20, 0.039, 0.0096 y 0.0020, justo las de 5 mV, 20 mV, 0.1 V, 0.5 V, 2 V y 10 V/div. <b>Las otras seis escalas no tienen hardware propio: salen de la escala vecina por software</b>, escalando ×2 o ×2.5, algo posible porque sobra rango en el ADC.</p>
  <p>¿Por qué pudieron simplificar tanto? Porque a 200 kHz el ruido de un divisor fijo y la ganancia que exige no son un problema. A nuestros 1.5 MHz sí (§4, §5).</p>
"""))

S.append(sec("ruido", "4", "El ruido de un divisor: una corrección importante", """
  <p>Al calcular el ruido de la rama A del WAVE2 me di cuenta de que <b>lo había calculado mal en todo el rediseño</b>. Había tratado el ruido térmico de las resistencias del divisor como ruido blanco hasta 1.5 MHz. Pero en un divisor compensado, los condensadores cortocircuitan ese ruido por encima de la frecuencia de esquina R·C, que está en decenas de kHz. El total queda acotado por <b>√(kT/C)</b> de la capacidad del nodo:</p>
  <div class="tw"><table>
    <thead><tr><th>Divisor</th><th>R del nodo</th><th>C del nodo</th><th>Esquina</th><th>Antes (blanco)</th><th>Real (kT/C)</th></tr></thead>
    <tbody>
      <tr><td>Nuestro ÷20 (sección B)</td><td class="n">47.4 kΩ</td><td class="n">200 pF</td><td class="n">16.8 kHz</td><td class="n">864 µV</td><td class="n"><b>91 µV</b></td></tr>
      <tr><td>÷100 de la propuesta P1</td><td class="n">9.9 kΩ</td><td class="n">1000 pF</td><td class="n">16.1 kHz</td><td class="n">1965 µV</td><td class="n"><b>202 µV</b></td></tr>
      <tr><td>WAVE2 E, rama A ÷7.67</td><td class="n">235 kΩ</td><td class="n">28 pF</td><td class="n">24 kHz</td><td class="n">734 µV</td><td class="n"><b>93 µV</b></td></tr>
      <tr><td>WAVE2 A, ÷20.6 fijo</td><td class="n">48.5 kΩ</td><td class="n">26 pF</td><td class="n">126 kHz</td><td class="n">896 µV</td><td class="n"><b>250 µV</b></td></tr>
    </tbody>
  </table></div>
  <p class="meta">Ruido referido a la entrada con 1.5 MHz de banda. Calculado integrando R ∥ C con el polo del sistema; coincide con √(kT/C) multiplicado por la atenuación.</p>
  <h3>Qué cambia y qué no</h3>
  <ul class="tight">
    <li><b>Cambian las cifras.</b> «El ÷20 fijo deja la escala de 5 mV/div en el 17 % de división» era falso: el divisor aporta un 1.8 %. Lo que de verdad pesa es que <b>multiplica ×20 el ruido de los amplificadores</b> que vienen detrás y obliga a una ganancia ×1000. Con eso el total es ≈ 0.32 mV rms, <b>≈ 6 %</b> de división: sigue siendo peor que el 0.3 % de la rama ×1.</li>
    <li><b>No cambian las decisiones.</b> D-05 (rama ×1) y D-06 siguen justificadas, por el ruido de los amplificadores y por la ganancia necesaria.</li>
    <li><b>Ya corregido</b> en <code>S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html</code> (D-05, aviso de B.8 y tabla de C.5) y en <code>S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html</code> (tabla de P1), con notas visibles de corrección.</li>
    <li><b>Abre una puerta:</b> con el modelo correcto, un divisor pequeño bufferizado deja de ser inaceptable. Eso hace viable la propuesta de la sección siguiente.</li>
  </ul>
""", ("t-crit", "Corrección")))

S.append(sec("p7", "5", "¿Nos sirve el grueso sin relé? Propuesta P7", """
  <p>Adaptado a nuestra especificación, el esquema de la revisión E queda así: <b>rama fina ÷2</b> (1 MΩ / 1 MΩ, 10 pF / 10 pF) y <b>rama gruesa ÷200</b> (1.99 MΩ / 10 kΩ), cada una con su buffer de entrada FET, y <b>un solo 74HC4053</b> que conmuta los tres canales detrás de los buffers. La escalera es la del DSO112 (1…1/40) y la ganancia fija sube a ×100. La relación 100 entre ramas mantiene la serie 1-2-5 de 5 mV a 20 V/div, y deja libres las entradas de masa y VCHECK del 4051, como en P1 y P3.</p>
  <div class="tw"><table>
    <thead><tr><th></th><th>Con relé (P1 + P2 + P4)</th><th>Sin relé (P7)</th></tr></thead>
    <tbody>
      <tr><td>Piezas por canal</td><td>relé + transistor + diodo</td><td>un amplificador de entrada más</td></tr>
      <tr><td>Piezas comunes</td><td>—</td><td>un 74HC4053 para los tres canales</td></tr>
      <tr><td>Consumo</td><td>monoestable: 100–140 mW por canal en escalas finas; latching: sólo pulsos</td><td>~30 mW por canal, siempre</td></tr>
      <tr><td>Ruido a 5 mV/div</td><td class="n">15 µV · 0.3 %</td><td class="n">42 µV · 0.8 %</td></tr>
      <tr><td>Ruido a 500 mV/div</td><td class="n">1.5 mV · 0.3 %</td><td class="n">3.1 mV · 0.6 %</td></tr>
      <tr><td>Ganancia fija</td><td>×50</td><td>×100 (dos etapas de ×10)</td></tr>
      <tr><td>Sobrevive a la red</td><td>en ÷100 siempre; en ×1 sólo con las piezas de alta tensión de P2</td><td><b>en todas las escalas</b>: cada rama es un divisor de ≥ 1 MΩ (0.35 mA, 0.12 W con 353 V)</td></tr>
      <tr><td>Ajustes de fábrica</td><td>1 ajustable por canal</td><td>2 ajustables por canal (o condensadores C0G muy ajustados)</td></tr>
      <tr><td>Piezas mecánicas</td><td>un relé por canal</td><td>ninguna</td></tr>
    </tbody>
  </table></div>
  <div class="callout w"><b>La limitación de P7.</b> En las escalas gruesas, si la entrada pasa de <b>±11.2 V</b> la rama fina recorta en sus clamps y empieza a consumir corriente: la impedancia de entrada efectiva baja a 820 kΩ con 20 V y a 735 kΩ con 40 V. Con una fuente de baja impedancia el error es despreciable (0.4 % con 10 kΩ de fuente a 40 V). Con una <b>sonda ×10</b>, cuya impedancia es de 9 MΩ, la forma de onda se deforma a partir de ±112 V en la punta. Hay que escribirlo en la especificación.</div>
  <p><b>Lectura:</b> P7 cumple los dos deseos con los que empezó este rediseño —sin relés y protección contra la red— a cambio de algo más de ruido (0.8 % frente a 0.3 %, los dos por debajo de un par de LSB) y una limitación acotada. Antes de elegirlo conviene <b>simularlo en LTspice</b>: el recorte de la rama fina, la compensación de las dos ramas con las parásitas reales y el ruido. La carpeta <code>Simulation_LTSpice/</code> ya existe.</p>
""", ("t-open", "Decidir")))

S.append(sec("offset", "6", "Offset vertical: la alternativa digital", """
  <p>La revisión A no tiene offset analógico. Suma 1.67 V fijos para centrar la señal en el ADC y hace que cada división valga sólo 20 mV en el ADC. El convertidor ve así ~165 divisiones y la pantalla es una ventana que se mueve por software. Se ahorra todo el circuito de posición vertical a cambio de resolución (≈ 25 códigos por división).</p>
  <p>Con nuestro ADC de 12 bits el reparto es más cómodo. Opciones para la sección E:</p>
  <div class="tw"><table>
    <thead><tr><th>8 divisiones ocupan…</th><th>Códigos por división</th><th>Margen digital fuera de pantalla</th><th>Offset analógico</th></tr></thead>
    <tbody>
      <tr><td>2.0 V (C.1 actual)</td><td class="n">≈ 410</td><td class="n">±1 div</td><td>necesario (PWM o DAC)</td></tr>
      <tr><td>1.0 V</td><td class="n">≈ 205</td><td class="n">±6 div</td><td>opcional</td></tr>
      <tr><td>0.5 V</td><td class="n">≈ 102</td><td class="n">±16 div</td><td>innecesario en la práctica</td></tr>
    </tbody>
  </table></div>
  <p>Incluso con 0.5 V seguimos teniendo cuatro veces la resolución del WAVE2 y del DSO112, y la ganancia fija necesaria se reduce en la misma proporción, lo que alivia el ancho de banda de C.4. La contrapartida es que un nivel de continua grande en una escala sensible sólo se puede mirar con acoplo AC.</p>
""", ("t-open", "Para la sección E")))

S.append(sec("generador", "7", "Generador", fig(W.generador(),
  "Redibujo de la salida del canal A (placa principal 00J). El canal B es igual, con PA5, U17B y LFB.") + """
  <p>Dos canales desde los DAC del STM32F100, <b>de 0 a 20 kHz</b>, amplitud de 0 a 3 V de pico, senoidal, cuadrada, diente de sierra o escalera, con ciclo de trabajo y desfase entre canales. El protocolo sólo admite <b>dos valores de offset, 0 o 3.3 V</b>.</p>
  <ul class="tight">
    <li><b>Filtro de reconstrucción conmutable con un pin:</b> C34 va a un GPIO. A nivel bajo, el condensador forma con R73 un paso bajo de 16.9 kHz que suaviza los escalones del DAC; en alta impedancia, el filtro desaparece. Sirve para nuestro AWG: filtro fuerte en frecuencias bajas y sin filtro en las altas, sin interruptor analógico.</li>
    <li><b>Offset con otro pin:</b> R67 lleva la entrada inversora del TL082 a un GPIO. A 0 V no hay offset; a 3.3 V se restan 3.3 V a la salida. Por eso sólo hay dos niveles. Para nosotros se queda corto.</li>
    <li><b>100 Ω en serie</b> a la salida, contra cortocircuitos breves.</li>
  </ul>
"""))

S.append(sec("sistema", "8", "Placa principal y sistema", """
  <div class="tw"><table>
    <thead><tr><th>Micro</th><th>Funciones</th></tr></thead>
    <tbody>
      <tr><td>STM32F103CB</td><td>ADC de los dos canales (PA0, PA1); TFT por bus de 8 bits (PB0–PB7 y PC13–PC15); microSD por SPI1; USB nativo (placas 00G y 00J); EEPROM 24LC32A por I²C; disparo externo en PB9 y salida de disparo TRIGOUT en PB10; da su reloj por MCO al otro micro</td></tr>
      <tr><td>STM32F100</td><td>Táctil resistivo, cinco botones y un codificador rotatorio; control de la placa analógica por 74HC595; generador con sus dos DAC; señal de prueba de 1 kHz (3.3 V o 0.14 V); vigilancia de batería y USB; apagado</td></tr>
    </tbody>
  </table></div>
  <ul class="tight">
    <li><b>Disparo:</b> el F103 no tiene comparador analógico, así que el disparo interno debe hacerse con el ADC; su «perro guardián analógico» sirve para eso. No lo he comprobado en el firmware. El externo es LVTTL: el firmware habla de 1.65 V de umbral y el manual de 15 V como máximo.</li>
    <li><b>Actualización:</b> se puentean BOOT0 y BOOT1 en el puerto auxiliar y se usa el bootloader grabado de fábrica en el STM32 con la aplicación de ST, a través de un convertidor USB-UART. <b>Idea para nosotros:</b> si el ESP32-S3 controla BOOT0 y NRST del G473, puede reprogramarlo por su bootloader de fábrica, es decir, actualizar el STM32 por WiFi. Hay que comprobar esos pines en el mapa firmado.</li>
    <li><b>Evolución de la placa principal:</b> la 00G usaba módulos soldados para el cargador (JYE118) y el interruptor (JYE117). La 00J añadió la EEPROM y diodos ESD PESD5V0 en las cuatro líneas del táctil. La 00M (2020) integró el cargador LTC4054 en la placa y cambió el USB nativo por un CH340N. Son los cambios típicos de un producto que se fabrica en serie: menos módulos, protección donde hubo fallos y el USB que menos problemas da.</li>
  </ul>
"""))

S.append(sec("energia", "9", "Alimentación y masas", """
  <ul class="tight">
    <li><b>Rieles:</b> un elevador AX5511 para V+ y un inversor MC34063 para V− (−7 V), igual que el DSO112. En la placa analógica, 78L05 y 79L05.</li>
    <li><b>Filtrado por canal:</b> cada riel de cada canal pasa por su propia bobina de 100 µH con 10 µF (AV1+, AV1−, AV2+, AV2−). Así un canal no contamina al otro por la alimentación.</li>
    <li><b>Masas por canal:</b> AGND1 y AGND2 son redes distintas, unidas a la masa general por resistencias de 0 Ω (R33, R34). Es una masa en estrella que se puede abrir para pruebas.</li>
    <li><b>VDDA aparte:</b> dos BL8060-3.3, uno para la lógica y otro sólo para VDDA, la alimentación analógica y referencia del ADC.</li>
    <li><b>Encendido y carga:</b> interruptor suave (SI2301 + 8550 + 3904, placa 117) y cargador LTC4054 (placa 118), el mismo concepto que el DSO112.</li>
  </ul>
  <p>Para nuestros tres canales, los dos primeros puntos son baratos y deberían entrar en la sección G.</p>
"""))

S.append(sec("protocolo", "10", "Protocolo serie", """
  <ul class="tight">
    <li><b>Modo texto:</b> órdenes legibles del tipo <code>Vsen2 = 5mV</code>, <code>TB = 0.2ms</code> o <code>trigsrc = ch2</code>; consulta con <code>?</code>; órdenes de paso <code>FREQ++</code>, <code>AMP--</code> con tamaño de paso configurable; y órdenes de acción (HOLD, RUN, SENDDATA, SAVEWF…). Hay además un modo binario con los mismos parámetros codificados.</li>
    <li><b>La Tabla 5 incluye la ganancia analógica de cada escala.</b> Documentar la ganancia real junto al código de la escala es una buena práctica: con ella se pudo verificar este análisis.</li>
    <li>La tabla de velocidades llega a <b>2.5 MSa/s</b>, pero la especificación oficial dice 1 MSa/s en tiempo real. Puede ser muestreo entrelazado con los dos ADC en un solo canal o equivalente en el tiempo; <b>no está verificado</b>.</li>
  </ul>
  <p class="meta">Nuestro SCPI cumple el mismo papel que su modo texto. Dos ideas para contrastar con él: las órdenes de paso (útiles para un mando giratorio remoto) y la orden que devuelve frecuencias y medidas de todos los canales en una sola línea.</p>
"""))

S.append(sec("firmware", "11", "Firmware", """
  <ul class="tight">
    <li><code>113-15801-092.hex</code>: 98 816 bytes desde 0x08000000, pila inicial en 0x20005000. Encaja con el STM32F103CB (128 KB de flash, 20 KB de RAM).</li>
    <li>Escrito con la biblioteca Standard Peripheral de ST; usa el perro guardián independiente (IWDG).</li>
    <li>Contiene los mensajes «Read ATSHA204A failed» y un aviso para enviar el PID al soporte: el firmware busca un <b>chip de autenticación ATSHA204A</b> para impedir copias. No aparece en ningún esquemático; mi hipótesis es que se monta en la huella de la EEPROM, que usa el mismo encapsulado y bus. No lo he verificado, y a nosotros no nos afecta.</li>
    <li>Otros textos: «1.65V for Ext. Trigger», «Aux port testing», «Touch Panel Calibration», «STB: Roll», «Pers. OFF».</li>
  </ul>
"""))

S.append(sec("evitar", "12", "Lo que no conviene copiar", """
  <ul class="tight">
    <li><b>Un divisor fijo para las escalas finas</b> (revisión A): a 1.5 MHz exige ×1000 de ganancia y multiplica ×20 el ruido de los amplificadores.</li>
    <li><b>20 mV por división en el ADC:</b> 25 códigos por división desperdician un ADC de 12 bits. Si adoptamos el offset digital, no bajar de ~100 códigos por división.</li>
    <li><b>TL084 en la cadena de señal:</b> 3 MHz de GBW; sirve para 200 kHz, no para nosotros.</li>
    <li><b>Offset del generador de sólo dos niveles.</b></li>
    <li><b>Dos ajustables por canal</b> si se puede evitar: ellos mismos los redujeron en la revisión A.</li>
  </ul>
"""))

HTML = (
 '<title>Anatomía del WAVE2</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el AFE rev 2.1</p>\n  <h1>Anatomía del WAVE2</h1>\n'
 '  <p class="lede">El osciloscopio de dos canales con generador de JYE Tech, heredero del DSO112: cómo resuelve el grueso sin relé, qué simplificó en su segunda revisión y qué nos sirve. Complementa <code>S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html</code> y el documento vivo <code>S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html</code>.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 23 sep 2026. Fuentes locales en <code>research_and_tests/Wave2/</code>. Especificaciones oficiales: '
 '<a href="https://jyetech.com/wave2-2-channel-portable-oscilloscope/">JYE Tech · WAVE2</a> y '
 '<a href="https://www.nooelec.com/store/test-equipment/oscilloscopes/wave2.html">Nooelec · WAVE2</a>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
