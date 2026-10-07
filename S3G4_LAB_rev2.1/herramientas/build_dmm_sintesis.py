# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/01_diseno/dmm_sintesis.html: sintesis de las 9 referencias del DMM y propuesta de
arquitectura para que decida Keneth. Cifras: calc_dmm_sintesis.py (y calc_dmm_adi, calc_dmm_34401a).
Dibujo: draw_dmm_sintesis.py. Plantilla: build_dmm_tida01012.py."""
import io, draw_dmm_sintesis as D, calc_dmm_sintesis as K, calc_dmm_34401a as A34
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/01_diseno/dmm_sintesis.html"

ART = {"TIDA-01012": "BzuS4XnvR7xVfP3ZutR9No", "HydraMeter": "5j4fYKqbpLK8TxGpkFgE7D", "TIDA-00879": "XKxwSffsJUNX7j4EGX2iLx",
       "121GW": "YcB94Hqks4aYz739W2KLwM", "Micro-DMM": "VXTHBpRXxs9tDhqPwQFTb6", "Martin": "R3vvm1wXKejCDjdHz8xVFR",
       "EEWorld 77845": "JMeU9V49kriNvnQjgBTxeg", "Analog Devices": "LsJG4aZhYxcP8A2SGfAiZN", "34401A": "Gd8rGXutjjVU3zHBf2p9LY"}
def ref(n): return f'<a href="https://claude.ai/artifact/{ART[n]}">{n}</a>'

c200 = K.CASOS_200
S = []
S.append(sec("resumen", "★", "En una página", f"""
  <p>Estudiamos nueve referencias: dos diseños de TI, dos DMM abiertos, uno comercial certificado, dos con el ADC de un STM32, un método de errores de Analog Devices y el 34401A de banco. La conclusión principal: <b>la arquitectura de la sección H estaba bien orientada</b>. Divisor de 10 MΩ con tomas, multiplexor, amplificador de deriva cero, driver diferencial, ADC5 sobremuestreado, ohmios por razón y continuidad por comparador coinciden con lo mejor de las referencias. El estudio la corrige en ocho puntos y le añade casi todo lo demás <b>en firmware, sin piezas</b>.</p>
  <ul class="tight">
    <li><b>Lo que cambia en el hardware</b> (céntimos):
      <ul class="tight">
        <li>la protección de la fuente de ohmios pasa de una PTC a un diodo y dos transistores (P42);</li>
        <li>ningún divisor en el lado del DUT (P25);</li>
        <li>derivador de 4 terminales (P27), fusible cerámico con puente de diodos (P31) y filtro de muestreo calculado (P20);</li>
        <li>una huella sin montar para un ADC ΣΔ de respaldo.</li>
      </ul></li>
    <li><b>Lo que se hace en firmware</b>: autocero con tiempo de asiento, integración a 60 Hz, corrección de la alterna, calibración multipunto con linealización del ADC5, autoprueba, cable abierto y aviso de tensión en ohmios.</li>
    <li><b>La especificación se mantiene</b> en ±(0.1 % + 10) en continua <b>tras la calibración por software al fabricar</b>. Sin linealizar el ADC5, lo que garantiza la hoja de datos es ±(0.1 % + 40).</li>
    <li><b>Te toca decidir</b> siete puntos (§9). Para cada uno hay una recomendación.</li>
  </ul>
  <p class="meta">Criterio aplicado (Keneth, 7 oct): estudiar y simular para dejar margen; al fabricar, calibrar por software. Especificaciones algo holgadas pero de instrumento profesional. Bajo coste y pocos componentes, sin sesgo hacia ninguna referencia. Nada de esto está aplicado a la sección H todavía.</p>
"""))

S.append(sec("referencias", "1", "Las nueve referencias, de un vistazo", f"""
  <div class="tw"><table>
    <thead><tr><th>#</th><th>Referencia</th><th>Qué es</th><th>ADC</th><th>Lo que más aportó</th><th>Propuestas</th></tr></thead>
    <tbody>
      <tr><td>R1</td><td>{ref('TIDA-01012')}</td><td>Diseño de TI, 4½ dígitos</td><td>SAR 18 bits externo</td><td>Divisor de 10 MΩ con patas conmutadas, driver diferencial con VCM, valor eficaz por firmware</td><td>P17–P22</td></tr>
      <tr><td>R2</td><td>{ref('HydraMeter')}</td><td>DMM abierto, todo discreto</td><td>ΣΔ 16 bits + PGA</td><td>Protección escalonada, ohmios con tensión medida en el borne, derivador de 4 terminales</td><td>P23–P27</td></tr>
      <tr><td>R6</td><td>{ref('TIDA-00879')}</td><td>Antecesor del 01012</td><td>ΣΔ 24 bits del MCU</td><td>Resistencia de alta tensión de entrada; calibración que no debe ir en el código</td><td>P28–P29</td></tr>
      <tr><td>R7</td><td>{ref('121GW')}</td><td>Comercial, CAT III 600 V</td><td>Chip de DMM</td><td>Protección certificada, fusibles de alto poder de corte y puente de diodos</td><td>P30–P32</td></tr>
      <tr><td>R3</td><td>{ref('Micro-DMM')}</td><td>DMM casero</td><td>ADS1115</td><td>Cable abierto (puente de Mann); el límite de un ohmímetro de divisor</td><td>P33–P34</td></tr>
      <tr><td>R8</td><td>{ref('Martin')}</td><td>DMM abierto, STM32F373</td><td>ΣΔ 16 bits del MCU</td><td>Errores medibles: referencia de corriente lejos del derivador y RMS mal corregido</td><td>refuerza</td></tr>
      <tr><td>R4</td><td>{ref('EEWorld 77845')}</td><td>Concurso, ficha corta</td><td>SAR 12 bits del F103</td><td>Límite inferior: ≈ 1 % sin referencia propia ni autocero</td><td>refuerza</td></tr>
      <tr><td>R5</td><td>{ref('Analog Devices')}</td><td>Método de 7½ dígitos</td><td>SAR 24 bits</td><td>El presupuesto de errores; la INL del ADC5 son 26–39 cuentas</td><td>P35–P37</td></tr>
      <tr><td>R9</td><td>{ref('34401A')}</td><td>Banco de 6½ dígitos</td><td>Multipendiente</td><td>Autocero con precarga, compensación de alterna programable, fuente de ohmios protegida con semiconductores, autoprueba</td><td>P38–P42</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("patrones", "2", "Lo que repiten los buenos diseños", f"""
  <div class="tw"><table>
    <thead><tr><th>Idea</th><th>Quién la usa</th><th>En la sección H</th></tr></thead>
    <tbody>
      <tr><td>Entrada de 10 MΩ con un divisor de precisión</td><td>TIDA ×2, 121GW, 34401A (Martin y HydraMeter, 1 MΩ)</td><td>{tg(OK,'Sí')}</td></tr>
      <tr><td>Conmutadores solo en nodos de baja tensión y en el lado de sentido</td><td>TIDA, 34401A, Martin, HydraMeter</td><td>{tg(OK,'Sí')} (R_PROT, sujeciones, sentido en ohmios y en la ganancia de A)</td></tr>
      <tr><td>Amplificador sin deriva y autocero</td><td>34401A (MC/MZ), TIDA (OPA333), 121GW (MAX4238)</td><td>{tg(OK,'Sí')} (OPA2188 + X3)</td></tr>
      <tr><td>Todo el ADC detrás de un buffer</td><td>TIDA, Martin, 34401A; el Micro-DMM, que no lo tiene, pierde un 2 % entre ganancias</td><td>{tg(OK,'Sí')}</td></tr>
      <tr><td>Ohmios ratiométricos</td><td>34401A (corriente de la misma referencia), HydraMeter</td><td>{tg(OK,'Sí')} (razón con R_ref)</td></tr>
      <tr><td>Valor eficaz por firmware</td><td>TIDA ×2, Martin (los comerciales lo hacen analógico)</td><td>{tg(OK,'Sí')}</td></tr>
      <tr><td>Calibración multipunto en memoria no volátil</td><td>Todas</td><td>{tg(WARN,'Parcial')} (ganancia y offset por rango; P26, P29)</td></tr>
      <tr><td>Protección de ohmios que no limita la corriente de medida</td><td>34401A (semiconductores), 121GW (PTC con fuente de mA)</td><td>{tg(CRIT,'No')} (la PTC de kΩ choca con 9.8 mA; P42)</td></tr>
      <tr><td>Fusible de alto poder de corte y puente de diodos en A</td><td>121GW, 34401A</td><td>{tg(WARN,'Parcial')} (P31)</td></tr>
    </tbody>
  </table></div>
"""))

fallos = [
    ("INL del ADC5", "R5", f"26–39 cuentas (hoja, 25 °C), no menos de 10", "Linealización al fabricar (P26) y huella ΣΔ de respaldo; especificación honesta sin linealizar: +40 (D1)"),
    ("PTC «de pocos kΩ» en serie con R_ref", "síntesis", f"Con 2 kΩ, el rango de 200 Ω baja de {c200['Sin protección (H §6, nominal)']['i']*1e3:.1f} a {c200['PTC de 2 kΩ en frío (H: «pocos kΩ»)']['i']*1e3:.1f} mA y usa el {c200['PTC de 2 kΩ en frío (H: «pocos kΩ»)']['ventana']*100:.0f} % de la ventana", f"P42 (diodo + 2 transistores): {c200['P42: diodo + transistores (≈ 1 V de caída)']['ventana']*100:.0f} % de la ventana, sin corriente de sujeción (D3)"),
    ("Divisor ÷4 en X6, en el lado del DUT", "R2", "Roba corriente que no pasa por el DUT", "Medir ese nodo sin cargarlo, o meter la carga en la calibración (P25)"),
    ("Fuga del 74HC4051 «unos nA»", "R9", f"La hoja solo garantiza 0.1 µA; con 1 nA ya son ≈ {K.FUGA_POR_NA['20 V (X1, ÷10)']:.0f} cuentas en 20 V", "Calibrar el offset por rango y fijar en S11 la fuga tolerable (D4)"),
    ("OPA2188 «160 pA»", "R5", "Es la típica; la máxima es de 850 pA (≈ 8 cuentas en 200 mV)", "Entra en el presupuesto; no cambia la pieza"),
    ("Red de 50 Hz implícita", "R9", f"En Perú es de 60 Hz: integrando 20 ms, solo {A34.RECH['60 Hz con 20 ms (ajuste de 50 Hz)']:.0f} dB de rechazo", "60 Hz por defecto, o 100 ms (P40)"),
    ("Autocero sin tiempo de asiento", "R9", "Al volver de X3, la toma ÷10 cae un 33 % y tarda 0.8 ms en recuperarse", "Esperar ≈ 1 ms por conmutación (P38)"),
    ("Trimmer o condensador «elegido en prueba» en ÷10", "R9 + P18", "Con un 2 % de desajuste de τ, −1.7 % a 20 kHz", "C0G fijos y corrección por firmware calibrada (P39)"),
]
S.append(sec("correcciones", "3", "Lo que el estudio corrige de la sección H", """
  <div class="tw"><table>
    <thead><tr><th>Punto de H</th><th>Lo vio</th><th>Cifra</th><th>Solución propuesta</th></tr></thead>
    <tbody>""" + "".join(f"<tr><td>{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>" for a, b, c, d in fallos) + """</tbody>
  </table></div>
"""))

S.append(sec("arquitectura", "4", "Arquitectura recomendada", f"""
{fig(D.bloques(), "Arquitectura del DMM tras la síntesis. Es la de la sección H con las correcciones de §3. Es una propuesta, no aplicada.")}
  <div class="tw"><table>
    <thead><tr><th>Bloque</th><th>Qué tomamos y de quién</th><th>Coste o complejidad</th></tr></thead>
    <tbody>
      <tr><td>Protección V/Ω</td><td>R_PROT de alta tensión en piezas repartidas y sujeción a los rieles (H, como el osciloscopio; reparto de tensión del HydraMeter y del 121GW). Sin descargadores ni varistores: no hay categoría y RD-10 son 10 s</td><td>Igual que H</td></tr>
      <tr><td>Divisor y rangos</td><td>10 MΩ con tomas ÷10 y ÷100; 200 mV y 2 V por X0 (H). Compensación con la misma τ y C0G fijos, más una R de amortiguación (P18, 121GW)</td><td>Igual que H; sin trimmer</td></tr>
      <tr><td>Mux, amplificador y ADC</td><td>74HC4051, OPA2188 de deriva cero, driver diferencial a 3.3 V y ADC5 sobremuestreado (H, TIDA-01012). Filtro de muestreo calculado (P20)</td><td>Igual que H</td></tr>
      <tr><td>ADC de respaldo</td><td>Huella sin montar para un ADS1115 (16 bits, INL de 1 LSB, LCSC C37593, 1.22 USD) en paralelo con el ADC5, solo para continua. Una cuenta suya son {K.ADS_CUENTAS_LSB:.2f} cuentas nuestras</td><td>0 USD si no se monta</td></tr>
      <tr><td>Ohmios</td><td>Razón con R_ref por rango y tensión leída en el borne (H, HydraMeter, 34401A). Protección con un diodo de 1 kV y dos PNP de 300 V (P42, 34401A). Ningún divisor en el lado del DUT (P25)</td><td>≈ {A34.COSTE_P42:.2f} USD, en lugar de una PTC</td></tr>
      <tr><td>Corriente</td><td>Un derivador de 0.1 Ω de 4 terminales con estrella en COM (P27, HydraMeter, Martin), fusible cerámico de alto poder de corte y puente DF10S (P31, 121GW, 34401A)</td><td>Unos céntimos más que H</td></tr>
      <tr><td>Continuidad</td><td>COMP7 con umbral del DAC2: &lt; 1 ms sin CPU (H). Ninguna referencia es más rápida (34401A: 300 muestras/s)</td><td>Igual que H</td></tr>
      <tr><td>Firmware</td><td>Media y RMS sin continua (P21, TIDA), NPLC de 60 Hz (P40, 34401A), corrección de alterna (P39, 34401A), calibración multipunto con linealización (P26, HydraMeter, Micro-DMM), memoria con CRC (P29), autoprueba (P41), cable abierto (P33, Micro-DMM), tensión en ohmios (P34)</td><td>Sin piezas</td></tr>
    </tbody>
  </table></div>
"""))

V = {"hw": tg(OK, "Adoptar · hardware"), "fw": tg(OK, "Adoptar · firmware"), "h": tg(OK, "Ya en H"), "opt": tg(OPEN, "Opcional"),
     "dec": tg(WARN, "Decidir"), "no": tg(CRIT, "Descartar"), "sus": tg(CRIT, "Sustituida")}
PROP = [
    ("P17", "Patas bajas conmutadas a COM", "no", "En 200 mV dejaría 10 MΩ de fuente: los 850 pA del OPA2188 serían 8.5 mV (4 % del fondo). H ya protege el mux con R_PROT y sujeciones"),
    ("P18", "Misma τ en todas las patas, C0G fijos y R de amortiguación", "hw", "Sin trimmer; el residuo lo quita P39 · S11"),
    ("P19", "Conmutadores en el lado de sentido", "h", "Ohmios y ganancia de A"),
    ("P20", "Filtro del ADC5 calculado por la carga de muestreo", "hw", "S11"),
    ("P21", "Medida en firmware: media, RMS sin continua, NPLC", "fw", ""),
    ("P22", "Riel propio del DMM, apagable", "hw", "Interruptor de carga; RF-18 (D7)"),
    ("P23", "Protección escalonada", "opt", "Sí al reparto en piezas de alta tensión (ya en H); no a descargadores ni varistores"),
    ("P24", "Ohmios con la tensión medida en el borne", "h", ""),
    ("P25", "Ningún divisor en el lado del DUT", "hw", "S11"),
    ("P26", "Calibración multipunto por tramos", "fw", "Es también la linealización del ADC5 · al fabricar"),
    ("P27", "Derivador de 4 terminales, estrella en COM", "hw", "PCB"),
    ("P28", "Resistencia de entrada de alta tensión", "opt", "H ya reparte 9 MΩ en 3 piezas (D6)"),
    ("P29", "Calibración en memoria, con CRC y versión, editable desde S3G4-UI", "fw", ""),
    ("P30", "PTC en la fuente de ohmios", "sus", "Por P42: una PTC de kΩ deja el rango de 200 Ω al 20 % de la ventana"),
    ("P31", "Fusible cerámico de alto poder de corte + puente DF10S", "hw", "BOM"),
    ("P32", "Aviso de fusible abierto", "opt", "Una resistencia y una entrada libre (D6)"),
    ("P33", "Cable abierto con la fuente de 20 MΩ", "fw", "Sin piezas · S11"),
    ("P34", "Detectar tensión externa en ohmios y desconectar la fuente", "fw", "S11 (tiempo de detección)"),
    ("P35", "Presupuesto de errores con el método de ADI", "fw", "Documento: en la revisión de H"),
    ("P36", "INL del ADC5", "dec", "D1: linealización al fabricar + huella ΣΔ"),
    ("P37", "Cuatro ensayos: ruido, INL, temperatura, estabilidad", "fw", "Con el prototipo, no en la placa WeAct"),
    ("P38", "Autocero con tiempo de asiento", "fw", "La precarga se descarta por ahora · S11"),
    ("P39", "Corrección de la alterna por firmware", "fw", "S11 + calibración"),
    ("P40", "Integración ligada a 60 Hz, o 100 ms", "fw", ""),
    ("P41", "Autoprueba al encender", "fw", ""),
    ("P42", "Protección de ohmios con diodo + transistores", "hw", "D3 · S11"),
]
N = {k: sum(1 for p in PROP if p[2] == k) for k in V}
assert sum(N.values()) == 26
S.append(sec("propuestas", "5", "Veredicto sobre las 26 propuestas", f"""
  <p>Resumen: {N['hw']} de hardware (pocos céntimos), {N['fw']} de firmware o documento, {N['h']} que ya están en H, {N['opt']} opcionales, {N['no']} descartada, {N['sus']} sustituida y {N['dec']} por decidir.</p>
  <div class="tw"><table>
    <thead><tr><th>#</th><th>Propuesta</th><th>Veredicto</th><th>Motivo y dónde se comprueba</th></tr></thead>
    <tbody>{''.join(f"<tr><td>{p}</td><td>{t}</td><td>{V[v]}</td><td>{m}</td></tr>" for p, t, v, m in PROP)}</tbody>
  </table></div>
"""))

SPEC = [
    ("Tensión continua (200 mV–50 V)", "±(0.1 % + 40)", "±(0.1 % + 10)", "121GW: 0.05 % + 5 (55 000 cuentas); 34401A: 0.0035 % + 0.0005 %"),
    ("Tensión alterna, 40 Hz–20 kHz", "±(1 % + 40)", "±(1 % + 20)", "121GW: 0.3 % + 10 (45–400 Hz), 1.5 % + 10 hasta 5 kHz"),
    ("Resistencia, 200 Ω–2 MΩ", "±(0.2 % + 40)", "±(0.2 % + 10)", "121GW: 0.2 % + 5 (5 kΩ–500 kΩ)"),
    ("Resistencia, 20 MΩ", "±(1 % + 40)", "±(1 % + 10)", "121GW: 1.2 % + 20 (50 MΩ)"),
    ("Corriente continua", "±(0.5 % + 40)", "±(0.5 % + 10)", "121GW: 0.25 % + 5 (mA)"),
    ("Corriente alterna", "±(1.5 % + 40)", "±(1.5 % + 20)", "—"),
]
S.append(sec("especificacion", "6", "Especificación propuesta: holgada, pero de instrumento", f"""
  <div class="tw"><table>
    <thead><tr><th>Función</th><th>Garantizada por diseño (sin linealizar)</th><th>Tras la calibración al fabricar</th><th>Referencias profesionales</th></tr></thead>
    <tbody>{''.join(f"<tr><td>{a}</td><td>{b}</td><td><b>{c}</b></td><td>{d}</td></tr>" for a, b, c, d in SPEC)}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>Condiciones</b> (como el 34401A y el 121GW): un año desde la calibración, a 23 ± 5 °C, y al menos un ciclo de red de 60 Hz. Fuera de 18–28 °C se añade 0.1 × la exactitud por °C.</li>
    <li><b>El término de lectura</b> (0.1 % en continua) sale del presupuesto de R5: {K.GAN_PPM:.0f} ppm en el peor rango con la REF3325, resistencias del 0.1 % y 25 ppm/°C y un patrón del 0.05 %. Queda margen para la deriva de un año sin redes apareadas.</li>
    <li><b>El término de cuentas</b> lo fija la INL del ADC5: {K.INL_TIP:.0f} cuentas típicas y {K.INL_MAX:.0f} máximas según la hoja. Linealizada al fabricar, debería bajar a ≈ 10. Si no baja, se monta el ΣΔ de respaldo.</li>
    <li>20 000 cuentas con +10 sigue siendo un instrumento de 4½ dígitos honesto: por encima de los de 6000 cuentas, por debajo del 121GW.</li>
  </ul>
"""))

S.append(sec("s11", "7", "Qué tiene que demostrar la simulación S11 antes de fabricar", """
  <p>Monte Carlo con tolerancias reales y aceptación en ≥ 95 % de las placas, como en el osciloscopio:</p>
  <ol class="tight">
    <li><b>Continua por rango</b>: resistencias, REF3325, OPA2188 (Vos, Ib) y fuga del 4051 barrida de 0.1 a 10 nA. Sale la fuga máxima tolerable con la calibración de offset por rango.</li>
    <li><b>Alterna</b>: planitud de 40 Hz a 20 kHz con C0G ±5 % y parásitas. Comprobar que la corrección de P39 la deja por debajo del 0.5 %.</li>
    <li><b>Ohmios</b>: los 6 rangos con la caída de P42, la ventana usada, la corriente de prueba y la prueba de diodo con un LED de 3 V.</li>
    <li><b>Corriente</b>: offset y ruido en 200 mA, caída a 2 A y el cruce con el divisor de tensión (P27).</li>
    <li><b>Autocero</b>: el asiento en cada toma tras volver de X3.</li>
    <li><b>Continuidad</b>: COMP7 con su divisor y sujeción.</li>
    <li><b>RD-10</b>: la red durante 10 s en tensión, en ohmios (P42) y con el equipo apagado. Ninguna pieza por encima del 80 % de su tensión ni del 50 % de su potencia.</li>
    <li><b>ESD</b>: ±4 kV por contacto y ±8 kV por aire en los tres bornes.</li>
    <li><b>Driver y muestreo del ADC5</b> (P20).</li>
  </ol>
  <p class="meta">La INL no se puede simular (es del chip): se resuelve al fabricar. La fuga del 4051 sí entra como parámetro.</p>
"""))

S.append(sec("fabricar", "8", "Qué se hace al fabricar: calibración por software", """
  <p>Una vez montada la placa, con una fuente estable y el mejor multímetro del laboratorio, sin tocar el hardware. Todo se guarda con CRC (P29) y se puede repetir desde S3G4-UI:</p>
  <ol class="tight">
    <li><b>Autoprueba</b> (P41), con las puntas al aire.</li>
    <li><b>Linealización del ADC5</b>: un barrido de ≈ 41 puntos en el rango de 2 V. Como todos los rangos llevan ±2 V al ADC, sirve para todos (P26, P36).</li>
    <li><b>Ganancia y offset</b> de cada rango y función, incluido el offset por la fuga del 4051.</li>
    <li><b>Alterna</b>: un punto a 1 kHz y otro a 20 kHz por rango, para la corrección de P39.</li>
    <li><b>El divisor de 10 MΩ</b>, medido para corregir el rango de 20 MΩ.</li>
    <li><b>Verificación</b> con los cuatro ensayos de P37. Si la INL no baja a ≈ 10 cuentas, se monta el ADS1115 y se repite el paso 2 con él.</li>
  </ol>
"""))

S.append(sec("decisiones", "9", "Lo que decides tú", f"""
  <div class="tw"><table>
    <thead><tr><th>#</th><th>Pregunta</th><th>Opciones</th><th>Recomendación</th></tr></thead>
    <tbody>
      <tr><td>D1</td><td>¿Cómo se trata la INL del ADC5?</td><td>(a) linealizar al fabricar, con huella ΣΔ sin montar · (b) solo ADC5 y +40 · (c) ΣΔ desde el principio</td><td><b>(a)</b>: no añade piezas y tiene salida si falla</td></tr>
      <tr><td>D2</td><td>¿Divisor con tomas (H) o patas conmutadas (P17)?</td><td>Tomas · patas</td><td><b>Tomas</b> (§5, P17)</td></tr>
      <tr><td>D3</td><td>¿Cómo se protege la fuente de ohmios?</td><td>Diodo + 2 transistores (P42) · PTC de pocos Ω con TVS robusta</td><td><b>P42</b>, a confirmar en S11</td></tr>
      <tr><td>D4</td><td>¿74HC4051 o mux de fuga garantizada?</td><td>74HC4051 (0.21 USD) con offset calibrado · uno garantizado (el MAX4051A cuesta 9.50 USD en LCSC)</td><td><b>74HC4051</b> si S11 tolera ≥ 1 nA</td></tr>
      <tr><td>D5</td><td>¿La especificación de §6?</td><td>Tal cual · más estricta · más holgada</td><td><b>Tal cual</b></td></tr>
      <tr><td>D6</td><td>¿Opcionales P28 (resistencia de alta tensión) y P32 (aviso de fusible)?</td><td>Sí · no</td><td>P32 sí si queda una entrada libre en el mapa de pines; P28 no</td></tr>
      <tr><td>D7</td><td>¿Riel propio del DMM, apagable (P22)?</td><td>Sí · no</td><td><b>Sí</b> (RF-18, céntimos)</td></tr>
    </tbody>
  </table></div>
  <p>Con tus respuestas reviso la sección H (y su hoja de especificaciones) y escribo el encargo S11.</p>
"""))

S.append(sec("descartes", "10", "Lo que no tomamos de nadie", """
  <ul class="tight">
    <li>Módulos (Arduino, Pico, ACS712, placas ADC): regla del plan.</li>
    <li>Chips de multímetro (HY3131): fijan la arquitectura y el firmware.</li>
    <li>ADC multipendiente, referencias de Zener enterrado y alimentaciones de ±18 V (34401A).</li>
    <li>Relés de función, convertidores RMS analógicos y caminos de alterna separados.</li>
    <li>Aislar todo el DMM o llevar COM a media alimentación (HydraMeter, Martin, Micro-DMM): va contra RD-05.</li>
    <li>Descargadores y varistores: son para categorías de medida que no buscamos.</li>
    <li>Ohmímetro de divisor con la referencia supuesta (Micro-DMM).</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "En una página"), ("referencias", "1 · Las nueve referencias"), ("patrones", "2 · Lo que se repite"),
    ("correcciones", "3 · Correcciones a H"), ("arquitectura", "4 · Arquitectura recomendada"), ("propuestas", "5 · Veredicto P17–P42"),
    ("especificacion", "6 · Especificación"), ("s11", "7 · Qué simula S11"), ("fabricar", "8 · Calibración al fabricar"),
    ("decisiones", "9 · Lo que decides"), ("descartes", "10 · Lo que no tomamos")])

HTML = (
 '<title>Síntesis del DMM</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code,a{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · DMM de la rev 2.1 · síntesis de las 9 referencias</p>\n  <h1>Síntesis del DMM</h1>\n'
 '  <p class="lede">Qué aprendimos de las nueve referencias, qué corrige en la sección H y qué arquitectura proponemos: simple, barata y con especificaciones de instrumento, para calibrar por software al fabricar.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Síntesis de Claude Code, 7 oct 2026, paso 8 de <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Páginas de cada referencia en <code>02_referencias/dmm_*.html</code>. Cifras: <code>herramientas/calc_dmm_sintesis.py</code>, <code>calc_dmm_adi.py</code> y <code>calc_dmm_34401a.py</code>. Nada está aplicado a la sección H hasta que Keneth decida.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
