"""Checks the changed matrix and exact integration/extrapolation with synthetic raw."""
import tempfile
from pathlib import Path
import numpy as np
import ejecutar_s11_1 as s
from leer_raw_s11_1 import audit_raw

cases=s.cases()
assert all(c['frequency']==60 for c in cases if c['stimulus']=='mains')
assert {c['rcold'] for c in cases if c['relay']}=={40,60}
assert all(c['stop']<=1 and c['step']<=50e-6 for c in cases if c['p'] in ('P2','P3','P4'))
assert all(c['stop']==10e-6 and c['step']<=1e-9 for c in cases if c['p']=='P6')
assert {c['grid'] for c in cases if c['p']=='P5' and c['fuse']}=={.5,1,2}
assert len({s.name(c) for c in cases})==len(cases)
assert all(c['opening']>=100 for c in cases if c['p']=='P1' and c['relay'])
assert all('RCOLD='+str(c['rcold']) in s.deck(c) for c in cases)
names=['time']+['v('+n+')' for n in ('vin','ain','x0','x1','x2','x5','n1','n2','rp','rn','shunt','theta','p1','p2','d1','d2','c1','c2','c3','pt','ms')]+['i(btvs)']+['i(d'+n+q+')' for n in ('0','1','2','5') for q in ('p','n')]
t=np.linspace(0,1,20001)
data=np.zeros((len(t),len(names)))
data[:,0]=t
data[:,names.index('v(n1)')]=2
data[:,names.index('i(btvs)')]=3
data[:,names.index('v(rp)')]=4.9
data[:,names.index('v(rn)')]=-4.9
header='Title: validation\nPlotname: Transient Analysis\nFlags: real double\nNo. Variables: '+str(len(names))+'\nNo. Points: '+str(len(t))+'\nVariables:\n'+''.join(f'\t{i}\t{n}\tvoltage\n' for i,n in enumerate(names))+'Binary:\n'
with tempfile.TemporaryDirectory() as d:
    p=Path(d)/'fixture.raw'
    p.write_bytes(header.encode()+data.astype('<f8').tobytes())
    c=next(c for c in cases if c['p']=='P2')
    r=audit_raw(p,1,60,c)
    assert abs(r['tvs_energy_simulated_J']-6)<1e-9
    assert abs(r['tvs_energy_extrapolated_J']-54)<1e-8
    assert abs(r['tvs_energy_total_estimate_J']-60)<1e-8
    assert r['extrapolation_valid']
    r=audit_raw(p,.99998,60,dict(c,stop=.99998))
    assert r['raw_complete'] and not r['raw_endpoint_exact']
    assert abs(r['raw_overrun_s']-20e-6)<1e-12
    r=audit_raw(p,2,60,dict(c,stop=2))
    assert not r['extrapolation_valid'] and 'tvs_energy_extrapolated_J' not in r
print(f'OK: {len(cases)} unique cases; 60 Hz, PTC endpoints, three P5 impedances, ESD steps; 6 J simulated + 54 J extrapolated; aborted raw cannot extrapolate; covered raw overshoot is complete.')
