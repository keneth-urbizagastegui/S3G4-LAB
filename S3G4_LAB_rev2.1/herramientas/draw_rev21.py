# -*- coding: utf-8 -*-
"""Esbozo del canal vertical rev 2.1: BNC -> divisor/limitador -> nodo atenuado -> buffer."""
from sch import Sch

def canal_a():
    s = Sch(1300, 560, "Rev 2.1 - entrada, divisor compensado y nodo atenuado")
    y = 120
    # BNC
    p = s.bnc(60, y, "J101", "KH-BNC50-3511")
    s.wire(p, (170, y)); s.net(78, y, "NET_IN_CH")
    s.dot(120, y); s.wire((120, y), (120, y+26)); s.tp(120, y+31, "TP_IN", "end")
    # rama superior: 3 x 316k con sus C en paralelo
    xs = [170, 300, 430, 560]
    for i, n in enumerate("ABC"):
        s.R((xs[i], y), (xs[i+1], y), f"R1{n}", "316 kΩ 0.1 %")
        s.wire((xs[i], y), (xs[i], y+60)); s.wire((xs[i+1], y), (xs[i+1], y+60))
        s.C((xs[i], y+60), (xs[i+1], y+60), f"C1{n}", "30 pF C0G 200 V", side="b")
        s.dot(xs[i], y)
    s.dot(xs[3], y)
    s.note(365, 235, "rama superior partida en tres: cada una ve 118 V con 353 V de entrada", "middle")
    s.note(365, 251, "y limita la corriente de falla a 0.37 mA — es el limitador", "middle")
    # nodo atenuado
    xn = 700
    s.wire((xs[3], y), (xn, y)); s.net(568, y, "NET_TAP")
    s.dot(620, y); s.wire((620, y), (620, y-26)); s.tp(620, y-31, "TP_TAP")
    # rama inferior
    s.dot(xn, y)
    s.R((xn, y), (xn, y+120), "R2", "49.9 kΩ 0.1 %", side="l"); s.gnd(xn, y+120)
    s.C((xn+70, y), (xn+70, y+120), "C2", "≈165 pF C0G", side="l"); s.gnd(xn+70, y+120)
    s.wire((xn, y), (xn+70, y)); s.dot(xn+70, y)
    s.note(540, y+210, "÷20.0 ·  Zin = 998 kΩ  ·  compensación C2·R2 = C1·R1", "start")
    # TVS y clamps en el nodo
    s.wire((xn+70, y), (1120, y))
    s.dot(820, y); s.D((820, y), (820, y+110), "D101", "TVS bidir. 5 V · C < 3 pF", kind="tvs"); s.gnd(820, y+110)
    s.dot(1000, y)
    s.D((1000, y), (1000, y-70), "D102", "½ BAV199 → +5 V", side="r"); s.rail(1000, y-70, "VCC_P5")
    s.D((1000, y+90), (1000, y), "D103", "½ BAV199 ← −5 V", side="r"); s.rail(1000, y+90, "VCC_N5", up=False)
    s.port(1120, y, "NET_TAP → acoplo", "r")
    s.note(1290, 300, "Con 0.37 mA de falla, los clamps pueden ir a los rieles de ±5 V:", "end")
    s.note(1290, 316, "desaparecen los rieles de sujeción de ±3 V y sus Zener.", "end")
    s.note(1290, 332, "La TVS va aquí, no en la BNC: por el divisor sólo pasan µA,", "end")
    s.note(1290, 348, "pero el ESD sí llega por los condensadores de compensación.", "end")
    return s.svg()

def canal_b():
    s = Sch(1300, 460, "Rev 2.1 - acoplo AC/DC/GND y entrada del buffer")
    y = 130
    s.port(20, y, "NET_TAP", "r"); s.wire((100, y), (150, y))
    s.frame(140, 40, 420, 250, "SW101 · SS23H37L6 · polo A (camino de señal)")
    # tres posiciones
    s.dot(150, y); s.wire((150, y), (150, 80)); s.wire((150, y), (150, 230))
    # DC directo
    s.wire((150, 80), (330, 80)); s.text(240, 72, "DC: directo", "pin", "middle")
    # AC por condensador
    s.C((150, 230), (280, 230), "C_AC", "1.5 nF C0G 50 V", side="b"); s.wire((280, 230), (330, 230))
    s.text(215, 205, "AC", "pin", "middle")
    # contactos
    c = s.spdt(430, 155, "", "", "", pos="a", span=75, dx=0.001)
    s.add('')
    s.text(360, 76, "T1", "pin"); s.text(360, 226, "T2", "pin")
    s.wire((330, 80), (420, 80)); s.wire((330, 230), (420, 230))
    s.wire((420, 155), (420, 155))
    s.text(352, 144, "T3 → AGND", "pin"); s.wire((330, 155), (420, 155)); s.gnd(330, 155)
    s.add('<circle class="ct" cx="420" cy="80" r="3"/><circle class="ct" cx="420" cy="155" r="3"/><circle class="ct" cx="420" cy="230" r="3"/>')
    s.add('<line class="blade" x1="470" y1="150" x2="426" y2="84"/>')
    s.add('<circle class="ct" cx="470" cy="150" r="3"/>')
    s.wire((470, 150), (540, 150), (540, y)); s.text(452, 300, "común", "pin", "middle")
    s.text(350, 310, "GND pone a masa la ENTRADA DEL BUFFER, nunca la BNC", "pin", "middle")
    # salida a buffer
    s.wire((540, y), (760, y)); s.net(560, y, "NET_BUF_IN")
    s.dot(640, y); s.R((640, y), (640, y+120), "R_BIAS", "10 MΩ 1 %", side="l"); s.gnd(640, y+120)
    U = s.opamp(780, y, "U101A", "buffer", inp_top=True)
    s.wire((760, y), U["inp"])
    s.wire(U["inm"], (760, y+16), (760, y+80), (900, y+80), (900, y)); s.wire(U["out"], (920, y)); s.dot(900, y)
    s.port(920, y, "→ ganancia (sección C)", "r")
    s.frame(600, 330, 660, 110, "Polo B · lectura de posición (2 líneas con pull-up → 74HC165)")
    s.text(620, 370, "AC → 0 1     DC → 1 0     GND → 1 1", "pin")
    s.text(620, 392, "el firmware necesita saber el acoplo o la pantalla miente", "pin")
    s.text(620, 414, "pines del símbolo: confirmar cuál es el común antes de rutar", "pin")
    return s.svg()
