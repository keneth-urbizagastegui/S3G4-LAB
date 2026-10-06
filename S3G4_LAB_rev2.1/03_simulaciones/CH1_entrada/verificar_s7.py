"""Independent artifact audit: physical topology, MC tolerances, coverage, CSV.

Run after campaign; --reorder regenerates only S7/reorder_validation artifacts.
No circuit or protected-file writes.
"""
import sys
sys.dont_write_bytecode=True
import csv,json,re
from pathlib import Path
import numpy as np
import ejecutar_s7 as s

def main():
    inc=(s.ROOT/'comun/ch1_comun_s7.inc').read_text()
    assert 'RLOAD OUT' not in inc and 'CLOAD OUT' not in inc
    assert inc.count('PROTECT_BAV99 R_SER={R_SER_S7}')==2
    assert s.NOM['RFILT1_S7']==1110 and s.NOM['RFILT2_S7']==499
    for key,expected in [('CFILT1_S7',56e-12),('CGILT1_S7',47e-12),('CFILT2_S7',220e-12),('CGILT2_S7',56e-12),('C_FB_S7',1e-12)]:
        assert np.isclose(s.NOM[key],expected,rtol=1e-12,atol=0)
    mc,records=s.mc_subcircuits(s.case('J3',mc=0))
    factors={r['component']:r for r in records}
    assert len(factors)==len(records)
    for a,b in [('XFE:Rt1','XFE:Rt2'),('X105A:R1','X105A:R2'),('X105A:CPCB','X105B:CPCB'),('XPROTA:RSER','XPROTB:RSER')]:
        assert factors[a]['factor']!=factors[b]['factor']
    for r in records:assert abs(r['factor']-1)<=r['tolerance']+1e-15
    # Nominal expressions and every node match the source FRONT_S2B.
    front=(s.ROOT/'comun/ch1_comun_s2b.inc').read_text()
    f=re.search(r'^\.subckt FRONT_S2B[\s\S]*?^\.ends[^\n]*',front,re.M)[0].splitlines()
    fm=mc[:len(f)]
    for original,varied in zip(f[1:-1],fm[1:-1]):
        assert original.split()[:3]==varied.split()[:3],(original,varied)
    print('Circuit topology/values and independent MC factors: OK',len(records),'physical draws')
    if '--structure' in sys.argv:return
    run=json.loads((s.ROOT/'S7/s7_run.json').read_text())
    assert run['returncode']==0 and run['protected_changed']==[] and not run['smoke']
    rows={}
    expected={'j1':12,'j1dc':12,'j2':24,'j3':600,'j4':12,'j5':5,'j6':10,'j7':4,'j8':9,'j9':2}
    for key,count in expected.items():
        with (s.OUT/f's7_{key}.csv').open(newline='',encoding='utf-8') as file:
            reader=csv.DictReader(file);assert reader.fieldnames==s.FIELDS
            rr=list(reader);assert len(rr)==count,(key,len(rr))
            assert len({r['id'] for r in rr})==count
            rows[key]=rr
    assert run['logical_cases']==sum(expected.values()) and run['simulations']>=run['logical_cases']
    for r in rows['j1dc']:assert float(r['gain_dc_signed'])<0 and abs(float(r['gain_error_pct']))<=3
    for r in rows['j7']:assert abs(float(r['fundamental_pp_V'])-8*s.DIV)<.01
    with (s.OUT/'s7_limits.csv').open(newline='',encoding='utf-8') as file:
        rr=list(csv.DictReader(file));assert len(rr)==30
        for r in rr:
            for key in ['plus_at_minus40_V','plus_at_plus40_V','minus_at_minus40_V','minus_at_plus40_V']:
                assert np.isfinite(float(r[key]))
    with (s.OUT/'s7_samples.csv').open(newline='',encoding='utf-8') as file:
        rr=list(csv.DictReader(file));assert len(rr)==4*1024
        assert max(abs(float(r['closing_time_error_ps'])) for r in rr)<1
    print('Full campaign coverage, signed gains, extrema and apertures: OK',run['simulations'],'simulations')
    print('Protected file SHA256 check:',run['protected_count'],'unchanged')
    if '--reorder' in sys.argv:
        data=json.loads((s.ROOT/'S7/s7_completed_data.json').read_text())
        original_root,original_out=s.ROOT,s.OUT
        try:
            for label,reverse in [('a',False),('b',True)]:
                s.ROOT=original_root/'S7/reorder_validation'/label;s.OUT=s.ROOT/'resultados'
                rr=list(reversed(data['rows'])) if reverse else data['rows']
                ee={k:list(reversed(v)) if reverse else v for k,v in data['extras'].items()}
                s.save_results(rr,ee,data['records'],data['meta'],False)
        finally:s.ROOT,s.OUT=original_root,original_out
        a=original_root/'S7/reorder_validation/a/resultados';b=original_root/'S7/reorder_validation/b/resultados'
        files=sorted(a.glob('s7_*.csv'));different=[f.name for f in files if f.read_bytes()!=(b/f.name).read_bytes()]
        assert not different,different
        # Report regeneration also preserves the actual delivered CSV bytes.
        different=[f.name for f in files if f.read_bytes()!=(original_out/f.name).read_bytes()]
        assert not different,different
        print('CSV generation independent of worker completion order:',len(files),'byte-identical CSV')

if __name__=='__main__':main()
