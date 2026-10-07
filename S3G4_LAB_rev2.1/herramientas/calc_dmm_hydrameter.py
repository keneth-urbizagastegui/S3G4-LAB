# -*- coding: utf-8 -*-
"""Cifras propias del HydraMeter 0.4 (John Duffy), a partir de la netlist exportada con kicad-cli de
research_and_tests/HydraMeter_0.4/MMTR_AFE_00_04_TORELEASE/*.kicad_sch (dic. 2024), la bitacora de hackaday
(log 223270, sep. 2023) y el firmware Code/HackBoard_V02_10_shbrd_cal. Ejecutar: python calc_dmm_hydrameter.py"""
import math

def par(*r): return 1/sum(1/x for x in r)
def ser_c(*c): return 1/sum(1/x for x in c)

# --- Entrada de tension (hoja Volt_AFE) ---
R_TOP1 = 100e3 + 100e3        # R1 + R2, THT verticales 1/4 W, Vpin -> N1
R_TOP2 = 400e3 + 400e3        # R3 + R4, THT verticales 1/4 W, N1 -> N2 -> Vout
R_TOP = R_TOP1 + R_TOP2       # 1.0 MΩ
C54, C55 = 1.5e-9, 220e-12    # en paralelo con R1+R2 y con R3+R4 (pelicula THT)
R12, C73 = 9.1e6, 33e-12      # siempre de Vout a COM
PATAS = {"÷1.11": (None, 0.0), "÷11.1": (100e3, 1.8e-9), "÷148": (6.8e3, 27e-9)}   # R13/C59, R14/C61 por U1 (NL7WB66)
C_RT1 = 70e-12                # MOV de 230 Vrms en N1, capacidad segun el autor («about 70pF»); RT3 desconocida
V_LIM = 1.5                   # el autor limita a ±1.5 V respecto a COM (rieles de 0-3.3 V con COM a 1.65 V)

volt = {}
for n, (Rp, Cp) in PATAS.items():
    Rb = R12 if Rp is None else par(R12, Rp)
    Cb = C73 + Cp
    k = Rb / (R_TOP + Rb)
    # division capacitiva con la C de RT1 en N1 (C de RT2, RT3 y del PGA despreciadas)
    c_low = ser_c(C55, Cb)
    k_c = (C54 / (C54 + C_RT1 + c_low)) * (C55 / (C55 + Cb))
    f_c = 1 / (2 * math.pi * Rb * Cb)          # frecuencia a partir de la cual mandan los condensadores
    volt[n] = dict(Rb=Rb, k=k, div=1/k, Zin=R_TOP + Rb, fs=V_LIM / k, tau_b=Rb * Cb,
                   k_c=k_c, err_ac=k_c / k - 1, f_c=f_c)
TAU_TOP1, TAU_TOP2 = R_TOP1 * C54, R_TOP2 * C55

# --- Cascada de proteccion (bitacora: 10 kV de ejemplo) ---
V_MOV1, V_GDT, V_MOV3 = 400.0, 75.0, 5.0     # tension de sujecion aproximada segun el autor
I_N1_10kV = (10e3 - V_MOV1) / R_TOP1
I_N2 = (V_MOV1 - V_GDT) / 400e3
I_VOUT = (V_GDT - V_MOV3) / 400e3
I_RED = 325.0 / R_TOP                          # 230 Vrms de pico con el MOV de 230 Vrms sin conducir
P_R_RED = (230.0 / R_TOP) ** 2 * 100e3         # en cada resistencia de 100 kΩ, 230 Vrms continuos
P_R4_RED = (230.0 / R_TOP) ** 2 * 400e3

# --- Corriente (hoja Amp_AFE) ---
R15, R16, R17 = 10e-3, 0.33, 100.0
CORR = {   # rango: (resistencia vista entre el nodo medido y COM, fondo de escala segun la calibracion, ganancia del PGA)
    "A":  (R15, 3.0, 8),
    "mA": (R16 + R15, 0.501, 5),
    "µA": (R17 + R16 + R15, 1.418e-3, 8),
}
corr = {n: dict(R=R, I=I, V=R*I, V_adc=R*I*g, P=R*I*I) for n, (R, I, g) in CORR.items()}
I_FUSE_A, I_FUSE_mA = 16.0, 0.5               # F1 y F2 (valor de la netlist)
P_R15_16A = 16.0**2 * R15

# --- Ohmios (hoja Ohm_AFE) ---
V_RAIL = 9.5 - 0.6            # 9V5_Ohms del B0309S menos D2 (1N4007)
R_RANGO = [510.0, 10e3, 100e3, 1e6]          # R26..R29
R25 = 1e3                     # serie de proteccion, 1 W THT
V_D1 = 0.6
I_CORTO = [(V_RAIL - V_D1) / (R + R25) for R in R_RANGO]
G_SENSE = 3.3e3 / 1e3         # R30/R31: la caida en la R de rango se divide por 3.3
V_SHUNT_MAX = V_LIM * G_SENSE
V_GATE_LOWV = V_RAIL * 16e3 / (33e3 + 16e3)   # R32/R33 con Q8 conduciendo
FW_RANGOS = ["0–330 Ω", "330 Ω–15 kΩ", "15–150 kΩ", "> 150 kΩ"]   # textos del firmware

# --- ADC (MCP3461R) ---
VREF_ADC = 2.4
LSB = VREF_ADC / 2**15

if __name__ == "__main__":
    print(f"tau arriba: R1+R2·C54 {TAU_TOP1*1e6:.0f} µs, R3+R4·C55 {TAU_TOP2*1e6:.0f} µs")
    for n, v in volt.items():
        print(f"{n}: ÷{v['div']:.2f} Zin {v['Zin']/1e6:.3f} MΩ fondo ±{v['fs']:.1f} V  tau abajo {v['tau_b']*1e6:.0f} µs  "
              f"division capacitiva {v['k_c']:.4f} → error en alta frecuencia {v['err_ac']*100:+.1f} % desde ≈{v['f_c']:.0f} Hz")
    print(f"10 kV: {I_N1_10kV*1e3:.0f} mA por R1+R2, {I_N2*1e3:.2f} mA hacia el GDT, {I_VOUT*1e6:.0f} µA hacia RT3")
    print(f"230 Vrms: {I_RED*1e3:.2f} mA de pico; {P_R_RED*1e3:.1f} mW en cada 100 kΩ, {P_R4_RED*1e3:.1f} mW en cada 400 kΩ")
    for n, c in corr.items():
        print(f"{n}: {c['R']:.4g} Ω, {c['I']:.4g} A → {c['V']*1e3:.1f} mV en el derivador, {c['V_adc']:.2f} V tras el PGA, {c['P']*1e3:.1f} mW")
    print(f"R15 con 16 A: {P_R15_16A:.2f} W")
    print("ohmios, corriente en corto:", [f"{i*1e3:.3f} mA" for i in I_CORTO], f"caida maxima medible {V_SHUNT_MAX:.1f} V, puerta LowV {V_GATE_LOWV:.2f} V")
    print(f"ADC: LSB {LSB*1e6:.1f} µV (±2.4 V, 16 bits)")
