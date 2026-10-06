import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
w=Path(__file__).parent/'tran_check';w.mkdir(exist_ok=True)
for ix,kind in [(1,'step'),(2,'square')]:
 ac=s.case('J1',ix);bias=w/(ac['id']+'.bias');p=w/(ac['id']+'.cir')
 s.write(p,s.net(ac).replace('\n.end\n',f'\n.savebias "{bias}" internal\n.end\n'))
 s.run_lt(p,w,120)
 c=s.case('J2',ix,kind=kind,amp=s.SCALES[ix]*(1 if kind=='step' else 3))
 c['bias_path']=str(bias)
 # Same waveform, time step and tolerances. Only iteration budget increased.
 original=s.net
 def net(c,source_amp=None):
  return original(c,source_amp).replace('.options method=gear','.options itl4=1000 method=gear')
 s.net=net
 t=time.perf_counter();r,e,rec=s.simulate(c,w);s.net=original
 print(ix,kind,'seconds',time.perf_counter()-t,'result',rec,'rise_ns',r.get('rise_ns'),flush=True)
