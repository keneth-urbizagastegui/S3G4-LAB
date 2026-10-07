# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_34401a.html (anatomia del Agilent 34401A).
Cifras: calc_dmm_34401a.py. Dibujos: draw_dmm_34401a.py. Plantilla: build_dmm_tida01012.py."""
import io, draw_dmm_34401a as D, calc_dmm_34401a as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_34401a.html"

def pct(x, d=2):
    return f"{x*100:+.{d}f} %".replace("-", "−")
def corriente(i):
    return f"{i*1e3:.3g} mA" if i >= 0.9995e-3 else f"{i*1e6:.3g} µA"

a10, a100 = K.ASIENTO["÷10 (pata de 1.11 MΩ)"], K.ASIENTO["÷100 (pata de 101 kΩ)"]
S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El 34401A (Hewlett-Packard 1991, luego Agilent y Keysight) es el multímetro de banco de 6½ dígitos de referencia en cualquier laboratorio. El manual de servicio publica los esquemas y explica cada bloque. Su ADC multipendiente y su referencia de Zener enterrado están fuera de nuestro alcance, pero varias soluciones del front-end se pueden llevar, o imitar, a nuestro DMM de 4½ dígitos.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el 34401A</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Autocero con precarga</td><td>El conmutador de entrada alterna entre medir (MC), cero (MZ) y precarga (PRE). La precarga deja el nodo a la tensión de la entrada antes de reconectarla, para no inyectarle carga (§4)</td><td>Al volver de X3 (COM), el común del 4051 roba hasta un {a10['salto']*100:.0f} % de la tensión de la toma ÷10 y tarda {a10['t']*1e3:.1f} ms en volver a 1 cuenta (P38)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Compensación de alterna sin trimmer</td><td>Un DAC multiplicador mueve el pie de un condensador de 5.6 pF: capacidad programable en 256 pasos, calibrada a 50 kHz en cada rango (§7)</td><td>Como nuestro valor eficaz se calcula en firmware, el equivalente es un filtro de corrección de primer orden por rango (P39)</td><td>{tg(OK,'Adoptar la idea')}</td></tr>
      <tr><td>Frecuencia de red</td><td>Mide la red (55–66 Hz → 60 Hz; si no, 50 Hz) e integra un número entero de ciclos (§8)</td><td>En Perú la red es de 60 Hz. Integrar 20 ms deja solo {K.RECH['60 Hz con 20 ms (ajuste de 50 Hz)']:.0f} dB de rechazo; 100 ms rechazan 50 y 60 Hz a la vez (P40)</td><td>{tg(WARN,'Adoptar')}</td></tr>
      <tr><td>Autoprueba con recursos internos</td><td>Al encender, prueba las ganancias, las fuentes de ohmios contra su divisor interno de 10 MΩ y la sección de alterna, con la entrada desconectada (§9)</td><td>Con X3, X7, la fuente de ohmios y el divisor se puede hacer igual, con las puntas al aire (P41)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>Fuente de ohmios protegida con semiconductores</td><td>Diodo de alta tensión para positivos y cuatro transistores en serie para negativos: ±1000 V sin PTC ni fusible (§5)</td><td>Con 2 × MMBTA92 y un 1N4007W (≈ {K.COSTE_P42:.2f} USD) se cubren los 325 V de pico de RD-10; alternativa a la PTC de P30 (P42)</td><td>{tg(OPEN,'Comparar con P30')}</td></tr>
      <tr><td>Conmutadores en el lado de sentido</td><td>La ganancia ×1/×10/×100 y las resistencias de la fuente de ohmios se eligen con el conmutador del lado que no lleva corriente (§4, §5)</td><td>Es P19; vale también para la ganancia ×1/×10 del amplificador A</td><td>{tg(OK,'Refuerza P19')}</td></tr>
      <tr><td>Fugas de entrada de 30 pA</td><td>Corriente de polarización de la entrada inferior a 30 pA (§2)</td><td>La hoja del 74HC4051 garantiza solo ±0.1 µA por canal a 25 °C: en la toma ÷10 serían ~{K.FUGA_CUENTAS['74HC4051 (0.1 µA máx., un canal)']:.0f} cuentas. Hay que medir la fuga real (P37)</td><td>{tg(WARN,'Para la síntesis')}</td></tr>
      <tr><td>ADC multipendiente, Zener enterrado, relés</td><td>±18 V, ADC discreto, referencia de 7 V y cuatro relés de función</td><td>Fuera de alcance y de coste</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><code>research_and_tests/Agilent_34401A/34401A_Service_Guide.pdf</code>: Keysight, ed. 9 de 2014, 167 p. Se usaron:
      <ul class="tight">
        <li>las especificaciones (pp. 20–23);</li>
        <li>la teoría de funcionamiento (pp. 100–115);</li>
        <li>las autopruebas (pp. 128–132);</li>
        <li>y los esquemas vectoriales del frente/trasera, la conmutación de funciones, el amplificador de continua con ohmios y la alterna (pp. 157–160), renderizados por zonas a 260–320 ppp.</li>
      </ul></li>
    <li>Para comparar con nuestra cadena: la hoja del 74HC4051 de Nexperia (<code>datasheet - componentes/74HC_HCT4051.pdf</code>, p. 10) y LCSC para el precio de las piezas de P42.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_34401a.py</code>; redibujos en <code>draw_dmm_34401a.py</code> (0 solapes, revisados a la vista).</li>
  </ul>
"""))

dcv = "".join(f"<tr><td>{r}</td><td>±({a} % + {b} %)</td></tr>" for r, (a, b) in K.DCV_1A.items())
S.append(sec("especificacion", "2", "Lo que especifica", f"""
  <div class="tw"><table>
    <thead><tr><th>Tensión continua</th><th>1 año, 23 ± 5 °C (lectura + rango)</th></tr></thead>
    <tbody>{dcv}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>Formato</b>: 24 h, 90 días y un año, más un coeficiente por °C fuera de 18–28 °C. Es el método de ADI (R5, P35) llevado a una especificación comercial.</li>
    <li><b>Entrada de tensión</b>: 10 MΩ ±1 % (o &gt; 10 GΩ en 0.1–10 V) y menos de 30 pA de polarización; protección de 1000 V en todos los rangos.</li>
    <li><b>Rechazo</b>: 60 dB de modo normal a partir de un ciclo de red y 140 dB de modo común.</li>
    <li><b>Ohmios</b>: corriente referida a LO; 2 o 4 hilos.</li>
    <li><b>Corriente</b>: derivadores de 0.1 Ω (1 y 3 A) y de 5 Ω (10 y 100 mA); fusible externo de 3 A / 250 V y fusible interno de 7 A / 250 V.</li>
    <li><b>Continuidad</b>: 300 muestras/s con tono, y umbral de 1 a 1000 Ω.</li>
    <li><b>Alterna</b>: 3 Hz–300 kHz, con 1 MΩ ±2 % ∥ 100 pF de entrada y protección de 750 Vrms. Acoplada en alterna: admite hasta 400 V de continua superpuesta. Factor de cresta 5:1.</li>
  </ul>
"""))

S.append(sec("arquitectura", "3", "Arquitectura", """
  <ul class="tight">
    <li><b>Parte flotante</b>: medida, ADC y CPU. Habla con la parte unida a tierra (GPIB y RS-232) por un enlace serie optoaislado. Las fuentes son de ±18 V y +5 V.</li>
    <li><b>Una sola entrada al ADC</b>: todas las funciones terminan en una tensión de continua de ±10 V a fondo (2 V en alterna). Luego, el ADC multipendiente III y la calibración guardada en una EERAM de 128 × 16 bits.</li>
    <li><b>Cuatro relés</b> (K101–K104) eligen la función; K101 se abre un momento en cada cambio de rango o de función.</li>
    <li><b>Una red de resistencias de película fina (U102)</b> reúne todas las relaciones que fijan ganancias: el divisor de 10 MΩ / 100 kΩ, la realimentación del amplificador, las resistencias de la fuente de ohmios y las del ADC. Todas siguen juntas con la temperatura.</li>
  </ul>
"""))

S.append(sec("tension", "4", "Entrada de tensión, autocero y protección", f"""
  <ul class="tight">
    <li><b>Rangos</b>: solo dos relaciones de divisor, ÷1 y ÷100 (10 MΩ / 100 kΩ), y ganancias de ×1, ×10 y ×100. Todos los rangos dan 10 V en el ADC.</li>
    <li><b>Ganancia sin error del conmutador</b>: la red de realimentación (180 k + 18 k + 2 k) tiene tomas, y el conmutador U101C lleva la toma elegida a la puerta del FET de entrada, que no consume corriente. Su resistencia no entra en la ganancia.</li>
    <li><b>Amplificador de entrada</b>: un FET doble seguidor, con las alimentaciones de esa etapa «bootstrapeadas» (siguen a la entrada), y un OP-27. Así la polarización y la linealidad no cambian con la tensión de modo común.</li>
    <li><b>Autocero en tres estados</b>: medir la entrada (MC), medir el cero (MZ) y precargar (PRE); el resultado es MC − MZ. La precarga lleva las capacidades internas a la tensión de la entrada antes de reconectarla, para no inyectar carga en el borne. Un PWM del procesador ajusta el offset del amplificador de precarga.</li>
    <li><b>Protección de HI</b>: un descargador de gas (E100) en serie con un varistor (RV100) ∥ 10 nF ∥ 2 MΩ a masa. A tensión normal el descargador no conduce, así que el varistor no fuga sobre la entrada; con un transitorio dispara y el varistor y el condensador absorben la energía. Además hay huecos de chispa en el circuito impreso.</li>
  </ul>
  <p><b>Lo que pasa en nuestra sección H</b> al volver de X3 (COM, 0 V) a una toma. La capacidad del común del 74HC4051 (25 pF) más la entrada del amplificador (≈ 5 pF) se reparten la carga con la toma:</p>
  <div class="tw"><table>
    <thead><tr><th>Toma</th><th>Capacidad de la toma</th><th>Salto inicial</th><th>Constante de tiempo</th><th>Hasta 1 cuenta</th></tr></thead>
    <tbody>{''.join(f"<tr><td>{n}</td><td>{a['c_tap']*1e12:.0f} pF</td><td>{a['salto']*100:.1f} %</td><td>{a['tau']*1e6:.0f} µs</td><td>{a['t']*1e3:.2f} ms</td></tr>" for n, a in K.ASIENTO.items())}</tbody>
  </table></div>
  <p class="meta">Con τ = 60 µs en las patas (10 MΩ con 6 pF, como el 121GW). Con autocero en cada lectura se pierde ≈ 1 ms por conmutación. Una precarga lo reduce y evita el pulso en el borne.</p>
"""))

ohm_rows = "".join(f"<tr><td>{n}</td><td>{corriente(i)}</td></tr>" for n, i in K.I_OHM.items())
S.append(sec("ohmios", "5", "Ohmios: fuente de corriente ratiométrica y protegida", f"""
{fig(D.ohmios(), "Redibujo por bloques de la fuente de ohmios (hoja 3). U102D es parte de la misma red de resistencias que fija las ganancias.")}
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Corriente</th></tr></thead>
    <tbody>{ohm_rows}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>Ratiométrica</b>: la corriente sale de la referencia de 7 V del ADC (IREF = 7 V / 40 kΩ). Si la referencia deriva, la corriente y la ganancia del ADC cambian igual y la lectura de ohmios no se mueve ({pct(K.lectura_ohm(100e-6), 3)} con 100 ppm de deriva). Nuestra medida por razón (sección H §6) consigue lo mismo midiendo R_ref.</li>
    <li><b>Fuerza y sentido en el conmutador</b>: U101E lleva por separado la corriente y la medida de la tensión de la resistencia de rango.</li>
    <li><b>Protección de ±1000 V sin PTC</b>: CR202 se bloquea con tensiones positivas en HI, y la escalera Q203–Q210 suma las tensiones colector-base de cuatro transistores con las negativas. La polarizan Q211 y R203–R206 (4 × 196 kΩ). No hay que esperar a que nada se enfríe ni hay fusible que cambiar.</li>
    <li><b>100 MΩ</b> se mide con 500 nA y el divisor interno de 10 MΩ en paralelo, y el resultado se calcula. El valor del divisor se mide en cada calibración de cero, como haría falta en nuestro rango de 20 MΩ.</li>
  </ul>
"""))

S.append(sec("corriente", "6", "Corriente: dos fusibles, puente y bootstrap", """
  <ul class="tight">
    <li><b>Derivadores</b>: 0.1 Ω (1 A y 3 A) y 5.1 Ω (10 y 100 mA), elegidos por K102. La tensión se toma en el punto de sentido de R121, con ganancias de ×10 y ×100.</li>
    <li><b>Dos fusibles en serie</b>: uno externo de 3 A / 250 V rápido y uno interno de 7 A / 250 V de alto poder de corte, por si se aplica una fuente de mucha energía. Antes de los fusibles, un varistor (RV102).</li>
    <li><b>Puente de diodos CR100</b> con los terminales de continua unidos, como en el 121GW. Ese nodo lo mueve U110, un seguidor de la tensión del derivador, de modo que los diodos que tocan el derivador están a 0 V y no fugan. Para 6½ dígitos en 10 mA hace falta; para nuestras cuentas de 10 µA en 200 mA, no.</li>
  </ul>
  <p class="meta">Refuerza P31 (fusible cerámico de alto poder de corte y puente como sujeción) y añade la idea de un fusible rápido accesible delante del de alto poder de corte.</p>
"""))

ac_rows = "".join(f"<tr><td>{m*100:.0f} %</td>" + "".join(f"<td>{pct(x)}</td>" for x in e) + "</tr>" for m, e in K.ERR_AC.items())
S.append(sec("alterna", "7", "Alterna: atenuador con condensador programable", f"""
{fig(D.alterna(), "Redibujo de la primera etapa de alterna en ×0.2 (hoja 4); se omiten el modo ×0.002 (R303, C305) y los conmutadores.")}
  <ul class="tight">
    <li><b>Camino propio</b>: la alterna no usa el divisor de continua. Entra por C301 a un atenuador inversor de 1 MΩ (×0.2 o ×0.002) y pasa por una segunda etapa de ×1, ×10 o ×100. Después vienen un convertidor RMS analógico con tres filtros y un comparador para la frecuencia.</li>
    <li><b>Compensación sin trimmer</b>: el DAC multiplicador U302 (AD7524) y el seguidor U303 llevan el pie de C306 a V_OUT·P/256, así que la capacidad de realimentación efectiva va de 0 a 5.6 pF en pasos de {K.C_PASO*1e15:.0f} fF. El paso P se ajusta a 50 kHz en cada rango y se guarda con la calibración.</li>
  </ul>
  <p><b>Para nosotros</b>: la alterna pasa por el mismo divisor compensado que la continua (P18), con condensadores C0G fijos. Con las τ desparejadas, el error en función de la frecuencia sería este (divisor ÷10, τ = 60 µs):</p>
  <div class="tw"><table>
    <thead><tr><th>Desajuste de τ</th>{''.join(f"<th>{f/1e3:g} kHz</th>" for f in K.FRECS)}</tr></thead>
    <tbody>{ac_rows}</tbody>
  </table></div>
  <p class="meta">Un 2 % de desajuste (la tolerancia de un C0G de pocos pF y las parásitas) ya se come casi todo el ±1 % de la alterna (RD-07). Como el valor eficaz se calcula en el G473, el error se puede corregir con un filtro digital del orden inverso (P39).</p>
"""))

rech_rows = "".join(f"<tr><td>{k}</td><td>{'∞' if v == float('inf') else f'{v:.0f} dB'}</td></tr>" for k, v in K.RECH.items())
S.append(sec("adc", "8", "ADC, referencia y frecuencia de red", f"""
  <ul class="tight">
    <li><b>Multipendiente III</b>: un integrador con corrientes de referencia de ±10 V que se reparten continuamente, el contador de pendientes en un circuito propio y el ADC de 10 bits del procesador para el residuo. No lo copiamos.</li>
    <li><b>Referencia</b>: un Zener de 7 V (U403) amplificado a +10 V y −10 V. De él salen también las corrientes de ohmios.</li>
    <li><b>Frecuencia de red</b>: el procesador la mide en el transformador. Entre 55 y 66 Hz la toma como 60 Hz; si no, como 50 Hz. El tiempo de integración se fija en ciclos enteros de esa frecuencia.</li>
  </ul>
  <div class="tw"><table>
    <thead><tr><th>Integración (con ±1 % de error de frecuencia)</th><th>Rechazo</th></tr></thead>
    <tbody>{rech_rows}</tbody>
  </table></div>
  <p class="meta">Nuestro DMM va con batería y no puede medir la red en un transformador. En Perú la red es de 220 V y 60 Hz: con la cuenta pensada en 50 Hz el rechazo se queda en ~16 dB.</p>
"""))

S.append(sec("autoprueba", "9", "Calibración y autoprueba", """
  <ul class="tight">
    <li><b>Calibración</b>: las constantes se guardan en una EERAM (128 × 16 bits) y se copian a RAM al encender. Cada rango tiene ganancia y offset, y el valor del divisor interno de 10 MΩ se mide en cada calibración de cero.</li>
    <li><b>Autoprueba</b> (K101 abre la entrada):
      <ul class="tight">
        <li>la frecuencia de red;</li>
        <li>la convergencia del ADC en el estado MZ;</li>
        <li>las ganancias ×1, ×10 y ×100 con una tensión interna de 0.6 V;</li>
        <li>cada fuente de ohmios contra el divisor de 10 MΩ (5 V ± 1 V con 500 nA; el límite de tensión en las demás);</li>
        <li>el cero en 1000 V;</li>
        <li>y la sección de alterna, cargando C301 con la fuente de 1 mA.</li>
      </ul>
      Pasarla «da más de un 90 % de confianza» en el hardware, pero no asegura la exactitud.</li>
  </ul>
"""))

S.append(sec("no-copiar", "10", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>El ADC multipendiente discreto y la referencia de Zener de 7 V con ±18 V.</li>
    <li>Los cuatro relés de función: con nuestras tensiones bastan conmutadores analógicos y la red de resistencias del divisor.</li>
    <li>El camino de alterna separado, con convertidor RMS analógico: el G473 calcula el valor eficaz.</li>
    <li>La etapa de entrada con FET y alimentación bootstrapeada: el OPA2188 tiene 134 dB de rechazo de modo común.</li>
    <li>El puente de diodos con bootstrap en la corriente: nuestras cuentas son mil veces mayores que su fuga.</li>
  </ul>
"""))

S.append(sec("comparacion", "11", "Comparación con la sección H", f"""
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>34401A</th><th>Sección H</th></tr></thead>
    <tbody>
      <tr><td>Dígitos / exactitud</td><td>6½; 0.0035 % + 0.0005 % en 10 V, un año</td><td>4½; objetivo 0.1 % + 30–40 cuentas (R5)</td></tr>
      <tr><td>Divisor</td><td>10 MΩ / 100 kΩ, ÷1 y ÷100, red única</td><td>10 MΩ con tomas ÷1, ÷10 y ÷100 (o P17)</td></tr>
      <tr><td>Autocero</td><td>MC / MZ / PRE en cada lectura</td><td>X3 (COM) en cada lectura, sin precarga</td></tr>
      <tr><td>Ohmios</td><td>Fuente de corriente ratiométrica, protección con semiconductores</td><td>Razón con R_ref, PTC</td></tr>
      <tr><td>Alterna</td><td>Camino propio de 1 MΩ, compensación programable, RMS analógico</td><td>El mismo divisor, C0G fijos, RMS por firmware</td></tr>
      <tr><td>Fugas en la entrada</td><td>&lt; 30 pA</td><td>OPA2188 ≤ 850 pA; 74HC4051 ≤ 0.1 µA por canal (máx.)</td></tr>
      <tr><td>Frecuencia de red</td><td>Medida en el transformador</td><td>Sin definir (batería)</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "12", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P37. <b>Ninguna está aplicada.</b></p>
  <h3>P38 · Autocero con tiempo de asiento y, si hace falta, precarga {tg(OK,'Adoptar')}</h3>
  <p>Tras cada conmutación del mux, esperar a que la toma vuelva a 1 cuenta: {a10['t']*1e3:.1f} ms en ÷10 y {a100['t']*1e3:.2f} ms en ÷100 con los valores de §4. Se calcula por rango y se comprueba en S11. Si la pérdida de tiempo o el pulso en el borne molestan, añadir un estado de precarga como el del 34401A: llevar el común a la última lectura antes de reconectar. Necesita un canal o un conmutador más.</p>
  <h3>P39 · Corrección de la respuesta en alterna por firmware {tg(OK,'Adoptar')}</h3>
  <p>Es el equivalente digital del condensador programable. En cada rango, un filtro de primer orden (un cero y un polo) sobre las muestras de 200 kSa/s compensa el desajuste de τ del divisor. Sus dos parámetros salen de calibrar a 1 kHz y a 20 kHz y se guardan con la calibración (P29). Así los condensadores fijos C0G de P18 no necesitan trimmer ni selección.</p>
  <h3>P40 · Tiempo de integración ligado a la red de 60 Hz {tg(WARN,'Adoptar')}</h3>
  <p>El valor por defecto debe ser 60 Hz (Perú), configurable en S3G4-UI. Para las lecturas lentas, integrar 100 ms, que rechaza 50 y 60 Hz a la vez sin saber cuál es; para las rápidas, un ciclo de la red elegida. Con el ajuste equivocado el rechazo cae a 14–16 dB.</p>
  <h3>P41 · Autoprueba al encender {tg(OK,'Adoptar')}</h3>
  <p>Con las puntas al aire:</p>
  <ul class="tight">
    <li>cero por X3;</li>
    <li>ganancia con X7 (VREF/2);</li>
    <li>fuente de ohmios en 20 MΩ contra el divisor de 10 MΩ (≈ 2.45 V esperados);</li>
    <li>el umbral de continuidad del COMP7;</li>
    <li>y la medida del divisor de 10 MΩ para corregir el rango de 20 MΩ.</li>
  </ul>
  <p>Si hay algo conectado, la autoprueba se declara no concluyente, igual que el 34401A con la entrada ocupada. El resultado se muestra en S3G4-UI.</p>
  <h3>P42 · Proteger la fuente de ohmios con semiconductores {tg(OPEN,'Comparar con P30')}</h3>
  <p>Es una alternativa a la PTC. Un diodo de alta tensión en serie (1N4007W, 1 kV, C18199088) bloquea las tensiones positivas, y {K.N_MMBTA92} MMBTA92 en escalera (300 V, C20069146) bloquean las negativas. Todo cuesta ≈ {K.COSTE_P42:.2f} USD en LCSC. Responde al instante y no necesita recuperarse. La caída del diodo queda fuera de la medida, porque la razón se mide en el borne. Hay que simular en S11 cómo se reparte la tensión entre los escalones y la fuga sobre la entrada en modo tensión.</p>
  <p class="meta">Además: refuerza P19 (conmutadores en el lado de sentido), P23 (descargador de gas en serie con varistor y condensador), P31 (dos fusibles: rápido accesible y de alto poder de corte), P35 (formato de especificación de 24 h, 90 días y un año) y P29 (calibración en memoria no volátil).</p>
"""))

S.append(sec("correcciones", "13", "Correcciones a lo dicho antes", f"""
  <ul class="tight">
    <li><b>Sección H §3</b> supone «unos nA» de fuga del 74HC4051. La hoja de Nexperia garantiza solo ±0.1 µA por canal a 25 °C (±1 µA de −40 a 85 °C). En la toma ÷10 eso serían ~{K.FUGA_CUENTAS['74HC4051 (0.1 µA máx., un canal)']:.0f} cuentas. El valor típico real es mucho menor, pero no está garantizado: hay que medirlo (P37) o elegir un conmutador de fuga especificada.</li>
    <li>La red de Perú es de <b>60 Hz</b> (y 220 V). Las cuentas de rechazo de la sección H deben hacerse con 16.67 ms, no con 20 ms (P40).</li>
    <li>El plan descartaba de entrada el 34401A y luego lo añadió como R9: queda estudiado.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("especificacion", "2 · Especificación"),
    ("arquitectura", "3 · Arquitectura"), ("tension", "4 · Tensión y autocero"), ("ohmios", "5 · Ohmios"),
    ("corriente", "6 · Corriente"), ("alterna", "7 · Alterna"), ("adc", "8 · ADC y red"), ("autoprueba", "9 · Calibración y autoprueba"),
    ("no-copiar", "10 · Lo que no conviene copiar"), ("comparacion", "11 · Comparación"), ("propuestas", "12 · Propuestas P38–P42"),
    ("correcciones", "13 · Correcciones")])

HTML = (
 '<title>Anatomía del 34401A</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code,a{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 9 de 9</p>\n  <h1>Anatomía del 34401A</h1>\n'
 '  <p class="lede">El multímetro de banco de 6½ dígitos de referencia, con los esquemas del manual de servicio. Su ADC no se copia, pero su autocero con precarga, la compensación programable de la alterna, la protección de la fuente de ohmios y la autoprueba sí se pueden llevar a nuestra escala.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuente: Keysight 34401A Service Guide, ed. 9 (2014), en <code>research_and_tests/Agilent_34401A/</code>. Cifras: <code>herramientas/calc_dmm_34401a.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
