# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_tida01012.html (anatomia del TIDA-01012).
Cifras: calc_dmm_tida01012.py. Dibujos: draw_dmm_tida01012.py. CSS: el del documento vivo."""
import io, draw_dmm_tida01012 as D, calc_dmm_tida01012 as K
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/dmm_tida01012.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css and ".sx{" in css
EXTRA = """
.lesson td:first-child{font-weight:600}
pre.mermaid{background:var(--paper);border:1px solid var(--rule);border-radius:8px;padding:12px;overflow-x:auto}
.meta{color:var(--muted);font-size:13px}
.toc{columns:2 260px;column-gap:28px;margin:6px 0 0;padding-left:20px;font-size:14px}
.toc li{break-inside:avoid;margin:2px 0}
.toc a{color:var(--accent);text-decoration:none} .toc a:hover{text-decoration:underline}
.eq{font-family:"IBM Plex Mono",monospace;font-size:13.5px;background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:8px 12px;margin:10px 0;overflow-x:auto;white-space:pre}
"""
def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def fig(svg, cap):
    return f'  <figure><div class="sx">{svg}</div><figcaption>{cap}</figcaption></figure>\n'
OK, OPEN, WARN, CRIT = "t-ok", "t-open", "t-warn", "t-crit"
def tg(c, t): return f'<span class="tag {c}">{t}</span>'
r = K.rangos

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El TIDA-01012 es el DMM de referencia de Texas Instruments: 4½ dígitos (50 000 cuentas), tensión y corriente en continua y en alterna con verdadero valor eficaz hasta 100 kHz, alimentado por una celda Li-ion y comunicado por Bluetooth. Su front-end es <b>discreto</b> y está construido alrededor de un ADC SAR de 18 bits, que es justo lo que queremos aprender: nosotros haremos lo mismo con el ADC5 del G473. <b>No mide resistencia, diodo ni continuidad</b>; esos bloques se estudian en el HydraMeter y el 121GW.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el TIDA-01012</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Conmutar las patas bajas del divisor</td><td>10 MΩ fijo arriba; un SP3T de 2.7 V elige la pata que va a COM. La toma vale ±50 mV a fondo en <b>todos</b> los rangos (§3)</td><td>El conmutador nunca ve la tensión de entrada y su resistencia (≈ 1 Ω) pesa como mucho {r['50 V']['ron_err']*1e6:.0f} ppm. Con la red, por la toma pasan solo {K.I_SOBRE['50 V']*1e6:.0f} µA. Alternativa a nuestras tomas fijas con R_PROT (P17)</td><td>{tg(OPEN,'Estudiar')}</td></tr>
      <tr><td>Compensación con la misma constante de tiempo</td><td>Cada pata cierra τ = 1 ms, igual que 10 MΩ ∥ 100 pF; la pata de 1 MΩ deja ≈ {K.CEQ_PATA_500mV*1e12:.0f} pF para el conmutador y el buffer (§3)</td><td>Condensadores fijos C0G, sin trimmer, con margen para la capacidad parásita (P18)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Ruido de la fuente de 10 MΩ</td><td>En 50 mV cambia a 499 kΩ por un conmutador manual: el ruido baja de {K.VN_50mV_CON_10M*1e6:.2f} a {r['50 mV']['vn_rms']*1e6:.2f} µV rms (§3)</td><td>Con una fuente de MΩ, el ruido térmico y la corriente de polarización del buffer cuentan. Afecta a la elección del amplificador si se adopta P17</td><td>{tg(WARN,'Tener en cuenta')}</td></tr>
      <tr><td>COM a media alimentación</td><td>COM = 1.35 V sobre la masa de la placa; toda la cadena va a 2.7 V con una sola fuente (§5)</td><td>Solo sirve en un instrumento flotante. Nuestro COM es la masa común del equipo (RD-05), así que necesitamos los ±4.9 V</td><td>{tg(CRIT,'No aplicable')}</td></tr>
      <tr><td>Fuerza y sentido en los derivadores</td><td>Un conmutador doble: una sección lleva la corriente y la otra elige el punto de medida (§4)</td><td>La resistencia del conmutador no entra en la medida. Confirma la razón de ohmios de nuestra sección H y sirve si se añade un rango de µA (P19)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Filtro del ADC calculado por la carga</td><td>52.3 Ω / 2.2 nF diferencial ({K.F_AA/1e3:.0f} kHz), con la carga del condensador de muestreo y el tiempo de adquisición (§5)</td><td>El mismo método para el ADC5 del G473 (P20)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Firmware de medida y calibración</td><td>DC por media de 32 K muestras; alterna por media de cuadrados menos DC y ruido; calibración de tres puntos por rango (§6)</td><td>Directo a nuestro firmware (P21)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>AFE apagable</td><td>Buck a 2.8 V y LDO a 2.7 V con habilitación por firmware (§8)</td><td>Resuelve el «interruptor de carga propio del DMM» de RF-18 (P22)</td><td>{tg(OPEN,'Estudiar')}</td></tr>
      <tr><td>Resolución por cuenta</td><td>Una cuenta = {K.LSB_POR_CUENTA:.1f} LSB de un ADC de 18 bits (§5)</td><td>En nuestra sección H, una cuenta es ≈ 1/12 de LSB de un ADC de 12 bits: todo depende del sobremuestreo. Hay que validarlo en S11</td><td>{tg(WARN,'Riesgo')}</td></tr>
      <tr><td>Protección de la entrada de tensión</td><td>Ninguna: la guía lo dice (2.4.1.1.2). Solo una PTC de 0.2 A en corriente (§9)</td><td>Nosotros pedimos aguantar la red 10 s (RD-10)</td><td>{tg(CRIT,'Evitar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", f"""
  <ul class="tight">
    <li><b>Guía de diseño</b> <code>research_and_tests/TIDA-01012/tidubv5b (1).pdf</code> (TIDUBV5B, rev. B de junio de 2017, 75 p). Leídas la especificación (tabla 1), la teoría del diseño (§2.4, pp. 25–51), la calibración (§3.1.2) y los resultados (§3.3, pp. 62–71). Las ecuaciones y las gráficas se renderizaron con PyMuPDF.</li>
    <li><b>Esquemático</b> <code>tidrny5 (2).pdf</code> (5 hojas Altium: bloques, MCU, AFE, hardware y alimentación). La hoja 3 (AFE) se leyó por zonas a 260–330 ppp. Todos los valores de esta página salen de ahí.</li>
    <li><b>Cálculos propios</b> en <code>herramientas/calc_dmm_tida01012.py</code>: relaciones del divisor, constantes de tiempo, ruido térmico en la toma, caídas en los derivadores, valor de una cuenta y corriente con la red en la entrada.</li>
    <li><b>Redibujos</b> en <code>herramientas/draw_dmm_tida01012.py</code>, comprobados con <code>chk_dmm.py</code> (0 solapes) y revisados a la vista.</li>
    <li><b>No se leyó</b>: la lista de materiales (archivo aparte en ti.com, no descargado) ni el firmware (zip del CCS). Lo que depende de ellos se marca «NO VERIFICADO».</li>
  </ul>
"""))

S.append(sec("arquitectura", "2", "Arquitectura", """
  <pre class="mermaid">flowchart LR
  J1["Borne rojo J1"] --> S1{"S1 · tensión o corriente"}
  S1 -->|tensión| DIV["10 MΩ o 499 kΩ<br/>+ patas a COM (TS5A3359)"]
  S1 -->|corriente| SH["PTC 0.2 A + derivadores<br/>95.8 Ω / 0.5 Ω (TS3A24159)"]
  DIV --> INP["IN_P · ±50 mV"]
  SH --> U25["TS5A3166"] --> INP
  INP --> BUF["2 × OPA2313"] --> FDA["THS4531 · ×44.2"] --> AA["52.3 Ω / 2.2 nF"] --> ADC["ADS8885 · 18 bits"]
  REF["REF3325 → OPA313"] --> ADC
  REF --> VCM["OPA333 · 1.35 V = COM"]
  ADC -->|SPI| MCU["CC2640 · BLE"]
  MSP["MSP430FR2532 · despertar por proximidad"] --> MCU
  NFC["RF430CL330H · emparejado NFC"] --> MCU
  MCU -->|BLE| HOST["PC · cálculo final y calibración"]</pre>
  <p>Hay una sola cadena de medida para tensión y corriente: los dos caminos terminan en el mismo nodo IN_P con ±50 mV a fondo, y desde ahí todo es común. El MCU solo acumula sumas y sumas de cuadrados; la cuenta final, la calibración y el filtrado los hace el PC (LabVIEW). Un producto real haría esa parte en el propio MCU.</p>
"""))

rows = "".join(
    f"<tr><td>{n}</td><td>{x['sw']}</td><td class='n'>÷{x['div']:.1f}</td><td class='n'>{x['v_toma']*1e3:.1f} mV</td>"
    f"<td class='n'>{K.Z_IN[n]/1e6:.1f} MΩ</td><td class='n'>{(x['tau_pata']*1e3 if x['tau_pata'] else 0):.2f} ms</td>"
    f"<td class='n'>{x['thev']/1e3:.0f} kΩ</td><td class='n'>{x['e_n']*1e9:.0f} nV/√Hz</td></tr>"
    for n, x in r.items()).replace("<td class='n'>0.00 ms</td>", "<td class='n'>—</td>")
S.append(sec("tension", "3", "Entrada de tensión: 10 MΩ arriba y patas conmutadas abajo", f"""
  <p>La idea central del diseño: <b>la resistencia de alta tensión es una sola y no se conmuta</b>. R16 (10 MΩ ∥ 100 pF) une el borne con la toma IN_P. Debajo, un SP3T de baja tensión (TS5A3359, alimentado a 2.7 V) conecta a COM una de tres patas, o ninguna. R9 (100 MΩ) está siempre. Cada pata fija el divisor para que <b>la toma valga ±50 mV a fondo en todos los rangos</b>.</p>
{fig(D.tension(), "Redibujo simplificado de la hoja 3 del esquemático («Voltage Front End» y «DMM Input/Select»). S1 y S2 son conmutadores deslizantes que mueve el usuario; S2 avisa al MCU por AFE_RIN-SEL.")}
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Salida del SP3T</th><th>División</th><th>Toma a fondo</th><th>Z de entrada</th><th>τ de la pata</th><th>Thévenin en la toma</th><th>Ruido térmico</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <p class="meta">Cálculo propio con los valores del esquemático y R9 en paralelo con cada pata. En 50 mV la entrada es R17 (499 kΩ) y no hay pata: la división es 100 MΩ / 100.5 MΩ.</p>
  <h3>Por qué funciona</h3>
  <ul class="tight">
    <li><b>El conmutador no ve la tensión de entrada.</b> Su lado alto es la toma, que nunca pasa de unos ±50 mV en uso normal. Basta un conmutador de 5 V, pequeño y barato, con ≈ 1 Ω: frente a la pata más baja (9.77 kΩ) son {r['50 V']['ron_err']*1e6:.0f} ppm, y la calibración se los lleva.</li>
    <li><b>Una sola ganancia para todo.</b> Como todas las tomas dan el mismo fondo de escala, el resto de la cadena (buffers, ×44.2, ADC) es igual en todos los rangos. Cada rango solo necesita su propio factor de calibración.</li>
    <li><b>La impedancia de entrada es 10–11 MΩ en todos los rangos</b>, porque la resistencia de arriba manda. En 50 mV llega a 100.5 MΩ, porque R9 es lo único que queda abajo.</li>
  </ul>
  <h3>Compensación para alterna</h3>
  <p>Es la misma regla que el ÷100 de nuestro osciloscopio: cada pata lleva un condensador en paralelo con la misma constante de tiempo que la resistencia de arriba (R16 · C22 = {K.TAU_IN*1e3:.1f} ms). Las tres patas cierran 1.00, 1.00 y 0.96 ms. La de 1 MΩ se queda corta a propósito: le faltan ≈ {K.CEQ_PATA_500mV*1e12:.0f} pF, que pone la capacidad del conmutador, del buffer y de la placa (la guía lo llama C<sub>eq</sub>, fig. 23). En las patas de baja impedancia, C<sub>eq</sub> no importa. Los condensadores son fijos: no hay trimmer.</p>
  <h3>El rango de 50 mV y el ruido de 10 MΩ</h3>
  <p>En 50 mV una cuenta es 1 µV. Con 10 MΩ arriba y solo R9 abajo, la toma vería ≈ 9 MΩ de Thévenin: {K.ruido(K.par(K.R_IN, K.R_SIEMPRE))*1e9:.0f} nV/√Hz, que con el ancho de banda del promedio ({K.ENBW:.1f} Hz) son {K.VN_50mV_CON_10M*1e6:.2f} µV rms, casi una cuenta. Por eso hay un <b>segundo camino con 499 kΩ</b> (R17 ∥ 22 nF): el ruido baja a {r['50 mV']['vn_rms']*1e6:.2f} µV y la entrada sigue por encima de 10 MΩ gracias a los 100 MΩ de R9. El inconveniente es que el cambio lo hace <b>el usuario</b> con S2.</p>
  <p>La misma cuenta dice algo de la corriente de polarización: con 9 MΩ de fuente, 10 pA del OPA2313 son 90 µV de error. Si nosotros adoptáramos esta topología con nuestras tomas de ±2 V, el amplificador de entrada tendría que ser de entrada CMOS (pA), no un chopper como el OPA2188 (cientos de pA). Ver P17.</p>
"""))

c5, c50 = K.corr["500 µA"], K.corr["50 mA"]
S.append(sec("corriente", "4", "Corriente: dos derivadores con fuerza y sentido", f"""
{fig(D.corriente(), "Redibujo de «Current Front End». La sección 1 del TS3A24159 lleva la corriente; la sección 2 elige qué nodo se mide; U25 conecta la medida a IN_P solo en modo corriente.")}
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Derivador medido</th><th>A fondo</th><th>Una cuenta</th><th>Potencia</th></tr></thead>
    <tbody>
      <tr><td>500 µA</td><td>R20 + R25 = {c5['R']:.1f} Ω</td><td class="n">{c5['V']*1e3:.1f} mV</td><td class="n">10 nA = {c5['v_cuenta']*1e9:.0f} nV</td><td class="n">{c5['P']*1e3:.2f} mW</td></tr>
      <tr><td>50 mA</td><td>R25 = 0.5 Ω (R20 puenteada)</td><td class="n">{c50['V']*1e3:.0f} mV</td><td class="n">1 µA = {c50['v_cuenta']*1e9:.0f} nV</td><td class="n">{c50['P']*1e3:.2f} mW</td></tr>
    </tbody>
  </table></div>
  <ul class="tight">
    <li><b>Fuerza y sentido.</b> En 50 mA la sección 1 une A con B y la corriente evita R20. La sección 2 mide en B, encima de R25: la resistencia del conmutador queda en el camino de la corriente, no en el de la medida. Es una medida Kelvin hecha con un conmutador barato.</li>
    <li><b>Aislamiento entre modos.</b> U25 (TS5A3166) desconecta los derivadores de IN_P en modo tensión, para que no carguen el divisor.</li>
    <li><b>Caída real.</b> La tabla 1 promete 50 mV. A eso hay que sumar la PTC F1 (NANOSMDC020F-2, 0.2 A) y la resistencia del conmutador. Con unos pocos ohmios de PTC en frío, la caída en 50 mA se acerca a 0.1–0.2 V. La resistencia en frío de la PTC está <b>NO VERIFICADA</b> (falta su hoja).</li>
    <li>Los rangos son pequeños: 50 mA como máximo. Nuestro RD-06 pide 2 A con un fusible de verdad, así que de aquí se toma la técnica, no los valores.</li>
  </ul>
"""))

S.append(sec("cadena", "5", "De la toma al ADC", f"""
{fig(D.cadena(), "Redibujo de «Single Input, Differential Output Buffer/Gain Stage», «ADC Reference and Buffer», «Common Mode Offset» y «Fully Differential SAR ADC».")}
  <ul class="tight">
    <li><b>Dos seguidores OPA2313</b> (CMOS, entrada y salida rail-to-rail, ≈ 10 pA) aíslan la toma y COM del amplificador diferencial. No son de deriva cero: el offset se resta con la calibración.</li>
    <li><b>THS4531</b>, amplificador totalmente diferencial con ganancia 133 k / 3.01 k = {K.G_FDA:.1f}. Convierte ±50 mV en ≈ ±2.2 V diferenciales centrados en VOCM = 1.35 V. Deja margen frente a los 2.5 V de la referencia.</li>
    <li><b>Filtro anti-alias de {K.F_AA/1e3:.0f} kHz</b> (52.3 Ω por rama y 2.2 nF entre AINP y AINN). La guía lo dimensiona por la carga, no por la frecuencia: Q<sub>SH</sub> = C<sub>SH</sub> · V<sub>FS</sub> = 55 pF · 5 V = 275 pC. El condensador del filtro aporta la mitad con una caída ≤ 100 mV, de modo que C ≥ 1.4 nF (eligen 2.2 nF, más de 10 veces C<sub>SH</sub>). R se acota para que el conjunto asiente en el 75 % del tiempo de adquisición (3.7 µs a ≈ 200 kSa/s). Es el procedimiento que conviene repetir para el ADC5 (P20).</li>
    <li><b>ADS8885</b>: SAR de 18 bits, entrada diferencial, a ≈ 210 kSa/s. Una cuenta (1 µV en la toma) son {K.V_CUENTA_ADC*1e6:.1f} µV en el ADC, {K.LSB_POR_CUENTA:.1f} LSB. Cada lectura promedia 32 K muestras: {K.LECTURAS_S:.1f} lecturas por segundo.</li>
    <li><b>Referencia.</b> La REF3325 pasa por un RC de {K.F_REF:.1f} Hz (10 kΩ, 4.7 µF), que corta su ruido de banda ancha, y por un OPA313 que carga los 22 µF del pin REF. Ese buffer oscilaría con 22 µF; lo estabilizan con «R<sub>ISO</sub> de doble realimentación» (8.2 Ω, 13.3 kΩ y 0.1 µF; margen de fase de 76°). El OPA333 se descartó por su impedancia de salida inductiva.</li>
    <li><b>VCM y COM.</b> VREF · 13.3/24.6 = {K.V_CM:.3f} V, seguido por un OPA333 y filtrado con 1 kΩ y 1 µF. Esa tensión es VOCM del THS4531 y, a la vez, <b>la red COM del borne negro</b>: IN_N está unida a 1P35V_REF. La corriente medida entra y sale por los bornes sin pasar por el OPA333, que solo fija la tensión del instrumento flotante respecto a su masa interna.</li>
  </ul>
"""))

S.append(sec("firmware", "6", "Firmware: cómo sale el número", f"""
  <p>El CC2640 acumula, para cada lectura, la suma y la suma de cuadrados de 32 K muestras y las envía por BLE. El PC hace el resto (guía, §2.4.1.5):</p>
  <div class="eq">Xdc   = Σ x(k) / N                                         N = 32 768
Xrms² = Σ x(k)² / N
DC         = Gain · (Xdc − Xdc_offset)
AC (solo)  = Gain · √(Xrms² − Xdc² − Xnoise²)
AC + DC    = √(DC² + AC²)
salida(t)  = α · lectura(t) + (1 − α) · salida(t−1)          α = 0.25</div>
  <ul class="tight">
    <li><b>Xnoise</b> es el ruido propio del sistema, medido con la entrada en cero durante la calibración. Restarlo en cuadratura evita que una entrada nula lea unas decenas de cuentas en alterna.</li>
    <li><b>Calibración de tres puntos por rango</b> (§3.1.2): fondo negativo, cero y fondo positivo con una Keithley 2400; regresión lineal → ganancia y offset en continua, y offset de ruido en alterna. Se cargan por BLE.</li>
    <li>El filtro exponencial con α = 0.25 suaviza la lectura a costa de unos segundos de asentamiento.</li>
    <li>Con {K.LECTURAS_S:.1f} lecturas por segundo y una ventana de {K.N_PROM/K.FS_ADC*1e3:.0f} ms, el promedio cubre unos 8 ciclos de 50 Hz. No es un número entero de ciclos (no hay NPLC): el rechazo de la red sale del propio promedio largo.</li>
  </ul>
"""))

S.append(sec("resultados", "7", "Lo que midió TI", f"""
  <p>Gráficas de la guía, figs. 64–67, 74 y tabla 13, después de la calibración de tres puntos y frente a un Agilent 34401A:</p>
  <div class="tw"><table>
    <thead><tr><th>Ensayo</th><th>Resultado (leído de las gráficas)</th><th>Límite de la especificación</th></tr></thead>
    <tbody>
      <tr><td>Linealidad, 50 V</td><td class="n">−4 … +7 mV</td><td>±(0.05 % + 5 cuentas): 5 mV en cero, 30 mV a fondo</td></tr>
      <tr><td>Linealidad, 5 V</td><td class="n">±0.5 mV (pico de +2 mV al empezar en −5 V)</td><td>0.5 … 3 mV</td></tr>
      <tr><td>Linealidad, 500 mV</td><td class="n">−80 … +50 µV</td><td>50 … 300 µV</td></tr>
      <tr><td>Linealidad, 50 mV</td><td class="n">−15 … +12 µV</td><td>5 … 30 µV</td></tr>
      <tr><td>Alterna, 50 mV a 5 V, seno</td><td class="n">±1.5 % hasta 10 kHz; −3 % a 100 kHz</td><td>3 % + 10 cuentas hasta 100 kHz</td></tr>
      <tr><td>Consumo</td><td class="n">5.2 mA activo, 25 µA apagado (3.7 V)</td><td>≈ 115 h con 600 mAh</td></tr>
    </tbody>
  </table></div>
  <p>El error tiene forma de pendiente en los cuatro rangos: es un resto de ganancia o de no linealidad que la calibración de tres puntos no termina de quitar. En 50 mV llega a 15 cuentas. Es la misma clase de error que nuestro presupuesto atribuye a la no linealidad del ADC5.</p>
"""))

S.append(sec("alimentacion", "8", "Alimentación", """
  <ul class="tight">
    <li><b>Celda</b> Li-ion de tamaño AAA (10440, 600 mAh), con un P-MOSFET SI2323DS contra la polaridad invertida y una resistencia de 10 mΩ para el medidor de carga BQ27426.</li>
    <li><b>Cargador BQ24232</b> con <i>power path</i> desde el micro-USB: el equipo funciona mientras carga (≈ 150 mA).</li>
    <li><b>Dos TPS62740</b> (buck de muy bajo consumo): uno da 1.9 V al CC2640; el otro da 2.8 V, que un <b>LDO TPS78227 baja a 2.7 V para el AFE</b>. El buck y el LDO del AFE tienen habilitaciones del MCU (PWR_DCDC1-EN, PWR_LDO1-EN): el AFE se apaga del todo cuando no se mide.</li>
    <li>Un TPS78230 da 3.0 V al MSP430 que vigila la proximidad.</li>
  </ul>
  <p>Para nosotros: el par buck + LDO con poco margen (100 mV) da un riel limpio con buen rendimiento, y las habilitaciones son el «interruptor de carga» que RF-18 pide para el DMM (P22).</p>
"""))

S.append(sec("seguridad", "9", "Seguridad: qué aguanta y qué no", f"""
  <ul class="tight">
    <li><b>Entrada de tensión sin protección.</b> La guía lo reconoce (2.4.1.1.2 y nota de §3.1). Por cálculo, con 325 V de pico por R16 pasan {K.I_SOBRE['50 V']*1e6:.0f} µA hacia los diodos internos del conmutador y del buffer: probablemente sobrevive. En 50 mV, con R17 de 499 kΩ, serían {K.I_SOBRE['50 mV']*1e6:.0f} µA. La tensión que soportan R16 y R17 depende de su encapsulado: <b>NO VERIFICADO</b> sin la BOM.</li>
    <li><b>Un mismo borne para tensión y corriente</b>, elegido con el deslizante S1. Medir tensión con S1 en corriente pone la fuente sobre 0.5 Ω, y solo la PTC de 0.2 A limita. Nuestro diseño tiene bornes separados (RD-02), que evitan este error.</li>
    <li><b>Sin categoría de medida</b> ni distancias de aislamiento declaradas. Es un diseño de laboratorio para demostrar exactitud y consumo.</li>
  </ul>
"""))

S.append(sec("no-copiar", "10", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>COM a media alimentación con una sola fuente: solo vale en un instrumento aislado (nuestro RD-05 lo impide).</li>
    <li>La entrada de tensión sin sujeción ni resistencia de protección.</li>
    <li>Conmutadores manuales que el firmware no controla: S2 (499 kΩ / 10 MΩ) y S1 (tensión / corriente) obligan al usuario a acertar.</li>
    <li>El cálculo final y la calibración en el PC: nuestro DMM debe dar el número por sí mismo, en la pantalla y en S3G4-UI.</li>
    <li>La PTC de 0.2 A como única protección de corriente.</li>
  </ul>
"""))

S.append(sec("modulos", "11", "Módulos", """
  <p><b>Ninguno.</b> Todo son circuitos integrados en la placa: el CC2640 lleva un balun integrado de Murata y una antena de chip de Molex, y el NFC usa una antena flexible propia. No hay que traducir nada a discreto.</p>
"""))

S.append(sec("comparacion", "12", "Comparación con nuestra sección H (7 oct)", f"""
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>TIDA-01012</th><th>Sección H (borrador)</th><th>Comentario</th></tr></thead>
    <tbody>
      <tr><td>Cambio de rango en tensión</td><td>Patas bajas conmutadas; toma de ±50 mV en todos los rangos</td><td>Tomas fijas ÷1/÷10/÷100 al 74HC4051; ÷1 por R_PROT de 3 × 33 kΩ</td><td>En el TIDA la protección sería trivial (µA); en H, R_PROT disipa con la red. P17</td></tr>
      <tr><td>Ganancia tras la toma</td><td>Fija, ×44.2</td><td>×1 o ×10 según el rango</td><td>Una sola ganancia simplifica la calibración</td></tr>
      <tr><td>Amplificador de entrada</td><td>OPA2313 (CMOS, pA, no de deriva cero)</td><td>OPA2188 (deriva cero, cientos de pA)</td><td>Con fuentes de MΩ, la corriente de polarización pesa más que el offset</td></tr>
      <tr><td>Driver al ADC</td><td>THS4531 diferencial, VOCM 1.35 V</td><td>Doble RRIO a 3.3 V, VCM 1.25 V</td><td>La misma idea; el método del filtro se puede copiar (P20)</td></tr>
      <tr><td>ADC</td><td>ADS8885, 18 bits; una cuenta = {K.LSB_POR_CUENTA:.1f} LSB</td><td>ADC5 de 12 bits con ×1024; una cuenta ≈ 0.08 LSB</td><td>Nuestro punto débil: S11 tiene que demostrar las 20 000 cuentas</td></tr>
      <tr><td>COM</td><td>1.35 V, flotante</td><td>Masa común (RD-05)</td><td>Obliga a ±4.9 V y a un driver que pase de bipolar a 0–2.5 V</td></tr>
      <tr><td>Corriente</td><td>500 µA y 50 mA, PTC 0.2 A</td><td>200 mA y 2 A, fusible 3.15 A</td><td>La técnica de fuerza y sentido sí sirve</td></tr>
      <tr><td>Ohmios, diodo y continuidad</td><td>No tiene</td><td>Razón con R_ref, PB14 y COMP7</td><td>Pendiente de las otras referencias</td></tr>
      <tr><td>Protección</td><td>Ninguna en tensión</td><td>R_PROT, sujeción, PTC y fusible</td><td>Aquí el TIDA no enseña nada</td></tr>
      <tr><td>Firmware</td><td>Media, media de cuadrados, calibración de 3 puntos</td><td>NPLC, autocero por el mux</td><td>Se complementan: tomar los dos (P21)</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "13", "Propuestas para la rev 2.1", f"""
  <p>Continúan la numeración global (P1–P16 son del osciloscopio y del G473). <b>Ninguna está aplicada</b>: se deciden en la síntesis de las referencias del DMM.</p>
  <h3>P17 · Patas bajas conmutadas en el divisor de 10 MΩ {tg(OPEN,'Estudiar')}</h3>
  <ul class="tight">
    <li>Arriba, 10 MΩ fijos en varias piezas (para la tensión de la red); abajo, patas a COM elegidas por el 74HC4051 que ya usamos.</li>
    <li>La toma tendría el mismo fondo en todos los rangos, sujeta a ±4.9 V a través de los 10 MΩ: con la red, solo {K.I_SOBRE['50 V']*1e6:.0f} µA. Desaparecen R_PROT y su disipación.</li>
    <li>A estudiar: el rango de 200 mV (la toma sin pata vale ÷1.1 con 9 MΩ de fuente; ruido y corriente de polarización), el amplificador de entrada CMOS de pA en lugar del OPA2188, y la fuga del 4051 en las patas de 1 MΩ.</li>
  </ul>
  <h3>P18 · Compensación con la misma τ y condensadores fijos {tg(OK,'Adoptar')}</h3>
  <p>Cada tramo del divisor con la misma constante de tiempo que el de arriba, en C0G, dejando en la pata de mayor impedancia unas decenas de pF para la capacidad parásita. Sin trimmer, salvo que S11 diga que la dispersión no basta para el ±1 % de alterna.</p>
  <h3>P19 · Fuerza y sentido con un conmutador doble {tg(OK,'Adoptar')}</h3>
  <p>Una sección del conmutador lleva la corriente y la otra elige el punto que se mide. Se usa en la razón de ohmios (ya en la sección H) y en cualquier derivador conmutado, si algún día se añade un rango de µA.</p>
  <h3>P20 · Filtro del ADC5 calculado por la carga de muestreo {tg(OK,'Adoptar')}</h3>
  <p>El procedimiento de §2.4.1.3.1 con los datos del G473: C<sub>SH</sub> del ADC5, el tiempo de muestreo programado y la frecuencia de lectura del DMM. Fija el condensador del filtro (≥ 10 × C<sub>SH</sub>) y la resistencia máxima para asentar en el 75 % de la ventana.</p>
  <h3>P21 · Firmware de medida del TIDA más NPLC y autocero {tg(OK,'Adoptar')}</h3>
  <p>DC por media, alterna por √(Xrms² − Xdc² − Xnoise²) con el ruido propio calibrado, calibración de tres puntos por rango (−fondo, 0, +fondo) y filtro exponencial. Se suma a lo que ya teníamos: ventana de un número entero de ciclos de red y autocero por el mux en cada lectura.</p>
  <h3>P22 · Riel propio del DMM con habilitación {tg(OPEN,'Estudiar')}</h3>
  <p>Como el AFE del TIDA (buck + LDO con habilitación), el DMM tendría su riel propio apagable. Cierra el pendiente de RF-18 (G.6). Se decide con los rieles (PLAN, paso 4).</p>
"""))

S.append(sec("correcciones", "14", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>En el plan de referencias (R1) dije «OPA333 de deriva cero» como si estuviera en la cadena de señal. <b>El OPA333 solo sigue la tensión de 1.35 V de VCM/COM.</b> Los buffers de la señal son OPA2313, CMOS sin deriva cero, y el de la referencia es un OPA313.</li>
    <li>En el borrador de arquitectura del DMM escribí que el TIDA tiene «conmutadores de baja tensión detrás del divisor de 10 MΩ». Es cierto, pero hay que precisarlo: los conmutadores están <b>en las patas bajas</b>, entre la toma y COM, no en las tomas de una cadena fija como en nuestra sección H.</li>
    <li>También escribí que el TIDA «resuelve» la entrada bipolar con VCM y un driver diferencial. Le funciona porque <b>su COM flota a 1.35 V</b>; nosotros no podemos hacer lo mismo.</li>
    <li>El TIDA no mide resistencia, diodo ni continuidad: no sirve de referencia para esos bloques.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("arquitectura", "2 · Arquitectura"),
    ("tension", "3 · Entrada de tensión"), ("corriente", "4 · Corriente"), ("cadena", "5 · De la toma al ADC"),
    ("firmware", "6 · Firmware"), ("resultados", "7 · Lo que midió TI"), ("alimentacion", "8 · Alimentación"),
    ("seguridad", "9 · Seguridad"), ("no-copiar", "10 · Lo que no conviene copiar"), ("modulos", "11 · Módulos"),
    ("comparacion", "12 · Comparación con la sección H"), ("propuestas", "13 · Propuestas P17–P22"),
    ("correcciones", "14 · Correcciones")])

HTML = (
 '<title>Anatomía del TIDA-01012</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 1 de 8</p>\n  <h1>Anatomía del TIDA-01012</h1>\n'
 '  <p class="lede">El DMM de referencia de Texas Instruments: 4½ dígitos, un front-end discreto alrededor de un ADC de 18 bits y una sola fuente de 2.7 V. Es la referencia más cercana a nuestra sección H y la que mejor enseña a cambiar de rango sin que los conmutadores vean la tensión de entrada.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes locales en <code>research_and_tests/TIDA-01012/</code>. '
 'Página de TI: <a href="https://www.ti.com/tool/TIDA-01012">ti.com/tool/TIDA-01012</a>. Cifras: <code>herramientas/calc_dmm_tida01012.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
