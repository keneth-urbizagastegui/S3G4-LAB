"""S3 contract: immutable S2b, native LTspice, TEN parallel workers throughout.

Copy CH1_entrada and set S3G4_MODELS to replay. CSVs are deterministic; elapsed
time/path data only occur in JSON/Markdown. Electrical failures are valid results.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s2b as prior

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
MODELS = Path(os.environ.get('S3G4_MODELS', str(PROJECT/'Simulation_LTSpice/models'))).resolve()
LT = Path(os.environ.get('S3G4_LTSPICE', str(prior.LT)))
RL = np.array([499.,249.,150.,49.9,24.9,24.9])
TAPS = np.array([RL[i:].sum()/RL.sum() for i in range(len(RL))])
RF1, RG1, RF2, RG2 = 1000.,249.,2260.,249.
G1, G2 = 1+RF1/RG1, 1+RF2/RG2
G = G1*G2
E15_PROXY_CORNERS = set()
SCALES = [.005,.010,.020,.050,.100,.200,.5,1.,2.,5.,10.,20.]
DIV_OUT = .25
FREQ = 2e6
PULSE_START, PULSE_WIDTH, PULSE_EDGE = 1e-6,10e-6,10e-9
PULSE_END = PULSE_START+PULSE_EDGE+PULSE_WIDTH+PULSE_EDGE
MODEL_SR = 43e-6/.1e-12  # A2 Isrc/Cout in supplied AD8038 macro; V/s.
write, csv_write, table = prior.write, prior.csv_write, prior.table


def raw_read(path):
    b=path.read_bytes(); marker='Binary:\n'.encode('utf-16le')
    k=b.index(marker)+len(marker);h=b[:k].decode('utf-16le')
    nv=int(re.search(r'No. Variables:\s*(\d+)',h)[1])
    names=[m[1].lower() for m in re.finditer(r'^\s*\d+\s+(\S+)\s+\S+\s*$',h,re.M)]
    if 'complex' in h.lower():
        data=np.frombuffer(b[k:],dtype='<c16').reshape(-1,nv)
        result={n:data[:,i] for i,n in enumerate(names)}
        result[names[0]]=result[names[0]].real
    else:
        data=np.frombuffer(b[k:],dtype='<f8').reshape(-1,nv)
        result={n:data[:,i] for i,n in enumerate(names)}
    return result


def case(test, ix=0, cpl='DC', corner='nomi', polarity='zero', **extra):
    pos=1 if ix<6 else 100;tap=ix%6
    if test in ['E11b','E15']:polarity='positive'
    if test=='E13':polarity='bipolar'
    if test=='E15':
        seq=transition(extra['transition']);tap=seq[0]
        ix=(0 if pos==1 else 6)+seq[-1]
    c=dict(test=test,scale_V_div=SCALES[ix],ix=ix,POS=pos,tap=tap,CPL=cpl,
           corner=corner,polarity=polarity,**extra)
    proxy=test=='E15' and corner in E15_PROXY_CORNERS
    c['mux_model']='fallback100' if proxy else 'SWI1'
    suffix='_'.join(f'{k}{v}' for k,v in extra.items() if k not in ('bnc_amp',))
    c['id']=(f'{test}_s{ix:02d}_pos{pos}_tap{tap}_cpl{cpl}_ron'+('fallback100_origin' if proxy else '')+f'{corner}_{polarity}'+
             ('_'+suffix if suffix else '')).lower().replace('.','p').replace('-','neg')
    return c


def meas(c, mode, name, expression):
    return f'.meas {mode} {c["id"]}_{name} {expression}'


def prefix(c):
    return [f'* S3 {c["id"]}',f'.include "{ROOT/"comun/ch1_comun_s3.inc"}"',
            f'.include "{MODELS/"OPA810/opa810_a.lib"}"',
            f'.include "{MODELS/"AD8039/AD8038_ltspice.sub"}"',
            f'.include "{MODELS/"74HC4051"/ ("hc_t"+c["corner"]+".cir")}"',
            '.options numdgt=15 plotwinsize=0 threads=1',
            '.options method=gear solver=alt reltol=0.0001 gminsteps=0', '.temp 25',
            '.param BUFFER_KIND=810', 'VP VP 0 5', 'VN VN 0 -5',
            'CPB VP 0 10u','CND VN 0 10u','CPP VP 0 100n','CNN VN 0 100n']


def chain(c):
    return prefix(c)+ (proxy_definition() if c['mux_model']=='fallback100' else [])+[
        f'XFE BNC RAWIN VP VN M TAP RSM X1 EQ SEL B T2 FRONT_S2B POS={c["POS"]} CPL={int(c["CPL"]=="AC")}',
        'VI101 RAWIN BI 0','VIM101 BO U101M 0',
        'VIP101 VP VP101 0','VIN101 VN VN101 0',
        'X101 BI U101M VP101 VN101 BO BUFFER_OPA810',
        'XLAD BO Y1 Y2 Y3 Y4 Y5 LADDER_S3','RVCHECK Y7 0 1k',
        f'XMUX BO Y1 Y2 Y3 Y4 Y5 0 Y7 COMMON A0 A1 A2 VP VN {"MUX_S3_PROXY" if c["mux_model"]=="fallback100" else "MUX_S3"} DYNAMIC={int(c["test"]=="E15")}',
        'CPCB COMMON 0 3p','VIA COMMON IPA 0','VIMA MA IMA 0',
        'VIB OA IPB 0','VIMB MB IMB 0',
        'VIPA VP VPA 0','VINA VN VNA 0','VIPB VP VPB 0','VINB VN VNB 0',
        'X103A IPA IMA VPA VNA OA AD8039_S3','X103B IPB IMB VPB VNB OUT AD8039_S3',
        'RFA OA MA {RF1}','RGA MA 0 {RG1}','CMA MA 0 1p',
        'RFB OUT MB {RF2}','RGB MB 0 {RG2}','CMB MB 0 1p',
        'RLOAD OUT 0 1k','CLOAD OUT 0 10p']


def proxy_definition():
    # Only E15 after failed native transient calibration. Preserve decoder,
    # eight off branches; terminal capacitances p10 split over the eight Z pins.
    s=(ROOT/'comun/ch1_comun_s3.inc').read_text(encoding='utf-8')
    mux=re.search(r'(?ms)^\.subckt MUX_S3 .*?^\.ends MUX_S3$',s)[0]
    mux=mux.replace('MUX_S3','MUX_S3_PROXY').replace(' SWI1',' SWI1_PROXY')
    return [mux, '.subckt SWI1_PROXY CTL Y Z VN VP GND',
            'S1 Y Z GND CTL PROXYSW',
            '.model PROXYSW SW(Ron=100 Roff=1e12 Vt=-2.5 Vh=0)',
            'CY Y GND 5p', 'CZ Z GND {25p/8}', '.ends SWI1_PROXY']


def address(c):
    if c['test']!='E15':return [f'VA{b} A{b} 0 {5*((c["tap"]>>b)&1)}' for b in range(3)]
    # All six permutations retained: the measured worst, not a guessed code.
    seq=transition(c['transition']);order=tuple(int(x) for x in c['order'])
    skew=10e-9 if c['skew']=='10ns' else 0.
    result=[]
    for b in range(3):
        current=5*((seq[0]>>b)&1);pts=[(0.,current)]
        for event,(a,z) in enumerate(zip(seq,seq[1:])):
            if (a>>b)&1 == (z>>b)&1:continue
            t=(event+1)*15e-6+skew*order.index(b)
            new=5*((z>>b)&1);pts.extend([(t,current),(t+1e-12,new)]);current=new
        pts.append((len(seq)*15e-6,current))
        result.append(f'VA{b} A{b} 0 PWL('+ ' '.join(f'{t:.16g} {v:.16g}' for t,v in pts)+')')
    return result


def transition(name):
    return {'0to1':[0,1], '1to2':[1,2], '4to5':[4,5],
            '0to5':[0,5], '5to0':[5,0], 'autozero':[0,6,0]}[name]


def net(c):
    if c['test'].startswith('ISO'):return isolated_net(c)
    l=chain(c)+address(c);test=c['test']
    source='Vsrc SRC 0 AC 1'
    stop,dt=30e-6,1e-9
    if test=='E11b':source=f'Vsrc SRC 0 PULSE(0 {c["scale_V_div"]:.16g} 1u 2n 2n 1 2)'
    if test=='E14':
        amp=min(10*4*c['scale_V_div'],40)*(1 if c['polarity']=='positive' else -1)
        source=f'Vsrc SRC 0 PULSE(0 {amp:.16g} {PULSE_START:.16g} {PULSE_EDGE:.16g} {PULSE_EDGE:.16g} {PULSE_WIDTH:.16g} 1)'
        stop,dt=1e-3,50e-9
    if test=='E13':
        source=f'Vsrc SRC 0 SINE(0 {c["bnc_amp"]:.16g} {FREQ:.16g})'
        stop,dt=20e-6,.5e-9
    if test=='E15':
        seq=transition(c['transition']);arrival=seq[-1]
        # GND cannot produce +2div. Autocero returns to tap 0 at +2div.
        source=f'Vsrc SRC 0 {c["bnc_amp"]:.16g}'
        stop,dt=len(seq)*15e-6,.5e-9
    l += [source,'Vsource_link SRC BNC 0' if test=='E14' else 'Rsource SRC BNC 50']
    if test=='E14':
        # Breakpoint clock, isolated from DUT: <=1ns through fast recovery.
        cycles=math.ceil((PULSE_END+5e-6)/1e-9)+2
        l += [f'Vtiming TIMING 0 PULSE(0 1 0 .25n .25n .5n 1n {cycles})']
    save=['V('+n+')' for n in ['SRC','BNC','BI','BO','IPA','IMA','IPB','IMB','OA','OUT','VP','VN','A0','A1','A2']]
    save += ['I('+n+')' for n in ['VI101','VIM101','VIA','VIMA','VIB','VIMB','VIP101','VIN101','VIPA','VINA','VIPB','VINB']]
    if test=='E11':
        for key,expr in [('gdc','mag(V(OUT)/V(BNC))'),('s3dc','mag(V(OUT)/V(BI))')]:
            l += [meas(c,'AC',key,f'FIND {expr} AT={1 if c["CPL"]=="DC" else 1000}')]
        l += [meas(c,'AC','g2m','FIND mag(V(OUT)/V(BNC)) AT=2Meg'),
              meas(c,'AC','s32m','FIND mag(V(OUT)/V(BI)) AT=2Meg'),
              '.save '+' '.join(save),'.ac dec 200 1 100Meg','.end']
    elif test=='E12':
        l += [meas(c,'NOISE','inoise_density_100k','FIND V(inoise) AT=100k'),
              '.noise V(OUT) Vsrc dec 200 1 10Meg','.end']
    else:
        for key,n in [('u101p','VIP101'),('u101n','VIN101'),('u103ap','VIPA'),('u103an','VINA'),('u103bp','VIPB'),('u103bn','VINB')]:
            l += [meas(c,'TRAN',key+'_idle',f'AVG I({n}) FROM=0 TO=0.5u')]
            if test=='E13':l += [meas(c,'TRAN',key+'_signal',f'AVG I({n}) FROM=10u TO=20u')]
        l += [meas(c,'TRAN','output_peak','MAX abs(V(OUT))'),'.save '+' '.join(save),
              f'.tran 0 {stop:.16g} 0 {dt:.16g}', '.end']
    return '\n'.join(l)+'\n'


def isolated_net(c):
    l=prefix(c);test=c['test']
    if test=='ISOAMP':
        l += ['VI IP 0 AC 1','XAMP IP IM VP VN OUT AD8039_S3',
              f'RF OUT IM {RF1 if c["stage"]=="a" else RF2}',
              f'RG IM 0 {RG1 if c["stage"]=="a" else RG2}',
              'CM IM 0 1p','RL OUT 0 1k','CL OUT 0 10p',
              meas(c,'AC','gain_dc','FIND mag(V(OUT)) AT=1'),
              '.save V(IP) V(OUT)', '.ac dec 240 1 1G','.end']
    elif test=='ISOLAD':
        l += ['VI BO 0 1','XL BO Y1 Y2 Y3 Y4 Y5 LADDER_S3']
        for i,n in enumerate(['BO','Y1','Y2','Y3','Y4','Y5']):l += [meas(c,'TRAN',f'tap{i}',f'AVG V({n}) FROM=0 TO=1u')]
        l += ['.save V(BO) V(Y1) V(Y2) V(Y3) V(Y4) V(Y5)','.tran 0 1u 0 100n','.end']
    elif test=='ISOSW':
        l += [f'VY Y 0 {c["level"]}',f'VC CTRL 0 {c["control"]}', 'XSW CTRL Y Z VN VP 0 SWI1']
        if c['control']==0:
            l += ['IL Z 0 100u',meas(c,'TRAN','ron','AVG (V(Y,Z)/100u) FROM=0 TO=1u')]
        else:l += ['RL Z 0 1k',meas(c,'TRAN','off_gain','AVG V(Z) FROM=0 TO=1u')]
        l += ['.save V(Y) V(Z)','.tran 0 1u 0 100n','.end']
    elif test=='ISOCTRL':
        l += ['VY Y 0 .1','VC CTL 0 PULSE(0 5 1u 30n 30n 1u 4u)',
              'XSW CTL Y Z VN VP 0 SWI1','RL Z 0 1k',
              '.save V(CTL) V(Y) V(Z)','.tran 0 3u 0 1n','.end']
    return '\n'.join(l)+'\n'


def interp(x,y,at):return float(np.interp(at,x,np.asarray(y).real))


def frequency_metrics(f,h,reference=None):
    m=np.abs(h);dc=float(m[0] if reference is None else reference)
    db=20*np.log10(m/dc);ix=np.flatnonzero(db<=-3)
    cutoff=float(np.exp(np.interp(-3,db[ix[0]-1:ix[0]+1][::-1],np.log(f[ix[0]-1:ix[0]+1])[::-1]))) if len(ix) and ix[0]>0 else None
    return dict(gain_dc=dc,loss_2m_db=-interp(np.log(f),db,np.log(FREQ)),
                peak_db=float(db.max()),peak_Hz=float(f[np.argmax(db)]),minus3_Hz=cutoff)


def integral_band(f,density,upper):
    # Interpolate the spectral density at the contractual integration endpoint.
    mask=(f>=1)&(f<upper);x=np.r_[f[mask],upper];y=np.r_[density[mask],np.interp(upper,f,density)]
    return float(np.sqrt(np.trapezoid(y**2,x)))


def settled(t,y,event,final,band):
    ix=np.flatnonzero((t>=event)&(np.abs(y-final)>band))
    if len(ix):
        j=int(ix[-1])
        if j==len(t)-1:return None
        # First saved point after the LAST violation: no first-crossing shortcut.
        return float(t[j+1]-event)
    return 0.


def analyze(c,raw,row):
    test=c['test']
    if test in ('ISOAMP','E11'):
        f=raw['frequency'];out=raw['v(out)']
        if test=='ISOAMP':row.update(frequency_metrics(f,out));row['ideal']=G1 if c['stage']=='a' else G2
        else:
            refat=1 if c['CPL']=='DC' else 1000
            row['source_gain_2m']=interp(f,np.abs(out/raw['v(src)']),FREQ)
            row['source_gain_dc']=float(np.abs(out/raw['v(src)'])[np.argmin(abs(f-refat))])
            for prefix,node in [('bnc','bnc'),('s3','bi')]:
                h=out/raw['v('+node+')'];ref=float(np.abs(h[np.argmin(abs(f-refat))]))
                row.update({prefix+'_'+k:v for k,v in frequency_metrics(f,h,ref).items()})
            row['ideal_gain']=G*TAPS[c['tap']]*prior.nominal_gain(c['POS'])
            row['gain_error_pct']=100*(row['bnc_gain_dc']/row['ideal_gain']-1)
    elif test=='E12':
        f=raw['frequency'];key=next(k for k in raw if 'inoise' in k and 'total' not in k)
        density=np.asarray(raw[key]).real
        for upper,label in [(3.15e6,'315m'),(10e6,'10m')]:
            rms=integral_band(f,density,upper);row['noise_'+label+'_uV']=rms*1e6
            row['noise_'+label+'_pct_div']=100*rms/c['scale_V_div']
        row['noise_trace']=key;row['noise_points']=len(f)
    elif test=='ISOCTRL':
        row['native_converged']=bool(raw['time'][-1]>=3e-6)
        row['last_time_s']=float(raw['time'][-1])
    elif test in ('E11b','E13','E14','E15'):
        t=raw['time'];y=raw['v(out)']; row['points']=len(t)
        for amp,plus,minus in [('u101','bi','bo'),('u103a','ipa','ima'),('u103b','ipb','imb')]:
            row[amp+'_differential_peak_V']=float(np.max(np.abs(raw['v('+plus+')']-raw['v('+minus+')'])))
            for node,label in [(plus,'plus'),(minus,'minus')]:
                a=raw['v('+node+')'];row[amp+'_'+label+'_min_V']=float(a.min());row[amp+'_'+label+'_max_V']=float(a.max())
                row[amp+'_'+label+'_rail_excess_V']=float(np.maximum(a-5,-5-a).max())
        for amp,ports in [('u101',['vi101','vim101']),('u103a',['via','vima']),('u103b',['vib','vimb'])]:
            for label,port in zip(['plus','minus'],ports):row[amp+'_'+label+'_current_peak_A']=float(np.max(np.abs(raw['i('+port+')'])))
        if test=='E11b':
            initial=float(np.mean(y[t<.5e-6]));final=float(np.mean(y[t>29e-6]));delta=final-initial
            row['overshoot_pct']=max(0.,float((y[t>=1e-6].max()-final)/abs(delta)*100))
            row['step_initial_V']=initial;row['step_final_V']=final
        elif test=='E14':
            # The source and topology after release equal the initial DC OP.
            # A late tail is not allowed to redefine the target and hide failure.
            final=float(np.mean(y[t<.5e-6]));row['final_V']=final
            row['terminal_V']=float(np.mean(y[t>t[-1]-1e-6]))
            row['terminal_error_V']=row['terminal_V']-final
            for div in [.1,.5]:row['recovery_'+str(div).replace('.','p')+'_s']=settled(t,y,PULSE_END,final,div*DIV_OUT)
            row['pulse_requested_V']=min(10*4*c['scale_V_div'],40)*(1 if c['polarity']=='positive' else -1)
            row['pulse_BNC_plateau_V']=interp(t,raw['v(bnc)'],6e-6)
            row['pulse_BNC_peak_V']=float(np.max(np.abs(raw['v(bnc)'])))
            row['pulse_end_s']=PULSE_END;row['observation_after_end_s']=t[-1]-PULSE_END
            intervals=np.diff(t);mask=(t[:-1]<PULSE_END+5e-6)&(t[1:]>=PULSE_START)
            row['max_step_pulse_and_5us_s']=float(intervals[mask].max())
            if row['max_step_pulse_and_5us_s']>1e-9*1.0001:raise ValueError('E14 resolution exceeded 1ns')
        elif test=='E13':
            # Coherent 20 cycles, endpoint excluded, Fourier least squares equivalent.
            ts=np.linspace(10e-6,20e-6,65536,endpoint=False);signal=np.interp(ts,t,y)
            a=np.fft.rfft(signal)/len(signal);bins=20*np.arange(1,10)
            harmonics=2*np.abs(a[bins]);row['thd_pct']=100*float(np.linalg.norm(harmonics[1:])/harmonics[0])
            row['output_pp_V']=float(2*harmonics[0]);row['max_dvdt_V_us']=float(np.max(np.abs(np.diff(y[t>=10e-6])/np.diff(t[t>=10e-6])))/1e6)
            row['model_SR_V_us']=MODEL_SR/1e6;row['slew_fraction']=row['max_dvdt_V_us']/(MODEL_SR/1e6)
            for i,v in enumerate(harmonics):row[f'harmonic{i+1}_V']=float(v)
        elif test=='E15':
            seq=transition(c['transition']);worst_recovery=0.;glitches=[];saturation=False
            code=np.zeros(len(t),dtype=int)
            for bit in range(3):code += (raw[f'v(a{bit})']>2.5).astype(int)*(2**bit)
            row['codes_observed']='>'.join(str(v) for v in code[np.r_[True,np.diff(code)!=0]])
            for k in range(len(seq)-1):
                event=(k+1)*15e-6;end=(k+2)*15e-6
                segment=(t>=event)&(t<end if k<len(seq)-2 else t<=end)
                final=float(np.mean(y[(t>end-1e-6)&(t<=end)]));initial=interp(t,y,event-1e-9)
                recovery=settled(t[segment],y[segment],event,final,.1*DIV_OUT)
                if recovery is None:worst_recovery=None
                elif worst_recovery is not None:worst_recovery=max(worst_recovery,recovery)
                excursion=max(float(y[segment].max())-max(initial,final),min(initial,final)-float(y[segment].min()),0.)
                glitches.append(excursion/DIV_OUT)
                row[f'event{k+1}_final_V']=final;row[f'event{k+1}_recovery_s']=recovery
                row[f'event{k+1}_glitch_div']=excursion/DIV_OUT
                for node in ['bo','oa','out']:
                    if node=='bo':demand=raw['v(bi)'];diff=raw['v(bi)']-raw['v(bo)']
                    elif node=='oa':demand=G1*raw['v(ipa)'];diff=raw['v(ipa)']-raw['v(ima)']
                    else:demand=G2*raw['v(ipb)'];diff=raw['v(ipb)']-raw['v(imb)']
                    clipped=(np.abs(demand)>4)&(np.abs(diff)>.05)
                    flag=bool(np.any(clipped[segment]));row[node+'_saturation_flag']=row.get(node+'_saturation_flag',False) or flag
                    saturation |= flag
            row['settlement_s']=worst_recovery;row['glitch_div']=max(glitches)
            row['transition_peak_div']=float(np.max(np.abs(y[t>=15e-6]))/DIV_OUT)
            row['saturation_4V_flag']=saturation


def simulate(c,work):
    path=work/(c['id']+'.cir');deck=net(c);write(path,deck)
    for ext in ['.log','.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    record=dict(id=c['id'],returncode=0,errors=[],warnings=[])
    row=dict(c)
    try:
        proc=subprocess.run([str(LT),'-b',str(path)],cwd=work,capture_output=True,timeout=30 if c['test']=='ISOCTRL' else 3600)
        record['returncode']=proc.returncode
        vals,errors,warnings,log=prior.old.read_log(path.with_suffix('.log'))
        expected={m.lower() for m in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        missing=expected-set(vals)
        if missing:errors.append('Missing measures '+str(sorted(missing)))
        record.update(errors=errors,warnings=warnings)
        row.update({k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        if c['test']=='ISOCTRL' and (errors or proc.returncode):
            native_failure(path,row,record,'; '.join(errors))
        elif not errors and not proc.returncode:analyze(c,raw_read(path.with_suffix('.raw')),row)
    except Exception as exc:
        if c['test']=='ISOCTRL' and isinstance(exc,subprocess.TimeoutExpired):
            native_failure(path,row,record,'Timeout after collapsed time step')
        else:record['errors'].append(repr(exc))
    for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    return (row if not record['errors'] and not record['returncode'] else {}),record


def native_failure(path,row,record,reason):
    b=path.with_suffix('.raw').read_bytes();marker='Binary:\n'.encode('utf-16le')
    k=b.index(marker)+len(marker);h=b[:k].decode('utf-16le')
    nv=int(re.search(r'No. Variables:\s*(\d+)',h)[1]);size=((len(b)-k)//(nv*8))*nv*8
    d=np.frombuffer(b[k:k+size],dtype='<f8').reshape(-1,nv)
    steps=np.diff(d[:,0]);small=steps<1e-15
    runs=np.convolve(small.astype(int),np.ones(8,dtype=int),mode='valid')
    candidates=np.flatnonzero(runs==8)
    if not len(candidates):
        record['errors'].append('Native failure without demonstrated step collapse');return
    first=int(candidates[0]);row.update(native_converged=False,stall_time_s=float(d[first,0]),
                                      collapsed_step_s=float(steps[first:first+8].max()))
    record.update(simulator_returncode=record['returncode'],returncode=0,errors=[],warnings=[],
                  native_failure=reason,last_time_s=float(d[-1,0]),
                  diagnostic='Native SWI1 failed compatibility test; E15 fallback authorized by S3 §1')


def execute(cases,work):
    rows=[];records=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        pending={pool.submit(simulate,c,work):c for c in cases}
        for f in as_completed(pending):
            c=pending[f]
            try:r,s=f.result()
            except Exception as exc:r={};s=dict(id=c['id'],returncode=1,errors=[repr(exc)],warnings=[])
            if r:rows.append(r)
            records.append(s)
            if s['errors'] or s['returncode']:print('ERROR',c['id'],str(s['errors'])[:500],flush=True)
    return sorted(rows,key=lambda r:r['id']),sorted(records,key=lambda r:r['id'])


def isolated_cases():
    return [case('ISOAMP',stage=s) for s in ['a','b']]+[case('ISOLAD')]+[
        case('ISOSW',level=v,control=0) for v in [-2,0,2]]+[case('ISOSW',level=1,control=5)]


def jobs(smoke):
    indices=[0,5,6,11] if smoke else range(12)
    jobs=[case(test,i) for test in ['E11','E12','E11b'] for i in indices]
    jobs += [case('E14',i,polarity=p) for i in indices for p in ['positive','negative']]
    jobs += [case('E11',i,cpl='AC') for i in [0,6]]
    jobs += [case('E11',i,corner='slow') for i in ([0] if smoke else [0,5])]
    for pos_ix in [0,6]:
        for corner in ['nomi','slow']:
            for transition in (['0to5','autozero'] if smoke else ['0to1','1to2','4to5','0to5','5to0','autozero']):
                jobs += [case('E15',pos_ix,corner=corner,transition=transition,skew='0ns',order='012')]
                for order in (['201'] if smoke else [''.join(map(str,p)) for p in itertools.permutations(range(3))]):
                    jobs += [case('E15',pos_ix,corner=corner,transition=transition,skew='10ns',order=order)]
    return jobs


def protected_hashes():
    files=[]
    for folder in [ROOT/'S1',ROOT/'S1b',ROOT/'S2',ROOT/'S2b',ROOT/'chequeo_claude',MODELS]:
        files += [p for p in folder.rglob('*') if p.is_file()]
    for pattern in ['*.py','ACTA_S*.md','PLAN_SIMULACION*.md','ENCARGO_CODEX*.md']:
        files += [p for p in ROOT.glob(pattern) if p.name not in ['ejecutar_s3.py','ACTA_S3.md']]
    files += [p for p in (ROOT/'resultados').glob('*') if p.is_file() and not p.name.startswith('s3_')]
    files += [p for p in (ROOT/'comun').glob('*') if p.name!='ch1_comun_s3.inc' and p.is_file()]
    files += [PROJECT/'ai-context/STATE.md',PROJECT/'ai-context/DECISIONS.md']
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


def clean_superseded(work,records):
    # Only this runner's S3 output folder; never previous stages or models.
    work=work.resolve()
    if not work.is_relative_to((ROOT/'S3').resolve()):raise ValueError('Cleanup outside S3')
    active={r['id'] for r in records}
    for path in work.glob('*.cir'):
        if path.stem in active:continue
        for ext in ['.cir','.log','.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)


def assess(rows,complete):
    result=[]
    def add(n,value,ok):result.append(dict(criterion=f'S3-C{n}',value=value,status=('PASA' if ok else 'FALLA') if complete else 'PARCIAL'))
    ac=[r for r in rows if r['test']=='E11' and r['CPL']=='DC']
    step=[r for r in rows if r['test']=='E11b'];noise=[r for r in rows if r['test']=='E12']
    sine=[r for r in rows if r['test']=='E13' and r['vpp']==2]
    pulse=[r for r in rows if r['test']=='E14'];switch=[r for r in rows if r['test']=='E15']
    if ac:
        loss=max(r['s3_loss_2m_db'] for r in ac);peak=max(r['s3_peak_db'] for r in ac)
        add(1,f'Loss S3 max {loss:.9g} dB / 0.5',loss<=.5)
        overshoot=max([r['overshoot_pct'] for r in step],default=math.inf)
        add(2,f'Peak S3 {peak:.9g} dB / 0.5; step {overshoot:.9g}% / 5',peak<=.5 and overshoot<=5)
        add(3,f'DC error max {max(abs(r["gain_error_pct"]) for r in ac):.9g}% (informativo)',True)
    if noise:
        v=max(r['noise_315m_pct_div'] for r in noise);add(4,f'Noise 1Hz–3.15MHz {v:.9g}% div / 0.45',v<=.45)
    if sine:
        thd=max(r['thd_pct'] for r in sine);slew=max(r['slew_fraction'] for r in sine)
        add(5,f'THD {thd:.9g}% / 1; SR fraction {slew:.9g} / 0.5',thd<=1 and slew<=.5)
    if pulse:
        rec=[r['recovery_0p1_s'] for r in pulse];v=max(x for x in rec if x is not None)
        add(6,f'Recovery max finite {v*1e6:.9g} us / 1; not recovered {rec.count(None)} (window {min(r["observation_after_end_s"] for r in pulse)*1e6:.9g}us)',None not in rec and v<=1e-6)
        da=max(r['u103a_differential_peak_V'] for r in pulse);db=max(r['u103b_differential_peak_V'] for r in pulse)
        d1=max(r['u101_differential_peak_V'] for r in pulse)
        rail=max(r[a+'_'+side+'_rail_excess_V'] for r in pulse for a in ['u103a','u103b'] for side in ['plus','minus'])
        ib=max(r['u101_'+s+'_current_peak_A'] for r in pulse for s in ['plus','minus'])
        r1=max(r['u101_'+s+'_rail_excess_V'] for r in pulse for s in ['plus','minus'])
        ok=da<=4 and db<=4 and rail<=0 and d1<=7 and ib<=.01 and r1<=.5
        add(7,f'Diff A {da:.9g}, B {db:.9g} / 4V; U101 {d1:.9g}/7V, I {ib*1e3:.9g}/10mA, rail excess {r1:.9g}/0.5V; AD rail excess {rail:.9g}V',ok)
    if switch:
        rec=[r['settlement_s'] for r in switch];v=max(x for x in rec if x is not None)
        add(8,f'Settle {v*1e6:.9g} us / 10; glitch {max(r["glitch_div"] for r in switch):.9g} div; not recovered {rec.count(None)}',None not in rec and v<=10e-6)
    return result


METHOD = '''
## Método, fuentes y dudas sin resolver

Se leyeron completos encargo, plan S3, contrato S2b, acta y auditoría S2b,
sus antecedentes S2/S1b/S1 y las decisiones del 3 oct. Fuentes rectoras:
revision_entrada_ch1.html §6 E11–E15; rediseno_afe_rev21.html C.3–C.6.
Se conserva la red y los valores de FRONT_S2B sin cambios, incluida su
CS derivada ≈1.169nF y CEQ≈8.668pF: no se sustituyen por 1.5nF/12pF de
las listas resumidas. CIN_BUF=0; CBUF_EST=2.5pF. S3 sólo añade carga aguas abajo.
Ideal BNC = toma calculada × ganancias calculadas × nominal_gain de S2,
incluida la carga RBIAS. Ganancia en continua por AC a 1Hz (DC coupling);
AC coupling se normaliza a 1kHz, no se llama ganancia DC. Rsource=50ohm;
E11 informa H respecto a BNC y respecto al pin de U101 después de R_PROT.
Caída positiva significa pérdida; negativa significa subida. Pico hasta 100MHz.
E11b es escalón BNC de 1div, 2ns; overshoot relativo a su delta final real.
E14 usa enlace ideal0V de SRC a BNC para imponer exactamente min(10FS,40V)
en el puerto; el resto usa fuente50ohm. Se guardan meseta y pico BNC reales.
Rieles ideales ±5V con 10uF+100nF: opción autorizada; no evalúa inyección en
rieles reales de G.3. Sensores de 0V separan ambos rieles y entradas de cada
amplificador; no se asigna consumo total del riel a una etapa.

U102: ocho SWI1 del fichero hc_tnomi.cir de Nexperia, nodo control/Y/Z/VEE/VCC/GND,
activo bajo, incluyendo las siete ramas apagadas. Sólo se incluye una esquina
por deck (nombres repetidos). hc_tslow en E11 y toda E15. Sin HC4051pck extra:
el contrato exige SWI1+3pF de pista. Sus parásitas son las del macro de transistor.
La hoja sólo publica capacitancias terminales (p10: Yn5pF, Z25pF), no una matriz
de capacidades ni una garantía de inyección. No se añaden otra vez al macro.
Nexperia declara el modelo para transitorio: que converja AC/noise no valida
su precisión experimental. Si converge, no se sustituye por Ron fijo.
En conmutación E15 SWI1 no converge: el control aislado30ns colapsa a pasos
<1fs sin alcanzar3us. El ejecutor comprueba ambas esquinas antes de campaña
y guarda su último tiempo/paso tras30s de diagnóstico. Sólo en las esquinas
que fallan E15 sustituye las ocho SWI1 por SW(Ron100ohm), Yn5pF y Z25pF
(distribuido25pF/8 en cada rama), p10. Las capacidades no especifican una
matriz de acoplamiento al control; el proxy NO reproduce inyección de carga.
Glitch y C8 son resultados de esta aproximación, pendientes de modelo/placa.
No se presenta un peor RON de proceso real en E15: ambos proxies usan100ohm.

E12 es V(inoise) de LTspice referido a Vsrc en la BNC con Rsource=50ohm,
no ruido de salida dividido por una ganancia constante. Se integra su densidad
al cuadrado mediante trapecios entre 1Hz y 3.15MHz y 10MHz; se interpola
explícitamente el punto de corte. Esta referencia incluye los 50ohm.
Diagnóstico adicional separado (S3/diagnostico_ruido_ad8039.cir y
diagnostico_ruido_opa810.cir, ambos ejecutados con código0): el AD8038
aislado con la red contractual×5 da inoise=1.61810882549e-8 V/raízHz
a100kHz, frente a8nV/raízHz de la hoja p3; OPA810 seguidor con la carga
de escalera da5.77019729804e-9 V/raízHz. La discrepancia de ruido del AD8038
queda abierta: NO se divide por2 ni se modifica el modelo para aprobar C4.
Los dos decks diagnósticos son anclados a la estructura original mediante
rutas relativas; la campaña principal sí soporta S3G4_MODELS en una copia.
E13 ajusta solamente el estímulo desde la AC medida para 2/4Vpp, no el diseño;
THD armónicos 2–9 sobre 20 períodos, rejilla uniforme65536 por interpolación
del raw ≤0.5ns; todos los armónicos se conservan. SR del macro = Isrc/Cout
de A2 =43uA/0.1pF, no se utiliza como sustituto el SR típico de la hoja.
E14: pulso de10us con flancos10ns, origen recuperación al FINAL del flanco
de bajada. Se busca la última violación respecto al offset final real, nunca
el primer cruce. Registro1ms; se informa ventana y recuperación censurada.
Paso <=1ns durante pulso y primeros5us tras su fin, verificado en raw;
después <=50ns. El objetivo es el punto DC inicial, no el último valor de cola.
Las corrientes de entrada AD8039 son del modelo simplificado: no representa
Ib400nA ni diodos diferenciales. No especifica límite de corriente la hoja.
La diferencial sí se juzga contra ±4V aunque el macro no se destruya.
AD8038_8039.pdf RevG p5 Table3; entrada común absoluta±VS; p3 reposo1mA
típ/1.5mA máx, salida±4V en RL2k, recuperación50ns en G2/1V no trasladable
a esta cadena. OPA810: ±7V diferencial, ±10mA; se informa también exceso de
VS±0.5V conservando la contradicción acta/auditoría S2b, sin resolverla.

E15: código binario comportamental a partir de las tres direcciones reales;
el código nuevo debe coincidir con el de20ns antes para cerrar. RC de control
tau=30ns/ln9 da flanco10–90%30ns; la separación al50% es20ns en cambio
simple. Se prueban las seis permutaciones de desfase10ns, incluyendo códigos
intermedios, no sólo el orden supuesto peor. El filtro limita pulsos de código
menores que BBM; no representa el decodificador físico ni su hazards exactos.
Se conserva el comportamiento del SWI1 detrás del control. Pico de glitch =
excursión fuera del intervalo entre salida inicial/final (div); se informa
además pico absoluto respecto a masa e indicio de saturación por etapa si
la salida ideal demandada supera4V y |diferencial|>50mV simultáneamente.
Esto reconoce el recorte del macro alrededor3.84V con nuestra carga, sin
confundirlo con el ±4V típico de hoja en RL2k. No es un límite de seguridad.
La entrada se calcula desde la ganancia DC medida en E11 y el offset de E11b para+2div en la toma
de llegada, y en autocero para
la toma de retorno: GND no puede producir+2div. Ambos eventos se miden.

Contradicción documental de tiempos: el plan atribuye30ns/20ns a la hoja;
74HC_HCT4051.pdf Rev12 p13–14 columna ±4.5V dice ton16–18ns típico y
toff18ns típico (máx51/42ns a25°C); NO declara BBM20ns. Se aplican30ns/20ns
como supuestos impuestos por contrato, no como citas verificadas de fabricante.
El documento vivo C.6 aún contiene la red4.02k/1k,9.09k/1k y candidatos
anteriores; manda decisión3oct y contrato S3:1k/249,2.26k/249,AD8039.
§6 de revisión conserva criterio ruido0.35%/10MHz; manda S3:0.45%/3.15MHz.
Resultados de modelo no prueban supervivencia, consumo real ni ESD en placa.
No se diseña S4 ni filtro, no se eligen protecciones ni se descargan ficheros.
No se modifican STATE/DECISIONS por prohibición específica del encargo.
CSV ordenados deterministas, .cir/.log retenidos, raw regenerable eliminado.
'''


def report(rows,records,run,prefix,out):
    criteria=assess(rows,not run['smoke'] and run['exit_code']==0)
    ac=[r for r in rows if r['test']=='E11' and r['corner']=='nomi' and r['CPL']=='DC']
    per_scale=[]
    for a in ac:
        n=next((r for r in rows if r['test']=='E12' and r['ix']==a['ix']),{})
        pulses=[r for r in rows if r['test']=='E14' and r['ix']==a['ix']]
        per_scale.append(dict(scale_V_div=a['scale_V_div'],POS=a['POS'],tap=a['tap'],gain_dc=a['bnc_gain_dc'],
            ideal=a['ideal_gain'],error_pct=a['gain_error_pct'],minus3_s3_Hz=a['s3_minus3_Hz'],
            minus3_bnc_Hz=a['bnc_minus3_Hz'],loss_s3_2m_db=a['s3_loss_2m_db'],loss_bnc_2m_db=a['bnc_loss_2m_db'],
            peak_s3_db=a['s3_peak_db'],peak_bnc_db=a['bnc_peak_db'],
            noise_uV=n.get('noise_315m_uV'),noise_pct_div=n.get('noise_315m_pct_div'),
            noise_10m_uV=n.get('noise_10m_uV'),
            recovery_positive_us=next((r['recovery_0p1_s']*1e6 if r['recovery_0p1_s'] is not None else 'not_recovered' for r in pulses if r['polarity']=='positive'),None),
            recovery_negative_us=next((r['recovery_0p1_s']*1e6 if r['recovery_0p1_s'] is not None else 'not_recovered' for r in pulses if r['polarity']=='negative'),None)))
    for test in ['ISOAMP','ISOLAD','ISOSW','ISOCTRL','E11','E12','E14','E13','E11b','E15']:
        csv_write(out/f'{prefix}_{test.lower()}.csv',[r for r in rows if r['test']==test])
    csv_write(out/f'{prefix}_resultados.csv',rows);csv_write(out/f'{prefix}_criterios.csv',criteria)
    csv_write(out/f'{prefix}_escalas.csv',per_scale)
    taps=[dict(tap=i,resistance_to_ground_Ohm=float(RL[i:].sum()),total_Ohm=float(RL.sum()),ratio=float(TAPS[i]),ideal_chain_gain=G*float(TAPS[i])) for i in range(6)]
    csv_write(out/f'{prefix}_tomas.csv',taps)
    text=f'# ACTA S3 — CH1 buffer, escalera, 4051 y AD8039\n\nCódigo {run["exit_code"]}; {run["simulations"]} ejecuciones; {run["errors"]} errores de campaña; {run["warnings"]} advertencias de campaña; {run["elapsed_seconds"]:.3f}s; diez trabajadores.\n\n'
    failures=[r for r in records if r.get('native_failure')]
    text+=f'De esas ejecuciones, {len(failures)} son pruebas de compatibilidad SWI1 que no convergen y activan la sustitución permitida sólo en E15; sus fallos y registros parciales no cuentan como una simulación nativa válida. E15 y C8 son aproximados (RON100, sin inyección de carga real).\n\n'
    if run['smoke']:text+='**SMOKE: parcial, sin aceptación.**\n\n'
    text+=table(criteria,['criterion','value','status'])+'\n\n'
    text+='## Comprobaciones aisladas anteriores a campaña\n\n'
    text+=f'Ganancias calculadas: G1={G1:.12g}, G2={G2:.12g}, producto={G:.12g}.\n\n'
    text+=table([r for r in rows if r['test']=='ISOAMP'],['stage','gain_dc','ideal','minus3_Hz','peak_db','loss_2m_db'])+'\n\n'
    text+=table(taps,list(taps[0]))+'\n\n'
    text+=table([r for r in rows if r['test']=='ISOSW'],['control','level','ron','off_gain'])+'\n\n'
    text+='## Convergencia nativa de SWI1 con control30ns\n\n'+table([r for r in rows if r['test']=='ISOCTRL'],['corner','native_converged','stall_time_s','collapsed_step_s'])+'\n\n'
    text+='## Por escala nominal DC\n\n'+table(per_scale,list(per_scale[0]) if per_scale else [])+'\n\n'
    text+='## E14: entradas y recuperación, ambas polaridades\n\n'
    text+=table([r for r in rows if r['test']=='E14'],['ix','polarity','pulse_requested_V','pulse_BNC_plateau_V','recovery_0p1_s','recovery_0p5_s','u103a_differential_peak_V','u103b_differential_peak_V','u101_differential_peak_V','u101_plus_current_peak_A','u103a_plus_current_peak_A','u103a_minus_current_peak_A','u103b_plus_current_peak_A','u103b_minus_current_peak_A','u103a_plus_rail_excess_V','u103b_plus_rail_excess_V'])+'\n\n'
    text+='## Gran señal y corriente por pin\n\n'+table([r for r in rows if r['test']=='E13'],['ix','vpp','output_pp_V','thd_pct','max_dvdt_V_us','model_SR_V_us','u101p_signal','u101n_signal','u103ap_signal','u103an_signal','u103bp_signal','u103bn_signal'])+'\n\n'
    idle=[r for r in rows if r['test']=='E11b']
    text+='## Reposo con BNC a cero\n\n'+table(idle,['ix','u101p_idle','u101n_idle','u103ap_idle','u103an_idle','u103bp_idle','u103bn_idle'])+'\n\n'
    text+='Corrientes en A: positiva entra al pin desde VP/VN; el retorno negativo suele tener signo negativo. Medidas individuales, no total del riel.\n\n'
    switches=[r for r in rows if r['test']=='E15']
    text+='## E15 peor caso por transición, POS y proceso\n\n'
    worst=[]
    for key,group in itertools.groupby(sorted(switches,key=lambda r:(r['POS'],r['corner'],r['transition'])),key=lambda r:(r['POS'],r['corner'],r['transition'])):
        g=list(group);w=max(g,key=lambda r:r['glitch_div']);worst.append({k:w[k] for k in ['POS','corner','transition','skew','order','codes_observed','glitch_div','transition_peak_div','settlement_s','saturation_4V_flag']})
    text+=table(worst,list(worst[0]) if worst else [])+'\n\n'
    text+=f'Protegidos {run["protected_files"]}; cambios {run["protected_changed"]}. Todos los estados y ambas entradas/corrientes en CSV.\n'+METHOD
    write(out/f'{prefix}_resumen.md',text)
    if not run['smoke']:write(ROOT/'ACTA_S3.md',text)
    return criteria


def set_e15_amplitudes(batch, rows):
    for c in batch:
        a=next(r for r in rows if r['test']=='E11' and r['ix']==c['ix'] and r['CPL']=='DC' and r['corner']=='nomi')
        zero=next(r for r in rows if r['test']=='E11b' and r['ix']==c['ix'])
        c['bnc_amp']=(2*DIV_OUT-zero['step_initial_V'])/a['source_gain_dc']


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--probe',action='store_true',help='single E15 convergence diagnostic, never acceptance')
    args=parser.parse_args()
    if args.probe:
        work=ROOT/'S3/probe';work.mkdir(parents=True,exist_ok=True)
        E15_PROXY_CORNERS.update(['nomi','slow'])
        rows,records=execute([case('E15',0,transition='0to5',skew='0ns',order='012',bnc_amp=2*DIV_OUT/(G*TAPS[5]*prior.nominal_gain(1)))],work)
        print(json.dumps(dict(rows=rows,records=records),indent=2),flush=True)
        return int(not rows)
    start=time.perf_counter();protected=protected_hashes()
    work=ROOT/'S3'/('smoke' if args.smoke else 'generados');work.mkdir(parents=True,exist_ok=True)
    out=ROOT/'resultados';out.mkdir(exist_ok=True);prefix='s3_smoke' if args.smoke else 's3'
    print('S3 workers=10; isolated amplifier, ladder and SWI1 FIRST',flush=True)
    rows,records=execute(isolated_cases(),work)
    print('ISOLATED',json.dumps(rows,ensure_ascii=False),flush=True)
    if len(rows)!=len(isolated_cases()):
        print('Isolated checks failed; campaign gated off',flush=True)
    else:
        controls=[case('ISOCTRL',corner=corner) for corner in ['nomi','slow']]
        rr,ss=execute(controls,work);rows+=rr;records+=ss
        E15_PROXY_CORNERS.update(r['corner'] for r in rr if not r['native_converged'])
        print('CONTROL CHECK',json.dumps(rr), 'E15 fallback corners',sorted(E15_PROXY_CORNERS),flush=True)
        # Ordered priorities, batches remain parallel with ten workers.
        all_jobs=jobs(args.smoke)
        for test in ['E11','E12','E14','E13','E11b','E15']:
            batch=[c for c in all_jobs if c['test']==test]
            if test=='E13':
                for ix in [0,6]:
                    a=next(r for r in rows if r['test']=='E11' and r['ix']==ix and r['CPL']=='DC' and r['corner']=='nomi')
                    # Exact Vsrc->OUT transfer measured in the same AC case.
                    amp_gain=a['source_gain_2m']
                    batch += [case('E13',ix,vpp=v,bnc_amp=v/2/amp_gain) for v in [2,4]]
            if test=='E15':
                set_e15_amplitudes(batch, rows)
            print('STAGE',test,'cases',len(batch),flush=True)
            rr,ss=execute(batch,work);rows+=rr;records+=ss
            print('DONE',test,'successful',len(rr),'/',len(batch),flush=True)
    rows.sort(key=lambda r:r['id']);records.sort(key=lambda r:r['id'])
    clean_superseded(work,records)
    changed=[p for p,h in protected.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records);warnings=sum(bool(r['warnings']) for r in records)
    run=dict(exit_code=int(bool(errors or changed)),simulations=len(records),errors=errors,warnings=warnings,
             elapsed_seconds=time.perf_counter()-start,workers=10,smoke=args.smoke,
             protected_files=len(protected),protected_changed=changed,records=records)
    criteria=report(rows,records,run,prefix,out)
    write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    print(table(criteria,['criterion','value','status']),flush=True)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} warnings={warnings} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return run['exit_code']


if __name__=='__main__':raise SystemExit(main())
