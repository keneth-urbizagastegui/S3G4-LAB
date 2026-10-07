# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del HydraMeter 0.4, a partir de la netlist exportada con kicad-cli
(hojas Volt_AFE, Amp_AFE y Ohm_AFE). Valores y referencias tal cual el proyecto KiCad."""
from sch import Sch
import calc_dmm_hydrameter as K


def tension():
    s = Sch(1300, 520, "HydraMeter: entrada de tension con proteccion escalonada")
    p = s.banana(70, 120, "Vpin", "#b3261e")
    s.wire(p, (100, 120))
    s.R((100, 120), (220, 120), "R1+R2", "2 × 100 kΩ THT")
    s.wire((220, 120), (260, 120)); s.dot(240, 120)
    s.wire((110, 120), (110, 70), (140, 70)); s.dot(110, 120)
    s.C((140, 70), (180, 70), "C54 · 1.5 nF", "")
    s.wire((180, 70), (240, 70), (240, 120))
    s.wire((240, 70), (240, 30), (330, 30)); s.C((330, 30), (370, 30), "C55 · 220 pF", "")
    s.wire((370, 30), (560, 30), (560, 120))
    s.R((260, 120), (360, 120), "R3", "400 kΩ THT")
    s.wire((360, 120), (400, 120)); s.dot(380, 120)
    s.R((400, 120), (500, 120), "R4", "400 kΩ THT")
    s.wire((500, 120), (1100, 120))
    s.net(250, 120, "N1", dy=16); s.net(390, 120, "N2", dy=16); s.net(566, 120, "Vout", dy=16)
    # descargadores al borne COM
    s.D((240, 120), (240, 300), "RT1", "MOV 230 Vrms", side="l", kind="tvs")
    s.D((380, 120), (380, 300), "RT2", "GDT 75 V", side="r", kind="tvs")
    s.wire((220, 300), (380, 300)); s.dot(240, 300)
    s.port(220, 300, "Common_Jack", "l")
    # nodo Vout
    s.dot(560, 120)
    s.D((560, 120), (560, 300), "RT3", "MOV 3.3 V", side="l", kind="tvs")
    s.dot(640, 120); s.R((640, 120), (640, 300), "R12", "9.1 MΩ", side="r")
    s.dot(720, 120); s.C((720, 120), (720, 300), "C73", "33 pF", side="r")
    for x, rn, rv, cn, cv in ((850, "R13", "100 kΩ", "C59", "1.8 nF"), (1010, "R14", "6.8 kΩ", "C61", "27 nF")):
        s.dot(x, 120); s.R((x, 120), (x, 240), rn, rv, side="l")
        s.wire((x, 130), (x + 40, 130)); s.dot(x, 130)
        s.C((x + 40, 130), (x + 40, 240), cn, cv, side="r")
        s.wire((x, 240), (x + 40, 240)); s.dot(x, 240)
        s.wire((x, 240), (x, 330))
    U1 = s.box(800, 342, 300, 50, "", "", pins=(("t", 50, "NO1", "a"), ("t", 210, "NO2", "b"), ("b", 150, "COM", "c")))
    s.text(950, 374, "U1 · NL7WB66 (2 × SPST, 3.3 V)", "ref", "middle")
    s.wire(U1["c"], (950, 440))
    for x in (560, 640, 720):
        s.wire((x, 300), (x, 440))
    s.wire((520, 440), (950, 440)); s.dot(640, 440); s.dot(720, 440)
    s.port(520, 440, "COM = 1.65 V", "l")
    s.R((1100, 120), (1180, 120), "R11", "1 kΩ"); s.wire((1180, 120), (1200, 120)); s.port(1200, 120, "CH0 → PGA", "r")
    s.note(20, 480, f"Divisiones: ÷{K.volt['÷1.11']['div']:.2f} (10.1 MΩ), ÷{K.volt['÷11.1']['div']:.1f} (1.10 MΩ), ÷{K.volt['÷148']['div']:.0f} (1.01 MΩ). "
                    f"Fondos ±{K.volt['÷1.11']['fs']:.1f}, ±{K.volt['÷11.1']['fs']:.1f} y ±{K.volt['÷148']['fs']:.0f} V con ±1.5 V en la toma.")
    s.note(20, 500, "RT1 y RT2 devuelven la corriente de falla al borne COM, no a la red COM interna; RT3 sujeta la toma a pocos voltios.")
    return s.svg()


def corriente():
    s = Sch(1300, 460, "HydraMeter: derivadores de A, mA y µA")
    pa = s.banana(70, 80, "A", "#b3261e")
    s.wire(pa, (110, 80)); s.FUSE((110, 80), (210, 80), "F1", "16 A")
    s.wire((210, 80), (600, 80)); s.dot(600, 80)
    pm = s.banana(70, 240, "mA/µA", "#b3261e")
    s.wire(pm, (110, 240)); s.FUSE((110, 240), (210, 240), "F2", "500 mA")
    s.wire((210, 240), (260, 240)); s.dot(250, 240)
    s.R((260, 240), (380, 240), "R17", "100 Ω")
    s.wire((380, 240), (420, 240)); s.dot(400, 240)
    s.R((420, 240), (540, 240), "R16", "0.33 Ω")
    s.wire((540, 240), (600, 240), (600, 80))
    # interruptor del panel que puentea R17 en mA
    s.wire((250, 240), (250, 190), (290, 190))
    S = s.spdt(320, 190, "", "", "", pos="a", span=12, dx=40)
    s.wire((360, 178), (400, 178), (400, 240))
    s.note(262, 172, "J5–J6: interruptor del panel, puentea R17 en mA")
    # diodos en antiparalelo
    s.D((260, 290), (380, 290), "D7/D8", "2 × 1N4007 antiparalelo", side="b", kind="tvs")
    s.wire((250, 240), (250, 290), (260, 290)); s.wire((380, 290), (400, 290), (400, 240))
    s.D((420, 290), (540, 290), "D9/D10", "", side="b", kind="tvs")
    s.wire((410, 240), (410, 290), (420, 290)); s.wire((540, 290), (560, 290), (560, 240)); s.dot(560, 240); s.dot(410, 240)
    # derivador de 4 terminales
    s.R((600, 80), (760, 80), "R15", "10 mΩ · 4 terminales")
    s.wire((760, 80), (900, 80)); s.port(900, 80, "Common_Jack", "r")
    s.wire((620, 80), (620, 130)); s.dot(620, 80)
    s.wire((740, 80), (740, 160)); s.dot(740, 80)
    s.net(626, 146, "sentido (pin 4)")
    s.net(746, 176, "pin 3 = COM (punto estrella)")
    s.D((600, 30), (760, 30), "D11/D12", "", kind="tvs")
    s.wire((600, 80), (600, 30)); s.wire((760, 30), (780, 30), (780, 80)); s.dot(780, 80)
    # medidas
    for y, src, lab in ((340, (250, 240), "CH2 (µA): R20+R23 2 kΩ + MOV 3.3 V"),
                        (380, (410, 240), "CH1 (mA): R19+R22 2 kΩ + MOV 3.3 V"),
                        (420, (620, 130), "CH3 (A): R18+R21 2 kΩ + MOV 3.3 V")):
        s.wire(src, (src[0], y), (900, y)); s.port(900, y, lab, "r")
    s.dot(250, 290); s.dot(410, 290)
    return s.svg()


def ohmios():
    s = Sch(1300, 520, "HydraMeter: fuente de ohmios con medida Kelvin en el borne")
    s.port(20, 70, "9V5_Ohms (B0309S aislado, ref. COM)", "r")
    s.D((262, 70), (340, 70), "D2", "1N4007")
    s.wire((340, 70), (480, 70)); s.dot(400, 70); s.net(406, 70, f"≈{K.V_RAIL:.1f} V")
    B = s.box(360, 120, 240, 70, "", "", pins=(("t", 40, "", "t"), ("b", 40, "", "b")))
    s.text(480, 146, "Q2–Q5 (P-MOS) + R26–R29", "ref", "middle")
    s.text(480, 166, "510 Ω · 10 kΩ · 100 kΩ · 1 MΩ, uno a la vez", "pin", "middle")
    s.wire((400, 70), B["t"])
    s.wire(B["b"], (400, 260)); s.dot(400, 230)
    A = s.box(700, 120, 260, 70, "", "", pins=(("l", 20, "", "hi"), ("l", 50, "", "lo"), ("r", 35, "", "o")))
    s.text(830, 146, "U4 LMC7101 + Q6 + R30/R31", "ref", "middle")
    s.text(830, 166, f"I(R) → V(CH4) = caída / {K.G_SENSE:.1f}", "pin", "middle")
    s.wire((480, 70), (660, 70), (660, 140), A["hi"])
    s.wire((400, 230), (660, 230), (660, 170), A["lo"])
    s.wire(A["o"], (1040, 155)); s.port(1040, 155, "CH4 (corriente)", "r")
    Q = s.box(340, 270, 120, 54, "", "", pins=(("t", 60, "", "d"), ("b", 60, "", "s")))
    s.text(400, 292, "Q1 · N-MOS", "ref", "middle"); s.text(400, 310, "seguidor de fuente", "pin", "middle")
    s.note(470, 300, f"puerta a la tensión del riel, o a {K.V_GATE_LOWV:.1f} V con LowV_EN (rangos altos):")
    s.note(470, 318, "limita la tensión del DUT para seguir en ÷1.11 (10 MΩ)")
    s.wire((400, 336), (400, 380)); s.dot(400, 380)
    s.wire((400, 380), (440, 380)); s.D((440, 380), (560, 380), "D1 · 1N4007 en serie", "")
    s.FUSE((580, 380), (670, 380), "F3", "63 mA"); s.wire((560, 380), (580, 380))
    s.R((690, 380), (800, 380), "R25", "1 kΩ · 1 W THT"); s.wire((670, 380), (690, 380))
    s.wire((800, 380), (860, 380))
    S = s.spdt(860, 380, "", "", "", pos="a", span=12, dx=40)
    s.wire((900, 368), (1000, 368)); s.port(1000, 368, "Vpin (borne V/Ω)", "r")
    s.note(820, 410, "interruptor del panel (J7–J8)")
    s.dot(400, 380)
    s.D((400, 470), (400, 400), "D6", "1N4007", side="l")
    s.wire((400, 380), (400, 400))
    s.wire((400, 380), (400, 380))
    s.dot(440, 380); s.wire((440, 380), (440, 400))
    s.D((440, 470), (440, 400), "RT7", "MOV 18 V", side="r", kind="tvs")
    s.wire((300, 470), (440, 470)); s.dot(400, 470)
    s.port(300, 470, "COM", "l")
    s.note(20, 505, "La tensión se mide en el borne con la entrada de tensión; la corriente, en la R de rango. D1, F3 y R25 no entran en la medida.")
    return s.svg()


if __name__ == "__main__":
    for f in (tension, corriente, ohmios):
        print(f.__name__, len(f()))
