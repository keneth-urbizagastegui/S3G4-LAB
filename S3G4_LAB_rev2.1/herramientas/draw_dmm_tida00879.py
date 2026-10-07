# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del TIDA-00879, a partir de la hoja 3 (AFE Block) de
research_and_tests/TIDA-00879/tidrmi4.pdf. Valores y referencias tal cual el esquematico y la BOM."""
from sch import Sch
import calc_dmm_tida00879 as K


def tension():
    s = Sch(1400, 600, "TIDA-00879: entrada de tension con patas conmutadas y dos trimmers")
    p = s.banana(70, 130, "J8 negro", "#1b2a2e")
    s.wire(p, (120, 130)); s.dot(120, 130)
    s.wire((120, 130), (120, 80), (160, 80)); s.R((160, 80), (280, 80), "R19", "10.0 MΩ · CRHV1206")
    s.wire((280, 80), (330, 80))
    s.wire((170, 80), (170, 40), (210, 40)); s.C((210, 40), (250, 40), "C27 · 100 pF", "")
    s.wire((250, 40), (300, 40), (300, 80)); s.dot(170, 80); s.dot(300, 80)
    s.wire((120, 130), (120, 190), (160, 190)); s.R((160, 190), (280, 190), "R20", "499 kΩ", side="b")
    s.wire((280, 190), (330, 190))
    s.wire((170, 190), (170, 246), (210, 246)); s.C((210, 246), (250, 246), "C30 · 100 pF", "", side="b")
    s.wire((250, 246), (300, 246), (300, 190)); s.dot(170, 190); s.dot(300, 190)
    J7 = s.spdt(420, 130, "J7 (puente)", "", "", pos="a", span=26, dx=44, flip=True)
    s.wire((330, 80), (350, 80), (350, 104), J7["a"])
    s.wire((330, 190), (350, 190), (350, 156), J7["b"])
    s.note(160, 300, "J7: 499 kΩ solo para 60 mV")
    s.wire(J7["com"], (1260, 130)); s.net(480, 130, "toma (±54.5 mV a fondo)", dy=-8)
    s.port(1260, 130, "V− → U4 OPA333", "r")
    patas = [(470, "R10+R14", "9.10 kΩ", "C41/C42/C23", "110 nF", False, "60 V · ÷1100"),
             (680, "R11+R15", "91.8 kΩ", "C43+C44", "10.9 nF", False, "6 V · ÷110"),
             (890, "R12+R16", "1.01 MΩ", "C38+C25 + C33", "980 pF + 4.5–20 pF", True, "600 mV · ÷11")]
    for x, rn, rv, cn, cv, trim, rng in patas:
        s.dot(x, 130); s.R((x, 130), (x, 250), rn, rv, side="l")
        s.wire((x, 140), (x + 44, 140)); s.dot(x, 140)
        s.C((x + 44, 140), (x + 44, 250), cn, cv, side="r", trim=trim)
        s.wire((x, 250), (x + 44, 250)); s.dot(x, 250)
        s.wire((x, 250), (x, 330))
        s.note(x + 8, 294, rng)
    U5 = s.box(420, 342, 520, 56, "", "", pins=(("t", 50, "NO2", "a"), ("t", 260, "NO1", "b"), ("t", 470, "NO0", "c"), ("b", 260, "COM", "o")))
    s.text(680, 376, "U5 · TS5A3359 (SP3T, ≈1 Ω, a AVCC 2.4 V)", "ref", "middle")
    s.wire(U5["o"], (680, 470))
    s.dot(1140, 130); s.R((1140, 130), (1140, 250), "R13", "100 MΩ", side="l")
    s.wire((1140, 140), (1184, 140)); s.dot(1140, 140)
    s.C((1184, 140), (1184, 250), "C34", "4.5–20 pF", side="r", trim=True)
    s.wire((1140, 250), (1184, 250)); s.dot(1140, 250)
    s.wire((1140, 250), (1140, 470))
    s.wire((380, 470), (1140, 470)); s.dot(680, 470)
    s.port(380, 470, "J6 rojo = referencia V+", "l")
    s.note(20, 540, f"Todas las patas cierran 1 ms como R19 ∥ C27. Los trimmers ajustan las dos patas de alta impedancia (C34 ideal ≈ {K.C34_IDEAL*1e12:.0f} pF).")
    s.note(20, 560, "La referencia (borne rojo) la fija U3, un OPA333 que sigue AVCC/2 = 1.2 V, a través de R7 de 4.7 Ω. No hay protección en la entrada.")
    return s.svg()


def corriente():
    s = Sch(1300, 440, "TIDA-00879: entrada de corriente con fuerza y sentido")
    p = s.banana(70, 330, "J9 azul", "#12667f")
    s.wire(p, (300, 330)); s.dot(300, 330); s.net(306, 330, "B", dy=16)
    s.R((300, 330), (300, 210), "R22", "95.3 Ω · 1 W", side="l"); s.dot(300, 210); s.net(306, 210, "A", dy=16)
    s.R((300, 210), (300, 110), "R23", "0.5 Ω", side="l"); s.dot(300, 110)
    s.wire((300, 110), (300, 90)); s.PTC((300, 90), (300, 30), "F1", "PTC 0.2 A", side="l")
    s.wire((300, 30), (300, 20), (560, 20)); s.port(560, 20, "J6 rojo (referencia)", "r")
    s.wire((300, 110), (1000, 110)); s.port(1000, 110, "I+ → SD1P0", "r")
    B1 = s.spdt(560, 250, "U13 sección 2 (puente)", "A", "", pos="a", span=26, dx=50, flip=True)
    s.wire((300, 330), (620, 330), (620, 250), B1["com"])
    s.wire(B1["a"], (470, 224), (470, 210), (300, 210))
    s.note(640, 254, "60 mA: une B con A y la corriente evita R22")
    B2 = s.spdt(560, 390, "U13 sección 1 (sentido)", "A (60 mA)", "B (600 µA)", pos="a", span=26, dx=50, flip=True)
    s.wire(B2["a"], (420, 364), (420, 210)); s.dot(420, 210)
    s.wire(B2["b"], (380, 416), (380, 330)); s.dot(380, 330)
    s.wire(B2["com"], (800, 390)); s.port(800, 390, "U10 OPA333 → I− (SD1N0)", "r")
    s.note(640, 160, f"600 µA → {K.corr['600 µA']['V']*1e3:.1f} mV en R22+R23 · 60 mA → {K.corr['60 mA']['V']*1e3:.0f} mV en R23")
    s.note(640, 180, "La PTC queda fuera de la medida: I+ se toma encima de R23.")
    return s.svg()


if __name__ == "__main__":
    for f in (tension, corriente):
        print(f.__name__, len(f()))
