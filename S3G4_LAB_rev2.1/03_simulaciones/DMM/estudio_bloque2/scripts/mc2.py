# -*- coding: utf-8 -*-
"""Residuo de planitud en alterna tras la corrección por firmware (un cero y un polo por rango, calibrados a 1 y 20 kHz).
Compara variantes de hardware con Monte Carlo (tolerancias de C0G, capacidades parásitas ±30 %, ruido de calibración)."""
import numpy as np, json, sys
from scipy.optimize import least_squares
from red import *

FG = np.geomspace(40, 20e3, 33)
def modelo(f, fa, fb): return np.abs((1+1j*f/fa)/(1+1j*f/fb))

def draw(base, rng, tolCt, tolC23, tolP, tolR=0.001):
    p = dict(base)
    p['Ct'] = np.mean(rng.uniform(1-tolCt, 1+tolCt, 3))*base['Ct']
    p['C2'] = base['C2']*rng.uniform(1-tolC23, 1+tolC23); p['C3'] = base['C3']*rng.uniform(1-tolC23, 1+tolC23)
    for k in ('Rt', 'R2', 'R3'): p[k] = base[k]*rng.uniform(1-tolR, 1+tolR)
    p['Rprot'] = base['Rprot']*rng.uniform(0.99, 1.01)
    for k in ('C_bav', 'C_ypin', 'C_pcb_pre', 'C_z', 'C_pcb_com'): p[k] = base[k]*rng.uniform(1-tolP, 1+tolP)
    p['C_amp'] = base['C_amp']*rng.uniform(0.85, 1.15); p['Ron'] = base['Ron']*rng.uniform(0.7, 1.3)
    return p

def rr(kind, p, f):
    f = np.atleast_1d(f)
    if kind == 'x0': return np.abs(h_x0(f, p))/abs(h_x0(np.array([1e-3]), p)[0])
    s = 1 if kind == 'x1' else 2
    return np.abs(h_div(f, p, s))/abs(h_div(np.array([1e-3]), p, s)[0])

def nominal_pz(kind, base):
    if kind == 'x0':
        r = rr('x0', base, 20e3)[0]; return 1e12, 20e3/np.sqrt(1/r**2-1)
    hf = rr(kind, base, 100e3)[0]
    # arranque del ajuste: cero en el codo del divisor
    fz = 1/(2*np.pi*base['Rt']/3*0+ 2*np.pi*0+1)   # no se usa
    return 530.0, 530.0*hf

def correr(kind, base, N, tolCt, tolC23, tolP, cal=(1e3, 20e3), sig=0.0005, libre='ambos', seed=1):
    rng = np.random.default_rng(seed)
    fa0, fb0 = nominal_pz(kind, base)
    cal = np.array(cal)
    res = []; droop = []
    for _ in range(N):
        p = draw(base, rng, tolCt, tolC23, tolP)
        r = rr(kind, p, FG); rc = rr(kind, p, cal)*(1+rng.normal(0, sig, len(cal)))
        if kind == 'x0' or libre == 'polo':
            a = fa0 if kind != 'x0' else 1e12
            f = least_squares(lambda x: modelo(cal, a, np.exp(x[0]))/rc-1, [np.log(fb0)])
            fa, fb = a, np.exp(f.x[0])
        else:
            f = least_squares(lambda x: modelo(cal, np.exp(x[0]), np.exp(x[1]))/rc-1, [np.log(fa0), np.log(fb0)])
            fa, fb = np.exp(f.x)
        res.append((r/modelo(FG, fa, fb)-1)*100); droop.append((r[-1]-1)*100)
    res = np.array(res); m = np.abs(res).max(axis=1)
    return dict(p50=float(np.percentile(m, 50)), p95=float(np.percentile(m, 95)), p99=float(np.percentile(m, 99)), max=float(m.max()),
                droop_med=float(np.median(droop)), droop_lo=float(np.percentile(droop, 2.5)), droop_hi=float(np.percentile(droop, 97.5)))

def fmt(d): return ' '.join(f'{k}={v:.2f}' for k, v in d.items())

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 400
    out = {}
    H = par()
    R = par(C2=270e-12, C3=2.7e-9)
    for nm, base, tCt, t23 in [('H (330p/3.0n, C0G 5%)', H, .05, .05), ('retoque 270p/2.7n, 5%', R, .05, .05), ('retoque 270p/2.7n, C2 y C3 al 1%', R, .05, .01)]:
        for kind in ('x1', 'x2'):
            for libre in ('ambos', 'polo'):
                d = correr(kind, base, N, tCt, t23, 0.30, libre=libre)
                out[f'{nm}|{kind}|{libre}'] = d
                print(f'{nm:38s} {kind} cero {libre:5s}: {fmt(d)}')
    # puntos de calibración
    for cal in [(1e3, 20e3), (100, 1e3, 20e3), (40, 1e3, 20e3), (200, 5e3, 20e3)]:
        d = correr('x1', R, N, .05, .05, 0.30, cal=cal)
        out[f'cal {cal}|x1'] = d; print('cal', cal, 'x1 (retoque, 5%):', fmt(d))
    for sig in (0.0, 0.0005, 0.001, 0.002):
        d = correr('x1', R, N, .05, .05, 0.30, sig=sig); print('ruido de calibracion', sig*100, '% : x1', fmt(d)); out[f'sig {sig}|x1'] = d
    json.dump(out, open('mc2_result.json', 'w'), indent=1)
