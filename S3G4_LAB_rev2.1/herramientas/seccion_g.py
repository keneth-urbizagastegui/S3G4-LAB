# -*- coding: utf-8 -*-
"""Inserta la seccion G (alimentacion y rieles) en S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html y actualiza D-03, D-06 y
las secciones pendientes. Las cifras salen de calc_rieles.py. Parche de una vez, como fix_ruido.py."""
import io, calc_rieles as R
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

DOC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
s = io.open(DOC, encoding="utf-8").read()
assert 'id="seccion-g"' not in s, "la seccion G ya esta insertada"

def f2(x): return f"{x:.2f}"
m1 = R.MODES[0][2]
rows_m1 = "".join(
    f'<tr><td>{n}</td><td><code>{r}</code></td><td class="n">{m:.1f} mA</td><td class="n">{R.p_bat(r, m):.3f} W</td><td class="src">{src}</td></tr>'
    for n, r, m, src in m1)
rows_modes = "".join(
    f'<tr{" class=\"pick\"" if k == "M1" else ""}><td class="n">{k}</td><td>{d}</td><td class="n">{R.total(L):.2f} W</td><td class="n">{R.hours(R.total(L)):.1f} h</td></tr>'
    for k, d, L in R.MODES)
p1 = R.total(m1)
h1 = R.hours(p1)
h1_aged = h1 * 0.8

MER = """  <pre class="mermaid">%%{init: {'theme':'neutral'}}%%
flowchart LR
  USB["USB-C 5 V"] --> CHG["Cargador con power path"]
  BAT["Batería 1S · 5000 mAh"] <--> CHG
  CHG --> VSYS["VSYS 3.0–4.4 V"]
  VSYS --> BUCK["Buck 3.3 V"] --> ESP["ESP32-S3 y lógica de la pantalla"]
  VSYS --> BL["Retroiluminación: fuente de corriente con PWM"]
  VSYS --> BOOST["Boost 5.3 V · BUS5"]
  BOOST --> LM["LM27762 · ±5.0 V · EN+ y EN−"] --> AFE["AFE CH1–CH3 y DMM"]
  BOOST --> LDO["LDO 3.3 V"] --> MCU["STM32G473: VDD, y VDDA por ferrita"]
  BOOST --> REL["3 relés monoestables con economizador"]
  VSYS --> AWGC["Convertidor ±6.5 V · EN"] --> AWG["2 salidas del AWG"]
  MCU --- REF["REF3325 2.5 V → VREF+"]
</pre>
"""

G = f"""
<section id="seccion-g">
  <div class="shead"><span class="num">G</span><h2>Sección G — Alimentación y rieles</h2><span class="tag t-open">En curso</span></div>
  <div class="callout"><b>Decisiones de Keneth del 23 sep (noche):</b>
    <ul class="tight">
      <li>Batería 1S de 5000 mAh.</li>
      <li>El AWG tiene su propio convertidor de ±6.5 V y no comparte la bomba de carga del AFE.</li>
      <li>Relés <b>monoestables con economizador</b> (revisa D-03).</li>
      <li><b>El DMM sólo mide baja tensión</b> (60 V en continua o 30 Vrms, CAT I, como el ELVIS) y comparte la masa con el osciloscopio, el AWG y el USB (revisa D-06).</li>
    </ul></div>

  <h3>G.1 · El árbol</h3>
{MER}  <ul class="tight">
    <li><b>Cargador con power path:</b> el equipo funciona mientras carga por USB-C. Hay que elegir una variante que no deje subir VSYS por encima de ~4.4 V con el USB conectado; si no, el boost de 5.3 V no podría regular. Por verificar en la hoja al elegir la pieza.</li>
    <li><b>Buck de 3.3 V para el ESP32-S3:</b> es el mayor consumidor digital, así que va por el convertidor más eficiente.</li>
    <li><b>Boost de 5.3 V (BUS5):</b> el LM27762 no sube la tensión. Su LDO positivo cae 45 mV a 100 mA, y el negativo necesita que la bomba dé más de 5.03 V: con una batería de 3.0–4.2 V no llega a ±5 V sin este boost.</li>
    <li><b>LM27762:</b> ±5.0 V limpios (bomba de 2 MHz seguida de LDO) para el AFE y el DMM. Sus patas EN+ y EN− lo apagan del todo (0.5 µA).</li>
    <li><b>LDO de 3.3 V para el G473</b>, y VDDA desde él por una ferrita. Así VDDA no puede adelantarse a VDD al arrancar (DS12712 §3.11.1), como ya resolvió la rev 2.0. La REF3325 da VREF+ (P9, RD-03).</li>
    <li><b>Convertidor de ±6.5 V para el AWG:</b> separa sus corrientes de carga de los rieles del AFE y permite ±5 V con 50 mA (RG-03, RG-04). Se apaga con su EN cuando el AWG no se usa.</li>
  </ul>

  <h3>G.2 · Cómo se calcula</h3>
  <p>La potencia que sale de la batería es la suma de lo que pide cada riel, dividida por el rendimiento de su convertidor:</p>
  <div class="eq" style="font-family:'IBM Plex Mono',monospace;font-size:13.5px;background:var(--bg);border:1px solid var(--rule);border-radius:6px;padding:8px 12px;overflow-x:auto;white-space:pre">conmutado (buck, boost):   P_bat = V · I / η          η = {R.ETA_BUCK:.2f} (buck), {R.ETA_BOOST:.2f} (boost), {R.ETA_AWG:.2f} (±6.5 V)
LDO:                       I_entrada = I_salida      →  P = V_entrada · I
bomba negativa + LDO:      I_entrada ≈ {R.K_NEG} · I_salida   (estimación de la rev 2.0; se confirmará con la curva de la hoja)
autonomía:                 t = C · V_nom · {R.USABLE:.2f} / P_bat     ({R.CAP_MAH} mAh · {R.V_BAT} V · {R.USABLE:.2f} = {R.CAP_MAH/1000*R.V_BAT*R.USABLE:.2f} Wh útiles)</div>
  <p>Ejemplo, el ESP32-S3: 120 mA a 3.3 V por el buck → 3.3 × 0.120 / {R.ETA_BUCK:.2f} = {R.p_bat("3V3D", 120):.3f} W de batería.</p>

  <h3>G.3 · El peor caso de RF-17, carga por carga</h3>
  <p>Todo activo, WiFi, pantalla a pleno brillo, los dos canales del AWG con un seno a fondo sobre 50 Ω y los tres relés en ×1:</p>
  <div class="tw"><table>
    <thead><tr><th>Carga</th><th>Riel</th><th>Corriente</th><th>Potencia de batería</th><th>Fuente del dato</th></tr></thead>
    <tbody>{rows_m1}
      <tr><td><b>Total</b></td><td></td><td></td><td class="n"><b>{p1:.2f} W</b></td><td></td></tr></tbody>
  </table></div>
  <p class="src">Los amplificadores del AFE se cuentan a {R.IQ_AMP} mA cada uno (el OPA1656 de la rev 2.0) hasta que se elija la pieza. Son 3 por canal más el filtro de CH1 (RF-03), y la etapa final va a 3.3 V (P8).</p>

  <h3>G.4 · Autonomía con 5000 mAh</h3>
  <div class="tw"><table>
    <thead><tr><th>Modo</th><th>Qué está encendido</th><th>Potencia</th><th>Autonomía</th></tr></thead>
    <tbody>{rows_modes}</tbody>
  </table></div>
  <p><b>RF-17 (≥ 4 h con todo activo y WiFi) se cumple con margen:</b> {h1:.1f} h en el peor caso y {h1_aged:.1f} h con la celda envejecida al 80 %. Los mayores consumidores del peor caso son el AWG cargado, el AFE, la pantalla y el ESP32-S3; ahí actúa RF-18.</p>

  <h3>G.5 · Comprobación de los rieles</h3>
  <ul class="tight">
    <li><b>LM27762:</b> {R.PLUS5:.0f} mA en +5 V y {R.MINUS5:.0f} mA en −5 V, de los 250 mA que admite cada salida. Sin el AWG, la bomba se queda en {R.CPOUT:.2f} V, {abs(R.CPOUT)-5.03:.2f} V por encima de lo que necesita el LDO de −5.0 V. Con el AWG compartido habría caído a −4.95 V y el LDO habría dejado de regular: por eso va aparte.</li>
    <li><b>BUS5:</b> {R.BUS5_IN:.0f} mA en el peor caso; con la celda a 3.0 V el boost toma ~{R.BOOST_IN:.2f} A de la batería.</li>
    <li><b>Convertidor del AWG:</b> hasta {R.AWG_PEAK} mA de pico por riel, con dos canales a 50 mA.</li>
  </ul>

  <h3>G.6 · Apagado por bloques (RF-18)</h3>
  <div class="tw"><table>
    <thead><tr><th>Bloque</th><th>Cómo se apaga</th><th>Lo que ahorra en el peor caso</th></tr></thead>
    <tbody>
      <tr><td>Canal del osciloscopio</td><td>Amplificadores con pata de apagado, o interruptor de carga en su +5 V y su −5 V. Su relé vuelve solo a ÷20</td><td>≈ {(R.p_bat('+5', 3*R.IQ_AMP)+R.p_bat('-5', 3*R.IQ_AMP)+R.p_bat('VDDM', R.IQ_AMP)+R.p_bat('BUS5', R.I_REL*R.ECON)):.2f} W por canal</td></tr>
      <tr><td>AFE y DMM enteros</td><td>EN+ y EN− del LM27762</td><td>Todo el ±5 V</td></tr>
      <tr><td>AWG</td><td>EN de su convertidor; DAC3 y los OPAMP internos, por firmware</td><td>{(R.p_bat('AWG+', 42)+R.p_bat('AWG-', 42)):.2f} W con carga</td></tr>
      <tr><td>Pantalla</td><td>PWM de la retroiluminación con atenuación automática</td><td>Hasta {R.p_bat('VSYS', 120):.2f} W</td></tr>
      <tr><td>WiFi</td><td>Ahorro de energía del ESP32-S3 entre tramas</td><td>Por medir</td></tr>
      <tr><td>CPU del G473</td><td>P13: 104 MHz con el ADC síncrono</td><td>≈ {(R.total(R.MODES[0][2])-R.total(R.MODES[5][2])):.2f} W</td></tr>
    </tbody>
  </table></div>
  <p><b>Condición de seguridad:</b> con un canal apagado, su sujeción no puede descargar la corriente de falla en un riel sin alimentar. Tiene que ir a masa (TVS o Zener) o a un riel que siga vivo. Los monoestables ayudan: sin alimentación el grueso cae a ÷20 y la corriente que llega a la sujeción es de fracciones de mA. Se cierra junto con la corrección de P4, donde la entrada del buffer llegaba a 6.1 V.</p>

  <h3>G.7 · Masa común y seguridad</h3>
  <p>El equipo tiene <b>una sola masa</b>: el blindaje de las BNC, la masa del AWG, el COM del DMM y la masa del USB. Reglas que irán en el panel y en el manual:</p>
  <ul class="tight">
    <li>La pinza de masa del osciloscopio y el COM del DMM van siempre al mismo punto: la masa del circuito.</li>
    <li>El equipo no mide la red. El DMM llega a 60 V en continua o 30 Vrms. El osciloscopio declara 50 Vpk y sobrevive 10 s a la red en ÷20 (D-06), pero eso es protección frente a un error, no un rango de medida.</li>
    <li>Con el USB conectado a un PC, la masa del equipo es la tierra del PC.</li>
  </ul>

  <h3>G.8 · Qué falta</h3>
  <ul class="tight">
    <li>Elegir en LCSC (RF-19) el cargador, el boost, el buck, el convertidor del AWG, la fuente de corriente de la retroiluminación y los interruptores de carga.</li>
    <li>Confirmar la corriente de entrada del lado negativo del LM27762 con su curva de rendimiento, y el consumo real de los amplificadores elegidos.</li>
    <li>Medir la autonomía en los modos de la tabla (plan de medición de la propuesta de arquitectura, §21).</li>
  </ul>
</section>
"""

anchor = '<section>\n  <div class="shead"><span class="num">Σ</span><h2>BOM en construcción</h2>'
assert s.count(anchor) == 1
s = s.replace(anchor, G.strip() + "\n\n" + anchor, 1)

old_d03 = ('<td class="n">D-03</td><td><b>Sin relés en el acoplo. Un relé latching por canal, sólo para el atenuador grueso</b> (×1 / ÷20)</td>'
           '<td>Lo que pesaba en la rev 2.0 eran 8 bobinas alimentadas: hasta 0.8 W de 2.6 W. Un latching sólo recibe un pulso al cambiar de escala: 0 mW en régimen. <i>Revisada el 23 sep.</i></td>')
new_d03 = ('<td class="n">D-03</td><td><b>Sin relés en el acoplo. Un relé monoestable con economizador por canal, sólo para el atenuador grueso</b> (×1 / ÷20)</td>'
           '<td>Sin alimentación vuelve solo a ÷20, la posición segura. Con el economizador gasta 72 mW por relé en ×1; con los tres en ×1, +0.25 W (sección G). En la rev 2.0 pesaban 8 bobinas: hasta 0.8 W de 2.6 W. <i>Revisada el 23 sep: primero latching; por la noche, monoestable con economizador (decisión de Keneth).</i></td>')
assert s.count(old_d03) == 1; s = s.replace(old_d03, new_d03, 1)

old_d06a = 'La protección fuerte contra la red va en el <b>puerto del DMM (600 V)</b></td>'
new_d06a = '<b>El equipo no mide la red:</b> el DMM sólo mide baja tensión (60 V en continua o 30 Vrms, CAT I)</td>'
assert s.count(old_d06a) == 1; s = s.replace(old_d06a, new_d06a, 1)
old_d06b = 'Y el DMM es la función que el estudiante sí apuntará a la red. <i>Acordada con Keneth el 23 sep.</i></td>'
new_d06b = ('<i>Acordada con Keneth el 23 sep. Revisada esa noche: sin aislamiento, un COM en la fase deja con tensión el metal de las BNC y del USB-C, '
            'así que Keneth eligió un DMM sólo de baja tensión con masa común (sección G.7).</i></td>')
assert s.count(old_d06b) == 1; s = s.replace(old_d06b, new_d06b, 1)

old_g = ('<li><b>G — Alimentación y rieles.</b> Sin bobinas que alimentar, el presupuesto cambia por completo. Debe absorber hasta 13 mA inyectados por los clamps (C.7) y alimentar ~270 mW de amplificadores.</li>')
new_g = '<li><b>G — Alimentación y rieles.</b> En curso: ver la sección G.</li>'
assert s.count(old_g) == 1; s = s.replace(old_g, new_g, 1)
old_dmm = ('<li><b>DMM — protección de 600 V</b> en su puerto, según D-06: resistencia serie alta, PTC y varistor. Referencia: <code>research_and_tests/Micro-DMM</code> (500 kΩ + dos diodos, probado a 1000 V).</li>')
new_dmm = ('<li><b>DMM — protección frente a errores.</b> Ya no mide la red (D-06 revisada). Queda por decidir cuánto debe aguantar si alguien lo conecta por error. '
           'Referencia: <code>research_and_tests/Micro-DMM</code> (500 kΩ + dos diodos, probado a 1000 V).</li>')
assert s.count(old_dmm) == 1; s = s.replace(old_dmm, new_dmm, 1)

if ".src{" not in s:
    s = s.replace("</style>", ".src{color:var(--muted);font-size:12.5px}" + chr(10) + "</style>", 1)
io.open(DOC, "w", encoding="utf-8").write(s)
print("ok", round(p1, 2), round(h1, 1))
