import sys,re,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
w=Path(__file__).parent/'bias_check';w.mkdir(exist_ok=True)
c=s.case('J3',3,0,phase='K2')
p=w/'ac.cir';bias=w/'ac.bias';s.write(p,s.net(c).replace('\n.end\n',f'\n.savebias "{bias}" internal\n.end\n'))
t=time.perf_counter();proc=s.run_lt(p,w,90);print('AC',proc.returncode,time.perf_counter()-t,flush=True)
for f in w.glob('*.raw'):
 raw=s.old.s4.s3.raw_read(f);print(f.name,len(raw),list(raw)[:20],flush=True)
print('BIAS',bias.exists(),flush=True)
for sweep in ['gainplus','gainminus','dacminus','dacplus']:
 c=s.case('J1DC',3,0,phase='K2DC',kind='dc');c.update(dac_point=True,k2_sweep=sweep)
 p=w/(sweep+'.cir');s.write(p,s.net(c).replace('\n.end\n',f'\n.loadbias "{bias}"\n.end\n'))
 t=time.perf_counter()
 try:
  proc=s.run_lt(p,w,45);raw=s.old.s4.s3.raw_read(p.with_suffix('.raw')); print(sweep,proc.returncode,time.perf_counter()-t,len(raw['v(pin)']),raw['v(pin)'][0],raw['v(pin)'][-1],flush=True)
 except Exception as e:print(sweep,repr(e),flush=True)
