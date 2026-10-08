import numpy as np
from red import *
def e20(p, f=20e3):
    h = h_x0(np.array([f, 1e-3]), p); return (abs(h[0])/abs(h[1])-1)*100
def sens(p, dC=1e-12):
    q = dict(p); q['C_pcb_pre'] += dC
    return e20(q)-e20(p)
print('Capacidades: pre = BAV199 4 + Yn 5 + pcb 3 ;  com = Z 25 + pcb 3 + OPA2188 9.5')
opts = {
 'A  H: 74HC4051 + OPA2188': par(),
 'B  TMUX4051 (Con=3 pF de LCSC) + OPA2188 [supuesto: Z=3, Yn=3]': par(C_z=3e-12, C_ypin=3e-12),
 'B2 TMUX4051 con Con=11 pF (variante DYY) [supuesto Z=11]': par(C_z=11e-12, C_ypin=3e-12),
 'C  buffer antes del mux (OPA192, Cin 5 pF [supuesto]) sin BAV199 aparte': par(C_bav=4e-12, C_ypin=5e-12, C_z=0, C_pcb_com=0, C_amp=0, C_pcb_pre=3e-12),
}
for n, p in opts.items():
    if n.startswith('C '):
        # el buffer carga R_PROT con su entrada (5 pF) + BAV199 4 + pcb 3 ; el resto queda tras el buffer (baja impedancia)
        C = 4e-12+3e-12+5e-12
        fp = 1/(2*np.pi*(99e3+100)*C); g = 1/np.sqrt(1+(20e3/fp)**2)
        print(f'{n}: C={C*1e12:.1f} pF fp={fp/1e3:.0f} kHz  20 kHz: {(g-1)*100:.2f} %   sens {-(1-g)*0:.0f}')
        # sensibilidad por pF
        C2 = C+1e-12; fp2 = 1/(2*np.pi*(99e3+100)*C2); g2 = 1/np.sqrt(1+(20e3/fp2)**2); print('     sensibilidad %.3f %%/pF' % ((g2-g)*100))
        continue
    Cpre = p['C_bav']+p['C_ypin']+p['C_pcb_pre']; Ccom = p['C_z']+p['C_pcb_com']+p['C_amp']
    print(f'{n}: Ctot~{(Cpre+Ccom)*1e12:.1f} pF  20 kHz: {e20(p):.2f} %  10 kHz: {e20(p,10e3):.2f} %  1 pF extra en el nodo: {sens(p):+.3f} %')
