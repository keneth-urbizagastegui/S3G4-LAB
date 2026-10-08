"""Recalcula desde el .raw un caso E3 (X0, 200 mV) y uno E6 (S11.4 GDT solo, -4 kV)."""
import sys,glob,numpy as np
import os;sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from leer_raw import leer
D=sys.argv[1] if len(sys.argv)>1 else r'C:\s12a\r\s\DMM\S12'
f=[x for x in glob.glob(D+'/*qE3*x0*.raw') if '.op.' not in x and 'a0d2_cq0' in x][0];r=leer(f)
t=r['time'];y=r['V(out)'];cnt=0.2/20000*10.1  # 1 cuenta en salida del rango 200 mV x10.1
tgt=2.02;err=np.abs(y-tgt);bad=np.where((err>cnt/2)&(t>=1e-3))[0]
print('E3 X0 200mV final',y[-1],'err cuentas',(y[-1]-tgt)/cnt,'asiento desde 1 ms',t[bad[-1]]-1e-3 if len(bad) else 0)
f=[x for x in glob.glob(D+'/*qE6*.raw') if '.op.' not in x][0];r=leer(f)
v=lambda n:r.get(f'V({n})',0*r['time'])
for a,b in (('vin','mid1'),('mid1','d1'),('d1','mid2'),('mid2','d2'),('d2','mid3'),('mid3','x1')):
    print('E6',a,b,'max',np.max(np.abs(v(a)-v(b))))
d=np.abs(v('vin')-v('mid1'));tt=r['time'];m=d>0.5*d.max()
print('E6 duracion >50% del pico',(tt[m].max()-tt[m].min())*1e9,'ns; >200V', (np.sum(np.diff(tt)[(d>200)[:-1]]))*1e9,'ns')
k=np.argmax(d);print('E6 pico en t=',tt[k]*1e9,'ns; puntos',len(tt))
for lev in (50,100,150):
    s=np.where(d>lev)[0];print(f' >{lev} V: de {tt[s].min()*1e9:.3f} a {tt[s].max()*1e9:.3f} ns' if len(s) else f' >{lev}: no')
