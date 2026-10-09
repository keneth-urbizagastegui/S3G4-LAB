# -*- coding: utf-8 -*-
"""Bloque 3, segunda parte: cuentas de pantalla que haria falta aceptar, deriva de la corriente, fugas tolerables, diodo y continuidad."""
import math, sys, io
from calc_b3 import *
out = io.StringIO()
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")

P("## Cuentas de pantalla que cubrirían la INL (la especificación D5 da 40 garantizada y 10 calibrada; 20 MΩ igual)")
diseños = {
 "Da: 4.9 kΩ, 0.5 mA (200 Ω ×10.1, 2 kΩ ×1)": ([0.5e-3, 0.5e-3, 100e-6, 10e-6, 1e-6, 0.2e-6], [10.1, 1, 1, 1, 1, 1]),
 "Db: ≤1.5 kΩ, 1 mA (200 Ω ×10.1, 2 kΩ ×1)": ([1.0e-3, 1.0e-3, 100e-6, 10e-6, 1e-6, 0.2e-6], [10.1, 1, 1, 1, 1, 1]),
 "Dc: 2.2 kΩ+R_S→0 (2.2 kΩ), 0.8 mA": ([0.8e-3, 0.8e-3, 100e-6, 10e-6, 1e-6, 0.2e-6], [10.1, 1, 1, 1, 1, 1]),
}
for nombre, (I, G) in diseños.items():
    P(f"\n{nombre}")
    for (n, k, fs), i, g in zip(RANGOS[:3], I, G):
        dg = digitos_necesarios(i, g, fs, PCT[k], 39); dc = digitos_necesarios(i, g, fs, PCT[k], 10)
        P(f"  {n}: garantizada {dg:.0f} (D5: 40), calibrada {dc:.0f} (D5: 10)")

P("\n## Deriva de la corriente tras calibrar (23 ± 5 °C), ppm")
DT = 5
def rss(*x): return math.sqrt(sum(v * v for v in x))
tc_rk, tc_r1, tc_r2 = 25 * DT, 25 * DT, 25 * DT
vosB = 2e-6 * DT / VSET * 1e6; vosA = 2e-6 * DT / VREF * 1e6
beta_nom = 150; npn = (1 / (beta_nom + 1)) * 0.006 * DT * 1e6
P(f"R_k {tc_rk}, R2/R1 {rss(tc_r1, tc_r2):.0f} (rss) / {tc_r1+tc_r2} (lineal), Vos de B {vosB:.0f}, Vos de A {vosA:.0f}, NPN de la etapa 1 (β=150, +0.6 %/°C) {npn:.0f}")
con_npn = rss(tc_rk, rss(tc_r1, tc_r2), vosB, vosA, npn); sin_npn = rss(tc_rk, rss(tc_r1, tc_r2), vosB, vosA)
lineal = tc_rk + tc_r1 + tc_r2 + vosB + vosA
P(f"total rss con NPN {con_npn:.0f} ppm; con MOSFET en la etapa 1 {sin_npn:.0f} ppm; peor caso lineal sin NPN {lineal:.0f} ppm")
P(f"PNP de paso (β=150): corriente perdida {1e6/(beta_nom+1):.0f} ppm, deriva {npn:.0f} ppm; a 0.2 µA la β baja (MMBT3906 hFE ≥ 60 a 10 µA)")
gan = rss(sin_npn, 250, 500)
P(f"ganancia de ohmios con MOSFET: rss(corriente {sin_npn:.0f}, driver 250, patrón 500) = {gan:.0f} ppm (H: 630)")

P("\n## Fuga tolerable en el nodo de la corriente (fuente → borne): deriva ×(√2−1)=0.41 de la fuga a 23 °C ≤ 25 % de la tolerancia que sobra tras la ganancia")
for (n, k, fs), i in zip(RANGOS, [1e-3, 1e-3, 100e-6, 10e-6, 1e-6, 0.2e-6]):
    sobra = (PCT[k] - gan * 1e-6)
    dI = 0.25 * sobra * i
    P(f"  {n} (I {i*1e6:.3g} µA): ΔI ≤ {dI*1e9:.3g} nA → fuga a 23 °C ≤ {dI/0.414*1e9:.3g} nA")

P("\n## Diodo: tensión disponible a 100 µA y a la corriente de silicio, rail -2 %")
for rser in (4.9e3, 1.5e3):
    for i in (100e-6, 0.5e-3, 1e-3):
        d = disponible(i, rser)
        P(f"  R_serie {rser/1e3:.1f} kΩ, {i*1e6:g} µA: {d:.2f} V")

P("\n## Continuidad: umbral 50 Ω; PB14 = A_out/2; comparador COMP7 y DAC2 (hoja DS12712 Rev 5, Tabla 74 y 72)")
OFFS_COMP, DAC_TUE = 9e-3, 5 * (2.5 / 4096)
for i in (0.5e-3, 1e-3):
    vx = 50 * i; pb14 = vx * 10.1 / 2
    sh = (OFFS_COMP + DAC_TUE)     # incertidumbre en PB14 sin calibrar, peor caso
    dR = sh * 2 / 10.1 / i
    P(f"  I {i*1e3:g} mA: V_x(50 Ω) = {vx*1e3:.1f} mV; A_out = {vx*10.1*1e3:.0f} mV; PB14 = {pb14*1e3:.0f} mV; DAC2 ≈ código {pb14/2.5*4096:.0f}; "
      f"incertidumbre sin calibrar ±{sh*1e3:.0f} mV en PB14 = ±{dR:.1f} Ω ({dR/50*100:.0f} % del umbral); histéresis HYST=1 típ. 9 mV = {9e-3*2/10.1/i:.1f} Ω")
open(sys.path[0] + "/../resultados/calc_b3b.txt", "w", encoding="utf8").write(out.getvalue())
