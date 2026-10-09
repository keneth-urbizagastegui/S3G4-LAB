"""S12c: targeted 100ns E3 convergence checks, separate signed cases."""
import concurrent.futures as cf,hashlib,json,time,csv
from pathlib import Path
import ejecutar_s12c as s

def main():
    cases=[]
    # New 20V range settling and /100 at both 50V polarities.
    for amp,g in ((20,10.1),(50,1),(-50,1)):
        c=next(c for c in s.cases() if c['q']=='E3' and c['kind']=='zero' and c['sel']==2 and c['gain']==g and c['amp']==amp and c['charge']==0)
        cases.append(dict(c,verification='maxstep100ns'))
    # Verify any rail violation too: S12b showed coarse steps can change this
    # verdict by millivolts. Never silently replace such a peak with a pass.
    path=s.RESULTS/'s12c_campaign.csv'
    if path.exists():
        rows=list(csv.DictReader(path.open(encoding='utf-8-sig')))
        bad={r['id'] for r in rows if r['q']=='E3' and r.get('all_channels_rail_pass')=='False'}
        valid=[r for r in rows if r['q']=='E3' and r.get('error_at_wait_counts')]
        if valid:bad.add(max(valid,key=lambda r:abs(float(r['error_at_wait_counts'])))['id'])
        for c in s.cases():
            name=c['q'].lower()+'_'+hashlib.sha256(s.ident(c).encode()).hexdigest()[:20]
            if name in bad and c['kind']=='zero':
                cc=dict(c,verification='maxstep100ns')
                if cc not in cases:cases.append(cc)
    for amp in (-50,50):
        c=next(c for c in s.cases() if c['q']=='E8' and c['kind']=='stress50' and c['amp']==amp)
        cases.append(dict(c,verification='ti_esd_traces'))
    original=s.deck;signature=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    def deck(c):
        text=original(c).replace(f'.tran 0 {c["stop"]} 0 1u',f'.tran 0 {c["stop"]} 0 100n')
        if c['kind']=='stress50':
            text=text.replace('.end','.save I(Xbuf0:X_U5:S1) I(Xbuf0:X_U5:S2) I(Xbuf0:X_U5:S3) I(Xbuf0:X_U5:S4)\n.end')
        return text.replace('.end',f'* verification_source_sha256 {signature}\n.end')
    s.deck=deck;start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(lambda c:s.run(c,True),cases))
    s.writecsv(s.RESULTS/'s12c_verificacion.csv',rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),elapsed_s=time.perf_counter()-start,reused=sum(r.get('reused',False) for r in rows))
    (s.RESULTS/'s12c_verificacion.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary))
    for r in rows:print({k:r.get(k) for k in ('q','amp','gain','status','error','error_at_wait_counts','error_at_3ms_counts','final_error_counts','bx0_peak_V','bi0_peak_V','buffer0_clamp_peak_A','buffer0_TI_direct_clamp_peak_A','all_channels_rail_pass')})
    return int(summary['ok']!=summary['total'])

if __name__=='__main__':raise SystemExit(main())
