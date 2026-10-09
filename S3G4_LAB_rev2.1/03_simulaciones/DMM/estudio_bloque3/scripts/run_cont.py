# -*- coding: utf-8 -*-
"""Continuidad: abierto -> corto (20 / 40 Ω) con la cadena completa: P43 + bloque 1 + R_PROT 99k + 10k + OPA4192 (buffer X0) + A (x10.1) + divisor /2 hasta PB14.
Mide el tiempo hasta que PB14 cruza el umbral de 50 Ω (I*50*10.1/2) y a cuanto queda a los 100 us / 1 ms."""
import gen_p43 as g, numpy as np, subprocess, os, shutil, sys
LIB192 = g.ROOT + r"\Simulation_LTSpice\models\OPA2192\OPAx192.LIB"
EXTRA = f'''.include "{LIB192}"
.model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)
* camino X0: R_PROT 99k, sujecion BAV199, 10k, buffer, mux (Ron 70, Cz 25p), A x10.1 (91k/10k)
Rp bor x0p 99k
Cp0 x0p 0 3p
D0p x0p vp BAV199
D0n vn x0p BAV199
Rx0 x0p bi0 10k
Cin bi0 0 9p
Xbuf bi0 bx0 vp vn bx0 OPAx192
Rmux bx0 mux 70
Czm mux 0 28p
Rfg out inv 91k
Rgg inv 0 10k
Ctm inv 0 5p
Xamp mux inv vp vn out OPAx192
Rload out vcm 10k
Cload out vcm 10p
Vcm vcm 0 1.25
* PB14: divisor /2 y 5 pF
Rd1 out pb14 10k
Rd2 pb14 0 10k
Cpb pb14 0 5p
Ssh bor 0 ctl 0 SWC
Vctl ctl 0 PULSE(0 1 {{TS}} 10n 10n 1 2)
.model SWC SW(Ron={{RC}} Roff=1G Vt=0.5 Vh=0)
'''
def caso(nm, rk, rs, r1, rcorto, i_set, ts=3e-3, tend=3.4e-3, iny="N2"):
    t = g.deck(nm,"MOS",rk,1e12,rs=rs,r1=r1,vto=-2.0,comp="Cc og sni 1n",rsn=1e3,ctvs="600p",inyec=iny)
    t += EXTRA.replace("{TS}",str(ts)).replace("{RC}",str(rcorto))
    t += f".options method=gear reltol=0.003\n.tran 0 {tend} 0 0.2u startup\n.end\n"
    p=os.path.join(g.WORK,nm+".cir"); open(p,"w",encoding="utf8").write(t); shutil.copy(p, os.path.join(g.DECKS,nm+".cir"))
    subprocess.run([g.LT,"-b",p],timeout=300,capture_output=True)
    d=g.leer(nm); tt=d["time"]; pb=d["V(pb14)"]; vb=d["V(bor)"]
    k0=np.searchsorted(tt,ts)-1
    umbral = i_set*50*10.1/2
    antes = pb[k0]
    # primer instante tras ts con PB14 < umbral
    idx=np.where((tt>ts)&(pb<umbral))[0]
    t_cruce = (tt[idx[0]]-ts) if len(idx) else None
    final = pb[-1]; esperado = i_set*rcorto*10.1/2
    # asiento a +-2 % del valor final
    idx2=np.where(np.abs(pb/final-1)>0.02)[0]; idx2=idx2[tt[idx2]>ts]
    t_as = (tt[idx2[-1]]-ts) if len(idx2) else 0
    return dict(nm=nm,antes=antes,vb_antes=vb[k0],umbral=umbral,t_cruce=t_cruce,final=final,esperado=esperado,t_asiento=t_as,i=i_set)
if __name__=="__main__":
    out=[]
    for lab,rk,rs,r1,i,iny in (("c1: 1 mA, R_serie 1.53 kΩ",499,0,1530,1.004e-3,"N1"),("a: 0.5 mA, R_serie 4.9 kΩ",1000,2700,2200,0.501e-3,"N2")):
        for rc in (20,40):
            r=caso(f"cont_{'c1' if 'c1:' in lab else 'a'}_{rc}",rk,rs,r1,rc,i,iny=iny)
            out.append(f"{lab}, corto {rc} Ω: abierto: V_bor {r['vb_antes']:.2f} V, PB14 {r['antes']*1e3:.0f} mV; umbral 50 Ω = {r['umbral']*1e3:.0f} mV; "
                       f"cruza en {r['t_cruce']*1e6 if r['t_cruce'] is not None else float('nan'):.1f} µs; final PB14 {r['final']*1e3:.1f} mV (ideal {r['esperado']*1e3:.1f}); asiento 2 % {r['t_asiento']*1e6:.0f} µs")
    print("\n".join(out)); open("../resultados/tran_continuidad.txt","w",encoding="utf8").write("\n".join(out)+"\n")
