import numpy as np, json
from mc2 import *
out = {}
H = par(); R = par(C2=270e-12, C3=2.7e-9)
N = 800
for nm, base in (('H 330p/3.0n', H), ('retoque 270p/2.7n', R)):
    for kind in ('x1', 'x2'):
        for cal, libre in [((1e3, 20e3), 'ambos'), ((1e3, 20e3), 'polo'), ((100, 1e3, 20e3), 'ambos'), ((100, 1e3, 20e3), 'polo')]:
            d = correr(kind, base, N, .05, .05, 0.30, cal=cal, libre=libre, seed=7)
            out[f'{nm}|{kind}|{cal}|{libre}'] = d
            print(f'{nm:20s} {kind} cal={str(cal):18s} cero {libre:5s} p50={d["p50"]:.2f} p95={d["p95"]:.2f} p99={d["p99"]:.2f} max={d["max"]:.2f}  (desvío sin corregir a 20 kHz: {d["droop_lo"]:.1f} .. {d["droop_hi"]:.1f} %)')
# X0
d = correr('x0', H, N, .05, .05, 0.30, seed=7); out['x0 H'] = d; print('X0 H (74HC4051+OPA2188)', d)
json.dump(out, open('mc3_result.json', 'w'), indent=1)
