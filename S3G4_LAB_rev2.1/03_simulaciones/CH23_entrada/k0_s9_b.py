"""S9-B gate: separate evidence, never overwrite original K0 or A results."""
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import argparse, json, time, re, hashlib
from concurrent.futures import ThreadPoolExecutor
import numpy as np
import ejecutar_s9 as s9
ROOT = Path(__file__).resolve().parent
MODEL = ROOT/'comun/lm6172_hoja.lib'
WORK = ROOT/'S9/B_hoja/K0'

def run(item):
    name, mode, gain, vin, rail = item
    ident = f's9b_k0_{name}_g{gain}_vin{s9.old.s4.number(vin)}_rail{rail}'
    p = WORK/(ident+'.cir')
    feedback = ['RFB OUT IM 900','RG IM 0 100'] if gain==10 else ['VFB OUT IM 0']
    deck = '\n'.join([f'* {ident}',f'.include "{MODEL}"',
        '.options gmin=1e-16 numdgt=15 plotwinsize=0 threads=1',
        f'VP VP 0 {rail}',f'VN VN 0 {-rail}',f'VI IN 0 {vin} AC 1',
        'VIP IN IP 0','VIM IM IMR 0','XLM IP IMR VP VN OUT LM6172/NS',
        'RL OUT 0 1k']+feedback+(
        ['.op','.save V(OUT) I(VP) I(VN) I(VIP) I(VIM)'] if mode=='op' else
        ['.ac dec 300 1 1G','.save V(OUT) V(IN)'] if mode=='ac' else
        ['.noise V(OUT) VI dec 300 1 10Meg'])+['.end'])+'\n'
    if mode=='noise_current':
        deck=deck.replace('VIP IN IP 0','RTEST IN INR 100k noiseless\nVIP INR IP 0')
    if mode=='noise_current_minus':
        deck=deck.replace('VIM IM IMR 0','RTEST IM IMT 100k noiseless\nVIM IMT IMR 0')
    s9.write(p,deck)
    start=time.perf_counter()
    proc=s9.sb.run_lt(p,WORK,120)
    if proc.returncode: raise RuntimeError(ident+' LT exit '+str(proc.returncode))
    raw=s9.old.s4.s3.raw_read(p.with_suffix('.raw'))
    row=dict(id=ident,mode=mode,gain=gain,vin=vin,rail=rail,returncode=proc.returncode,seconds=time.perf_counter()-start)
    if mode=='op':
        row.update(out_V=float(raw['v(out)'][0]),ip_A=float(raw['i(vip)'][0]),im_A=float(raw['i(vim)'][0]),supply_plus_A=float(-raw['i(vp)'][0]),supply_minus_A=float(raw['i(vn)'][0]))
    elif mode=='ac':
        f=raw['frequency'];h=raw['v(out)']/raw['v(in)'];db=20*np.log10(abs(h/h[0]));ix=np.flatnonzero(db<=-3)[0]
        row.update(gain_dc=float(h[0].real),minus3_Hz=float(np.exp(np.interp(-3,db[ix-1:ix+1][::-1],np.log(f[ix-1:ix+1])[::-1]))),peak_db=float(db.max()))
    else:
        f=raw['frequency'];key=next(k for k in raw if 'inoise' in k and 'total' not in k);en=raw[key].real*1e9;mask=(f>=1e4)&(f<=1e6)
        row.update(en10k_nV=float(np.interp(1e4,f,en)),en100k_nV=float(np.interp(1e5,f,en)),en1m_nV=float(np.interp(1e6,f,en)),en_band_min_nV=float(en[mask].min()),en_band_max_nV=float(en[mask].max()))
    return row

def main():
    WORK.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    jobs=[(f'op{i}','op',1,v,r) for i,(v,r) in enumerate([(0,4.9),(.1,4.9),(-.1,4.9),(4,5),(-4,5)])]+[('ac','ac',g,0,4.9) for g in [1,10]]+[('noise','noise',1,0,4.9),('noise_current','noise_current',1,0,4.9),('noise_current_minus','noise_current_minus',1,0,4.9)]
    jobs += [('swing_nominal_plus','op',1,4,4.9),('swing_nominal_minus','op',1,-4,4.9)]
    with ThreadPoolExecutor(max_workers=10) as pool: rows=list(pool.map(run,jobs))
    op=rows[0];follow=rows[5];ten=rows[6];noise=rows[7]
    # Input-referred noise with a 100k noiseless source impedance isolates in.
    # Same unity follower/loading: subtract the baseline voltage noise in quadrature.
    in_pA=float(np.sqrt(rows[8]['en10k_nV']**2-noise['en10k_nV']**2)*1e-9/1e5*1e12)
    im_pA=float(np.sqrt(rows[9]['en10k_nV']**2-noise['en10k_nV']**2)*1e-9/1e5*1e12)
    checks=dict(gain10_bandwidth=5.95e6<=ten['minus3_Hz']<=8.05e6,
        follower_bandwidth=100e6<=follow['minus3_Hz']<=160e6,
        follower_peak=follow['peak_db']<=3,
        supply=all(2.2e-3*.85<=op[k]<=2.2e-3*1.15 for k in ['supply_plus_A','supply_minus_A']),
        noise=9.9<=noise['en_band_min_nV'] and noise['en_band_max_nV']<=12.1,
        current_noise=.9<=in_pA<=1.1 and .9<=im_pA<=1.1,
        offset=abs(op['out_V'])<=.003,
        bias=max(abs(op['ip_A']),abs(op['im_A']))<=2.5e-6,
        swing=rows[3]['out_V']>=3.1 and rows[4]['out_V']<=-3.1,
        swing_nominal=rows[10]['out_V']>=3.1 and rows[11]['out_V']<=-3.1)
    meta=dict(passed=all(checks.values()),checks=checks,simulations=len(rows),seconds=time.perf_counter()-start,rows=rows,model_sha256=hashlib.sha256(MODEL.read_bytes()).hexdigest(),total_current_noise_target_pA=1.,external_current_noise_pA=float(np.sqrt(16465.619974/27454.902706102806)),measured_current_noise_pA=in_pA,measured_minus_current_noise_pA=im_pA,temperature='LTspice run25C, tnom27C; sheet limits at25C')
    s9.write(ROOT/'resultados/s9b_puerta_k0.json',json.dumps(meta,indent=2))
    s9.csv_write(ROOT/'resultados/s9b_k0.csv',rows,['id','mode','gain','vin','rail','returncode','seconds','out_V','ip_A','im_A','supply_plus_A','supply_minus_A','gain_dc','minus3_Hz','peak_db','en10k_nV','en100k_nV','en1m_nV','en_band_min_nV','en_band_max_nV'])
    print(json.dumps(meta,indent=2))
    return int(not meta['passed'])
if __name__=='__main__': raise SystemExit(main())
