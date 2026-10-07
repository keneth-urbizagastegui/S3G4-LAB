# -*- coding: utf-8 -*-
"""Cifras de la sintesis de las 9 referencias del DMM (7 oct 2026). Reutiliza calc_dmm_adi (INL) y calc_dmm_34401a.
Datos de la seccion H: 01_diseno/dmm_rev21.html (fuente de ohmios de 4.9 V, R_ref de 301 Ω en 200 Ω, tomas del divisor).
Ejecutar: python calc_dmm_sintesis.py"""
import calc_dmm_adi as ADI

V_FUENTE = 4.9
VENTANA = 2.0                                        # ±2 V en el ADC = ±19 999 cuentas

# --- 1) La PTC en serie con R_ref (seccion H §6) frente a la proteccion con semiconductores (P42) ---
R_REF_200, RX_FS = 301.0, 200.0
def ohm_200(r_serie, caida=0.0):
    i = (V_FUENTE - caida) / (R_REF_200 + r_serie + RX_FS)
    vx = i * RX_FS
    return dict(i=i, vx=vx, ventana=vx / VENTANA)
CASOS_200 = {"Sin protección (H §6, nominal)": ohm_200(0),
             "PTC de 2 kΩ en frío (H: «pocos kΩ»)": ohm_200(2000),
             "PTC de 50 Ω (tipo telecomunicaciones)": ohm_200(50),
             "P42: diodo + transistores (≈ 1 V de caída)": ohm_200(0, 1.0)}
def diodo_led(r_ref, r_serie, caida=0.0, vf=3.0):
    return max(0.0, (V_FUENTE - caida - vf) / (r_ref + r_serie))
LED = {"Sin protección": diodo_led(3010, 0), "PTC de 2 kΩ": diodo_led(3010, 2000),
       "P42 (1 V)": diodo_led(3010, 0, 1.0), "P42 con R_ref de 1 kΩ": diodo_led(1000, 0, 1.0)}

# --- 2) Fuga del mux referida a la entrada: ≈ I × (resistencia de arriba) en los rangos divididos ---
R_PROT = 99e3
RANGOS = {  # rango: (Thevenin del nodo que lee el mux, division, cuenta en la entrada)
    "200 mV (X0)": (R_PROT, 1, 10e-6),
    "2 V (X0)": (R_PROT, 1, 100e-6),
    "20 V (X1, ÷10)": (1 / (1 / (9e6 + R_PROT) + 1 / 1e6), 10, 1e-3),
    "50 V (X2, ÷100)": (1 / (1 / (9.9e6 + R_PROT) + 1 / 100e3), 100, 10e-3),
}
FUGA_POR_NA = {r: 1e-9 * rth * div / cuenta for r, (rth, div, cuenta) in RANGOS.items()}   # cuentas por nA
DERIVA_FUGA_5C = 2 ** (5 / 10) - 1                  # la fuga se duplica cada ≈ 10 °C: +41 % con +5 °C

# --- 3) Especificacion propuesta: terminos de cuentas con y sin linealizacion del ADC5 ---
INL_TIP, INL_MAX = ADI.INL_CUENTAS["típica (25 °C)"], ADI.INL_CUENTAS["máx. (25 °C, VDDA = VREF+ = 3 V)"]
INL_PEOR = ADI.INL_CUENTAS["máx. (otras condiciones)"]
GAN_PPM = max(ADI.GAN_RSS.values())

# --- 4) Respaldo opcional (huella sin montar): ADS1115 a ±2.048 V ---
ADS_LSB = 2.048 / 32768
ADS_CUENTAS_LSB = ADS_LSB / ADI.CUENTA

if __name__ == "__main__":
    for n, c in CASOS_200.items():
        print(f"{n}: I {c['i']*1e3:.2f} mA, V_x a 200 Ω {c['vx']:.2f} V ({c['ventana']*100:.0f} % de la ventana)")
    for n, i in LED.items():
        print(f"LED de 3 V, {n}: {i*1e3:.2f} mA")
    for r, k in FUGA_POR_NA.items():
        print(f"fuga 1 nA en {r}: {k:.1f} cuentas")
    print(f"deriva de la fuga con +5 °C: +{DERIVA_FUGA_5C*100:.0f} %")
    print(f"INL: {INL_TIP:.0f} / {INL_MAX:.0f} / {INL_PEOR:.0f} cuentas; ganancia RSS máx {GAN_PPM:.0f} ppm")
    print(f"ADS1115: {ADS_LSB*1e6:.1f} µV/LSB = {ADS_CUENTAS_LSB:.2f} cuentas")
