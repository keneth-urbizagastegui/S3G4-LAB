from pathlib import Path
import subprocess
import ejecutar_s11_1 as s
inc=(s.HERE/'comun/dmm_bloque1.inc').read_text()
c=next(c for c in s.cases() if c['p']=='P2' and c['source']==0)
c.update(stop=.001,step=1e-5)
for variant in ('full','fullnoics','idealrails','noamp'):
    txt=inc
    if variant in ('noic','both'):
        txt='\n'.join(x for x in txt.splitlines() if not x.startswith(('Xm','Xamp')))
        txt+='\nRdiag mux 0 1G\n'
    if variant=='nomux':
        txt='\n'.join(x for x in txt.splitlines() if not x.startswith('Xm'))
        txt+='\nRdiag x0 mux 1u\n'
    if variant=='noamp':
        txt='\n'.join(x for x in txt.splitlines() if not x.startswith('Xamp'))
        txt+='\nRdiag mux 0 1G\nRout out 0 1G\n'
    if variant in ('idealrails','both'):
        txt='\n'.join(x for x in txt.splitlines() if not x.startswith(('Brp ','Brn ')))
        txt+='\nVdiagp rp 0 4.802\nVdiagn rn 0 -4.802\n'
    d=s.deck(c).replace(f'.include "{s.HERE / "comun/dmm_bloque1.inc"}"',txt)
    if variant=='fullnoics': d='\n'.join(x for x in d.splitlines() if not x.startswith('.ic'))
    if variant=='fulluic': d=d.replace('.tran 0 0.001 0 1e-05 ','.tran 0 0.001 0 1e-05 uic')
    p=s.JOBS/f'diagnostic_{variant}.cir'; p.write_text(d)
    proc=subprocess.Popen([str(s.LT),'-b',str(p)])
    try: proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
    vals,log=s.parse_log(p.with_suffix('.log'))
    print(variant,len(vals),log[-500:])
