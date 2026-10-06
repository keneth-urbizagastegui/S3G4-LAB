"""Compare independently executed S3 CSVs and save reviewable SHA256 evidence."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime

ROOT=Path(__file__).resolve().parent


def main():
    parser=argparse.ArgumentParser();parser.add_argument('replay',type=Path)
    args=parser.parse_args();replay=args.replay.resolve()
    run=json.loads((replay/'resultados/s3_ejecucion.json').read_text(encoding='utf-8'))
    files=sorted(p for p in (ROOT/'resultados').glob('s3_*.csv') if not p.name.startswith('s3_smoke_'))
    results=[]
    for p in files:
        other=replay/'resultados'/p.name
        a=hashlib.sha256(p.read_bytes()).hexdigest()
        b=hashlib.sha256(other.read_bytes()).hexdigest()
        results.append(dict(file=p.name,original_sha256=a,replay_sha256=b,equal=a==b))
    sources=[]
    for rel in ['ejecutar_s3.py','ejecutar_s2b.py','ejecutar_s2.py']+[str(p.relative_to(ROOT)) for p in sorted((ROOT/'comun').glob('*.inc'))]:
        a=hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()
        b=hashlib.sha256((replay/rel).read_bytes()).hexdigest()
        sources.append(dict(file=rel,original_sha256=a,replay_sha256=b,equal=a==b))
    ok=len(results)==14 and all(x['equal'] for x in results+sources) and run['exit_code']==0
    evidence=dict(verified_at=datetime.now().astimezone().isoformat(),replay_directory=str(replay),
                  replay_exit_code=run['exit_code'],replay_seconds=run['elapsed_seconds'],
                  replay_simulations=run['simulations'],workers=run['workers'],csv=results,sources=sources,
                  verification_exit_code=int(not ok))
    (ROOT/'resultados/s3_reproducibilidad.json').write_text(json.dumps(evidence,indent=2,ensure_ascii=False),encoding='utf-8')
    print(f'CSV identical: {sum(x["equal"] for x in results)}/{len(results)}; replay code {run["exit_code"]}; verification code {int(not ok)}')
    for x in results:
        if not x['equal']:print('DIFFERENT',x['file'])
    return int(not ok)


if __name__=='__main__':raise SystemExit(main())
