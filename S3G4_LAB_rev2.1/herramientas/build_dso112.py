# -*- coding: utf-8 -*-
import io, re, draw_dso112 as D
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/analisis_dso112.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css and ".sx{" in css, "falta el CSS de esquemas"

EXTRA = """
.lesson td:first-child{font-weight:600}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:10px 0;font-size:14px}
.kv dt{color:var(--muted)} .kv dd{margin:0}
pre.mermaid{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:12px;overflow-x:auto}
.asm{font:12.5px/1.5 "IBM Plex Mono",ui-monospace,monospace}
.asm td{padding:3px 9px}
.meta{color:var(--muted);font-size:13px}
.toc{columns:2 260px;column-gap:28px;margin:6px 0 0;padding-left:20px;font-size:14px}
.toc li{break-inside:avoid;margin:2px 0}
.toc a{color:var(--accent);text-decoration:none} .toc a:hover{text-decoration:underline}
"""

def sec(id_, num, title, body, tag=""):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'

def fig(svg, cap):
    return f'  <figure><div class="sx">{svg}</div><figcaption>{cap}</figcaption></figure>\n'

ADOPT = ("t-ok", "Adoptar"); ADAPT = ("t-warn", "Adaptar"); AVOID = ("t-crit", "Evitar"); DECIDE = ("t-open", "Decidir")

S = []

S.append(sec("resumen", "★", "Lo que nos llevamos", """
  <p>Resumen de todo el análisis en una tabla. Cada fila remite a su sección. El veredicto dice qué hacer con la idea en nuestra rev 2.1; <b>nada de esto está decidido</b>, las filas «Decidir» esperan tu respuesta.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el DSO112</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Divisor permanente + rama ×1</td><td>÷100 siempre conectado; el relé elige entre su toma y una rama ×1 (§2)</td><td>Es exactamente nuestra D-05. Confirma la arquitectura</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Rama ×1 con 100 kΩ ∥ 270 pF</td><td>Limita la corriente de falla a 0.45 mA sin recortar el ancho de banda (§2)</td><td>Pasar nuestra rama de 10 kΩ ∥ 10 nF a <b>100 kΩ ∥ 1 nF</b>: diez veces menos corriente en los clamps (P2)</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Grueso ÷100 y escalera de 6 tomas</td><td>12 escalas de 5 mV a 20 V/div con sólo 6 tomas (§4)</td><td>Cambiar nuestro ÷20 por ÷100 libera dos entradas del 4051 (P1)</td><td><span class="tag t-open">Decidir</span></td></tr>
      <tr><td>Entrada del 4051 a masa y VCHECK</td><td>Autocero y comprobación de ganancia sin intervención del usuario (§4)</td><td>Las dos entradas que libera P1 sirven justo para esto (P3)</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>La escalera atenúa y la ganancia es fija</td><td>×20 · ×2 fijos tras el 4051 (§4)</td><td>Es nuestra D-09. Confirmado</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Relé monoestable, reposo en ÷100</td><td>Sin corriente queda en el rango seguro; consume sólo en escalas finas (§2, §8)</td><td>Es la segunda opción de C.2. Elegir entre esto y latching (P4)</td><td><span class="tag t-open">Decidir</span></td></tr>
      <tr><td>Disparo con el comparador del micro</td><td>Comparador analógico del ATmega64 contra un nivel PWM (§6, §7)</td><td>Ya está en nuestro mapa firmado, y mejor: COMP + DAC del G4</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Filtro RC antes del comparador</td><td>1 kΩ / 150 pF (≈ 1 MHz) sólo en el camino del disparo (§6)</td><td>Añadir un RC igual o usar la histéresis del COMP (P5)</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Offset por PWM filtrado</td><td>Tres polos RC y un inversor; se inyecta en la rama de masa de la última etapa (§5)</td><td>Candidato para la sección E, sin el condensador dentro de la red de ganancia (P6)</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>Alimentación: conmutada → LC → lineal</td><td>+7.6 V y −7.1 V conmutados, filtrados y regulados a ±5 V (§8)</td><td>Referencia directa para la sección G</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Interruptor suave y autoapagado</td><td>Un botón, retención por el micro y apagado tras inactividad (§8)</td><td>Encaja con nuestro equipo a batería</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Captura por software a 5 / 2.5 MSa/s, 8 bits, sin anti-alias</td><td>Bucles de instrucciones contadas; 2 MHz de banda con Nyquist de 1.25 MHz (§7)</td><td>Nuestro ADC+DMA del G4, 12 bits y el filtro de la sección D ya lo superan</td><td><span class="tag t-crit">Evitar</span></td></tr>
    </tbody>
  </table></div>
""", ("t-open", "Con propuestas")))

S.append(sec("fuentes-metodo", "i", "Qué se analizó y cómo", """
  <dl class="kv">
    <dt>Esquemático</dt><dd><code>research_and_tests/DSO112/schematic_112g.pdf</code>, documento 105-11200-00G. Hoja 1: digital. Hoja 2: canal analógico y alimentación. El cajetín dice «de 3», pero <b>la hoja 3 no está en el PDF</b>.</dd>
    <dt>Manuales</dt><dd><code>dso112a-user-manual.pdf</code> y <code>dso112a-quick-guide.pdf</code>, del modelo DSO112<b>A</b>. El esquemático es de la placa G: las diferencias entre versiones se señalan donde aparecen.</dd>
    <dt>Firmware</dt><dd><code>113-11201-211.hex</code> (programa principal del ATmega64, 56.8 KB) y <code>113-11205-024.hex</code> (su bootloader, 8 KB en 0xE000). El del ATmega48 no está en la carpeta.</dd>
    <dt>Método</dt><dd>Hojas renderizadas a 250–330 ppp con PyMuPDF y leídas por zonas; firmware descodificado desde Intel HEX y desensamblado en las zonas de captura; manual extraído por secciones. Para contrastar: DSO150 (<code>105-15006-00A.pdf</code>) y DSO138 mini (<code>dso138-mini-schematic-analog-j.pdf</code>).</dd>
    <dt>Límites</dt><dd>No hay placa física: todo es análisis de documentos. Donde un trazo del esquemático es ambiguo lo digo. Los esquemas de esta página son <b>redibujos propios</b> con los designadores del original, no copias.</dd>
  </dl>
  <ol class="toc">
    <li><a href="#arquitectura">Arquitectura</a></li><li><a href="#entrada">Canal de entrada</a></li>
    <li><a href="#buffer">Buffer y lazo de corrección</a></li><li><a href="#ganancia">Escalera, selector y ganancia</a></li>
    <li><a href="#offset">Offset y posición vertical</a></li><li><a href="#adc">ADC, disparo y frecuencímetro</a></li>
    <li><a href="#captura">Cómo captura: el firmware</a></li><li><a href="#energia">Alimentación y energía</a></li>
    <li><a href="#sistema">Sistema digital y protocolo</a></li><li><a href="#funciones">Funciones de usuario</a></li>
    <li><a href="#evitar">Lo que no conviene copiar</a></li><li><a href="#propuestas">Propuestas para la rev 2.1</a></li>
    <li><a href="#comparativa">DSO112, OpenScope y S3G4</a></li><li><a href="#correcciones">Correcciones a lo dicho antes</a></li>
  </ol>
"""))

S.append(sec("arquitectura", "1", "Arquitectura", """
  <p>Dos microcontroladores. El <b>ATmega64</b> hace el trabajo de osciloscopio: captura, disparo, pantalla, USB y memoria. El <b>ATmega48</b> es un ayudante: lee el táctil resistivo, vigila batería y USB, gobierna el botón de encendido y genera la señal de prueba. Hablan entre sí por una UART (<code>KEYCMD</code> / <code>KEYDATA</code>), y el ATmega48 toma el reloj del ATmega64.</p>
  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  J6["MCX J6"] --> CPL["Acoplo AC/DC<br/>C21 + PhotoMOS"]
  CPL --> DIV["Divisor ÷100<br/>992 k / 10 k"]
  CPL --> X1["Rama ×1<br/>100 k ∥ 270 pF"]
  DIV --> RLY["Relé TQ2"]
  X1 --> RLY
  RLY --> BUF["Buffer J309 + Q4<br/>servo U7B"]
  BUF --> LAD["Escalera 1 kΩ<br/>6 tomas"]
  LAD --> MUX["74HC4051<br/>+ GND + VCHECK"]
  MUX --> G1["U6A ×20"]
  G1 --> G2["U6B ×2<br/>+ offset PWM"]
  G2 --> ADC["TLC5510<br/>8 bits"]
  G2 --> CMP["Comparador<br/>del ATmega64"]
  G2 --> FC["Contador T1"]
  ADC --> M64["ATmega64 20 MHz"]
  CMP --> M64
  FC --> M64
  M64 --- LCD["TFT 2.4 pulgadas<br/>bus de 8 bits"]
  M64 --- M48["ATmega48<br/>táctil, energía,<br/>señal de prueba"]
  M64 --- USB["CP2102 USB"]
  M64 --- EE["AT24C1024<br/>presets y forma de onda"]
</pre>
  <p class="meta">El canal completo cabe en dos amplificadores dobles (LM6172 y TL084), un 4051, un JFET, cuatro transistores y un relé. Todo lo que puede hacer el micro (nivel de disparo, offset, reloj del ADC, frecuencímetro, comparador) lo hace el micro.</p>
"""))

S.append(sec("entrada", "2", "Canal de entrada", fig(D.entrada(),
  "Redibujo de la hoja 2, zona superior izquierda. Estado dibujado: relé en reposo (÷100) y acoplo en AC.") + """
  <h3>Acoplo AC / DC</h3>
  <p><b>C21</b> (0.1 µF, 100 V) va en serie con la entrada y el <b>PhotoMOS RLY1</b> (CPC1017N) la cortocircuita. El LED se alimenta desde +3.3 V por R24 (1 kΩ) y el micro lo enciende poniendo <code>CPLSEL</code> a cero: <b>CPLSEL = 0 → DC; CPLSEL = 1 o flotante → AC</b>. El condensador está delante del divisor, por eso necesita 100 V; el nuestro va detrás y le bastan 50 V. <b>No hay posición GND en hardware</b>: se hace por software con la entrada I/O0 del 4051 (§4).</p>

  <h3>Divisor permanente y rama ×1: es nuestra D-05</h3>
  <p>El nodo N1 alimenta a la vez un <b>divisor ÷100</b> (R37 910 k + R38 82 k sobre R40 10 k: 1002 kΩ, relación 100.2) y una <b>rama ×1</b> (R31 100 kΩ con C22 270 pF en paralelo). El relé RLY2A sólo elige qué nodo llega al buffer. El divisor no se desconecta nunca, así que la impedancia de entrada es ≈ 1 MΩ en las dos posiciones. <b>Es la misma topología que adoptamos en la sección C</b>, con otra relación (÷100 frente a nuestro ÷20).</p>

  <h3>Cómo protege</h3>
  <ul class="tight">
    <li><b>En ÷100</b>, el propio divisor limita: 50 V entre 1 MΩ son 50 µA.</li>
    <li><b>En ×1</b>, R31 limita: (50 − 5.6) V ÷ 100 kΩ = 0.44 mA. C22 la puentea en alta frecuencia, así que R31 <b>no recorta el ancho de banda</b>. La constante 100 k · 270 p = 27 µs está emparejada con R50 (10 MΩ) y la capacidad de la puerta (~2.7 pF): el mismo razonamiento que nuestra R_S ∥ C_S.</li>
    <li><b>La sujeción la hace el JFET.</b> Hacia arriba, la unión puerta-drenador del J309 conduce contra AV+; hacia abajo, D1 (1N4148) contra AV−. No hay TVS ni BAV199: con 0.44 mA, la unión del JFET (máx. 10 mA) basta.</li>
  </ul>

  <h3>El relé</h3>
  <p>RLY2A es un <b>TQ2 monoestable de una bobina</b>. Los pines 5 y 6 de la bobina y los tres del segundo polo (RLY2B) están marcados sin conexión. En reposo el contacto está en <b>1/100</b>; la bobina se alimenta sólo en las escalas finas, desde <code>VRAW</code> (la batería) a través de L1 (100 µH) y el transistor Q7, gobernado por <code>SENSEL3</code>. Es decir: <b>sin alimentación, el equipo está en el rango seguro</b>, y paga el consumo de la bobina sólo mientras se usan las escalas de 5 a 200 mV/div. No se ve diodo de rueda libre en la bobina (§11).</p>

  <h3>La compensación no cuadra con los valores nominales</h3>
  <p>El ÷100 necesita C<sub>abajo</sub> = 3 pF × 992 k ÷ 10 k ≈ <b>298 pF</b>. En la placa hay C25 150 pF + C64 15 pF (por JP2) + C24 ajustable de hasta 25 pF: <b>≤ 190 pF</b>. Con esos valores sólo se compensa si la capacidad efectiva de arriba es ~1.9 pF, no 3 pF. No encuentro qué lo explica en el dibujo; el valor impreso de C23 puede no ser el montado. Para nosotros no cambia nada: la condición de compensación es la de la sección B.</p>
"""))

S.append(sec("buffer", "3", "Buffer discreto y lazo de corrección", """
  <p>El buffer está hecho con piezas sueltas, como en el Rigol DS1054Z:</p>
  <div class="tw"><table>
    <thead><tr><th>Pieza</th><th>Función</th><th>Valor clave</th></tr></thead>
    <tbody>
      <tr><td><code>Q3</code> J309</td><td>Seguidor de fuente: altísima impedancia de entrada</td><td>corriente fijada por Q6</td></tr>
      <tr><td><code>R28</code></td><td>Aísla la fuente del JFET de la base de Q4; evita oscilaciones</td><td>100 Ω</td></tr>
      <tr><td><code>Q4</code> MMBT3904</td><td>Seguidor de emisor: entrega la corriente que pide la escalera de 1 kΩ</td><td>—</td></tr>
      <tr><td><code>Q5</code> + R26 / R46 / R45</td><td>Fuente de corriente para Q4</td><td>(10 V · 5.1/15.1 − 0.65) / 510 Ω ≈ <b>5.4 mA</b></td></tr>
      <tr><td><code>Q6</code> + R43 / R44</td><td>Fuente de corriente para el JFET, <b>ajustada por el lazo U7B</b></td><td>R44 150 Ω</td></tr>
    </tbody>
  </table></div>
  <h3>El lazo U7B: por qué hace falta y cómo funciona</h3>
  <p>La tensión de trabajo de un J309 varía mucho de una pieza a otra y con la temperatura, así que la salida del buffer tendría un offset de cientos de mV distinto en cada placa. U7B (TL084) lo corrige despacio:</p>
  <ul class="tight">
    <li>Su entrada <b>+</b> ve la salida del buffer filtrada: R47 10 MΩ · C33 0.1 µF = <b>1 s</b>.</li>
    <li>Su entrada <b>−</b> ve la continua de la puerta a través de R50 10 MΩ, filtrada por C35 (también 1 s). Por R50 no circula corriente en continua, así que ese nodo copia la continua de la entrada.</li>
    <li>Integra la diferencia (C37 0.01 µF) y mueve la base de Q6, que cambia la corriente del JFET y con ella su tensión puerta-fuente.</li>
  </ul>
  <p><b>Resultado:</b> la continua de salida iguala a la de entrada. Offset cero sin ajuste, y sin borrar la componente continua de la señal, porque compara salida con entrada y no con masa. Es el precio de un buffer discreto: con un amplificador FET integrado (nuestra propuesta de C.7) el offset ya es de pocos mV y este lazo sobra.</p>
"""))

S.append(sec("ganancia", "4", "Escalera, selector y ganancia", fig(D.ganancia(),
  "Redibujo de la hoja 2, zona superior. Los nombres X1_n son los de las redes del original.") + """
  <h3>La escalera: los mismos valores que la nuestra</h3>
  <p>Cadena de <b>997.7 Ω</b> (R27 499, R29 249, R32 150, R34 49.9, R39 24.9, R41 24.9 Ω) con tomas en 1, 1/2, 1/4, 1/10, 1/20 y 1/40. Errores de relación ≤ 0.2 %. Llegamos a 1 kΩ por nuestra cuenta en C.3, con valores casi idénticos.</p>

  <h3>Las 8 entradas del 4051 no son 8 escalas</h3>
  <div class="tw"><table>
    <thead><tr><th>Entrada</th><th>I/O0</th><th>I/O1</th><th>I/O2</th><th>I/O3</th><th>I/O4</th><th>I/O5</th><th>I/O6</th><th>I/O7</th></tr></thead>
    <tbody><tr><td>Señal</td><td><b>masa</b></td><td>1/40</td><td>1/20</td><td><b>VCHECK</b></td><td>1/10</td><td>1/1</td><td>1/4</td><td>1/2</td></tr></tbody>
  </table></div>
  <ul class="tight">
    <li><b>I/O0 a masa.</b> Con ella el micro mide el offset de toda la cadena posterior (4051, U6A, U6B, ADC) cuando quiera: <b>autocero</b>. Y es también como se implementa el acoplo «GND» del menú, sin pieza extra.</li>
    <li><b>I/O3 = VCHECK</b>: AREF (2.56 V, la referencia interna del ATmega64) dividida por R72 10 kΩ y R68 75 Ω = <b>19.1 mV</b>. Tras la ganancia fija son ~0.76 V en el ADC (~97 códigos). Sirve para <b>comprobar la ganancia</b> sin señal externa. El firmware contiene una pantalla «Test Mode», que el manual no documenta, con lecturas V0/V50, Vavr en DC y en AC, Vext, Vraw y Vchr, que encaja con este uso de fábrica.</li>
  </ul>

  <h3>Ganancia fija ≈ ×40</h3>
  <p>U6A (LM6172): 1 + R30/R35 = 1 + 1430/75 = <b>×20.07</b>; con 100 MHz de GBW le quedan ~5 MHz. U6B: 1 + R33/(R36 + R42) = <b>×1.99</b> en continua. Total ≈ <b>×39.95</b>. A 5 mV/div eso da 0.2 V por división en el ADC; los 2 V de su rango equivalen a <b>10 divisiones</b>, y quedan 25.6 códigos por división.</p>

  <h3>Las 12 escalas</h3>
  <div class="tw"><table>
    <thead><tr><th>Relé</th><th colspan="6">Toma de la escalera</th></tr></thead>
    <tbody>
      <tr><td></td><td>1/1</td><td>1/2</td><td>1/4</td><td>1/10</td><td>1/20</td><td>1/40</td></tr>
      <tr><td><b>1/1</b></td><td>5 mV</td><td>10 mV</td><td>20 mV</td><td>50 mV</td><td>0.1 V</td><td>0.2 V</td></tr>
      <tr><td><b>1/100</b></td><td>0.5 V</td><td>1 V</td><td>2 V</td><td>5 V</td><td>10 V</td><td>20 V</td></tr>
    </tbody>
  </table></div>
  <p>El salto de 0.2 V a 0.5 V/div (×2.5) mantiene la secuencia 1-2-5: por eso la relación gruesa es 100 y no otra. El DSO112A anuncia también <b>2 mV/div</b>, pero no hay hardware para ella: la toma de mayor ganancia ya es la de 5 mV/div. <b>Deduzco</b> que es una ampliación digital, con ~10 códigos por división.</p>
"""))

S.append(sec("offset", "5", "Offset y posición vertical", """
  <p>El micro no tiene DAC. La posición vertical sale de un <b>PWM filtrado</b>:</p>
  <div class="tw"><table>
    <thead><tr><th>Etapa</th><th>Piezas</th><th>Polo</th></tr></thead>
    <tbody>
      <tr><td>RC de entrada</td><td><code>VPOS_PWM</code> → R53 510 kΩ · C38 0.1 µF</td><td class="n">3.1 Hz</td></tr>
      <tr><td>Seguidor</td><td>U7D (TL084)</td><td>—</td></tr>
      <tr><td>Inversor con filtro</td><td>U7A: R52 100 kΩ, R48 100 kΩ ∥ C34 0.1 µF</td><td class="n">16 Hz</td></tr>
      <tr><td>Inyección</td><td>R42 100 Ω · C26 0.1 µF → R36 909 Ω → entrada − de U6B</td><td class="n">16 kHz</td></tr>
    </tbody>
  </table></div>
  <p>El truco es <b>dónde</b> se inyecta: en la rama de masa de la red de ganancia de U6B. El offset se suma a la salida con ganancia −R33/(R36 + R42) ≈ −0.99 sin tocar la entrada de señal. De paso centra la señal bipolar en el rango unipolar del ADC (0.6–2.6 V). El inversor U7A convierte el PWM (0 a 3.3 V) en 0 a −3.3 V, que U6B vuelve a invertir.</p>
  <div class="callout w"><b>Un efecto secundario que no debemos copiar.</b> C26 está dentro de la red de ganancia. En continua, la rama de masa de U6B ve R36 + R42 = 1009 Ω → ×1.99; por encima de ~16 kHz, C26 cortocircuita la unión y ve sólo R36 = 909 Ω → ×2.10. Con los valores nominales hay un <b>escalón de ganancia del +5.5 %</b> a partir de ~16 kHz. O compensa algo que no se ve en el dibujo, o es un defecto. La lección para nuestra sección E: filtrar el PWM antes, fuera de la red de ganancia.</div>
  <p class="meta">Un PWM tan filtrado tarda del orden de 0.2 s en asentarse: vale para mover la traza, no para cambiar el offset durante una captura.</p>
"""))

S.append(sec("adc", "6", "ADC, disparo y frecuencímetro", """
  <h3>TLC5510</h3>
  <ul class="tight">
    <li><b>8 bits, hasta 20 MSa/s</b>; aquí trabaja a 5 MSa/s como máximo.</li>
    <li><b>Rango de 0.6 a 2.6 V sin referencia externa</b>: VRTS unido a VRT y VRBS a VRB, la autopolarización interna del chip.</li>
    <li>Reloj <code>ADCLK</code> desde una salida de comparación del Timer1 del ATmega64 (PB6/OC1B): el instante de muestreo lo fija el hardware, no el software.</li>
    <li>Las 8 salidas pasan por resistencias de 1 kΩ (RN1, RN2): el ADC funciona a 5 V y el micro a 3.3 V, y las resistencias limitan la corriente por los diodos de protección del micro. Es un adaptador de niveles improvisado.</li>
    <li>Entrada con R19 100 Ω / C13 100 pF: aísla el muestreador del amplificador. Corta en 16 MHz: <b>no es un filtro anti-alias</b>.</li>
  </ul>
  <h3>Disparo: el comparador del micro</h3>
  <p>Nivel de disparo: <code>TLVL_PWM</code> (PB4/OC0) → R7 100 kΩ · C1 0.1 µF (10 ms) → <b>AIN0</b> (PE2). Señal: <code>ANALOG</code> → R16 1 kΩ · C12 150 pF (≈ 1 MHz, quita ruido al disparo) → <code>ANALOGA</code> → PF3/ADC3, que el multiplexor del ADC puede llevar a la <b>entrada negativa del comparador analógico</b>. El pin AIN1 queda libre. El firmware consulta la bandera de ese comparador dentro del bucle de captura (§7).</p>
  <h3>Frecuencímetro</h3>
  <p><code>ANALOG</code> → R73 1 kΩ ∥ C57 150 pF → C5 10 µF → polarizado a 1.65 V por R12/R14 (2 MΩ + 2 MΩ) → <b>T1</b> (PD6), la entrada de reloj externo del Timer1. <code>CNT_EN</code> (PE5/OC3C) está unido a <b>ICP1</b> (PD4): todo indica que un temporizador abre la ventana de medida y otro captura la cuenta, aunque no lo he comprobado en el firmware. La entrada digital sólo conmuta con señales de al menos ~1/3 de pantalla.</p>
"""))

S.append(sec("captura", "7", "Cómo captura: el firmware", """
  <p>Un AVR de 20 MHz no tiene DMA. El DSO112 captura con <b>bucles de instrucciones contadas</b>. Encontré el rápido en la dirección <code>0x0CF7C</code> del programa principal:</p>
  <div class="tw"><table class="asm">
    <thead><tr><th>Instrucción</th><th>Ciclos</th><th>Qué hace</th></tr></thead>
    <tbody>
      <tr><td>SBIC PINB,6 / RJMP −2</td><td>—</td><td>Espera a que ADCLK esté en bajo</td></tr>
      <tr><td>SBIS PINB,6 / RJMP −2</td><td>—</td><td>Espera el flanco de subida: <b>sincroniza el bucle con el reloj del ADC</b></td></tr>
      <tr><td>IN r24, PINC</td><td>1</td><td>Lee los 8 bits del TLC5510 (puerto C)</td></tr>
      <tr><td>ST X+, r24</td><td>2</td><td>Guarda en SRAM desde 0x0800 y avanza</td></tr>
      <tr><td>NOP</td><td>1</td><td>Completa 4 ciclos</td></tr>
      <tr><td>… ×8 por vuelta, cierre con CP / BRNE</td><td>32 por vuelta</td><td>512 o 1024 muestras (2 o 4 páginas de 256 B)</td></tr>
    </tbody>
  </table></div>
  <ul class="tight">
    <li><b>4 ciclos por muestra a 20 MHz = 5 MSa/s.</b> El reparto dentro de la vuelta es 4-4-4-4-4-4-3-5, pero da igual: quien muestrea es el ADC con su reloj de hardware; el software sólo tiene que leer cada palabra mientras es válida.</li>
    <li><b>Con disparo es la mitad.</b> El bucle de pre-disparo (<code>0x0D00C</code>) añade <code>SBIC ACSR,4</code> para vigilar la bandera del comparador y reinicia el puntero al llegar al final: búfer circular. Son 8 ciclos por muestra, <b>2.5 MSa/s</b>. De ahí salen los «2.5 MSPS en tiempo real» del manual frente a los «5 Msps» de la guía rápida.</li>
    <li><b>Bases de tiempo lentas:</b> otros bucles (0x0D09C y siguientes) generan el reloj del ADC por software, con <code>OUT PORTB</code> y NOPs.</li>
    <li>El ATmega64 corre a <b>20 MHz con 3.3 V</b>, por encima de lo que garantiza su hoja de datos: funciona, pero fuera de especificación.</li>
  </ul>
  <div class="callout"><b>La consecuencia que importa:</b> con disparo muestrea a 2.5 MSa/s (Nyquist 1.25 MHz) y anuncia 2 MHz de banda sin filtro anti-alias. Una señal entre 1.25 y 2 MHz se ve con una frecuencia falsa. Nosotros hacemos lo mismo por hardware (ADC + DMA + COMP + temporizadores del G4) a 6.5 / 3.47 MSa/s, con 12 bits y un filtro diseñado en la sección D.</div>
"""))

S.append(sec("energia", "8", "Alimentación y energía", """
  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  VBUS["USB 5 V"] -->|"LTC4054 · 500 mA"| BAT["Li-ion 3.7 V<br/>1200 mAh"]
  VBUS -->|"D3 Schottky"| P["Nodo de carga"]
  BAT -->|"Q8 SI2301"| P
  P -->|"Q9 SI2301<br/>interruptor suave"| VRAW["VRAW"]
  VRAW -->|"AX5511 elevador"| VP["V+ 7.6 V"]
  VP -->|"L5 + 78L05"| AVP["AV+ 5 V"]
  VRAW -->|"MC34063 inversor"| VN["V− −7.1 V"]
  VN -->|"L2 + 79L05"| AVN["AV− −5 V"]
  VRAW -->|"MIC5255"| D33["+3.3 V"]
  VRAW --> COIL["Bobina TQ2 vía L1"]
</pre>
  <div class="tw"><table>
    <thead><tr><th>Bloque</th><th>Cómo</th><th>Cálculo</th></tr></thead>
    <tbody>
      <tr><td>Carga</td><td>LTC4054, lineal; LED de carga en nCHRG</td><td>1000 V ÷ R71 2 kΩ = <b>500 mA</b></td></tr>
      <tr><td>Selección USB / batería</td><td>USB por D3; batería por Q8 (P-MOS) cuya puerta ve VBUS: con USB se apaga, sin USB conduce</td><td>diodo ideal con 1 transistor</td></tr>
      <tr><td>Encendido</td><td>Q9 (P-MOS) + Q10: el botón SW1 enciende, el micro mantiene con <code>PWREN</code> y lee el botón por <code>PWRSW</code></td><td>autoapagado: 2 min por defecto</td></tr>
      <tr><td>Riel positivo</td><td>AX5511 elevador → L5 100 µH → 78L05</td><td>1.2 · (1 + 330 k/62 k) = <b>7.59 V</b> → 5 V</td></tr>
      <tr><td>Riel negativo</td><td>MC34063 inversor (su GND va a V−) → L2 100 µH → 79L05</td><td>1.25 · (1 + 4.7 k/1 k) = <b>7.13 V</b> → −5 V</td></tr>
      <tr><td>Quién usa qué</td><td>LM6172 en V± (±7 V, más margen); JFET, 4051 y TL084 en AV± (±5 V); micros en 3.3 V</td><td>—</td></tr>
      <tr><td>Vigilancia</td><td>VBAT, VEXT y VCHR a entradas analógicas del ATmega48</td><td>divisores 10 k / 1.43 k = <b>0.125</b></td></tr>
    </tbody>
  </table></div>
  <p><b>Consumo total declarado: menos de 300 mA con 3.7 V</b> (~1.1 W), autonomía de unas 4 h con 1200 mAh. El esquema responde a la pregunta de la sección G: <b>conversión conmutada → filtro LC → regulador lineal</b>. Los amplificadores rápidos van a rieles más anchos que los analógicos lentos, y la bobina del relé va directa a la batería, sin pasar por ningún regulador.</p>
"""))

S.append(sec("sistema", "9", "Sistema digital, conectores y protocolo", """
  <dl class="kv">
    <dt>ATmega64</dt><dd>Puerto A: bus de 8 bits del TFT. Puerto C: datos del ADC. Puerto B: <code>SENSEL0–3</code>, <code>TLVL_PWM</code>, <code>CPLSEL</code>, <code>ADCLK</code>, <code>VPOS_PWM</code>. UART0 al CP2102 (USB) y UART1 al ATmega48. I²C a la EEPROM. PF1 lleva un puente de configuración (JP1).</dd>
    <dt>ATmega48</dt><dd>Táctil resistivo de 4 hilos en ADC0–3, retroiluminación, VCHR/VEXT/VBAT, <code>PWRSW</code>/<code>PWREN</code>, señal de prueba (<code>TESTSIN</code> en OC1B) y su amplitud (<code>TS_AMP1/2</code>, <code>TS_CAP</code>). Su firmware se identifica como TS11202.</dd>
    <dt>J5, conector doble</dt><dd>Sale la señal de prueba (3.3 V, 1 kΩ de salida; 1 Hz a 1 MHz y 440 Hz) y entra el disparo externo (0–15 V), según el modo. Un par complementario FDC6333 conmuta el pin. El detalle de cómo se reparten R76 (0 Ω) y TS_CAP es ambiguo en el dibujo.</dd>
    <dt>Integración</dt><dd>J8 botón remoto, J9 alimentación de 4.5–5.5 V, J10 USB alternativo, J11 UART LVTTL con 3.3 V. El equipo está pensado para usarse como módulo dentro de otro sistema.</dd>
    <dt>Arranque</dt><dd>El bootloader espera unos 2 s una orden de actualización por USB (herramienta AVRUBD); después arranca el programa, muestra versión 2 s y permite entrar al modo de ajuste (fábrica o calibración del táctil).</dd>
  </dl>
  <h3>Protocolo serie</h3>
  <ul class="tight">
    <li>115200 8N1. Tramas con <b>byte de sincronía 0xFE</b>, identificador, longitud de 16 bits y carga útil en little endian. Si un dato vale 0xFE se transmite seguido de 0x00 (<b>relleno de bytes</b>), así la sincronía nunca aparece dentro de la carga.</li>
    <li>Órdenes: consulta de modelo, conectar y desconectar el <b>modo USB Scope</b> (apaga la pantalla y envía los datos), leer los rangos de cada parámetro, leer y escribir parámetros, y órdenes especiales (mediciones, valores de fábrica, alineación de offset, presets).</li>
    <li>Datos: con 20 ms/div o más rápido, <b>un bloque con todo el búfer</b> por trama; con 50 ms/div o más lento, <b>una muestra por trama</b>, en modo desplazamiento.</li>
    <li>Mediciones en enteros de 16 bits con signo, en unidades de <b>20 µV (VBU)</b>, y frecuencia en 32 bits sin signo: <b>sin coma flotante en el protocolo</b>.</li>
  </ul>
  <p class="meta">Nuestro S3G4-IP ya cubre este papel entre ESP32 y STM32. Ideas que podemos contrastar con él: el relleno de bytes, el «modo remoto» que libera la pantalla local, la orden que devuelve los rangos válidos de cada parámetro y la unidad fija de tensión.</p>
"""))

S.append(sec("funciones", "10", "Funciones de usuario", """
  <p>Lista para comparar con la especificación de nuestra interfaz:</p>
  <div class="tw"><table>
    <thead><tr><th>Grupo</th><th>DSO112A</th></tr></thead>
    <tbody>
      <tr><td>Disparo</td><td>AUTO, NORM y SING; flanco de subida o de bajada; interno o externo; posición en 1/8, 1/4, 1/2, 3/4 o 7/8 del búfer; SING pasa a HOLD al disparar</td></tr>
      <tr><td>Captura</td><td>512 o 1024 puntos; bases de 1 µs/div a 50 s/div; modo HOLD con el botón</td></tr>
      <tr><td>Mediciones</td><td>Vmax, Vmin, Vpp, Vmedia, Vrms verdadero y frecuencia; se desactivan desde 50 ms/div</td></tr>
      <tr><td>Cursores</td><td>ΔT y ΔV con lectura</td></tr>
      <tr><td>Memoria</td><td>24 presets con nombre, una forma de onda guardada en EEPROM y envío como CSV</td></tr>
      <tr><td>Calibración</td><td>«VPos Cal» (alineación del cero), calibración del táctil, restauración de fábrica y pantalla oculta de prueba</td></tr>
      <tr><td>Energía</td><td>Autoapagado a 2, 5, 15, 30 o 60 min, o nunca; sólo con batería</td></tr>
      <tr><td>Señal de prueba</td><td>1 Hz, 10 Hz, 100 Hz, 440 Hz, 1 kHz, 10 kHz, 100 kHz o 1 MHz, cuadrada de 3.3 V</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("evitar", "11", "Lo que no conviene copiar", """
  <ul class="tight">
    <li><b>8 bits:</b> 25.6 códigos por división. Nosotros tenemos ~410 con 12 bits.</li>
    <li><b>Error de sensibilidad de hasta el 5 %</b>, según su guía rápida. La calibración por escala con VCHECK y autocero debería bajarlo mucho.</li>
    <li><b>Ancho de banda por encima de Nyquist sin filtro anti-alias</b> (§7).</li>
    <li><b>Micro fuera de especificación:</b> 20 MHz con 3.3 V.</li>
    <li><b>Niveles mezclados:</b> ADC a 5 V hacia un micro de 3.3 V por resistencias de 1 kΩ, y reloj de 3.3 V hacia una entrada de 5 V.</li>
    <li><b>Bobina de relé sin diodo de rueda libre visible.</b> Un transistor que corta una bobina sin diodo sufre un pico de tensión en cada cambio. El nuestro lo llevará.</li>
    <li><b>Condensador dentro de la red de ganancia</b> para filtrar el offset (§5).</li>
    <li><b>Un solo canal</b> y búfer de 1024 puntos.</li>
  </ul>
"""))

S.append(sec("propuestas", "12", "Propuestas para la rev 2.1", """
  <p>Ninguna está aplicada. Cada una dice qué decisión tocaría.</p>

  <h3>P1 · Grueso ÷100 en vez de ÷20 <span class="tag t-open">Decidir</span></h3>
  <p>Con ÷100 y la escalera del DSO112 (1, 1/2, 1/4, 1/10, 1/20, 1/40) salen <b>12 escalas, de 5 mV a 20 V/div, con sólo 6 tomas</b>. Las mismas cuentas de C.1: a 500 mV/div, 4 Vpp ÷ 100 × 1 × 50 = 2.0 V; a 10 V/div, 80 Vpp ÷ 100 ÷ 20 × 50 = 2.0 V.</p>
  <div class="tw"><table>
    <thead><tr><th></th><th>÷20 (sección C actual)</th><th>÷100 (propuesta)</th></tr></thead>
    <tbody>
      <tr><td>Tomas de la escalera</td><td>8: no sobra ninguna</td><td><b>6: sobran 2</b> para masa y VCHECK</td></tr>
      <tr><td>Escalas</td><td>11 (5 mV – 10 V/div)</td><td><b>12 (5 mV – 20 V/div)</b></td></tr>
      <tr><td>Nodo protegido con ±40 V</td><td>±2 V</td><td><b>±0.4 V</b></td></tr>
      <tr><td>Nodo con 353 V (red)</td><td>17.6 V → los clamps conducen</td><td><b>3.5 V → los clamps ni se enteran</b></td></tr>
      <tr><td>Compensación</td><td>C<sub>abajo</sub> ≈ 190 pF: las parásitas pesan ~13 %</td><td>C<sub>abajo</sub> ≈ 990 pF: pesan ~2.5 %</td></tr>
      <tr><td>Rama ×1 en uso</td><td>5 – 100 mV/div</td><td>5 – 200 mV/div</td></tr>
      <tr><td>Ruido en la primera escala del divisor</td><td>~0.5 % div (200 mV/div)</td><td>~0.5 % div (500 mV/div)</td></tr>
    </tbody>
  </table></div>
  <p>Valores: arriba 3 × 330 kΩ (116 V cada una con 353 V) y 3 × 30 pF; abajo 10.0 kΩ y ≈ 990 pF. Zin = 1.000 MΩ. <b>Tocaría D-09 y las tablas de C.1, C.3 y C.6</b>; D-05 (±40 V) no cambia. La única contrapartida es que la rama ×1 vuelve a usarse hasta 200 mV/div, como en el DSO112.</p>

  <h3>P2 · Rama ×1 con 100 kΩ ∥ 1 nF <span class="tag t-ok">Adoptar</span></h3>
  <p>Hoy: 10 kΩ ∥ 10 nF. Propuesta: <b>100 kΩ ∥ 1.0 nF</b>, la misma τ = 100 µs, emparejada con R_BIAS 10 MΩ × ~10 pF. En continua la relación es 10 M ÷ 10.1 M = 0.9901; en alta frecuencia, 1 n ÷ 1.01 n = 0.9901. Si C_in varía entre 7 y 13 pF, el desajuste queda en ±0.3 %.</p>
  <ul class="tight">
    <li>Corriente con 50 V: <b>0.44 mA</b> en vez de 4.4 mA. Con los tres canales, 1.3 mA hacia los rieles en vez de 13 mA: <b>desaparece el aviso de C.7 para la sección G</b>.</li>
    <li>R_S disipa 20 mW con 50 V: sirve una 0805.</li>
    <li>Su ruido térmico lo cortocircuita C_S por encima de 1.6 kHz, como antes.</li>
    <li><b>Opción de bajo coste que cerraría el hueco de D-06:</b> R_S como dos 1206 de 49.9 kΩ en serie y C_S de 1 nF C0G de ≥ 630 V (o dos de 2.2 nF de 250 V en serie). Con 250 Vrms la rama ×1 disiparía ~0.31 W por resistencia durante ≤ 10 s y los clamps recibirían 3.5 mA de pico: <b>sobreviviría a la red también en las escalas finas</b>. Hay que confirmar en JLCPCB la tensión y la sobrecarga de corta duración de las piezas, y que el relé aguante ≥ 400 V entre contactos abiertos.</li>
  </ul>

  <h3>P3 · Autocero y VCHECK <span class="tag t-ok">Adoptar si P1</span></h3>
  <p>Con las dos entradas libres de P1: <b>I/O a masa</b> para medir el offset de la cadena de ganancia y el ADC cuando el equipo quiera, y <b>VCHECK</b> para comprobar la ganancia. Un divisor desde la referencia del ADC (2.5 V × 100 / 12.5 k ≈ 20 mV) daría ~1 V en el ADC con la ganancia ×50: cuatro divisiones. Sin P1 habría que añadir un segundo 4051 o renunciar a una escala.</p>

  <h3>P4 · Relé: monoestable con reposo en el divisor, o latching <span class="tag t-open">Decidir</span></h3>
  <p>El DSO112 eligió el monoestable: sin corriente siempre queda en ÷100. Paga la bobina sólo en las escalas finas y, con P1, las escalas finas son sólo las de 5 a 200 mV/div. El latching ahorra ese consumo, pero depende del firmware para volver al rango seguro. Con cualquiera de los dos: <b>diodo de rueda libre</b>.</p>

  <h3>P5 · Disparo por hardware con un filtro <span class="tag t-warn">Adaptar</span></h3>
  <p>Nuestro mapa ya lleva COMP3 en PA0, COMP1 en PA1 y COMP6 en PD11, con umbrales desde DAC internos. Del DSO112 tomamos el <b>RC de 1 kΩ / 150 pF (≈ 1 MHz)</b> sólo en el camino del comparador, o su equivalente con la histéresis programable del COMP. El frecuencímetro sale del mismo comparador hacia un temporizador, sin piezas extra.</p>

  <h3>P6 · Offset: PWM filtrado, inyectado en la rama de masa <span class="tag t-warn">Adaptar</span></h3>
  <p>Para la sección E, si los DAC siguen asignados a los comparadores: PWM + dos o tres polos RC con un amplificador, inyectado en la rama de masa de la última etapa, como U6B. <b>Sin condensador dentro de la red de ganancia</b>, para no crear el escalón del +5.5 %.</p>
""", ("t-open", "Pendiente de ti")))

S.append(sec("comparativa", "13", "DSO112, OpenScope y S3G4", """
  <div class="tw"><table>
    <thead><tr><th></th><th>DSO112A</th><th>OpenScope MZ</th><th>S3G4 rev 2.1</th></tr></thead>
    <tbody>
      <tr><td>Canales</td><td>1</td><td>2</td><td><b>3</b></td></tr>
      <tr><td>ADC</td><td>TLC5510, 8 bits</td><td>el del PIC32MZ, 12 bits</td><td>STM32G473, 12 bits</td></tr>
      <tr><td>Muestreo</td><td>5 MSa/s; 2.5 con disparo</td><td>6.25 MSa/s máx.</td><td>6.5 MSa/s (CH1) · 3.47 (CH2, CH3)</td></tr>
      <tr><td>Ancho de banda</td><td>2 MHz, sin anti-alias</td><td>no verificado</td><td>1.5 MHz con filtro (sección D)</td></tr>
      <tr><td>Rango</td><td>±50 V útiles (50 Vpk)</td><td>±20 V</td><td><b>±40 V</b> (50 Vpk)</td></tr>
      <tr><td>Escalas</td><td>12 + 2 mV digital</td><td>4 rangos analógicos (1, 1/4, 1/8, 3/40)</td><td>11 (12 con P1) + 20 V/div digital</td></tr>
      <tr><td>Grueso</td><td>relé ×1 / ÷100</td><td>sin rama ×1</td><td>relé ×1 / ÷20 (÷100 con P1)</td></tr>
      <tr><td>Protección de entrada</td><td>R31 + unión del JFET + 1N4148</td><td>ninguna</td><td>divisor + BAV199 + TVS; red en ÷20</td></tr>
      <tr><td>Offset</td><td>PWM filtrado</td><td>PWM filtrado</td><td>sección E pendiente</td></tr>
      <tr><td>Disparo</td><td>comparador del micro + PWM</td><td>—</td><td>COMP + DAC del G4</td></tr>
      <tr><td>Captura</td><td>bucles de software</td><td>ADC + DMA</td><td>ADC + DMA, entrelazado en CH1</td></tr>
    </tbody>
  </table></div>
  <p class="meta">OpenScope: datos de su firmware en <code>research_and_tests/openscope-mz</code> (<code>ParseOpenScope.cpp</code>, <code>OpenScope.h</code>). Donde no hay dato verificado pongo «—» o «no verificado».</p>
"""))

S.append(sec("correcciones", "14", "Correcciones a lo que dije antes", """
  <p>Con el esquemático renderizado se ven cosas que el texto suelto del PDF no mostraba. Cinco afirmaciones mías de sesiones anteriores eran falsas o incompletas:</p>
  <div class="tw"><table>
    <thead><tr><th>Dije</th><th>Lo correcto</th></tr></thead>
    <tbody>
      <tr><td>La compensación del ÷100 del DSO112 «cuadra al 1 %»</td><td>Había tomado C22 (270 pF) como condensador de abajo, pero C22 pertenece a la rama ×1. Con los valores nominales <b>no cuadra</b> (§2).</td></tr>
      <tr><td>El TQ2 es latching de dos bobinas</td><td><b>Monoestable de una bobina</b>; los pines 5 y 6 no se conectan.</td></tr>
      <tr><td>El segundo polo pone a masa la rama no usada</td><td>En el DSO112 <b>el segundo polo no se usa</b>. El DSO150 sí usa los dos, pero para desconectar los dos extremos del divisor que no se usa, no para ponerlo a masa.</td></tr>
      <tr><td>El DSO112 deja la rama ×1 sin proteger</td><td>La protegen <b>R31 (100 kΩ), la unión del J309 y D1</b>, hasta los 50 Vpk declarados.</td></tr>
      <tr><td>Los 200 kHz del DSO138 mini y del DSO150 son el precio de su resistencia de 100 kΩ</td><td><b>Cierto sólo en el DSO150</b>: su R2 es la mitad superior de un divisor ×1.11 con 1 pF, sin compensar, y el polo cae en ~200 kHz. En el <b>DSO138 mini</b>, R1 lleva 220 pF en paralelo y no limita la banda.</td></tr>
    </tbody>
  </table></div>
  <p class="meta">También dije en esta sesión que <code>113-11205-024</code> era el firmware del ATmega48. Es el bootloader del ATmega64. Las decisiones D-05 y D-06 no se ven afectadas por ninguna de estas correcciones.</p>
"""))

HTML = (
 '<title>Anatomía del DSO112</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n'
 '<div class="wrap">\n'
 '<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el AFE rev 2.1</p>\n'
 '  <h1>Anatomía del DSO112</h1>\n'
 '  <p class="lede">Lo que el esquemático, el firmware y el manual del JYE Tech DSO112 enseñan para nuestro rediseño: cómo está hecho cada bloque, con sus valores, qué nos confirma, qué conviene copiar y qué no. Complementa el documento vivo <code>S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html</code>.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 23 sep 2026. Fuentes en <code>research_and_tests/DSO112/</code>; contraste con <code>research_and_tests/105-15006-00A.pdf</code> (DSO150), <code>research_and_tests/dso138-mini-schematic-analog-j.pdf</code> y <code>research_and_tests/openscope-mz/</code>. Direcciones de firmware referidas a <code>113-11201-211.hex</code>.</p></footer>\n'
 '</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML), "bytes")
