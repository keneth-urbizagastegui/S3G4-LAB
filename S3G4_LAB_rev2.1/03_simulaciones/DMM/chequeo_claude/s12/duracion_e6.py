"""Duración y energía del pulso en una 1.5 MΩ en los .raw de E6 (cadena GDT+MOV)."""
import sys,os,glob,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
B=r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\S12'
for pat in sys.argv[1:]:
    f=[x for x in glob.glob(B+'/**/'+pat+'*.raw',recursive=True) if '.op.' not in x][0];r=leer(f);t=r['time']
    d=np.abs(r['V(vin)']-r['V(mid1)']);k=np.argmax(d);vin=np.abs(r['V(vin)'])
    print(os.path.basename(f)[:60]);print(f'  pico {d[k]:.1f} V en {t[k]*1e9:.1f} ns; Vin pico {vin.max():.0f} V')
    for lev in (200,300,400):
        s=d>lev;print(f'  >{lev} V durante {np.sum(np.diff(t)[s[:-1]])*1e9:.1f} ns' )
    p=d**2/1.5e6;print(f'  energía en la 1.5 MΩ {np.trapezoid(p,t)*1e9:.3f} nJ; P pico {p.max()*1e3:.2f} mW')
