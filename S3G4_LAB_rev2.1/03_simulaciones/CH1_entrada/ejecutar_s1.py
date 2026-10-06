"""Contrato S1: LTspice en lote; todos los resultados proceden de .meas.

Python 3.12 / stdlib. Semilla fija; tolerancias de piezas independientes.
Las piezas de compensacion se calculan nominalmente y permanecen fijas en E4.
Ejecutar: python ejecutar_s1.py (sin descargas ni cambios fuera de CH1_entrada).
"""
from __future__ import annotations
import argparse
import csv
import json
import math
import random
import re
import subprocess
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LT = Path(r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe')
RESULT = ROOT / 'resultados'
WORK = ROOT / 'S1' / 'generados'
CRITERIA = {
    'S1-C1': dict(nom=1e6, tol=.02),
    'S1-C2': dict(lo=10e-12, hi=30e-12, delta=2e-12),
    'S1-C3': dict(tol=.005),
    'S1-C4': dict(flat=.01, peak_db=.1, fc=10.),
    'S1-C5': dict(step=.02),
}
# Multiplicadores de cada pieza. RT1/RT2, RS1/RS2 y CT1/CT2 independientes.
BOUNDS = {
    'FRT1': (.999,1.001), 'FRT2': (.999,1.001), 'FRB': (.999,1.001),
    'FRS1': (.99,1.01), 'FRS2': (.99,1.01), 'FRBIAS': (.99,1.01),
    'FREQ': (.99,1.01), 'FCT1': (.98,1.02), 'FCT2': (.98,1.02),
    'FCB': (.98,1.02), 'FCS': (.98,1.02), 'FCEQ': (.98,1.02),
    'FCAC': (.95,1.05), 'FCOFF': (.5,1.5), 'FCSEL': (.5,1.5),
    'FCIN': (.6,1.4), 'FCJO': (.7,1.3), 'FCX1': (.5,1.5),
    'FCBNC': (2/3,4/3),
}
CPL_NAMES = {0:'DC',1:'AC',2:'GND'}
SIMS = []


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def tag(pos, cpl, ct):
    return f'pos{pos}_cpl{CPL_NAMES[cpl]}_ct1_{ct}p'.lower()


def header(title):
    inc = ROOT / 'comun' / 'ch1_comun.inc'
    return [f'* {title}', f'.include "{inc}"', '.options numdgt=15 plotwinsize=0', 'XR VP VN RAILS']


def instance(t, pos, cpl, ct, factors, bnc=None, out=None):
    args = ' '.join(f'{k}={v:.15g}' for k,v in factors.items())
    return f'X{t} {bnc or "BNC_"+t} {out or "OUT_"+t} VP VN FRONT_P4B POS={pos} CPL={cpl} CT1={ct}p {args}'


def ac_net(title, factors=None, e1=False):
    lines = header(title)
    for ct in (20,12):
        for pos in (1,100):
            for cpl in (0,1,2):
                t = tag(pos,cpl,ct)
                lines += [f'Vsrc_{t} SRC_{t} 0 AC 1', f'Vsense_{t} BNC_{t} SRC_{t} 0', instance(t,pos,cpl,ct,factors or {})]
                lines += [f'.meas AC {t}_zin FIND mag(V(BNC_{t})/I(Vsense_{t})) AT=100',
                          f'.meas AC {t}_cin FIND (-im(I(Vsense_{t})/V(BNC_{t}))/(2*pi*1Meg)) AT=1Meg']
                if cpl==2 or e1:
                    continue
                gain = f'mag(V(OUT_{t})/V(BNC_{t}))'
                lines += [f'.meas AC {t}_g1 FIND {gain} AT=1k',
                          f'.meas AC {t}_gmin MIN {gain} FROM=10 TO=2Meg',
                          f'.meas AC {t}_gmax MAX {gain} FROM=10 TO=2Meg',
                          f'.meas AC {t}_peak MAX {gain} FROM=1 TO=20Meg']
                for hz,label in ((100000,'100k'),(1000000,'1m'),(2000000,'2m')):
                    lines += [f'.meas AC {t}_g{label} FIND {gain} AT={hz}']
                if cpl==1:
                    lines += [f'.meas AC {t}_fc WHEN {gain}={t}_g1/sqrt(2) RISE=1']
    lines += ['.ac dec 240 10 10Meg' if e1 else '.ac dec 240 1 20Meg', '.end']
    return '\n'.join(lines)+'\n'


def tran_net(title, comps, factors=None, only_one=False, maxstep='200n'):
    lines = header(title)
    lines += ['.param FP=1k TR=5n VPK=1 RGEN=50 RPROBE=9Meg CPROBE=10p CCABLE=80p']
    period=1/1000
    edge=5e-9
    t0=1.5*period
    for ct in (20,12):
        for pos in ((1,) if only_one else (1,100)):
            t=tag(pos,0,ct)
            comp=comps[ct]
            lines += [f'Vtip_{t} TIP_{t} 0 PULSE({{-VPK}} {{VPK}} {{0.5/FP}} {{TR}} {{TR}} {{0.5/FP-TR}} {{1/FP}})',
                      f'Rgen_{t} TIP_{t} P_{t} {{RGEN}}', f'Rprobe_{t} P_{t} BNC_{t} {{RPROBE}}',
                      f'Cprobe_{t} P_{t} BNC_{t} {{CPROBE}}', f'Ccable_{t} BNC_{t} 0 {{CCABLE}}']
            if comp>0:
                lines += [f'Ccomp_{t} BNC_{t} 0 {comp:.15g}']
            lines += [instance(t,pos,0,ct,factors or {})]
            # DC reference with the same actual resistors and diode model;
            # symmetry gives low=-V(REF), high=+V(REF), height=2*V(REF).
            lines += [f'Vdc_{t} DCTIP_{t} 0 {{VPK}}', f'Rdcgen_{t} DCTIP_{t} DP_{t} {{RGEN}}',
                      f'Rdcprobe_{t} DP_{t} DBNC_{t} {{RPROBE}}',
                      instance('ref_'+t,pos,0,ct,factors or {},'DBNC_'+t,'REF_'+t),
                      f'.meas TRAN {t}_ref FIND V(REF_{t}) AT={t0:.15g}',
                      f'.meas TRAN {t}_max MAX V(OUT_{t}) FROM={t0:.15g} TO={t0+.4*period:.15g}',
                      f'.meas TRAN {t}_objective MAX abs(V(OUT_{t})-V(REF_{t})) FROM={t0+100e-9:.15g} TO={t0+200e-6:.15g}']
            for us in (2,20,200):
                # Offsets measured from END of 5 ns rising edge.
                at=t0+edge+us*1e-6
                lines += [f'.meas TRAN {t}_v{us} FIND V(OUT_{t}) AT={at:.15g}']
    lines += [f'.tran 0 {t0+.401*period:.15g} 0 {maxstep}', '.end']
    return '\n'.join(lines)+'\n'


def read_log(path):
    b=path.read_bytes()
    text=b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8',errors='replace')
    values={}
    for line in text.splitlines():
        fc=re.match(r'^([a-z][a-z0-9_]*_fc):.*\sAT\s+([-+0-9.eE]+)\s*$',line,re.I)
        if fc:
            values[fc[1].lower()]=float(fc[2])
            continue
        m=re.match(r'^([a-z][a-z0-9_]*):.*?=\s*(\([^\r\n]+?\)|[-+0-9.eE]+)(?:\s+at|\s+FROM|$)',line,re.I)
        if m:
            tok=m[2]
            db=re.match(r'\(([-+0-9.eE]+)dB,',tok)
            values[m[1].lower()]=10**(float(db[1])/20) if db else float(tok)
    errors=[l for l in text.splitlines() if re.search(r'Fatal|Error:|failed|unknown parameter|unknown subcircuit|singular matrix|Expected device|syntax error',l,re.I)]
    warnings=[l for l in text.splitlines() if re.search(r'warning|questionable|timestep too small',l,re.I)]
    return values,errors,warnings


def simulate(path, net):
    write(path,net)
    # Remove stale output; an unsuccessful run must never reuse earlier .meas.
    for ext in ('.log','.raw'):
        path.with_suffix(ext).unlink(missing_ok=True)
    start=time.monotonic()
    proc=subprocess.run([str(LT),'-b',str(path)],cwd=path.parent,capture_output=True,timeout=180)
    log=path.with_suffix('.log')
    if not log.exists():
        raise RuntimeError(f'{path.name}: no log, process={proc.returncode}')
    values,errors,warnings=read_log(log)
    expected=set(s.lower() for s in re.findall(r'^\.meas\s+\w+\s+(\w+)',net,re.M|re.I))
    # LTspice Options:numdgt=15 plotwinsize=0 resembles a scalar log entry.
    # Accept only exact names declared in this netlist, never metadata.
    values={k:v for k,v in values.items() if k in expected}
    if set(values)!=expected:
        errors.append(f'Missing declared measures: {sorted(expected-set(values))}')
    SIMS.append(dict(file=str(path.relative_to(ROOT)),returncode=proc.returncode,
                     seconds=time.monotonic()-start,errors=errors,warnings=warnings,measures=len(values)))
    if proc.returncode or errors or not values:
        raise RuntimeError(f'{path.name}: return={proc.returncode}; errors={errors}; measures={len(values)}')
    # .raw regenerable; keep netlists and logs, not hundreds of redundant waveforms.
    path.with_suffix('.raw').unlink(missing_ok=True)
    path.with_suffix('.op.raw').unlink(missing_ok=True)
    path.with_suffix('.db').unlink(missing_ok=True)
    return values


def metrics(ac, tr=None):
    rows=[]
    for ct in (20,12):
        delta=abs(ac[tag(1,0,ct)+'_cin']-ac[tag(100,0,ct)+'_cin'])
        for pos in (1,100):
            for cpl in (0,1,2):
                t=tag(pos,cpl,ct)
                r=dict(CT1_pF=ct,POS=pos,CPL=CPL_NAMES[cpl],zin_ohm=ac[t+'_zin'],cin_pF=ac[t+'_cin']*1e12,delta_cin_pF=delta*1e12)
                if cpl!=2 and t+'_g1' in ac:
                    nominal=10e6/(99800+10e6) if pos==1 else (11000*10e6/(11000+10e6))/(2*549000+11000*10e6/(11000+10e6))
                    g=ac[t+'_g1']
                    r.update(gain_1k=g,nominal_gain=nominal,gain_error_pct=100*(g/nominal-1),
                             flat_min_pct=100*(ac[t+'_gmin']/g-1),flat_max_pct=100*(ac[t+'_gmax']/g-1),
                             peak_db=20*math.log10(ac[t+'_peak']/g))
                    for label in ('100k','1m','2m'):
                        r['dev_'+label+'_pct']=100*(ac[t+'_g'+label]/g-1)
                    if cpl==1:
                        r['fc_hz']=ac[t+'_fc']
                if cpl==0 and tr is not None:
                    ref=tr[t+'_ref']; height=2*abs(ref)
                    r.update(step_height_v=height,overshoot_pct=100*max(0,tr[t+'_max']-ref)/height,
                             objective_pct=100*tr[t+'_objective']/height)
                    for us in (2,20,200):
                        r[f'error_{us}us_pct']=100*(tr[t+f'_v{us}']-ref)/height
                rows.append(r)
    return rows


def evaluate(rows):
    ans=[]
    def add(r,c,value,ok):
        ans.append(dict(criterion=c,CT1_pF=r['CT1_pF'],POS=r['POS'],CPL=r['CPL'],value=value,status='PASA' if ok else 'FALLA'))
    for r in rows:
        if r['CPL']=='GND':
            continue
        c=CRITERIA['S1-C1']; add(r,'S1-C1',f"{r['zin_ohm']/1e6:.6f} Mohm",abs(r['zin_ohm']/c['nom']-1)<=c['tol'])
        if r['CPL']=='DC':
            c=CRITERIA['S1-C2']; add(r,'S1-C2',f"Cin={r['cin_pF']:.6f} pF; delta={r['delta_cin_pF']:.6f} pF",c['lo']<=r['cin_pF']*1e-12<=c['hi'] and r['delta_cin_pF']*1e-12<=c['delta'])
        if 'gain_error_pct' in r:
            add(r,'S1-C3',f"G={r['gain_1k']:.9g}; error={r['gain_error_pct']:+.6f}%",abs(r['gain_error_pct'])<=100*CRITERIA['S1-C3']['tol'])
            c=CRITERIA['S1-C4']
            if r['CPL']=='DC':
                add(r,'S1-C4',f"[{r['flat_min_pct']:+.6f}, {r['flat_max_pct']:+.6f}]%; pico={r['peak_db']:+.6f} dB",max(abs(r['flat_min_pct']),abs(r['flat_max_pct']))<=100*c['flat'] and r['peak_db']<=c['peak_db'])
            else:
                add(r,'S1-C4',f"fc={r['fc_hz']:.6f} Hz",r['fc_hz']<c['fc'])
        if 'overshoot_pct' in r:
            c=CRITERIA['S1-C5']; add(r,'S1-C5',f"sobre={r['overshoot_pct']:.6f}%; e2={r['error_2us_pct']:+.6f}%",max(r['overshoot_pct'],abs(r['error_2us_pct']))<=100*c['step'])
    return ans


def csv_write(path, rows):
    keys=list(dict.fromkeys(k for row in rows for k in row))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=keys); w.writeheader(); w.writerows(rows)


def md_table(rows,keys):
    return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+'\n'.join('| '+' | '.join(str(r.get(k,'')) for k in keys)+' |' for r in rows)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke',action='store_true'); args=parser.parse_args()
    RESULT.mkdir(exist_ok=True); WORK.mkdir(parents=True,exist_ok=True)
    (RESULT/'s1_error.json').unlink(missing_ok=True)
    ac1=simulate(ROOT/'S1/E1_zin.cir',ac_net('E1 nominal',e1=True))
    ac=simulate(ROOT/'S1/E2_respuesta.cir',ac_net('E2 nominal'))
    # Independent E1 and E2 measurements must agree at common frequencies.
    for k,v in ac1.items():
        if not math.isclose(v,ac[k],rel_tol=2e-5,abs_tol=1e-18):
            raise RuntimeError(f'E1/E2 inconsistency {k}: {v} vs {ac[k]}')
    if args.smoke:
        tr=simulate(ROOT/'S1/E3_sonda.cir',tran_net('E3 smoke',dict.fromkeys((20,12),0)))
        print(json.dumps(metrics(ac,tr),indent=2)); return 0
    sweeps=[]; best={20:(math.inf,0),12:(math.inf,0)}
    def sweep(values,prefix):
        for i,c in enumerate(values):
            tr=simulate(WORK/f'{prefix}_{i:03d}.cir',tran_net('E3 CCOMP sweep',dict.fromkeys((20,12),c)))
            for ct in (20,12):
                t=tag(100,0,ct); score=tr[t+'_objective']/(2*abs(tr[t+'_ref']))
                sweeps.append(dict(stage=prefix,CT1_pF=ct,CCOMP_pF=c*1e12,objective_pct=100*score))
                if score<best[ct][0]: best[ct]=(score,c)
            if i%10==0: print(f'{prefix}: {i+1}/{len(values)}',flush=True)
    sweep([i*2e-12 for i in range(31)],'sonda_grueso')
    fine=sorted(set(max(0,best[ct][1]+i*.1e-12) for ct in (20,12) for i in range(-20,21)))
    sweep(fine,'sonda_fino')
    comps={ct:best[ct][1] for ct in (20,12)}
    tr=simulate(ROOT/'S1/E3_sonda.cir',tran_net('E3 nominal; CCOMP fixed in POS100',comps))
    nominal=metrics(ac,tr); criteria=evaluate(nominal)
    allrows=[dict(campaign='nominal',case='nominal',**r) for r in nominal]
    rng=random.Random(20261002); samples=[]; sensitivity=[]
    for i in range(200):
        factors={k:rng.uniform(*b) for k,b in BOUNDS.items()}
        case=f'mc_{i:03d}'; samples.append(dict(case=case,**factors))
        path=ROOT/'S1/E4_mc.cir' if i==0 else WORK/f'{case}_ac.cir'
        a=simulate(path,ac_net(f'E4 {case}; seed=20261002',factors))
        t=simulate(WORK/f'{case}_tran.cir',tran_net(f'E4 {case}; nominal CCOMP',comps,factors,only_one=True))
        # POS100 E3 not required by E4; only POS1 metrics attach transient.
        rs=metrics(a)
        for r in rs:
            if r['POS']==1 and r['CPL']=='DC':
                tt=tag(1,0,r['CT1_pF']); ref=t[tt+'_ref']
                r['overshoot_pct']=100*max(0,t[tt+'_max']-ref)/(2*abs(ref))
        allrows.extend(dict(campaign='MonteCarlo',case=case,**r) for r in rs)
        if i%20==0: print(f'Monte Carlo: {i+1}/200',flush=True)
    for param,bounds in BOUNDS.items():
        for side,v in zip(('min','max'),bounds):
            case=f'{param}_{side}'
            a=simulate(WORK/f'sens_{case}.cir',ac_net(f'E4 sensitivity {case}',{param:v}))
            rs=metrics(a)
            allrows.extend(dict(campaign='sensibilidad',case=case,**r) for r in rs)
            for r in rs:
                if r['CPL']=='DC':
                    base=next(n for n in nominal if n['CT1_pF']==r['CT1_pF'] and n['POS']==r['POS'] and n['CPL']=='DC')
                    sensitivity.append(dict(parameter=param,extreme=side,factor=v,CT1_pF=r['CT1_pF'],POS=r['POS'],delta_cin_pF=r['delta_cin_pF'],shift_delta_pF=r['delta_cin_pF']-base['delta_cin_pF'],dev_1m_pct=r['dev_1m_pct'],shift_dev_1m_pct=r['dev_1m_pct']-base['dev_1m_pct']))
        print(f'Sensibilidad: {param}',flush=True)
    # Temporal resolution check, not a design modification.
    fine_tr=simulate(WORK/'verificacion_paso.cir',tran_net('E3 temporal convergence 50ns',comps,maxstep='50n'))
    convergence=[]
    for r in metrics(ac,fine_tr):
        if 'overshoot_pct' in r:
            base=next(n for n in nominal if n['CT1_pF']==r['CT1_pF'] and n['POS']==r['POS'] and n['CPL']=='DC')
            convergence.append(dict(CT1_pF=r['CT1_pF'],POS=r['POS'],shift_overshoot_pp=r['overshoot_pct']-base['overshoot_pct'],shift_error2_pp=r['error_2us_pct']-base['error_2us_pct']))
    csv_write(RESULT/'s1_resultados.csv',allrows); csv_write(RESULT/'s1_criterios.csv',criteria)
    csv_write(RESULT/'s1_sonda_barrido.csv',sweeps); csv_write(RESULT/'s1_mc_parametros.csv',samples)
    csv_write(RESULT/'s1_sensibilidad.csv',sensitivity); csv_write(RESULT/'s1_convergencia.csv',convergence)
    errors=sum(bool(s['errors'] or s['returncode']) for s in SIMS); warnings=sum(bool(s['warnings']) for s in SIMS)
    write(RESULT/'s1_ejecucion.json',json.dumps(dict(simulations=SIMS,CCOMP_pF={k:v*1e12 for k,v in comps.items()},errors=errors,warnings=warnings,exit_code=int(bool(errors)),seed=20261002),indent=2))
    dc=[r for r in allrows if r['campaign']=='MonteCarlo' and r['CPL']=='DC']
    ranges=[]
    for ct in (20,12):
        for pos in (1,100):
            for cpl in ('DC','AC','GND'):
                group=[r for r in allrows if r['campaign']=='MonteCarlo' and r['CT1_pF']==ct and r['POS']==pos and r['CPL']==cpl]
                for metric in ('zin_ohm','cin_pF','delta_cin_pF','dev_100k_pct','dev_1m_pct','dev_2m_pct','overshoot_pct'):
                    numbers=sorted(r[metric] for r in group if metric in r)
                    if numbers:
                        ranges.append(dict(CT1_pF=ct,POS=pos,CPL=cpl,metric=metric,n=len(numbers),minimum=numbers[0],maximum=numbers[-1],median=(numbers[99]+numbers[100])/2))
    csv_write(RESULT/'s1_mc_rangos.csv',ranges)
    worst_delta=max(dc,key=lambda r:r['delta_cin_pF']); worst_dev=max(dc,key=lambda r:abs(r['dev_1m_pct']))
    dom_delta=max(sensitivity,key=lambda r:abs(r['shift_delta_pF'])); dom_dev=max(sensitivity,key=lambda r:abs(r['shift_dev_1m_pct']))
    summary='# Resultados S1 — LTspice\n\n'
    summary+=f'Código de salida: {int(bool(errors))}. Simulaciones: {len(SIMS)}; con error: {errors}; con advertencia: {warnings}. Semilla: 20261002. MC: 200 muestras, ambas CT1.\n\n'
    summary+='## Criterios nominales\n\n'+md_table(criteria,['criterion','CT1_pF','POS','CPL','value','status'])+'\n\n'
    summary+='## E1 GND (sólo informe)\n\n'+md_table([r for r in nominal if r['CPL']=='GND'],['CT1_pF','POS','zin_ohm','cin_pF'])+'\n\n'
    summary+='## E3\n\n'+f'CCOMP (pF): { {k:v*1e12 for k,v in comps.items()} }.\n\n'+md_table([r for r in nominal if 'overshoot_pct' in r],['CT1_pF','POS','step_height_v','overshoot_pct','error_2us_pct','error_20us_pct','error_200us_pct'])+'\n\n'
    summary+='## E4\n\n'
    for label,r in [('Peor ΔCin MC',worst_delta),('Peor desviación 1 MHz MC',worst_dev),('Dominante ΔCin (uno por uno)',dom_delta),('Dominante 1 MHz (uno por uno)',dom_dev)]:
        summary+=f'- {label}: {r}\n'
    summary+='\n'+md_table(sensitivity,['parameter','extreme','factor','CT1_pF','POS','delta_cin_pF','shift_delta_pF','dev_1m_pct','shift_dev_1m_pct'])+'\n'
    summary+='\n## Rangos Monte Carlo\n\n'+md_table(ranges,['CT1_pF','POS','CPL','metric','n','minimum','maximum','median'])+'\n'
    write(RESULT/'s1_resumen.md',summary)
    acta=summary.replace('# Resultados S1 — LTspice','# ACTA S1 — entrada pasiva P4b de CH1',1)
    acta+='''

## Alcance, métodos y evidencia

Ejecutor: Codex. Contrato: `PLAN_SIMULACION_S1.md`, §§2–6; auditoría previa leída:
`../P4_P7_grueso/AUDITORIA_CLAUDE_P4_P7.md`. Fuentes de diseño consultadas:
`../../01_diseno/revision_entrada_ch1.html`, §4, y memoria S3G4 vía MCP.
No se prueban placas, protecciones de ±100 V/ESD, amplificadores reales ni etapas S2–S8.
No se cambian valores del diseño, ni se seleccionan ajustables.

Los `.cir` y `.log` de cada ejecución están en `S1/` y `S1/generados/`.
`resultados/s1_ejecucion.json` identifica cada simulación, número de medidas,
estado del proceso, errores y advertencias. Las formas de onda regenerables se
eliminan para limitar espacio. `ejecutar_s1.py` genera y ejecuta todo de nuevo;
la semilla 20261002 y los factores efectivos figuran en `s1_mc_parametros.csv`.
El CSV largo contiene nominales, MC y sensibilidad; los criterios nominales
están en `s1_criterios.csv`. El código no considera un criterio fallido como
error de simulación. `--smoke` es sólo una comprobación corta, no la campaña.

E1 usa 240 puntos/década, 10 Hz–10 MHz; E2, 240 puntos/década, 1 Hz–20 MHz.
La fuente de 0 V tiene su terminal positivo en BNC y negativo en SRC: su
corriente es la que retorna a la fuente, de modo que la fórmula contractual
−Im(I/V)/(2πf) da la Cin positiva de la entrada. Las medidas repetidas de E1
y E2 se comparan automáticamente. Cada nombre contiene POS, CPL y CT1 nominal;
en MC, la CT1 efectiva es el producto de la nominal por el factor registrado.

E2 normaliza la planitud y el pico a la ganancia medida a 1 kHz. El pico es
el máximo de todo el barrido 1 Hz–20 MHz; la planitud DC se limita a 10 Hz–2 MHz.
La frecuencia baja AC usa el primer cruce ascendente de G(1 kHz)/sqrt(2).
La nominal de S1-C3 se calcula con la fórmula del contrato, sin introducir
los factores de tolerancia para cambiar la referencia nominal.

E3 usa CPL=DC. La sonda tiene 9 MΩ∥10 pF, cable de 80 pF y fuente de 50 Ω.
CCOMP físico no negativo se barre de 0 a 60 pF en incrementos de 2 pF y luego
se refina a 0.1 pF alrededor del mínimo (±2 pF, truncado en cero). La función
objetivo es el máximo error absoluto entre 0.1 y 200 µs después del inicio
del segundo flanco ascendente, en POS100. El CCOMP elegido se conserva en
POS1 y en MC. El fichero `s1_sonda_barrido.csv` registra todos los puntos.
El nivel alto de referencia se mide con una copia DC del mismo circuito y
sonda; por simetría el nivel bajo es su negativo y la altura es 2·Vref.
Los errores se dividen por esa altura, nunca por el nivel alto. Los tiempos
2, 20 y 200 µs se cuentan desde el final de los 5 ns de subida.
El sobreimpulso es max(0,Vmax−Vref)/altura, entre 0 y 400 µs después del
flanco. Esto no confunde una respuesta que queda por debajo con sobreimpulso.
`s1_convergencia.csv` compara pasos máximos de 200 ns y 50 ns.

E4 aplica distribuciones uniformes a todas las piezas indicadas, con 200
muestras por cada CT1 y estado E1/E2. RT1 y RT2, RS1 y RS2, Ct1 y Ct2
tienen variaciones independientes; RBIAS y REQ también. El parámetro CJO
es compartido por ambos diodos. Los factores de parásitas son comunes a
los contactos de la misma clase. Las mismas muestras se usan en ambos POS,
CPL y CT1 para comparar posiciones del mismo circuito. CB, CS y CEQ se
calculan con las piezas nominales y después reciben sólo su propia tolerancia;
no se reajustan en cada muestra. E3 MC cubre POS1 con la compensación nominal.
La sensibilidad de uno en uno contiene ambos extremos de los 19 factores.

## Lo que enseña cada prueba

E1 distingue la impedancia de baja frecuencia de la capacidad efectiva a
1 MHz. DC y AC cumplen nominalmente S1-C1; ambas CT1 cumplen nominalmente
S1-C2. GND cambia la carga vista por la BNC y sólo se informa, según contrato.
E2 cumple nominalmente S1-C3 y S1-C4 en los estados ensayados. El divisor
siempre conectado y el acoplamiento capacitivo producen pequeños desplazamientos
de la ganancia respecto a la nominal resistiva, incluso a 1 kHz.
E3 falla S1-C5 en ambos POS para las dos CT1: la mejor CCOMP ensayada está
en el límite inferior, cero. El fallo es el error del escalón, no sobreimpulso.
E4 muestra la dispersión y separa el efecto de cada factor del efecto conjunto.
El peor punto MC no se atribuye a una sola pieza: la muestra tiene múltiples
variaciones simultáneas. Los parámetros dominantes arriba son los que mayor
desplazamiento producen en la sensibilidad de uno en uno. Son magnitudes
distintas del peor valor absoluto MC. E4 no tiene umbral de aceptación.

## Dudas y contradicciones, sin resolver

1. El contrato estima la carga SEL usando 2·CJO, pero CJO=1.5 pF es la
   capacidad a cero voltios del modelo. Con los diodos polarizados inversamente
   por los rieles ±5 V, su capacidad de pequeña señal es inferior. No se
   reemplaza el modelo ni se cambia la fórmula de compensación.
2. `revision_entrada_ch1.html` §4 muestra CS≈1.5 nF y CEQ≈12 pF, y el
   contrato da valores derivados que no son esos redondeos. La referencia
   de auditoría (27.7 pF y −0.3 %) omite diodos y SW1. Aquí se incluyen una
   sola vez los diodos, las dos capacidades de tiros abiertos de SW1 y CIN
   detrás de RPROT; no se fuerzan los resultados a coincidir con el chequeo.
3. C_SEL_EST suma sólo una COFF_SW, mientras el circuito exige capacitancia
   entre el común y cada tiro abierto. En DC hay dos tiros abiertos; uno
   conecta a T2, ligado capacitivamente a SEL por CAC. Se conserva tanto la
   fórmula como la topología especificada, sin resolver su aproximación.
4. El contrato no fija resistencia de SW1 ni fuga resistiva de contactos.
   Se representa el contacto cerrado de SW1 con 0.1 Ω (igual a RON_RELE)
   y el abierto con 1e18 Ω, con la capacitancia contractual sólo en abierto.
   Son elecciones numéricas del banco, no decisiones de pieza física.
5. E3 no fija rango de CCOMP, función de error, flanco de referencia ni CPL.
   Los métodos se explicitan arriba. El mínimo físico obtenido está en
   cero; no se introduce una capacidad negativa para compensar. La combinación
   de cable de 80 pF y capacidad de entrada ya supera los 90 pF de la relación
   resistiva ideal 9 MΩ/1 MΩ con 10 pF en la punta. La compensación una sola
   vez solicitada no logra S1-C5 con esta sonda contractual.
6. E2 no repite explícitamente el barrido de CT1 de E1 y E4 no especifica
   estados ni correlación entre piezas. Se cubren ambas CT1 y todos los
   estados de E1; E2 cubre DC/AC, y E3 DC. Las correlaciones elegidas están
   documentadas; no equivalen a una caracterización estadística de piezas reales.
7. E4 dice «decide si C_EQ y/o Cb llevan ajustable», pero §7 prohíbe elegir
   ajustables o recomendar cambios. Se entregan medidas de sensibilidad y
   dispersión, dejando esa decisión al auditor y al usuario.

No se editan `STATE.md`, `DECISIONS.md`, `chequeo_claude/`, P4/P7 ni documentos
de diseño. Se escribe únicamente esta carpeta y el diario autorizado.
'''
    write(ROOT/'ACTA_S1.md',acta)
    print(summary.split('## E1')[0],flush=True)
    print('E4 worst:',json.dumps(dict(delta=worst_delta,dev=worst_dev,dominant_delta=dom_delta,dominant_dev=dom_dev)))
    return int(bool(errors))


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (RuntimeError,subprocess.TimeoutExpired,KeyError,ValueError,OSError) as exc:
        RESULT.mkdir(exist_ok=True)
        write(RESULT/'s1_error.json',json.dumps(dict(error=str(exc),simulations=SIMS),indent=2))
        print(f'ERROR DE SIMULACION/MEDIDA: {exc}',flush=True)
        raise SystemExit(1)
