# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del Open Source Multimeter de Martin, rev 1.5,
a partir de research_and_tests/Martin_STM32_multimeter/hardware/v15.sch (leido como XML) y sus PNG.
Se omiten el MCU, la generacion de VREF/2 (MCP1501 + 1 kΩ/1 kΩ + IC9A) y los condensadores de desacoplo."""
from sch import Sch
import calc_dmm_martin as K


def tension():
    s = Sch(1420, 640, "Martin rev 1.5: divisor de 1 MOhm, patas conmutadas a COM y COM a VREF/2")
    p = s.banana(90, 140, "V", "#b3261e")
    s.wire(p, (120, 140)); s.R((120, 140), (280, 140), "R12", "1 MΩ (C18 TBD)")
    s.wire((280, 140), (400, 140)); s.dot(330, 140)
    s.D((330, 140), (330, 80), "D4", "", side="l"); s.rail(330, 80, "3V")
    a7 = s.spdt(400, 140, "", "B", "A", pos="b")
    s.text(400, 196, "IC7", "ref", "middle")
    # toma (N$9) y patas; el camino directo (N$13) va por arriba
    s.wire(a7["b"], (980, 166)); s.dot(520, 166); s.dot(640, 166)
    s.net(700, 166, "toma", dy=14)
    s.R((520, 166), (520, 250), "R11", "150 kΩ", side="l")
    s.R((640, 166), (640, 250), "R13", "15 kΩ", side="r")
    s.note(656, 236, "C17, C20 (TBD) en paralelo")
    s.wire((640, 250), (640, 334), (716, 334))
    s.wire((520, 250), (520, 386), (716, 386))
    a3 = s.spdt(760, 360, "", "A: 15 kΩ", "B: 150 kΩ", pos="a", flip=True)
    s.text(760, 424, "IC3 (VSEL0)", "ref", "middle")
    s.wire(a3["com"], (860, 360)); s.dot(860, 360)
    # COM, P1 e IC2
    s.wire((860, 360), (860, 560), (99, 560))
    q = s.banana(90, 560, "COM", "#1b2a2e")
    s.net(560, 560, "COM", dy=-6)
    s.dot(860, 460); s.wire((860, 460), (930, 460))
    a2 = s.spdt(930, 460, "", "A: VREF/2 = 0.9 V", "B: AGND", pos="a")
    s.text(930, 516, "IC2 (OFSEL)", "ref", "middle")
    # camino directo (N$13); R14 (a AGND) va sin montar y no se dibuja
    s.wire(a7["a"], (980, 114))
    s.net(700, 114, "directo (R14 a AGND, sin montar)", dy=-6)
    a8 = s.spdt(1024, 140, "", "B", "A", pos="b", flip=True)
    s.text(1024, 196, "IC8", "ref", "middle")
    # buffer y SDADC
    A = s.opamp(1080, 156, "IC9B · MCP6072", "seguidor", inp_top=True)
    s.wire(a8["com"], (1060, 140), A["inp"])
    s.wire(A["inm"], (1060, 172), (1060, 220), (1170, 220), (1170, 156)); s.dot(1170, 156)
    s.wire(A["out"], (1218, 156))
    B = s.box(1230, 120, 160, 140, "SDADC2 · F373", "16 bits ΣΔ",
              pins=(("l", 36, "AIN8P", "p"), ("l", 106, "AIN8M", "m")))
    s.wire((1218, 226), (1200, 226)); s.net(1196, 226, "VREF/2", "end", dy=4)
    s.text(1310, 196, "±0.9 V", "pin", "middle")
    s.note(40, 600, f"60 V: IC7/IC8 en A, IC3 en A (÷{K.DIV['60 V']['k']:.1f}).  6 V: IC3 en B (÷{K.DIV['6 V']['k']:.2f}).  "
                    "600 mV y 60 mV: IC7/IC8 en B, directo (×8 en el SDADC para 60 mV).  C17, C18 y C20 son «TBD» en el esquema y el BOM.")
    s.note(40, 618, "COM vale VREF/2 para medir negativos con una sola alimentación de 3 V; IC2 lo baja a AGND en continuidad.")
    return s.svg()


def corriente():
    s = Sch(1320, 520, "Martin rev 1.5: derivadores en serie, toma elegida por IC4 e INA199")
    p = s.banana(90, 100, "A", "#b3261e")
    s.wire(p, (120, 100)); s.FUSE((120, 100), (240, 100), "F1", "2.5 A rápido")
    s.wire((240, 100), (400, 100)); s.dot(300, 100); s.dot(340, 100); s.dot(370, 100)
    s.D((300, 100), (300, 40), "D3", "", side="l"); s.rail(300, 40, "3V")
    s.D((340, 170), (340, 100), "D2", "", side="l"); s.gnd(340, 170)
    s.R((400, 100), (520, 100), "R10", "50 mΩ")
    s.wire((520, 100), (600, 100)); s.dot(560, 100)
    s.R((600, 100), (720, 100), "R9", "5 mΩ")
    s.wire((720, 100), (1040, 100), (1040, 460), (99, 460))
    s.banana(90, 460, "COM", "#1b2a2e")
    s.net(870, 100, "COM", dy=-6)
    # tomas hacia IC4
    s.wire((560, 100), (560, 234))
    s.wire((370, 100), (370, 286), (560, 286))
    a4 = s.spdt(604, 260, "", "A: R9", "B: R9 + R10", pos="a", flip=True)
    s.text(604, 316, "IC4 (ISEL)", "ref", "middle")
    B = s.box(700, 220, 130, 110, "IC5 · INA199", "",
              pins=(("l", 40, "IN+", "ip"), ("l", 80, "IN−", "im"), ("r", 40, "OUT", "o"), ("b", 65, "REF", "ref")))
    s.wire(a4["com"], B["ip"])
    s.wire(B["im"], (660, 300)); s.net(656, 300, "VREF/2", "end", dy=4)
    s.wire(B["ref"], (765, 370)); s.net(769, 372, "VREF/2", dy=4)
    s.port(860, 260, "ADCI → SDADC1 (PB0)", "r")
    s.wire(B["o"], (860, 260))
    s.dot(1040, 380); s.wire((1040, 380), (1110, 380))
    s.spdt(1110, 380, "", "A: VREF/2", "B: AGND", pos="a")
    s.text(1110, 436, "IC2 (OFSEL)", "ref", "middle")
    s.note(40, 494, f"La corriente pasa siempre por R10 + R9 (55 mΩ, {K.CAIDA_2A5*1e3:.0f} mV a 2.5 A sin el fusible); IC4 solo elige la toma que lee el INA199.")
    s.note(40, 512, "IN− va a la red VREF/2 y no al pie de R9: lo que circule por IC2 entre COM y VREF/2 se suma a la lectura de corriente.")
    return s.svg()


if __name__ == "__main__":
    for f in (tension, corriente):
        print(f.__name__, len(f()))
