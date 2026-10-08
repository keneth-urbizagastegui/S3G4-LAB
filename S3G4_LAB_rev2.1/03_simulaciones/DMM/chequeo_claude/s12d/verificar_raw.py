"""Recalcula desde .raw un caso de E3, E5 y E8 del smoke S12d (copia en C:/s12d). Uso: python verificar_raw.py <dir S12d>"""
import sys,os,numpy as np,warnings;warnings.filterwarnings('ignore')
sys.path.insert(0,os.path.dirname(__file__));import rawlt
S=sys.argv[1]
def R(f): return rawlt.read(os.path.join(S,f+'.raw'))[1]
# E3: -50 V en rango 200 mV (sobrecarga): riel mux y pinza IN+ continua
d=R('e3_2036960e77ceb0a3407d');t=d['time'];m=t>1e-3
print('E3 max|V(mux)| =%.4f V (lim 4.95)'%np.nanmax(np.abs(d['V(mux)'])))
for b in ('xbuf0','xbuf2'):
    s=[np.nanmax(np.abs(d[f'I({b}:x_u5:S{k})'][m])) for k in (1,2,3,4)]
    print('E3',b,'|I| ESD S1..S4 t>1ms (A):',['%.3g'%x for x in s])
print('E3 I(Vib0) max t>1ms %.3g A, I(Vibn0) %.3g A'%(np.nanmax(np.abs(d['I(Vib0)'][m])),np.nanmax(np.abs(d['I(Vibn0)'][m]))))
# otros E3 del smoke: error en rango
for f in ('e3_68a85525270bfc05583a','e3_d4f8f9fe4e3c4b9ee2ff'):
    d=R(f);t=d['time'];
    for tt in (21.1e-3,24e-3):
        i=np.searchsorted(t,tt);print('E3',f,'t=%.1fms V(out)=%.6g V(x2)=%.6g V(vin)=%.6g'%(tt*1e3,d['V(out)'][i],d['V(x2)'][i],d['V(vin)'][i]))
# E5: PM
d=R('e5_2e54e1c05cf50543c809');f=d['frequency'].real;T=-d['V(inv)']/d['V(test)'];g=np.abs(T)
k=np.where((g[:-1]>=1)&(g[1:]<1))[0][0];ph=np.unwrap(np.angle(T))
x=(0-np.log(g[k]))/(np.log(g[k+1])-np.log(g[k]));p=ph[k]+x*(ph[k+1]-ph[k])
print('E5 fc=%.4g Hz PM=%.2f deg'%(np.exp(np.log(f[k])+x*np.log(f[k+1]/f[k])),180+np.degrees(p)%360-360 if np.degrees(p)>0 else 180+np.degrees(p)))
# E8: conduccion diodos de pinza
d=R('e8_b19988880df4a7e557f5')
for n in ('I(xbpin0:Dhi)','I(xbpin0:Dlo)','I(xbpin2:Dhi)','I(xbpin2:Dlo)'):print('E8',n,'max|I|=%.4g A (lim 5e-3)'%np.nanmax(np.abs(d[n])))
