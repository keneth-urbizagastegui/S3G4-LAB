"""Compara s13_smoke.csv reejecutado (copia en C:/s13) con el de Codex. Uso: comparar_smoke.py nuevo.csv codex.csv"""
import csv,sys,math
a=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig')));b=list(csv.DictReader(open(sys.argv[2],encoding='utf-8-sig')))
A={r['id']:r for r in a};B={r['id']:r for r in b}
skip={'elapsed_s','reused','signature','sig'}
worst=0;n=0;bad=[]
for k in A:
  if k not in B:print('falta',k);continue
  for c,v in A[k].items():
    if c in skip or 'elapsed' in c: continue
    w=B[k].get(c,'')
    try:x=float(v);y=float(w)
    except: 
      if v!=w and c not in skip: bad.append((k,c,v,w))
      continue
    n+=1;d=abs(x-y)/max(abs(y),1e-15)
    if d>worst:worst=d;wc=(k,c,x,y)
print('ids',len(A),len(B),'valores numericos',n,'peor dif rel',worst,wc if worst else '')
print('difs no numericas',bad[:10])
