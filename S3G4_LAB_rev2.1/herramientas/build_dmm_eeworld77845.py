# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/02_referencias/dmm_eeworld77845.html (ficha corta del «STM32 Digital Multimeter» de EEWorld).
No hay esquema: las cifras son pocas y se calculan aqui mismo. Fuente: https://en.eeworld.com.cn/Reference_Designs/detail/77845
(texto, diagrama de bloques, diagrama del software y fotos, leidos en el navegador el 7 oct 2026).
Plantilla: build_dmm_tida01012.py."""
import io
from build_dmm_tida01012 import css, EXTRA, sec, tg, OK, OPEN, WARN, CRIT
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent
OUT = str(R21) + r"/02_referencias/dmm_eeworld77845.html"

# --- Cifras propias ---
VDDA = 3.3                       # STM32F103C8T6 (LQFP48): VREF+ unido a VDDA, que da el LM1117 de 3.3 V
LSB = VDDA / 4096
DIV_MIN = 30 / VDDA              # 0-30 V en 0-3.3 V: atenuacion minima
LSB_30V = LSB * DIV_MIN          # una cuenta en la entrada, sin sobremuestreo
CUENTAS_30V = 30 / LSB_30V
FOTO = (0.5009, 0.5017)          # foto: el DMM marca 0.5009 V y el UT71C 0.5017 V
ERR_FOTO = FOTO[0] / FOTO[1] - 1
RESULTADOS = {"Tensión (0–30 V)": 0.74, "Corriente (0–2 A)": 0.96, "Resistencia (0–100 kΩ)": 0.85}

res_rows = "".join(f"<tr><td>{n}</td><td>±1 %</td><td>{v:.2f} %</td></tr>" for n, v in RESULTADOS.items())

S = []
S.append(sec("resumen", "★", "Lo que nos llevamos", f"""
  <p>Es un multímetro de concurso (Lichuang / LCSC) con un STM32F103C8T6 en una placa «blue pill» y su ADC SAR de 12 bits. Medido contra un UNI-T UT71C, el autor da errores medios por debajo del 1 %. <b>No hay esquema</b>: en la página solo están el texto, dos diagramas, fotos, un vídeo y el binario. Por eso es una ficha corta. Su valor es el <b>límite inferior</b>: lo que da un SAR de 12 bits del MCU con cuidado, pero sin referencia propia, sin sobremuestreo y sin autocero.</p>
  <div class="tw"><table class="lesson">
    <thead><tr><th>Hallazgo</th><th>En el EEWorld 77845</th><th>Para la rev 2.1</th><th>Veredicto</th></tr></thead>
    <tbody>
      <tr><td>≈ 1 % con un SAR de 12 bits</td><td>Errores medios de 0.74 % (V), 0.96 % (I) y 0.85 % (Ω), con resistencias del 0.1 % y un ajuste lineal (§2, §5)</td><td>Nuestro objetivo es ±(0.1 % + 10): hay que ganar un factor 10 con referencia, autocero, buffer y sobremuestreo</td><td>{tg(OPEN,'Para la síntesis')}</td></tr>
      <tr><td>Ajuste lineal por rango contra un patrón</td><td>Lecturas frente a un DMM de 40 000 cuentas y regresión en MATLAB (r = 0.9999981) (§5)</td><td>El mínimo de P26, que pide más puntos</td><td>{tg(OK,'Confirma P26')}</td></tr>
      <tr><td>Tiempo de muestreo máximo</td><td>239.5 ciclos del ADC para que la fuente cargue bien el condensador de muestreo (§5)</td><td>Nosotros lo resolvemos con el driver y el filtro de P20</td><td>{tg(OK,'Confirma P20')}</td></tr>
      <tr><td>Amplificador de corriente solo de lado alto</td><td>MAX4080 (×20): modo común de 4.5 a 76 V y un solo sentido (§4)</td><td>No vale para un borne A cerca de masa; nuestro OPA2188 sí</td><td>{tg(CRIT,'No adoptar')}</td></tr>
      <tr><td>Relés en el camino de la corriente</td><td>Eligen el derivador; su contacto queda en serie (§4)</td><td>Sin conmutadores en la corriente (P19, sección H)</td><td>{tg(CRIT,'No adoptar')}</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("metodo", "1", "Qué hay y cómo se analizó", """
  <ul class="tight">
    <li>Página <a href="https://en.eeworld.com.cn/Reference_Designs/detail/77845">en.eeworld.com.cn/Reference_Designs/detail/77845</a>, leída en el navegador integrado el 7 oct 2026, sin iniciar sesión. Contiene el texto, el diagrama de bloques, el del software y fotos. Los archivos son un vídeo («Lichuang Invitational_1.mp4») y el binario <code>.axf</code>.</li>
    <li>El título del vídeo apunta a un concurso de LCSC/JLC, cuyos proyectos suelen estar en OSHWHub. Busqué en OSHWHub («MAX4080», «数字万用表 MAX4080») y en la web general: el proyecto original no aparece.</li>
    <li>Lo que sigue sale del texto y de los diagramas. Las deducciones sobre piezas concretas se marcan y se apoyan en las hojas de datos.</li>
  </ul>
"""))

S.append(sec("especificacion", "2", "Requisitos y resultados", f"""
  <div class="tw"><table>
    <thead><tr><th>Magnitud</th><th>Requisito</th><th>Error medio medido</th></tr></thead>
    <tbody>{res_rows}</tbody>
  </table></div>
  <ul class="tight">
    <li>El patrón es un UNI-T UT71C (40 000 cuentas, verdadero RMS). Se promediaron 20 lecturas en cada punto.</li>
    <li>En la foto, el DMM marca {FOTO[0]} V y el UT71C {FOTO[1]} V ({ERR_FOTO*100:+.2f} %).</li>
    <li>Solo continua y solo positivos (0–30 V, 0–2 A). La placa se alimenta con +12 V y tiene autorango.</li>
  </ul>
"""))

S.append(sec("arquitectura", "3", "Arquitectura (del diagrama de bloques)", """
  <ul class="tight">
    <li><b>Alimentación</b>: dos LM1117 en cascada, de 12 V a 5 V y de 5 V a 3.3 V.</li>
    <li><b>Tensión</b>: un LM324 en tres caminos (amplificador, atenuador y seguidor) y un CD4052 que elige cuál llega al ADC.</li>
    <li><b>Corriente</b>: un MAX4080 de ganancia 20; los relés eligen el derivador.</li>
    <li><b>Resistencia</b>: un divisor con resistencias de rango que eligen MOSFET, y un buffer.</li>
    <li><b>MCU y resto</b>: STM32F103C8T6, OLED de 1.91″, teclado matricial, puerto serie y SWD. El firmware está hecho con STM32CubeMX y HAL.</li>
  </ul>
"""))

S.append(sec("deducciones", "4", "Lo que se deduce sin esquema", f"""
  <ul class="tight">
    <li><b>Referencia</b>: en el encapsulado de 48 pines del F103, VREF+ está unido a VDDA, así que la referencia es el LM1117 de 3.3 V. Su tolerancia entra entera en la medida, y de ahí el ajuste lineal por unidad.</li>
    <li><b>Resolución</b>: un LSB vale {LSB*1e3:.2f} mV. Para meter 30 V en 3.3 V hay que dividir al menos por {DIV_MIN:.1f}, así que una cuenta vale ≥ {LSB_30V*1e3:.1f} mV en la entrada: unas {CUENTAS_30V:,.0f} cuentas a 30 V (3½ dígitos) sin sobremuestreo.</li>
    <li><b>Corriente</b>: según Analog Devices, el MAX4080 es de lado alto, con un modo común de 4.5 a 76 V y un solo sentido. El derivador tiene que estar al menos 4.5 V por encima de la masa del amplificador, y la corriente solo puede ir en un sentido. Cómo lo resolvieron no se ve sin esquema: <b>NO VERIFICADO</b>. Los relés quedan en serie con el derivador; si no se mide después del contacto, su resistencia entra en la lectura.</li>
    <li><b>Tensión</b>: el LM324 no es carril a carril. Que su salida quepa en los 3.3 V del ADC depende de su alimentación, que no se publica.</li>
  </ul>
"""))

S.append(sec("precision", "5", "Cómo llegan al 1 %", """
  <ol class="tight">
    <li>Resistencias de división del 0.1 %.</li>
    <li>La autocalibración del ADC (<code>HAL_ADCEx_Calibration_Start</code>).</li>
    <li>El tiempo de muestreo máximo (239.5 ciclos), porque la medida no tiene prisa.</li>
    <li>Un filtro de ventana deslizante.</li>
    <li>Un ajuste lineal por rango: lecturas frente al UT71C y regresión en MATLAB (r = 0.9999981).</li>
  </ol>
  <p>Son las técnicas básicas, y dan ≈ 1 %. Faltan las que dan el siguiente factor 10:</p>
  <ul class="tight">
    <li>una referencia propia (nuestro REF3325);</li>
    <li>el autocero en cada lectura (X3 de la sección H);</li>
    <li>el buffer y el driver del ADC;</li>
    <li>el sobremuestreo (×256 + ×4);</li>
    <li>y una calibración de varios puntos guardada en memoria (P26, P29).</li>
  </ul>
"""))

S.append(sec("modulos", "6", "Módulos", """
  <div class="tw"><table>
    <thead><tr><th>Módulo</th><th>Función</th><th>En la rev 2.1</th></tr></thead>
    <tbody>
      <tr><td>«Blue pill» STM32F103C8T6</td><td>MCU y ADC</td><td>STM32G473 en placa</td></tr>
      <tr><td>OLED de 1.91″ y teclado de 4 × 4</td><td>Interfaz</td><td>TFT táctil del ESP32-S3</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("propuestas", "7", "Para la rev 2.1", """
  <p><b>Sin propuestas nuevas.</b> Confirma P20 (muestreo con tiempo suficiente, en nuestro caso con driver) y P26 (ajuste por rango contra un patrón). Para la síntesis deja el dato del límite inferior: ≈ 1 % con un SAR de 12 bits del MCU sin referencia propia.</p>
  <p>Y una advertencia de piezas: un amplificador de corriente solo de lado alto (MAX4080, INA180 y similares de modo común alto) no sirve para el borne A de un DMM con COM a masa.</p>
"""))

S.append(sec("correcciones", "8", "Correcciones a lo dicho antes", """
  <ul class="tight">
    <li>Nada que corregir en el plan: STM32F1, LM324 y CD4052, MAX4080 con relés, MOSFET en ohmios y ≈ 1 % medido se confirman. El proyecto original no aparece en OSHWHub, así que se queda en ficha corta.</li>
  </ul>
"""))

TOC = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in [
    ("resumen", "Lo que nos llevamos"), ("metodo", "1 · Qué hay"), ("especificacion", "2 · Requisitos y resultados"),
    ("arquitectura", "3 · Arquitectura"), ("deducciones", "4 · Lo que se deduce"), ("precision", "5 · Cómo llegan al 1 %"),
    ("modulos", "6 · Módulos"), ("propuestas", "7 · Para la rev 2.1"), ("correcciones", "8 · Correcciones")])

HTML = (
 '<title>Ficha del EEWorld 77845</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + 'code,a{overflow-wrap:anywhere}\n</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · referencia para el DMM de la rev 2.1 · 7 de 9 · ficha corta</p>\n  <h1>Ficha del EEWorld 77845</h1>\n'
 '  <p class="lede">Un multímetro con el ADC de 12 bits de un STM32F103 que llega a ≈ 1 % con técnicas básicas. Sin esquema publicado: sirve como límite inferior de lo que se consigue con el ADC del MCU.</p>\n'
 f'  <ul class="toc">{TOC}</ul>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Análisis de Claude Code, 7 oct 2026, según <code>06_plan/PLAN_REFERENCIAS_DMM.md</code>. Fuente: '
 '<a href="https://en.eeworld.com.cn/Reference_Designs/detail/77845">EEWorld, Reference Design 77845</a>. Cifras en <code>herramientas/build_dmm_eeworld77845.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
