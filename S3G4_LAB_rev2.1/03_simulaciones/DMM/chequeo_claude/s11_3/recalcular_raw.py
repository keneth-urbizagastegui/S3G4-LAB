"""Auditoría S11.3 (Claude). Genera decks con el generador de Codex (copia en C:/s113),
aplica variantes opcionales, ejecuta LTspice y recalcula con un lector raw propio.
Uso: python recalcular_raw.py  (escribe resultados en C:/s113/claude/)"""
import sys, re, math, subprocess, json, os
from pathlib import Path
import numpy as np
COPY = Path(r"C:/s113/a/b/DMM"); sys.path.insert(0, str(COPY))
os.environ.setdefault('S3G4_MODELS', r"C:/Users/Keneth/Desktop/S3G4 LAB/Simulation_LTSpice/models")
import ejecutar_s11_3 as e
LT = r"C:/Users/Keneth/AppData/Local/Programs/ADI/LTspice/LTspice.exe"
OUT = Path(r"C:/s113/claude"); OUT.mkdir(exist_ok=True)

def readraw(p):
    b = p.read_bytes(); enc = 'utf-16-le' if b[1:2] == b'\x00' else 'latin-1'
    mark = 'Binary:\n'.encode(enc); off = b.find(mark); hdr = b[:off].decode(enc)
    nv = int(re.search(r'No. Variables:\s*(\d+)', hdr)[1]); npnt = int(re.search(r'No. Points:\s*(\d+)', hdr)[1])
    names = [m.lower() for m in re.findall(r'^\s*\d+\s+(\S+)\s+\S+', hdr.split('Variables:')[-1], re.M)]
    dbl = 'double' in re.search(r'Flags:(.*)', hdr)[1]
    off += len(mark); data = b[off:]
    if dbl:
        a = np.frombuffer(data[:npnt*8*nv], '<f8').reshape(npnt, nv); cols = {n: a[:, i] for i, n in enumerate(names)}
    else:
        rec = np.dtype([('t', '<f8')] + [(f'c{i}', '<f4') for i in range(1, nv)])
        a = np.frombuffer(data[:npnt*rec.itemsize], rec); cols = {names[0]: a['t']}
        cols.update({n: a[f'c{i}'].astype(float) for i, n in enumerate(names) if i})
    cols['time'] = np.abs(cols['time']); return cols

def find(**kw):
    for c in e.cases():
        if all((abs(c[k]-v) < 1e-12*max(1, abs(v))) if isinstance(v, (int, float)) else c[k] == v for k, v in kw.items()): return c
    raise KeyError(kw)

def sim(tag, c, repl=()):
    txt = e.deck(c)
    for a, b in repl:
        assert a in txt, a; txt = txt.replace(a, b)
    p = OUT/(tag+'.cir'); p.write_text(txt, encoding='utf-8')
    subprocess.run([LT, '-b', str(p)], timeout=600, check=False)
    return readraw(p.with_suffix('.raw'))

def V(d, a, b='0'):
    g = lambda x: d['v('+x+')'] if x != '0' else 0*d['time']
    return g(a)-g(b)

def above(t, y, thr):
    m = np.abs(y) > thr; return float(np.sum(np.diff(t)[m[:-1]]))

res = {}
# 1) R3: peor Rohm (60 Vrms, apagado, body, rail 1.02, fuente apagada)
c = find(q='R3', power=0, body=1, rail=1.02, source=0, stimulus='mains', phase=0)
d = sim('R3_peor', c); t = d['time']; m = t >= t[-1]-5/60
p1 = V(d, 'ptin', 'ohmid')*d['i(rohm1)']; pr = V(d, 'vin', 'p1')*d['i(rprot1)']
res['R3'] = dict(rohm1_W=float(np.trapezoid(p1[m], t[m])/(t[m][-1]-t[m][0])), rprot1_W=float(np.trapezoid(pr[m], t[m])/(t[m][-1]-t[m][0])),
                 n1_peak=float(np.max(np.abs(d['v(n1)']))), tvs_W=float(np.trapezoid((d['v(n1)']*d['i(btvs)'])[m], t[m])/(t[m][-1]-t[m][0])))
# 2) R6: aire +8 kV modo tensión, RX0/RX2=100 (peor Cc1) y contacto -4 kV
for tag, amp in (('R6_aire', 8000), ('R6_contacto', -4000)):
    c = find(q='R6', amplitude=amp, mode='v', rail=.98, power=0, body=1, rx0=100)
    d = sim(tag, c); t = d['time']; vc = {k: V(d, a, b) for k, a, b in (('cc1', 'c1', 'd1'), ('cc2', 'c2', 'd2'), ('cc3', 'c3', 'x1'))}
    r = {k+'_pk_V': float(np.max(np.abs(y))) for k, y in vc.items()}
    r.update(cc1_t_sobre_504V_ns=above(t, vc['cc1'], 504)*1e9, cc1_t_sobre_630V_ns=above(t, vc['cc1'], 630)*1e9,
             vin_pk_V=float(np.max(np.abs(d['v(vin)']))), ix0_pk_mA=1e3*float(np.max(np.abs(d['i(rx0)']))),
             ix1_pk_mA=1e3*float(np.max(np.abs(d['i(rx1)']))), ix1_t_sobre_10mA_ns=above(t, d['i(rx1)'], 10e-3)*1e9,
             rprot1_pk_V=float(np.max(np.abs(V(d, 'vin', 'p1')))), rdiv1_pk_V=float(np.max(np.abs(V(d, 'vin', 'd1')))))
    res[tag] = r
# 3) R6 aire con RX1 = 150 y 220 ohm (comprobación de cambio mínimo)
c = find(q='R6', amplitude=8000, mode='v', rail=.98, power=0, body=1, rx0=100)
for rx1 in (150, 220):
    d = sim(f'R6_aire_rx1_{rx1}', c, repl=(('Rx1 x1 hx1 100', f'Rx1 x1 hx1 {rx1}'),))
    res[f'R6_aire_RX1_{rx1}'] = dict(ix1_pk_mA=1e3*float(np.max(np.abs(d['i(rx1)']))), ix0_pk_mA=1e3*float(np.max(np.abs(d['i(rx0)']))))
# 4) R1 diodo a 100 uA: barrido; cadena de caídas a V(vin)=3.5 V
c = find(q='R1', mode='diode', source=.0001, rail=1)
d = sim('R1_diodo_100u', c); vin = d['v(vin)']; o = np.argsort(vin)
def at(x): return float(np.interp(3.5, vin[o], x[o]))
iD = d['i(vdut)']; isrc = d['i(vsense)']; m = (t := d['time']) > .002
comp = float(np.max(vin[m][isrc[m] >= .99e-4])) if np.any(isrc[m] >= .99e-4) else None
res['R1_100u'] = dict(compliance_fuente_V=comp, rp=at(d['v(rp)']), msource=at(d['v(msource)']), bp=at(d['v(bp)']), n2=at(d['v(n2)']), n1=at(d['v(n1)']),
                      ptin=at(d['v(ptin)']), i_src_uA=1e6*at(isrc), i_dut_uA=1e6*at(iD), i_tvs_uA=1e6*at(d['i(btvs)']))
(OUT/'claude_s11_3.json').write_text(json.dumps(res, indent=1)); print(json.dumps(res, indent=1))
