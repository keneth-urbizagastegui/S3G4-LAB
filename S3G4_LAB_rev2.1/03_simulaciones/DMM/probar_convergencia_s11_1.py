"""Isolated numerical diagnostics; never substitute these for the campaign."""
import subprocess
import ejecutar_s11_1 as s

c=next(c for c in s.cases() if c['p']=='P3' and c['rs']==100 and c['source']==.001)
c.update(stop=.001,macro='full')
for label,option in [('gshunt1p','gshunt=1e-12'),('gshunt100p','gshunt=1e-10'),('gmin1n','gmin=1e-9')]:
    p=s.JOBS/f'diagnostic_relaunch_{label}.cir'
    p.write_text(s.deck(c).replace('.end',f'.options {option}\n.end'),encoding='utf-8')
    proc=subprocess.Popen([str(s.LT),'-b',str(p)],creationflags=subprocess.CREATE_NO_WINDOW,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try: proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
        proc.wait()
    values,log=s.parse_log(p.with_suffix('.log'))
    print(label,len(values),log[-250:],flush=True)
