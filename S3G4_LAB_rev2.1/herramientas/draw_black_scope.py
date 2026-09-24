# -*- coding: utf-8 -*-
"""Redibujo propio (simplificado) del canal 1 de black_scope: divisor + LMV324 + OPAMP1 en PGA + ADC1,
con la polarizacion comun desde DAC2 (hardware/black_scope/outputs/pdf/black_scope.pdf y netlist .xml)."""
from sch import Sch
import calc_black_scope as K

def afe():
    s = Sch(1300, 730, "black_scope - canal 1 completo")
    y = 260
    s.port(20, y, "CH1 · J4-1", "r"); s.wire((103, y), (130, y))
    s.R((130, y), (250, y), "R5", "8k2 ±0.5 %")
    s.wire((250, y), (430, y)); s.dot(300, y); s.dot(370, y)
    s.net(376, y, "Vn", dy=-6)
    s.R((300, y), (300, 150), "R11", "2k7", side="l"); s.rail(300, 150, "+3.3VA")
    s.R((300, y), (300, 380), "R12", "4k3", side="l"); s.gnd(300, 380)
    s.C((370, y), (370, 380), "C23", "100 pF", side="r"); s.gnd(370, 380)
    A = s.opamp(440, 244, "U8A", "LMV324 · seguidor", inp_top=False)
    s.wire(A["inm"], (420, 228), (420, 186), (530, 186), (530, 244)); s.dot(530, 244)
    s.wire(A["out"], (728, 244)); s.dot(580, 244)
    s.net(646, 244, "PA7", dy=-6)
    # ruta directa al ADC (sin usar por el firmware)
    s.wire((580, 244), (580, 510), (652, 510))
    s.port(652, 510, "PB12 → ADC1_IN11", "r")
    s.note(652, 534, "(lento, sin usar)")
    # MCU
    s.frame(640, 70, 640, 490, "STM32G473VET6")
    P = s.box(740, 190, 190, 110, "OPAMP1 · PGA interno", "",
              pins=(("l", 54, "VINP", "inp"), ("r", 38, "OUT", "out"), ("b", 75, "VINM0", "vb")))
    s.text(835, 212, f"G = 2 … 64 · R1 = {K.R1_PGA/1e3:.0f} kΩ", "pin", "middle")
    s.text(835, 262, "Vout = G·(VINP − VB) + VB", "pin", "middle")
    s.text(835, 278, f"BW = GBW/G: {K.bw_pga[64][1]/1e3:.0f} kHz a ×64", "pin", "middle")
    s.wire(P["out"], (988, 228))
    D = s.box(1000, 170, 170, 120, "ADC1 · 12 bits", "", pins=(("l", 58, "VOPAMP1", "in"),))
    s.text(1085, 196, f"{K.FADC/1e6:.1f} MHz (PCLK/4)", "pin", "middle")
    s.text(1085, 262, f"muestreo 2.5 ciclos = {K.TS_CFG*1e9:.1f} ns", "pin", "middle")
    s.text(1085, 278, f"(mínimo {K.TS_OPAMP_MIN*1e9:.0f} ns)", "pin", "middle")
    s.note(1270, 330, "TIM2 marca cada muestra; DMA circular de 512 muestras.", "end")
    s.note(1270, 348, "AWD1 arma y AWD2 dispara (8 bits); la ISR arranca TIM3.", "end")
    s.note(1270, 366, "TIM3 cuenta las muestras restantes y para los 4 DMA.", "end")
    s.note(1270, 384, "Sólo CH1 puede disparar.", "end")
    # polarizacion comun
    B = s.box(900, 440, 110, 44, "DAC2", "", pins=(("b", 55, "", "o"),))
    s.text(955, 466, "buffer ON", "pin", "middle")
    s.wire(B["o"], (955, 600)); s.dot(955, 600)
    s.net(960, 576, "PA6")
    s.wire(P["vb"], (815, 600), (955, 600))
    s.net(820, 576, "PA3")
    s.wire((955, 600), (1080, 600)); s.dot(1010, 600)
    s.R((1010, 600), (1010, 680), "R25", "10 kΩ", side="l"); s.gnd(1010, 680)
    s.C((1080, 600), (1080, 680), "C22", "100 nF", side="r"); s.gnd(1080, 680)
    s.net(1100, 604, "VB · también PA1, PB2, PB15")
    s.note(700, 712, f"C22 es {K.CL_FACTOR:.0f} veces la carga máxima del DAC con buffer (50 pF).")
    # notas del divisor
    s.note(20, 440, f"Vn = {K.G_IN:.3f}·Vin + {K.V0:.3f} V · Zin = {K.ZIN/1e3:.2f} kΩ")
    s.note(20, 458, f"Rango {f"{K.VIN_MIN:.1f}".replace(chr(45), chr(8722))} V … +{K.VIN_MAX_RAIL:.1f} V; +{K.VIN_MAX_CM:.1f} V si el LMV324 es el de TI")
    s.note(20, 476, f"Polo de entrada {K.FC/1e6:.2f} MHz · al aire lee +{K.VIN_OPEN:.2f} V")
    s.note(20, 512, "CH2–CH4 iguales: U8C/U8D/U8B → OPAMP3/5/6 → ADC3/5/4.")
    s.note(20, 530, "Rutas directas a PB1, PD11 y PD12, también sin usar.")
    return s.svg()
