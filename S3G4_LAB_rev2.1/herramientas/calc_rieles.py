# -*- coding: utf-8 -*-
"""Presupuesto de energia de la rev 2.1 (seccion G), con la arquitectura decidida el 23 sep:
bateria 1S 5000 mAh; boost 5.3 V (BUS5) -> LM27762 +-5.0 V (AFE y DMM) y LDO 3.3 V (G473);
buck 3.3 V (ESP32-S3); convertidor aparte +-6.5 V para el AWG; reles monoestables con economizador.
Revisado el 6 oct con los amplificadores reales del AFE (AD8039 en los tres canales) y el rele TQ2SA.
Corrientes en mA. Cada supuesto lleva su fuente en la tabla LOADS."""

V_BAT, USABLE = 3.7, 0.90          # celda Li-ion nominal; energia util (apagado al 5 %, margen)
CAP_MAH = 5000                     # decidido el 23 sep
V_BUS, V_ANA, V_DIG, V_AWG = 5.3, 5.0, 3.3, 6.5
ETA_BOOST, ETA_BUCK, ETA_AWG = 0.90, 0.90, 0.80
K_NEG = 1.3                        # LM27762: entrada/salida del lado negativo (estimacion rev 2.0; verificar)
R_NEG = 2.5                        # ohm, hoja LM27762, salida de la bomba (CPOUT)
# AFE por canal (6 oct: CH1 cerrado en S3-S7b y AD8039 elegido para CH2/CH3, DECISIONS 6 oct).
# Corrientes de reposo segun las hojas, no los macromodelos (el OPA810 del modelo da 1.9 mA).
I_OPA810 = 3.7                     # mA por riel, hoja OPA810
I_AD8039 = 1.0                     # mA por amplificador y riel; U103 y U105 son dobles -> 4 por canal
N_AD8039 = 4
I_RAIL_CH = I_OPA810 + N_AD8039 * I_AD8039   # 7.7 mA por riel y canal
I_OPA836 = 1.0                     # mA, etapa final a 3.3 V (P8), hoja OPA836
I_VMID_DAC = 0.2                   # mA por canal: VMID desde VREF (0.16) + DAC (0.05), simulado en S9-A
# Rele TQ2SA-5V-Z con economizador de dos tensiones (DECISIONS 4 oct): mantenimiento ~2.88 V,
# ~46 mW en la bobina -> ~16 mA desde el 3.3 V. Ese 3.3 V es el LDO del G473 (VDDM, desde BUS5).
I_REL_HOLD = 16.0

def loads(ch=3, dmm=True, awg=True, awg_load=True, n_x1=3, display=True, mhz=170):
    L = [("ESP32-S3 con WiFi (media)", "3V3D", 120, "rev 2.0 §12; hoja: RX 88–91 mA, TX 283–340 mA de pico")]
    if display:
        L += [("Lógica de la pantalla", "3V3D", 10, "estimación"),
              ("Retroiluminación, 6 LED", "VSYS", 120, "hoja ER-TFT035IPS-6: 120 mA a 3.2 V")]
    L += [("Varios: cargador, LED, zumbador", "VSYS", 5, "estimación"),
          ("STM32G473 a %d MHz" % mhz, "VDDM", {170: 45, 104: 32}[mhz], "DS T.21 + bloques analógicos + periféricos")]
    if ch:
        src = "%d × (OPA810 %.1f + %d × AD8039 %.1f) mA, hojas" % (ch, I_OPA810, N_AD8039, I_AD8039)
        L += [("AFE: %d canales, OPA810 + 2 AD8039 dobles, a ±4.9 V" % ch, "+5", ch * I_RAIL_CH, src),
              ("AFE: %d canales, OPA810 + 2 AD8039 dobles, a ±4.9 V" % ch, "-5", ch * I_RAIL_CH, "idem"),
              ("AFE: %d etapas finales OPA836 a 3.3 V (P8), VMID y DAC" % ch, "VDDM", ch * (I_OPA836 + I_VMID_DAC),
               "%d × (%.1f + %.1f) mA; hoja OPA836 y S9-A" % (ch, I_OPA836, I_VMID_DAC))]
        if n_x1:
            L += [("Relés TQ2SA en ×1 (%d), mantenimiento desde 3.3 V" % n_x1, "VDDM", n_x1 * I_REL_HOLD,
                   "%d × %.0f mA a ≈ 2.9 V; DECISIONS 4 oct" % (n_x1, I_REL_HOLD))]
    if dmm:
        L += [("DMM: referencia, amplificadores, fuente de corriente", "+5", 3, "rev 2.0 §12")]
    if awg:
        L += [("AWG: reposo de las 2 salidas", "AWG+", 10, "rev 2.0 §06.5"), ("AWG: reposo de las 2 salidas", "AWG-", 10, "idem")]
        if awg_load:
            L += [("AWG: 2 canales, seno a fondo sobre 50 Ω", "AWG+", 32, "rev 2.0: 32 mA típicos por riel"),
                  ("AWG: 2 canales, seno a fondo sobre 50 Ω", "AWG-", 32, "idem")]
    return L

def p_bat(rail, ma):
    i = ma / 1000
    return {"VSYS": V_BAT * i, "3V3D": V_DIG * i / ETA_BUCK, "BUS5": V_BUS * i / ETA_BOOST,
            "+5": V_BUS * i / ETA_BOOST, "-5": V_BUS * K_NEG * i / ETA_BOOST,
            "VDDM": V_BUS * i / ETA_BOOST, "AWG+": V_AWG * i / ETA_AWG, "AWG-": V_AWG * i / ETA_AWG}[rail]

def total(L): return sum(p_bat(r, m) for _, r, m, _ in L)
def hours(p, mah=CAP_MAH): return mah / 1000 * V_BAT * USABLE / p

MODES = [
 ("M1", "Peor caso de RF-17: todo activo, WiFi, pantalla, AWG sobre 50 Ω, 3 relés en ×1", loads()),
 ("M2", "Uso típico: todo activo, AWG sobre alta impedancia, 1 relé en ×1", loads(awg_load=False, n_x1=1)),
 ("M3", "Osciloscopio + WiFi + pantalla", loads(dmm=False, awg=False, n_x1=1)),
 ("M4", "Sólo DMM + WiFi + pantalla (AFE y AWG apagados)", loads(ch=0, awg=False)),
 ("M5", "Como M1 sin pantalla (sólo cliente web)", loads(display=False)),
 ("M6", "Como M1 con la CPU a 104 MHz (P13)", loads(mhz=104)),
]

def rail_sum(L, rail): return sum(m for _, r, m, _ in L if r == rail)
M1 = MODES[0][2]
PLUS5, MINUS5 = rail_sum(M1, "+5"), rail_sum(M1, "-5")
CPOUT = -(V_BUS - MINUS5 / 1000 * R_NEG)          # sin el AWG en la bomba
AWG_PEAK = 2 * 50                                 # mA por riel: 2 canales a 50 mA de pico
BUS5_IN = (rail_sum(M1, "+5") + K_NEG * rail_sum(M1, "-5") + rail_sum(M1, "VDDM") + rail_sum(M1, "BUS5"))  # mA en BUS5
BOOST_IN = V_BUS * BUS5_IN / 1000 / ETA_BOOST / 3.0   # A de bateria al boost con la celda a 3.0 V

if __name__ == "__main__":
    for k, d, L in MODES:
        p = total(L); print(f"{k} {d}: {p:.2f} W -> {hours(p):.1f} h")
    print(f"M1: +5 = {PLUS5:.0f} mA, -5 = {MINUS5:.0f} mA de 250; CPOUT = {CPOUT:.2f} V; BUS5 = {BUS5_IN:.0f} mA; boost a 3.0 V = {BOOST_IN:.2f} A")
    for n, r, m, s in M1: print(f"   {n:52s} {r:5s} {m:6.1f} mA  {p_bat(r, m):.3f} W")
