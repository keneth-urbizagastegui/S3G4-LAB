"""Isolated S9-B campaign with sheet-adjusted local LM6172. A is read-only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,json,time,hashlib,csv
import ejecutar_s9 as s
ROOT=Path(__file__).resolve().parent
MODEL=ROOT/'comun/lm6172_hoja.lib'
original_net=s.net
original_analyze=s.analyze
original_native=s.native

def net(c):
    assert c['variant']=='B'
    d=original_net(c)
    for path in [s.MODELS/'LM6172/lm6172.lib',ROOT/'comun/lm6172_s9_ruido_hoja.lib']:
        d=d.replace(str(path),str(MODEL))
    for el in ['RINA','RINB']:
        d=d.replace(':XCORE:'+el,':XCORE:XCORE:'+el)
    return d

def analyze(c,raw,row):
    if c['s9_test']=='K6':
        # Local noise wrapper adds one level; retain tested analysis schema.
        for key in list(raw):
            if ':xcore:xcore:rin' in key:
                raw[key.replace(':xcore:xcore:rin',':xcore:rin')]=raw[key]
    return original_analyze(c,raw,row)
s.net=net
s.analyze=analyze

def native(c,work,deck=None,timeout=120,bias=None):
    # Prefer this adjusted B's solved nominal recommendation for transient start.
    # .loadbias remains a Newton initial guess, never a fixed node or component.
    if (bias is None or not bias.exists()) and deck is None and c['s9_test']!='K1':
        own=work/(s.case('K1','B',c['ix'])['id']+'.bias')
        if own.exists():bias=own
    return original_native(c,work,deck,timeout,bias)
s.native=native

def bcase(test,ix=0,mc=-1,**kw): return s.case(test,'B',ix,mc,**kw)

def batches(smoke=False,preflight=False):
    inds=[0,6] if smoke or preflight else range(12)
    bs=[[bcase('K1',i) for i in inds]]
    if preflight:
        bs += [[bcase('K5AC',i,m) for i in [0,6] for m in range(10)]]
        return bs
    bs += [[bcase('K3',i) for i in inds]]
    n=2 if smoke else 500
    bs += [[bcase('K5AC',i,m) for i in ([0,6] if smoke else [0,3,6,9]) for m in range(n)]]
    bs += [[bcase('K5NOISE',i,m) for i in [0,6] for m in range(1 if smoke else 100)]]
    bs += [[bcase('K5OP',i,m) for i in ([0,6] if smoke else [0,3,6,9]) for m in range(n)]]
    prot=[]
    for rp,rn in ([(4.8,5)] if smoke else [(4.8,4.8),(4.8,5),(5,4.8),(5,5)]):
        for ix,lim,cpl in ([(0,40,0),(6,100,0)] if smoke else [(i,40,0) for i in [0,1,5,6,11]]+[(i,100,cpl) for i in [0,6] for cpl in [0,1]]):
            prot.append(bcase('K6',ix,rail_plus_set_V=rp,rail_minus_set_V=rn,dc_limit_V=lim,CPL=cpl))
    bs += [prot]
    bs += [[bcase('K6REC',ix,kind='overload',amp=a) for ix,amps in ([(0,[.2,-.2]),(6,[40,-40])] if smoke else [(0,[.2,2,4.5,-.2,-2,-4.5]),(6,[20,40,-20,-40])]) for a in amps]]
    bs += [[bcase('K2',i,kind='step',amp=s.SCALES[i]) for i in inds]]
    bs += [[bcase('K5OP',i) for i in inds], [bcase('K8',kind='idle')]]
    return bs

def a_guard():
    # All existing S9 result files are read-only, including A aggregates and K0.
    # Hash every file (also calibration_B's historical empty file); exclude new s9b outputs.
    paths=[p for p in (ROOT/'resultados').glob('*') if p.is_file() and not p.name.startswith('s9b_')]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--preflight',action='store_true');ap.add_argument('--smoke',action='store_true');ap.add_argument('--resume',action='store_true');a=ap.parse_args()
    gate=json.loads((ROOT/'resultados/s9b_puerta_k0.json').read_text())
    digest=hashlib.sha256(MODEL.read_bytes()).hexdigest()
    if not gate['passed'] or gate['model_sha256']!=digest:raise RuntimeError('K0 missing/failed or model changed')
    f=json.loads((ROOT/'resultados/s9_filtros.json').read_text());s.FILTERS['A']=s.FILTERS['B']=tuple(f['A'])
    profile='preflight' if a.preflight else 'smoke' if a.smoke else 'campaign'
    work=ROOT/'S9/B_hoja'/profile;work.mkdir(parents=True,exist_ok=True)
    lock=work/'s9b_model_lock.json'
    if lock.exists():
        if json.loads(lock.read_text())['model_sha256']!=digest:
            raise RuntimeError('Existing case directory belongs to a different model')
    elif any(work.glob('s9_k*.json')):
        if not (work/'s9b_meta.json').exists():
            raise RuntimeError('Interrupted directory lacks a model lock; verify before resuming')
        if json.loads((work/'s9b_meta.json').read_text())['model_sha256']!=digest:
            raise RuntimeError('Existing completed directory model mismatch')
    s.write(lock,json.dumps(dict(model_sha256=digest,filters=s.FILTERS,seed=s.SEED)))
    prev=json.loads((work/'s9b_meta.json').read_text()) if a.resume and (work/'s9b_meta.json').exists() else {}
    if a.resume and prev.get('model_sha256',digest)!=digest:raise RuntimeError('Resume model mismatch')
    before=s.protected()|a_guard();s.write(work/'protected_before.json',json.dumps(before))
    start=time.perf_counter();rows=[];extras={};records=[];expected=0
    if a.preflight:
        dist=[dict(mc=n,rail_plus_V=r['rp'],rail_minus_mag_V=r['rn'],vref_V=r['vref'],**r['offsets']) for n in range(10) for r in [s.sb.realization(n)]]
        s.csv_write(work/'s9b_mc_10.csv',dist,list(dist[0]))
    for batch in batches(a.smoke,a.preflight):
        expected+=len(batch);rr,ex,recs=s.execute(batch,work,a.resume);rows+=rr;records+=recs
        for key,vals in ex.items():extras.setdefault(key,[]).extend(vals)
        s.csv_write(work/'s9b_all.csv',rows,s.FIELDS)
        s.write(work/'s9b_checkpoint.json',json.dumps(dict(rows=rows,extras=extras,records=records)))
    after=s.protected()|a_guard();changed=[k for k,v in before.items() if after.get(k)!=v]
    s.write(work/'protected_after.json',json.dumps(after))
    meta=dict(returncode=int(len(rows)!=expected or bool(changed)),logical_cases=expected,successful=len(rows),simulations=sum(1 for r in records if '_analysis_attempt' not in r['id']),seconds=time.perf_counter()-start+prev.get('seconds',0),workers=10,seed=s.SEED,profile=profile,protected_count=len(before),protected_changed=changed,filters=s.FILTERS,model_sha256=digest)
    s.write(work/'s9b_meta.json',json.dumps(meta,indent=2));s.write(work/'s9b_records.json',json.dumps(records,indent=2))
    out=ROOT/'resultados' if profile=='campaign' else work
    s.csv_write(out/'s9b_all.csv',rows,s.FIELDS)
    for test in sorted({r['test'] for r in rows}):s.csv_write(out/('s9b_'+test.lower()+'.csv'),[r for r in rows if r['test']==test],s.FIELDS)
    for key,rs in extras.items():s.csv_write(out/f's9b_{key}.csv',rs,s.EXTRA_FIELDS[key])
    print(json.dumps(meta),flush=True)
    return meta['returncode']
if __name__=='__main__':raise SystemExit(main())
