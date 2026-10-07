"""Borne A: fusible 5x20 de 3.15 A + derivador 0.1 ohm en paralelo con un puente (+ y - unidos).
Corriente de la red (230 Vrms, 60 Hz) de impedancia Rnet; el fusible se supone un corto de 0.04 ohm hasta
fundir (I2t_melt) y la corriente se sigue hasta k*I2t_melt (arco). Claude, 7 oct 2026."""
import numpy as np, json
VT = 0.02585
W = 2*np.pi*60
VPK = 325.269
def bridge_table(Vf, If, Rs, n=2.0):
    vj = Vf - If*Rs
    IS = If/np.expm1(vj/(n*VT))
    ib = np.logspace(-9, 3.5, 4000)
    vd = n*VT*np.log1p(ib/IS) + ib*Rs
    return ib, 2*vd, IS           # dos diodos en serie por sentido (puente con + y - unidos)
BRIDGES = {   # Vf (V) a If (A) por pata; Rs supuesta 15 mohm/pata (20 mohm en el DF08S, ajuste de Codex)
 'DF08S (actual)':  dict(Vf=1.1, If=1.0, Rs=.02, I2t=10.4, ifsm=50., cost=.10),
 'GBU808':          dict(Vf=1.1, If=8.0, Rs=.015, I2t=175.**2*.0083/2, ifsm=175., cost=.20),
 'GBU1510':         dict(Vf=1.1, If=7.5, Rs=.012, I2t=220.**2*.0083/2, ifsm=220., cost=.23),
 'GBU2510':         dict(Vf=1.1, If=12.5, Rs=.008, I2t=300.**2*.0083/2, ifsm=300., cost=.36),
 'sin puente':      None,
}
def itotal(vs, Rtot, Rsh, tab):
    """corriente total y reparto para una tension de fuente vs (array) con resistencia serie Rtot"""
    sgn = np.sign(vs); a = np.abs(vs)
    lo = np.zeros_like(a); hi = a.copy()
    if tab is None:
        itot = a/(Rtot+Rsh); vb = itot*Rsh; ib = np.zeros_like(a)
    else:
        ibt, vbt, _ = tab
        for _ in range(60):
            mid = (lo+hi)/2
            ib = np.interp(mid, vbt, ibt, right=ibt[-1])
            itot = mid/Rsh + ib
            f = mid + Rtot*itot - a
            hi = np.where(f > 0, mid, hi); lo = np.where(f > 0, lo, mid)
        vb = (lo+hi)/2; ib = np.interp(vb, vbt, ibt, right=ibt[-1]); itot = vb/Rsh + ib
    return sgn*itot, sgn*ib, sgn*vb/Rsh, sgn*vb

def analyse(Rnet, i2t_melt, bridge, phase_deg, k=(1, 2, 3), Rf=.04, Rsh=.1, dt=2e-6, T=12e-3):
    t = np.arange(0, T, dt)
    vs = VPK*np.sin(W*t + np.radians(phase_deg))
    tab = None
    if BRIDGES[bridge] is not None:
        b = BRIDGES[bridge]; tab = bridge_table(b['Vf'], b['If'], b['Rs'])
    it, ib, ish, vb = itotal(vs, Rnet+Rf, Rsh, tab)
    cum = np.cumsum(it**2)*dt
    out = {}
    for kk in k:
        idx = np.searchsorted(cum, kk*i2t_melt)
        if idx >= len(t): idx = len(t)-1
        sl = slice(0, idx+1)
        out[kk] = dict(t_ms=t[idx]*1e3, I_tot_pk=float(np.abs(it[sl]).max()), I_br_pk=float(np.abs(ib[sl]).max()),
                       I2t_br=float(np.sum(ib[sl]**2)*dt), I_sh_pk=float(np.abs(ish[sl]).max()),
                       E_sh_J=float(np.sum(ish[sl]**2)*dt*Rsh), V_pk=float(np.abs(vb[sl]).max()))
    return out

FUSES = {'HOLLY 50CF-032H (C356446) 4.27': 4.271, 'Littelfuse 0216 3.15 (C95689) 6.7': 6.7,
         'SETsafe SCF520F (C50386930) 8.5': 8.5, 'Eaton BK/S501 (C3156611) 8.1': 8.1,
         'temporizado Littelfuse 0215 43.3 (C142723)': 43.255}
if __name__ == '__main__':
    import csv
    rows = []
    for fn, i2 in FUSES.items():
        for br in BRIDGES:
            for Rn in (.5, 1., 2.):
                env = None
                for ph in range(0, 180, 10):                  # envolvente sobre la fase de cierre
                    o = analyse(Rn, i2, br, ph)
                    cur = dict(I_tot_pk=o[2]['I_tot_pk'], I_pk_puente=o[2]['I_br_pk'], I_sh_pk=o[2]['I_sh_pk'], V_sh_pk=o[2]['V_pk'], t_k2_ms=o[2]['t_ms'],
                               **{f'I2t_puente_k{k}': o[k]['I2t_br'] for k in (1, 2, 3)}, **{f'E_sh_k{k}_J': o[k]['E_sh_J'] for k in (1, 2, 3)})
                    if env is None: env = dict(cur)
                    else:
                        for kk, vv in cur.items():
                            env[kk] = min(env[kk], vv) if kk == 't_k2_ms' else max(env[kk], vv)
                b = BRIDGES[br]
                rows.append(dict(fusible=fn, i2t_fus=i2, puente=br, Rnet=Rn, I2t_lim_puente=(b['I2t'] if b else None), ifsm=(b['ifsm'] if b else None), **env))
    json.dump(rows, open('borneA.json', 'w'), indent=1)
    with open('borneA.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    for r in rows:
        print(r['fusible'][:12], r['puente'][:8], r['Rnet'], 'Ipk %d Ibr %d' % (r['I_tot_pk'], r['I_pk_puente']),
              'I2t_br k1/2/3 %.1f/%.1f/%.1f' % (r['I2t_puente_k1'], r['I2t_puente_k2'], r['I2t_puente_k3']),
              'Esh %.2f/%.2f/%.2f Vsh %.0f t2min %.2fms' % (r['E_sh_k1_J'], r['E_sh_k2_J'], r['E_sh_k3_J'], r['V_sh_pk'], r['t_k2_ms']))
