# -*- coding: utf-8 -*-
"""Redibujo propio (simplificado) del canal analogico 1 del OpenScope MZ (hoja 4 de openscope-mz-sch-revg.pdf)."""
from sch import Sch

def afe():
    s = Sch(1300, 650, "OpenScope MZ - canal analogico 1")
    y = 360
    s.port(20, y, "AIN1 · ±20 V", "r"); s.wire((117, y), (150, y))
    s.R((150, y), (270, y), "R31", "1 MΩ")
    s.wire((270, y), (320, y)); s.dot(300, y)
    A = s.opamp(330, 376, "IC5A", "LMV116 · ±5 V", inp_top=False)
    s.wire(A["inp"], (310, 392), (310, 420)); s.gnd(310, 420)
    s.wire((300, y), (300, 290)); s.dot(300, 290)
    s.R((300, 290), (440, 290), "R30", "200 kΩ")
    s.wire((300, 290), (300, 240)); s.wire((440, 290), (440, 240))
    s.C((300, 240), (440, 240), "C27", "0.3 pF")
    s.dot(440, 290); s.wire((440, 290), (440, 376))
    s.wire(A["out"], (440, 376)); s.dot(440, 376)
    s.R((440, 376), (560, 376), "R32", "3.6 kΩ")
    s.wire((440, 376), (440, 440)); s.wire((560, 376), (560, 440))
    s.C((440, 440), (560, 440), "C28", "33 pF", side="b")
    s.dot(560, 376); s.wire((560, 376), (690, 376)); s.dot(600, 376)
    s.net(606, 376, "S", dy=-6)
    # inyecciones en el nodo suma
    s.port(330, 520, "VREF3V0", "r"); s.wire((394, 520), (470, 520))
    s.R((470, 520), (580, 520), "R33+R34", "3.41 kΩ", side="b")
    s.port(200, 590, "offset · PWM OC8 filtrado", "r"); s.wire((389, 590), (470, 590))
    s.R((470, 590), (580, 590), "R2Sx", "10 k / 2.4 k / 1.37 k / 1.02 k", side="b")
    s.wire((580, 520), (600, 520)); s.wire((580, 590), (600, 590)); s.wire((600, 590), (600, 376)); s.dot(600, 520)
    # etapa suma
    B = s.opamp(700, 392, "IC6A", "LMV116 · 3.3 V", inp_top=False)
    s.wire(B["inp"], (680, 408), (680, 470)); s.port(680, 470, "VREF1V5", "r")
    # realimentacion conmutada
    s.wire((600, 376), (600, 205))
    F = s.box(620, 150, 180, 110, "IC4 · TS3A5017 + ramas R∥C", "", pins=(("l", 55, "", "s"), ("r", 55, "", "o")))
    s.wire((600, 205), F["s"])
    for i, t in enumerate(("18 kΩ → ×1", "4.53 kΩ ∥ 22 pF → ×1/4", "2.26 kΩ ∥ 51 pF → ×1/8", "1.33 kΩ ∥ 91 pF → ×3/40")):
        s.text(630, 176 + 20 * i, t, "pin")
    s.wire(F["o"], (840, 205), (840, 392))
    s.wire(B["out"], (860, 392)); s.dot(840, 392)
    s.R((860, 392), (960, 392), "R35", "68 Ω")
    s.dot(980, 392); s.wire((960, 392), (1010, 392))
    s.C((980, 392), (980, 470), "C31", "470 pF", side="l"); s.gnd(980, 470)
    s.port(1010, 392, "AN0 + AN1 · 0–3 V", "r")
    s.note(1290, 60, "La entrada nunca ve la tensión de la BNC: R31 entra a una tierra virtual.", "end")
    s.note(1290, 78, "IC5A invierte y divide ×0.2; IC6A invierte otra vez y elige la ganancia.", "end")
    s.note(1290, 96, "El conmutador trabaja a 1.5 V fijos (la tierra virtual de IC6A): sin distorsión.", "end")
    s.note(1290, 130, "IC6A se alimenta a 3.3 V, como el ADC: no puede sacar una tensión que lo dañe.", "end")
    s.note(1290, 148, "La otra mitad del TS3A5017 elige R2Sx: el offset escala con la ganancia.", "end")
    s.note(1290, 166, "Los condensadores de cada rama limitan la banda a 1.3–1.6 MHz: filtro anti-alias.", "end")
    return s.svg()
