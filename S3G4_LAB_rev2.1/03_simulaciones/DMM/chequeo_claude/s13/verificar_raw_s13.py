"""Auditoria Claude S13: recalcula desde .raw un caso C2, uno C3 y uno C1.
Uso: python -B verificar_raw_s13.py <carpeta DMM>  (solo lectura)."""
import sys,csv,numpy as np
from pathlib import Path
D=Path(sys.argv[1]);sys.path.insert(0,str(D/'estudio_bloque3/scripts'));import rawlt
J=D/'S13';SET=2.5*4990/24900;I0=SET/499
camp={r['id']:r for r in csv.DictReader(open(D/'resultados/s13_campaign.csv',encoding='utf-8-sig'))}
def rd(n):
    _,d=rawlt.read(str(J/(n+'.raw')));return {k.lower():np.real(v) for k,v in d.items()}
# C2: placas que fallan + una buena
print('== C2 compliancia (2 kohm, 1 mA) ==')
for n in ['s13_C2_compliance_0040','s13_C2_compliance_0044','s13_C2_compliance_0083','s13_C2_compliance_0000']:
    d=rd(n);vb=d['v(bor)'];ii=d['i(vdut)']+vb/10.01e6;i0=ii[0]
    vx=I0*2000*10.01e6/(2000+10.01e6)
    cn=vb[ii>=.99*I0].max() if (ii>=.99*I0).any() else 0.   # nominal (criterio campaña)
    cc=vb[ii>=.99*i0].max()                                   # calibrado (corriente propia)
    ron=(d['v(s)'][-1]-d['v(f)'][-1])/d['i(rk)'][-1]
    # caida extra en el mux de fuerza por encima del Ron nominal de la placa
    rnom=float(camp[n]['ron']);extra=I0*(abs(ron)-rnom)
    print(f"{n}: I0={i0*1e3:.4f} mA err={((i0/I0)-1)*100:+.3f}% comp_nom={cn:.2f} comp_cal={cc:.2f} Vx_cal={i0*2000:.4f} "
          f"margen_cal={cc-i0*2000:.3f} V | campaña margin_V={float(camp[n]['margin_V']):.3f} | Ron_mux={abs(ron):.1f} ohm (nominal {rnom:.1f}) caida extra={extra*1e3:.0f} mV")
# C3
print('== C3 continuidad ==')
n='s13_C3_continuity_0431';d=rd(n);t=np.abs(d['time']);pb=d['v(pb14)'];cm=d['v(comp)']
for lab,ts,cond in [('cierre',20e-6,pb<.2525-.0045),('apertura',170e-6,pb>.2525+.0045)]:
    ix=np.flatnonzero((t>=ts)&cond);print(lab,f"{(t[ix[0]]-ts)*1e6:.3f} us" if len(ix) else None)
m=(t>20e-6)&(t<320e-6);rail=float(camp[n]['rail'])
print('transiciones COMP',int(np.count_nonzero(np.diff(cm[m]>.5*rail))),'t_final',t[-1],'V(bor) final',d['v(bor)'][-1],
      '| campaña close',camp[n]['close_s'],'open',camp[n]['open_s'],'trans',camp[n]['transitions'])
# PB14 en cortocircuito y abierto
print('PB14 cerrado(150us)',np.interp(150e-6,t,pb),'abierto(300us)',np.interp(300e-6,t,pb))
# C1
print('== C1 60 V (peor R1) ==')
n='s13_C1_fault60_0376';d=rd(n);t=np.abs(d['time']);vin=d['v(vin)']
print('vin max/min',vin.max(),vin.min(),'Vrms ult. 5 ciclos',end=' ')
w=t>=t[-1]-5/60;print(np.sqrt(np.trapezoid(vin[w]**2,t[w])/(t[w][-1]-t[w][0])))
for i,a,z in ((1,'ptin','ohmida'),(2,'ohmida','ohmidb'),(3,'ohmidb','n1')):
    vv=d['v('+a+')']-d['v('+z+')'];pw=vv*vv/510
    print(f"R1_{i}: Pavg total={np.trapezoid(pw,t)/(t[-1]-t[0]):.4f} W  Pavg ult5ciclos={np.trapezoid(pw[w],t[w])/(t[w][-1]-t[w][0]):.4f} W  Vpico={np.abs(vv).max():.2f} V | campaña {float(camp[n][f'r1_{i}_Pavg_W']):.4f}")
print('N1 max',d['v(n1)'].max(),'rail sep max',(d['v(rp)']-d['v(rn)']).max(),'BAT54 inv',(d['v(n1)']-d['v(bp)']).max(),'BSS84 Vds',np.abs(d['v(bp)']-d['v(msource)']).max())
