"""Derive compact summaries and per-piece impulse records from S12b CSV only.
No LTspice launch or writes to preceding campaigns. Values are calculated.
"""
import csv,json
from pathlib import Path
import numpy as np
import ejecutar_s12b as s

def main():
    s.dc_budget() # includes X1-buffer input leakage coupling into unbuffered X2
    p=s.RESULTS/'s12b_campaign.csv'
    rows=list(csv.DictReader(p.open(encoding='utf-8-sig',newline='')))
    def f(r,k):return float(r[k]) if r.get(k) else None
    def group(q):return [r for r in rows if r['q']==q and r['status']=='ok']
    def maxima(rs,k):
        valid=[r for r in rs if r.get(k)]
        return {'value':f(max(valid,key=lambda r:f(r,k)),k),'id':max(valid,key=lambda r:f(r,k))['id']} if valid else None
    result={'counts':{q:len(group(q)) for q in s.PRIORITY},'errors':[{'id':r['id'],'error':r.get('error')} for r in rows if r['status']!='ok']}
    result['E1']={}
    for sigma in (.0005,.001):
        key=f'residual_{sigma}_pct';joint={}
        for fs,sel,g,lsb in s.RANGES:
            rs=[r for r in group('E1') if f(r,'amp')==fs];vals=[f(r,key) for r in rs]
            result['E1'][str(fs)+'_'+str(sigma)]=float(np.percentile(vals,95)) if vals else None
            for r in rs:joint[r['unit']]=max(joint.get(r['unit'],0),f(r,key))
        result['E1']['joint_'+str(sigma)]=float(np.percentile(list(joint.values()),95)) if joint else None
    result['E1']['nominal_X0_droop20_pct']=[f(r,'droop20_pct') for r in group('C2') if f(r,'sel')==0 and f(r,'extra')==0]
    result['E2']=[]
    budget={float(r['range_V']):r for r in csv.DictReader((s.RESULTS/'s12b_dc_budget.csv').open(encoding='utf-8-sig'))}
    for fs,sel,g,lsb in s.RANGES:
        rs=[r for r in group('E2') if f(r,'amp')==fs];base=next((r for r in rs if f(r,'temp')==23),None)
        div=(1,1.01/10.01,.1/10.01)[sel]
        result['E2'].append(dict(range_V=fs,SPICE_offset_counts=max(abs(f(r,'offset_V')-f(base,'offset_V'))/(lsb*div*g) for r in rs) if base else None,SPICE_gain_ppm=max(abs(f(r,'slope')/f(base,'slope')-1)*1e6 for r in rs) if base else None,budget=budget[fs]))
    rs=group('E3');valid=[r for r in rs if r.get('in_range')=='True']
    result['E3']=dict(rail_fail_ids=[r['id'] for r in rs if r.get('unselected_channels_rail_pass')!='True'],all_channels_rail_fail_ids=[r['id'] for r in rs if r.get('all_channels_rail_pass')!='True'],unselected_peak=maxima(rs,'unselected_channels_peak_V'),rail_peaks={n:maxima(rs,n+'_peak_V') for n in ('bx0','bx1','x2')},one_count_fail_ids=[r['id'] for r in valid if r.get('one_count_pass')!='True'],valid_range_cases=len(valid),max_error_at_wait_counts=max(abs(f(r,'error_at_wait_counts')) for r in valid),max_settle_s=maxima(valid,'settle_s'))
    reference=json.loads((s.JOBS/'e3_referencia_paso100ns.json').read_text())
    current={r['id']:r for r in rs};comparison=[]
    for old in reference:
        if old.get('elapsed_s',0)<100:continue # last smoke already at1us
        new=current.get(old['id'])
        if new:comparison.append(dict(id=old['id'],peak_delta_V=max(abs(f(new,k)-old[k]) for k in ('bx0_peak_V','bx1_peak_V','x2_peak_V')),wait_delta_counts=abs(f(new,'error_at_wait_counts')-old['error_at_wait_counts']) if 'error_at_wait_counts' in old else None,same_rail_verdict=str(old['all_channels_rail_pass'])==new['all_channels_rail_pass']))
    result['E3_step_comparison']=comparison
    lookup={s.ident({k:v for k,v in c.items() if k!='base'}):c for c in s.cases()}
    rs=group('E8');result['E8']={}
    for category in ('50V','esd4k','esd8k','mains'):
        rr=[r for r in rs if ('50V' if r['kind']=='stress50' else 'esd'+str(int(abs(f(r,'amp'))/1000))+'k' if lookup[r['id']]['base']['stimulus']=='esd' else 'mains')==category]
        currents=[(f(r,k),r,k) for r in rr for k in r if k.endswith('_peak_A') and r.get(k)]
        if currents:
            value,r,pin=max(currents,key=lambda x:x[0]);result['E8'][category]=dict(max_A=value,pin=pin,id=r['id'],state=lookup[r['id']].get('base'),failed=sum(r['input_current_pass']!='True' for r in rr),cases=len(rr))
    result['E4']=dict(misleading_points=sum(int(f(r,'misleading_points') or 0) for r in group('E4')),recovery=maxima([r for r in group('E4') if r['kind']=='recover' and r['model']=='192'],'settle_s'))
    result['E5']=dict(min_pm_deg=min(f(r,'pm_deg') for r in group('E5') if r.get('pm_deg')),loop=[{k:r[k] for k in ('gain','tmux','pm_deg','unity_hz')} for r in group('E5') if r['kind']=='loop'],switch_settle=maxima([r for r in group('E5') if r['kind']=='gain'],'settle_s'))
    result['E7']=[{k:r[k] for k in ('amp','noise_rms_V','noise_counts','noise_autozero_counts')} for r in group('E7')]
    impulse=[]
    for r in group('E6'):
        c=lookup[r['id']];base=c['base'];category='mains' if base['stimulus']!='esd' else 'contact4k' if abs(c['amp'])==4000 else 'air8k'
        for part in ('r1a','r1b','r2a','r2b','r3a','r3b','r910k','r100k','rc1','rc2','rc3'):
            impulse.append(dict(id=r['id'],state=s.ident(c),category=category,tau_s=c['tau'],piece=part,peak_V=f(r,part+'_peak_V'),energy_J=f(r,part+'_energy_J'),work_V=200 if not part.startswith('rc') else None,above_work_s=f(r,part+'_above_work_s'),above_200V_s=f(r,part+'_above_200V_s'),above_400V_s=f(r,part+'_above_400V_s'),above_1000V_s=f(r,part+'_above_1000V_s')))
    s.writecsv(s.RESULTS/'s12b_impulsos.csv',impulse)
    result['E6']={}
    for category in ('contact4k','air8k','mains'):
        result['E6'][category]={}
        for part in ('r1a','r1b','r2a','r2b','r3a','r3b','r910k','r100k','rc1','rc2','rc3'):
            rr=[r for r in impulse if r['category']==category and r['piece']==part]
            result['E6'][category][part]={k:max((r[k] for r in rr if r[k] is not None),default=None) for k in ('peak_V','energy_J','above_work_s','above_200V_s','above_400V_s','above_1000V_s')}
    (s.RESULTS/'s12b_resumen.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
