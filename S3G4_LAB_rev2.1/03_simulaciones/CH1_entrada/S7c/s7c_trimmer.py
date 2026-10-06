"""S7c (Claude, 4 oct 2026): Monte Carlo del rango del trimmer con la opción A de Keneth.
Misma fórmula que realization() de ejecutar_s7b.py (igualdad de tau del ÷100, S2b).
Escenarios: S7b (validación), tolerancias estrechas, y huecos DNP de ajuste."""
import numpy as np, csv, json
N=20000; SEED=20261004
def board(rng,tol_ct,tol_cb1,tol_cb2):
    u=lambda t:1+t*rng.uniform(-1,1)
    rp=4.9*u(.02); rn=4.9*u(.02)
    Rt1=549e3*u(.001); Rt2=549e3*u(.001); Rb=11e3*u(.001); Rbias=10e6*u(.01)
    Ct1=20e-12*u(tol_ct); Ct2f=16e-12*u(tol_ct)
    Cb=1e-9*u(tol_cb1)+68e-12*u(tol_cb2) if tol_cb2 is not None else 1088.5e-12*u(tol_cb1)
    Csel_p=3e-12*u(.5); Ctap=2e-12*u(.05); CswAC=0.5e-12*u(.05); CswGND=0.5e-12*u(.05); Coff=1e-12*u(.05)
    cj=lambda v:1.9002e-12/(1+v/1.2722)**.35193
    rbp=Rb*Rbias/(Rb+Rbias); rtop=Rt1+Rt2
    csel=cj(rp)+cj(rn)+Csel_p+2.5e-12+CswAC+CswGND
    def req(dnp_top=0.0,dnp_bot=0.0):
        ctop=rbp*(Cb+dnp_bot+csel+Ctap)/rtop-Coff
        return (Ct1*ctop/(Ct1-ctop)-(Ct2f+dnp_top))*1e12
    return req
def run(label,tol_ct,tol_cb1,tol_cb2,dnp_top_opts=(),dnp_bot_opts=()):
    rng=np.random.default_rng(SEED)
    reqs=[board(rng,tol_ct,tol_cb1,tol_cb2) for _ in range(N)]
    base=np.array([r() for r in reqs])
    inr=(base>=2)&(base<=6)
    fixed=inr.copy(); used={}
    for i,r in enumerate(reqs):
        if inr[i]: continue
        if base[i]>6:
            for d in dnp_top_opts:
                v=r(dnp_top=d*1e-12)
                if 2<=v<=6: fixed[i]=True; used[('top',d)]=used.get(('top',d),0)+1; break
        else:
            for d in dnp_bot_opts:
                v=r(dnp_bot=d*1e-12)
                if 2<=v<=6: fixed[i]=True; used[('bot',d)]=used.get(('bot',d),0)+1; break
    p=np.percentile(base,[2.5,50,97.5])
    res=dict(escenario=label,N=N,p2_5=round(p[0],3),p50=round(p[1],3),p97_5=round(p[2],3),
             bajo_2pF_pct=round((base<2).mean()*100,2),sobre_6pF_pct=round((base>6).mean()*100,2),
             trimmer_solo_pct=round(inr.mean()*100,2),con_DNP_pct=round(fixed.mean()*100,2),
             DNP_usados={f'{k[0]} {k[1]} pF':v for k,v in sorted(used.items())})
    print(json.dumps(res,ensure_ascii=False)); return res
out=[]
out.append(run('S7b (validación): Ct ±5 %, Cb ±5 % en una pieza',.05,.05,None))
out.append(run('A1: Ct ±2 %, Cb = 1 nF ±1 % + 68 pF ±2 %',.02,.01,.02))
out.append(run('A2: Ct ±1 %, Cb = 1 nF ±1 % + 68 pF ±1 %',.01,.01,.01))
out.append(run('A1 + DNP arriba (∥ C1B) 0.5/1/1.5/2.2 pF y abajo (∥ Cb) 15/22/33 pF',.02,.01,.02,(0.5,1,1.5,2.2),(15,22,33)))
out.append(run('A2 + DNP igual',.01,.01,.01,(0.5,1,1.5,2.2),(15,22,33)))
with open('s7c_resultados.json','w',encoding='utf8') as f: json.dump(out,f,ensure_ascii=False,indent=1)
