# -*- coding: utf-8 -*-
"""PNP de paso (BF=150, XTB=1.5, ISE/NE para que beta caiga a baja corriente) frente al BSS84: corriente en Rx y su deriva con 18/23/28 C."""
import gen_p43 as g, numpy as np
rk = {"1mA":499,"100uA":4990,"10uA":49900,"1uA":499e3,"0.2uA":2.499e6}
rxfs = {"1mA":2000,"100uA":20e3,"10uA":200e3,"1uA":2e6,"0.2uA":20e6}
out=["| rango | PNP: I a 23 °C | deriva 18→28 °C (ppm) | MOS: I a 23 °C | deriva (ppm) |","|---|---|---|---|---|"]
for k in rk:
    row=[]
    for tipo in ("PNP","MOS"):
        iv=[]
        for T in (18,23,28):
            nm=f"pnp_{tipo}_{k}_{T}"
            t=g.deck(nm,tipo,rk[k],rxfs[k],rs=510,r1=990,beta=150,vto=-2.0,comp="Cc og sni 1n",rsn=1e3)
            t=t.replace("Vref ref 0 2.5",f"Vref ref 0 2.5\n.temp {T}")
            o=g.op(nm,t); vb=o["V(bor)"]; iv.append(vb/rxfs[k]+vb/10.01e6)
        row.append((iv[1],(iv[2]-iv[0])/iv[1]*1e6))
    out.append(f"| {k} | {row[0][0]*1e6:.5g} µA | {row[0][1]:+.0f} | {row[1][0]*1e6:.5g} µA | {row[1][1]:+.0f} |")
print("\n".join(out)); open("../resultados/pnp_frente_a_mos.txt","w",encoding="utf8").write("\n".join(out)+"\n")
