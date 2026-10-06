"""Contract PLAN_SIMULACION_S2. Ten independent LTspice workers from startup.

No downloads, no imports or writes to S1/S1b. CSV order is independent of workers.
Macromodel results beyond rated supply/common-mode are observations, not proof
of survival. In particular AD8065 explicitly excludes overload recovery.
"""
from __future__ import annotations
import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import math
import re
import subprocess
import time
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parents[2]
MODELS = PROJECT / 'Simulation_LTSpice/models'
LT = Path(r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe')
CPLS = {0: 'DC', 1: 'AC'}
# All acceptance / component limits in this single table. Source pages in acta.
LIMITS = {
    'S2-C1': dict(zin=1e6, zin_pct=2, cin_lo=10, cin_hi=30, delta=2,
                  gain_pct=.5, flat_pct=1, peak_db=.1, fc=10),
    'S2-C2': dict(r1206_w=.125, r1206_v=100, r0805_w=.0625,
                  r0805_v=75, cap_fraction=.8),
    'S2-C3': dict(rail_extension=.5, OPA810_i=.010, AD8065_i=.030,
                  OPA810_diff=7, AD8065_diff=1.8),
    'S2-C4': dict(lo=4.75, hi=5.25),
    'S2-C5': dict(rail=.5),
    'S2-C6': dict(bav_ifsm=4, bav_vr=75, bav_if=.080, tvs_peak=38.8),
    'S2-C7': dict(offset=.0005),
    'S2-C8': dict(thd_pct=.1, bav_current=1e-6),
    'E8': dict(one_div=.005, tenth_div=.0005, aim_s=10e-6),
    'capacitor_ratings': dict(ct1=100, ct2fixed=100, ct2trim=100,
                              cb=50, cs=100, cac=50, ceq=None),
}
R_PARTS = {
    'rt1': ('BNC', 'M', 549e3, '1206'),
    'rt2': ('M', 'TAP', 549e3, '1206'),
    'rb': ('TAP', '0', 11e3, '0805'),
    'rs1': ('BNC', 'RSM', 49.9e3, '1206'),
    'rs2': ('RSM', 'X1', 49.9e3, '1206'),
    'req': ('EQ', '0', 10e6, '0805'),
    'rbias': ('B', '0', 10e6, '0805'),
    'rprot': ('B', 'RAWIN', 1e3, '0805'),
}
C_PARTS = dict(ct1=('BNC', 'M'), ct2fixed=('M', 'TAP'),
               ct2trim=('M', 'TAP'), cb=('TAP', '0'), cs=('BNC', 'X1'),
               cac=('SEL', 'T2'), ceq=('EQ', '0'))


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def csv_write(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def table(rows, keys):
    return ('| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+
            ' |\n'+'\n'.join('| '+' | '.join(str(r.get(k, '')) for k in keys)+' |' for r in rows))


def derived():
    cj = 1.9002e-12/(1+5/1.2722)**.35193
    csel = 2*cj+3e-12+5e-12+2*.5e-12
    rbp = 11e3*10e6/(11e3+10e6)
    rs=R_PARTS['rs1'][2]+R_PARTS['rs2'][2]
    ct1=20e-12;cx1=2e-12;coff=1e-12
    return dict(CJ_POL_pF=cj*1e12, C_SEL_EST_pF=csel*1e12,
                CEQ_pF=csel*1e12, CS_pF=10e6*(cx1+coff+csel)/rs*1e12,
                CB_pF=((ct1/2+coff)*2*549e3/rbp-csel-2e-12)*1e12)


def nominal_gain(pos):
    bias=R_PARTS['rbias'][2]
    rs=R_PARTS['rs1'][2]+R_PARTS['rs2'][2]
    rb=R_PARTS['rb'][2];rbp=rb*bias/(rb+bias)
    return bias/(rs+bias) if pos==1 else rbp/(R_PARTS['rt1'][2]+R_PARTS['rt2'][2]+rbp)


def case(test, buf='OPA810', pos=100, cpl=0, power=1, bleed=0,
         stimulus='zero', temp=25, connection='50ohm', tip=None, step=None, variant='real'):
    # Name identifies the actual circuit, including signed stimulus and power.
    name = (f'{test}_{buf}_pos{pos}_cpl{CPLS[cpl]}_pwr{power}_bleed{bleed}_'
            f'{stimulus}_t{temp}_{connection}_{variant}'+(f'_dt{step}' if step else ''))
    return dict(test=test, buffer=buf, POS=pos, CPL=CPLS[cpl], power=power,
                bleed=bleed, stimulus=stimulus, temperature_C=temp,
                connection=connection, variant=variant, id=name.lower().replace('-', 'neg').replace('.', 'p'), tip=tip, step=step)


def base(c):
    lines = [f'* S2 {c["id"]}',
            f'.include "{ROOT / "comun/ch1_comun_s2.inc"}"',
            f'.include "{MODELS / ("OPA810/opa810_a.lib" if c["buffer"] == "OPA810" else "ad8065.cir")}"',
            '.options numdgt=15 plotwinsize=0 threads=1',
            '.options method=gear solver=alt', f'.temp {c["temperature_C"]}',
            f'XR VP VN RAILS_S2 POWER={c["power"]} BLEED={c["bleed"]}',
            f'XFE BNC RAWIN VP VN M TAP RSM X1 EQ SEL B T2 FRONT_S2 POS={c["POS"]} CPL={0 if c["CPL"]=="DC" else 1}',
            'VIMON RAWIN BI 0',
            'Rladder OUT 0 997.7']
    if c['variant']=='real':
        lines += [f'XBUF BI OUT VP VN OUT BUFFER_{c["buffer"]}']
    else:
        # Diagnostic only: exactly the contractual off-rail 1Mohm load, without
        # an invalid always-on macro-model bias source at zero supply.
        lines += ['Rinput_off BI 0 1e18', 'Routput_off OUT 0 1Meg',
                  '* OFF_LOAD_ONLY: no amplifier model; no input survival claim.']
    return lines


def v(a, b='0'):
    return f'V({a})' if b == '0' else f'V({a},{b})'


def meas(c, analysis, metric, directive):
    return f'.meas {analysis} {c["id"]}_{metric} {directive}'


def source(c):
    stim = c['stimulus']
    if c['test'] == 'E0':
        return ['Vsrc SRC 0 AC 1', 'Vsense BNC SRC 0']
    if c['test'] == 'E9':
        return ['Vsrc SRC 0 0', 'Rsource SRC BNC 50'] if c['connection'] == '50ohm' else []
    if c['test'] == 'E7':
        amp = int(stim.replace('kv', ''))*1000
        # Cap charged at t=0, isolated switch closes at 100ns. No invented L.
        return [f'Cgun GUN 0 150p IC={amp}', 'Resd GUN DISCH 330',
                'Sgun DISCH BNC CTRL 0 GUNSW',
                '.model GUNSW SW(Ron=0.01 Roff=1e18 Vt=0.5 Vh=0)',
                'Vctrl CTRL 0 PULSE(0 1 100n 0.5n 0.5n 3u 6u)',
                'Rgunleak GUN 0 1e18']
    if c['test'] == 'E8':
        amp = int(stim)
        return [f'Vsrc BNC 0 PWL(0 0 1u 0 1.01u {amp} 1.00101m {amp} 1.00102m 0 20m 0)']
    if c['test'] == 'E10':
        return ['Vsrc SRC 0 SINE(0 400 1k)', 'Rsource SRC TIP 50',
                'Rprobe TIP BNC 9Meg', f'Cprobe TIP BNC {c["tip"]:.16g}',
                'Ccable BNC 0 80p']
    if stim == 'sine100':
        return ['Vsrc BNC 0 SINE(0 100 1k)']
    return [f'Vsrc BNC 0 {int(stim)}']


def net(c):
    lines = base(c)+source(c)
    save = [v(n) for n in ['BNC', 'BI', 'RAWIN', 'OUT', 'VP', 'VN', 'SEL', 'B',
                          'M', 'TAP', 'RSM', 'X1', 'EQ', 'T2']]+['I(VIMON)']
    if c['test'] == 'E0':
        g = 'mag(V(OUT)/V(BNC))'
        lines += [meas(c, 'AC', 'zin', 'FIND mag(V(BNC)/I(Vsense)) AT=100'),
                  meas(c, 'AC', 'cin', 'FIND (-im(I(Vsense)/V(BNC))/(2*pi*1Meg)) AT=1Meg'),
                  meas(c, 'AC', 'g1', f'FIND {g} AT=1k'),
                  meas(c, 'AC', 'gmin', f'MIN {g} FROM=10 TO=2Meg'),
                  meas(c, 'AC', 'gmax', f'MAX {g} FROM=10 TO=2Meg'),
                  meas(c, 'AC', 'peak', f'MAX {g} FROM=1 TO=20Meg')]
        if c['CPL'] == 'AC':
            lines += [meas(c, 'AC', 'fc', f'WHEN {g}={c["id"]}_g1/sqrt(2) RISE=1')]
        lines += ['.save '+ ' '.join(save+['I(Vsense)']), '.ac dec 240 1 20Meg', '.end']
        return '\n'.join(lines)+'\n'
    if c['test'] == 'E9':
        lines += [meas(c, 'TRAN', 'offset', 'FIND V(OUT) AT=1u'),
                  meas(c, 'TRAN', 'input_i', 'FIND I(VIMON) AT=1u'),
                  meas(c, 'TRAN', 'bi', 'FIND V(BI) AT=1u')]
        lines += ['.save '+' '.join(save), '.tran 0 1u 0 100n', '.end']
        return '\n'.join(lines)+'\n'
    # E5 continuous DC / last sine cycle; E6 DC equilibrium; E7 pulse window.
    # E8 and E10 also retain all electrical stress data for audit.
    start, stop, dt = 0., 1e-6, 1e-7
    if c['stimulus'] == 'sine100' or c['test'] == 'E10':
        start, stop, dt = .007, .008, .2e-6
    elif c['test'] == 'E7':
        start, stop, dt = 100e-9, 2e-6, c['step'] or .1e-9
    elif c['test'] == 'E8':
        start, stop, dt = 0., .020, 100e-9
    interval = f'FROM={start:.16g} TO={stop:.16g}'
    exprs = dict(vp='V(VP)', vn='V(VN)', bi='V(BI)', differential='V(BI,OUT)',
                 input_i='I(VIMON)',
                 positive_rail_excess='V(BI,VP)', negative_rail_excess='V(VN,BI)',
                 dhp_i='I(XFE:DHP)', dlp_i='I(XFE:DLP)',
                 dhp_reverse='V(VP,SEL)', dlp_reverse='V(SEL,VN)',
                 tvsp_i='I(XR:DtvsP)', tvsn_i='I(XR:DtvsN)',
                 rail_sourcep_i='I(XR:DVP)', rail_sourcen_i='I(XR:DVN)',
                 relay_open='V(SEL,X1)' if c['POS']==100 else 'V(SEL,TAP)',
                 relay_second_open='V(X1,EQ)')
    for label, expr in exprs.items():
        lines += [meas(c, 'TRAN', label+'_max', f'MAX {expr} {interval}'),
                  meas(c, 'TRAN', label+'_min', f'MIN {expr} {interval}')]
        if label.endswith('_i'):
            save.append(expr)
    for label, (a,b,r,size) in R_PARTS.items():
        expr = v(a,b)
        lines += [meas(c, 'TRAN', label+'_v', f'MAX abs({expr}) {interval}'),
                  meas(c, 'TRAN', label+'_p', f'AVG ({expr}**2/{r:.16g}) {interval}')]
        if label in ('rs1','rs2','rprot'):
            lines += [meas(c, 'TRAN', label+'_energy', f'INTEG ({expr}**2/{r:.16g}) {interval}')]
    for label,(a,b) in C_PARTS.items():
        lines += [meas(c, 'TRAN', label+'_v', f'MAX abs({v(a,b)}) {interval}')]
    lines += [meas(c, 'TRAN', 'input_energy', f'INTEG abs(V(BI)*I(VIMON)) {interval}'),
              meas(c, 'TRAN', 'input_charge', f'INTEG abs(I(VIMON)) {interval}')]
    if c['test']=='E7':
        save += ['I(Resd)', 'V(GUN)']
        lines += [meas(c, 'TRAN', 'gun_i_peak', f'MAX abs(I(Resd)) {interval}')]
    if c['test']=='E10':
        lines += ['.four 1k 7 V(OUT)']
    # E7 uses the DC operating point with the charged capacitor IC retained.
    # UIC would leave the amplifier uninitialized and is deliberately avoided.
    lines += ['.save '+' '.join(dict.fromkeys(save)),
              f'.tran 0 {stop:.16g} 0 {dt:.16g}', '.end']
    return '\n'.join(lines)+'\n'


def read_log(path):
    b=path.read_bytes()
    s=b.decode('utf-16' if b.startswith((b'\xff\xfe',b'\xfe\xff')) else 'utf-8',errors='replace')
    vals={}
    for line in s.splitlines():
        m=re.match(r'^([a-z][a-z0-9_]*_fc):.*\sAT\s+([-+0-9.eE]+)\s*$',line,re.I)
        if m:
            vals[m[1].lower()]=float(m[2]);continue
        m=re.match(r'^([a-z][a-z0-9_]*):.*?=\s*(\([^\r\n]+?\)|[-+0-9.eE]+)(?:\s+at|\s+FROM|$)',line,re.I)
        if m:
            db=re.match(r'\(([-+0-9.eE]+)dB,',m[2])
            vals[m[1].lower()]=10**(float(db[1])/20) if db else float(m[2])
    errors=[l for l in s.splitlines() if re.search(r'Fatal|Error:|failed|unknown parameter|unknown subcircuit|singular matrix|Expected device|syntax error|not found',l,re.I)
            and not re.search(r'Direct Newton iteration failed|Gmin stepping failed',l,re.I)]
    warnings=[l for l in s.splitlines() if re.search(r'warning|questionable|timestep too small',l,re.I)]
    return vals,errors,warnings,s


def raw_read(path):
    raw=path.read_bytes()
    marker='Binary:\n'.encode('utf-16le')
    k=raw.index(marker)+len(marker)
    h=raw[:k].decode('utf-16le')
    nv=int(re.search(r'No. Variables:\s*(\d+)',h)[1])
    names=[m[1].lower() for m in re.finditer(r'^\s*\d+\s+(\S+)\s+\S+\s*$',h,re.M)]
    data=np.frombuffer(raw[k:],dtype='<f8').reshape(-1,nv)
    return {n:data[:,i] for i,n in enumerate(names)}


def absmax(row, key):
    return max(abs(row[key+'_max']),abs(row[key+'_min']))


def simulate(c,work):
    path=work/(c['id']+'.cir')
    circuit=net(c)
    write(path,circuit)
    for ext in ('.log','.raw','.op.raw'):
        path.with_suffix(ext).unlink(missing_ok=True)
    proc=subprocess.run([str(LT),'-b',str(path)],cwd=path.parent,capture_output=True)
    record=dict(id=c['id'],file=path.relative_to(ROOT).as_posix(),returncode=proc.returncode,
                errors=[],warnings=[],measures=0)
    if not path.with_suffix('.log').exists():
        record['errors']=['No log generated'];return c,{},record
    vals,errors,warnings,log=read_log(path.with_suffix('.log'))
    expected=set(x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',circuit,re.M|re.I))
    missing=expected-set(vals)
    if missing:errors.append('Missing measures: '+str(sorted(missing)))
    vals={k[len(c['id'])+1:]:value for k,value in vals.items() if k in expected}
    if any(not math.isfinite(x) for x in vals.values()):errors.append('Nonfinite measurement')
    record.update(errors=errors,warnings=warnings,measures=len(vals))
    row={k:value for k,value in c.items() if k not in ('tip','step')}
    row.update(vals)
    if not errors and c['test']=='E0':
        nom=nominal_gain(c['POS'])
        row.update(cin_pF=row['cin']*1e12,gain_error_pct=100*(row['g1']/nom-1),
                   flat_pct=max(abs(row['gmin']/row['g1']-1),abs(row['gmax']/row['g1']-1))*100,
                   peak_db=20*math.log10(row['peak']/row['g1']))
    if not errors and c['test']=='E9':
        gain=nominal_gain(c['POS'])
        row['offset_bnc_v']=row['offset']/gain
    if not errors and c['test'] in ('E7','E8','E10'):
        try:
            raw=raw_read(path.with_suffix('.raw'))
            ts=raw['time'];out=raw['v(out)']
            record['transient_points']=len(ts)
            if c['test']=='E7':
                t0=100e-9;t1=t0+200e-9
                delta=np.diff(ts);mask=(ts[:-1]<t1)&(ts[1:]>t0)
                row['max_step_first200ns']=float(delta[mask].max())
                record['max_step_first200ns']=row['max_step_first200ns']
                if row['max_step_first200ns']>(c['step'] or .1e-9)*1.0001:
                    errors.append('ESD temporal resolution exceeded')
                cur=np.abs(raw['i(resd)']);peak=int(np.argmax(cur))
                # actual monotonic crossings before the peak, no ideal IEC assumption
                pre=np.flatnonzero((ts>=t0)&(np.arange(len(ts))<=peak))
                cross=[]
                for fraction in (.1,.9):
                    ix=pre[cur[pre]>=fraction*cur[peak]]
                    if len(ix):
                        j=int(ix[0]);cross.append(float(np.interp(fraction*cur[peak],cur[j-1:j+1],ts[j-1:j+1])))
                row['gun_rise_10_90_s']=cross[1]-cross[0] if len(cross)==2 else None
                row['gun_peak_time_s']=float(ts[peak]-t0)
                row['gun_initial_v']=float(raw['v(gun)'][0])
                row['gun_final_v']=float(raw['v(gun)'][-1])
                expected_voltage=int(c['stimulus'].replace('kv',''))*1000
                if abs(row['gun_initial_v']-expected_voltage)>abs(expected_voltage)*1e-6:
                    errors.append('ESD capacitor initial voltage differs from charged condition')
                # Displacement current can dominate the pin current in ESD.
            elif c['test']=='E8':
                end=.00100102
                final=float(out[-1]);row['final_output_v']=final
                for name,threshold in [('one_div',LIMITS['E8']['one_div']),('tenth_div',LIMITS['E8']['tenth_div'])]:
                    indices=np.flatnonzero((ts>=end)&(np.abs(out)>threshold))
                    # Stable entry: all later samples remain inside the absolute band.
                    if abs(final)>threshold:
                        row['recovery_'+name+'_s']='not_recovered_20ms'
                    elif len(indices):
                        j=int(indices[-1]);row['recovery_'+name+'_s']=float(ts[min(j+1,len(ts)-1)]-end)
                    else:row['recovery_'+name+'_s']=0.
                # Measured band is absolute zero, not the final offset.
                row['recovery_duration_s']=float(ts[-1]-end)
            else:
                grid=np.linspace(.007,.008,32768,endpoint=False)
                signal=np.interp(grid,ts,out)
                harmonics=np.fft.rfft(signal)/len(signal)
                row['thd_pct']=float(100*np.sqrt(sum(abs(harmonics[j])**2 for j in range(2,8)))/abs(harmonics[1]))
                row['fundamental_vpk']=float(2*abs(harmonics[1]))
                row['CTIP_pF']=c['tip']*1e12
                m=re.search(r'Total Harmonic Distortion:\s*([-+\d.eE]+)%',log,re.I)
                if m:row['lt_four_thd_pct']=float(m[1])
        except Exception as exc:
            errors.append('Raw analysis: '+repr(exc))
    for ext in ('.raw','.op.raw','.db'):
        path.with_suffix(ext).unlink(missing_ok=True)
    return c,({} if errors or proc.returncode else row),record


def execute(cases,work,workers):
    ordered={};records={}
    with futures.ThreadPoolExecutor(max_workers=workers) as pool:
        pending={pool.submit(simulate,c,work):i for i,c in enumerate(cases)}
        for future in futures.as_completed(pending):
            i=pending[future]
            try:
                c,row,record=future.result()
            except Exception as exc:
                c=cases[i];row={};record=dict(id=c['id'],file=c['id']+'.cir',returncode=1,
                                              errors=[repr(exc)],warnings=[],measures=0)
            ordered[i]=row;records[i]=record
            print(f'{c["id"]}: '+('ERROR ('+str(len(record['errors']))+' diagnostics)' if record['errors'] or record['returncode'] else 'OK'),flush=True)
    return [ordered[i] for i in sorted(ordered) if ordered[i]], [records[i] for i in sorted(records)]


def jobs(smoke=False):
    result=[]
    for buf in ('OPA810','AD8065'):
        result += [case('E0',buf,p,c) for p in (1,100) for c in (0,1)]
        for p in (1,100):
            for c in (0,1):
                stims=['100','-100','50','-50','sine100'] if buf=='OPA810' else ['100','-100']
                result += [case('E5',buf,p,c,stimulus=s) for s in stims]
        # Off-channel real buffer included, in addition to specified 1Mohm.
        if buf=='OPA810':
            result += [case('E6',buf,100,c,power=0,bleed=b,stimulus=s,variant=variant)
                       for c in (0,1) for b in (0,1,2) for s in ('100','-100') for variant in ('real','off_load_only')]
        for p in (1,100):
            result += [case('E7',buf,p,stimulus=s) for s in (('4kv','-4kv','8kv','-8kv') if buf=='OPA810' else ('8kv','-8kv'))]
        if buf=='OPA810':
            result += [case('E7',buf,100,power=0,bleed=b,stimulus='8kv',variant=variant)
                       for b in (0,1,2) for variant in ('real','off_load_only')]
        result += [case('E8',buf,1,stimulus=s) for s in ('40','-40')]
        result += [case('E9',buf,p,c,temp=t,connection=con)
                   for p in (1,100) for c in (0,1) for t in (25,85) for con in ('50ohm','air')]
    if smoke:
        # Full E0 required for compensation of E10, plus one of each other family
        # and positive/negative E8. Uses pool from its first simulation.
        keep=[]
        for buf in ('OPA810','AD8065'):
            for test in ('E0','E5','E6','E7','E8','E9'):
                subset=[c for c in result if c['buffer']==buf and c['test']==test]
                keep += subset if test in ('E0','E8') else subset[:2] if test=='E6' else subset[:1]
        return keep
    return result


def assess(rows,complete):
    result=[]
    for buf in ('OPA810','AD8065'):
        r=[x for x in rows if x['buffer']==buf]
        def add(k,text,passed):
            result.append(dict(criterion=k,buffer=buf,value=text,
                               status=('PASA' if passed else 'FALLA') if complete else 'SMOKE/INCOMPLETO'))
        e0=[x for x in r if x['test']=='E0']; lim=LIMITS['S2-C1']
        if len(e0)==4:
            dc=[x for x in e0 if x['CPL']=='DC'];delta=abs(dc[0]['cin_pF']-dc[1]['cin_pF'])
            zin=min(x['zin'] for x in e0),max(x['zin'] for x in e0)
            cin=min(x['cin_pF'] for x in dc),max(x['cin_pF'] for x in dc)
            gain=max(abs(x['gain_error_pct']) for x in e0)
            flat=max(x['flat_pct'] for x in dc);peak=max(x['peak_db'] for x in e0)
            fc=max(x['fc'] for x in e0 if x['CPL']=='AC')
            passed=(all(abs(x/lim['zin']-1)*100<=lim['zin_pct'] for x in zin)
                    and cin[0]>=lim['cin_lo'] and cin[1]<=lim['cin_hi'] and delta<=lim['delta']
                    and gain<=lim['gain_pct'] and flat<=lim['flat_pct'] and peak<=lim['peak_db'] and fc<lim['fc'])
            add('S2-C1',f'Zin {zin[0]/1e6:.6f}–{zin[1]/1e6:.6f} MΩ; Cin {cin[0]:.6f}–{cin[1]:.6f} pF; Δ {delta:.6f} pF; gain {gain:.6f}%; flat {flat:.6f}%; peak {peak:.6f}dB; fc {fc:.6f}Hz',passed)
        e5=[x for x in r if x['test']=='E5']; lim=LIMITS['S2-C2']
        if e5:
            stress=[]
            for x in e5:
                if x['stimulus'] not in ('100','-100','sine100'):continue
                for key,(_,_,_,size) in R_PARTS.items():
                    stress += [(x[key+'_v']/lim['r'+size+'_v'],key+'_v',x[key+'_v']),
                               (x[key+'_p']/lim['r'+size+'_w'],key+'_p',x[key+'_p'])]
                for key,rating in LIMITS['capacitor_ratings'].items():
                    if rating:stress += [(x[key+'_v']/(rating*lim['cap_fraction']),key+'_v',x[key+'_v'])]
            worst=max(stress)
            add('S2-C2',f'worst {worst[1]}={worst[2]:.6g}; {worst[0]:.6f} × derated limit; CEQ rating unspecified',worst[0]<=1)
            rail_lo=min(min(x['vp_min'],-x['vn_max']) for x in e5)
            rail_hi=max(max(x['vp_max'],-x['vn_min']) for x in e5)
            add('S2-C4',f'|rails| {rail_lo:.6f}–{rail_hi:.6f} V',rail_lo>=LIMITS['S2-C4']['lo'] and rail_hi<=LIMITS['S2-C4']['hi'])
        abuse=[x for x in r if x['test'] in ('E5','E6','E7') and x['variant']=='real']
        if abuse:
            excess=max(max(x['positive_rail_excess_max'],x['negative_rail_excess_max']) for x in abuse)
            imax=max(absmax(x,'input_i') for x in abuse)
            diff=max(absmax(x,'differential') for x in abuse)
            lim=LIMITS['S2-C3']
            add('S2-C3',f'VIN beyond rail {excess:.6g} V (<0.5); |IIN| {imax:.6g} A; |differential| {diff:.6g} V',
                excess<lim['rail_extension'] and imax<lim[buf+'_i'] and diff<lim[buf+'_diff'])
        e6=[x for x in r if x['test']=='E6' and x['variant']=='off_load_only']
        if e6:
            bleed={b:max(max(absmax(x,'vp'),absmax(x,'vn')) for x in e6 if x['bleed']==b) for b in sorted(set(x['bleed'] for x in e6))}
            add('S2-C5','OFF_LOAD_ONLY: '+'; '.join(f'bleed{b} {x:.6g} V' for b,x in bleed.items()),min(bleed.values())<=LIMITS['S2-C5']['rail'])
        e7=[x for x in r if x['test']=='E7' and x['variant']=='real']
        if e7:
            bav=max(max(absmax(x,'dhp_i'),absmax(x,'dlp_i')) for x in e7)
            tvs=max(max(absmax(x,'tvsp_i'),absmax(x,'tvsn_i')) for x in e7)
            energy=max(x['input_energy'] for x in e7)
            excess=max(max(x['positive_rail_excess_max'],x['negative_rail_excess_max']) for x in e7)
            imax=max(absmax(x,'input_i') for x in e7)
            diff=max(absmax(x,'differential') for x in e7)
            add('S2-C6',f'BAV |I|={bav:.6g} A vs 4 A/1us; TVS |I|={tvs:.6g} A vs generic 38.8 A; input ∫|VI|={energy:.6g} J; no rated transient energy',
                bav<=LIMITS['S2-C6']['bav_ifsm'] and tvs<=LIMITS['S2-C6']['tvs_peak']
                and excess<LIMITS['S2-C3']['rail_extension'] and imax<LIMITS['S2-C3'][buf+'_i'] and diff<LIMITS['S2-C3'][buf+'_diff'])
            # No pulse-energy allowance exists in the buffer sheets. An integral
            # is reported, never invented as a survival threshold.
        e9=[x for x in r if x['test']=='E9' and x['POS']==1 and x['temperature_C']==25 and x['connection']=='50ohm']
        if e9:
            off=max(abs(x['offset_bnc_v']) for x in e9)
            add('S2-C7',f'|offset BNC|={off*1e3:.6f} mV',off<=LIMITS['S2-C7']['offset'])
        e10=[x for x in r if x['test']=='E10']
        if e10:
            thd=max(x['thd_pct'] for x in e10)
            current=max(max(absmax(x,'dhp_i'),absmax(x,'dlp_i')) for x in e10)
            add('S2-C8',f'THD={thd:.6f}%; |BAV I|={current*1e6:.6f} µA',thd<=LIMITS['S2-C8']['thd_pct'] and current<LIMITS['S2-C8']['bav_current'])
    return sorted(result,key=lambda x:(x['criterion'],x['buffer']))


def findings(rows):
    text='\n## Lo que enseña cada prueba\n\n'
    for buf in ('OPA810','AD8065'):
        r=[x for x in rows if x['buffer']==buf]
        text+=f'### {buf}\n\n'
        e5=[x for x in r if x['test']=='E5']
        if e5:
            values=[]
            for label,(_,_,_,size) in R_PARTS.items():
                values.append(dict(part=label,voltage_V=max(x[label+'_v'] for x in e5),
                                   power_W=max(x[label+'_p'] for x in e5),
                                   voltage_limit_V=LIMITS['S2-C2']['r'+size+'_v'],
                                   power_limit_W=LIMITS['S2-C2']['r'+size+'_w']))
            text+='E5: tensiones pico y potencia media máximas, sin cambiar valores.\n\n'
            text+=table(values,['part','voltage_V','voltage_limit_V','power_W','power_limit_W'])+'\n\n'
            values=[dict(part=label,voltage_V=max(x[label+'_v'] for x in e5),
                         derated_limit_V=rating*LIMITS['S2-C2']['cap_fraction'] if rating else 'SIN DEFINIR')
                    for label,rating in LIMITS['capacitor_ratings'].items()]
            text+=table(values,['part','voltage_V','derated_limit_V'])+'\n\n'
            text+=f'BAV corriente terminal continua/seno máxima: {max(max(absmax(x,"dhp_i"),absmax(x,"dlp_i")) for x in e5):.9g} A. Contactos abiertos: {max(absmax(x,"relay_open") for x in e5):.9g} V.\n\n'
        e6=[x for x in r if x['test']=='E6']
        if e6:
            values=[]
            for variant in sorted(set(x['variant'] for x in e6)):
                for bleed in (0,1,2):
                    g=[x for x in e6 if x['variant']==variant and x['bleed']==bleed]
                    if g:values.append(dict(variant=variant,bleed=bleed,rail_abs_V=max(max(absmax(x,'vp'),absmax(x,'vn')) for x in g),
                                            vp_min_V=min(x['vp_min'] for x in g),vn_max_V=max(x['vn_max'] for x in g)))
            text+='E6: referencia de carga apagada frente al macro no validado a cero alimentación.\n\n'
            text+=table(values,['variant','bleed','rail_abs_V','vp_min_V','vn_max_V'])+'\n\n'
        e7=[x for x in r if x['test']=='E7' and '_dt' not in x['id']]
        if e7:
            values=[]
            for x in e7:
                values.append(dict(POS=x['POS'],power=x['power'],bleed=x['bleed'],variant=x['variant'],
                                   stimulus=x['stimulus'],gun_peak_A=x['gun_i_peak'],rise_ns=x['gun_rise_10_90_s']*1e9 if x['gun_rise_10_90_s'] is not None else 'N/A',
                                   bav_peak_A=max(absmax(x,'dhp_i'),absmax(x,'dlp_i')),
                                   tvs_peak_A=max(absmax(x,'tvsp_i'),absmax(x,'tvsn_i')),
                                   pin_peak_V=absmax(x,'bi'),pin_current_A=absmax(x,'input_i'),
                                   rail_peak_V=max(absmax(x,'vp'),absmax(x,'vn')),
                                   rs_energy_J=x['rs1_energy']+x['rs2_energy'],input_energy_J=x['input_energy']))
            text+='E7: valores del circuito 150pF/330Ω, sin equipararlo a ensayo IEC certificado.\n\n'
            text+=table(values,list(values[0]))+'\n\n'
        e9=[x for x in r if x['test']=='E9'];drift=[]
        for x in e9:
            if x['temperature_C']!=25:continue
            hotter=next((a for a in e9 if a['POS']==x['POS'] and a['CPL']==x['CPL'] and a['connection']==x['connection'] and a['temperature_C']==85),None)
            if hotter:drift.append(dict(POS=x['POS'],CPL=x['CPL'],connection=x['connection'],offset25_bnc_mV=x['offset_bnc_v']*1e3,
                                       offset85_bnc_mV=hotter['offset_bnc_v']*1e3,drift_bnc_uV_C=(hotter['offset_bnc_v']-x['offset_bnc_v'])/(85-25)*1e6))
        if drift:
            text+='E9: fugas/offset y deriva del modelo, referidos a BNC.\n\n'+table(drift,list(drift[0]))+'\n\n'
        e10=[x for x in r if x['test']=='E10']
        if e10:
            x=e10[0]
            text+=f'E10: CTIP={x["CTIP_pF"]:.9g}pF fijo, fundamental {x["fundamental_vpk"]:.9g}Vpk; THD por remuestreo {x["thd_pct"]:.9g}%, por .four {x.get("lt_four_thd_pct","sin dato")}%.\n\n'
    text+='E0 contrasta el nominal real con S1b en s2_s1b_comparacion.csv. E8 se informa en la tabla de recuperación, incluyendo ambas polaridades y segunda fuente. s2_segunda_fuente.csv conserva las diferencias por estado.\n'
    return text


METHOD = '''
## Método, fuentes y dudas sin resolver

Ejecutor Codex; contrato PLAN_SIMULACION_S2, planes S1/S1b, actas y auditorías
leídas completas; DECISIONS 2/3 oct; revisión de entrada §4/§6 y documento vivo
C.6/G.3/G.5/G.6. Sólo S2, este ejecutor, resultados s2_* y diario se escriben.
No ensayos físicos, descargas, modificaciones del diseño ni selección de piezas.

OPA810: hoja local SBOS799E, agosto 2024, p.4: entrada entre VEE−0.5 y VCC+0.5,
corriente continua ±10mA, diferencial ≤min(7V, tensión total de alimentación).
AD8065: hoja local Rev.L, p.9: mismo límite relativo a rieles, diferencial 1.8V;
p.21 admite protección con corriente limitada a 30mA, lo que no equivale a
autorizar cualquier tensión ni una energía ESD. BAV199 Nexperia 1 abril 2023,
p.2: 160mA con un diodo cargado, 140mA con ambos; IFSM 4A/1us, VR75V.
Se informa tanto la corriente terminal total (incluye desplazamiento) como sus
extremos firmados: IFSM es de conducción directa y no valida un pico capacitivo.
La BV=113.3V del modelo no sustituye VR=75V de la hoja. No hay modelo térmico.

1. CIN_BUF=5pF explícita de S1b se conserva por contrato. OPA810 añade 2.5pF
de modo común y 0.5pF diferencial; AD8065 añade 1.1pF por pin y 4pF diferencial
en su modelo (distinto de 6.6pF en hoja). Por tanto la estimación contractual
C_SEL_EST no cuenta toda la capacidad real y E0 no tiene por qué pasar. No se
restan capacidades ni se reajusta CB/CEQ para forzar aceptación.
2. C_EQ no tiene tensión nominal en C.6 ni en el contrato: se informa su tensión,
sin inventar una selección comercial. Los demás ratings usan §3/C.6; C1≥100V
se evalúa conservadoramente a 100V. R/C no están elegidas por MPN: pulse rating,
derating térmico y tensión transitoria todavía requieren hoja de pieza concreta.
3. Las cargas resistivas son 5/42mA y 5/39mA (derivadas, sin redondeo). El buffer
real añade su consumo al equivalente agregado: posible doble conteo en G.3.
El regulador es de entrega unilateral (diodo ideal y 0.5Ω); el interruptor abierto
conserva desacoplo y 1MΩ del contrato y el buffer real. Los modelos de buffers
no garantizan corriente correcta con alimentación ausente; E6 no certifica
ausencia de alimentación parásita en silicio. Se añade OFF_LOAD_ONLY: sin macro
del amplificador, sólo 1MΩ de carga por riel, y entrada observada sin protección
interna. C5 se evalúa sobre esa carga contractual; los resultados REAL se dejan
en el CSV, incluso si invierten la polaridad de los rieles. OFF_LOAD_ONLY no
permite juzgar C3 ni corriente de entrada del buffer. Purga10k/100Ω no se elige.
4. La TVS es genérica, Rs=(10.3−6.67)/(38.8−0.001). BV a 1mA y Rs no obligan
a la ecuación Shockley a cruzar exactamente 10.3V a 38.8A. No se elige SMAJ.
5. ESD: 150pF inicialmente cargados, 330Ω, switch con Ron0.01Ω y mando de
0.5ns a 100ns. Paso global ≤0.1ns; se verifica el .raw en los primeros 200ns.
Sin inductancia ni modelo de arco: la subida medida no es el pulso normativo
IEC. ±8kV se descarga por contacto como pide E7, aunque el requisito es aire.
No demuestra conformidad IEC ni ±100V sin daño. Se informa corriente/energía
y excursión de entrada; no existe energía admisible en hoja para declarar
supervivencia si se exceden los máximos. Los modelos no simulan destrucción.
6. E5 DC usa equilibrio, con fuente ideal rígida, no un escalón de conexión.
En AC se mide el último ciclo de 8ms (100Vpk/1kHz), potencia media y tensión
pico de cada R/C. E6 añade CPL AC además de DC. E7 usa CPL DC; sin alimentación
POS100 forzado. No se hacen extrapolaciones al banco o a hardware conectado.
7. E8: pulso a cada polaridad de 40V, 1ms, flancos10ns, POS1/DC; último instante
fuera de ±5mV/±0.5mV, conservando offset absoluto (no resta del valor final).
Si no se asienta antes de 20ms se indica censura, sin tiempo ficticio. AD8065
declara explícitamente no modelar overload recovery ni distortion: sus tiempos
son observaciones del modelo y no comparación válida del silicio.
8. E9 referencia offset a BNC con ganancia nominal calculada; incluye Vos, fugas
del modelo y bias. Al aire en AC/DC se resuelve equilibrio, sin contaminación
de PCB ni absorción dieléctrica. La deriva es diferencia 85−25°C, no garantía.
9. E10 usa 9MΩ∥CTIP y cable80pF. CTIP se calcula por igualdad de constantes de
tiempo resistivas, con la Cin de POS100/DC medida en E0 a 1MHz; queda fijo.
Es compensación capacitiva nominal de la sonda de S1b, sin ajustar el DUT.
THD con 7 armónicos (2…7/fundamental) en último ciclo, remuestreo32768 puntos;
.four 1k 7 conserva un control independiente en el log. La corriente máxima
de BAV incluye componente capacitiva: también se informa el signo y el pulso.

CSV en orden determinista, pool de10 por defecto, threads=1 por LTspice.
.cir/.log se conservan, .raw regenerables se analizan antes de eliminarlos.
Hash de entregables S1/S1b, modelos, chequeo, STATE/DECISIONS al inicio/final.
Código distinto de cero sólo por errores de simulación/medida; fallos eléctricos
son resultados válidos. El modo smoke usa carpeta y prefijos separados.
'''


def protected_hashes():
    files=[]
    for folder in [ROOT/'S1',ROOT/'S1b',ROOT/'chequeo_claude',MODELS]:
        files += [p for p in folder.rglob('*') if p.is_file() and p.suffix not in ('.raw','.db')]
    files += [p for p in (ROOT/'resultados').glob('s1*') if p.is_file()]
    files += [ROOT/'comun/ch1_comun.inc',ROOT/'comun/ch1_comun_s1b.inc',
              ROOT/'ejecutar_s1.py',ROOT/'ejecutar_s1b.py',ROOT/'ACTA_S1.md',ROOT/'ACTA_S1b.md',
              PROJECT/'ai-context/STATE.md',PROJECT/'ai-context/DECISIONS.md']
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--smoke',action='store_true')
    parser.add_argument('--workers',type=int,default=10)
    args=parser.parse_args()
    if args.workers<1:parser.error('workers must be positive')
    start=time.perf_counter();hashes=protected_hashes()
    work=ROOT/'S2'/('smoke' if args.smoke else 'generados');work.mkdir(parents=True,exist_ok=True)
    out=ROOT/'resultados';out.mkdir(exist_ok=True)
    prefix='s2_smoke' if args.smoke else 's2'
    print(f'S2 pool={args.workers}; smoke={args.smoke}',flush=True)
    rows,records=execute(jobs(args.smoke),work,args.workers)
    # Adaptive E10 depends on E0; unrelated jobs all start in the first pool.
    opa=[x for x in rows if x['test']=='E0' and x['buffer']=='OPA810' and x['POS']==100 and x['CPL']=='DC' and 'cin' in x]
    if opa:
        zin=opa[0]['zin'];cin=opa[0]['cin']
        tip=(cin+80e-12)*zin/9e6
        extra=[case('E10',stimulus='sine400',tip=tip)]
        if not args.smoke:
            # Numerical convergence on worst-coupled ESD path, both buffers.
            extra += [case('E7',buf,1,stimulus=s,step=.05e-9) for buf in ('OPA810','AD8065') for s in ('8kv','-8kv')]
        rr,ss=execute(extra,work,args.workers);rows+=rr;records+=ss
    rows=sorted(rows,key=lambda x:x['id']);records=sorted(records,key=lambda x:x['id'])
    errors=sum(bool(s['errors'] or s['returncode']) for s in records)
    warnings=sum(bool(s['warnings']) for s in records)
    changed=[p for p,h in hashes.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    criteria=assess(rows,not args.smoke and not errors)
    recovery=[x for x in rows if x['test']=='E8']
    differences=[]
    # Match actual state and metric, compare AD8065 − OPA810.
    opa={(x['test'],x['POS'],x['CPL'],x['power'],x['bleed'],x['stimulus'],x['temperature_C'],x['connection'],x['id'].rsplit('_dt',1)[-1] if '_dt' in x['id'] else ''):x
         for x in rows if x['buffer']=='OPA810'}
    for ad in rows:
        if ad['buffer']!='AD8065':continue
        key=(ad['test'],ad['POS'],ad['CPL'],ad['power'],ad['bleed'],ad['stimulus'],ad['temperature_C'],ad['connection'],ad['id'].rsplit('_dt',1)[-1] if '_dt' in ad['id'] else '')
        if key not in opa:continue
        op=opa[key]
        for metric in ('cin_pF','gain_error_pct','flat_pct','offset_bnc_v','recovery_one_div_s','recovery_tenth_div_s','bi_max','bi_min','input_i_max','input_i_min','differential_max','differential_min'):
            if metric not in ad or metric not in op:continue
            av,ov=ad[metric],op[metric]
            differences.append(dict(test=ad['test'],POS=ad['POS'],CPL=ad['CPL'],stimulus=ad['stimulus'],temperature_C=ad['temperature_C'],connection=ad['connection'],metric=metric,OPA810=ov,AD8065=av,delta_AD_minus_OPA=av-ov if isinstance(av,(float,int)) and isinstance(ov,(float,int)) else 'censored'))
    convergence=[]
    for fine in rows:
        if '_dt' not in fine['id']:continue
        baseline=next((x for x in rows if x['id']==fine['id'].rsplit('_dt',1)[0]),None)
        if baseline:
            for metric in ('gun_i_peak','bi_max','bi_min','input_i_max','input_i_min','input_energy'):
                convergence.append(dict(buffer=fine['buffer'],stimulus=fine['stimulus'],metric=metric,step_100ps=baseline[metric],step_50ps=fine[metric],relative_change=abs(fine[metric]-baseline[metric])/max(abs(fine[metric]),1e-30)))
    elapsed=time.perf_counter()-start
    run=dict(exit_code=int(bool(errors)),simulations=len(records),errors=errors,warnings=warnings,
             elapsed_seconds=elapsed,workers=args.workers,smoke=args.smoke,
             protected_files=len(hashes),protected_changed=changed,derived=derived(),records=records)
    for suffix,data in [('resultados',rows),('criterios',criteria),('e8',recovery),('segunda_fuente',differences),('convergencia_esd',convergence)]:
        csv_write(out/f'{prefix}_{suffix}.csv',data)
    comparisons=[]
    with (out/'s1b_resultados.csv').open(encoding='utf-8',newline='') as f:
        baseline=list(csv.DictReader(f))
    for r in rows:
        if r['test']!='E0':continue
        old=next((x for x in baseline if x['campaign']=='N' and x['case']=='nom' and x['POS']==str(r['POS']) and x['CPL']==r['CPL']),None)
        if old:
            for metric in ('zin_ohm','cin_pF','gain_1k'):
                key={'zin_ohm':'zin','gain_1k':'g1'}.get(metric,metric)
                comparisons.append(dict(buffer=r['buffer'],POS=r['POS'],CPL=r['CPL'],metric=metric,S1b=float(old[metric]),S2=r[key],delta=r[key]-float(old[metric])))
    csv_write(out/f'{prefix}_s1b_comparacion.csv',comparisons)
    for test in ('E0','E5','E6','E7','E9','E10'):
        csv_write(out/f'{prefix}_{test.lower()}.csv',[x for x in rows if x['test']==test])
    write(out/f'{prefix}_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    text=f'# Resultados S2 — protección P4b\n\nCódigo {run["exit_code"]}; {len(records)} simulaciones; {errors} con error; {warnings} con advertencia. {elapsed:.3f}s ({elapsed/60:.3f}min), {args.workers} trabajadores.\n\n'
    if args.smoke:text+='**SMOKE: validación del ejecutor, no aceptación.**\n\n'
    text+=table(criteria,['criterion','buffer','value','status'])+'\n\n'
    text+='## Recuperación E8\n\n'+table(recovery,['buffer','stimulus','recovery_one_div_s','recovery_tenth_div_s','final_output_v'])+'\n\n'
    text+='## Derivados contractuales\n\n'+table([derived()],list(derived()))+'\n\n'
    text+=f'Archivos protegidos: {len(hashes)}; cambios: {changed}. Manifest y detalle por estado en `{prefix}_ejecucion.json` y CSV.\n'
    text+=findings(rows)+METHOD
    write(out/f'{prefix}_resumen.md',text)
    if not args.smoke:write(ROOT/'ACTA_S2.md',text.replace('# Resultados S2 — protección P4b','# ACTA S2 — protección P4b',1))
    print(table(criteria,['criterion','buffer','value','status']),flush=True)
    print(f'FINAL exit={run["exit_code"]} sims={len(records)} errors={errors} warnings={warnings} seconds={elapsed:.3f}',flush=True)
    return run['exit_code']


if __name__=='__main__':
    raise SystemExit(main())
