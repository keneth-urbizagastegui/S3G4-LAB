# -*- coding: utf-8 -*-
"""Genera S3G4_LAB_rev2.1/00_requisitos/requisitos_dmm_awg.html: requisitos del DMM y del AWG acordados con Keneth el 23 sep 2026."""
import io
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1

SRC = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
OUT = str(R21) + r"/00_requisitos/requisitos_dmm_awg.html"
base = io.open(SRC, encoding="utf-8").read()
css = base[base.find("<style>") + 7: base.find("</style>")]
assert ".w{" in css
EXTRA = """
.meta{color:var(--muted);font-size:13px}
.src{color:var(--muted);font-size:12.5px}
td.id{font-family:"IBM Plex Mono",monospace;white-space:nowrap;font-weight:500}
"""
# Cifras derivadas
ENOB_DIF = 10.9            # DS12712 T.63, diferencial, tipico
OVS = 1024                 # sobremuestreo maximo del firmware del banco (etapa J1)
BITS_GAIN = 0.5 * (OVS.bit_length() - 1)   # +0.5 bit por cada duplicacion: log4(1024) = 5
LEVELS = 2 ** (ENOB_DIF + BITS_GAIN)       # niveles en todo el tramo diferencial
SHUNT, I_MAX = 0.1, 2.0
V_SHUNT = SHUNT * I_MAX                    # tension en el derivador a fondo de escala
P_SHUNT = SHUNT * I_MAX ** 2               # potencia en el derivador
RAM_SCOPE = 3 * 8192 * 2
RAM_ARB = 2 * 4096 * 2
RAM_TOTAL = 128 * 1024
DDS_FS = 15e6
PHASE_BITS = 32
DDS_RES = DDS_FS / 2 ** PHASE_BITS

def sec(id_, num, title, body, tag=None):
    t = f'<span class="tag {tag[0]}">{tag[1]}</span>' if tag else ""
    return f'<section id="{id_}">\n  <div class="shead"><span class="num">{num}</span><h2>{title}</h2>{t}</div>\n{body}\n</section>\n'
def tag(c, t): return f'<span class="tag {c}">{t}</span>'
NEW = tag("t-ok", "Acordado hoy")
PREV = tag("t-ok", "Acordado")

RD = [
 ("RD-01", "Funciones", "Tensión continua y alterna (verdadero valor eficaz), corriente continua y alterna, resistencia, prueba de diodo y continuidad con zumbador", NEW),
 ("RD-02", "Bornes", "Tres, como el NI ELVIS II: V/Ω, COM y A", NEW),
 ("RD-03", "Resolución", "20 000 cuentas (4½ dígitos), con el ADC5 en diferencial y sobremuestreo: ×256 por hardware (P16, el máximo del G473) y ×4 más en firmware, ×1024 en total. <i>Corregido el 30 sep: decía «por hardware», que sólo llega a ×256</i>", NEW),
 ("RD-04", "Tensión máxima", "Sólo baja tensión: hasta 50 V en continua y 50 Vrms en alterna (≈ 71 Vpk), como el rango de 50 V del TI TIDA-01012 (<code>research_and_tests/tidubv5b (1).pdf</code>, tabla 1, p. 4). El equipo no mide la red. <i>Revisado por Keneth el 30 sep: antes decía 60 V DC / 30 Vrms «como el ELVIS II», que en realidad es 60 V DC / 20 Vrms.</i> Sustituye a CAT II 600 V", tag("t-warn", "Revisado")),
 ("RD-05", "Aislamiento", "Sin aislamiento. El COM es la masa común del equipo: blindaje de las BNC, masa del AWG y USB. La pinza del osciloscopio y el COM van siempre al mismo punto (sección G.7). Sustituye al enclavamiento", tag("t-warn", "Revisado")),
 ("RD-06", "Corriente", "Hasta 2 A con un único derivador, como el ELVIS II, y ganancia conmutada para los rangos bajos. Fusible rápido, como el de 3.15 A del ELVIS: sin la red ya no hace falta uno de 600 V", NEW),
 ("RD-07", "Alterna", "De 40 Hz a 20 kHz en tensión y en corriente", NEW),
 ("RD-08", "Prueba de diodo", "Hasta ~3.5 V: enciende LED de cualquier color", NEW),
 ("RD-09", "Ayudas", "Autorango, relativo, mínimo y máximo, retención, registro en el tiempo con exportación y detección de cable abierto", NEW),
 ("RD-10", "Protección de red", "Ya no aplica: el DMM no mide la red (D-06 revisada). Queda por decidir cuánto debe aguantar si alguien lo conecta por error", tag("t-warn", "Revisado")),
]
RG = [
 ("RG-01", "Canales", "Dos", NEW),
 ("RG-02", "Frecuencia", "Seno de 1 Hz a 1 MHz, con síntesis DDS a frecuencia de actualización fija. Cuadrada, triángulo y rampa con un tiempo de subida de ≈ 175 ns (filtro de 2 MHz), útiles con buena forma hasta 100–200 kHz. <i>Revisado por Keneth el 30 sep: decía 1 MHz en todas las formas</i>", tag("t-warn", "Revisado")),
 ("RG-03", "Amplitud y offset", "Hasta 10 Vpp (±5 V) en vacío, en dos rangos: uno fino, de ~1 Vpp, y uno grueso, de 10 Vpp; offset de ±5 V", NEW),
 ("RG-04", "Salida", "50 Ω y ±50 mA. Soporta un cortocircuito indefinido y ±15 V aplicados desde fuera sin dañarse", NEW),
 ("RG-05", "Formas", "Seno, cuadrada con ciclo de trabajo ajustable, triángulo, rampa y continua. Pulso, PWM, ruido, arbitraria, barrido y AM/FM se pueden añadir después por firmware", NEW),
 ("RG-06", "Arbitraria", "4096 puntos por canal, reservados en RAM", NEW),
 ("RG-07", "Fuentes de continua", "Sin fuentes aparte: el AWG en continua (±5 V, ±50 mA) cubre ese uso y es la fuente de la autocalibración (P10). <b>En conflicto con RG-04:</b> a través de 50 Ω, con 50 mA caen 2.5 V. Se decide al definir los rieles del AWG (30 sep)", tag("t-open", "Por decidir")),
 ("RG-08", "Sincronización", "Interna: el osciloscopio puede disparar con el ciclo del AWG. Sin conector de sincronismo", NEW),
]
def rows(L): return "".join(f'<tr><td class="id">{a}</td><td><b>{b}</b></td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in L)

CONS = [
 ("RD-03", f"En diferencial el ADC5 da ~{ENOB_DIF} bits efectivos; con ×{OVS} gana ~{BITS_GAIN:.0f} bits, unos {LEVELS/1000:.0f} 000 niveles en todo el tramo: caben las ±19 999 cuentas con margen. La exactitud pide una referencia externa (tipo REF3325: 0.15 %, 30 ppm/°C), divisores del 0.1 % de baja deriva y la calibración de P10", "Sección DMM, referencia (F)", tag("t-open", "Por diseñar")),
 ("RD-04, RD-10", "50 Vrms son ≈ 71 Vpk: más que los 50 Vpk del osciloscopio y más que el umbral de 30 Vrms de IEC 61010-1, así que el borne V/Ω lleva tensión peligrosa y necesita aviso en el panel y en el manual. La entrada V/Ω y su protección se dimensionan para 71 Vpk continuos. Distancias de baja tensión en la placa. La protección frente a errores de conexión (resistencia serie, PTC, sujeción) está por decidir", "Sección DMM", tag("t-open", "Por decidir")),
 ("RD-05", "Masa común y sin enclavamiento. Las reglas de uso van en el panel y en el manual (sección G.7). Sin aislamiento, un COM en la fase dejaría con tensión el metal de las BNC y del USB: por eso se renuncia a medir la red", "Panel y manual", tag("t-ok", "Decidido")),
 ("RD-06", f"Derivador de {SHUNT} Ω: {V_SHUNT*1e3:.0f} mV y {P_SHUNT:.1f} W a {I_MAX:.0f} A (pieza de ≥ 1 W). Para los rangos bajos hace falta un amplificador de deriva cero: un error de 10 µV ya son 0.1 mA", "Sección DMM", tag("t-open", "Por diseñar")),
 ("RD-07", "El divisor de ~10 MΩ se compensa para que sea plano hasta 20 kHz. El verdadero valor eficaz ya está en el firmware del banco (etapa J1). Hace falta un filtro anti-alias antes del ADC5 (acta del mapa de pines, H-2)", "Sección DMM", tag("t-open", "Por diseñar")),
 ("RD-08", "Fuente de corriente alimentada desde 5 V. Antes de PB14 hace falta un divisor (≈ ÷2) además de la sujeción: 3.5 V superan VREF+ = 2.5 V y V_DDA (P14), y una sujeción sola recortaría la lectura. <i>Corregido el 30 sep</i>", "Sección DMM", tag("t-open", "Por diseñar")),
 ("RD-09", "La detección de cable abierto necesita una pequeña corriente de prueba en la entrada, como en el Micro-DMM. El resto es firmware y S3G4-UI", "Sección DMM y firmware", tag("t-open", "Por diseñar")),
 ("RG-02", f"DAC3 a {DDS_FS/1e6:.0f} MSa/s pasa por OPAMP6/OPAMP3 en modo de alta velocidad, después por un filtro de reconstrucción de ~2 MHz y después por la etapa de salida. Con un acumulador de fase de {PHASE_BITS} bits la resolución de frecuencia es de {DDS_RES*1e3:.1f} mHz; la exactitud la da el cristal", "Sección AWG", tag("t-open", "Por diseñar")),
 ("RG-03", "Resuelto en la sección G (23 sep): el AWG tiene su propio convertidor de ±6.5 V, así que la etapa de salida dispone de 1.5 V de margen para dar ±5 V. Límite de uso: |offset| + amplitud/2 ≤ 5 V en vacío", "Sección AWG y G", tag("t-ok", "Decidido")),
 ("RG-04", "Con +15 V aplicados y la salida sujetada a +6.5 V, por la resistencia de 50 Ω pasan ≈ 156 mA y se disipan ≈ 1.2 W: hace falta un PTC y sujeción a la salida, y una resistencia que aguante el pulso hasta que el PTC actúe. Con el AWG apagado, la sujeción no puede descargar en un riel sin alimentar (G.6). En cortocircuito, sin límite de corriente, la salida pide 100 mA de pico; los 50 mA de RG-04 obligan a limitar la corriente en la etapa, y G.5 dimensiona el convertidor con ese límite", "Sección AWG", tag("t-open", "Por diseñar")),
 ("RG-06", f"Osciloscopio {RAM_SCOPE//1024} KiB + arbitraria {RAM_ARB//1024} KiB = {(RAM_SCOPE+RAM_ARB)//1024} KiB de los {RAM_TOTAL//1024} KiB de RAM del G473", "Firmware", tag("t-ok", "Cabe")),
 ("RG-01, RG-04", "Calculado en la sección G.3: los dos canales con un seno a fondo sobre 50 Ω gastan 0.68 W de batería (32 mA por riel). Con todo activo, 6.0 h; RF-17 se cumple", "Sección G", tag("t-ok", "Calculado")),
]
cons_rows = "".join(f'<tr><td class="id">{a}</td><td>{b}</td><td>{c}</td><td>{d}</td></tr>' for a, b, c, d in CONS)

S = []
S.append(sec("contexto", "i", "De dónde salen", """
  <p>Dos rondas de preguntas para el DMM y dos para el AWG, igual que con el osciloscopio. Cada pregunta partía de lo que ya existía:</p>
  <ul class="tight">
    <li>El mapa de pines firmado. El DMM va en PD13/PD14 (ADC5 diferencial) y en PB14 (OPAMP5), con zumbador en PA7. El AWG sale de DAC3 por OPAMP6 hacia PB11 y por OPAMP3 hacia PB1.</li>
    <li>El firmware del banco. El DMM ya calcula continua, verdadero valor eficaz, Vpp y frecuencia, con sobremuestreo de ×16 a ×1024. El AWG ya tiene comandos SCPI de 1 Hz a 1 MHz y 512 puntos de forma arbitraria.</li>
    <li>La rev 2.0: cuatro bornes en el DMM y dos rangos de amplitud en el generador.</li>
    <li>Las referencias: el NI ELVIS II para el DMM, el OpenScope para el generador y las fuentes, y el Micro-DMM para la seguridad.</li>
    <li>La revisión del G473 y los requisitos del osciloscopio (RF-01…RF-19, <code>S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html</code>).</li>
  </ul>
"""))
S.append(sec("dmm", "1", "Requisitos del DMM", f"""
  <div class="tw"><table>
    <thead><tr><th>Id</th><th>Tema</th><th>Requisito</th><th>Estado</th></tr></thead>
    <tbody>{rows(RD)}</tbody>
  </table></div>
  <p class="src">Referencia del ELVIS II (<code>research_and_tests/NI ELVIS II Series.pdf</code>): derivador de 0.1 Ω, 2 A en continua, 500 mA o 2 A en alterna, caída menor de 0.6 V, fusible rápido de 3.15 A, alterna de 40 Hz a 20 kHz en tensión y de 40 Hz a 5 kHz en corriente. Su DMM está aislado, pero sólo es CAT I de 60 V DC / 20 Vrms; sus rangos son 100 mV, 1 V, 10 V y 60 V en continua y 200 mV, 2 V y 20 V en alterna.</p>
  <p><b>RD-07, confirmado por Keneth:</b> de 40 Hz a 20 kHz tanto en tensión como en corriente, aunque el ELVIS sólo llega a 5 kHz en corriente.</p>
"""))
S.append(sec("awg", "2", "Requisitos del AWG", f"""
  <div class="tw"><table>
    <thead><tr><th>Id</th><th>Tema</th><th>Requisito</th><th>Estado</th></tr></thead>
    <tbody>{rows(RG)}</tbody>
  </table></div>
  <p><b>Formas de onda y hardware.</b> Las formas que se añadan después (pulso, PWM, ruido, arbitraria, barrido, AM/FM) son firmware sobre el mismo DAC y el mismo filtro: no cambian el hardware. La excepción serían pulsos de flanco muy rápido o señales por encima de ~1 MHz, que el filtro de reconstrucción redondea. Para eso haría falta una ruta aparte por temporizador.</p>
"""))
S.append(sec("consecuencias", "3", "Qué obliga cada requisito en el diseño", f"""
  <div class="tw"><table>
    <thead><tr><th>Requisito</th><th>Consecuencia</th><th>Dónde</th><th>Estado</th></tr></thead>
    <tbody>{cons_rows}</tbody>
  </table></div>
"""))
S.append(sec("abierto", "4", "Lo que queda abierto", """
  <ul class="tight">
    <li>Rangos concretos del DMM (propuesta a validar en el diseño): en continua 200 mV, 2 V, 20 V y 50 V; en alterna 200 mV, 2 V, 20 V y 50 Vrms (RD-04); el rango alto de ±19 999 cuentas se limita a 50 V. El TIDA-01012 usa 50 mV, 500 mV, 5 V y 50 V con 50 000 cuentas. <i>Corregido el 30 sep: decía 200 V y 600 V, de cuando el DMM iba a medir la red</i>; de 200 Ω a 20 MΩ en resistencia; 200 mA y 2 A en corriente.</li>
    <li>Elegir el convertidor de ±6.5 V del AWG (sección G.8) y decidir RG-07 (fuente de continua frente a la salida de 50 Ω). <i>Los rieles y el presupuesto de RF-17 ya están calculados en la sección G.</i></li>
    <li>Protección del DMM frente a una conexión accidental a la red (RD-10) y texto de seguridad del manual.</li>
  </ul>
"""))

HTML = (
 '<title>Requisitos del DMM y del AWG</title>\n'
 '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
 '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans+Condensed:wght@500;600&display=swap">\n'
 '<style>' + css + EXTRA + '</style>\n<div class="wrap">\n<header class="hero">\n'
 '  <p class="eyebrow">S3G4 LAB · rev 2.1 · acordado el 23 sep 2026</p>\n  <h1>Requisitos del DMM y del AWG</h1>\n'
 '  <p class="lede">Qué deben hacer el multímetro y el generador, fijado por Keneth pregunta a pregunta. Completa los requisitos del osciloscopio (<code>S3G4_LAB_rev2.1/00_requisitos/requisitos_osciloscopio.html</code>).</p>\n'
 '</header>\n' + "".join(S) +
 '<footer><p class="meta">Redacción de Claude Code, 23 sep 2026, a partir de las respuestas de Keneth. Las cifras derivadas salen de <code>S3G4_LAB_rev2.1/herramientas/build_requisitos_dmm_awg.py</code>.</p></footer>\n</div>\n')
io.open(OUT, "w", encoding="utf-8").write(HTML)
print("ok", len(HTML), round(LEVELS), V_SHUNT, P_SHUNT, DDS_RES)
