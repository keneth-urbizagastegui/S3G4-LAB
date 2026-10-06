# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html: requisitos funcionales acordados con Keneth el 23 sep 2026."""
import io
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/00_requisitos/requisitos_osciloscopio.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css
EXTRA = """
.meta{color:var(--muted);font-size:13px}
.src{color:var(--muted);font-size:12.5px}
.tri{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin:14px 0}
.tri div{border:1px solid var(--rule);border-radius:8px;padding:12px 14px;background:var(--paper)}
.tri h3{margin:0 0 6px;font-size:15px}
.tri ul{margin:0;padding-left:18px;font-size:14px}
td.id{font-family:"IBM Plex Mono",monospace;white-space:nowrap;font-weight:500}
"""
# Cada muestra: 3 canales x 8192 muestras x 2 bytes
RAM_BYTES = 3 * 8192 * 2
RAM_G473 = 128 * 1024

def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def tag(c, t): return f'<span class="tag {c}">{t}</span>'
OK, NEW = tag("t-ok", "Acordado"), tag("t-ok", "Acordado hoy")

RF = [
 ("RF-01", "Canales", "3 canales simultáneos", "D-01", OK),
 ("RF-02", "Muestreo", "CH1 a 6.5 MSa/s (ADC1 + ADC2 entrelazados sobre PA0); CH2 y CH3 a 3.47 MSa/s (ADC3 y ADC4)", "D-02", OK),
 ("RF-03", "Ancho de banda (−3 dB)", "CH1 ≈ 2 MHz; CH2 y CH3 ≈ 1 MHz", "Respuesta de Keneth", NEW),
 ("RF-04", "Escalas", "De 5 mV/div a 20 V/div en 12 pasos (secuencia 1-2-5); fondo de escala ±40 V en la BNC", "D-05 + P1 (2 oct)", OK),
 ("RF-05", "Acoplo", "AC / DC / GND con conmutador deslizante; corte del acoplo AC ≤ 10 Hz", "D-04 + respuesta", NEW),
 ("RF-06", "Entrada máxima", "50 Vpk declarados; sin daño con ±100 V en cualquier escala, también apagado, y ESD de ±8 kV en aire y ±4 kV en contacto. Ya no se diseña para la red; el DMM se limita a baja tensión (RD-04)", "D-06 (revisada el 2 oct)", OK),
 ("RF-07", "Sonda ×10", "Lineal hasta ±400 V en la punta: todo el fondo de escala con sonda estándar", "Respuesta de Keneth", NEW),
 ("RF-08", "Impedancia de entrada", "1 MΩ ±2 %; 10–30 pF y ≤ 2 pF de diferencia entre escalas, para compensar la sonda una sola vez", "Respuesta de Keneth", NEW),
 ("RF-09", "Disparo", "Flanco de subida o de bajada en CH1, CH2 o CH3, con nivel, posición e histéresis; modos auto, normal y único", "Respuesta de Keneth", NEW),
 ("RF-10", "Memoria", "8 k muestras por canal en cada captura", "Respuesta de Keneth", NEW),
 ("RF-11", "Base de tiempos", "De 1 µs/div a 50 s/div; interpolación sin(x)/x en las rápidas y roll en las lentas", "Respuesta de Keneth", NEW),
 ("RF-12", "Adquisición", "Normal, único, roll, detección de picos y promedio", "Respuesta de Keneth", NEW),
 ("RF-13", "Análisis", "Medidas automáticas (Vpp, Vrms, media, frecuencia, periodo, ciclo de trabajo, subida y bajada), cursores, FFT, Bode con el AWG, A ± B, A × B y XY", "Respuesta de Keneth", NEW),
 ("RF-14", "Offset vertical", "±5 divisiones en todas las escalas", "Respuesta de Keneth", NEW),
 ("RF-15", "Precisión en continua", "±1 % con autocalibración, sin instrumentos externos", "Respuesta de Keneth", NEW),
 ("RF-16", "Funciones a la vez", "Osciloscopio, AWG y DMM funcionando a la vez, con masa común (sección G.7)", "Respuesta de Keneth", NEW),
 ("RF-17", "Autonomía", "≥ 4 h de uso continuo con las tres funciones y el WiFi activos", "Respuesta de Keneth", NEW),
 ("RF-18", "Gestión de energía", "Apagado por hardware de cada canal y de cada función que no se use", "Respuesta de Keneth", NEW),
 ("RF-19", "Componentes y coste", "Coste relativo, sin tope nuevo. Prioridad: alta disponibilidad y bajo precio en LCSC, con montaje en JLCPCB. Se acepta un equivalente (3PEAK, SGMICRO, etc.) si su hoja de datos cumple las cifras clave del requisito", "Respuesta de Keneth", NEW),
]
rf_rows = "".join(f'<tr><td class="id">{a}</td><td><b>{b}</b></td><td>{c}</td><td class="src">{d}</td><td>{e}</td></tr>' for a, b, c, d, e in RF)

CONS = [
 ("RF-07", "<b>P4, con un relé por canal, es el grueso.</b> P7 da 4.4 % de THD con 200–400 V en la punta y su entrada efectiva cae a 739 kΩ. P7 queda archivado", "Sección C", tag("t-ok", "Consecuencia directa")),
 ("RF-08", "Entrada P4b: réplica de la carga en el segundo polo del relé (R_EQ ∥ C_EQ) y Rt + Rb = 1.109 MΩ. S1: 999.1 kΩ en las dos posiciones y 0.54 pF de diferencia; trimmer por canal para la planitud de ÷100 (S7c: en rango en el 100 % de las placas)", "Sección C.2 + S1, S7c", tag("t-ok", "Resuelto")),
 ("RF-06", "Rama ×1 con 2 × 49.9 kΩ 1206 ∥ 1.2 nF C0G ≥ 200 V, BAV199 a los rieles con una TVS por riel y R_PROT de 1 kΩ delante del buffer. S2 y S2b: ±100 V encendido y apagado y ESD IEC sin daño", "Secciones B y C + S2, S2b", tag("t-ok", "Resuelto")),
 ("RF-03", "CH1: filtro de 6.º orden (dos Sallen-Key con un AD8039, el RC del ADC y la etapa final): 2.0 MHz y 21.7 dB a 4.5 MHz en el 100 % de 500 placas (S5, S7b). CH2 y CH3 a 1 MHz, no a 1.5 MHz (Keneth, 2 oct): S9", "Sección D", tag("t-warn", "CH1 resuelto; CH2/CH3 en S9")),
 ("RF-09", "Disparo con el watchdog de 12 bits (AWD1) de cada ADC y la cadena por hardware P12. CH2 y CH3 en PE9/PE15 no tienen comparador y no lo necesitan; en CH1 el comparador es opcional", "Firmware y mapa de pines", tag("t-ok", "Resuelto sin hardware")),
 ("RF-10", f"3 × 8192 × 2 B = {RAM_BYTES // 1024} KiB de los {RAM_G473 // 1024} KiB de RAM del G473", "Firmware", tag("t-ok", "Cabe")),
 ("RF-11, RF-12", "El G473 hace la decimación con mínimo y máximo (detección de picos) y el promedio. La interfaz interpola sin(x)/x", "Firmware y S3G4-UI", tag("t-open", "Por hacer")),
 ("RF-13", "Se calcula en el ESP32-S3 o en el cliente web. El Bode usa el AWG y dos canales", "S3G4-UI", tag("t-open", "Por hacer")),
 ("RF-14", "DAC del G473 con buffer (PA4–PA6) en la etapa final a 3.3 V (OPA836, P8): +5.2 / −4.85 div, y ±4.5 div tras compensar el offset de cada placa en el 97 % de ellas (S4, S7b). −4.85 div aceptado por Keneth", "Sección E", tag("t-ok", "Resuelto")),
 ("RF-15", "P10 + P16: tabla de calibración por escala con signo (S7b), VCHECK de 12.4 kΩ / 100 Ω al 0.1 % en una entrada libre del 74HC4051, el AWG en continua como fuente y la corrección de ganancia y offset en el propio ADC", "Secciones C y F, y firmware", tag("t-open", "En curso")),
 ("RF-16, RF-17, RF-18", "Sección G: con 5000 mAh, 6.0 h en el peor caso (todo activo, WiFi, pantalla y AWG sobre 50 Ω) y 8.1 h en uso típico. Apagado por canal y por función, y el AWG con su propio convertidor de ±6.5 V", "Sección G (rieles)", tag("t-open", "En curso")),
 ("RF-19", "Cada pieza nueva se busca en LCSC con stock alto. Se anotan el original y el equivalente, con las cifras de la hoja que lo justifican", "Todas", tag("t-ok", "Regla de trabajo")),
]
cons_rows = "".join(f'<tr><td class="id">{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in CONS)

S = []
S.append(sec("triangulo", "★", "El punto del triángulo", """
  <p>Cada requisito sale de una pregunta cruzada con los siete artefactos: el esbozo de la rev 2.0, el documento vivo de la rev 2.1, las anatomías del DSO112, el WAVE2, el OpenScope MZ y black_scope, y la revisión analógica del G473. Donde había una tensión entre prestaciones, coste y energía, eligió Keneth. Esto es lo que quedó en cada vértice:</p>
  <div class="tri">
    <div><h3>Prestaciones</h3><ul><li>CH1 hasta 2 MHz; CH2 y CH3 hasta 1 MHz</li><li>Sonda ×10 hasta ±400 V</li><li>±1 % en continua con autocalibración</li><li>Osciloscopio, AWG y DMM a la vez</li></ul></div>
    <div><h3>Coste</h3><ul><li>3 canales en vez de 4</li><li>Acoplo mecánico, sin relés</li><li>Un relé por canal, sólo para el grueso</li><li>Piezas de LCSC con alta disponibilidad y equivalentes que cumplan</li></ul></div>
    <div><h3>Energía</h3><ul><li>≥ 4 h con todo activo y WiFi</li><li>Apagado por canal y por función</li><li>Relés monoestables con economizador: ≈ 46 mW por relé (TQ2SA-5V-Z) sólo mientras está en ×1</li><li>CPU del G473 más lenta si el firmware cabe (P13)</li></ul></div>
  </div>
"""))

S.append(sec("requisitos", "1", "Requisitos funcionales del osciloscopio", f"""
  <p>Los que ya eran decisiones (D-01 a D-06) se recogen para tener la lista completa. Los demás los fijó Keneth el 23 sep 2026 respondiendo al cuestionario.</p>
  <div class="tw"><table>
    <thead><tr><th>Id</th><th>Tema</th><th>Requisito</th><th>Origen</th><th>Estado</th></tr></thead>
    <tbody>{rf_rows}</tbody>
  </table></div>
  <p><b>Surgió para el DMM:</b> resolución de 16 bits con el ADC5 por sobremuestreo por hardware (P16). La alta resolución no es un modo del osciloscopio.</p>
"""))

S.append(sec("consecuencias", "2", "Qué obliga cada requisito en el diseño", f"""
  <div class="tw"><table>
    <thead><tr><th>Requisito</th><th>Consecuencia</th><th>Dónde</th><th>Estado</th></tr></thead>
    <tbody>{cons_rows}</tbody>
  </table></div>
  <p class="src">Evidencia: simulación P4/P7 de Codex y su auditoría (<code>S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md</code>), <code>S3G4_LAB_rev2.1/02_referencias/g473_analogico.html</code>, <code>S3G4_LAB_rev2.1/02_referencias/analisis_black_scope.html</code> y el documento vivo.</p>
"""))

S.append(sec("verificacion", "3", "Cómo se comprobará cada uno", """
  <div class="tw"><table>
    <thead><tr><th>Requisitos</th><th>En simulación</th><th>En banco</th></tr></thead>
    <tbody>
      <tr><td class="id">RF-03, RF-04</td><td>Respuesta en frecuencia de cada escala (T02)</td><td>Barrido con el AWG y un generador de referencia</td></tr>
      <tr><td class="id">RF-07, RF-08</td><td>T01 y T05 con modelo de sonda ×10</td><td>Salida de compensación de 1 kHz con sonda real en todas las escalas</td></tr>
      <tr><td class="id">RF-06</td><td>S2 y S2b: ±100 V encendido y apagado, ESD IEC de ±4 kV en contacto y ±8 kV en aire</td><td>Ensayo destructivo en una placa de pruebas</td></tr>
      <tr><td class="id">RF-09 a RF-14</td><td>—</td><td>Pruebas de firmware y de la S3G4-UI</td></tr>
      <tr><td class="id">RF-15</td><td>—</td><td>Contra una referencia calibrada, antes y después de autocalibrar</td></tr>
      <tr><td class="id">RF-16 a RF-18</td><td>Presupuesto de energía</td><td>Descarga de la batería con las tres funciones y el WiFi activos (plan de medición de la propuesta de arquitectura, §21)</td></tr>
    </tbody>
  </table></div>
"""))

S.append(sec("abierto", "4", "Lo que queda abierto", """
  <ul class="tight">
    <li><b>Requisitos del DMM y del AWG:</b> acordados el mismo día en <code>S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html</code> (RD-01…RD-10 y RG-01…RG-08).</li>
    <li><b>El tope RE-01 de 120 USD de la tesis</b> no se discutió: RF-19 fija la prioridad (disponibilidad y precio), no una cifra.</li>
    <li><s>Correcciones de P4 para RF-08 y RF-06, y el ajustable.</s> <i>Resueltas con la entrada P4b y el trimmer por canal (S1–S2b, S7c).</i></li>
    <li><s>Orden del filtro anti-alias de CH1.</s> <i>Resuelto: 6.º orden, intermedio (S5).</i> Sigue abierto el reloj de la CPU (P13), que depende del firmware y de RF-17.</li>
    <li><b>CH2 y CH3 a 1 MHz:</b> en simulación (S9).</li>
  </ul>
"""))

HTML = (
 '<title>Requisitos del osciloscopio S3G4</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · AFE rev 2.1 · acordado el 23 sep 2026 · revisado el 4 oct</p>\n  <h1>Requisitos del osciloscopio S3G4</h1>\n'
 '  <p class="lede">Qué debe hacer el osciloscopio, fijado por Keneth pregunta a pregunta y cruzado con los siete artefactos del proyecto. Cada requisito lleva su origen y lo que obliga en el diseño.</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Redacción de Claude Code, 23 sep 2026, a partir de las respuestas de Keneth; revisada el 4 oct con P1, D-06 revisada y las simulaciones de CH1 (S1–S7c, <code>03_simulaciones/CH1_entrada/</code>). Fuentes: <code>ai-context/DECISIONS.md</code>, <code>S3G4_LAB_rev2.1/01_diseno/rediseno_afe_rev21.html</code>, las anatomías de <code>docs/</code> y la simulación de <code>S3G4_LAB_rev2.1/03_simulaciones/P4_P7_grueso/</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML))
