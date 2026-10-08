"""S11.4: read-only reuse of S11.3; no previous output is written.

GDT DC corners 420/780 V; impulse datum 1000 V at 100 V/us is common
to both corners. Extrapolation to faster ESD fronts is an assumption.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, inspect, json, math, os, re, subprocess, threading, time
from pathlib import Path
import numpy as np
import ejecutar_s11_3 as s3

HERE=Path(__file__).resolve().parent
MODELS=s3.MODELS; LT=s3.LT; old=s3.old; prev=s3.prev
JOBS=HERE/'S11_4'; RESULTS=HERE/'resultados'; LOCK=threading.Lock(); RLIM=700
writecsv=prev.writecsv; raw=prev.raw
STANDARD=Path.home()/'AppData/Local/LTspice/lib/cmp/standard.dio'
DEPENDENCY_SIGNATURE=hashlib.sha256(b''.join(p.read_bytes() for p in (
    HERE/'ejecutar_s11_3.py',HERE/'ejecutar_s11_2.py',HERE/'ejecutar_s11_1.py',
    HERE/'comun/dmm_reducido_s11_1.inc',HERE/'comun/dmm_bloque1_final.inc',STANDARD))).hexdigest()
exec(inspect.getsource(prev.deck).replace('def deck(', 'def inherited_deck(').replace('dmm_bloque1_o2.inc','dmm_bloque1_final.inc').replace('base+=red+',"base+='\\n'+red+"),globals())
exec(inspect.getsource(s3.deck).replace('def deck(', 'def s3_deck('),globals())
exec(inspect.getsource(prev.run).replace('s11_2_attempts','s11_4_attempts').replace('timeout=300','timeout=900'),globals())

def name(c):
    # Every .meas shares this complete physical-state prefix.
    return (f"{c['q']}_{c['borne']}_{c['mode']}_rel{c['relay']}_rs2700_rx100_100_none_p{c['power']}_b{c['body']}_r{c['rail']}_i{c['source']}_tap{c['tap']}_ph{c['phase']}_gdc{c['gdc']}_gimp1000_{c['stimulus']}_a{c['amplitude']}_t{c['stop']}_off{c['remove']}_{c['macro']}").replace('.','d').replace('-','m').replace('+','p')

def cases():
    out=[]
    for base in s3.cases():
        c=dict(base,rx0=100,rx2=1e-6,gdc=420)
        if base['q']=='R6' and base['borne']=='vo' and base['rx0']==100:
            for dc in (420,780):out.append(dict(c,q='T2',gdc=dc,stop=50e-6))
        elif base['q']=='R1' and base['rail'] in (.98,1) and base['mode'] in ('diode','silicon'):
            out.append(dict(c,q='T1'))
            if base['mode']=='silicon':
                for voltage in (3.,3.2):out.append(dict(c,q='T1',mode='led',amplitude=voltage))
        elif base['q']=='R2':out.append(dict(c,q='T3'))
        elif base['q']=='R3' and base['source']==0:
            # Worst R3 identified by S11.3 audit: source off; all rail/body
            # states and both AC phases retained, plus positive/negative DC.
            out.append(dict(c,q='T4'))
        elif base['q']=='R7' and base['mode']=='v':out.append(dict(c,q='T5'))
    return sorted(out,key=lambda c:('T2','T1','T3','T4','T5').index(c['q']))

def deck(c):
    text=s3_deck(c).replace('RSER=3300','RSER=2700')
    text=text.replace('Dblk bp n2 BAV199','Dblk bp n2 BAT54')
    # RX2 is a direct connection, no physical third series resistor.
    text=text.replace('Rx2 x2 hx2 {RX2}','* RX2 absent; hx2 merged into x2')
    text=re.sub(r'\bhx2\b','x2',text)
    bat=next(line for line in old.read_text(STANDARD).splitlines() if re.match(r'^\.model BAT54\s',line,re.I))
    text=text.replace('.param RX0=',bat+f'\n.param GDC={c["gdc"]} GIMP=1000 GHOLD=.01 GARC=20 GRON=1 GTAU=1n\n.param RX0=')
    prefix=name(c).lower()
    measures=[('gdt_v','MAX abs(V(vin))'),('gdt_arc_i','MAX abs(I(Bgdt))'),('gdt_state','MAX V(gstate)'),('gdt_e','INTEG V(vin)*I(Bgdt)'),('gdt_on','WHEN V(gstate)=.5 RISE=1')]
    text=text.replace('\n.end\n','\n'+'\n'.join(f'.meas tran {prefix}__{n} {cmd}' for n,cmd in measures)+'\n.end\n')
    return text

def audit(path,c):
    mapped=dict(c,q={'T1':'R1','T2':'R6','T3':'R2','T4':'R3','T5':'R7'}[c['q']])
    r=s3.audit(path,mapped)
    d=raw(path); t=np.abs(np.asarray(d['time'])); n=len(t)
    def v(node):return np.asarray(d.get('v('+node+')',np.zeros(n)))
    arc=np.asarray(d.get('i(bgdt)',np.zeros(n)));state=v('gstate')
    r.update(gdt_voltage_peak_V=float(np.max(np.abs(v('vin')))),gdt_arc_peak_A=float(np.max(np.abs(arc))),gdt_state_max=float(np.max(state)),gdt_arc_E_J=float(np.trapezoid(v('vin')*arc,t)),gdt_final_arc_A=float(arc[-1]))
    ix=np.flatnonzero(state>=.5);r['gdt_ignition_s']=float(t[ix[0]]) if len(ix) else None
    active=(state>.99)&(np.abs(arc)>.01)
    r['gdt_arc_voltage_min_V']=float(np.min(np.abs(v('vin')[active]))) if np.any(active) else None
    r['gdt_arc_voltage_max_V']=float(np.max(np.abs(v('vin')[active]))) if np.any(active) else None
    if c['stimulus']=='dut':r['dut_final_A']=float(np.asarray(d['i(vdc)'])[-1])
    for i in (0,1):
        keys=[k for k in d if ('xh'+str(i)+':') in k and k.endswith((':dhi)',':dlo)'))]
        y=np.maximum.reduce([np.abs(np.asarray(d[k])) for k in keys]) if keys else np.zeros(n)
        # Uniform 1ns grid, minimum over 20ns, maximum across the event;
        # supplement only: D4 still reports the unfiltered absolute peak.
        if c['q']=='T2':
            from scipy.ndimage import minimum_filter1d
            grid=np.arange(0,c['stop'],1e-9); yi=np.interp(grid,t,y)
            r[f'xh{i}_sustained20ns_A']=float(np.max(minimum_filter1d(yi,size=21,mode='constant',cval=0)))
    return r

def main():
    ap=argparse.ArgumentParser()
    for flag in ('smoke','resume','preflight','build','keep-raw'):ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10);ap.add_argument('--label')
    args=ap.parse_args();JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True)
    cs=cases()
    if args.only:cs=[c for c in cs if c['q'] in args.only]
    if args.build:
        for c in cs:(JOBS/(name(c)+'.cir')).write_text(deck(c),encoding='utf-8')
        print(json.dumps({'built':len(cs)}));return 0
    if args.preflight:cs=cs[:1]
    elif args.smoke:
        selected=[next(c for c in cs if c['q']==q) for q in ('T2','T1','T3','T4','T5') if any(c['q']==q for c in cs)]
        for q,mode,gdc,amp,source in [('T2','v',780,8000,0),('T2','v',420,4000,0),('T1','diode',420,60,.0001),('T1','led',420,3.2,.0001)]:
            found=next((c for c in cs if c['q']==q and c['mode']==mode and c['gdc']==gdc and c['amplitude']==amp and c['source']==source),None)
            if found is not None and found not in selected:selected.append(found)
        cs=selected
    start=time.perf_counter();records=[]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for f in cf.as_completed([pool.submit(run,c,args) for c in cs]):
            r=f.result();records.append(r)
            if len(records)%10==0 or args.smoke or args.preflight or r['status']!='ok':print(f'{len(records)}/{len(cs)} {r["q"]} {r["status"]} {r["elapsed_s"]:.3f}s',flush=True)
    dest=RESULTS/f's11_4_{args.label or ("smoke" if args.smoke else "preflight" if args.preflight else "campaign")}.csv'
    writecsv(dest,sorted(records,key=lambda r:r['id']))
    summary=dict(total=len(records),ok=sum(r['status']=='ok' for r in records),reused=sum(r.get('reused',False) for r in records),elapsed_s=time.perf_counter()-start,workers=args.workers,timeout_s=900,csv=str(dest))
    dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)
    return int(summary['ok']!=summary['total'])

if __name__=='__main__':raise SystemExit(main())
