import json, numpy as np
from gen import build
from rdlib import *
res = []
for name, kw in (('O0', dict(opt='O0', rptc=200., rs=330.)), ('O1', dict(opt='O1', rptc=200., rs=330.)), ('O2b', dict(opt='O2', rs=47., clampcom=True)), ('O2', dict(opt='O2', rs=47.))):
    for vdut in (1.0, 2.0, 4.0):
        opt = kw['opt']; k2 = {a: b for a, b in kw.items() if a != 'opt'}
        k2.update(grid='dc', vdc=vdut, isrc=0.0, analysis='tran', tstop=1e-3, dtmax=1e-4)
        cir = f'lk_{name}_{vdut}.cir'; open(cir, 'w').write(build(opt, title=name, **k2))
        raw, log = run(cir); d = read_raw(raw)
        r = {'opt': name, 'Vn2_V': vdut}
        for dev in ('d2p', 'd2n', 'dcn', 'dblk', 'dmosbody'):
            if f'i({dev})' in d: r[dev] = float(d[f'i({dev})'][-1])
        r['I_total_vin'] = float(d['i(vgrid)'][-1])
        res.append(r); print(r)
json.dump(res, open('leak.json', 'w'), indent=1)
