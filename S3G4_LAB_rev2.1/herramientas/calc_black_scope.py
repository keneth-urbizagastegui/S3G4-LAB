# -*- coding: utf-8 -*-
"""Cifras del analisis de black_scope. Toda cifra derivada de la pagina sale de aqui.
Fuentes: netlist/esquematico de research_and_tests/black_scope (hardware/black_scope), firmware
software/stm32g4_scope (y _lvgl), DS12712 Rev 5 (tablas 61, 62, 69, 75) y RM0440 Rev 9."""
import math, itertools

k, T = 1.380649e-23, 300.0
VCC = 3.3                                   # +3.3VA: alimenta divisor, LMV324, VREF+ (via L2/C8) y DAC
RS, RUP, RDN, CIN = 8.2e3, 2.7e3, 4.3e3, 100e-12   # R5, R11, R12, C23 (canal 1; iguales en los 4)
TOL = 0.005                                 # nota del esquematico: "0.5% tolerance"
def par(a, b): return a * b / (a + b)

RP = par(RUP, RDN)
VTH = VCC * RDN / (RUP + RDN)
G_IN = RP / (RS + RP)                       # V/V desde el conector al nodo
V0 = VTH * RS / (RS + RP)                   # nodo con la entrada a 0 V
ZIN = RS + RP
RNODE = par(RS, RP)
FC = 1 / (2 * math.pi * RNODE * CIN)
VIN_MIN = (0 - V0) / G_IN                   # nodo a 0 V
VIN_MAX_RAIL = (VCC - V0) / G_IN            # nodo a 3.3 V
LMV_CM_MARGIN = 0.8                         # LMV324 de TI: modo comun hasta VCC-0.8 V (tipico, no esta en el repo)
VIN_MAX_CM = (VCC - LMV_CM_MARGIN - V0) / G_IN
VIN_OPEN = (VTH - V0) / G_IN                # lo que muestra la entrada al aire

v0s = []
for a, b, c in itertools.product((-1, 1), repeat=3):
    rs, ru, rd = RS * (1 + TOL * a), RUP * (1 + TOL * b), RDN * (1 + TOL * c)
    rp = par(ru, rd); v0s.append(VCC * rd / (ru + rd) * rs / (rs + rp))
DV0 = (max(v0s) - min(v0s)) / 2             # +/- entre canales, en el nodo
DV0_IN = DV0 / G_IN

# PGA interno (DS12712 T.75): ganancias, R1 = 10 kOhm, BW = GBW/G, ruido
GAINS = [2, 4, 8, 16, 32, 64]
N = 4096
GBW_TYP, GBW_MIN = 13e6, 7e6
SR_NORMAL = (2.5e6, 6.5e6)                  # V/s min, tip
R1_PGA = 10e3
span_in = {g: VCC / (g * G_IN) for g in GAINS}          # tramo de entrada que cabe en el ADC
lsb_in = {g: VCC / N / (g * G_IN) for g in GAINS}
vbias = {g: (g * V0 - VCC / 2) / (g - 1) for g in GAINS}  # VINM0 que centra 0 V en mitad del ADC
bw_pga = {g: (GBW_MIN / g, GBW_TYP / g) for g in GAINS}
i_bias_pin = {g: (VCC / 2) / g / R1_PGA for g in GAINS}  # corriente por VINM0 con el ADC a fondo, por canal
dv0_adc = {g: g * DV0 for g in GAINS}                     # desalineo entre canales en el ADC
dac_lsb_move = {g: (g - 1) * VCC / N for g in GAINS}      # un LSB del DAC2 mueve la salida (g-1) LSB
FPBW_3V = (SR_NORMAL[0] / (math.pi * 3.2), SR_NORMAL[1] / (math.pi * 3.2))  # 3.2 Vpp sin limitar por SR

# Ruido (orden de magnitud)
EN_R = math.sqrt(4 * k * T * RNODE)
EN_LMV = 39e-9                              # LMV324 TI tipico a 1 kHz (no esta en el repo)
EN_OPA_10K, EN_OPA_1K = 90e-9, 250e-9       # DS12712 T.75
F_LMV = 1e6                                 # GBW del LMV324 (seguidor)
def noise_in(g):
    bw = min(FC, F_LMV, GBW_TYP / g)
    en_node = math.sqrt(EN_R**2 + EN_LMV**2 + EN_OPA_10K**2)
    vn = en_node * math.sqrt(1.57 * bw) / G_IN
    return bw, vn
noise = {g: noise_in(g) for g in GAINS}

# ADC
HCLK = 170e6; FADC = HCLK / 4               # ADC_CLOCK_SYNC_PCLK_DIV4
TS_CFG = 2.5 / FADC
TS_OPAMP_MIN = 200e-9                       # DS12712 T.75, TS_OPAMP_VOUT, VDDA >= 2 V
SMP = [2.5, 6.5, 12.5, 24.5, 47.5, 92.5, 247.5, 640.5]
SMP_OK = next(s for s in SMP if s / FADC >= TS_OPAMP_MIN)
FS_CFG = FADC / (2.5 + 12.5)
FS_OK = FADC / (SMP_OK + 12.5)
UI_MAX = 2500e3                             # ui_build_horizontal.c: escala 0..2500 kHz
AWD2_STEP = 16                              # AWD2/AWD3: 8 bits (RM0440 21.4.28)
trig_step_in = {g: AWD2_STEP * VCC / N / (g * G_IN) for g in GAINS}
SCALE_MIN_OK = HCLK / (2 * 65536) / 1000    # kSa/s: por debajo el prescaler de 16 bits desborda (version Nuklear)
LEN = 512
BUF_BYTES = 8 * LEN * 2

# DAC2 como polarizacion
CL_MAX = 50e-12; CL_BS = 100e-9
CL_FACTOR = CL_BS / CL_MAX

# Generador: DAC1 + LMV358, 512 puntos
DAC_LEN = 512; DAC_MAX = 1e6
F_FULL = DAC_MAX / DAC_LEN
def gen_real(f):
    psc = int((HCLK / (f * DAC_LEN)) / 2 - 1)
    fs = HCLK / (2 * (psc + 1)); return fs / DAC_LEN, fs
gen = {f: gen_real(f) for f in (100, 1000, 5000, 10000, 20000)}

# Proteccion: sobretension en la entrada
VD = 0.6
def clamp(vin):
    vn = VCC + VD if vin > 0 else -VD
    i_rs = (vin - vn) / RS
    i_div = (vn - VCC) / RUP + vn / RDN
    return i_rs, i_rs - i_div, (vin - vn) ** 2 / RS
prot = {v: clamp(v) for v in (20, 50, 325)}

if __name__ == "__main__":
    print(f"G_IN={G_IN:.5f} V0={V0:.4f} V ZIN={ZIN/1e3:.3f} k FC={FC/1e6:.3f} MHz")
    print(f"VIN {VIN_MIN:.2f} .. {VIN_MAX_RAIL:.2f} V (CM LMV: {VIN_MAX_CM:.2f}) abierta={VIN_OPEN:.3f} V")
    print(f"DV0=+/-{DV0*1e3:.2f} mV nodo = +/-{DV0_IN*1e3:.1f} mV entrada")
    for g in GAINS:
        bw, vn = noise[g]
        print(f"G{g}: span={span_in[g]:.3f} V lsb={lsb_in[g]*1e6:.0f} uV vb={vbias[g]:.4f} BW={bw_pga[g][0]/1e3:.0f}-{bw_pga[g][1]/1e3:.0f} kHz "
              f"Ib={i_bias_pin[g]*1e6:.1f} uA dv0adc={dv0_adc[g]*1e3:.0f} mV ruido={vn*1e3:.3f} mV ({vn/span_in[g]*100:.2f}% tramo) trig={trig_step_in[g]*1e3:.1f} mV")
    print(f"ADC {FADC/1e6:.1f} MHz ts={TS_CFG*1e9:.1f} ns vs {TS_OPAMP_MIN*1e9:.0f} ns -> SMP {SMP_OK} -> {FS_OK/1e6:.2f} MSa/s (cfg {FS_CFG/1e6:.2f})")
    print(f"escala min {SCALE_MIN_OK:.3f} kSa/s; DAC2 CL x{CL_FACTOR:.0f}; FPBW {FPBW_3V[0]/1e3:.0f}-{FPBW_3V[1]/1e3:.0f} kHz; F_FULL {F_FULL:.0f} Hz")
    for f, (fr, fs) in gen.items(): print(f"gen {f} Hz -> {fr:.1f} Hz ({(fr/f-1)*100:+.2f} %), {fs/1e6:.3f} MSa/s")
    for v, (i, idd, p) in prot.items(): print(f"{v} V: I_R5={i*1e3:.2f} mA, al diodo {idd*1e3:.2f} mA, P_R5={p:.3f} W")
