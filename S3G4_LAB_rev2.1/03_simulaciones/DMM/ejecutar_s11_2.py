"""S11.2. Read-only reuse of S11.1; all new artifacts have S11_2 names.
Run --build, --preflight, --smoke, then --resume. Ten workers, 300s/case.
Rlim700 is diagnostic ONLY: Q0 shows no guaranteed feasible resistance.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, csv, hashlib, json, math, os, re
import subprocess, time, threading
from pathlib import Path
import numpy as np
from scipy.integrate import cumulative_trapezoid
from scipy.optimize import brentq
import ejecutar_s11_1 as old

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MODELS=Path(os.environ.get('S3G4_MODELS',ROOT/'Simulation_LTSpice/models'))
LT=Path(os.environ.get('S3G4_LTSPICE',Path.home()/'AppData/Local/Programs/ADI/LTspice/LTspice.exe'))
JOBS=HERE/'S11_2'; RESULTS=HERE/'resultados'; LOCK=threading.Lock()
RLIM=700

def writecsv(path,rows):
    if not rows:return
    with path.open('w',newline='',encoding='utf-8-sig') as f:
        w=csv.DictWriter(f,fieldnames=sorted(set().union(*(r.keys() for r in rows))))
        w.writeheader();w.writerows(rows)

def build():
    """Transform exact prior topology, preserving voltage network and rail models."""
    base=(HERE/'comun/dmm_bloque1.inc').read_text(encoding='utf-8')
    base='\n'.join(s for s in base.splitlines() if not s.startswith(('.func rptc','Vptc ','Bptc ','Cthermal ','Rthermal ','Bheat ','Btvs ')))
    base=base.replace('D2n rn n2 BAV199','D2n 0 n2 BAV199')
    base=base.replace('Xm6 ct6 n2 mux rn rp 0 SWI1','* Channel6 removed from N2; spare grounded.\nXm6 ct6 0 mux rn rp 0 SWI1')
    base=base.replace('Xm4 ct4 shunt mux rn rp 0 SWI1','Rb shunt bin 10k\nXm4 ct4 bin mux rn rp 0 SWI1')
    base=base.replace('Mpass n2 gate msource msource BSS84','Mpass bp gate msource msource BSS84\nDblk bp n2 BAV199')
    # Schmitt switch latches the irreversible opening; opens at q=6.7*ARC.
    # 2mA2s hysteresis prevents roundoff from closing a melted fuse again.
    base=base.replace('.model FUSE_SW SW(Ron=.04 Roff=1e12 Vt=.5 Vh=0)', '.model FUSE_SW SW(Ron=.04 Roff=1e12 Vt=0 Vh=.001)')
    base=base.replace('Vfctl fc 0 {FUSEON}','Bfctl fc 0 V=6.7*ARC-V(qfus)-.001\nCqfus qfus 0 1 IC=0\nBqfus 0 qfus I=I(Vfs)**2')
    base=base.replace('Sfuse ain shunt fc 0 FUSE_SW','Vfs ain af 0\nSfuse af shunt fc 0 FUSE_SW')
    # GBU808 p2 VF1V@4A; Rs15mohm is unverified high-current assumption.
    gbu_is=4/math.expm1((1-.015*4)/(2*8.617333262e-5*298.15))
    base=base.replace('.model DF08 D(Is={DFIS} N=2 Rs=.02 Cjo=25p BV=800 Ibv=10u)',f'.model GBU808 D(Is={gbu_is:.16g} N=2 Rs=.015 Cjo=130p BV=800 Ibv=5u)')
    base=base.replace(' DF08',' GBU808')
    base+='\n* O2 crossed gates; NO TVS or PTC.\nVlf1 ptin ld1 0\nXf1 ld1 s2 s1 BSS126_EST IDS={IDSS} VP={VP} RON={RON} TC={TC}\nRlim s1 s2 {RLIM}\nVlf2 n1 ld2 0\nXf2 ld2 s1 s2 BSS126_EST IDS={IDSS} VP={VP} RON={RON} TC={TC}\n'
    # No local BZT sheet: voltage tolerance and dynamic slope sensitivity unverified.
    base+='* BZT52C5V6 approximate sink, no local sheet found: 5.6V at5mA, Rd40ohm.\n.model Z56 D(Is=1n N=1.5 BV={ZBV} Ibv=5m Rs=40 Cjo=100p)\nDzp 0 rp Z56\nDzn rn 0 Z56\n'
    base='* S11.2 O2 derived from S11.1, originals read-only.\n'+base+'\n'
    dest=HERE/'comun/dmm_bloque1_o2.inc'
    if not dest.exists() or dest.read_text(encoding='utf-8')!=base:dest.write_text(base,encoding='utf-8')
    q0=[]
    for ids in (.007,.021):
        for vp in (1.6,2.7):
            v0=vp/(1-math.sqrt(8e-6/ids))
            kp=2*ids/v0**2
            core=v0/(2*ids)*2/(1+math.sqrt(1-.003/ids))
            for temp in (0,25,70):
                vpt=v0+.0037*(temp-25)
                kpt=kp*math.exp(-.0055*(temp-25))*v0/vpt
                lim=brentq(lambda i:i-.5*kpt*max(vpt-i*RLIM,0)**2,0,.05)
                q0.append(dict(idss_25_A=ids,idss_kind='guaranteed_min' if ids==.007 else 'assumed_sensitivity_NOT_max',threshold25_V=-vp,temp_C=temp,vto_model_V=-vpt,kp_A_V2=kpt,rd_model_ohm=max(700-core,0)*math.exp(.0055*(temp-25)),rlim_diagnostic_ohm=RLIM,shockley_ilim_A=lim,ron_target25_ohm=700,source='Infineon pp2,3,6; approximate thermal drift'))
    writecsv(RESULTS/'s11_2_q0_model.csv',q0)
    transfer=[]
    for r in q0:
        for vg in (-3,-2.7,-2,-1.6,-1,0):
            transfer.append(dict(r,VGS_V=vg,ID_sat_A=.5*r['kp_A_V2']*max(vg-r['vto_model_V'],0)**2))
    writecsv(RESULTS/'s11_2_q0_transfer.csv',transfer)

def cases():
    out=[]
    def add(q,**kw):
        c=dict(q=q,borne='vo',mode='ohm',relay=1,power=1,body=0,rail=1,source=.001,tap=1,phase=0,grid=.5,arc=1,idss=.007,vp=1.6,ron=700,temp=25,stimulus='mains',amplitude=230,frequency=60,stop=1.,step=50e-6,remove=10.,load=0,zbv=5.6,macro='reduced')
        c.update(kw);out.append(c)
    for temp in (0,25,70):
        for ids in (.007,.021):
            for vp in (1.6,2.7):
                for rail in (.98,1,1.02):
                    for phase in (0,90):
                        add('Q3',temp=temp,idss=ids,vp=vp,rail=rail,phase=phase)
                        for body in (0,1):
                            add('Q4',temp=temp,idss=ids,vp=vp,rail=rail,phase=phase,power=0,source=0,body=body)
    # Off voltage path, actual unpowered relay open.
    for body in (0,1):
        for rail in (.98,1,1.02):
            add('Q4',mode='v',relay=0,source=0,power=0,body=body,rail=rail,tap=0)
    for grid in (.5,1,2):
        for arc in (1,2,3):
            for phase in (0,30,60,90,120,150):
                for rail in (.98,1,1.02):
                    add('Q5',borne='a',mode='a',relay=0,source=0,tap=4,grid=grid,arc=arc,phase=phase,rail=rail,stop=.02,step=1e-7)
    for rail in (.98,1,1.02):
        for source in (.001,.0001):
            for ids,vp in ((.007,1.6),(.007,2.7),(.021,1.6),(.021,2.7)):
                add('Q1',mode='diode',stimulus='sweep',source=source,rail=rail,idss=ids,vp=vp,macro='full',stop=.02,step=10e-6)
        for source,load in ((.2e-6,20e6),(1e-6,2e6)):
            add('Q1',mode='leak',stimulus='load',source=source,load=load,rail=rail,macro='full',stop=.05,step=10e-6)
    for amp in (-4000,4000,-8000,8000):
        for mode,borne,relay,tap in (('ohm','vo',1,1),('v','vo',0,0),('a','a',0,4)):
            for ids,vp in ((.007,1.6),(.021,2.7)):
                for rail in (.98,1,1.02):
                    add('Q6',mode=mode,borne=borne,relay=relay,tap=tap,source=.001 if relay else 0,amplitude=amp,stimulus='esd',stop=10e-6,step=1e-9,idss=ids,vp=vp,rail=rail)
    for temp in (0,25,70):
        for ids in (.007,.021):
            for vp in (1.6,2.7):
                add('Q7',temp=temp,idss=ids,vp=vp,remove=10.,stop=11.,load=650,stimulus='recovery')
    return out

def name(c):
    return (f"{c['q']}_{c['borne']}_{c['mode']}_relay{c['relay']}_never_rs47_rlim700_pwr{c['power']}_body{c['body']}_rail{c['rail']}_i{c['source']}_tap{c['tap']}_ph{c['phase']}_ids{c['idss']}_vp{c['vp']}_ron{c['ron']}_t{c['temp']}_grid{c['grid']}_arc{c['arc']}_{c['stimulus']}_amp{c['amplitude']}_stop{c['stop']}_{c['macro']}").replace('.','d').replace('-','m')

def deck(c):
    base=(HERE/'comun/dmm_bloque1_o2.inc').read_text(encoding='utf-8')
    if c['macro']=='reduced':
        excluded=('Xm','Bsel','Vhead ','Vsense ','Ccontrol ','Rcontrol ','Berror ','Bgate ','Mpass ','Dblk ', 'Vamp ','Eampp ','Eampn ','Ecalc ','Xamp ','Eout ','Xphysical ','Cphysical','Rloadp ','Rloadn ')
        base='\n'.join(s for s in base.splitlines() if not s.startswith(excluded))
        red=(HERE/'comun/dmm_reducido_s11_1.inc').read_text(encoding='utf-8')
        red=red.replace('Xh6 n2 rp rn PINHC','Xh6 0 rp rn PINHC').replace('Xh4 shunt rp rn PINHC','Xh4 bin rp rn PINHC')
        for a,b in (('Bsource msource n2','Bsource msource bp'),('Dmosbody n2 msource','Dmosbody bp msource'),('Cmosgd ms n2','Cmosgd ms bp'),('Cmosds n2 msource','Cmosds bp msource')):red=red.replace(a,b)
        red+='\nDblk bp n2 BAV199\n'
        if not c['power']:red=red.replace('Riqother rp rn {9.8/(.003-2*415u-2*550u-16u)}','* External residual load disconnected when off.')
        node={0:'x0',1:'x1',2:'x2',4:'bin',5:'x5'}.get(c['tap'],'0')
        base+=red+f'\nRselected {node} mux 60\n'
    lines=[f'* {name(c)}',f'* STATE {json.dumps(c,sort_keys=True)}',f'.include "{HERE / "comun/bss126_s11_2.inc"}"',
        f'.param RSER=47 POWER={c["power"]} RAIL={c["rail"]} BODYCASE={c["body"]} TAP={c["tap"]} ISOURCE={c["source"]} ARC={c["arc"]} IDSS={c["idss"]} VP={c["vp"]} RON={c["ron"]} TC={c["temp"]} RLIM={RLIM} ZBV={c["zbv"]}']
    if c['macro']=='full':lines += [f'.include "{MODELS / "74HC4051/hc_tnomi.cir"}"',f'.include "{MODELS / "OPA2188/OPAx188.LIB"}"']
    lines += [base,f'.temp {c["temp"]}',f'Brc rc 0 V={c["relay"]}']
    target='vin' if c['borne']=='vo' else 'ain';other='ain' if target=='vin' else 'vin'
    if c['stimulus'] in ('mains','recovery'):
        lines += [f'Bstim gen 0 V=if(time<{c["remove"]},{230*math.sqrt(2):.15g}*sin(2*pi*60*time+{math.radians(c["phase"]):.15g}),0)',f'Rgrid gen {target} {c["grid"] if target=="ain" else "1u"}']
        if c['stimulus']=='recovery':
            lines[-1]='Rgrid gen gun 1u'
            lines += ['Sremove gun vin ctremove 0 RELAY','Bremove ctremove 0 V=if(time<10,1,0)',f'Rtestload vin 0 {c["load"]}']
    elif c['stimulus']=='sweep':lines += ['Vdut vin 0 PWL(0 0 .02 4.5)']
    elif c['stimulus']=='load':lines += [f'Rtestload vin 0 {c["load"]}']
    else:
        lines += [f'Cesd charged 0 150p IC={c["amplitude"]}',f'Resd charged gun {330 if abs(c["amplitude"])==4000 else 630}',f'Sesd gun {target} fire 0 RELAY','Vfire fire 0 PULSE(0 1 100n 1p 1p 1 2)',f'.ic V(charged)={c["amplitude"]}']
    lines += [f'Rother {other} 0 1G','.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1',f'.ic V(rp)={4.9*c["rail"]*c["power"]} V(rn)={-4.9*c["rail"]*c["power"]} V(qfus)=0','.save V(*) I(*)',f'.tran 0 {c["stop"]} 0 {c["step"]}']
    if c['macro']=='reduced':
        lines += ['.save '+ ' '.join(f'I({pin}:{diode})' for pin in ('xh0','xh1','xh2','xh3','xh4','xh5','xh6','xh7','xhz','xopi','xopn','xtlvi','xtlvn') for diode in ('dhi','dlo'))]
    prefix=name(c).lower()
    def meas(n,cmd):lines.append(f'.meas tran {prefix}__{n} {cmd}')
    meas('span_max','MAX V(rp,rn)');meas('terminal_final',f'FIND V({target}) AT {c["stop"]}')
    for part,a,b,cur in (('fet1','ld1','s1','Vlf1'),('fet2','ld2','s2','Vlf2')):
        meas(part+'_vds',f'MAX abs(V({a},{b}))');meas(part+'_p',f'AVG V({a},{b})*I({cur})');meas(part+'_e',f'INTEG V({a},{b})*I({cur})')
    meas('lim_peak','MAX abs(I(Vlf1))');meas('fuse_q','MAX V(qfus)')
    if c['q']=='Q5':meas('fuse_open','WHEN V(qfus)=6.7*'+str(c['arc'])+' RISE=1')
    lines += ['.end',''];return '\n'.join(lines)

def raw(path):
    with path.open('rb') as f:h=f.read(50000)
    enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8';mark='Binary:\n'.encode(enc);off=h.find(mark)
    if off<0:raise ValueError('No binary raw')
    hdr=h[:off].decode(enc);nv=int(re.search(r'No. Variables:\s*(\d+)',hdr)[1]);npnt=int(re.search(r'No. Points:\s*(\d+)',hdr)[1]);names=[m[1].lower() for m in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hdr,re.M)]
    off+=len(mark);cnt=min(npnt,(path.stat().st_size-off)//(8*nv))
    arr=np.memmap(path,dtype='<f8',mode='r',offset=off,shape=(cnt,nv))
    return {n:arr[:,i] for i,n in enumerate(names)}

def audit(path,c):
    d=raw(path);t=np.abs(d['time']);t=np.array(t);n=len(t)
    if n<2:raise ValueError('raw fewer than2 points')
    def v(x):return d.get('v('+x+')',np.zeros(n)) if x!='0' else np.zeros(n)
    def cur(x):return d.get('i('+x.lower()+')',np.zeros(n))
    def integ(y):return float(np.trapezoid(y,t))
    r=dict(raw_complete=bool(t[-1]>=c['stop']-max(1e-9,c['stop']*1e-7)),observed_stop_s=float(t[-1]),points=n,maxstep_s=float(np.max(np.diff(t))))
    for node in ('vin','ain','n1','n2','bin','mux','x0','x1','x2','x5','rp','rn','bp','msource'):
        r[node+'_max']=float(np.max(v(node)));r[node+'_min']=float(np.min(v(node)))
    r['span_max']=float(np.max(v('rp')-v('rn')))
    for node in ('mux','bin','x0','x1','x2','x5','bp','msource'):
        r[node+'_rail_excess']=float(np.max(np.maximum(v(node)-v('rp'),v('rn')-v(node))))
    currents=['Vlf1','Vlf2','Vsense','Dblk','D2p','D2n','Dzp','Dzn','Dbr1','Dbr2','Dbr3','Dbr4','Vfs','Rshunt','Rb']
    for part in currents:
        y=cur(part);r[part.lower()+'_peak_A']=float(np.max(np.abs(y)));r[part.lower()+'_i2t_A2s']=integ(y*y)
    for i,a,b in ((1,'ld1','s1'),(2,'ld2','s2')):
        vv=v(a)-v(b);yy=cur('Vlf'+str(i));p=vv*yy
        r[f'fet{i}_vds_V']=float(np.max(np.abs(vv)));r[f'fet{i}_vgs_V']=float(np.max(np.abs(v('s2' if i==1 else 's1')-v(b))))
        r[f'fet{i}_ppeak_W']=float(np.max(p));r[f'fet{i}_E_sim_J']=integ(p)
        if c['q'] in ('Q3','Q4') and r['raw_complete']:
            start=c['stop']-5/60;mask=t>=start;cy=t[mask];py=p[mask]
            mean=float(np.trapezoid(py,cy)/(cy[-1]-cy[0]));extra=mean*(10-c['stop'])
            r[f'fet{i}_P_period_W']=mean;r[f'fet{i}_E_extrap_J']=extra;r[f'fet{i}_E10_J']=integ(p)+extra
            r[f'fet{i}_Tj_est_C']=c['temp']+250*(integ(p)+extra)/10
            periods=[]
            for j in range(5):
                a0=c['stop']-(j+1)/60;b0=c['stop']-j/60;m=(t>=a0)&(t<=b0)
                periods.append(float(np.trapezoid(p[m],t[m])/(t[m][-1]-t[m][0])))
            r[f'fet{i}_period_spread']=float(np.ptp(periods)/max(abs(mean),1e-12))
    for part,a,b in (('Rprot1','vin','p1'),('Rprot2','p1','p2'),('Rprot3','p2','x0'),('Rdiv1','vin','d1'),('Rdiv2','d1','d2'),('Rdiv3','d2','x1'),('Rdiv4','x1','x2'),('Rdiv5','x2','0'),('Rc1','vin','c1'),('Rc2','d1','c2'),('Rc3','d2','c3'),('Rs','n1','n2'),('Rlim','s1','s2'),('Rb','shunt','bin'),('Rwarn','ain','x5'),('Rshunt','shunt','0')):
        vv=v(a)-v(b);p=vv*cur(part);r[part.lower()+'_V']=float(np.max(np.abs(vv)));r[part.lower()+'_E_sim_J']=integ(p);r[part.lower()+'_Pavg_W']=integ(p)/(t[-1]-t[0])
    for part,a,b in (('D2p','n2','rp'),('D2n','0','n2'),('Dblk','bp','n2'),('Dzp','0','rp'),('Dzn','rn','0')):
        r[part.lower()+'_E_sim_J']=integ((v(a)-v(b))*cur(part))
    injp=cur('D0p')+cur('D1p')+cur('D2p')+cur('D5p')
    injn=cur('D0n')+cur('D1n')+cur('D5n')
    # Actual internal clamps from raw, including HC and OPA and TLV.
    for key in d:
        if key.endswith(':dhi)'):injp=injp+d[key]
        if key.endswith(':dlo)'):injn=injn+d[key]
    r['railp_injection_peak_A']=float(np.max(injp));r['railn_injection_peak_A']=float(np.max(injn))
    for pin in ('xh0','xh1','xh2','xh4','xh5','xhz','xopi','xopn','xtlvi','xtlvn'):
        r[pin+'_clamp_peak_A']=max([float(np.max(np.abs(d[k]))) for k in d if (k.startswith('i('+pin+':') or k.startswith('i(d:'+pin+':')) and (':dhi)' in k or ':dlo)' in k)] or [float('nan')])
    if c['q']=='Q5':
        q=v('qfus');idx=np.flatnonzero(v('fc')<=-.001);r['fuse_open_s']=float(t[idx[0]]) if len(idx) else None
        ix=np.flatnonzero(q>=6.7*(1-1e-5));r['fuse_melt_s']=float(t[ix[0]]) if len(ix) else None
        r['fuse_q_final_A2s']=float(q[-1]);r['fuse_final_A']=float(cur('Vfs')[-1]);r['prospective_rms_A']=230/c['grid']
        if len(idx):r['postopen_peak_A']=float(np.max(np.abs(cur('Vfs')[t>t[idx[0]]+1e-6])))
    if c['q']=='Q1':
        r['source_final_A']=float(cur('Vsense')[-1]);r['terminal_final_V']=float(v('vin')[-1])
        if c['stimulus']=='sweep':
            mask=(cur('Vsense')>=.99*c['source'])&(t>.002)
            r['compliance99_V']=float(np.max(v('vin')[mask])) if np.any(mask) else None
        else:
            r['bav_leak_A']=float((cur('D2p')-cur('D2n'))[-1]);r['bav_added_ppm']=abs(r['bav_leak_A'])/c['source']*1e6
    if c['q']=='Q7':
        ref=float(v('n2')[-1]);mask=t>=10.;err=np.abs(v('n2')-ref);bad=np.flatnonzero(mask&(err>100e-6))
        lastbad=float(t[bad[-1]]) if len(bad) else 10.
        r['recovery_onecount_s']=max(lastbad-10,0);r['recovery_reference_V']=ref;r['recovery_end_drift_V']=float(np.ptp(v('n2')[t>10.9]))
    return r

def run(c,args):
    ident=name(c);p=JOBS/(ident+'.cir');content=deck(c)
    digest=hashlib.sha256((content+Path(__file__).read_text(encoding='utf-8')+(HERE/'comun/bss126_s11_2.inc').read_text()+''.join(old.read_text(MODELS/x) for x in ('OPA2188/OPAx188.LIB','74HC4051/hc_tnomi.cir'))).encode()).hexdigest()
    stamp=p.with_suffix('.json')
    if args.resume and stamp.exists():
        rec=json.loads(stamp.read_text());
        if rec.get('signature')==digest and rec.get('status')=='ok':return dict(rec,reused=True)
    p.write_text(content,encoding='utf-8');start=time.perf_counter();status='ok';code=None
    for suffix in ('.log','.raw','.op.raw'):
        pp=p.with_suffix(suffix)
        if pp.exists():pp.unlink()
    try:
        proc=subprocess.Popen([str(LT),'-b',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        code=proc.wait(timeout=300)
        if code:status='error'
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);proc.wait();status='timeout'
    values,log=old.parse_log(p.with_suffix('.log'))
    if not values or 'Fatal Error' in log:status='error' if status=='ok' else status
    rec=dict(c,id=ident,status=status,returncode=code,elapsed_s=time.perf_counter()-start,signature=digest,**values)
    try:
        rec.update(audit(p.with_suffix('.raw'),c))
        if not rec['raw_complete'] and status=='ok':rec['status']='incomplete'
    except Exception as ex:
        rec['raw_error']=str(ex)
        if status=='ok':rec['status']='audit_error'
    if not args.keep_raw:
        for suffix in ('.raw','.op.raw'):
            pp=p.with_suffix(suffix)
            if pp.exists():pp.unlink()
    stamp.write_text(json.dumps(rec,indent=2),encoding='utf-8')
    with LOCK:
        with (RESULTS/'s11_2_attempts.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
    return rec

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');ap.add_argument('--resume',action='store_true');ap.add_argument('--preflight',action='store_true');ap.add_argument('--build',action='store_true');ap.add_argument('--keep-raw',action='store_true');ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10)
    args=ap.parse_args();JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True);build()
    if args.build:return 0
    allcases=cases();priority=('Q3','Q5','Q4','Q1','Q6','Q7');allcases.sort(key=lambda c:priority.index(c['q']))
    if args.only:allcases=[c for c in allcases if c['q'] in args.only]
    if args.preflight:allcases=[allcases[0]]
    elif args.smoke:allcases=[next(c for c in allcases if c['q']==q) for q in priority if any(c['q']==q for c in allcases)]
    start=time.perf_counter();records=[]
    with cf.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(run,c,args) for c in allcases]
        for fut in cf.as_completed(futures):
            r=fut.result();records.append(r)
            if len(records)%10==0 or args.smoke or args.preflight or r['status']!='ok':print(f'{len(records)}/{len(allcases)} {r["q"]} {r["status"]} {r["elapsed_s"]:.3f}s',flush=True)
    prefix='preflight' if args.preflight else 'smoke' if args.smoke else 'campaign'
    p=RESULTS/f's11_2_{prefix}.csv';writecsv(p,sorted(records,key=lambda r:r['id']))
    summary=dict(total=len(records),ok=sum(r['status']=='ok' for r in records),reused=sum(r.get('reused',False) for r in records),elapsed_s=time.perf_counter()-start,workers=args.workers,timeout_s=300,rlim_ohm=RLIM,rlim_status='diagnostic_only_no_guaranteed_solution',csv=str(p))
    p.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)
    return 0 if summary['ok']==summary['total'] else 1

if __name__=='__main__':raise SystemExit(main())
