"""Independent replay in a short temporary path; compare all campaign CSV bytes."""
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import ejecutar_s3b as s


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    base=Path(tempfile.mkdtemp(prefix='s3b-replay-'))
    dest=base/'rev'/'sim'/'CH1_entrada'
    shutil.copytree(s.ROOT,dest,ignore=shutil.ignore_patterns('__pycache__','*.raw','*.db'))
    env=dict(os.environ,S3G4_MODELS=str(s.s3.MODELS),PYTHONDONTWRITEBYTECODE='1')
    print('Replay:',dest,'S3G4_MODELS:',env['S3G4_MODELS'],flush=True)
    with (base/'console.txt').open('w',encoding='utf-8') as output:
        p=subprocess.run([sys.executable,str(dest/'ejecutar_s3b.py')],cwd=dest,env=env,stdout=output,stderr=subprocess.STDOUT)
    run=json.loads((dest/'resultados/s3b_ejecucion.json').read_text(encoding='utf-8'))
    names=[f's3b_b{i}.csv' for i in range(7)]+['s3b_resultados.csv','s3b_criterios.csv','s3b_escalas.csv']
    comparisons=[]
    for name in names:
        original=s.ROOT/'resultados'/name;replay=dest/'resultados'/name
        comparisons.append(dict(file=name,original_sha256=sha(original),replay_sha256=sha(replay),identical=original.read_bytes()==replay.read_bytes()))
    source_names=['ejecutar_s3b.py','ejecutar_s3.py','ejecutar_s2b.py','ejecutar_s2.py','ejecutar_s1b.py','ejecutar_s1.py',
                  'comun/ch1_comun_s3b.inc','comun/ch1_comun_s3.inc','comun/ch1_comun_s2b.inc']
    sources=[dict(file=name,original_sha256=sha(s.ROOT/name),replay_sha256=sha(dest/name),identical=sha(s.ROOT/name)==sha(dest/name)) for name in source_names]
    result=dict(exit_code=p.returncode,simulations=run['simulations'],elapsed_seconds=run['elapsed_seconds'],
                replay_path=str(dest),console_path=str(base/'console.txt'),models=str(s.s3.MODELS),
                csv_count=len(names),csv_identical=sum(c['identical'] for c in comparisons),comparisons=comparisons,
                sources=sources,protected_changed=run['protected_changed'])
    s.write(s.ROOT/'resultados/s3b_reproducibilidad.json',json.dumps(result,indent=2,ensure_ascii=False))
    print(json.dumps({k:result[k] for k in ['exit_code','simulations','elapsed_seconds','csv_count','csv_identical','protected_changed']},indent=2),flush=True)
    return int(bool(p.returncode or not all(c['identical'] for c in comparisons+sources) or run['protected_changed']))


if __name__=='__main__':raise SystemExit(main())
