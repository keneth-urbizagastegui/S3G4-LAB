# -*- coding: utf-8 -*-
"""Cifras de la seccion H revisada tras la sintesis (7 oct 2026): fuente de corriente de ohmios (P43, propuesta),
proteccion P42 y presupuesto con el metodo de ADI. Reutiliza calc_dmm_adi y calc_dmm_sintesis.
Ejecutar: python calc_dmm_h.py"""
import math
import calc_dmm_adi as ADI, calc_dmm_sintesis as SIN

def par(*r): return 1 / sum(1 / x for x in r)

# --- Fuente de corriente ratiometrica (P43), como el 34401A ---
RIEL, VREF = 4.9, 2.5
R1, R2 = 24.9e3, 4.99e3                 # IREF = VREF/R1 baja por R2 desde el riel: V_set = VREF·R2/R1
IREF = VREF / R1
V_SET = IREF * R2
RON_4051, VCE_SAT, CAIDA_P42 = 100.0, 0.2, 0.8    # 74HC4051 a ±4.9 V; PNP de paso; 1N4007W + 2 × MMBTA92 en conduccion
R_DIV = 10e6 + 99e3                     # divisor de 10 MΩ + R_PROT, en paralelo con Rx
RANGOS = [("200 Ω", 200.0, 50.0), ("2 kΩ", 2e3, 500.0), ("20 kΩ", 20e3, 5e3),
          ("200 kΩ", 200e3, 50e3), ("2 MΩ", 2e6, 500e3), ("20 MΩ", 20e6, 2.49e6)]   # 20 MΩ a 0.2 µA: ver COMPROBACION
OHM = []
for n, fs, rr in RANGOS:
    i = V_SET / rr
    vx = i * par(fs, R_DIV)
    disp = RIEL - V_SET - i * RON_4051 - VCE_SAT - CAIDA_P42      # tension disponible en el borne
    vacio = min(disp, i * R_DIV)
    OHM.append(dict(rango=n, fs=fs, rr=rr, i=i, vx=vx, disp=disp, margen=disp - vx, vacio=vacio))
I_DIODO = V_SET / 500.0                  # el rango de 2 kΩ: 1 mA
DISP_DIODO = RIEL - V_SET - I_DIODO * RON_4051 - VCE_SAT - CAIDA_P42
V_CONT = 50.0 * OHM[0]["i"]              # 50 Ω en el rango de 200 Ω
V_PB14 = V_CONT / 2

# Deriva de la corriente tras calibrar (23 ± 5 °C)
DT = 5
DERIVA_I = math.sqrt((25 * DT) ** 2 + (50 * DT) ** 2 + (2e-6 * DT / V_SET * 1e6) ** 2)   # R_rango, R1/R2, TLV2372 (2 µV/°C)

# --- Comparacion: corriente medida por razon (H original) frente a fuente calibrada ---
DV_FS = 1.5 / 2.5 * (RIEL - 1.0)         # caida en R_ref a fondo, con ≈ 1 V de proteccion en serie
def err_razon(cuentas, div=4):
    return math.sqrt(2) * cuentas * div * ADI.CUENTA / DV_FS
ERR_RAZON = {"típica": err_razon(ADI.INL_CUENTAS["típica (25 °C)"]),
             "máxima": err_razon(ADI.INL_CUENTAS["máx. (25 °C, VDDA = VREF+ = 3 V)"]),
             "linealizada (10 cuentas)": err_razon(10)}

# --- Ganancia de ohmios (ppm de lectura) con la fuente de corriente ---
GAN_OHM = math.sqrt(DERIVA_I ** 2 + (50 * DT) ** 2 + ADI.PATRON ** 2)    # + relacion del driver y patron

# --- Comprobacion de la especificacion D5 en ohmios: cuentas del ADC (INL) pasadas a Ω ---
# El divisor de 10 MΩ en paralelo aplana V_x(Rx): dV/dRx = I·(R_DIV/(Rx+R_DIV))². Se recorre 10…100 % del rango
# y se compara, en suma lineal, con lo que deja la especificacion tras la ganancia de ohmios.
LSB_DMM = 100e-6
ESPEC_OHM = {"200 Ω": 0.002, "2 kΩ": 0.002, "20 kΩ": 0.002, "200 kΩ": 0.002, "2 MΩ": 0.002, "20 MΩ": 0.01}
NIVELES = {"garantizada": (39, 40), "calibrada": (10, 10)}      # (cuentas de INL del ADC, cuentas de la especificacion)
def comprobar(i, fs, pct, n_adc, n_esp):
    peor = None
    for k in range(1, 11):
        r = fs * k / 10
        error = n_adc * LSB_DMM / (i * (R_DIV / (r + R_DIV)) ** 2)
        tolerancia = (pct - GAN_OHM * 1e-6) * r + n_esp * fs / 20000
        if peor is None or error / tolerancia > peor[0]:
            peor = (error / tolerancia, k * 10)
    return peor
COMPROBACION = {(o["rango"], niv): comprobar(o["i"], o["fs"], ESPEC_OHM[o["rango"]], *NIVELES[niv])
                for o in OHM for niv in NIVELES}
# Lo mismo con la corriente de 0.1 µA de la primera version de P43 en 20 MΩ
I_20M_ANTES = V_SET / 5e6
COMP_20M_ANTES = comprobar(I_20M_ANTES, 20e6, 0.01, *NIVELES["garantizada"])
# Fuga del 4051 e Ib del OPA2188 frente a la corriente de 20 MΩ (se calibran; queda su deriva)
I_20M = OHM[-1]["i"]
FUGA_20M = 1e-9 / I_20M                  # por nA de fuga
IB_20M = 0.85e-9 / I_20M                 # Ib maxima del OPA2188
KOHM_POR_CUENTA_20M = LSB_DMM / (I_20M * (R_DIV / (20e6 + R_DIV)) ** 2)

if __name__ == "__main__":
    print(f"V_set = {V_SET*1e3:.1f} mV (IREF {IREF*1e6:.1f} µA)")
    for o in OHM:
        print(f"{o['rango']}: R {o['rr']:g} Ω, I {o['i']*1e6:.4g} µA, V_x a fondo {o['vx']:.3f} V, "
              f"disponible {o['disp']:.2f} V (margen {o['margen']:.2f} V), en vacío {o['vacio']:.2f} V")
    print(f"diodo: {I_DIODO*1e3:.2f} mA, hasta {DISP_DIODO:.2f} V; continuidad 50 Ω → {V_CONT:.3f} V ({V_PB14:.3f} V en PB14)")
    print(f"deriva de la corriente ±5 °C: {DERIVA_I:.0f} ppm; ganancia de ohmios {GAN_OHM:.0f} ppm")
    for k, v in ERR_RAZON.items():
        print(f"razón, INL {k}: {v*100:.2f} % de lectura")
    for (rango, niv), (q, pc) in COMPROBACION.items():
        print(f"especificación {rango} {niv}: error / tolerancia = {q:.2f} (peor en {pc} % del rango)")
    print(f"20 MΩ con 0.1 µA (antes), garantizada: {COMP_20M_ANTES[0]:.2f} (peor en {COMP_20M_ANTES[1]} %)")
    print(f"20 MΩ: una cuenta del ADC = {KOHM_POR_CUENTA_20M/1e3:.1f} kΩ cerca del fondo; 1 nA de fuga = "
          f"{FUGA_20M*100:.2f} % de la corriente; Ib máx. = {IB_20M*100:.2f} %")
