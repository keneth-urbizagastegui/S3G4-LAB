# -*- coding: utf-8 -*-
"""Cifras propias del EEVblog 121GW, a partir del esquematico research_and_tests/EEVblog_121GW/121GW_schematic.pdf
(ene. 2018, copia de archive.org) y del manual EEVblog-121GW-Manual.pdf (rev. 3 mar 2025).
Ejecutar: python calc_dmm_121gw.py"""
import math

# --- Divisor de tension (alrededor del HY3131; el emparejamiento R-C esta deducido de la disposicion) ---
R_TOP = 10e6                      # R11 «10MD» (0.5 %)
C_TOP, R_TOP_DAMP = 6e-12, 30e3   # C13 6 pF en serie con R9 30 kΩ, en paralelo con R11
PATAS = {                         # nombre: (R, C de compensacion o None si los condensadores estan sin montar)
    "÷10":    (1.11e6, None),               # R13 «1.11MC»; C16, C17 «x»
    "÷100":   (101e3, 36e-12 + 560e-12),    # R15 «101KC»; C19, C20
    "÷1000":  (10e3, 750e-12 + 5.6e-9),     # R21 «10KC»; C22, C23
    "÷10000": (1e3, 10e-9 + 56e-9),         # R26 «1KC»; C24, C26
}
TAU_TOP = R_TOP * C_TOP
div = {}
for n, (R, C) in PATAS.items():
    k = R / (R_TOP + R)
    div[n] = dict(R=R, k=k, d=1/k, tau=(R * C) if C else None, err=((R * C) / TAU_TOP - 1) if C else None,
                  C_ideal=TAU_TOP / R)

# --- Proteccion del borne V/Ω ---
R_SERIE_V = 1.2e3 + 1e3           # PTC3 (1.2 kΩ en frio) + R16
V_MOV_1MA = 910.0                 # S05K575: tension de varistor tipica a 1 mA (575 Vrms nominal)
N_MOV_SERIE = 2                   # MOV1 + MOV3 hacia AGND
V_MOV_SERIE = N_MOV_SERIE * V_MOV_1MA
V_CAT = 600.0 * math.sqrt(2)      # 600 Vrms de pico
I_TOP_600 = V_CAT / R_TOP
V_PULSO, R_PULSO = 6e3, 2.0       # «6 kV 2 Ω» del manual
I_PULSO = (V_PULSO - V_MOV_SERIE) / (R_PULSO + R_SERIE_V)

# --- Corriente ---
R33, R43, SHUNT = 100.0, 1.0, 0.01
BURDEN_MANUAL = {"µA": 100e-6 / 1e-6, "mA": 2e-3 / 1e-3, "A": 0.03}   # V por A, del manual
R_MEDIDA = {"µA (50 / 500 µA)": R33 + R43 + SHUNT, "mA (5 / 50 mA)": R43 + SHUNT, "A (0.5 / 5 / 10 A)": SHUNT}
G_LOWBURDEN = 1 + 90e3 / 10e3     # MAX4238 con R106 90 kΩ / R46 10 kΩ
V_50uA = 50e-6 * (R33 + R43 + SHUNT)

# --- Diodo y LowZ ---
R_DIODO = 2.2e3                   # «nominal 2.2 K resistor (includes PTC)»: PTC4 1.2 kΩ + R17 1 kΩ
I_DIODO = {"3 V": 1.4e-3, "15 V": 7e-3}
V_FUENTE_15 = 7e-3 * R_DIODO            # la corriente de prueba es la de cortocircuito: fuente ≈ 15.4 V
P_LOWZ_230 = 230.0**2 / R_DIODO   # potencia inicial si se aplica la red en LowZ (antes de que la PTC suba)

if __name__ == "__main__":
    print(f"tau arriba {TAU_TOP*1e6:.0f} µs")
    for n, v in div.items():
        tau = f"{v['tau']*1e6:.1f} µs ({v['err']*100:+.1f} %)" if v["tau"] else f"sin C (haria falta {v['C_ideal']*1e12:.0f} pF)"
        print(f"{n}: {v['R']:.4g} Ω → ÷{v['d']:.1f}, tau {tau}")
    print(f"600 Vrms: {I_TOP_600*1e6:.0f} µA por R11; MOV en serie ≈ {V_MOV_SERIE:.0f} V; pulso 6 kV → {I_PULSO:.2f} A por PTC3+R16")
    for n, R in R_MEDIDA.items():
        print(f"{n}: {R:.4g} Ω")
    print(f"×{G_LOWBURDEN:.0f} en 50 µA: {V_50uA*1e3:.1f} mV → {V_50uA*G_LOWBURDEN*1e3:.0f} mV")
    print(f"diodo 15 V: fuente ≈ {V_FUENTE_15:.1f} V; LowZ con 230 V: {P_LOWZ_230:.0f} W al principio")
