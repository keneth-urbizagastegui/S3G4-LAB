"""S11.1, LTspice 26; no downloads; 10 workers, timeout, auditable resume.
Each job stores exact deck, log, raw, measurements and content signature.
PTC parameters are calculated; absence of a thermal curve is explicit.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, csv, hashlib, json, math, os
from pathlib import Path
import re, subprocess, time, threading, shutil
from leer_raw_s11_1 import audit_raw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2] if len(HERE.parents)>=3 else HERE.parent
MODELS = Path(os.environ.get('S3G4_MODELS', ROOT/'Simulation_LTSpice'/'models'))
LT = Path(os.environ.get('S3G4_LTSPICE', Path.home()/'AppData/Local/Programs/ADI/LTspice/LTspice.exe'))
JOBS = HERE/'S11_1'
RESULTS = HERE/'resultados'
TRACE_LOCK=threading.Lock()
G = 50*.14**2
E = -G/math.log1p(-.14**2)
VT = 8.617333262e-5*298.15
DFIS = 1/math.expm1((1.1-.02)/(2*VT))
TVRD = (19.9-14.7)/(20.1-.001)
TVKNEE = 14.7-.001*TVRD

def read_text(p):
    b = p.read_bytes()
    return b.decode('utf-16-le' if b'\x00' in b[:80] else 'utf-8', errors='replace').lstrip('\ufeff')

def cases():
    out=[]
    def add(p, **kw):
        d=dict(p=p, borne='vo', mode='v', relay=0, rs=100, power=1,
               body=0, rail=1, opening=0, phase=0, source=0, tap=2,
               stimulus='mains', fuse=1, stop=1., step=50e-6, amplitude=230,
               frequency=60, remove=10., load=0, rcold=40, grid=.5)
        d.update(kw); out.append(d)
    for rs in (100,330):
        for rail in (.98,1,1.02):
            for phase in (0,90):
                for opening in (.02,.1,100):
                    for source in (1e-3,1e-6,0):
                        add('P3',rs=rs,rail=rail,phase=phase,opening=opening,
                            source=source,mode='ohm',relay=1,tap=6)
            for tap in (0,1,2):
                add('P2',rs=rs,rail=rail,tap=tap)
                for body in (0,1):
                    for mode in ('v','ohm'):
                        add('P4',rs=rs,rail=rail,tap=tap,power=0,body=body,mode=mode)
            for phase in (0,90):
                for grid in (.5,1,2):
                    add('P5',borne='a',rs=rs,rail=rail,phase=phase,tap=4,stop=.01,step=1e-6,grid=grid)
            add('P5',borne='a',rs=rs,rail=rail,fuse=0,tap=5)
            for tap in (0,1,2):
                for amp in (-50,50):
                    add('P1',rs=rs,rail=rail,tap=tap,stimulus='dc',amplitude=amp,stop=.02,step=10e-6)
                for freq in (60,20000):
                    add('P1',rs=rs,rail=rail,tap=tap,stimulus='sine',amplitude=50,frequency=freq,
                        stop=.05 if freq==60 else .002,step=20e-6 if freq==60 else .2e-6)
            add('P1',rs=rs,rail=rail,mode='diode',relay=1,tap=6,source=.001,
                stimulus='load',load=1,stop=.02,step=10e-6,opening=100)
            for source,load in ((1e-6,2e6),(.2e-6,20e6)):
                add('P1',rs=rs,rail=rail,mode='leak',relay=1,tap=6,source=source,
                    stimulus='load',load=load,stop=.05,step=10e-6,opening=100)
            for amp in (-4000,4000,-8000,8000):
                for mode,borne,relay,tap in (('v','vo',0,0),('ohm','vo',1,6),('a','a',0,4)):
                    add('P6',rs=rs,rail=rail,mode=mode,borne=borne,relay=relay,tap=tap,
                        stimulus='esd',amplitude=amp,stop=10e-6,step=1e-9,
                        source=.001 if relay else 0)
            for mode,relay,tap in (('v',0,0),('ohm',1,6)):
                add('P7',rs=rs,rail=rail,mode=mode,relay=relay,tap=tap,opening=100,
                    remove=1.,stop=2.,source=.001 if relay else 0)
    expanded=[]
    for c in out:
        # Only connected ohm paths depend on cold resistance; no redundant P2/P4/P5.
        for rcold in ((40,60) if c['relay'] else (40,)):
            expanded.append(dict(c,rcold=rcold))
    return expanded

def name(c):
    # Every measurement inherits the actual physical state, including delay.
    cmd='never' if c['opening']>=100 else c['opening']
    actual='never' if c['relay'] and c['opening']>=100 else c['opening']+.003 if c['relay'] else 0
    return (f"{c['p']}_t25_{c['borne']}_{c['mode']}_k{c['relay']}_rs{c['rs']}_"
            f"pwr{c['power']}_body{c['body']}_rail{c['rail']}_open{cmd}_"
            f"actual{actual}_ph{c['phase']}_i{c['source']}_tap{c['tap']}_{c['stimulus']}_"
            f"amp{c['amplitude']}_f{c['frequency']}_fuse{c['fuse']}_macro{c.get('macro','full')}_ptc{c['rcold']}_grid{c['grid']}").replace('.','d').replace('-','m')

def deck(c):
    lines=[f"* {name(c)}",f'* STATE {json.dumps(c,sort_keys=True)}',
           f'.include "{MODELS / "74HC4051/hc_tnomi.cir"}"',
           f'.include "{MODELS / "OPA2188/OPAx188.LIB"}"',
           f'.param RCOLD={c["rcold"]} ECRIT={-c["rcold"]*.14**2/math.log1p(-.14**2):.15g} GTHERM={c["rcold"]*.14**2:.15g} DFIS={DFIS:.15g}',
           f'.param REGDROP={.1*8.617333262e-5*300.15*math.log1p(.003/1e-9)+.11*.003:.15g}',
           f'.param TVRD={TVRD:.15g} TVKNEE={TVKNEE:.15g} TVLEAK=5u',
           f".param RSER={c['rs']} POWER={c['power']} RAIL={c['rail']} BODYCASE={c['body']}",
           f".param TAP={c['tap']} ISOURCE={c['source']} FUSEON={c['fuse']}",
           f'.include "{HERE / "comun/dmm_bloque1.inc"}"']
    lines+=['.temp 25']
    if c.get('macro')=='reduced':
        include=(HERE/'comun/dmm_bloque1.inc').read_text()
        excluded=('Xm','Bsel','Vhead ','Vsense ','Ccontrol ','Rcontrol ','Berror ','Bgate ','Mpass ',
                  'Vamp ','Eampp ','Eampn ','Ecalc ','Xamp ','Eout ','Xphysical ','Cphysical','Rloadp ','Rloadn ')
        include='\n'.join(x for x in include.splitlines() if not x.startswith(excluded))
        include+='\n'+(HERE/'comun/dmm_reducido_s11_1.inc').read_text()
        if not c['power']:
            # §1.4: remove residual external load while retaining §3c IC equivalents.
            # Powered decks remain byte-identical, so their exact signatures resume.
            include=include.replace('Riqother rp rn {9.8/(.003-2*415u-2*550u-16u)}',
                                    '* Residual external load disconnected: DMM off, §1.4.')
        node=['x0','x1','x2','0','shunt','x5','n2','0'][c['tap']]
        include+=f'\nRselected {node} mux 60\n'
        lines=[x.replace(f'.include "{HERE / "comun/dmm_bloque1.inc"}"',include) for x in lines if 'hc_tnomi.cir' not in x and 'OPAx188.LIB' not in x]
    if c.get('macro') in ('input','external'):
        include=(HERE/'comun/dmm_bloque1.inc').read_text()
        include='\n'.join(x for x in include.splitlines() if not x.startswith(('Xamp ','Eampp ','Eampn ','Bampip ','Bampin ','Ecalc ','Eout ','Xphysical ','Cphysical')))
        include+='\nXampinput ampin out rp rn ESD_IN_OPAx188\nCampin ampin 0 9.5p\nCampout out 0 9.5p\nCampdiff ampin out 6p\nRout out 0 1T\n'
        if c.get('macro')=='external':
            # Diagnostic external protection bound; no claim to model IC behavior.
            include='\n'.join(x for x in include.splitlines() if not x.startswith(('Xm','Xampinput ','Camp','Bsel')))
            node=['x0','x1','x2','0','shunt','x5','n2','0'][c['tap']]
            include+=f'\nRdiagnostic {node} mux 1T\n'
        lines=[x.replace(f'.include "{HERE / "comun/dmm_bloque1.inc"}"',include) for x in lines]
    end=c['opening']+.003
    lines.append(f"Brc rc 0 V={c['relay']}" if c['opening']>=100 else f"Brc rc 0 V=if(time<{end:.15g},{c['relay']},0)")
    target='vin' if c['borne']=='vo' else 'ain'
    other='ain' if target=='vin' else 'vin'
    if c['stimulus'] in ('mains','sine'):
        peak=c['amplitude']*math.sqrt(2)
        lines += [f"Bstim gen 0 V=if(time<{c['remove']},{peak:.15g}*sin(2*pi*{c['frequency']}*time+{math.radians(c['phase']):.15g}),0)",
                  f"Rgrid gen {target} {c['grid'] if target=='ain' else '1u'}"]
    elif c['stimulus']=='dc':
        lines += [f"Vstim {target} 0 {c['amplitude']}"]
    elif c['stimulus']=='load':
        # Test resistance calculated for approximately 1mA at compliance.
        # An exact 1mA sink is inconsistent with a 1mA source plus leakage.
        rtest=(4.9*c['rail']-.5-c['source']*(c['rcold']+c['rs']+.1))/c['source'] if c['load']==1 else c['load']
        lines += [f'Rtestload vin 0 {rtest:.15g}', '.save I(Rtestload)']
    else:
        # Contract simple IEC energy network, not calibrated IEC current shape.
        lines += [f"Cesd charged 0 150p IC={c['amplitude']}",
                  f'Resd charged gun {330 if abs(c["amplitude"])==4000 else 630}',
                  f'Sesd gun {target} fire 0 RELAY',
                  'Vfire fire 0 PULSE(0 1 100n 1p 1p 1 2)']
        lines += [f'.ic V(charged)={c["amplitude"]}']
    lines.append(f'Rother {other} 0 1G')
    # SAVE minimal raw signals needed for independent waveform audits.
    lines += ['.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1',
              f'.ic V(rp)={4.9*c["rail"]*c["power"]} V(rn)={-4.9*c["rail"]*c["power"]} V(mainp)={4.9*c["rail"]} V(mainn)={-4.9*c["rail"]} V(theta)=0',
              '.save V(0) V(vin) V(ain) V(x0) V(x1) V(x2) V(x5) V(n1) V(n2) V(rp) V(rn) V(theta) V(shunt) V(mux) V(out) V(p1) V(p2) V(d1) V(d2) V(c1) V(c2) V(c3) V(ms) V(pt) V(ptin) I(Vptc) I(Vsense) I(Vamp) I(Rs) I(Btvs) I(Rprot1) I(Rprot2) I(Rprot3) I(Rdiv1) I(Rdiv2) I(Rdiv3) I(Rdiv4) I(Rdiv5) I(Rc1) I(Rc2) I(Rc3) I(Rwarn) I(Rshunt) I(D0p) I(D0n) I(D1p) I(D1n) I(D2p) I(D2n) I(D5p) I(D5n) I(Dbr1) I(Dbr2) I(Dbr3) I(Dbr4)',
              f".tran 0 {c['stop']} 0 {c['step']}"]
    prefix=name(c).lower()
    def meas(metric,command):
        lines.append(f'.meas tran {prefix}__{metric} {command}')
    for node in ('x0','x1','x2','n1','n2','mux','shunt','x5','rp','rn','theta'):
        meas(node+'_max',f'MAX V({node})')
        meas(node+'_min',f'MIN V({node})')
    meas('span_max','MAX V(rp,rn)')
    for node in ('x0','x1','x2','n2','mux','x5','shunt'):
        meas(node+'_excess','MAX max(V('+node+')-V(rp),V(rn)-V('+node+'))')
    for diode in ('D0p','D0n','D1p','D1n','D2p','D2n','D5p','D5n','Dbr1','Dbr2','Dbr3','Dbr4'):
        meas(diode.lower()+'_peak',f'MAX abs(I({diode}))')
        meas(diode.lower()+'_i2t',f'INTEG I({diode})*I({diode})')
    for n in ('0','1','2','5'):
        node={'0':'x0','1':'x1','2':'n2','5':'x5'}[n]
        p=f'max(V({node},rp)*I(D{n}p),0)+max(V(rn,{node})*I(D{n}n),0)'
        meas(f'bav{n}_p',f'AVG ({p})')
        meas(f'bav{n}_e',f'INTEG ({p})')
    meas('injp_peak','MAX max(I(D0p)+I(D1p)+I(D2p)+I(D5p),0)')
    meas('injn_peak','MAX max(I(D0n)+I(D1n)+I(D2n)+I(D5n),0)')
    meas('pass_peak','MAX abs(I(Vsense))')
    meas('pass_final',f'FIND I(Vsense) AT {c["stop"]}')
    meas('amp_input_peak','MAX abs(I(Vamp))')
    meas('pass_vds','MAX abs(V(n2,ms))')
    meas('ptc_peak','MAX abs(I(Vptc))')
    meas('ptc_v','MAX abs(V(pt,n1))')
    meas('ptc_e','INTEG V(pt,n1)*I(Vptc)')
    meas('trip','WHEN V(theta)=1 RISE=1')
    resistors={'Rprot1':('vin','p1'),'Rprot2':('p1','p2'),'Rprot3':('p2','x0'),
               'Rdiv1':('vin','d1'),'Rdiv2':('d1','d2'),'Rdiv3':('d2','x1'),
               'Rdiv4':('x1','x2'),'Rdiv5':('x2','0'),'Rc1':('vin','c1'),
               'Rc2':('d1','c2'),'Rc3':('d2','c3'),'Rs':('n1','n2'),
               'Rwarn':('ain','x5'),'Rshunt':('shunt','0')}
    for part,(a,b) in resistors.items():
        v=f'V({a})' if b=='0' else f'V({a},{b})'
        expr=f'{v}*I({part})'
        meas(part.lower()+'_v',f'MAX abs({v})')
        meas(part.lower()+'_p',f'AVG {expr}')
        meas(part.lower()+'_e',f'INTEG {expr}')
    meas('tvs_p','AVG V(n1)*I(Btvs)')
    meas('tvs_peak_p','MAX V(n1)*I(Btvs)')
    meas('tvs_e','INTEG V(n1)*I(Btvs)')
    for part,a,b in (('cc1','c1','d1'),('cc2','c2','d2'),('cc3','c3','x1'),('cdiv4','x1','x2'),('cdiv5','x2','0')):
        meas(part+'_v',f'MAX abs(V({a}))' if b=='0' else f'MAX abs(V({a},{b}))')
    for i in range(20):
        if c['p']=='P3':
            meas(f'tvs_half{i}_e',f'INTEG V(n1)*I(Btvs) FROM {i/(2*c["frequency"])} TO {(i+1)/(2*c["frequency"])}')
    meas('terminal_final',f'FIND V(vin) AT {c["stop"]}')
    if c['stimulus']=='load': meas('testload_final',f'FIND I(Rtestload) AT {c["stop"]}')
    meas('leak_tvs_final',f'FIND I(Btvs) AT {c["stop"]}')
    meas('leak_bav_final',f'FIND (I(D2p)-I(D2n)) AT {c["stop"]}')
    meas('leak_prot_final',f'FIND (I(D0p)-I(D0n)) AT {c["stop"]}')
    meas('relay_v','MAX abs(V(vin,ptin))')
    if c['p']=='P7':
        meas('x0_recovery',f'MAX abs(V(x0)) FROM {c["remove"]+.9} TO {c["stop"]}')
        # ohm reference is not zero; independent postprocessing is required.
        meas('theta_after',f'FIND V(theta) AT {c["stop"]}')
    lines += ['.end','']
    return '\n'.join(lines)

def parse_log(path):
    text=read_text(path) if path.exists() else ''
    values={}
    for line in text.splitlines():
        m=re.match(r'\s*(\S+?)__(\w+)\s*:.*?=\s*([-+\d.eE]+)(?:\s|$)',line)
        if m:
            try: values[m[2]]=float(m[3])
            except ValueError: pass
    return values,text

def run(c,args):
    if args.resume and c['p']=='P1' and not c['relay']:
        for old in args.legacy:
            ignore={'rcold','frequency'} if c['stimulus']=='dc' else {'rcold'}
            if all(old.get(k)==v for k,v in c.items() if k not in ignore):
                return dict(old,reused_legacy=True,rcold=c['rcold'],legacy_frequency=old['frequency'])
    ident=name(c); p=JOBS/(ident+'.cir'); content=deck(c)
    digest=hashlib.sha256((content+(HERE/'comun/dmm_bloque1.inc').read_text()+
            read_text(MODELS/'OPA2188/OPAx188.LIB')+read_text(MODELS/'74HC4051/hc_tnomi.cir')).encode()).hexdigest()
    stamp=p.with_suffix('.json')
    if args.resume and stamp.exists():
        old=json.loads(stamp.read_text())
        if old.get('signature')==digest and old.get('status')=='ok': return old
    if p.with_suffix('.log').exists():
        archive=RESULTS/'intentos'; archive.mkdir(exist_ok=True)
        shutil.copy2(p.with_suffix('.log'),archive/(ident+f'_{time.time_ns()}.log'))
        p.with_suffix('.log').unlink()
    p.write_text(content,encoding='utf-8')
    t=time.perf_counter(); status='ok'; code=None
    try:
        proc=subprocess.Popen([str(LT),'-b',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                              creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        while proc.poll() is None:
            if time.perf_counter()-t>args.timeout: raise subprocess.TimeoutExpired(proc.args,args.timeout)
            lp=p.with_suffix('.log')
            if lp.exists():
                with lp.open('rb') as f:
                    f.seek(max(0,lp.stat().st_size-6000)); tail=f.read().decode(errors='replace')
                if tail.count('Simulation tolerance relaxed')>=3 or 'Time step too small' in tail:
                    status='numerical_failure'
                    subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
                    break
            time.sleep(.25)
        code=proc.wait()
        if code and status=='ok': status='error'
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
        proc.wait(); status='timeout'
    values,log=parse_log(p.with_suffix('.log'))
    if not values or 'Fatal Error' in log or 'Unknown' in log: status='error' if status=='ok' else status
    # Success means numerical completion with required endpoint, not acceptance.
    if 'span_max' not in values or 'terminal_final' not in values: status='error' if status=='ok' else status
    record=dict(c,id=ident,status=status,returncode=code,elapsed_s=time.perf_counter()-t,
                signature=digest,**values)
    try: record.update(audit_raw(p.with_suffix('.raw'),c['stop'],c['frequency'],c))
    except Exception as ex: record['raw_audit_error']=str(ex)
    if not args.keep_raw:
        for suffix in ('.raw','.op.raw'):
            raw=p.with_suffix(suffix)
            if raw.exists() and raw.resolve().parent==JOBS.resolve(): raw.unlink()
    stamp.write_text(json.dumps(record,indent=2),encoding='utf-8')
    with TRACE_LOCK:
        with (RESULTS/'s11_1_intentos.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(record)+'\n')
    return record

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--resume',action='store_true'); ap.add_argument('--workers',type=int,default=10)
    ap.add_argument('--timeout',type=float,default=300); ap.add_argument('--only',nargs='*')
    ap.add_argument('--preflight',action='store_true',help='Run exactly one reduced P3 before any campaign')
    ap.add_argument('--input-only',action='store_true',help='Explicit partial model: TI input clamps and capacitances; no amplifier transfer/recovery validation')
    ap.add_argument('--external-only',action='store_true',help='External network diagnostic only; excludes IC models, never certifies C3/C7')
    ap.add_argument('--keep-raw',action='store_true',help='Retain raw; otherwise numeric audits and decks/logs permit regeneration')
    args=ap.parse_args(); JOBS.mkdir(exist_ok=True); RESULTS.mkdir(exist_ok=True)
    for p in (LT,MODELS/'OPA2188/OPAx188.LIB',MODELS/'74HC4051/hc_tnomi.cir'):
        if not p.exists(): raise FileNotFoundError(p)
    allcases=cases()
    priority=('P3','P2','P4','P5','P1','P6','P7')
    allcases.sort(key=lambda c:priority.index(c['p']))
    args.legacy=[]  # §3c: only exact current signatures may be reused.
    for c in allcases: c['macro']='external' if args.external_only else 'input' if args.input_only else 'full' if c['p']=='P1' else 'reduced'
    if args.only: allcases=[c for c in allcases if c['p'] in args.only]
    if args.preflight:
        allcases=[next(c for c in allcases if c['p']=='P3')]
    if args.smoke:
        # One representative per group and R_S; full matrix runs after smoke.
        allcases=[next(c for c in allcases if c['p']==p and c['rs']==rs and (p not in ('P1','P2') or c['tap']==2))
                  for p in ('P3','P2','P4','P5','P1','P6','P7') if any(c['p']==p for c in allcases)
                  for rs in (100,330)]
    start=time.perf_counter(); records=[]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futs=[pool.submit(run,c,args) for c in allcases]
        for future in cf.as_completed(futs):
            rec=future.result(); records.append(rec)
            if len(records)%10==0 or args.smoke or rec['status']!='ok':
                print(f"{len(records)}/{len(allcases)} {rec['status']} {rec['id']} {rec['elapsed_s']:.2f}s",flush=True)
    keys=sorted(set().union(*(r.keys() for r in records)))
    csvpath=RESULTS/(('s11_1_preflight_' if args.preflight else 's11_1_smoke_' if args.smoke else 's11_1_campana_')+('external' if args.external_only else 'input' if args.input_only else 'mixta')+'.csv')
    with csvpath.open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=keys); writer.writeheader(); writer.writerows(sorted(records,key=lambda r:r['id']))
    summary=dict(total=len(records),ok=sum(r['status']=='ok' for r in records),
                 elapsed_s=time.perf_counter()-start,workers=args.workers,timeout=args.timeout,
                 thermal=dict(Rcold=[40,60],G_per_ohm=.14**2,Ecrit_per_ohm=-.14**2/math.log1p(-.14**2),tau=E/G,trip_1A_s=1),
                 csv=str(csvpath),smoke=args.smoke)
    csvpath.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary),flush=True)
    return 0 if summary['ok']==summary['total'] else 1

if __name__=='__main__': raise SystemExit(main())
