"""Final integrity/accounting audit, including preserved A acta and campaign."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json
from pathlib import Path
import ejecutar_s9_b as b

ROOT=b.ROOT


def snapshot():
    paths=[p for p in (ROOT/'resultados').glob('*') if p.is_file() and not p.name.startswith('s9b_') and p.name!='s9_tabla_calibracion_B.csv']
    paths += [p for p in (ROOT/'S9/campaign').rglob('*') if p.is_file()]
    protected={}
    for ix,p in enumerate(paths,1):
        protected[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
        if ix%10000==0:print('Integrity progress:',ix,'/',len(paths),flush=True)
    acta=(ROOT/'ACTA_S9.md').read_text(encoding='utf-8')
    begin='<!-- S9_B_CODEX_BEGIN -->';end='<!-- S9_B_CODEX_END -->'
    before,rest=acta.split(begin,1);_,after=rest.split(end,1)
    protected['ACTA_OUTSIDE_B']=hashlib.sha256((before+after).encode()).hexdigest()
    return protected


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--snapshot',action='store_true');args=ap.parse_args()
    path=ROOT/'resultados/s9b_integridad_base.json'
    current=snapshot()
    if args.snapshot:
        if path.exists():raise RuntimeError('Never replace original integrity snapshot')
        b.s.write(path,json.dumps(current))
        print('Integrity baseline:',len(current),'A files and outside-B acta digest')
        return 0
    before=json.loads(path.read_text());changed=[k for k,v in before.items() if current.get(k)!=v]
    reports=[ROOT/'S9/B_hoja/campaign/s9b_auditoria_codex.json',ROOT/'S9/B_hoja/smoke/s9b_auditoria_codex.json',ROOT/'S9/B_hoja/op_corregido/s9b_op_corregido_auditoria.json',ROOT/'resultados/s9b_smoke_repeticion.json']
    audits=[json.loads(p.read_text()) for p in reports]
    original=ROOT/'S9/B_hoja/campaign';corrected=ROOT/'S9/B_hoja/op_corregido'
    metadata=[json.loads((original/'s9b_meta.json').read_text()),json.loads((corrected/'s9b_op_corregido_meta.json').read_text())]
    warnings=[];history=[]
    for work in [original,corrected]:
        hh=[json.loads(l) for l in (work/'native_history.jsonl').read_text().splitlines()]
        history.append(dict(profile=work.name,native_attempts=len(hh),failed_attempts=sum(r['returncode']!=0 for r in hh),native_elapsed_sum_s=sum(r['seconds'] for r in hh),failure_kinds=sorted(set(str(r['errors']) for r in hh if r['returncode']!=0))))
        data=json.loads((work/('s9b_checkpoint.json' if work==original else 's9b_op_corregido_checkpoint.json')).read_text())
        records=[r for r in data['records'] if '_analysis_attempt' not in r['id']]
        final=list({r['id']:r for r in records}.values())
        warnings.append(dict(profile=work.name,final_native_ids=len(final),final_failed=sum(r['returncode']!=0 for r in final),warning_cases=sum(bool(r['warnings']) for r in final),warning_messages=sum(len(r['warnings']) for r in final)))
    bad=bool(changed) or any(a['returncode'] for a in audits) or any(m['successful']!=m['logical_cases'] for m in metadata) or any(w['final_failed'] for w in warnings)
    # Guard snapshots compare CH1/models and shared memory during each run.
    guards=[]
    for work in [original,corrected]:
        old=json.loads((work/'protected_before.json').read_text());new=json.loads((work/'protected_after.json').read_text())
        changes=[k for k,v in old.items() if new.get(k)!=v]
        shared=[k for k in changes if Path(k).name in ['STATE.md','DECISIONS.md'] and Path(k).parent.name=='ai-context']
        guards.append(dict(profile=work.name,protected_count=len(old),changed=changes,shared_memory_changes=shared,circuit_or_A_changes=[k for k in changes if k not in shared]))
    bad=bad or any(g['circuit_or_A_changes'] for g in guards)
    result=dict(returncode=int(bad),A_protected_files=len(before),A_changed=changed,audits_passed=all(a['returncode']==0 for a in audits),guards=guards,metadata=metadata,history=history,final_native_status=warnings,notes='No simulations run by this audit. A calibration/table/campaign and acta outside B byte-for-byte preserved. B calibration output explicitly excluded. Shared-memory guard changes are reported separately and never erase runner returncodes: external STATE edit at20:41:07 added Claude resumption reference; earlier DECISIONS change documented in prior journal. Codex shared-memory closure occurs only after all campaign guards.')
    b.s.write(ROOT/'resultados/s9b_auditoria_cierre.json',json.dumps(result,indent=2))
    print(json.dumps({k:result[k] for k in ['returncode','A_protected_files','A_changed','audits_passed','guards','final_native_status']}))
    return result['returncode']


if __name__=='__main__':raise SystemExit(main())
