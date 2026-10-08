"""Auditoría Claude S12b, E8: pico de corriente de pinza (resistiva) en los 144 casos ESD/red guardados."""
import csv,sys,numpy as np
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent));from e8_descomponer import raw,dur
DMM=Path(__file__).resolve().parents[2]
rows=[r for r in csv.DictReader(open(DMM/'resultados/s12b_campaign.csv',encoding='utf-8-sig')) if r['q']=='E8' and r['kind']=='protection']
res=[]
for r in rows:
    p=DMM/'S12b'/(r['id']+'.raw')
    if not p.exists():print('falta',r['id']);continue
    d=raw(p);t=np.abs(d['time']);rp=d['v(rp)'];rn=d['v(rn)']
    for ch in (0,1):
        b=d[f'v(bi{ch})'];i=d[f'i(vib{ch})'];icl=np.clip(b-rp-.5,0,None)-np.clip(rn-b-.5,0,None)
        res.append((np.max(np.abs(icl)),np.max(np.abs(i)),dur(t,np.abs(i),5e-3),dur(t,np.abs(icl),2.5e-3),ch,abs(float(r['amp'])),r['id']))
res.sort()
tot=[x for x in res];print('casos-canal',len(tot))
print('peor pinza: %.3f mA (|I| %.3f mA), canal %d, %s'%(res[-1][0]*1e3,res[-1][1]*1e3,res[-1][4],res[-1][6]))
print('canal-casos con |I|>5 mA:',sum(x[1]>5e-3 for x in res),' con pinza>5 mA:',sum(x[0]>5e-3 for x in res))
print('max duración |I|>5 mA: %.2f ns; max duración pinza>2.5 mA: %.2f us'%(max(x[2] for x in res)*1e9,max(x[3] for x in res)*1e6))
for a in sorted(set(x[5] for x in res)):
    s=[x for x in res if x[5]==a];print(f'  amp {a:g}: pinza max {max(x[0] for x in s)*1e3:.3f} mA, |I| max {max(x[1] for x in s)*1e3:.3f} mA')
