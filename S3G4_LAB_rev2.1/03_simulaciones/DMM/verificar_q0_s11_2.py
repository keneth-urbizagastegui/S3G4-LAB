"""LTspice checks of BSS126 IDSS, threshold-at8uA and Ron-at3mA.
Computed separately from campaign; 12 decks, no changes to vendor models.
"""
import concurrent.futures as cf, json, subprocess, time
from pathlib import Path
import numpy as np
import ejecutar_s11_2 as s

def one(c):
    ident=f'Q0_ids{c["idss_25_A"]}_vp{-c["threshold25_V"]}_t{c["temp_C"]}'.replace('.','d')
    p=s.JOBS/(ident+'.cir');ids=c['idss_25_A'];vp=-c['threshold25_V'];temp=c['temp_C']
    threshold=c['vto_model_V']+np.sqrt(16e-6/c['kp_A_V2'])
    txt=f'''* {ident} model verification; idss21mA is sensitivity, NOT max
.include "{s.HERE/'comun/bss126_s11_2.inc'}"
Vds d 0 25
Vg g 0 0
Xid d g 0 BSS126_EST IDS={ids} VP={vp} RON=700 TC={temp}
Vdt dt 0 3
Vgt gt 0 {threshold}
Xth dt gt 0 BSS126_EST IDS={ids} VP={vp} RON=700 TC={temp}
Itest 0 dr 3m
Xron dr 0 0 BSS126_EST IDS={ids} VP={vp} RON=700 TC={temp}
.temp {temp}
.options numdgt=15 plotwinsize=0 threads=1
.save V(*) I(*)
.tran 0 1u 0 100n
.meas tran {ident}__idss FIND -I(Vds) AT 1u
.meas tran {ident}__threshold_id FIND -I(Vdt) AT 1u
.meas tran {ident}__ron FIND V(dr)/.003 AT 1u
.end
'''
    p.write_text(txt,encoding='utf8');start=time.perf_counter()
    try:
        proc=subprocess.run([str(s.LT),'-b',str(p)],timeout=300,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        vals,log=s.old.parse_log(p.with_suffix('.log'))
        r=dict(c,deck=ident,elapsed_s=time.perf_counter()-start,status='ok' if proc.returncode==0 and len(vals)==3 else 'error',threshold_test_V=float(threshold),**vals)
    except subprocess.TimeoutExpired:r=dict(c,status='timeout',elapsed_s=time.perf_counter()-start)
    return r

def main():
    s.JOBS.mkdir(exist_ok=True);s.RESULTS.mkdir(exist_ok=True);s.build()
    import csv
    rows=list(csv.DictReader((s.RESULTS/'s11_2_q0_model.csv').open(encoding='utf-8-sig')))
    cases=[{k:float(v) if k not in ('idss_kind','source') else v for k,v in r.items()} for r in rows]
    start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool:results=list(pool.map(one,cases))
    s.writecsv(s.RESULTS/'s11_2_q0_ltspice.csv',results)
    summary=dict(total=len(results),ok=sum(r['status']=='ok' for r in results),elapsed_s=time.perf_counter()-start)
    (s.RESULTS/'s11_2_q0_ltspice.json').write_text(json.dumps(summary,indent=2));print(summary)

if __name__=='__main__':main()
