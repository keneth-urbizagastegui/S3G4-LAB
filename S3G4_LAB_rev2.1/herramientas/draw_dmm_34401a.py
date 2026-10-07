# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del Agilent 34401A, a partir de los esquemas del manual de servicio
(research_and_tests/Agilent_34401A/34401A_Service_Guide.pdf, hojas 3 y 4, pp. 159-160).
La fuente de ohmios se dibuja por bloques; el atenuador de alterna, pieza a pieza (sin el modo ×0.002)."""
from sch import Sch
import calc_dmm_34401a as K


def ohmios():
    s = Sch(1300, 500, "34401A: fuente de corriente de ohmios y su proteccion de ±1000 V")
    s.wire((180, 70), (640, 70)); s.net(250, 70, "≈ +12.9 V (18 V menos un zéner de 5.1 V)", dy=-8)
    s.dot(240, 70); s.dot(420, 70)
    s.R((240, 70), (240, 170), "28.57 kΩ", "U102D", side="l")
    s.dot(240, 170); s.wire((240, 170), (180, 170), (180, 208))
    s.box(90, 220, 140, 80, "", "", pins=(("t", 90, "", "t"),))
    s.text(160, 246, "U201A + Q201", "ref", "middle")
    s.text(160, 266, "IREF = 7 V / 40 kΩ", "pin", "middle"); s.text(160, 284, "(o 7 V / 400 kΩ)", "pin", "middle")
    s.R((420, 70), (420, 170), "R de rango", "5 k · 50 k · 500 k · 1 M", side="r")
    B = s.box(370, 190, 140, 60, "", "", pins=(("t", 50, "", "t"), ("r", 20, "fuerza", "f"), ("b", 50, "sentido", "s")))
    s.text(440, 232, "U101E", "ref", "middle")
    s.wire((420, 170), B["t"])
    A = s.opamp(320, 350, "U201B", "", inp_top=True)
    s.wire((240, 170), (240, 334), A["inp"])
    s.wire(B["s"], (420, 410), (290, 410), (290, 366), A["inm"])
    Q = s.box(560, 190, 90, 40, "Q202 · JFET", "", pins=(("l", 20, "", "i"), ("r", 20, "", "o"), ("b", 45, "", "g")))
    s.wire(B["f"], Q["i"])
    s.wire(A["out"], (605, 350), Q["g"])
    E = s.box(700, 180, 210, 60, "Q203–Q210 · Q211", "", pins=(("l", 30, "", "i"), ("r", 30, "", "o")))
    s.text(805, 206, "4 escalones de transistores", "pin", "middle"); s.text(805, 222, "en serie (Vcb sumadas)", "pin", "middle")
    s.wire(Q["o"], E["i"])
    s.D((922, 210), (1000, 210), "CR202", "")
    s.wire((1000, 210), (1030, 210)); s.port(1030, 210, "K102 → Input HI", "r")
    s.note(40, 446, "U201B copia en la R de rango la caída que IREF crea en 28.57 kΩ (5 V o 0.5 V); el conmutador lleva fuerza y sentido por separado.")
    s.note(40, 464, "Corrientes: " + ", ".join(f"{n} → " + (f"{i*1e3:.3g} mA" if i >= 0.9995e-3 else f"{i*1e6:.3g} µA") for n, i in K.I_OHM.items()) + ".")
    s.note(40, 482, "Con tensión positiva en HI se bloquea CR202; con negativa, la escalera de transistores, polarizada por Q211 y R203–R206 (4 × 196 kΩ).")
    return s.svg()


def alterna():
    s = Sch(1300, 560, "34401A: atenuador de alterna ×0.2 con condensador programable")
    s.port(40, 120, "AC_IN", "r")
    s.wire((100, 120), (150, 120)); s.C((150, 120), (230, 120), "C301", "0.22 µF")
    s.wire((230, 120), (380, 120)); s.dot(270, 120)
    s.C((380, 120), (420, 120), "C302", "1.8 pF")
    s.wire((420, 120), (460, 120)); s.dot(460, 120)
    s.wire((270, 120), (270, 210)); s.R((270, 210), (420, 210), "R301 + R302", "2 × 500 kΩ", side="b")
    s.wire((420, 210), (460, 210)); s.dot(460, 210)
    s.wire((460, 120), (460, 310))
    s.net(466, 300, "S (masa virtual)", dy=0)
    A = s.opamp(540, 226, "U301", "")
    s.wire((460, 210), A["inm"]); s.wire(A["inp"], (510, 242), (510, 260)); s.gnd(510, 260)
    s.wire(A["out"], (700, 226)); s.dot(660, 226)
    s.wire((460, 120), (460, 60), (490, 60)); s.R((490, 60), (630, 60), "R304", "200 kΩ"); s.wire((630, 60), (660, 60), (660, 226))
    s.dot(460, 60)
    s.C((480, 130), (520, 130), "C304", ""); s.text(500, 160, "6.8 pF", "val", "middle")
    s.wire((460, 130), (480, 130)); s.R((540, 130), (620, 130), "R313", "", body=30); s.text(580, 160, "6.19 kΩ", "val", "middle")
    s.wire((520, 130), (540, 130)); s.wire((620, 130), (660, 130)); s.dot(660, 130); s.dot(460, 130)
    s.port(700, 226, "→ 2.ª etapa (×1, ×10, ×100)", "r")
    # condensador programable
    s.C((460, 310), (460, 370), "C306", "5.6 pF", side="r")
    s.wire((460, 370), (460, 400)); s.dot(460, 400)
    U = s.opamp(320, 400, "U303", "seguidor", inp_top=True)
    s.wire(U["out"], (460, 400))
    s.wire(U["inm"], (300, 416), (300, 450), (400, 450), (400, 400)); s.dot(400, 400)
    D = s.box(90, 350, 150, 80, "U302 · AD7524", "", pins=(("r", 34, "V·P/256", "o"), ("b", 75, "V", "i")))
    s.text(165, 410, "DAC multiplicador", "pin", "middle")
    s.wire(D["o"], U["inp"])
    s.wire((660, 226), (660, 480), (165, 480), D["i"])
    s.note(40, 516, f"Baja frecuencia: −200 kΩ / 1 MΩ = ×{K.G_AC}. El pie de C306 sigue a V_OUT·P/256: es una capacidad de realimentación de 0 a 5.6 pF en 256 pasos ({K.C_PASO*1e15:.0f} fF).")
    s.note(40, 534, f"Respuesta plana con C302 / C_fb = 0.2, es decir, C_fb ≈ {K.C_FB_PLANO*1e12:.0f} pF (P ≈ {K.P_PLANO:.0f} sin contar R313). El paso se calibra a 50 kHz en cada rango.")
    return s.svg()


if __name__ == "__main__":
    for f in (ohmios, alterna):
        print(f.__name__, len(f()))
