"""Derive compact evidence tables, never promote failed runs to acceptance."""
import csv, json, math
from collections import Counter
import ejecutar_s11_2 as s

def number(r,k):
    try:return float(r[k])
    except (KeyError,TypeError,ValueError):return float('nan')

def main():
    p=s.RESULTS/'s11_2_campaign.csv'
    if p.exists():rows=list(csv.DictReader(p.open(encoding='utf-8-sig')))
    else:rows=[json.loads(p.read_text()) for p in s.JOBS.glob('Q[134567]*.json')]
    # Supplement only missing opening timestamps; original campaign is retained.
    pa=s.RESULTS/'s11_2_fuse_open_audit.csv'
    audits={r['id']:r for r in csv.DictReader(pa.open(encoding='utf-8-sig'))} if pa.exists() else {}
    for r in rows:
        a=audits.get(r['id'])
        if a and a['status']=='ok':
            r['fuse_open_s']=a['fuse_open_audited_s'];r['postopen_peak_A']=a['postopen_peak_audited_A']
        if r['q']=='Q7' and (str(r.get('raw_complete')).lower()!='true' or number(r,'observed_stop_s')<11-1e-6):
            for k in ('recovery_onecount_s','recovery_reference_V','recovery_end_drift_V'):r[k]=''
            r['recovery_audit_note']='incomplete_waveform_no_recovery_evidence'
    s.writecsv(s.RESULTS/'s11_2_campaign_audited.csv',rows)
    good=[r for r in rows if r['status']=='ok']
    def maximum(rs,k):return max((number(r,k) for r in rs if math.isfinite(number(r,k))),default=float('nan'))
    def minimum(rs,k):return min((number(r,k) for r in rs if math.isfinite(number(r,k))),default=float('nan'))
    print('COUNTS',dict(Counter((r['q'],r['status']) for r in rows)))
    fet=[]
    for temp in (0,25,70):
        for ids in (.007,.021):
            for vp in (1.6,2.7):
                rs=[r for r in good if r['q']=='Q3' and number(r,'temp')==temp and number(r,'idss')==ids and number(r,'vp')==vp]
                if not rs:continue
                row=dict(temp_C=temp,idss25_A=ids,vth25_V=-vp,n=len(rs),idss_kind='minimum' if ids==.007 else 'sensitivity_NOT_max',Ilim_min_mA=minimum(rs,'vlf1_peak_A')*1e3,Ilim_max_mA=maximum(rs,'vlf1_peak_A')*1e3,span_max_V=maximum(rs,'span_max'))
                for i in (1,2):
                    for key,suf in (('vds_V','vds_V'),('P_period_W','P_W'),('Tj_est_C','Tj_C'),('E_sim_J','E_sim_J'),('E_extrap_J','E_extrap_J'),('E10_J','E10_J'),('period_spread','period_spread')):row[f'F{i}_{suf}']=maximum(rs,f'fet{i}_{key}')
                fet.append(row)
    s.writecsv(s.RESULTS/'s11_2_bss126_extremes.csv',fet)
    print('BSS126 rows',len(fet),'see s11_2_bss126_extremes.csv')
    bridge=[]
    for grid in (.5,1,2):
        for arc in (1,2,3):
            rs=[r for r in good if r['q']=='Q5' and number(r,'grid')==grid and number(r,'arc')==arc]
            if not rs:continue
            row=dict(grid_ohm=grid,arc_k=arc,n=len(rs),bridge_peak_A=max(maximum(rs,'dbr'+str(i)+'_peak_A') for i in range(1,5)),bridge_i2t_A2s=max(maximum(rs,'dbr'+str(i)+'_i2t_A2s') for i in range(1,5)),shunt_E_J=maximum(rs,'rshunt_E_sim_J'),bin_peak_V=max(maximum(rs,'bin_max'),-minimum(rs,'bin_min')),fuse_open_min_us=minimum(rs,'fuse_open_s')*1e6,fuse_open_max_us=maximum(rs,'fuse_open_s')*1e6,fuse_q_max_A2s=maximum(rs,'fuse_q_final_A2s'),postopen_peak_A=maximum(rs,'postopen_peak_A'))
            row['C8_peak_pass']=row['bridge_peak_A']<=100;row['C8_i2t_pass']=row['bridge_i2t_A2s']<=83;bridge.append(row)
    s.writecsv(s.RESULTS/'s11_2_borne_a.csv',bridge);print('BORNEA rows',len(bridge),'see s11_2_borne_a.csv')
    esd=[]
    for amp in (-4000,4000,-8000,8000):
        for mode in ('ohm','v','a'):
            rs=[r for r in good if r['q']=='Q6' and number(r,'amplitude')==amp and r['mode']==mode]
            if not rs:continue
            row=dict(amplitude_V=amp,mode=mode,n=len(rs),span_V=maximum(rs,'span_max'),fet_Vds_V=max(maximum(rs,'fet1_vds_V'),maximum(rs,'fet2_vds_V')),fet_Vgs_V=max(maximum(rs,'fet1_vgs_V'),maximum(rs,'fet2_vgs_V')),fet_E_J=max(maximum(rs,'fet1_E_sim_J'),maximum(rs,'fet2_E_sim_J')),relay_V=maximum(rs,'relay_V') if any('relay_V' in r for r in rs) else float('nan'),ic_excess_V=max(maximum(rs,x+'_rail_excess') for x in ('mux','bin','x0','x1','x2','x5','bp','msource')),hc_clamp_A=max(maximum(rs,x+'_clamp_peak_A') for x in ('xh0','xh1','xh2','xh4','xh5','xhz')),opa_clamp_A=max(maximum(rs,x+'_clamp_peak_A') for x in ('xopi','xopn')),bav_i2t_A2s=max(maximum(rs,x+'_i2t_A2s') for x in ('d2p','d2n','dblk')))
            esd.append(row)
    s.writecsv(s.RESULTS/'s11_2_esd.csv',esd);print('ESD rows',len(esd),'see s11_2_esd.csv')
    for q in ('Q3','Q4','Q1','Q7'):
        rs=[r for r in good if r['q']==q]
        keys=('span_max','railp_injection_peak_A','railn_injection_peak_A','dzp_peak_A','dzn_peak_A','d2p_peak_A','d2n_peak_A','compliance99_V','bav_added_ppm','recovery_onecount_s','recovery_end_drift_V')
        print(q,{k:(minimum(rs,k),maximum(rs,k)) for k in keys if any(k in r for r in rs)})
    recover=[r for r in rows if r['q']=='Q7']
    print('Q7 raw_complete independent of process status',[(r['status'],r.get('raw_complete'),number(r,'observed_stop_s'),number(r,'recovery_onecount_s')) for r in recover])

if __name__=='__main__':main()
