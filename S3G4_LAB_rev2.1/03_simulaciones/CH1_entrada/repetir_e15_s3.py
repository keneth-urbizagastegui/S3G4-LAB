"""Rerun only E15 after correcting its source offset; reuse unchanged measured cases.

The independent complete replay must subsequently match every output CSV.
"""
import sys
sys.dont_write_bytecode=True
import csv
import argparse
import hashlib
import json
import re
import time
from pathlib import Path
import ejecutar_s3 as s3


def typed(value, key):
    if key in ('order','codes_observed'):return value
    if value in ('True','False'):return value=='True'
    if re.fullmatch(r'[-+]?\d+',value):return int(value)
    try:return float(value)
    except ValueError:return value


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--repair-columns-only',action='store_true',help='Restore missing-field header position without changing measured values')
    args=parser.parse_args()
    if args.repair_columns_only:
        evidence=[]
        for name in ['s3_e11.csv','s3_resultados.csv']:
            p=s3.ROOT/'resultados'/name;before=hashlib.sha256(p.read_bytes()).hexdigest()
            with p.open(encoding='utf-8',newline='') as f:
                reader=csv.DictReader(f);fields=list(reader.fieldnames);rows=list(reader)
            # frequency_metrics always inserts minus3_Hz after peak_Hz,
            # even when the cutoff is None (the AC-coupled first case).
            fields.remove('bnc_minus3_Hz');fields.insert(fields.index('bnc_peak_Hz')+1,'bnc_minus3_Hz')
            with p.open('w',encoding='utf-8',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows)
            with p.open(encoding='utf-8',newline='') as f:assert list(csv.DictReader(f))==rows
            evidence.append(dict(file=name,before_sha256=before,after_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),rows=len(rows),measured_fields_unchanged=True))
        s3.write(s3.ROOT/'resultados/s3_serializacion.json',json.dumps(evidence,indent=2))
        print('Two CSV column orders restored; every measured field unchanged.')
        return 0
    start=time.perf_counter();protected=s3.protected_hashes()
    out=s3.ROOT/'resultados'
    run=json.loads((out/'s3_ejecucion.json').read_text(encoding='utf-8'))
    rows=[]
    for test in ['isoamp','isolad','isosw','isoctrl','e11','e12','e14','e13','e11b']:
        with (out/f's3_{test}.csv').open(encoding='utf-8',newline='') as f:
            rows += [{k:typed(v,k) if v!='' else None for k,v in r.items()} for r in csv.DictReader(f)]
    records=[r for r in run['records'] if not r['id'].startswith('e15_')]
    s3.E15_PROXY_CORNERS.update(r['corner'] for r in rows if r['test']=='ISOCTRL' and not r['native_converged'])
    batch=[c for c in s3.jobs(False) if c['test']=='E15']
    s3.set_e15_amplitudes(batch,rows)
    print(f'E15 offset revision: {len(batch)} cases, ten workers',flush=True)
    rr,ss=s3.execute(batch,s3.ROOT/'S3/generados');rows+=rr;records+=ss
    rows.sort(key=lambda r:r['id']);records.sort(key=lambda r:r['id'])
    s3.clean_superseded(s3.ROOT/'S3/generados',records)
    changed=[p for p,h in protected.items() if not Path(p).exists() or hashlib.sha256(Path(p).read_bytes()).hexdigest()!=h]
    errors=sum(bool(r['errors'] or r['returncode']) for r in records)
    warnings=sum(bool(r['warnings']) for r in records)
    revised=time.perf_counter()-start
    run.update(exit_code=int(bool(errors or changed)),errors=errors,warnings=warnings,
               elapsed_seconds=run['elapsed_seconds']+revised,records=records,
               protected_files=len(protected),protected_changed=changed,
               e15_revision_seconds=revised,e15_revised_simulations=len(batch),
               total_simulation_attempts=run['simulations']+len(batch))
    criteria=s3.report(rows,records,run,'s3',out)
    s3.write(out/'s3_ejecucion.json',json.dumps(run,indent=2,ensure_ascii=False))
    print(s3.table(criteria,['criterion','value','status']),flush=True)
    print(f'FINAL exit={run["exit_code"]} unique={len(records)} revised={len(batch)} seconds={revised:.3f}',flush=True)
    return run['exit_code']


if __name__=='__main__':raise SystemExit(main())
