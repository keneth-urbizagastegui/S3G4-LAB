# -*- coding: utf-8 -*-
import io, draw_openscope as O
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/analisis_openscope.html"
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
  <p>El OpenScope MZ es el único de nuestros referentes que se diseñó como <b>instrumento multifunción</b>: osciloscopio, generador, fuentes de continua, analizador lógico y WiFi. Su punto fuerte no es el canal analógico, que renuncia a las escalas finas, sino <b>cómo se calibra a sí mismo</b>. Cada fila remite a su sección; nada está decidido.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el OpenScope</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Entrada inversora a tierra virtual</td><td>1 MΩ hacia una tierra virtual, ×0.2; la entrada nunca ve tensión (§2)</td><td>Sin relé y protegida por construcción, pero con un suelo de ruido de 0.56 mV: <b>no sirve para escalas finas</b>. No cambia la decisión P4/P7 (§3)</td><td><span class="tag t-open">Contexto</span></td></tr>
      <tr><td>Ganancia conmutada en la tierra virtual</td><td>TS3A5017 de 3.3 V en un nodo fijo a 1.5 V: sin distorsión (§2)</td><td>Idea para la etapa final: P8</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Filtro anti-alias dentro de la ganancia</td><td>Un condensador por rama de realimentación: 1.3–1.6 MHz (§2)</td><td>Sección D sin etapa aparte: P8</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>La etapa final se alimenta como el ADC</td><td>IC6A a 3.3 V: no puede sacar una tensión que dañe el ADC (§2)</td><td>Sección F</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Referencia única y ratiométrica</td><td>LM4040 de 3.000 V como VREF+ del ADC; de ella salen 3.0 V y 1.5 V con resistencias del 0.1 % (§4)</td><td>Secciones E y F: P9</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Red de realimentación</td><td>El ADC mide rieles, referencias, generador y fuentes con divisores del 0.1 % (§5)</td><td>Autodiagnóstico y base de la autocalibración: P10</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Calibración encadenada</td><td>Referencia → fuentes de continua → entradas del osciloscopio, con detección de cable no conectado (§5)</td><td>Con nuestro AWG en continua como fuente: P10</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Disparo con comparadores del ADC</td><td>Dos umbrales, uno arma y otro dispara: histéresis sobre la muestra digitalizada (§8)</td><td>Alternativa con los analog watchdog del G4: P11</td><td><span class="tag t-open">Estudiar</span></td></tr>
      <tr><td>Generador R-2R con mapa de corrección</td><td>Mide sus 1024 códigos y construye una tabla (§6)</td><td>No hace falta con el DAC del G4; sí la idea de medir y corregir la salida</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Sin acoplo AC en placa</td><td>Sólo DC; un adaptador de terceros lo añade (§10)</td><td>Nuestro D-04 ya lo cubre</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Offset por PWM lento</td><td>500 ms de espera cada vez que cambia (§8)</td><td>Si usamos PWM, filtrar más rápido</td><td><span class="tag t-crit">Evitar</span></td></tr>
    </tbody>
  </table></div>
""", ("t-open", "Con propuestas")))

S.append(sec("fuentes", "i", "Qué se analizó y cómo", """
  <dl class="kv">
    <dt>Esquemático</dt><dd><code>research_and_tests/openscope-mz/openscope-mz-sch-revg.pdf</code>, revisión G, 12 hojas. Su texto no se puede extraer, por eso <b>nunca lo habíamos leído</b>; ahora se renderizó hoja por hoja.</dd>
    <dt>Firmware</dt><dd>Clon del repositorio oficial de Digilent: <code>AnalogIn.c</code>, <code>Trigger.c</code>, <code>AWG.c</code>, <code>DCInstruments.c</code>, <code>FeedBack.c</code>, <code>LA.c</code>, <code>Config.cpp</code>, <code>WiFi.cpp</code>, <code>OpenScope.h</code>, el analizador JSON y la prueba de fabricación.</dd>
    <dt>Aplicación</dt><dd><code>research_and_tests/waveforms-live</code>, versión 1.4.10.</dd>
    <dt>Adaptador</dt><dd><code>OpenScopeMZ-Adapter_Schema.pdf</code> y <code>openscope-Adapter.zip</code> (gerbers): una placa de terceros de 2021.</dd>
    <dt>Especificaciones</dt><dd>Del manual de referencia de Digilent publicado en Farnell (fuente al pie); la web de Digilent rechaza las descargas automáticas.</dd>
    <dt>Método</dt><dd>El mismo que con el DSO112 y el WAVE2. El dibujo es un redibujo propio, revisado con el comprobador y a la vista.</dd>
  </dl>
  <ol class="toc">
    <li><a href="#que-es">Qué es</a></li><li><a href="#canal">Canal analógico</a></li>
    <li><a href="#p4p7">¿Cambia la decisión del grueso?</a></li><li><a href="#referencias">Referencias y alimentación</a></li>
    <li><a href="#calibracion">Realimentación y autocalibración</a></li><li><a href="#generador">Generador</a></li>
    <li><a href="#dc">Fuentes de continua</a></li><li><a href="#captura">Captura y disparo</a></li>
    <li><a href="#protocolo">Protocolo y aplicación</a></li><li><a href="#adaptador">El adaptador de terceros</a></li>
    <li><a href="#evitar">Lo que no conviene copiar</a></li><li><a href="#propuestas">Propuestas</a></li>
  </ol>
"""))

S.append(sec("que-es", "1", "Qué es", """
  <div class="tw"><table>
    <thead><tr><th>Función</th><th>OpenScope MZ</th></tr></thead>
    <tbody>
      <tr><td>Osciloscopio</td><td>2 canales, 12 bits, 6.25 MSa/s, <b>2 MHz a −3 dB</b>, 1 MΩ, <b>±20 V</b>, 32 640 muestras por canal</td></tr>
      <tr><td>Generador</td><td>10 bits, de 1 Hz a 1 MHz, 3 Vpp con ±1.5 V de offset, 10 mA; senoidal, triangular, diente de sierra, cuadrada y continua</td></tr>
      <tr><td>Fuentes de continua</td><td>2 canales, ±4 V, 50 mA</td></tr>
      <tr><td>Analizador lógico / GPIO</td><td>10 canales compartidos, 10 MSa/s</td></tr>
      <tr><td>Conectividad</td><td>WiFi 802.11g (módulo MRF24WG0MA) y USB (FT232RQ); microSD</td></tr>
      <tr><td>Alimentación</td><td><b>Sólo USB de 5 V</b>: regulador de 3.3 V y bomba de carga LM2660 para −5 V. Sin batería</td></tr>
    </tbody>
  </table></div>
  <p>Un único micro, el <b>PIC32MZ</b> a 200 MHz, lo hace todo: captura, generador, fuentes, analizador, pila TCP/IP, servidor HTTP y protocolo JSON. Nosotros lo repartimos entre el STM32 (medida) y el ESP32 (comunicación e interfaz), que es más robusto.</p>
"""))

S.append(sec("canal", "2", "Canal analógico", fig(O.afe(),
  "Redibujo del canal 1 (hoja 4). El canal 2 (hoja 5) es idéntico, con IC8A, IC9A e IC7.") + """
  <h3>Dos etapas inversoras</h3>
  <ul class="tight">
    <li><b>IC5A (LMV116 a ±5 V):</b> R31 de 1 MΩ entra a su tierra virtual. La ganancia es −R30/R31 = <b>−0.2</b> y la impedancia de entrada, 1 MΩ. El amplificador no ve la tensión de la entrada, sólo la corriente que deja pasar R31. C27 (0.3 pF) compensa R30 frente a la capacidad parásita de R31.</li>
    <li><b>IC6A (LMV116 a 3.3 V):</b> sumador inversor con su entrada no inversora en VREF1V5. Al nodo suma S llegan tres cosas: la señal por R32 (3.6 kΩ, puenteada por C28 en alta frecuencia), una corriente fija desde VREF3V0 (centra la salida en el rango del ADC) y el offset desde un PWM.</li>
    <li><b>La ganancia se elige en la realimentación</b> con un TS3A5017, dos multiplexores 4:1 de 3.3 V. Como el conmutador está en la tierra virtual, su tensión es siempre 1.5 V: no distorsiona y basta un chip barato. Su resistencia de ~10 Ω está descontada en el cálculo de cada rama.</li>
    <li><b>La otra mitad del TS3A5017</b> elige la resistencia del offset, así que el recorrido del offset escala con la ganancia.</li>
  </ul>
  <div class="tw"><table>
    <thead><tr><th>Ganancia total</th><th>Realimentación</th><th>Cálculo: 5 · G · 3.6 kΩ</th><th>Polo del condensador</th></tr></thead>
    <tbody>
      <tr><td>×1</td><td>18 kΩ</td><td class="n">18.0 kΩ</td><td>sin condensador</td></tr>
      <tr><td>×1/4</td><td>4.53 kΩ ∥ 22 pF</td><td class="n">4.50 kΩ</td><td class="n">1.60 MHz</td></tr>
      <tr><td>×1/8</td><td>2.26 kΩ ∥ 51 pF</td><td class="n">2.25 kΩ</td><td class="n">1.38 MHz</td></tr>
      <tr><td>×3/40</td><td>1.33 kΩ ∥ 91 pF</td><td class="n">1.35 kΩ</td><td class="n">1.32 MHz</td></tr>
    </tbody>
  </table></div>
  <p>Los condensadores de realimentación <b>hacen de filtro anti-alias</b> de primer orden dentro de la propia etapa de ganancia. La salida pasa por R35 (68 Ω) y C31 (470 pF) y llega <b>a dos pines del ADC a la vez</b> (AN0 y AN1): son los dos convertidores que se entrelazan. Rango de entrada del ADC: 0–3 V.</p>
  <p><b>Toda la ganancia es atenuación:</b> el canal nunca amplifica. Con ×1, los 3 V del ADC corresponden a 3 Vpp en la entrada (≈ 300 mV/div con 10 divisiones); lo que se vea más fino es zoom digital.</p>
"""))

S.append(sec("p4p7", "3", "¿Cambia la decisión del grueso (P4 o P7)?", """
  <p>No. La entrada inversora del OpenScope tiene un <b>suelo de ruido que sale sólo de sus resistencias</b>, y a diferencia de un divisor compensado no hay condensador que lo cortocircuite: R31 va a una tierra virtual y el ruido de R30 aparece directamente en la salida.</p>
  <div class="tw"><table>
    <thead><tr><th>Fuente</th><th>Densidad referida a la entrada</th></tr></thead>
    <tbody>
      <tr><td>R31 (1 MΩ)</td><td class="n">129 nV/√Hz</td></tr>
      <tr><td>R30 (200 kΩ), dividido por la ganancia 0.2</td><td class="n">288 nV/√Hz</td></tr>
      <tr><td><b>Suelo con 2 MHz de banda</b></td><td class="n"><b>≈ 0.56 mV rms</b></td></tr>
    </tbody>
  </table></div>
  <p>Eso es un 0.19 % de división a 300 mV/div, su escala nativa; un 1.1 % a 50 mV/div; y <b>un 11 % a 5 mV/div</b>, sin contar el amplificador. Es decir, la técnica funciona porque renuncia a las escalas finas.</p>
  <div class="tw"><table>
    <thead><tr><th></th><th>DSO112</th><th>WAVE2 rev E</th><th>OpenScope MZ</th></tr></thead>
    <tbody>
      <tr><td>Grueso</td><td>relé ×1 / ÷100</td><td>dos divisores bufferizados + 74HC4053</td><td>ninguno: ÷5 fijo a tierra virtual</td></tr>
      <tr><td>Escala fina real</td><td>5 mV/div</td><td>5 mV/div a 200 kHz</td><td>~300 mV/div; lo demás es zoom</td></tr>
      <tr><td>Equivalente nuestro</td><td>P4 (relé)</td><td>P7 (sin relé)</td><td>—</td></tr>
    </tbody>
  </table></div>
  <p>La elección sigue siendo entre P4 y P7, y conviene simularla. Lo que el OpenScope sí aporta son técnicas para las etapas que vienen <b>después</b> del grueso: P8 y P9.</p>
""", ("t-ok", "Resuelto")))

S.append(sec("referencias", "4", "Referencias y alimentación", """
  <ul class="tight">
    <li><b>Una sola referencia:</b> un LM4040 de 3.000 V, alimentado desde 3.3 V por 56 Ω, es la <b>VREF+ del ADC</b> del PIC32.</li>
    <li>De ese mismo nodo salen <b>VREF3V0</b> (filtrada 10 kΩ · 1 µF y bufferizada con un LMV324) y <b>VREF1V5</b> (divisor de 5.36 k + 4.64 k y 10 k al <b>0.1 %</b>, filtrado y bufferizado).</li>
    <li>Todo el canal se refiere a esas dos tensiones. <b>Si la referencia deriva, la mitad de escala y los offsets derivan igual que el ADC</b> y el error se cancela: diseño ratiométrico.</li>
    <li>El manual lo dice expresamente: el diseño da por buena la referencia de 3 V con su realimentación, resistencias del 0.1 % y condensadores del 10 %, y todo lo demás se calibra.</li>
    <li><b>Alimentación:</b> sólo USB. NCP1117 para 3.3 V y bomba de carga LM2660 para −5 V (sin regular). Un puente elige entre el USB y una entrada de 5 V.</li>
  </ul>
"""))

S.append(sec("calibracion", "5", "Realimentación y autocalibración", """
  <p>La hoja 11 lleva divisores del 0.1 % que llevan al ADC <b>los rieles de 3.3 V, +5 V y −5 V, las dos referencias, la salida del generador y las dos fuentes de continua</b>. Con eso el firmware se calibra en cadena:</p>
  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  REF["LM4040 3.000 V<br/>VREF+ del ADC"] --> ADC["ADC del PIC32<br/>con sobremuestreo"]
  FB["Red de realimentación<br/>divisores 0.1 %"] --> ADC
  DC["Fuentes DC por PWM"] --> FB
  AWG["Generador R-2R"] --> FB
  RAIL["Rieles y referencias"] --> FB
  DC -. "cable del usuario" .-> OSC["Entradas del osciloscopio"]
  OSC --> ADC
</pre>
  <ol class="tight">
    <li><b>Fuentes de continua:</b> las lleva a +3 V y −3 V, mide el valor real por la realimentación y obtiene su recta PWM → tensión.</li>
    <li><b>Generador:</b> calibra su offset y después <b>mide los 1024 códigos</b> de la escalera R-2R, los ordena y guarda una tabla de corrección (§6).</li>
    <li><b>Osciloscopio, por cada una de las 4 ganancias:</b> pide al usuario unir cada fuente de continua a su entrada. La pone a +V y a −V (medidas por la realimentación) y deduce la pendiente <b>A</b>. Si la lectura no cambia, avisa de que el cable no está conectado. Con 0 V a la entrada mueve el PWM de offset y obtiene <b>B</b>; con todo a cero, <b>C</b>. Modelo: Vin = A · código + B · PWM + C.</li>
    <li>Las medidas usan el <b>sobremuestreo por hardware del ADC</b>, y el resultado se guarda como archivo en un sistema FAT de la flash interna (con copia en microSD si la hay).</li>
  </ol>
  <p>La aplicación WaveForms Live tiene una página «calibrate» que guía al usuario. Es la pieza que más nos conviene copiar: con nuestro AWG en modo continua como fuente, y con la masa y VCHECK del 4051 (P3), podríamos calibrar toda la cadena con un solo cable.</p>
""", ("t-ok", "Adoptar")))

S.append(sec("generador", "6", "Generador", """
  <ul class="tight">
    <li><b>DAC de 10 bits hecho con resistencias:</b> una escalera R-2R (1500 Ω y 750 Ω; tres tramos son de 732 Ω, un 2.5 % menores que el resto) conectada a 10 pines del puerto H del PIC32. El DMA escribe el puerto hasta <b>10 MSa/s</b>, con búferes de hasta 25 000 muestras; señales de hasta 1 MHz.</li>
    <li><b>Filtro de reconstrucción:</b> dos RC (750 Ω · 36 pF y 750 Ω · 43 pF) y 5.6 pF en la realimentación del amplificador.</li>
    <li><b>Salida:</b> amplificador inversor MCP6H91 a ±5 V, referido a VREF1V5, con el offset por PWM (OC7) filtrado en dos polos. Rango de ±3 V.</li>
    <li><b>Calibración de la escalera:</b> una escalera de resistencias baratas no es lineal ni siquiera monótona. El firmware mide los 1024 códigos por la realimentación, los ordena y guarda qué código da cada tensión. Así el DAC barato se comporta como uno bueno.</li>
  </ul>
  <p>Nuestro G473 tiene DAC de 12 bits a 15 MSa/s y no necesita la escalera. Sí nos sirve la idea de <b>medir la salida real del generador por la realimentación y corregirla</b>, que cubre también el error de la etapa de salida.</p>
"""))

S.append(sec("dc", "7", "Fuentes de continua", """
  <p>Cada fuente: un PWM → dos RC de 1 kΩ · 4.7 µF y 1 kΩ hacia el nodo suma → amplificador inversor MCP6H82 con ganancia −4 (12 kΩ / 3 kΩ), referido a VREF1V5 y centrado con VREF3V0. Salida de ±4 V y 50 mA. El firmware calcula el PWM con la recta calibrada y verifica el resultado por la realimentación. Nuestro instrumento no tiene fuentes, pero la técnica es la misma que la del offset.</p>
"""))

S.append(sec("captura", "8", "Captura y disparo", """
  <ul class="tight">
    <li><b>Entrelazado:</b> cada canal va a dos ADC dedicados de 12 bits. Un temporizador dispara uno y una salida de comparación, desfasada medio periodo, dispara el otro; dos canales de DMA recogen los datos. Máximo 2 × 3.125 = <b>6.25 MSa/s</b>. Por debajo de ~2 kSa/s usa un solo ADC. Es lo mismo que nuestro ADC1+ADC2 sobre PA0.</li>
    <li><b>Disparo:</b> usa los <b>comparadores digitales del ADC</b>. El primero se arma cuando la muestra cruza un umbral bajo; al dispararse, activa el segundo, que detecta el cruce del umbral alto. Son dos umbrales, es decir histéresis, y se trabaja sobre la misma muestra que se dibuja. Después el firmware afina el punto exacto recorriendo el búfer. El STM32G4 puede hacer lo mismo con sus «analog watchdog».</li>
    <li><b>Analizador lógico:</b> DMA desde el puerto E, 10 MSa/s y 32 K muestras. El disparo digital usa la interrupción por cambio de pin.</li>
    <li><b>Offset:</b> PWM de 303 kHz con 330 pasos (10 mV), filtrado en dos polos de ~72 Hz. Tras cada cambio el firmware <b>espera 500 ms</b> a que se asiente.</li>
  </ul>
"""))

S.append(sec("protocolo", "9", "Protocolo y aplicación", """
  <ul class="tight">
    <li><b>Digilent Instrumentation Protocol:</b> órdenes en JSON agrupadas por objeto (<code>device</code>, <code>osc</code>, <code>awg</code>, <code>dc</code>, <code>la</code>, <code>trigger</code>, <code>file</code>, <code>log</code>, <code>gpio</code>, <code>mode</code>, <code>test</code>). Las formas de onda vuelven como binario dentro de una transferencia fragmentada: un trozo JSON que describe los datos y otro con los datos en bruto.</li>
    <li>El mismo protocolo viaja por <b>HTTP en el puerto 80</b> sobre WiFi o por el puerto serie USB.</li>
    <li>Hay un modo de <b>prueba de fabricación</b> con el mismo formato JSON (<code>"test"</code>).</li>
    <li><b>WaveForms Live</b> (Ionic 2 / Angular 2) tiene páginas de panel de instrumentos, calibración, configuración WiFi, actualización de firmware, registrador de datos, diagrama de Bode, matemáticas y explorador de archivos.</li>
  </ul>
  <p class="meta">Nuestro S3G4-IP es binario y ya tiene SCPI. Para contrastar con él: la separación JSON + binario para las formas de onda, la página de calibración guiada y el modo de prueba de fabricación.</p>
"""))

S.append(sec("adaptador", "10", "El adaptador de terceros", """
  <p>Una placa de 2021 hecha en KiCad (C. Feyer, fpb-synths) para usar el OpenScope con conectores normales. Añade:</p>
  <ul class="tight">
    <li><b>BNC</b> para los dos canales, el disparo y el generador.</li>
    <li><b>Acoplo AC/DC</b> con un puente: 100 nF en serie y 27 MΩ de polarización.</li>
    <li>Entrada de disparo por BNC con un transistor.</li>
    <li>Adaptadores de nivel a 5 V para las líneas digitales.</li>
    <li>Un convertidor ±12 V para las fuentes y un amplificador con salida balanceada para el generador.</li>
  </ul>
  <p>Lo relevante: <b>el OpenScope no tiene acoplo AC en hardware</b> y hubo que añadírselo fuera. Nuestro conmutador AC/DC/GND (D-04) ya lo resuelve en placa.</p>
"""))

S.append(sec("evitar", "11", "Lo que no conviene copiar", """
  <ul class="tight">
    <li><b>Canal que sólo atenúa:</b> sin escalas finas reales.</li>
    <li><b>Una sola resistencia de 1 MΩ</b> como única barrera: limita la corriente, pero una 0805 no aguanta cientos de voltios entre sus terminales.</li>
    <li><b>Sin acoplo AC.</b></li>
    <li><b>Offset por PWM con 500 ms de espera.</b></li>
    <li><b>Un único micro para medir y para la pila TCP/IP.</b></li>
    <li><b>Sólo USB:</b> sin batería.</li>
  </ul>
"""))

S.append(sec("propuestas", "12", "Propuestas para la rev 2.1", """
  <p>Continúan la numeración del DSO112 (P1–P6) y del WAVE2 (P7). Ninguna está aplicada.</p>
  <h3>P8 · Una sola etapa final por canal, al estilo del OpenScope <span class="tag t-open">Decidir</span></h3>
  <p>Un sumador inversor <b>alimentado igual que el ADC</b> que haga a la vez la ganancia fija, el filtro anti-alias de primer orden (condensador de realimentación), el desplazamiento a mitad de escala desde la referencia y la inyección del offset. Las secciones D, E y F quedarían en una etapa por canal, y el ADC quedaría protegido por construcción. Hay que comprobar que un filtro de primer orden basta: con 3.47 MSa/s en CH2 y CH3 el margen hasta Nyquist es corto. Se estudia en la sección D.</p>
  <h3>P9 · Referencia única y ratiométrica <span class="tag t-ok">Adoptar</span></h3>
  <p>La referencia del ADC, sea VREFBUF del G473 o una externa, genera la mitad de escala con un divisor del 0.1 % y un buffer, y todo el canal se refiere a ella. Se decide en la sección F.</p>
  <h3>P10 · Autocalibración encadenada <span class="tag t-ok">Adoptar</span></h3>
  <ul class="tight">
    <li>Divisores del 0.1 % que lleven a canales lentos del ADC la salida del AWG, los rieles y las referencias.</li>
    <li>El AWG en modo continua como fuente de calibración de los tres canales, con un cable del usuario y detección de cable no conectado.</li>
    <li>La masa y VCHECK del 4051 (P3) para la parte interna de la cadena.</li>
    <li>Modelo por escala: Vin = A · código + B · offset + C, guardado en flash, y una pantalla de calibración guiada en la S3G4-UI.</li>
    <li><b>Requisito:</b> pines libres de ADC para la realimentación; hay que revisar el mapa firmado.</li>
  </ul>
  <h3>P11 · Disparo con los analog watchdog del ADC <span class="tag t-open">Estudiar</span></h3>
  <p>Dos umbrales, uno para armar y otro para disparar, sobre la muestra digitalizada, como alternativa o complemento del COMP + DAC del mapa firmado. Hay que resolverlo junto con el entrelazado de CH1 en el firmware.</p>
"""))

HTML = (
 '<title>Anatomía del OpenScope MZ</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el AFE rev 2.1</p>\n  <h1>Anatomía del OpenScope MZ</h1>\n'
 '  <p class="lede">El instrumento multifunción abierto de Digilent: un canal que sólo atenúa, pero una arquitectura de referencia y autocalibración que merece copiarse. Completa la serie con <code>S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html</code> y <code>S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html</code>.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 23 sep 2026. Fuentes locales en <code>research_and_tests/openscope-mz/</code> y <code>research_and_tests/waveforms-live/</code>. Especificaciones: '
 '<a href="https://www.farnell.com/datasheets/2339652.pdf">OpenScope MZ Reference Manual (Farnell)</a> y '
 '<a href="https://www.manualslib.com/manual/1517997/Digilent-Openscope-Mz.html">ManualsLib</a>. Adaptador: '
 '<a href="https://fpb-synths.de/en/projects/openscope-mz-adapter">fpb-synths</a>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
