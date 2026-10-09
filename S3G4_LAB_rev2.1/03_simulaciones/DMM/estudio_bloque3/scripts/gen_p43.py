# -*- coding: utf-8 -*-
"""Genera y lanza decks LTspice de la fuente P43 (TLV2372 + NPN de referencia + BSS84 o PNP de paso).
Salidas en C:/b3/work y copia de los decks en ../decks_ltspice."""
import os, subprocess, sys, shutil, itertools, json
from concurrent.futures import ThreadPoolExecutor
ROOT = r"C:\Users\Keneth\Desktop\S3G4 LAB"
TLV = ROOT + r"\Simulation_LTSpice\models\TLV2372\TLV2372.LIB"
LT = r"C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
WORK = r"C:\b3\work"; DECKS = os.path.join(os.path.dirname(__file__), "..", "decks_ltspice")
os.makedirs(WORK, exist_ok=True); os.makedirs(DECKS, exist_ok=True)

HEAD = f'''* Estudio bloque 3 - fuente de corriente P43 ({{TIPO}})
.include "{TLV}"
.model NPNREF NPN(IS=1e-14 BF=200 VAF=100 CJE=8p CJC=4p TF=0.4n)
.model PNPPAS PNP(IS=1e-14 BF={{BETA}} VAF=100 CJE=8p CJC=4p TF=0.4n XTB=1.5 ISE=1e-16 NE=1.5 IKF=0.05)
.model BSS84 VDMOS(pchan Rg=3 Vto={{VTO}} Rd=2.4 Rs=1.8 Rb=3 Kp=.2 Cgdmax=.04n Cgdmin=.001n Cgs=.02n Cjo=.01n Is=2p ksubthres=.1)
.model BAT54 D(Is=.1u Rs=2.2 N=1 Cjo=12p M=.3 Eg=.69 Xti=2)
Vp vp 0 {{RAIL}}
Vn vn 0 -{{RAIL}}
Vref ref 0 2.5
* etapa 1: V_set = VREF*R2/R1 bajo el riel
XU1 ref e1 vp vn o1 TLV2372
Rb1 o1 b1 10k
Q1 cn b1 e1 NPNREF
R1 e1 0 24.9k
R2 vp cn 4.99k
* etapa 2: amplificador B + elemento de paso. R_k entre riel y S; 4051 de fuerza (Ron 110, Cz 25p) entre S y F; sentido por 4051 (Ron 110, Cz 25p + Cin 8p)
Rk vp s {{RK}}
Rf s f 110
Cz f 0 25p
Cy s 0 5p
Rsn s sno {{RSN}}
Vsn sno sni 0
Cs sni 0 33p
Ct sni 0 0
XU2 cn sni vp vn ogi TLV2372
Vinj ogi og 0 AC 1
{{COMP}}
'''
PASO_MOS = '''Rg og gate 1k
M1 d gate f f BSS84
'''
PASO_PNP = '''Rg og base 1k
Q2 d base f PNPPAS
'''
CARGA = '''* cadena de bloque 1: BAT54, R_S, TVS (200 pF) en N1, R1, borne con 25 pF, Rx y divisor
Dblk d n2 BAT54
Rs n2 n1 {RS}
Ctvs n1 0 {CTVS}
R1c n1 bor {R1}
Cbor bor 0 25p
Rx bor 0 {RX}
Rdiv bor 0 10.01Meg
'''
CARGA_N1 = '''* opcion c: el BAT54 inyecta en N1 (nodo de la TVS); R_S y las sujeciones quedan como rama de falta (no se modelan)
Dblk d n1 BAT54
Ctvs n1 0 {CTVS}
R1c n1 bor {R1}
Cbor bor 0 25p
Rx bor 0 {RX}
Rdiv bor 0 10.01Meg
'''
def deck(nombre, tipo, rk, rx, rs=2.7e3, r1=2.2e3, beta=150, vto=-2.0, rail=4.8, comp="", ctvs="200p", extra="", rsn=110, inyec="N2"):
    t = HEAD.replace("{TIPO}", tipo).replace("{BETA}", str(beta)).replace("{VTO}", str(vto)).replace("{RAIL}", str(rail)).replace("{RK}", str(rk)).replace("{COMP}", comp).replace("{RSN}", str(rsn))
    t += (PASO_MOS if tipo.startswith("MOS") else PASO_PNP)
    t += (CARGA_N1 if inyec == "N1" else CARGA).replace("{RS}", str(rs)).replace("{R1}", str(r1)).replace("{RX}", str(rx)).replace("{CTVS}", ctvs)
    t += extra
    return t

def run(nombre, texto):
    p = os.path.join(WORK, nombre + ".cir"); open(p, "w", encoding="utf8").write(texto)
    shutil.copy(p, os.path.join(DECKS, nombre + ".cir"))
    r = subprocess.run([LT, "-b", p], capture_output=True, text=True, timeout=900)
    return nombre

if __name__ == "__main__":
    pass

import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
import rawlt
def leer(nombre):
    n, d = rawlt.read(os.path.join(WORK, nombre + ".raw")); return d
def op(nombre, texto):
    run(nombre, texto + ".op\n.end\n"); d = leer(nombre)
    return {k: float(np.real(v[0])) for k, v in d.items()}
def pm(nombre, texto):
    run(nombre, texto + ".ac dec 60 10 200Meg\n.end\n"); d = leer(nombre)
    f = np.real(d["frequency"]); T = -d["V(ogi)"] / d["V(og)"]
    mag = np.abs(T); ph = np.degrees(np.unwrap(np.angle(T)))
    idx = np.where(mag < 1)[0]
    if len(idx) == 0: return dict(fc=None, pm=None, dc=20*np.log10(mag[0]))
    k = idx[0]
    # interpolacion log
    f1, f2 = f[k-1], f[k]; m1, m2 = np.log10(mag[k-1]), np.log10(mag[k])
    a = (0 - m1) / (m2 - m1); fc = 10 ** (np.log10(f1) + a * (np.log10(f2) - np.log10(f1)))
    p = ph[k-1] + a * (ph[k] - ph[k-1])
    return dict(fc=fc, pm=180 + p, dc=20*np.log10(mag[0]))
