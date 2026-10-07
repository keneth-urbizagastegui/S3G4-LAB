"""Compara el smoke reejecutado (C:\\s11a) con el de Codex, columna a columna numerica."""
import csv, sys, math
a = sys.argv[1]; b = sys.argv[2]
def load(p):
    with open(p, encoding='utf-8-sig') as f:
        return {r['id']: r for r in csv.DictReader(f)}
A, B = load(a), load(b)
print('casos', len(A), len(B), 'comunes', len(set(A) & set(B)))
worst = []
for k in sorted(set(A) & set(B)):
    for col, va in A[k].items():
        vb = B[k].get(col)
        try: x, y = float(va), float(vb)
        except (TypeError, ValueError): continue
        if col.endswith(('_s', 'elapsed')) and 'elapsed' in col: continue
        d = abs(x - y) / max(abs(x), abs(y), 1e-12)
        worst.append((d, k[:40], col, x, y))
worst.sort(reverse=True)
skip = [w for w in worst if 'elapsed' not in w[2] and 'wall' not in w[2]]
print('max diff relativa (sin tiempos de pared):')
for w in skip[:8]: print('  %.3g %s %s %.6g %.6g' % w)
print('columnas comparadas', len(skip), '; con diff > 1e-3:', sum(w[0] > 1e-3 for w in skip))
