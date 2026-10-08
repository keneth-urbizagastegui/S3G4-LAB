"""S12: LTspice campaign; no changes to earlier campaigns or manufacturer files.
AC/noise mux uses datasheet lumped model (NXP is transient-only).
--resume validates deck, executor, include and model hashes. 900s timeout.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, csv, hashlib, json, math, os, re, subprocess, time
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
import ejecutar_s11_4 as protection
from ejecutar_s11_2 import writecsv

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
MODELS=Path(os.environ.get('S3G4_MODELS',ROOT/'Simulation_LTSpice/models'))
LT=Path(os.environ.get('S3G4_LTSPICE',Path.home()/'AppData/Local/Programs/ADI/LTspice/LTspice.exe'))
JOBS=HERE/'S12'; RESULTS=HERE/'resultados'
PRIORITY=('E4','E1','E2','E3','E5','E6','E7','C2','C3','Q0')
RANGES=((.2,0,10.1,10e-6),(2,0,1,100e-6),(20,1,1,1e-3),(50,2,1,.01))

def raw(path):
    with path.open('rb') as f:h=f.read(50000)
    enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8';mark='Binary:\n'.encode(enc);off=h.find(mark)
    if off<0:raise ValueError('binary raw missing')
    hdr=h[:off].decode(enc);nv=int(re.search(r'No. Variables:\s*(\d+)',hdr)[1]);n=int(re.search(r'No. Points:\s*(\d+)',hdr)[1]);names=[m[1].lower() for m in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hdr,re.M)]
    off+=len(mark);complex_data='Flags: complex' in hdr
    dt='<c16' if complex_data else '<f8';width=16 if complex_data else 8
    count=min(n,(path.stat().st_size-off)//(width*nv))
    if count!=n:raise ValueError(f'incomplete raw {count}/{n}')
    arr=np.memmap(path,dtype=dt,mode='r',offset=off,shape=(count,nv))
    return {name:arr[:,i] for i,name in enumerate(names)}

def ident(c):
    aliases=dict(amp='a',gain='g',kind='k',leak='i',model='m',q='q',rail='r',sel='x',stop='s',temp='t',tmux='ron',unit='u',charge='cq',extra='cp')
    def fmt(v):return f'{v:.6g}' if isinstance(v,(int,float)) else str(v)
    result='_'.join(f'{aliases.get(k,k)}{fmt(v)}' for k,v in sorted(c.items()) if k not in ('params','base'))
    if 'base' in c:
        b=c['base'];result+=f'_p{b["power"]}b{b["body"]}k{b["relay"]}dc{b["gdc"]}ph{b["phase"]}'
    return result.replace('.','d').replace('-','m').replace('+','p')

def cases(n=200):
    out=[]
    def add(q,kind,**kw):
        c=dict(q=q,kind=kind,sel=0,gain=1,rail=4.9,temp=23,amp=.1,unit=0,tmux=60,leak=0,model='192',stop=.006)
        c.update(kw);out.append(c)
    for model in ('192','188'):
        for g in (1,10.1):
            add('E4','cm',gain=g,model=model)
            add('E4','recover',gain=g,model=model,amp=4)
    rng=np.random.default_rng(12082026)
    for unit in range(n):
        p={k:float(v*rng.uniform(.999,1.001)) for k,v in dict(R1A=1.5e6,R1B=1.5e6,R2A=1.5e6,R2B=1.5e6,R3A=1.5e6,R3B=1.5e6,RLOW=910e3,RBOT=100e3,RF=91e3,RG=10e3).items()}
        p.update({k:float(v*rng.uniform(.95,1.05)) for k,v in dict(CT1=100e-12,CT2=100e-12,CT3=100e-12,C2=330e-12,C3=3e-9).items()})
        p.update(CPRE=float(3e-12*rng.uniform(.7,1.3)),CZ=float(25e-12*rng.uniform(.7,1.3)),CPCB=float(3e-12*rng.uniform(.7,1.3)),RON=float(70*rng.uniform(.7,1.3)))
        for fs,sel,g,lsb in RANGES:add('E1','ac',sel=sel,gain=g,amp=fs,unit=unit,params=p)
    for fs,sel,g,lsb in RANGES:
        for temp in (18,23,28):add('E2','dc',sel=sel,gain=g,amp=fs,temp=temp,leak=1e-9*2**((temp-23)/10))
        for charge in (0,5e-12):add('E3','zero',sel=sel,gain=g,amp=fs,charge=charge,stop=.008)
    for g in (1,10.1):
        for ron in (60,400):
            add('E5','loop',gain=g,tmux=ron)
            add('E5','gain',gain=g,tmux=ron,amp=.2,stop=.004)
    # Reuse exact S11.4 reduced protection decks; new six-piece divider only.
    for c in protection.cases():
        if c['q']=='T2' and c['mode']=='v' and c['amplitude'] in (-4000,4000,-8000,8000):
            out.append(dict(q='E6',kind='protection',base=c,sel=c['tap'],gain=1,rail=4.9*c['rail'],temp=25,amp=c['amplitude'],unit=len(out),tmux=60,leak=0,model='reduced',stop=c['stop']))
        elif c['q']=='T3' and c['power']==1 and c['rail']==1 and c['phase']==0:
            for amp in (230,253):out.append(dict(q='E6',kind='protection',base=dict(c,amplitude=amp),sel=c['tap'],gain=1,rail=4.9,temp=25,amp=amp,unit=len(out),tmux=60,leak=0,model='reduced',stop=c['stop']))
    for fs,sel,g,lsb in (RANGES[0],RANGES[2]):add('E7','noise',sel=sel,gain=g,amp=fs)
    for sel,g,fs in ((0,1,2),(1,1,20)):
        for cp in ((-10,0,10) if sel==0 else (-20,0,20)):add('C2','ac',sel=sel,gain=g,amp=fs,extra=cp)
    for voltage in (-2,-1,0,1,2):add('C3','cap',amp=voltage,stop=20e-6)
    for amplitude in (.2,2):add('C3','sine',amp=amplitude,stop=.0025)
    for kind in ('cm','loop'):add('Q0',kind)
    return sorted(out,key=lambda c:PRIORITY.index(c['q']))

def header(c):
    model='OPA2192/OPAx192.LIB' if c['model']=='192' else 'OPA2188/OPAx188.LIB'
    return f'* {ident(c)}\n.include "{MODELS/model}"\n.include "{MODELS/"74HC4051/hc_tnomi.cir"}"\n.temp {c["temp"]}\n.options plotwinsize=0 numdgt=15 threads=1 method=gear solver=alt reltol=.001 cshunt=1f\nVp vp 0 {c["rail"]}\nVn vn 0 {-c["rail"]}\n'

def deck(c):
    name=ident(c).lower();k=c['kind'];g=c['gain']
    if k=='protection':
        text=protection.deck(c['base'])
        text=text.replace('Cin a 0 9.5p','Cin a 0 6.4p').replace('Copdiff ampin out 6p','Copdiff ampin out 1.6p')
        text=text.replace('2*415u','2*1m')
        for i,a,b in ((1,'vin','d1'),(2,'d1','d2'),(3,'d2','x1')):
            text=text.replace(f'Rdiv{i} {a} {b} 3Meg',f'Rdiv{i}a {a} mid{i} 1.5Meg\nRdiv{i}b mid{i} {b} 1.5Meg')
        text=text.replace('Rdiv4 x1 x2 900k','Rdiv4 x1 x2 910k')
        text=re.sub(r'^\.meas .*$','',text,flags=re.M)
        text=text.replace('.save ','.save V(mid1) V(mid2) V(mid3) ',1)
        extra='\n'.join(f'.meas tran {name}__r{i}{s}_v MAX abs(V({a},{b}))' for i,x,y in ((1,'vin','d1'),(2,'d1','d2'),(3,'d2','x1')) for s,a,b in (('a',x,f'mid{i}'),('b',f'mid{i}',y)))
        extra+='\n'+ '\n'.join(f'.meas tran {name}__{part}_v MAX abs({"V("+a+")" if b=="0" else "V("+a+","+b+")"})' for part,a,b in (('r910k','x1','x2'),('r100k','x2','0'),('c100p1','c1','d1'),('c100p2','c2','d2'),('c100p3','c3','x1')))
        return re.sub(r'^\.end\s*$',lambda m:extra+'\n.end',text,flags=re.M)
    h=header(c)
    if k=='cap':
        h+=f'Vctl ctl 0 0\nVy y 0 PWL(0 {c["amp"]} 2u {c["amp"]} 2.1u {c["amp"]+.01} 20u {c["amp"]+.01})\nVz z 0 PWL(0 {c["amp"]} 2u {c["amp"]} 2.1u {c["amp"]+.01} 20u {c["amp"]+.01})\nXsw ctl y z vn vp 0 SWI1\nVoff off 0 4.9\n'
        h+='\n'.join(f'Xoff{i} off 0 z vn vp 0 SWI1' for i in range(7))+'\n'
        h+=f'.tran 0 20u 0 2n\n.save V(z) V(y) I(Vy) I(Vz)\n.meas tran {name}__zmax MAX V(z)\n.end\n'
        return h
    if c['q']=='Q0':
        if k=='cm':
            return h+f'Vin src 0 0\nVs src inp 0\nXamp inp out vp vn out OPAx192\nRl out 0 10k\n.dc Vin -4.5 4.5 .05\n.save V(src) V(out) I(Vs) I(Vp) I(Vn)\n.meas dc {name}__ib FIND I(Vs) AT=0\n.meas dc {name}__out FIND V(out) AT=1\n.end\n'
        return h+f'Vin inp 0 0\nXamp inp inv vp vn out OPAx192\nRf out inv 1T\nLf out inv 1T\nCi inv 0 1T\nVtest inv 0 AC 1\nRl out 0 10k\nCl out 0 10p\n.ac dec 100 100 100Meg\n.save V(out)\n.meas ac {name}__unity WHEN mag(V(out))=1 FALL=1\n.end\n'
    body=(HERE/'comun/dmm_bloque2.inc').read_text(encoding='utf-8')
    body=body.replace('OPAx192','OPAx188') if c['model']=='188' else body
    p=dict(SEL=c['sel'],GAIN=g,MUXAC=int(k not in ('zero','recover','gain','sine')),RTMUX=c['tmux'],LEAK=c['leak'])
    p.update(c.get('params',{}))
    if not p['MUXAC']:
        mux='\n'.join(f'X{i} ctl{min(i,4)} {("x0","x1","x2","0","0","0","0","0")[i]} mux vn vp 0 SWI1' for i in range(8))
        body=re.sub(r'\* BEGIN_MUX.*?\* END_MUX',mux,body,flags=re.S)
    if c.get('extra',0)<0:p['CZ']=25e-12+c['extra']*1e-12
    for key,val in p.items():body=re.sub(r'\b'+key+r'=[^\s]+',f'{key}={val:.15g}',body)
    h+=body+'\n'
    if k in ('cm','dc','ac','noise','loop'):
        h+=f'Rsel {("x0","x1","x2","0")[c["sel"]]} mux {{RON}}\n'
    h+=f'Cextra mux 0 {max(c.get("extra",0),0)*1e-12}\n'
    if c.get('extra',0)<0:h=h.replace('CZ=25p',f'CZ={25e-12+c["extra"]*1e-12}')
    h+=f'Vgain1 gain1 0 {int(g==1)}\nVgain10 gain10 0 {int(g>1)}\n'
    if k in ('zero','recover','gain','sine'):
        for i in range(5):
            selected=c['sel']==i
            if k=='zero' and i in (c['sel'],3):value=f'PULSE({0 if i==3 else 4.9} {4.9 if i==3 else 0} {1e-3 if i==3 else 1.002e-3} 1u 1u 1 2)'
            else:value=str(0 if selected else 4.9)
            h+=f'Vctl{i} ctl{i} 0 {value}\n'
    if k=='cm':
        h+='Vin vin 0 0\n.dc Vin 0 4.5 .025\n.save V(vin) V(out) V(mux)\n'
        h+=f'.meas dc {name}__out4 FIND V(out) AT=4\n'
    elif k=='dc':
        h+='Vin vin 0 0\n.dc Vin -'+str(c['amp'])+' '+str(c['amp'])+' '+str(c['amp']/10)+'\n.save V(vin) V(out) V(mux)\n'
        h+=f'.meas dc {name}__out0 FIND V(out) AT=0\n'
    elif k in ('ac','noise'):
        h+='Vin vin 0 0 AC 1\n.save V(out) V(vin)\n'
        if k=='ac':
            h+='.ac dec 60 .1 100k\n'
            for f in (.1,40,100,1000,20000):h+=f'.meas ac {name}__g{str(f).replace(".","d")} FIND mag(V(out)) AT={f}\n'
        else:h+=f'.noise V(out) Vin dec 80 .1 100k\n.meas noise {name}__integrated INTEG V(onoise)\n'
    elif k=='loop':
        h=h.replace('Xamp mux inv','Xamp mux test')
        h+='Vin vin 0 0\nVtest test inv DC 0 AC 1\n.ac dec 100 100 100Meg\n.save V(inv) V(test)\n'
        h+=f'.meas ac {name}__cross WHEN mag(-V(inv)/V(test))=1 FALL=1\n'
    else:
        if k=='recover':h+='Vin vin 0 PULSE(4 .1 1m 1n 1n 1 2)\n'
        elif k=='sine':h+=f'Vin vin 0 SINE(0 {c["amp"]} 20k)\n'
        else:h+=f'Vin vin 0 {c["amp"]}\n'
        if k=='gain':
            h=h.replace(f'Vgain1 gain1 0 {int(g==1)}',f'Vgain1 gain1 0 PULSE({int(g==1)} {int(g!=1)} 1m 1n 1n 1 2)')
            h=h.replace(f'Vgain10 gain10 0 {int(g>1)}',f'Vgain10 gain10 0 PULSE({int(g>1)} {int(g<=1)} 1m 1n 1n 1 2)')
        if k=='zero' and c.get('charge'):h+=f'Icharge 0 mux PULSE(0 {c["charge"]/10e-9} 1m 1p 1p 10n 1)\n'
        h+=f'.tran 0 {c["stop"]} 0 100n\n.save V(out) V(mux) V(vin) I(Vp) I(Vn)\n.meas tran {name}__final FIND V(out) AT={c["stop"]}\n'
        if k=='zero':h+='.options solver=normal method=trap reltol=.003\n'
        if k=='sine':h+=f'.meas tran {name}__rms RMS V(out) FROM=1.5m TO=2.5m\n'
    return h+'.end\n'

def parse_log(path):
    b=path.read_bytes();s=b.decode('utf-16-le' if b'\x00' in b[:100] else 'utf-8',errors='replace')
    vals={}
    for line in s.splitlines():
        if '__' not in line or 'FAIL' in line.upper():continue
        metric=line.split('__',1)[1].split(':',1)[0]
        nums=re.findall(r'(?:=|AT\s+)([+-]?[\d.]+(?:e[+-]?\d+)?)',line,re.I)
        if nums:vals[metric]=float(nums[-1] if metric in ('cross','unity','bw') else nums[0])
    return vals,s

def settle(t,y,start,target,tol):
    bad=np.flatnonzero((t>=start)&(np.abs(y-target)>tol))
    return float(max(t[bad[-1]]-start,0)) if len(bad) else 0.

def audit(c,path):
    d=raw(path);k=c['kind'];r={};q=c['q']
    if k=='protection':return r
    if k in ('ac','loop','noise'):
        # LTspice AC/noise raw uses frequency axis, complex values.
        axis=np.real(np.asarray(d.get('frequency',d.get('freq',[]))))
        if not len(axis):raise ValueError('frequency axis missing: '+str(list(d)[:5]))
        if k=='loop':
            if q=='Q0':loop=-np.asarray(d['v(out)'])
            else:loop=-np.asarray(d['v(inv)'])/np.asarray(d['v(test)'])
            mag=np.abs(loop);ix=np.flatnonzero(mag<=1);i=ix[0] if len(ix) else len(axis)-1
            phase=np.unwrap(np.angle(loop))*180/np.pi
            r.update(unity_hz=float(axis[i]),pm_deg=float(180+phase[i]))
        elif k=='ac':
            y=np.abs(np.asarray(d['v(out)']));f=np.geomspace(40,20000,101);cal=np.array([100,1000,20000]);dc=float(np.interp(.1,axis,y));norm=y/dc
            r['g_dc']=dc;r['droop20_pct']=float((np.interp(20000,axis,norm)-1)*100)
            rng=np.random.default_rng(1200+c['unit']+c['sel']*10000+int(c['gain']*100))
            for sigma in (.0005,.001):
                obs=np.interp(cal,axis,norm)*(1+rng.normal(0,sigma,3));fz=1e15 if c['sel']==0 else 1/(2*np.pi*3e6*100e-12)
                def model(freq,x):return np.exp(x[0])*np.sqrt((1+(freq/fz)**2)/(1+(freq/np.exp(x[1]))**2))
                fit=least_squares(lambda x:model(cal,x)/obs-1,[0,np.log(35000 if c['sel']==0 else 500)],bounds=([-1,np.log(10)],[1,np.log(1e8)]))
                r['residual_'+str(sigma)+'_pct']=float(np.max(np.abs(np.interp(f,axis,norm)/model(f,fit.x)-1))*100)
        else:
            y=np.asarray(d.get('v(onoise)',d.get('onoise',[]))).real
            if not len(y):raise ValueError('noise trace missing '+str(list(d)))
            # 100ms rectangular averaging sinc transfer. Independent autocero doubles variance.
            rms=float(np.sqrt(np.trapezoid(y*y*np.sinc(axis*.1)**2,axis)))
            lsb=100e-6 if c['sel']==1 else 10.1*10e-6
            r.update(noise_rms_V=rms,noise_counts=rms/lsb,noise_autozero_counts=math.sqrt(2)*rms/lsb)
        return r
    t=np.abs(np.asarray(d.get('time',d.get('v(vin)',d.get('v(src)',[])))))
    y=np.asarray(d.get('v(out)',[]));
    if k=='cm':
        x=np.asarray(d.get('v(vin)',d.get('v(src)',[])))
        r.update(out4_V=float(np.interp(4,x,y)),out45_V=float(np.interp(4.5,x,y)))
        if q=='E4':
            # A valid voltage result lies within range +/-2.02V at A output.
            over=x*c['gain']>2.02;r['misleading_points']=int(np.sum(over&(np.abs(y)<=2.02)))
    elif k=='dc':
        x=np.asarray(d['v(vin)']);coef=np.polyfit(x,y,1);r.update(slope=float(coef[0]),offset_V=float(coef[1]))
    elif k=='cap':
        t=np.abs(np.asarray(d['time']));z=np.asarray(d['v(z)']);current=-np.asarray(d['i(vz)'])
        baseline=float(np.median(current[(t>1e-6)&(t<1.9e-6)]));m=(t>=2e-6)&(t<=3e-6)
        r['cap_COM_pF']=float(np.trapezoid(current[m]-baseline,t[m])/.01/1e-12)
    elif k=='sine':
        grid=np.linspace(.0015,.0025,10000,endpoint=False);wave=np.interp(grid,t,y);wave-=np.mean(wave)
        spectrum=np.abs(np.fft.rfft(wave));fundamental=20
        r['thd_pct']=float(np.sqrt(sum(spectrum[fundamental*i]**2 for i in range(2,10)))/spectrum[fundamental]*100)
        r['rms_V']=float(np.sqrt(np.mean(wave**2)))
    else:
        fs=next((x for x in RANGES if x[1]==c['sel'] and x[2]==c['gain']),RANGES[0]);div=1 if c['sel']==0 else 1.01/10.01 if c['sel']==1 else .1/10.01
        tol=fs[3]*div*c['gain']/2
        target=float(np.mean(y[t>c['stop']-.0002]));r['settle_s']=settle(t,y,.001,target,tol);r['target_V']=target
        if k=='zero':
            expected=c['amp']*div*c['gain'];output_lsb=fs[3]*div*c['gain']
            r.update(expected_V=expected,final_error_counts=(target-expected)/output_lsb,settle_to_tail_s=r['settle_s'])
            # Convergence to a wrong tail is NOT successful acquisition settling.
            if abs(target-expected)>tol:r.update(settle_s=None,criterion_pass=False)
            else:r.update(settle_s=settle(t,y,.001,expected,tol),criterion_pass=r['settle_s']<({0:.0001,1:.003,2:.0015}[c['sel']]))
        if k=='gain':
            finalgain=10.1 if c['gain']==1 else 1
            r['settle_s']=settle(t,y,.001,target,finalgain*10e-6/2)
            r['output_halfcount_V']=finalgain*10e-6/2
        if k=='recover':r['recovery_error_V']=target-.1*c['gain']
        if 'i(vp)' in d:r['supply_mW']=float(c['rail']*(np.mean(-d['i(vp)'][t>.002])+np.mean(d['i(vn)'][t>.002]))*1000)
    return r

def run(c,resume=False):
    name=ident({k:v for k,v in c.items() if k!='base'});p=JOBS/(name+'.cir');content=deck(c)
    dependencies=[Path(__file__),HERE/'comun/dmm_bloque2.inc',MODELS/'OPA2192/OPAx192.LIB',MODELS/'OPA2188/OPAx188.LIB',MODELS/'74HC4051/hc_tnomi.cir']
    digest=hashlib.sha256(content.encode()+b''.join(f.read_bytes() for f in dependencies)).hexdigest();stamp=p.with_suffix('.json')
    if resume and stamp.exists():
        r=json.loads(stamp.read_text());
        if r.get('signature')==digest and r['status']=='ok':return dict(r,reused=True)
    p.write_text(content,encoding='utf-8');start=time.perf_counter();r={k:v for k,v in c.items() if k not in ('params','base')};r.update(id=name,signature=digest,status='ok')
    try:
        proc=subprocess.Popen([str(LT),'-b',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:r['returncode']=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);raise TimeoutError('900s')
        values,log=parse_log(p.with_suffix('.log'));r.update(values)
        if r['returncode'] or 'Fatal Error' in log or not values:raise RuntimeError(log[-800:])
        r.update(audit(c,p.with_suffix('.raw')))
    except Exception as e:r.update(status='error',error=str(e))
    r['elapsed_s']=time.perf_counter()-start;stamp.write_text(json.dumps(r,indent=2),encoding='utf-8');return r

def dc_budget():
    """Separate statistical engineering budget, not counted as LTspice runs.
    Uniform independent TCs within +/-25ppm/C; worst signed SOIC drift .5uV/C.
    Leakage doubles per10C (assumption); same aggregate leakage in mux COM.
    """
    rng=np.random.default_rng(1202);n=10000;tc=rng.uniform(-25e-6,25e-6,(n,10));rs=np.array([1.5e6]*6+[910e3,100e3,91e3,10e3]);out=[]
    for fs,sel,g,lsb in RANGES:
        div_nom=1 if sel==0 else 1.01/10.01 if sel==1 else .1/10.01
        source_lsb=lsb*div_nom
        gains=[]
        for dt in (-5,5):
            rr=rs*(1+tc*dt)
            div=1 if sel==0 else (rr[:,6]+rr[:,7])/np.sum(rr[:,:8],axis=1) if sel==1 else rr[:,7]/np.sum(rr[:,:8],axis=1)
            div0=1 if sel==0 else (rs[6]+rs[7])/sum(rs[:8]) if sel==1 else rs[7]/sum(rs[:8])
            gain=1 if g==1 else 1+rr[:,8]/rr[:,9]
            gains.append(np.abs(np.asarray(div/div0*gain/g)-1)*1e6)
        p95=float(np.percentile(np.maximum(*gains),95))
        resistance=99100+70 if sel==0 else 9e6*1.01e6/10.01e6+170 if sel==1 else 100e3*9.91e6/10.01e6+70
        # Gain-switch typical .3nA drift, and amp Ib20pA drift, conservative .5uV/C.
        other=(2.5e-6+20e-12*resistance*(math.sqrt(2)-1)+(.3e-9*91000/g*(math.sqrt(2)-1) if g>1 else 0))/source_lsb
        per_nA=1e-9*resistance*(math.sqrt(2)-1)/source_lsb
        out.append(dict(range_V=fs,gain_p95_ppm=p95,offset_1nA_counts=other+per_nA,leak_max_nA=max(0,(4-other)/per_nA),other_counts=other,leak_model='aggregate_COM_current_double_per10C',population=n))
    writecsv(RESULTS/'s12_dc_budget.csv',out);return out

def main():
    ap=argparse.ArgumentParser()
    for flag in ('smoke','resume','preflight','build','reanalyze'):ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10);ap.add_argument('--n',type=int,default=200)
    a=ap.parse_args();JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True);cs=cases(a.n)
    if a.only:cs=[c for c in cs if c['q'] in a.only]
    if a.preflight:cs=cs[:1]
    elif a.smoke:cs=[next(c for c in cs if c['q']==q) for q in PRIORITY if any(c['q']==q for c in cs)]
    if a.build:
        for c in cs:(JOBS/(ident({k:v for k,v in c.items() if k!='base'})+'.cir')).write_text(deck(c),encoding='utf-8')
        print(json.dumps({'built':len(cs)}));return
    if a.reanalyze:
        rows=[]
        for c in cs:
            p=JOBS/(ident({k:v for k,v in c.items() if k!='base'})+'.cir')
            if p.read_text(encoding='utf-8')!=deck(c):raise ValueError('saved deck changed: '+str(p))
            r=json.loads(p.with_suffix('.json').read_text(encoding='utf-8'));r.update(audit(c,p.with_suffix('.raw')))
            r['reaudited']=True;p.with_suffix('.json').write_text(json.dumps(r,indent=2),encoding='utf-8');rows.append(r)
        label='preflight' if a.preflight else 'smoke' if a.smoke else 'campaign'
        dest=RESULTS/f's12_{label}.csv';writecsv(dest,rows)
        summary=json.loads(dest.with_suffix('.json').read_text());summary['reaudited']=len(rows)
        dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary));return 0
    start=time.perf_counter();rows=[]
    # Complete each priority group before starting the next.
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for q in PRIORITY:
            group=[c for c in cs if c['q']==q]
            for fut in cf.as_completed([pool.submit(run,c,a.resume) for c in group]):rows.append(fut.result())
            if group:print(q,len(group),'ok',sum(r['status']=='ok' for r in rows if r['q']==q),flush=True)
    label='preflight' if a.preflight else 'smoke' if a.smoke else 'campaign'
    dest=RESULTS/f's12_{label}.csv';writecsv(dest,rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),elapsed_s=time.perf_counter()-start,reused=sum(r.get('reused',False) for r in rows),workers=a.workers,timeout_s=900,n_population=a.n)
    dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');dc_budget();print(json.dumps(summary),flush=True)
    return int(summary['total']!=summary['ok'])

if __name__=='__main__':raise SystemExit(main())
