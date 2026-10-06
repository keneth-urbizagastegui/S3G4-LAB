"""Independent delivery checks; no import of the simulation runner."""
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
RESULT=ROOT/'resultados'
run=json.loads((RESULT/'s2_ejecucion.json').read_text(encoding='utf-8'))
first=json.loads((ROOT/'S2/reproducibilidad_primera.json').read_text(encoding='utf-8'))
with (RESULT/'s2_resultados.csv').open(encoding='utf-8',newline='') as f:
    rows=list(csv.DictReader(f))
assert run['exit_code']==0 and run['errors']==0 and run['warnings']==0
assert not run['protected_changed']
assert len(rows)==run['simulations']==119
ids=[r['id'] for r in rows]
assert ids==sorted(ids) and len(set(ids))==len(ids)
coverage=Counter((r['test'],r['buffer'],r['variant']) for r in rows)
assert coverage=={
    ('E0','OPA810','real'):4, ('E0','AD8065','real'):4,
    ('E5','OPA810','real'):20, ('E5','AD8065','real'):8,
    ('E6','OPA810','real'):12, ('E6','OPA810','off_load_only'):12,
    ('E7','OPA810','real'):13, ('E7','OPA810','off_load_only'):3,
    ('E7','AD8065','real'):6,
    ('E8','OPA810','real'):2, ('E8','AD8065','real'):2,
    ('E9','OPA810','real'):16, ('E9','AD8065','real'):16,
    ('E10','OPA810','real'):1,
}
records={r['id']:r for r in run['records']}
assert len(records)==len(rows)
total_measures=0
fine_steps=[]
for row in rows:
    rec=records[row['id']]
    path=ROOT/rec['file']
    net=path.read_text(encoding='utf-8')
    b=path.with_suffix('.log').read_bytes()
    log=b.decode('utf-16' if b.startswith(b'\xff\xfe') else 'utf-8',errors='replace')
    assert 'Maximum thread count: 1' in log
    pos=int(re.search(r'XFE .* FRONT_S2 POS=(\d+)',net)[1])
    cpl=int(re.search(r'XFE .* FRONT_S2 .* CPL=(\d+)',net)[1])
    power=int(re.search(r'XR .* RAILS_S2 POWER=(\d+)',net)[1])
    bleed=int(re.search(r'XR .* RAILS_S2 .* BLEED=(\d+)',net)[1])
    assert pos==int(row['POS']) and cpl=={'DC':0,'AC':1}[row['CPL']]
    assert power==int(row['power']) and bleed==int(row['bleed'])
    assert power or pos==100
    measurements=re.findall(r'^\.meas \w+ (\w+)',net,re.M)
    assert len(measurements)==rec['measures']
    assert all(m.startswith(row['id']+'_') for m in measurements)
    assert len(set(measurements))==len(measurements)
    total_measures+=len(measurements)
    if row['variant']=='real':
        assert f'XBUF BI OUT VP VN OUT BUFFER_{row["buffer"]}' in net
    else:
        assert 'XBUF ' not in net and power==0
    if row['test']=='E7':
        maxstep=float(net.split('.tran 0 ')[1].splitlines()[0].split()[-1])
        assert maxstep<=.1e-9
        assert rec['max_step_first200ns']<=maxstep*1.0001
        expected=int(row['stimulus'].replace('kv',''))*1000
        assert abs(float(row['gun_initial_v'])-expected)<abs(expected)*1e-6
        assert 'Cgun GUN 0 150p' in net and 'Resd GUN DISCH 330' in net
        fine_steps.append(rec['max_step_first200ns'])
    if row['test']=='E10':
        assert '.four 1k 7 V(OUT)' in net
        assert 'Rprobe TIP BNC 9Meg' in net and 'Ccable BNC 0 80p' in net
        assert 'SINE(0 400 1k)' in net

common=(ROOT/'comun/ch1_comun_s2.inc').read_text(encoding='utf-8')
assert 'XAMP IP IM OUT VP VN OPA810' in common
assert 'XAMP IP IM VP VN OUT AD8065' in common
original=(ROOT.parents[2]/'Simulation_LTSpice/models/BAV199.txt').read_text()
def model_parameters(s):
    part=re.search(r'\.MODEL BAV199 D\s*\n((?:\+[^\n]*\n)+)',s,re.I)[1]
    return {k.upper():float(v) for k,v in re.findall(r'(\w+)\s*=\s*([-+\d.Ee]+)',part)}
assert model_parameters(common)==model_parameters(original)
reproduced={fn:hashlib.sha256((RESULT/fn).read_bytes()).hexdigest()==sha for fn,sha in first['csv_sha256'].items()}
assert all(reproduced.values()),[k for k,v in reproduced.items() if not v]
with (RESULT/'s2_convergencia_esd.csv').open(encoding='utf-8',newline='') as f:
    convergence=list(csv.DictReader(f))
report=dict(status='PASS',simulations=len(rows),unique_states=len(ids),
            measures_checked=total_measures,coverage={':'.join(k):v for k,v in sorted(coverage.items())},
            csv_byte_identical=reproduced,first_seconds=first['elapsed_seconds'],
            rerun_seconds=run['elapsed_seconds'],
            esd_max_step_ns=max(fine_steps)*1e9,
            esd_max_convergence_relative=max(float(x['relative_change']) for x in convergence),
            protected_files_unchanged=run['protected_files'],
            manifest_sha256=hashlib.sha256((RESULT/'s2_ejecucion.json').read_bytes()).hexdigest(),
            runner_sha256=hashlib.sha256((ROOT/'ejecutar_s2.py').read_bytes()).hexdigest(),
            common_sha256=hashlib.sha256((ROOT/'comun/ch1_comun_s2.inc').read_bytes()).hexdigest())
(ROOT/'S2/verificacion_entrega.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k not in ('coverage','csv_byte_identical')},indent=2))
