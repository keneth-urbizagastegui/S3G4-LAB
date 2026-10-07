import json, numpy as np
from gen import build
from rdlib import *
def headroom(name, **kw):
    opt = kw.pop('opt'); isrc = kw['isrc']
    kw.update(grid='dc', vdc=0, analysis='dc')
    cir = f'dc2_{name}.cir'; open(cir, 'w').write(build(opt, title=name, **kw))
    raw, log = run(cir); d = read_raw(raw)
    v = d['v(vin)']; i = d['i(vgrid)']
    f = lambda x: float(np.interp(x, v, i))
    ok = np.where(i >= .99 * isrc)[0]
    return dict(V99=float(v[ok].max()) if len(ok) else 0., I_at_0p65=f(.65), I_at_2p0=f(2.0), I_at_3p0=f(3.0), I_at_3p5=f(3.5))
cases = [
 ('ref_PTC50_rs100', dict(opt='O0', rptc=50., rs=100.)),
 ('O1_ptc200_rs330', dict(opt='O1', rptc=200., rs=330.)),
 ('O2_ron700_rs47', dict(opt='O2', ilim=2e-3, ron_lim=700., rs=47.)),
 ('O2_ron450_rs47', dict(opt='O2', ilim=2e-3, ron_lim=450., rs=47.)),
 ('O2_ron1000_rs47', dict(opt='O2', ilim=2e-3, ron_lim=1000., rs=47.)),
 ('O3a_2ptc570_1k_rs3300', dict(opt='O0', rptc=1140., rser=1000., rs=3300.)),
 ('O4_R2200_rs3300', dict(opt='O0', rptc=1e-3, rser=2200., rs=3300.)),
]
res = []
for n, kw in cases:
    r = {'name': n}
    for tag, isrc in (('1mA', 1e-3), ('100uA', 1e-4)):
        q = headroom(n + '_' + tag, isrc=isrc, **dict(kw))
        r[tag] = q
    res.append(r); print(n, {k: {a: round(b, 4) for a, b in v.items()} for k, v in r.items() if k != 'name'}, flush=True)
json.dump(res, open('dc_diodo2.json', 'w'), indent=1)
