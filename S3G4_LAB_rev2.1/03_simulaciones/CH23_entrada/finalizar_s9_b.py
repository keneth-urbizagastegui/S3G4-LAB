"""Sequential closure: wait for resume, audit, repeat B smoke, corrected OP, report.

Console files stay in TEMP. This script does not run A, K0, AC or noise again.
"""
import sys
sys.dont_write_bytecode=True
import argparse,ctypes,json,os,subprocess,time
from pathlib import Path

ROOT=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--wait-pid',type=int)
    ap.add_argument('--resume-after-smoke',action='store_true',
                    help='Audit the completed smoke and resume closure without repeating the campaign or smoke')
    args=ap.parse_args()
    if args.wait_pid:
        kernel=ctypes.windll.kernel32
        kernel.OpenProcess.restype=ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes=[ctypes.c_void_p,ctypes.c_ulong]
        kernel.CloseHandle.argtypes=[ctypes.c_void_p]
        handle=kernel.OpenProcess(0x100000,False,args.wait_pid)
        if handle:
            print('Waiting for original B resume PID',args.wait_pid,flush=True)
            while kernel.WaitForSingleObject(handle,1000)==258:pass
            kernel.CloseHandle(handle)
    campaign=ROOT/'S9/B_hoja/campaign'
    meta=json.loads((campaign/'s9b_meta.json').read_text())
    if meta['successful']!=meta['logical_cases']:raise RuntimeError('Original B incomplete')
    record_path=ROOT/'resultados/s9b_cierre.json'
    records=json.loads(record_path.read_text()) if args.resume_after_smoke and record_path.exists() else []
    session_stamp=time.strftime('%Y%m%d_%H%M%S',time.gmtime())
    def run(script,*options):
        log=Path(os.environ['TEMP'])/('s9b_cierre_'+Path(script).stem+'_'+session_stamp+'.log')
        print('Running',script,*options,'log',log,flush=True)
        start=time.perf_counter()
        with log.open('w',encoding='utf-8') as stream:
            completed=subprocess.run([sys.executable,script,*options],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
        record=dict(script=script,options=options,returncode=completed.returncode,seconds=time.perf_counter()-start,console=str(log))
        records.append(record)
        (ROOT/'resultados/s9b_cierre.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print('Finished',json.dumps(record),flush=True)
        if completed.returncode:raise RuntimeError('Stage failed; inspect '+str(log))
    if args.resume_after_smoke:
        smoke_meta=json.loads((ROOT/'S9/B_hoja/smoke/s9b_meta.json').read_text())
        if smoke_meta['returncode'] or smoke_meta['successful']!=25 or smoke_meta['logical_cases']!=25:
            raise RuntimeError('Saved smoke incomplete or unsuccessful; inspect its metadata')
        if smoke_meta['model_sha256']!=meta['model_sha256']:
            raise RuntimeError('Saved campaign and smoke model hashes differ')
        print('Resuming after completed 25-case smoke; original campaign metadata preserved.',flush=True)
    else:
        run('verificar_s9_b.py')
        run('ejecutar_s9_b.py','--smoke')
    run('verificar_s9_b.py','--smoke')
    # Compare regenerated B smoke numerically against preserved final baseline.
    base=json.loads((ROOT/'resultados/s9b_smoke_baseline.json').read_text())
    current=json.loads((ROOT/'S9/B_hoja/smoke/s9b_checkpoint.json').read_text())
    oldrows={r['id']:r for r in base['rows']}; newrows={r['id']:r for r in current['rows']}
    if oldrows.keys()!=newrows.keys():raise RuntimeError('Smoke state set changed')
    differences=[]
    for ident,row in oldrows.items():
        for key,value in row.items():
            new=newrows[ident].get(key)
            if isinstance(value,(int,float)) and not isinstance(value,bool) and isinstance(new,(int,float)):
                if abs(new-value)>1e-9*max(1,abs(value)):differences.append(dict(id=ident,metric=key,old=value,new=new))
            elif new!=value: differences.append(dict(id=ident,metric=key,old=value,new=new))
    comparison=dict(logical_cases=len(newrows),differences=differences,returncode=int(bool(differences)),relative_tolerance=1e-9,absolute_tolerance=1e-9)
    (ROOT/'resultados/s9b_smoke_repeticion.json').write_text(json.dumps(comparison,indent=2),encoding='utf-8')
    if differences:raise RuntimeError('Smoke changed; review measured differences before corrected OP')
    run('ejecutar_s9_b_op_corregido.py','--resume')
    run('verificar_s9_b_op_corregido.py')
    run('informar_s9_b.py')
    print('Simulation closure complete; shared STATE/journal/sync still require root agent.',flush=True)


if __name__=='__main__':main()
