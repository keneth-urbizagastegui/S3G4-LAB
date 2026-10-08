import subprocess, re, os, sys, itertools
LT = r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe'
def deck(sel, C2, C3, Q, Ccom, tag):
    vin = {0: 0.2, 1: 20, 2: 50}[sel]; vf = {0: vin, 1: vin*0.1, 2: vin*0.01}[sel]
    thr = 5e-6 if sel == 0 else 50e-6          # 0.5 cuenta: 200 mV: 10 uV/cuenta -> 5 uV; en X1/X2: 0.5 cuenta = 50 uV en la toma
    sw = {0: 'S0 x0p c0 ctl 0 SW\nR0 c0 com 100\n', 1: 'S1 t1 c1 ctl 0 SW\nR1 c1 com 100\n', 2: 'S2 t2 com ctl 0 SW\n'}[sel]
    return f"""* asiento del autocero sel={sel} C2={C2} C3={C3} Qinj={Q} Ccom={Ccom}
.param Vin={vin}
Vin in 0 {vin}
Rp in x0p 99k
Cx0 x0p 0 12p
Rt1 in a 3Meg
Ct1 in ma 100p
Rd1 ma a 3.3k
Rt2 a b 3Meg
Ct2 a mb 100p
Rd2 mb b 3.3k
Rt3 b t1 3Meg
Ct3 b mc 100p
Rd3 mc t1 3.3k
R2 t1 t2 900k
C2 t1 t2 {C2}
R3 t2 0 100k
C3 t2 0 {C3}
Cp1 t1 0 12p
Cp2 t2 0 8p
Vc ctl 0 PULSE(0 1 20u 10n 10n 1 2)
.model SW SW(Ron=100 Roff=1G Vt=0.5 Vh=0.1)
{sw}Ccom com 0 {Ccom}
Iq 0 com PULSE(0 {Q/10e-9 if Q else 0} 20u 1n 1n 10n 2)
.ic V(com)=0
.tran 0 15m 0 1u
.meas tran tset WHEN abs(v(com)-{vf})={thr} FALL=LAST
.meas tran vmin0 MIN v(com) from 20u to 40u
.meas tran dv0 FIND v(com) at 20.5u
.end
"""
rows = []
for sel, (C2, C3), Q in itertools.product((0, 1, 2), (('330p', '3.0n'), ('270p', '2.7n')), (0, 5e-12)):
    if sel == 0 and C2 == '270p': continue
    tag = f's{sel}_{C2}_{int(Q*1e12)}'
    open(f'st_{tag}.cir', 'w').write(deck(sel, C2, C3, Q, '37.5p', tag))
    subprocess.run([LT, '-b', f'st_{tag}.cir'], cwd=os.path.dirname(os.path.abspath(__file__)), timeout=120)
    log = open(f'st_{tag}.log', errors='ignore').read()
    m = re.search(r'tset:.*?AT\s+([-0-9.eE+]+)', log)
    t = float(m.group(1))-20e-6 if m else None
    rows.append((sel, C2, C3, Q, t)); print(sel, C2, C3, Q, t if t is None else f'{t*1e3:.2f} ms')
