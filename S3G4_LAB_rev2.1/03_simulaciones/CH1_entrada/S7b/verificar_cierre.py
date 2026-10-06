"""Audit complete S7b artifacts against native evidence and original baseline."""
import sys
sys.dont_write_bytecode = True
import collections, csv, json, math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import ejecutar_s7b as s

work = ROOT / 'S7b' / 'campaign'
d = json.loads((work / 's7b_checkpoint.json').read_text(encoding='utf-8'))
rows, meta = d['rows'], d['meta']
assert meta['returncode'] == 0 and meta['successful'] == meta['logical_cases'] == 4416
assert len(rows) == len({r['id'] for r in rows}) == 4416
expected = {('K1','J1'):12, ('K1','J1DC'):12, ('K1','J2'):24,
            ('K1','J4'):12, ('K1','J8'):108, ('K1','J9'):2,
            ('K3','J5'):20, ('K3E5','J5'):16, ('K2','J3'):2000,
            ('K2NOISE','J4'):200, ('K2DC','J1DC'):2000, ('K4','J6'):10}
assert dict(collections.Counter((r['phase'],r['test']) for r in rows)) == expected
for phase in ['K2','K2DC']:
    for ix in [0,3,6,9]:
        assert {r['mc'] for r in rows if r['phase']==phase and r['ix']==ix} == set(range(500))
for ix in [0,6]:
    assert {r['mc'] for r in rows if r['phase']=='K2NOISE' and r['ix']==ix} == set(range(100))
limits = collections.Counter(r['id'] for r in d['extras']['limits'])
assert len(limits)==36 and set(limits.values())=={6}
for r in rows:
    for value in r.values():
        if isinstance(value,float): assert math.isfinite(value), r['id']
latest = {r['id']:r for r in d['records']}
assert not any(r['returncode'] or r['errors'] for r in latest.values())
assert meta['simulations']==sum(r.get('simulations',1) for r in d['records'])
j8=[]
for r in rows:
    if r['test']=='J8' and r.get('dc_retry'):
        child=r['id']+'_retry_dacfrom1p25_maxstep5m'
        values,errors,_,_=s.old.s4.s3.prior.old.read_log(work/(child+'.log'))
        assert not errors
        native=values[child.lower()+'_center_v']
        assert r['center_V']==r['adc_min_V']==r['adc_max_V']==native
        j8.append(dict(scale=r['scale_V_div'],dac=r['vdac_V'],center=native))
assert len(j8)==3
for ix in range(12):
    rr=sorted((r for r in rows if r['test']=='J8' and r['ix']==ix),key=lambda r:r['vdac_V'])
    assert len(rr)==9 and all(a['center_V']>b['center_V'] for a,b in zip(rr,rr[1:]))
original=json.loads((ROOT/'S7b'/'campaign_before_warm_restart'/'s7b_protected_before.json').read_text(encoding='utf-8'))
after=s.protected()
changed=[k for k,v in original.items() if after.get(k)!=v]
assert not changed and not meta['protected_changed']
files=list((ROOT/'resultados').glob('s7b_*.csv'))
for path in files:
    with path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        assert len(reader.fieldnames)==len(set(reader.fieldnames)), path.name
        for row in reader:
            assert None not in row and None not in row.values(), path.name
            assert not any(v.lower() in ['nan','inf','-inf'] for v in row.values()), path.name
with (ROOT/'resultados'/'s7b_tabla_calibracion.csv').open(encoding='utf-8-sig',newline='') as f:
    assert len(list(csv.DictReader(f)))==12
audit=dict(status='PASS',meta=meta,logical_counts={f'{p}/{t}':n for (p,t),n in expected.items()},
           unique_boards=500,noise_boards_per_scale=100,protection_rows=216,
           repaired_j8_native_endpoints=j8,original_protected_count=len(original),
           original_protected_changed=changed,csv_count=len(files),
           latest_record_warnings=sum(len(r.get('warnings',[])) for r in latest.values()))
(work/'s7b_auditoria_cierre.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(audit,ensure_ascii=False))
