"""Auditoría Claude S12b, E5: margen de fase de A (x1, Ron 400 ohm) según lo que mueve la entrada no inversora.
Copia el deck de Codex a C:/s12b/e5 y cambia solo la fuente de la entrada + de A."""
import re,subprocess,numpy as np,shutil
from pathlib import Path
DMM=Path(__file__).resolve().parents[2];W=Path('C:/s12b/e5');W.mkdir(parents=True,exist_ok=True)
LT=Path.home()/'AppData/Local/Programs/ADI/LTspice/LTspice.exe'
base=(DMM/'S12b/a0d1_g1_kloop_i0_m192_qe5_r4d9_x0_s0d006_t23_ron400_u0.cir').read_text()
def raw(p):
    h=p.open('rb').read(60000);enc='utf-16-le' if b'\x00' in h[:80] else 'utf-8'
    m='Binary:\n'.encode(enc);o=h.find(m);hd=h[:o].decode(enc)
    nv=int(re.search(r'No. Variables:\s*(\d+)',hd)[1]);n=int(re.search(r'No. Points:\s*(\d+)',hd)[1])
    names=[x[1].lower() for x in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',hd,re.M)]
    a=np.fromfile(p,dtype='<c16',offset=o+len(m)).reshape(n,nv);return {k:a[:,i] for i,k in enumerate(names)}
def pm(name,txt):
    p=W/f'{name}.cir';p.write_text(txt);subprocess.run([str(LT),'-b',str(p)],timeout=300)
    d=raw(p.with_suffix('.raw'));f=d['frequency'].real;T=-d['v(inv)']/d['v(test)']
    i=np.flatnonzero(np.abs(T)<=1)[0];ph=np.unwrap(np.angle(T))*180/np.pi
    # Método de Codex: primer punto con |T|<=1 (rejilla 100/déc), sin interpolar.
    # Claude: interpolación en log|T| frente a log f entre i-1 e i.
    m=np.log10(np.abs(T));x=(0-m[i-1])/(m[i]-m[i-1]);fc=10**(np.log10(f[i-1])+x*(np.log10(f[i])-np.log10(f[i-1])));pmi=180+ph[i-1]+x*(ph[i]-ph[i-1])
    print(f'{name:30s} rejilla: fc={f[i]/1e6:6.3f} MHz PM={180+ph[i]:7.3f} | interpolado: fc={fc/1e6:6.3f} MHz PM={pmi:7.3f} deg');return pmi
V={}
V['codex_s12b']=base
V['buffer_ideal(E)']=base.replace('Xbuf0 bi0 bn0 vp vn bx0 OPAx192','Ebuf0 bx0 0 bi0 0 1\nRdum0 bn0 bx0 1')
V['A_desde_x0_como_S12']=base.replace('Rsel bx0 mux','Rsel x0 mux')
for r in (100,220,470,1000):
    V[f'R_iso_{r}_buffer->mux']=base.replace('Rsel bx0 mux {RON}',f'Riso bx0 bxi {r}\nRsel bxi mux {{RON}}')
V['codex_ron60']=base.replace('RTMUX=400','RTMUX=60')
V['C_mux_+100p']=base.replace('Cextra mux 0 0.0','Cextra mux 0 100p')
V['Ron520_85C']=base.replace('RTMUX=400','RTMUX=520')
for c in (5,3):V[f'Ctm_{c}p']=base.replace('Ctm inv 0 10p',f'Ctm inv 0 {c}p')
V['CDon_pi_5p+5p_Ron400']=base.replace('Ctm inv 0 10p','Ctm inv 0 5p'+chr(10)+'Ctmo g1 0 5p')
V['CDon_pi_5p+5p_Ron520']=V['CDon_pi_5p+5p_Ron400'].replace('RTMUX=400','RTMUX=520')
V['CDon_pi_Cf5p_Ron520']=V['CDon_pi_5p+5p_Ron520'].replace('Ctmo g1 0 5p','Ctmo g1 0 5p'+chr(10)+'Cf out inv 5p')
b10=(DMM/'S12b/a0d1_g10d1_kloop_i0_m192_qe5_r4d9_x0_s0d006_t23_ron400_u0.cir').read_text()
V['x10_codex']=b10
for cf in (2,3,5):
    V[f'Cf_{cf}p_out-inv_x1']=base.replace('Ctm inv 0 10p','Ctm inv 0 10p'+chr(10)+f'Cf out inv {cf}p')
    V[f'Cf_{cf}p_out-inv_x10']=b10.replace('Ctm inv 0 10p','Ctm inv 0 10p'+chr(10)+f'Cf out inv {cf}p')
    V[f'Cf_{cf}p_x1_Ron520']=V[f'Cf_{cf}p_out-inv_x1'].replace('RTMUX=400','RTMUX=520')
for k,t in V.items():V[k]=pm(k.replace('(','_').replace(')','').replace('>','').replace('+',''),t)
