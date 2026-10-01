# -*- coding: utf-8 -*-
import io, draw_black_scope as B, calc_black_scope as K
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/analisis_black_scope.html"
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
.eq{font-family:"IBM Plex Mono",monospace;font-size:13.5px;background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:8px 12px;margin:10px 0;overflow-x:auto;white-space:pre}
@media (max-width:640px){.kv{grid-template-columns:1fr}.kv dt{margin-top:6px}}
"""
def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def fig(svg, cap):
    return f'  <figure><div class="sx">{svg}</div><figcaption>{cap}</figcaption></figure>\n'
def m(x, n=1):
    return f"{x:.{n}f}".replace("-", "−")

g = K.GAINS
S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>black_scope es el único de nuestros referentes que usa <b>nuestro mismo microcontrolador</b>, el STM32G473VET6. Por eso su valor no está en el canal analógico, que es mínimo, sino en que <b>pone a prueba las partes analógicas internas del G473</b> que nosotros decidimos no usar como etapa principal. Cada fila remite a su sección; nada está decidido.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En black_scope</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>El PGA interno como ganancia del osciloscopio</td><td>OPAMP en PGA ×2…×64 leído por el canal interno del ADC (§3)</td><td>Ancho de banda de {K.bw_pga[64][1]/1e3:.0f} kHz a ×64, ruido de 90 nV/√Hz y muestreo más corto que el mínimo del fabricante. <b>Confirma</b> que el OPAMP interno no sirve de etapa final</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Muestreo del OPAMP interno</td><td>2.5 ciclos = {K.TS_CFG*1e9:.0f} ns; el datasheet pide ≥ {K.TS_OPAMP_MIN*1e9:.0f} ns (§3)</td><td>Si algún día usamos un OPAMP interno hacia el ADC (DMM, batería), programar ≥ 12.5 ciclos</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Entrada de {K.ZIN/1e3:.1f} kΩ</td><td>Divisor resistivo hacia una polarización a mitad de riel (§2)</td><td>Incompatible con sondas ×10, que esperan 1 MΩ. Nuestra entrada ya es de 1 MΩ</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Un único DAC para el offset de los cuatro canales</td><td>DAC2 con buffer cargado con 100 nF: {K.CL_FACTOR:.0f} veces la carga permitida (§4)</td><td>Offset por canal (P6) y, si es continua, DAC en sample-and-hold (P15)</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Disparo con dos analog watchdog</td><td>AWD1 arma y AWD2 dispara; AWD2 sólo tiene 8 bits (§5)</td><td>Confirma P11. La latencia de la interrupción se evita con P12</td><td><span class="tag t-warn">Adaptar</span></td></tr>
      <tr><td>DMA circular + temporizador de parada</td><td>Espera un búfer lleno antes de armar, y dos juegos de búfer alternos (§5)</td><td>Patrón del firmware de captura</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Sólo CH1 dispara</td><td>La interfaz ofrece Ch1–Ch4, pero el código sólo programa el ADC1 (§5)</td><td>Disparo desde cualquier canal</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Reloj del ADC síncrono</td><td>PCLK/4 = {K.FADC/1e6:.1f} MHz: el disparo de TIM2 no añade incertidumbre (§3)</td><td>P13, en la revisión del G473</td><td><span class="tag t-ok">Adoptar</span></td></tr>
      <tr><td>Referencia ratiométrica</td><td>VREF+, el DAC y el divisor de entrada cuelgan del mismo +3.3VA (§7)</td><td>Confirma P9</td><td><span class="tag t-ok">Confirmado</span></td></tr>
      <tr><td>Generador con 512 puntos y prescaler entero</td><td>Error de frecuencia del {(K.gen[10000][0]/10000-1)*100:.1f} % a 10 kHz y el DAC fuera de especificación (§6)</td><td>Nuestro AWG usa DAC3 a 15 MSa/s; conviene un acumulador de fase</td><td><span class="tag t-crit">Evitar</span></td></tr>
      <tr><td>Las notas del autor</td><td>«Cambiar el OPAMP, el ADC y el DAC por otros con más ancho de banda», «arreglar el ruido del ADC» (§9)</td><td>El propio autor llegó a nuestra conclusión</td><td><span class="tag t-ok">Confirmado</span></td></tr>
    </tbody>
  </table></div>
""", ("t-open", "Con propuestas")))

S.append(sec("fuentes", "i", "Qué se analizó y cómo", """
  <dl class="kv">
    <dt>Origen</dt><dd><code>research_and_tests/black_scope</code>, clon de <a href="https://github.com/jgpeiro/black_scope">github.com/jgpeiro/black_scope</a>. <code>black_scope_1</code> es el mismo clon con cambios locales en <code>wavegen.c/.h</code> (añade pulso, rectificada y seno con rizado; quita continua y cuadrada).</dd>
    <dt>Hardware</dt><dd>KiCad 7.0.6: esquemático de una hoja (<code>outputs/pdf/black_scope.pdf</code>, con texto extraíble), netlist <code>black_scope.xml</code> (84 componentes, 137 redes) y BOM del 17 ago 2023.</dd>
    <dt>Firmware</dt><dd><code>software/stm32g4_scope</code> (interfaz Nuklear) y <code>stm32g4_scope_lvgl</code> (interfaz LVGL), ambos con CubeMX 6.9 y FreeRTOS. Se leyeron el <code>.ioc</code>, <code>adc.c</code>, <code>opamp.c</code>, <code>dac.c</code>, <code>stm32g4xx_it.c</code>, <code>Lib/Scope</code>, <code>Lib/Tasks</code>, <code>Lib/WaveGen</code> y <code>Lib/Ui</code>. También <code>test_nucleo_f401re</code> y <code>firmware_15_sep.hex</code>.</dd>
    <dt>Diagramas</dt><dd><code>images/capture engine.png</code> y <code>capture engine 2.png</code>: el autor documenta la máquina de estados de la captura.</dd>
    <dt>Contraste</dt><dd>Cada cifra del G473 se contrastó con DS12712 Rev 5 y RM0440 Rev 9 (la revisión está en <code>S3G4_LAB_rev2.1/02_referencias/g473_analogico.html</code>). Las cifras derivadas salen de <code>S3G4_LAB_rev2.1/herramientas/calc_black_scope.py</code>.</dd>
  </dl>
  <ol class="toc">
    <li><a href="#que-es">Qué es</a></li><li><a href="#canal">Canal analógico</a></li>
    <li><a href="#pga">PGA interno y ADC</a></li><li><a href="#offset">Offset común desde DAC2</a></li>
    <li><a href="#captura">Captura y disparo</a></li><li><a href="#generador">Generador</a></li>
    <li><a href="#proteccion">Protección y alimentación</a></li><li><a href="#software">Firmware</a></li>
    <li><a href="#notas">Las notas del autor</a></li><li><a href="#evitar">Lo que no conviene copiar</a></li>
    <li><a href="#propuestas">Propuesta P12</a></li>
  </ol>
"""))

S.append(sec("que-es", "1", "Qué es", f"""
  <p>Un osciloscopio de <b>cuatro canales</b> y generador de <b>dos canales</b> con una sola placa y un solo microcontrolador. Todo pasa por el STM32G473: la captura, la pantalla y la interfaz táctil.</p>
  <dl class="kv">
    <dt>Entradas</dt><dd>4 canales por un conector de pines <code>J4</code> (2×4, 2.54 mm), sin BNC ni acoplo AC. Rango nominal de unos ±10 V.</dd>
    <dt>Captura</dt><dd>4 ADC (ADC1, ADC3, ADC4, ADC5), uno por canal, 12 bits, hasta 2.5 MSa/s en la interfaz, <b>{K.LEN} muestras por canal</b>.</dd>
    <dt>Generador</dt><dd>DAC1 (PA4, PA5) → LMV358 → 51 Ω → <code>J5</code>.</dd>
    <dt>Pantalla</dt><dd>TFT IPS de 3.5″ con ILI9488 por FMC de 16 bits, táctil resistivo con XPT2046 por SPI3 y PSRAM por QSPI para el framebuffer.</dd>
    <dt>Alimentación</dt><dd>USB-C, batería LiPo (conector JST-PH) con cargador MCP73831 y regulador XC6206 de 3.3 V. <b>No mide la batería</b>, y una nota del autor lo pide.</dd>
    <dt>Caja</dt><dd>Impresa en 3D (OpenSCAD).</dd>
  </dl>
  <p>La arquitectura que dibuja el autor es la de la figura <code>capture engine 2.png</code>: <b>ZIN → LMV324 → PGA → ADC → DMA</b>, con el DAC2 como offset, TIM2 como reloj de muestreo y TIM3 como parada. La misma figura trae un «borrador» sin PGA, del LMV324 directo al ADC por ADC1_IN11/IN12 y ADC3_IN8/IN9: son las rutas directas que la placa tiene cableadas y el firmware no usa.</p>
"""))

S.append(sec("canal", "2", "Canal analógico", fig(B.afe(), "Redibujo propio del canal 1, contrastado con el esquemático y la netlist. Los cuatro canales son iguales.") + f"""
  <h3>El divisor a mitad de riel, paso a paso</h3>
  <p>La entrada ve R5 en serie, y el nodo <code>Vn</code> cuelga de dos resistencias: R11 a +3.3 V y R12 a masa. Por Thévenin, R11 y R12 equivalen a una fuente <code>V<sub>th</sub></code> con una resistencia <code>R<sub>p</sub></code>:</p>
  <div class="eq">R_p  = R11 ∥ R12 = 2.7k ∥ 4.3k = {K.RP/1e3:.4f} kΩ
V_th = 3.3 V · 4.3k / (2.7k + 4.3k) = {K.VTH:.4f} V
Vn   = Vin · R_p/(R5 + R_p) + V_th · R5/(R5 + R_p)
     = {K.G_IN:.5f} · Vin + {K.V0:.4f} V</div>
  <ul class="tight">
    <li><b>Impedancia de entrada:</b> R5 + R<sub>p</sub> = {K.ZIN/1e3:.2f} kΩ, <b>hacia una fuente de {K.VTH:.2f} V</b>. Una sonda ×10 espera 1 MΩ, así que con ésta la atenuación saldría mal.</li>
    <li><b>Rango:</b> el nodo va de 0 a 3.3 V si la entrada va de {m(K.VIN_MIN)} a +{K.VIN_MAX_RAIL:.1f} V. Pero el LMV324 no es rail-to-rail en la entrada: el de TI admite hasta unos V<sub>CC</sub> − 0.8 V, y eso recorta el rango positivo a <b>+{K.VIN_MAX_CM:.1f} V</b>. Es un dato típico de TI; el repositorio no trae la hoja del LMV324 ni dice el fabricante. La nota del autor de pasar al OPA4322, rail-to-rail en entrada y salida, lo corregiría.</li>
    <li><b>Entrada al aire:</b> el nodo se queda en V<sub>th</sub> y la pantalla muestra <b>+{K.VIN_OPEN:.2f} V</b> sin nada conectado. Nuestra entrada, con su resistencia a masa, marca 0 V.</li>
    <li><b>Polo de entrada:</b> C23 con R5 ∥ R11 ∥ R12 = {K.RNODE:.0f} Ω da <b>{K.FC/1e6:.2f} MHz</b>. Es el único filtro anti-alias del canal.</li>
    <li><b>Tolerancia:</b> con resistencias del 0.5 %, el cero de cada canal puede separarse ±{K.DV0*1e3:.1f} mV en el nodo, <b>±{K.DV0_IN*1e3:.0f} mV en la entrada</b>. Como el offset es común (§4), el hardware no puede igualarlos.</li>
  </ul>
  <h3>Ruido</h3>
  <p>El nodo aporta √(4kTR) = {K.EN_R*1e9:.1f} nV/√Hz; el LMV324, unos 39 nV/√Hz (típico de TI); el OPAMP interno, 90 nV/√Hz a 10 kHz y 250 nV/√Hz a 1 kHz (DS12712, tabla 75). El OPAMP interno domina. Referido a la entrada (÷ {K.G_IN:.3f}) y con el ancho de banda de cada ganancia, el resultado ronda <b>{K.noise[2][1]*1e3:.2f} mV rms</b> hasta ×8 y {K.noise[64][1]*1e3:.2f} mV rms a ×64. Frente al tramo de pantalla es poco, del 0.01 % al {K.noise[64][1]/K.span_in[64]*100:.2f} %. Frente a nuestro objetivo de 5 mV/div es mucho: esta cadena no llega a escalas finas por ancho de banda, no por ruido.</p>
"""))

rows = "".join(
    f'<tr><td class="n">×{x}</td><td class="n">{K.span_in[x]:.3f} V</td><td class="n">{K.lsb_in[x]*1e6:.0f} µV</td>'
    f'<td class="n">{K.bw_pga[x][0]/1e3:.0f}–{K.bw_pga[x][1]/1e3:.0f} kHz</td><td class="n">{K.vbias[x]:.4f} V</td>'
    f'<td class="n">{K.trig_step_in[x]*1e3:.1f} mV</td><td class="n">±{K.dv0_adc[x]*1e3:.0f} mV</td></tr>' for x in g)
S.append(sec("pga", "3", "PGA interno y ADC", f"""
  <p>Cada seguidor alimenta a la vez un pin del ADC (ruta directa) y la entrada VINP de un OPAMP interno. El firmware sólo usa el OPAMP: lo pone en <b>PGA con VINM0 como polarización</b> (<code>OPAMP_PGA_CONNECT_INVERTINGINPUT_IO0_BIAS</code>), así que la salida es</p>
  <div class="eq">Vout = G · (VINP − VB) + VB      G ∈ {{2, 4, 8, 16, 32, 64}}</div>
  <p>El ADC la lee por el canal interno (VOPAMP1 en ADC1, VOPAMP3 en ADC3, VOPAMP6 en ADC4 y VOPAMP5 en ADC5). La interfaz no muestra voltios por división: la escala es el índice de ganancia (0–5) y el offset es un código de DAC (0–4095).</p>
  <div class="tw"><table>
    <thead><tr><th>Ganancia</th><th>Tramo de entrada que cabe en el ADC</th><th>1 LSB en la entrada</th><th>Ancho de banda del PGA (GBW/G, mín–típ)</th><th>VB que centra 0 V</th><th>Paso del nivel de disparo (AWD2)</th><th>Desalineo entre canales en el ADC</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>Ancho de banda:</b> el PGA divide el GBW de 7–13 MHz por la ganancia (DS12712, tabla 75). A ×64 quedan {K.bw_pga[64][0]/1e3:.0f}–{K.bw_pga[64][1]/1e3:.0f} kHz. En modo normal el slew rate es de 2.5–6.5 V/µs: una salida de 3.2 Vpp sólo es limpia hasta {K.FPBW_3V[0]/1e3:.0f}–{K.FPBW_3V[1]/1e3:.0f} kHz. El firmware no activa el modo de alta velocidad.</li>
    <li><b>Muestreo demasiado corto:</b> el ADC corre a {K.FADC/1e6:.1f} MHz (PCLK/4) con 2.5 ciclos de muestreo, es decir {K.TS_CFG*1e9:.1f} ns. El datasheet exige <b>≥ {K.TS_OPAMP_MIN*1e9:.0f} ns</b> para leer la salida del OPAMP por el canal interno (<code>TS_OPAMP_VOUT</code>, tabla 75). El primer valor válido a esa frecuencia es 12.5 ciclos, y entonces el máximo baja de {K.FS_CFG/1e6:.2f} a <b>{K.FS_OK/1e6:.2f} MSa/s</b>. La interfaz ofrece hasta {K.UI_MAX/1e6:.1f} MSa/s. Es un buen candidato al «ruido del ADC» que el autor anota.</li>
    <li><b>La ruta directa tampoco es rápida:</b> PB12, PB1, PD11 y PD12 son canales lentos. A 12 bits no admiten 2.5 ciclos (DS12712, tabla 62).</li>
    <li><b>Ganancia:</b> ±1 % hasta ×16 y ±2 % a ×32 y ×64 (tabla 75). El firmware no calibra la ganancia; sólo llama a <code>HAL_OPAMP_SelfCalibrate</code>, que corrige el offset.</li>
    <li><b>Reloj síncrono:</b> <code>ADC_CLOCK_SYNC_PCLK_DIV4</code> quita la incertidumbre entre el disparo de TIM2 y el inicio del muestreo (RM0440 §21.4.3). Es una buena decisión que conviene copiar (P13 en la revisión del G473).</li>
  </ul>
"""))

S.append(sec("offset", "4", "Offset común desde DAC2", f"""
  <p>DAC2_OUT1 (PA6) va por fuera del chip a los cuatro pines VINM0 (PA3, PB2, PB15 y PA1), con R25 de 10 kΩ y C22 de 100 nF a masa. Es un solo nivel VB para los cuatro canales.</p>
  <ul class="tight">
    <li><b>Carga fuera de especificación:</b> con el buffer activado, el DAC admite como mucho 50 pF y 5 kΩ (DS12712, tabla 69). C22 es <b>{K.CL_FACTOR:.0f} veces</b> esa capacidad. Un buffer así cargado puede oscilar o tardar mucho en asentarse. Las notas «añadir pull-down» y «añadir condensador» sugieren que C22 llegó como remedio. El G4 tiene un modo pensado para esto, el <b>sample-and-hold</b>, que admite de 0.1 a 1 µF (tabla 69).</li>
    <li><b>Corriente por VINM0:</b> en modo PGA con polarización, R1 = 10 kΩ va de la entrada inversora a VB. Por cada canal circula (VINP − VB)/R1: con el ADC a fondo, {K.i_bias_pin[2]*1e6:.1f} µA a ×2 y {K.i_bias_pin[64]*1e6:.1f} µA a ×64. Los cuatro canales cargan el mismo nodo, y lo que uno mueve lo ven los otros multiplicado por (G − 1).</li>
    <li><b>Un offset para cuatro canales:</b> el desalineo de §2 multiplicado por la ganancia llega a <b>±{K.dv0_adc[64]*1e3:.0f} mV en el ADC a ×64</b>, un {K.dv0_adc[64]/3.3*100:.0f} % del rango, y no hay forma de corregirlo canal a canal en hardware. Además, a ×64 un solo código del DAC mueve la traza {K.dac_lsb_move[64]*1e3:.0f} mV en el ADC.</li>
  </ul>
"""))

MER = """  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  I["IDLE"] -->|"scope_start: ADC + DMA circular + TIM2"| W["Espera búfer lleno"]
  W -->|"DMA completo: habilita AWD1"| A["Espera armado"]
  A -->|"AWD1: la señal pasa por debajo del nivel"| T["Espera disparo"]
  T -->|"AWD2: la señal cruza el nivel; la ISR arranca TIM3"| P["Espera parada"]
  P -->|"TIM3: len/2 + offset muestras; lee CNDTR y para los DMA"| I
</pre>
"""
S.append(sec("captura", "5", "Captura y disparo", MER + f"""
  <p>Es la máquina de estados de <code>Lib/Scope/scope.c</code>, la misma que el autor dibuja en <code>capture engine 2.png</code>. Los cuatro ADC convierten a la vez con el mismo TIM2 y DMA circular de {K.LEN} muestras por canal.</p>
  <ul class="tight">
    <li><b>Buena idea: esperar un búfer lleno antes de armar.</b> Así siempre hay muestras previas al disparo.</li>
    <li><b>Buena idea: dos juegos de búfer</b> (8 × {K.LEN} × 2 B = {K.BUF_BYTES//1024} KiB): mientras uno se dibuja, el otro se llena.</li>
    <li><b>Arma y dispara con dos analog watchdog</b>, como el OpenScope: para flanco de subida, AWD1 salta cuando la señal está por debajo del nivel y AWD2 cuando lo supera. La histéresis es cero. Además, AWD2 y AWD3 del G4 sólo tienen <b>8 bits</b> (RM0440 §21.4.28), así que el nivel se mueve de {K.AWD2_STEP} en {K.AWD2_STEP} LSB: {K.trig_step_in[2]*1e3:.0f} mV en la entrada a ×2.</li>
    <li><b>Latencia de software:</b> entre el cruce y el arranque de TIM3 hay una interrupción con la HAL de por medio. En la parada, <code>TIM3_IRQHandler</code> lee <code>DMA1_Channel1-&gt;CNDTR</code> y el firmware <b>supone</b> que el disparo quedó {K.LEN}/2 muestras antes. A 2.5 MSa/s, cada microsegundo de latencia son 2.5 muestras de error en la posición del disparo, y además variable. Hay un intento comentado de leer CNDTR en la propia interrupción del ADC.</li>
    <li><b>Sólo CH1 dispara:</b> <code>scope_config_trigger</code> programa los watchdog sólo en el ADC1 aunque la interfaz ofrezca Ch1–Ch4.</li>
    <li><b>Escalas lentas rotas en la versión Nuklear:</b> el prescaler de 16 bits desborda por debajo de {K.SCALE_MIN_OK:.2f} kSa/s. La versión LVGL lo arregla multiplicando también el periodo.</li>
    <li>Las medidas (mínimo, máximo, media, periodo y ciclo de trabajo) se calculan en software sobre el búfer.</li>
  </ul>
  <p>El G4 tiene una salida que evita esa latencia: cada watchdog y cada comparador se puede llevar <b>por hardware</b> a la entrada ETR de varios temporizadores (RM0440, tablas 268 y 292). Es la propuesta P12, en §11.</p>
"""))

gr = "".join(f'<tr><td class="n">{f:,} Hz</td><td class="n">{fr:,.1f} Hz</td><td class="n">{(fr/f-1)*100:+.2f} %</td><td class="n">{fs/1e6:.3f} MSa/s</td></tr>'.replace(",", " ")
             for f, (fr, fs) in K.gen.items())
S.append(sec("generador", "6", "Generador", f"""
  <p>DAC1 con buffer, disparado por TIM4 (canal 1) y TIM6 (canal 2), con DMA desde una tabla de <b>{K.DAC_LEN} puntos</b>. Detrás, un LMV358 como seguidor y 51 Ω hacia <code>J5</code>. La frecuencia se fija con el prescaler: fs = 170 MHz / (2 · (PSC + 1)) y f = fs / {K.DAC_LEN}.</p>
  <div class="tw"><table><thead><tr><th>Pedida</th><th>Real</th><th>Error</th><th>Actualización del DAC</th></tr></thead><tbody>{gr}</tbody></table></div>
  <p>El DAC1 con buffer está especificado hasta 1 MSa/s (DS12712 §3.19), así que con {K.DAC_LEN} puntos el límite limpio es <b>{K.F_FULL:.0f} Hz</b>. Por encima, el prescaler entero da saltos de frecuencia y el DAC trabaja fuera de especificación. Nuestro AWG usa DAC3, de 15 MSa/s y sin salida a pin, a través de un OPAMP (mapa firmado). La lección es otra: <b>usar un acumulador de fase (DDS)</b> con la frecuencia de actualización fija, en vez de estirar la tabla con el prescaler.</p>
"""))

pr = K.prot
S.append(sec("proteccion", "7", "Protección y alimentación", f"""
  <p>La única protección es <b>R5 de 8.2 kΩ (0603)</b> frente a los diodos internos del LMV324, que descargan al riel +3.3VA. Cálculo con el nodo sujeto a 3.3 V + 0.6 V:</p>
  <div class="tw"><table><thead><tr><th>Entrada</th><th>Corriente por R5</th><th>Al diodo del LMV324</th><th>Potencia en R5</th></tr></thead><tbody>
    <tr><td>+20 V</td><td class="n">{pr[20][0]*1e3:.2f} mA</td><td class="n">{pr[20][1]*1e3:.2f} mA</td><td class="n">{pr[20][2]*1e3:.0f} mW</td></tr>
    <tr><td>+50 V</td><td class="n">{pr[50][0]*1e3:.2f} mA</td><td class="n">{pr[50][1]*1e3:.2f} mA</td><td class="n">{pr[50][2]:.2f} W</td></tr>
    <tr><td>Pico de 230 Vrms (325 V)</td><td class="n">{pr[325][0]*1e3:.0f} mA</td><td class="n">{pr[325][1]*1e3:.0f} mA</td><td class="n">{pr[325][2]:.1f} W</td></tr>
  </tbody></table></div>
  <ul class="tight">
    <li>Una 0603 suele admitir 0.1 W y 50–75 V: a 50 V ya se calienta, y con la red se destruye. Nuestra D-06 cubre ese caso.</li>
    <li>La corriente del diodo entra en +3.3VA, que sale de un XC6206: un regulador lineal que no absorbe corriente. Con poca carga, el riel sube.</li>
    <li><b>Ratiométrico:</b> VREF+ es +3.3VA a través de L2 (47 µH) y C8 (270 nF), y del mismo riel cuelgan los divisores y el DAC2. Si el riel cambia, cambian igual la referencia, el cero del divisor y el offset. Es la idea de P9.</li>
    <li>LiPo → MCP73831 → XC6206: sin medida de batería y sin conmutación entre USB y batería (D4 está sin conectar en la netlist).</li>
  </ul>
"""))

S.append(sec("software", "8", "Firmware", """
  <ul class="tight">
    <li><b>FreeRTOS con cinco tareas:</b> <code>taskTsc</code> (táctil), <code>taskUi</code>, <code>taskScope</code>, <code>taskWavegen</code> y la tarea por defecto. Se comunican por colas (<code>queueTscUi</code>, <code>queueUiScope</code>, <code>queueUiWavegen</code>, <code>queueUiLcd</code>) y un semáforo para la pantalla. Es la misma separación entre interfaz e instrumento que nosotros hacemos entre el ESP32-S3 y el G473.</li>
    <li><b>Mensajes sin tipo:</b> la interfaz manda la configuración en <code>msgUiScope.data[0..16]</code>, con significado por índice. Nuestro protocolo con la S3G4-UI debe seguir tipado.</li>
    <li><b>Dos interfaces:</b> Nuklear (modo inmediato) y LVGL. El núcleo de captura es casi idéntico en ambas: 29 líneas distintas en <code>scope.c</code>.</li>
    <li><b>Framebuffer en PSRAM por QSPI</b> y pantalla por FMC con DMA, según <code>capture engine 2.png</code>. No nos aplica: la pantalla la lleva el ESP32-S3.</li>
    <li><code>test_nucleo_f401re</code> es un prototipo previo en una Nucleo-F401RE (ADC a PCLK/4 y 3 ciclos). <code>firmware_15_sep.hex</code> es una imagen de 512 KB desde 0x0800 0000: no aporta nada que el código no diga.</li>
  </ul>
"""))

S.append(sec("notas", "9", "Las notas del autor", """
  <p>El esquemático trae una lista de pendientes. Las que tocan lo analógico:</p>
  <ul class="tight">
    <li>«Change OPAMP ADC and DAC IC with bigger BW», y al lado de la parte analógica: <b>OPA4322</b> y <b>OPA2322</b> (20 MHz, rail-to-rail en entrada y salida).</li>
    <li>«Add capacitors to ADC channels» y «<b>Fix ADC noise issues</b>».</li>
    <li>«Add pull-down to DAC2-OUT1» y «Add capacitor to DAC2-OUT1»: el origen de R25 y C22.</li>
    <li>«Add battery measurement», «Add digital channels?», «bigger diodes footprint» y «Change schottky diodes to SOT23-3».</li>
  </ul>
  <p>Con los datos de §3 y §4 hay dos causas probables del ruido: <b>el muestreo de 59 ns sobre la salida del OPAMP</b> y <b>el buffer del DAC2 con 100 nF</b>. Ninguna se ha medido: es una hipótesis.</p>
"""))

S.append(sec("evitar", "10", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>Entrada de 10 kΩ que lee +2 V al aire y no admite sondas ×10.</li>
    <li>El OPAMP interno como etapa de ganancia del osciloscopio.</li>
    <li>Muestrear la salida del OPAMP interno por debajo de 200 ns.</li>
    <li>Un offset común a todos los canales, y un DAC con buffer cargado con 100 nF.</li>
    <li>Disparo por software con latencia variable, sólo en CH1 y con histéresis cero.</li>
    <li>Generador de tabla fija con el prescaler como control de frecuencia.</li>
    <li>Una resistencia 0603 como única protección.</li>
  </ul>
"""))

S.append(sec("propuestas", "11", "Propuesta para la rev 2.1", """
  <p>Continúa la numeración de los referentes anteriores (P1–P11). Las propuestas P13–P16 salen de la revisión del G473 (<code>S3G4_LAB_rev2.1/02_referencias/g473_analogico.html</code>). Ninguna está aplicada.</p>
  <h3>P12 · Cadena de disparo por hardware <span class="tag t-open">Estudiar</span></h3>
  <p>El disparo no pasaría por ninguna interrupción:</p>
  <ul class="tight">
    <li>La fuente es un comparador (COMP) o un analog watchdog (AWD).</li>
    <li>Su salida entra por la <b>ETR de un temporizador</b>, que arranca en modo de un solo pulso. Todas las salidas de comparador llegan a las ETR de TIM1/8/20 y TIM2/3/4/5; las de los watchdog, a TIM1/8/20 y TIM3 (RM0440, tablas 268 y 292).</li>
    <li>Ese temporizador cuenta las muestras posteriores al disparo con el mismo reloj que el ADC y, al terminar, bloquea en hardware el temporizador de muestreo (modo esclavo con puerta).</li>
    <li>El firmware sólo lee CNDTR con todo ya parado: la posición del disparo es exacta a la muestra y no depende de la latencia.</li>
  </ul>
  <p>Complementa P11. Queda por ver si el temporizador que da la puerta puede ser el mismo que marca el entrelazado de CH1 (D-02).</p>
"""))

HTML = (
 '<title>Anatomía de black_scope</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el AFE rev 2.1</p>\n  <h1>Anatomía de black_scope</h1>\n'
 '  <p class="lede">Un osciloscopio de cuatro canales hecho con nuestro mismo STM32G473, que usa sus OPAMP internos como etapa de ganancia. Sirve de prueba de lo que el G473 puede y no puede hacer. Completa la serie con <code>S3G4_LAB_rev2.1/02_referencias/analisis_dso112.html</code>, <code>S3G4_LAB_rev2.1/02_referencias/analisis_wave2.html</code> y <code>S3G4_LAB_rev2.1/02_referencias/analisis_openscope.html</code>.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 23 sep 2026. Fuentes locales en <code>research_and_tests/black_scope/</code>; datasheet y manual en <code>datasheet/</code>. Proyecto original: '
 '<a href="https://github.com/jgpeiro/black_scope">jgpeiro/black_scope</a>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
