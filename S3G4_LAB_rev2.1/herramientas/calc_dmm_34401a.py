# -*- coding: utf-8 -*-
"""Cifras propias del Agilent/Keysight 34401A, a partir de research_and_tests/Agilent_34401A/34401A_Service_Guide.pdf
(ed. 9, 2014): especificaciones (pp. 20-23), teoria (pp. 100-115), autopruebas (pp. 128-132) y esquemas (pp. 157-160).
Para la seccion H: 74HC4051 de Nexperia (datasheet - componentes/74HC_HCT4051.pdf, rev. 12, p. 10).
Ejecutar: python calc_dmm_34401a.py"""
import math, cmath

# --- Especificaciones de 1 año (23 ± 5 °C), % de lectura + % de rango (p. 20) ---
DCV_1A = {"100 mV": (0.0050, 0.0035), "1 V": (0.0040, 0.0007), "10 V": (0.0035, 0.0005),
          "100 V": (0.0045, 0.0006), "1000 V": (0.0045, 0.0010)}
IB_34401 = 30e-12                               # < 30 pA a 25 °C

# --- Fuente de ohmios (p. 106 y hoja 3): IREF de la referencia de 7 V ---
V7 = 7.0
R_IREF = {"alta": 40e3, "baja": 400e3}          # R202 / R201
R_2857 = 28.57e3
V_FUERZA = {k: V7 / r * R_2857 for k, r in R_IREF.items()}       # ≈ 5 V y 0.5 V
RANGOS_OHM = {"100 Ω y 1 kΩ": (5e3, "alta"), "10 kΩ": (50e3, "alta"), "100 kΩ": (500e3, "alta"),
              "1 MΩ": (1e6, "alta"), "10 MΩ y 100 MΩ": (1e6, "baja")}
I_OHM = {n: V_FUERZA[s] / r for n, (r, s) in RANGOS_OHM.items()}
def lectura_ohm(deriva_ref):
    """La corriente y la ganancia del ADC salen de la misma referencia: la deriva se cancela."""
    i = (1 + deriva_ref)                         # la corriente sube con la referencia
    g_adc = 1 / (1 + deriva_ref)                 # el ADC lee menos cuentas por voltio
    return i * g_adc - 1
ESCALONES, VCB_MIN = 4, 250                      # 4 transistores en serie para ±1000 V
R_POL = 196e3                                    # R203-R206

# --- Alternativa barata para RD-10 (P42): MMBTA92 (300 V) + 1N4007W (1 kV) de LCSC ---
V_RED_PICO = 230 * math.sqrt(2)
N_MMBTA92 = math.ceil(V_RED_PICO * 1.5 / 300)    # con un 50 % de margen
COSTE_P42 = N_MMBTA92 * 0.0288 + 0.009 + N_MMBTA92 * 0.002   # transistores, diodo y resistencias (USD)

# --- Condensador programable del atenuador de alterna (hoja 4) ---
C306, PASOS = 5.6e-12, 256
C_PASO = C306 / PASOS
R_IN_AC, R304, C302, C304 = 1e6, 200e3, 1.8e-12, 6.8e-12
G_AC = R304 / R_IN_AC                            # ×0.2
C_FB_PLANO = C302 / G_AC                         # capacidad de realimentacion para respuesta plana
P_PLANO = (C_FB_PLANO - C304) / C306 * PASOS     # paso del DAC que la da (sin R313)

# --- P39: error de un divisor compensado con las τ desparejadas ---
def h_div(f, k, tau_top, m):
    """Respuesta relativa |H(f)/H(0)| de un divisor con τ_pata = τ_arriba·(1+m), razon k = Rb/(Rt+Rb)."""
    rt = 1.0; rb = k / (1 - k) * rt
    ct = tau_top / rt; cb = tau_top * (1 + m) / rb
    s = 2j * math.pi * f
    zt = rt / (1 + s * rt * ct); zb = rb / (1 + s * rb * cb)
    return abs(zb / (zt + zb)) / k
TAU_TOP = 10e6 * 6e-12                           # 60 µs: 10 MΩ con 6 pF, como el 121GW
FRECS = [1e3, 5e3, 10e3, 20e3]
DESAJUSTES = [0.01, 0.02, 0.05]
ERR_AC = {m: [h_div(f, 0.1, TAU_TOP, m) - 1 for f in FRECS] for m in DESAJUSTES}

# --- P40: rechazo de la red integrando un tiempo T ---
def rechazo_db(f, t):
    x = math.pi * f * t
    return float("inf") if abs(math.sin(x)) < 1e-12 else -20 * math.log10(abs(math.sin(x) / x))
RECH = {"60 Hz con 20 ms (ajuste de 50 Hz)": rechazo_db(60, 0.020),
        "60 Hz con 16.67 ms": rechazo_db(60.6, 1 / 60),
        "50 Hz con 16.67 ms (ajuste de 60 Hz)": rechazo_db(50, 1 / 60),
        "50 Hz y 60 Hz con 100 ms (5 y 6 ciclos)": min(rechazo_db(50.5, 0.1), rechazo_db(60.6, 0.1))}

# --- P38: carga que inyecta el mux al volver del autocero ---
C_Z, C_OPA = 25e-12, 5e-12                       # 74HC4051: Csw del comun Z (p. 10); entrada del OPA2188 (supuesto)
C_S = C_Z + C_OPA
CUENTA_REL = 0.1e-3 / 2.0                        # 1 cuenta = 100 µV de 2 V
TOMAS = {"÷10 (pata de 1.11 MΩ)": (10e6, 1.11e6), "÷100 (pata de 101 kΩ)": (10e6, 101e3)}
ASIENTO = {}
for n, (rt, rb) in TOMAS.items():
    c_tap = TAU_TOP / rt + TAU_TOP / rb          # compensacion arriba + pata
    salto = C_S / (C_S + c_tap)
    tau = (rt * rb / (rt + rb)) * (c_tap + C_S)
    ASIENTO[n] = dict(c_tap=c_tap, salto=salto, tau=tau, t=tau * math.log(salto / CUENTA_REL))

# --- Fugas: 34401A frente a nuestra cadena ---
IS_OFF_MAX = 0.1e-6                              # 74HC4051, por canal, 25 °C (max)
IB_OPA2188 = 850e-12
R_TOMA10 = 1 / (1 / (10e6 + 99e3) + 1 / 1.11e6)
FUGA_CUENTAS = {"34401A (30 pA)": IB_34401 * R_TOMA10 / 1e-4,
                "OPA2188 (850 pA máx.)": IB_OPA2188 * R_TOMA10 / 1e-4,
                "74HC4051 (0.1 µA máx., un canal)": IS_OFF_MAX * R_TOMA10 / 1e-4}

if __name__ == "__main__":
    print("DCV 1 año:", ", ".join(f"{k} {a}+{b} %" for k, (a, b) in DCV_1A.items()))
    print("fuerza:", {k: round(v, 3) for k, v in V_FUERZA.items()}, "V;",
          ", ".join(f"{n} {i*1e6:.3g} µA" for n, i in I_OHM.items()))
    print(f"deriva de 100 ppm en la referencia → lectura de ohmios {lectura_ohm(100e-6)*1e6:+.3f} ppm")
    print(f"P42: {N_MMBTA92} × MMBTA92 para {V_RED_PICO:.0f} Vpk; ≈ {COSTE_P42:.3f} USD")
    print(f"C306: {C_PASO*1e15:.1f} fF por paso; plano con C_fb {C_FB_PLANO*1e12:.1f} pF → P ≈ {P_PLANO:.0f}")
    for m, e in ERR_AC.items():
        print(f"desajuste {m*100:.0f} %: " + ", ".join(f"{f/1e3:g} kHz {x*100:+.2f} %" for f, x in zip(FRECS, e)))
    for k, v in RECH.items():
        print(f"rechazo {k}: {v:.0f} dB")
    for n, a in ASIENTO.items():
        print(f"{n}: C_toma {a['c_tap']*1e12:.0f} pF; salto {a['salto']*100:.1f} %; τ {a['tau']*1e6:.0f} µs; a 1 cuenta en {a['t']*1e3:.2f} ms")
    for k, v in FUGA_CUENTAS.items():
        print(f"fuga en la toma ÷10: {k} → {v:.2g} cuentas")
