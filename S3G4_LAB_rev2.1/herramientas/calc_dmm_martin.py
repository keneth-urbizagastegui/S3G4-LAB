# -*- coding: utf-8 -*-
"""Cifras propias del Open Source Multimeter de Martin (embedblog.eu), rev 1.5, a partir de
research_and_tests/Martin_STM32_multimeter/: hardware/v15.sch (EAGLE, leido como XML), v15_BOM.txt,
firmware-multimeter/ (config.h, sdadc.cpp, interrupt.cpp, draw.cpp, ctest.cpp) y firmware-calibration/draw.cpp.
Datos de catalogo: INA199 (ti.com: ganancias 50/100/200, VOS ±150 µV max, error de ganancia ±1.5 % max),
SN74LVC1G3157 (ti.com: Ron tipico 6 Ω).  Ejecutar: python calc_dmm_martin.py"""
import math

# --- Referencia y SDADC (STM32F373) ---
VREF = 1.8                       # MCP1501-18 en VREFSD+ (config.h: VREF 1.8f)
VMID = VREF / 2                  # VREF/2 por R19/R20 1 kΩ / 1 kΩ y buffer IC9A; COM se lleva aqui
FS_DIFF = VREF / 2               # fondo diferencial con ganancia 1: ±VREFSD+/2 (comprobado abajo con la calibracion)
CUENTAS = 32768
LSB_ADC = FS_DIFF / CUENTAS      # V por cuenta a la entrada del SDADC
F_SDADC = 6e6                    # 72 MHz / 12 (RCC_CFGR_SDADCPRE_DIV12)
SPS = 50e3                       # modo rapido continuo, un canal (RM0313); NO VERIFICADO en placa
REFRESCO = 2                     # Hz (SCREEN_UPDATE_RATE)
MUESTRAS = SPS / REFRESCO

# --- Divisor de tension: 1 MΩ arriba y patas de 15 kΩ / 150 kΩ conmutadas a COM ---
R_TOP = 1e6
RANGOS = {  # nombre: (pata o None si es directo, ganancia del SDADC)
    "60 V":   (15e3, 1),
    "6 V":    (150e3, 1),
    "600 mV": (None, 1),
    "60 mV":  (None, 8),
}
DIV = {}
for n, (leg, g) in RANGOS.items():
    k = (R_TOP + leg) / leg if leg else 1.0
    lsb_in = LSB_ADC / g * k
    DIV[n] = dict(k=k, g=g, fondo=FS_DIFF / g * k, lsb=lsb_in, zin=(R_TOP + leg) if leg else math.inf)
V_TOMA_MENOS60 = VMID - 60 / DIV["60 V"]["k"]   # tension de la toma con −60 V (encima de AGND)

# --- Calibracion real de una unidad (firmware-calibration/draw.cpp), frente a lo nominal ---
GAIN_V = [0.00179685383230002, 0.00020376070289328, 0.02661292851990090e-3, 0.00329895192147729e-3]  # V/cuenta
OFFSET_V = [-0.11050651068644900, -0.00463333146790479, 0.15401938337034100e-3, 2.11392447180170000e-3]  # V
GAIN_I = [0.00001887419809107, 0.00000413386486215]      # A/cuenta: [2.5 A, 250 mA]
OFFSET_I = [-0.00301374198091053, -0.00102421359418443]
FONDO_NOM = [60, 6, 0.6, 0.06]
CAL_V = []
for (n, d), gv, ov, fs in zip(DIV.items(), GAIN_V, OFFSET_V, FONDO_NOM):
    CAL_V.append(dict(rango=n, real=gv, nominal=d["lsb"], razon=gv / d["lsb"], offset=ov, offset_fs=ov / fs))

# Error del modo RMS: el firmware hace sqrt(media(cuentas^2)) y luego * ganancia + offset
def rms_mostrado(s_rms, i):
    """Lectura RMS para una senoide de s_rms voltios (sin continua) en el rango i, segun el firmware."""
    o_cuentas = -OFFSET_V[i] / GAIN_V[i]                   # cuentas que da una entrada nula
    s_cuentas = s_rms / GAIN_V[i]
    return math.sqrt(s_cuentas**2 + o_cuentas**2) * GAIN_V[i] + OFFSET_V[i]
RMS_CERO = [rms_mostrado(0.0, i) for i in range(4)]
RMS_10mV = rms_mostrado(10e-3, 3)
RMS_50mV = rms_mostrado(50e-3, 3)

# --- Corriente: derivadores siempre en serie, IC4 elige la toma; INA199 con REF = VREF/2 ---
R9, R10 = 0.005, 0.050
TOMA = {"2.5 A": R9, "250 mA": R9 + R10}
GANANCIAS_INA = [50, 100, 200]
FONDO_I = {g: {n: FS_DIFF / (g * r) for n, r in TOMA.items()} for g in GANANCIAS_INA}
FONDO_I_CAL = [CUENTAS * GAIN_I[0], CUENTAS * GAIN_I[1]]        # lo que dan las constantes del firmware
CAIDA_2A5 = 2.5 * (R9 + R10)                                     # sin contar el fusible
VOS_INA = 150e-6
ERR_VOS = {n: VOS_INA / r for n, r in TOMA.items()}               # en amperios
RON_3157 = 6.0                                                    # tipico (ti.com, a 4.5 V; algo mas a 3 V)
I_DIV_60V = 60 / DIV["60 V"]["zin"]
DV_CRUCE = I_DIV_60V * RON_3157                                   # COM se separa de VREF/2 por IC2
ERR_CRUCE = {n: DV_CRUCE / r for n, r in TOMA.items()}

# --- Continuidad: GPIO a 3 V por 220 Ω (+23 Ω de IO_COMPENSATION), ADC1 de 12 bits con VDDA ---
R_CONT = 220 + 23
def r_cont(code): return R_CONT * code / (4096 - code)            # VSUP se cancela
I_CONT_MAX = 2.99 / R_CONT
CODE_50 = 4096 * 50 / (50 + R_CONT)
OHM_POR_CUENTA_50 = R_CONT * 4096 / (4096 - CODE_50) ** 2

# --- Frecuencia: TIM2 cuenta flancos en PA5 (ETR) durante 1/REFRESCO s ---
RES_FREC = REFRESCO

if __name__ == "__main__":
    print(f"LSB del SDADC {LSB_ADC*1e6:.2f} µV; {MUESTRAS:.0f} muestras por lectura")
    for n, d in DIV.items():
        print(f"{n}: ÷{d['k']:.2f} ×{d['g']}; fondo {d['fondo']:.4g} V; {d['lsb']*1e6:.2f} µV/cuenta; Zin {d['zin']/1e6:.3g} MΩ")
    print(f"toma con −60 V: {V_TOMA_MENOS60*1e3:.1f} mV sobre AGND")
    for c in CAL_V:
        print(f"{c['rango']}: real/nominal {c['razon']:.4f} ({(c['razon']-1)*100:+.1f} %); offset {c['offset']*1e3:+.3f} mV = {c['offset_fs']*100:+.2f} % del fondo")
    print("RMS con entrada nula (mV): " + ", ".join(f"{x*1e3:.2f}" for x in RMS_CERO))
    print(f"60 mV: 10 mV rms → {RMS_10mV*1e3:.2f} mV; 50 mV rms → {RMS_50mV*1e3:.2f} mV")
    for g, d in FONDO_I.items():
        print(f"INA199 ×{g}: " + ", ".join(f"{n} → fondo {v:.3g} A" for n, v in d.items()))
    print(f"constantes de calibración: fondo {FONDO_I_CAL[0]:.3f} A y {FONDO_I_CAL[1]:.3f} A")
    print(f"caída a 2.5 A: {CAIDA_2A5*1e3:.1f} mV + fusible; VOS: " + ", ".join(f"{n} {v*1e3:.1f} mA" for n, v in ERR_VOS.items()))
    print(f"cruce V→I con 60 V: {I_DIV_60V*1e6:.1f} µA × {RON_3157} Ω = {DV_CRUCE*1e3:.3f} mV → "
          + ", ".join(f"{n} {v*1e3:.1f} mA" for n, v in ERR_CRUCE.items()))
    print(f"continuidad: hasta {I_CONT_MAX*1e3:.1f} mA; en 50 Ω, código {CODE_50:.0f} y {OHM_POR_CUENTA_50:.3f} Ω por cuenta")
