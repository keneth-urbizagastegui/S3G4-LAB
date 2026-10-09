# -*- coding: utf-8 -*-
"""Margen de fase del lazo de la fuente (Rsn 1 kΩ + Cc 1 nF) en esquinas: Vth BSS84 -0.8/-2.0 V, Ron del 4051 60/130 Ω, capacidades x0.6/x1.5, riel 4.8/5.0 V, 5 rangos a fondo."""
import gen_p43 as g, itertools, sys
rk = {"1mA":499,"100uA":4990,"10uA":49900,"1uA":499e3,"0.2uA":2.499e6}
rxfs = {"1mA":2000,"100uA":20e3,"10uA":200e3,"1uA":2e6,"0.2uA":20e6}
res={}
for k in rk:
    peor=(999,None)
    for vto,ron,cs,rail in itertools.product((-0.8,-2.0),(60,130),(0.6,1.5),(4.8,5.0)):
        t=g.deck("pe",  "MOS",rk[k],rxfs[k],rs=510,r1=990,vto=vto,rail=rail,comp="Cc og sni 1n",rsn=1e3)
        t=t.replace("Rf s f 110",f"Rf s f {ron}").replace("Cz f 0 25p",f"Cz f 0 {25*cs}p").replace("Cs sni 0 33p",f"Cs sni 0 {33*cs}p").replace("Cy s 0 5p",f"Cy s 0 {5*cs}p")
        p=g.pm("pe",t)
        if p["pm"] is not None and p["pm"]<peor[0]: peor=(p["pm"],(vto,ron,cs,rail,p["fc"]))
    res[k]=peor
out=[f"{k}: PM mínimo {v[0]:.0f}° en Vth={v[1][0]}, Ron={v[1][1]}, C×{v[1][2]}, riel {v[1][3]} V (fc {v[1][4]/1e6:.2f} MHz)" for k,v in res.items()]
print("\n".join(out)); open("../resultados/pm_esquinas.txt","w",encoding="utf8").write("\n".join(out)+"\n")
