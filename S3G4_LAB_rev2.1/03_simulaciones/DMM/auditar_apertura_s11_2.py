"""Replays missing opening timestamps with identical decks, no solver changes.
Floating-point equality at q=6.7*k is not a switch state; infer actual open
from off-state conductance/current once accumulated I2t is at the threshold.
Preserves campaign measurements, outputs a separate audit CSV.
"""
import concurrent.futures as cf, csv, gc, json, shutil, subprocess, time
import numpy as np
import ejecutar_s11_2 as s

AUD=s.JOBS/'apertura_audit'

def one(r):
    ident=r['id'];p=AUD/(ident+'.cir');shutil.copy2(s.JOBS/(ident+'.cir'),p)
    start=time.perf_counter()
    try:
        proc=subprocess.run([str(s.LT),'-b',str(p)],timeout=300,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        d=s.raw(p.with_suffix('.raw'));t=np.abs(d['time']);q=d['v(qfus)'];i=d['i(vfs)']
        idx=np.flatnonzero((q>.99*float(r['arc'])*6.7)&(np.abs(i)<1e-6))
        oi=int(idx[0]) if len(idx) else None
        result=dict(id=ident,q='Q5',grid=float(r['grid']),arc=int(r['arc']),phase=float(r['phase']),rail=float(r['rail']),status='ok' if proc.returncode==0 and oi is not None else 'error',elapsed_s=time.perf_counter()-start)
        if oi is not None:
            result.update(fuse_open_audited_s=float(t[oi]),postopen_peak_audited_A=float(np.max(np.abs(i[t>t[oi]+1e-6]))),q_at_open_A2s=float(q[oi]),q_final_A2s=float(q[-1]),q_threshold_relative_error=abs(float(q[-1])/(float(r['arc'])*6.7)-1))
        peak=float(np.max(np.abs(d['i(dbr1)'])));i2t=float(np.trapezoid(d['i(dbr1)']**2,t))
        result.update(bridge_peak_replay_A=peak,bridge_i2t_replay_A2s=i2t,bridge_peak_delta_A=peak-float(r['dbr1_peak_A']),bridge_i2t_delta_A2s=i2t-float(r['dbr1_i2t_A2s']))
        del d,t,q,i;gc.collect()
    except subprocess.TimeoutExpired:result=dict(id=ident,status='timeout',elapsed_s=time.perf_counter()-start)
    except Exception as ex:result=dict(id=ident,status='error',error=str(ex),elapsed_s=time.perf_counter()-start)
    for suffix in ('.raw','.op.raw'):
        p.with_suffix(suffix).unlink(missing_ok=True)
    p.with_suffix('.json').write_text(json.dumps(result,indent=2),encoding='utf8')
    return result

def main():
    AUD.mkdir(exist_ok=True)
    rows=list(csv.DictReader((s.RESULTS/'s11_2_campaign.csv').open(encoding='utf-8-sig')))
    cases=[r for r in rows if r['q']=='Q5' and r['status']=='ok' and not r.get('fuse_open_s')]
    start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool:
        results=[]
        for r in pool.map(one,cases):
            results.append(r)
            if len(results)%10==0:print('opening audit',len(results),'/',len(cases),flush=True)
    s.writecsv(s.RESULTS/'s11_2_fuse_open_audit.csv',results)
    summary=dict(total=len(results),ok=sum(r['status']=='ok' for r in results),elapsed_s=time.perf_counter()-start)
    (s.RESULTS/'s11_2_fuse_open_audit.json').write_text(json.dumps(summary,indent=2));print(summary,flush=True)

if __name__=='__main__':main()
