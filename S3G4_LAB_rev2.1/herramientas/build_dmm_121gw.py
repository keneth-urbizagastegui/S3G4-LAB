# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_121gw.html (anatomia del EEVblog 121GW).
Cifras: calc_dmm_121gw.py. Dibujos: draw_dmm_121gw.py. Plantilla: build_dmm_tida01012.py."""
import io, draw_dmm_121gw as D, calc_dmm_121gw as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_121gw.html"

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El 121GW es un multímetro comercial de 4⅘ dígitos (55 000 cuentas) diseñado por EEVblog con UEI, certificado <b>CAT III 600 V</b> (cETLus, IEC 61010-1 3.ª ed.), con el esquema publicado. La medida la hace un chip de multímetro (Hycon <b>HY3131</b>) y el STM32L152 se ocupa del resto. No vamos a usar un chip así, pero es <b>la única referencia con una protección certificada</b>: de ella sale cómo proteger de verdad los tres bornes.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el 121GW</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Patas bajas conmutadas, también aquí</td><td>10 MΩ (±0.5 %) arriba y patas de 1.11 MΩ, 101 kΩ, 10 kΩ y 1 kΩ que el HY3131 pone a masa (§3)</td><td>Un DMM comercial usa la misma idea que los TIDA: refuerza P17</td><td>{tg(OK,'Confirma P17')}</td></tr>
      <tr><td>Cadena de protección en V/Ω</td><td>PTC de 1.2 kΩ + 1 kΩ, varistores S05K575 en serie hacia masa y hacia el camino de ohmios, ferrita y 10 MΩ; 6 kV en pulso (§4)</td><td>La versión certificada de P23. Para RD-10 basta una parte</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>PTC en la fuente de ohmios y diodo</td><td>2.2 kΩ en total, incluida la PTC: limita la corriente de prueba y absorbe la red si se aplica (§5)</td><td>Cierra el pendiente «PTC de la fuente de ohmios» de la sección H (P30)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Fusibles HRC con poder de corte</td><td>400 mA / 600 V con 10 kA y 11 A / 1000 V con 20 kA; puente de diodos DF10S como sujeción (§6)</td><td>Nuestro fusible de 3.15 A debe ser cerámico, con poder de corte declarado (P31); el puente sirve en lugar de dos diodos sueltos (P27)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Amplificador ×10 de deriva cero en corriente</td><td>MAX4238 con ganancia 10 elegible por un 74HC4053 («Low Burden») (§6)</td><td>Es nuestro amplificador B (OPA2188 ×10): confirma la elección</td><td>{tg(OK,'Confirma H')}</td></tr>
      <tr><td>Compensación con R de amortiguación</td><td>τ ≈ {K.TAU_TOP*1e6:.0f} µs; el condensador de arriba (6 pF) va en serie con 30 kΩ (§3)</td><td>Limita la corriente por el condensador en un transitorio: añadir a P18</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Aviso de fusible abierto</td><td>Dos comparadores TLC272 miden el borne antes del fusible a través de 9.4 MΩ (señales FUSE_mA y FUSE_A) (§7)</td><td>Barato y útil: el firmware sabría que el fusible saltó (P32)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>LowZ y diodo de 15 V</td><td>2.2 kΩ con PTC a masa para drenar tensiones fantasma; prueba de diodo de 15 V con un elevador (§5)</td><td>Fuera de nuestros requisitos (RD-08 pide ≈ 3.5 V)</td><td>{tg(OPEN,'Idea')}</td></tr>
      <tr><td>Chip de multímetro, verdadero RMS analógico y selector rotatorio</td><td>HY3131, AD8436 y un selector mecánico de funciones (§8)</td><td>Nuestra arquitectura es otra: ADC5, RMS por firmware y selección electrónica</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><b>Esquema</b> <code>research_and_tests/EEVblog_121GW/121GW_schematic.pdf</code>: una hoja vectorial de enero de 2018. eevblog.com daba error 502; la copia sale de web.archive.org. Leído por zonas a 330–420 ppp.</li>
    <li><b>Manual</b> <code>EEVblog-121GW-Manual.pdf</code> (rev. de 3 mar 2025, 73 p): especificaciones (pp. 15–23), descripción de bornes y modos.</li>
    <li>El esquema es de 2018 y el manual de 2025: donde no coinciden (el fusible de mA), se dice.</li>
    <li>El selector rotatorio reparte señales entre 37 contactos; su tabla de conexiones no está publicada. Los caminos que dependen de él se describen por su función, no contacto a contacto.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_121gw.py</code>; redibujos en <code>draw_dmm_121gw.py</code> (0 solapes, revisados a la vista).</li>
  </ul>
"""))

S.append(sec("especificacion", "2", "Lo que especifica el fabricante", """
  <div class="tw"><table>
    <thead><tr><th>Función</th><th>Rangos</th><th>Exactitud (± % lectura + cuentas)</th><th>Notas</th></tr></thead>
    <tbody>
      <tr><td>Tensión DC</td><td>50 mV · 500 mV · 5 V · 50 V · 500 V · 600 V</td><td>0.05 % + 5 (5–500 V); 0.1 % + 10 (50 mV, 500 mV, 600 V)</td><td>Protección 600 V con PTC y MOV</td></tr>
      <tr><td>Tensión AC (TRMS)</td><td>50 mV … 600 V</td><td>0.3 % + 10 (5–500 V) en 45–400 Hz; 1.5 % + 10 hasta 5 kHz</td><td>AD8436; factor de cresta &lt; 10</td></tr>
      <tr><td>Corriente DC</td><td>50 µA … 10 A (7 rangos)</td><td>0.25 % + 5 (mA); 0.75 % + 15 (A); 1.5 % + 15 (µA)</td><td>Caída 100 µV/µA, 2 mV/mA, 0.03 V/A</td></tr>
      <tr><td>Resistencia</td><td>50 Ω … 50 MΩ</td><td>0.2 % + 5 (5 kΩ–500 kΩ); 1.2 % + 20 (50 MΩ)</td><td>—</td></tr>
      <tr><td>Diodo</td><td>3 V · 15 V</td><td>sin especificar</td><td>1.4 mA y 7 mA por 2.2 kΩ (con la PTC)</td></tr>
      <tr><td>General</td><td>55 000 cuentas, 5 lecturas/s</td><td>coef. de temperatura 0.1 × exactitud / °C</td><td>CAT III 600 V; transitorios 6 kV, 2 Ω</td></tr>
    </tbody>
  </table></div>
  <p class="meta">Manual, pp. 15–20. Protección de los bornes de corriente: 400 mA / 600 V HRC (10 kA) y 11 A / 1000 V HRC (20 kA), cada uno con diodos.</p>
"""))

d = K.div
S.append(sec("divisor", "3", "Divisor: patas que pone a masa el HY3131", f"""
{fig(D.entrada(), "Redibujo de la entrada V/Ω y del divisor. Los varistores se dibujan con el símbolo de un diodo bidireccional.")}
  <p>R11 (10 MΩ, ±0.5 %) une la entrada con la toma, y cuatro patas van de la toma a pines del HY3131, que pone a masa la del rango elegido: {', '.join(f'{n} con {v["R"]/1e3:g} kΩ' for n, v in d.items())}. El chip ve siempre unos cientos de mV, igual que en los TIDA.</p>
  <ul class="tight">
    <li><b>Compensación</b>: el condensador de arriba (C13, 6 pF) da τ = {K.TAU_TOP*1e6:.0f} µs con R11. Las patas de ÷100, ÷1000 y ÷10000 cierran {d['÷100']['tau']*1e6:.0f}, {d['÷1000']['tau']*1e6:.0f} y {d['÷10000']['tau']*1e6:.0f} µs (+0.3, +5.8 y +10 %). La de ÷10 tiene sus condensadores sin montar: necesitaría ≈ {d['÷10']['C_ideal']*1e12:.0f} pF. O se monta en fabricación, o ese rango confía en la capacidad parásita. El emparejamiento R–C está deducido de la disposición del esquema: <b>NO VERIFICADO</b>.</li>
    <li><b>R9 (30 kΩ) en serie con C13</b>: en un transitorio rápido el condensador conduce mucho antes que R11; la resistencia limita esa corriente sin cambiar la compensación a las frecuencias de medida.</li>
    <li>Una ferrita (FB4) antes de R11 y un TVS SM6T22CA (600 W, 22 V) en otro nodo de la entrada completan el filtrado frente a interferencias y picos.</li>
  </ul>
"""))

S.append(sec("proteccion", "4", "Protección del borne V/Ω", f"""
  <p>Es el núcleo de esta referencia. La cadena, desde el borne:</p>
  <ol class="tight">
    <li><b>PTC3 (1.2 kΩ en frío) + R16 (1 kΩ)</b>: limitan la corriente. Con un pulso de 6 kV y 2 Ω (el ensayo del manual) pasan ≈ {K.I_PULSO:.1f} A durante microsegundos; con una tensión sostenida, la PTC se calienta y sube a muchos kΩ.</li>
    <li><b>Varistores S05K575</b> (575 Vrms, ≈ {K.V_MOV_1MA:.0f} V a 1 mA, disco de 5 mm): MOV1 + MOV3 en serie hacia masa (≈ {K.V_MOV_SERIE:.0f} V) y MOV1 + MOV2 hacia el camino de ohmios. Ponerlos en serie sube la tensión a la que conducen, de modo que 600 Vrms ({K.V_CAT:.0f} V de pico) no los toca, pero un pulso de kV sí.</li>
    <li><b>R11 de 10 MΩ</b>: con 600 Vrms solo pasan {K.I_TOP_600*1e6:.0f} µA.</li>
  </ol>
  <p>Para nosotros, RD-10 pide mucho menos: 230 Vrms durante 10 s, sin categoría de medida. Con 10 MΩ arriba (P17) la toma ya está a salvo; lo que hace falta es que el primer tramo aguante la tensión y los picos (P23, P28). Los varistores en serie y la PTC son el modelo si algún día se quiere certificar una categoría.</p>
"""))

S.append(sec("ohmios", "5", "Ohmios, diodo y LowZ", f"""
  <ul class="tight">
    <li><b>Un camino propio con PTC</b> (PTC4 1.2 kΩ + R17 1 kΩ = {K.R_DIODO/1e3:.1f} kΩ) lleva la fuente de ohmios y de diodo al borne V/Ω. El manual lo dice: esos 2.2 kΩ, PTC incluida, son los que fijan la corriente de prueba del diodo (1.4 mA a 3 V, 7 mA a 15 V; la fuente de 15 V la da un elevador RT9271).</li>
    <li>Ese mismo camino a masa es el <b>modo LowZ</b>: la entrada queda cargada con 2.2 kΩ para drenar tensiones fantasma. Si se aplica la red, la PTC disipa ≈ {K.P_LOWZ_230:.0f} W en el primer instante y sube enseguida: por eso es una PTC y no una resistencia.</li>
    <li>Otra rama con dos PTC de 1.5 kΩ va al selector (función no confirmada sin la tabla del selector).</li>
    <li>La medida de ohmios en sí la hace el HY3131 con su fuente y su referencia (ADR3412, 1.2 V).</li>
  </ul>
  <p>Para nuestra sección H: la fuente de ohmios necesita exactamente esto, una <b>PTC de alta tensión en serie</b> de unos 1–2 kΩ en frío, que no moleste a la medida por razón (queda fuera de la medida Kelvin, P24) y que se dispare con la red (P30).</p>
"""))

S.append(sec("corriente", "6", "Corriente: fusibles HRC, puente de diodos y «Low Burden»", f"""
{fig(D.corriente(), "Redibujo de los derivadores y del amplificador de baja caída. El selector rotatorio reparte el borne mA/µA entre la toma de µA y la de mA.")}
  <ul class="tight">
    <li><b>Derivadores en cadena</b>: R33 100 Ω, R43 1 Ω y 10 mΩ. µA mide {K.R_MEDIDA['µA (50 / 500 µA)']:.0f} Ω, mA {K.R_MEDIDA['mA (5 / 50 mA)']:.2f} Ω y A 10 mΩ.</li>
    <li><b>Fusibles HRC</b> (cerámicos de alto poder de corte): 400 mA / 600 V con 10 kA y 11 A / 1000 V con 20 kA según el manual. El esquema de 2018 dice 440 mA / 1000 V; el registro de cambios del manual corrigió el valor a 400 mA / 600 V en enero de 2018, aunque la sección de VA del mismo manual todavía nombra 440 mA / 1000 V.</li>
    <li><b>Puente DF10S con los terminales de continua unidos</b>: dos diodos en serie en cada sentido entre el borne y masa, de 1000 V y con mucha corriente de pico. Sujeta la caída a ≈ 1.4 V hasta que abre el fusible, en una sola pieza.</li>
    <li><b>«Low Burden»</b>: la señal del derivador pasa por un MAX4238 (deriva cero) con ganancia 1 + 90 k/10 k = {K.G_LOWBURDEN:.0f}, y un 74HC4053 elige ×1 o ×10. En 50 µA, los {K.V_50uA*1e3:.1f} mV del derivador llegan como {K.V_50uA*K.G_LOWBURDEN*1e3:.0f} mV: la misma resolución con diez veces menos caída.</li>
  </ul>
"""))

S.append(sec("auxiliares", "7", "Circuitos auxiliares", """
  <ul class="tight">
    <li><b>Aviso de fusible abierto.</b> Desde cada borne de corriente, antes del fusible, 9.4 MΩ llegan a un comparador TLC272 con resistencias de 10 MΩ a la alimentación. Con el fusible sano, el borne está a masa a través del derivador; con el fusible abierto, las resistencias lo suben y el comparador avisa (FUSE_mA, FUSE_A). La «input warning» que describe el manual puede ser esto o algo más: <b>NO VERIFICADO</b>.</li>
    <li><b>Verdadero RMS analógico</b> con un AD8436 y multiplexores HEF4052/4053; el manual especifica la alterna hasta 5 kHz.</li>
    <li><b>Alimentación</b>: 4 pilas AAA (6 V), LDO NJU7200 de 3.3 V y un regulador de 4.0 V para el AD8436; reloj de tiempo real, microSD y un módulo BLE marcado «no usado» en el esquema.</li>
  </ul>
"""))

S.append(sec("no-copiar", "8", "Lo que no conviene copiar (para nosotros)", """
  <ul class="tight">
    <li>El chip de multímetro (HY3131): fija la arquitectura, los rangos y el firmware; nosotros medimos con el ADC5.</li>
    <li>El verdadero RMS analógico: el firmware lo hace sin piezas (P21).</li>
    <li>El selector rotatorio mecánico de 37 contactos: caro, específico y difícil de cambiar.</li>
    <li>La prueba de diodo de 15 V y el modo LowZ: útiles, pero no los piden nuestros requisitos.</li>
  </ul>
"""))

S.append(sec("modulos", "9", "Módulos", """
  <p>Solo el módulo Bluetooth BLE112, marcado «no usado» en el esquema (en el producto sí va). Todo lo demás son piezas sueltas.</p>
"""))

S.append(sec("comparacion", "10", "Comparación con las referencias anteriores y la sección H", """
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>121GW</th><th>TIDA-01012 / 00879</th><th>HydraMeter</th><th>Sección H</th></tr></thead>
    <tbody>
      <tr><td>Divisor</td><td>10 MΩ + patas a masa (chip)</td><td>10 MΩ + patas (SP3T)</td><td>1 MΩ + patas</td><td>Tomas fijas</td></tr>
      <tr><td>Protección V/Ω</td><td>PTC + R + MOV en serie, certificada</td><td>Ninguna</td><td>THT + MOV + GDT + MOV</td><td>R_PROT + BAV199</td></tr>
      <tr><td>Fuente de ohmios</td><td>2.2 kΩ con PTC</td><td>—</td><td>D + fusible + 1 kΩ 1 W</td><td>PTC por elegir</td></tr>
      <tr><td>Corriente</td><td>HRC + puente, ×10 de deriva cero</td><td>PTC 0.2 A</td><td>Fusibles + 1N4007</td><td>Fusible 3.15 A, ×10/×100 con OPA2188</td></tr>
      <tr><td>Cuentas</td><td>55 000</td><td>50 000 / 60 000</td><td>16 bits</td><td>20 000 (objetivo)</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "11", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P29. <b>Ninguna está aplicada.</b></p>
  <h3>P30 · PTC de alta tensión en la fuente de ohmios y diodo {tg(OK,'Adoptar')}</h3>
  <p>Una PTC de 1–2 kΩ en frío, para tensión de red, en serie con el camino de la fuente (dentro del lazo Kelvin de P24, así que no afecta a la medida). Limita la corriente en cortocircuito y absorbe 230 Vrms durante los 10 s de RD-10. Hay que buscar la pieza en LCSC (tensión máxima, tiempo de disparo y resistencia en frío).</p>
  <h3>P31 · Fusible HRC cerámico con poder de corte declarado {tg(OK,'Adoptar')}</h3>
  <p>El 3.15 A rápido de RD-06 en versión cerámica de alto poder de corte, con tensión nominal de al menos 250 V, y un puente de diodos (tipo DF10S) con los terminales de continua unidos como sujeción sobre el derivador. Complementa P27.</p>
  <h3>P32 · Aviso de fusible abierto {tg(OK,'Adoptar')}</h3>
  <p>Medir el borne A antes del fusible a través de ≈ 10 MΩ con un comparador o con un canal libre del ADC, y una resistencia alta a la alimentación: si el fusible abre, el nodo sube y el firmware avisa en pantalla y en S3G4-UI.</p>
  <p class="meta">Además: P17 queda confirmada por un diseño comercial; P18 suma una resistencia de amortiguación en serie con el condensador de arriba; el amplificador B ×10 de deriva cero de la sección H coincide con el «Low Burden» del 121GW.</p>
"""))

S.append(sec("correcciones", "12", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>En el plan escribí que el 121GW lleva «fusible HRC, TVS, PTC, MOV y puente de diodos» en la entrada, citando una búsqueda. Por el esquema: PTC, resistencia, varistores y un TVS en la entrada V/Ω; el puente de diodos está en los bornes de <b>corriente</b>, junto a los fusibles HRC.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("especificacion", "2 · Especificación"),
    ("divisor", "3 · Divisor"), ("proteccion", "4 · Protección V/Ω"), ("ohmios", "5 · Ohmios, diodo y LowZ"),
    ("corriente", "6 · Corriente"), ("auxiliares", "7 · Auxiliares"), ("no-copiar", "8 · Lo que no conviene copiar"),
    ("modulos", "9 · Módulos"), ("comparacion", "10 · Comparación"), ("propuestas", "11 · Propuestas P30–P32"),
    ("correcciones", "12 · Correcciones")])

HTML = (
 '<title>Anatomía del 121GW</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 4 de 9</p>\n  <h1>Anatomía del 121GW</h1>\n'
 '  <p class="lede">Un multímetro comercial CAT III 600 V con el esquema publicado. La medida la hace un chip dedicado, pero su protección certificada (PTC, varistores, fusibles HRC y puente de diodos) es justo lo que nos faltaba estudiar.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes en <code>research_and_tests/EEVblog_121GW/</code>; producto: '
 '<a href="https://eevblog.com/product/121gw/">eevblog.com/product/121gw</a>. Cifras: <code>herramientas/calc_dmm_121gw.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
