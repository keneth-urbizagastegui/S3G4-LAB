"""S11.3 O4. Prior executors imported read-only; 10 workers, 300 s/case."""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, inspect, json, math, os, re, subprocess, threading, time
from pathlib import Path
import numpy as np
import ejecutar_s11_2 as prev
HERE=Path(__file__).resolve().parent
MODELS=prev.MODELS; LT=prev.LT; old=prev.old; LOCK=threading.Lock()
JOBS=HERE/'S11_3'; RESULTS=HERE/'resultados'; RLIM=700
writecsv=prev.writecsv; raw=prev.raw
DEPENDENCY_SIGNATURE=hashlib.sha256(b''.join(p.read_bytes() for p in (HERE/'ejecutar_s11_2.py',HERE/'ejecutar_s11_1.py',HERE/'comun/dmm_reducido_s11_1.inc'))).hexdigest()
# Reuse process management in an isolated namespace; no S11.2 writes.
exec(inspect.getsource(prev.run).replace('s11_2_attempts','s11_3_attempts'),globals())
exec(inspect.getsource(prev.deck).replace('def deck(', 'def inherited_deck(').replace('dmm_bloque1_o2.inc','dmm_bloque1_o4.inc').replace('base+=red+',"base+='\\n'+red+"),globals())

def name(c):
    labels={'relay':'rel','power':'p','body':'b','rail':'rail','source':'iset','tap':'tap','phase':'ph','grid':'z','arc':'k','amplitude':'amp','frequency':'hz','stop':'t','remove':'off','rx0':'x0r','rx2':'x2r','load':'load'}
    state='_'.join(f'{labels[k]}{c[k]:g}' for k in labels)
    return (f'{c["q"]}_{c["borne"]}_{c["mode"]}_rs3300_x1r100_'+state+'_'+c['stimulus']+'_'+c['macro']).replace('.','d').replace('-','m').replace('+','p')

def cases():
    out=[]
    def add(q,**kw):
        c=dict(q=q,borne='vo',mode='ohm',relay=1,power=1,body=0,rail=1,source=.001,tap=1,phase=0,grid=.5,arc=1,idss=.007,vp=1.6,ron=700,temp=25,stimulus='mains',amplitude=60,frequency=60,stop=1.,step=50e-6,remove=10.,load=0,zbv=5.6,macro='reduced',rx0=1e-6,rx2=1e-6)
        c.update(kw);out.append(c)
    for rail in (.98,1,1.02):
        for power,body in ((1,0),(0,0),(0,1)):
            for source in (.001,.0001,.2e-6,0):
                for stimulus,amp in (('dc',60),('dc',-60),('mains',60)):
                    for phase in ((0,90) if stimulus=='mains' else (0,)):
                        add('R3',rail=rail,power=power,body=body,source=source,stimulus=stimulus,amplitude=amp,phase=phase)
            for phase in (0,90):
                add('R2',rail=rail,power=power,body=body,mode='v',relay=0,source=0,amplitude=230,phase=phase,tap=0)
                add('R3b',rail=rail,power=power,body=body,amplitude=230,phase=phase,stop=.1,step=10e-6)
    for amp in (-4000,4000,-8000,8000):
        for mode,borne,relay,tap in (('ohm','vo',1,1),('v','vo',0,0),('a','a',0,4)):
            for rail in (.98,1,1.02):
                for power,body in ((1,0),(0,0),(0,1)):
                    for rx0,rx2 in ((1e-6,1e-6),(100,100)):
                        add('R6',amplitude=amp,stimulus='esd',mode=mode,borne=borne,relay=relay,tap=tap,rail=rail,power=power,body=body,source=.001 if relay else 0,stop=10e-6,step=1e-9,rx0=rx0,rx2=rx2)
    for grid in (.5,1,2):
        for arc in (1,2,3):
            for phase in (0,30,60,90,120,150):
                for rail in (.98,1,1.02):
                    add('R5',borne='a',mode='a',relay=0,source=0,tap=4,grid=grid,arc=arc,phase=phase,rail=rail,amplitude=230,stop=.02,step=1e-7)
    for rail in (.98,1,1.02):
        for source in (.001,.0001):
            add('R1',mode='diode',stimulus='sweep',source=source,rail=rail,macro='full',stop=.02,step=10e-6)
            add('R1',mode='silicon',stimulus='dut',amplitude=.65,source=source,rail=rail,macro='full',stop=.02,step=10e-6)
        for source,load in ((.2e-6,20e6),(1e-6,2e6)):
            add('R1',mode='leak',stimulus='load',source=source,load=load,rail=rail,macro='full',stop=.05,step=10e-6)
        for tap in (0,1,2):
            for stimulus,amp,freq in (('dc',50,60),('dc',-50,60),('mains',50,60),('mains',50,20000)):
                add('R1',mode='v',relay=0,source=0,tap=tap,rail=rail,stimulus=stimulus,amplitude=amp,frequency=freq,stop=.01 if freq==20000 else .1,step=1e-6 if freq==20000 else 10e-6)
    for rail in (.98,1,1.02):
        for mode,amp,relay,tap in (('v',230,0,0),('ohm',60,1,1)):
            for power,body in ((1,0),(0,0),(0,1)):
                add('R7',mode=mode,amplitude=amp,relay=relay,tap=tap,rail=rail,power=power,body=body,source=.001 if relay else 0,stimulus='recovery',remove=10.,stop=12.,load=650,step=50e-6)
    return out

def deck(c):
    text=inherited_deck(c)
    text=re.sub(r'^\.include .*bss126_s11_2.inc.*\n','',text,flags=re.M)
    text=re.sub(r'^\.meas .*__(fet[12]_.*|lim_peak) .*\n','',text,flags=re.M)
    text=text.replace('RSER=47','RSER=3300')
    text=text.replace('.param RSER=',f'.param TVRD={old.TVRD:.15g} TVKNEE={old.TVKNEE:.15g} TVLEAK=5u\n.param RSER=')
    text=text.replace('.param RSER=',f'.param RX0={c["rx0"]} RX2={c["rx2"]}\n.param RSER=')
    for i in range(3):text=text.replace(f'Xh{i} x{i} rp rn',f'Xh{i} hx{i} rp rn')
    text=text.replace('Rselected x','Rselected hx')
    text=text.replace('325.269119345812',f'{c["amplitude"]*math.sqrt(2):.15g}').replace('2*pi*60*time',f'2*pi*{c["frequency"]}*time')
    if c['stimulus'] in ('dc','dut'):
        text=re.sub(r'^Cesd .*\n|^Resd .*\n|^Sesd .*\n|^Vfire .*\n|^\.ic V\(charged\).*\n','',text,flags=re.M)
        text=text.replace('Rother ',f'Vdc vin 0 {c["amplitude"]}\nRother ')
    if c['stimulus']=='recovery':
        text=text.replace('time<10,1,0',f'time<{c["remove"]},1,0')
    prefix=name(c).lower()
    if c['q']=='R5':text=text.replace('\n.end\n',f'\n.meas tran {prefix}__fuse_open WHEN V(qfus)={6.7*c["arc"]} RISE=1\n.end\n')
    text=text.replace('\n.end\n',f'\n.meas tran {prefix}__ohm1_e INTEG V(ptin,ohmid)*I(Rohm1)\n.meas tran {prefix}__tvs_e INTEG V(n1)*I(Btvs)\n.end\n')
    assert 'BSS126_EST' not in text and 'Rlim ' not in text
    return '* Read-only dependencies sha256 '+DEPENDENCY_SIGNATURE+'\n'+text

def audit(path,c):
    mapped=dict(c,q={'R1':('Q1' if c['source'] else 'R1'),'R5':'Q5'}.get(c['q'],c['q']))
    r=prev.audit(path,mapped)
    d=raw(path);t=np.abs(np.array(d['time']));n=len(t)
    def v(x):return np.asarray(d.get('v('+x+')',np.zeros(n))) if x!='0' else np.zeros(n)
    def cur(x):return np.asarray(d.get('i('+x.lower()+')',np.zeros(n)))
    parts=[('rohm1','ptin','ohmid'),('rohm2','ohmid','n1'),('rs','n1','n2'),('btvs','n1','0'),('rx0','x0','hx0'),('rx1','x1','hx1'),('rx2','x2','hx2')]
    parts += [(f'rprot{i}',a,b) for i,a,b in ((1,'vin','p1'),(2,'p1','p2'),(3,'p2','x0'))]
    parts += [('dzp','0','rp'),('dzn','rn','0'),('rshunt','shunt','0'),('rb','shunt','bin')]
    parts += [('dbr1','shunt','bridge'),('dbr2','0','bridge'),('dbr3','bridge','shunt'),('dbr4','bridge','0')]
    parts += [('d0p','x0','rp'),('d0n','rn','x0'),('d1p','x1','rp'),('d1n','rn','x1'),('d2p','n2','rp'),('d2n','rn','n2'),('d5p','x5','rp'),('d5n','rn','x5'),('dblk','bp','n2')]
    for part,a,b in parts:
        vv=v(a)-v(b);p=vv*cur(part);energy=float(np.trapezoid(p,t))
        r[part+'_V']=float(np.max(np.abs(vv)));r[part+'_Ppeak_W']=float(np.max(p));r[part+'_E_sim_J']=energy
        r[part+'_Ipeak_A']=float(np.max(np.abs(cur(part))))
        if c['q'] in ('R2','R3') and r['raw_complete']:
            mask=t>=t[-1]-5/c['frequency'];mean=float(np.trapezoid(p[mask],t[mask])/(t[mask][-1]-t[mask][0]))
            r[part+'_P_period_W']=mean;r[part+'_E_extrap_J']=mean*(10-t[-1]);r[part+'_E10_J']=energy+mean*(10-t[-1])
    for pin in ('hx0','hx1','hx2','mux','ampin','out','ms','msource','bin','x5'):
        r[pin+'_rail_excess']=float(np.max(np.maximum(v(pin)-v('rp'),v('rn')-v(pin))))
    r['relay_drop_max_V']=float(np.max(np.abs(v('vin')-v('ptin'))))
    r['source_at_065_A']=float(np.interp(.65,v('vin'),cur('Vsense'))) if c['stimulus']=='sweep' else float(cur('Vsense')[-1])
    r['bss84_vds_peak_V']=float(np.max(np.abs(v('bp')-v('msource'))))
    for cap,a,b in (('cc1','c1','d1'),('cc2','c2','d2'),('cc3','c3','x1'),('cdiv4','x1','x2'),('cdiv5','x2','0')):
        r[cap+'_voltage_peak_V']=float(np.max(np.abs(v(a)-v(b))))
    if c['stimulus']=='sweep':
        # Positive source current into its + terminal is absorbed by the DUT.
        dut=cur('Vdut');r['dut_at_065_A']=float(np.interp(.65,v('vin'),dut))
        mask=(dut>=.99*c['source'])&(t>.002)
        r['dut_compliance99_V']=float(np.max(v('vin')[mask])) if np.any(mask) else None
        r['dut_at_35V_A']=float(np.interp(3.5,v('vin'),dut))
    elif c['stimulus']=='dut':r['dut_at_065_A']=float(cur('Vdc')[-1])
    r['tvs_final_A']=float(cur('Btvs')[-1]);r['n1_final_V']=float(v('n1')[-1]);r['n2_final_V']=float(v('n2')[-1])
    measured,_=old.parse_log(path.with_suffix('.log'))
    for part,key in (('rohm1','ohm1_e'),('btvs','tvs_e')):
        r[part+'_meas_raw_difference_J']=r[part+'_E_sim_J']-measured[key] if key in measured else None
    if c['q']=='R3b':
        for part,a,b in parts[:2]:
            p=(v(a)-v(b))*cur(part);ix=np.flatnonzero(p>1)
            r[part+'_first_over_1W_s']=float(t[ix[0]]) if len(ix) else None
    if c['q']=='R7' and r['raw_complete']:
        for node in ('x0','n2'):
            end=t>c['stop']-.1;ref=float(np.mean(v(node)[end]));bad=np.flatnonzero((t>=c['remove'])&(np.abs(v(node)-ref)>100e-6))
            r[node+'_recovery_s']=max(float(t[bad[-1]])-c['remove'],0) if len(bad) else 0
            r[node+'_end_drift_V']=float(np.ptp(v(node)[end]))
    energies={key.removesuffix('_E_sim_J'):value for key,value in r.items() if key.endswith('_E_sim_J') and math.isfinite(value)}
    r['largest_energy_part']=max(energies,key=energies.get)
    return r

def main():
    ap=argparse.ArgumentParser()
    for flag in ('smoke','resume','preflight','build','keep-raw'):ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10);ap.add_argument('--label');ap.add_argument('--modes',nargs='*')
    args=ap.parse_args();JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True)
    if args.build:return 0
    priority=('R3','R6','R2','R5','R1','R7','R3b');cs=sorted(cases(),key=lambda c:priority.index(c['q']))
    if args.only:cs=[c for c in cs if c['q'] in args.only]
    if args.modes:cs=[c for c in cs if c['mode'] in args.modes]
    if args.preflight:cs=[cs[0]]
    elif args.smoke:
        selected=[next(c for c in cs if c['q']==q) for q in priority if any(c['q']==q for c in cs)]
        for mode,source in (('diode',.0001),('silicon',.001),('leak',.2e-6),('v',0)):
            match=next((c for c in cs if c['q']=='R1' and c['mode']==mode and c['source']==source),None)
            if match is not None and match not in selected:selected.append(match)
        cs=selected
    start=time.perf_counter();records=[]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for fut in cf.as_completed([pool.submit(run,c,args) for c in cs]):
            r=fut.result();records.append(r)
            if len(records)%10==0 or args.smoke or args.preflight or r['status']!='ok':print(f'{len(records)}/{len(cs)} {r["q"]} {r["status"]} {r["elapsed_s"]:.3f}s',flush=True)
    prefix=args.label or ('preflight' if args.preflight else 'smoke' if args.smoke else 'campaign')
    dest=RESULTS/f's11_3_{prefix}.csv';writecsv(dest,sorted(records,key=lambda r:r['id']))
    summary=dict(total=len(records),ok=sum(r['status']=='ok' for r in records),reused=sum(r.get('reused',False) for r in records),elapsed_s=time.perf_counter()-start,workers=args.workers,timeout_s=300,csv=str(dest))
    dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)
    return int(summary['ok']!=summary['total'])

if __name__=='__main__':raise SystemExit(main())
