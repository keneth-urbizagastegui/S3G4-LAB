# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del EEVblog 121GW, a partir de research_and_tests/EEVblog_121GW/121GW_schematic.pdf.
La conmutacion de funciones del selector rotatorio se omite; el emparejamiento R-C del divisor esta deducido."""
from sch import Sch
import calc_dmm_121gw as K


def entrada():
    s = Sch(1420, 560, "121GW: proteccion del borne V/Ω y divisor alrededor del HY3131")
    p = s.banana(70, 120, "V/Ω", "#b3261e")
    s.wire(p, (110, 120)); s.dot(110, 120)
    s.PTC((110, 120), (210, 120), "PTC3", "1.2 kΩ")
    s.R((210, 120), (300, 120), "R16", "1 kΩ")
    s.wire((300, 120), (420, 120)); s.dot(340, 120); s.net(346, 120, "V1", dy=16)
    # camino R (fuente de diodo/ohmios y LowZ)
    s.wire((110, 120), (110, 300), (140, 300))
    s.PTC((140, 300), (240, 300), "PTC4", "1.2 kΩ", side="b")
    s.R((240, 300), (330, 300), "R17", "1 kΩ", side="b")
    s.wire((330, 300), (380, 300)); s.port(380, 300, "R: diodo, ohmios, LowZ (2.2 kΩ)", "r")
    s.dot(360, 300)
    # MOVs
    s.D((340, 120), (340, 200), "MOV1", "S05K575", side="l", kind="tvs")
    s.dot(340, 200)
    s.D((340, 200), (360, 300), "", "", kind="tvs")
    s.text(372, 262, "MOV2", "ref")
    s.wire((340, 200), (220, 200)); s.D((220, 200), (220, 250), "MOV3", "", side="l", kind="tvs")
    s.gnd(220, 250)
    s.note(20, 380, f"MOV1 + MOV3 a masa: ≈ {K.V_MOV_SERIE:.0f} V de varistor en serie; 600 Vrms ({K.V_CAT:.0f} V de pico) no los hacen conducir.")
    s.note(20, 398, "PTC1 + PTC2 (2 × 1.5 kΩ) llevan otra rama al selector rotatorio (no dibujada).")
    # divisor
    s.wire((420, 120), (440, 120)); s.L((440, 120), (500, 120), "FB4", "ferrita")
    s.wire((500, 120), (540, 120)); s.dot(540, 120)
    s.R((540, 120), (720, 120), "R11", "10 MΩ ±0.5 %")
    s.wire((540, 120), (540, 60), (580, 60)); s.R((580, 60), (640, 60), "R9 30 kΩ", "", body=30)
    s.C((660, 60), (690, 60), "C13 · 6 pF", ""); s.wire((640, 60), (660, 60)); s.wire((690, 60), (740, 60), (740, 120))
    s.wire((720, 120), (1290, 120)); s.dot(740, 120)
    s.net(760, 120, "toma del divisor → HY3131", dy=-8)
    patas = [(800, "R13", "1.11 MΩ", "", "sin montar", "÷10"),
             (960, "R15", "101 kΩ", "C19+C20", "596 pF", "÷100"),
             (1120, "R21", "10 kΩ", "C22+C23", "6.35 nF", "÷1000"),
             (1280, "R26", "1 kΩ", "C24+C26", "66 nF", "÷10000")]
    for x, rn, rv, cn, cv, d in patas:
        s.dot(x, 120); s.R((x, 120), (x, 250), rn, rv, side="l")
        if cn:
            s.wire((x, 130), (x + 40, 130)); s.dot(x, 130)
            s.C((x + 40, 130), (x + 40, 250), cn, cv, side="r")
            s.wire((x, 250), (x + 40, 250)); s.dot(x, 250)
        else:
            s.note(x + 8, 200, "C16, C17")
            s.note(x + 8, 216, "sin montar")
        s.wire((x, 250), (x, 330)); s.note(x + 6, 300, d)
    B = s.box(760, 342, 600, 60, "", "", pins=(("t", 40, "PA", "a"), ("t", 200, "PA", "b"), ("t", 360, "PA", "c"), ("t", 520, "PA", "d")))
    s.text(1060, 380, "U3 · HY3131: pone a masa la pata elegida", "ref", "middle")
    s.note(560, 460, f"τ arriba = R11 · C13 = {K.TAU_TOP*1e6:.0f} µs. Patas: ÷100 {K.div['÷100']['tau']*1e6:.0f} µs, ÷1000 {K.div['÷1000']['tau']*1e6:.0f} µs, ÷10000 {K.div['÷10000']['tau']*1e6:.0f} µs.")
    s.note(560, 478, "R9 amortigua C13: limita el pico de corriente por el condensador en un transitorio.")
    s.note(560, 496, "Emparejamiento R–C deducido de la disposición del esquema (NO VERIFICADO).")
    return s.svg()


def corriente():
    s = Sch(1300, 420, "121GW: derivadores, puente de diodos y amplificador ×10 de baja caida")
    p = s.banana(70, 80, "mA/µA", "#b3261e")
    s.wire(p, (110, 80)); s.FUSE((110, 80), (230, 80), "F1", "400–440 mA HRC")
    s.wire((230, 80), (300, 80)); s.dot(270, 80)
    s.D((270, 80), (270, 160), "BD1", "DF10S, +/− unidos", side="l", kind="tvs"); s.gnd(270, 160)
    s.wire((300, 80), (330, 80))
    s.text(340, 72, "selector", "pin")
    s.wire((380, 80), (420, 80)); s.dot(420, 80)
    s.wire((330, 80), (380, 80))
    s.R((420, 80), (420, 190), "R33", "100 Ω", side="l"); s.dot(420, 190)
    s.R((420, 190), (420, 290), "R43", "1 Ω", side="l"); s.dot(420, 290)
    s.R((420, 290), (420, 370), "SHUNT", "0.01 Ω", side="l"); s.gnd(420, 370)
    s.net(426, 80, "A_OUT (µA)", dy=-6); s.net(426, 190, "mA", dy=-6)
    p2 = s.banana(170, 290, "10 A", "#b3261e")
    s.wire(p2, (200, 290)); s.FUSE((200, 290), (330, 290), "F2", "11 A HRC 1000 V", side="b"); s.wire((330, 290), (420, 290))
    s.wire((420, 80), (560, 80)); s.L((560, 80), (610, 80), "FB2", ""); s.R((610, 80), (700, 80), "R126", "100 Ω")
    A = s.opamp(770, 96, "U8 · MAX4238", "deriva cero, ×10", inp_top=True)
    s.wire((700, 80), A["inp"])
    s.wire(A["inm"], (740, 112), (740, 200)); s.dot(740, 200)
    s.R((740, 200), (740, 300), "R46", "10 kΩ", side="l"); s.gnd(740, 300)
    s.R((740, 200), (860, 200), "R106", "90 kΩ", side="b"); s.wire((860, 200), (880, 200), (880, 96)); s.dot(880, 96)
    s.wire(A["out"], (980, 96)); s.net(900, 96, "×10", dy=-6)
    s.wire((560, 80), (560, 40), (980, 40)); s.dot(560, 80); s.net(600, 40, "×1", dy=-6)
    B = s.box(980, 24, 150, 96, "", "", pins=(("r", 48, "", "o"),))
    s.text(1055, 66, "U11 · 74HC4053", "ref", "middle"); s.text(1055, 84, "×1 o ×10", "pin", "middle")
    s.wire(B["o"], (1180, 72)); s.port(1180, 72, "A_IN → HY3131", "r")
    s.note(560, 360, f"Caída del manual: 100 µV/µA, 2 mV/mA y 0.03 V/A (incluye el fusible). En 50 µA el ×10 lleva {K.V_50uA*1e3:.1f} mV a {K.V_50uA*K.G_LOWBURDEN*1e3:.0f} mV.")
    s.note(560, 380, "El puente con los terminales de continua unidos deja dos diodos en serie en cada sentido (≈ 1.4 V).")
    return s.svg()


if __name__ == "__main__":
    for f in (entrada, corriente):
        print(f.__name__, len(f()))
