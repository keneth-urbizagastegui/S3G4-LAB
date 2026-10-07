"""Validate the provisional PTC's one available timing point, not a curve fit."""
import json, math, subprocess, time
from pathlib import Path
import ejecutar_s11_1 as s

def main():
    func=next(x for x in (s.HERE/'comun/dmm_bloque1.inc').read_text().splitlines() if x.startswith('.func rptc'))
    p=s.JOBS/'P0_ptc_calibracion_1A.cir'
    prefix='p0_t25_borne_ptc_cal_modo_1a_rele_na_rs_na_rieles_na_apertura_na'
    p.write_text('\n'.join([
        '* P0 calibration; the datasheet has NO time/current curve for this part.',func,
        'Ical 0 pin 1', 'Bptc pin 0 I=V(pin)/rptc(V(theta))',
        f'Cthermal theta 0 {s.E:.15g} IC=0',f'Rthermal theta 0 {1/s.G:.15g}',
        'Bheat 0 theta I=V(pin)',
        '.options threads=1 solver=alt method=gear plotwinsize=0 reltol=.001', '.temp 25',
        '.tran 0 1.001 0 100u uic', '.save V(theta) V(pin)',
        f'.meas tran {prefix}__trip WHEN V(theta)=1 RISE=1', '.end','']),encoding='utf-8')
    t=time.perf_counter(); proc=subprocess.Popen([str(s.LT),'-b',str(p)])
    try: proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True)
    vals,log=s.parse_log(p.with_suffix('.log'))
    result=dict(Rcold_contract_ohm=35,Rcold_datasheet_ohm=50,Rcold_datasheet_tolerance=.2,
        Ecrit_J=s.E,G_W=s.G,tau_s=s.E/s.G,Rhot_assumed_ohm=1e6,
        theta_growth_start=1,theta_growth_end=1.4,
        target_trip_1A_s=1,ltspice_trip_1A_s=vals.get('trip'),
        elapsed_s=time.perf_counter()-t,source='ptctl.pdf p.1; 3 technical pages, no timing or R(T) curve',
        unique_physical_fit=False,thermal_mass_identified=False,
        caveat='140mA is treated as an asymptotic threshold, not its guaranteed finite tripping current. Hot resistance, growth interval and cooling are unverified assumptions.')
    result['relative_timing_error']=None if vals.get('trip') is None else abs(vals['trip']-1)
    (s.RESULTS/'s11_1_modelo_ptc.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)

if __name__=='__main__': main()
