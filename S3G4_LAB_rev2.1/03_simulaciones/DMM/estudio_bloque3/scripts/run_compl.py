# -*- coding: utf-8 -*-
"""Compliancia simulada: tension maxima en el borne con la corriente a >= 99 % de la nominal (rail 4.8 V, Vth BSS84 -2.0 V)."""
import gen_p43 as g
def i_en(rk, rs, r1, rx, rail=4.8, iny="N2"):
    t=g.deck("cmp","MOS",rk,rx,rs=rs,r1=r1,vto=-2.0,rail=rail,comp="Cc og sni 1n",rsn=1e3,inyec=iny)
    o=g.op("cmp",t); vb=o["V(bor)"]; return vb/rx+vb/10.01e6, vb
out=[]
for lab,rk,rs,r1,i0,iny in (("c1 (1.53 kΩ) 1 mA",499,0,1530,1.004e-3,"N1"),("c1 (1.53 kΩ) 100 µA",4990,0,1530,100.4e-6,"N1"),):
    ref,_=i_en(rk,rs,r1,1.0,iny=iny)           # corriente con carga pequeña (como referencia)
    lo,hi=100.0,2e6
    for _ in range(10):
        mid=(lo*hi)**0.5; i,vb=i_en(rk,rs,r1,mid,iny=iny)
        if i>=0.99*ref: lo=mid
        else: hi=mid
    i,vb=i_en(rk,rs,r1,lo,iny=iny)
    out.append(f"{lab}: I_ref {ref*1e6:.4g} µA; 99 % hasta Rx = {lo:.4g} Ω, V_bor = {vb:.3f} V")
print("\n".join(out)); open("../resultados/compliancia_spice_c.txt","w",encoding="utf8").write("\n".join(out)+"\n")
