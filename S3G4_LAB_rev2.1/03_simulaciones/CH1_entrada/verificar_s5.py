"""Independent artifact audit and short-path replay CSV comparison for S5."""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--replay',required=True,type=Path);args=ap.parse_args()
    out=ROOT/'resultados';replay=args.replay.resolve();run=json.loads((out/'s5_ejecucion.json').read_text())
    rerun=json.loads((replay/'resultados/s5_ejecucion.json').read_text())
    errors=[];comparisons=[];states=[]
    for p in sorted(out.glob('s5_*.csv')):
        if p.name.startswith(('s5_controls_','s5_smoke_')):continue
        other=replay/'resultados'/p.name
        equal=other.exists() and p.read_bytes()==other.read_bytes()
        entry=dict(file=p.name,identical_bytes=equal,sha256=sha(p),replay_sha256=sha(other) if other.exists() else None)
        with p.open(encoding='utf-8',newline='') as f:
            reader=csv.DictReader(f);schema=reader.fieldnames;rows=list(reader)
        entry.update(columns=schema,rows=len(rows))
        if not equal:
            errors.append('CSV differs: '+p.name)
            if other.exists():
                with other.open(encoding='utf-8',newline='') as f:
                    rr=csv.DictReader(f);other_schema=rr.fieldnames;other_rows=list(rr)
                entry['same_schema']=schema==other_schema
                entry['same_row_count']=len(rows)==len(other_rows)
                max_rel=0.;nonnumeric=[]
                if schema==other_schema and len(rows)==len(other_rows):
                    for j,(a,b) in enumerate(zip(rows,other_rows)):
                        for k in schema:
                            if a[k]==b[k]:continue
                            try:
                                x,y=float(a[k]),float(b[k]);max_rel=max(max_rel,abs(x-y)/max(abs(x),abs(y),1e-30))
                            except ValueError:nonnumeric.append([j,k,a[k],b[k]])
                entry.update(max_relative_numeric_difference=max_rel,nonnumeric_differences=nonnumeric)
        comparisons.append(entry)
    rows=list(csv.DictReader((out/'s5_resultados.csv').open(encoding='utf-8',newline='')))
    byid={r['id']:r for r in rows}
    if len(rows)!=len(byid):errors.append('Duplicate result IDs')
    decks=list((ROOT/'S5/generados').glob('*.cir'))
    if {p.stem for p in decks}!=set(byid):errors.append('Deck/result ID mismatch')
    for path in decks:
        s=path.read_text(encoding='utf-8');r=byid[path.stem]
        measures=re.findall(r'^\.meas\s+\w+\s+(\S+)',s,re.M|re.I)
        if not measures or any(not x.startswith(path.stem+'_') for x in measures):errors.append('Invalid measure state '+path.stem)
        if r['test']!='G0':
            pos=re.search(r'^XFE .* POS=(\d+) CPL=(\d+)',s,re.M)
            tap=sum(int(re.search(rf'^VA{b} A{b} 0 (\d+)',s,re.M)[1])//5*2**b for b in range(3))
            if not pos or int(pos[1])!=int(r['POS']) or pos[2]!='0' or tap!=int(r['tap']):errors.append('Circuit scale state mismatch '+path.stem)
        if r['test']=='G3':
            actual=dict(re.findall(r'^\.param (R[12][AB]|C[12][AB])=(\S+)',s,re.M))
            if set(actual)!=set(['R1A','R1B','C1A','C1B','R2A','R2B','C2A','C2B']):errors.append('Missing MC parameters '+path.stem)
            if any(float(v)!=float(r[k]) for k,v in actual.items()):errors.append('MC values differ from simulated deck '+path.stem)
        if r['test']=='G5':
            if 'AD8038_ltspice_ruido_hoja.sub' not in s or 'AD8038_ltspice.sub"' in s:errors.append('Noise model mismatch '+path.stem)
        elif 'AD8038_ltspice_ruido_hoja.sub' in s:errors.append('Noise model in non-noise case '+path.stem)
        states.append(dict(id=path.stem,measures=len(measures),deck_sha256=sha(path)))
    candidates={r['candidate'] for r in rows}
    expected=len(candidates)*(2+12+2*2+200+12+2*2+2)
    for q,label in [(run,'original'),(rerun,'replay')]:
        if q['exit_code'] or q['simulations']!=expected or q['errors'] or q['protected_changed']:errors.append('Incomplete or changed '+label)
    result=dict(exit_code=int(bool(errors)),original=dict(exit_code=run['exit_code'],simulations=run['simulations'],elapsed_seconds=run['elapsed_seconds']),
                replay=dict(path=str(replay),exit_code=rerun['exit_code'],simulations=rerun['simulations'],elapsed_seconds=rerun['elapsed_seconds']),
                identical_csvs=sum(c['identical_bytes'] for c in comparisons),total_csvs=len(comparisons),
                audited_decks=len(decks),errors=errors,csvs=comparisons,states=sorted(states,key=lambda x:x['id']))
    (out/'s5_reproducibilidad.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['csvs','states']},indent=2))
    return result['exit_code']

if __name__=='__main__':raise SystemExit(main())
