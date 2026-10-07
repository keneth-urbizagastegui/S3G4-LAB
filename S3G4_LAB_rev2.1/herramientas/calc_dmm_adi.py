# -*- coding: utf-8 -*-
"""R5: metodo de presupuesto de errores de Analog Devices («How to Achieve 7.5-Digit Accuracy in Instrumentation
Applications», partes 1 y 2, D. Guo y O. Liu, 2024; research_and_tests/Analog_/) y su aplicacion a la seccion H.
Datos del G473: datasheet/stm32g473.pdf (DS12712 Rev 5), tablas 63-68 (exactitud del ADC).
REF3325 y OPA2188: paginas de producto de ti.com (7 oct 2026).  Ejecutar: python calc_dmm_adi.py"""
import math

def rss(*v): return math.sqrt(sum(x * x for x in v))

# ---------- 1) Comprobacion de las cuentas de ADI (parte 1) ----------
OFF_TC = rss(0.002, 0.005, 0.2, 0.007)             # ppm/°C, tabla 7 (buffer, atenuador, LT5400, cero del AD4630)
INL_AD4630 = 0.9                                    # ppm, se cuenta como offset
OFF_24H = rss(OFF_TC * 1, INL_AD4630)               # ±1 °C
GAIN_TC = rss(0.5, 0.2, 0.07)                       # ppm/°C, tabla 8 (LT5400, ADR1001, AD4630)
GAIN_24H = rss(GAIN_TC * 1, 0.1, 0.1)               # + CMRR del buffer y del atenuador
OFF_1A_T, GAIN_1A_T = rss(OFF_TC * 5, INL_AD4630), rss(GAIN_TC * 5, 0.1, 0.1)   # ±5 °C
EA, KB = 0.68, 8.62e-5
def arrhenius(t_uso, t_ensayo):
    """Cuantas horas de uso equivalen a una hora de ensayo (>1 si el uso es mas frio). La ecuacion (1) del articulo
    esta impresa con el signo cambiado; su resultado (1.81) es el de esta formula."""
    return math.exp(EA / KB * (1 / t_uso - 1 / t_ensayo))
ARRH = arrhenius(301, 308)                           # 28 °C de uso frente a 35 °C de ensayo del LT5400
ARRH_SIGNO_IMPRESO = math.exp(-EA / KB * (1 / 301 - 1 / 308))
LT5400_1A = 2 * math.sqrt(8760 / (2000 * ARRH))     # ppm, deriva del LT5400 en un año
ADR1001_1A = 4 * math.sqrt(8760 * arrhenius(298, 301) / 1000)   # 4 ppm/1000 h a 25 °C, usado a 28 °C

# ---------- 2) El ADC5 del G473 en diferencial ----------
VREF = 2.5                                          # REF3325
LSB_DIFF = 2 * VREF / 4096                          # el diferencial va de −VREF+ a +VREF+
CUENTA = 2.0 / 19999                                # seccion H: ±19 999 cuentas = ±2 V en el ADC
INL = {"típica (25 °C)": 2.1, "máx. (25 °C, VDDA = VREF+ = 3 V)": 3.2, "máx. (otras condiciones)": 4.1}   # LSB, T.63-65
INL_CUENTAS = {k: v * LSB_DIFF / CUENTA for k, v in INL.items()}
DNL_MAX = 1.6                                       # LSB, diferencial
SINAD_DIFF = 67.5                                   # dB, tipico (T.63)
RUIDO_MUESTRA = (VREF / math.sqrt(2)) / 10 ** (SINAD_DIFF / 20)   # V rms por muestra
RUIDO_1024 = RUIDO_MUESTRA / math.sqrt(1024)
H_INL_DICHO = 0.0006                                # §8 de H: «≈ 0.06 % del fondo», sobre el recorrido de 12 bits
H_INL_DICHO_V = H_INL_DICHO * 2 * VREF              # en voltios

# ---------- 3) Presupuesto de la seccion H con el metodo de ADI ----------
DT = 5                                              # 23 ± 5 °C, como la especificacion de 1 año
REF_TC = 30                                         # ppm/°C max (REF33)
R_TC = 25                                           # ppm/°C de cada resistencia del 0.1 %
RATIO_TC = 2 * R_TC                                 # peor caso de la relacion de dos resistencias
PATRON = 500                                        # ppm: incertidumbre del multimetro con el que se calibra (supuesto)
GANANCIA = {  # rango: lista de (fuente, ppm de lectura)
    "200 mV": [("REF3325 · 30 ppm/°C × 5 °C", REF_TC * DT), ("×10 de A · relación 50 ppm/°C × 5 °C", RATIO_TC * DT),
               ("Driver · relación 50 ppm/°C × 5 °C", RATIO_TC * DT), ("Patrón de calibración (supuesto)", PATRON)],
    "2 V":    [("REF3325 · 30 ppm/°C × 5 °C", REF_TC * DT), ("Driver · relación 50 ppm/°C × 5 °C", RATIO_TC * DT),
               ("Patrón de calibración (supuesto)", PATRON)],
    "20 V":   [("REF3325 · 30 ppm/°C × 5 °C", REF_TC * DT), ("Divisor ÷10 · relación 50 ppm/°C × 5 °C", RATIO_TC * DT),
               ("Driver · relación 50 ppm/°C × 5 °C", RATIO_TC * DT), ("Patrón de calibración (supuesto)", PATRON)],
}
GAN_RSS = {r: rss(*(v for _, v in l)) for r, l in GANANCIA.items()}
MARGEN_LTD = {r: math.sqrt(max(0, 1000 ** 2 - g ** 2)) for r, g in GAN_RSS.items()}   # lo que queda para deriva a 1 año

IB_MAX = 850e-12                                    # OPA2188, 25 °C
RS = {"200 mV": 99e3, "2 V": 99e3, "20 V": 1 / (1 / (9e6 + 99e3) + 1 / 1e6)}   # impedancia vista por el amplificador
CUENTA_ENTRADA = {"200 mV": CUENTA / 10, "2 V": CUENTA, "20 V": CUENTA}         # referida al nodo que lee A
FUGA_4051 = 1e-9                                    # supuesto de la seccion H («unos nA»)
OFFSET = {}
for r in RS:
    ib = IB_MAX * RS[r] / CUENTA_ENTRADA[r]
    fuga = FUGA_4051 * RS[r] / CUENTA_ENTRADA[r] if r == "20 V" else 0.0
    ruido = RUIDO_1024 / CUENTA
    OFFSET[r] = dict(ib=ib, fuga=fuga, ruido=ruido,
                     tip=rss(INL_CUENTAS["típica (25 °C)"], ib, fuga, ruido),
                     max=rss(INL_CUENTAS["máx. (25 °C, VDDA = VREF+ = 3 V)"], ib, fuga, ruido))

if __name__ == "__main__":
    print(f"ADI: offset TC {OFF_TC:.3f} ppm/°C → 24 h {OFF_24H:.2f} ppm; ganancia TC {GAIN_TC:.2f} ppm/°C → 24 h {GAIN_24H:.2f} ppm")
    print(f"ADI ±5 °C: offset {OFF_1A_T:.2f} ppm, ganancia {GAIN_1A_T:.2f} ppm; Arrhenius {ARRH:.2f} (impreso: {ARRH_SIGNO_IMPRESO:.2f}); LT5400 1 año {LT5400_1A:.1f} ppm; ADR1001 {ADR1001_1A:.1f} ppm")
    print(f"ADC5: LSB diferencial {LSB_DIFF*1e3:.3f} mV; una cuenta del DMM {CUENTA*1e6:.0f} µV")
    for k, v in INL_CUENTAS.items():
        print(f"  INL {k}: {INL[k]} LSB = {v:.0f} cuentas ({INL[k]*LSB_DIFF/2*100:.2f} % de 2 V)")
    print(f"  lo dicho en H §8: {H_INL_DICHO_V*1e3:.1f} mV = {H_INL_DICHO_V/CUENTA:.0f} cuentas")
    print(f"  ruido por muestra {RUIDO_MUESTRA*1e3:.2f} mV rms = {RUIDO_MUESTRA/CUENTA:.1f} cuentas; ×1024: {RUIDO_1024/CUENTA:.2f} cuentas")
    for r in GANANCIA:
        print(f"ganancia {r}: RSS {GAN_RSS[r]:.0f} ppm; margen para deriva anual {MARGEN_LTD[r]:.0f} ppm")
        o = OFFSET[r]
        print(f"  offset {r}: Ib {o['ib']:.1f}, fuga {o['fuga']:.1f}, ruido {o['ruido']:.2f} → {o['tip']:.0f} (típ.) / {o['max']:.0f} (máx.) cuentas")
