"""Compara el smoke reejecutado (C:/s113) con el de Codex: max diferencia relativa por columna numérica."""
import csv,sys,math
A=r"C:\s113\a\b\DMM\resultados\s11_3_smoke.csv"
B=r"C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\resultados\s11_3_smoke.csv"
def load(p):return {r['id']:r for r in csv.DictReader(open(p,encoding='utf-8-sig'))}
a,b=load(A),load(B)
print('ids comunes',len(set(a)&set(b)),'solo nuevo',len(set(a)-set(b)),'solo codex',len(set(b)-set(a)))
worst=[]
for i in set(a)&set(b):
    for k,v in a[i].items():
        if k in('elapsed_s','id') or 'time' in k: continue
        try:x=float(v);y=float(b[i].get(k,''))
        except:continue
        if not(math.isfinite(x) and math.isfinite(y)):continue
        d=abs(x-y)/max(abs(x),abs(y),1e-9)
        worst.append((d,i[:40],k,x,y))
worst.sort(reverse=True);n=len(worst)
print('valores comparados',n,'con dif rel>1e-6:',sum(w[0]>1e-6 for w in worst))
for w in worst[:6]:print(w)
