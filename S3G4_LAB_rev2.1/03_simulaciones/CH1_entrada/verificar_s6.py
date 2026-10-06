"""Audit S6 decks/state/aperture/coherence; optional independent finer runs."""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse
import csv
import json
import time
import numpy as np
import ejecutar_s6 as s

def read(name):
    with (s.OUT/name).open(encoding='utf-8',newline='') as f:return list(csv.DictReader(f))

def typed(r):
    c={k:r[k] for k in s.BASE_FIELDS}
    for k in ['RSW_Ohm','target_Hz','freq_Hz','M','level_V','source_dc_V','source_amp_V']:
        if c[k]!='NA':c[k]=float(c[k])
    c['M']=int(c['M'])
    if c['RSW_Ohm']!='NA':c['RSW_Ohm']=int(c['RSW_Ohm'])
    return c

def audit(prefix):
    defects=[];cases={}
    for test in ['h1','h2','h3']:
        for r in read(f'{prefix}_{test}.csv'):cases[r['id']]=typed(r)
    work=s.ROOT/'S6'/('smoke' if prefix=='s6_smoke' else 'generados')
    for c in cases.values():
        p=work/(c['id']+'.cir')
        if p.read_text(encoding='utf-8')!=s.net(c):defects.append('deck differs '+c['id'])
        if c['test']!='H1':
            if not c['M']%2 or c['freq_Hz']!=c['M']*s.a6.FS/s.a6.N:defects.append('noncoherent '+c['id'])
    samples=read(f'{prefix}_muestras.csv')
    aperturemax=0.
    for r in samples:
        c=cases[r['id']];n=int(r['n']);adc=int(r['adc']);t=float(r['time_s'])
        if adc!=n%2+1:defects.append('ADC parity '+r['id'])
        expected=s.a6.START+s.a6.TS+(s.a6.FIRST+n)/s.a6.FS
        if abs(t-expected)>1e-15:defects.append('time '+r['id'])
        if float(r['track_left_clock_V'])<.5 or float(r['track_left_time_s'])>t+1e-15:defects.append('not tracking '+r['id'])
        aperturemax=max(aperturemax,abs(float(r['closing_time_error_ps'])))
        if abs(float(r['sample_V'])-float(r['reference_V'])-float(r['error_V']))>1e-14:defects.append('error '+r['id'])
    manifest=json.loads((s.OUT/f'{prefix}_ejecucion.json').read_text(encoding='utf-8'))
    flanks=read(f'{prefix}_h0_flancos.csv');widths={};periods={}
    for adc in [1,2]:
        rises=[float(r['time_s']) for r in flanks if int(r['adc'])==adc and r['edge']=='rise']
        falls=[float(r['time_s']) for r in flanks if int(r['adc'])==adc and r['edge']=='fall']
        widths[str(adc)]=falls[0]-rises[0];periods[str(adc)]=rises[1]-rises[0]
        if abs(widths[str(adc)]-s.a6.TS)>1e-12 or abs(periods[str(adc)]-s.a6.PERIOD)>1e-12:defects.append('clock ADC'+str(adc))
    for r in manifest['records']:
        p=work/(r['id']+'.cir')
        deck=p.read_text(encoding='utf-8')
        if any(not l.split()[2].startswith(r['id']+'_') for l in deck.splitlines() if l.startswith('.meas ')):defects.append('meas state '+r['id'])
    result=dict(decks=len(manifest['records']),sample_cases=len(cases),samples=len(samples),aperture_max_ps=aperturemax,
        adc_widths_s=widths,adc_periods_s=periods,defects=sorted(set(defects)))
    s.write(s.OUT/f'{prefix}_auditoria_codex.json',json.dumps(result,indent=2));print(json.dumps(result),flush=True)
    return cases,result

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--precision',action='store_true')
    args=parser.parse_args();prefix='s6_smoke' if args.smoke else 's6'
    cases,result=audit(prefix)
    if result['defects']:return 1
    if not args.precision:return 0
    start=time.perf_counter();before=s.protected()
    chosen=[c for c in cases.values() if c['RSW_Ohm']==825 and ((c['test']=='H1' and c['state']=='Z' and c['level_V']==2.25) or
             (c['test']=='H2' and c['target_Hz']==2e6 and c['state'] in ['P','Z']) or c['test']=='H3')]
    dd,records=s.execute(chosen,s.ROOT/'S6'/'precision',dt=.25e-9)
    original={}
    for test in ['h1','h2','h3']:
        for r in read(f'{prefix}_{test}.csv'):original[(r['id'],int(r['adc']))]=r
    origfft={(r['id'],r['sequence']):r for r in read(f'{prefix}_fft.csv')}
    differences=[]
    for d in dd:
        for r in d['metrics']:
            old=original[(r['id'],r['adc'])]
            diff=dict(id=r['id'],adc=r['adc'])
            for key in ['error_max_mV','error_rms_mV','residual_rms_mV','gain_delta_db','phase_delta_deg']:
                if key in r:diff[key+'_delta']=r[key]-float(old[key])
            differences.append(diff)
        for r in d['fft']:
            old=origfft[(r['id'],r['sequence'])]
            differences.append(dict(id=r['id'],sequence=r['sequence'],sfdr_db_delta=r['sfdr_db']-float(old['sfdr_db']),thd_pct_delta=r['thd_pct']-float(old['thd_pct'])))
    changed=[p for p,h in before.items() if not s.Path(p).exists() or s.hashlib.sha256(s.Path(p).read_bytes()).hexdigest()!=h]
    out=dict(simulations=len(records),elapsed_seconds=time.perf_counter()-start,records=records,differences=differences,protected_changed=changed,
             exit_code=int(len(dd)!=len(chosen) or bool(changed)))
    s.write(s.OUT/'s6_precision.json',json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='records'}),flush=True)
    return out['exit_code']

if __name__=='__main__':raise SystemExit(main())
