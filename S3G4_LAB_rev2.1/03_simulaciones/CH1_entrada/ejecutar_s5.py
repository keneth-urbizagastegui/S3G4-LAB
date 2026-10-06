"""S5 LTspice campaign. Ten workers; immutable S1-S4; deterministic CSV schema.

Exit 0 means a complete campaign, never electrical acceptance or selection.
S3G4_MODELS and S3G4_LTSPICE are inherited from the S4 runner.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s4 as s4
import sintesis_s5 as synthesis

s3=s4.s3
ROOT,MODELS,PROJECT,LT=s4.ROOT,s4.MODELS,s4.PROJECT,s4.LT
COMPONENTS,IDEAL=synthesis.synthesize()
CANDIDATES=['BE','TR','BU']
SEED=20261003
# Independent uniform draws for R1,R2,C1,C2 of A then B. Paired between candidates.
MC=np.random.default_rng(SEED).uniform(-1,1,(200,8))
PARAMETERS=['R1A','R1B','C1A','C1B','R2A','R2B','C2A','C2B']
write,table=s4.write,s4.table

def csv_write(path,rows,fields=None):
    # Same columns in every invocation, independent of completion order.
    if fields is None:fields=sorted({k for r in rows for k in r})
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='raise')
        w.writeheader();w.writerows(sorted(rows,key=lambda r:str(r.get('id',r.get('candidate','')))))

def case(test,candidate,ix=0,mc=-1,kind='ac',polarity='bipolar',amplitude=0.,freq=0.,section=0):
    c=dict(test=test,candidate=candidate,ix=ix,scale_V_div=s3.SCALES[ix],
           POS=1 if ix<6 else 100,tap=ix%6,mc=mc,kind=kind,polarity=polarity,
           amplitude_V=amplitude,freq_Hz=freq,section=section)
    state=f's{ix:02d}_pos{c["POS"]}_tap{c["tap"]}'
    if test=='G0':
        c.update(ix='NA',scale_V_div='NA',POS='NA',tap='NA')
        state='sna_posna_tapna'
    c['id']=(f'{test}_{candidate}_{state}_dc_mc{mc if mc>=0 else "nom"}'
             f'_{kind}_{polarity}_a{s4.number(amplitude)}_f{s4.number(freq)}_sec{section}').lower()
    return c

def values(c):
    rows=[r for r in COMPONENTS if r['candidate']==c['candidate']]
    v=np.array([x for r in rows for x in [r['R1_Ohm'],r['R2_Ohm'],r['C1_pF']*1e-12,r['C2_pF']*1e-12]])
    if c['mc']>=0:v*=1+MC[c['mc']]*np.array([.01,.01,.05,.05]*2)
    return v

def m(c,mode,name,expr):return s3.meas(c,mode,name,expr)

def filter_lines(c,isolated=False):
    v=values(c);l=[f'.param {k}={x:.17g}' for k,x in zip(PARAMETERS,v)]
    if isolated:
        j=c['section'];n=1 if j==1 else 2
        l += [f'X105A IN ADC1 VP VN IPA105 IMA105 SK_S5 RA={{R{n}A}} RB={{R{n}B}} CF={{C{n}A}} CG={{C{n}B}}']
    else:
        l += ['X105A OUT OA105 VP VN IPA105 IMA105 SK_S5 RA={R1A} RB={R1B} CF={C1A} CG={C1B}',
              'X105B OA105 FILTEROUT VP VN IPB105 IMB105 SK_S5 RA={R2A} RB={R2B} CF={C2A} CG={C2B}']
    return l

def net(c):
    test=c['test']
    if test=='G0':
        l=[f'* S5 isolated {c["id"]}',f'.include "{ROOT/"comun/ch1_comun_s5.inc"}"',
           f'.include "{MODELS/"AD8039/AD8038_ltspice.sub"}"',
           '.param BUFFER_KIND=810','.temp 25','.options numdgt=15 plotwinsize=0 threads=1',
           'VP VP 0 5','VN VN 0 -5','VI IN 0 AC 1']+filter_lines(c,True)
        l += [m(c,'AC','gain_ref','FIND mag(V(ADC1)) AT=1k'),
              '.save V(ADC1) V(IN)','.ac dec 300 1k 200Meg','.end']
        return '\n'.join(l)+'\n'
    old=s4.case('F6' if test=='G5' else 'F2',scope='chain',ix=c['ix'])
    l=s4.base(old)
    l=[x.replace('ch1_comun_s4.inc','ch1_comun_s5.inc') for x in l]
    l+=filter_lines(c)+s4.mid_network(old)+s4.stage(old,1)+['VINLINK FILTEROUT IN1 0']
    amp=c['amplitude_V']
    if test=='G2':
        source=(f'PULSE(0 {amp:.17g} 1u 2n 2n 1 2)' if c['kind']=='step' else
                f'PULSE({-amp:.17g} {amp:.17g} 1u 2n 2n 5u 10u)')
    elif test=='G6':source=f'PULSE(0 {amp:.17g} 1u 10n 10n 10u 1)'
    elif test=='G4':source=f'SINE(0 {amp:.17g} {c["freq_Hz"]:.17g})'
    else:source='AC 1'
    l += [f'Vsrc SRC 0 {source}', 'VLINK SRC BNC 0' if test=='G6' else 'Rsource SRC BNC 50']
    saves=['V(ADC1)','V(BNC)','V(SRC)','V(OUT)','V(OA105)','V(FILTEROUT)',
           'V(IPA105)','V(IMA105)','V(IPB105)','V(IMB105)','V(VM1)',
           'I(X105A:VIP)','I(X105A:VIM)','I(X105B:VIP)','I(X105B:VIM)',
           'I(X105A:VCCP)','I(X105A:VCCN)','I(X105B:VCCP)','I(X105B:VCCN)']
    if test in ['G1','G3']:
        for name,at in [('gain_ref','1k'),('gain_1m','1Meg'),('gain_2m','2Meg'),
                        ('gain_3p25m','3.25Meg'),('gain_4p5m','4.5Meg'),('gain_6p5m','6.5Meg')]:
            l += [m(c,'AC',name,f'FIND mag(V(ADC1)/V(BNC)) AT={at}')]
        l+=['.save '+' '.join(saves),'.ac dec 300 1k 200Meg']
    elif test=='G5':
        l+=[m(c,'NOISE','onoise_100k','FIND V(onoise) AT=100k'),'.noise V(ADC1) Vsrc dec 300 1 3.15Meg']
    else:
        l+=[m(c,'TRAN','adc_min','MIN V(ADC1)'),m(c,'TRAN','adc_max','MAX V(ADC1)'),
            m(c,'TRAN','bnc_peak','MAX abs(V(BNC))')]
        for j,p,n in [('a','IPA105','IMA105'),('b','IPB105','IMB105')]:
            l += [m(c,'TRAN',j+'_diff','MAX abs(V('+p+','+n+'))'),
                  m(c,'TRAN',j+'_ip','MAX abs(I(X105'+j.upper()+':VIP))'),
                  m(c,'TRAN',j+'_im','MAX abs(I(X105'+j.upper()+':VIM))')]
            for rail in ['P','N']:
                l += [m(c,'TRAN',j+'_idle_'+rail.lower(),f'AVG I(X105{j.upper()}:VCC{rail}) FROM=0 TO=0.5u')]
        stop='5u' if test=='G2' and c['kind']=='step' else '30u' if test in ['G2','G6'] else '40u'
        dt='.5n' if test=='G4' else '1n'
        l += ['.save '+' '.join(saves),f'.tran 0 {stop} 0 {dt}']
    return '\n'.join(l+['.end'])+'\n'

def ac_metrics(f,h):
    mag=np.abs(h);db=20*np.log10(mag/mag[0]);ix=np.flatnonzero(db<=-3)
    cutoff=None
    if len(ix) and ix[0]>0:
        j=ix[0];cutoff=float(np.exp(np.interp(-3,db[j-1:j+1][::-1],np.log(f[j-1:j+1])[::-1])))
    r=dict(minus3_Hz=cutoff,gain_ref=float(mag[0]))
    for label,at in [('1m',1e6),('2m',2e6),('3p25m',3.25e6),('4p5m',4.5e6),('6p5m',6.5e6)]:
        r['atten_'+label+'_db']=-float(np.interp(np.log(at),np.log(f),db))
        r['gain_source_'+label]=None
    r['peak_db']=float(db[f<=2e6].max());r['peak_Hz']=float(f[f<=2e6][np.argmax(db[f<=2e6])])
    high=f>4.5e6;ref=-r['atten_4p5m_db']
    r.update(high_max_db=float(db[high].max()),high_max_Hz=float(f[high][np.argmax(db[high])]),
             rebound_excess_db=max(0.,float(db[high].max()-ref)),ac_points=len(f),ac_last_Hz=float(f[-1]))
    gd=-np.gradient(np.unwrap(np.angle(h)),2*np.pi*f)
    band=f<=2e6;r['gd_min_ns']=float(gd[band].min()*1e9);r['gd_max_ns']=float(gd[band].max()*1e9)
    r['gd_variation_ns']=r['gd_max_ns']-r['gd_min_ns']
    return r

def crossing(t,y,level):
    ix=np.flatnonzero(y>=level)
    if not len(ix):return None
    j=int(ix[0])
    return float(t[0]) if j==0 else float(np.interp(level,y[j-1:j+1],t[j-1:j+1]))

def analyze(c,raw,r):
    test=c['test']
    if test in ['G0','G1','G3']:
        f=raw['frequency'];h=raw['v(adc1)']/raw['v(in)' if test=='G0' else 'v(bnc)']
        r.update(ac_metrics(f,h))
        if test=='G0':
            # Fit complex biquad below 10MHz, quantifies the real-model/parasitic shift.
            mask=f<=10e6;w=2j*np.pi*f[mask];hh=h[mask]/h[0]
            matrix=np.column_stack([hh*w*w,hh*w]);target=1-hh
            ab=np.linalg.lstsq(np.r_[matrix.real,matrix.imag],np.r_[target.real,target.imag],rcond=None)[0]
            if ab[0]>0:r.update(fit_f0_Hz=float(1/(2*np.pi*np.sqrt(ab[0]))),fit_Q=float(np.sqrt(ab[0])/ab[1]))
            db=20*np.log10(abs(h/h[0]))
            r.update(isolated_peak_db=float(db.max()),isolated_peak_Hz=float(f[np.argmax(db)]))
        else:
            source=np.abs(raw['v(adc1)']/raw['v(src)'])
            for tag,freq in [('1m',1e6),('2m',2e6)]:r['gain_source_'+tag]=float(np.interp(np.log(freq),np.log(f),source))
        return
    if test=='G5':
        key=next(k for k in raw if 'onoise' in k and 'total' not in k)
        rms=s3.integral_band(raw['frequency'],raw[key].real,3.15e6)
        r.update(noise_uV=rms*1e6,noise_pct_div=100*rms/s4.DIV,noise_trace=key)
        return
    t=raw['time'];y=raw['v(adc1)'];bnc=raw['v(bnc)']
    r.update(bnc_actual_peak_V=float(abs(bnc).max()),last_time_s=float(t[-1]),max_step_s=float(np.diff(t).max()))
    if abs(bnc).max()>4.5+1e-8:raise ValueError('BNC exceeds 4.5V')
    if t[-1]<(5e-6 if test=='G2' and c['kind']=='step' else 30e-6 if test in ['G2','G6'] else 40e-6)-1e-12:raise ValueError('Incomplete transient')
    for j,p,n in [('a','ipa105','ima105'),('b','ipb105','imb105')]:
        r[j+'_differential_V']=float(abs(raw['v('+p+')']-raw['v('+n+')']).max())
        for name in ['vip','vim']:r[j+'_'+name+'_peak_A']=float(abs(raw[f'i(x105{j}:{name})']).max())
    r['u105_idle_power_mW']=sum(5*(r[j+'_idle_p']-r[j+'_idle_n'])*1e3 for j in ['a','b'])
    if test=='G2':
        first=t<.5e-6;plateau=(t>4e-6)&(t<5e-6)
        initial=float(y[first].mean());final=float(y[plateau].mean());delta=final-initial
        mask=(t>=1e-6)&(t<5e-6);ts=t[mask];z=(y[mask]-initial)/delta
        t10=crossing(ts,z,.1);t90=crossing(ts,z,.9)
        r.update(rise_ns=(t90-t10)*1e9 if t90 is not None and t10 is not None else None,
                 overshoot_pct=max(0.,float(z.max()-1)*100),
                 settling_1pct_ns=s3.settled(ts,y[mask],1e-6,final,.01*abs(delta)),
                 step_initial_V=initial,step_final_V=final,step_delta_V=delta)
        if r['settling_1pct_ns'] is not None:r['settling_1pct_ns']*=1e9
        if c['kind']=='square':
            end=6.004e-6;mask=(t>=end)&(t<10.9e-6)
            r['square_fall_settling_ns']=s3.settled(t[mask],y[mask],end,initial,.01*abs(delta))
            if r['square_fall_settling_ns'] is not None:r['square_fall_settling_ns']*=1e9
    elif test=='G6':
        initial=float(y[t<.5e-6].mean());rec=s3.settled(t,y,s3.PULSE_END,initial,.1*s4.DIV)
        r.update(recovery_us=rec*1e6 if rec is not None else None,initial_V=initial,terminal_error_V=float(y[-1]-initial),
                 recovery_band_V=.1*s4.DIV,pulse_end_s=s3.PULSE_END,observation_after_end_us=(t[-1]-s3.PULSE_END)*1e6)
    elif test=='G4':
        ts=np.linspace(20e-6,40e-6,131072,endpoint=False);uniform=np.interp(ts,t,y)
        spec=np.fft.rfft(uniform)/len(ts);bin0=round(c['freq_Hz']*20e-6)
        harms=2*abs(spec[bin0*np.arange(1,10)])
        r.update(thd_pct=100*float(np.linalg.norm(harms[1:])/harms[0]),fundamental_pp_V=float(2*harms[0]),
                 actual_pp_V=float(np.ptp(uniform)),mean_adc_V=float(uniform.mean()),
                 target_pp_V=8*s4.DIV,amplitude_error_pct=100*float(2*harms[0]/(8*s4.DIV)-1))
        for j,v in enumerate(harms,1):r[f'harmonic{j}_V']=float(v)

def simulate(c,work):
    path=work/(c['id']+'.cir');deck=net(c);write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    record=dict(id=c['id'],returncode=0,errors=[],warnings=[]);r=dict(c)
    if c['mc']>=0:
        r['seed']=SEED
        for k,v in zip(PARAMETERS,values(c)):r[k]=float(v)
    try:
        proc=subprocess.run([str(LT),'-b',str(path)],cwd=work,capture_output=True,timeout=3600)
        vals,errors,warnings,_=s3.prior.old.read_log(path.with_suffix('.log'))
        expected={x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        if expected-set(vals):errors.append('Missing measures '+str(sorted(expected-set(vals))))
        record.update(returncode=proc.returncode,errors=errors,warnings=warnings)
        r.update({k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        if not errors and not proc.returncode:analyze(c,s3.raw_read(path.with_suffix('.raw')),r)
    except Exception as exc:record['errors'].append(repr(exc))
    if not record['errors'] and not record['returncode']:
        for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    return (r if not record['errors'] and not record['returncode'] else {}),record

def execute(cases,work):
    rows=[];records=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        futures={pool.submit(simulate,c,work):c for c in cases}
        for f in as_completed(futures):
            c=futures[f]
            try:r,s=f.result()
            except Exception as e:r={};s=dict(id=c['id'],returncode=1,errors=[repr(e)],warnings=[])
            if r:rows.append(r)
            records.append(s)
            if s['errors'] or s['returncode']:print('ERROR',c['id'],s['errors'],flush=True)
            if len(records)%50==0:print('PROGRESS',cases[0]['test'],len(records),'/',len(cases),flush=True)
    return sorted(rows,key=lambda r:r['id']),sorted(records,key=lambda r:r['id'])

def controls():return [case('G0',b,kind='isolated',section=j) for b in CANDIDATES for j in [1,2]]

def jobs(test,smoke,rows):
    if test in ['G1','G5']:return [case(test,b,ix=i,kind='noise' if test=='G5' else 'ac') for b in CANDIDATES for i in ([0,6] if smoke else range(12))]
    if test=='G2':return [case(test,b,ix=i,kind=k,polarity='positive' if k=='step' else 'bipolar',amplitude=s3.SCALES[i]*(1 if k=='step' else 2)) for b in CANDIDATES for i in [0,6] for k in ['step','square']]
    if test=='G3':return [case(test,b,mc=j) for b in CANDIDATES for j in range(3 if smoke else 200)]
    if test=='G6':return [case(test,b,kind='pulse',polarity='negative' if v<0 else 'positive',amplitude=v) for b in CANDIDATES for v in [-4.5,-2,2,4.5]]
    if test=='G4':
        result=[]
        for b in CANDIDATES:
            ac=next(r for r in rows if r['test']=='G1' and r['candidate']==b and r['ix']==0)
            for f,tag in [(1e6,'1m'),(2e6,'2m')]:result.append(case(test,b,kind='sine',freq=f,amplitude=4*s4.DIV/ac['gain_source_'+tag]))
        return result
    raise ValueError(test)

def protected():
    files=[p for p in ROOT.rglob('*') if p.is_file() and not p.is_relative_to(ROOT/'S5') and
           not p.name.startswith('s5_') and p.name not in ['ejecutar_s5.py','sintesis_s5.py','verificar_s5.py','ch1_comun_s5.inc','ACTA_S5.md','RESPUESTA_FINAL_S5.md']]
    # Logs anywhere are operational records, never protected source files.
    files=[p for p in files if p.suffix.lower() not in ['.log','.raw','.db'] and '__pycache__' not in p.parts]
    files += [p for p in MODELS.rglob('*') if p.is_file()]
    context_project=PROJECT if (PROJECT/'ai-context').exists() else MODELS.parents[1]
    files += [context_project/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}

def assess(rows,complete):
    result=[];compare=[];mc_stats=[]
    for b in CANDIDATES:
        by=lambda test:[r for r in rows if r['candidate']==b and r['test']==test]
        ac,step,mc,noise,pulse,thd=[by(t) for t in ['G1','G2','G3','G5','G6','G4']]
        def add(n,ok,value,covered):
            result.append(dict(candidate=b,criterion=f'S5-C{n}',status=('PASA' if ok else 'FALLA') if complete and covered else 'PARCIAL',value=value))
        if ac:
            cuts=[r['minus3_Hz'] for r in ac];valid=all(x is not None and 1.8e6<=x<=2.2e6 for x in cuts)
            add(1,valid,f'{min(x for x in cuts if x is not None)/1e6:.6g}..{max(x for x in cuts if x is not None)/1e6:.6g} MHz; {len(ac)}/12',len(ac)==12)
            peak=max(r['peak_db'] for r in ac);add(3,peak<=.5,f'{peak:.9g} dB',len(ac)==12)
            rebound=max(r['rebound_excess_db'] for r in ac);add(4,rebound<=1e-9,f'exceso {rebound:.9g} dB; max alta {max(r["high_max_db"] for r in ac):.9g} dB',len(ac)==12)
        if mc:
            cuts=np.array([r['minus3_Hz'] if r['minus3_Hz'] is not None else np.nan for r in mc]);fraction=float(np.mean((cuts>=1.8e6)&(cuts<=2.2e6)))
            add(2,fraction>=.95,f'{round(fraction*len(mc))}/{len(mc)} = {100*fraction:.6g}%',len(mc)==200)
            stat=dict(candidate=b,cases=len(mc),seed=SEED,within_pct=100*fraction)
            for key in ['minus3_Hz','peak_db','atten_4p5m_db']:
                x=np.array([r[key] for r in mc],float)
                for label,v in [('min',np.min(x)),('p05',np.percentile(x,5)),('mean',np.mean(x)),('p95',np.percentile(x,95)),('max',np.max(x)),('std',np.std(x,ddof=1))]:stat[key+'_'+label]=float(v)
            mc_stats.append(stat)
        if step:
            rise=[r['rise_ns'] for r in step]
            add(5,all(x is not None and 175*.8<=x<=175*1.2 for x in rise),f'{min(x for x in rise if x is not None):.6g}..{max(x for x in rise if x is not None):.6g} ns',len(step)==4)
        if thd:add(6,max(r['thd_pct'] for r in thd)<=1,f'{max(r["thd_pct"] for r in thd):.9g}%',len(thd)==2)
        if noise:add(7,max(r['noise_pct_div'] for r in noise)<=.45,f'{max(r["noise_pct_div"] for r in noise):.9g}% div; {len(noise)}/12',len(noise)==12)
        if pulse:
            rec=[r['recovery_us'] for r in pulse];diff=max(r[j+'_differential_V'] for r in pulse for j in ['a','b'])
            worst=max([x for x in rec if x is not None],default=math.inf)
            add(8,None not in rec and worst<=1 and diff<=2,f'rec {worst:.9g} us; censurados {rec.count(None)}; diferencial {diff:.9g} V',len(pulse)==4)
        a=next((r for r in ac if r['ix']==0),{});s=next((r for r in step if r['ix']==0 and r['kind']=='step'),{})
        square=next((r for r in step if r['ix']==0 and r['kind']=='square'),{})
        z=dict(candidate=b,minus3_MHz=a.get('minus3_Hz',math.nan)/1e6,
               atten_3p25m_db=a.get('atten_3p25m_db'),atten_4p5m_db=a.get('atten_4p5m_db'),atten_6p5m_db=a.get('atten_6p5m_db'),
               overshoot_pct=s.get('overshoot_pct'),square_overshoot_pct=square.get('overshoot_pct'),rise_ns=s.get('rise_ns'),gd_variation_ns=a.get('gd_variation_ns'),
               noise_max_pct_div=max([r['noise_pct_div'] for r in noise],default=math.nan),
               mc_within_pct=100*fraction if mc else None,thd_max_pct=max([r['thd_pct'] for r in thd],default=math.nan),
               u105_idle_power_mW=s.get('u105_idle_power_mW'))
        compare.append(z)
    return sorted(result,key=lambda r:(CANDIDATES.index(r['candidate']),r['criterion'])),compare,mc_stats

METHOD='''
## Método y dudas

Fuentes leídas: encargo y plan S5; plan, acta y auditoría S4;
DECISIONS del 3 oct; revision_entrada_ch1 §6; canal_rapido_ch1 §6;
models/LEEME. S4.base/stage/mid_network y S3.chain/address se reutilizan
sin modificar sus fuentes. M1, C_F1pF, DAC1.25V, R_IN/R_F10k,
R_OFF8.06k, R_ADC68, C_ADC470p y C_SH5p conservados. U103 protegido
con 470ohm/BAV99; U105 NO lleva protecciones añadidas.
Cada .meas identifica grupo, candidato, escala/POS/tap, caso MC,
estímulo, polaridad y sección reales. Modelos originales salvo G5,
que usa AD8038_ltspice_ruido_hoja en U103 y U105. Modelo AD8038
es el modelo contractual de cada mitad AD8039, no prueba física.

Síntesis: besselap(norm=mag), buttap, TR con pares de polos en orden
Q creciente, media geométrica de módulos/arimética de ángulos.
Se escalan los cuatro polos para -3dB exactos a2MHz contando polos
ideales f_RC=1/(2pi*68*470p) y10.8MHz. No se altera ninguno de los
polos fijos. C2 se recorre en E12 entre47 y220p, C1 se redondea primero
al E12 más cercano y R al E96 más cercano entre499 y2490ohm. Se
minimiza error de Q, luego f0 y se favorece C2 mayor en empate.
Se informa f0/Q por pasivos, y ajuste biquad del AC aislado real con
1p de pista en IN+. No se retoca la síntesis después de la campaña.

G1/G3: 300puntos/década,1kHz..200MHz. H=V(ADC1)/V(BNC), normalizada
a1kHz (acoplo DC). Atenuaciones por interpolación log-frecuencia.
Pico se mide en1k..2MHz; máximo alta frecuencia en>4.5..200MHz.
Retardo de grupo por derivada de fase desenrollada: variación1k..2MHz;
0..1kHz no se simula, se informa esta limitación del barrido contractual.
C4 compara máximo alta frecuencia contra H(4.5MHz), sin ocultar rebote.
G3:200casos/candidato, semilla20261003, numpy default_rng, uniforme
independiente ±1% en cuatro R y±5% en cuatro C del filtro. Mismos
ocho factores por índice entre candidatos (comparación pareada).
Los polos fijos,1p de pista y S1-S4 no se aleatorizan. Distribuciones
de corte/pico/A4.5, componentes reales y factores recuperables en CSV.

G2: escalón1div positivo,2ns; cuadrada100kHz de4div pp,centrada
(±2div),2ns. Dos escalas5mV y0.5V/div. Normalización con signo de
la cadena inversora; subida al primer cruce10/90%; overshoot y última
violación de±1% respecto a meseta4..5us. Resolución<=1ns.
G6: BNC impuesta±2/±4.5V,10us,flancos10ns; recuperación desde final
de bajada11.02us hasta permanecer en±0.1div de la salida inicial;
ventana30us. Se conserva censura si no recupera. Diferencial y ambas
corrientes por U105A/B con sensores ideales0V,sin diodos añadidos.
G4: seno1/2MHz,offset0,DAC1.25; fuente calculada desde G1 para2Vpp
(8div) en pin ADC. THD armónicos2..9,ventana20..40us coherente,
131072puntos interpolados del raw<=0.5ns. Se informa amplitud real.
G5: integral ONOISE1Hz..3.15MHz en pin ADC,por trapecios de densidad
al cuadrado y extremo interpolado; porcentaje sobre0.25V/div.
C_SH5p estático permanece después del pin; no hay kickback S6.
Consumo U105 por sensores de ambos rieles en reposo; incluye macro,
no garantía del consumo real. Corrientes de entrada del AD8038
macro no representan toda la Ib de400nA ni daños por sobrecarga.

Contradicciones conservadas: E17 antiguo menciona Butterworth5º y
pérdidaS3 -0.97dB; contratoS5 exige tres filtros4º activos y usa
S4 real más RC sin cambiar S1-S4. Tablaideal omite la pequeña pérdida
S1-S3; cadena real la incluye. RLOAD1k/CLOAD10p heredados de S3/S4
eran sustitutos de carga; permanecen en U103B además del filtro,
por prohibición de cambiar la cadena. El poloS4 de10.8MHz es una
aproximación ideal para síntesis: la campaña conserva el macromodelo
completo,cargaADC y5p estáticos. Fuentes VREF yDAC ideales no
certifican ruidoREF3325/DAC. No se resuelven discrepancias acta/auditoría
S4 ni se elige candidato. Sin descargas,ni cambios deSTATE/DECISIONS.

## Reejecución

En CH1_entrada: python sintesis_s5.py; python ejecutar_s5.py --controls;
python ejecutar_s5.py --smoke; python ejecutar_s5.py.
En copia: fijar S3G4_MODELS a modelos originales (sólo lectura).
Diez trabajadores desdeG0. CSV con columnas fijas ordenadas y filas
porID; .cir/.log conservados, raw exitosos regenerables eliminados.
Registros bajoS5 (excluido) o fuera deCH1_entrada. HuellasSHA256
antes/después de fuentes/modelos/S1-S4/STATE/DECISIONS.
Código0=ejecución completa,sin implicar aprobación eléctrica.
'''

def report(rows,records,run,prefix):
    out=ROOT/'resultados';complete=not run['smoke'] and not run['controls_only'] and run['exit_code']==0
    criteria,comparison,stats=assess(rows,complete)
    # Build each schema from all generated cases, so interrupted stages retain
    # the same complete schema upon replay; result schema is explicitly saved.
    for test in ['G0','G1','G2','G3','G4','G5','G6']:
        rr=[r for r in rows if r['test']==test];csv_write(out/f'{prefix}_{test.lower()}.csv',rr)
    csv_write(out/f'{prefix}_resultados.csv',rows);csv_write(out/f'{prefix}_criterios.csv',criteria)
    csv_write(out/f'{prefix}_comparativa.csv',comparison);csv_write(out/f'{prefix}_montecarlo.csv',stats)
    csv_write(out/'s5_componentes.csv',COMPONENTS,list(COMPONENTS[0]));csv_write(out/'s5_ideal.csv',IDEAL,list(IDEAL[0]))
    text=f'# ACTA S5 — filtro anti-alias de CH1\n\nCódigo {run["exit_code"]}; {run["simulations"]} simulaciones; {run["elapsed_seconds"]:.3f} s; diez trabajadores; errores {run["errors"]}; advertencias {run["warnings"]}.\n\n'
    if run.get('reused_successful_cases'):
        text+=f'Casos finales verificados={run["simulations"]}; reutilizados con deck idéntico={run["reused_successful_cases"]}; nuevas ejecuciones={run["native_simulations_this_run"]}; intentos nativos acumulados={run["attempts"]}.\n\n'
    if not complete:text+='**Ejecución parcial: sin aceptación de criterios.**\n\n'
    text+='## Síntesis ideal\n\n'+table(IDEAL,list(IDEAL[0]))+'\n\n'
    text+='## Componentes (C1 realimentación, C2 a masa; sección1 Q bajo)\n\n'+table(COMPONENTS,list(COMPONENTS[0]))+'\n\n'
    text+='## Criterios por candidato\n\n'+table(criteria,['candidate','criterion','status','value'])+'\n\n'
    text+='## Comparativa (nominal5mV/div; ruido peor escala)\n\n'+table(comparison,list(comparison[0]))+'\n\n'
    text+='## Monte Carlo\n\n'+table(stats,list(stats[0]) if stats else [])+'\n\n'
    text+='## G0 secciones aisladas reales\n\n'+table([r for r in rows if r['test']=='G0'],['candidate','section','fit_f0_Hz','fit_Q','minus3_Hz','isolated_peak_db','isolated_peak_Hz'])+'\n\n'
    text+='## G1 todas las escalas\n\n'+table([r for r in rows if r['test']=='G1'],['candidate','scale_V_div','minus3_Hz','atten_3p25m_db','atten_4p5m_db','atten_6p5m_db','peak_db','high_max_db','high_max_Hz','rebound_excess_db','gd_variation_ns'])+'\n\n'
    text+='## G2 flancos y cuadrada\n\n'+table([r for r in rows if r['test']=='G2'],['candidate','scale_V_div','kind','overshoot_pct','rise_ns','settling_1pct_ns','square_fall_settling_ns','u105_idle_power_mW'])+'\n\n'
    text+='## G4 gran señal\n\n'+table([r for r in rows if r['test']=='G4'],['candidate','freq_Hz','amplitude_V','fundamental_pp_V','amplitude_error_pct','thd_pct','adc_min','adc_max'])+'\n\n'
    text+='## G5 ruido\n\n'+table([r for r in rows if r['test']=='G5'],['candidate','scale_V_div','noise_uV','noise_pct_div'])+'\n\n'
    text+='## G6 sobrecarga\n\n'+table([r for r in rows if r['test']=='G6'],['candidate','amplitude_V','recovery_us','terminal_error_V','a_differential_V','b_differential_V','a_vip_peak_A','a_vim_peak_A','b_vip_peak_A','b_vim_peak_A'])+'\n\n'
    text+=f'Protegidos={run["protected_files"]}; cambios={run["protected_changed"]}.\n'+METHOD
    write(out/f'{prefix}_resumen.md',text);write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    if prefix=='s5':write(ROOT/'ACTA_S5.md',text)
    return criteria

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--controls',action='store_true')
    parser.add_argument('--resume-smoke',action='store_true',help='reuse successful smoke cases only after verifying identical decks')
    args=parser.parse_args();start=time.perf_counter();before=protected()
    if args.resume_smoke and (not args.smoke or args.controls):raise ValueError('--resume-smoke requires --smoke')
    prefix='s5_controls' if args.controls else 's5_smoke' if args.smoke else 's5'
    work=ROOT/'S5'/('controles' if args.controls else 'smoke' if args.smoke else 'generados');work.mkdir(parents=True,exist_ok=True)
    cached={};good={};old_run={};reused=0
    if args.resume_smoke:
        old_run=json.loads((ROOT/'resultados/s5_smoke_ejecucion.json').read_text(encoding='utf-8'))
        if old_run['exit_code'] or old_run['protected_changed']:raise ValueError('Only a successful unchanged smoke may be resumed')
        cached={r['id']:r for r in s4.read_saved_rows(ROOT/'resultados/s5_smoke_resultados.csv')}
        good={r['id']:r for r in old_run['records'] if not r['errors'] and not r['returncode']}
        if set(cached)!=set(good):raise ValueError('Smoke CSV/manifest mismatch')
        archive=ROOT/'resultados/s5_smoke_inicial_ejecucion.json'
        if not archive.exists():write(archive,json.dumps(old_run,indent=2,ensure_ascii=False))
    def batch_execute(batch):
        nonlocal reused
        reusable={c['id'] for c in batch if c['id'] in cached and (work/(c['id']+'.cir')).exists()
                  and (work/(c['id']+'.cir')).read_text(encoding='utf-8')==net(c)}
        rr,ss=execute([c for c in batch if c['id'] not in reusable],work)
        rr += [cached[k] for k in sorted(reusable)];ss += [good[k] for k in sorted(reusable)]
        reused+=len(reusable)
        return sorted(rr,key=lambda r:r['id']),sorted(ss,key=lambda r:r['id'])
    print('S5 workers=10; G0 first',flush=True)
    rows,records=batch_execute(controls());control_ok=len(rows)==len(controls())
    print('G0',table(rows,['candidate','section','fit_f0_Hz','fit_Q']),flush=True)
    if control_ok and not args.controls:
        for test in ['G1','G2','G3','G5','G6','G4']:
            batch=jobs(test,args.smoke,rows);print('STAGE',test,'cases',len(batch),flush=True)
            rr,ss=batch_execute(batch);rows+=rr;records+=ss
            print('DONE',test,len(rr),'/',len(batch),flush=True)
            if len(rr)!=len(batch):break
    # Remove only superseded generated decks in this runner's resolved work area.
    # Logs remain paired with active decks; this excludes old G0 state labels.
    if not work.resolve().is_relative_to((ROOT/'S5').resolve()):raise ValueError('Cleanup outside S5')
    active={r['id'] for r in records}
    for path in work.glob('*.cir'):
        if path.stem not in active:
            for ext in ['.cir','.log','.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    changed=[p for p,h in before.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records);warnings=sum(bool(r['warnings']) for r in records)
    nscale=len([0,6]) if args.smoke else len(s3.SCALES)
    planned_counts={'G0':len(controls())}
    if not args.controls:
        planned_counts.update(G1=len(CANDIDATES)*nscale,G2=len(CANDIDATES)*len([0,6])*len(['step','square']),
                              G3=len(CANDIDATES)*(3 if args.smoke else len(MC)),G5=len(CANDIDATES)*nscale,
                              G6=len(CANDIDATES)*len([-4.5,-2,2,4.5]),G4=len(CANDIDATES)*len([1e6,2e6]))
    expected=sum(planned_counts.values())
    run=dict(exit_code=int(bool(errors or changed or len(records)!=expected or not control_ok)),simulations=len(records),expected_simulations=expected,
             errors=errors,warnings=warnings,elapsed_seconds=old_run.get('elapsed_seconds',0)+time.perf_counter()-start,workers=10,smoke=args.smoke,controls_only=args.controls,
             protected_files=len(before),protected_changed=changed,seed=SEED,planned_counts=planned_counts,records=sorted(records,key=lambda r:r['id']))
    run.update(reused_successful_cases=reused,native_simulations_this_run=len(records)-reused,
               attempts=(old_run.get('attempts',old_run.get('simulations',0))+len(records)-reused))
    criteria=report(rows,records,run,prefix)
    print(table(criteria,['candidate','criterion','status','value']),flush=True)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} warnings={warnings} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return run['exit_code']

if __name__=='__main__':raise SystemExit(main())
