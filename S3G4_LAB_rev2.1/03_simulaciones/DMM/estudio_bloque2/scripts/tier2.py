import numpy as np
from scipy.optimize import least_squares
from red import *
def hf(p, sel, buf2):
    f=np.array([100e3]); h=h_div_buf(f,p,sel,buf2=buf2); h0=h_div_buf(np.array([1e-3]),p,sel,buf2=buf2)[0]
    return (abs(h[0])/abs(h0)-1)*100
for buf2 in (False, True):
    p=par()
    print('buf2=',buf2,'H tal cual: X1 %.2f %%  X2 %.2f %%' % (hf(p,1,buf2),hf(p,2,buf2)))
    r=least_squares(lambda x:[hf(par(C2=x[0]*1e-12,C3=x[1]*1e-9),1,buf2),hf(par(C2=x[0]*1e-12,C3=x[1]*1e-9),2,buf2)],[300,3.0])
    print('  optimo C2=%.1f pF C3=%.3f nF' % (r.x[0],r.x[1]), 'con 270/2.7:', np.round([hf(par(C2=270e-12,C3=2.7e-9),1,buf2),hf(par(C2=270e-12,C3=2.7e-9),2,buf2)],2),
          'con 300/2.7 (E24):', np.round([hf(par(C2=300e-12,C3=2.7e-9),1,buf2),hf(par(C2=300e-12,C3=2.7e-9),2,buf2)],2))
f=np.array([40,1e3,10e3,20e3])
p=par(C2=270e-12,C3=2.7e-9)
print('X0 con buffer, error %:', np.round((np.abs(h_x0_buf(f,p))-1)*100,2))
# sensibilidad a +-5 pF de la carga del nodo ÷10 y ÷100 con y sin buffer
for nm,fn in [('X1 sin buffer', lambda q: abs(h_div(np.array([20e3]),q,1)[0])/abs(h_div(np.array([1e-3]),q,1)[0])),
              ('X1 con buffer', lambda q: abs(h_div_buf(np.array([20e3]),q,1)[0])/abs(h_div_buf(np.array([1e-3]),q,1)[0]))]:
    best = par(C2=270e-12,C3=2.7e-9)
    q=dict(best); q['C_pcb_pre']+=5e-12
    print(nm,'+5 pF en el nodo ÷10: %.2f %% -> %.2f %%' % ((fn(best)-1)*100,(fn(q)-1)*100))
