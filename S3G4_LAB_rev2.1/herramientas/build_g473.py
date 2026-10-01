# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/g473_analogico.html: revision de las partes analogicas del STM32G473 (DS12712 Rev 5, RM0440 Rev 9)."""
import io, calc_g473 as G
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/02_referencias/g473_analogico.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css
EXTRA = """
.lesson td:first-child{font-weight:600}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 16px;margin:10px 0;font-size:14px}
.kv dt{color:var(--muted)} .kv dd{margin:0}
.meta{color:var(--muted);font-size:13px}
.toc{columns:2 260px;column-gap:28px;margin:6px 0 0;padding-left:20px;font-size:14px}
.toc li{break-inside:avoid;margin:2px 0}
.toc a{color:var(--accent);text-decoration:none} .toc a:hover{text-decoration:underline}
.eq{font-family:"IBM Plex Mono",monospace;font-size:13.5px;background:var(--paper);border:1px solid var(--rule);border-radius:6px;padding:8px 12px;margin:10px 0;overflow-x:auto;white-space:pre}
.src{color:var(--muted);font-size:12.5px}
@media (max-width:640px){.kv{grid-template-columns:1fr}.kv dt{margin-top:6px}}
"""
def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def tag(c, t): return f'<span class="tag {c}">{t}</span>'
def ms(x): return f"{x/1e6:.2f}"

r52 = next(r for r in G.rates if r["f"] == 52e6)
r425 = next(r for r in G.rates if abs(r["f"] - 42.5e6) < 1)
n25 = G.ADC_NOISE[(2.5, 66.9)]; n25b = G.ADC_NOISE[(2.5, 63.2)]

S = []
S.append(sec("resumen", "★", "Lo que cambia para la rev 2.1", f"""
  <p>Revisión de todas las partes analógicas del STM32G473 en el datasheet (DS12712 Rev 5) y el manual de referencia (RM0440 Rev 9) de <code>datasheet/</code>. La rev 2.0 ya había verificado varias cifras (52 MHz, 6.5 MSa/s entrelazado, OPAMP interno descartado); aquí se confirman y se añade lo que faltaba. Cada fila remite a su sección; nada está decidido.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>Dato del fabricante</th><th>Consecuencia</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Velocidades de D-02</td><td>f<sub>ADC</sub> ≤ 52 MHz con varios ADC y V<sub>DDA</sub> ≥ 2.7 V (T.61); SMPPLUS da 16 ciclos (RM §21.4.12)</td><td>CH1 a {r52['il_fast']/1e6:.1f} MSa/s y CH2/CH3 a {ms(r52['fast'])} MSa/s <b>sólo en canales rápidos</b> y con V<sub>DDA</sub> ≥ 2.7 V (§2)</td><td>{tag('t-ok','Confirmado')}</td></tr>
      <tr><td>Reloj asíncrono = incertidumbre de disparo</td><td>Latencia de 1.5–2.5 ciclos con CKMODE = 00; fija en modo síncrono (T.61, RM §21.4.3)</td><td>En el peor caso, SNR ≤ {G.jit[1e6]:.0f} dB a 1 MHz. Con HCLK/2 a 104 MHz se mantienen 52 MHz y la CPU gasta {G.SAVE_104:.1f} mA menos: P13 (§3)</td><td>{tag('t-open','Decidir')}</td></tr>
      <tr><td>El ADC también hace ruido</td><td>SNR típico 66.9 dB (T.63); 63.2 dB con varios ADC en todo el rango de temperatura (T.68)</td><td>Con VREF+ = 2.5 V son {n25*1e3:.2f}–{n25b*1e3:.2f} mV rms: <b>{n25/G.VDIV_ADC*100:.2f}–{n25b/G.VDIV_ADC*100:.2f} % de división</b>, del orden del ruido del AFE de la sección C (§2)</td><td>{tag('t-warn','Tener en cuenta')}</td></tr>
      <tr><td>Carga del pin a 2.5 ciclos</td><td>R<sub>AIN</sub> ≤ 100 Ω en canal rápido; en canal lento, 2.5 ciclos no se admiten (T.62)</td><td>La etapa final debe atacar al pin con ≤ 100 Ω; el RC anti-alias, con R pequeña y C grande (§2)</td><td>{tag('t-ok','Adoptar')}</td></tr>
      <tr><td>Sin inyección positiva</td><td>Los pines FT/TT no tienen diodo a V<sub>DD</sub>; TT_a aguanta 4.0 V; la inyección negativa degrada otros canales (T.14, T.15, T.63)</td><td>La última etapa, alimentada como el ADC (P8), o sujeción externa: P14 (§9)</td><td>{tag('t-ok','Adoptar')}</td></tr>
      <tr><td>CH2 y CH3 no tienen comparador</td><td>PE9 y PE15 no son entrada de ningún COMP (RM T.199)</td><td>Con D-02, el disparo de CH2/CH3 va por analog watchdog (P11/P12), por un segundo pin, o moviendo CH2 a PE7, que sí llega a COMP4 (§12)</td><td>{tag('t-open','Decidir')}</td></tr>
      <tr><td>Comparadores y DAC3</td><td>COMP1 y COMP3 toman el umbral de DAC3_CH1 o DAC1_CH1 (RM T.200); DAC3 es el AWG en el mapa firmado</td><td>El umbral de CH1 sale de DAC1 en modo interno, como ya prevé el mapa (§7)</td><td>{tag('t-ok','Confirmado')}</td></tr>
      <tr><td>OPAMP interno</td><td>GBW 7–13 MHz, 500 µA, 50 pF, 90–250 nV/√Hz, muestreo ≥ 200 ns (T.75)</td><td>El generador necesita modo de alta velocidad y un buffer externo. En el óhmetro, el ruido 1/f puede notarse (§6)</td><td>{tag('t-warn','Tener en cuenta')}</td></tr>
      <tr><td>DAC con buffer</td><td>C<sub>L</sub> ≤ 50 pF y R<sub>L</sub> ≥ 5 kΩ; en sample-and-hold, 0.1–1 µF (T.69)</td><td>Tensiones de continua con poco consumo: P15 (§5)</td><td>{tag('t-open','Estudiar')}</td></tr>
      <tr><td>VREFBUF</td><td>2.048 / 2.5 / 2.9 V ±4 mV, hasta ~100 ppm/°C, PSRR 40–55 dB; al arrancar, VREF+ queda como entrada (T.73, RM T.197)</td><td>Si la referencia es externa, el firmware <b>nunca</b> debe dejar HIZ = 0 con ENVR = 0: lleva VREF+ a masa (§8)</td><td>{tag('t-crit','Cuidado')}</td></tr>
      <tr><td>Ayudas del ADC</td><td>Compensación de ganancia y offset, sobremuestreo ×256, BULB y SMPTRIG (RM §21.4)</td><td>Aplicar la calibración P10 y mejorar el DMM sin CPU: P16 (§4)</td><td>{tag('t-open','Estudiar')}</td></tr>
    </tbody>
  </table></div>
""", ("t-open", "Con propuestas")))

S.append(sec("fuentes", "i", "Qué se revisó y cómo", """
  <dl class="kv">
    <dt>Datasheet</dt><dd><code>datasheet/stm32g473.pdf</code> = DS12712 Rev 5, 229 páginas: §3.18–3.22 (descripción), §4 (pines, tabla 12 del LQFP100), §5.2 (máximos absolutos), §5.3.4 (VREFINT), §5.3.5 (consumo), §5.3.13–5.3.14 (inyección y E/S), §5.3.17 (booster), §5.3.18–5.3.24 (ADC, DAC, VREFBUF, COMP, OPAMP, temperatura, VBAT).</dd>
    <dt>Manual</dt><dd><code>datasheet/rm0440-…pdf</code> = RM0440 Rev 9, 2140 páginas: capítulos 21 (ADC), 22 (DAC), 23 (VREFBUF), 24 (COMP), 25 (OPAMP) y las tablas de interconexión de temporizadores (268 y 292).</dd>
    <dt>Método</dt><dd>Texto extraído con PyMuPDF, tablas leídas página a página y cruzadas con la HAL de CubeG4 (<code>stm32g4xx_ll_adc.h</code>) para los números de canal interno. Las cifras derivadas salen de <code>S3G4_LAB_rev2.1/herramientas/calc_g473.py</code>.</dd>
    <dt>No cubierto</dt><dd>Los otros PDF de la carpeta: ESP32-S3, OPA313, LM27762 y REF3325. Del REF3325 sólo se cita el resumen de la primera página (§8).</dd>
    <dt>Referencias T. y RM</dt><dd>«T.61» es la tabla 61 del datasheet; «RM T.199» o «RM §21.4.3», del manual.</dd>
  </dl>
  <ol class="toc">
    <li><a href="#inventario">Inventario</a></li><li><a href="#adc-vel">ADC: velocidad, carga y ruido</a></li>
    <li><a href="#adc-reloj">ADC: reloj y disparo</a></li><li><a href="#adc-modos">ADC: modos y ayudas</a></li>
    <li><a href="#dac">DAC</a></li><li><a href="#opamp">OPAMP</a></li>
    <li><a href="#comp">COMP</a></li><li><a href="#vref">Referencias</a></li>
    <li><a href="#pines">Pines analógicos</a></li><li><a href="#inter">Interconexiones útiles</a></li>
    <li><a href="#consumo">Consumo</a></li><li><a href="#mapa">Contraste con el mapa y D-02</a></li>
    <li><a href="#propuestas">Propuestas P13–P16</a></li>
  </ol>
"""))

S.append(sec("inventario", "1", "Inventario", """
  <div class="tw"><table>
    <thead><tr><th>Bloque</th><th>Cuántos</th><th>Cifras clave</th><th>Fuente</th></tr></thead>
    <tbody>
      <tr><td>ADC SAR 12 bits</td><td class="n">5</td><td>4 MSa/s con un solo ADC a 60 MHz; hasta 5 canales rápidos (IN1–IN5) y 13 lentos por ADC; 3 analog watchdog; sobremuestreo ×256; diferencial; pares duales ADC1/ADC2 y ADC3/ADC4; ADC5 va solo</td><td class="src">§3.18, T.61, RM §21.2</td></tr>
      <tr><td>DAC 12 bits</td><td class="n">7 canales</td><td>DAC1 (2 canales, PA4/PA5) y DAC2 (1 canal, PA6): con buffer y 1 MSa/s. DAC3 y DAC4 (2 canales cada uno): sólo internos, sin buffer, 15 MSa/s</td><td class="src">§3.19, RM T.183</td></tr>
      <tr><td>OPAMP</td><td class="n">6</td><td>GBW 13 MHz típico (7 mín.), rail-to-rail, PGA ×2…×64 o −1…−63, salida interna al ADC</td><td class="src">§3.22, T.75</td></tr>
      <tr><td>COMP</td><td class="n">7</td><td>16.7 ns típico, histéresis en 8 pasos, umbral desde DAC o VREFINT, salida a temporizadores</td><td class="src">§3.21, T.74</td></tr>
      <tr><td>VREFBUF</td><td class="n">1</td><td>2.048, 2.5 o 2.9 V hacia VREF+</td><td class="src">§3.20, T.73</td></tr>
      <tr><td>Internos</td><td>—</td><td>VREFINT 1.212 V típico; sensor de temperatura de 2.5 mV/°C; VBAT/3</td><td class="src">T.20, T.76, T.77</td></tr>
    </tbody>
  </table></div>
"""))

rrows = "".join(
    f'<tr><td>{r["clk"]}</td><td class="n">{ms(r["fast"])}</td><td class="n">{ms(r["slow"])}</td><td class="n">{ms(r["opamp"])}</td>'
    + (f'<td class="n">—</td><td class="n">—</td>' if r["f"] == 60e6 else f'<td class="n">{ms(r["il_fast"])}</td><td class="n">{ms(r["il_slow"])}</td>')
    + '</tr>' for r in G.rates)
rain = "".join(f'<tr><td class="n">{c}</td><td class="n">{ns:g} ns</td><td class="n">{a} Ω</td><td class="n">{"no admitido" if b is None else f"{b} Ω"}</td></tr>' for c, ns, a, b in G.RAIN12)
S.append(sec("adc-vel", "2", "ADC: velocidad, carga del pin y ruido", f"""
  <p>Cada conversión dura el muestreo más 12.5 ciclos, así que f<sub>s</sub> = f<sub>ADC</sub> / (muestreo + 12.5). Lo que limita es f<sub>ADC</sub>: 60 MHz con un solo ADC, <b>52 MHz con varios</b> si V<sub>DDA</sub> ≥ 2.7 V y 42 MHz por debajo (T.61). Además, los canales lentos no admiten 2.5 ciclos a 12 bits (T.62), y la salida de un OPAMP por el canal interno necesita ≥ 200 ns de muestreo (T.75).</p>
  <div class="tw"><table>
    <thead><tr><th>Reloj del ADC</th><th>Canal rápido, 2.5 ciclos</th><th>Canal lento, 6.5 ciclos</th><th>OPAMP interno, ≥ 200 ns</th><th>Dos ADC entrelazados, rápido</th><th>Dos ADC entrelazados, lento</th></tr></thead>
    <tbody>{rrows}</tbody>
  </table></div>
  <p class="src">MSa/s. Entrelazado rápido: SMPPLUS convierte 2.5 ciclos en 3.5, cada ADC tarda 16 ciclos y se alternan cada 8 (RM §21.4.12). Entrelazado lento: cálculo propio sobre RM §21.4.30 con disparo externo. El esclavo empieza muestreo + 0.5 + DELAY ciclos después del maestro; con DELAY = {r52['il_delay']}, cada muestra llega cada {6.5 + 0.5 + r52['il_delay']:g} ciclos. <b>Está por verificar en banco.</b> El entrelazado necesita dos ADC, así que no aplica a la fila de 60 MHz.</p>
  <h3>Qué resistencia puede ver el pin</h3>
  <p>El condensador de muestreo (C<sub>ADC</sub> = 5 pF) debe cargarse a menos de medio LSB en el tiempo de muestreo. El fabricante lo resume en la R<sub>AIN</sub> máxima (T.62, 12 bits, f<sub>ADC</sub> = 60 MHz):</p>
  <div class="tw"><table><thead><tr><th>Ciclos</th><th>Tiempo</th><th>Canal rápido</th><th>Canal lento</th></tr></thead><tbody>{rain}</tbody></table></div>
  <p>Consecuencia para las secciones D y F: con 2.5 ciclos, <b>la etapa final debe atacar al pin con menos de 100 Ω</b>. Un RC anti-alias justo antes del pin tiene que ser de R pequeña y C grande (el OpenScope usa 68 Ω y 470 pF). Así el condensador externo actúa de depósito: cede carga al de 5 pF sin que la tensión caiga.</p>
  <h3>El ruido del propio ADC</h3>
  <p>SNR típico de 66.9 dB con un solo ADC (T.63) y 63.2 dB con varios en todo el rango de temperatura (T.68); ENOB de 10.1–10.7 bits. Una senoide a fondo de escala tiene V<sub>REF</sub>/(2√2) rms, así que el ruido equivalente es:</p>
  <div class="eq">v_n = (VREF+ / 2√2) / 10^(SNR/20)
VREF+ = 2.5 V:  {G.ADC_NOISE[(2.5,66.9)]*1e3:.2f} mV (66.9 dB) … {G.ADC_NOISE[(2.5,63.2)]*1e3:.2f} mV (63.2 dB)
VREF+ = 3.3 V:  {G.ADC_NOISE[(3.3,66.9)]*1e3:.2f} mV … {G.ADC_NOISE[(3.3,63.2)]*1e3:.2f} mV</div>
  <p>Con 0.25 V por división en el ADC (sección C), eso es <b>{n25/G.VDIV_ADC*100:.2f}–{n25b/G.VDIV_ADC*100:.2f} % de división</b> con 2.5 V, lo mismo que el ruido del AFE que calculamos (0.2–0.3 %). Los dos se suman en cuadratura: bajar más el ruido del AFE rinde poco, porque el ADC ya pone ese suelo. El sobremuestreo lo mejora en escalas lentas (§4).</p>
"""))

jrows = "".join(f'<tr><td class="n">{f/1e3:g} kHz</td><td class="n">{s:.0f} dB</td><td class="n">{G.enob(s):.1f}</td></tr>' for f, s in G.jit.items())
S.append(sec("adc-reloj", "3", "ADC: reloj y disparo", f"""
  <p>El reloj del ADC puede venir de dos sitios (RM §21.4.3):</p>
  <ul class="tight">
    <li><b>Asíncrono</b> (CKMODE = 00): del reloj del sistema o del PLL «P», con prescaler propio. Llega a 52/60 MHz sea cual sea la frecuencia de la CPU, pero el disparo del temporizador se resincroniza: la latencia varía entre 1.5 y 2.5 ciclos (T.61).</li>
    <li><b>Síncrono</b> (CKMODE = 01/10/11): HCLK/1, /2 o /4. La latencia es fija (2, 2.25 o 2.125 ciclos) y el manual lo recomienda cuando el ADC lo dispara un temporizador y hace falta precisión.</li>
  </ul>
  <p>Si la fase entre el disparo y el reloj del ADC fuera aleatoria, un ciclo de incertidumbre a 52 MHz ({1/52e6*1e9:.1f} ns, σ = {G.JIT_SIGMA*1e9:.2f} ns) limitaría así una senoide a fondo de escala. Es el peor caso: con relojes del mismo PLL, parte del error se vuelve periódico en vez de aleatorio.</p>
  <div class="tw"><table><thead><tr><th>Frecuencia de la señal</th><th>SNR máximo por incertidumbre</th><th>ENOB equivalente</th></tr></thead><tbody>{jrows}</tbody></table></div>
  <p>La salida limpia es el modo síncrono. <b>HCLK = 104 MHz con CKMODE = HCLK/2</b> da exactamente 52 MHz: se mantienen las velocidades de D-02 y la CPU consume unos {G.IDD_104:.1f} mA en vez de {G.IDD[170]:.1f} mA a 170 MHz (T.21, interpolado). black_scope usa HCLK/4 = 42.5 MHz, que baja D-02 a {ms(r425['il_fast'])} y {ms(r425['fast'])} MSa/s. Es la propuesta P13.</p>
"""))

S.append(sec("adc-modos", "4", "ADC: modos y ayudas por hardware", f"""
  <dl class="kv">
    <dt>Dual</dt><dd>Sólo ADC1+ADC2 y ADC3+ADC4. Hay siete combinaciones de simultáneo regular, simultáneo inyectado, entrelazado y disparo alterno (RM §21.4.30). En entrelazado sólo un ADC muestrea a la vez; DELAY va de 1 a 12 ciclos a 12 bits (RM T.179). DUAL y DELAY sólo se escriben con los ADC parados, como recoge D-02.</dd>
    <dt>Watchdogs</dt><dd><b>AWD1</b>: umbrales de 12 bits, sobre un canal o todos, con filtro de N conversiones fuera de rango. <b>AWD2 y AWD3</b>: umbrales de <b>8 bits</b> (los 8 MSB) sobre cualquier grupo de canales (RM §21.4.28). Cada uno saca una señal <code>ADCy_AWDx_OUT</code> hacia la ETR de temporizadores (§10).</dd>
    <dt>Sobremuestreo</dt><dd>De ×2 a ×256 con desplazamiento de 0 a 8 bits y resultado de hasta 16 bits (RM §21.4.29). Útil para el DMM y para un modo de alta resolución en bases de tiempo lentas.</dd>
    <dt>Ganancia y offset</dt><dd>Hasta cuatro offsets por ADC que se restan por canal, con saturación, y un factor de ganancia (GCOMP) aplicado por hardware (RM §21.4.26). Encaja con el modelo A · código + C de P10.</dd>
    <dt>BULB</dt><dd>El muestreo empieza al acabar la conversión anterior y lo cierra el disparo (RM §21.4.12). A 1 MSa/s con 52 MHz deja ≈ {G.BULB_1M:.0f} ciclos de muestreo sin perder velocidad: sirve para canales lentos o fuentes de más impedancia. No admite modo continuo ni inyectados.</dd>
    <dt>SMPTRIG</dt><dd>El flanco de subida del disparo abre el muestreo y el de bajada lo cierra. Así el instante de muestreo queda fijado por un PWM; es una base posible para muestreo en tiempo equivalente.</dd>
    <dt>Calibración</dt><dd><code>ADCAL</code> tras cada arranque (lo recomienda T.61); 116 ciclos.</dd>
  </dl>
"""))

S.append(sec("dac", "5", "DAC", """
  <div class="tw"><table>
    <thead><tr><th></th><th>DAC1 y DAC2 (1 MSa/s)</th><th>DAC3 y DAC4 (15 MSa/s)</th></tr></thead>
    <tbody>
      <tr><td>Salida</td><td>Pin (PA4, PA5, PA6) y/o periféricos internos; buffer opcional</td><td>Sólo interna: COMP, OPAMP VINP</td></tr>
      <tr><td>Carga con buffer</td><td>C<sub>L</sub> ≤ 50 pF, R<sub>L</sub> ≥ 5 kΩ; salida de 0.2 V a VREF+ − 0.2 V</td><td>—</td></tr>
      <tr><td>Sin buffer</td><td>R<sub>O</sub> = 9.6–13.8 kΩ; salida de 0 a VREF+</td><td>Siempre sin buffer, de 0 a VREF+</td></tr>
      <tr><td>Asentamiento</td><td>1.7 µs típico, 3 µs máximo (±0.5 LSB)</td><td>64 ns a 1 LSB con un COMP; 93 ns con COMP y OPAMP</td></tr>
      <tr><td>Precisión</td><td>TUE ±30 LSB (±23 LSB calibrado); ganancia ±0.5 %; SNR 71 dB</td><td>TUE ±5 LSB</td></tr>
      <tr><td>Consumo típico</td><td>315 µA de V<sub>DDA</sub> + 185 µA de VREF+ con buffer; ~155 µA sin buffer</td><td>720 µA de VREF+ (código medio)</td></tr>
    </tbody>
  </table></div>
  <p class="src">T.69–T.72; RM §22.3 y §22.4.12.</p>
  <ul class="tight">
    <li><b>Sample-and-hold</b> (RM §22.4.12): el DAC convierte, carga un condensador externo de 0.1–1 µF, se apaga y refresca de vez en cuando con el reloj LSI/LSE. Consume unas 15 veces menos. Es la forma correcta de dar una tensión de continua con un condensador grande, justo lo que black_scope hace mal con DAC2.</li>
    <li><b>Modos del buffer</b> (DAC_MCR): 000 pin con buffer; 001 pin y periféricos con buffer; 010 pin sin buffer; 011 sólo periféricos sin buffer. El mapa firmado usa DAC1 en modo interno para liberar PA4 y PA5.</li>
    <li><b>Ondas por hardware:</b> ruido, triángulo y diente de sierra con incremento programable, sin DMA.</li>
  </ul>
"""))

prow = "".join(f'<tr><td class="n">×{g}</td><td class="n">{r2:g} / 10 kΩ</td><td class="n">{bmin/1e3:.0f}–{btyp/1e3:.0f} kHz</td><td class="n">{"±1 %" if g <= 16 else "±2 %"}</td></tr>' for g, r2, bmin, btyp in G.PGA)
S.append(sec("opamp", "6", "OPAMP", f"""
  <div class="tw"><table>
    <thead><tr><th>Parámetro</th><th>Valor</th><th>Lectura para nosotros</th></tr></thead>
    <tbody>
      <tr><td>GBW</td><td>7 MHz mín., 13 MHz típ.</td><td>Seguidor de un AWG de 1 MHz: bien</td></tr>
      <tr><td>Slew rate</td><td>2.5–6.5 V/µs normal; 18–45 V/µs alta velocidad</td><td>3 Vpp sin distorsión: {G.FPBW['normal'][0]/1e3:.0f}–{G.FPBW['normal'][1]/1e3:.0f} kHz en normal y {G.FPBW['alta velocidad'][0]/1e6:.1f}–{G.FPBW['alta velocidad'][1]/1e6:.1f} MHz en alta velocidad: <b>el generador necesita alta velocidad (OPAHSM)</b></td></tr>
      <tr><td>Carga</td><td>500 µA (270 µA en PGA), 50 pF</td><td>No puede dar 50 Ω ni un cable: hace falta buffer externo</td></tr>
      <tr><td>Offset</td><td>±1.5 mV a 25 °C, ±3 mV en todo el rango; 10 µV/°C</td><td>Autocalibrable (RM §25.3.7)</td></tr>
      <tr><td>Ruido</td><td>250 nV/√Hz a 1 kHz, 90 nV/√Hz a 10 kHz</td><td>Unas 10 veces un OPA313 (25 nV/√Hz). Si la pendiente fuera 1/f pura: ≈ {G.VN_01_10*1e6:.0f} µV rms entre 0.1 y 10 Hz. Estimación por verificar en el óhmetro del DMM</td></tr>
      <tr><td>CMRR / PSRR</td><td>60 dB / 80 dB</td><td></td></tr>
      <tr><td>Muestreo hacia el ADC</td><td>≥ 200 ns (V<sub>DDA</sub> ≥ 2 V)</td><td>≥ 12.5 ciclos a 52 MHz</td></tr>
      <tr><td>Consumo</td><td>1.3 mA típ. (1.4 en alta velocidad); 0.45 mA con salida interna</td><td></td></tr>
    </tbody>
  </table></div>
  <p class="src">T.75; RM §25.3.</p>
  <h3>PGA</h3>
  <div class="tw"><table><thead><tr><th>Ganancia</th><th>R2 / R1</th><th>Ancho de banda (GBW/G)</th><th>Error de ganancia</th></tr></thead><tbody>{prow}</tbody></table></div>
  <p>R1 y R2 varían ±15 % en absoluto, pero su cociente es preciso. En modo inversor, la impedancia de la fuente se suma a R1 y cambia la ganancia (RM §25.3.6). Los modos «con filtrado» sacan el nodo inversor a un pin para poner un condensador en paralelo con R2 (RM §25.3.5).</p>
  <h3>Rutas internas</h3>
  <ul class="tight">
    <li><b>VINP desde DAC:</b> OPAMP1 y OPAMP6 desde DAC3_CH1; OPAMP3 desde DAC3_CH2; OPAMP4 desde DAC4_CH1; OPAMP5 desde DAC4_CH2 (RM T.204). Es la ruta del AWG del mapa firmado: DAC3_CH1 → OPAMP6 → PB11 y DAC3_CH2 → OPAMP3 → PB1.</li>
    <li><b>Salida al ADC</b> (verificado en la HAL): VOPAMP1 → ADC1 canal 13; VOPAMP2 → ADC2 canal 16; VOPAMP3 → ADC2 canal 18 y ADC3 canal 13; VOPAMP4 → ADC5 canal 5; VOPAMP5 → ADC5 canal 3; VOPAMP6 → ADC4 canal 17.</li>
    <li><b>Multiplexor por temporizador</b> (RM §25.3.8): un temporizador conmuta VINP/VINM entre dos configuraciones.</li>
  </ul>
"""))

S.append(sec("comp", "7", "COMP", """
  <dl class="kv">
    <dt>Retardo</dt><dd>16.7 ns típico, 31 ns máximo con V<sub>DDA</sub> ≥ 2.7 V, para un escalón de 200 mV con 100 mV de sobreexcitación.</dd>
    <dt>Offset</dt><dd>−9 / +3 mV en todo el rango.</dd>
    <dt>Histéresis</dt><dd>0, 9, 18, 27, 36, 45, 54 o 63 mV típicos. <b>Sólo actúa en el flanco de bajada de la salida</b>: es asimétrica (RM §24.3.5).</dd>
    <dt>Otros</dt><dd>Blanking por temporizador, bloqueo de configuración y 450 µA de consumo típico.</dd>
  </dl>
  <p class="src">T.74; RM §24.</p>
  <div class="tw"><table>
    <thead><tr><th>COMP</th><th>INP (INPSEL 0 / 1)</th><th>INM desde DAC (100 / 101)</th><th>INM desde pin (110 / 111)</th></tr></thead>
    <tbody>
      <tr><td>COMP1</td><td>PA1 / PB1</td><td>DAC3_CH1 / DAC1_CH1</td><td>PA4 / PA0</td></tr>
      <tr><td>COMP2</td><td>PA7 / PA3</td><td>DAC3_CH2 / DAC1_CH2</td><td>PA5 / PA2</td></tr>
      <tr><td>COMP3</td><td>PA0 / PC1</td><td>DAC3_CH1 / DAC1_CH1</td><td>PF1 / PC0</td></tr>
      <tr><td>COMP4</td><td>PB0 / PE7</td><td>DAC3_CH2 / DAC1_CH1</td><td>PE8 / PB2</td></tr>
      <tr><td>COMP5</td><td>PB13 / PD12</td><td>DAC4_CH1 / DAC1_CH2</td><td>PB10 / PD13</td></tr>
      <tr><td>COMP6</td><td>PB11 / PD11</td><td>DAC4_CH2 / DAC2_CH1</td><td>PD10 / PB15</td></tr>
      <tr><td>COMP7</td><td>PB14 / PD14</td><td>DAC4_CH1 / DAC2_CH1</td><td>PD15 / PB12</td></tr>
    </tbody>
  </table></div>
  <p class="src">RM T.199 y T.200. INMSEL 000–011 selecciona ¼, ½, ¾ o todo VREFINT.</p>
  <p>Para CH1 en PA0, el comparador es COMP3 y su umbral sale de DAC3_CH1 o de DAC1_CH1. Como DAC3 es el AWG, <b>el umbral tiene que venir de DAC1_CH1</b>, que el mapa firmado ya reserva en modo interno. COMP1 comparte las mismas dos fuentes: con un solo canal de disparo activo a la vez no hay conflicto.</p>
"""))

S.append(sec("vref", "8", "Referencias", """
  <div class="tw"><table>
    <thead><tr><th></th><th>VREFBUF interno</th><th>REF3325 (en <code>datasheet/</code>)</th></tr></thead>
    <tbody>
      <tr><td>Tensión</td><td>2.048 / 2.5 / 2.9 V, ±4 mV</td><td>2.5 V, ±0.15 % máx.</td></tr>
      <tr><td>Deriva</td><td>La de VREFINT (30–50 ppm/°C) + 50 ppm/°C</td><td>30 ppm/°C máx.</td></tr>
      <tr><td>V<sub>DDA</sub> mínima</td><td>2.4 / 2.8 / 3.135 V según la tensión elegida</td><td>110 mV de caída</td></tr>
      <tr><td>Carga</td><td>6.5 mA; necesita 0.5–1.5 µF con un 100 nF de baja ESR</td><td>±5 mA</td></tr>
      <tr><td>PSRR</td><td>40–55 dB en continua, 25–40 dB a 100 kHz</td><td>—</td></tr>
      <tr><td>Consumo</td><td>16 µA</td><td>3.9 µA</td></tr>
    </tbody>
  </table></div>
  <p class="src">T.73; RM §23 y T.197; primera página de la hoja del REF3325.</p>
  <ul class="tight">
    <li><b>Modos del VREFBUF</b> (RM T.197): ENVR = 0 y HIZ = 1 es el estado tras el reset, con VREF+ como entrada para una referencia externa. ENVR = 1 y HIZ = 0 activa la referencia interna. <b>ENVR = 0 y HIZ = 0 conecta VREF+ a masa</b>: con una referencia externa, ese estado la cortocircuita. El firmware no debe escribirlo nunca.</li>
    <li><b>VREFINT</b>: 1.182–1.232 V (1.212 V típico), calibrado a 30 °C con V<sub>DDA</sub> = 3.0 V (dirección 0x1FFF 75AA). Necesita ≥ 4 µs de muestreo. Sirve para medir V<sub>DDA</sub> o la batería sin referencia externa.</li>
    <li><b>Sensor de temperatura</b>: 2.5 mV/°C, calibrado a 30 y 130 °C (0x1FFF 75A8 y 0x1FFF 75CA), ≥ 5 µs de muestreo. <b>VBAT/3</b>: ≥ 12 µs.</li>
    <li>VREF+ no puede superar a V<sub>DDA</sub> en más de 0.4 V (T.14).</li>
  </ul>
"""))

S.append(sec("pines", "9", "Pines analógicos y protección", """
  <ul class="tight">
    <li><b>Tipos:</b> «_a» marca un pin con interruptor analógico alimentado desde V<sub>DDA</sub>. <b>TT_a</b> tolera 3.6 V; <b>FT_a</b> tolera 5 V como digital (T.12).</li>
    <li><b>Máximos absolutos</b> (T.14): TT_xx de −0.3 a 4.0 V; FT_xxx hasta min(V<sub>DD</sub>, V<sub>DDA</sub>) + 4 V.</li>
    <li><b>Sin inyección positiva</b> (T.15): «positive injection is not possible on these I/Os». No hay diodo hacia V<sub>DD</sub> que recorte una sobretensión: el pin sube hasta romperse. La negativa se tolera hasta −5 mA por pin y −25 mA en total.</li>
    <li><b>La inyección negativa estropea otras medidas:</b> reduce la precisión de la conversión en curso en otro canal. El fabricante recomienda un Schottky del pin a masa si puede ocurrir (notas de T.63–T.68).</li>
    <li><b>Fuga y capacidad:</b> ±100 nA (FT) o ±150 nA (TT) entre 0 y V<sub>DD</sub>; 5 pF por pin (T.54). La fuga es también la corriente de polarización de los OPAMP internos: 150 nA sobre 1 MΩ son 150 mV.</li>
    <li><b>Booster de los interruptores</b> (T.60, SYSCFG BOOSTEN): sólo hace falta con V<sub>DDA</sub> &lt; 2.4 V y consume hasta 900 µA. A 3.3 V debe quedar apagado.</li>
  </ul>
  <p><b>Consecuencia:</b> ninguna tensión de la entrada puede llegar a un pin del ADC sin pasar por algo que la limite a 0…V<sub>DDA</sub>. La forma robusta es la de P8: la última etapa se alimenta desde el mismo V<sub>DDA</sub> y no puede sacar más. Es la propuesta P14.</p>
"""))

S.append(sec("inter", "10", "Interconexiones útiles", """
  <div class="tw"><table>
    <thead><tr><th>Origen</th><th>Destino</th><th>Uso</th><th>Fuente</th></tr></thead>
    <tbody>
      <tr><td>COMP1…COMP7</td><td>ETR de TIM1/8/20 y TIM2/3/4/5; entradas de captura; BKIN</td><td>Disparo por comparador sin interrupción (P12)</td><td class="src">RM T.268, T.292</td></tr>
      <tr><td>ADC1/ADC4 AWD1–3</td><td>ETR de TIM1</td><td rowspan="3">Disparo por watchdog sin interrupción (P12)</td><td class="src" rowspan="3">RM T.268, T.292</td></tr>
      <tr><td>ADC2/ADC3 AWD1–3</td><td>ETR de TIM8; ADC2 también a TIM3</td></tr>
      <tr><td>ADC3/ADC5 AWD1–3</td><td>ETR de TIM20</td></tr>
      <tr><td>DAC3/DAC4</td><td>VINP de OPAMP; INM de COMP</td><td>AWG rápido; umbrales</td><td class="src">RM T.204, T.200</td></tr>
      <tr><td>OPAMPx</td><td>Canal interno del ADC (OPAINTOEN)</td><td>Medidas lentas sin gastar pin</td><td class="src">RM §25.3.1</td></tr>
      <tr><td>Temporizadores</td><td>Disparo de ADC y DAC; DMA</td><td>Muestreo y AWG a ritmo fijo</td><td class="src">RM §21.4.18, §22.4.7</td></tr>
    </tbody>
  </table></div>
"""))

brow = "".join(f'<tr><td>{n}</td><td class="n">{v/1000:.2f} mA</td></tr>' for n, v in G.BUDGET)
S.append(sec("consumo", "11", "Consumo", f"""
  <p><b>CPU</b> (T.21, típico a 25 °C, desde flash y sin periféricos): {G.IDD[170]:.1f} mA a 170 MHz, {G.IDD[150]:.1f} mA a 150 MHz, {G.IDD[120]:.1f} mA a 120 MHz y {G.IDD[80]:.1f} mA a 80 MHz. A 104 MHz, interpolando, unos <b>{G.IDD_104:.1f} mA</b>.</p>
  <p><b>Bloques analógicos</b>, con valores típicos de las tablas del fabricante y una configuración supuesta (no decidida):</p>
  <div class="tw"><table><thead><tr><th>Bloque</th><th>Corriente</th></tr></thead><tbody>{brow}
    <tr><td><b>Total</b></td><td class="n"><b>{G.BUDGET_TOTAL/1000:.2f} mA</b></td></tr></tbody></table></div>
  <p>Frente a la radio del ESP32-S3, las partes analógicas del G473 pesan poco. La decisión que más ahorra es la frecuencia de la CPU (P13).</p>
"""))

S.append(sec("mapa", "12", "Contraste con el mapa firmado y con D-02", """
  <div class="tw"><table>
    <thead><tr><th>Pin</th><th>Uso (mapa de la rev 2.0 o D-02)</th><th>Canal de ADC</th><th>Tipo</th><th>Comparador</th><th>OPAMP</th></tr></thead>
    <tbody>
      <tr><td><code>PA0</code></td><td>CH1, ADC1+ADC2 entrelazados (D-02)</td><td>ADC12_IN1</td><td>rápido</td><td>COMP3_INP</td><td>—</td></tr>
      <tr><td><code>PE9</code></td><td>Candidato a CH2 en ADC3 (D-02); en la rev 2.0 era CH3</td><td>ADC3_IN2</td><td>rápido</td><td><b>ninguno</b></td><td>—</td></tr>
      <tr><td><code>PE15</code></td><td>Candidato a CH3 en ADC4 (D-02); en la rev 2.0 era CH4</td><td>ADC4_IN2</td><td>rápido</td><td><b>ninguno</b></td><td>—</td></tr>
      <tr><td><code>PE7</code></td><td>Libre en el mapa</td><td>ADC3_IN4</td><td>rápido</td><td>COMP4_INP</td><td>—</td></tr>
      <tr><td><code>PA1</code></td><td>CH2 en la rev 2.0 (ADC2_IN2)</td><td>ADC12_IN2</td><td>rápido</td><td>COMP1_INP</td><td>OPAMP1/3 VINP, OPAMP6 VINM</td></tr>
      <tr><td><code>PD11</code></td><td>Rev 2.0: CH3 entrelazado y disparo COMP6</td><td>ADC345_IN8</td><td>lento</td><td>COMP6_INP</td><td>OPAMP4 VINP</td></tr>
      <tr><td><code>PD12</code></td><td>Rev 2.0: disparo COMP5 de CH4</td><td>ADC345_IN9</td><td>lento</td><td>COMP5_INP</td><td>OPAMP5 VINP</td></tr>
      <tr><td><code>PD13</code> / <code>PD14</code></td><td>DMM diferencial</td><td>ADC5_IN10 / ADC345_IN11</td><td>lento</td><td>COMP5_INM / COMP7_INP</td><td>OPAMP2 VINP (PD14)</td></tr>
      <tr><td><code>PB14</code></td><td>DMM: resistencia, diodo y continuidad</td><td>ADC4_IN4 / ADC1_IN5</td><td>rápido</td><td>COMP7_INP</td><td>OPAMP5 VINP0</td></tr>
      <tr><td><code>PB13</code></td><td>Batería y temperatura</td><td>ADC3_IN5</td><td>rápido</td><td>COMP5_INP</td><td>OPAMP4 VINP0</td></tr>
      <tr><td><code>PB11</code> / <code>PB1</code></td><td>AWG CH1 / CH2</td><td>ADC12_IN14 / ADC3_IN1</td><td>lento / rápido</td><td>COMP6_INP / COMP1_INP</td><td>OPAMP6 / OPAMP3 VOUT</td></tr>
    </tbody>
  </table></div>
  <p class="src">Pines de la tabla 12 del datasheet (LQFP100); comparadores de RM T.199; OPAMP de RM T.204; usos de <code>docs/MAPA_PINES_FIRMADO.md</code> y de D-02.</p>
  <ul class="tight">
    <li><b>Coherente:</b> los tres canales del osciloscopio de D-02 caen en canales rápidos, y el entrelazado de CH1 usa un pin compartido por ADC1 y ADC2.</li>
    <li><b>Abierto:</b> PE9 y PE15 no llegan a ningún comparador. Para disparar CH2 o CH3 hay tres caminos:
      <ul class="tight">
        <li>El analog watchdog de su ADC (P11), que sí llega por hardware a un temporizador (P12).</li>
        <li>Cablear la salida de la etapa final también a PD11/PD12, como hacía la rev 2.0 con CH3 y CH4.</li>
        <li>Para CH2, usar <code>PE7</code> (ADC3_IN4, rápido), que llega a COMP4_INP; su umbral saldría de DAC1_CH1, compartido con CH1. En ADC4, el único canal rápido con comparador es PB14 (COMP7), y el mapa lo usa para el DMM.</li>
      </ul></li>
    <li><b>Abierto:</b> el mapa firmado es de la rev 2.0, con cuatro canales. Con tres canales y D-02 hay que revisarlo; este contraste no lo modifica.</li>
  </ul>
"""))

S.append(sec("propuestas", "13", "Propuestas para la rev 2.1", f"""
  <p>Continúan la numeración: P1–P11 de los referentes y P12 de black_scope. Ninguna está aplicada.</p>
  <h3>P13 · Reloj del ADC síncrono <span class="tag t-open">Decidir</span></h3>
  <p>CKMODE = HCLK/2 con HCLK = 104 MHz: 52 MHz exactos para el ADC, sin incertidumbre de disparo y con unos {G.SAVE_104:.1f} mA menos en la CPU. La alternativa es HCLK = 170 MHz con /4 (42.5 MHz), que baja D-02 a {ms(r425['il_fast'])} y {ms(r425['fast'])} MSa/s. Falta comprobar que el resto del firmware (enlace con el ESP32-S3, DMA, AWG) cabe a 104 MHz. Se decide con la sección D.</p>
  <h3>P14 · Ningún pin analógico recibe más de V<sub>DDA</sub> <span class="tag t-ok">Adoptar</span></h3>
  <p>El G473 no admite inyección positiva: la etapa que ataca cada pin del ADC se alimenta desde V<sub>DDA</sub> (P8), o se sujeta con un Schottky a V<sub>DDA</sub> y otro a masa detrás de una resistencia. Esa resistencia debe respetar la R<sub>AIN</sub> de §2, así que la sujeción va antes del RC anti-alias. Se aplica en la sección F.</p>
  <h3>P15 · Tensiones de continua con el DAC en sample-and-hold <span class="tag t-open">Estudiar</span></h3>
  <p>El offset por canal (P6), los umbrales lentos y las polarizaciones pueden salir de un DAC en sample-and-hold con condensador externo de 0.1–1 µF: dentro de especificación y con una fracción del consumo. Alternativa: DAC sin buffer (≈ 12 kΩ de salida) con un buffer externo de bajo consumo, como el OPA313 de la carpeta.</p>
  <h3>P16 · Calibración y DMM con las ayudas del ADC <span class="tag t-open">Estudiar</span></h3>
  <p>El modelo de P10 (A · código + C por escala) se puede aplicar por hardware con GCOMP y los offsets por canal. El DMM gana resolución con el sobremuestreo de hasta ×256, y los canales lentos toleran fuentes de más impedancia con BULB. Es trabajo de firmware y no cambia el hardware.</p>
"""))

HTML = (
 '<title>Periféricos analógicos del G473</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · STM32G473VET6 · referencia para el AFE rev 2.1</p>\n  <h1>Periféricos analógicos del G473</h1>\n'
 '  <p class="lede">ADC, DAC, OPAMP, COMP, VREFBUF y pines analógicos del STM32G473, leídos en el datasheet y el manual de referencia, con lo que cada cifra significa para nuestro osciloscopio, DMM y generador. Acompaña a <code>S3G4_LAB_rev2.1/02_referencias/analisis_black_scope.html</code>, que pone a prueba estos mismos bloques.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Revisión de Claude Code, 23 sep 2026. Fuentes: <code>datasheet/stm32g473.pdf</code> (DS12712 Rev 5) y <code>datasheet/rm0440-stm32g4-series-advanced-armbased-32bit-mcus-stmicroelectronics (1).pdf</code> (RM0440 Rev 9). '
 'Cifras derivadas en <code>S3G4_LAB_rev2.1/herramientas/calc_g473.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
