# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_tida00879.html (anatomia del TIDA-00879).
Cifras: calc_dmm_tida00879.py. Dibujos: draw_dmm_tida00879.py. Plantilla: build_dmm_tida01012.py."""
import io, draw_dmm_tida00879 as D, calc_dmm_tida00879 as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_tida00879.html"
r = K.rangos

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El TIDA-00879 (junio de 2016) es el <b>antecesor directo del TIDA-01012</b>: el mismo autor de TI, el mismo front-end con patas conmutadas y derivadores con fuerza y sentido. La gran diferencia es que no tiene ADC externo: usa los <b>tres ADC ΣΔ de 24 bits del MSP430F6736</b> y su driver de LCD de segmentos. Comparar los dos diseños enseña qué cambió TI y por qué.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el TIDA-00879</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>ADC integrado en el micro</td><td>ΣΔ de 24 bits con PGA ×16, a 31 kSa/s; 60 000 cuentas y ±(0.03 % + 5) en continua (§5, §7)</td><td>Un ΣΔ integrado da precisión DC con pocas piezas, pero poco ancho de banda en alterna (1 kHz). Nuestro G473 no tiene ΣΔ: la comparación con nuestro ADC5 es menos directa de lo que dije en el plan</td><td>{tg(WARN,'Contexto')}</td></tr>
      <tr><td>Resistencia de entrada de alta tensión</td><td>R19 es una Vishay CRHV1206 (serie de alta tensión, 0.3 W) (§3)</td><td>Una pieza concreta para los 10 MΩ de arriba (P28)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Dos trimmers de compensación</td><td>4.5–20 pF en las patas de 1 MΩ y de 100 MΩ (§3)</td><td>El TIDA-01012 los quitó y usó condensadores fijos, con mejor resultado en alterna. Refuerza P18</td><td>{tg(OK,'Confirma P18')}</td></tr>
      <tr><td>Interruptor de carga para el AFE</td><td>El TPS62740 tiene un conmutador integrado que apaga el AFE (§8)</td><td>Igual que P22: el DMM con su riel apagable</td><td>{tg(OK,'Confirma P22')}</td></tr>
      <tr><td>Potencia real con muestreo simultáneo</td><td>Dos ADC ΣΔ a la vez, tensión y corriente; producto muestra a muestra (§6)</td><td>No está en nuestros requisitos; con un solo ADC5 no se puede. Se anota como idea</td><td>{tg(OPEN,'Idea')}</td></tr>
      <tr><td>Calibración compilada en el código</td><td>Ganancia y offset por rango en un <code>#define</code>; para recalibrar hay que recompilar (§6)</td><td>Guardar las constantes en memoria no volátil y editarlas desde S3G4-UI (P29)</td><td>{tg(CRIT,'Evitar')}</td></tr>
      <tr><td>Bornes de colores confusos</td><td>El rojo es la referencia común de tensión y corriente; la tensión entra por el negro y la corriente por el azul (§3, §4)</td><td>Nuestros bornes V/Ω, COM y A con el COM a masa son lo habitual</td><td>{tg(CRIT,'Evitar')}</td></tr>
      <tr><td>Sin protección de tensión</td><td>Igual que el 01012: solo una PTC de 0.2 A en corriente (§9)</td><td>RD-10 pide más</td><td>{tg(CRIT,'Evitar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><b>Guía de diseño</b> <code>research_and_tests/TIDA-00879/tidubm4.pdf</code> (TIDUBM4A, rev. de enero de 2017, 38 p): especificación, teoría (§4), calibración (§5.2.3) y resultados (§8, gráficas renderizadas).</li>
    <li><b>Esquemático</b> <code>tidrmi4.pdf</code> (5 hojas: bloques, MCU, AFE, prueba y varios), leído por zonas a 200 ppp; <b>BOM</b> <code>tidrmi5.pdf</code> para números de pieza, tolerancias y encapsulados.</li>
    <li>Bajados de ti.com el 7 oct 2026 con permiso de Keneth. El firmware (zip para IAR) no se bajó: lo que sale de él viene de la guía.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_tida00879.py</code>; redibujos en <code>draw_dmm_tida00879.py</code> (0 solapes, revisados a la vista).</li>
  </ul>
"""))

S.append(sec("arquitectura", "2", "Arquitectura", """
  <pre class="mermaid">flowchart LR
  J8["Borne negro J8 · tensión"] --> DIV["10 MΩ (o 499 kΩ por J7)<br/>+ patas a la referencia (TS5A3359)"]
  DIV --> U4["OPA333 · V−"]
  J9["Borne azul J9 · corriente"] --> SH["95.3 Ω / 0.5 Ω + PTC 0.2 A<br/>(TS3A24159)"]
  SH --> U10["OPA333 · I−"]
  J6["Borne rojo J6 · referencia"] --- U3["OPA333 · AVCC/2 = 1.2 V"]
  U4 --> SD0["SD24 canal 0 (V+ − V−)"]
  U10 --> SD1["SD24 canal 1 (I+ − I−)"]
  SD0 --> MCU["MSP430F6736<br/>multiplicador de 32 bits"]
  SD1 --> MCU
  MCU --> LCD["LCD de segmentos"]
  MCU --> UART["UART aislado (prueba y calibración)"]</pre>
  <p>Cada señal tiene su propio ADC ΣΔ con PGA, y los dos muestrean a la vez: por eso puede medir potencia real. El borne rojo es la referencia común: lo fija un OPA333 a la mitad de la alimentación analógica (2.4 V). El instrumento flota con sus pilas, como el TIDA-01012.</p>
"""))

rows = "".join(
    f"<tr><td>{n}</td><td class='n'>÷{x['div']:.1f}</td><td class='n'>{x['v_toma']*1e3:.1f} mV</td><td class='n'>{x['Zin']/1e6:.1f} MΩ</td>"
    f"<td class='n'>{x['tau'][0]*1e3:.2f}{'' if abs(x['tau'][0]-x['tau'][1])<1e-6 else '–'+format(x['tau'][1]*1e3,'.2f')} ms</td></tr>"
    for n, x in r.items())
S.append(sec("tension", "3", "Entrada de tensión", f"""
{fig(D.tension(), "Redibujo de la hoja 3 (AFE Block). C33 y C34 son trimmers Murata TZB4 de 4.5–20 pF.")}
  <p>Es el mismo esquema que el TIDA-01012: 10 MΩ fijos arriba, un SP3T de baja tensión que elige la pata hacia la referencia y 100 MΩ siempre. Cada pata da <b>54.5 mV a fondo</b> en la toma, en todos los rangos.</p>
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>División</th><th>Toma a fondo</th><th>Z de entrada</th><th>τ de la pata</th></tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>R19 es una resistencia de alta tensión</b> (Vishay CRHV1206, 10.0 MΩ al 1 %, 0.3 W). Es la única pieza que ve la tensión de entrada; el resto son 0402 al 1 %. La tensión máxima de la serie CRHV en 1206 está <b>NO VERIFICADA</b>.</li>
    <li><b>Dos trimmers</b> (4.5–20 pF) ajustan las patas de alta impedancia: C33 en la de 1 MΩ (junto a 980 pF fijos) y C34 en la de 100 MΩ, donde el valor ideal es {K.C34_IDEAL*1e12:.0f} pF. En el TIDA-01012, TI quitó los dos (C18 y C19 sin montar) y fijó 950 pF en la pata de 1 MΩ.</li>
    <li><b>60 mV con 499 kΩ por un puente</b> (J7): baja el ruido térmico, igual que el deslizante S2 del 01012, pero aquí el firmware no sabe en qué posición está.</li>
    <li>La división del rango de 60 mV con R19 es ÷1.1 (entrada de 110 MΩ); con R20, ÷1.005 (100.5 MΩ).</li>
  </ul>
"""))

c6, c60 = K.corr["600 µA"], K.corr["60 mA"]
S.append(sec("corriente", "4", "Corriente", f"""
{fig(D.corriente(), "Redibujo de la parte de corriente. I+ se toma encima de R23; I− lo elige la sección 1 del TS3A24159 y lo sigue U10.")}
  <ul class="tight">
    <li>600 µA: R22 + R23 = {c6['R']:.1f} Ω → {c6['V']*1e3:.1f} mV a fondo. 60 mA: R23 = 0.5 Ω → {c60['V']*1e3:.0f} mV. R22 es una 2512 de 1 W.</li>
    <li>La misma técnica de fuerza y sentido que el 01012 (P19). <b>La PTC queda fuera de la medida</b>: I+ se toma entre la PTC y R23.</li>
    <li>La corriente entra por el borne azul y sale por el rojo, que es la referencia común. Para medir potencia, la guía obliga a un montaje «del lado alto»: en el otro sentido, los derivadores harían de cortocircuito entre los dos lados de la fuente.</li>
  </ul>
"""))

S.append(sec("adc", "5", "El ADC ΣΔ del MSP430F6736", f"""
  <ul class="tight">
    <li>Tres ADC <b>SD24_B</b> de 24 bits con PGA. Modulador a {K.F_MOD/1e6:.0f} MHz y sobremuestreo ×{K.OSR}: {K.FS_ADC/1e3:.2f} kSa/s y 19 bits útiles (18 + signo), según la guía.</li>
    <li><b>PGA ×{K.PGA}</b> en tensión y en corriente: la toma de ±54.5 mV llega a ±{K.V_ADC_FS:.2f} V. ×32 saturaría. La guía pide la misma ganancia en los dos canales para que el desfase sea igual en el modo de potencia.</li>
    <li>El filtro SINC3 del ΣΔ limita la alterna: TI promete ±1 % <b>hasta 1 kHz</b> (el TIDA-01012, con un SAR externo, llega a 100 kHz).</li>
    <li>El fondo de escala exacto del SD24 depende de su referencia; con el esquema no se puede confirmar si es la interna. <b>NO VERIFICADO.</b></li>
  </ul>
"""))

S.append(sec("firmware", "6", "Firmware y calibración", f"""
  <ul class="tight">
    <li>El multiplicador hardware de 32 bits eleva al cuadrado (o multiplica V × I) cada muestra en los 30.5 µs entre muestras. Se acumulan {K.N_ACC} muestras por lectura: {K.LECTURAS_S:.1f} lecturas por segundo (la guía dice 8).</li>
    <li>Los offsets se restan antes de multiplicar en alterna y en potencia; en continua, al final, para ahorrar energía. Después, raíz cuadrada (en alterna) y ganancia de calibración en coma flotante, y un filtro exponencial.</li>
    <li><b>Calibración de tres puntos</b> por modo y rango (−fondo, 0, +fondo) con una Keithley 2400 y regresión lineal. En el modo de potencia las constantes son distintas, porque los dos canales están activos.</li>
    <li><b>Las constantes viven en <code>dmm_00879_defines.h</code></b>: recalibrar obliga a recompilar y reprogramar. El modo de calibración solo envía los códigos crudos por el UART aislado.</li>
  </ul>
"""))

S.append(sec("resultados", "7", "Lo que midió TI", """
  <div class="tw"><table>
    <thead><tr><th>Ensayo</th><th>Resultado (leído de las gráficas)</th><th>Límite</th></tr></thead>
    <tbody>
      <tr><td>Linealidad, 60 V</td><td class="n">−10 … +4 mV</td><td>±(0.03 % + 5): 5 mV en cero, 23 mV a fondo</td></tr>
      <tr><td>Linealidad, 6 V</td><td class="n">−0.3 … +0.9 mV</td><td>0.5 … 2.3 mV</td></tr>
      <tr><td>Linealidad, 600 mV</td><td class="n">−30 … +110 µV</td><td>50 … 230 µV</td></tr>
      <tr><td>Linealidad, 60 mV</td><td class="n">−8 … +12 µV</td><td>5 … 23 µV</td></tr>
      <tr><td>Alterna, 6 V, seno</td><td class="n">±1 % hasta ≈ 2 kHz; +6 % a 4 kHz</td><td>±1 % hasta 1 kHz</td></tr>
      <tr><td>Alterna, ondas cuadradas</td><td class="n">+14 … +18 % a 4 kHz</td><td>sus armónicos superan el ancho de banda</td></tr>
      <tr><td>Consumo</td><td class="n">1.6–2.6 mA a 3.6 V; 13 µA apagado</td><td>≈ 676 h con 3 × AAA</td></tr>
    </tbody>
  </table></div>
  <p class="meta">Límites calculados con la tabla 1, ±(0.03 % + 5 cuentas). Las líneas verdes de las gráficas de TI dibujan límites más anchos (35 mV a fondo en 60 V, es decir ±(0.05 % + 5)): parecen copiadas del criterio del 01012.</p>
  <p>En continua, el 00879 es algo mejor que el 01012 (ΣΔ de 24 bits frente a SAR de 18). En alterna es mucho peor: el error crece con la frecuencia porque el filtro del ΣΔ y los 31 kSa/s no dan más.</p>
"""))

S.append(sec("alimentacion", "8", "Alimentación", """
  <ul class="tight">
    <li>Tres pilas AAA (2.4–4.8 V) con un P-MOS (FDN302P) de protección y encendido, y un divisor para medir la batería (la función existe en hardware pero no en el firmware).</li>
    <li>Un TPS62740 da 2.4 V a todo; es el mínimo del SD24. Sus pines VSEL van al MCU, que puede subir la tensión si necesita más velocidad.</li>
    <li>El <b>conmutador de carga integrado</b> del TPS62740 alimenta el AFE (AVCC, con 10 Ω y 22 µF): el MCU lo apaga en reposo.</li>
    <li>El puerto de prueba (UART por optoacopladores PS8802 y una SRAM de 8 KB) tiene su propio LDO de 3 V, encendido solo en modo prueba.</li>
  </ul>
"""))

S.append(sec("seguridad", "9", "Seguridad", """
  <p>Igual que el 01012: <b>sin protección en la entrada de tensión</b> (la guía lo dice en §4.1) y una PTC de 0.2 A en corriente. Tiene un pictograma de tensión peligrosa en la placa, pero ninguna medida que lo respalde. Como en la R19 de alta tensión cae casi toda la entrada, el resto del divisor ve solo milivoltios mientras el rango sea el correcto.</p>
"""))

S.append(sec("evolucion", "10", "Del TIDA-00879 al TIDA-01012: qué cambió TI", """
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>TIDA-00879 (jun. 2016)</th><th>TIDA-01012 (oct. 2016)</th><th>Lectura</th></tr></thead>
    <tbody>
      <tr><td>ADC</td><td>ΣΔ 24 bits integrado, 31 kSa/s, PGA ×16</td><td>SAR 18 bits externo, 210 kSa/s, ×44.2 diferencial</td><td>Para tener alterna hasta 100 kHz hizo falta un SAR rápido</td></tr>
      <tr><td>Exactitud DC</td><td>±(0.03 % + 5), 60 000 cuentas</td><td>±(0.05 % + 5), 50 000 cuentas</td><td>El ΣΔ gana en continua</td></tr>
      <tr><td>Alterna</td><td>±1 % hasta 1 kHz</td><td>3 % hasta 100 kHz (±1.5 % hasta 10 kHz medido)</td><td>El SAR gana en alterna</td></tr>
      <tr><td>Compensación</td><td>Dos trimmers</td><td>Condensadores fijos</td><td>Los trimmers no hacían falta</td></tr>
      <tr><td>Rango más bajo</td><td>Puente J7</td><td>Deslizante S2 con lectura de posición</td><td>El firmware necesita saber la posición</td></tr>
      <tr><td>Buffers</td><td>OPA333 (deriva cero, 17 µA, 350 kHz)</td><td>OPA2313 (RRIO, 1 MHz)</td><td>Más ancho de banda para la alterna</td></tr>
      <tr><td>Bornes</td><td>Tres (rojo = referencia)</td><td>Dos y un selector V/A</td><td>Ninguno es lo habitual</td></tr>
      <tr><td>Interfaz</td><td>LCD de segmentos</td><td>BLE hacia el PC</td><td>—</td></tr>
      <tr><td>Energía</td><td>3 × AAA, 6–9 mW</td><td>Li-ion, 19 mW</td><td>—</td></tr>
    </tbody>
  </table></div>
  <p>Para nosotros, el G473 no tiene ΣΔ: estamos más cerca del 01012 (un SAR) que del 00879, pero con 12 bits y sobremuestreo en lugar de 18 bits. La alterna hasta 20 kHz (RD-07) no es problema; la precisión en continua sí lo es, y por eso la síntesis tiene que mirar con cuidado las 20 000 cuentas.</p>
"""))

S.append(sec("no-copiar", "11", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>Las constantes de calibración compiladas en el código.</li>
    <li>El borne rojo como referencia común y los tres colores fuera de lo habitual.</li>
    <li>Puentes y trimmers que obligan a abrir el equipo.</li>
    <li>La entrada sin protección (igual que el 01012).</li>
  </ul>
"""))

S.append(sec("modulos", "12", "Módulos", """
  <p><b>Ninguno.</b> El LCD de segmentos se conecta directo al MSP430; el UART de prueba usa optoacopladores sueltos.</p>
"""))

S.append(sec("propuestas", "13", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P27. <b>Ninguna está aplicada.</b></p>
  <h3>P28 · Resistencia de entrada de alta tensión específica {tg(OK,'Adoptar')}</h3>
  <p>Los 10 MΩ de arriba (P17) en una pieza de la familia de alta tensión (tipo CRHV1206), o en varias 1206 de alta tensión en serie si así se reparte mejor la tensión con la red (P23). Hay que buscar el equivalente en LCSC y su tensión máxima de trabajo.</p>
  <h3>P29 · Constantes de calibración en memoria no volátil {tg(OK,'Adoptar')}</h3>
  <p>Ganancia, offset y tablas de varios puntos (P21, P26) por rango, guardadas en la flash del G473 (o en una EEPROM) con un número de versión, y editables con un procedimiento guiado desde S3G4-UI. Así se recalibra sin recompilar.</p>
  <p class="meta">Confirma además P18 (condensadores fijos, sin trimmer), P19 (fuerza y sentido) y P22 (riel del DMM apagable). La potencia real con muestreo simultáneo queda como idea fuera de los requisitos.</p>
"""))

S.append(sec("correcciones", "14", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>En el plan presenté el TIDA-00879 como «nuestro caso: ADC del micro con front-end propio». Es cierto que usa el ADC del micro, pero es un <b>ΣΔ de 24 bits</b>, no un SAR de 12 bits como el del G473. Su precisión en continua no se puede trasladar a nuestro ADC5.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("arquitectura", "2 · Arquitectura"),
    ("tension", "3 · Tensión"), ("corriente", "4 · Corriente"), ("adc", "5 · ADC ΣΔ"), ("firmware", "6 · Firmware"),
    ("resultados", "7 · Lo que midió TI"), ("alimentacion", "8 · Alimentación"), ("seguridad", "9 · Seguridad"),
    ("evolucion", "10 · Del 00879 al 01012"), ("no-copiar", "11 · Lo que no conviene copiar"), ("modulos", "12 · Módulos"),
    ("propuestas", "13 · Propuestas P28–P29"), ("correcciones", "14 · Correcciones")])

HTML = (
 '<title>Anatomía del TIDA-00879</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 3 de 9</p>\n  <h1>Anatomía del TIDA-00879</h1>\n'
 '  <p class="lede">El primer DMM de referencia de TI de esta familia: el mismo front-end que el TIDA-01012, pero con los ADC ΣΔ de 24 bits del propio microcontrolador. Muy preciso en continua, limitado en alterna, y una buena lección de por qué TI cambió de ADC.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes en <code>research_and_tests/TIDA-00879/</code>, de '
 '<a href="https://www.ti.com/tool/TIDA-00879">ti.com/tool/TIDA-00879</a>. Cifras: <code>herramientas/calc_dmm_tida00879.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
