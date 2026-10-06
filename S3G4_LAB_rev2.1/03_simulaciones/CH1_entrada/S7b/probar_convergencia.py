"""Numerical-only solver experiments; no circuit/model changes."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
import re,subprocess,time
from concurrent.futures import ThreadPoolExecutor
w=Path(__file__).parent/'solver_check';w.mkdir(exist_ok=True)
c=s.case('J1DC',3,0,phase='K2DC',kind='dc')
def run(cfg):
 name,solver,options=cfg
 deck=s.net(dict(c,dac_point=True,k2_sweep='gainplus'))
 deck=re.sub(r'^\.dc .*$', '.op',deck,flags=re.M)
 deck=re.sub(r'^\.meas .*$', '',deck,flags=re.M)
 deck=deck.replace('solver=alt','solver='+solver).replace('gminsteps=0',options)
 p=w/(name+'.cir');s.write(p,deck)
 t=time.perf_counter()
 try:
  proc=subprocess.run([str(s.LT),'-b',str(p)],cwd=w,capture_output=True,timeout=30)
  log=p.with_suffix('.log').read_text(errors='replace')
  raw=s.old.s4.s3.raw_read(p.with_suffix('.raw')) if p.with_suffix('.raw').exists() else {}
  print(name,proc.returncode,round(time.perf_counter()-t,2),raw.get('v(pin)'),log[-200:],flush=True)
 except Exception as e:print(name,repr(e),flush=True)
with ThreadPoolExecutor(max_workers=5) as pool:
 list(pool.map(run,[('normal','normal','gminsteps=0 srcsteps=0'),('alt','alt','gminsteps=0 srcsteps=0'),('normal_gmin','normal','gminsteps=25 srcsteps=0'),('normal_relax','normal','gminsteps=0 srcsteps=0 reltol=1e-4'),('alt_relax','alt','gminsteps=0 srcsteps=0 reltol=1e-4')]))
