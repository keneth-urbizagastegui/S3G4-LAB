# -*- coding: utf-8 -*-
"""Redibujos propios (simplificados) del Micro-DMM, a partir de las netlists exportadas con kicad-cli:
puente del voltimetro de SimplifiedOpenLeadVoltmeter (igual que DMM Feather Redux, con otras resistencias de entrada)
y ohmimetro de DMM_KiCAD_V4_next. Se omiten el aislamiento (opto/ISO1540) y los drivers IX4426."""
from sch import Sch
import calc_dmm_microdmm as K


def sw(s, p1, p2, name, val="", side="r"):
    """Interruptor (MOSFET usado como tal), dibujado abierto."""
    mx, my, ang, h = s._two(p1, p2, 30)
    s.add(f'<g transform="translate({mx},{my}) rotate({ang})"><circle class="ct" cx="-15" cy="0" r="2.6"/>'
          '<circle class="ct" cx="15" cy="0" r="2.6"/><line class="blade" x1="-15" y1="0" x2="13" y2="-9"/></g>')
    s._labels(mx, my, h, name, val, side)


def puente():
    S = K.PLACAS["SimplifiedOpenLeadVoltmeter"]
    s = Sch(1320, 580, "Micro-DMM: puente de Mann del voltimetro (valores del SimplifiedOpenLeadVoltmeter)")
    p = s.banana(100, 120, "Float", "#b3261e")
    s.wire(p, (130, 120)); s.R((130, 120), (290, 120), "R17", "499 kΩ")
    s.wire((290, 120), (1060, 120))
    q = s.banana(100, 360, "REF", "#1b2a2e")
    s.wire(q, (130, 360)); s.R((130, 360), (290, 360), "R18", "499 kΩ")
    s.wire((290, 360), (1060, 360))
    s.net(300, 120, "AIN1 (lado que varía)", dy=-8); s.net(300, 360, "AIN0 (lado fijo, 2.5 V)", dy=-8)
    # brazos del puente
    s.dot(520, 120); s.dot(520, 360)
    s.R((520, 120), (520, 360), "R14", "1 MΩ fijo", side="l")
    s.dot(660, 120); s.dot(660, 360)
    sw(s, (660, 120), (660, 220), "Q8 · AO3400A", "lo abre la prueba", side="r")
    s.R((660, 220), (660, 360), "R24", "15 kΩ", side="r")
    # sujeciones en AIN1
    s.dot(800, 120); s.D((800, 120), (800, 70), "D4", "", side="l", kind="s"); s.rail(800, 70, "5V-iso")
    s.dot(880, 120); s.D((880, 230), (880, 120), "D5", "Schottky", side="r", kind="s"); s.gnd(880, 230, "Gnd-iso")
    # referencia en AIN0
    s.dot(820, 360); s.D((820, 450), (820, 360), "U10", "LM4040-2.5", side="l", kind="z"); s.gnd(820, 450)
    s.dot(940, 360); s.R((940, 360), (940, 280), "R27", "4.7 kΩ", side="r"); s.rail(940, 280, "5V-iso")
    s.dot(1010, 360); s.C((1010, 360), (1010, 440), "C17", "0.1 µF", side="r"); s.gnd(1010, 440)
    s.box(1072, 90, 150, 300, "U3 · ADS1115", "16 bits · AIN0 − AIN1",
          pins=(("l", 30, "AIN1", "a1"), ("l", 270, "AIN0", "a0")))
    s.text(1147, 246, "diferencial", "pin", "middle")
    s.note(40, 500, f"Medida: Q8 conduce y el puente vale 15 kΩ ∥ 1 MΩ → escala ÷{S['k_on']:.1f}; el firmware usa 69.95, "
                    f"que es lo que sale con la Z diferencial del ADS a ±0.256/0.512 V (710 kΩ).")
    s.note(40, 518, "Prueba (lectura ≈ 0 V): Q8 se abre y AIN1 solo queda unido a AIN0 por R14 y por las puntas (998 kΩ + lo que haya entre ellas).")
    s.note(40, 536, f"Lo que tira de AIN1 hacia abajo no está en el esquema: según los umbrales del firmware, ≈ {K.R_PD_CERR/1e3:.0f} kΩ "
                    "(fuga de D5 y entrada del ADS; NO VERIFICADO).")
    s.note(40, 554, "En la DMM_KiCAD_V4_next los valores están al revés (R14 = 15 kΩ fijo, R24 = 1 MΩ conmutado): al abrir Q8 el puente no se rompe.")
    return s.svg()


def ohmios():
    s = Sch(1320, 480, "Micro-DMM V4_next: fuente de ohmios de 20 mA y divisor de 22 kOhm")
    s.port(40, 120, "IX4426 · OUT_B (9 V conmutados)", "r")
    B = s.box(300, 96, 100, 48, "U1 · LM317", "", pins=(("l", 24, "VI", "vi"), ("r", 24, "VO", "vo"), ("b", 50, "ADJ", "adj")))
    s.wire((262, 120), B["vi"])
    s.R(B["vo"], (560, 120), "R5", "62 Ω")
    s.wire((560, 120), (640, 120)); s.dot(600, 120)
    s.wire(B["adj"], (350, 230), (900, 230)); s.wire((600, 120), (600, 230)); s.dot(600, 230)
    s.net(360, 230, "R Circuit I Output", dy=-6)
    s.dot(700, 230); s.R((700, 230), (700, 330), "R6", "330 Ω purga", side="r"); s.gnd(700, 330)
    s.dot(800, 230); s.D((800, 330), (800, 230), "U11", "LM4040-5", side="r", kind="z"); s.gnd(800, 330)
    s.C((900, 230), (900, 330), "C18", "1 µF", side="r"); s.gnd(900, 330)
    # divisor y conmutador de rango
    s.R((640, 120), (800, 120), "R9", "22 kΩ")
    s.dot(620, 120); s.wire((620, 120), (620, 60), (660, 60))
    sw(s, (660, 60), (780, 60), "Q2 · AO3400A", "rango bajo: puentea R9")
    s.wire((780, 60), (820, 60), (820, 120)); s.dot(820, 120)
    s.wire((800, 120), (1080, 120)); s.dot(950, 120); s.dot(1000, 120)
    s.C((950, 120), (950, 200), "C3", "2.2 µF", side="r"); s.gnd(950, 200)
    s.wire((1000, 120), (1000, 180), (1040, 180)); s.port(1040, 180, "AIN2 del ADS1115 (R21, 0 Ω)", "r")
    s.port(1080, 120, "J14 centro: punta Ω", "r")
    s.net(830, 120, "Resistor_Input", dy=-8)
    s.wire((1010, 300), (1030, 300)); s.FUSE((1030, 300), (1110, 300), "F1", "1206", side="b"); s.wire((1110, 300), (1130, 300))
    s.port(1130, 300, "J14 funda: punta COM", "r"); s.gnd(1010, 300)
    s.note(40, 392, f"Rango bajo (Q2 conduce): el LM317 fija 1.25 V / 62 Ω = {K.I_FUENTE*1e3:.1f} mA y la purga R6 se lleva su parte → R = V / (I − V/330).")
    s.note(40, 410, f"Rango alto (Q2 abierto): el nodo queda sujeto a 5.0 V por U11 y la medida es un divisor con R9 → R = 22 kΩ · V / (5.0 − V).")
    s.note(40, 428, f"Cambio de rango en {K.UMBRAL_RANGO:.0f} Ω ± 5 %. La tensión se lee en el borne respecto a Gnd-iso: puntas, fusible y contactos se restan con el nulo.")
    s.note(40, 446, "Sin protección ante tensión externa: Q2 y U11 conducen (el manual avisa de que el MOSFET se quema).")
    return s.svg()


if __name__ == "__main__":
    for f in (puente, ohmios):
        print(f.__name__, len(f()))
