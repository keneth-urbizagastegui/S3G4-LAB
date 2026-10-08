# -*- coding: utf-8 -*-
"""Bloque 2: deriva de la relación del divisor (tema 1), fugas e Ib (tema 5) y presupuesto de cuentas.
Ejecutar: python calc_b2.py   (solo numpy; no usa red ni LTspice)"""
import itertools, math
import numpy as np

DT = 5.0   # 23 ± 5 °C

def ratio_drift(Rt, n_top, tc_top, R2, tc2, R3, tc3, tap):
    """deriva relativa de la relación del divisor (ppm) para ±DT.
    Peor caso: cada grupo toma ±TC (se enumeran los signos). Estadística: uniformes independientes (sigma = TC/sqrt(3)), n piezas en la parte alta."""
    Rtot = Rt+R2+R3
    def rho(a_t, a_2, a_3):
        # sensibilidad logarítmica de la relación frente a cada grupo
        if tap == 10:
            lo = R2+R3; return (1-lo/Rtot)*((R2*a_2+R3*a_3)/lo - a_t)
        return a_3 - (Rt*a_t+R2*a_2+R3*a_3)/Rtot
    wc = max(abs(rho(s1*tc_top, s2*tc2, s3*tc3)) for s1, s2, s3 in itertools.product((-1, 1), repeat=3))*DT
    # estadística: derivadas parciales
    def partial(i):
        e = [0, 0, 0]; e[i] = 1.0; return rho(*e)
    s = [tc_top/math.sqrt(3*n_top), tc2/math.sqrt(3), tc3/math.sqrt(3)]
    sig = math.sqrt(sum((partial(i)*s[i])**2 for i in range(3)))*DT
    return wc, sig

opts = {
 'H (no existe en LCSC): 3x3 MΩ 0.1 %, 25 ppm': dict(Rt=9e6, n=3, tt=25, R2=900e3, t2=25, R3=100e3, t3=25, usd=None),
 'D1: 3x3.01 MΩ película gruesa 1 %, 100 ppm (C49656332)': dict(Rt=9.03e6, n=3, tt=100, R2=910e3, t2=25, R3=100e3, t3=25, usd=3*0.0047+0.0569+0.075),
 'D1b: 3x3 MΩ película gruesa 1 %, 100 ppm, TODO grueso': dict(Rt=9e6, n=3, tt=100, R2=900e3, t2=100, R3=100e3, t3=100, usd=3*0.0072+0.01),
 'D3: 6x1.5 MΩ película delgada 0.1 %, 25 ppm (C728673)': dict(Rt=9e6, n=6, tt=25, R2=910e3, t2=25, R3=100e3, t3=25, usd=6*0.0841+0.0569+0.075),
 'D4: 9x1 MΩ película delgada 0.1 %, 25 ppm (C55205340)': dict(Rt=9e6, n=9, tt=25, R2=910e3, t2=25, R3=100e3, t3=25, usd=9*0.0491+0.0569+0.075),
 'D5: 6x1.5 MΩ delgada + 25 ppm pero R2/R3 de 10 ppm (hipotético)': dict(Rt=9e6, n=6, tt=25, R2=910e3, t2=10, R3=100e3, t3=10, usd=None),
}
print('=== Tema 1: deriva de la relación con ΔT = ±%g °C ===' % DT)
print(f"{'opción':62s} {'÷10 peor':>9s} {'÷10 σ':>7s} {'÷100 peor':>10s} {'÷100 σ':>7s}  USD")
rows = {}
for k, o in opts.items():
    w10, s10 = ratio_drift(o['Rt'], o['n'], o['tt'], o['R2'], o['t2'], o['R3'], o['t3'], 10)
    w100, s100 = ratio_drift(o['Rt'], o['n'], o['tt'], o['R2'], o['t2'], o['R3'], o['t3'], 100)
    rows[k] = (w10, s10, w100, s100)
    print(f"{k:62s} {w10:9.0f} {s10:7.0f} {w100:10.0f} {s100:7.0f}  {o['usd'] if o['usd'] else '-'}")

print('\n=== Presupuesto de ganancia del rango de 20 V (ppm de lectura, ±5 °C) ===')
REF, DRV, PAT, GAIN10 = 150, 250, 500, 250
def rss(*v): return math.sqrt(sum(x*x for x in v))
for k, (w10, s10, w100, s100) in rows.items():
    tot_w = rss(REF, DRV, PAT, w10); tot_s = rss(REF, DRV, PAT, s10*2)       # 2σ ≈ 95 %
    print(f"{k:62s} total peor {tot_w:5.0f} ppm (margen p/ envejecimiento {math.sqrt(max(0,1000**2-tot_w**2)):4.0f})  | 2σ {tot_s:5.0f} (margen {math.sqrt(max(0,1000**2-tot_s**2)):4.0f})")
print('Referencia de H: divisor 250 -> total', round(rss(REF, DRV, PAT, 250)), 'ppm')

print('\n=== Tensión por pieza con 230 Vrms (325 Vpk) y con un pulso de 1 kV (reparto capacitivo igual) ===')
for n in (3, 6, 9):
    print(f'{n} piezas arriba: {325/n:5.0f} Vpk en régimen; {1000/n:5.0f} V con 1 kV; potencia por pieza a 230 Vrms: {(230**2/10e6)/n*1e3:.2f} mW')

print('\n=== Tema 5: cuentas por nA de fuga (resistencia de fuente vista) ===')
cuenta = {'200 mV (X0, A x10)': 10e-6, '2 V (X0)': 100e-6, '20 V (X1)': 1e-3, '50 V (X2)': 10e-3}
Rs = {'200 mV (X0, A x10)': 99.1e3, '2 V (X0)': 99.1e3, '20 V (X1)': 0.9e6+100, '50 V (X2)': 1/(1/10e6+1/100e3)}
fact = {'200 mV (X0, A x10)': 1, '2 V (X0)': 1, '20 V (X1)': 1, '50 V (X2)': 1}
for r in cuenta:
    print(f'{r:22s} Rs={Rs[r]/1e3:7.1f} kΩ  -> {Rs[r]*1e-9/ (cuenta[r] if r.startswith(("200","2 V")) else cuenta[r]/ (10 if r.startswith("20 V") else 100) ):6.2f} cuentas por nA')
print('\nDeriva por temperatura (la fuga se duplica cada 10 °C; Ib del OPA2188 cada 11.8 °C, hoja: 160 pA a 25 °C -> 18 nA a 105 °C)')
k_fuga = 2**(DT/10)-1; k_ib = math.exp(math.log(18e3/160)/80*DT)-1
print(f'fuga: +{k_fuga*100:.0f} % con +5 °C (y {-(1-2**(-DT/10))*100:.0f} % con −5 °C); Ib del OPA2188: +{k_ib*100:.0f} %')
cn = {'200 mV': 9.91, '2 V': 0.991, '20 V': 9.0, '50 V': 0.99}
print('Fuga tolerable a 25 °C para que su deriva sea ≤ 3 cuentas:')
for r, c in cn.items():
    print(f'  {r:7s}: {3/(c*k_fuga):5.2f} nA (≤ 2 cuentas: {2/(c*k_fuga):5.2f} nA)')
print('Ib del OPA2188 (máx. 850 pA a 25 °C): valor estático (se calibra) y su deriva con +5 °C, en cuentas')
for r, c in cn.items():
    print(f'  {r:7s}: estático {0.85*c:5.1f}  deriva {0.85*c*k_ib:4.1f}   (típico 160 pA: {0.16*c:4.1f} / {0.16*c*k_ib:4.2f})')
print('Con OPA2192 (5 pA típico, LCSC; máximo por confirmar en la hoja):')
for r, c in cn.items():
    print(f'  {r:7s}: estático {0.005*c:5.2f}  deriva (supone x1.34) {0.005*c*0.34:5.3f}')
