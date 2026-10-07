# -*- coding: utf-8 -*-
"""Cifras propias del TIDA-01012 (DMM de 4 1/2 digitos de TI), sacadas del esquematico
research_and_tests/TIDA-01012/tidrny5 (2).pdf (hoja 3, WirelessDMM_AFE) y de la guia tidubv5b (1).pdf.
Cada constante lleva la pieza de la que sale. Ejecutar: python calc_dmm_tida01012.py"""
import math

k_B, T = 1.380649e-23, 300.0
def par(*r): return 1/sum(1/x for x in r)
def ruido(R): return math.sqrt(4*k_B*T*R)            # V/sqrt(Hz)

# --- Divisor de tension (hoja 3, "Voltage Front End") ---
R_IN, C_IN = 10.0e6, 100e-12          # R16 10.0 MΩ ∥ C22 100 pF (S2 en la posicion normal)
R_IN50, C_IN50 = 499e3, 22e-9         # R17 499 kΩ ∥ C23 0.022 µF (S2 en la posicion de 50 mV)
R_SIEMPRE = 100e6                     # R9 100 MΩ + R13 0 Ω, siempre a COM (C18, C19 sin montar)
PATAS = {                             # rango: (R de la pata, C de la pata, salida del TS5A3359)
    "50 V":   (9.76e3 + 10.0, 1200e-12 + 1200e-12 + 0.1e-6, "NO2"),   # R6+R10; C10+C11+C12
    "5 V":    (100e3 + 0.0,   10e-12 + 0.01e-6,              "NO1"),   # R7+R11; C13+C14
    "500 mV": (1.00e6 + 10.2e3, 330e-12 + 470e-12 + 150e-12, "NO0"),   # R8+R12; C15+C16+C17
}
RON_U4 = 1.0                          # TS5A3359: ≈1 Ω (hoja de TI, ti.com/product/TS5A3359)

rangos = {}
for nombre, (Rp, Cp, sw) in PATAS.items():
    Rb = par(Rp + RON_U4, R_SIEMPRE)
    k = Rb / (R_IN + Rb)
    vfs = float(nombre.split()[0]) * (1e-3 if "mV" in nombre else 1)
    rangos[nombre] = dict(R_baja=Rb, k=k, div=1/k, v_toma=vfs*k, tau_pata=Rp*Cp, sw=sw,
                          ron_err=RON_U4/Rp, thev=par(R_IN, Rb))
# 50 mV: S2 cambia la resistencia de entrada a 499 kΩ y no hay pata (solo R9)
k50 = R_SIEMPRE / (R_IN50 + R_SIEMPRE)
rangos["50 mV"] = dict(R_baja=R_SIEMPRE, k=k50, div=1/k50, v_toma=50e-3*k50, tau_pata=None, sw="ninguna",
                       ron_err=0.0, thev=par(R_IN50, R_SIEMPRE))
TAU_IN = R_IN * C_IN                  # 1 ms
TAU_IN50 = R_IN50 * C_IN50            # 11 ms
Z_IN = {n: (R_IN50 if n == "50 mV" else R_IN) + r["R_baja"] for n, r in rangos.items()}
# C equivalente que deja libre la pata de 1 MΩ para cerrar 1 ms
CEQ_PATA_500mV = TAU_IN / (PATAS["500 mV"][0]) - PATAS["500 mV"][1]

# --- Ruido termico en la toma con el ancho de banda del promedio de 32 K muestras ---
FS_ADC = 210e3                        # ≈210 kSa/s (guia, figura 21)
N_PROM = 32 * 1024                    # 32 K muestras por lectura (guia, 2.4.1.5)
T_LECT = N_PROM / FS_ADC              # s por lectura
ENBW = 1 / (2 * T_LECT)               # ancho de banda de ruido de un promedio rectangular
for r in rangos.values():
    r["e_n"] = ruido(r["thev"])
    r["vn_rms"] = r["e_n"] * math.sqrt(ENBW)
VN_50mV_CON_10M = ruido(par(R_IN, R_SIEMPRE)) * math.sqrt(ENBW)   # si en 50 mV se usara R16

# --- Buffers y FDA (hoja 3, "Single Input, Differential Output Buffer/Gain Stage") ---
G_FDA = 133e3 / 3.01e3                # R19/R4 = R23/R14 (THS4531)
V_ADC_FS = 2.2                        # ±2.2 V diferenciales (guia 2.4.1.2)
VREF = 2.5                            # REF3325
LSB_ADC = 2 * VREF / 2**18            # ADS8885, 18 bits diferenciales
V_TOMA_FS = 50e-3                     # ±50 mV en la toma en todos los rangos
CUENTAS = 50000
V_CUENTA_TOMA = V_TOMA_FS / CUENTAS               # 1 µV en la toma
V_CUENTA_ADC = V_CUENTA_TOMA * G_FDA              # en el ADC
LSB_POR_CUENTA = V_CUENTA_ADC / LSB_ADC
LECTURAS_S = FS_ADC / N_PROM

# Filtro anti-alias: R5/R15 52.3 Ω y C20 2.2 nF diferencial
R_AA, C_AA = 52.3, 2.2e-9
F_AA = 1 / (2 * math.pi * 2 * R_AA * C_AA)
# Filtro de la referencia: R3 10.0 kΩ, C7 4.7 µF
F_REF = 1 / (2 * math.pi * 10e3 * 4.7e-6)
# VCM y COM: VREF por R21 11.3 kΩ / R24 13.3 kΩ, buffer OPA333 (U9), R55 1.0 kΩ, C27 1 µF
V_CM = VREF * 13.3e3 / (11.3e3 + 13.3e3)
F_CM = 1 / (2 * math.pi * 1.0e3 * 1e-6)

# --- Corriente (hoja 3, "Current Front End") ---
R20, R25 = 95.3, 0.5
SHUNT = {"500 µA": (R20 + R25, 500e-6), "50 mA": (R25, 50e-3)}
corr = {n: dict(R=R, I=I, V=R*I, P=R*I*I, cuenta=I/CUENTAS, v_cuenta=R*I/CUENTAS) for n, (R, I) in SHUNT.items()}
F1_HOLD = 0.2                         # NANOSMDC020F-2, 0.2 A (Littelfuse)

# --- Sobretension en la entrada de tension (la guia admite que no hay proteccion) ---
V_ESD = 2.7 + 0.3                     # la toma se apoya en los diodos internos a V2P7 (≈3 V)
I_SOBRE = {n: (325 - V_ESD) / (R_IN50 if n == "50 mV" else R_IN) for n in rangos}   # 230 Vrms de pico

# --- Energia (guia, tabla 13) ---
I_ACTIVO, I_APAGADO, V_BAT = 5.2e-3, 25e-6, 3.7

if __name__ == "__main__":
    print(f"Ganancia del THS4531 = {G_FDA:.2f}; una cuenta = {V_CUENTA_TOMA*1e6:.1f} µV en la toma = "
          f"{V_CUENTA_ADC*1e6:.1f} µV en el ADC = {LSB_POR_CUENTA:.2f} LSB de 18 bits")
    print(f"{LECTURAS_S:.1f} lecturas/s; ENBW del promedio {ENBW:.2f} Hz")
    print(f"tau entrada {TAU_IN*1e3:.2f} ms; C libre para Ceq en la pata de 1 MΩ {CEQ_PATA_500mV*1e12:.0f} pF")
    for n, r in rangos.items():
        tau = f"{r['tau_pata']*1e3:.3f} ms" if r["tau_pata"] else "—"
        print(f"{n:7s} ÷{r['div']:8.2f}  toma {r['v_toma']*1e3:6.2f} mV  tau {tau:9s}  Zin {Z_IN[n]/1e6:6.1f} MΩ  "
              f"Ron/Rpata {r['ron_err']*1e6:5.0f} ppm  Thevenin {r['thev']/1e3:8.1f} kΩ  en {r['e_n']*1e9:5.0f} nV/√Hz  "
              f"vn {r['vn_rms']*1e6:.2f} µVrms  Isobre {I_SOBRE[n]*1e6:.0f} µA")
    print(f"50 mV con R16 en vez de R17: vn {VN_50mV_CON_10M*1e6:.2f} µVrms")
    print(f"AA {F_AA/1e3:.0f} kHz; filtro de referencia {F_REF:.1f} Hz; VCM {V_CM:.3f} V; filtro de VCM {F_CM:.0f} Hz")
    for n, c in corr.items():
        print(f"{n}: derivador {c['R']} Ω, {c['V']*1e3:.1f} mV a fondo, {c['P']*1e3:.2f} mW, cuenta {c['cuenta']*1e9:.0f} nA = {c['v_cuenta']*1e9:.0f} nV")
    print(f"Consumo {I_ACTIVO*V_BAT*1e3:.1f} mW activo, {I_APAGADO*V_BAT*1e6:.0f} µW apagado")
