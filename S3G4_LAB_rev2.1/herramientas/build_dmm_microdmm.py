# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_microdmm.html (anatomia del Micro-DMM).
Cifras: calc_dmm_microdmm.py. Dibujos: draw_dmm_microdmm.py. Plantilla: build_dmm_tida01012.py."""
import io, math, draw_dmm_microdmm as D, calc_dmm_microdmm as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_microdmm.html"

def ohm(r):
    if r == math.inf: return "abiertas"
    if r == 0: return "0 Ω (cortocircuito)"
    return f"{r/1e6:g} MΩ" if r >= 1e6 else f"{r/1e3:g} kΩ" if r >= 1e3 else f"{r:g} Ω"

def pct(x, d=1):
    return "≈ 0 %" if abs(x) * 100 < 0.5 * 10**-d else f"{x*100:+.{d}f} %".replace("-", "−")

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El Micro-DMM es un multímetro de 4½ dígitos hecho por un técnico (Nicholas Mann, OIH Designs) sobre placas Arduino, con un ADC ADS1115 de 16 bits. Su aporte es el <b>puente de Mann</b>: el voltímetro distingue «0 V porque las puntas tocan el mismo nodo» de «0 V porque no hay circuito entre ellas». Es exactamente nuestro RD-09 (cable abierto). Lo estudiamos a fondo, y de paso entendemos por qué su ohmímetro pierde exactitud por encima de 100 kΩ.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el Micro-DMM</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Cable abierto en tensión</td><td>Un MOSFET en serie con el brazo bajo del puente; al abrirlo, el lado que varía solo sigue unido a la referencia a través de las puntas (§4, §5)</td><td>Es la idea que pide RD-09. En nuestra arquitectura cabe sin piezas nuevas: una lectura breve en el rango de 20 MΩ (P33)</td><td>{tg(OK,'Adoptar la idea')}</td></tr>
      <tr><td>La prueba depende de una fuga</td><td>Lo que baja el nodo durante la prueba no está en el esquema: ≈ {K.R_PD_CERR/1e3:.0f} kΩ deducidos de los umbrales (fuga del Schottky y entrada del ADC). Por eso los umbrales se ajustan por placa (§5)</td><td>Con resistencias definidas y un buffer de pA, los umbrales salen de la cuenta (P33)</td><td>{tg(WARN,'Corregir')}</td></tr>
      <tr><td>Espera en alterna</td><td>Solo prueba si la lectura lleva un cuarto de periodo bajo el umbral (4 ms a 60 Hz), para no confundir un paso por cero con un cable abierto (§5)</td><td>Igual en P33, con 5 ms a 50 Hz</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Ohmios por divisor con la referencia supuesta</td><td>5.0 V a través de 22 kΩ; el firmware da la tensión por buena. Sin calibrar, las 3 placas del autor leen 4.7 MΩ con errores de −18 % a +44 % (§6)</td><td>Confirma la sección H: razón medida con el mismo ADC y R_ref ≈ 1.5 × fondo (S = {K.S_H_FONDO:.2f} frente a {K.ALTO[4.7e6]['S']:.0f})</td><td>{tg(OK,'Confirma H')}</td></tr>
      <tr><td>La impedancia del ADC cambia con la ganancia</td><td>La Z diferencial del ADS1115 pasa de 710 kΩ a 22 MΩ; con una sola constante, la escala se mueve ≈ 1.5–2 % al pasar de ±0.512 V (§4)</td><td>Nuestro ADC5 va detrás de un buffer. La lección vale para cualquier ADC sin buffer</td><td>{tg(OK,'Confirma H')}</td></tr>
      <tr><td>Calibración por tramos en memoria</td><td>15 factores por tramo de resistencia; el detector BlinkyHawk guarda su configuración con número mágico, versión, CRC y migración (§8)</td><td>Es el formato que deben tener P26 y P29</td><td>{tg(OK,'Refuerza P26/P29')}</td></tr>
      <tr><td>Selección automática V/Ω</td><td>Mide tensión y ohmios a la vez y pasa a tensión por encima de 1 V (§8)</td><td>En ohmios, si aparece tensión externa, desconectar la fuente y avisar (P34)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Aislamiento con módulos, Arduino y sensor Hall</td><td>DC-DC aislado, ISO1540, optoacopladores; ACS712 o AMC0330R para corriente (§9, §12)</td><td>Nuestro DMM es de masa común (RD-05) y con derivador propio</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><b>Repositorio</b> <code>research_and_tests/Micro-DMM/</code> (último commit, 12 ago 2026), con unas 35 placas KiCad. Elegí tres:
      <ul class="tight">
        <li><code>PCBDesigns/DMM_KiCAD_V4_next</code> (cambiado por última vez el 11 dic 2025): la arquitectura y el ohmímetro;</li>
        <li><code>SimplifiedOpenLeadVoltmeter</code> y <code>DMM Feather Redux</code> (mayo–junio 2026): el puente. En la V4_next está dibujado de forma que no puede romperse (§4);</li>
        <li><code>OpenLead_Headless_V3</code> (ago 2026): el detector de bolsillo «BlinkyHawk».</li>
      </ul></li>
    <li>Netlists exportadas con <code>kicad-cli</code> 10 y leídas pieza a pieza con <code>herramientas/kinet.py</code>. El esquema de la V4_next se renderizó y se leyó por zonas.</li>
    <li><b>White paper</b> «An Open-Lead Detection Voltmeter Circuit» (N. Mann, 17 jul 2025, 6 p, borrador), manual de uso (texto) y README.</li>
    <li><b>Firmware</b>:
      <ul class="tight">
        <li><code>microDMM_RA4M1_XIAO_SMD_V5</code>: ohmios y calibración;</li>
        <li><code>OpenLeadDetect_Feather_Voltmeter</code>: puente, ago 2026;</li>
        <li><code>BlinkyHawk_RA4M1</code>: detector, ago 2026.</li>
      </ul></li>
    <li><b>Datos medidos</b>: hoja «Calibrations» de <code>DMM Collected Spreadsheets.xlsx</code> (lecturas de 3 placas frente a resistencias medidas). ADS1115: hoja SBAS444E de la carpeta del autor.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_microdmm.py</code>; redibujos en <code>draw_dmm_microdmm.py</code> (0 solapes, revisados a la vista).</li>
  </ul>
"""))

cal_rows = "".join(f"<tr><td>{l}</td><td>{ohm(n)}</td>" + "".join(f"<td>{pct(e)}</td>" for e in errs) + "</tr>"
                   for l, n, errs in K.CAL_ERR)
S.append(sec("especificacion", "2", "Lo que dice el autor y lo que midió", f"""
  <div class="tw"><table>
    <thead><tr><th>Función</th><th>Alcance</th><th>Notas</th></tr></thead>
    <tbody>
      <tr><td>Tensión DC</td><td>±50 V probados; el white paper lo prueba hasta 120 VAC</td><td>Entrada ≈ 1 MΩ diferencial. «No está pensado para tensiones peligrosas»</td></tr>
      <tr><td>Tensión AC</td><td>Aviso por encima de 1 Vrms</td><td>El propio autor la llama «comprobación de cordura», no medida</td></tr>
      <tr><td>Resistencia</td><td>De menos de 10 mΩ a ≈ 1 MΩ; por encima, solo orientativo</td><td>Rango bajo de 20 mA y alto de ≈ 4–5 V; 80 mW como máximo</td></tr>
      <tr><td>Diodo / impedancia</td><td>Tensión entre puntas en mV</td><td>Con la fuente del rango alto (≈ 0.2 mA)</td></tr>
      <tr><td>Corriente</td><td>No incluida</td><td>Módulo Hall externo</td></tr>
      <tr><td>General</td><td>4½ dígitos, 4–6 h de batería, 90 mA por USB</td><td>Cable abierto en tensión en las placas recientes</td></tr>
    </tbody>
  </table></div>
  <p>Lo medido por el autor (hoja «Calibrations»): error de lectura <b>antes</b> de aplicar los factores de calibración, en tres placas.</p>
  <div class="tw"><table>
    <thead><tr><th>Tramo</th><th>Resistencia</th><th>Placa 1</th><th>Placa 2</th><th>Placa 3</th></tr></thead>
    <tbody>{cal_rows}</tbody>
  </table></div>
  <p class="meta">Entre 330 Ω y 100 kΩ las placas leen dentro de ±1 %; por debajo de 33 Ω pesan el nulo y la fuente; por encima de 330 kΩ el error crece con la resistencia, que es lo que explica §6. El −6.6 % de la placa 1 en 33 Ω no tiene explicación en el circuito: NO VERIFICADO.</p>
"""))

S.append(sec("arquitectura", "3", "Arquitectura", """
  <ul class="tight">
    <li><b>Dos entradas</b>, cada una con su conector (dos jacks de barril en la V4_next): el voltímetro diferencial (J15) y el ohmímetro (J14).</li>
    <li><b>Lado de medida flotante (Gnd-iso)</b>:
      <ul class="tight">
        <li>un ADS1115 con cuatro entradas: AIN0 y AIN1 para el voltímetro, AIN2 para ohmios y AIN3 para el módulo de corriente;</li>
        <li>dos referencias: LM4040-2.5 para el puente y LM4040-5 para ohmios;</li>
        <li>alimentación por un DC-DC aislado RFM-0505S (5 V → 5 V, 1 kVDC durante 1 s) y un doblador MAX1683 (+9 V) para los drivers IX4426;</li>
        <li>el I²C cruza por un ISO1540 y las órdenes por optoacopladores LTV-824.</li>
      </ul></li>
    <li><b>MCU</b>: una placa Arduino Uno R4 o XIAO RA4M1 (módulo); pantalla OLED o TFT por conector.</li>
    <li><b>Por qué flota</b>: el autor quiere evitar los lazos de masa cuando el medidor va por USB y el circuito medido está enchufado a la red.</li>
  </ul>
"""))

P = K.PLACAS
placa_rows = "".join(
    f"<tr><td><code>{n}</code></td><td>{ohm(p['Rin'])}</td><td>{ohm(p['fijo'])}</td><td>{ohm(p['conm'])}</td>"
    f"<td>÷{p['k_on']:.1f} / ÷{p['k_off']:.1f}</td><td>{tg(OK,'Sí') if p['rompe'] else tg(CRIT,'No')}</td></tr>"
    for n, p in P.items())
pga_rows = "".join(
    f"<tr><td>±{f:g} V</td><td>{ohm(K.Z_DIFF[f])}</td><td>÷{K.ESCALA[f]:.2f}</td><td>{pct(K.ESCALA_FW/K.ESCALA[f]-1, 2)}</td><td>{K.V_MAX_FSR[f]:.0f} V</td></tr>"
    for f in K.FSR)
S.append(sec("voltimetro", "4", "Voltímetro: el puente de Mann", f"""
{fig(D.puente(), "Redibujo del voltímetro del SimplifiedOpenLeadVoltmeter (la DMM Feather Redux es igual, con 2 × 240 kΩ por lado). El MOSFET se dibuja como un interruptor.")}
  <p>Mide la diferencia entre un lado fijo (AIN0, sujeto a 2.5 V por un LM4040) y un lado que varía (AIN1). Cada punta entra por ≈ 0.5 MΩ, así que la tensión de entrada se reparte entre ≈ 1 MΩ y el puente, y el ADS1115 lee la caída en el puente. Las resistencias de entrada limitan la corriente, y dos Schottky sujetan AIN1 a 0 V y 5 V.</p>
  <div class="tw"><table>
    <thead><tr><th>Placa</th><th>Entrada por lado</th><th>Brazo fijo</th><th>Brazo con MOSFET</th><th>Escala (MOSFET conduce / abierto)</th><th>¿Se rompe el puente?</th></tr></thead>
    <tbody>{placa_rows}</tbody>
  </table></div>
  <p>En la <b>V4_next</b>, el brazo fijo es de 15 kΩ y el MOSFET solo conecta 1 MΩ en paralelo. Al abrirlo, la escala pasa de ÷{P['DMM_KiCAD_V4_next']['k_on']:.1f} a ÷{P['DMM_KiCAD_V4_next']['k_off']:.1f}, y AIN1 sigue unido a la referencia por 15 kΩ: la prueba de cable abierto no puede funcionar así. En las placas posteriores los valores están al revés (1 MΩ fijo y 15 kΩ conmutado), como en la figura 2 del white paper. Es un error de la V4_next o una versión anterior a la idea; para nosotros no cambia nada.</p>
  <h3>La impedancia del ADC según la ganancia</h3>
  <p>El ADS1115 no tiene buffer: su impedancia diferencial (SBAS444E, p. 5) queda en paralelo con el puente de 14.8 kΩ y depende del fondo de escala. El firmware usa una sola constante, 69.95, que es justo la escala con 710 kΩ (fondos de ±0.256 y ±0.512 V). Al subir de rango cambia la escala, y la lectura se desvía:</p>
  <div class="tw"><table>
    <thead><tr><th>Fondo del PGA</th><th>Z diferencial</th><th>Escala real</th><th>Desvío de la lectura con 69.95</th><th>Entrada a fondo</th></tr></thead>
    <tbody>{pga_rows}</tbody>
  </table></div>
  <p>Por encima de unos 36 V la lectura sale entre un 1.5 % y un 2 % alta. Es una deducción de las hojas, no una medida: <b>NO VERIFICADO</b>. Para nosotros: confirma que el ADC debe ir detrás de un buffer (sección H §4), o que hace falta una constante por ganancia.</p>
"""))

S.append(sec("cable-abierto", "5", "Cable abierto: cómo funciona de verdad", f"""
  <h3>La secuencia (firmware de ago 2026)</h3>
  <ol class="tight">
    <li>El voltímetro mide con el puente cerrado y filtra con una media exponencial.</li>
    <li>Si la lectura filtrada baja de 0.3 V, el firmware abre el MOSFET, pone el ADC a ±2.048 V y a la mayor velocidad, hace <b>una</b> lectura diferencial y vuelve a cerrar el MOSFET.</li>
    <li>Si la diferencia queda por debajo de {K.UMBRAL_FW} V, las puntas están cerradas; si no, están al aire. Hacen falta dos resultados seguidos para cambiar de estado.</li>
    <li>Con una tabla medida en el banco, el firmware también estima la resistencia entre puntas por escalones (&lt; 33 kΩ, 100 kΩ, 330 kΩ, 1 MΩ, &gt; 10 MΩ).</li>
  </ol>
  <h3>Lo que no dice el esquema</h3>
  <p>Con el puente abierto, AIN1 solo está unido a AIN0 por R14 (1 MΩ) y, si las puntas tocan un circuito, también por las puntas (998 kΩ más lo que haya entre ellas). Algo tiene que tirar de AIN1 hacia abajo para que haya diferencia, y en el esquema no hay ninguna resistencia que lo haga. Los valores del firmware lo delatan:</p>
  <ul class="tight">
    <li>cerrado (&lt; 10 kΩ): {K.DIFF_CERR} V, es decir, AIN1 = {K.AIN1_CERR:.2f} V;</li>
    <li>abierto (&gt; 10 MΩ): {K.DIFF_ABIE} V, es decir, AIN1 = {K.AIN1_ABIE:.2f} V.</li>
  </ul>
  <p>Para eso hace falta una bajada de ≈ {K.R_PD_CERR/1e3:.0f} kΩ en los dos casos. La entrada del ADS a ±2.048 V es de 6 MΩ en modo común, así que la mayor parte debe ser la <b>fuga del Schottky D5</b>, que crece mucho con la temperatura (NO VERIFICADO). Las consecuencias se ven en el código:</p>
  <ul class="tight">
    <li>los umbrales cambian de una placa a otra (1.34 V en la «roja», 1.42 V en otra, 0.25 V en la versión de placas separadas);</li>
    <li>el detector BlinkyHawk elige el umbral con dos interruptores DIP y lo guarda en memoria;</li>
    <li>y además prueba dos métodos dinámicos: el tiempo que tarda en volver (0.7–0.95 ms) y el área de la vuelta, porque la diferencia estática es pequeña.</li>
  </ul>
  <h3>Corriente y tiempos</h3>
  <ul class="tight">
    <li>Corriente por las puntas durante la prueba: ≈ {K.I_PUNTAS_CERR*1e6:.1f} µA con las puntas en cortocircuito. El white paper habla de {K.I_WP_FIG1*1e9:.0f} nA (y {K.I_WP_FIG2*1e9:.0f} nA con el 1 MΩ fijo), porque simula el ADC con 10 MΩ.</li>
    <li>En alterna, la prueba solo se hace si la lectura lleva <b>4 ms</b> por debajo del umbral (un cuarto de periodo a 60 Hz). Un paso por cero de la red dura microsegundos y no la dispara.</li>
    <li>El BlinkyHawk (OpenLead_Headless_V3):
      <ul class="tight">
        <li>usa el ADC de 14 bits del RA4M1 en seudodiferencial (dos lecturas unipolares restadas), un TL431 de 2.5 V y 5 × 100 kΩ por lado;</li>
        <li>su puente es de 100 kΩ conmutado más 1 MΩ fijo;</li>
        <li>espera 300 µs tras abrir el MOSFET y duerme a 1 mA.</li>
      </ul></li>
  </ul>
  <p><b>Lo que vale</b> es la idea: probar la continuidad desde detrás de la protección del voltímetro, sin pasar a ohmios, con menos de un µA. <b>Lo que hay que corregir</b>: la bajada debe ser una resistencia conocida y el nodo debe leerse con un buffer, para que los umbrales se calculen y no dependan de la temperatura.</p>
"""))

alto_rows = "".join(
    f"<tr><td>{ohm(r)}</td><td>{a['S']:.1f}</td><td>{a['lsb_pct']*100:.2f} %</td><td>{a['gain_pct']*100:.1f} %</td><td>{pct(a['carga'])}</td><td>{pct(a['vz6mV'])}</td></tr>"
    for r, a in K.ALTO.items())
S.append(sec("ohmios", "6", "Ohmios: fuente de 20 mA y divisor de 22 kΩ", f"""
{fig(D.ohmios(), "Redibujo del ohmímetro de la DMM_KiCAD_V4_next. El driver IX4426 da los 9 V que alimentan al LM317 y mueve la puerta de Q2.")}
  <ul class="tight">
    <li><b>Rango bajo</b> (Q2 conduce): fuente de {K.I_FUENTE*1e3:.2f} mA (el firmware la calibra por placa; en la placa 3, 20.087 mA). La purga de 330 Ω se lleva parte de la corriente, de ahí la fórmula R = V / (I − V/330). En el cambio de rango (400 Ω) el borne está a {K.V_EN_UMBRAL:.2f} V y pasan {K.I_DUT_UMBRAL*1e3:.1f} mA por la resistencia.</li>
    <li><b>Resolución</b>: a ±0.256 V cada LSB del ADS vale {K.MOHM_POR_LSB:.2f} mΩ, así que 10 mΩ son {K.LSB_10mOHM:.0f} LSB. Lo de «mejor que 0.01 Ω» es cierto en resolución, pero depende del nulo: las puntas, el fusible y los contactos están dentro de la medida.</li>
    <li><b>Rango alto</b> (Q2 abierto): 5.0 V a través de 22 kΩ, con la tensión de U11 supuesta en el firmware. En un divisor así, cualquier error relativo en V/V_ref se multiplica por S = (R + 22 kΩ) / 22 kΩ:</li>
  </ul>
  <div class="tw"><table>
    <thead><tr><th>R medida</th><th>S</th><th>1 LSB a ±6.144 V</th><th>0.15 % de error de ganancia</th><th>Carga del ADS (≈ {K.Z_ADS_SE/1e6:.1f} MΩ)</th><th>Referencia 6 mV baja</th></tr></thead>
    <tbody>{alto_rows}</tbody>
  </table></div>
  <p>Las tres causas son del mismo orden que lo medido en §2 (en 4.7 MΩ, de −18 % a +44 % según la placa): <b>el límite es el método, no las piezas</b>. Y el método falla porque la referencia no se mide, el ADC carga el nodo y R9 está muy lejos del valor medido.</p>
  <p>Nuestra sección H §6 ya evita las tres cosas:</p>
  <ul class="tight">
    <li>razón con el mismo ADC (la ganancia se cancela);</li>
    <li>R_ref por rango, ≈ 1.5 × fondo (S = {K.S_H_FONDO:.2f} a fondo);</li>
    <li>buffer de pA delante del ADC. El divisor de 10 MΩ en paralelo es una carga conocida y estable, y se corrige.</li>
  </ul>
  <p><b>Purga y ahorro.</b> R6 gasta {K.P_PURGA*1e3:.0f} mW siempre que la fuente está encendida. Por eso hay un modo de ahorro: con las puntas al aire durante 5 s, el firmware baja la fuente y la vuelve a subir al cortocircuitarlas (el manual dice 30 s). Nuestra fuente por R_ref no gasta nada en vacío.</p>
  <p><b>Sin protección.</b> El manual lo dice claro: medir ohmios en un circuito con tensión puede quemar el MOSFET de rango. Q2 conduce por su diodo interno y U11 sujeta a 5 V sin límite de corriente.</p>
"""))

S.append(sec("corriente", "7", "Corriente", """
  <p>No tiene amperímetro propio. El conector J11 (5V-iso, señal y Gnd-iso) recibe un módulo Hall ACS712 o una placa aislada con AMC0330R, y la señal va a AIN3. El autor también propone, sin más, «una resistencia baja sobre el voltímetro». Nada que aprender para nuestro derivador de 0.1 Ω con el OPA2188 (sección H §5).</p>
"""))

S.append(sec("firmware", "8", "Firmware", """
  <ul class="tight">
    <li><b>Autorango del PGA</b>: por número de cuentas (sube de ganancia por debajo de 10 000 y la baja por encima de 26 000, de 32 768), con una relectura tras cada cambio.</li>
    <li><b>Filtros</b>: media exponencial (1/5 en tensión, 1/10 en el puente) y una media de 100 lecturas para ohmios.</li>
    <li><b>Velocidad del ADS adaptativa</b>: 475 SPS ante un salto, 128 SPS normal y 16 SPS en «modo preciso», cuando la lectura está quieta.</li>
    <li><b>Ohmios</b>:
      <ul class="tight">
        <li>cambio de rango en 400 Ω ± 5 %;</li>
        <li>«abierto» si la tensión supera el tope menos 7 mV;</li>
        <li>nulo automático al arrancar si la primera lectura es menor de 10 Ω, y nulo por botón.</li>
      </ul></li>
    <li><b>Calibración</b>:
      <ul class="tight">
        <li>15 factores multiplicativos por tramo (CF_A … CF_O), más la escala del voltímetro, la corriente de la fuente y el tope de tensión, por placa;</li>
        <li>la EEPROM guarda el número de placa y las constantes están en el código (<code>CalibrationConstants.ino</code>);</li>
        <li>una hoja de cálculo sirve de plantilla para obtenerlos.</li>
      </ul>
      El BlinkyHawk va más allá: toda su configuración vive en memoria de datos, con número mágico, versión, CRC, migración entre versiones y órdenes <code>!SET</code>/<code>!SAVE</code> por el puerto serie.</li>
    <li><b>Alterna</b>: valor eficaz de 32 o 100 lecturas a ≤ 860 SPS; solo orientativo.</li>
    <li><b>Selección de función</b>: mide las dos entradas siempre y muestra tensión si supera ≈ 1 V; vuelve a ohmios al cortocircuitar las puntas.</li>
    <li><b>Extras</b>:
      <ul class="tight">
        <li>teclea el valor por USB (teclado HID) en una hoja de cálculo;</li>
        <li>mínimo/máximo, registro y un LED que parpadea con tensión de nivel lógico (&gt; 3.2 V);</li>
        <li>un protocolo de diagnóstico (<code>!CAP</code>) que captura el transitorio del puente para ajustarlo.</li>
      </ul></li>
  </ul>
"""))

S.append(sec("alimentacion", "9", "Alimentación y aislamiento", """
  <p>Batería Li-ion con un elevador TPS613222 a 5 V. El DC-DC aislado RFM-0505S alimenta el lado de medida (1 kVDC durante 1 s, 75 pF de acoplo) y un doblador MAX1683 saca +9 V para los drivers. Da de 4 a 6 h y consume 90 mA por USB. El aislamiento es funcional (contra lazos de masa), no de seguridad.</p>
"""))

S.append(sec("seguridad", "10", "Seguridad: qué aguanta y qué no", f"""
  <ul class="tight">
    <li><b>Voltímetro</b>: con 230 Vrms pasan {K.I_RED*1e3:.2f} mA. Cada 499 kΩ 0805 disipa {K.P_R_RED*1e3:.0f} mW, pero ve {K.V_R_RED:.0f} Vrms ({K.V_R_RED*math.sqrt(2):.0f} V de pico), por encima de los ≈ 150 V habituales de un 0805. Las placas posteriores lo reparten mejor (4 × 240 kΩ o 10 × 100 kΩ). El autor lo probó con un megóhmetro de 1000 V (con corriente limitada) y con 120 VAC.</li>
    <li><b>Ohmímetro</b>: sin protección (§6).</li>
    <li><b>Aislamiento</b>: el del módulo, 1 kVDC de prueba; no es una categoría de medida.</li>
  </ul>
"""))

S.append(sec("no-copiar", "11", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>Una bajada por fuga en la prueba de cable abierto, con umbrales ajustados a mano por placa.</li>
    <li>Un ohmímetro de divisor con una sola resistencia de 22 kΩ y la referencia supuesta en el firmware.</li>
    <li>Una sola constante de escala para todas las ganancias de un ADC sin buffer.</li>
    <li>Una fuente de 20 mA con purga permanente, que obliga a un modo de ahorro.</li>
    <li>La fuente de ohmios sin protección.</li>
    <li>El aislamiento completo con módulos: va contra RD-05 y añade coste.</li>
  </ul>
"""))

S.append(sec("modulos", "12", "Módulos y su equivalente discreto", """
  <div class="tw"><table>
    <thead><tr><th>Módulo</th><th>Función</th><th>En la rev 2.1</th></tr></thead>
    <tbody>
      <tr><td>Arduino Uno R4, XIAO RA4M1, Feather, Giga</td><td>MCU, USB, pantalla</td><td>STM32G473 + ESP32-S3</td></tr>
      <tr><td>ACS712 / placa AMC0330R</td><td>Corriente (Hall o amplificador aislado)</td><td>Derivador de 0.1 Ω + OPA2188 (H §5)</td></tr>
      <tr><td>RFM-0505S + ISO1540 + LTV-824</td><td>Lado de medida flotante</td><td>No hace falta: masa común (RD-05)</td></tr>
      <tr><td>Placas ADS aisladas (ADS1256, ADS1115)</td><td>ADC externos para experimentar</td><td>ADC5 del G473</td></tr>
    </tbody>
  </table></div>
  <p class="meta">El ADS1115 de la placa principal es un circuito integrado, no un módulo: se estudia como el resto de piezas.</p>
"""))

S.append(sec("comparacion", "13", "Comparación con las referencias anteriores y la sección H", """
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>Micro-DMM</th><th>TIDA-01012 / 00879</th><th>HydraMeter</th><th>121GW</th><th>Sección H</th></tr></thead>
    <tbody>
      <tr><td>ADC</td><td>ΣΔ 16 bits externo (ADS1115)</td><td>SAR 18 bits / ΣΔ 24 bits del MCU</td><td>ΣΔ 16 bits + PGA</td><td>Chip de multímetro</td><td>ADC5 de 12 bits sobremuestreado</td></tr>
      <tr><td>Entrada de tensión</td><td>2 × 0.5 MΩ diferencial, puente</td><td>10 MΩ + patas</td><td>1 MΩ + patas</td><td>10 MΩ + patas</td><td>Tomas fijas (P17 en estudio)</td></tr>
      <tr><td>Ohmios</td><td>Corriente de 20 mA / divisor de 22 kΩ, sin razón</td><td>No miden</td><td>Kelvin, corriente medida</td><td>Del chip, con PTC</td><td>Razón con R_ref por rango</td></tr>
      <tr><td>Cable abierto</td><td>Sí (puente de Mann)</td><td>No</td><td>No</td><td>No</td><td>RD-09, sin circuito todavía</td></tr>
      <tr><td>Protección</td><td>0.5 MΩ + Schottky; ohmios sin proteger</td><td>Ninguna en tensión; PTC de 0.2 A en corriente</td><td>Escalonada</td><td>Certificada CAT III</td><td>R_PROT + sujeción; PTC por elegir</td></tr>
      <tr><td>Masa</td><td>Flotante y aislada</td><td>COM a media alimentación</td><td>COM a 1.65 V, aislado</td><td>Flotante (pilas)</td><td>Masa común</td></tr>
    </tbody>
  </table></div>
"""))

a_rows = "".join(f"<tr><td>{ohm(rx)}</td><td>{K.toma_A(rx):.2f} V</td><td>{K.borne_B(rx):.2f} V</td></tr>" for rx in K.RX)
S.append(sec("propuestas", "14", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P32. <b>Ninguna está aplicada.</b></p>
  <h3>P33 · Cable abierto en tensión con resistencias definidas (RD-09) {tg(OK,'Adoptar')}</h3>
  <p>Funcionamiento:</p>
  <ul class="tight">
    <li><b>Cuándo</b>: si la lectura lleva al menos 5 ms (un cuarto de periodo a 50 Hz) por debajo de un umbral, el DMM hace una prueba de unos 10 ms con un sesgo de alta impedancia conocido y vuelve a medir.</li>
    <li><b>Qué muestra</b>: «cerrado», una resistencia estimada o «abierto», en pantalla y en S3G4-UI.</li>
  </ul>
  <p>Dos formas de hacerlo en nuestra arquitectura:</p>
  <ul class="tight">
    <li><b>B, sin piezas nuevas</b>: una lectura en el rango de 20 MΩ de ohmios (4.9 V por la R_ref de 10 MΩ, con el divisor de 10.1 MΩ en paralelo en el borne). Como mucho {K.I_MAX_B*1e9:.0f} nA. La fuente ya va protegida por la PTC (P30).</li>
    <li><b>A, como el puente de Mann</b>: un brazo de 10 MΩ de la toma de P17 a VREF, con un conmutador. La prueba se hace desde detrás de R_PROT y de los 10 MΩ, sin conectar la fuente de ohmios al borne. Como mucho {K.I_MAX_A*1e9:.0f} nA.</li>
  </ul>
  <div class="tw"><table>
    <thead><tr><th>Entre las puntas</th><th>A: tensión en la toma</th><th>B: tensión en el borne</th></tr></thead>
    <tbody>{a_rows}</tbody>
  </table></div>
  <p>B distingue mejor las resistencias bajas; A deja la fuente de ohmios fuera del modo de tensión. Tiempos: la constante de la toma es de ≈ {K.TAU_NODO*1e6:.0f} µs. Con 100 pF de cable entre puntas abiertas llega a {K.TAU_CABLE*1e3:.0f} ms, así que basta una ventana de ≈ 10 ms. Los umbrales salen de esta tabla y no del banco. Queda para la síntesis: elegir A o B, el umbral y si avisa con sonido.</p>
  <h3>P34 · En ohmios, detectar tensión externa y desconectar la fuente {tg(OK,'Adoptar')}</h3>
  <p>El Micro-DMM mide tensión y ohmios a la vez y enseña la tensión si supera ≈ 1 V. En nuestro DMM las dos funciones comparten el borne V/Ω. En ohmios, el firmware debería reconocer que hay tensión externa: una lectura negativa, una por encima de los 4.9 V de la fuente, o una que no cambia al cambiar de R_ref. Entonces:</p>
  <ul class="tight">
    <li>deshabilita la fuente y la R_ref;</li>
    <li>avisa «tensión en el circuito»;</li>
    <li>y pasa a medir tensión.</li>
  </ul>
  <p>Con la red aplicada (RD-10), la PTC y la sujeción solo tienen que aguantar unos milisegundos, no hasta que la PTC dispare. Hay que comprobar en S11 cuánto tarda la detección.</p>
  <p class="meta">Además:</p>
  <ul class="tight meta">
    <li>P26 y P29 quedan reforzadas: 15 tramos de calibración y configuración en memoria con versión y CRC.</li>
    <li>P21 suma la media exponencial y la velocidad del ADC adaptativa.</li>
    <li>La sección H §4 (buffer delante del ADC) y §6 (razón con R_ref por rango) quedan confirmadas por los errores de este diseño.</li>
  </ul>
"""))

S.append(sec("correcciones", "15", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>RD-09 (requisitos del DMM) dice «una pequeña corriente de prueba en la entrada, como en el Micro-DMM». Matiz: el Micro-DMM no inyecta una corriente definida. Rompe el puente y deja que una fuga baje el nodo. P33 sí la define.</li>
    <li>En el plan y en el diario de retomada la placa que mandaba era la DMM_KiCAD_V4_next, pero su puente, tal como está dibujado, no puede romperse. El puente válido está en SimplifiedOpenLeadVoltmeter, DMM Feather Redux y OpenLead_Headless_V3.</li>
    <li>El plan decía «ADS1115/ADS1256». La placa principal solo lleva el ADS1115; el ADS1256 aparece en placas aisladas aparte.</li>
    <li>La figura 1 del white paper usa un IRFZ44N y un ADR5041; las placas llevan AO3400A (SI2302 según el texto) y LM4040-2.5.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("especificacion", "2 · Especificación y medidas"),
    ("arquitectura", "3 · Arquitectura"), ("voltimetro", "4 · Voltímetro: puente de Mann"), ("cable-abierto", "5 · Cable abierto"),
    ("ohmios", "6 · Ohmios"), ("corriente", "7 · Corriente"), ("firmware", "8 · Firmware"), ("alimentacion", "9 · Alimentación"),
    ("seguridad", "10 · Seguridad"), ("no-copiar", "11 · Lo que no conviene copiar"), ("modulos", "12 · Módulos"),
    ("comparacion", "13 · Comparación"), ("propuestas", "14 · Propuestas P33–P34"), ("correcciones", "15 · Correcciones")])

HTML = (
 '<title>Anatomía del Micro-DMM</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 5 de 9</p>\n  <h1>Anatomía del Micro-DMM</h1>\n'
 '  <p class="lede">Un DMM casero con un ADS1115 cuyo voltímetro sabe si las puntas están al aire. Es la idea de nuestro RD-09: aquí se ve cómo funciona de verdad, de qué depende y cómo hacerla con resistencias conocidas.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes en <code>research_and_tests/Micro-DMM/</code>; proyecto: '
 '<a href="https://github.com/oihdesigns/Micro-DMM">github.com/oihdesigns/Micro-DMM</a>. Cifras: <code>herramientas/calc_dmm_microdmm.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
