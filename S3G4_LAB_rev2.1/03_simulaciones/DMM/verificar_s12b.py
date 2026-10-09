"""Independent finer-step confirmation of S12b worst E3 cases.
Uses100ns throughout, same parts/stimuli; no campaign records overwritten.
Run after campaign, with10-worker executor and900s/case inherited limit.
"""
import argparse,concurrent.futures as cf
import json,time
import ejecutar_s12b as s

original=s.deck
def fine_deck(c):
    return original(c).replace(f'.tran 0 {c["stop"]} 0 1u',f'.tran 0 {c["stop"]} 0 100n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--only-zero-charge',action='store_true');a=ap.parse_args()
    cs=[]
    for sel,charge in ((0,5e-12),(2,0),(0,0)):
        c=next(c for c in s.cases() if c['q']=='E3' and c['amp']==50 and c['sel']==sel and c['gain']==1 and c.get('charge')==charge)
        cs.append(dict(c,fine100ns=1))
    if a.only_zero_charge:cs=[c for c in cs if c['sel']==0 and c['charge']==0]
    else:
        nominal=next(c for c in s.cases() if c['q']=='E1' and c['amp']==.2)
        cs.append(dict(nominal,params={},unit=200,nominal=1))
    s.deck=fine_deck;start=time.perf_counter()
    with cf.ThreadPoolExecutor(max_workers=10) as pool:rows=list(pool.map(lambda c:s.run(c,True),cs))
    label='verificacion50V0pC' if a.only_zero_charge else 'verificacion100ns'
    s.writecsv(s.RESULTS/f's12b_{label}.csv',rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),reused=sum(r.get('reused',False) for r in rows),elapsed_s=time.perf_counter()-start,workers=10,timeout_s=900)
    (s.RESULTS/f's12b_{label}.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    print(json.dumps(summary));print(json.dumps([{k:r.get(k) for k in ('id','bx0_peak_V','all_channels_rail_pass','error_at_wait_counts','final_error_counts','droop20_pct','status')} for r in rows]))

if __name__=='__main__':main()
