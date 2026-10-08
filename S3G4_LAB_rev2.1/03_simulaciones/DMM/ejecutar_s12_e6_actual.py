"""S12 supplement: approved GDT + MOV versus contractual S11.4 bare GDT.
Read-only reuse of the local GDT study; all outputs remain in S12/resultados.
No new parts or manufacturer model edits. Tau 1/100ns are model assumptions.
"""
import argparse, concurrent.futures as cf, importlib.util, json, re, time
from pathlib import Path
import numpy as np
import ejecutar_s12 as s

spec=importlib.util.spec_from_file_location('gdt_study',s.HERE/'gdt_seguimiento/gdt_seguimiento.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
original=s.deck

def deck(c):
    text=original(c)
    text=re.sub(r'^(?:Cgdt|Cgstate|Rgstate|Bgthreshold|Bgstate|Bgdt|\.param GDC)[^\n]*\n','',text,flags=re.M)
    block='\n'.join(study.gdt_block('mov',c['base']['gdc'],c['tau']))+'\n'
    return text.replace('.temp 25',block+'.temp 25')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--smoke',action='store_true');ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    cs=[dict(c,chain='gdtmov',tau=tau) for c in s.cases() if c['q']=='E6' for tau in (1e-9,1e-7)]
    if a.smoke:cs=cs[:1]
    s.deck=deck;s.JOBS=s.HERE/'S12/e6_actual';s.JOBS.mkdir(exist_ok=True)
    start=time.perf_counter();rows=[]
    with cf.ThreadPoolExecutor(max_workers=10) as pool:
        for fut in cf.as_completed([pool.submit(s.run,c,a.resume) for c in cs]):rows.append(fut.result())
    label='smoke' if a.smoke else 'campaign';dest=s.RESULTS/f's12_e6_actual_{label}.csv';s.writecsv(dest,rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),elapsed_s=time.perf_counter()-start,reused=sum(r.get('reused',False) for r in rows),workers=10,timeout_s=900)
    dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
    return int(summary['total']!=summary['ok'])

if __name__=='__main__':raise SystemExit(main())
