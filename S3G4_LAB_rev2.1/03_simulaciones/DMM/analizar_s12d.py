"""Derive S12d calibrated metrics, compact summary and integrity evidence."""
import csv,json,hashlib,re
from pathlib import Path
import ejecutar_s12d as m

def main():
    rows=[json.loads((m.JOBS/(c['q'].lower()+'_'+hashlib.sha256(m.ident(c).encode()).hexdigest()[:20]+'.json')).read_text(encoding='utf-8')) for c in m.cases()]
    valid=[r for r in rows if r['status']=='ok']; dc=[]
    for fs,sel,g,lsb in m.RANGES:
        for sign in (-1,1):
            group=[r for r in valid if r['q']=='E2' and r['sel']==sel and r['gain']==g and r['leaksign']==sign]
            cal=next((r for r in group if r['temp']==23),None)
            if cal is None:continue
            for r in group:
                if r['temp']==23:continue
                dc.append(dict(range_V=fs,temp_C=r['temp'],leaksign=sign,offset_counts=(r['offset_V']-cal['offset_V'])/(cal['slope']*lsb),gain_drift_ppm=(r['slope']/cal['slope']-1)*1e6,fit_residual_V=r['DC_fit_residual_V']))
    m.writecsv(m.RESULTS/'s12d_dc_calibrado.csv',dc)
    budget=m.dc_budget()
    e3=[r for r in valid if r['q']=='E3'];dc3=[r for r in e3 if 'error_at_wait_counts' in r];ac3=[r for r in e3 if 'ac_error_after_wait_counts' in r]
    e5=[r for r in valid if r['q']=='E5'];e8=[r for r in valid if r['q']=='E8']
    def maximum(rs,k):return max((abs(r[k]) for r in rs if k in r),default=None)
    summary=dict(total=len(rows),valid=len(valid),groups={q:sum(r['q']==q for r in rows) for q in m.PRIORITY},
        E2=dict(spice_offset_counts=maximum(dc,'offset_counts'),spice_gain_ppm=maximum(dc,'gain_drift_ppm'),budgets=budget,calibrated=dc),
        E3=dict(dc_wait_counts=maximum(dc3,'error_at_wait_counts'),settling_counts=maximum(dc3,'settling_error_counts'),ac_wait_counts=maximum(ac3,'ac_error_after_wait_counts'),mux_peak_V=maximum(e3,'mux_channel_peak_V'),continuous_A=max(maximum(e3,f'buffer{i}_continuous_clamp_A') or 0 for i in (0,2)),rail_failures=sum(not r['all_channels_rail_pass'] for r in e3),continuous_failures=sum(not r['continuous_clamp_pass'] for r in e3),accuracy_failures=sum(not r['one_count_pass'] for r in dc3+ac3),dc_cases=len(dc3),ac_cases=len(ac3)),
        E5=dict(min_pm_deg=min((r['pm_deg'] for r in e5),default=None),cases=[{k:r[k] for k in ('gain','tmux','pm_deg','unity_hz')} for r in e5]),
        E8=dict(max_clamp_A=max(maximum(e8,f'buffer{i}_clamp_peak_A') or 0 for i in (0,2)),failures=sum(not r['input_current_pass'] for r in e8)))
    for name,pred in [('50V',lambda r:r['kind']=='stress50'),('4kV',lambda r:r['kind']=='protection' and abs(r['amp'])==4000),('8kV',lambda r:r['kind']=='protection' and abs(r['amp'])==8000),('red',lambda r:r['kind']=='protection' and abs(r['amp']) in (230,253))]:
        subset=[r for r in e8 if pred(r)];summary['E8'][name]=dict(cases=len(subset),clamp_A=max(maximum(subset,f'buffer{i}_clamp_peak_A') or 0 for i in (0,2)))
    integrity=[]
    for c,r in zip(m.cases(),rows):
        p=m.JOBS/(r['id']+'.cir');content=m.deck(c);saved=p.read_text(encoding='utf-8')
        names=re.findall(r'(?im)^\.meas\s+\S+\s+(\S+)',saved)
        integrity.append(dict(id=r['id'],exact_deck=saved==content,signature=r['signature']==m.signature(content),meas_state=all(n.startswith(m.ident(c)+'__') for n in names),meas_count=len(names)))
    summary['integrity']=dict(cases=len(integrity),exact_decks=sum(r['exact_deck'] for r in integrity),signatures=sum(r['signature'] for r in integrity),meas_state=sum(r['meas_state'] for r in integrity))
    m.writecsv(m.RESULTS/'s12d_integridad.csv',integrity)
    (m.RESULTS/'s12d_resumen.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    compact={k:v for k,v in summary.items() if k!='E2'};compact['E2']={k:v for k,v in summary['E2'].items() if k not in ('budgets','calibrated')}
    print(json.dumps(compact,indent=2))
    return int(len(valid)!=len(rows) or any(not all(r[k] for k in ('exact_deck','signature','meas_state')) for r in integrity))

if __name__=='__main__':raise SystemExit(main())
