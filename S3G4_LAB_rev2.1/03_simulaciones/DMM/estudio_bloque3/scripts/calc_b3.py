# -*- coding: utf-8 -*-
"""Bloque 3 del DMM (ohmios, diodo, continuidad): cuentas de compliancia, ventana del ADC y especificacion D5.
Modelo propio, a mano; las constantes salen de dmm_rev21.html (6, 8), ACTA_S12d y las hojas del repositorio.
Ejecutar: python calc_b3.py   (escribe resultados/calc_b3.txt)"""
import math, sys, io
RAIL_NOM, RAIL_TOL = 4.9, 0.02
RAIL = RAIL_NOM * (1 - RAIL_TOL)           # peor caso, como S11.4 (riel -2 %)
VREF = 2.5
R1, R2 = 24.9e3, 4.99e3
VSET = VREF * R2 / R1                      # 0.501 V
RON4051 = 110.0                            # 74HCT4051 a +-4.9 V cerca del riel (hoja Fig. 8: 70-110 ohm); fuerza
VDS_MOS = 0.03                             # BSS84 con Vgs -7..-9 V, I <= 1 mA (Rds(on) <= 10 ohm)
R_DIV = 10.01e6                            # divisor 6x1.5M+910k+100k, entre V/Ohm y COM (ACTA_S12d)
LSB = 100e-6                               # una cuenta = 100 uV en el ADC (ventana +-2 V = +-19999 cuentas)
G_OHM = math.sqrt(280**2 + 250**2 + 500**2)    # ppm: deriva I (280), relacion del driver (250), patron 0.05 % (500)  -> 630
INL = {"garantizada": (39, 40), "calibrada": (10, 10)}   # (cuentas de INL del ADC, cuentas de la especificacion)
PCT = {"200": 0.002, "2k": 0.002, "20k": 0.002, "200k": 0.002, "2M": 0.002, "20M": 0.01}
def par(a, b): return a * b / (a + b)
def vf_bat54(i):                           # Nexperia BAT54, maximos de hoja: 0.24 V a 0.1 mA, 0.32 V a 1 mA, 0.40 V a 10 mA
    return max(0.0, 0.32 + 0.08 * math.log10(i / 1e-3))
def disponible(i, rser, rail=RAIL, vset=VSET, ron=RON4051, tol=0.01):
    return rail - vset - i * ron - VDS_MOS - vf_bat54(i) - i * rser * (1 + tol)

RANGOS = [("200 Ω", "200", 200.0), ("2 kΩ", "2k", 2e3), ("20 kΩ", "20k", 20e3),
          ("200 kΩ", "200k", 200e3), ("2 MΩ", "2M", 2e6), ("20 MΩ", "20M", 20e6)]

def comprobar(i, g, fs, pct, n_adc, n_esp):
    """Peor cociente error/tolerancia al recorrer del 10 al 100 % del rango. error: n_adc cuentas del ADC llevadas a ohmios
    con la curva V_x = I (Rx || R_DIV) y la ganancia g; tolerancia: (pct - ganancia de ohmios) * lectura + n_esp cuentas de la pantalla."""
    peor = (0, 0)
    for k in range(1, 11):
        r = fs * k / 10
        err = n_adc * LSB / (g * i * (R_DIV / (r + R_DIV)) ** 2)
        tol = (pct - G_OHM * 1e-6) * r + n_esp * fs / 20000
        peor = max(peor, (err / tol, k * 10))
    return peor

def digitos_necesarios(i, g, fs, pct, n_adc):
    """cuentas de pantalla (n_esp) que haria falta para que el error de INL quepa en la tolerancia en todo el 10-100 % del rango"""
    peor = 0
    for k in range(1, 11):
        r = fs * k / 10
        err = n_adc * LSB / (g * i * (R_DIV / (r + R_DIV)) ** 2)
        fijo = (pct - G_OHM * 1e-6) * r
        peor = max(peor, (err - fijo) * 20000 / fs)
    return peor


def tabla(nombre, corrientes, ganancias, rser, vset=VSET, rail=RAIL):
    out = [f"### {nombre}", f"R_serie = {rser:g} Ω, V_set = {vset:.3f} V, riel {rail:.2f} V", "",
           "| Rango | I | G | V_x a fondo | V_ADC a fondo (ventana) | disponible | margen | cuentas ADC por Ω | garantizada (peor, %) | calibrada (peor, %) |",
           "|---|---|---|---|---|---|---|---|---|---|"]
    for (n, k, fs), i, g in zip(RANGOS, corrientes, ganancias):
        vx = i * par(fs, R_DIV)
        disp = disponible(i, rser, rail=rail, vset=vset)
        cg, pg = comprobar(i, g, fs, PCT[k], *INL["garantizada"])
        cc, pc = comprobar(i, g, fs, PCT[k], *INL["calibrada"])
        vacio = min(disp, i * R_DIV)
        # cuentas ADC por ohmio (a fondo, derivada local)
        cpo = g * i * (R_DIV / (fs + R_DIV)) ** 2 / LSB
        out.append(f"| {n} | {i*1e6:.4g} µA | ×{g:g} | {vx:.3f} V | {g*vx:.3f} V ({g*vx/2*100:.0f} %) | {disp:.2f} V | {disp-vx:+.2f} V "
                   f"| {cpo:.3g} | {cg*100:.0f} ({pg} %) | {cc*100:.0f} ({pc} %) |")
    return "\n".join(out)

if __name__ == "__main__":
    buf = io.StringIO()
    def P(*a):
        print(*a); buf.write(" ".join(str(x) for x in a) + "\n")
    P(f"V_set = {VSET:.4f} V; ganancia de ohmios (ppm) = {G_OHM:.0f}; riel peor = {RAIL:.3f} V")
    H = [10e-3, 1e-3, 100e-6, 10e-6, 1e-6, 0.2e-6]
    P(tabla("D0 · bloque 1 con las corrientes de H (4.9 kΩ)", H, [1] * 6, 4.9e3))
    A = [0.5e-3, 0.5e-3, 100e-6, 10e-6, 1e-6, 0.2e-6]
    P(); P(tabla("Da · 4.9 kΩ, 0.5 mA en 200 Ω (×10.1) y 2 kΩ (×1)", A, [10.1, 1, 1, 1, 1, 1], 4.9e3))
    for rs in (1.5e3, 1.8e3, 2.3e3):
        B = [1.0e-3, 1.0e-3, 100e-6, 10e-6, 1e-6, 0.2e-6]
        P(); P(tabla(f"Db · R_serie {rs:g} Ω, 1 mA en 200 Ω (×10.1) y 2 kΩ (×1)", B, [10.1, 1, 1, 1, 1, 1], rs))
    # corriente maxima en 2 kΩ a fondo para cada R_serie, con margen 0.3 V
    P(); P("I máxima en el rango de 2 kΩ (V_x a fondo = I·2 kΩ ∥ 10 MΩ) con margen ≥ 0.3 V, y llenado de la ventana:")
    for rs in (1.0e3, 1.5e3, 1.8e3, 2.3e3, 3.0e3, 4.0e3, 4.9e3):
        lo, hi = 1e-6, 2e-3
        for _ in range(60):
            mid = (lo + hi) / 2
            if disponible(mid, rs) - mid * par(2e3, R_DIV) >= 0.3: lo = mid
            else: hi = mid
        P(f"  R_serie {rs/1e3:.1f} kΩ → I ≤ {lo*1e3:.3f} mA, V_ADC a fondo {lo*par(2e3,R_DIV):.2f} V ({lo*par(2e3,R_DIV)/2*100:.0f} % de la ventana)")
    open(sys.path[0] + "/../resultados/calc_b3.txt", "w", encoding="utf8").write(buf.getvalue())
