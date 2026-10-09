# -*- coding: utf-8 -*-
"""Arranque de la fuente P43 por rango (rieles con 'startup', TVS 600 pF): tiempo en que la corriente en el borne queda a 1 % / 0.1 % / 0.01 % de su valor final."""
import gen_p43 as g, numpy as np, subprocess, os, sys
rk = {"1mA":499,"100uA":4990,"10uA":49900,"1uA":499e3,"0.2uA":2.499e6}
rxfs = {"1mA":2000,"100uA":20e3,"10uA":200e3,"1uA":2e6,"0.2uA":20e6}
tend = {"1mA":"1m","100uA":"1m","10uA":"3m","1uA":"20m","0.2uA":"80m"}
step = {"1mA":"1u","100uA":"1u","10uA":"2u","1uA":"10u","0.2uA":"50u"}
def correr(nm, t, to=120):
    p=os.path.join(g.WORK,nm+".cir"); open(p,"w",encoding="utf8").write(t)
    import shutil; shutil.copy(p, os.path.join(g.DECKS,nm+".cir"))
    subprocess.run([g.LT,"-b",p],timeout=to,capture_output=True)
    return g.leer(nm)
out=[]
for k in rk:
    for rxlab,rx in (("fondo",rxfs[k]),("10 %",rxfs[k]*0.1)):
        nm=f"arr_{k}_{rxlab.replace(' %','p')}"
        t=g.deck(nm,"MOS",rk[k],rx,rs=500,r1=1530,vto=-2.0,comp="Cc og sni 1n",rsn=1e3,ctvs="600p",inyec="N1")
        t+=f".options method=gear reltol=0.003\n.tran 0 {tend[k]} 0 {step[k]} startup\n.end\n"
        d=correr(nm,t); tt=d["time"]; v=d["V(bor)"]; vf=v[-1]
        # tiempo desde que los rieles estan arriba (50 us) hasta entrar y quedarse en la banda
        def t_banda(tol):
            idx=np.where(np.abs(v/vf-1)>tol)[0]; return (tt[idx[-1]] if len(idx) else 0)
        i_f = vf/rx + vf/10.01e6
        out.append(f"{k} Rx={rx:g}: V_bor final {vf:.4f} V, I_total {i_f*1e6:.4g} uA, 1 % en {t_banda(1e-2)*1e3:.3f} ms, 0.1 % en {t_banda(1e-3)*1e3:.3f} ms, 0.01 % en {t_banda(1e-4)*1e3:.3f} ms")
print("\n".join(out)); open("../resultados/tran_arranque.txt","w",encoding="utf8").write("\n".join(out)+"\n")
