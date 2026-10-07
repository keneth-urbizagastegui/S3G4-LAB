# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_martin.html (anatomia del Open Source Multimeter de Martin).
Cifras: calc_dmm_martin.py. Dibujos: draw_dmm_martin.py. Plantilla: build_dmm_tida01012.py."""
import io, draw_dmm_martin as D, calc_dmm_martin as K
from build_dmm_tida01012 import css, EXTRA, sec, fig, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_martin.html"

def pct(x, d=1):
    return "≈ 0 %" if abs(x) * 100 < 0.5 * 10**-d else f"{x*100:+.{d}f} %".replace("-", "−")
def volt(v):
    return (f"{v*1e3:.3g} mV" if abs(v) < 1 else f"{v:.3g} V").replace("-", "−")
def fino(v):
    return f"{v*1e3:.3g} mV" if v >= 1e-3 else f"{v*1e6:.3g} µV"

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>El multímetro de Martin (embedblog.eu, rev 1.5 de 2019) mide con los <b>ADC ΣΔ de 16 bits</b> del STM32F373: uno para la tensión y otro para la corriente, sincronizados. Lo alimenta una sola batería a 3 V, y para medir negativos lleva el borne COM a VREF/2 = 0.9 V. Está todo publicado (EAGLE, BOM y firmware) y sin módulos analógicos, así que se puede leer pieza a pieza. Lo que más enseña son cuatro errores que se pueden cuantificar.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el diseño de Martin</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>Patas del divisor conmutadas a COM</td><td>1 MΩ arriba y patas de 15 kΩ o 150 kΩ que un 74LVC1G3157 une a COM; otro conmutador en serie da el camino directo de los rangos bajos (§4)</td><td>Cuarto diseño con la idea de P17</td><td>{tg(OK,'Confirma P17')}</td></tr>
      <tr><td>Derivadores siempre en serie</td><td>La corriente pasa por 50 + 5 mΩ; un conmutador solo elige qué toma lee el INA199 (§5)</td><td>Ningún conmutador en el camino de la corriente, como en P19 y en la sección H</td><td>{tg(OK,'Confirma P19')}</td></tr>
      <tr><td>Referencia de corriente lejos del derivador</td><td>IN− del INA199 va a VREF/2 y no al pie de R9. Con 60 V en la entrada de tensión, la corriente del divisor que vuelve por el conmutador de COM falsea la corriente en un {K.ERR_CRUCE['250 mA']/0.25*100:.1f}–{K.ERR_CRUCE['2.5 A']/2.5*100:.1f} % del fondo (§5)</td><td>Es justo lo que evita P27: sentido Kelvin en el derivador y punto estrella en el borne COM</td><td>{tg(WARN,'Refuerza P27')}</td></tr>
      <tr><td>RMS con el offset sumado después de la raíz</td><td>Con la entrada en cortocircuito, el rango de 60 mV marca {K.RMS_CERO[3]*1e3:.1f} mV RMS, y 10 mV RMS se leen como {K.RMS_10mV*1e3:.1f} mV (§7)</td><td>El offset se resta muestra a muestra, o la continua se resta en cuadratura (P21)</td><td>{tg(WARN,'Refuerza P21')}</td></tr>
      <tr><td>Calibración de dos puntos en EEPROM</td><td>Ganancia y offset por rango en un AT24C02; un firmware aparte, con las constantes en el código, la escribe (§7)</td><td>La calibración debe poder escribirse desde S3G4-UI, sin cambiar de firmware (P29)</td><td>{tg(OK,'Refuerza P29')}</td></tr>
      <tr><td>V e I a la vez</td><td>Dos ΣΔ sincronizados, pero la potencia se calcula como |V̄·Ī| o Vrms·Irms (aparente) (§7)</td><td>No es requisito; nuestro ADC5 pasa por un mux y no mide V e I a la vez</td><td>{tg(OPEN,'Idea')}</td></tr>
      <tr><td>Promedio de 25 000 muestras de 16 bits</td><td>Una lectura cada 0.5 s con todo lo que da el ΣΔ en ese tiempo (§6)</td><td>El G473 no tiene ΣΔ: dato para el riesgo de resolución de la síntesis</td><td>{tg(OPEN,'Para la síntesis')}</td></tr>
      <tr><td>COM a media alimentación, rangos manuales, bornes sin proteger</td><td>Funciona porque todo es flotante y de baja tensión (§9, §10)</td><td>Masa común (RD-05), autorango (RD-09) y RD-10</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué se analizó y cómo", """
  <ul class="tight">
    <li><b>Repositorio</b> <code>research_and_tests/Martin_STM32_multimeter/</code> (GitHub, último commit del 6 ene 2021). Es la rev 1.5 «estable», con el esquema fechado el 29 sep 2019.</li>
    <li><b>Esquema</b>: <code>hardware/v15.sch</code> de EAGLE, leído como XML (piezas, valores y la red de cada pin), y los dos PNG del esquema para la vista. También la placa del aislador USB (<code>V15_USB_isolator.sch</code>) y el BOM (<code>v15_BOM.txt</code>).</li>
    <li><b>Firmware</b> (<code>firmware-multimeter/</code>, Keil, registros directos): <code>config.h</code>, <code>sdadc.cpp</code>, <code>interrupt.cpp</code>, <code>draw.cpp</code>, <code>ctest.cpp</code> y <code>adc.cpp</code>. Además, el firmware de calibración y su hoja de cálculo (<code>firmware-calibration/</code>).</li>
    <li><b>Hojas de datos</b>: las páginas de TI del INA199 (ganancias, offset y error de ganancia) y del SN74LVC1G3157 (Ron), y la de ST del STM32F373. El fondo diferencial del SDADC (±VREFSD+/2) es del manual de referencia; la calibración de §7 lo confirma.</li>
    <li>Cálculos en <code>herramientas/calc_dmm_martin.py</code>; redibujos en <code>draw_dmm_martin.py</code> (0 solapes, revisados a la vista).</li>
  </ul>
"""))

cal_rows = "".join(
    f"<tr><td>{c['rango']}</td><td>{fino(c['nominal'])}</td><td>{fino(c['real'])}</td><td>{pct(c['razon']-1)}</td>"
    f"<td>{volt(c['offset'])}</td><td>{pct(c['offset_fs'], 2)}</td></tr>" for c in K.CAL_V)
S.append(sec("especificacion", "2", "Lo que dice el autor y lo que dice su calibración", f"""
  <div class="tw"><table>
    <thead><tr><th>Función</th><th>Alcance (README, rev 1.5)</th></tr></thead>
    <tbody>
      <tr><td>Tensión</td><td>±60 V, ±6 V, ±600 mV y ±60 mV; continua o RMS</td></tr>
      <tr><td>Corriente</td><td>±250 mA y ±2500 mA; continua o RMS</td></tr>
      <tr><td>Potencia</td><td>Tensión y corriente a la vez, y su producto</td></tr>
      <tr><td>Continuidad</td><td>Resistencia y caída de tensión</td></tr>
      <tr><td>Otros</td><td>Prueba de componentes, frecuencia hasta 10 MHz, puerto serie aislado, EEPROM, carga por USB y retención</td></tr>
    </tbody>
  </table></div>
  <p>No publica la exactitud. Lo que sí está es la <b>calibración de una unidad</b>, con las constantes en el firmware de calibración. Comparada con lo nominal (1 MΩ y patas exactas, ±0.9 V en 32 768 cuentas):</p>
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Nominal por cuenta</th><th>Calibrado por cuenta</th><th>Diferencia</th><th>Offset</th><th>Offset / fondo</th></tr></thead>
    <tbody>{cal_rows}</tbody>
  </table></div>
  <p class="meta">Los cuatro rangos salen entre un 3.1 % y un 3.9 % por debajo de lo nominal. Es un error común de la referencia o del SDADC, no del divisor, y confirma el fondo de ±0.9 V: con ±1.8 V, la razón sería ≈ 0.48. El offset del rango de 60 mV (2.1 mV) es un 3.5 % del fondo; no hay autocero que lo siga con la temperatura.</p>
"""))

S.append(sec("arquitectura", "3", "Arquitectura", """
  <ul class="tight">
    <li><b>Cuatro bornes</b>: V (P2), COM (P1), A (P3) y un cuarto (P4) para continuidad, componentes y frecuencia.</li>
    <li><b>Tensión</b>: divisor de 1 MΩ con patas conmutadas, seguidor MCP6072 y SDADC2 en diferencial frente a VREF/2.</li>
    <li><b>Corriente</b>: 50 + 5 mΩ en serie, un conmutador de toma, INA199 con REF = VREF/2 y SDADC1, sincronizado con el SDADC2.</li>
    <li><b>Referencia</b>: MCP1501 de 1.8 V en VREFSD+, y VREF/2 = 0.9 V con dos resistencias de 1 kΩ y el otro amplificador del MCP6072.</li>
    <li><b>COM</b> va a VREF/2 por un 74LVC1G3157 (IC2); el firmware lo baja a AGND en continuidad.</li>
    <li><b>MCU y resto</b>: STM32F373CCT6 a 72 MHz, pantalla Nokia 5110, AT24C02, zumbador, LED RGB y cuatro botones. Una placa aparte aísla el puerto serie USB.</li>
  </ul>
"""))

rng_rows = "".join(
    f"<tr><td>{n}</td><td>{'÷%.2f' % d['k'] if d['k'] > 1 else 'directo'}</td><td>×{d['g']}</td><td>±{volt(d['fondo'])}</td>"
    f"<td>{fino(d['lsb'])}</td><td>{'%.3g MΩ' % (d['zin']/1e6) if d['zin'] < 1e9 else 'la del seguidor (GΩ)'}</td></tr>"
    for n, d in K.DIV.items())
S.append(sec("tension", "4", "Tensión: divisor de 1 MΩ y COM a VREF/2", f"""
{fig(D.tension(), "Redibujo de la etapa de tensión de la rev 1.5. Los conmutadores son 74LVC1G3157 (A con la orden baja, B con la orden alta).")}
  <div class="tw"><table>
    <thead><tr><th>Rango</th><th>Divisor</th><th>Ganancia del SDADC</th><th>Fondo</th><th>Una cuenta en la entrada</th><th>Impedancia de entrada</th></tr></thead>
    <tbody>{rng_rows}</tbody>
  </table></div>
  <ul class="tight">
    <li><b>Patas conmutadas</b>: IC3 une a COM la pata de 15 kΩ o la de 150 kΩ desde la toma. Su Ron (≈ {K.RON_3157:g} Ω) pesa un {K.RON_3157/15e3*100:.2f} % en la pata de 15 kΩ y se calibra. Es la idea de P17, con 1 MΩ arriba en lugar de 10 MΩ.</li>
    <li><b>Camino directo</b>: en 600 mV y 60 mV, IC7 e IC8 llevan la entrada al seguidor por R12, que hace de limitador (60 V / 1 MΩ = 60 µA).</li>
    <li><b>COM a 0.9 V</b>: con una sola alimentación de 3 V, el SDADC en diferencial mide la toma frente a VREF/2, y COM está en VREF/2. Con −60 V, la toma queda a {K.V_TOMA_MENOS60*1e3:.0f} mV sobre AGND, al límite de lo que saca un amplificador carril a carril.</li>
    <li><b>Sujeción</b>: solo D4 hacia 3 V. Hacia abajo protegen los diodos internos de los conmutadores, con la corriente limitada por R12.</li>
    <li><b>Compensación sin definir</b>: C17, C18 y C20 están como «TBD» en el esquema y en el BOM, así que la respuesta en alterna de los rangos divididos depende de las parásitas.</li>
  </ul>
"""))

fi_rows = "".join(
    f"<tr><td>×{g}</td><td>{d['2.5 A']:.2f} A</td><td>{d['250 mA']*1e3:.0f} mA</td><td>{tg(OK,'Sí') if d['2.5 A'] >= 2.5 and d['250 mA'] >= 0.25 else tg(CRIT,'No')}</td></tr>"
    for g, d in K.FONDO_I.items())
S.append(sec("corriente", "5", "Corriente: derivadores en serie e INA199", f"""
{fig(D.corriente(), "Redibujo de la etapa de corriente. IC2 es el mismo conmutador de COM de la figura anterior.")}
  <ul class="tight">
    <li><b>Sin conmutar la corriente</b>: siempre pasa por R10 + R9 (55 mΩ, {K.CAIDA_2A5*1e3:.0f} mV a 2.5 A más el fusible). IC4 lleva al INA199 la toma de R9 (rango de 2.5 A) o la de R9 + R10 (rango de 250 mA).</li>
    <li><b>Variante del INA199</b>: no figura ni en el esquema ni en el BOM. Solo la de ganancia 50 alcanza los fondos anunciados con ±0.9 V:</li>
  </ul>
  <div class="tw"><table>
    <thead><tr><th>Ganancia</th><th>Fondo (toma de 5 mΩ)</th><th>Fondo (toma de 55 mΩ)</th><th>¿Llega a 2.5 A y 250 mA?</th></tr></thead>
    <tbody>{fi_rows}</tbody>
  </table></div>
  <p>Las constantes de calibración de corriente del firmware dan fondos de {K.FONDO_I_CAL[0]:.2f} A y {K.FONDO_I_CAL[1]*1e3:.0f} mA, que no cuadran con ninguna variante. Pueden ser de otra unidad o de otra revisión: <b>NO VERIFICADO</b>.</p>
  <ul class="tight">
    <li><b>Offset</b>: los ±150 µV máximos del INA199 equivalen a {K.ERR_VOS['2.5 A']*1e3:.0f} mA en la toma de 5 mΩ y a {K.ERR_VOS['250 mA']*1e3:.1f} mA en la de 55 mΩ (≈ 1.2 % del fondo). La calibración los resta.</li>
    <li><b>Cruce de tensión a corriente</b>: IN− va a la red VREF/2, y COM está unido a VREF/2 por el Ron de IC2. En modo potencia, con 60 V en la entrada de tensión, los {K.I_DIV_60V*1e6:.0f} µA del divisor vuelven por IC2 y separan COM de VREF/2 en {K.DV_CRUCE*1e3:.2f} mV. Eso aparece como {K.ERR_CRUCE['2.5 A']*1e3:.0f} mA falsos en el rango de 2.5 A y {K.ERR_CRUCE['250 mA']*1e3:.1f} mA en el de 250 mA. Es una cuenta con el Ron típico: <b>NO VERIFICADO</b> en placa.</li>
    <li><b>Sujeción</b>: D2 y D3 llevan el lado del fusible a AGND y a 3 V. Con la red en el borne A, el fusible (de vidrio, en un portafusibles SHK20L) debe abrir antes de que se dañen los diodos.</li>
  </ul>
"""))

S.append(sec("adc", "6", "ADC: el ΣΔ del F373 y la adquisición", f"""
  <ul class="tight">
    <li>SDADC1 (corriente, canal 6) y SDADC2 (tensión, canal 8) arrancan juntos y convierten en continuo, en modo rápido. El reloj es de 72 MHz / 12 = {K.F_SDADC/1e6:.0f} MHz, que da ≈ {K.SPS/1e3:.0f} kSa/s por canal según el manual (<b>NO VERIFICADO</b> en placa).</li>
    <li>El DMA mueve bloques de 1000 pares. La interrupción acumula la suma y la suma de cuadrados, y cada 0.5 s (TIM3) se calculan la media o el RMS de ≈ {K.MUESTRAS:,.0f} muestras.</li>
    <li>Una cuenta vale {K.LSB_ADC*1e6:.1f} µV a la entrada del SDADC. Todas sus entradas llegan con buffer (el seguidor, el INA199 y el seguidor de VREF/2), así que la carga del ΣΔ no toca el divisor.</li>
    <li><b>Para nuestro riesgo de resolución</b>: Martin tiene un ADC de 16 bits y promedia 25 000 muestras, y aun así necesita calibrar offsets del 3.5 % del fondo en el rango más bajo. Nosotros partimos de un SAR de 12 bits. El ΣΔ no es una opción: el G473 no lo tiene.</li>
  </ul>
"""))

S.append(sec("firmware", "7", "Firmware", f"""
  <ul class="tight">
    <li><b>Rangos manuales</b>: un botón recorre los rangos; otros, el modo, la continua o RMS y la retención. El estado se guarda en los registros de respaldo del RTC, que se alimentan aparte, y sobrevive a un reinicio.</li>
    <li><b>Calibración</b>:
      <ul class="tight">
        <li>ganancia y offset por rango (4 en tensión y 2 en corriente), como números en coma flotante en un AT24C02, con un byte de marca;</li>
        <li>las calcula una hoja de cálculo a partir de dos puntos;</li>
        <li>y las escribe un <b>firmware aparte</b> con las constantes en el código.</li>
      </ul></li>
    <li><b>RMS mal corregido</b>: hace la raíz de la media de las cuentas al cuadrado y <i>después</i> aplica la ganancia y suma el offset. Con el offset del rango de 60 mV:
      <ul class="tight">
        <li>la entrada en cortocircuito marca {K.RMS_CERO[3]*1e3:.1f} mV (en 600 mV, {K.RMS_CERO[2]*1e3:.2f} mV);</li>
        <li>10 mV RMS se leen como {K.RMS_10mV*1e3:.1f} mV, y 50 mV como {K.RMS_50mV*1e3:.1f} mV.</li>
      </ul>
      En los rangos de 60 V y 6 V el error se anula por casualidad, porque ahí el offset es negativo. Además, el RMS incluye la continua.</li>
    <li><b>Potencia</b>: |V̄ · Ī| en continua, o Vrms · Irms. Lo segundo es potencia aparente, aunque las muestras son simultáneas y la potencia activa sería la media de v·i.</li>
  </ul>
"""))

S.append(sec("auxiliares", "8", "Continuidad, componentes y frecuencia", f"""
  <ul class="tight">
    <li><b>Continuidad</b>: IC2 baja COM a AGND, PA5 pone 3 V en P4 a través de 220 Ω y el ADC SAR de 12 bits lee P4 por PA1. El firmware suma 23 Ω por la salida del GPIO (<code>IO_COMPENSATION</code>). Como el GPIO y la referencia del ADC salen del mismo 3 V, la fórmula queda R = 243 Ω · código / (4096 − código): <b>es ratiométrica sin proponérselo</b>.
      <ul class="tight">
        <li>Hasta {K.I_CONT_MAX*1e3:.1f} mA de prueba; en 50 Ω, {K.OHM_POR_CUENTA_50:.3f} Ω por cuenta.</li>
        <li>Zumba por debajo de 50 Ω, pero refresca a 10 Hz: hasta 100 ms de retardo. Nuestro COMP7 de la sección H responde en menos de 1 ms.</li>
      </ul></li>
    <li><b>Componentes</b> (estilo «transistor tester»): dos nodos, TP1A y TP2A, cada uno con tres resistencias a GPIO (220 Ω, 2.2 kΩ y 220 kΩ).
      <ul class="tight">
        <li>Resistencia: divisor con 2.2 kΩ en los dos sentidos.</li>
        <li>Diodo: si las dos medidas difieren más de un 25 %.</li>
        <li>Condensador: el tiempo hasta el 63 % con 2.2 kΩ.</li>
      </ul></li>
    <li><b>Frecuencia</b>: PA5 pasa a ser la entrada de reloj externo (ETR) de TIM2 y cuenta flancos durante 0.5 s, con 2 Hz de resolución. Solo sirve para señales lógicas de 0–3 V que entren por P4 y R22.</li>
  </ul>
"""))

S.append(sec("alimentacion", "9", "Alimentación y aislamiento", """
  <ul class="tight">
    <li><b>Alimentación</b>: una batería Li-ion por el conector PWR, el LDO MCP1700 a 3.0 V (que también alimenta el RTC) y un divisor 10 k / 10 k para medir la batería.</li>
    <li><b>Placa del aislador USB</b>:
      <ul class="tight">
        <li>un CH330 (USB a serie) con dos optoacopladores PC817 aísla los datos;</li>
        <li>un TP4056 con un DW01 carga y protege la batería;</li>
        <li>un conmutador doble une el USB con el lado del cargador. Mientras carga, el aislamiento queda puenteado.</li>
      </ul>
      Es el mismo compromiso que nuestro riesgo de lazos de masa con USB: aislado para datos, no para cargar.</li>
  </ul>
"""))

S.append(sec("seguridad", "10", "Seguridad: qué aguanta y qué no", """
  <ul class="tight">
    <li><b>V</b>: R12 de 1 MΩ en 1206 (unos 200 V de tensión de trabajo típica) y D4. Con 230 Vrms, la resistencia ve 325 V de pico: fuera de su especificación, aunque la corriente sea de 0.33 mA.</li>
    <li><b>A</b>: fusible de vidrio de 2.5 A rápido, sin poder de corte de alta capacidad, y dos diodos MiniMELF de pequeña señal.</li>
    <li><b>P4</b>: va directo a PA1, y a PA3, PA4 y PA5 a través de 220 kΩ, 2.2 kΩ y 220 Ω. Ninguna protección.</li>
    <li>El autor declara ±60 V como máximo; no hay ninguna categoría de medida.</li>
  </ul>
"""))

S.append(sec("no-copiar", "11", "Lo que no conviene copiar", """
  <ul class="tight">
    <li>La referencia del amplificador de corriente tomada lejos del derivador.</li>
    <li>El offset aplicado después de la raíz en el RMS.</li>
    <li>La calibración escrita por un firmware aparte con las constantes compiladas.</li>
    <li>Los condensadores de compensación sin definir («TBD»).</li>
    <li>COM a media alimentación: exige aislar todo y choca con RD-05.</li>
    <li>Rangos solo manuales y sin autocero.</li>
    <li>Un cuarto borne conectado directamente a pines del MCU.</li>
    <li>1 MΩ de entrada: carga diez veces más el circuito que los 10 MΩ habituales.</li>
  </ul>
"""))

S.append(sec("modulos", "12", "Módulos", """
  <p>Solo la pantalla Nokia 5110 y la placa del aislador USB, que es del propio autor. El MCU, el ADC, la referencia y todo el front-end están en la placa: es la referencia más «discreta» después de los TIDA.</p>
"""))

S.append(sec("comparacion", "13", "Comparación con las otras referencias y la sección H", """
  <div class="tw"><table>
    <thead><tr><th>Aspecto</th><th>Martin</th><th>Micro-DMM</th><th>TIDA-01012</th><th>Sección H</th></tr></thead>
    <tbody>
      <tr><td>ADC</td><td>ΣΔ 16 bits del MCU (F373)</td><td>ADS1115 (ΣΔ 16 bits)</td><td>SAR 18 bits externo</td><td>SAR 12 bits del G473, sobremuestreado</td></tr>
      <tr><td>Entrada de tensión</td><td>1 MΩ + patas a COM</td><td>2 × 0.5 MΩ, puente</td><td>10 MΩ + patas</td><td>Tomas fijas (P17 en estudio)</td></tr>
      <tr><td>Corriente</td><td>55 mΩ en serie, toma elegida, INA199</td><td>Módulo externo</td><td>Dos derivadores, fuerza y sentido</td><td>0.1 Ω + OPA2188</td></tr>
      <tr><td>Alimentación del front-end</td><td>3 V, COM a 0.9 V</td><td>5 V aislado</td><td>3.3 V, COM a 1.35 V</td><td>±4.9 V, COM a masa</td></tr>
      <tr><td>Calibración</td><td>2 puntos por rango, EEPROM</td><td>15 tramos, en el código</td><td>3 puntos y regresión</td><td>Ganancia y offset por rango</td></tr>
      <tr><td>Rango</td><td>Manual</td><td>Automático</td><td>Automático</td><td>Automático (RD-09)</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "14", "Propuestas para la rev 2.1", """
  <p><b>No añade propuestas nuevas.</b> Refuerza cinco de las anteriores con cifras:</p>
  <ul class="tight">
    <li><b>P17</b>: cuarta referencia que conmuta las patas desde la toma.</li>
    <li><b>P19</b>: la corriente no pasa por ningún conmutador; se elige la toma.</li>
    <li><b>P21</b>: el offset y la continua se quitan antes de la raíz (el error de §7 llega al 23 %).</li>
    <li><b>P27</b>: el amplificador de corriente debe medir en los dos extremos del derivador, con el punto estrella en el borne COM. El cruce de §5 llega al 2.8 % del fondo.</li>
    <li><b>P29</b>: la calibración se guarda como datos que S3G4-UI puede escribir, no en un firmware aparte.</li>
  </ul>
  <p class="meta">Para la síntesis: la medida de potencia (V e I a la vez) no es requisito y nuestro mux no la permite. Si algún día se quisiera, el DMM y un canal del osciloscopio podrían medir a la vez.</p>
"""))

S.append(sec("correcciones", "15", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>La tabla del plan describía a R8 como «STM32F1 con su ADC interno… lo más cercano a nosotros en microcontrolador». La rev 1.5 usa el <b>STM32F373 y su ΣΔ de 16 bits</b> (el propio README avisa del cambio), que el G473 no tiene. En tipo de ADC, la más cercana es la ficha del EEWorld 77845 (SAR de 12 bits del F103).</li>
    <li>El README dice «2 kB EEPROM»: el AT24C02 tiene 2 kbit (256 bytes).</li>
    <li>Los comentarios de <code>sdadc.cpp</code> intercambian los canales; el código es correcto: SDADC1, canal 6, mide la corriente y SDADC2, canal 8, la tensión.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué se analizó"), ("especificacion", "2 · Especificación y calibración"),
    ("arquitectura", "3 · Arquitectura"), ("tension", "4 · Tensión"), ("corriente", "5 · Corriente"), ("adc", "6 · ADC ΣΔ"),
    ("firmware", "7 · Firmware"), ("auxiliares", "8 · Continuidad, componentes y frecuencia"), ("alimentacion", "9 · Alimentación"),
    ("seguridad", "10 · Seguridad"), ("no-copiar", "11 · Lo que no conviene copiar"), ("modulos", "12 · Módulos"),
    ("comparacion", "13 · Comparación"), ("propuestas", "14 · Propuestas"), ("correcciones", "15 · Correcciones")])

HTML = (
 '<title>Anatomía del DMM de Martin</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 6 de 9</p>\n  <h1>Anatomía del DMM de Martin</h1>\n'
 '  <p class="lede">Un multímetro abierto con los ΣΔ de 16 bits del STM32F373, alimentado a 3 V y con el COM a 0.9 V. Confirma varias ideas nuestras y deja cuatro errores medibles que conviene no repetir.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuentes en <code>research_and_tests/Martin_STM32_multimeter/</code>; artículo del autor: '
 '<a href="http://embedblog.eu/?p=438">embedblog.eu/?p=438</a>. Cifras: <code>herramientas/calc_dmm_martin.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
