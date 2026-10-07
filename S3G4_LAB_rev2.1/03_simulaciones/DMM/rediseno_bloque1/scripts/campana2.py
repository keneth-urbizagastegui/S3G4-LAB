import json, numpy as np
from gen import build
from rdlib import *
from run1 import one
rows = []
def logrow(r):
    rows.append(r); print({k: (round(float(v), 4) if isinstance(v, (float, np.floating)) else v) for k, v in r.items()}, flush=True)
# a) O2b: limitador + sujecion negativa a COM
for il in (1.5e-3, 2e-3, 3e-3, 5e-3):
    for ph in (0, 90):
        r = one(f'O2b_ilim{il*1e3:g}mA_ph{ph}', opt='O2', ilim=il, ron_lim=700., rs=47., ph=ph, clampcom=True, zener=True)
        r['E_lim_pk_check'] = r.get('P_lim_pk_W')
        logrow(r)
# b) O3 corregido: 2 PTC de 570 + 1k (2.14k)
for ph in (0, 90):
    logrow(one(f'O3a_2ptc570_1k_rs3300_ph{ph}', opt='O0', rptc=1140., rser=1000., rs=3300., ph=ph, zener=True))
json.dump(rows, open('campana2.json', 'w'), indent=1)

# c) termico, 1 s, disparo en E_trip
def thermal(name, etrip, **kw):
    opt = kw.pop('opt'); kw.update(etrip=etrip, tstop=1.0, dtmax=50e-6)
    cir = f'th_{name}.cir'; open(cir, 'w').write(build(opt, title=name, **kw))
    raw, log = run(cir); d = read_raw(raw); t = d['time']
    V = lambda n: d[f'v({n})']; I = lambda n: d[f'i({n})']
    th = V('theta'); trip = float(t[np.argmax(th >= .98)]) if (th >= .98).any() else None
    isr = I('vsr'); rptc = kw['rptc']; rs = kw['rs']; rser = kw.get('rser', 0.)
    ptv = V('n1') * I('btvs')
    iptc = I('bptc')
    pptc = (V('pt') - V('pt2')) * iptc
    out = dict(name=name, etrip_J=etrip, t_trip_s=trip, I_pk_A=float(np.abs(isr).max()),
               E_tvs_J=integ(t, ptv), E_ptc_J=integ(t, pptc), E_rser_J=integ(t, isr**2 * rser),
               E_rs_J=integ(t, I('rs')**2 * rs), P_tvs_pk_W=float(np.abs(ptv).max()),
               span_max_V=float((V('rp') - V('rn')).max()), rp_max_V=float(V('rp').max()), rn_min_V=float(V('rn').min()))
    if trip:
        m = t > trip + .05
        out['I_post_pk_A'] = float(np.abs(isr[m]).max()); out['I_post_rms_A'] = float(np.sqrt(np.mean(isr[m]**2)))
        out['P_tvs_post_avg_W'] = float(np.mean(ptv[m]))
        # corriente en el instante de disparo (ultimos 8 ms antes)
        mm = (t > trip - 0.0084) & (t <= trip)
        out['I_pre_trip_pk_A'] = float(np.abs(isr[mm]).max())
        # energia hasta el disparo
        k = t <= trip
        out['E_tvs_to_trip_J'] = integ(t[k], ptv[k]); out['E_rser_to_trip_J'] = integ(t[k], (isr**2 * rser)[k])
    return out
th_rows = []
for et in (20., 100.):
    th_rows.append(thermal(f'O1_ptc200_et{int(et)}', et, opt='O1', rptc=200., rs=330.))
    th_rows.append(thermal(f'O3a_2ptc570_et{int(et)}', et, opt='O0', rptc=1140., rser=1000., rs=3300., zener=True))
    th_rows.append(thermal(f'O3b_1ptc570_1k6_et{int(et)}', et, opt='O0', rptc=570., rser=1630., rs=3300., zener=True))
for r in th_rows: logrow(r)
json.dump(rows, open('campana2.json', 'w'), indent=1)
