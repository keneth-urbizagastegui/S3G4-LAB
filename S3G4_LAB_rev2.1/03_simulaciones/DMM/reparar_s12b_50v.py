"""Repeat the two50V current tests after fixing their explicit .save list."""
import concurrent.futures as cf
import json,time
import ejecutar_s12b as s
def main():
    cs=[c for c in s.cases() if c['kind']=='stress50'];start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(lambda c:s.run(c,True),cs))
    s.writecsv(s.RESULTS/'s12b_repeticion50V.csv',rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),reused=sum(r.get('reused',False) for r in rows),elapsed_s=time.perf_counter()-start,workers=10,timeout_s=900)
    (s.RESULTS/'s12b_repeticion50V.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
    return int(summary['ok']!=summary['total'])
if __name__=='__main__':raise SystemExit(main())
