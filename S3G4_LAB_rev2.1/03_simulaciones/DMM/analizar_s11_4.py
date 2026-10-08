"""Consolidate current signed S11.4 records; emit derived findings only."""
import collections, hashlib, json, math
from pathlib import Path
import ejecutar_s11_4 as sim

HERE=Path(__file__).resolve().parent
def main():
    records=[];missing=[]
    for c in sim.cases():
        path=sim.JOBS/(sim.name(c)+'.json')
        if not path.exists():missing.append(sim.name(c));continue
        r=json.loads(path.read_text(encoding='utf-8'))
        content=sim.deck(c)
        digest=hashlib.sha256((content+Path(sim.__file__).read_text(encoding='utf-8')+(HERE/'comun/bss126_s11_2.inc').read_text()+''.join(sim.old.read_text(sim.MODELS/x) for x in ('OPA2188/OPAx188.LIB','74HC4051/hc_tnomi.cir'))).encode()).hexdigest()
        if r.get('signature')!=digest:missing.append(sim.name(c)+' STALE');continue
        if c['stimulus']=='dut':
            r['source_at_dut_A']=r.get('source_final_A')
            r['dut_at_dut_A']=r.get('dut_final_A')
            if c['amplitude']!=.65:
                r.pop('source_at_065_A',None);r.pop('dut_at_065_A',None)
        # The inherited parser extracts V(gstate)=.5, not the following AT.
        # Keep the parsed state under its physical unit, and raw crossing
        # under gdt_ignition_s. Do not present .5 as an ignition time.
        if 'gdt_on' in r:r['gdt_on_state']=r.pop('gdt_on')
        records.append(r)
    valid=[r for r in records if r['status']=='ok' and r.get('raw_complete')]
    def group(q):return [r for r in valid if r['q']==q]
    def envelope(rows,key,minimum=False):
        pairs=[(r[key],r['id']) for r in rows if isinstance(r.get(key),(int,float)) and math.isfinite(r[key])]
        if not pairs:return {'value':None,'case':None}
        value,case=(min if minimum else max)(pairs)
        return dict(value=value,case=case)
    findings=dict(expected=len(sim.cases()),valid=len(valid),missing=missing,counts={q:dict(collections.Counter(r['status'] for r in records if r['q']==q)) for q in ('T2','T1','T3','T4','T5')})
    findings['esd']=[]
    for dc in (420,780):
        for amp in (4000,8000):
            for mode in ('v','ohm'):
                rows=[r for r in group('T2') if r['gdc']==dc and abs(r['amplitude'])==amp and r['mode']==mode]
                e=dict(gdc=dc,amplitude_abs=amp,mode=mode,cases=len(rows))
                for key in ('gdt_voltage_peak_V','gdt_arc_peak_A','gdt_arc_E_J','gdt_state_max','relay_drop_max_V','rprot1_V','rdiv1_V','rc1_V','rohm1_V','cc1_voltage_peak_V','xh0_clamp_peak_A','xh1_clamp_peak_A','xh0_sustained20ns_A','xh1_sustained20ns_A','span_max'):
                    e[key]=envelope(rows,key)
                e['ignited']=sum(r.get('gdt_ignition_s') is not None for r in rows)
                e['first_ignition_s']=envelope(rows,'gdt_ignition_s',True)
                e['last_ignition_s']=envelope(rows,'gdt_ignition_s')
                findings['esd'].append(e)
    findings['diode']=[{k:r.get(k) for k in ('id','mode','rail','source','amplitude','compliance99_V','dut_compliance99_V','source_at_065_A','dut_at_065_A','dut_at_35V_A','dut_final_A','source_at_dut_A','dut_at_dut_A')} for r in group('T1')]
    findings['long']={q:{key:envelope(group(q),key) for key in ('gdt_voltage_peak_V','gdt_arc_peak_A','gdt_state_max','span_max','rprot1_P_period_W','rprot1_E_sim_J','rprot1_E_extrap_J','rprot1_E10_J','rohm1_V','rohm1_P_period_W','rohm1_E_sim_J','rohm1_E_extrap_J','rohm1_E10_J','btvs_P_period_W','x0_recovery_s','n2_recovery_s','x0_end_drift_V','n2_end_drift_V')} for q in ('T3','T4','T5')}
    contacts=[r for r in group('T2') if abs(r['amplitude'])==4000]
    d4=max((r.get(k,0) for r in contacts for k in ('xh0_clamp_peak_A','xh1_clamp_peak_A')),default=math.nan)
    d5=envelope([r for r in group('T1') if r['mode']=='diode' and r['source']==.0001 and r['rail']==.98],'compliance99_V',True)
    d6=max((r.get(k,0) for r in group('T5') for k in ('x0_recovery_s','n2_recovery_s')),default=math.nan)
    d7=envelope(group('T2')+group('T3')+group('T4'),'span_max')
    relay=envelope([r for r in group('T2') if r['mode']=='v'],'relay_drop_max_V')
    mains=envelope(group('T3'),'gdt_voltage_peak_V')
    criteria=[
        dict(criterion='D1',result='NO CERTIFICADO / supera tensión de trabajo',value=envelope(group('T2'),'rohm1_V')['value'],limit=200,unit='V Rohm,80% de250V trabajo',reason='Pulso supera margen de tensión de trabajo; sin rating de pulso no demuestra destrucción ni supervivencia. Faltan ratings por pieza/energía'),
        dict(criterion='D2',result='PARCIAL / NO CERTIFICADO',value=relay['value'],limit=1200,unit='V relé abierto',reason='Relé contra 1500V pulso p6; faltan tensiones de sobrecarga garantizadas de cada1206'),
        dict(criterion='D3',result='CUMPLE EN MODELO' if mains['value'] is not None and mains['value']<=336 and all(r['gdt_state_max']<.5 for r in group('T3')) else 'NO CUMPLE',value=mains['value'],limit=336,unit='V GDT',reason='80% de420V; verificar ausencia de corriente de arco'),
        dict(criterion='D4',result='CUMPLE EN MODELO' if d4<=.01 else 'NO CUMPLE',value=d4,limit=.01,unit='A clamp X0/X1 contacto',reason='Pico bruto, sin descartar muestras;máximo absoluto20mA HC4051 p5'),
        dict(criterion='D5',result='CUMPLE EN MODELO' if d5['value'] is not None and d5['value']>=3.5 else 'NO CUMPLE',value=d5['value'],limit=3.5,unit='V compliance fuente99%',reason='100uA,riel-2%; corriente DUT informada aparte'),
        dict(criterion='D6',result=('CUMPLE EN MODELO' if d6<=1 and len(group('T5'))==9 else 'NO ACREDITADO EN VENTANA' if len(group('T5'))==9 else 'SIN COBERTURA'),value=('>2, censurado' if d6>=2 else d6),limit=1,unit='s recuperación',reason='Seis N2 apagados siguen derivando a2s;100uV respecto a media final no es referencia estacionaria. No presentar el extremo como tiempo de recuperación'),
        dict(criterion='D7',result='CUMPLE EN MODELO' if d7['value'] is not None and d7['value']<=11 else 'NO CUMPLE',value=d7['value'],limit=11,unit='V entre rieles',reason='T2–T4; zener aproximado')]
    findings['criteria']=criteria
    sim.writecsv(sim.RESULTS/'s11_4_campaign_audited.csv',records)
    sim.writecsv(sim.RESULTS/'s11_4_criteria.csv',criteria)
    sim.writecsv(sim.RESULTS/'s11_4_diode.csv',findings['diode'])
    sim.writecsv(sim.RESULTS/'s11_4_esd.csv',[{k:(v['value'] if isinstance(v,dict) else v) for k,v in e.items()} for e in findings['esd']])
    stresses=[]
    for r in valid:
        for key in r:
            if key.endswith('_E_sim_J'):
                part=key.removesuffix('_E_sim_J')
                stresses.append(dict(case=r['id'],test=r['q'],part=part,voltage_V=r.get(part+'_V'),energy_sim_J=r[key],energy_extrap_J=r.get(part+'_E_extrap_J'),energy10_J=r.get(part+'_E10_J'),power_period_W=r.get(part+'_P_period_W'),power_avg_sim_W=r.get(part+'_Pavg_W'),power_peak_W=r.get(part+'_Ppeak_W')))
        for part in ('cc1','cc2','cc3','cdiv4','cdiv5'):
            stresses.append(dict(case=r['id'],test=r['q'],part=part,voltage_V=r.get(part+'_voltage_peak_V')))
        stresses.append(dict(case=r['id'],test=r['q'],part='gdt_arc',voltage_V=r.get('gdt_voltage_peak_V'),energy_sim_J=r.get('gdt_arc_E_J')))
        stresses.append(dict(case=r['id'],test=r['q'],part='relay',voltage_V=r.get('relay_drop_max_V')))
        stresses.append(dict(case=r['id'],test=r['q'],part='bss84',voltage_V=r.get('bss84_vds_peak_V')))
    sim.writecsv(sim.RESULTS/'s11_4_stresses.csv',stresses)
    (sim.RESULTS/'s11_4_findings.json').write_text(json.dumps(findings,indent=2),encoding='utf-8')
    print(json.dumps(dict(expected=findings['expected'],valid=findings['valid'],missing=len(missing),counts=findings['counts'],criteria=criteria),ensure_ascii=False))

if __name__=='__main__':main()
