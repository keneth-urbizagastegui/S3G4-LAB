# -*- coding: utf-8 -*-
"""Cifras propias del TIDA-00879 (DMM de 4 1/2 digitos de TI con el MSP430F6736), a partir del esquematico
research_and_tests/TIDA-00879/tidrmi4.pdf (hoja 3, AFE), la BOM tidrmi5.pdf y la guia tidubm4.pdf (TIDUBM4A).
Ejecutar: python calc_dmm_tida00879.py"""
import math

def par(*r): return 1/sum(1/x for x in r)

R_IN, C_IN = 10.0e6, 100e-12          # R19 CRHV1206 10.0 MΩ (alta tension, 0.3 W) ∥ C27 100 pF C0G 100 V
R_IN60, C_IN60 = 499e3, 100e-12       # R20 499 kΩ 0402 ∥ C30 100 pF (puente J7, solo 60 mV)
R_SIEMPRE = 100e6                     # R13 100 MΩ 0603 (5 %) + R17 0 Ω, con el trimmer C34 4.5-20 pF
C34 = (4.5e-12, 20e-12)
PATAS = {   # rango: (R de la pata, C fija, trimmer)
    "60 V":   (9.09e3 + 10.0, 1800e-12 + 8200e-12 + 0.1e-6, None),   # R10+R14; C41+C42+C23
    "6 V":    (90.9e3 + 931.0, 910e-12 + 0.01e-6, None),             # R11+R15; C43+C44
    "600 mV": (1.00e6 + 10.2e3, 470e-12 + 510e-12, (4.5e-12, 20e-12)),  # R12+R16; C38+C25 + C33
}
rangos = {}
for n, (Rp, Cp, trim) in PATAS.items():
    Rb = par(Rp, R_SIEMPRE); k = Rb / (R_IN + Rb)
    vfs = float(n.split()[0]) * (1e-3 if "mV" in n else 1)
    tau = (Rp * (Cp + trim[0]), Rp * (Cp + trim[1])) if trim else (Rp * Cp, Rp * Cp)
    rangos[n] = dict(k=k, div=1/k, v_toma=vfs*k, tau=tau, Zin=R_IN + Rb)
k60 = R_SIEMPRE / (R_IN + R_SIEMPRE)
k60b = R_SIEMPRE / (R_IN60 + R_SIEMPRE)
rangos["60 mV"] = dict(k=k60, div=1/k60, v_toma=60e-3*k60, tau=(R_SIEMPRE*C34[0], R_SIEMPRE*C34[1]), Zin=R_IN + R_SIEMPRE)
rangos["60 mV (J7 en 499 kΩ)"] = dict(k=k60b, div=1/k60b, v_toma=60e-3*k60b, tau=(R_SIEMPRE*C34[0], R_SIEMPRE*C34[1]), Zin=R_IN60 + R_SIEMPRE)
TAU_IN = R_IN * C_IN
C34_IDEAL = TAU_IN / R_SIEMPRE        # 10 pF para cerrar 1 ms en la pata de 100 MΩ

# Referencia (borne rojo J6): AVCC/2 con R6/R8 100 k, OPA333 (U3) y R7 4.7 Ω
AVCC = 2.4
V_REF = AVCC / 2

# ADC SD24_B del MSP430F6736 (guia 4.2)
F_MOD, OSR, PGA = 2e6, 64, 16
FS_ADC = F_MOD / OSR                  # 31.25 kSa/s («32K»)
N_ACC = 4096
LECTURAS_S = FS_ADC / N_ACC           # ≈ 7.6 («8 por segundo»)
V_ADC_FS = 54.5e-3 * PGA              # toma a fondo × ganancia

# Corriente (borne azul J9 → R22 → R23 → F1 → borne rojo J6)
R22, R23 = 95.3, 0.5                  # R22 1 W 2512; R23 0603
corr = {"600 µA": (R22 + R23, 600e-6), "60 mA": (R23, 60e-3)}
corr = {n: dict(R=R, I=I, V=R*I, P=R*I*I) for n, (R, I) in corr.items()}

# Energia (tabla 4, 3.6 V)
I_MODOS = {"DC tensión": 1.61e-3, "DC corriente": 1.73e-3, "AC tensión": 1.70e-3, "AC corriente": 1.80e-3, "potencia": 2.55e-3, "apagado": 13e-6}
V_BAT = 3.6

if __name__ == "__main__":
    for n, r in rangos.items():
        print(f"{n:22s} ÷{r['div']:8.2f}  toma {r['v_toma']*1e3:6.2f} mV  Zin {r['Zin']/1e6:6.1f} MΩ  tau {r['tau'][0]*1e3:.2f}–{r['tau'][1]*1e3:.2f} ms")
    print(f"tau entrada {TAU_IN*1e3:.2f} ms; C34 ideal {C34_IDEAL*1e12:.0f} pF; referencia {V_REF:.2f} V")
    print(f"ADC {FS_ADC/1e3:.2f} kSa/s, {LECTURAS_S:.1f} lecturas/s, ±{V_ADC_FS:.2f} V tras el PGA ×{PGA}")
    for n, c in corr.items():
        print(f"{n}: {c['R']} Ω, {c['V']*1e3:.1f} mV, {c['P']*1e3:.2f} mW")
    print({k: f"{v*V_BAT*1e3:.2f} mW" for k, v in I_MODOS.items()})
