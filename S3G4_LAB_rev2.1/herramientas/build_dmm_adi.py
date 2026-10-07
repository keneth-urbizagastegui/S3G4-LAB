# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_adi_errores.html (R5: metodo de presupuesto de errores de Analog Devices
y su aplicacion a la seccion H). Cifras: calc_dmm_adi.py. Plantilla: build_dmm_tida01012.py."""
import io, calc_dmm_adi as K
from build_dmm_tida01012 import css, EXTRA, sec, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_adi_errores.html"

inl_t, inl_m = K.INL_CUENTAS["típica (25 °C)"], K.INL_CUENTAS["máx. (25 °C, VDDA = VREF+ = 3 V)"]

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>Los dos artículos de Analog Devices (D. Guo y O. Liu, 2024) no describen un multímetro. Explican <b>cómo se hace el presupuesto de errores</b> de una cadena de medida de 7½ dígitos y luego lo comprueban en placa. El método no depende de la escala: lo aplicamos a nuestra sección H, que pide ±(0.1 % + 10) con el ADC5 del G473. El resultado cambia una cifra de la especificación.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En ADI</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Dos cubos: lectura y rango</td><td>Los errores de ganancia van a «% de lectura» y los de offset a «% de rango»; cada término entra como coeficiente de temperatura × ΔT, más la deriva con el tiempo, y se suman en cuadratura (§2)</td><td>Nuestra tabla de §8 mezcla «sin calibrar» y «tras calibrar» sin decir a qué temperatura ni durante cuánto tiempo (P35)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>La INL cuenta como offset</td><td>«Como no se sabe dónde cae su pico», la INL del ADC va al término de rango (§2)</td><td>La INL del ADC5 es de {K.INL['típica (25 °C)']}–{K.INL['máx. (25 °C, VDDA = VREF+ = 3 V)']} LSB diferenciales: <b>{inl_t:.0f}–{inl_m:.0f} cuentas</b>, no menos de 10 (§5, P36)</td><td>{tg(CRIT,'Corregir H')}</td></tr>
      <tr><td>El 0.1 % de lectura se sostiene</td><td>—</td><td>Con 23 ± 5 °C, la REF3325, resistencias del 0.1 % y 25 ppm/°C y un patrón del 0.05 %, la ganancia suma {K.GAN_RSS['2 V']:.0f}–{K.GAN_RSS['20 V']:.0f} ppm. Queda margen para la deriva de un año sin redes apareadas (§5)</td><td>{tg(OK,'Confirma H')}</td></tr>
      <tr><td>El ruido no es el problema</td><td>El sobremuestreo baja el ruido con √n: 16 veces más muestras dan 4 veces menos ruido (§4)</td><td>Con ×1024, el ruido del ADC5 baja a {K.OFFSET['2 V']['ruido']:.2f} cuentas; manda la INL, no el ruido</td><td>{tg(OK,'Confirma H')}</td></tr>
      <tr><td>Cuatro ensayos para demostrarlo</td><td>Ruido con la entrada en corto, INL con un barrido y calibración de 2 puntos, coeficiente de temperatura a tres temperaturas y estabilidad a 24 h (§4)</td><td>Plantilla para S11 y para el banco del DMM (P37)</td><td>{tg(OK,'Adoptar')}</td></tr>
      <tr><td>La referencia manda en la ganancia</td><td>Con la misma placa, cambiar la referencia lleva el coeficiente de 0.59 a 1.44 ppm/°C y la deriva de 24 h de 0.55 a 9.2 ppm (§4)</td><td>La REF3325 (30 ppm/°C) es nuestro término de ganancia mayor después del patrón</td><td>{tg(OPEN,'Para la síntesis')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><code>research_and_tests/Analog_/achieve-7-pt-5-digits-accuracy-instrumentation-apps-part1.pdf</code> (7 p, teoría y cálculo) y <code>7-5-digit-accuracy-in-instrumentation-apps-part-2.pdf</code> (8 p, medidas). Ambos de 2024, texto extraído con PyMuPDF.</li>
    <li>Todas las cifras de ADI se recalcularon en <code>herramientas/calc_dmm_adi.py</code> y salen iguales, salvo un signo de la ecuación de Arrhenius (§2).</li>
    <li>Para nuestra parte: la tabla 63 (y 64–68) de exactitud del ADC del G473 en <code>datasheet/stm32g473.pdf</code> (DS12712 Rev 5, pp. 138–146); la REF3325 y el OPA2188, de sus páginas en ti.com; y el §8 de <code>01_diseno/dmm_rev21.html</code>.</li>
    <li>No hay circuito que redibujar: la página tiene tablas y no figuras.</li>
  </ul>
"""))

S.append(sec("metodo-adi", "2", "El método, en seis reglas", f"""
  <ol class="tight">
    <li><b>Dos cubos.</b> El offset no depende de la señal y se especifica como «ppm de rango». La ganancia es proporcional a la señal y va como «ppm de lectura». La especificación final es ±(lectura + rango).</li>
    <li><b>La INL va al offset</b>, porque no se sabe en qué parte del rango cae su pico.</li>
    <li><b>Lo absoluto se calibra; lo que cambia con la temperatura y el tiempo, no.</b> Cada término entra como coeficiente × ΔT: ±1 °C para la exactitud de 24 h y ±5 °C para la de un año (23 ± 5 °C).</li>
    <li><b>Suma cuadrática</b> de fuentes independientes. ADI: offset √(0.002² + 0.005² + 0.2² + 0.007²) = {K.OFF_TC:.2f} ppm/°C, y con la INL de 0.9 ppm, {K.OFF_24H:.2f} ppm a 24 h. Ganancia: {K.GAIN_TC:.2f} ppm/°C, que da {K.GAIN_24H:.2f} ppm a 24 h y {K.GAIN_1A_T:.1f} ppm con ±5 °C.</li>
    <li><b>Deriva con el tiempo</b>: crece con √t y se lleva a la temperatura de uso con Arrhenius (Ea = 0.68 eV). Para el LT5400 sale un factor {K.ARRH:.2f} y {K.LT5400_1A:.1f} ppm en un año; para la ADR1001, {K.ADR1001_1A:.0f} ppm. Es el término mayor del año.</li>
    <li><b>Condiciones explícitas</b>: velocidad de lectura (10 o 100 ciclos de red), temperatura, tiempo desde la calibración y coeficiente fuera del intervalo.</li>
  </ol>
  <p class="meta">Corrección al artículo: la ecuación (1) está impresa con el signo cambiado; con ella sale {K.ARRH_SIGNO_IMPRESO:.2f}. El 1.81 del texto, que es el bueno, corresponde a exp(+Ea/k · (1/T_uso − 1/T_ensayo)).</p>
"""))

S.append(sec("cadenas", "3", "La cadena de ADI frente a la nuestra", """
  <div class="tw"><table>
    <thead><tr><th>Bloque</th><th>ADI (7½ dígitos)</th><th>Sección H (4½ dígitos)</th></tr></thead>
    <tbody>
      <tr><td>Entrada</td><td>Buffer de deriva cero (ADA4523-1), alta impedancia</td><td>OPA2188 (deriva cero), detrás del mux</td></tr>
      <tr><td>Escalado</td><td>Red apareada LT5400 (÷4), 1 ppm/°C de seguimiento</td><td>Resistencias del 0.1 % y 25 ppm/°C</td></tr>
      <tr><td>Paso a diferencial</td><td>Amplificador con VCOM = 2.5 V sacado de la referencia</td><td>Driver con VCM = 1.25 V sacado de VREF</td></tr>
      <tr><td>ADC</td><td>AD4630-24, SAR de 24 bits, INL de 0.1 ppm típica</td><td>ADC5 del G473, SAR de 12 bits, INL de 2.1 LSB típica</td></tr>
      <tr><td>Referencia</td><td>ADR1001, Zener enterrado con horno (&lt; 0.2 ppm/°C)</td><td>REF3325 (30 ppm/°C máx.)</td></tr>
      <tr><td>Promedio</td><td>Promediador del ADC (×1024 a ×65 536) y 10 o 100 ciclos de red</td><td>×256 por hardware, ×4 por firmware y un número entero de ciclos de red</td></tr>
    </tbody>
  </table></div>
  <p>La arquitectura es la misma; cambian las piezas, unas 10 000 veces. Por eso el método sirve tal cual: solo hay que cambiar las cifras.</p>
"""))

S.append(sec("medidas", "4", "Lo que midieron (parte 2)", """
  <ul class="tight">
    <li><b>Ruido</b> (entrada en corto, 50 lecturas a 10 ciclos de red): 0.44–0.82 µV rms muestreando a 62.5 kHz y 0.12–0.32 µV rms a 1 MHz. Con 16 veces más muestras por lectura, el ruido baja unas 4 veces, como predice √n. El buffer ADA4523-1 hace menos ruido que el ADA4522.</li>
    <li><b>INL</b>: barrido de ±9 V con una fuente verificada por un DMM de 8½ dígitos y calibración de dos puntos (los extremos). El residuo queda por debajo de 0.2 ppm a 100 ciclos de red y de 0.32 ppm a 10 ciclos: con más ruido empeora la linealidad medida.</li>
    <li><b>Coeficiente de temperatura</b> (0, 23 y 40 °C; entradas de 0, ±5 y ±9 V): ganancia 0.59 ppm/°C y offset 0.017 ppm/°C con la ADR1001.</li>
    <li><b>Estabilidad a 24 h</b>: 0.55 ppm de lectura + 0.07 ppm de rango, dentro de lo que dice el cálculo de la parte 1.</li>
    <li><b>La referencia manda</b>: con la ADR1399, 1.12 ppm/°C y 1.84 ppm en 24 h; con la ADR4550D, 1.44 ppm/°C y 9.2 ppm en 24 h. El offset no cambia con la referencia, porque viene de la red de resistencias.</li>
  </ul>
"""))

inl_rows = "".join(f"<tr><td>{k}</td><td>{K.INL[k]} LSB</td><td>{K.INL[k]*K.LSB_DIFF*1e3:.2f} mV</td><td>{v:.0f}</td><td>{K.INL[k]*K.LSB_DIFF/2*100:.2f} %</td></tr>"
                   for k, v in K.INL_CUENTAS.items())
gan_rows = ""
for r, l in K.GANANCIA.items():
    for i, (f, v) in enumerate(l):
        gan_rows += f"<tr><td>{r if i == 0 else ''}</td><td>{f}</td><td>{v:.0f}</td></tr>"
    gan_rows += f"<tr><td></td><td><b>Suma cuadrática</b> (queda {K.MARGEN_LTD[r]:.0f} ppm para la deriva de un año)</td><td><b>{K.GAN_RSS[r]:.0f}</b></td></tr>"
off_rows = "".join(
    f"<tr><td>{r}</td><td>{inl_t:.0f} / {inl_m:.0f}</td><td>{o['ib']:.1f}</td><td>{o['fuga']:.1f}</td><td>{o['ruido']:.2f}</td><td><b>{o['tip']:.0f} / {o['max']:.0f}</b></td></tr>"
    for r, o in K.OFFSET.items())
S.append(sec("presupuesto", "5", "Nuestro presupuesto, con este método", f"""
  <h3>La INL del ADC5, en cuentas del DMM</h3>
  <p>En diferencial, el ADC5 va de −VREF+ a +VREF+: un LSB vale 2 × 2.5 V / 4096 = {K.LSB_DIFF*1e3:.3f} mV. La sección H fija que una cuenta valga {K.CUENTA*1e6:.0f} µV en el ADC (±19 999 = ±2 V). Con la tabla 63 de la hoja:</p>
  <div class="tw"><table>
    <thead><tr><th>INL diferencial</th><th>LSB</th><th>Tensión</th><th>Cuentas del DMM</th><th>% de 2 V</th></tr></thead>
    <tbody>{inl_rows}</tbody>
  </table></div>
  <p>El §8 de la sección H dice «≈ 0.06 % del fondo» y que las 10 cuentas cubren la no linealidad. Ese 0.06 % es del recorrido de códigos del ADC ({K.H_INL_DICHO_V*1e3:.1f} mV), que en cuentas del DMM son ≈ {K.H_INL_DICHO_V/K.CUENTA:.0f}, no 10. El sobremuestreo no lo arregla: la INL es sistemática y no se promedia. La hoja advierte además que estos valores salen de caracterización, sin ensayo en producción.</p>
  <h3>Ganancia (ppm de lectura), un año, 23 ± 5 °C, tras calibrar a 23 °C</h3>
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Fuente</th><th>ppm</th></tr></thead>
    <tbody>{gan_rows}</tbody>
  </table></div>
  <p class="meta">El patrón de calibración (el multímetro de banco con el que se ajusta) entra entero: aquí se supone del 0.05 %. Falta la deriva anual de la REF3325, que no figura en la página de producto, y la deriva de ganancia del ADC5, que la hoja no especifica: las dos caben en el margen, pero hay que medirlas. Una relación de resistencias del 0.1 % y 25 ppm/°C da como mucho 250 ppm con ±5 °C, así que <b>no hace falta una red apareada</b>.</p>
  <h3>Offset (cuentas), por rango</h3>
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>INL típ. / máx.</th><th>Ib del OPA2188 (850 pA máx.)</th><th>Fuga del 4051 (1 nA, supuesto de H)</th><th>Ruido con ×1024</th><th>Total típ. / máx.</th></tr></thead>
    <tbody>{off_rows}</tbody>
  </table></div>
  <p><b>Resultado</b>: con el ADC5 tal cual, la especificación honesta es <b>±(0.1 % + 30)</b> en condiciones típicas y <b>±(0.1 % + 40)</b> en el peor caso a 25 °C. Para volver a «+10» hay que quitar unas 3/4 partes de la INL, y eso solo se sabe midiéndola (P36).</p>
"""))

S.append(sec("ensayos", "6", "Cómo lo comprobaríamos", """
  <p>Los cuatro ensayos de ADI, a nuestra escala:</p>
  <ol class="tight">
    <li><b>Ruido</b>: entrada en corto, 50 lecturas por rango a 1 y 10 ciclos de red. Criterio: menos de 1 cuenta rms.</li>
    <li><b>INL</b>: barrido de −2 V a +2 V en el ADC (y por cada rango), en ≥ 41 puntos. La fuente se mide a la vez con el mejor multímetro del laboratorio; se calibra con dos puntos y se mira el residuo. Repetirlo en varias placas (criterio de Keneth: ≥ 95 % de placas).</li>
    <li><b>Coeficiente de temperatura</b>: 0 V y ±1.8 V a dos o tres temperaturas (una caja con calefactor basta para 23 → 33 °C). Se separan ganancia y offset.</li>
    <li><b>Estabilidad</b>: las mismas lecturas tras 24 h y tras una semana, para estimar la deriva sin esperar un año.</li>
  </ol>
  <p class="meta">La INL del ensayo 2 también se puede medir antes de tener el DMM: basta la placa del G473 con el ADC5 en diferencial y una fuente estable.</p>
"""))

S.append(sec("propuestas", "7", "Propuestas para la rev 2.1", f"""
  <p>Siguen a P17–P34. <b>Ninguna está aplicada.</b></p>
  <h3>P35 · Presupuesto de errores con el método de ADI {tg(OK,'Adoptar')}</h3>
  <p>Sustituir la tabla del §8 por dos tablas separadas:</p>
  <ul class="tight">
    <li>ganancia en % de lectura: referencia, relaciones de resistencias, ganancia del ADC y patrón de calibración;</li>
    <li>offset en cuentas: INL, ruido, Ib × Rs y fugas.</li>
  </ul>
  <p>Cada término, como coeficiente × ΔT más la deriva, sumado en cuadratura. Hay que declarar las condiciones: un año, 23 ± 5 °C, la velocidad de lectura y el coeficiente fuera del intervalo. Las cifras de §5 de esta página son la primera versión.</p>
  <h3>P36 · El término de cuentas: medir la INL del ADC5 y elegir {tg(WARN,'Decidir')}</h3>
  <p>Con la hoja, la INL vale {inl_t:.0f}–{inl_m:.0f} cuentas: el «+10» de RD-03 / §8 no se cumple. Antes de fijar la especificación, medir la INL del ADC5 en diferencial en el banco (ensayo 2 de §6) en varias placas. Según lo que salga:</p>
  <ol class="tight" type="a">
    <li>especificar ±(0.1 % + 40);</li>
    <li>una tabla de linealización por placa, si la INL es estable con la temperatura y entre lecturas;</li>
    <li>o un ADC ΣΔ externo solo para el DMM, decisión de la síntesis, que también resolvería el riesgo de resolución.</li>
  </ol>
  <h3>P37 · Plan de ensayo del DMM con los cuatro ensayos de ADI {tg(OK,'Adoptar')}</h3>
  <p>Ruido, INL, coeficiente de temperatura y estabilidad (§6), como parte de S11 y del banco del DMM, con el criterio de ≥ 95 % de placas.</p>
"""))

S.append(sec("correcciones", "8", "Correcciones a lo dicho antes", f"""
  <ul class="tight">
    <li><b>Sección H §8</b>: la INL del ADC5 no es «≈ 0.06 % del fondo» cubierto por 10 cuentas, sino {inl_t:.0f}–{inl_m:.0f} cuentas ({K.INL['típica (25 °C)']*K.LSB_DIFF/2*100:.2f}–{K.INL['máx. (25 °C, VDDA = VREF+ = 3 V)']*K.LSB_DIFF/2*100:.2f} % de 2 V). Afecta a la especificación ±(0.1 % + 10) de la hoja del DMM.</li>
    <li><b>Sección H §2</b>: el OPA2188 tiene 160 pA de corriente de polarización <i>típica</i>; la máxima es de 850 pA a 25 °C. En el rango de 200 mV, con los 99 kΩ de R_PROT, eso son {K.OFFSET['200 mV']['ib']:.0f} cuentas.</li>
    <li><b>Artículo de ADI</b>: la ecuación (1) de la parte 1 tiene el signo cambiado (§2).</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("metodo-adi", "2 · El método"),
    ("cadenas", "3 · Su cadena y la nuestra"), ("medidas", "4 · Lo que midieron"), ("presupuesto", "5 · Nuestro presupuesto"),
    ("ensayos", "6 · Cómo comprobarlo"), ("propuestas", "7 · Propuestas P35–P37"), ("correcciones", "8 · Correcciones")])

HTML = (
 '<title>Errores según ADI</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code,a{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 8 de 9</p>\n  <h1>Errores según ADI</h1>\n'
 '  <p class="lede">El método de Analog Devices para el presupuesto de errores de un DMM de 7½ dígitos, aplicado a nuestra sección H. El 0.1 % de lectura se sostiene; el «+10 cuentas» no, por la INL del ADC5.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes: D. Guo y O. Liu, «How to Achieve 7.5-Digit Accuracy in Instrumentation Applications», partes 1 y 2 (Analog Devices, 2024), en <code>research_and_tests/Analog_/</code>; DS12712 Rev 5. Cifras: <code>herramientas/calc_dmm_adi.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
