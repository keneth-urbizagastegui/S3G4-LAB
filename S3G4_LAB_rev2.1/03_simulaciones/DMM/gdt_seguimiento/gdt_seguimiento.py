"""GDT en V/Ohm: corriente de seguimiento de red y ESD, cadenas R / MOV / fusible.
Base: deck T2 (modo V, rele abierto) de S11_4 (solo lectura). Trabaja en C:\\s115.
Uso: python gdt_seguimiento.py build|run|analyze
"""
import re, sys, json, subprocess, concurrent.futures as cf, math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
BASE=HERE.parent/'S11_4'/'T2_vo_v_rel0_rs2700_rx100_100_none_p0_b0_r0d98_i0_tap0_ph0_gdc420_gimp1000_esd_a4000_t5em05_off10d0_reduced.cir'
WORK=Path('C:/s115'); LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe'
# Supuestos de pieza (marcados en el informe)
MOV_V1=430.; MOV_I1=1e-3; MOV_ALPHA=math.log(50/1e-3)/math.log(710/430)   # 14D431K: 430 V @1 mA, 710 V @ 50 A
FUSE_I2T=0.00064; FUSE_RCOLD=6.0                                             # Littelfuse 0466.125NRHF
RNET=0.7; VPK=325.269; F=60

def base_text():
    t=BASE.read_text(encoding='utf-8',errors='replace').splitlines()
    k=next(i for i,l in enumerate(t) if l.startswith('Brc rc 0'))
    return [l for l in t[:k+1] if not re.match(r'(Cgdt|Cgstate|Rgstate|Bgthreshold|Bgstate|Bgdt)',l)]

def gdt_block(chain,gdc,tau,leak=True):
    L=['.param GDC=%g GIMP=1000 GHOLD=.01 GARC=20 GRON=1 GTAU=%g'%(gdc,tau)]
    if chain=='nogdt': return L
    L+=['Cgdt ga 0 .5p','Cgstate gstate 0 1n IC=0','Rgstate gstate 0 1T',
        'Bgthreshold gthreshold 0 V={GDC+(GIMP-GDC)*limit(abs(ddt(V(ga)))/100Meg,0,1)}',
        'Bgstate 0 gstate I={1n/GTAU*if(abs(V(ga))>=V(gthreshold),1-V(gstate),if(V(gstate)>1u,if(abs(I(Bgdt))>=GHOLD,1-V(gstate),-V(gstate)),-V(gstate)))}',
        'Bgdt ga 0 I={limit(V(gstate),0,1)*sgn(V(ga))*max(abs(V(ga))-GARC,0)/GRON}']
    if leak: L.append('Rgleak ga 0 1G')
    if chain=='gdt': L.append('Rser vin ga 1u')
    elif chain.startswith('r'): L.append('Rser vin ga %s'%chain[1:])
    elif chain in('mov','mov271'):
        v1,vc=(MOV_V1,710.) if chain=='mov' else (270.,455.)
        N=1.002*0.025852*1000; N=(vc-v1)/math.log(50/MOV_I1) if chain=='mov271' else N
        IS=MOV_I1/math.exp(v1/N)
        L+=['* MOV 14D431K (supuesto de ficha): 430 V @1 mA, 710 V @50 A; diodos antiparalelo N=1002 (exponencial) + Rs',
            '.model MOVD D(Is=%g N=%g Rs=0.15)'%(IS,N/0.025852),'Dm1 vin ga MOVD','Dm2 ga vin MOVD']
    elif chain=='fuse':
        L+=['.model FUSE_SW2 SW(Ron=1m Roff=1e12 Vt=0 Vh=.001)','Vgf vin gf0 0','Rfuse gf0 gf %g'%FUSE_RCOLD,
            'Sfz gf ga fc2 0 FUSE_SW2','Bfc2 fc2 0 V=(%g-V(qf2))*10000'%FUSE_I2T,'Cqf2 qf2 0 1 IC=0','Bqf2 0 qf2 I=I(Vgf)**2']
    return L

SAVE='.save V(vin) V(ga) V(ptin) V(p1) V(p2) V(x0) V(x1) V(x2) V(gen) V(gstate) V(qf2) I(Rx0) I(Rx1) I(Bgdt) I(Dm1) I(Dm2) I(Rser) I(Vgf) I(Rfuse) I(Rsrc) I(Rprot1)'
def tail_esd(v,tstop=50e-6,tau=1e-9):
    return ['Cesd charged 0 150p IC=%g'%v,'Resd charged gun 330','Sesd gun vin fire 0 RELAY','Vfire fire 0 PULSE(0 1 100n 1p 1p 1 2)','.ic V(charged)=%g'%v,
            'Rother ain 0 1G','.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1',
            '.ic V(rp)=0.0 V(rn)=-0.0 V(qfus)=0',SAVE,'.tran 0 %g 0 1e-9'%tstop,'.end']
def tail_surge(phase_deg,vtot=1000.,tstop=25e-3,mains=VPK):
    t0=phase_deg/360/F; vm=mains*math.sin(2*math.pi*F*t0); amp=(vtot-vm)*1.037
    surge='if(time>%g,%g*(exp(-(time-%g)/68u)-exp(-(time-%g)/.4u)),0)'%(t0,amp,t0,t0)
    return ['Bstim gen 0 V=%g*sin(2*pi*60*time)+%s'%(mains,surge),'Rsrc gen vin %g'%RNET,'Rother ain 0 1G',
            '.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1',
            '.ic V(rp)=0.0 V(rn)=-0.0 V(qfus)=0',SAVE,'.tran 0 %g 0 1e-7'%tstop,'.end']
def tail_nom(vrms,rs,tstop=0.1):
    return ['Bstim gen 0 V=%g*sin(2*pi*60*time)'%(vrms*math.sqrt(2)),'Rsrc gen vin %g'%rs,'Rother ain 0 1G',
            '.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1',
            '.ic V(rp)=0.0 V(rn)=-0.0 V(qfus)=0',SAVE,'.tran 0 %g 0 2e-5'%tstop,'.end']

CHAINS=['nogdt','gdt','r10','r22','r47','r100','mov','fuse']
def cases():
    out=[]
    for ch in CHAINS:
        for v in (4000,-4000):
            for tau in (1e-9,1e-7): out.append(dict(kind='esd',chain=ch,v=v,tau=tau))
    for ch in CHAINS[1:]:
        for ph in (90,10): out.append(dict(kind='surge',chain=ch,ph=ph,tau=1e-9))
    for ch in ('mov271',):
        out+=[dict(kind='esd',chain=ch,v=4000,tau=t) for t in (1e-9,1e-7)]+[dict(kind='surge',chain=ch,ph=p,tau=1e-9) for p in (90,10)]
    for ch in ('nogdt','gdt','mov'):
        for vr in (230,253): out.append(dict(kind='nom',chain=ch,vr=vr,rs=1e5,tau=1e-9))
    return out
def name(c):
    s={'esd':'esd_%s_%d_tau%d'%(c['chain'],c.get('v',0),int(c['tau']*1e9)),'surge':'surge_%s_ph%d'%(c['chain'],c.get('ph',0)),
       'nom':'nom_%s_%d'%(c['chain'],c.get('vr',0))}[c['kind']]
    return s.replace('-','m')
def deck(c):
    L=base_text(); L=[l for l in L if not l.startswith('.param GDC')]
    L+=gdt_block(c['chain'],420,c['tau'])
    L+={'esd':lambda:tail_esd(c.get('v'),tau=c['tau']),'surge':lambda:tail_surge(c.get('ph')),'nom':lambda:tail_nom(c.get('vr'),c.get('rs'))}[c['kind']]()
    return '\n'.join(['* gdt_seguimiento '+json.dumps(c)]+L)+'\n'

def build():
    (HERE/'decks').mkdir(exist_ok=True); WORK.mkdir(exist_ok=True)
    for c in cases():
        n=name(c); (HERE/'decks'/(n+'.cir')).write_text(deck(c),encoding='utf-8'); (WORK/(n+'.cir')).write_text(deck(c),encoding='utf-8')
    print(len(cases()),'decks')
def runone(c):
    n=name(c); r=subprocess.run([LT,'-b',str(WORK/(n+'.cir'))],capture_output=True,timeout=3000)
    return n,r.returncode

def readraw(path):
    with path.open('rb') as f:h=f.read(60000)
    enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8'; mark='Binary:\n'.encode(enc); off=h.find(mark)
    hdr=h[:off].decode(enc); nv=int(re.search(r'No. Variables:\s*(\d+)',hdr)[1]); npnt=int(re.search(r'No. Points:\s*(\d+)',hdr)[1])
    names=[m[1].lower() for m in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hdr,re.M)]
    off+=len(mark); cnt=min(npnt,(path.stat().st_size-off)//(8*nv))
    a=np.memmap(path,dtype='<f8',mode='r',offset=off,shape=(cnt,nv)); return {n:np.array(a[:,i]) for i,n in enumerate(names)}

def analyze(c):
    n=name(c); d=readraw(WORK/(n+'.raw')); t=np.abs(d['time']); N=len(t)
    g=lambda k:d.get(k,np.zeros(N)); mx=lambda y:float(np.max(np.abs(y)))
    I=lambda y:float(np.trapezoid(y,t))
    r=dict(name=n,**{k:v for k,v in c.items()},stop=float(t[-1]),pts=N)
    vin,ga=g('v(vin)'),g('v(ga)'); igdt=g('i(bgdt)'); imov=g('i(dm1)')-g('i(dm2)')
    if c['kind']=='esd':
        r.update(relay_open_V=mx(vin-g('v(ptin)')),vin_peak_V=mx(vin),rprot_V=mx(vin-g('v(x0)')),x0_V=mx(g('v(x0)')),
                 x0_A=mx(g('i(rx0)')),x1_A=mx(g('i(rx1)')),i_total_gdt_A=mx(igdt),
                 gdt_E_J=I(ga*igdt),chain_drop_V=mx(vin-ga))
        for k,y in (('rser',g('i(rser)')),('mov',imov),('fuse',g('i(vgf)'))):
            if np.any(y): r[k+'_peak_A']=mx(y); r[k+'_i2t']=I(y**2)
        if c['chain'] in('r10','r22','r47','r100'): r['r_E_J']=I(g('i(rser)')**2*float(c['chain'][1:]))
        if c['chain'].startswith('mov'): r['mov_E_J']=I((vin-ga)*imov)
        if c['chain']=='fuse': r['fuse_qmax_pct']=100*mx(g('v(qf2)'))/FUSE_I2T
    elif c['kind']=='surge':
        ig=np.abs(igdt); act=np.flatnonzero(ig>0.01)
        t0=c['ph']/360/F
        r.update(t_surge_s=t0,gdt_peak_A=mx(igdt),gdt_E_J=I(ga*igdt),gdt_I2t=I(igdt**2),
                 first_s=float(t[act[0]]) if len(act) else None,last_s=float(t[act[-1]]) if len(act) else None)
        if len(act):
            r['dur_ms']=1e3*(t[act[-1]]-t[act[0]])
            late=np.flatnonzero((ig>0.01)&(t>t0+300e-6)); r['follow_dur_ms']=1e3*(t[late[-1]]-t0-300e-6) if len(late) else 0.
            mask=t>t0+300e-6; r['follow_peak_A']=float(np.max(ig[mask])) if mask.any() else 0.
            r['follow_E_J']=float(np.trapezoid((ga*igdt)[mask],t[mask])) if mask.any() else 0.
        r['src_peak_A']=mx(g('i(rsrc)')); r['src_E_J']=I((g('v(gen)')-vin)*g('i(rsrc)'))
        if c['chain'] in('r10','r22','r47','r100'):
            R=float(c['chain'][1:]); r['r_E_J']=I(g('i(rser)')**2*R); r['r_Vpeak_V']=mx(vin-ga); r['r_Ppeak_W']=mx(g('i(rser)'))**2*R
        if c['chain'].startswith('mov'): r['mov_E_J']=I((vin-ga)*imov); r['mov_peak_A']=mx(imov); r['mov_Vpeak_V']=mx(vin-ga)
        if c['chain']=='fuse': r['fuse_peak_A']=mx(g('i(vgf)')); r['fuse_i2t']=I(g('i(vgf)')**2); r['fuse_Vafter_V']=mx(vin-ga); r['fuse_qmax_pct']=100*mx(g('v(qf2)'))/FUSE_I2T
        r['relay_open_V']=mx(vin-g('v(ptin)')); r['vin_peak_V']=mx(vin)
        r['x0_A']=mx(g('i(rx0)'))
    else:
        s=t>t[-1]-2/F; rms=lambda y:float(np.sqrt(np.mean(y[s]**2)))
        r.update(x2_rms=rms(g('v(x2)')),vin_rms=rms(vin),gdt_peak_A=mx(igdt),state_max=mx(g('v(gstate)')),
                 chain_I_rms_uA=1e6*rms(g('i(rser)')+imov+ (ga/1e9)),gleak_peak_uA=1e6*mx(ga/1e9),
                 ga_peak_V=mx(ga))
        r['mov_peak_uA']=1e6*mx(imov)
    return r

if __name__=='__main__':
    m=sys.argv[1]
    if m=='build': build()
    elif m=='run':
        with cf.ThreadPoolExecutor(6) as p:
            for n,rc in p.map(runone,cases()): print(n,rc,flush=True)
    elif m=='analyze':
        res=[]
        for c in cases():
            try: res.append(analyze(c))
            except Exception as e: res.append(dict(name=name(c),error=str(e)))
        (HERE/'resultados_gdt.json').write_text(json.dumps(res,indent=1,default=float),encoding='utf-8'); print(len(res),'ok')
