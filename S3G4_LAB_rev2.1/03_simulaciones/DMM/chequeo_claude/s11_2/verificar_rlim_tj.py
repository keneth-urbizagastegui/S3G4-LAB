"""Auditoria Claude S11.2: ventana de R_LIM con la hoja del BSS126 y Tj con Zth (p. 4, fig. 4).
Sin LTspice. Numeros de hoja: Infineon BSS126 rev 2.1, p1 (Ptot 0.5 W, Tj 150, HBM clase 0),
p2 (IDSS>=7 mA a VGS=0/VDS=25 V; VGS(th) -2.7/-2.0/-1.6 V a 8 uA; RthJA 250 K/W huella minima),
p4 fig. 4 (Zth single pulse leido a mano: ~60 K/W a 8.3 ms, ~155 K/W a 10 s, ~240 K/W a 100 s)."""
import numpy as np
from scipy.optimize import brentq

def ilim(R, idss, vth, dvt=0.0):
    # Shockley con el umbral de 8 uA (misma aproximacion que la hoja permite, no garantizada)
    vp = vth / (1 - np.sqrt(8e-6 / idss)) + dvt
    return brentq(lambda i: i - idss * (1 - i * R / vp) ** 2, 1e-9, vp / R)

print('== Ventana de R_LIM (25 C) ==')
for R in (700, 725, 900, 1125, 1500):
    lo = ilim(R, 7e-3, 1.6); hi_inf = 2.7 / R
    print(f'R={R:5d}: Ilim min (IDSS 7 mA, Vth -1.6) {lo*1e3:.3f} mA ; Ilim max cota IDSS->inf = |Vth|max/R {hi_inf*1e3:.3f} mA ;'
          f' IDSS 21 mA/Vth -2.7 {ilim(R, 21e-3, 2.7)*1e3:.3f} mA')
Rlo = brentq(lambda R: ilim(R, 7e-3, 1.6) - 1.3e-3, 100, 5000)
print(f'R max para >=1.3 mA: {Rlo:.1f} ohm ; R min para <=2.4 mA sin cota de IDSS: {2.7/2.4e-3:.1f} ohm')
print('Por banda H6906 (p2, misma banda por bobina): J -1.8..-1.6, N -2.4..-2.2 -> razon de umbral en banda <=1.13')
for band, (a, b) in {'J': (1.6, 1.8), 'N': (2.2, 2.4)}.items():
    Rb = brentq(lambda R: ilim(R, 7e-3, a) - 1.3e-3, 100, 5000)
    print(f'  banda {band}: R<= {Rb:.0f} ohm para 1.3 mA; cota alta |Vth|max/R = {b/Rb*1e3:.3f} mA')

print('\n== Tj del FET peor (TA 70 C) ==')
P = 0.262652          # W, media en 10 s del FET2 peor, de Codex y reproducido por formula Vpk*I/pi
Ihalf = 2 * P         # potencia media durante el semiciclo en que bloquea
for name, z10, zh in (('Codex: RthJA 250 en 10 s, sin rizado', 250, 0), ('Zth 10 s ~155 + rizado 8.3 ms ~60', 155, 60),
                      ('Zth 10 s 140 / 170 (lectura +-)', 140, 50), ('', 170, 70)):
    tj = 70 + P * z10 + (Ihalf - P) * zh
    print(f'  {name:42s} Tj = {tj:.1f} C (limite 120 C)')
print(f'  Ptot(70 C) = {(150-70)/250:.3f} W ; 50 % = {(150-70)/250/2:.3f} W ; P/50% = {P/0.16:.2f}')
print(f'  Capacidad a 10 s por Zth: (150-70)/155 = {80/155:.3f} W ; 50 % = {40/155:.3f} W')
for ta in (25, 70):
    for zz in (155,):
        pmax = (120 - ta) / (zz + 60)   # con rizado
        print(f'  TA {ta}: P max para Tj<=120 con Zth10s+rizado = {pmax:.3f} W -> Ilim max {pmax*np.pi/(230*2**.5)*1e3:.2f} mA')
print(f'  50 % de Ptot a 70 C (0.16 W) -> Ilim max {0.16*np.pi/(230*2**.5)*1e3:.2f} mA')
