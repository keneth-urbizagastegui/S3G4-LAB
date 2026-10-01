# -*- coding: utf-8 -*-
"""Redibujo propio (simplificado) del canal del DSO112 a partir de schematic_112g.pdf, hoja 2."""
from sch import Sch

def entrada():
    s = Sch(1300, 480, "DSO112 - entrada, acoplo, atenuador grueso y buffer")
    y = 180
    p = s.bnc(60, y, "J6", "MCX-V")
    s.wire(p, (120, y)); s.dot(120, y)
    s.C((120, y), (250, y), "C21", "0.1 µF 100 V", side="b")
    B = s.box(145, 70, 80, 40, "RLY1 · CPC1017N", "", pins=(("l", 20, "", "l"), ("r", 20, "", "r")))
    s.text(185, 95, "PhotoMOS", "pin", "middle")
    s.wire((120, y), (120, 90), B["l"]); s.wire(B["r"], (250, 90), (250, y))
    s.note(185, 250, "CPLSEL = 0 → cortocircuita C21 → DC", "middle")
    s.dot(250, y); s.wire((250, y), (300, y)); s.dot(300, y); s.net(256, y, "N1")
    # rama x1
    s.wire((300, y), (300, 100))
    s.R((300, 100), (440, 100), "R31", "100 kΩ")
    s.wire((300, 100), (300, 50)); s.wire((440, 100), (440, 50))
    s.C((300, 50), (440, 50), "C22", "270 pF")
    s.dot(300, 100); s.dot(440, 100)
    s.wire((440, 100), (880, 100)); s.net(470, 100, "rama ×1")
    # rama :100
    s.wire((300, y), (300, 260))
    s.R((300, 260), (400, 260), "R37", "910 kΩ 1 %")
    s.R((400, 260), (500, 260), "R38", "82 kΩ 1 %")
    s.wire((300, 260), (300, 320)); s.wire((500, 260), (500, 320))
    s.C((300, 320), (500, 320), "C23", "3 pF", side="b")
    s.dot(300, 260); s.dot(500, 260)
    s.wire((500, 260), (880, 260))
    for x, (n, v, kind) in zip((530, 660, 790), (("R40", "10 kΩ 1 %", "R"), ("C24", "25 pF aj.", "T"), ("C25", "150 pF", "C"))):
        s.dot(x, 260)
        if kind == "R": s.R((x, 260), (x, 370), n, v, side="r")
        else: s.C((x, 260), (x, 370), n, v, side="r", trim=(kind == "T"))
        s.gnd(x, 370)
    # rele
    K = s.spdt(940, y, "RLY2A · TQ2", "1/1 · bobina ON", "1/100 · reposo", pos="b", span=80, dx=60, flip=True)
    s.wire(K["com"], (1010, y)); s.dot(1010, y); s.net(1016, y, "G", dy=-6)
    s.D((1010, 300), (1010, y), "D1", "1N4148", side="r"); s.rail(1010, 300, "AV−", up=False)
    s.R((1010, y), (1010, 70), "R50", "10 MΩ", side="r")
    s.port(1010, 62, "servo U7B", "r")
    U = s.box(1090, 150, 110, 60, "Q3 J309 + Q4", "buffer", pins=(("l", 30, "G", "g"), ("r", 30, "S", "o")))
    s.wire((1010, y), U["g"]); s.net(1216, y, "TP39")
    s.note(20, 420, "Zin ≈ 1 MΩ en las dos posiciones: el divisor ÷100 (992 k + 10 k) está siempre conectado a N1; el relé sólo elige qué nodo va al buffer.", "start")
    s.note(20, 438, "Rama ×1: R31 limita la corriente de falla (0.45 mA con 50 V) y C22 la puentea en alta frecuencia: τ = 100 k · 270 p = 27 µs ≈ R50 · C_puerta.", "start")
    s.note(20, 456, "Protección: R31 + unión puerta-drenador del J309 hacia AV+ (positiva) + D1 hacia AV− (negativa). No hay TVS. RLY2B (segundo polo) no se usa.", "start")
    return s.svg()

LAD = [("R27", "499 Ω", "X1_1"), ("R29", "249 Ω", "X1_2"), ("R32", "150 Ω", "X1_4"),
       ("R34", "49.9 Ω", "X1_10"), ("R39", "24.9 Ω", "X1_20"), ("R41", "24.9 Ω", "X1_40")]
MUX = ["GND", "X1_40", "X1_20", "VCHECK", "X1_10", "X1_1", "X1_4", "X1_2"]

def ganancia():
    s = Sch(1300, 600, "DSO112 - escalera, selector, ganancia fija y ADC")
    x, y0, dy = 150, 120, 62
    s.port(20, y0, "TP39 buffer", "r"); s.wire((112, y0), (x, y0))
    ys = [y0 + i*dy for i in range(7)]
    for i, (n, v, t) in enumerate(LAD):
        s.R((x, ys[i]), (x, ys[i+1]), n, v, side="l")
        s.dot(x, ys[i]); s.wire((x, ys[i]), (290, ys[i])); s.net(196, ys[i], t)
    s.gnd(x, ys[6])
    pins = tuple(("l", 30 + i*48, f"I/O{i}", f"p{i}") for i in range(8)) + \
           (("r", 220, "I/O", "com"), ("b", 35, "A", "a"), ("b", 70, "B", "b"), ("b", 105, "C", "c"))
    U = s.box(400, 100, 140, 400, "U5 · 74HC4051", "", pins=pins)
    for i, t in enumerate(MUX):
        py = U[f"p{i}"][1]
        if t == "GND":
            s.wire((352, py), U[f"p{i}"]); s.gnd(352, py)
        else:
            s.wire((300, py), U[f"p{i}"]); s.net(304, py, t)
    for k in ("a", "b", "c"): s.wire(U[k], (U[k][0], 530))
    s.text(470, 548, "SENSEL0–2 ← ATmega64", "pin", "middle")
    A = s.opamp(620, 336, "U6A", "×20.07", inp_top=True)
    s.wire(U["com"], (580, 320), A["inp"])
    s.wire(A["inm"], (600, 352), (600, 420)); s.dot(600, 420)
    s.R((600, 420), (720, 420), "R30", "1.43 kΩ", side="b")
    s.R((600, 420), (600, 500), "R35", "75 Ω", side="l"); s.gnd(600, 500)
    s.wire(A["out"], (740, 336)); s.dot(720, 336); s.wire((720, 420), (720, 336))
    s.R((740, 336), (820, 336), "R25", "499 Ω")
    B = s.opamp(860, 352, "U6B", "×2", inp_top=True)
    s.wire((820, 336), B["inp"])
    s.wire(B["inm"], (840, 368), (840, 440)); s.dot(840, 440)
    s.R((840, 440), (960, 440), "R33", "1 kΩ", side="b")
    s.wire(B["out"], (1040, 352)); s.dot(960, 352); s.wire((960, 440), (960, 352))
    s.R((840, 440), (840, 510), "R36", "909 Ω", side="l"); s.dot(840, 510)
    s.wire((840, 510), (780, 510)); s.C((780, 510), (780, 560), "C26", "0.1 µF", side="l"); s.gnd(780, 560)
    s.R((840, 510), (950, 510), "R42", "100 Ω", side="b"); s.port(950, 510, "offset U7A", "r")
    s.dot(1040, 352); s.net(972, 352, "ANALOG")
    s.R((1040, 352), (1130, 352), "R19", "100 Ω", side="b")
    s.dot(1150, 352); s.wire((1130, 352), (1170, 352))
    s.C((1150, 352), (1150, 420), "C13", "100 pF", side="l"); s.gnd(1150, 420)
    s.port(1170, 352, "TLC5510 VIN", "r")
    s.note(1290, 60, "Ganancia fija ≈ ×40 (×20.07 · ×1.99); la escalera sólo atenúa.", "end")
    s.note(1290, 78, "I/O0 a masa: autocero y acoplo GND por software.", "end")
    s.note(1290, 96, "I/O3 = VCHECK: AREF 2.56 V · 75 / 10 075 = 19.1 mV.", "end")
    s.note(1290, 130, "ANALOG también va a R16 1 kΩ / C12 150 pF → comparador", "end")
    s.note(1290, 148, "del ATmega64 (disparo) y a R73 ∥ C57 → C5 → T1 (frecuencia).", "end")
    s.note(1290, 250, "ADC de 8 bits, 0.6–2.6 V por autopolarización (VRT/VRB).", "end")
    s.note(1290, 268, "No hay filtro anti-alias: R19/C13 cortan en 16 MHz.", "end")
    return s.svg()
