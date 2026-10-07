# -*- coding: utf-8 -*-
"""Estimaciones de Claude para el plan S11 del DMM (7 oct 2026). Son a mano y con supuestos marcados;
S11 las confirma o las corrige con LTspice. Reutiliza calc_dmm_h (fuente de ohmios P43).
Ejecutar: python calc_dmm_s11.py"""
import math
import calc_dmm_h as H

PI2 = 2 * math.pi

# --- 1) Camino X0 en alterna: R_PROT con la capacidad del nodo X0 (polo de primer orden) ---
R_PROT = 3 * 33e3
C_X0 = {"BAV199 (2 diodos, 1.08 pF a 5 V, modelos/LEEME)": 2 * 1.08e-12,
        "74HC4051 canal Y + común Z (hoja Nexperia)": 5e-12 + 25e-12,
        "OPA2188, entrada (supuesto, se lee de la hoja en K0)": 6e-12,
        "pista (supuesto)": 2e-12}
C_X0_TOT = sum(C_X0.values())
F_X0 = 1 / (PI2 * R_PROT * C_X0_TOT)
CAIDA_X0_20K = 1 / math.sqrt(1 + (20e3 / F_X0) ** 2) - 1

# --- 2) Compensación del divisor de 10 MΩ (P18): misma τ en los tres tramos ---
R_ALTO, R_MEDIO, R_BAJO = 9e6, 900e3, 100e3
C_ALTO = 100e-12 / 3                     # 3 × 100 pF C0G 630 V, uno sobre cada 3 MΩ
TAU = R_ALTO * C_ALTO
C_MEDIO, C_BAJO = TAU / R_MEDIO, TAU / R_BAJO          # ideales; en el plan: 330 pF y 3.0 nF (E12/E24)
DESAJUSTE_MEDIO = 330e-12 / C_MEDIO - 1
DESAJUSTE_BAJO = 3.0e-9 / C_BAJO - 1
R_AMORT = 10e3
F_AMORT = 1 / (PI2 * R_AMORT * C_ALTO)

# --- 3) P42 con la fuente encendida y la red en V/Ω (semiciclo negativo) ---
V_PICO = 230 * math.sqrt(2)
P42 = []
for o in H.OHM:
    v = V_PICO + H.RIEL - H.V_SET    # tensión que reparte la escalera en el pico
    p_pico = o["i"] * v / 2           # por MMBTA92 (2 en serie, reparto ideal)
    e_semiciclo = o["i"] * V_PICO * (2 / math.pi) * (1 / 120) / 2   # energía por transistor en 8.3 ms
    P42.append((o["rango"], o["i"], p_pico, e_semiciclo))
P_MMBTA92 = 0.35                         # W, SOT-23 (supuesto; K0 lo lee de la hoja)

# --- 4) Tensión en vacío frente al modo común del OPA2188 (V+ − 1.5 V, supuesto de la hoja) ---
def vacio(riel):
    return [(o["rango"], min(riel - H.V_SET - o["i"] * H.RON_4051 - H.VCE_SAT - H.CAIDA_P42,
                             o["i"] * H.R_DIV)) for o in H.OHM]
CM_OPA2188 = {riel: riel - 1.5 for riel in (4.9 * 0.98, 4.9, 4.9 * 1.02)}

# --- 5) PNP de paso: la corriente de base no llega a Rx (α = β/(β+1)) ---
TC_BETA = 0.006                          # +0.6 %/°C (supuesto típico de un PNP de señal)
ALFA = {b: (1 / (b + 1), (1 / (b + 1)) * TC_BETA * H.DT) for b in (50, 100, 200)}

# --- 6) Driver → ADC5: carga media del muestreo como resistencia equivalente ---
F_S, C_S = 200e3, 5e-12                  # 200 kSa/s y C_S de S6 (DS12712)
R_EQ = 1 / (F_S * C_S)
REJILLA_RC = [(r, 1 / (PI2 * r * 50e3)) for r in (100, 330, 1e3, 3.3e3)]

# --- 7) Rechazo de la red (P40): integración de 1 ciclo de 60 Hz con la red desviada ---
def rechazo_db(t_int, f):
    x = f * t_int
    return -20 * math.log10(abs(math.sin(math.pi * x) / (math.pi * x)))
RECHAZO = {(round(t * 1e3, 1), f): rechazo_db(t, f) for t in (1 / 60, 0.1) for f in (49.5, 50, 50.5, 59.5, 60, 60.5)}

if __name__ == "__main__":
    print(f"X0: C = {C_X0_TOT*1e12:.1f} pF → polo en {F_X0/1e3:.1f} kHz; a 20 kHz {CAIDA_X0_20K*100:.1f} %")
    print(f"divisor: τ = {TAU*1e6:.0f} µs; C_medio {C_MEDIO*1e12:.0f} pF (330 pF: {DESAJUSTE_MEDIO*100:+.1f} %), "
          f"C_bajo {C_BAJO*1e9:.2f} nF (3.0 nF: {DESAJUSTE_BAJO*100:+.1f} %); amortiguación {F_AMORT/1e3:.0f} kHz")
    for n, i, p, e in P42:
        print(f"P42 {n}: I {i*1e6:.4g} µA → {p:.3g} W de pico y {e*1e3:.3g} mJ por semiciclo y transistor "
              f"({p/P_MMBTA92*100:.0f} % de {P_MMBTA92} W)")
    for riel, cm in CM_OPA2188.items():
        print(f"riel {riel:.2f} V: modo común del OPA2188 hasta {cm:.2f} V; en vacío " +
              ", ".join(f"{n} {v:.2f}" for n, v in vacio(riel)))
    for b, (a, d) in ALFA.items():
        print(f"PNP β = {b}: corriente perdida {a*1e6:.0f} ppm; deriva ±5 °C {d*1e6:.0f} ppm")
    print(f"muestreo: R_eq = {R_EQ/1e6:.1f} MΩ")
    for r, c in REJILLA_RC:
        print(f"  R {r:g} Ω, C {c*1e9:.3g} nF (50 kHz): error lineal {r/R_EQ*1e6:.0f} ppm")
    for (t, f), db in RECHAZO.items():
        print(f"integración {t} ms, {f} Hz: {db:.1f} dB")
