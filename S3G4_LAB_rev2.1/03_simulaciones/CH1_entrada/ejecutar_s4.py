"""S4: native LTspice, ten workers from the first isolated check.

Replay in a copy of CH1_entrada with S3G4_MODELS pointing to immutable models.
Exit 0 means complete execution, not electrical acceptance. No design selection.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
import ast
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s3b as previous

s3 = previous.s3
ROOT, MODELS, PROJECT, LT = s3.ROOT, s3.MODELS, s3.PROJECT, s3.LT
write, csv_write, table = s3.write, s3.csv_write, s3.table
RI, RF, RO, RT, RB, REF, VDD, DIV = 10000., 10000., 8060., 10000., 5230., 2.5, 3.3, s3.DIV_OUT
AI, AO = RF/RI, RF/RO
NG = 1+AI+AO
MID = REF*RB/(RT+RB)
CENTER = NG*MID-AO*REF/2
VARIANTS = [(m,c) for m in ['M1','M2'] for c in ['C0','C1']]
VDS = [.2,1.25,2.3]


def number(x):
    return format(x,'.12g').replace('-','n').replace('.','p').replace('+','')


def case(test, m='M1', cf='C1', scope='iso', ix=0, vd=1.25, vin=0., esd=True, supply='3p3', **extra):
    c=s3.case(test,ix)
    c.update(test=test,vmid=m,cf=cf,scope=scope,vdac_V=vd,vin_V=vin,esd=int(esd),supply=supply,**extra)
    if scope!='chain':
        c.update(scale_V_div='NA',POS='NA',tap='NA')
    vi=extra.get('amplitude_V',vin)
    if test in ['F0','ISOEQ']:tag='sw1p25'
    elif test in ['F1','ISODC']:tag='sw5'
    elif test=='F4':tag='sw3p9'
    elif test=='F5':tag='sin'+number(extra['bnc_amp'])
    elif test in ['F2','F6','ISOAC']:tag='ac1dc'+number(vi)
    else:tag=number(vi)
    pol='both' if tag.startswith(('sw','sin','ac')) else ('neg' if vi<0 else 'pos' if vi>0 else 'zero')
    c['polarity']=pol
    c['id']=(f'{test}_{m}_{cf}_{scope}_s{ix if scope=="chain" else "na"}_vi{tag}'
             f'_d{number(vd)}_{pol}_vdd{supply}_e{int(esd)}'+
             (f'_ref{number(extra["ref_V"])}' if 'ref_V' in extra else '')).lower()
    return c


def protected():
    files=[p for p in ROOT.rglob('*') if p.is_file() and
           not p.is_relative_to(ROOT/'S4') and not p.name.startswith('s4_') and
           p.name not in ['ejecutar_s4.py','ch1_comun_s4.inc','ACTA_S4.md','RESPUESTA_FINAL_S4.md']]
    files += [p for p in MODELS.rglob('*') if p.is_file()]
    files += [PROJECT/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


def base(c):
    # Use immutable S3b connection list, retaining its original 1k || 10p load.
    if c['scope']=='chain':
        old=s3.case(c['test'],c['ix'])
        l=s3.chain(old)+s3.address(old)
        l=[x.replace('ch1_comun_s3.inc','ch1_comun_s4.inc') for x in l]
        l=[x.replace('VIA COMMON IPA 0','VIA COMMON SERA 0').replace('VIB OA IPB 0','VIB OA SERB 0') for x in l]
        l += ['XPROTA SERA IPA IMA PROTECT_BAV99 R_SER=470',
              'XPROTB SERB IPB IMB PROTECT_BAV99 R_SER=470']
        if c['test']=='F6':
            l=[x.replace('AD8038_ltspice.sub','AD8038_ltspice_ruido_hoja.sub') for x in l]
    else:
        l=[f'* S4 {c["id"]}',f'.include "{ROOT/"comun/ch1_comun_s4.inc"}"',
           '.options numdgt=15 plotwinsize=0 threads=1',
           '.options method=gear solver=alt reltol=0.0001 gminsteps=0','.temp 25','.param BUFFER_KIND=810',
           'VP VP 0 5','VN VN 0 -5']
    l += [f'.include "{MODELS/"OPA836/opa836_a.lib"}"']
    if c['test']=='F6' and c['vmid']=='M2':
        # Only numerical initialization, no circuit/device parameter changes.
        l += ['.options gminsteps=25 srcstepmethod=1']
    if c['test']=='F7' and c['supply']=='ramp':
        l += ['VDD VDDA 0 PWL(0 0 1m {VDDA_NOM} 1.2m {VDDA_NOM})',
              'BREF VREF 0 V=V(VDDA)*VREF_NOM/VDDA_NOM',
              f'BDAC DAC1 0 V=V(VREF)*{c["vdac_V"]:.16g}/VREF_NOM']
    else:
        power=0 if c['supply']=='off' else VDD
        ref=c.get('ref_V',0 if c['supply']=='off' else REF)
        l += [f'VDD VDDA 0 {power:.16g}',f'VREF VREF 0 {ref:.16g}',f'VDAC DAC1 0 {c["vdac_V"]:.16g}']
    l += ['CDD1 VDDA 0 100n','CDD2 VDDA 0 1u']
    return l


def stage(c, j):
    wrap='OPA836_S4_ESD' if c['esd'] else 'OPA836_S4_BARE'
    l=[f'RIN{j} IN{j} SUM{j} {{R_IN_S4}}',f'ROFF{j} DAC{j} SUM{j} {{R_OFF_S4}}',
       f'RF{j} O{j} SUM{j} {{R_F_S4}}',f'CSUM{j} SUM{j} 0 {{C_SUM_S4}}',
       f'VIP{j} VM{j} IP{j} 0',f'VIM{j} SUM{j} IM{j} 0',f'VCC{j} VDDA VCC{j} 0',
       f'XAMP{j} IP{j} IM{j} O{j} VCC{j} 0 VDDA {wrap}',
       f'RADC{j} O{j} ADC{j} {{R_ADC_S4}}',f'CADC{j} ADC{j} 0 {{C_ADC_S4}}',
       f'CSH{j} ADC{j} 0 {{C_SH_S4}}']
    if c['cf']=='C1': l += [f'CF{j} O{j} SUM{j} 1p']
    return l


def mid_network(c):
    if c['vmid']=='M1':
        return ['RT VREF VM1 {RT_MID}','RB VM1 0 {RB_MID}','CMID VM1 0 1u']
    wrap='OPA836_S4_ESD' if c['esd'] else 'OPA836_S4_BARE'
    l=['RT VREF MID_DIV {RT_MID}','RB MID_DIV 0 {RB_MID}',
       'VBUFIP MID_DIV BUFIP 0','VBUFIM BUFOUT BUFIM 0','VBUFCC VDDA BUFCC 0',
       f'XBUF BUFIP BUFIM BUFOUT BUFCC 0 VDDA {wrap}',
       'VBUFOUT BUFOUT BUFDRIVE 0']
    for j in [1,2,3]:
        l += [f'RMID{j} BUFDRIVE VM{j} 49.9',f'CMID{j} VM{j} 0 1u',f'CMIDHF{j} VM{j} 0 100n']
    return l


def m(c, mode, name, expr): return s3.meas(c,mode,name,expr)


def net(c):
    test=c['test']; l=base(c)
    if test=='ISOAC' and c['scope']=='follower':
        l += ['VI IN1 0 1.25 AC 1','XF IN1 O1 O1 VDDA 0 VDDA OPA836','RL O1 0 2k',
              m(c,'AC','gain_1hz','FIND mag(V(O1)) AT=1'),
              '.save V(IN1) V(O1)','.ac dec 200 1 1G','.end']
        return '\n'.join(l)+'\n'
    l += mid_network(c)
    if c['vmid']=='M2':
        # Newton initial guess only (.nodeset is released by the solver).
        # Avoid source-stepping through the unspecified sub-2.5V macro regime.
        ref=c.get('ref_V',0 if c['supply']=='off' else REF)
        mid=ref*RB/(RT+RB)
        power=0 if c['supply']=='off' else VDD
        initial=-5 if test=='F1' else -3.9 if test=='F4' else c['vin_V'] if test=='F7' else 0
        center=NG*mid-AO*c['vdac_V']-AI*initial
        guess=max(0,min(power,center))
        quiet=max(0,min(power,NG*mid-AO*(0 if c['supply']=='off' else REF/2)))
        l += [f'.nodeset V(MID_DIV)={mid:.16g} V(BUFOUT)={mid:.16g} '+
              ' '.join(f'V(VM{j})={mid:.16g}' for j in [1,2,3])+f' V(O1)={guess:.16g} V(O2)={quiet:.16g} V(O3)={quiet:.16g}']
    for j in ([1] if c['vmid']=='M1' else [1,2,3]):
        l += stage(c,j)
        if j>1:
            l += [f'VI{j} IN{j} 0 0']
            if test=='F7' and c['supply']=='ramp':
                l += [f'BDAC{j} DAC{j} 0 V=V(VREF)/2']
            else:
                l += [f'VD{j} DAC{j} 0 '+('0' if test=='F7' and c['supply']=='off' else '{VREF_NOM/2}')]
    if c['scope']=='chain':
        l += ['VINLINK OUT IN1 0']
        if test=='F3':
            l += [f'Vsrc SRC 0 PULSE(0 {c["amplitude_V"]:.16g} 1u 10n 10n 10u 1)', 'VLINK SRC BNC 0']
        elif test=='F5':
            l += [f'Vsrc SRC 0 SINE(0 {c["bnc_amp"]:.16g} {s3.FREQ:.16g})','Rsource SRC BNC 50']
        else:l += ['Vsrc SRC 0 AC 1','Rsource SRC BNC 50']
    else:
        source='VI IN1 0 0 AC 1'
        if test in ['F0','F1','ISODC','ISOEQ','F4']:source='VI IN1 0 0'
        elif test=='F3':source=f'VI IN1 0 PULSE(0 {c["amplitude_V"]:.16g} 1u 10n 10n 10u 1)'
        elif test=='F7':source=f'VI IN1 0 {c["vin_V"]:.16g}'
        l += [source]
    saves=['V(VDDA)','V(VREF)','V(DAC1)','I(VDD)','I(RT)']
    for j in ([1] if c['vmid']=='M1' else [1,2,3]):
        saves += [f'V({n}{j})' for n in ['IN','VM','IP','IM','O','ADC']]
        saves += [f'I({n}{j})' for n in ['VIP','VIM','VCC','ROFF']]
        if c['esd']:saves += [f'I(XAMP{j}:DP)',f'I(XAMP{j}:DN)']
    if c['vmid']=='M2':
        saves += ['V(MID_DIV)','V(BUFOUT)','V(BUFIP)','V(BUFIM)','I(VBUFCC)','I(VBUFOUT)','I(VBUFIP)','I(VBUFIM)']
    if c['scope']=='chain':saves+=['V(SRC)','V(BNC)','V(OUT)','V(IPA)','V(IMA)','V(IPB)','V(IMB)']
    if test in ['ISOAC','F2']:
        ref='BNC' if c['scope']=='chain' else 'IN1'
        l += [m(c,'AC','gain_1hz',f'FIND mag(V(ADC1)/V({ref})) AT=1'),
              m(c,'AC','gain_2m',f'FIND mag(V(ADC1)/V({ref})) AT=2Meg'),
              '.save '+' '.join(saves),f'.ac dec 200 1 {"1G" if test=="ISOAC" else "100Meg"}']
    elif test in ['F0','ISOEQ']:
        l += [m(c,'DC','center','FIND V(ADC1) AT=0'),'.save '+' '.join(saves),'.dc VI -1.25 1.25 .05']
    elif test in ['F1','ISODC','F4']:
        for name,expr in [('adc_min','MIN V(ADC1)'),('adc_max','MAX V(ADC1)'),
                          ('diff_peak','MAX abs(V(IP1,IM1))'),('ip_peak','MAX abs(I(VIP1))'),('im_peak','MAX abs(I(VIM1))')]:
            l += [m(c,'DC',name,expr)]
        limit=3.9 if test=='F4' else 5
        l += ['.save '+' '.join(saves),f'.dc VI {-limit:.16g} {limit:.16g} .01']
    elif test=='F6':
        l += [m(c,'NOISE','onoise_100k','FIND V(onoise) AT=100k'),'.noise V(ADC1) Vsrc dec 200 1 10Meg']
    elif test in ['F3','F5']:
        l += [m(c,'TRAN','adc_min','MIN V(ADC1)'),m(c,'TRAN','adc_max','MAX V(ADC1)'),
              '.save '+' '.join(saves),f'.tran 0 {"30u" if test=="F3" else "20u"} 0 {"1n" if test=="F3" else ".5n"}']
    elif test=='F7':
        if c['supply']=='off':l += ['.save '+' '.join(saves),'.op']
        else:
            l += [m(c,'TRAN','adc_min','MIN V(ADC1)'),m(c,'TRAN','adc_max','MAX V(ADC1)'),
                  m(c,'TRAN','excess_vdda','MAX (V(ADC1)-V(VDDA))'),
                  '.save '+' '.join(saves),'.tran 0 1.2m 0 100n']
    return '\n'.join(l+['.end'])+'\n'


def limits(c,raw,r):
    vdd=raw['v(vdda)'];adc=raw['v(adc1)']
    r.update(adc_min_V=float(adc.min()),adc_max_V=float(adc.max()),
             adc_below_zero_V=float(max(0,-adc.min())),adc_above_vdda_V=float(max(0,(adc-vdd).max())))
    for j in ([1] if c['vmid']=='M1' else [1,2,3]):
        for n in ['ip','im']:
            v=raw[f'v({n}{j})'];i=raw[f'i(v{n}{j})']
            r[f'{n}{j}_min_V']=float(v.min());r[f'{n}{j}_max_V']=float(v.max())
            r[f'{n}{j}_current_peak_A']=float(np.abs(i).max())
            r[f'{n}{j}_rail_excess_V']=float(np.maximum(-.7-v,v-vdd-.7).max())
        r[f'diff{j}_peak_V']=float(np.abs(raw[f'v(ip{j})']-raw[f'v(im{j})']).max())
        for n in ['vm','o','adc']:
            r[f'{n}{j}_min_V']=float(raw[f'v({n}{j})'].min());r[f'{n}{j}_max_V']=float(raw[f'v({n}{j})'].max())
        cur=raw[f'i(vcc{j})'];r[f'iq{j}_min_A']=float(cur.min());r[f'iq{j}_max_A']=float(cur.max());r[f'iq{j}_mean_A']=float(cur.mean())
        if c['esd']:
            for n in ['dp','dn']:r[f'diode{j}_{n}_peak_A']=float(np.abs(raw[f'i(xamp{j}:{n})']).max())
    rt=raw['i(rt)'];r['vref_current_min_A']=float(rt.min());r['vref_current_max_A']=float(rt.max())
    r['dac_current_peak_A']=float(np.abs(raw['i(roff1)']).max())
    if c['vmid']=='M2':
        r['buffer_iq_min_A']=float(raw['i(vbufcc)'].min());r['buffer_iq_max_A']=float(raw['i(vbufcc)'].max())
        r['buffer_output_current_peak_A']=float(np.abs(raw['i(vbufout)']).max())
        r['buffer_diff_peak_V']=float(np.abs(raw['v(bufip)']-raw['v(bufim)']).max())
        for n in ['ip','im']:
            r[f'buffer_{n}_current_peak_A']=float(np.abs(raw[f'i(vbuf{n})']).max())
            v=raw[f'v(buf{n})'];r[f'buffer_{n}_rail_excess_V']=float(np.maximum(-.7-v,v-vdd-.7).max())


def transfer(raw,r):
    x=raw['v(in1)'];y=raw['v(adc1)'];vd=raw['v(dac1)']
    predicted=NG*MID-AI*x-AO*vd
    # Report full sweep literally AND the unsaturated region, never discard clipping.
    linear=(predicted>=.2)&(predicted<=VDD-.2)
    if linear.sum()<3:raise ValueError('Not enough linear F0 points')
    a,b=np.polyfit(x[linear],y[linear],1)
    r.update(linear_gain=float(a),linear_intercept_V=float(b),linear_points=int(linear.sum()),
             linear_nonlinearity_pct_fs=float(100*np.abs(y[linear]-(a*x[linear]+b)).max()/REF),
             full_equation_error_V=float(np.abs(y-predicted).max()),
             full_nonlinearity_pct_fs=float(100*np.abs(y-(a*x+b)).max()/REF),
             center_V=s3.interp(x,y,0),ideal_center_V=NG*MID-AO*float(vd[0]))
    r['linear_equation_error_V']=float(np.abs(y[linear]-predicted[linear]).max())


def analyze(c,raw,r):
    test=c['test']
    if test in ['ISOAC','F2']:
        f=raw['frequency']
        if c['scope']=='follower':r.update(s3.frequency_metrics(f,raw['v(o1)']));return
        ref='bnc' if c['scope']=='chain' else 'in1'
        for label,node in [('amp','o1'),('adc','adc1')]:
            r.update({label+'_'+k:v for k,v in s3.frequency_metrics(f,raw[f'v({node})']/raw[f'v({ref})']).items()})
        r['signed_gain_real']=float((raw['v(adc1)']/raw[f'v({ref})'])[0].real)
        if c['scope']=='chain':r['source_gain_2m']=s3.interp(f,np.abs(raw['v(adc1)']/raw['v(src)']),s3.FREQ)
        return
    if test=='F6':
        k=next(k for k in raw if 'onoise' in k and 'total' not in k)
        rms=s3.integral_band(raw['frequency'],raw[k].real,3.15e6)
        r.update(noise_adc_uV=rms*1e6,noise_pct_div=100*rms/DIV,noise_trace=k)
        return
    limits(c,raw,r)
    if test in ['F0','ISOEQ']:transfer(raw,r)
    if test in ['F1','ISODC','F4']:
        x=raw['v(in1)'];r.update(points=len(x),sweep_min_V=float(x.min()),sweep_max_V=float(x.max()),step_max_V=float(np.diff(x).max()))
        lim=3.9 if test=='F4' else 5
        if x.min()>-lim+1e-8 or x.max()<lim-1e-8 or np.diff(x).max()>.02000001:raise ValueError('Incomplete limit sweep')
        for vi,tag in [(-3.9,'neg3p9'),(0,'zero'),(3.9,'pos3p9')]:
            for n in ['ip1','im1','adc1','vm1']:r[f'{n}_at_{tag}_V']=s3.interp(x,raw[f'v({n})'],vi)
            r[f'diff_at_{tag}_V']=s3.interp(x,raw['v(im1)']-raw['v(ip1)'],vi)
        if test=='F4':
            for n in ['vm1','vm2','vm3','adc2','adc3']:
                baseline=s3.interp(x,raw[f'v({n})'],0)
                for vi,tag in [(-3.9,'neg'),(3.9,'pos')]:r[f'{n}_shift_{tag}_V']=s3.interp(x,raw[f'v({n})'],vi)-baseline
            r['crosstalk_peak_div']=max(abs(r[f'{n}_shift_{tag}_V'])/DIV for n in ['adc2','adc3'] for tag in ['neg','pos'])
        for key,rawkey in [('adc_min','adc_min_V'),('adc_max','adc_max_V'),('diff_peak','diff1_peak_V'),('ip_peak','ip1_current_peak_A'),('im_peak','im1_current_peak_A')]:
            if not math.isclose(r[key],r[rawkey],rel_tol=1e-6,abs_tol=1e-11):raise ValueError('meas/raw mismatch '+key)
    if test=='F3':
        t=raw['time'];y=raw['v(adc1)'];initial=float(np.mean(y[t<.5e-6]))
        r['recovery_s']=s3.settled(t,y,s3.PULSE_END,initial,.1*DIV)
        r['initial_V']=initial;r['terminal_error_V']=float(y[-1]-initial)
        r['pulse_end_s']=s3.PULSE_END;r['observation_after_end_s']=float(t[-1]-s3.PULSE_END)
        r['vmid_during_shift_V']=s3.interp(t,raw['v(vm1)'],s3.PULSE_END-1e-8)-float(np.mean(raw['v(vm1)'][t<.5e-6]))
        r['vmid_after_shift_V']=float(raw['v(vm1)'][-1]-np.mean(raw['v(vm1)'][t<.5e-6]))
        if c['scope']=='chain':
            r['bnc_peak_V']=float(np.abs(raw['v(bnc)']).max())
            if r['bnc_peak_V']>4.5+1e-8:raise ValueError('BNC over 4.5V')
        r['step_max_s']=float(np.diff(t).max())
        if r['step_max_s']>1.0001e-9:raise ValueError('Recovery resolution over 1ns')
    if test=='F5':
        t=raw['time'];y=raw['v(adc1)'];ts=np.linspace(10e-6,20e-6,65536,endpoint=False)
        spec=np.fft.rfft(np.interp(ts,t,y))/len(ts);harm=2*np.abs(spec[20*np.arange(1,10)])
        r.update(thd_pct=100*float(np.linalg.norm(harm[1:])/harm[0]),fundamental_pp_V=float(2*harm[0]),
                 actual_pp_V=float(np.ptp(y[t>=10e-6])),mean_adc_V=float(np.mean(np.interp(ts,t,y))),
                 bnc_peak_V=float(np.abs(raw['v(bnc)']).max()))
        for j,v in enumerate(harm,1):r[f'harmonic{j}_V']=float(v)
    if test=='F7' and c['supply']=='ramp':
        t=raw['time'];k=int(np.argmax(raw['v(adc1)']-raw['v(vdda)']))
        r.update(last_time_s=float(t[-1]),adc_excess_at_s=float(t[k]),vdda_at_excess_V=float(raw['v(vdda)'][k]),
                 adc_at_excess_V=float(raw['v(adc1)'][k]))
        if t[-1]<1.2e-3-1e-10:raise ValueError('Incomplete power ramp')


def simulate(c,work):
    path=work/(c['id']+'.cir');deck=net(c);write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    record=dict(id=c['id'],returncode=0,errors=[],warnings=[]);r=dict(c)
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
        pending={pool.submit(simulate,c,work):c for c in cases}
        for f in as_completed(pending):
            c=pending[f]
            try:r,s=f.result()
            except Exception as exc:r={};s=dict(id=c['id'],returncode=1,errors=[repr(exc)],warnings=[])
            if r:rows.append(r)
            records.append(s)
            if s['errors'] or s['returncode']:print('ERROR',c['id'],s['errors'],flush=True)
    return sorted(rows,key=lambda r:r['id']),sorted(records,key=lambda r:r['id'])


def read_saved_rows(path):
    rows=[]
    with path.open(newline='',encoding='utf-8') as handle:
        for record in csv.DictReader(handle):
            row={}
            for key,value in record.items():
                if value=='':
                    if key=='recovery_s' and record['test']=='F3':row[key]=None
                    continue
                try:row[key]=ast.literal_eval(value)
                except (ValueError,SyntaxError):row[key]=value
            rows.append(row)
    return rows


def controls():
    return ([case('ISOAC',m='NA',cf='C0',scope='follower',vin=1.25,esd=False)] +
            [case('ISOAC',cf=cf) for cf in ['C0','C1']] +
            [case('ISODC',vd=vd,esd=e) for vd in VDS for e in [False,True]] +
            [case('ISOEQ',vd=vd) for vd in [.2,.725,1.25,1.775,2.3]])


def jobs(test,smoke,rows):
    if test=='F1':return [case(test,m,vd=vd,esd=e) for m in ['M1','M2'] for vd in VDS for e in [False,True]]
    if test=='F7':
        return ([case(test,m,vin=v,vd=0,supply='off',ref_V=ref) for m in ['M1','M2'] for v in [-3.9,3.9] for ref in [0,REF]]+
                [case(test,m,vin=v,vd=vd,supply='ramp') for m in ['M1','M2'] for v in [-1,1] for vd in VDS])
    if test=='F0':return [case(test,vd=vd) for vd in [.2,.725,1.25,1.775,2.3]]
    if test=='F2':return ([case(test,cf=cf) for cf in ['C0','C1']]+
                           [case(test,m,cf,'chain',ix=ix) for m,cf in VARIANTS for ix in [0,6]])
    if test=='F3':
        dac=[1.25] if smoke else VDS
        return ([case(test,m,cf,vd=vd,amplitude_V=v) for m,cf in VARIANTS for vd in dac for v in [-3.9,3.9]]+
                [case(test,m,cf,'chain',vd=vd,amplitude_V=v) for m,cf in VARIANTS for vd in dac for v in ([-2,2] if smoke else [-4.5,-2,2,4.5])])
    if test=='F4':return [case(test,'M2',vd=vd,esd=e) for vd in VDS for e in [False,True]]
    if test=='F6':return [case(test,m,cf,'chain',ix=ix) for m,cf in VARIANTS for ix in ([0,6] if smoke else range(12))]
    if test=='F5':
        result=[]
        for m,cf in VARIANTS:
            ac=next(r for r in rows if r['test']=='F2' and r['vmid']==m and r['cf']==cf and r['scope']=='chain' and r['ix']==0)
            for off in ([0] if smoke else [-2,0,2]):
                vd=REF/2-off*DIV/AO
                result.append(case(test,m,cf,'chain',vd=vd,offset_div=off,bnc_amp=1/ac['source_gain_2m']))
        return result
    raise ValueError(test)


def criteria(rows,complete):
    result=[]
    for vm,cf in VARIANTS:
        by=lambda test:[r for r in rows if r['test']==test and r['esd']==1 and r['vmid']==vm and r['cf']==cf]
        def add(n,ok,value,inherited=False):
            result.append(dict(variant=vm+'-'+cf,criterion=f'S4-C{n}',status=('PASA' if ok else 'FALLA') if complete else 'PARCIAL',value=value,inherited=inherited))
        f0=[r for r in rows if r['test']=='F0']
        if f0:
            gain=max(abs(r['linear_gain']+1) for r in f0)*100
            nl=max(r['full_nonlinearity_pct_fs'] for r in f0)
            center=next(r['center_V'] for r in f0 if r['vdac_V']==1.25)
            hi=next(r['center_V'] for r in f0 if r['vdac_V']==.2)-center
            lo=center-next(r['center_V'] for r in f0 if r['vdac_V']==2.3)
            if vm=='M1':
                add(1,gain<=1 and nl<=.05 and min(hi,lo)>=5*DIV,
                    f'error G lineal={gain:.9g}%; NL F0 completo={nl:.9g}% FS; offset +{hi/DIV:.9g}/-{lo/DIV:.9g} div',cf!='C1')
            else:
                f1=[r for r in rows if r['test']=='F1' and r['vmid']=='M2' and r['esd']==1]
                if len(f1)==3:
                    center=next(r['adc1_at_zero_V'] for r in f1 if r['vdac_V']==REF/2)
                    hi=next(r['adc1_at_zero_V'] for r in f1 if r['vdac_V']==min(VDS))-center
                    lo=center-next(r['adc1_at_zero_V'] for r in f1 if r['vdac_V']==max(VDS))
                    add(1,min(hi,lo)>=5*DIV,f'rango F1 +{hi/DIV:.9g}/-{lo/DIV:.9g} div; F0 ganancia/NL solo M1',cf=='C0')
                    if complete and min(hi,lo)>=5*DIV:result[-1]['status']='NO VERIFICADO'
        safety=[r for r in rows if r['test'] in ['F1','F7'] and r['vmid']==vm and r['esd']==1]
        if safety:
            low=max(r['adc_below_zero_V'] for r in safety);high=max(r['adc_above_vdda_V'] for r in safety)
            add(2,low<=0 and high<=0,f'por debajo 0={low:.9g} V; exceso VDDA={high:.9g} V',cf=='C0')
            current=max(r[k] for r in safety for k in r if k.endswith('_current_peak_A') and (k.startswith(('ip','im','buffer_ip','buffer_im'))))
            rail=max(r[k] for r in safety for k in r if k.endswith('_rail_excess_V'))
            diff=max(r[k] for r in safety for k in r if k.startswith(('diff','buffer_diff')) and k.endswith('_peak_V'))
            add(3,current<=.00043 and rail<=0,f'I={current*1e3:.9g} mA /0.43; exceso VS+-0.7={rail:.9g} V; dif={diff:.9g} V /1',cf=='C0')
        ac=by('F2');iso=[r for r in rows if r['test']=='F2' and r['scope']=='iso' and r['cf']==cf]
        if ac and iso:
            loss=max(r['amp_loss_2m_db'] for r in iso);peak=max(r['amp_peak_db'] for r in iso)
            chain_peak=max(r['adc_peak_db'] for r in ac if r['scope']=='chain')
            total=max(r['adc_loss_2m_db'] for r in ac if r['scope']=='chain')
            add(4,loss<=.1 and peak<=.5 and chain_peak<=.5,f'S4 perdida={loss:.9g} dB; pico={peak:.9g}; cadena pico={chain_peak:.9g}, perdida={total:.9g} dB')
        rec=by('F3')
        if rec:
            times=[r['recovery_s'] for r in rec];worst=max((t for t in times if t is not None),default=math.inf)
            add(5,None not in times and worst<=1e-6,f'rec={worst*1e6:.9g} us; sin recuperar={times.count(None)}')
        f4=[r for r in rows if r['test']=='F4' and r['esd']==1]
        if vm=='M2' and f4:
            v=max(r['crosstalk_peak_div'] for r in f4);add(6,v<=.1,f'interferencia={v:.9g} div',cf=='C0')
        elif vm=='M1' and rec:
            result.append(dict(variant=vm+'-'+cf,criterion='S4-C6',status='INFORMADO',value=f'VMID durante max={max(abs(r["vmid_during_shift_V"]) for r in rec):.9g} V; despues max={max(abs(r["vmid_after_shift_V"]) for r in rec):.9g} V',inherited=False))
        thd=by('F5')
        if thd:
            v=max(r['thd_pct'] for r in thd);add(7,v<=1,f'THD={v:.9g}%')
        noise=by('F6')
        if noise:
            v=max(r['noise_pct_div'] for r in noise);add(8,v<=.45,f'ruido={v:.9g}% div; escalas={len(noise)}/12')
    return result


METHOD='''
## Método y límites de interpretación

Fuentes: ENCARGO_CODEX_S4 y PLAN_SIMULACION_S4 completos; plan/acta/auditoría
S3b, plan/acta/auditoría S3; DECISIONS del 3 oct; revisión entrada §6 E16;
canal rápido bloques 7 y 9; G473 P14/P15; models/LEEME y OPA836 SLOS712J
pp.8 y 26. Sin descargas. Diez trabajadores incluso en controles.
S3b incluido sin cambios. BAV99HY y PROTECT_BAV99 copiados textualmente de
y_b3_g_s00_pos1_tap0_cpldc_nomi_bipolar_t25.cir; 470 ohm en ambos AD8039.
Se retiene RLOAD=1k y CLOAD=10p de S3b porque el contrato prohíbe cambiar
la cadena delante; era una carga sustituta de S4 en S3. Esta ambigüedad
se deja anotada: S4 se suma a ella, no se elimina silenciosamente.
OPA836 seis nodos, PD unido a VDDA. Sensores ideales de 0V miden corriente
TOTAL de cada entrada, incluyendo diodos diferenciales añadidos. DESD es
suposición contractual (Is=1e-15 N=1 Rs=10), no pieza ni validación física.
F1/F4 se repiten con el macro sin diodos para cuantificar la dependencia.
M2 siempre tiene tres S4 reales; entradas de CH2/3=0, DAC2/3=1.25 V.
Sólo NOISE usa AD8038_ltspice_ruido_hoja.sub; modelos intactos.
R_ADC68/C_ADC470p más C_SH5p estático. Sin filtro S5 ni kickback S6.

F0 incluye todas las 51 posiciones -1.25..1.25 por DAC; se informa la
no linealidad del barrido completo, incluida saturación, además de ajuste
lineal restringido al intervalo ideal 0.2..3.1V. C1 no oculta el recorte.
Rango de offset medido a Vin=0 respecto del centro a DAC1.25, no una
extrapolación ideal. F0 es M1-C1 por contrato; M1-C0 hereda su continua.
C1 de M2 usa el rango medido directamente en F1 a Vin=0; F0 no mide
ganancia/no linealidad de M2. F1/F7/F4 sólo C1; C0 hereda
C2/C3/C6 según el cruce definido en 2.3, no un transitorio C0 de arranque.
F2 aislada M1; M2 hereda esa respuesta aislada, pero su cadena se simula.
F2 separa O1 (antes del RC, cargada por él) y ADC1 (pin después del RC).
Frecuencias 200 puntos/década; pérdida positiva respecto de AC a1Hz;
pico hasta100MHz. Controles aislados hasta1GHz para localizar -3dB.
F1 -5..5V, 10mV, extrema por raw y .meas independientes.
F4 -3.9..3.9V sostenido con DAC extremos y nominal, variación respecto
de CH1=0 en el mismo circuito; sin redefinir la línea base por otro macro.
F3 flancos10ns, pulso10us, dt<=1ns, recuperación desde FINAL del flanco
de bajada hasta permanecer en +/-25mV del punto inicial; ventana30us.
Si no recupera se informa censura, no se toma el último valor como cero.
F5 seno2MHz, amplitud de fuente calculada desde F2 de la misma variante
para2Vpp en pin ADC; offset0,+/-2div, DAC calculado desde RF/ROFF.
THD armónicos2..9, 20ciclos coherentes, rejilla65536; se informa recorte.
F6 integra ONOISE en el PIN de1Hz a3.15MHz (no inoise/BNC), cuadrado
por trapecios con extremo interpolado; porcentaje respecto de0.25V/div.

F7(a) VDDA=0, +/-5 presentes, Vin=+/-3.9, DAC=0. Como el plan no fija
VREF apagada, se prueban VREF=0 y2.5V sin decidir su secuencia real.
F7(b) rampa VDDA0..3.3 en1ms; suposición explícita VREF sigue
VDDA*2.5/3.3; DAC sigue VREF en proporciones0.2/2.5,1.25/2.5,2.3/2.5.
La alimentación <2.5V está FUERA del rango recomendado del macro/hoja.
Resultados de arranque/apagado son diagnóstico del macro, no garantía
de silicio. Se comprueba ADC frente a VDDA instantánea, no sólo3.3V.
M2 usa .nodeset calculado desde resistencias y estímulo como estimación
inicial de Newton; no fuerza tensiones finales ni modifica componentes.
En F7 todos los DAC están a0V apagados; DAC2/3 siguen VREF/2 en rampa.
F6 M2 usa gminsteps=25 y srcstepmethod=1 para inicializar el mismo
circuito: source stepping0 se detuvo inicialmente en cuatro casos;
la copia de reproducción mostró bloqueos adicionales y se generalizó.
Se conservan los intentos fallidos; --resume verifica cada deck exitoso
antes de reutilizarlo. La reejecución en copia se hace completa.
Consumo por sensor de alimentación por amplificador; RT es demanda de
VMID a VREF, no incluye ADC/DAC ni ruido real de REF3325/DAC idealizados.
Valores medios en barrido son medias de puntos, no consumo temporal.

Contradicciones no resueltas: E16 pide rizado sample-and-hold0.1LSB,
pero el contrato usa DAC con buffer continuo y no aporta modelo S/H;
no se certifica rizado. La ecuación positiva en la guía de CH1 es previa
a la sumadora inversora de este contrato. El rango ideal +/-5.21div no
asegura igual rango REAL con recorte contra masa. Ganancia de ruido3.24
no permite inferir63MHz de ancho de banda con resistencias10k y parásitas;
se mide. BAV99 de Nexperia se simula con modelo Rohm contractual.
Fuentes ideales no evalúan el power path, impedancia real ni REF/DAC
apagados. Sin selección M1/M2 o C0/C1, ni modificaciones a valores.
El intervalo0..VDDA de C2 es seguridad del pin; la conversión útil es
0..VREF+=2.5V. S4 no modela saturación de códigos del ADC, y el offset
con señal puede superar VREF incluso si permanece por debajo de VDDA.
CSV ordenados/deterministas; decks y logs retenidos; raw regenerables
se eliminan después de análisis correcto. Error eléctrico es válido;
código0 sólo indica campaña completa, no aceptación.

## Reproducción

Desde CH1_entrada: `python ejecutar_s4.py --controls`, luego
`python ejecutar_s4.py --smoke` y `python ejecutar_s4.py`.
En una copia, fijar S3G4_MODELS a la ruta Windows de
Simulation_LTSpice/models antes de ejecutar. S3G4_LTSPICE permite
indicar otro ejecutable LTspice instalado. No hay dependencias descargadas.
'''


def report(rows,records,run,prefix):
    out=ROOT/'resultados';out.mkdir(exist_ok=True)
    crit=criteria(rows,not run['smoke'] and not run['controls_only'] and run['exit_code']==0)
    for test in ['ISOAC','ISODC','ISOEQ','F0','F1','F2','F3','F4','F5','F6','F7']:
        csv_write(out/f'{prefix}_{test.lower()}.csv',[r for r in rows if r['test']==test])
    csv_write(out/f'{prefix}_resultados.csv',rows);csv_write(out/f'{prefix}_criterios.csv',crit)
    txt=f'# ACTA S4 — OPA836 a 3.3 V, offset y VMID\n\nCódigo {run["exit_code"]}; {run["simulations"]} simulaciones; {run["elapsed_seconds"]:.3f} s; diez trabajadores; errores {run["errors"]}; advertencias {run["warnings"]}.\n\n'
    if run['smoke'] or run['controls_only']:txt+='**Parcial: sin aceptación.**\n\n'
    txt+=f'Intentos técnicos={run.get("attempts",run["simulations"])}; fallidos/abortados iniciales={len(run.get("failed_attempts",[]))}; casos exitosos reutilizados con deck verificado={run.get("reused_successful_cases",0)}.\n\n'
    txt+='## Criterios por variante\n\n'+table(crit,['variant','criterion','status','value','inherited'])+'\n\n'
    txt+=f'Valores derivados de resistencias: A_IN={AI:.12g}, A_OFF={AO:.12g}, NG={NG:.12g}, VMID ideal={MID:.12g} V, centro ideal={CENTER:.12g} V.\n\n'
    f0=[r for r in rows if r['test']=='F0'] or [r for r in rows if r['test']=='ISOEQ']
    if len(f0)==5:
        dac=np.array([r['vdac_V'] for r in f0]);intercepts=np.array([r['linear_intercept_V'] for r in f0])
        slope,intercept=np.polyfit(dac,intercepts,1)
        gain=float(np.mean([r['linear_gain'] for r in f0]))
        center=next(r['center_V'] for r in f0 if r['vdac_V']==REF/2)
        hi=next(r['center_V'] for r in f0 if r['vdac_V']==min(VDS))-center
        lo=center-next(r['center_V'] for r in f0 if r['vdac_V']==max(VDS))
        equation=dict(signal_coefficient=gain,dac_coefficient=float(slope),intercept_V=float(intercept),
                      center_V=center,offset_positive_V=hi,offset_negative_V=-lo,
                      offset_positive_div=hi/DIV,offset_negative_div=-lo/DIV,
                      linear_nonlinearity_pct_fs=max(r['linear_nonlinearity_pct_fs'] for r in f0),
                      full_nonlinearity_pct_fs=max(r['full_nonlinearity_pct_fs'] for r in f0))
        csv_write(out/f'{prefix}_ecuacion.csv',[equation])
        txt+=f'**Ecuación medida en región lineal:** V_ADC={intercept:.12g} {gain:+.12g}·V_in {slope:+.12g}·V_DAC. Centro real={center:.12g} V; rango de offset real=+{hi:.12g}/-{lo:.12g} V (+{hi/DIV:.9g}/-{lo/DIV:.9g} div).\n\n'
    sections=[('ISOAC','Comprobación aislada AC',['cf','scope','gain_dc','minus3_Hz','adc_minus3_Hz','amp_minus3_Hz','amp_peak_db','amp_loss_2m_db']),
              ('ISODC','Comprobación aislada DC',['vdac_V','esd','adc_min_V','adc_max_V','diff_at_neg3p9_V','diff_at_pos3p9_V','ip1_current_peak_A','im1_current_peak_A']),
              ('F0','Transferencia y rango real',['vdac_V','linear_gain','linear_intercept_V','center_V','linear_nonlinearity_pct_fs','full_nonlinearity_pct_fs','full_equation_error_V']),
              ('F1','Extremos estáticos',['vmid','vdac_V','esd','adc_min_V','adc_max_V','ip1_min_V','ip1_max_V','im1_min_V','im1_max_V','diff1_peak_V','ip1_current_peak_A','im1_current_peak_A']),
              ('F7','Secuencia de encendido',['vmid','supply','ref_V','vin_V','vdac_V','adc_min_V','adc_max_V','adc_above_vdda_V','adc_below_zero_V','ip1_min_V','ip1_max_V','im1_min_V','im1_max_V','diff1_peak_V','ip1_current_peak_A','im1_current_peak_A']),
              ('F2','Respuesta en frecuencia',['vmid','cf','scope','scale_V_div','amp_loss_2m_db','amp_peak_db','adc_loss_2m_db','adc_peak_db','adc_minus3_Hz']),
              ('F3','Recuperación',['vmid','cf','scope','vdac_V','amplitude_V','recovery_s','terminal_error_V','vmid_during_shift_V','vmid_after_shift_V']),
              ('F4','Interferencia por VMID',['vdac_V','esd','vm1_shift_neg_V','vm1_shift_pos_V','adc2_shift_neg_V','adc2_shift_pos_V','crosstalk_peak_div']),
              ('F5','Gran señal',['vmid','cf','offset_div','vdac_V','fundamental_pp_V','actual_pp_V','mean_adc_V','thd_pct','adc_min_V','adc_max_V']),
              ('F6','Ruido de canal completo en ADC',['vmid','cf','scale_V_div','noise_adc_uV','noise_pct_div'])]
    for test,title,cols in sections:txt+=f'## {test}: {title}\n\n'+table([r for r in rows if r['test']==test],cols)+'\n\n'
    idle=[r for r in rows if r['test'] in ['F0','F1','F4','F7']]
    txt+='## Alimentación y demanda a VREF\n\n'+table(idle,['test','vmid','vdac_V','vin_V','supply','esd','iq1_min_A','iq1_max_A','iq2_mean_A','iq3_mean_A','buffer_iq_min_A','buffer_iq_max_A','vref_current_min_A','vref_current_max_A','dac_current_peak_A'])+'\n\n'
    txt+=f'Archivos protegidos={run["protected_files"]}; cambios={run["protected_changed"]}.\n\n'+METHOD
    write(out/f'{prefix}_resumen.md',txt);write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    if prefix=='s4':write(ROOT/'ACTA_S4.md',txt)
    return crit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--controls',action='store_true')
    parser.add_argument('--probe',action='store_true',help='M2 initial operating point diagnostic only')
    parser.add_argument('--probe-noise',action='store_true',help='M2 tap 1/2 noise convergence diagnostic')
    parser.add_argument('--resume',action='store_true',help='reuse verified successful cases after an interrupted full run')
    args=parser.parse_args();start=time.perf_counter();before=protected()
    if args.probe or args.probe_noise:
        work=ROOT/'S4/diagnostico';work.mkdir(parents=True,exist_ok=True)
        job=case('F6','M2','C1','chain',ix=1) if args.probe_noise else case('F1','M2')
        rows,records=execute([job],work)
        write(ROOT/('resultados/s4_probe_noise.json' if args.probe_noise else 'resultados/s4_probe.json'),json.dumps(dict(rows=rows,records=records),indent=2))
        print('M2 PROBE',len(rows),records,flush=True)
        return int(not rows)
    prefix='s4_controls' if args.controls else 's4_smoke' if args.smoke else 's4'
    work=ROOT/'S4'/('controles' if args.controls else 'smoke' if args.smoke else 'generados');work.mkdir(parents=True,exist_ok=True)
    cached={};old_run={};failed_attempts=[]
    if args.resume:
        if args.smoke or args.controls:raise ValueError('--resume only applies to the full campaign')
        old_run=json.loads((ROOT/'resultados/s4_ejecucion.json').read_text(encoding='utf-8'))
        if old_run['protected_changed']:raise ValueError('Cannot resume after protected source changes')
        cached={r['id']:r for r in read_saved_rows(ROOT/'resultados/s4_resultados.csv')}
        good={r['id']:r for r in old_run['records'] if not r['errors'] and not r['returncode']}
        if set(cached)!=set(good):raise ValueError('CSV/manifest mismatch in resume data')
        failed_attempts=old_run.get('failed_attempts',[])+[r for r in old_run['records'] if r['errors'] or r['returncode']]
        archive=ROOT/'resultados/s4_intento_inicial.json'
        if not archive.exists():write(archive,json.dumps(old_run,indent=2,ensure_ascii=False))
    reused=0;changed_records=[]
    def batch_execute(batch):
        nonlocal reused
        reuse=[c for c in batch if c['id'] in cached]
        for c in list(reuse):
            if (work/(c['id']+'.cir')).read_text(encoding='utf-8')!=net(c):
                reuse.remove(c);changed_records.append(good[c['id']])
        reusable={c['id'] for c in reuse}
        missing=[c for c in batch if c['id'] not in reusable]
        fresh,status=execute(missing,work)
        reused+=len(reuse)
        fresh += [cached[c['id']] for c in reuse]
        status += [good[c['id']] for c in reuse]
        return sorted(fresh,key=lambda r:r['id']),sorted(status,key=lambda r:r['id'])
    print('S4 workers=10; isolated checks FIRST',flush=True)
    batch=controls();rows,records=batch_execute(batch);control_ok=len(rows)==len(batch)
    for r in rows:
        if r['test']=='ISOAC':print('ISOLATED AC',r['scope'],r['cf'],{k:r[k] for k in r if k in ['minus3_Hz','amp_minus3_Hz','amp_peak_db','amp_loss_2m_db','adc_minus3_Hz']},flush=True)
        if r['test']=='ISODC':print('ISOLATED DC DAC',r['vdac_V'],'ESD',r['esd'],{k:r[k] for k in ['adc_min_V','adc_max_V','diff_at_neg3p9_V','diff_at_pos3p9_V']},flush=True)
        if r['test']=='ISOEQ':print('ISOLATED EQUATION',r['vdac_V'],r['linear_gain'],r['linear_intercept_V'],r['center_V'],flush=True)
    if control_ok and not args.controls:
        for test in ['F1','F7','F0','F2','F3','F4','F6','F5']:
            batch=jobs(test,args.smoke,rows);print('STAGE',test,'cases',len(batch),flush=True)
            rr,ss=batch_execute(batch);rows+=rr;records+=ss
            print('DONE',test,len(rr),'/',len(batch),flush=True)
            if len(rr)!=len(batch):break
    rows.sort(key=lambda r:r['id']);records.sort(key=lambda r:r['id'])
    # Remove superseded decks only inside this runner's explicitly resolved area.
    if not work.resolve().is_relative_to((ROOT/'S4').resolve()):raise ValueError('Cleanup outside S4')
    active={r['id'] for r in records}
    for p in work.glob('*.cir'):
        if p.stem not in active:
            for ext in ['.cir','.log','.raw','.op.raw','.db']:p.with_suffix(ext).unlink(missing_ok=True)
    changed=[p for p,h in before.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records);warnings=sum(bool(r['warnings']) for r in records)
    active_ids={r['id'] for r in records}
    superseded=old_run.get('superseded_successful_records',[])+changed_records
    if args.resume:superseded += [r for r in old_run['records'] if not r['errors'] and not r['returncode'] and r['id'] not in active_ids]
    run=dict(exit_code=int(bool(errors or changed or not control_ok)),simulations=len(records),errors=errors,warnings=warnings,
             elapsed_seconds=old_run.get('elapsed_seconds',0)+time.perf_counter()-start,workers=10,smoke=args.smoke,controls_only=args.controls,
             protected_files=len(before),protected_changed=changed,records=records,
             reused_successful_cases=reused,failed_attempts=failed_attempts,
             superseded_successful_records=superseded,
             attempts=len(records)+len(failed_attempts)+len(superseded))
    crit=report(rows,records,run,prefix)
    print(table(crit,['variant','criterion','status','value']),flush=True)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} warnings={warnings} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return run['exit_code']


if __name__=='__main__':raise SystemExit(main())
