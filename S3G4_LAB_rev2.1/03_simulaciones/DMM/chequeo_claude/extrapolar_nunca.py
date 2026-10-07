"""Extrapolacion propia a 10 s del caso P3 'nunca' (rele cerrado): ultimos 5 ciclos a 60 Hz."""
import sys, numpy as np
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auditar_raw import read_raw, integ
d = read_raw(sys.argv[1]); t = d['time']; V=lambda n:d[f'V({n})']; I=lambda n:d[f'I({n})']
P = {'tvs': V('n1')*I('Btvs'), 'ptc': (V('pt')-V('n1'))*I('Vptc'), 'rs': (V('n1')-V('n2'))*I('Rs')}
m = t >= t[-1]-5/60
for k,p in P.items():
    es = integ(t,p); pw = integ(t,p,m)/(5/60)
    # estabilidad: potencia media de cada uno de los 5 ciclos
    cyc=[integ(t,p,(t>=t[-1]-(j+1)/60)&(t<t[-1]-j/60))*60 for j in range(5)]
    print(f'{k}: E simulada 0-1 s {es:.4f} J; P media ult. 5 ciclos {pw:.4e} W (dispersion {np.ptp(cyc)/max(abs(np.mean(cyc)),1e-30)*100:.2f} %); extrapolado 1-10 s {pw*9:.4f} J; total {es+pw*9:.4f} J')
r = (V('pt')-V('n1'))/np.where(np.abs(I('Vptc'))>1e-12, I('Vptc'), np.nan)
print(f'R_PTC media ult. ciclo (|I|>0.1 mA) {np.nanmedian(np.abs(r[m & (np.abs(I("Vptc"))>1e-4)])):.3e} ohm; theta final {V("theta")[-1]:.3f}; I_PTC rms ult. 5 ciclos {np.sqrt(integ(t,I("Vptc")**2,m)/(5/60))*1e3:.2f} mA')
print(f'rp/rn final {V("rp")[-1]:.3f}/{V("rn")[-1]:.3f} V; rp max ult 5 ciclos {V("rp")[m].max():.3f}')
