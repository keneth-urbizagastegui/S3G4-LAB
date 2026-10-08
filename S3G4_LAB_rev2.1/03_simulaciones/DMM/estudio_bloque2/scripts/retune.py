import numpy as np
from scipy.optimize import least_squares
from red import *
def hf_err(p):
    f = np.array([100e3])
    e1 = err_pct(h_div(f,p,1), h_div(np.array([1e-3]),p,1)[0])[0]
    e2 = err_pct(h_div(f,p,2), h_div(np.array([1e-3]),p,2)[0])[0]
    return e1, e2
p = par()
print('H tal cual (100k):', hf_err(p))
# retoque de C2 y C3 (Ct fijo)
def fun(x):
    q = par(C2=x[0]*1e-12, C3=x[1]*1e-9); return hf_err(q)
r = least_squares(fun, [270, 2.7])
print('optimo C2=%.1f pF  C3=%.3f nF -> errores' % (r.x[0], r.x[1]), fun(r.x))
# valores E12/E24
for c2,c3 in [(270,2.7),(270,3.0),(240,2.7),(300,2.7),(270,3.3),(330,3.0),(220,2.7),(240,3.0)]:
    print(c2,c3, np.round(fun([c2,c3]),2))
# retoque con Ct tambien (3 x Ct)
def fun3(x):
    q = par(C2=x[0]*1e-12, C3=x[1]*1e-9, Ct=x[2]*1e-12); return hf_err(q)
r3 = least_squares(fun3, [270, 2.7, 100]); print('opt con Ct', r3.x, fun3(r3.x))
# con mux de poca capacidad (C_z=3 pF TMUX4051 Con) 
for nm,kw in [('TMUX4051 Cz=3p',dict(C_z=3e-12,C_ypin=3e-12)),('sin BAV199',dict(C_bav=0))]:
    q = par(**kw); print(nm, 'H tal cual:', np.round(hf_err(q),2))
    r = least_squares(lambda x: hf_err(par(C2=x[0]*1e-12, C3=x[1]*1e-9, **kw)), [300, 3.0]); print('  opt', np.round(r.x,3))
