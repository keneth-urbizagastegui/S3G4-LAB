"""S12c: remaining apparent E3 one-count failures at 100 ns."""
import concurrent.futures as cf, hashlib, json, time
from pathlib import Path
import ejecutar_s12c as s

def main():
    cases=[]
    for amp,charge in ((-20,0),(0,0),(20,5e-12)):
        c=next(c for c in s.cases() if c['q']=='E3' and c['kind']=='zero' and c['sel']==2 and c['gain']==10.1 and c['amp']==amp and c['charge']==charge)
        cases.append(dict(c,verification='maxstep100ns'))
    original=s.deck; signature=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def deck(c):
        text=original(c).replace(f'.tran 0 {c["stop"]} 0 1u',f'.tran 0 {c["stop"]} 0 100n')
        return text.replace('.end',f'* verification_source_sha256 {signature}\n.end')
    s.deck=deck; start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool: rows=list(pool.map(lambda c:s.run(c,True),cases))
    s.writecsv(s.RESULTS/'s12c_verificacion_extra.csv',rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),elapsed_s=time.perf_counter()-start,reused=sum(r.get('reused',False) for r in rows))
    (s.RESULTS/'s12c_verificacion_extra.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))
    for r in rows: print({k:r.get(k) for k in ('amp','charge','status','error_at_wait_counts','bx0_peak_V','all_channels_rail_pass')})
    return int(summary['ok']!=summary['total'])

if __name__=='__main__': raise SystemExit(main())
