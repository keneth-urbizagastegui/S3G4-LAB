"""Compara s12d_smoke.csv de Claude (copia) con el de Codex: max diff relativa por columna numerica."""
import csv,sys
a={r['id']:r for r in csv.DictReader(open(sys.argv[1],encoding='utf-8-sig'))}
b={r['id']:r for r in csv.DictReader(open(sys.argv[2],encoding='utf-8-sig'))}
print('ids iguales:',set(a)==set(b),len(a))
worst=[]
for i in a:
  for k,v in a[i].items():
    w=b[i].get(k,'')
    try: x,y=float(v),float(w)
    except: continue
    if k.startswith('elapsed') or 'time' in k: continue
    d=abs(x-y)/max(abs(y),1e-30) if (x or y) else 0
    worst.append((d,i,k,x,y))
worst.sort(reverse=True)
for t in worst[:8]: print('%.2e %s %s %g %g'%t)
