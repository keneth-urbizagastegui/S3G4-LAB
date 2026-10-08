"""Compara el smoke de S12 reejecutado en C:/s12a con el CSV de Codex (solo lectura)."""
import csv,sys,math
A=r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\resultados\s12_smoke.csv'
B=r'C:\s12a\r\s\DMM\resultados\s12_smoke.csv'
SKIP={'elapsed_s','signature','reaudited'}
def load(p):return {r['id']:r for r in csv.DictReader(open(p,encoding='utf-8-sig'))}
a,b=load(A),load(B);worst=0
for k in a:
    for f,v in a[k].items():
        if f in SKIP or not v:continue
        w=b[k].get(f,'')
        try:x,y=float(v),float(w);d=abs(x-y)/max(abs(x),1e-30)
        except ValueError:d=0 if v==w else 1
        if d>1e-6:print(k[:40],f,v,w)
        worst=max(worst,d)
print('casos',len(a),len(b),'peor diferencia relativa',worst)
