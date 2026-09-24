# -*- coding: utf-8 -*-
"""Corrige el modelo de ruido del divisor (kT/C) en el documento vivo y en el analisis del DSO112."""
import io, math
from pathlib import Path
R21 = Path(__file__).resolve().parent.parent   # carpeta S3G4_LAB_rev2.1
k, T = 1.380649e-23, 300
ENB = math.sqrt(1.57 * 1.5e6)
en = 7e-9
div = 20.09 * math.sqrt(k * T / 200e-12)            # divisor ÷20, 200 pF de nodo
st = en * 20.09 * ENB                                # una etapa de 7 nV/√Hz referida a la entrada
fixed5 = math.sqrt(div**2 + 2 * st**2)
r200 = math.sqrt(div**2 + st**2 + (en * 2 * 20.09 * ENB)**2)
r500 = math.sqrt(div**2 + st**2 + (en * 5 * 20.09 * ENB)**2)
p1_500 = math.sqrt((100 * math.sqrt(k * T / 1000e-12))**2 + 2 * (en * 100 * ENB)**2)
print(f"divisor ÷20: {div*1e6:.0f} µV · etapa: {st*1e6:.0f} µV · ÷20 fijo a 5 mV/div: {fixed5*1e6:.0f} µV = {fixed5/5e-3*100:.1f} %")
print(f"200 mV/div: {r200*1e6:.0f} µV = {r200/0.2*100:.2f} % · 500 mV/div: {r500*1e3:.2f} mV = {r500/0.5*100:.2f} % · P1 500 mV/div: {p1_500*1e3:.2f} mV = {p1_500/0.5*100:.2f} %")

def patch(fn, pairs):
    s = io.open(fn, encoding="utf-8").read()
    for a, b in pairs:
        assert s.count(a) == 1, (fn, a[:70]); s = s.replace(a, b)
    io.open(fn, "w", encoding="utf-8").write(s)

LIVE = str(R21) + r"/01_diseno/rediseno_afe_rev21.html"
patch(LIVE, [
 ("Sin rama ×1, la escala de 5 mV/div es inutilizable: 864 µV de ruido referido a la entrada (17 % de división) y ganancia 125. Con ella, ~0.3 % de división.",
  "Sin rama ×1, la escala de 5 mV/div exige ganancia ×1000 detrás del ÷20 y multiplica ×20 el ruido de los amplificadores: ≈ 0.32 mV rms (6 % de división). Con ella, ~0.3 % de división. <i>Cifra corregida el 23 sep; la anterior (864 µV, 17 %) salía de un modelo de ruido equivocado.</i>"),
 ("Con el divisor siempre puesto, el ruido térmico del nodo (47.4 kΩ → 28 nV/√Hz) sale multiplicado por 20 al referirlo a la entrada: <b>≈870 µVrms con 1.5 MHz de banda</b>, que en la escala de 5 mV/div es el 17 % de una división. Con un límite de banda de 200 kHz baja a ≈317 µV, menos del 1 %. Es exactamente el compromiso que el DSO150 resuelve teniendo <b>200 kHz de ancho de banda total</b>. Habrá que elegir entre escalas finas o ancho de banda, y ese es el tema de la sección C.",
  "<i>Corregido el 23 sep.</i> El ruido térmico de las resistencias del divisor <b>no es blanco hasta 1.5 MHz</b>: los condensadores de compensación lo cortocircuitan por encima de ~17 kHz y el total queda acotado por √(kT/C) del nodo, ≈ 4.5 µV con 200 pF, es decir <b>≈ 91 µV referidos a la entrada</b>. Lo que de verdad hace un divisor fijo en las escalas finas es <b>multiplicar ×20 el ruido de los amplificadores</b> que vienen detrás (≈ 0.2 mV por etapa a 1.5 MHz) y obligar a una ganancia ×1000 en 5 mV/div: en total ≈ 0.32 mV rms, un 6 % de división. La cifra que había aquí antes (870 µV, 17 %) usaba un modelo equivocado. Ese es el tema de la sección C."),
 ('<tr><td>200 mV/div</td><td>divisor ÷20 (864 µV) + U103A</td><td class="n">≈ 1 mV</td><td class="n">≈ 0.5 %</td></tr>',
  '<tr><td>200 mV/div</td><td>buffer y U103A multiplicados por el ÷20; el divisor sólo aporta 91 µV</td><td class="n">≈ 0.5 mV</td><td class="n">≈ 0.25 %</td></tr>'),
 ('<tr><td>500 mV–10 V/div</td><td>divisor ÷20 + U103A</td><td class="n">1.4 mV a 22 mV</td><td class="n">≈ 0.2–0.3 %</td></tr>',
  '<tr><td>500 mV–10 V/div</td><td>U103A multiplicado por la toma y por el ÷20</td><td class="n">1.1 mV a 22 mV</td><td class="n">≈ 0.2 %</td></tr>'),
 ("<p><b>Todas las escalas quedan entre 0.2 y 0.5 % de división</b>, del orden de uno o dos LSB del ADC de 12 bits (2.5 V / 4096 = 0.61 mV, un 0.24 % de división). La peor es 200 mV/div, la primera que pasa por el divisor. Antes de la rama ×1, la escala de 5 mV/div estaba en el 17 %.</p>",
  "<p><b>Todas las escalas quedan en ≈ 0.2–0.3 % de división</b>, del orden de un LSB del ADC de 12 bits (2.5 V / 4096 = 0.61 mV, un 0.24 % de división). Sin la rama ×1, la escala de 5 mV/div estaría en ≈ 6 %. <i>Corregido el 23 sep: el ruido de las resistencias del divisor se calcula como √(kT/C) de su nodo, no como ruido blanco hasta 1.5 MHz.</i></p>"),
])
DSO = str(R21) + r"/02_referencias/analisis_dso112.html"
patch(DSO, [
 ("<tr><td>Ruido en la primera escala del divisor</td><td>~0.5 % div (200 mV/div)</td><td>~0.5 % div (500 mV/div)</td></tr>",
  "<tr><td>Ruido en la primera escala del divisor</td><td>~0.25 % div (200 mV/div)</td><td>~0.3 % div (500 mV/div)</td></tr>"),
])
print("parches aplicados")
