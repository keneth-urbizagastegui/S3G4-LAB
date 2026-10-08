"""Auditoría Claude S12b, E8: separa la corriente de entrada del buffer X0 en pinza (resistiva) y capacitiva."""
import re,sys,numpy as np
from pathlib import Path
DMM=Path(__file__).resolve().parents[2]
def raw(p):
    h=p.open('rb').read(60000);enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8'
    m='Binary:\n'.encode(enc);o=h.find(m);hd=h[:o].decode(enc)
    nv=int(re.search(r'No. Variables:\s*(\d+)',hd)[1]);n=int(re.search(r'No. Points:\s*(\d+)',hd)[1])
    names=[x[1].lower() for x in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hd,re.M)]
    a=np.fromfile(p,dtype='<f8',offset=o+len(m)).reshape(n,nv);return {k:a[:,i] for i,k in enumerate(names)}
def dur(t,y,lim):
    m=y>lim;return float(np.sum(np.diff(t)[m[:-1]&m[1:]]))
def ana(p,ch=0):
    d=raw(p);t=np.abs(d['time']);i=d[f'i(vib{ch})'];b=d[f'v(bi{ch})'];x=d[f'v(bx{ch})'];rp=d['v(rp)'];rn=d['v(rn)']
    ihi=np.clip(b-rp-.5,0,None)/1;ilo=np.clip(rn-b-.5,0,None)/1;icl=ihi-ilo
    icap=i-icl
    k=np.argmax(np.abs(i))
    print(f'{p.name[:60]} canal {ch}')
    print(f'  pico |I|={abs(i[k])*1e3:.3f} mA en t={t[k]*1e9:.1f} ns; pinza en ese instante {icl[k]*1e3:+.3f} mA, capacitiva {icap[k]*1e3:+.3f} mA')
    print(f'  pico pinza={np.max(np.abs(icl))*1e3:.3f} mA; pico capacitiva={np.max(np.abs(icap))*1e3:.3f} mA')
    for lim in (5e-3,10e-3):print(f'  tiempo |I|>{lim*1e3:.0f} mA: {dur(t,np.abs(i),lim)*1e9:.1f} ns; pinza>{lim*1e3:.0f} mA: {dur(t,np.abs(icl),lim)*1e9:.1f} ns')
    q=np.trapezoid(np.abs(icl),t);print(f'  carga pinza={q*1e9:.2f} nC; carga |I| total={np.trapezoid(np.abs(i),t)*1e9:.2f} nC; I2t pinza={np.trapezoid(icl**2,t)*1e9:.3f} nA2s')
    print(f'  V(bi)-rail max={np.max(np.maximum(b-rp,rn-b)):.3f} V; rp max={rp.max():.2f} V, rn min={rn.min():.2f} V')
S=DMM/'S12b'
if __name__=='__main__':
 for n in sys.argv[1:] or ['am8000_chaingdtmov_g1_kprotection_i0_mreduced_qe8_r4d998_x0_s5em05_tau1em07_t25_ron60_u884','a8000_chaingdtmov_g1_kprotection_i0_mreduced_qe8_r4d998_x0_s5em05_tau1em07_t25_ron60_u902']:
    p=Path(n) if n.endswith('.raw') else S/(n+'.raw')
    for ch in (0,1):ana(p,ch)
