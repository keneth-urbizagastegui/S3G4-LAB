# -*- coding: utf-8 -*-
"""Diagrama de bloques de la arquitectura recomendada del DMM tras la sintesis de las 9 referencias (7 oct 2026).
Es una propuesta: no esta aplicada a la seccion H hasta que Keneth decida."""
from sch import Sch


def bloque(s, x, y, w, h, titulo, l1="", l2="", cls="blk"):
    s.rect(x, y, w, h, cls, 4)
    s.text(x + w / 2, y + 20, titulo, "ref", "middle")
    if l1: s.text(x + w / 2, y + 38, l1, "pin", "middle")
    if l2: s.text(x + w / 2, y + 53, l2, "pin", "middle")


def bloques():
    s = Sch(1220, 640, "DMM rev 2.1: arquitectura recomendada tras la sintesis")
    # fila de tension
    s.banana(70, 100, "V/Ω", "#b3261e"); s.wire((79, 100), (110, 100)); s.dot(95, 100)
    bloque(s, 110, 70, 160, 62, "Protección", "R_PROT 3 × 33 kΩ", "BAV199 a ±4.9 V")
    bloque(s, 300, 70, 170, 62, "Divisor 10 MΩ", "3 × 3 MΩ + 900 k + 100 k", "tomas ÷10 (sujeta) y ÷100")
    bloque(s, 500, 70, 150, 62, "Mux de señal", "74HC4051 · X0…X7", "X3 = COM (autocero)")
    bloque(s, 680, 70, 130, 62, "A · OPA2188", "×1 / ×10", "deriva cero")
    bloque(s, 840, 70, 150, 62, "Driver diferencial", "3.3 V · VCM 1.25 V", "filtro de muestreo (P20)")
    bloque(s, 1020, 70, 150, 62, "ADC5 del G473", "diferencial ±2 V", "×1024 y NPLC")
    bloque(s, 1020, 160, 150, 64, "ΣΔ opcional", "ADS1115 · huella", "sin montar", cls="grp")
    s.wire((270, 100), (300, 100)); s.wire((470, 100), (500, 100)); s.wire((650, 100), (680, 100))
    s.wire((810, 100), (840, 100)); s.wire((990, 100), (1020, 100))
    s.dot(1005, 100); s.wire((1005, 100), (1005, 192), (1020, 192))
    # fila de ohmios
    bloque(s, 500, 232, 150, 62, "Fuente de ohmios", "4.9 V · R_ref 301 Ω…10 MΩ", "4051 fuerza / sentido")
    bloque(s, 300, 232, 170, 62, "Bloqueo (P42)", "1N4007W + 2 × MMBTA92", "en lugar de la PTC")
    s.wire((500, 263), (470, 263)); s.wire((300, 263), (95, 263), (95, 100))
    s.wire((575, 232), (575, 132)); s.net(581, 190, "X5, X6", dy=0)
    s.note(110, 290, "V_x se lee en el borne por X0")
    # continuidad
    bloque(s, 680, 232, 130, 62, "Continuidad", "÷2 → PB14 · COMP7", "umbral DAC2 · < 1 ms")
    s.wire((745, 132), (745, 232))
    # fila de corriente
    s.banana(70, 400, "A", "#b3261e"); s.wire((79, 400), (110, 400))
    bloque(s, 110, 370, 160, 62, "Fusible HRC 3.15 A", "cerámico (P31)", "+ puente DF10S")
    bloque(s, 300, 370, 170, 62, "Derivador 0.1 Ω", "4 terminales (P27)", "estrella en el borne COM")
    bloque(s, 500, 370, 150, 62, "B · OPA2188", "×10 del derivador", "→ X4 del mux")
    s.wire((270, 400), (300, 400)); s.wire((470, 400), (500, 400))
    s.wire((650, 400), (665, 400), (665, 120), (650, 120))
    s.banana(70, 480, "COM", "#1b2a2e"); s.wire((79, 480), (385, 480), (385, 432))
    # firmware
    s.frame(840, 240, 330, 250, "Firmware del G473 (sin piezas)")
    for i, t in enumerate(["autocero X3 con asiento de ≈ 1 ms (P38)", "integración: 60 Hz o 100 ms (P40)",
                           "valor eficaz y corrección de alterna (P21, P39)", "calibración multipunto y linealización (P26)",
                           "constantes en memoria, editables (P29)", "autoprueba al encender (P41)",
                           "cable abierto en tensión (P33)", "tensión externa en ohmios (P34)"]):
        s.note(856, 280 + i * 25, t)
    s.note(40, 560, "Discontinuo: huella opcional, sin montar, por si la linealización del ADC5 no basta (P36).")
    s.note(40, 580, "Cambios frente a la sección H: P42 en vez de la PTC, ningún divisor en el lado del DUT (P25), filtro P20,")
    s.note(40, 600, "fusible HRC con puente (P31), derivador Kelvin (P27), huella del ΣΔ y las funciones de firmware de la derecha.")
    return s.svg()


if __name__ == "__main__":
    print(len(bloques()))
