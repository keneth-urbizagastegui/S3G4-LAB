"""Auditoría Claude S12b: recálculo independiente desde .raw (E3 X2/±50 V, E8 peor)."""
import re,sys,numpy as np
from pathlib import Path
DMM=Path(__file__).resolve().parents[2]; S=DMM/'S12b'
def raw(p):
    h=p.open('rb').read(60000);enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8'
    m='Binary:\n'.encode(enc);o=h.find(m);hd=h[:o].decode(enc)
    nv=int(re.search(r'No. Variables:\s*(\d+)',hd)[1]);n=int(re.search(r'No. Points:\s*(\d+)',hd)[1])
    names=[x[1].lower() for x in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hd,re.M)]
    a=np.memmap(p,dtype='<f8',mode='r',offset=o+len(m),shape=(n,nv));return {k:np.array(a[:,i]) for i,k in enumerate(names)}
def e3(amp,q='0'):
    d=raw(S/f'a{amp}_cq{q}_g1_kzero_i0_m192_pretime0d02_qe3_r4d9_x2_s0d028_t23_ron60_u0.raw');t=np.abs(d['time'])
    amp=float(amp.replace('m','-'));lsb=.01*.1/10.01;exp=amp*.1/10.01;tail=t>.028-.0002
    out=d['v(out)'].mean(where=tail) if False else d['v(out)'][tail].mean()
    w=np.interp(.021+.0015,t,d['v(out)'])
    print(f'E3 X2 {amp:+.0f}V q={q}: Vout_fin={out:.7f} esperado={exp:.7f} err_fin={(out-exp)/lsb:+.4f} cuentas; err@1.5ms={(w-exp)/lsb:+.4f}')
    for k in ('v(x2)','v(bx1)','i(vib1)','i(vibn1)','v(bx0)','i(vib0)'):
        if k in d:print(f'   {k} final={d[k][tail].mean():.6g}')
    x2=d['v(x2)'][tail].mean();print(f'   error ya en X2: {(x2-exp)/lsb:+.4f} cuentas')
if __name__=="__main__":
    for a in ("50","m50","20"):e3(a)
