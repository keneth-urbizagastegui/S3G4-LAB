# -*- coding: utf-8 -*-
"""Cifras de la pagina sobre las partes analogicas del STM32G473. Fuentes: DS12712 Rev 5
(datasheet/stm32g473.pdf) y RM0440 Rev 9 (datasheet/rm0440-...pdf). Las cifras de las tablas del
fabricante se copian tal cual; lo que se deriva se calcula aqui."""
import math

SMP = [2.5, 6.5, 12.5, 24.5, 47.5, 92.5, 247.5, 640.5]
CONV = 12.5                                   # ciclos de conversion a 12 bits
F_ONE, F_MULTI_27, F_MULTI_162 = 60e6, 52e6, 42e6   # DS T.61: fADC maximo
TS_OPAMP = 200e-9                             # DS T.75: TS_OPAMP_VOUT, VDDA >= 2 V
SLOW_MIN_SMP = 6.5                            # DS T.62: 2.5 ciclos "N/A" en canales lentos

def fs(fadc, smp): return fadc / (smp + CONV)
def smp_min_time(fadc, t): return next(s for s in SMP if s / fadc >= t)

# Casos de muestreo (MSa/s por ADC o combinados)
def interleave_fast(fadc):  # SMPPLUS: 3.5 + 12.5 = 16 ciclos, un ADC cada 8
    return fadc / 8
def interleave_slow(fadc, smp=6.5):
    # disparo externo: el esclavo empieza ts + 0.5 + DELAY despues; cada ADC necesita smp+12.5 ciclos
    for delay in range(1, 13):
        sp = smp + 0.5 + delay
        if 2 * sp >= smp + CONV: return fadc / sp, delay, sp
CLOCKS = [("60 MHz · un solo ADC activo", F_ONE), ("52 MHz · varios ADC, VDDA ≥ 2.7 V", F_MULTI_27),
          ("42.5 MHz · HCLK 170 MHz / 4, síncrono", 170e6 / 4)]
rates = []
for name, f in CLOCKS:
    smp_op = smp_min_time(f, TS_OPAMP)
    isl = interleave_slow(f)
    rates.append(dict(clk=name, f=f, fast=fs(f, 2.5), slow=fs(f, SLOW_MIN_SMP), opamp=fs(f, smp_op), smp_op=smp_op,
                      il_fast=interleave_fast(f), il_slow=isl[0], il_delay=isl[1]))

# Incertidumbre de disparo con reloj asincrono (DS T.61: tLATR 1.5-2.5 ciclos con CKMODE=00)
def snr_jitter(f_sig, fadc):
    sigma = (1 / fadc) / math.sqrt(12)       # peor caso: fase uniforme en un ciclo
    return -20 * math.log10(2 * math.pi * f_sig * sigma), sigma
jit = {f: snr_jitter(f, 52e6)[0] for f in (10e3, 100e3, 500e3, 1e6)}
JIT_SIGMA = snr_jitter(1e6, 52e6)[1]
def enob(snr): return (snr - 1.76) / 6.02

# Corriente de la CPU (DS T.21, tipico 25 C, desde flash): interpolacion lineal a 104 MHz
IDD = {170: 29.5, 150: 24.5, 120: 19.5, 80: 13.0}
IDD_104 = IDD[80] + (IDD[120] - IDD[80]) * (104 - 80) / (120 - 80)
SAVE_104 = IDD[170] - IDD_104

# Presupuesto analogico orientativo (tipicos DS; configuracion supuesta, no decidida)
BUDGET = [
    ("3 ADC a ~3.5 MSa/s (fila de 4 Msps: 590 µA VDDA + 110 µA VREF+)", 3 * (590 + 110)),
    ("ADC5 lento para DMM y realimentación (10 ksps: 16 + 0.6 µA)", 16 + 0.6),
    ("DAC3, dos canales internos de 15 MSa/s (720 µA de VREF+ cada uno, código medio)", 2 * 720),
    ("2 OPAMP seguidores del generador, modo normal (1.3 mA cada uno)", 2 * 1300),
    ("1 COMP de disparo activo (450 µA)", 450),
    ("DAC1 interno sin buffer para el umbral (155 µA de VREF+)", 155),
    ("VREFBUF encendido (16 µA)", 16),
]
BUDGET_TOTAL = sum(v for _, v in BUDGET)

# OPAMP interno
GBW = (7e6, 13e6); SR_N = (2.5e6, 6.5e6); SR_HS = (18e6, 45e6)
def fpbw(sr, vpp): return sr / (math.pi * vpp)
FPBW = {m: (fpbw(s[0], 3.0), fpbw(s[1], 3.0)) for m, s in (("normal", SR_N), ("alta velocidad", SR_HS))}
PGA = [(g, 10 * (g - 1), GBW[0] / g, GBW[1] / g) for g in (2, 4, 8, 16, 32, 64)]
# Ruido 1/f del OPAMP extrapolado desde 250 nV/rtHz a 1 kHz (supuesto: pendiente 1/f pura)
EN_1HZ = 250e-9 * math.sqrt(1000)
VN_01_10 = EN_1HZ * math.sqrt(math.log(10 / 0.1))

# Ventaja de BULB a 1 MSa/s con 52 MHz: ciclos de muestreo disponibles
BULB_1M = 52e6 / 1e6 - CONV

if __name__ == "__main__":
    for r in rates:
        print(f"{r['clk']}: rapido {r['fast']/1e6:.2f}, lento {r['slow']/1e6:.2f}, OPAMP interno {r['opamp']/1e6:.2f} (SMP {r['smp_op']}), "
              f"entrelazado rapido {r['il_fast']/1e6:.2f}, entrelazado lento {r['il_slow']/1e6:.2f} (DELAY {r['il_delay']})")
    print("sigma", JIT_SIGMA * 1e9, "ns;", {f: (round(s, 1), round(enob(s), 1)) for f, s in jit.items()})
    print(f"IDD 104 MHz ~{IDD_104:.1f} mA, ahorro {SAVE_104:.1f} mA")
    print(f"presupuesto {BUDGET_TOTAL/1000:.2f} mA")
    print("FPBW 3 Vpp", {m: (round(a/1e3), round(b/1e3)) for m, (a, b) in FPBW.items()})
    print(f"1/f: {EN_1HZ*1e6:.1f} uV/rtHz a 1 Hz, {VN_01_10*1e6:.0f} uV rms 0.1-10 Hz; BULB {BULB_1M:.1f} ciclos")

# Ruido propio del ADC expresado en divisiones (seccion C: 8 div = 2.0 V en el ADC, 0.25 V/div)
VDIV_ADC = 0.25
def adc_noise(vref, snr_db): return (vref / 2 / math.sqrt(2)) / 10 ** (snr_db / 20)
ADC_NOISE = {(vref, snr): adc_noise(vref, snr) for vref in (2.5, 3.3) for snr in (66.9, 63.2)}

# DS12712 tabla 62, 12 bits, fADC = 60 MHz: (ciclos, ns, RAIN rapido, RAIN lento)
RAIN12 = [(2.5, 41.67, 100, None), (6.5, 108.33, 330, 100), (12.5, 208.33, 680, 470), (24.5, 408.33, 1500, 1200),
          (47.5, 791.67, 2200, 1800), (92.5, 1541.67, 4700, 3900), (247.5, 4125, 12000, 10000), (640.5, 10675, 39000, 33000)]

if __name__ == "__main__":
    for (vref, snr), v in ADC_NOISE.items():
        print(f"VREF {vref} SNR {snr}: {v*1e3:.2f} mV rms = {v/VDIV_ADC*100:.2f} % div")
