# -*- coding: utf-8 -*-
"""Regulacion de carga y de rieles de la fuente P43: corriente en el borne con Rx en cortocircuito, a fondo y cerca de la compliancia; rieles 4.8/4.9/5.0 V."""
import gen_p43 as g, numpy as np
rk = {"1mA":499,"100uA":4990,"10uA":49900,"1uA":499e3,"0.2uA":2.499e6}
ifs = {"1mA":1.004e-3,"100uA":100.4e-6,"10uA":10.04e-6,"1uA":1.004e-6,"0.2uA":0.2005e-6}
rxfs = {"1mA":2000,"100uA":20e3,"10uA":200e3,"1uA":2e6,"0.2uA":20e6}
out=[]
def corriente(k, rx, rail=4.8, vto=-2.0):
    nm=f"reg_{k}_{int(rx*100)}_{rail}".replace(".","p")
    t=g.deck(nm,"MOS",rk[k],rx,rs=510,r1=990,vto=vto,rail=rail,comp="Cc og sni 1n",rsn=1e3)
    o=g.op(nm,t); vb=o["V(bor)"]
    return vb/rx+vb/10.01e6 if rx>0 else None, vb, (o["V(vp)"]-o["V(s)"])/rk[k]
for k in rk:
    res=[]
    for lab,rx in (("corto",0.1),("fondo",rxfs[k]),("casi compliancia",(4.3 if k in ("1mA",) else 3.4)/ifs[k])):
        if lab=="casi compliancia":
            # carga resistiva que deja V_bor ~ compliancia-0.15 V (solo informativa)
            rx = min(rx, 1e9) if k!="1mA" else 3.3/1.004e-3
        i,vb,ik=corriente(k,rx)
        res.append((lab,rx,i,vb,ik))
    i0=res[0][2]
    out.append(f"{k}: " + "; ".join(f"{lab} (Rx {rx:.3g} Ω, V_bor {vb:.2f} V): I {i*1e6:.5g} µA ({(i/i0-1)*1e6:+.0f} ppm)" for lab,rx,i,vb,ik in res))
    # riel
    ir=[corriente(k,rxfs[k],rail=r)[0] for r in (4.8,4.9,5.0)]
    out.append(f"   rieles 4.8/4.9/5.0 V a fondo: " + ", ".join(f"{x*1e6:.5g}" for x in ir) + f" µA ({(ir[2]/ir[0]-1)*1e6:+.0f} ppm por 0.2 V)")
print("\n".join(out)); open("../resultados/regulacion.txt","w",encoding="utf8").write("\n".join(out)+"\n")
