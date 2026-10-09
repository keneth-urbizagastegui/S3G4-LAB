# -*- coding: utf-8 -*-
"""Esfuerzos de la cadena de ohmios (R1 -> TVS SMAJ12CA en N1 -> R_S -> sujeciones/zener en N2) con 60 V DC y 60 Vrms.
Modelo estatico: TVS lineal por tramos (VBR + Rd*I, Rd=(19.9-14.7)/20.1 de la hoja DS19005), sujecion de N2 a +-(5.6+0.65) V con 30 ohm."""
import math, numpy as np
VBR = {"min": 13.3, "max": 14.7}; RD = (19.9 - 14.7) / 20.1
VCL, RCL = 5.6 + 0.65, 30.0
def resolver(v, r1, rs, vbr):
    """Devuelve (i1, it, is_, vn1) para tension de entrada v (signo respetado)."""
    s = 1 if v >= 0 else -1; v = abs(v)
    # sin conduccion de TVS: N1 = v - i*r1; i = (N1-VCL)/(rs+RCL) si N1>VCL
    def n1_de(i1):
        pass
    # barrido por bisecccion en N1
    lo, hi = 0.0, v
    for _ in range(80):
        n1 = (lo + hi) / 2
        it = max(0.0, (n1 - vbr) / RD)                 # TVS conduce por encima de VBR
        is_ = max(0.0, (n1 - VCL) / (rs + RCL))
        i1 = (v - n1) / r1
        if i1 > it + is_: lo = n1
        else: hi = n1
    n1 = (lo + hi) / 2
    it = max(0.0, (n1 - vbr) / RD); is_ = max(0.0, (n1 - VCL) / (rs + RCL)); i1 = (v - n1) / r1
    return s * i1, s * it, s * is_, s * n1
def estres(r1, rs, modo, vbr="min", n1pcs=2):
    if modo == "DC":
        i1, it, is_, n1 = resolver(60.0, r1, rs, VBR[vbr])
        P = dict(R1_total=i1**2 * r1, R1_cada=i1**2 * r1 / n1pcs, TVS=abs(it * n1), RS=is_**2 * rs, ZENER=abs(is_) * 5.6, i1=i1, it=it, is_=is_, V_R1_cada=(60 - n1) / n1pcs)
    else:
        th = np.linspace(0, 2 * math.pi, 4000, endpoint=False); v = 60 * math.sqrt(2) * np.sin(th)
        res = [resolver(x, r1, rs, VBR[vbr]) for x in v]
        i1 = np.array([r[0] for r in res]); it = np.array([r[1] for r in res]); is_ = np.array([r[2] for r in res]); n1 = np.array([r[3] for r in res])
        P = dict(R1_total=np.mean(i1**2) * r1, R1_cada=np.mean(i1**2) * r1 / n1pcs, TVS=np.mean(np.abs(it * n1)), RS=np.mean(is_**2) * rs,
                 ZENER=np.mean(np.abs(is_)) * 5.6, i1=np.max(np.abs(i1)), it=np.max(np.abs(it)), is_=np.max(np.abs(is_)), V_R1_cada=np.max(np.abs(v - n1)) / n1pcs)
    return P
if __name__ == "__main__":
    import sys, io
    out = io.StringIO()
    def P(*a):
        s = " ".join(str(x) for x in a); print(s); out.write(s + "\n")
    P("| R1 (piezas) | R_S | R_serie | 60 V DC: I_R1 | R1 cada (W) | TVS (W) | R_S (W) | zéner (W) | 60 Vrms: R1 cada (W) | TVS (W) | R_S (W) | zéner (W) | V pico por R1 |")
    P("|---|---|---|---|---|---|---|---|---|---|---|---|---|")
    for lab, r1, n, rs in (("2 × 1.1 kΩ (hoy)", 2.2e3, 2, 2.7e3), ("2 × 1.1 kΩ + R_S 1.0 k", 2.2e3, 2, 1.0e3), ("2 × 750 Ω", 1.5e3, 2, 0.0),
                           ("2 × 560 Ω + 470 Ω", 1.12e3, 2, 470), ("2 × 510 Ω + 470 Ω", 1.02e3, 2, 470), ("3 × 330 Ω + 510 Ω", 0.99e3, 3, 510), ("2 × 510 Ω + 330 Ω", 1.02e3, 2, 330)):
        d = estres(r1, rs, "DC", "min", n); a = estres(r1, rs, "AC", "min", n)
        P(f"| {lab} | {rs:g} Ω | {(r1+rs)/1e3:.2f} kΩ | {d['i1']*1e3:.1f} mA | {d['R1_cada']:.2f} | {d['TVS']:.2f} | {d['RS']:.3f} | {d['ZENER']:.3f} | {a['R1_cada']:.2f} | {a['TVS']:.2f} | {a['RS']:.3f} | {a['ZENER']:.3f} | {a['V_R1_cada']:.0f} V |")
    open(sys.path[0] + "/../resultados/calc_prot.txt", "w", encoding="utf8").write(out.getvalue())
