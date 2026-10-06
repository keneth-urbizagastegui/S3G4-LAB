# -*- coding: utf-8 -*-
"""Rev 2.1 seccion C: entrada P4b (grueso x1 / :100 con replica de carga) y cadena de ganancia.
Regenerado el 2 oct 2026 con P1 (:100, 6 tomas) y P4b (revision_entrada_ch1.html)."""
from sch import Sch

def grueso():
    s = Sch(1300, 520, "Rev 2.1 - entrada P4b: divisor :100, rama x1 y rele DPDT con replica de carga")
    y = 180
    p = s.bnc(60, y, "J101", "KH-BNC50-3511")
    s.wire(p, (150, y)); s.net(80, y, "NET_IN_CH"); s.dot(150, y)
    # rama :100 (siempre conectada)
    s.wire((150, y), (150, 70), (170, 70))
    s.R((170, 70), (290, 70), "R1A", "549 kΩ 0.1 % 1206")
    s.wire((170, 70), (170, 120)); s.wire((290, 70), (290, 120))
    s.C((170, 120), (290, 120), "C1A", "20 pF C0G", side="b")
    s.dot(170, 70); s.dot(290, 70)
    s.wire((290, 70), (320, 70))
    s.R((320, 70), (440, 70), "R1B", "549 kΩ 0.1 % 1206")
    s.wire((320, 70), (320, 200)); s.wire((440, 70), (440, 200))
    s.C((320, 120), (440, 120), "C1B", "20 pF C0G", side="b")
    s.C((320, 200), (440, 200), "C_TRIM", "trimmer · rango S1b", side="b", trim=True)
    s.dot(320, 70); s.dot(440, 70); s.dot(320, 120); s.dot(440, 120)
    s.wire((440, 70), (680, 70)); s.net(468, 70, "NET_TAP", dy=-5)
    s.dot(560, 70); s.R((560, 70), (560, 170), "R2", "11.0 kΩ 0.1 %", side="l"); s.gnd(560, 170)
    s.dot(610, 70); s.C((610, 70), (610, 170), "C2", "≈1.08 nF C0G", side="r"); s.gnd(610, 170)
    # rama x1: R_S partida en dos 1206 y C_S en paralelo con las dos
    s.wire((150, y), (150, 290), (170, 290))
    s.R((170, 290), (270, 290), "R_S1", "49.9 kΩ 1206")
    s.R((300, 290), (400, 290), "R_S2", "49.9 kΩ 1206")
    s.wire((270, 290), (300, 290))
    s.wire((170, 290), (170, 340)); s.wire((400, 290), (400, 340))
    s.C((170, 340), (400, 340), "C_S", "1.5 nF C0G 100 V", side="b")
    s.dot(170, 290); s.dot(400, 290)
    s.wire((400, 290), (680, 290)); s.net(520, 290, "NET_X1"); s.dot(470, 290)
    # rele K101A: elige toma o X1
    K = s.spdt(780, y, "K101A", "÷100 (reposo)", "×1", pos="a", span=110, dx=100, flip=True)
    
    s.wire(K["com"], (960, y)); s.net(786, y, "NET_SEL")
    # K101B: replica de la carga de SEL colgada de X1 en reposo
    s.wire((470, 290), (470, 430), (500, 430))
    KB = s.spdt(500, 430, "", "reposo: cerrado", "×1: abierto", pos="a", span=25, dx=60)
    s.text(470, 470, "K101B", "ref", "middle")
    s.wire(KB["a"], (720, 405)); s.dot(720, 405)
    s.R((720, 405), (720, 485), "R_EQ", "10 MΩ (= R_BIAS)", side="l"); s.gnd(720, 485)
    s.wire((720, 405), (800, 405))
    s.C((800, 405), (800, 485), "C_EQ", "≈12 pF · en prueba", side="r"); s.gnd(800, 485)
    # sujecion a los rieles
    s.dot(870, y)
    s.D((870, y), (870, 100), "D102", "½ BAV199 → +5 V", side="r"); s.rail(870, 100, "VCC_P5")
    s.D((870, 260), (870, y), "D103", "½ BAV199 ← −5 V", side="r"); s.rail(870, 260, "VCC_N5", up=False)
    s.port(960, y, "→ SW101 · R_BIAS · R_PROT → buffer", "r")
    s.note(950, 250, "Divisor siempre conectado: (Rt+Rb) ∥ (R_S+R_BIAS)", "start")
    s.note(950, 266, "= 1.109 MΩ ∥ 10.1 MΩ = 999 kΩ en ×1 y en ÷100.", "start")
    s.note(950, 296, "K101 monoestable DPDT: sin corriente está en ÷100;", "start")
    s.note(950, 312, "el polo B cuelga de X1 la réplica R_EQ ∥ C_EQ de", "start")
    s.note(950, 328, "la carga de SEL: Zin y Cin no cambian al conmutar.", "start")
    s.note(950, 358, "Con 100 V: 0.09 mA por el divisor, 0.95 mA por R_S.", "start")
    s.note(950, 374, "Sin TVS en SEL (por su fuga): una TVS en cada riel.", "start")
    s.note(950, 404, "C_TRIM: un trimmer por canal (planitud de ÷100).", "start")
    s.note(950, 420, "C_EQ: C0G fijo seleccionado al medir el prototipo.", "start")
    return s.svg()

LAD = [("RL1", "499 Ω", "1/1"), ("RL2", "249 Ω", "1/2"), ("RL3", "150 Ω", "1/4"),
       ("RL4", "49.9 Ω", "1/10"), ("RL5", "24.9 Ω", "1/20"), ("RL6", "24.9 Ω", "1/40")]

def ganancia():
    s = Sch(1300, 540, "Rev 2.1 - escalera de 6 tomas con GND y VCHECK tras el buffer, y ganancia fija x50")
    x, y0, dy = 160, 120, 44
    s.port(20, y0, "U101A buffer", "r")
    s.wire((125, y0), (x, y0))
    ys = [y0 + i*dy for i in range(len(LAD) + 1)]
    for i, (n, v, t) in enumerate(LAD):
        s.R((x, ys[i]), (x, ys[i+1]), n, v, side="l")
        s.dot(x, ys[i]); s.wire((x, ys[i]), (318, ys[i]))
        s.text(250, ys[i]-4, t, "pin", "middle")
    s.gnd(x, ys[-1])
    yx = [y0 + i*dy for i in range(8)]
    pins = tuple(("l", yx[i]-100, f"X{i}", f"x{i}") for i in range(8)) + \
           (("r", 180, "X", "com"), ("b", 30, "A", "a"), ("b", 60, "B", "b"), ("b", 90, "C", "c"))
    U = s.box(330, 100, 120, 360, "U102 · 74HC4051", "", pins=pins)
    # X6 = masa (autocero), X7 = VCHECK
    s.wire((318, yx[6]), (290, yx[6])); s.gnd(290, yx[6])
    s.text(250, yx[6]-4, "GND", "pin", "middle")
    s.port(318, yx[7], "VCHECK", "l")
    for k in ("a", "b", "c"):
        s.wire(U[k], (U[k][0], 495))
    s.text(390, 512, "SENSEL_A/B/C ← 74HCT595", "pin", "middle")
    # etapa A x5
    A = s.opamp(560, 296, "U103A", "×5", inp_top=True)
    s.wire(U["com"], (500, 280), (500, A["inp"][1]), A["inp"])
    s.wire(A["inm"], (540, A["inm"][1]), (540, 370)); s.dot(540, 370)
    s.R((540, 370), (660, 370), "R_F1", "4.02 kΩ", side="b")
    s.R((540, 370), (540, 450), "R_G1", "1.00 kΩ", side="l"); s.gnd(540, 450)
    s.wire(A["out"], (700, 296)); s.dot(660, 296); s.wire((660, 370), (660, 296))
    # etapa B x10
    B = s.opamp(760, 296, "U103B", "×10", inp_top=True)
    s.wire((700, 296), (700, B["inp"][1]), B["inp"])
    s.wire(B["inm"], (740, B["inm"][1]), (740, 370)); s.dot(740, 370)
    s.R((740, 370), (860, 370), "R_F2", "9.09 kΩ", side="b")
    s.R((740, 370), (740, 450), "R_G2", "1.00 kΩ", side="l"); s.gnd(740, 450)
    s.wire(B["out"], (900, 296)); s.dot(860, 296); s.wire((860, 370), (860, 296))
    s.port(900, 296, "→ filtro anti-alias (sección D)", "r")
    s.note(1290, 60, "La escalera ATENÚA y la ganancia es FIJA: el ancho de banda", "end")
    s.note(1290, 76, "es el mismo en las 12 escalas, como en el DSO112.", "end")
    s.note(1290, 110, "Seis tomas (1 … 1/40), usadas con el grueso en ×1 y en ÷100.", "end")
    s.note(1290, 126, "X6 a masa: autocero. X7: VCHECK, comprobación de ganancia (P3).", "end")
    s.note(1290, 160, "Cadena de 997.7 Ω: la toma de mayor impedancia ve 250 Ω;", "end")
    s.note(1290, 176, "con Ron ≤ 130 Ω y ~30 pF, el polo queda en ~14 MHz.", "end")
    s.note(1290, 210, "El 4051 entrega a una entrada no inversora: su Ron no", "end")
    s.note(1290, 226, "lleva corriente y no introduce error de ganancia.", "end")
    s.note(1290, 420, "U102: VCC +5 V · VEE −5 V · VCC−VEE = 10 V, justo en su máximo.", "end")
    s.note(1290, 436, "HC basta: lo gobierna el 74HCT595 a 5 V.", "end")
    return s.svg()
