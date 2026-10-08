"""Auditoría Claude S11.4: duración y energía del pulso ESD en Rprot y Rohm, desde el .raw.

Uso: python pulso_esd.py <carpeta con T2_*.raw>  (sólo lectura)
"""
import re, sys
from pathlib import Path
import numpy as np

def raw(path):
    with path.open('rb') as f: h = f.read(50000)
    enc = 'utf-16-le' if b'\x00' in h[:80] else 'utf-8'
    mark = 'Binary:\n'.encode(enc); off = h.find(mark)
    hdr = h[:off].decode(enc)
    nv = int(re.search(r'No. Variables:\s*(\d+)', hdr)[1]); npnt = int(re.search(r'No. Points:\s*(\d+)', hdr)[1])
    names = [m[1].lower() for m in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+', hdr, re.M)]
    off += len(mark); cnt = min(npnt, (path.stat().st_size - off) // (8 * nv))
    a = np.memmap(path, dtype='<f8', mode='r', offset=off, shape=(cnt, nv))
    return {n: np.array(a[:, i]) for i, n in enumerate(names)}

def width(t, y, thr):
    m = np.abs(y) > thr
    if not m.any(): return 0.0
    dt = np.diff(t); return float(np.sum(dt[m[:-1] | m[1:]]))

d = Path(sys.argv[1])
for p in sorted(d.glob('T2_*.raw')):
    if p.name.endswith('.op.raw'): continue
    x = raw(p); t = np.abs(x['time']); v = lambda n: x.get('v(' + n + ')', np.zeros_like(t))
    out = {'vin_pk': np.max(np.abs(v('vin')))}
    pairs = {'Rprot1': ('vin', 'p1', 33e3), 'Rohm1': ('ptin', 'ohmid', 1.1e3)}
    for k, (a, b, R) in pairs.items():
        u = v(a) - v(b); pk = np.max(np.abs(u)); E = np.trapezoid(u * u / R, t)
        i0 = np.argmax(np.abs(u))
        out[k] = dict(pk=round(pk, 1), t_pk_ns=round(t[i0] * 1e9, 2),
                      w_gt100V_ns=round(width(t, u, 100) * 1e9, 2), w_gt160V_ns=round(width(t, u, 160) * 1e9, 2),
                      w_gt200V_ns=round(width(t, u, 200) * 1e9, 2), w_half_ns=round(width(t, u, pk / 2) * 1e9, 2),
                      E_nJ=round(E * 1e9, 3), Ppk_W=round(pk * pk / R, 1))
    rel = v('vin') - v('ptin'); out['rele_pk_V'] = round(float(np.max(np.abs(rel))), 1)
    out['vin_w_gt1kV_ns'] = round(width(t, v('vin'), 1000) * 1e9, 1)
    for r in ('rx0', 'rx1'):
        i = x.get('i(' + r + ')')
        if i is not None: out[r + '_pk_mA'] = round(float(np.max(np.abs(i))) * 1e3, 3)
    g = x.get('v(gstate)')
    if g is not None:
        on = np.where(g > 0.5)[0]; out['gdt_on_ns'] = round(t[on[0]] * 1e9, 2) if len(on) else None
    print(p.name[:90]); print('  ', out)
