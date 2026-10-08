"""Auditoría Claude S11.4: compara el smoke reejecutado con el de Codex (columna a columna).
Uso: python comparar_smoke.py <smoke_codex.csv> <smoke_claude.csv>
"""
import csv, sys, math
def load(p):
    with open(p, encoding='utf-8-sig', newline='') as f: return list(csv.DictReader(f))
a, b = load(sys.argv[1]), load(sys.argv[2])
key = lambda r: r.get('name') or r.get('case') or r.get('id')
ia = {key(r): r for r in a}; ib = {key(r): r for r in b}
print('casos codex', len(a), 'claude', len(b), 'comunes', len(set(ia) & set(ib)))
skip = ('elapsed', 'time_s', 'wall', 'path', 'signature', 'started', 'finished')
worst = []
for k in sorted(set(ia) & set(ib)):
    for c in ia[k]:
        if any(s in c.lower() for s in skip): continue
        x, y = ia[k].get(c), ib[k].get(c)
        try: fx, fy = float(x), float(y)
        except (TypeError, ValueError):
            if x != y: worst.append((float('inf'), k[:40], c, x, y))
            continue
        if math.isnan(fx) and math.isnan(fy): continue
        rel = abs(fx - fy) / max(abs(fx), abs(fy), 1e-30)
        if rel > 1e-9: worst.append((rel, k[:40], c, fx, fy))
worst.sort(key=lambda w: -w[0])
print('columnas que difieren (>1e-9 relativo):', len(worst))
for w in worst[:15]: print(w)
