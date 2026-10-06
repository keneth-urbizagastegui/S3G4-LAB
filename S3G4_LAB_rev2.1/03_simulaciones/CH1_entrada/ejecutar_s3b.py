"""S3b contract: immutable S3, ten workers in every batch, native SWI1.

Replay: copy CH1_entrada, set S3G4_MODELS, python ejecutar_s3b.py.
Electrical failures do not cause a nonzero exit; missing/failed cases do.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import time
import numpy as np
import ejecutar_s3 as s3

ROOT = Path(__file__).resolve().parent
VARIANTS = {'A': (470., 'BAT54'), 'B': (1000., 'BAT54'),
            'C': (470., 'BAV199'), 'D': (1000., 'BAV199')}
write, csv_write, table = s3.write, s3.csv_write, s3.table


def case(test, variant='NONE', ix=0, temp=25, polarity='zero', **extra):
    c = s3.case(test, ix, polarity=polarity, **extra)
    c.update(variant=variant, temp_C=temp, noise_model='sheet' if test == 'B2' else 'original')
    c['id'] = (f'{test}_{variant}_s{ix:02d}_pos{c["POS"]}_tap{c["tap"]}_cpldc_nomi_{polarity}_t{temp}'
               + ''.join(f'_{k}{v}' for k, v in extra.items() if k != 'bnc_amp')).lower().replace('.', 'p')
    if test == 'B0':
        c['id']=f'b0_{variant.lower()}_isolated_scalena_posna_tapna_cplna_zero_t{temp}'
    return c


def protected():
    files = []
    for folder in ['S1','S1b','S2','S2b','S3','chequeo_claude','comun','resultados']:
        files += [p for p in (ROOT/folder).rglob('*') if p.is_file()
                  and not p.name.startswith('s3b_') and p.name != 'ch1_comun_s3b.inc']
    files += [p for p in ROOT.glob('*') if p.is_file()
              and p.name not in ['ejecutar_s3b.py','ACTA_S3b.md','RESPUESTA_FINAL_S3b.md']]
    files += [p for p in s3.MODELS.rglob('*') if p.is_file()]
    files += [s3.PROJECT/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


def base(c, isolated=False):
    l = s3.prefix(c) if isolated else s3.chain(c) + s3.address(c)
    l = [x.replace('ch1_comun_s3.inc','ch1_comun_s3b.inc') for x in l]
    if c['noise_model'] == 'sheet':
        l = [x.replace('AD8038_ltspice.sub','AD8038_ltspice_ruido_hoja.sub') for x in l]
    l = [f'.temp {c["temp_C"]}' if x.startswith('.temp ') else x for x in l]
    if not isolated:
        l = [x.replace('X101 BI U101M VP101 VN101 BO BUFFER_OPA810',
                       'X101 BI U101M VP101 VN101 BO_DRIVE BUFFER_OPA810') for x in l]
        l += ['VOUT101 BO_DRIVE BO 0']
        if c['variant'] != 'NONE':
            l = [x.replace('VIA COMMON IPA 0','VIA COMMON SER_IN 0') for x in l]
            rs, diode = VARIANTS[c['variant']]
            l += [f'XPROT SER_IN IPA IMA PROTECT_{diode} R_SER={rs:.16g}']
    return l


def measure(c, mode, name, expr):
    return s3.meas(c, mode, name, expr)


def net(c):
    test = c['test']
    if test == 'B0':
        rs, diode = VARIANTS[c['variant']]
        l = base(c, True) + ['VI COMMON 0 AC 1',
             f'XPROT COMMON IPA IMA PROTECT_{diode} R_SER={rs:.16g}',
             'XAMP IPA IMA VP VN OUT AD8039_S3','RF OUT IMA {RF1}',
             'RG IMA 0 {RG1}','CM IMA 0 1p','RL OUT 0 1k','CL OUT 0 10p',
             measure(c,'AC','gain_dc','FIND mag(V(OUT)) AT=1'),
             '.save V(COMMON) V(IPA) V(IMA) V(OUT)', '.ac dec 240 1 1G','.end']
        return '\n'.join(l)+'\n'
    l = base(c)
    source = 'Vsrc SRC 0 AC 1'
    if test == 'B3': source = 'Vsrc SRC 0 0'
    if test == 'B4':
        amp = c['amplitude_V'] * (1 if c['polarity'] == 'positive' else -1)
        source = f'Vsrc SRC 0 PULSE(0 {amp:.16g} {s3.PULSE_START:.16g} {s3.PULSE_EDGE:.16g} {s3.PULSE_EDGE:.16g} {s3.PULSE_WIDTH:.16g} 1)'
    if test == 'B5': source = f'Vsrc SRC 0 SINE(0 {c["bnc_amp"]:.16g} {s3.FREQ:.16g})'
    if test == 'B6': source = 'Vsrc SRC 0 0'
    l += [source, 'Vsource_link SRC BNC 0' if test in ['B3','B4'] else 'Rsource SRC BNC 50']
    save = ['V('+n+')' for n in ['SRC','BNC','BI','BO','COMMON','IPA','IMA','IPB','IMB','OA','OUT']]
    save += ['I('+n+')' for n in ['VI101','VIM101','VIA','VIMA','VIB','VIMB','VOUT101','VIP101','VIN101','VIPA','VINA','VIPB','VINB']]
    if c['variant'] != 'NONE': save += ['I(XPROT:DP)','I(XPROT:DN)']
    if test == 'B1':
        for ref,node in [('bnc','BNC'),('s3','BI')]:
            l += [measure(c,'AC',ref+'_dc',f'FIND mag(V(OUT)/V({node})) AT=1'),
                  measure(c,'AC',ref+'_2m',f'FIND mag(V(OUT)/V({node})) AT=2Meg')]
        l += ['.save '+' '.join(save),'.ac dec 200 1 100Meg']
    elif test == 'B2':
        l += [measure(c,'NOISE','density_100k','FIND V(inoise) AT=100k'),
              '.noise V(OUT) Vsrc dec 200 1 10Meg']
    elif test == 'B3':
        for name,expr in [('diff_a','abs(V(IPA,IMA))'),('diff_b','abs(V(IPB,IMB))'),
                          ('switch_current','abs(I(VIA))'),('diode_p','abs(I(XPROT:DP))'),
                          ('diode_n','abs(I(XPROT:DN))'),('opa810_current','abs(I(VOUT101))')]:
            l += [measure(c,'DC',name+'_peak','MAX '+expr)]
        l += [measure(c,'DC','inplus_min','MIN V(IPA)'),measure(c,'DC','inplus_max','MAX V(IPA)'),
              '.save '+' '.join(save),'.dc Vsrc -40 40 .05']
    elif test == 'B4':
        l += [measure(c,'TRAN','out_peak','MAX abs(V(OUT))'),'.save '+' '.join(save),
              '.tran 0 30u 0 .5n']
    elif test == 'B5':
        l += [measure(c,'TRAN','out_peak','MAX abs(V(OUT))'),'.save '+' '.join(save),
              '.tran 0 20u 0 .5n']
    elif test == 'B6':
        # LTspice .op results are extracted directly from the saved operating point.
        l += ['.save '+' '.join(save),'.op']
    return '\n'.join(l+['.end'])+'\n'


def analyze(c, raw, row):
    test = c['test']
    if test == 'B0': row.update(s3.frequency_metrics(raw['frequency'],raw['v(out)']))
    elif test == 'B1':
        f=raw['frequency'];out=raw['v(out)']
        for prefix,node in [('bnc','bnc'),('s3','bi')]:
            row.update({prefix+'_'+k:v for k,v in s3.frequency_metrics(f,out/raw['v('+node+')']).items()})
        row['source_gain_2m']=s3.interp(f,np.abs(out/raw['v(src)']),s3.FREQ)
    elif test == 'B2':
        key=next(k for k in raw if 'inoise' in k and 'total' not in k)
        for upper,label in [(3.15e6,'315m'),(10e6,'10m')]:
            rms=s3.integral_band(raw['frequency'],np.asarray(raw[key]).real,upper)
            row['noise_'+label+'_uV']=rms*1e6
            row['noise_'+label+'_pct_div']=100*rms/c['scale_V_div']
    elif test == 'B3':
        axis=raw['v(src)'];row.update(sweep_min_V=float(axis.min()),sweep_max_V=float(axis.max()),points=len(axis),step_max_V=float(np.diff(axis).max()))
        if len(axis)<1601 or axis.min()>-40 or axis.max()<40-1e-8: raise ValueError('Incomplete DC sweep')
        for name,p,m in [('u103a','ipa','ima'),('u103b','ipb','imb')]:
            diff=np.abs(raw['v('+p+')']-raw['v('+m+')']);k=int(np.argmax(diff))
            row[name+'_differential_peak_V']=float(diff[k]);row[name+'_peak_at_BNC_V']=float(raw['v(bnc)'][k])
        for name,key in [('switch','i(via)'),('diode_p','i(xprot:dp)'),('diode_n','i(xprot:dn)'),('opa810','i(vout101)')]:
            values=np.abs(raw[key]);k=int(np.argmax(values));row[name+'_current_peak_A']=float(values[k]);row[name+'_peak_at_BNC_V']=float(raw['v(bnc)'][k])
        v=raw['v(ipa)'];row['inplus_min_V']=float(v.min());row['inplus_max_V']=float(v.max());row['inplus_rail_margin_V']=float(np.minimum(5-v,v+5).min())
        row['u103b_margin_V']=4-row['u103b_differential_peak_V']
        # Independent .meas versus full raw extrema, do not substitute missing measures.
        for name,other in [('diff_a_peak','u103a_differential_peak_V'),('diff_b_peak','u103b_differential_peak_V'),('switch_current_peak','switch_current_peak_A'),('diode_p_peak','diode_p_current_peak_A'),('diode_n_peak','diode_n_current_peak_A'),('opa810_current_peak','opa810_current_peak_A')]:
            if not math.isclose(row[name],row[other],rel_tol=1e-7,abs_tol=1e-12): raise ValueError('Raw/meas disagreement '+name)
    elif test == 'B4':
        t=raw['time'];y=raw['v(out)'];final=float(np.mean(y[t<.5e-6]))
        row['recovery_s']=s3.settled(t,y,s3.PULSE_END,final,.1*s3.DIV_OUT)
        row['initial_offset_V']=final;row['terminal_error_V']=float(y[-1]-final)
        row['pulse_end_s']=s3.PULSE_END;row['observation_after_end_s']=float(t[-1]-s3.PULSE_END)
        row['BNC_peak_V']=float(np.max(np.abs(raw['v(bnc)'])))
        row['BNC_plateau_V']=s3.interp(t,raw['v(bnc)'],6e-6)
        dt=np.diff(t);mask=(t[:-1]<s3.PULSE_END+5e-6)&(t[1:]>=s3.PULSE_START)
        row['max_step_pulse_and_5us_s']=float(dt[mask].max())
        if row['max_step_pulse_and_5us_s']>1.0001e-9 or row['BNC_peak_V']>4.5+1e-9: raise ValueError('B4 resolution/amplitude contract violated')
    elif test == 'B5':
        # Reuse immutable S3 coherent harmonic analysis, with identical raw state.
        transformed=dict(c,test='E13');s3.analyze(transformed,raw,row)
    elif test == 'B6':
        row['output_offset_V']=float(raw['v(out)'][0]);row['output_offset_div']=row['output_offset_V']/s3.DIV_OUT
        row['inplus_V']=float(raw['v(ipa)'][0]);row['inminus_V']=float(raw['v(ima)'][0])
        if c['variant']!='NONE':
            row['diode_p_current_A']=float(raw['i(xprot:dp)'][0]);row['diode_n_current_A']=float(raw['i(xprot:dn)'][0])


def simulate(c,work):
    path=work/(c['id']+'.cir');deck=net(c);write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    record=dict(id=c['id'],returncode=0,errors=[],warnings=[]);row=dict(c)
    try:
        proc=subprocess.run([str(s3.LT),'-b',str(path)],cwd=work,capture_output=True,timeout=3600)
        vals,errors,warnings,log=s3.prior.old.read_log(path.with_suffix('.log'))
        expected={m.lower() for m in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        if expected-set(vals):errors.append('Missing measures '+str(sorted(expected-set(vals))))
        record.update(returncode=proc.returncode,errors=errors,warnings=warnings)
        row.update({k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        if not errors and not proc.returncode:analyze(c,s3.raw_read(path.with_suffix('.raw')),row)
    except Exception as exc:record['errors'].append(repr(exc))
    for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    return (row if not record['errors'] and not record['returncode'] else {}),record


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


def controls():
    jobs=[case('B0',v) for v in VARIANTS]
    for model in ['sheet','original']:
        c=case('B2',control=model);c['noise_model']=model;jobs.append(c)
    return jobs


def jobs(test,smoke,rows):
    indices=[0,6] if smoke else range(12)
    if test in ['B1','B2']: return [case(test,v,i) for v in VARIANTS for i in indices]
    if test=='B3':return [case(test,v,i,polarity='bipolar') for v in VARIANTS for i in [0,1]]
    if test=='B4':return [case(test,v,polarity=p,amplitude_V=a) for v in VARIANTS for a in ([.2] if smoke else [.2,2.,4.5]) for p in ['positive','negative']]
    if test=='B5':
        result=[]
        for v in VARIANTS:
            for i in [0,6]:
                gain=next(r['source_gain_2m'] for r in rows if r['test']=='B1' and r['variant']==v and r['ix']==i)
                result.append(case(test,v,i,polarity='bipolar',vpp=2,bnc_amp=1/gain))
        return result
    if test=='B6':return [case(test,v,i,temp=t) for v in ['NONE',*VARIANTS] for i in [0,5] for t in [25,70]]
    raise ValueError(test)


def criteria(rows,complete):
    result=[]
    for v in VARIANTS:
        by={t:[r for r in rows if r['variant']==v and r['test']==t] for t in ['B0','B1','B2','B3','B4','B5']}
        if not all(by.values()):continue
        a=max(r['u103a_differential_peak_V'] for r in by['B3']);b=max(r['u103b_differential_peak_V'] for r in by['B3'])
        sw=max(r['switch_current_peak_A'] for r in by['B3']);d=max(r[k] for r in by['B3'] for k in ['diode_p_current_peak_A','diode_n_current_peak_A'])
        n=max(r['noise_315m_pct_div'] for r in by['B2'])
        loss=max([r['loss_2m_db'] for r in by['B0']]+[r['s3_loss_2m_db'] for r in by['B1']])
        peak=max([r['peak_db'] for r in by['B0']]+[r['s3_peak_db'] for r in by['B1']])
        rec=[r['recovery_s'] for r in by['B4']];finite=[x for x in rec if x is not None];recovery=max(finite,default=math.inf)
        thd=max(r['thd_pct'] for r in by['B5'])
        tests=[(1,a<=2 and b<=4,f'A={a:.9g} V; B={b:.9g} V; margen B={4-b:.9g} V'),
               (2,sw<=.0125 and d<=.5*(.300 if v in 'AB' else .140),f'4051={sw*1e3:.9g} mA; diodo={d*1e3:.9g} mA'),
               (3,n<=.45,f'{n:.9g} % div; exceso={max(0,n-.45):.9g} puntos'),
               (4,loss<=.5 and peak<=.5,f'perdida={loss:.9g} dB; pico={peak:.9g} dB'),
               (5,None not in rec and recovery<=1e-6,f'{recovery*1e6:.9g} us; sin recuperar={rec.count(None)}'),
               (6,thd<=1,f'THD={thd:.9g} %')]
        for num,ok,value in tests:
            status=('PASA' if ok else 'FALLA') if complete else 'PARCIAL'
            # Model Iave is NOT an independently verified BAT54S sheet rating.
            if num==2 and v in 'AB' and complete and ok:status='CONDICIONAL'
            result.append(dict(variant=v,criterion=f'S3b-C{num}',status=status,value=value))
    return result


METHOD='''
## Método y dudas sin resolver

Fuentes completas leídas: encargo y contrato S3b; plan, acta y auditoría S3;
plan/acta/auditoría S2b; decisiones del 3 oct; revisión de entrada §6 E11–E15
y documento vivo C.3–C.6. No se modifican entregables previos ni modelos.
El ejecutor importa S3 sin escribirlo y reutiliza su lista de conexiones;
ch1_comun_s3b.inc incluye ch1_comun_s3.inc, que incluye S2b. Sólo se inserta
R_SER y dos diodos en sentidos opuestos entre IPA e IMA. CPCB sigue en COMMON.
VIA mide la corriente total que sale del común del 4051; VOUT101 mide toda la
corriente de salida del OPA810, incluida la escalera. Los sensores son fuentes
ideales de 0 V. U103A/B se miden en sus pines IPA/IMA, IPB/IMB.
Ocho SWI1 hc_tnomi reales, sin proxy. Modelos originales en AC/DC/TRAN/OP;
sólo NOISE usa AD8038_ltspice_ruido_hoja.sub. B0 es U103A aislada con
1 kohm paralelo 10 pF de carga como comprobación S3; su barrido llega a 1 GHz
para localizar -3 dB; el pico contractual se comprueba también en B1 a 100 MHz.
B1 informa función S3 OUT/BI y completa OUT/BNC; C4 mantiene el criterio S3
(pérdida de la parte añadida), sin ocultar la pérdida BNC. Rsource=50 ohm
en B1/B2/B5/B6; enlace ideal BNC en B3/B4 para imponer exactamente el estímulo.
Ruido inoise referido a Vsrc, integración del cuadrado de 1 Hz a 3.15/10 MHz
con interpolación del extremo, mismo método que S3. B3 -40 a +40 V, 50 mV;
extremos y número de puntos verificados; .meas y raw contrastados.
B4 flancos 10 ns, ancho 10 us, amplitud máxima 4.5 V; paso global máximo
0.5 ns comprobado en raw. Recuperación desde el FINAL del flanco descendente
a +/-25 mV del punto inicial; se busca última violación, no primer cruce;
30 us de registro, sin redefinir el objetivo por la cola. B5 amplitud del
estímulo calculada desde AC de la misma variante para 2 Vpp; armónicos 2–9,
20 ciclos coherentes y 65536 puntos interpolados, método inmutable de S3.
B6 .op real: extraído del raw, sin inventar una .meas TRAN con otro estado.
Offset añadido = (OUT protegido - OUT S3 sin protección) / 0.25 V por división.

1. No hay hoja local de BAT54S Vishay. El modelo contractual BAT54 de standard.dio
declara Iave=300 mA; el chequeo numérico C2 de A/B usa su mitad, 150 mA,
pero su estatus es CONDICIONAL hasta verificar IF continuo de la pieza dual
en su hoja. La hoja local onsemi BAT54T1G da 200 mA (mitad 100 mA), otra pieza
y otro encapsulado: NO se atribuye ese rating a BAT54S. Sin descargas.
BAV199 Nexperia p2 IF=160 mA con un diodo, 140 mA con ambos: se usa 70 mA,
conservador. 4051 p5 ISW=25 mA, criterio mitad 12.5 mA. Nota de esa página:
caída Y→Z >0.4 V puede sacar corriente de VCC; se informa como limitación
del criterio de corriente sin rediseñar la red. OPA810 p6 a +/-5 V: 52 mA
mín./75 mA típ. de drive lineal con VO=2.65 V, 100 mA típ. en cortocircuito;
son condiciones diferentes de B3, no un máximo absoluto ni garantía a saturación.
2. AD8038 simplificado no representa Ib real de 400 nA ni su deriva; B6 muestra
la contribución del par simétrico y de la resistencia en ESTE modelo, no
predice offset absoluto de placa. No se inyecta Ib artificial fuera del contrato.
BAT54 y BAV199 con mismo modelo en ambos sentidos tampoco incluyen mismatch.
3. BAV199 TT=1.023 us de fabricante; su recuperación puede dominar B4 aunque
proteja bien en DC. El modelo no simula destrucción ni temperatura de unión.
4. S3 conserva CS/CEQ derivados de S2b, no los valores resumidos 1.5 nF/12 pF;
no se retoca ningún valor. Documento vivo aún tiene candidatos/red/ruido antiguos;
mandan decisiones 3 oct y contratos S3/S3b. No se resuelven contradicciones.
5. Se respeta la recuperación aceptada de aproximadamente 0.6 ms tras conducción
de BAV199 de entrada: no se repite ese ensayo. Rieles ideales de S3 no validan
riel real ni prueba física. Sin selección de variante ni diseño S4.
CSV deterministas ordenados, .cir y .log retenidos; raw regenerable eliminado.
'''


def report(rows,records,run,prefix):
    out=ROOT/'resultados';out.mkdir(exist_ok=True)
    for r in rows:
        if r['test']=='B6' and r['variant']!='NONE':
            ref=next(z for z in rows if z['test']=='B6' and z['variant']=='NONE' and z['ix']==r['ix'] and z['temp_C']==r['temp_C'])
            r['baseline_offset_V']=ref['output_offset_V'];r['added_offset_div']=(r['output_offset_V']-ref['output_offset_V'])/s3.DIV_OUT
    crit=criteria(rows,not run['smoke'] and not run['controls_only'] and run['exit_code']==0)
    for test in ['B0','B1','B2','B3','B4','B5','B6']:csv_write(out/f'{prefix}_{test.lower()}.csv',[r for r in rows if r['test']==test])
    csv_write(out/f'{prefix}_resultados.csv',rows);csv_write(out/f'{prefix}_criterios.csv',crit)
    scales=[]
    for a in rows:
        if a['test']!='B1':continue
        n=next((r for r in rows if r['test']=='B2' and r['ix']==a['ix'] and r['variant']==a['variant']),{})
        scales.append({k:a[k] for k in ['variant','scale_V_div','POS','tap','s3_gain_dc','s3_loss_2m_db','s3_peak_db','bnc_loss_2m_db','bnc_peak_db']} | {k:n.get(k) for k in ['noise_315m_uV','noise_315m_pct_div','noise_10m_pct_div']})
    csv_write(out/f'{prefix}_escalas.csv',scales)
    text=f'# ACTA S3b — Protección diferencial de U103A\n\nCódigo {run["exit_code"]}; {run["simulations"]} simulaciones; {run["elapsed_seconds"]:.3f} s; diez trabajadores; errores {run["errors"]}; advertencias {run["warnings"]}.\n\n'
    if run['smoke'] or run['controls_only']:text+='**Comprobación parcial, sin aceptación.**\n\n'
    text+='## Criterios por variante\n\n'+table(crit,['variant','criterion','status','value'])+'\n\n'
    text+='## B0 y controles previos\n\n'+table([r for r in rows if r['test']=='B0'],['variant','gain_dc','minus3_Hz','peak_db','loss_2m_db'])+'\n\n'
    text+=table([r for r in rows if r['test']=='B2' and r['variant']=='NONE'],['noise_model','noise_315m_uV','noise_315m_pct_div','noise_10m_pct_div'])+'\n\n'
    text+='## Por escala y variante\n\n'+table(scales,list(scales[0]) if scales else [])+'\n\n'
    for test,title,columns in [
        ('B3','Barrido estático y márgenes',['variant','scale_V_div','u103a_differential_peak_V','u103b_differential_peak_V','u103b_margin_V','switch_current_peak_A','diode_p_current_peak_A','diode_n_current_peak_A','opa810_current_peak_A','inplus_min_V','inplus_max_V','inplus_rail_margin_V']),
        ('B4','Recuperación desde final de pulso',['variant','amplitude_V','polarity','BNC_plateau_V','recovery_s','terminal_error_V','max_step_pulse_and_5us_s']),
        ('B5','Gran señal',['variant','scale_V_div','output_pp_V','thd_pct','max_dvdt_V_us']),
        ('B6','Offset OP frente a S3',['variant','scale_V_div','temp_C','output_offset_V','baseline_offset_V','added_offset_div'])]:
        text+=f'## {test}: {title}\n\n'+table([r for r in rows if r['test']==test],columns)+'\n\n'
    text+=f'Archivos protegidos: {run["protected_files"]}; cambios detectados: {run["protected_changed"]}.\n\n'
    text+=METHOD
    write(out/f'{prefix}_resumen.md',text)
    write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    if prefix=='s3b':write(ROOT/'ACTA_S3b.md',text)
    return crit


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--controls',action='store_true')
    args=parser.parse_args();start=time.perf_counter();before=protected()
    prefix='s3b_controls' if args.controls else ('s3b_smoke' if args.smoke else 's3b')
    work=ROOT/'S3b'/('controles' if args.controls else ('smoke' if args.smoke else 'generados'));work.mkdir(parents=True,exist_ok=True)
    print('S3b workers=10; B0 and noise controls FIRST',flush=True)
    rows,records=execute(controls(),work)
    for r in rows:
        if r['test']=='B0':print('B0',r['variant'],{k:r[k] for k in ['gain_dc','minus3_Hz','peak_db','loss_2m_db']},flush=True)
        else:print('NOISE CONTROL',r['noise_model'],r['noise_315m_pct_div'],'% div',flush=True)
    control_ok=len(rows)==6 and all(abs(r['noise_315m_pct_div']-({'sheet':.396,'original':.644}[r['noise_model']]))<.001 for r in rows if r['test']=='B2')
    if not control_ok:print('Controls failed: campaign gated off',flush=True)
    if control_ok and not args.controls:
        for test in ['B3','B2','B1','B4','B5','B6']:
            batch=jobs(test,args.smoke,rows);print('STAGE',test,'cases',len(batch),flush=True)
            rr,ss=execute(batch,work);rows+=rr;records+=ss
            print('DONE',test,len(rr),'/',len(batch),flush=True)
            if len(rr)!=len(batch):break
    rows.sort(key=lambda r:r['id']);records.sort(key=lambda r:r['id'])
    changed=[p for p,h in before.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records);warnings=sum(bool(r['warnings']) for r in records)
    run=dict(exit_code=int(bool(errors or changed or not control_ok)),simulations=len(records),errors=errors,warnings=warnings,
             elapsed_seconds=time.perf_counter()-start,workers=10,smoke=args.smoke,controls_only=args.controls,
             protected_files=len(before),protected_changed=changed,records=records)
    crit=report(rows,records,run,prefix)
    print(table(crit,['variant','criterion','status','value']),flush=True)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} warnings={warnings} seconds={run["elapsed_seconds"]:.3f}',flush=True)
    return run['exit_code']


if __name__=='__main__':raise SystemExit(main())
