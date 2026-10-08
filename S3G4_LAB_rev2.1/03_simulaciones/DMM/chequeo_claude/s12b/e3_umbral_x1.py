"""Auditoría Claude S12b, E3: error estático de X2 en 50 V según Vin (buffer X1 sobreexcitado).
Copia el deck de Codex (X2, +50 V, 0 pC) a C:/s12b/e3 y cambia solo la amplitud;."""
import re,subprocess,numpy as np
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys;sys.path.insert(0,str(Path(__file__).parent));from recalcular_raw import raw
DMM=Path(__file__).resolve().parents[2];W=Path('C:/s12b/e3');W.mkdir(parents=True,exist_ok=True)
LT=Path.home()/'AppData/Local/Programs/ADI/LTspice/LTspice.exe'
base=(DMM/'S12b/a50_cq0_g1_kzero_i0_m192_pretime0d02_qe3_r4d9_x2_s0d028_t23_ron60_u0.cir').read_text()
assert base.count('20u 50 ')==1
def one(v):
    p=W/f'x2_{v:g}V.cir'.replace('.','p',1) if False else W/f'x2_{str(v).replace(".","p")}V.cir'
    p.write_text(base.replace('20u 50 ',f'20u {v} ').replace(' 0.028 50)',f' 0.028 {v})'));subprocess.run([str(LT),'-b',str(p)],timeout=600)
    d=raw(p.with_suffix('.raw'));t=np.abs(d['time']);tail=t>.0278;lsb=.01*.1/10.01;exp=v*.1/10.01
    out=d['v(out)'][tail].mean();w=np.interp(.0225,t,d['v(out)'])
    return f'Vin={v:5.1f} V: X1p≈{v*1.01/10.01:.3f} V; I(Vib1)={d["i(vib1)"][tail].mean()*1e9:7.3f} nA; err final={(out-exp)/lsb:+.3f} cuentas; err a 1.5 ms={(w-exp)/lsb:+.3f}'
with ThreadPoolExecutor(5) as ex:
    for s in ex.map(one,tuple(float(a) for a in sys.argv[1:]) or (48,49,49.5,50,52)):print(s)
