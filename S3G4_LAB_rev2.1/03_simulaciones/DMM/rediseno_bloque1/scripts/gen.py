"""Generador de decks LTspice para el rediseno del bloque 1 del DMM (ruta de ohmios).
Claude, 7 oct 2026. Opciones: O0 (referencia), O1, O2, O3, O4 (ver REDISENO_BLOQUE1.md)."""
import math, textwrap

HEAD = """* {title}
.options numdgt=15 plotwinsize=0 gmin=1e-15
.model RELAY SW(Ron=.1 Roff=1e12 Vt=.5 Vh=0)
.model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)
.model BODY D(Is=1n N=1 Rs=.1)
.model REGSUP D(Ron=1u Roff=1e18 Vfwd=0)
.model ICHC D(Ron=1 Roff=1T Vfwd=.5)
.model ICTLV D(Ron=1 Roff=1T Vfwd=.2)
.model ZD D(Is=1e-14 Rs=1 BV=5.6 IBV=1m)
.subckt PINHC a rp rn
Dhi a rp ICHC
Dlo rn a ICHC
Cin a 0 5p
.ends
.subckt PINTLV a rp rn
Dhi a rp ICTLV
Dlo rn a ICTLV
Cin a 0 8p
.ends
"""
# TVS SMAJ12CA, hoja p.3: VBR 13.3-14.7 V a 1 mA, VC 19.9 V a 20.1 A. Rodilla central 14.0 V.
TVS_KNEE = 14.0
TVS_RD = (19.9 - 14.7) / (20.1 - .001)

def rails(zener=False):
    s = f"""Vregp regp 0 4.9
Vregn regn 0 -4.9
Rdp regp regpf .5
Rdn regnf regn .5
Dregp regpf rp REGSUP
Dregn rn regnf REGSUP
Rload rp rn {{9.8/.003}}
Crp rp 0 1u
Crn rn 0 1u
"""
    if zener:
        s += "Dzp 0 rp ZD\nDzn rn 0 ZD\n"
    return s

def source(isrc, vhead=.7):
    # fuente P43: BSS84 como elemento de paso, compliancia = rp - vhead (4.9-.7 = 4.2 V ... 4.1 V con el limit de .1 V)
    return f"""Vhead rp ms {vhead}
Vsense ms msource 0
Bsource msource n2s I={isrc}*limit(V(msource,n2s)/.1,0,1)
Xtl1 ms rp rn PINTLV
Xtl2 msource rp rn PINTLV
Dmosbody n2s msource BODY
Xh6 n2s rp rn PINHC
"""

def build(opt, title="", grid="ac", ph=0, topen=None, rptc=200., rs=330., isrc=1e-3,
          ilim=2.5e-3, ron_lim=700., rser=0., zener=False, vac=325.269, vdc=None,
          tstop=0.0834, dtmax=20e-6, analysis='tran', etrip=None, rhot=35e3, clampcom=False):
    """opt: O0|O1|O2|O3|O4. rptc: R del PTC en frio (ohm) o caliente. rser: resistencia fija en serie."""
    s = HEAD.format(title=title or opt)
    # red o fuente de CC
    if grid == "ac":
        s += f"Vgrid g 0 SIN(0 {vac} 60 0 0 {ph})\nRgrid g vin 1m\n"
    else:
        s += f"Vgrid g 0 {vdc}\nRgrid g vin 1m\n"
    # rele (cerrado o con apertura real en topen)
    if topen is None:
        s += "Vrc rc 0 1\n"
    else:
        s += f"Vrc rc 0 PULSE(1 0 {topen} 1u 1u 10 20)\n"
    s += "Srelay vin ptin rc 0 RELAY\nCoff vin ptin 1p\nVsr ptin pt 0\n"
    # elemento limitador del camino
    if opt == "O2":
        s += f"Blim pt n1 I={ilim}*tanh(V(pt,n1)/({ilim}*{ron_lim}))\n"
    else:
        if etrip:
            s += f"Bptc pt pt2 I=V(pt,pt2)/({rptc}+({rhot}-{rptc})*limit((V(theta)-0.98)/0.04,0,1))\nCth theta 0 {etrip} IC=0\nRth theta 0 1T\nBheat 0 theta I=V(pt,pt2)*I(Vsr)\n"
        else:
            s += f"Rptc pt pt2 {rptc}\n"
        if rser > 0:
            s += f"Rser pt2 n1 {rser}\n"
        else:
            s += "Vlink pt2 n1 0\n"
    # TVS bidireccional a COM en n1 (no en O2)
    if opt != "O2":
        s += f"Btvs n1 0 I=sgn(V(n1))*max(abs(V(n1))-{TVS_KNEE},0)/{TVS_RD}\n"
    s += f"Rs n1 n2 {rs}\n"
    if opt == "O1":
        # proteccion de la fuente desviada a COM + diodo serie que bloquea el diodo de cuerpo del BSS84
        s += "Dblk n2s n2 BAV199\nDcn 0 n2 BAV199\nCn2 n2 0 2p\n"
    else:
        s += "Vn2 n2 n2s 0\nD2p n2 rp BAV199\n"
        s += ("Dcn 0 n2 BAV199\n" if clampcom else "D2n rn n2 BAV199\n")
    s += source(isrc)
    s += rails(zener or opt in ("O2",))
    if analysis == "tran":
        s += f".tran 0 {tstop} 0 {dtmax}\n.end\n"
    else:
        s += ".dc Vgrid 0 4.6 0.005\n.end\n"
    return s

def metrics(d, opt, t0, t1, rptc, rs):
    import numpy as np
    from rdlib import integ
    t = d['time']; m = (t >= t0) & (t <= t1)
    V = lambda n: d[f'v({n})']; I = lambda n: d[f'i({n})']
    out = {}
    isr = I('vsr')
    out['I_pk_A'] = float(np.abs(isr[m]).max())
    out['I_rms_A'] = float(np.sqrt(integ(t[m], isr[m]**2) / (t[m][-1]-t[m][0])))
    if opt == 'O2':
        pser = V('pt') * 0  # no se usa
        pl = (V('pt') - V('n1')) * isr
        out['E_lim_J_per_cyc'] = integ(t[m], pl[m]); out['P_lim_pk_W'] = float(np.abs(pl[m]).max())
        out['V_lim_pk_V'] = float(np.abs(V('pt')-V('n1'))[m].max())
        out['P_ptc_avg_W'] = 0.0
    else:
        pp = isr**2 * rptc
        out['P_ptc_avg_W'] = integ(t[m], pp[m]) / (t[m][-1]-t[m][0])
        out['P_ptc_pk_W'] = float(pp[m].max())
        out['E_ptc_J_per_cyc'] = integ(t[m], pp[m])
        ptv = V('n1') * I('btvs')
        out['E_tvs_J_per_cyc'] = integ(t[m], ptv[m]); out['P_tvs_pk_W'] = float(np.abs(ptv[m]).max())
        out['P_tvs_avg_W'] = out['E_tvs_J_per_cyc'] / (t[m][-1]-t[m][0])
        out['I_tvs_pk_A'] = float(np.abs(I('btvs')[m]).max())
        out['V_n1_pk_V'] = float(np.abs(V('n1')[m]).max())
    irs = I('rs')
    out['I_Rs_pk_A'] = float(np.abs(irs[m]).max())
    out['P_Rs_avg_W'] = integ(t[m], (irs**2 * rs)[m]) / (t[m][-1]-t[m][0])
    out['E_Rs_J_per_cyc'] = integ(t[m], (irs**2 * rs)[m])
    out['P_Rs_pk_W'] = float((irs**2 * rs)[m].max())
    out['rp_max_V'] = float(V('rp')[m].max()); out['rn_min_V'] = float(V('rn')[m].min())
    out['span_max_V'] = float((V('rp') - V('rn'))[m].max())
    ip = -I('vhead')                           # corriente que entra en rp por el diodo de cuerpo
    out['I_body_pk_A'] = float(ip[m].max())
    for nm in ('d2p', 'd2n', 'dblk', 'dcn'):
        if f'i({nm})' in d: out[f'I_{nm}_pk_A'] = float(np.abs(d[f'i({nm})'][m]).max())
    out['I_Xh6_rp_pk_A'] = float(np.abs(d['ix(xh6:rp)'][m]).max()); out['I_Xh6_rn_pk_A'] = float(np.abs(d['ix(xh6:rn)'][m]).max())
    if 'i(dzp)' in d:
        out['I_zener_p_pk_A'] = float(np.abs(d['i(dzp)'][m]).max()); out['I_zener_n_pk_A'] = float(np.abs(d['i(dzn)'][m]).max())
    # corriente que corta el rele: al azar (pico) y 1 ms despues de un cruce por cero
    zc = t[m][1:][np.diff(np.sign(V('vin')[m])) != 0]
    if len(zc):
        out['I_cut_1ms_after_zc_A'] = float(np.abs(np.interp(zc[-1] + 1e-3, t, isr)))
    return out
