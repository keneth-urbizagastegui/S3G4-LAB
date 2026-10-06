"""S1b: search in a linearized RC network, verify every selected value in LTspice.

Final criteria use LTspice .meas exclusively. Fixed seed and ordered CSVs.
No S1 writes/imports (including __pycache__); no external downloads.
"""
from __future__ import annotations
import argparse
import concurrent.futures as futures
import csv
import hashlib
import json
import math
import os
import random
import re
import subprocess
import threading
import time
from pathlib import Path
# Avoid nested BLAS parallelism inside the independent LTspice case workers.
# This is process-local; no host configuration or electrical parameter changes.
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
import numpy as np
from scipy.linalg import eigh
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parent
WORK = ROOT / 'S1b' / 'generados'
RESULT = ROOT / 'resultados'
LT = Path(r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe')
SEED = 20261003
CRITERIA = {
    'S1b-C1': {'zin': 1e6, 'tol_pct': 2},
    'S1b-C2': {'lo_pF': 10, 'hi_pF': 30, 'delta_pF': 2},
    'S1b-C3': {'tol_pct': .5},
    'S1b-C4': {'flat_pct': 1, 'peak_db': .1, 'fc_hz': 10},
    'S1b-C5': {'step_pct': 2, 'convergence_pp': .05},
    'S1b-C6': {'flat_pct': 1, 'stop_cases': 0},
    'S1b-C7': {'delta_pF': 2},
    'S1b-C8': {'step_pct': 2},
    'S1b-C9': {'zin': 1e6, 'tol_pct': 2, 'flat_pct': 1},
}
RANGES = {1: (2., 6.), 2: (3., 10.), 3: (5., 20.)}
CPLS = {0: 'DC', 1: 'AC', 2: 'GND'}
CJO = 1.5e-12
CJP = CJO/(1+5/.6)**.3
CSEL = 2*CJP+3e-12+5e-12+2*.5e-12
RS = 2*49.9e3
RBP = 11e3*10e6/(11e3+10e6)
CB = (20e-12/2+1e-12)*2*549e3/RBP-(CSEL+2e-12)
CS = 10e6*(2e-12+1e-12+CSEL)/RS
BOUNDS_A = {
    'FRT1': (.999, 1.001), 'FRT2': (.999, 1.001), 'FRB': (.999, 1.001),
    'FRS1': (.99, 1.01), 'FRS2': (.99, 1.01), 'FRBIAS': (.99, 1.01),
    'FREQ': (.99, 1.01), 'FCT1': (.98, 1.02), 'FCT2F': (.98, 1.02),
    'FCB': (.98, 1.02), 'FCS': (.98, 1.02), 'FCEQ': (.98, 1.02),
    'FCAC': (.95, 1.05), 'FCOFF': (.8, 1.2), 'FCSEL': (.9, 1.1),
    'FCIN': (.9, 1.1), 'FCJO': (.8, 1.2), 'FCX1': (.9, 1.1),
    'FCBNC': (.9, 1.1), 'FCSW': (.8, 1.2),
}
BOUNDS_B = dict(BOUNDS_A, FCOFF=(.5, 1.5), FCSEL=(.5, 1.5),
                FCIN=(.6, 1.4), FCJO=(.7, 1.3), FCX1=(.5, 1.5),
                FCBNC=(2/3, 4/3))
SIMS = []
CASE_ERRORS = []
LOCK = threading.Lock()


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def csv_write(path, rows):
    keys = list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader(); w.writerows(rows)


def table(rows, keys):
    return '| '+' | '.join(keys)+' |\n| '+' | '.join(['---']*len(keys))+' |\n'+ '\n'.join(
        '| '+' | '.join(str(r.get(k, '')) for k in keys)+' |' for r in rows)


def header(title):
    return [f'* {title}', f'.include "{ROOT / "comun/ch1_comun_s1b.inc"}"',
            '.options numdgt=15 plotwinsize=0 threads=1', 'XR VP VN RAILS']


def tag(campaign, case, rango, pos, cpl, stage='final'):
    return f'{campaign}_{case}_r{rango}_pos{pos}_cpl{CPLS[cpl]}_{stage}'.lower()


def inst(t, pos, cpl, rango, trim, f, ceq=CSEL, dtrim=0., bnc=None, out=None):
    args = ' '.join(f'{k}={v:.16g}' for k, v in f.items())
    return (f'X{t} {bnc or "BNC_"+t} {out or "OUT_"+t} VP VN FRONT_P4B '
            f'POS={pos} CPL={cpl} CT1=20p RANGO={rango} CTRIM={trim*1e-12:.16g} '
            f'DTRIM={dtrim*1e-12:.16g} CEQSEL={ceq:.16g} {args}')


def ac_net(campaign, case, rango, trim, f, ceq=CSEL, states=None,
           stage='final', e1=False, dtrim=0.):
    lines = header(f'{campaign} {case} R{rango} {stage}')
    states = states or [(p, c) for p in (1, 100) for c in (0, 1, 2)]
    saved = []
    for pos, cpl in states:
        t = tag(campaign, case, rango, pos, cpl, stage)
        lines += [f'Vsrc_{t} SRC_{t} 0 AC 1', f'Vsense_{t} BNC_{t} SRC_{t} 0',
                  inst(t, pos, cpl, rango, trim, f, ceq, dtrim)]
        saved += [f'V(BNC_{t})', f'I(Vsense_{t})', f'V(OUT_{t})']
        lines += [f'.meas AC {t}_zin FIND mag(V(BNC_{t})/I(Vsense_{t})) AT=100',
                  f'.meas AC {t}_cin FIND (-im(I(Vsense_{t})/V(BNC_{t}))/(2*pi*1Meg)) AT=1Meg']
        if not e1 and cpl != 2:
            gain = f'mag(V(OUT_{t})/V(BNC_{t}))'
            lines += [f'.meas AC {t}_g1 FIND {gain} AT=1k',
                      f'.meas AC {t}_gmin MIN {gain} FROM=10 TO=2Meg',
                      f'.meas AC {t}_gmax MAX {gain} FROM=10 TO=2Meg',
                      f'.meas AC {t}_amin MIN {gain} FROM=10k TO=2Meg',
                      f'.meas AC {t}_amax MAX {gain} FROM=10k TO=2Meg',
                      f'.meas AC {t}_peak MAX {gain} FROM=1 TO=20Meg']
            for hz, label in ((100000, '100k'), (1000000, '1m'), (2000000, '2m')):
                lines += [f'.meas AC {t}_g{label} FIND {gain} AT={hz}']
            if cpl == 1:
                lines += [f'.meas AC {t}_fc WHEN {gain}={t}_g1/sqrt(2) RISE=1']
    lines += ['.save '+' '.join(saved), '.ac dec 240 10 10Meg' if e1 else '.ac dec 240 1 20Meg', '.end']
    return '\n'.join(lines)+'\n'


def tran_net(campaign, case, rango, trim, f, tips, ceq=CSEL, dtrim=0.,
             maxstep='2n', periodic=False, windowed=True):
    lines = header(f'E3b {campaign} {case} R{rango}; tips={tips}; maxstep={maxstep}')
    lines += ['.options method=gear solver=alt']
    # First rising edge from the solved -1V equilibrium. Nominal also checked
    # with the second edge of the periodic square wave used in S1.
    t0 = .0015 if periodic else 1e-7
    delay = .0005 if periodic else t0
    stop = t0+.000401
    saved = []
    for j, tip in enumerate(tips):
        # Only the center candidate needs POS1; the probe is adjusted in POS100.
        for pos in ((1, 100) if j == len(tips)//2 else (100,)):
            t = tag(campaign, case, rango, pos, 0, f'tip{j}_{maxstep}')
            lines += [f'Vtip_{t} TIP_{t} 0 PULSE(-1 1 {delay:.16g} 5n 5n {{0.5/1k-5n}} 1m)',
                      f'Rgen_{t} TIP_{t} P_{t} 50', f'Rprobe_{t} P_{t} BNC_{t} 9Meg',
                      f'Cprobe_{t} P_{t} BNC_{t} {tip*1e-12:.16g}', f'Ccable_{t} BNC_{t} 0 80p',
                      inst(t, pos, 0, rango, trim, f, ceq, dtrim),
                      f'Vdc_{t} DCTIP_{t} 0 1', f'Rdcgen_{t} DCTIP_{t} DP_{t} 50',
                      f'Rdcprobe_{t} DP_{t} DBNC_{t} 9Meg',
                      inst('ref_'+t, pos, 0, rango, trim, f, ceq, dtrim, 'DBNC_'+t, 'REF_'+t)]
            saved += [f'V(OUT_{t})', f'V(REF_{t})']
            lines += [f'.meas TRAN {t}_ref FIND V(REF_{t}) AT={t0:.16g}',
                      f'.meas TRAN {t}_max MAX V(OUT_{t}) FROM={t0:.16g} TO={t0+.0004:.16g}',
                      f'.meas TRAN {t}_objective MAX abs(V(OUT_{t})-V(REF_{t})) FROM={t0+1e-7:.16g} TO={t0+5e-9+.0002:.16g}']
            for us in (2, 20, 200):
                lines += [f'.meas TRAN {t}_v{us} FIND V(OUT_{t}) AT={t0+5e-9+us*1e-6:.16g}']
    if windowed:
        # Explicit PWL breakpoints force <=2ns (or <=1ns) around the measured
        # edge. Guard is an isolated numerical voltage source, not a component
        # added to the DUT. Outside the window use 100ns; raw times are checked.
        dt = 1e-9 if maxstep == '1n' else 2e-9
        points = ['0 0']
        n = math.ceil((5e-6+5e-9)/dt)+1
        points += [f'{t0+k*dt:.16g} {k%2}' for k in range(n)]
        points += [f'{t0+n*dt:.16g} 0']
        lines += ['Vtimeguard TIMEGUARD 0 PWL('+' '.join(points)+')',
                  f'* Required fine window: {t0:.16g} to {t0+5e-9+5e-6:.16g}; dt<={dt:.16g}']
        dmax = '100n'
    else:
        dmax = maxstep
    lines += ['.save '+' '.join(saved), f'.tran 0 {stop:.16g} 0 {dmax}', '.end']
    return '\n'.join(lines)+'\n'


def read_log(path):
    b = path.read_bytes()
    s = b.decode('utf-16' if b.startswith((b'\xff\xfe', b'\xfe\xff')) else 'utf-8', errors='replace')
    values = {}
    for line in s.splitlines():
        m = re.match(r'^([a-z][a-z0-9_]*_fc):.*\sAT\s+([-+0-9.eE]+)\s*$', line, re.I)
        if m:
            values[m[1].lower()] = float(m[2]); continue
        m = re.match(r'^([a-z][a-z0-9_]*):.*?=\s*(\([^\r\n]+?\)|[-+0-9.eE]+)(?:\s+at|\s+FROM|$)', line, re.I)
        if m:
            db = re.match(r'\(([-+0-9.eE]+)dB,', m[2])
            values[m[1].lower()] = 10**(float(db[1])/20) if db else float(m[2])
    errors = [l for l in s.splitlines() if re.search(r'Fatal|Error:|failed|unknown parameter|unknown subcircuit|singular matrix|Expected device|syntax error', l, re.I)]
    warnings = [l for l in s.splitlines() if re.search(r'warning|questionable|timestep too small', l, re.I)]
    return values, errors, warnings


def _simulate(path, net):
    write(path, net)
    for ext in ('.log', '.raw', '.op.raw'):
        path.with_suffix(ext).unlink(missing_ok=True)
    proc = subprocess.run([str(LT), '-b', str(path)], cwd=path.parent,
                          capture_output=True)
    log = path.with_suffix('.log')
    if not log.exists():
        raise RuntimeError(f'{path}: no log; code={proc.returncode}')
    values, errors, warnings = read_log(log)
    expected = set(re.findall(r'^\.meas\s+\w+\s+(\w+)', net, re.M | re.I))
    expected = {s.lower() for s in expected}
    values = {k: v for k, v in values.items() if k in expected}
    if expected != set(values):
        errors += [f'Missing measures: {sorted(expected-set(values))}']
    if any(not math.isfinite(v) for v in values.values()):
        errors += ['Non-finite measurement']
    timecheck = {}
    window = re.search(r'Required fine window: ([\d.eE+-]+) to ([\d.eE+-]+); dt<=([\d.eE+-]+)', net)
    if window and path.with_suffix('.raw').exists():
        raw = path.with_suffix('.raw').read_bytes()
        marker = 'Binary:\n'.encode('utf-16le')
        k = raw.index(marker)+len(marker)
        rh = raw[:k].decode('utf-16le')
        nv = int(re.search(r'No. Variables:\s*(\d+)', rh)[1])
        times = np.frombuffer(raw[k:], dtype='<f8').reshape(-1, nv)[:, 0]
        t0, t1, limit = map(float, window.groups())
        dt = np.diff(times)
        mask = (times[:-1] < t1) & (times[1:] > t0)
        measured = float(max(dt[mask]))
        timecheck = dict(maximum_fine_step_ns=measured*1e9, fine_step_limit_ns=limit*1e9,
                         transient_points=len(times))
        if measured > limit*1.00001:
            errors += [f'Fine time window violation: {measured} > {limit}']
    with LOCK:
        SIMS.append(dict(file=path.relative_to(ROOT).as_posix(), returncode=proc.returncode,
                         errors=errors, warnings=warnings, measures=len(values), **timecheck))
    for ext in ('.raw', '.op.raw', '.db'):
        path.with_suffix(ext).unlink(missing_ok=True)
    if proc.returncode or errors:
        raise RuntimeError(f'{path.name}: code={proc.returncode}; {errors}')
    return values


def simulate(path, net):
    try:
        return _simulate(path, net)
    except Exception as exc:
        name = path.relative_to(ROOT).as_posix()
        with LOCK:
            if not any(s['file'] == name for s in SIMS):
                SIMS.append(dict(file=name, returncode=1, errors=[str(exc)],
                                 warnings=[], measures=0))
        raise


def rc_matrices(pos, rango, trim, f, ceq=CSEL, probe=None, merge=False):
    """Exact passive topology for search; closed contacts retain 0.1 ohm.
    Rails are AC ground, reverse-biased diodes linearized at 5V only here.
    LTspice retains full nonlinear diodes and finite rail source resistance.
    """
    names = ['BNC', 'M', 'TAP', 'X1', 'EQ', 'SEL', 'T2', 'B', 'BI']
    if probe is not None:
        names += ['P']
    aliases = {n: n for n in names}
    if merge:
        aliases['SEL'] = aliases['B'] = 'TAP' if pos == 100 else 'X1'
        aliases['T2'] = aliases['SEL']  # isolated AC throw in DC; unobservable floating mode
        if pos == 100: aliases['EQ'] = 'X1'
    unique = list(dict.fromkeys(aliases.values()))
    idx = {n: unique.index(aliases[n]) for n in names}
    G = np.zeros((len(unique), len(unique))); C = G.copy()
    def stamp(matrix, a, b, v):
        ia, ib = idx.get(a), idx.get(b)
        if ia == ib: return
        if ia is not None: matrix[ia, ia] += v
        if ib is not None: matrix[ib, ib] += v
        if ia is not None and ib is not None:
            matrix[ia, ib] -= v; matrix[ib, ia] -= v
    def r(a, b, v): stamp(G, a, b, 1/v)
    def c(a, b, v): stamp(C, a, b, v)
    F = lambda k: f.get(k, 1.)
    r('BNC', 'M', 549e3*F('FRT1')); r('M', 'TAP', 549e3*F('FRT2'))
    c('BNC', 'M', 20e-12*F('FCT1'))
    c('M', 'TAP', ((20-sum(RANGES[rango])/2)*F('FCT2F')+trim)*1e-12)
    r('TAP', None, 11e3*F('FRB')); c('TAP', None, CB*F('FCB')+2e-12)
    r('BNC', 'X1', 49.9e3*(F('FRS1')+F('FRS2'))); c('BNC', 'X1', CS*F('FCS'))
    c('X1', None, 2e-12*F('FCX1')); c('BNC', None, 3e-12*F('FCBNC'))
    r('TAP', 'SEL', .1 if pos == 100 else 1e18)
    r('X1', 'SEL', .1 if pos == 1 else 1e18)
    c('X1' if pos == 100 else 'TAP', 'SEL', 1e-12*F('FCOFF'))
    r('X1', 'EQ', .1 if pos == 100 else 1e18)
    if pos == 1: c('X1', 'EQ', 1e-12*F('FCOFF'))
    r('EQ', None, 10e6*F('FREQ')); c('EQ', None, ceq*F('FCEQ'))
    c('SEL', None, 3e-12*F('FCSEL')+2*CJP*F('FCJO'))
    c('SEL', 'T2', 1.8e-9*F('FCAC'))
    r('B', 'SEL', .1); r('B', 'T2', 1e18); r('B', None, 1e18)
    c('B', 'T2', .5e-12*F('FCSW')); c('B', None, .5e-12*F('FCSW'))
    r('B', None, 10e6*F('FRBIAS')); r('B', 'BI', 1e3); c('BI', None, 5e-12*F('FCIN'))
    if probe is not None:
        r('P', None, 50); r('P', 'BNC', 9e6)
        c('P', 'BNC', probe*1e-12); c('BNC', None, 80e-12)
    return G, C, idx


FREQS = np.unique(np.r_[1000., np.geomspace(1e4, 2e6, 600), 1e5, 1e6])


def predicted_ac(pos, rango, trim, f, ceq=CSEL, freqs=FREQS):
    G, C, idx = rc_matrices(pos, rango, trim, f, ceq)
    Y = G[None, :, :]+2j*np.pi*np.asarray(freqs)[:, None, None]*C[None, :, :]
    v = np.linalg.solve(Y[:, 1:, 1:], -Y[:, 1:, 0, None])[:, :, 0]
    h = v[:, idx['BI']-1]
    current = Y[:, 0, 0]+np.einsum('fi,fi->f', Y[:, 0, 1:], v)
    return h, current


def trim_guess(rango, f, ceq=CSEL):
    lo, hi = RANGES[rango]
    def balance(t):
        h, _ = predicted_ac(100, rango, t, f, ceq)
        dev = np.abs(h[1:])/abs(h[0])-1
        return float(dev.min()+dev.max())
    if balance(lo) >= 0: return lo
    if balance(hi) <= 0: return hi
    for _ in range(14):
        mid = (lo+hi)/2
        if balance(mid) > 0: hi = mid
        else: lo = mid
    return round(((lo+hi)/2)/.05)*.05


def ac_rows(a, campaign, case, rango, stage='final'):
    rows = []
    for pos in (1, 100):
        for cpl in (0, 1, 2):
            t = tag(campaign, case, rango, pos, cpl, stage)
            if t+'_zin' not in a: continue
            r = dict(campaign=campaign, case=case, RANGO=rango, POS=pos,
                     CPL=CPLS[cpl], stage=stage, zin_ohm=a[t+'_zin'], cin_pF=a[t+'_cin']*1e12)
            if t+'_g1' in a:
                g = a[t+'_g1']; nom = 10e6/(RS+10e6) if pos == 1 else RBP/(2*549e3+RBP)
                r.update(gain_1k=g, gain_error_pct=100*(g/nom-1),
                         flat_min_pct=100*(a[t+'_gmin']/g-1), flat_max_pct=100*(a[t+'_gmax']/g-1),
                         adj_min_pct=100*(a[t+'_amin']/g-1), adj_max_pct=100*(a[t+'_amax']/g-1),
                         peak_db=20*math.log10(a[t+'_peak']/g))
                for label in ('100k', '1m', '2m'): r['dev_'+label+'_pct'] = 100*(a[t+'_g'+label]/g-1)
                if cpl == 1: r['fc_hz'] = a[t+'_fc']
            rows.append(r)
    dc = [r for r in rows if r['CPL'] == 'DC']
    if len(dc) == 2:
        delta = dc[0]['cin_pF']-dc[1]['cin_pF']
        for r in rows: r.update(delta_cin_signed_pF=delta, delta_cin_pF=abs(delta))
    return rows


def flat(r, adjustment=False):
    prefix = 'adj' if adjustment else 'flat'
    return max(abs(r[prefix+'_min_pct']), abs(r[prefix+'_max_pct']))


def adjust(campaign, case, rango, f, ceq):
    guess = trim_guess(rango, f, ceq)
    lo, hi = RANGES[rango]
    tested = {}; history = []
    # Search accelerator never decides criteria: final grid minimum and both
    # adjacent points are measured with LTspice. Walk if the predictor missed.
    for iteration in range(20):
        for t in sorted({lo, hi, max(lo, round(guess-.05, 8)), guess, min(hi, round(guess+.05, 8))}):
            if t in tested: continue
            stage = f'trim{len(tested):03d}'
            a = simulate(WORK/f'{campaign}_{case}_r{rango}_{stage}.cir',
                         ac_net(campaign, case, rango, t, f, ceq, [(100, 0)], stage))
            score = flat(ac_rows(a, campaign, case, rango, stage)[0], True)
            tested[t] = score
            history.append(dict(campaign=campaign, case=case, RANGO=rango,
                                CTRIM_pF=t, flat_pct=score, stage=stage))
        best = min(tested, key=lambda t: (tested[t], t))
        if abs(best-guess) < 1e-8: return best, history
        guess = best
    raise RuntimeError(f'Trimmer search did not converge: {campaign} {case} R{rango}')


def tip_guess(rango, trim, f, ceq):
    times = np.geomspace(1e-7, .0002+5e-9, 600)
    def objective(tip):
        G, C, idx = rc_matrices(100, rango, trim, f, ceq, tip, merge=True)
        b = np.zeros(len(G)); b[idx['P']] = 1/50
        dc = np.linalg.solve(G, b)
        lam, q = eigh(G, C)
        if min(lam) <= 0: raise RuntimeError('Unstable linear search model')
        coeff = q[idx['BI'], :]*(q.T@C@dc)
        # Exact response to a 5ns ramp, normalized to the full 2V DC step.
        ramp = -np.expm1(-lam*5e-9)/(lam*5e-9)
        error = -(coeff*ramp)@np.exp(-lam[:, None]*(times[None, :]-5e-9))/dc[idx['BI']]
        return float(np.max(abs(error)))
    opt = minimize_scalar(objective, bounds=(5., 25.), method='bounded', options={'xatol': .0001})
    return round(float(opt.x), 5)


def tr_rows(t, campaign, case, rango, j=0, maxstep='2n'):
    rows = []
    for pos in (1, 100):
        tt = tag(campaign, case, rango, pos, 0, f'tip{j}_{maxstep}')
        if tt+'_ref' not in t: continue
        ref = t[tt+'_ref']; height = 2*abs(ref)
        r = dict(campaign=campaign, case=case, RANGO=rango, POS=pos, CPL='DC',
                 step_height_v=height, overshoot_pct=100*max(0, t[tt+'_max']-ref)/height,
                 objective_pct=100*t[tt+'_objective']/height)
        for us in (2, 20, 200): r[f'error_{us}us_pct'] = 100*(t[tt+f'_v{us}']-ref)/height
        rows.append(r)
    return rows


def probe_adjust(campaign, case, rango, trim, f, ceq):
    tip = tip_guess(rango, trim, f, ceq)
    history = []
    for iteration in range(12):
        tips = [round(tip-.002, 6), tip, round(tip+.002, 6)]
        values = simulate(WORK/f'{campaign}_{case}_r{rango}_probe{iteration:02d}.cir',
                          tran_net(campaign, case, rango, trim, f, tips, ceq))
        groups = [tr_rows(values, campaign, case, rango, j) for j in range(3)]
        scores = [next(r for r in rs if r['POS'] == 100)['objective_pct'] for rs in groups]
        best = min(range(3), key=lambda j: (scores[j], abs(j-1)))
        for j in range(3):
            history.append(dict(campaign=campaign, case=case, RANGO=rango,
                                iteration=iteration, CTIP_pF=tips[j], objective_pct=scores[j]))
        if best == 1:
            return tip, groups[1], history
        tip = tips[best]
    raise RuntimeError(f'Probe search did not converge {campaign} {case} R{rango}')


def select_ceq(campaign, case, rango, trim, f):
    def delta(ceq, stage):
        a = simulate(WORK/f'{campaign}_{case}_r{rango}_{stage}.cir',
                     ac_net(campaign, case, rango, trim, f, ceq, [(1, 0), (100, 0)], stage, e1=True))
        return ac_rows(a, campaign, case, rango, stage)[0]['delta_cin_signed_pF']
    lo, hi = 1e-12, 30e-12
    dlo, dhi = delta(lo, 'ceqlo'), delta(hi, 'ceqhi')
    if dlo*dhi >= 0: raise RuntimeError('CEQ root not bracketed')
    hist = []
    for i in range(15):
        mid = (lo+hi)/2; d = delta(mid, f'ceqbis{i:02d}')
        hist.append(dict(campaign=campaign, case=case, RANGO=rango, CEQ_pF=mid*1e12, delta_pF=d))
        if d*dlo > 0: lo, dlo = mid, d
        else: hi = mid
    target = (lo+hi)/2
    e24 = [v*10**k*1e-12 for k in (-1, 0, 1) for v in (1., 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2., 2.2, 2.4, 2.7, 3., 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1)]
    picked = min(e24, key=lambda x: abs(x-target))
    return target, picked, hist


def run_case(job):
    campaign, i, rango, f, resolution = job
    case = f'c{i:03d}'
    trim, th = adjust(campaign, case, rango, f, CSEL)
    lo, hi = RANGES[rango]
    actual = min(hi, max(lo, trim+resolution))
    acpath = (ROOT/'S1b/E4A_mc.cir' if campaign == 'A' and i == 0 and rango == 1
              else ROOT/'S1b/E4B_mc.cir' if campaign == 'B' and i == 0
              else WORK/f'{campaign}_{case}_r{rango}_ac.cir')
    before = simulate(acpath,
                      ac_net(campaign, case, rango, actual, f))
    rows = ac_rows(before, campaign, case, rango)
    for r in rows:
        if r['CPL'] == 'DC':
            h, current = predicted_ac(r['POS'], rango, actual, f, freqs=np.array([1000., 1e6]))
            r['search_gain_validation_rel'] = abs(abs(h[0])/r['gain_1k']-1)
            r['search_cin_validation_pF'] = abs(current[1].imag/(2*np.pi*1e6)*1e12-r['cin_pF'])
            if r['search_gain_validation_rel'] > 1e-4 or r['search_cin_validation_pF'] > .01:
                raise RuntimeError(f'Linear AC search model differs from LTspice: {campaign} {case}')
    metadata = dict(campaign=campaign, case=case, RANGO=rango, CTRIM_set_pF=trim,
                    CTRIM_resolution_pF=resolution, CTRIM_actual_pF=actual,
                    at_stop=int(trim in (lo, hi) or actual in (lo, hi)))
    ceq = CSEL; sh = []; selection = []
    initial_probe = None; initial_history = []
    if campaign == 'B':
        initial_tip, initial_trs, initial_history = probe_adjust('B_initial', case, rango, actual, f, CSEL)
        initial_probe = (initial_tip, initial_trs)
        target, ceq, sh = select_ceq(campaign, case, rango, actual, f)
        after = simulate(WORK/f'{campaign}_{case}_r{rango}_selected.cir',
                         ac_net(campaign, case, rango, actual, f, ceq, stage='selected'))
        after_rows = ac_rows(after, campaign, case, rango, 'selected')
        selection = [dict(**metadata, CEQ_target_pF=target*1e12, CEQ_E24_pF=ceq*1e12,
                          delta_before_pF=rows[0]['delta_cin_pF'], delta_after_pF=after_rows[0]['delta_cin_pF'],
                          flat100_after_pct=flat(next(r for r in after_rows if r['POS'] == 100 and r['CPL'] == 'DC'), True))]
        rows += after_rows
    tip, trs, ph = probe_adjust(campaign, case, rango, actual, f, ceq)
    for r in rows:
        rtip, rtrs = initial_probe if campaign == 'B' and r['stage'] == 'final' else (tip, trs)
        r.update(metadata, CTIP_pF=rtip, CEQ_pF=ceq*1e12 if r['stage'] == 'selected' else CSEL*1e12)
        if r['CPL'] == 'DC':
            r.update({k: v for k, v in next(x for x in rtrs if x['POS'] == r['POS']).items() if k not in ('campaign', 'case', 'RANGO', 'POS', 'CPL')})
    return rows, th, initial_history+ph, sh, selection


def summary(nominal, conv, rows, selection, count):
    criteria = []
    def add(c, value, ok, rango='nominal'):
        criteria.append(dict(criterion=c, RANGO=rango, value=value, status='PASA' if ok else 'FALLA'))
    dc = [r for r in nominal if r['CPL'] == 'DC']
    ng = [r for r in nominal if r['CPL'] != 'GND']
    c = CRITERIA['S1b-C1']; zs = [r['zin_ohm']/1e6 for r in ng]
    add('S1b-C1', f'{min(zs):.6f}…{max(zs):.6f} MΩ', all(abs(r['zin_ohm']/c['zin']-1)*100 <= c['tol_pct'] for r in ng))
    c = CRITERIA['S1b-C2']; cs = [r['cin_pF'] for r in dc]; d = dc[0]['delta_cin_pF']
    add('S1b-C2', f'Cin={min(cs):.6f}…{max(cs):.6f} pF; Δ={d:.6f} pF', all(c['lo_pF'] <= x <= c['hi_pF'] for x in cs) and d <= c['delta_pF'])
    err = max(abs(r['gain_error_pct']) for r in ng)
    add('S1b-C3', f'Error máximo {err:.6f} %', err <= CRITERIA['S1b-C3']['tol_pct'])
    c = CRITERIA['S1b-C4']; fd = max(flat(r) for r in dc); pk = max(r['peak_db'] for r in dc); fc = max(r['fc_hz'] for r in ng if r['CPL'] == 'AC')
    add('S1b-C4', f'Planitud {fd:.6f} %; pico {pk:.6f} dB; corte {fc:.6f} Hz', fd <= c['flat_pct'] and pk <= c['peak_db'] and fc < c['fc_hz'])
    c = CRITERIA['S1b-C5']; over = max(r['overshoot_pct'] for r in dc); e2 = max(abs(r['error_2us_pct']) for r in dc); change = max(abs(v) for r in conv for k, v in r.items() if k.startswith('shift_'))
    add('S1b-C5', f'Sobre {over:.6f} %; |e2| {e2:.6f} %; convergencia {change:.6f} pp', max(over, e2) <= c['step_pct'] and change <= c['convergence_pp'])
    ranges = []; eligible = []
    for rango in RANGES:
        group = [r for r in rows if r['campaign'] == 'A' and r['RANGO'] == rango and r['CPL'] == 'DC' and r['POS'] == 100]
        if not group: continue
        stops = sum(r['at_stop'] for r in group); bad = sum(flat(r, True) > CRITERIA['S1b-C6']['flat_pct'] for r in group)
        worst = max(flat(r, True) for r in group)
        ok = len(group) == count and bad == 0 and stops == 0
        if ok: eligible.append(rango)
        add('S1b-C6', f'Máx {worst:.6f} %; fuera {bad}/{len(group)}; topes {stops}/{len(group)}', ok, rango)
        vals = [r['CTRIM_set_pF'] for r in group]
        ranges.append(dict(RANGO=rango, cases=len(group), stops=stops, outside=bad,
                           trim_min_pF=min(vals), trim_median_pF=float(np.median(vals)), trim_max_pF=max(vals), worst_flat_pct=worst))
    chosen = min(eligible) if eligible else None
    # C7 and C9 apply to every tested A range. C8 uses only the smallest C6 range.
    a = [r for r in rows if r['campaign'] == 'A' and r['CPL'] == 'DC']
    if a:
        delta = max(r['delta_cin_pF'] for r in a)
        complete = len(a) == len(RANGES)*count*2
        add('S1b-C7', f'|ΔCin| máx {delta:.6f} pF', complete and delta <= CRITERIA['S1b-C7']['delta_pF'], 'A todos')
        g = [r for r in a if r['POS'] == 1 and r['RANGO'] == chosen]
        if g:
            over = max(r['overshoot_pct'] for r in g); e2 = max(abs(r['error_2us_pct']) for r in g)
            add('S1b-C8', f'Sobre máx {over:.6f} %; |e2| máx {e2:.6f} %', max(over, e2) <= CRITERIA['S1b-C8']['step_pct'], chosen)
        else:
            add('S1b-C8', 'Sin rango que cumpla C6: no evaluable', False, 'A')
        g = [r for r in a if r['POS'] == 1]; c = CRITERIA['S1b-C9']
        zg = [r for r in rows if r['campaign'] == 'A' and r['CPL'] != 'GND']
        zerr = max(abs(r['zin_ohm']/c['zin']-1)*100 for r in zg); fl = max(flat(r) for r in g)
        add('S1b-C9', f'Error Zin máx {zerr:.6f} %; planitud ×1 máx {fl:.6f} %', complete and zerr <= c['tol_pct'] and fl <= c['flat_pct'], 'A todos')
    return criteria, ranges, chosen


METHOD = '''
## Métodos y alcance

Contrato: PLAN_SIMULACION_S1b.md y PLAN_SIMULACION_S1.md; leídos ACTA_S1,
AUDITORIA_CLAUDE_S1, auditoría P4/P7 y revisión de entrada CH1 (§4 y §6).
Modelos: DBAV199 genérico, buffer ideal, rieles ±5 V con 1 Ω. No prueba física,
certificación de seguridad ni amplificador real. Ninguna pieza de diseño cambiada.

AC: 240 puntos/década; E1 10 Hz–10 MHz y E2 1 Hz–20 MHz. Cin a 1 MHz,
Zin a 100 Hz. Planitud nominal C4/C9 10 Hz–2 MHz; ajuste/C6 10 kHz–2 MHz,
normalizados a 1 kHz. Las medidas incluyen 100 kHz, 1 MHz y 2 MHz.
La corriente de Vsense retorna a la fuente: −Im(I/V)/(2πf) da Cin positiva.

Búsqueda del trimmer: red RC nodal de la misma topología, diodos linealizados
a 5 V, bisección de la suma de desviaciones extrema positiva/negativa; rejilla
de 0.05 pF. LTspice verifica el punto candidato, ambos vecinos y ambos topes,
y camina por la rejilla hasta mínimo local. La búsqueda usa POS100/CPLDC real.
Los CSV de búsqueda conservan todas esas .meas; los criterios sólo usan .meas.
La incertidumbre ±0.1 pF se aplica después del ajuste como error uniforme,
compartido para la misma muestra en los tres rangos, limitado al recorrido físico.
Se registran tanto ajuste solicitado como valor efectivo; un tope en cualquiera
cuenta. Los casos contra tope no se descartan. CT2F varía al 2 %, CTRIM no al 2 %.

Sonda: 9 MΩ ∥ CTIP, cable 80 pF, sin CCOMP; fuente ±1 V, 1 kHz, 5 ns y 50 Ω.
CTIP minimiza error máximo de 0.1 a 200 µs después del flanco en POS100.
Se busca primero mediante la solución modal RC de la rampa de 5 ns (contactos
cerrados ideales sólo en ese acelerador, circuito LTspice completo con 0.1 Ω), luego
se verifica y refina en LTspice a 0.002 pF con el candidato y ambos vecinos.
CTIP es idéntico en los dos POS de cada caso y rango. La altura es 2·Vref de
una copia DC con los mismos parámetros, incluyendo los diodos no lineales.
Errores a 2,20,200 µs desde el final del flanco; sobreimpulso entre 0 y 400 µs.
Pasos máximos reales ≤2 ns durante los 5 µs después del final del flanco,
forzados por puntos de quiebre PWL de una fuente numérica aislada del circuito.
Fuera de esa ventana, máximo 100 ns. Se leen los tiempos de cada .raw antes de
eliminarlo y se verifica la ventana; resultados en s1b_ejecucion.json. Se usa
Gear con solver Alternate; no hay timeout del proceso LTspice. Los contactos
cerrados conservan 0.1 Ω, sin alterar ningún componente por razones numéricas.
Se contrasta el nominal de ventana con paso global de 2 ns; convergencia contra
1 ns global en el mismo caso compensado. No se modifica el circuito por ello.
MC usa el primer flanco desde equilibrio negativo (DC de LTspice). Se comprueba
en el nominal frente al segundo flanco a 1.5 ms de una cuadrada periódica.

Mismas 200 muestras A en cada rango; B usa otras 200, semilla fija. Piezas
RT1/RT2, RS1/RS2 y CT1/CT2F independientes; CJO compartido entre ambos diodos;
parásitas de cada clase comunes entre contactos. Capacidades de compensación
calculadas con nominales y luego su propia tolerancia; no se recalculan con
parásitas de cada muestra. La selección CEQ de B mantiene el factor de tolerancia
de la pieza: bisección LTspice de la diferencia firmada Cin1−Cin100 a 1 MHz,
15 iteraciones, 1–30 pF nominales, luego E24 más próximo por distancia absoluta.
Trimmer B ajustado con CEQ inicial; se informa también planitud después de E24.
E1 cubre DC, AC y GND en cada caso A/B; GND sólo se informa. E3 de B se mide
antes y después de seleccionar CEQ, ajustando CTIP en POS100 en cada estado.

Simulaciones independientes en procesos LTspice con rutas únicas, mediante
ThreadPoolExecutor de 10 trabajadores por defecto (configurable con --workers).
Cada instancia lleva .options threads=1 para evitar paralelismo anidado;
es una opción del ejecutor, sin cambiar el circuito. Fuente ADI:
https://ez.analog.com/design-tools-and-calculators/ltspice/f/q-a/592257/option-to-limit-the-maximum-number-of-threads
Casos y rangos A comparten el pool; las búsquedas dentro de cada caso son
secuenciales. B espera la elección del rango C6. Un fallo se registra y los
otros casos continúan; no se presentan campañas incompletas como aprobadas.
CSV ordenados por campaña/rango/caso, nunca por orden de finalización. Los .cir
y .log quedan; .raw, .op.raw y .db regenerables se eliminan después de leer el log.
La tabla CRITERIA del ejecutor concentra todos los umbrales. El código de salida
señala errores de simulación/medida, no criterios eléctricos fallidos.

## Dudas y contradicciones sin resolver

1. Dispersión A de Coff/layout supuesta por el auditor, sin caracterización
   de unidades HFD27 o PCB; el MC no demuestra capacidad de producción real.
2. C_SEL_EST cuenta dos COFF_SW. Una de ellas vuelve a SEL a través de CAC,
   no directamente a masa; el circuito explícito se conserva sin corregir el plan.
3. C9 no fija banda de planitud; se usa la banda completa de E2 (10 Hz–2 MHz).
   También se informa 10 kHz–2 MHz. Zin se comprueba tanto en DC como en AC.
4. El contrato no define objetivo/precisión de CTIP, correlaciones ni la aplicación
   de ±0.1 pF. Las elecciones del banco están descritas, no son decisiones de pieza.
5. «En los 200 casos» es una muestra de Monte Carlo, no todos los extremos
   posibles ni una garantía de fabricación. C6 no elige comercialmente un trimmer.
6. Modelo de diodo genérico y buffer ideal: los modelos de fabricante y las
   protecciones de ±100 V/ESD pertenecen a S2, fuera de este encargo.
7. La selección CEQ de B puede mover ligeramente la planitud tras el ajuste
   del trimmer; se informa ambos estados sin reajustar otra pieza por conveniencia.

No se modifica S1, chequeo_claude, STATE.md ni DECISIONS.md.
'''


def main():
    started = time.perf_counter()
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true', help='nominal + 2 muestras/rango; no aceptación de campaña')
    parser.add_argument('--workers', type=int, default=10)
    args = parser.parse_args()
    if args.workers < 1: parser.error('--workers debe ser positivo')
    WORK.mkdir(parents=True, exist_ok=True); RESULT.mkdir(exist_ok=True)
    (RESULT/'s1b_error.json').unlink(missing_ok=True)
    SIMS.clear()
    CASE_ERRORS.clear()
    protected = [p for p in (ROOT/'S1').rglob('*') if p.is_file() and p.suffix != '.raw']
    protected += [ROOT/'comun/ch1_comun.inc', ROOT/'ejecutar_s1.py', ROOT/'ACTA_S1.md',
                  ROOT.parents[2]/'ai-context/STATE.md', ROOT.parents[2]/'ai-context/DECISIONS.md']
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in protected if p.exists()}
    count = 2 if args.smoke else 200
    print(f'S1b: {count} casos por campaña; {args.workers} procesos LTspice', flush=True)
    a1 = simulate(ROOT/'S1b/E1b_zin.cir', ac_net('N', 'nom', 1, 4., {}, e1=True))
    a2 = simulate(ROOT/'S1b/E2b_respuesta.cir', ac_net('N', 'nom', 1, 4., {}))
    for k, v in a1.items():
        if not math.isclose(v, a2[k], rel_tol=2e-5, abs_tol=1e-18): raise RuntimeError('E1/E2 disagreement')
    nominal = ac_rows(a2, 'N', 'nom', 1)
    # S1 clone with ONLY the contractual C_SEL_EST correction, in S1b.
    # Compare evolved trimmer-at-midpoint against the original unsplit CT2.
    refinc = WORK/'reference_s1_corrected.inc'
    original = (ROOT/'comun/ch1_comun.inc').read_text(encoding='utf-8')
    corrected = original.replace('C_SEL_EST=2*CJO+CSEL_PAR+CIN_BUF+COFF_SW',
                                 'C_SEL_EST=2*CJO/(1+5/0.6)**0.3+CSEL_PAR+CIN_BUF+2*COFF_SW')
    write(refinc, corrected)
    refnet = ac_net('N', 'nom', 1, 4., {}).replace(str(ROOT/'comun/ch1_comun_s1b.inc'), str(refinc))
    reference = simulate(WORK/'reference_s1_corrected.cir', refnet)
    reference_changes = []
    for k, v in a2.items():
        change = abs(v-reference[k])/max(abs(v), 1e-30)
        reference_changes.append(dict(measure=k, relative_change=change))
        if change > 1e-8: raise RuntimeError('Midpoint does not reproduce S1 with corrected SEL')
    # At midpoint R2/R3 must reproduce R1: only CT2F/CTRIM split changes.
    equivalence = []
    for rango in (2, 3):
        ac = simulate(WORK/f'midpoint_r{rango}.cir', ac_net('N', 'nom', rango, sum(RANGES[rango])/2, {}))
        rs = ac_rows(ac, 'N', 'nom', rango)
        for base, row in zip(nominal, rs):
            for k in ('zin_ohm', 'cin_pF', 'gain_1k'):
                if k in base:
                    rel = abs(row[k]/base[k]-1)
                    equivalence.append(dict(RANGO=rango, POS=row['POS'], CPL=row['CPL'], metric=k, relative_change=rel))
                    if rel > 1e-8: raise RuntimeError('Midpoint equivalence failed')
    tip, trs, ph = probe_adjust('N', 'nom', 1, 4., {}, CSEL)
    tr = simulate(ROOT/'S1b/E3b_sonda.cir', tran_net('N', 'nom', 1, 4., {}, [tip]))
    trs = tr_rows(tr, 'N', 'nom', 1)
    for r in nominal:
        if r['CPL'] == 'DC': r.update({k: v for k, v in next(t for t in trs if t['POS'] == r['POS']).items() if k not in ('campaign', 'case', 'RANGO', 'POS', 'CPL')})
        r['CTIP_pF'] = tip
    full = simulate(WORK/'global_2ns_validation.cir', tran_net('N', 'nom', 1, 4., {}, [tip], windowed=False))
    full_rows = tr_rows(full, 'N', 'nom', 1)
    guarded_changes = []
    for base, global_row in zip(trs, full_rows):
        for metric in ('overshoot_pct', 'objective_pct', 'error_2us_pct', 'error_20us_pct', 'error_200us_pct'):
            shift = base[metric]-global_row[metric]
            guarded_changes.append(dict(POS=base['POS'], metric=metric, shift_pp=shift))
            if abs(shift) > .005: raise RuntimeError('Fine-window result differs from global 2ns by >0.005pp')
    fine = simulate(WORK/'convergence_1ns.cir', tran_net('N', 'nom', 1, 4., {}, [tip], maxstep='1n', windowed=False))
    fine_rows = tr_rows(fine, 'N', 'nom', 1, maxstep='1n')
    periodic = simulate(WORK/'periodic_second_edge.cir', tran_net('N', 'periodic', 1, 4., {}, [tip], periodic=True))
    periodic_rows = tr_rows(periodic, 'N', 'periodic', 1)
    conv = []; edgecheck = []
    for base, refined, per in zip(trs, fine_rows, periodic_rows):
        keys = ['overshoot_pct', 'objective_pct', 'error_2us_pct', 'error_20us_pct', 'error_200us_pct']
        conv.append(dict(POS=base['POS'], **{'shift_'+k: refined[k]-base[k] for k in keys}))
        edgecheck.append(dict(POS=base['POS'], **{'shift_'+k: per[k]-base[k] for k in keys}))
    if max(abs(v) for r in edgecheck for k, v in r.items() if k.startswith('shift_')) > .05:
        raise RuntimeError('Equilibrium first edge differs from periodic second edge by >0.05 pp')
    print(f'Nominal listo. CTIP={tip:.5f} pF; sobre ×1={trs[0]["overshoot_pct"]:.6f} %', flush=True)
    rng = random.Random(SEED); samples = []
    factors_by_campaign = {}
    for campaign, bounds in (('A', BOUNDS_A), ('B', BOUNDS_B)):
        samplelist = []
        for i in range(count):
            f = {k: rng.uniform(*b) for k, b in bounds.items()}; resolution = rng.uniform(-.1, .1)
            samplelist.append((f, resolution))
            samples.append(dict(campaign=campaign, case=f'c{i:03d}', DTRIM_pF=resolution, **f))
        factors_by_campaign[campaign] = samplelist
    rows = []; th = []; sh = []; selection = []
    def execute(jobs):
        results = {}
        progress = {}
        with futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            # Interleave ranges at submission so all three run concurrently.
            # Keep original indices for the deterministic range/case merge.
            schedule = sorted(enumerate(jobs), key=lambda pair: (pair[1][0], pair[1][1], pair[1][2]))
            pending = {pool.submit(run_case, job): i for i, job in schedule}
            for future in futures.as_completed(pending):
                i = pending[future]; job = jobs[i]
                try:
                    results[i] = future.result()
                except Exception as exc:
                    failure = dict(campaign=job[0], case=f'c{job[1]:03d}', RANGO=job[2], error=str(exc))
                    CASE_ERRORS.append(failure)
                    print(f'ERROR de caso: {failure}', flush=True)
                key = (job[0], job[2]); progress[key] = progress.get(key, 0)+1
                n = progress[key]
                if n % 5 == 0 or n == count:
                    print(f'{key[0]} R{key[1]}: {n}/{count} terminados', flush=True)
        # Merge in submission order, independently of completion order.
        for i in sorted(results):
            rs, trimhistory, probehistory, selecthistory, selections = results[i]
            rows.extend(rs); th.extend(trimhistory); ph.extend(probehistory); sh.extend(selecthistory); selection.extend(selections)
    jobs_a = []
    for rango, limits in RANGES.items():
        ct2f = 20-sum(limits)/2
        if ct2f < 1:
            print(f'R{rango} omitido: CT2F={ct2f} pF', flush=True); continue
        jobs_a.extend(('A', i, rango, f, resolution) for i, (f, resolution) in enumerate(factors_by_campaign['A']))
    execute(jobs_a)
    criteria, ranges, chosen = summary(nominal, conv, rows, selection, count)
    if chosen is not None:
        execute([('B', i, chosen, f, resolution) for i, (f, resolution) in enumerate(factors_by_campaign['B'])])
    else:
        print('Campaña B no ejecutada: ningún rango cumple C6, requisito previo del contrato.', flush=True)
    criteria, ranges, chosen = summary(nominal, conv, rows, selection, count)
    csv_write(RESULT/'s1b_resultados.csv', nominal+rows)
    csv_write(RESULT/'s1b_criterios.csv', criteria)
    csv_write(RESULT/'s1b_mc_parametros.csv', samples)
    csv_write(RESULT/'s1b_trimmer_busqueda.csv', th)
    csv_write(RESULT/'s1b_sonda_busqueda.csv', ph)
    csv_write(RESULT/'s1b_ceq_busqueda.csv', sh)
    csv_write(RESULT/'s1b_ceq_seleccion.csv', selection)
    csv_write(RESULT/'s1b_convergencia.csv', conv)
    csv_write(RESULT/'s1b_flanco_verificacion.csv', edgecheck)
    csv_write(RESULT/'s1b_ventana_verificacion.csv', guarded_changes)
    csv_write(RESULT/'s1b_equivalencia.csv', equivalence)
    csv_write(RESULT/'s1b_referencia_s1.csv', reference_changes)
    csv_write(RESULT/'s1b_trimmer_rangos.csv', ranges)
    # Descriptive distributions, not hidden acceptance criteria.
    distributions = []
    for rango in RANGES:
        g = [r for r in rows if r['campaign'] == 'A' and r['RANGO'] == rango and r['POS'] == 100 and r['CPL'] == 'DC']
        hist, edges = np.histogram([r['CTRIM_set_pF'] for r in g], bins=8, range=RANGES[rango])
        for n, lo, hi in zip(hist, edges[:-1], edges[1:]):
            distributions.append(dict(RANGO=rango, low_pF=lo, high_pF=hi, count=int(n)))
    csv_write(RESULT/'s1b_trimmer_distribucion.csv', distributions)
    for p, expected in hashes.items():
        if hashlib.sha256(Path(p).read_bytes()).hexdigest() != expected: raise RuntimeError(f'Protected file changed: {p}')
    sims = sorted(SIMS, key=lambda x: x['file'])
    errors = sum(bool(s['errors'] or s['returncode']) for s in sims)
    warnings = sum(bool(s['warnings']) for s in sims)
    elapsed = time.perf_counter()-started
    run = dict(seed=SEED, cases_per_campaign=count, smoke=args.smoke, exit_code=int(bool(errors or CASE_ERRORS)),
               workers=args.workers, elapsed_seconds=elapsed,
               case_errors=sorted(CASE_ERRORS, key=lambda r: (r['campaign'], r['RANGO'], r['case'])),
               simulations=sims, errors=errors, warnings=warnings, smallest_C6_range=chosen,
               protected_files_unchanged=len(hashes), CTIP_nominal_pF=tip,
               derived=dict(CJ_POL_pF=CJP*1e12, C_SEL_EST_pF=CSEL*1e12, CEQ_pF=CSEL*1e12,
                            CS_pF=CS*1e12, CB_pF=CB*1e12))
    write(RESULT/'s1b_ejecucion.json', json.dumps(run, indent=2, ensure_ascii=False))
    text = '# Resultados S1b — LTspice\n\n'
    if args.smoke: text += '**SMOKE: 2 muestras, no aceptación de producción.**\n\n'
    text += f'Código de salida: {run["exit_code"]}. Simulaciones: {len(sims)}; error: {errors}; advertencia: {warnings}. Semilla: {SEED}. Casos por campaña: {count}.\n\n'
    text += f'Pool: {args.workers} trabajadores. Tiempo total: {elapsed:.3f} s ({elapsed/60:.3f} min). Casos fallidos: {len(CASE_ERRORS)}.\n\n'
    checkpath = ROOT/'S1b/paralelizacion_verificacion.json'
    if checkpath.exists():
        check = json.loads(checkpath.read_text(encoding='utf-8'))
        text += (f'Verificación de paralelización: smoke de 1 y 10 trabajadores, '
                 f'{check["csv_count"]} CSV idénticos byte a byte; '
                 f'{check["simulations_each"]} simulaciones por variante, sin errores ni advertencias. '
                 f'Tiempos: {check["sequential_seconds"]:.3f} s secuencial y '
                 f'{check["parallel_seconds"]:.3f} s paralelo. Evidencia: '
                 '`S1b/paralelizacion_verificacion.json` y directorios smoke.\n\n')
    if CASE_ERRORS:
        text += '## Casos fallidos (campañas incompletas)\n\n'+table(run['case_errors'], ['campaign', 'RANGO', 'case', 'error'])+'\n\n'
    text += table(criteria, ['criterion', 'RANGO', 'value', 'status'])+'\n\n'
    text += f'Rango mínimo que cumple C6: {"R"+str(chosen) if chosen else "ninguno"}. Esto no selecciona una pieza comercial.\n\n'
    text += '## Trimmer: recorrido y reparto\n\n'+table(ranges, ['RANGO', 'cases', 'stops', 'outside', 'trim_min_pF', 'trim_median_pF', 'trim_max_pF', 'worst_flat_pct'])+'\n\n'
    text += table(distributions, ['RANGO', 'low_pF', 'high_pF', 'count'])+'\n\n'
    text += '## E3b nominal y convergencia\n\n'+table(trs, ['POS', 'step_height_v', 'overshoot_pct', 'error_2us_pct', 'error_20us_pct', 'error_200us_pct'])+'\n\n'
    text += table(conv, list(conv[0]))+'\n\n'
    text += '## Campaña B\n\n'
    if selection:
        before = [s['delta_before_pF'] for s in selection]; after = [s['delta_after_pF'] for s in selection]
        text += f'|ΔCin| antes: {min(before):.6f}…{max(before):.6f} pF; mediana {np.median(before):.6f}. Después de E24: {min(after):.6f}…{max(after):.6f} pF; mediana {np.median(after):.6f}.\n\n'
        bdc = [r for r in rows if r['campaign'] == 'B' and r['CPL'] == 'DC' and r['POS'] == 100]
        initial = [r for r in bdc if r['stage'] == 'final']; final = [r for r in bdc if r['stage'] == 'selected']
        text += f'Topes: {sum(r["at_stop"] for r in initial)}/{len(initial)}. Planitud ÷100 máxima tras ajuste: {max(flat(r, True) for r in initial):.6f} %; tras E24: {max(flat(r, True) for r in final):.6f} %. Sólo informativa.\n\n'
        values = sorted(set(round(s['CEQ_E24_pF'], 8) for s in selection))
        text += table([dict(CEQ_E24_pF=v, count=sum(abs(s['CEQ_E24_pF']-v)<1e-7 for s in selection)) for v in values], ['CEQ_E24_pF', 'count'])+'\n'
    else: text += 'No ejecutada: falta rango que cumpla C6.\n'
    text += '\n## Qué enseña cada prueba\n\nE1b/E2b miden Zin, Cin, ganancia, planitud y corte AC con la estimación SEL corregida; GND sólo se informa en el CSV. E3b comprueba la sonda compensada y la convergencia real del caso compensado. E4A cuantifica el recorrido y los fallos de producción supuesta sin ocultar topes. E4B separa el ajuste del trimmer de la selección E24 de CEQ.\n'
    write(RESULT/'s1b_resumen.md', text)
    write(ROOT/'ACTA_S1b.md', text.replace('# Resultados S1b — LTspice', '# ACTA S1b — entrada pasiva P4b de CH1', 1)+METHOD)
    print(table(criteria, ['criterion', 'RANGO', 'value', 'status']), flush=True)
    print(f'FINAL: exit={run["exit_code"]}; simulations={len(sims)}; errors={errors}; warnings={warnings}; smallest_R={chosen}', flush=True)
    return run['exit_code']


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        RESULT.mkdir(exist_ok=True)
        write(RESULT/'s1b_error.json', json.dumps(dict(error=str(exc), simulations=sorted(SIMS, key=lambda x: x['file'])), indent=2))
        print(f'ERROR: {exc}', flush=True)
        raise SystemExit(1)
