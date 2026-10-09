"""Compact derived S12c findings from CSVs, no previous campaign writes."""
import csv,json,math
import numpy as np
from scipy.optimize import least_squares
import ejecutar_s12c as s

def analyze():
    rows=list(csv.DictReader((s.RESULTS/'s12c_campaign.csv').open(encoding='utf-8-sig',newline='')))
    def f(r,k):return float(r[k]) if r.get(k) else None
    def group(q):return [r for r in rows if r['q']==q and r['status']=='ok']
    def maximum(rr,k,absolute=False):
        rr=[r for r in rr if r.get(k)]
        if not rr:return None
        r=max(rr,key=lambda r:abs(f(r,k)) if absolute else f(r,k))
        return dict(value=f(r,k),id=r['id'],state=r['physical_state'])
    result={'counts':{q:len(group(q)) for q in s.PRIORITY},'errors':[dict(id=r['id'],error=r.get('error')) for r in rows if r['status']!='ok']}
    result['E3_coarse_summary']={'one_count_fails':[r['id'] for r in group('E3') if r.get('in_range')=='True' and r.get('one_count_pass')!='True'],'rail_fails':[r['id'] for r in group('E3') if r.get('all_channels_rail_pass')!='True']}
    fine={};checks=[]
    for name in ('s12c_verificacion.csv','s12c_verificacion_extra.csv'):
        p=s.RESULTS/name
        if p.exists():
            checkrows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
            checks.extend({k:r.get(k) for k in ('id','q','status','error','elapsed_s')} for r in checkrows)
            fine.update({r['physical_state']:r for r in checkrows if r['status']=='ok' and r['q']=='E3'})
    result['verification_attempts']=checks
    convergence=[]
    for c in s.cases():
        if c['q']!='E3':continue
        r=fine.get(s.ident(dict(c,verification='maxstep100ns')))
        if not r:continue
        base=next(b for b in rows if b['physical_state']==s.ident(c))
        convergence.append(dict(base_id=base['id'],fine_id=r['id'],coarse_error=base.get('error_at_wait_counts'),fine_error=r.get('error_at_wait_counts'),coarse_rail=base.get('all_channels_rail_pass'),fine_rail=r.get('all_channels_rail_pass')))
        for k in ('error_at_wait_counts','error_at_3ms_counts','final_error_counts','one_count_pass','all_channels_rail_pass','buffer_input_cm_pass','bx0_peak_V','x2_peak_V','bi0_peak_V','settle_s'):
            if r.get(k):base[k]=r[k]
    result['E3_convergence']=convergence
    result['E1']={}
    for sigma in (.0005,.001):
        key=f'residual_{sigma}_pct';joint={}
        for fs,sel,g,lsb in s.RANGES:
            rr=[r for r in group('E1') if r['kind']=='ac' and f(r,'amp')==fs]
            result['E1'][f'{fs}_{sigma}']=float(np.percentile([f(r,key) for r in rr],95))
            for r in rr:joint[r['unit']]=max(joint.get(r['unit'],0),f(r,key))
        result['E1'][f'joint_{sigma}']=float(np.percentile(list(joint.values()),95))
    full=[]
    for fs,sel,g,lsb in s.RANGES:
        rr=sorted([r for r in group('E1') if r['kind']=='fullac' and f(r,'rms')==fs],key=lambda r:f(r,'freq'))
        if len(rr)==4:
            freq=np.array([f(r,'freq') for r in rr]);y=np.array([f(r,'transfer_rms') for r in rr]);cal=freq>=100
            fz=1e15 if sel==0 else 1/(2*np.pi*3e6*100e-12)
            def model(x):return np.exp(x[0])*np.sqrt((1+(freq/fz)**2)/(1+(freq/np.exp(x[1]))**2))
            fit=least_squares(lambda x:(model(x)/y-1)[cal],[np.log(y[0]),np.log(35000 if sel==0 else 500)],bounds=([-20,np.log(10)],[5,np.log(1e8)]))
            full.append(dict(range_V=fs,residual_four_points_pct=float(np.max(np.abs(y/model(fit.x)-1))*100),thd_max_pct=max(f(r,'thd_pct') for r in rr),X2_max_V=max(f(r,'x2_peak_V') for r in rr),buffer_input_max_V=max(f(r,'bi0_peak_V') for r in rr),rms=[dict(freq=f(r,'freq'),out_rms=f(r,'rms_V'),gain=f(r,'transfer_rms'),THD_pct=f(r,'thd_pct')) for r in rr]))
    result['E1']['full_signal']=full
    result['E2']=[]
    budgets={r['range_V']:r for r in s.dc_budget()}
    for fs,sel,g,lsb in s.RANGES:
        rr=[r for r in group('E2') if f(r,'amp')==fs];base=next(r for r in rr if f(r,'temp')==23);div=1 if sel==0 else .1/10.01
        result['E2'].append(dict(range_V=fs,SPICE_offset_counts=max(abs(f(r,'offset_V')-f(base,'offset_V'))/(lsb*div*g) for r in rr),SPICE_gain_ppm=max(abs(f(r,'slope')/f(base,'slope')-1)*1e6 for r in rr),fit_residual_V=max(f(r,'DC_fit_residual_V') for r in rr),budget=budgets[fs]))
    rr=group('E3');valid=[r for r in rr if r.get('in_range')=='True'];zero=[r for r in rr if r['kind']=='zero']
    result['E3']=dict(rail_fails=[r['id'] for r in rr if r['all_channels_rail_pass']!='True'],input_cm_fails=[r['id'] for r in rr if r['buffer_input_cm_pass']!='True'],mux_peaks={n:maximum(rr,n+'_peak_V') for n in ('bx0','x2')},buffer_input_peak=maximum(rr,'bi0_peak_V'),valid_cases=len(valid),one_count_fails=[r['id'] for r in valid if r.get('one_count_pass')!='True'],max_error=maximum(valid,'error_at_wait_counts',True),error20_at3ms=maximum([r for r in valid if f(r,'sel')==2 and f(r,'gain')>1],'error_at_3ms_counts',True),settle=maximum(valid,'settle_s'),AC_cases=len(rr)-len(zero))
    result['E8']={}
    for category in ('50V','contact4k','air8k','mains'):
        rr=[r for r in group('E8') if ('50V' if r['kind']=='stress50' else 'contact4k' if abs(f(r,'amp'))==4000 else 'air8k' if abs(f(r,'amp'))==8000 else 'mains')==category]
        key='buffer0_clamp_peak_A'
        result['E8'][category]=dict(cases=len(rr),clamp=maximum(rr,key),total=maximum(rr,'buffer0_total_peak_A'),fails=sum(r.get('input_current_pass')!='True' for r in rr))
    result['E4']=dict(misleading_points=sum(int(f(r,'misleading_points') or 0) for r in group('E4')),recovery=maximum([r for r in group('E4') if r['kind']=='recover' and r['model']=='192'],'settle_s'))
    result['E5']=dict(min_pm_deg=min(f(r,'pm_deg') for r in group('E5') if r['kind']=='loop'),loops=[{k:f(r,k) for k in ('gain','tmux','pm_deg','pm_grid_deg','unity_hz')} for r in group('E5') if r['kind']=='loop'],switch_settle=maximum([r for r in group('E5') if r['kind']=='gain'],'settle_s'))
    result['E7']=[{k:f(r,k) for k in ('amp','noise_rms_V','noise_counts','noise_autozero_counts')} for r in group('E7')]
    impulses=[];result['E6']={}
    for r in group('E6'):
        category='contact4k' if abs(f(r,'amp'))==4000 else 'air8k' if abs(f(r,'amp'))==8000 else 'mains'
        for part in ('r1a','r1b','r2a','r2b','r3a','r3b','r910k','r100k','rc1','rc2','rc3'):
            impulses.append(dict(id=r['id'],state=r['physical_state'],category=category,piece=part,peak_V=f(r,part+'_peak_V'),energy_J=f(r,part+'_energy_J'),above_work_s=f(r,part+'_above_work_s'),above_400V_s=f(r,part+'_above_400V_s'),above_1000V_s=f(r,part+'_above_1000V_s')))
    s.writecsv(s.RESULTS/'s12c_impulsos.csv',impulses)
    capacitors=[]
    for r in group('E6'):
        category='contact4k' if abs(f(r,'amp'))==4000 else 'air8k' if abs(f(r,'amp'))==8000 else 'mains'
        for part,cap in (('c1',100e-12),('c2',100e-12),('c3',100e-12),('c4',330e-12),('c5',3e-9)):
            peak=f(r,part+'_peak_V')
            capacitors.append(dict(id=r['id'],state=r['physical_state'],category=category,piece=part,cap_F=cap,peak_V=peak,stored_energy_J=.5*cap*peak**2))
    s.writecsv(s.RESULTS/'s12c_capacitores.csv',capacitors)
    result['E6_capacitors']={cat:{part:{key:max(r[key] for r in capacitors if r['category']==cat and r['piece']==part) for key in ('peak_V','stored_energy_J')} for part in ('c1','c2','c3','c4','c5')} for cat in ('contact4k','air8k','mains')}
    for category in ('contact4k','air8k','mains'):
        result['E6'][category]={}
        for part in ('r1a','r1b','r2a','r2b','r3a','r3b','r910k','r100k','rc1','rc2','rc3'):
            rr=[r for r in impulses if r['category']==category and r['piece']==part]
            result['E6'][category][part]={k:max((r[k] for r in rr if r[k] is not None),default=None) for k in ('peak_V','energy_J','above_work_s','above_400V_s','above_1000V_s')}
    result['auxiliary']=dict(C2=[{k:f(r,k) for k in ('sel','gain','extra','droop20_pct')} for r in group('C2')],C3_cap_pF=[f(r,'cap_COM_pF') for r in group('C3') if r['kind']=='cap'])
    q=next(r for r in group('Q0') if r['kind']=='cm')
    raw=s.raw(s.JOBS/(q['id']+'.raw'));idx=int(np.argmin(abs(raw['vin'])))
    result['auxiliary']['single_OPA192_IQ_A']=(abs(float(raw['i(vp)'][idx]))+abs(float(raw['i(vn)'][idx])))/2
    result['auxiliary']['dual_OPA2192_IQ_estimate_A']=2*result['auxiliary']['single_OPA192_IQ_A']
    result['auxiliary']['reduced_protection_budget_A']=.004116
    (s.RESULTS/'s12c_resumen.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('counts','errors','E1','E2','E3','E8','E4','E5','E7')},indent=2))
    print('E6 maxima',json.dumps({cat:{'RT_V':max(result['E6'][cat][p]['peak_V'] for p in ('r1a','r1b','r2a','r2b','r3a','r3b')),'Rc_V':result['E6'][cat]['rc1']['peak_V'],'Rc_J':result['E6'][cat]['rc1']['energy_J']} for cat in result['E6']}))

if __name__=='__main__':analyze()
