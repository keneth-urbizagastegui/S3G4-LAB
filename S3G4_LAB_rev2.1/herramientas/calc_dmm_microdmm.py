# -*- coding: utf-8 -*-
"""Cifras propias del Micro-DMM (Nicholas Mann, OIH Designs), a partir de research_and_tests/Micro-DMM/:
netlists exportadas con kicad-cli de PCBDesigns/DMM_KiCAD_V4_next, DMM Feather Redux, SimplifiedOpenLeadVoltmeter
y OpenLead_Headless_V3; firmware ArduinoProgrammingFiles/ (microDMM_RA4M1_XIAO_SMD_V5, OpenLeadDetect_Feather_Voltmeter,
BlinkyHawk_RA4M1); hoja «Calibrations» de DMM Collected Spreadsheets.xlsx; ADS1115 (SBAS444E, p. 5).
Ejecutar: python calc_dmm_microdmm.py"""
import math

# --- ADS1115 (SBAS444E p. 5): impedancias de entrada por fondo de escala (FSR) ---
FSR = [6.144, 4.096, 2.048, 1.024, 0.512, 0.256]
Z_CM = {6.144: 10e6, 4.096: 6e6, 2.048: 6e6, 1.024: 3e6, 0.512: 100e6, 0.256: 100e6}
Z_DIFF = {6.144: 22e6, 4.096: 15e6, 2.048: 4.9e6, 1.024: 2.4e6, 0.512: 710e3, 0.256: 710e3}
LSB = {f: f / 32768 for f in FSR}
GAIN_ERR_MAX = 0.0015               # 0.15 % max a ±2.048 V, 25 °C

def par(*r): return 1 / sum(1 / x for x in r)

# --- Voltimetro: puente de Mann en cuatro placas (resistencias de entrada por lado, brazo fijo, brazo conmutado) ---
VREF = 2.5                          # LM4040-2.5 (U10) alimentado por 4.7 kΩ desde 5V-iso
PLACAS = {
    "DMM_KiCAD_V4_next":           dict(Rin=499e3,     fijo=15e3, conm=1e6),    # Q8 + R24 1 MΩ en paralelo con R14 15 kΩ
    "DMM Feather Redux":           dict(Rin=2 * 240e3, fijo=1e6,  conm=15e3),   # Q8 + R24 15 kΩ; R14 1 MΩ fijo
    "SimplifiedOpenLeadVoltmeter": dict(Rin=499e3,     fijo=1e6,  conm=15e3),
    "OpenLead_Headless_V3":        dict(Rin=5 * 100e3, fijo=1e6,  conm=100e3),  # Q1 + R5 100 kΩ; R22 1 MΩ fijo
}
for p in PLACAS.values():
    p["Rb_on"] = par(p["fijo"], p["conm"])
    p["k_on"] = (2 * p["Rin"] + p["Rb_on"]) / p["Rb_on"]          # escala: V_entrada / V_puente
    p["k_off"] = (2 * p["Rin"] + p["fijo"]) / p["fijo"]
    p["rompe"] = p["fijo"] > 100e3                                # al abrir el MOSFET queda un brazo alto

# Escala del Simplified con la Z diferencial del ADS en paralelo con el puente (firmware: VOLTAGE_SCALE_full = -69.95)
S = PLACAS["SimplifiedOpenLeadVoltmeter"]
ESCALA = {f: (2 * S["Rin"] + par(S["Rb_on"], Z_DIFF[f])) / par(S["Rb_on"], Z_DIFF[f]) for f in FSR}
ESCALA_FW = 69.95
DESV = {f: ESCALA[f] / ESCALA_FW - 1 for f in FSR}               # error de usar una sola constante
V_MAX_FSR = {f: f * ESCALA[f] for f in FSR}                       # tension de entrada a fondo de cada FSR

# Red de 230 Vrms en la entrada del voltimetro (Simplified): tension y potencia en cada 499 kΩ 0805
V_RED = 230.0
I_RED = V_RED / (2 * S["Rin"] + S["Rb_on"])
V_R_RED, P_R_RED = I_RED * S["Rin"], I_RED**2 * S["Rin"]

# --- Cable abierto (Simplified, firmware OpenLeadDetect_Feather_Voltmeter: ADS1015 a ±2.048 V) ---
DIFF_CERR, DIFF_ABIE = 1.262, 1.706  # BRIDGE_BASELINE_V (~10 kΩ) y umbral «>10M» de bridgeResistanceLabel()
UMBRAL_FW = 1.42                     # vClosedThres
R_UP_CERR = par(S["fijo"], 2 * S["Rin"])
R_UP_ABIE = S["fijo"]
AIN1_CERR, AIN1_ABIE = VREF - DIFF_CERR, VREF - DIFF_ABIE
R_PD_CERR = AIN1_CERR / (DIFF_CERR / R_UP_CERR)                    # bajada efectiva que hace falta para esas lecturas
R_PD_ABIE = AIN1_ABIE / (DIFF_ABIE / R_UP_ABIE)
I_PUNTAS_CERR = DIFF_CERR / (2 * S["Rin"])                         # corriente por las puntas en la prueba
# White paper, figura 1: 500 k + 500 k y un ADC simulado con 10 MΩ; figura 2 añade 1 MΩ fijo
I_WP_FIG1 = VREF / (1e6 + 10e6)
I_WP_FIG2 = I_WP_FIG1 / 2

# --- Ohmimetro (V4_next) ---
I_FUENTE = 1.25 / 62.0               # LM317 con R5 62 Ω; firmware constantI = 0.02016 (placa 3: 0.020087)
R_PURGA = 330.0                      # R6 «330 R Circuit I Bleeder»
VZ, RS = 5.0, 22e3                   # U11 LM4040-5 y R9 22 kΩ (rango alto)
UMBRAL_RANGO = 400.0                 # OHMS_RANGE_THRESHOLD (±5 %)
def r_bajo(v): return v / (I_FUENTE - v / R_PURGA)                # formula del firmware, rango bajo
def v_bajo(r): return I_FUENTE * par(r, R_PURGA)
V_EN_UMBRAL = v_bajo(UMBRAL_RANGO)
I_DUT_UMBRAL = V_EN_UMBRAL / UMBRAL_RANGO
P_PURGA = VZ**2 / R_PURGA            # lo que gasta la purga con la fuente encendida y las puntas abiertas
LSB_10mOHM = 0.01 * I_FUENTE / LSB[0.256]                          # LSB del ADS en 10 mΩ a ±0.256 V
MOHM_POR_LSB = LSB[0.256] / I_FUENTE * 1e3

# Rango alto: amplificacion de errores S = (R + Rs)/Rs y efecto de carga del ADS
Z_ADS_SE = par(Z_CM[6.144], Z_DIFF[6.144])                       # aproximacion para la entrada unipolar a ±6.144 V
R_PRUEBA = [1e3, 10e3, 100e3, 330e3, 1e6, 4.7e6]
ALTO = {}
for r in R_PRUEBA:
    s = (r + RS) / RS
    v = VZ * r / (r + RS)
    carga = par(r, Z_ADS_SE) / r - 1
    vz_err = (lambda v_true: RS * v_true / (VZ - v_true) / r - 1)(4.994 * r / (r + RS))   # 6 mV menos de referencia
    ALTO[r] = dict(S=s, v=v, lsb_pct=s * LSB[6.144] / v, gain_pct=s * GAIN_ERR_MAX, carga=carga, vz6mV=vz_err)

# Seccion H (R_ref ≈ 1.5 × fondo): misma S a fondo de rango
S_H_FONDO = (1 + 1.5) / 1.5

# --- Calibracion medida: hoja «Calibrations» (valor real, lectura de las placas 1-1, 1-2, 1-3 antes de corregir) ---
CAL = [  # letra, nominal, real, lecturas
    ("A", 0.5, 0.491, (0.5, 0.47492, 0.4976)),
    ("B", 1, 0.997, (1.0173, 0.98665, 0.99628)),
    ("C", 4.7, 4.651, (4.7352, 4.67061, 4.657)),
    ("D", 10, 10.021, (10.272, 10.1489, 10.05)),
    ("E", 33, 32.91, (30.749, 34.03932, 33.07)),
    ("F", 100, 99.49, (98.221, 98.20018, 99.88)),
    ("G", 330, 331.5, (329.4, 330.07413, 332.5)),
    ("H", 1e3, 1000.1, (1000.492, 999.77908, 995.6776)),
    ("I", 3e3, 3002, (3004.04, 3004.83235, 2992.8354)),
    ("J", 10e3, 9928, (9945.82, 9944.46693, 9905.3516)),
    ("K", 33e3, 32970, (33081.32, 33002.20861, 32825.832)),
    ("L", 100e3, 100090, (100973.83, 100404.04012, 99177.039)),
    ("M", 333e3, 326400, (336925.69, 327829.59458, 319441.656)),
    ("N", 1e6, 1038500, (1144097.75, 1078753.77995, 968296.4375)),
    ("O", 4.7e6, 4705000, (6443228.5, 6787841.52495, 3834936.25)),
]
CAL_ERR = [(l, n, [lec / real - 1 for lec in lecs]) for l, n, real, lecs in CAL]

# --- P33: cable abierto con resistencias definidas, en nuestra arquitectura (seccion H + P17) ---
R_PROT_H, R_TOP_H = 99e3, 10e6       # R_PROT de 3 × 33 kΩ y la resistencia de arriba de P17
R_B = 10e6                           # variante A: brazo de sesgo de la toma a VREF
VREF_H = 2.5
RX = [0, 100e3, 1e6, 10e6, 100e6, math.inf]
def toma_A(rx):
    if rx == math.inf: return VREF_H
    r = R_PROT_H + R_TOP_H + rx
    return VREF_H * r / (r + R_B)
V_FUENTE_H, R_REF_20M, R_DIV_H = 4.9, 10e6, R_PROT_H + R_TOP_H   # variante B: fuente de ohmios en el rango de 20 MΩ
def borne_B(rx):
    rp = R_DIV_H if rx == math.inf else par(rx, R_DIV_H) if rx > 0 else 0.0
    return V_FUENTE_H * rp / (rp + R_REF_20M)
I_MAX_A = VREF_H / (R_PROT_H + R_TOP_H + R_B)
I_MAX_B = V_FUENTE_H / R_REF_20M
TAU_NODO = par(R_TOP_H + R_PROT_H, R_B) * 20e-12                   # toma con ≈ 20 pF (4051 + compensacion + buffer)
TAU_CABLE = (R_PROT_H + R_TOP_H + R_B) * 100e-12                   # puntas abiertas con ≈ 100 pF entre ellas
T_CUARTO_50HZ = 1 / 50 / 4

if __name__ == "__main__":
    for n, p in PLACAS.items():
        print(f"{n}: escala ÷{p['k_on']:.2f} (MOSFET conduce) / ÷{p['k_off']:.2f} (abierto); "
              f"{'rompe el puente' if p['rompe'] else 'NO rompe el puente: el brazo fijo es de 15 kΩ'}")
    for f in FSR:
        print(f"±{f} V: Zdiff {Z_DIFF[f]/1e3:g} kΩ → escala {ESCALA[f]:.2f} ({DESV[f]*100:+.2f} % frente a 69.95); "
              f"fondo = {V_MAX_FSR[f]:.1f} V")
    print(f"230 Vrms: {I_RED*1e3:.2f} mA; {V_R_RED:.0f} Vrms ({V_R_RED*math.sqrt(2):.0f} Vpk) y {P_R_RED*1e3:.0f} mW por 499 kΩ")
    print(f"cable abierto: AIN1 {AIN1_CERR:.3f} V cerrado / {AIN1_ABIE:.3f} V abierto → bajada efectiva "
          f"{R_PD_CERR/1e3:.0f} kΩ / {R_PD_ABIE/1e3:.0f} kΩ; puntas {I_PUNTAS_CERR*1e6:.2f} µA; "
          f"white paper {I_WP_FIG1*1e9:.0f} nA / {I_WP_FIG2*1e9:.0f} nA")
    print(f"fuente {I_FUENTE*1e3:.2f} mA; en {UMBRAL_RANGO:.0f} Ω: {V_EN_UMBRAL:.3f} V y {I_DUT_UMBRAL*1e3:.2f} mA por el DUT; "
          f"purga {P_PURGA*1e3:.0f} mW; 10 mΩ = {LSB_10mOHM:.1f} LSB; {MOHM_POR_LSB:.2f} mΩ/LSB")
    for r, a in ALTO.items():
        print(f"{r:>9.0f} Ω: S {a['S']:.1f}; LSB {a['lsb_pct']*100:.3f} %; error de ganancia 0.15 % → {a['gain_pct']*100:.1f} %; "
              f"carga del ADS {a['carga']*100:+.1f} %; 6 mV de referencia {a['vz6mV']*100:+.1f} %")
    print(f"sección H a fondo: S = {S_H_FONDO:.2f}")
    for l, n, e in CAL_ERR:
        print(f"{l} {n:>9g}: " + " ".join(f"{x*100:+6.2f} %" for x in e))
    for rx in RX:
        print(f"P33 Rx = {rx:>8g}: A toma {toma_A(rx):.3f} V; B borne {borne_B(rx):.3f} V")
    print(f"P33 corriente máx.: A {I_MAX_A*1e9:.0f} nA, B {I_MAX_B*1e9:.0f} nA; τ toma {TAU_NODO*1e6:.0f} µs; "
          f"τ con 100 pF de cable {TAU_CABLE*1e3:.1f} ms; cuarto de periodo a 50 Hz {T_CUARTO_50HZ*1e3:.0f} ms")
