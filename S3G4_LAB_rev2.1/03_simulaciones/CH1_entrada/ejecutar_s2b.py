"""S2b contract. Reuses S2 read-only helpers; no previous file is written.

Copy the whole CH1_entrada folder and set S3G4_MODELS to replay elsewhere.
Generator calibration gates DUT ESD. Electrical failures do not set exit code.
"""
from __future__ import annotations
import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s2 as old

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
MODELS = Path(os.environ.get('S3G4_MODELS', str(PROJECT/'Simulation_LTSpice/models'))).resolve()
LT = Path(os.environ.get('S3G4_LTSPICE', str(old.LT)))
CBUF = {'OPA810': 2.5e-12, 'OPA828': 9e-12}
LIMITS = {
    'S2b-C1': dict(zin=1e6, zin_pct=2, cin_lo=10, cin_hi=30, delta=2,
                   gain_pct=.5, flat_pct=1, peak_db=.1, fc=10),
    'S2b-C2': dict(r1206_w=.25*.5, r1206_v=200*.5,
                   r0805_w=.125*.5, r0805_v=150*.5, cap_fraction=.8),
    'S2b-C3': dict(rail_extension=.5, input_i=.010, OPA810_diff=7),
    'S2b-C4': dict(peak_tolerance=.15, rise=.8e-9, rise_tolerance=.25,
                   tail_tolerance=.30, peak_per_kv=15/4, i30_per_kv=8/4, i60_per_kv=4/4),
    'S2b-C5': dict(bav_ifsm=4, bav_tp=1e-6, fraction=.5, input_i=.010,
                   OPA810_diff=7),
    'capacitors': dict(ct1=100, ct2fixed=100, ct2trim=100, cb=50,
                       cs=200, cac=50, ceq=200),
    'numerical': dict(first100ns_step=.05e-9, t0=100e-9, stop=.002,
                       tail_i2t_fraction=1e-4),
}
GUN = dict(Cbody=150e-12, Rbody=330, Lbody=1.8e-6,
           Cfast=5e-12, Rfast=155, Lfast=180e-9, Rcontact=.01, Rair=300)
R_PARTS = dict(old.R_PARTS)
R_PARTS['req'] = (*R_PARTS['req'][:3], '1206')
write, csv_write, table = old.write, old.csv_write, old.table
absmax, nominal_gain = old.absmax, old.nominal_gain


def derived(buf):
    cj=1.9002e-12/(1+5/1.2722)**.35193
    sel=2*cj+3e-12+CBUF[buf]+2*.5e-12
    rbp=11e3*10e6/(11e3+10e6)
    return dict(buffer=buf, CIN_BUF_pF=0, CBUF_EST_pF=CBUF[buf]*1e12,
                CJ_POL_pF=cj*1e12, C_SEL_EST_pF=sel*1e12, CEQ_pF=sel*1e12,
                CS_pF=10e6*(2e-12+1e-12+sel)/(2*49.9e3)*1e12,
                CB_pF=((20e-12/2+1e-12)*2*549e3/rbp-(sel+2e-12))*1e12)


def case(test, buf='OPA810', pos=100, cpl=0, power=1, bleed=0,
         stimulus='zero', mode='contact', temp=25, connection='50ohm', variant='real', stop=None):
    family={'E0b':'E0','E5b':'E5','E7a':'E7','E7b':'E7','E7c':'E7','E9':'E9'}[test]
    c=old.case(family,buf,pos,cpl,power,bleed,stimulus,temp,connection,variant=variant)
    c.update(s2b_test=test, mode=mode, stop=stop or LIMITS['numerical']['stop'])
    c['id']=c['id'].replace(family.lower()+'_',test.lower()+'_',1)+'_'+mode
    if test=='E7a':c['id']='e7a_target2ohm_'+stimulus.replace('-','neg')+'_'+mode
    if stop: c['id']+='_tailcheck'
    return c


def generator(c):
    amp=int(c['stimulus'].replace('kv',''))*1000
    t0=LIMITS['numerical']['t0']
    arc=GUN['Rair'] if c['mode']=='air' else GUN['Rcontact']
    return [f'* Passive two-branch charged RLC; same network for target and BNC.',
            f'Cbody GB 0 {GUN["Cbody"]:.16g} IC={amp}',
            f'Rbody GB LB {GUN["Rbody"]:.16g}',
            f'Lbody LB JOIN {GUN["Lbody"]:.16g} IC=0',
            f'Cfast GF 0 {GUN["Cfast"]:.16g} IC={amp}',
            f'Rfast GF LF {GUN["Rfast"]:.16g}',
            f'Lfast LF JOIN {GUN["Lfast"]:.16g} IC=0',
            'Sgun JOIN ARC CTRL 0 GUNSW',
            '.model GUNSW SW(Ron=1u Roff=1e18 Vt=.5 Vh=0)',
            f'Rarc ARC BNC {arc:.16g}',
            f'Vctrl CTRL 0 PULSE(0 1 {t0-.5e-12:.16g} 1p 1p 1 2)',
            'RleakB GB 0 1e18', 'RleakF GF 0 1e18']


def base(c):
    model={'OPA810':'OPA810/opa810_a.lib','OPA828':'OPA828/OPAx828.LIB'}[c['buffer']]
    lines=[f'* S2b {c["id"]}', f'.include "{ROOT/"comun/ch1_comun_s2b.inc"}"',
           f'.include "{MODELS/model}"', '.options numdgt=15 plotwinsize=0 threads=1',
           '.options method=gear solver=alt', f'.temp {c["temperature_C"]}',
           f'.param BUFFER_KIND={810 if c["buffer"]=="OPA810" else 828}',
           f'XR VP VN RAILS_S2B POWER={c["power"]} BLEED={c["bleed"]}',
           f'XFE BNC RAWIN VP VN M TAP RSM X1 EQ SEL B T2 FRONT_S2B POS={c["POS"]} CPL={0 if c["CPL"]=="DC" else 1}',
           'VIMON RAWIN BI 0', 'Rladder OUT 0 997.7']
    if c['variant']=='real':lines += [f'XBUF BI OUT VP VN OUT BUFFER_{c["buffer"]}']
    else:lines += ['Rinput_off BI 0 1e18','Routput_off OUT 0 1Meg']
    return lines


ORIGINAL_SOURCE=old.source
def source(c):
    return generator(c) if c['test']=='E7' else ORIGINAL_SOURCE(c)


# Configure only in-memory imported helper globals. S2 files remain read-only.
old.base=base
old.source=source
old.R_PARTS=R_PARTS


def timing(stop):
    t0=LIMITS['numerical']['t0']; dt=LIMITS['numerical']['first100ns_step']
    # Isolated breakpoint source; no load, no alteration to DUT or generator.
    times=np.r_[0,t0+np.arange(0,100e-9+dt/2,dt),
                t0+np.arange(100.5e-9,2e-6,.5e-9), stop]
    return 'Vtiming TIMING 0 PWL('+ ' '.join(f'{t:.16g} {i%2}' for i,t in enumerate(times))+')'


def net(c):
    if c['s2b_test']=='E7a':
        lines=[f'* S2b calibration {c["id"]}', '.options numdgt=15 plotwinsize=0 threads=1',
               '.options method=gear solver=alt','Rtarget BNC 0 2']+generator(c)
        interval=f'FROM=0 TO={c["stop"]:.16g}'
        lines += [old.meas(c,'TRAN','gun_i_peak',f'MAX abs(I(Rarc)) {interval}'),
                  old.meas(c,'TRAN','gun_i2t',f'INTEG (I(Rarc)**2) {interval}'),
                  '.save V(BNC) V(GB) V(GF) I(Rarc)', timing(c['stop']),
                  f'.tran 0 {c["stop"]:.16g} 0 200n', '.end']
        return '\n'.join(lines)+'\n'
    text=old.net(c)
    if c['test']!='E7':return text
    # Integrals and extrema cover the entire 2ms record, including the slow tail.
    text=text.replace('I(Resd)', 'I(Rarc)').replace('V(GUN)','V(GB)')
    text=re.sub(r'FROM=1e-07 TO=2e-06',f'FROM=0 TO={c["stop"]:.16g}',text)
    text=re.sub(r'^\.tran .*$',f'.tran 0 {c["stop"]:.16g} 0 200n',text,flags=re.M)
    extra=[timing(c['stop'])]
    for d in ('dhp','dlp'):
        expr=f'I(XFE:{d.upper()})'
        extra += [old.meas(c,'TRAN',d+'_i2t',f'INTEG ({expr}**2) FROM=0 TO={c["stop"]:.16g}')]
    for label in ('rt1','rt2'):
        a,b,r,_=R_PARTS[label]
        extra += [old.meas(c,'TRAN',label+'_energy',f'INTEG ({old.v(a,b)}**2/{r:.16g}) FROM=0 TO={c["stop"]:.16g}')]
    extra += [old.meas(c,'TRAN','diff_supply_excess',f'MAX (abs(V(BI,OUT))-abs(V(VP,VN))) FROM=0 TO={c["stop"]:.16g}'),
              '.save V(GF)']
    return text.replace('.end','\n'.join(extra)+'\n.end')


def pulse_metrics(raw,c):
    ts=raw['time'];cur=np.abs(raw['i(rarc)']);t0=LIMITS['numerical']['t0']
    # First peak, not a late tail: first 20ns, also report global peak via .meas.
    first=np.flatnonzero((ts>=t0)&(ts<=t0+20e-9))
    k=int(first[np.argmax(cur[first])]);peak=float(cur[k])
    pre=np.flatnonzero((ts>=t0-1e-9)&(np.arange(len(ts))<=k))
    cross=[]
    for f in (.1,.9):
        j=int(pre[np.flatnonzero(cur[pre]>=f*peak)[0]])
        cross.append(float(np.interp(f*peak,cur[j-1:j+1],ts[j-1:j+1])))
    delta=np.diff(ts);mask=(ts[:-1]<t0+100e-9)&(ts[1:]>t0)
    return dict(first_peak_A=peak, rise_10_90_ns=(cross[1]-cross[0])*1e9,
                t10_s=cross[0], peak_time_ns=(ts[k]-t0)*1e9,
                i30_A=float(np.interp(cross[0]+30e-9,ts,cur)),
                i60_A=float(np.interp(cross[0]+60e-9,ts,cur)),
                i30_switch_A=float(np.interp(t0+30e-9,ts,cur)),
                i60_switch_A=float(np.interp(t0+60e-9,ts,cur)),
                max_step_first100ns=float(delta[mask].max()),
                gun_body_initial_V=float(raw['v(gb)'][0]),
                gun_fast_initial_V=float(raw['v(gf)'][0]),
                gun_body_final_V=float(raw['v(gb)'][-1]),
                gun_fast_final_V=float(raw['v(gf)'][-1]),
                gun_final_current_A=float(cur[-1]))


def simulate(c,work):
    path=work/(c['id']+'.cir');circuit=net(c);write(path,circuit)
    for ext in ('.log','.raw','.op.raw','.db'):path.with_suffix(ext).unlink(missing_ok=True)
    proc=subprocess.run([str(LT),'-b',str(path)],cwd=path.parent,capture_output=True)
    record=dict(id=c['id'],file=path.relative_to(ROOT).as_posix(),returncode=proc.returncode,
                errors=[],warnings=[],measures=0)
    row={k:v for k,v in c.items() if k not in ('tip','step')}
    errors=[]
    try:
        vals,errors,warnings,_=old.read_log(path.with_suffix('.log'))
        expected=set(m.lower() for m in re.findall(r'^\.meas\s+\w+\s+(\w+)',circuit,re.M|re.I))
        missing=expected-set(vals)
        if missing:errors.append('Missing measures: '+str(sorted(missing)))
        row.update({k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        record.update(warnings=warnings,measures=len(vals))
        if any(not math.isfinite(v) for v in vals.values()):errors.append('Nonfinite measure')
        if not errors and c['test']=='E0':
            nom=nominal_gain(c['POS'])
            row.update(cin_pF=row['cin']*1e12,gain_error_pct=100*(row['g1']/nom-1),
                       flat_pct=max(abs(row['gmin']/row['g1']-1),abs(row['gmax']/row['g1']-1))*100,
                       peak_db=20*math.log10(row['peak']/row['g1']))
        if not errors and c['test']=='E9':row['offset_bnc_v']=row['offset']/nominal_gain(c['POS'])
        if not errors and c['test']=='E7':
            raw=old.raw_read(path.with_suffix('.raw'));row.update(pulse_metrics(raw,c))
            record['transient_points']=len(raw['time'])
            if row['max_step_first100ns']>LIMITS['numerical']['first100ns_step']*1.0001:
                errors.append('First100ns step exceeded')
            voltage=int(c['stimulus'].replace('kv',''))*1000
            for key in ('gun_body_initial_V','gun_fast_initial_V'):
                if abs(row[key]-voltage)>abs(voltage)*1e-6:errors.append('Initial charge incorrect')
            if c['s2b_test']!='E7a':
                for d in ('dhp','dlp'):
                    current=raw['i(xfe:'+d+')'];ts=raw['time']
                    integ=float(np.trapezoid(current**2,ts))
                    row[d+'_i2t_raw']=integ
                    row[d+'_i2t_uA2s']=integ*1e6
                    row[d+'_i2t_disagreement']=abs(integ-row[d+'_i2t'])/max(integ,1e-30)
                    tail=ts>=c['stop']/2
                    row[d+'_tail_i2t']=float(np.trapezoid(current[tail]**2,ts[tail]))
                    bound=LIMITS['S2b-C5']['fraction']*LIMITS['S2b-C5']['bav_ifsm']**2*LIMITS['S2b-C5']['bav_tp']
                    row[d+'_i2t_absolute_disagreement']=abs(integ-row[d+'_i2t'])
                    if abs(integ-row[d+'_i2t'])>max(integ*.001,bound*1e-6):
                        errors.append('I2t log/raw disagree '+d+': '+str((integ,row[d+'_i2t'])))
                    if row[d+'_tail_i2t']>max(integ*LIMITS['numerical']['tail_i2t_fraction'],bound*1e-6):
                        errors.append('Pulse integration tail not converged '+d)
    except Exception as exc:errors.append(repr(exc))
    record['errors']=errors
    for ext in ('.raw','.op.raw','.db'):path.with_suffix(ext).unlink(missing_ok=True)
    return ({} if errors or proc.returncode else row),record


def execute(cases,work,workers):
    rows=[];records=[]
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(simulate,c,work):c for c in cases}
        for f in futures.as_completed(pending):
            c=pending[f]
            try:r,s=f.result()
            except Exception as exc:r={};s=dict(id=c['id'],returncode=1,errors=[repr(exc)],warnings=[])
            if r:rows.append(r)
            records.append(s)
            if s['errors'] or s['returncode']:print(c['id'],'ERROR',str(s['errors'])[:450],flush=True)
    return sorted(rows,key=lambda r:r['id']),sorted(records,key=lambda r:r['id'])


def calibration_pass(r):
    lim=LIMITS['S2b-C4'];kv=abs(int(r['stimulus'].replace('kv','')))
    pairs=[(r['first_peak_A'],kv*lim['peak_per_kv'],lim['peak_tolerance']),
           (r['rise_10_90_ns']*1e-9,lim['rise'],lim['rise_tolerance']),
           (r['i30_A'],kv*lim['i30_per_kv'],lim['tail_tolerance']),
           (r['i60_A'],kv*lim['i60_per_kv'],lim['tail_tolerance'])]
    return all(abs(v/target-1)<=tol for v,target,tol in pairs)


def jobs(smoke,bufs):
    result=[]
    for buf in bufs:
        result += [case('E0b',buf,p,c) for p in (1,100) for c in (0,1)]
        result += [case('E5b',buf,p,c,stimulus=s) for p in (1,100) for c in (0,1)
                   for s in (('100','-100','sine100') if buf=='OPA810' else ('100','-100'))]
        result += [case('E7b',buf,p,stimulus=s,mode=m) for p in (1,100)
                   for s,m in [('4kv','contact'),('-4kv','contact'),('8kv','contact'),('-8kv','contact'),('8kv','air')]]
        # Real macro at zero supply is retained and separately flagged as unvalidated.
        result += [case('E7c',buf,100,power=0,bleed=b,stimulus=s,mode=m,variant=v)
                   for b in (0,1,2) for s,m in [('4kv','contact'),('-4kv','contact'),('8kv','air')]
                   for v in ('real','off_load_only')]
        result += [case('E9',buf,p,c,temp=t,connection=con)
                   for p in (1,100) for c in (0,1) for t in (25,85) for con in ('50ohm','air')]
    if smoke:
        result=[c for c in result if c['s2b_test']=='E0b' or
                (c['s2b_test']=='E5b' and c['POS']==1 and c['CPL']=='DC') or
                (c['s2b_test']=='E7b' and c['POS']==1 and c['stimulus']=='4kv') or
                (c['s2b_test']=='E7c' and c['bleed']==2 and c['stimulus']=='4kv') or
                (c['s2b_test']=='E9' and c['POS']==1 and c['CPL']=='DC' and c['temperature_C']==25)]
    return result


def assess(rows,complete,bufs):
    result=[]
    def add(criterion,buf,value,ok):
        result.append(dict(criterion=criterion,buffer=buf,value=value,
                           status=('PASA' if ok else 'FALLA') if complete else 'PARCIAL'))
    for buf in bufs:
        r=[x for x in rows if x['buffer']==buf]
        e0=[x for x in r if x['s2b_test']=='E0b'];lim=LIMITS['S2b-C1']
        if len(e0)==4:
            dc=[x for x in e0 if x['CPL']=='DC'];delta=abs(dc[0]['cin_pF']-dc[1]['cin_pF'])
            ze=max(abs(x['zin']/lim['zin']-1)*100 for x in e0)
            ge=max(abs(x['gain_error_pct']) for x in e0);flat=max(x['flat_pct'] for x in dc)
            peak=max(x['peak_db'] for x in dc);fc=max(x['fc'] for x in e0 if x['CPL']=='AC')
            ok=ze<=lim['zin_pct'] and all(lim['cin_lo']<=x['cin_pF']<=lim['cin_hi'] for x in dc) and delta<=lim['delta'] and ge<=lim['gain_pct'] and flat<=lim['flat_pct'] and peak<=lim['peak_db'] and fc<lim['fc']
            add('S2b-C1',buf,f'Zin error {ze:.6f}%; Cin {min(x["cin_pF"] for x in dc):.6f}–{max(x["cin_pF"] for x in dc):.6f} pF; delta {delta:.6f} pF; gain {ge:.6f}%; flat {flat:.6f}%; peak {peak:.6f} dB; fc {fc:.6f} Hz',ok)
        e5=[x for x in r if x['s2b_test']=='E5b'];lim=LIMITS['S2b-C2']
        if e5:
            stress=[]
            for x in e5:
                for key,(_,_,_,size) in R_PARTS.items():
                    stress += [(x[key+'_v']/lim['r'+size+'_v'],key+'_v',x[key+'_v'],x['id']),
                               (x[key+'_p']/lim['r'+size+'_w'],key+'_p',x[key+'_p'],x['id'])]
                for key,rating in LIMITS['capacitors'].items():
                    stress += [(x[key+'_v']/(rating*lim['cap_fraction']),key+'_v',x[key+'_v'],x['id'])]
            w=max(stress);add('S2b-C2',buf,f'{w[1]}={w[2]:.6g}; {w[0]:.6f} times derated limit ({w[3]})',w[0]<=1)
            excess=max(max(x['positive_rail_excess_max'],x['negative_rail_excess_max']) for x in e5)
            ii=max(absmax(x,'input_i') for x in e5);diff=max(absmax(x,'differential') for x in e5)
            dex=max(x['diff_supply_excess'] for x in e5) if 'diff_supply_excess' in e5[0] else None
            # E5 supplies essentially constant: reconstruct conservative minimum span.
            span=min(x['vp_min']-x['vn_max'] for x in e5)
            dl=LIMITS['S2b-C3']['OPA810_diff'] if buf=='OPA810' else span
            add('S2b-C3',buf,f'rail excess {excess:.6g} V; input {ii*1e3:.6g} mA; diff {diff:.6g} V / {dl:.6g} V',excess<=.5 and ii<=LIMITS['S2b-C3']['input_i'] and diff<=dl)
        e7=[x for x in r if x['s2b_test'] in ('E7b','E7c') and abs(int(x['stimulus'].replace('kv','')))==4 and x['mode']=='contact' and x['variant']=='real']
        if e7:
            energy=max(max(x['dhp_i2t_raw'],x['dlp_i2t_raw']) for x in e7)
            ii=max(absmax(x,'input_i') for x in e7);diff=max(absmax(x,'differential') for x in e7)
            lim=LIMITS['S2b-C5'];bound=lim['fraction']*lim['bav_ifsm']**2*lim['bav_tp']
            dok=diff<=lim['OPA810_diff'] if buf=='OPA810' else max(x['diff_supply_excess'] for x in e7)<=0
            add('S2b-C5',buf,f'BAV max I2t {energy*1e6:.6g} microA2s / {bound*1e6:.6g}; input {ii*1e3:.6g} mA; diff {diff:.6g} V; OFF macro unvalidated',energy<=bound and ii<=lim['input_i'] and dok)
    cal=[x for x in rows if x['s2b_test']=='E7a' and x['mode']=='contact']
    add('S2b-C4','GENERATOR','four points at 4 and 8 kV; see calibration CSV',len(cal)==2 and all(calibration_pass(x) for x in cal))
    return sorted(result,key=lambda r:(r['criterion'],r['buffer']))


def protected_hashes():
    files=[]
    for folder in [ROOT/'S1',ROOT/'S1b',ROOT/'S2',ROOT/'chequeo_claude',MODELS]:
        files += [p for p in folder.rglob('*') if p.is_file()]
    files += [p for p in (ROOT/'resultados').glob('s[12]*') if p.is_file() and not p.name.startswith('s2b_')]
    files += [p for p in ROOT.glob('*.py') if p.name!='ejecutar_s2b.py']
    files += [p for p in ROOT.glob('ACTA_S*.md') if p.name!='ACTA_S2b.md']
    files += [p for p in (ROOT/'comun').glob('*') if p.name!='ch1_comun_s2b.inc']
    files += [PROJECT/'ai-context/STATE.md',PROJECT/'ai-context/DECISIONS.md']
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


METHOD='''
## Método y dudas sin resolver

Contrato S2b y documentos rectoros S2/S1b/S1, actas, auditorías y decisiones
2/3 oct leídos; revisión de entrada §4/§6 y documento vivo C.6/G.3/G.5/G.6.
Sin descargas, ensayos físicos ni cambios a entregables anteriores o modelos.
El ejecutor importa las funciones de lectura/netlist de ejecutar_s2.py y sólo
configura sus objetos en memoria; requiere ese fichero en la copia de CH1_entrada.
S3G4_MODELS permite apuntar a modelos externos. Diez trabajadores; threads=1.

Generador pasivo de dos ramas RLC inicialmente cargadas al nivel indicado:
150pF/330ohm/1.8uH y 5pF/155ohm/180nH. Síntesis numérica propia de banco,
no selección de protección ni modelo certificado de una pistola comercial.
El switch cierra a 100ns; flanco de mando 1ps, la subida de corriente la fijan
los inductores. Contacto: 0.01ohm; aire: 300ohm en serie, orientativo.
E7a verifica realmente la suma de corriente sobre 2ohm antes de habilitar E7b/c.
Tiempo de subida 10–90%; I30/I60 desde el primer cruce del 10% del pico,
y CSV conserva también I30/I60 desde el cierre del switch. Primer pico en
los primeros 20ns; el máximo global también se conserva. Los cuatro puntos
no determinan de forma única la impedancia de salida o la energía del generador.

I2t por cada BAV199 = integral de la corriente terminal al cuadrado de 0 a 2ms,
incluida corriente capacitiva e inversa. El valor usado es el trapecio del raw;
.meas es control independiente. Tolerancia de contraste: 0.1% de la integral
o 1ppm del límite de C5 (8e-12 A2s), el mayor; evita errores relativos ficticios
en el diodo casi inactivo. Cierre de cola: 0.01% o ese mismo piso absoluto.
Se conserva cada discrepancia y la contribución de la segunda mitad en CSV.
La fuente PWL aislada introduce quiebres de 50ps en los primeros 100ns y 0.5ns
hasta 2us; el raw se comprueba, no se presume el paso de la directiva .tran.
Después se permite adaptación hasta 200ns; se informa una comprobación a 4ms.
Las energías Rt1/Rt2 representan R1A/R1B del contrato; Rs1/Rs2 son R_S1/R_S2.

OPA810: SBOS799E local, p4 máximo diferencial min(7V, alimentación total),
input ±10mA, riel ±0.5V; 2/2.5pF común, se usa 2.5pF para diseño.
OPA828: SBOS671D local, p4 diferencial igual al span de alimentación, sin
diodos entre entradas; riel ±0.5V y ±10mA. p5: 9pF común, 6pF diferencial,
modo común operativo limitado a VEE+2.5…VCC−3.5V. No es aceptación comercial
ni prueba de intercambiabilidad de encapsulado. CIN_BUF=0 en ambos circuitos.
CB/CS/CEQ derivados se recalculan para cada buffer como manda el contrato;
ningún valor se ajusta después de observar un fallo.

1. I2t 4A²·1us es un criterio encargado, no un rating IEC ni demostración de
supervivencia: IFSM está referido a conducción directa, aquí se incluye corriente
terminal capacitiva. El modelo no simula destrucción ni temperatura de unión.
La BV del modelo BAV199 no reemplaza VR=75V de la hoja.
2. E7c conserva el macro REAL a cero alimentación para informar corriente y
diferencial solicitadas, pero no está validado ahí. OFF_LOAD_ONLY añade el
equivalente contractual sin macro, con input sin protección interna: corriente
de entrada y diferencial de un amplificador ausente no certifican C5. Se
informan ambas variantes sin sustituir REAL para forzar aceptación.
3. C5 del plan fija ±7V diferencial también apagado; la hoja OPA810 exige el
menor de 7V y el span instantáneo. Se informa el exceso frente al span en CSV;
la tabla contractual OPA810 usa 7V, sin resolver la contradicción. La segunda
fuente se compara frente a su span instantáneo, incluso si el macro de riel
apagado invierte polaridad. Ninguno demuestra ausencia de alimentación parásita.
4. Los límites de R/C son genéricos de formato; faltan MPN y ratings de pulso.
Se cambian sólo ratings de R_EQ/C_EQ/C_S a 200V, no piezas para aprobar.
5. Rieles con fuente que sólo entrega, TVS genérica y cargas 42/39mA: el macro
añade consumo al equivalente agregado, posible doble cuenta heredada de S2.
No se elige TVS, purga ni interruptor. S2b no repite ±100V apagado de E6.
6. E5 DC es equilibrio, no transitorio de conectar 100V. El seno es 100Vpk/1kHz,
medido en el último ciclo 7–8ms. E7 utiliza CPL DC, como S2. Aire +8kV es
orientativo; el requisito acordado dice ±8kV aire, pero §3 sólo encarga +8kV.
7. Acoplo por una COFF_SW a través de CAC y capacidades diferenciales del macro
no equivale exactamente a la estimación C_SEL_EST. Se conserva la topología.
8. Los fallos eléctricos son resultados válidos. Código no cero indica error de
simulación/medida, calibración ausente/inválida o archivos protegidos cambiados.
CSV deterministas, .cir/.log retenidos, raw regenerable se elimina tras análisis.
'''


def outcomes(rows):
    text='\n## Lectura de resultados y contradicciones medidas\n\n'
    aggregate=[]
    for buf in ('OPA810','OPA828'):
        r=[x for x in rows if x['buffer']==buf]
        if not r:continue
        e5=[x for x in r if x['s2b_test']=='E5b']
        if e5:
            worst=max(e5,key=lambda x:max(x['positive_rail_excess_max'],x['negative_rail_excess_max']))
            excess=max(worst['positive_rail_excess_max'],worst['negative_rail_excess_max'])
            text+=f'{buf}: C3 falla por tensión en `{worst["id"]}`: {excess:.9g} V más allá del riel frente a 0.5 V. No se convierte la corriente pequeña en permiso para superar el máximo de tensión.\n\n'
        off=[x for x in r if x['s2b_test']=='E7c' and x['variant']=='real']
        if off:
            text+=f'{buf}, apagado: exceso máximo de |diferencial| frente al span instantáneo de alimentación = {max(x["diff_supply_excess"] for x in off):.9g} V. El C5 contractual del OPA810 usa 7 V, pero su hoja pide min(7 V, span); esta discrepancia queda abierta y el macro sin alimentación no valida supervivencia.\n\n'
        for mode,levels,label in [('contact',('4kv','-4kv'),'±4 kV contacto'),
                                   ('contact',('8kv','-8kv'),'±8 kV contacto'),
                                   ('air',('8kv',),'+8 kV aire')]:
            group=[x for x in r if x['s2b_test'] in ('E7b','E7c') and x['mode']==mode and x['stimulus'] in levels]
            if group:
                aggregate.append(dict(buffer=buf,level=label,
                                      DHP_I2t_micro_A2s=max(x['dhp_i2t_raw'] for x in group)*1e6,
                                      DLP_I2t_micro_A2s=max(x['dlp_i2t_raw'] for x in group)*1e6))
        e9=[x for x in r if x['s2b_test']=='E9' and x['POS']==1 and x['CPL']=='DC' and x['temperature_C']==25 and x['connection']=='50ohm']
        if e9:text+=f'E9 {buf}: offset referido a BNC, ×1/DC, 50 Ω y 25 °C = {e9[0]["offset_bnc_v"]*1e3:.9g} mV. Resto de estados y deriva en CSV; comparación por estado en s2b_segunda_fuente.csv.\n\n'
    text+='I²t máximos por diodo sobre todos los estados ensayados (incluidas variantes apagadas); unidades 10⁻⁶ A²·s, límite reducido 8.\n\n'
    text+=table(aggregate,['buffer','level','DHP_I2t_micro_A2s','DLP_I2t_micro_A2s'])+'\n\n'
    text+='±8 kV en contacto supera el límite reducido por diodo; +8 kV aire queda por debajo en esta aproximación. El nivel contractual C5 es ±4 kV contacto. OPA828 tiene diferencial dentro de su hoja en los estados simulados, pero falla el nominal por Cin >30 pF y error de ganancia >0.5%, y falla C3 por tensión. No se acepta como sustituto directo.\n\n'
    text+='La auditoría de S2 atribuía la excursión de tensión sólo a ESD; E5b muestra un exceso también en continuo. Se conserva el hallazgo sin cambiar el diseño. C.6 del documento vivo aún dice C_S de 100 V y valores de partida: se aplican las decisiones del 3 oct y el contrato S2b, sin editar ese documento.\n'
    return text


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--workers',type=int,default=10);args=parser.parse_args()
    if args.workers<1:parser.error('workers must be positive')
    start=time.perf_counter();protected=protected_hashes()
    work=ROOT/'S2b'/('smoke' if args.smoke else 'generados');work.mkdir(parents=True,exist_ok=True)
    out=ROOT/'resultados';out.mkdir(exist_ok=True);prefix='s2b_smoke' if args.smoke else 's2b'
    bufs=['OPA810']+(['OPA828'] if (MODELS/'OPA828/OPAx828.LIB').exists() else [])
    print(f'S2b workers={args.workers} smoke={args.smoke}; calibration FIRST',flush=True)
    calibration=[case('E7a',stimulus=s) for s in ('4kv','8kv')]
    calibration += [case('E7a',stimulus='8kv',mode='air')]
    rows,records=execute(calibration,work,args.workers)
    contact=[r for r in rows if r['mode']=='contact']
    calibrated=len(contact)==2 and all(calibration_pass(r) for r in contact)
    print('CALIBRATION',[(r['stimulus'],r['first_peak_A'],r['rise_10_90_ns'],r['i30_A'],r['i60_A']) for r in contact],flush=True)
    extra=jobs(args.smoke,bufs)
    if not calibrated:
        print('Generator invalid: E7b/c gated off',flush=True)
        extra=[c for c in extra if c['test']!='E7']
    rr,ss=execute(extra,work,args.workers);rows+=rr;records+=ss
    if calibrated and not args.smoke:
        tailcase=case('E7b','OPA810',1,stimulus='4kv',stop=2*LIMITS['numerical']['stop'])
        rr,ss=execute([tailcase],work,args.workers);rows+=rr;records+=ss
    rows.sort(key=lambda r:r['id']);records.sort(key=lambda r:r['id'])
    changed=[p for p,h in protected.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records)
    warnings=sum(bool(r['warnings']) for r in records)
    code=int(bool(errors or changed or not calibrated))
    criteria=assess(rows,not args.smoke and not code,bufs)
    esd=[dict(buffer=r['buffer'],test=r['s2b_test'],POS=r['POS'],CPL=r['CPL'],power=r['power'],
              bleed=r['bleed'],variant=r['variant'],stimulus=r['stimulus'],mode=r['mode'],
              DHP_I2t_uA2s=r['dhp_i2t_uA2s'],DLP_I2t_uA2s=r['dlp_i2t_uA2s'],
              DHP_peak_A=absmax(r,'dhp_i'),DLP_peak_A=absmax(r,'dlp_i'),
              input_peak_mA=absmax(r,'input_i')*1e3,input_peak_V=absmax(r,'bi'),
              differential_V=absmax(r,'differential'),diff_supply_excess_V=r['diff_supply_excess'],
              rail_peak_V=max(absmax(r,'vp'),absmax(r,'vn')),CS_peak_V=r['cs_v'],
              relay_peak_V=max(absmax(r,'relay_open'),absmax(r,'relay_second_open')),
              RS1_energy_J=r['rs1_energy'],RS2_energy_J=r['rs2_energy'],
              R1A_energy_J=r['rt1_energy'],R1B_energy_J=r['rt2_energy'],
              gun_peak_A=r['first_peak_A'],gun_rise_ns=r['rise_10_90_ns'],
              max_step_s=r['max_step_first100ns'],id=r['id'])
         for r in rows if r['s2b_test'] in ('E7b','E7c')]
    calkeys=['stimulus','mode','first_peak_A','rise_10_90_ns','i30_A','i60_A','i30_switch_A','i60_switch_A']
    calrows=[{k:r[k] for k in calkeys} for r in rows if r['s2b_test']=='E7a']
    limits=LIMITS['S2b-C2'];stress=[]
    for buf in bufs:
        group=[r for r in rows if r['buffer']==buf and r['s2b_test']=='E5b']
        if not group:continue
        for key,(_,_,_,size) in R_PARTS.items():
            stress.append(dict(buffer=buf,part=key,voltage_V=max(r[key+'_v'] for r in group),
                               voltage_limit_V=limits['r'+size+'_v'],power_W=max(r[key+'_p'] for r in group),power_limit_W=limits['r'+size+'_w']))
        for key,rating in LIMITS['capacitors'].items():
            stress.append(dict(buffer=buf,part=key,voltage_V=max(r[key+'_v'] for r in group),voltage_limit_V=rating*limits['cap_fraction']))
    tail=[]
    for fine in rows:
        if not fine['id'].endswith('_tailcheck'):continue
        baseline=next(r for r in rows if r['id']==fine['id'].removesuffix('_tailcheck'))
        for d in ('dhp','dlp'):
            tail.append(dict(diode=d,I2t_2ms=baseline[d+'_i2t'],I2t_4ms=fine[d+'_i2t'],
                             relative_change=abs(fine[d+'_i2t']-baseline[d+'_i2t'])/max(fine[d+'_i2t'],1e-30)))
    comparison=[]
    for r in rows:
        if r['buffer']!='OPA828':continue
        counterpart=r['id'].replace('opa828','opa810')
        op=next((x for x in rows if x['id']==counterpart),None)
        if not op:continue
        for metric in ('cin_pF','gain_error_pct','flat_pct','offset_bnc_v','bi_max','bi_min',
                       'input_i_max','input_i_min','differential_max','differential_min',
                       'dhp_i2t_raw','dlp_i2t_raw','diff_supply_excess'):
            if metric in r and metric in op:
                comparison.append(dict(test=r['s2b_test'],POS=r['POS'],CPL=r['CPL'],power=r['power'],
                                       bleed=r['bleed'],variant=r['variant'],stimulus=r['stimulus'],mode=r['mode'],
                                       temperature_C=r['temperature_C'],connection=r['connection'],metric=metric,
                                       OPA810=op[metric],OPA828=r[metric],delta_OPA828_minus_OPA810=r[metric]-op[metric]))
    run=dict(exit_code=code,simulations=len(records),errors=errors,warnings=warnings,
             elapsed_seconds=time.perf_counter()-start,workers=args.workers,smoke=args.smoke,
             generator_calibrated=calibrated,second_source='OPA828' in bufs,
             protected_files=len(protected),protected_changed=changed,
             derived=[derived(b) for b in bufs],generator=GUN,limits=LIMITS,records=records)
    for suffix,data in [('resultados',rows),('criterios',criteria),('generador',calrows),
                        ('esd',esd),('componentes',stress),('cola',tail),('derivados',run['derived']),
                        ('segunda_fuente',comparison)]:
        csv_write(out/f'{prefix}_{suffix}.csv',data)
    for test in ('E0b','E5b','E7a','E7b','E7c','E9'):
        csv_write(out/f'{prefix}_{test.lower()}.csv',[r for r in rows if r['s2b_test']==test])
    write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    text=f'# ACTA S2b — entrada P4b\n\nCódigo {code}; {len(records)} simulaciones; {errors} errores; {warnings} advertencias; {run["elapsed_seconds"]:.3f} s; {args.workers} trabajadores.\n\n'
    if args.smoke:text+='**SMOKE: parcial, no aceptación.**\n\n'
    text+=table(criteria,['criterion','buffer','value','status'])+'\n\n'
    text+='## Generador sobre 2ohm; aire orientativo\n\n'+table(calrows,calkeys)+'\n\n'
    text+='## Derivados por buffer\n\n'+table(run['derived'],list(run['derived'][0]))+'\n\n'
    text+='## I2t y estrés por estado\n\n'+table(esd,['buffer','test','POS','power','bleed','variant','stimulus','mode','DHP_I2t_uA2s','DLP_I2t_uA2s','DHP_peak_A','DLP_peak_A','input_peak_mA','differential_V'])+'\n\n'
    text+='µA²s en las columnas I2t significa 10⁻⁶ A²·s, no (µA)²·s. Límite por diodo: 50% de 4²·1µs = 8·10⁻⁶ A²·s.\n\n'
    text+='## R/C en E5b\n\n'+table(stress,['buffer','part','voltage_V','voltage_limit_V','power_W','power_limit_W'])+'\n\n'
    text+='## Cierre de integral 2 frente a 4ms\n\n'+table(tail,['diode','I2t_2ms','I2t_4ms','relative_change'])+'\n\n'
    text+=f'Protegidos: {len(protected)} archivos; cambios: {changed}. Segunda fuente: {run["second_source"]}. Los CSV completos conservan tensión/corriente de entrada, rieles, energía por resistencia, CS y contactos. E9 OPA828 en s2b_e9.csv.\n'
    text+=METHOD+outcomes(rows)
    write(out/f'{prefix}_resumen.md',text)
    if not args.smoke:write(ROOT/'ACTA_S2b.md',text)
    print(table(criteria,['criterion','buffer','value','status']),flush=True)
    print(f'FINAL exit={code} sims={len(records)} errors={errors} warnings={warnings} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return code


if __name__=='__main__':raise SystemExit(main())
