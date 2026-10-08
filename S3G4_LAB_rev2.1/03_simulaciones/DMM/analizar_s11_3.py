"""Derived tables from completed campaign JSON; no prior artifacts modified."""
from pathlib import Path
import collections, json, math
import ejecutar_s11_3 as sim
R=sim.RESULTS

def main():
    records=[]
    for c in sim.cases():
        p=sim.JOBS/(sim.name(c)+'.json')
        if p.exists():records.append(json.loads(p.read_text()))
    good=[r for r in records if r['status']=='ok'];out={}
    sim.writecsv(R/'s11_3_campaign_audited.csv',sorted(records,key=lambda r:r['id']))
    def maximum(rows,key):
        vals=[r[key] for r in rows if isinstance(r.get(key),(int,float)) and math.isfinite(r[key])]
        return max(vals) if vals else None
    def minimum(rows,key):
        vals=[r[key] for r in rows if isinstance(r.get(key),(int,float)) and math.isfinite(r[key])]
        return min(vals) if vals else None
    energy=[]
    for r in good:
        for key,e in r.items():
            if key.endswith('_E_sim_J'):
                part=key.removesuffix('_E_sim_J')
                energy.append(dict(id=r['id'],q=r['q'],part=part,simulated_s=r['observed_stop_s'],E_sim_J=e,P_period_W=r.get(part+'_P_period_W'),E_extrap_J=r.get(part+'_E_extrap_J'),E10_J=r.get(part+'_E10_J')))
    sim.writecsv(R/'s11_3_energias.csv',energy)
    stress=[]
    for q in ('R3','R6','R2','R5','R1','R7','R3b'):
        rows=[r for r in good if r['q']==q]
        allrows=[r for r in records if r['q']==q]
        group={'cases':len(allrows),'status':dict(collections.Counter(r['status'] for r in allrows))}
        if rows:
            erows=[e for e in energy if e['q']==q]
            top=max(erows,key=lambda x:x.get('E10_J') if x.get('E10_J') is not None else x['E_sim_J'])
            group['largest_energy']=top
        for key in ('span_max','rohm1_P_period_W','rohm2_P_period_W','btvs_P_period_W','rprot1_Pavg_W','rohm1_V','rohm1_E_sim_J','rshunt_E_sim_J','btvs_E_sim_J','xh0_clamp_peak_A','xh1_clamp_peak_A','xh2_clamp_peak_A','xopi_clamp_peak_A','bin_rail_excess','hx0_rail_excess','hx1_rail_excess','hx2_rail_excess','relay_drop_max_V','bss84_vds_peak_V','cc1_voltage_peak_V','fuse_open_s','x0_recovery_s','n2_recovery_s','x0_end_drift_V','n2_end_drift_V'):
            group[key]=maximum(rows,key)
        out[q]=group
        if rows:stress.append(dict(q=q,part=group['largest_energy']['part'],id=group['largest_energy']['id'],E_sim_J=group['largest_energy']['E_sim_J'],E10_J=group['largest_energy']['E10_J']))
    sim.writecsv(R/'s11_3_pieza_mas_cargada.csv',stress)
    diode=[]
    for source in (.001,.0001):
        rows=[r for r in good if r['q']=='R1' and r['source']==source and r['mode']=='diode']
        silicon=[r for r in good if r['q']=='R1' and r['source']==source and r['mode']=='silicon']
        diode.append(dict(source_A=source,source_compliance99_min_V=minimum(rows,'compliance99_V'),source_compliance99_max_V=maximum(rows,'compliance99_V'),dut_compliance99_min_V=minimum(rows,'dut_compliance99_V'),dut_compliance99_max_V=maximum(rows,'dut_compliance99_V'),silicon_source_min_A=minimum(silicon,'source_at_065_A'),silicon_source_max_A=maximum(silicon,'source_at_065_A'),silicon_dut_min_A=minimum(silicon,'dut_at_065_A'),silicon_dut_max_A=maximum(silicon,'dut_at_065_A'),dut_at35_min_A=minimum(rows,'dut_at_35V_A'),dut_at35_max_A=maximum(rows,'dut_at_35V_A')))
    out['diode']=diode;sim.writecsv(R/'s11_3_diodo.csv',diode)
    leak=[]
    for source in (.2e-6,1e-6):
        rows=[r for r in good if r['q']=='R1' and r['mode']=='leak' and r['source']==source]
        leak.append(dict(source_A=source,tvs_leak_min_A=minimum(rows,'tvs_final_A'),tvs_leak_max_A=maximum(rows,'tvs_final_A'),tvs_leak_max_ppm=(maximum(rows,'tvs_final_A') or 0)/source*1e6,bav_leak_max_A=maximum(rows,'bav_leak_A'),n1_min_V=minimum(rows,'n1_final_V'),n1_max_V=maximum(rows,'n1_final_V'),n2_min_V=minimum(rows,'n2_final_V'),n2_max_V=maximum(rows,'n2_final_V')))
    out['leak']=leak;sim.writecsv(R/'s11_3_fugas.csv',leak)
    bridge=[]
    for grid in (.5,1,2):
        for arc in (1,2,3):
            rows=[r for r in good if r['q']=='R5' and r['grid']==grid and r['arc']==arc]
            bridge.append(dict(grid_ohm=grid,arc=arc,peak_A=max((maximum(rows,f'dbr{i}_peak_A') or 0 for i in range(1,5))),i2t_A2s=max((maximum(rows,f'dbr{i}_i2t_A2s') or 0 for i in range(1,5))),shunt_J=maximum(rows,'rshunt_E_sim_J'),open_min_s=minimum(rows,'fuse_open_s'),open_max_s=maximum(rows,'fuse_open_s'),bin_max_V=maximum(rows,'bin_max'),bin_excess_V=maximum(rows,'bin_rail_excess')))
    out['bridge']=bridge;sim.writecsv(R/'s11_3_borne_a.csv',bridge)
    esd=[]
    for rx in (1e-6,100):
        for amp in (4000,8000):
            for mode in ('v','ohm','a'):
                rows=[r for r in good if r['q']=='R6' and r['rx0']==rx and abs(r['amplitude'])==amp and r['mode']==mode]
                esd.append(dict(rx0_rx2_ohm=rx,abs_amplitude_V=amp,mode=mode,span_V=maximum(rows,'span_max'),hc0_A=maximum(rows,'xh0_clamp_peak_A'),hc1_A=maximum(rows,'xh1_clamp_peak_A'),hc2_A=maximum(rows,'xh2_clamp_peak_A'),opa_A=maximum(rows,'xopi_clamp_peak_A'),ohm1_voltage_V=maximum(rows,'rohm1_V'),ohm1_energy_J=maximum(rows,'rohm1_E_sim_J'),tvs_energy_J=maximum(rows,'btvs_E_sim_J'),hc0_excess_V=maximum(rows,'hx0_rail_excess'),hc1_excess_V=maximum(rows,'hx1_rail_excess')))
    out['esd']=esd;sim.writecsv(R/'s11_3_esd.csv',esd)
    out['R3b']['first_over1W_min_s']=minimum([r for r in good if r['q']=='R3b'],'rohm1_first_over_1W_s')
    out['R3b']['rohm1_ppeak_W']=maximum([r for r in good if r['q']=='R3b'],'rohm1_Ppeak_W')
    out['meas_max_difference_J']=max(abs(r[p+'_meas_raw_difference_J']) for r in good for p in ('rohm1','btvs') if r.get(p+'_meas_raw_difference_J') is not None)
    out['coverage']={'expected':len(sim.cases()),'observed':len(records),'good':len(good)}
    out['capacitor_esd']=[dict(amplitude_V=amp,cc1_peak_V=maximum([r for r in good if r['q']=='R6' and abs(r['amplitude'])==amp],'cc1_voltage_peak_V')) for amp in (4000,8000)]
    r5=[r for r in good if r['q']=='R5']
    out['fuse']={'identified_openings':sum(r.get('fuse_open_s') is not None for r in r5),'cases':len(r5),'max_final_current_A':maximum(r5,'fuse_final_A'),'max_absolute_final_current_A':max(abs(r.get('fuse_final_A',0)) for r in r5)}
    criteria=[dict(criterion='C1',status='FALLA / faltan ratings',value=maximum([r for r in good if r['q']=='R6'],'cc1_voltage_peak_V'),unit='V',limit=504,reason='C0G 100p/630V; ademas rohm supera margen supuesto 0.5W'),dict(criterion='C2',status='PASA modelo',value=max(out[q]['span_max'] or 0 for q in ('R2','R3','R6')),unit='V',limit=11,reason='Zener aproximado sin hoja'),dict(criterion='C3',status='FALLA',value=out['R6']['xh0_clamp_peak_A'],unit='A',limit=.01,reason='Referencia; variante RX0/RX2=100 deja X1 11.832mA a8kV'),dict(criterion='C4',status='NO CERTIFICADO',value=out['R3']['rohm1_P_period_W'],unit='W',limit=.5,reason='Margen 50% supuesto1W no cierra; no modelo destructivo ni MPN'),dict(criterion='C5',status='INFORMATIVO',reason='Modelo fuga TVS lineal a12V; sin garantia a4V'),dict(criterion='C6',status='FALLA',value=diode[1]['source_compliance99_min_V'],unit='V',limit=3.5,reason='A1mA se informa corriente real'),dict(criterion='C7',status='PARCIAL / NO CERTIFICADO',value=out['R7']['x0_recovery_s'],unit='s',limit=1,reason='9ok y9timeout; proxy una cuenta100uV'),dict(criterion='C8',status='PASA modelo',value=max(row['i2t_A2s'] for row in bridge),unit='A2s',limit=83,reason='166A2s de hoja; sin comparar IFSM8.3ms con pulso corto')]
    out['criteria']=criteria;sim.writecsv(R/'s11_3_criterios.csv',criteria)
    attempts=[json.loads(line) for line in (R/'s11_3_attempts.jsonl').read_text().splitlines()]
    out['attempts']={'total':len(attempts),'status':dict(collections.Counter(r['status'] for r in attempts))}
    (R/'s11_3_hallazgos.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False))

if __name__=='__main__':main()
