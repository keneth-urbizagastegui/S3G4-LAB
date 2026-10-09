# -*- coding: utf-8 -*-
"""Tabla comparativa de las opciones para los 4.9 kΩ: a (0.5 mA), c2 (inyectar en N1, R1 = 2.2 kΩ, 0.79 mA), c1 (inyectar en N1, R1 = 1.5 kΩ, 1 mA) y b (R1 + R_S = 1.5 kΩ)."""
import sys, io
from calc_b3 import *
out = io.StringIO()
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")
ops = [("a · 4.9 kΩ", 4.9e3, 0.501 / 1000.0), ("c2 · 2.2 kΩ (inyectar en N1)", 2.2e3, 0.501 / 634.0), ("c1 · 1.53 kΩ (R1 = 3 × 510 Ω)", 1.53e3, 0.501 / 499.0), ("b · 1.5 kΩ (R1 = 3 × 330 Ω + R_S 510 Ω)", 1.5e3, 0.501 / 499.0)]
P("| Opción | R_serie | I (200 Ω y 2 kΩ) | V_x a fondo 2 kΩ / V_ADC (ventana) | V_disponible | margen | LED 100 µA: V_disp | silicio: I y V_disp | cuentas/Ω en 200 Ω | dígitos necesarios (garantizada / calibrada) | error/tolerancia (garantizada / calibrada), 2 kΩ |")
P("|---|---|---|---|---|---|---|---|---|---|---|")
for n, rs, i in ops:
    vx2 = i * par(2e3, R_DIV); vd = disponible(i, rs); vled = disponible(100e-6, rs)
    dg = digitos_necesarios(i, 1, 2e3, 0.002, 39); dc = digitos_necesarios(i, 1, 2e3, 0.002, 10)
    cg = comprobar(i, 1, 2e3, 0.002, 39, 40); cc = comprobar(i, 1, 2e3, 0.002, 10, 10)
    cpo = 10.1 * i * (R_DIV / (200 + R_DIV)) ** 2 / LSB
    P(f"| {n} | {rs/1e3:.1f} kΩ | {i*1e3:.3f} mA | {vx2:.2f} V / {vx2/2*100:.0f} % | {vd:.2f} V | {vd-vx2:+.2f} V | {vled:.2f} V | {i*1e3:.2f} mA, {vd:.2f} V | {cpo:.0f} | {dg:.0f} / {dc:.0f} | {cg[0]*100:.0f} % / {cc[0]*100:.0f} % |")
open(sys.path[0] + "/../resultados/calc_opciones.txt", "w", encoding="utf8").write(out.getvalue())
