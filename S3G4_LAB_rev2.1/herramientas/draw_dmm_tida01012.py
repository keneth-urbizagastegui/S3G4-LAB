# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del TIDA-01012, a partir de la hoja 3 (WirelessDMM_AFE) de
research_and_tests/TIDA-01012/tidrny5 (2).pdf. Valores y referencias tal cual el esquematico."""
from sch import Sch
import calc_dmm_tida01012 as K


def tension():
    s = Sch(1300, 560, "TIDA-01012: entrada de tension con patas conmutadas")
    # borne y selector V/A (S1, deslizante)
    p = s.banana(70, 130, "V/A", "#b3261e")
    s.wire(p, (96, 130))
    S1 = s.spdt(96, 130, "S1", "tensión", "corriente", pos="a", span=26, dx=44)
    s.wire(S1["b"], (140, 220), (160, 220)); s.port(160, 220, "CURR_IN", "r")
    s.wire(S1["a"], (200, 104)); s.dot(200, 104)
    # rama normal: R16 ∥ C22
    s.wire((200, 104), (200, 80), (230, 80)); s.R((230, 80), (330, 80), "R16", "10.0 MΩ")
    s.wire((330, 80), (360, 80))
    s.wire((240, 80), (240, 40), (280, 40)); s.C((280, 40), (320, 40), "C22 · 100 pF", "", side="")
    s.wire((320, 40), (350, 40), (350, 80)); s.dot(240, 80); s.dot(350, 80)
    # rama de 50 mV: R17 ∥ C23
    s.wire((200, 104), (200, 180), (230, 180)); s.R((230, 180), (330, 180), "R17", "499 kΩ", side="b")
    s.wire((330, 180), (360, 180))
    s.wire((240, 180), (240, 236), (280, 236)); s.C((280, 236), (320, 236), "C23 · 22 nF", "", side="b")
    s.wire((320, 236), (350, 236), (350, 180)); s.dot(240, 180); s.dot(350, 180)
    # S2 (deslizante, manual): elige la resistencia de entrada
    S2 = s.spdt(450, 130, "S2", "", "", pos="a", span=26, dx=44, flip=True)
    s.wire((360, 80), (380, 80), (380, 104), S2["a"])
    s.wire((360, 180), (380, 180), (380, 156), S2["b"])
    s.note(330, 300, "S2 manual: 499 kΩ solo en 50 mV")
    # toma IN_P
    s.wire(S2["com"], (1140, 130))
    s.net(560, 130, "IN_P (toma, ±50 mV)")
    s.port(1140, 130, "IN_P → U5A", "r")
    # patas: (x, nombre R, valor R, nombre C, valor C, pin, rango)
    patas = [(560, "R6+R10", "9.77 kΩ", "C10–C12", "102 nF", "NO2", "50 V · ÷1025"),
             (750, "R7+R11", "100 kΩ", "C13+C14", "10 nF", "NO1", "5 V · ÷101"),
             (940, "R8+R12", "1.01 MΩ", "C15–C17", "950 pF", "NO0", "500 mV · ÷11")]
    for x, rn, rv, cn, cv, pin, rng in patas:
        s.dot(x, 130); s.R((x, 130), (x, 250), rn, rv, side="l")
        s.wire((x, 140), (x + 44, 140)); s.dot(x, 140)
        s.C((x + 44, 140), (x + 44, 250), cn, cv, side="r")
        s.wire((x, 250), (x + 44, 250)); s.dot(x, 250)
        s.wire((x, 250), (x, 330))
        s.note(x + 8, 294, rng)
    # TS5A3359 (U4): SP3T a 2.7 V entre las patas y COM
    U4 = s.box(500, 342, 500, 60, "", "",
               pins=(("t", 60, "NO2", "n2"), ("t", 250, "NO1", "n1"), ("t", 440, "NO0", "n0"),
                     ("b", 250, "COM", "c")))
    s.text(640, 376, "U4 · TS5A3359 (SP3T, ≈1 Ω, a V2P7)", "ref", "middle")
    s.text(870, 376, "AFE_VRNG-SEL0/1: una pata o ninguna", "pin", "middle")
    s.wire(U4["c"], (750, 470))
    # R9 siempre
    s.dot(1080, 130); s.R((1080, 130), (1080, 330), "R9", "100 MΩ", side="r")
    s.wire((1080, 330), (1080, 470))
    s.note(1088, 360, "siempre; C18, C19 sin montar")
    # bus COM
    s.wire((500, 470), (1080, 470)); s.dot(750, 470)
    s.port(500, 470, "COM = IN_N = 1P35V_REF", "l")
    s.note(20, 520, f"Todas las patas cierran τ ≈ {K.TAU_IN*1e3:.1f} ms como R16 ∥ C22; la de 1 MΩ deja ≈ {K.CEQ_PATA_500mV*1e12:.0f} pF para el conmutador, el buffer y la placa.")
    s.note(20, 540, "La toma vale ±50 mV a fondo en todos los rangos: el conmutador nunca ve la tensión de entrada. No hay sujeción ni protección (guía, 2.4.1.1.2).")
    return s.svg()


def corriente():
    s = Sch(1300, 430, "TIDA-01012: entrada de corriente con fuerza y sentido")
    s.port(20, 90, "CURR_IN", "r")
    s.wire((83, 90), (130, 90)); s.PTC((130, 90), (250, 90), "F1", "PTC 0.2 A")
    s.wire((250, 90), (420, 90)); s.dot(300, 90); s.dot(420, 90)
    s.net(306, 90, "A")
    s.R((300, 90), (300, 210), "R20", "95.3 Ω", side="l"); s.dot(300, 210); s.net(306, 210, "B")
    s.R((300, 210), (300, 330), "R25", "0.5 Ω", side="l")
    s.wire((300, 330), (300, 360)); s.port(300, 360, "COM", "l")
    # seccion 1: puentea R20 en 50 mA
    B1 = s.spdt(560, 150, "U8 sección 1 (puente)", "B", "", pos="a", span=26, dx=50, flip=True)
    s.wire((420, 90), (660, 90), (660, 150), B1["com"])
    s.wire(B1["a"], (470, 124), (470, 210), (300, 210))
    s.note(680, 154, "50 mA: une A con B y la corriente evita R20; en 500 µA queda abierto")
    # seccion 2: elige el nodo que se mide (sin corriente)
    B2 = s.spdt(560, 290, "U8 sección 2 (sentido)", "B (50 mA)", "A (500 µA)", pos="a", span=26, dx=50, flip=True)
    s.wire(B2["a"], (420, 264), (420, 210))
    s.dot(420, 210)
    s.wire(B2["b"], (440, 316), (440, 90))
    s.dot(440, 90)
    s.wire(B2["com"], (760, 290))
    U25 = s.box(760, 260, 140, 60, "U25 · TS5A3166", "SPST, I-SEL", pins=(("r", 30, "", "o"),))
    s.wire((760, 290), (760, 290))
    s.wire(U25["o"], (1000, 290)); s.port(1000, 290, "IN_P", "r")
    s.note(560, 370, "Kelvin (TS3A24159): la resistencia del conmutador queda en el camino de la corriente,")
    s.note(560, 388, "no en el de la medida.")
    s.note(560, 412, f"500 µA → {K.corr['500 µA']['V']*1e3:.1f} mV en R20+R25 · 50 mA → {K.corr['50 mA']['V']*1e3:.0f} mV en R25 · en tensión, U25 abre.")
    return s.svg()


def cadena():
    s = Sch(1300, 470, "TIDA-01012: buffers, amplificador diferencial y ADC de 18 bits")
    s.port(20, 120, "IN_P", "r")
    A = s.opamp(150, 104, "U5A", "OPA2313 (seguidor)")
    s.wire((63, 120), A["inp"])
    s.wire(A["inm"], (130, 88), (130, 50), (240, 50), (240, 104)); s.dot(240, 104)
    s.port(20, 300, "IN_N = COM", "r")
    B = s.opamp(150, 284, "U5B", "OPA2313 (seguidor)")
    s.wire((103, 300), B["inp"])
    s.wire(B["inm"], (130, 268), (130, 230), (240, 230), (240, 284)); s.dot(240, 284)
    s.R(A["out"], (360, 104), "R4", "3.01 kΩ")
    s.R(B["out"], (360, 284), "R14", "3.01 kΩ", side="b")
    F = s.fda(470, 194, "U6 · THS4531", "")
    s.text(556, 250, f"G = {K.G_FDA:.1f}", "val")
    s.wire((360, 104), (440, 104), (440, 170), F["inp"]); s.dot(440, 104)
    s.wire((360, 284), (440, 284), (440, 218), F["inm"]); s.dot(440, 284)
    s.R((440, 104), (620, 104), "R19", "133 kΩ"); s.wire((620, 104), (640, 104), (640, 182), F["outn"])
    s.R((440, 284), (620, 284), "R23", "133 kΩ", side="b"); s.wire((620, 284), (640, 284), (640, 206), F["outp"])
    s.wire(F["vocm"], (500, 360)); s.net(506, 360, "VOCM = 1P35V_REF")
    s.wire((640, 182), (700, 182)); s.dot(640, 182); s.R((700, 182), (790, 182), "R5 · 52.3 Ω", "")
    s.wire((640, 206), (700, 206)); s.dot(640, 206); s.R((700, 206), (790, 206), "R15 · 52.3 Ω", "", side="b")
    s.wire((790, 182), (900, 182)); s.wire((790, 206), (900, 206))
    s.dot(830, 182); s.dot(830, 206)
    s.wire((830, 182), (830, 188)); s.wire((830, 200), (830, 206))
    s.C((830, 188), (830, 200), "", "")
    s.text(846, 160, "C20 2.2 nF", "val")
    s.text(846, 238, f"filtro {K.F_AA/1e3:.0f} kHz", "val")
    D = s.box(912, 150, 170, 90, "U1 · ADS8885", "18 bits, ≈210 kSa/s",
              pins=(("l", 32, "AINP", "p"), ("l", 56, "AINN", "n"), ("r", 70, "REF", "r")))
    s.wire((900, 182), D["p"]); s.wire((900, 206), D["n"])
    s.text(997, 218, "SPI → CC2640", "pin", "middle")
    # referencia
    R = s.box(760, 320, 150, 50, "U2 · REF3325 → U3 · OPA313", "", pins=(("r", 25, "", "o"),))
    s.text(835, 350, f"RC {K.F_REF:.1f} Hz · RISO 8.2 Ω", "pin", "middle")
    s.wire(R["o"], (1120, 345), (1120, 220), D["r"])
    s.note(1130, 300, "VREF 2.5 V, 22 µF")
    # VCM / COM
    V = s.box(470, 390, 200, 40, "U9 · OPA333 (seguidor)", "", pins=(("r", 20, "", "o"),))
    s.text(570, 415, f"VREF·13.3/24.6 = {K.V_CM:.3f} V", "pin", "middle")
    s.wire(V["o"], (720, 410)); s.net(724, 400, "→ 1 kΩ + 1 µF → 1P35V_REF = COM")
    s.note(20, 450, f"Una cuenta = {K.V_CUENTA_TOMA*1e6:.0f} µV en la toma = {K.V_CUENTA_ADC*1e6:.1f} µV en el ADC = {K.LSB_POR_CUENTA:.1f} LSB. "
                    f"32 K muestras por lectura → {K.LECTURAS_S:.1f} lecturas/s. Toda la cadena va a 2.7 V con una sola fuente.")
    return s.svg()


if __name__ == "__main__":
    for f in (tension, corriente, cadena):
        print(f.__name__, len(f()))
