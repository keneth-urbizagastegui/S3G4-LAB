"""Audit campaign coverage, state names, numerical checks and relocated replay."""
import csv
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]


def main():
    started=time.perf_counter()
    run=json.loads((ROOT/'resultados/s2b_ejecucion.json').read_text(encoding='utf-8'))
    rows=list(csv.DictReader((ROOT/'resultados/s2b_resultados.csv').open(encoding='utf-8',newline='')))
    issues=[];names=0
    if run['exit_code'] or run['errors'] or run['protected_changed']:issues.append('Campaign errors')
    if len(rows)!=run['simulations'] or len({r['id'] for r in rows})!=len(rows):issues.append('Unique rows / manifest mismatch')
    required={'OPA810':{'E0b':4,'E5b':12,'E7b':11,'E7c':18,'E9':16},
              'OPA828':{'E0b':4,'E5b':8,'E7b':10,'E7c':18,'E9':16}}
    for buf,tests in required.items():
        if buf=='OPA828' and not run['second_source']:continue
        for test,n in tests.items():
            actual=sum(r['buffer']==buf and r['s2b_test']==test for r in rows)
            if actual!=n:issues.append(f'Coverage {buf}/{test}: {actual} expected {n}')
    if sum(r['s2b_test']=='E7a' for r in rows)!=3:issues.append('Calibration coverage')
    for r in rows:
        file=ROOT/'S2b/generados'/(r['id']+'.cir');text=file.read_text(encoding='utf-8')
        measures=re.findall(r'^\.meas\s+\w+\s+(\w+)',text,re.M|re.I);names+=len(measures)
        if any(not m.startswith(r['id']+'_') for m in measures):issues.append('Name mismatch '+r['id'])
        if 'threads=1' not in text:issues.append('Internal threads '+r['id'])
        if r['s2b_test']=='E7a':
            if 'Rtarget BNC 0 2' not in text or 'XFE ' in text:issues.append('Calibration actual target')
        else:
            if f'POS={r["POS"]} CPL={0 if r["CPL"]=="DC" else 1}' not in text:issues.append('POS/CPL mismatch '+r['id'])
            if f'POWER={r["power"]} BLEED={r["bleed"]}' not in text:issues.append('Power/bleed mismatch '+r['id'])
            if (r['variant']=='real')!=('XBUF ' in text):issues.append('Buffer variant '+r['id'])
            kind='810' if r['buffer']=='OPA810' else '828'
            if '.param BUFFER_KIND='+kind not in text:issues.append('Capacitance selection '+r['id'])
        if r['test']=='E7':
            if float(r['max_step_first100ns'])>run['limits']['numerical']['first100ns_step']*1.0001:issues.append('Raw step '+r['id'])
            voltage=int(r['stimulus'].replace('kv',''))*1000
            if f'IC={voltage}' not in text:issues.append('Signed stimulus '+r['id'])
            arc=run['generator']['Rair'] if r['mode']=='air' else run['generator']['Rcontact']
            if f'Rarc ARC BNC {arc:.16g}' not in text:issues.append('Air/contact actual state')
    include=(ROOT/'comun/ch1_comun_s2b.inc').read_text(encoding='utf-8')
    if 'CIN_BUF=0' not in include or 'CSEL_PAR+CBUF_EST+2*COFF_SW' not in include:issues.append('Capacitance bookkeeping')
    # A short clean path avoids LTspice legacy MAX_PATH errors. Only dependencies
    # needed by S2b are copied; existing S1/S1b/S2 and models remain read-only.
    scratch=Path(tempfile.mkdtemp(prefix='s2b_'))/'CH1_entrada';scratch.mkdir()
    (scratch/'comun').mkdir()
    for name in ('ejecutar_s2b.py','ejecutar_s2.py'):shutil.copy2(ROOT/name,scratch/name)
    shutil.copy2(ROOT/'comun/ch1_comun_s2b.inc',scratch/'comun/ch1_comun_s2b.inc')
    env=dict(os.environ)
    env['S3G4_MODELS']=str(Path(env.get('S3G4_MODELS',str(ROOT.parents[2]/'Simulation_LTSpice/models'))).resolve())
    replay=subprocess.run(['python',str(scratch/'ejecutar_s2b.py')],cwd=scratch,env=env,capture_output=True,text=True)
    (ROOT/'S2b/replay_stdout.log').write_text(replay.stdout,encoding='utf-8')
    (ROOT/'S2b/replay_stderr.log').write_text(replay.stderr,encoding='utf-8')
    if replay.returncode:issues.append('Relocated replay exit '+str(replay.returncode))
    comparison=[]
    for p in sorted((ROOT/'resultados').glob('s2b_*.csv')):
        if p.name.startswith('s2b_smoke_'):continue
        other=scratch/'resultados'/p.name
        a=hashlib.sha256(p.read_bytes()).hexdigest();b=hashlib.sha256(other.read_bytes()).hexdigest() if other.exists() else None
        comparison.append(dict(file=p.name,original_sha256=a,replay_sha256=b,identical=a==b))
        if a!=b:issues.append('CSV differs '+p.name)
    replayrun=json.loads((scratch/'resultados/s2b_ejecucion.json').read_text(encoding='utf-8')) if (scratch/'resultados/s2b_ejecucion.json').exists() else {}
    report=dict(exit_code=int(bool(issues)),issues=issues,checked_measure_names=names,
                unique_states=len(rows),first100ns_max_step=max(float(r['max_step_first100ns']) for r in rows if r['test']=='E7'),
                campaign_manifest_sha256=hashlib.sha256((ROOT/'resultados/s2b_ejecucion.json').read_bytes()).hexdigest(),
                relocated_path=str(scratch),models_env=env['S3G4_MODELS'],replay_exit_code=replay.returncode,
                replay_simulations=replayrun.get('simulations'),replay_elapsed_seconds=replayrun.get('elapsed_seconds'),
                csv_comparison=comparison,elapsed_seconds=time.perf_counter()-started)
    (ROOT/'S2b/verificacion_entrega.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k not in ('csv_comparison','models_env','relocated_path')},ensure_ascii=False))
    print(f'CSV identical: {sum(x["identical"] for x in comparison)}/{len(comparison)}')
    return report['exit_code']


if __name__=='__main__':raise SystemExit(main())
