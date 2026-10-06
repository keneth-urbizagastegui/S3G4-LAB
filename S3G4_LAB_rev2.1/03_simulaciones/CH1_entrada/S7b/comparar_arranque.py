import sys,time,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
w=Path(__file__).parent/'warm_mc_check';w.mkdir(exist_ok=True)
results=[]
for phase in ['K2COLDTEST','K2']:
 c=s.case('J3',3,499,phase=phase)
 t=time.perf_counter();r,e,rec=s.simulate(c,w)
 results.append(dict(phase=phase,row=r,record=rec,seconds=time.perf_counter()-t))
 print(phase,rec['returncode'],rec['errors'],results[-1]['seconds'],{k:r.get(k) for k in ['minus3_Hz','peak_db','gain_dc_signed']},flush=True)
s.write(w/'comparison.json',json.dumps(results))
if all(x['row'] for x in results):
 for k in ['minus3_Hz','peak_db','gain_dc_signed','atten_4p5m_db']:
  a,b=[x['row'][k] for x in results]
  print('DELTA',k,b-a,flush=True)
