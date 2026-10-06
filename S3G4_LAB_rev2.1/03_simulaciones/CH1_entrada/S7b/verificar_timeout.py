import sys,time
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ejecutar_s7b as s
p=Path(__file__).parent/'solver_check'/'alt.cir'
t=time.perf_counter()
try:
 s.run_lt(p,p.parent,2)
 raise AssertionError('Expected numerical timeout')
except s.subprocess.TimeoutExpired:
 print('TIMEOUT VERIFIED',round(time.perf_counter()-t,2),flush=True)
