"""Refresh partial valid S12b results only after exact canonical deck comparison.
Current RAW audit must succeed; preserve old signature and provenance. No
LTspice launch, no reuse of errors/mismatched decks or preceding campaigns.
"""
import argparse,csv,hashlib,json,time
from pathlib import Path
import ejecutar_s12b as s

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--collect',action='store_true');args=ap.parse_args()
    dependencies=[s.HERE/'ejecutar_s12b.py',s.HERE/'ejecutar_s12.py',s.HERE/'ejecutar_s11_4.py',s.HERE/'gdt_seguimiento/gdt_seguimiento.py',s.HERE/'comun/dmm_bloque2b.inc',s.MODELS/'OPA2192/OPAx192.LIB',s.MODELS/'OPA2188/OPAx188.LIB',s.MODELS/'74HC4051/hc_tnomi.cir']
    material=b''.join(p.read_bytes() for p in dependencies)
    done=0;skipped=0;errors=[];rows=[];start=time.perf_counter()
    for c in s.cases():
        name=s.ident({k:v for k,v in c.items() if k!='base'});p=s.JOBS/(name+'.cir');stamp=p.with_suffix('.json')
        if not p.exists() or not stamp.exists():skipped+=1;continue
        r=json.loads(stamp.read_text());content=s.deck(c)
        if r.get('status')!='ok' or p.read_text(encoding='utf-8')!=content:skipped+=1;continue
        try:
            r.update(s.audit(c,p.with_suffix('.raw')))
            previous=r['signature'];r['signature']=hashlib.sha256(content.encode()+material).hexdigest()
            if previous!=r['signature']:r.setdefault('signature_history',[]).append(previous)
            r['previous_signature']=previous;r['reaudited_exact_deck']=True
            stamp.write_text(json.dumps(r,indent=2),encoding='utf-8');done+=1;rows.append(r)
        except Exception as e:errors.append(dict(id=name,error=str(e)))
    summary=dict(refreshed=done,skipped=skipped,errors=errors,elapsed_s=time.perf_counter()-start,method='exact deck + current RAW audit + current dependency hash')
    (s.RESULTS/'s12b_refresco.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary))
    if args.collect:
        if skipped or errors:raise RuntimeError('Cannot collect incomplete/mismatched campaign')
        dest=s.RESULTS/'s12b_campaign.csv';previous_rows={r['id']:r for r in csv.DictReader(dest.open(encoding='utf-8-sig'))}
        for r in rows:r['reused']=previous_rows.get(r['id'],{}).get('reused')=='True'
        s.writecsv(dest,rows);meta=json.loads(dest.with_suffix('.json').read_text())
        meta['before_reaudit_ok']=meta['ok'];meta.update(total=len(rows),ok=len(rows),reaudited=len(rows),analysis_elapsed_s=summary['elapsed_s'])
        meta['correction50V_elapsed_s']=json.loads((s.RESULTS/'s12b_repeticion50V.json').read_text())['elapsed_s']
        meta['phase_previa_process_wall_s']=json.loads((s.RESULTS/'s12b_fase_previa.json').read_text())['process_wall_elapsed_s']
        meta['elapsed_phases_sum_s']=meta['elapsed_s']+meta['phase_previa_process_wall_s']+meta['correction50V_elapsed_s']+meta['analysis_elapsed_s']
        dest.with_suffix('.json').write_text(json.dumps(meta,indent=2),encoding='utf-8');print(json.dumps(meta))

if __name__=='__main__':main()
