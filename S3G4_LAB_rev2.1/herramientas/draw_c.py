# -*- coding: utf-8 -*-
"""Rev 2.1 seccion C: seleccion gruesa x1 / :20 y cadena de ganancia."""
from sch import Sch

def grueso():
    s = Sch(1300, 430, "Rev 2.1 - seleccion gruesa x1 / :20 por rele latching")
    y = 155
    p = s.bnc(60, y, "J101", "KH-BNC50-3511")
    s.wire(p, (150, y)); s.net(80, y, "NET_IN_CH"); s.dot(150, y)
    # rama :20 (la de la seccion B)
    s.wire((150, y), (150, 80), (208, 80))
    P = s.box(220, 55, 260, 50, "Divisor ÷20 · sección B", "", pins=(("l", 25, "IN", "i"), ("r", 25, "TAP", "o")))
    s.wire(P["o"], (574, 80)); s.net(500, 80, "NET_TAP20", dy=15)
    s.note(350, 128, "1 MΩ permanente · 0.35 mA con 353 V", "middle")
    # rama x1: resistencia serie compensada
    s.wire((150, y), (150, 230), (230, 230))
    s.R((230, 230), (330, 230), "R_S", "10 kΩ 1 % 1206")
    s.wire((230, 230), (230, 290)); s.wire((330, 230), (330, 290))
    s.C((230, 290), (330, 290), "C_S", "10 nF C0G 100 V", side="b")
    s.dot(230, 230); s.dot(330, 230)
    s.wire((330, 230), (574, 230)); s.net(400, 230, "NET_X1")
    # rele
    K = s.spdt(640, y, "K101", "÷20 (arranque)", "×1", pos="a", span=75, dx=60, flip=True)
    s.wire((574, 80), K["a"]); s.wire((574, 230), K["b"])
    s.wire(K["com"], (1060, y)); s.net(664, y, "NET_SEL")
    # sujecion y TVS en el nodo seleccionado
    s.dot(820, y)
    s.D((820, y), (820, 85), "D102", "½ BAV199 → +5 V", side="r"); s.rail(820, 85, "VCC_P5")
    s.D((820, 245), (820, y), "D103", "½ BAV199 ← −5 V", side="r"); s.rail(820, 245, "VCC_N5", up=False)
    s.dot(960, y)
    s.D((960, y), (960, 245), "D101", "TVS bidir. 5 V", kind="tvs"); s.gnd(960, 245)
    s.port(1060, y, "→ SW101 acoplo → buffer", "r")
    s.note(20, 350, "En ÷20 la rama ×1 queda abierta: su nodo está a la tensión de la BNC pero no conduce; la capacidad", "start")
    s.note(20, 366, "del contacto abierto (~1 pF) queda en paralelo con C1A–C1C y el ajuste de compensación la absorbe.", "start")
    s.note(20, 390, "R_S·C_S = 100 µs ≈ R_BIAS·C_in: la rama ×1 es un divisor compensado de relación 1.001 → plano, sin ajuste.", "start")
    s.note(20, 414, "K101 latching no tiene reposo: el firmware lo lleva a ÷20 al arrancar, al apagar y al detectar saturación.", "start")
    return s.svg()

LAD = [("RL1", "499 Ω", "1/1"), ("RL2", "249 Ω", "1/2"), ("RL3", "49.9 Ω", "1/4"), ("RL4", "100 Ω", "1/5"),
       ("RL5", "49.9 Ω", "1/10"), ("RL6", "30.1 Ω", "1/20"), ("RL7", "10.0 Ω", "1/50"), ("RL8", "10.0 Ω", "1/100")]

def ganancia():
    s = Sch(1300, 540, "Rev 2.1 - escalera fina tras el buffer y ganancia fija x50")
    x, y0, dy = 160, 120, 44
    s.port(20, y0, "U101A buffer", "r")
    s.wire((125, y0), (x, y0))
    ys = [y0 + i*dy for i in range(9)]
    for i, (n, v, t) in enumerate(LAD):
        s.R((x, ys[i]), (x, ys[i+1]), n, v, side="l")
        s.dot(x, ys[i]); s.wire((x, ys[i]), (318, ys[i]))
        s.text(250, ys[i]-4, t, "pin", "middle")
    s.gnd(x, ys[8])
    pins = tuple(("l", ys[i]-100, f"X{i}", f"x{i}") for i in range(8)) + \
           (("r", 180, "X", "com"), ("b", 30, "A", "a"), ("b", 60, "B", "b"), ("b", 90, "C", "c"))
    U = s.box(330, 100, 120, 360, "U102 · 74HCT4051", "", pins=pins)
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
    s.note(1290, 76, "es el mismo en las 11 escalas, como en el DSO112.", "end")
    s.note(1290, 110, "Cadena de 1 kΩ: la toma de mayor impedancia ve 250 Ω;", "end")
    s.note(1290, 126, "con ≤60 pF del 74HCT4051 el polo queda en ≥10 MHz.", "end")
    s.note(1290, 160, "El 4051 entrega a una entrada no inversora: su Ron no", "end")
    s.note(1290, 176, "lleva corriente y no introduce error de ganancia.", "end")
    s.note(1290, 420, "U102: VCC +5 V · VEE −5 V · VCC−VEE = 10 V, justo en su máximo.", "end")
    s.note(1290, 436, "HCT porque sus entradas aceptan 3.3 V como nivel alto.", "end")
    return s.svg()
