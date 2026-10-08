"""S12d short confirmation derived from S12c, earlier files read-only.
10 workers; --smoke/--resume; 900s per case; local models only.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
_src=(HERE/'ejecutar_s12c.py').read_text(encoding='utf-8')
_src=_src.replace('S12c','S12d').replace('s12c_','s12d_').replace('dmm_bloque2c.inc','dmm_bloque2d.inc')
_src=_src.rsplit("\nif __name__=='__main__':raise SystemExit(main())",1)[0]
exec(compile(_src,str(HERE/'ejecutar_s12c.py'),'exec'),globals())
_cdeck=deck; _cprotection=protection_deck; _caudit=audit; _ccases=cases; _cident=ident; _csignature=signature
PRIORITY=('E2','E3','E5','E8')

def ident(c):
    state=dict(c)
    if c.get('base'):state['base']=dict(c['base'],rx0=10000,rx2=10000)
    result=_cident(state).replace('rx100_none_none','rx10000_none_10000')
    return result+'_opa4192_rx0_10k_rx2_10k_x1com_waitx2_3ms_waitx0_0d1ms'

def cases(n=200):
    global PRIORITY
    priority=PRIORITY; PRIORITY=('E3','E8','E2','E1','E6','E5','E4','E7','C2','C3','Q0')
    try: old=_ccases(1)
    finally: PRIORITY=priority
    out=[]
    for c in old:
        if c['q'] not in priority:continue
        if c['q']=='E5' and c['kind']!='loop':continue
        if c['q']=='E2':
            for sign in (-1,1):
                out.append(dict(c,leak=sign*.4e-6*2**((c['temp']-25)/10),bleak=sign*.6e-9*2**((c['temp']-23)/10),leaksign=sign,leakref25_A=.4e-6))
        elif c['kind']=='railac':out.append(dict(c,stop=max(.028,.020+6/c['freq']),pretime=.020,charge=0))
        else:out.append(c)
    return sorted(out,key=lambda c:priority.index(c['q']))

def deck(c):
    if c['kind']=='protection':return protection_deck(c)
    if c['kind']=='railac':
        text=_cdeck(dict(c,kind='zero'))
        text=text.replace(f'PWL(0 0 20u {c["amp"]} {c["stop"]} {c["amp"]})',f'SINE(0 {c["amp"]} {c["freq"]})')
        # Same preconditioned X3 -> signal event as DC, followed by AC.
        text=text.replace(f'.tran 0 {c["stop"]} 0 1u',f'.tran 0 {c["stop"]} 0 {min(1e-6,1/(300*c["freq"])):.12g} uic')
    else:text=_cdeck(c)
    text=text.replace('X2 ctl2 x2 mux','X2 ctl2 bx2 mux').replace('Rsel x2 mux','Rsel bx2 mux')
    if c['q']=='E2':
        # One aggregate ON current at COM. Do not also count it at Yn.
        text=re.sub(r'\bMLEAK=[^\s]+','MLEAK=0',text)
    if c['q'] in ('E3','E8'):
        saves=' '.join(f'I(Xbuf{i}:X_U5:S{j})' for i in (0,2) for j in (1,2,3,4))
        text=text.replace('.end',f'.save V(bx2) V(bi2) V(bn2) I(Vib2) I(Vibn2) {saves}\n.end')
    # AC decks are assembled through the zero-event builder, but every measure
    # must identify their actual sine stimulus, frequency and railac state.
    text=re.sub(r'(?m)^(\.meas\s+\w+\s+)\S+?__',lambda m:m[1]+ident(c)+'__',text)
    return text

def protection_deck(c):
    text=_cprotection(c)
    # Original S11 RX0 parameter is 100; override only this derived deck.
    text=re.sub(r'\bRX0=100\b','RX0=10000',text,flags=re.I)
    text=re.sub(r'(?m)^Rx0 ([^\n]*?) 100$',r'Rx0 \1 10k',text)
    text=text.replace('Xh2 x2 rp rn','Xh2 bx2 rp rn').replace('Rselected x2 mux','Rselected bx2 mux')
    extra='Rx2 x2 hx2 10k\nVib2 hx2 bi2 0\nXbpin2 bi2 rp rn PINOPA\nEbi2 ti2 0 bi2 0 1\nVibn2 bx2 bni2 0\nXbuf2 ti2 bni2 bvp bvn bx2 OPAx192\nCbd2 bi2 bx2 1.6p\nXunused 0 unused bvp bvn unused OPAx192\n'
    # Reduced current budget adds X2 and the unused channel, not a residual.
    text=text.replace('Riqbuffers rp rn {9.8/.001}','Riqbuffers rp rn {9.8/.003}')
    text=text.replace('IC budget4.116mA','IC budget6.116mA')
    text=re.sub(r'(?m)^\.end\s*$',lambda m:extra+'.save V(bi2) V(bx2) I(Vib2) I(Xbpin2:Dhi) I(Xbpin2:Dlo)\n.end',text)
    text=re.sub(r'(?m)^(\.meas\s+\w+\s+)\S+?__',lambda m:m[1]+ident(c)+'__',text)
    return text

def audit(c,path):
    if c['q']=='E2' or c['kind']=='loop':return _caudit(c,path)
    d=raw(path);t=np.abs(np.asarray(d['time']));v=lambda n:np.asarray(d['v('+n+')']);r={}
    for i in (0,2):
        if c['kind']=='protection':
            hi=np.asarray(d[f'i(xbpin{i}:dhi)']);lo=np.asarray(d[f'i(xbpin{i}:dlo)'])
            clamp=hi-lo;method='reduced_PINOPA_direct_diode_conduction_Vf0.5_Ron1_assumed'
        else:
            keys=[f'i(xbuf{i}:x_u5:s{j})' for j in (1,2,3,4)]
            if not all(k in d for k in keys):raise ValueError('missing TI direct clamp currents')
            # Switches 1/2 clamp IN+, 3/4 clamp IN-; assess both pins separately.
            ip=np.asarray(d[keys[0]])+np.asarray(d[keys[1]])
            inn=np.asarray(d[keys[2]])+np.asarray(d[keys[3]])
            clamp=ip
            r[f'buffer{i}_n_clamp_peak_A']=float(np.max(np.abs(inn)))
            method='TI_direct_internal_ESD_switch_currents'
        r[f'buffer{i}_clamp_peak_A']=float(np.max(np.abs(clamp)))
        tail=t>c['stop']-.0002
        r[f'buffer{i}_clamp_tail_peak_A']=float(np.max(np.abs(clamp[tail])))
        r[f'buffer{i}_total_peak_A']=float(np.max(np.abs(d[f'i(vib{i})'])))
        r[f'buffer{i}_clamp_method']=method
    r['input_current_pass']=max(r[f'buffer{i}_clamp_peak_A'] for i in (0,2))<=.005
    if c['kind']=='protection':return r
    r['mux_channel_peak_V']=max(float(np.max(np.abs(v(n)))) for n in ('bx0','bx2'))
    r['all_channels_rail_pass']=r['mux_channel_peak_V']<=c['rail']+.05
    # Continuous criterion excludes power-on charging, retains the complete AC
    # waveform after startup and the complete mux switching interval for DC.
    continuous=t>(max(2/c['freq'],.001) if c['kind']=='railac' else .001)
    for i in (0,2):
        keys=[f'i(xbuf{i}:x_u5:s{j})' for j in (1,2)]
        wave=np.asarray(d[keys[0]])+np.asarray(d[keys[1]])
        r[f'buffer{i}_continuous_clamp_A']=float(np.max(np.abs(wave[continuous])))
    r['continuous_clamp_pass']=max(r[f'buffer{i}_continuous_clamp_A'] for i in (0,2))<=50e-6
    if c['q']=='E3' and c['kind']=='zero':
        fs=next(x for x in RANGES if x[1]==c['sel'] and x[2]==c['gain'])
        div=1 if c['sel']==0 else .1/10.01; lsb=fs[3]*div*c['gain'];expected=c['amp']*div*c['gain']
        wait=.0001 if c['sel']==0 else .003
        r['in_range']=abs(c['amp'])<=fs[0];r['wait_s']=wait
        if r['in_range']:
            at=float(np.interp(.021+wait,t,v('out')))
            r['error_at_wait_counts']=(at-expected)/lsb
            r['final_error_counts']=(float(np.mean(v('out')[t>.0278]))-expected)/lsb
            # Isolate acquisition settling from fixed calibrated DC offset/gain.
            r['settling_error_counts']=r['error_at_wait_counts']-r['final_error_counts']
            r['one_count_pass']=abs(r['error_at_wait_counts'])<=1
    if c['kind']=='railac':
        # Calibrated periodic tail includes gain/phase and harmonic distortion;
        # compare acquisition with the same phase after the firmware wait.
        r['in_range']=c['sel']==2 and c['gain']==1
        r['ac_accuracy_scope']='all_range_rails_clamps;50V_range_periodic_tail_after_3ms;not_raw_phase_error'
        if r['in_range']:
            f=c['freq'];grid=np.linspace(.024,.024+1/f,1200,endpoint=False)
            cycles=math.floor((c['stop']-grid[-1])*f)
            late=grid+cycles/f
            lsb=.01*.1/10.01
            errors=(np.interp(grid,t,v('out'))-np.interp(late,t,v('out')))/lsb
            r['ac_error_after_wait_counts']=float(np.max(np.abs(errors)))
            r['one_count_pass']=r['ac_error_after_wait_counts']<=1
    return r

def dc_budget():
    rng=np.random.default_rng(1202);tc=rng.uniform(-25e-6,25e-6,(10000,10));rs=np.array([1.5e6]*6+[910e3,100e3,91e3,10e3]);out=[]
    drift=math.sqrt(2)-1; mux_at23=.4e-6*2**(-2/10)
    for fs,sel,g,lsb in RANGES:
        div=1 if sel==0 else .1/10.01;input_lsb=lsb*div
        source=(99e3 if sel==0 else 100e3*9.91e6/10.01e6)+10e3
        mux_r=71.;gains=[]
        for dt in (-5,5):
            rr=rs*(1+tc*dt);ratio=1 if sel==0 else rr[:,7]/np.sum(rr[:,:8],axis=1)
            gg=1 if g==1 else 1+rr[:,8]/rr[:,9]
            gains.append(np.abs(np.asarray(ratio/div*gg/g)-1)*1e6)
        vos=5e-6/input_lsb;ib=20e-12*(source+mux_r)*drift/input_lsb
        tm=(.3e-9*91000/g*drift if g>1 else 0)/input_lsb
        mux=mux_at23*mux_r*drift/input_lsb
        fixed=vos+ib+tm+mux;per=1e-9*source*drift/input_lsb
        out.append(dict(range_V=fs,gain_p95_ppm=float(np.percentile(np.maximum(*gains),95)),offset_budget_counts=fixed+.6*per,leak_max_nA=max(0,(4-fixed)/per),fixed_counts=fixed,assumed_leak_nA=.6,mux_ON25_A=.4e-6,mux_ON23_A=mux_at23,source_ohm=source,vos_counts=vos,Ib_counts=ib,TMUX_counts=tm,mux_counts=mux,input_leak_counts=.6*per,assumptions='signed_ON0.4uA_at25;double_per10C_assumed;23C_cal;18_28C;Ib20pA_extra;Rout1ohm;Ron70ohm;SOIC0.5uV_C_per_channel'))
    writecsv(RESULTS/'s12d_dc_budget.csv',out);return out

def signature(content):
    return hashlib.sha256((_csignature(content)+hashlib.sha256((HERE/'ejecutar_s12c.py').read_bytes()).hexdigest()).encode()).hexdigest()

def collect(n=200):
    """Keep exact unchanged decks; rerun changed decks, including name fixes.
    Source-only audit revisions are resigned only with identical deck proof.
    Preserve timing/signature history; never accept a changed electrical deck.
    """
    start=time.perf_counter();rows=[];repair=[]
    for c in cases():
        name=c['q'].lower()+'_'+hashlib.sha256(ident(c).encode()).hexdigest()[:20]
        p=JOBS/(name+'.cir');stamp=p.with_suffix('.json');content=deck(c)
        if not stamp.exists() or not p.exists():repair.append(c);continue
        r=json.loads(stamp.read_text(encoding='utf-8'));saved=p.read_text(encoding='utf-8')
        if r['status']!='ok' or saved!=content:
            if saved!=content:
                neutral=lambda s:re.sub(r'(?m)^(\.meas\s+\w+\s+)\S+?__',r'\1STATE__',s)
                if neutral(saved)!=neutral(content):raise ValueError('electrical deck changed, abort name-only repair: '+name)
            hist=stamp.with_suffix('.before_meas_fix.json')
            hist.write_text(json.dumps(r,indent=2),encoding='utf-8');repair.append(c);continue
        old=r['signature'];new=signature(content)
        if old!=new:r.setdefault('signature_history',[]).append(dict(signature=old,reason='exact_saved_deck_proof;AC_meas_prefix_only_source_revision'))
        r.update(signature=new,reaudited_exact_deck=True)
        stamp.write_text(json.dumps(r,indent=2),encoding='utf-8');rows.append(r)
    with cf.ThreadPoolExecutor(max_workers=10) as pool:
        for fut in cf.as_completed([pool.submit(run,c,False) for c in repair]):rows.append(fut.result())
    writecsv(RESULTS/'s12d_campaign.csv',rows)
    summary=json.loads((RESULTS/'s12d_campaign.json').read_text(encoding='utf-8'))
    summary.update(ok=sum(r['status']=='ok' for r in rows),collect_elapsed_s=time.perf_counter()-start,collect_reexecuted=len(repair),reaudited_exact_deck=len(rows)-len(repair),repair_reason='AC_meas_state_prefix;electrical_deck_unchanged')
    (RESULTS/'s12d_campaign.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    # Keep original measured smoke elapsed/reuse metadata, update its records.
    smoke=RESULTS/'s12d_smoke.csv';ids=[r['id'] for r in csv.DictReader(smoke.open(encoding='utf-8-sig'))]
    current={r['id']:r for r in rows};writecsv(smoke,[current[i] for i in ids])
    dc_budget();print(json.dumps(summary),flush=True)
    for r in rows:
        if r['status']!='ok':print('ERROR',r['id'],r.get('error','')[:300],flush=True)
    return int(summary['ok']!=len(rows))

if __name__=='__main__':raise SystemExit(main())
