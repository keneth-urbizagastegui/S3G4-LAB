"""S9 contract: ten workers, native LTspice, durable fixed-schema CSV, resume.

Exit 0 means all simulations completed; failing electrical criteria are valid.
No writes to CH1, manufacturer models, STATE or DECISIONS.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import argparse,csv,hashlib,json,os,re,time,threading
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
ROOT=Path(__file__).resolve().parent
CH1=ROOT.parent/'CH1_entrada'
sys.path.insert(0,str(CH1))
import ejecutar_s7b as sb
old=sb.old
MODELS=Path(os.environ.get('S3G4_MODELS',str(sb.MODELS)))
PROJECT=ROOT.parents[2]
INC=ROOT/'comun/ch23_comun_s9.inc'
SEED=sb.SEED
FS=52e6/15;TS=2.5/52e6;PERIOD=15/52e6;N=1024;FIRST=256;START=1e-6
FILTERS={'A':(2490.,1100.),'B':(2490.,1100.)}
SCALES=sb.SCALES
write,csv_write=sb.write,sb.csv_write
BASE=['id','test','variant','ix','scale_V_div','POS','tap','mc','kind','amplitude_V','freq_Hz','M','vdac_V','CPL','rail_plus_set_V','rail_minus_set_V','dc_limit_V','F1','F2','state','RSW']
METRICS=['minus3_Hz','peak_db','peak_Hz','atten_1p73m_db','atten_2p47m_db','rebound_excess_db','rebound_Hz','gd_min_ns','gd_max_ns','gd_variation_ns','gain_dc_signed','gain_nominal_signed','gain_error_pct','center_V','offset_uncal_V','dac_center_V','position_plus_div','position_minus_div','position_pass','offset_compensable','noise_pin_uV','noise_pct_div','noise_with_adc_low_pct','noise_with_adc_high_pct','rise_ns','overshoot_pct','recovery_us','bav199_conducts','bav199_forward_max_V','bav199_peak_A','adc_min_V','adc_max_V','mux_low_margin_V','mux_high_margin_V','mux_supply_max_V','protection_pass','sfdr_db','reference_sfdr_db','residual_rms_LSB','residual_max_LSB','error_max_LSB','error_rms_LSB','gain_delta_db','phase_delta_deg','fundamental_pp_V','sample_width_ns','sample_period_ns','closing_time_error_ps','returncode']
FIELDS=BASE+METRICS
EXTRA_FIELDS={
    'mc_components':['id','variant','mc','component','nominal_SI','tolerance','draw','factor','value_SI','seed'],
    'limits':old.LIMIT_FIELDS+['variant','phase','POS','CPL','dc_limit_V','rail_plus_set_V','rail_minus_set_V','plus_pin_current_abs_max_A','minus_pin_current_abs_max_A'],
    'stress':['id','variant','part','voltage_V','power_W','dc_limit_V'],
    'bav99':['id','variant','stage','diode','current_abs_max_A'],
    'consumption':old.CON_FIELDS,
    'samples':['id','n','time_s','sample_V','reference_V','error_V','track_left_time_s','track_left_clock_V','closing_clock_time_s','closing_time_error_ps'],
    'bins':['id','sequence','bin','freq_Hz','amplitude_V'],
}
NUMERIC_LOCK=threading.Lock()

def case(test,variant='A',ix=0,mc=-1,**kw):
    mapping={'K1':'J1','K1SWEEP':'J1','K2':'J2','K3':'J4','K5AC':'J3','K5NOISE':'J4','K5OP':'J1DC','K6':'J5','K6REC':'J6','K8':'J9'}
    c=old.case(mapping.get(test,'J1'),ix,mc,**{k:v for k,v in kw.items() if k in ['kind','amp','vdac']})
    c.update(test=mapping.get(test,'J1'),s9_test=test,variant=variant,CPL=0,rail_plus_set_V=4.9,rail_minus_set_V=4.9,dc_limit_V=40.,F1=FILTERS[variant][0],F2=FILTERS[variant][1],state='',RSW=0)
    c.update({k:v for k,v in kw.items() if k not in ['amp','vdac']})
    if mc>=0:
        rr=sb.realization(mc);c.update(rail_plus_set_V=rr['rp'],rail_minus_set_V=rr['rn'])
    c['id']=f's9_{test.lower()}_{variant.lower()}_s{ix:02d}_pos{c["POS"]}_tap{c["tap"]}_mc{mc}_cpl{c["CPL"]}_rp{old.s4.number(c["rail_plus_set_V"])}_rn{old.s4.number(c["rail_minus_set_V"])}_f1{old.s4.number(c["F1"])}_f2{old.s4.number(c["F2"])}'
    c['id']+=f'_a{old.s4.number(c["amplitude_V"])}_dac{old.s4.number(c["vdac_V"])}'
    if c['freq_Hz']:c['id']+=f'_f{old.s4.number(c["freq_Hz"])}'
    if c['state']:c['id']+=f'_{c["state"].lower()}_rsw{c["RSW"]}'
    if test=='K6':c['id']+=f'_limit{old.s4.number(c["dc_limit_V"])}'
    if test=='K4':c['id']=c['id'].replace('_a0_','_acalculated_')
    c['id']=c['id'].replace('mc-1','mcnom')
    return c

def mc_subcircuits(c):
    if c['mc']<0:return [],[]
    rr=sb.realization(c['mc']);lines=list(rr['lines']);records=[dict(x,id=c['id'],variant=c['variant']) for x in rr['records']]
    section=''
    for i,line in enumerate(lines):
        if line.startswith('.subckt'):section=line.split()[1]
        if section in ['SK_S7_MCA','SK_S7_MCB'] and re.match(r'^R[12] ',line):
            head,val=line.rsplit(None,1);which=0 if section.endswith('MCA') else 1
            target=c['F1'] if which==0 else c['F2'];orig=sb.NOM['RFILT1_S7' if which==0 else 'RFILT2_S7']
            lines[i]=head+' '+format(float(val)*target/orig,'.17g')
            for r in records:
                if r['component']==('X105A:' if which==0 else 'X105B:')+line.split()[0]:r['nominal_SI']=target;r['value_SI']=float(val)*target/orig
        if c['variant']=='B' and line.startswith(('XAMP ','X103A ','X103B ')):
            lines[i]=lines[i].replace('AD8038','LM6172_W')
    return lines,records

old.mc_subcircuits=mc_subcircuits

def net(c):
    d=old.net(c)
    d=d.replace(str(CH1/'comun/ch1_comun_s7.inc'),str(INC))
    d=d.replace('RAILS_S2B POWER=1','RAILS_S7B POWER=1').replace('RAILS_S7_MC POWER=1','RAILS_S7B POWER=1')
    d=d.replace('RAILS_S7B POWER=1',f'RAILS_S7B POWER=1 RP={c["rail_plus_set_V"]:.17g} RN={c["rail_minus_set_V"]:.17g}')
    d=d.replace('CHANNEL_S7 POS=','CHANNEL_S9 POS=')
    r=sb.realization(c['mc']) if c['mc']>=0 else None
    if r:d=d.replace('VREF VREF 0 {VREF_NOM}',f'VREF VREF 0 {r["vref"]:.17g}')
    lines=d.splitlines()
    for j,line in enumerate(lines):
        if line.startswith('XCH BNC '):
            lines[j]=line+f' CPL={c["CPL"]}'
            if r:lines[j]+=' '+' '.join(f'{k}={v:.17g}' for k,v in r['offsets'].items())
            else:lines[j]+=f' AMP={int(c["variant"]=="B")} F1={c["F1"]:.17g} F2={c["F2"]:.17g}'
    noise=c['s9_test'] in ['K3','K5NOISE']
    lm=ROOT/'comun/lm6172_s9_ruido_hoja.lib' if noise else MODELS/'LM6172/lm6172.lib'
    lines.insert(1,f'.include "{lm}"')
    is_transient=c['s9_test'] in ['K2','K6REC','K8']
    if c['variant']=='B' and is_transient:lines=[line.replace('abstol=1e-12','abstol=1e-10') for line in lines]
    lines.insert(2,f'.options gmin={"1e-16" if c["variant"]=="B" and not is_transient else "1e-12"} itl1=1000 itl2=1000'+(' itl4=1000' if c['variant']=='B' and is_transient else ''))
    lines.insert(1,f'.param AMP_S9_SELECT={int(c["variant"]=="B")}\n.subckt AMP_S9 IP IM VP VN OUT params: KIND=0\nXSELECT IP IM VP VN OUT AMP_S9_{c["variant"]}\n.ends AMP_S9')
    d='\n'.join(lines)+'\n'
    if noise:d=d.replace('1 3.15Meg','1 10Meg')
    if c['s9_test']=='K6':
        direction=c.get('direction',1);lim=c['dc_limit_V']
        d=re.sub(r'^\.dc .*$',f'.dc Vsrc 0 {direction*lim:.17g} {direction*.001:.17g}',d,flags=re.M)
        extra=['V(XCH:'+n+')' for n in ['bo','y1','y2','y3','y4','y5','y7','common','m','tap','rsm','x1','eq','b','sel','rawin']]
        extra += [f'I(XCH:XPROT{stage}:{diode})' for stage in ['A','B'] for diode in ['DP','DN']]
        if c['variant']=='B':
            for stage in ['X103A','X103B','X105A:XAMP','X105B:XAMP']:
                mid=':XSELECT:XB' if c['mc']<0 else ''
                extra += [f'I(XCH:{stage}{mid}:XCORE:{r})' for r in ['RINA','RINB']]
        d=re.sub(r'^(\.save .*?)$',lambda m:m[0]+' '+' '.join(extra),d,flags=re.M)
    if c['s9_test']=='K5OP':
        d=re.sub(r'^\.dc .*$', '.op',d,flags=re.M)
        d=re.sub(r'^\.meas DC .*\n','',d,flags=re.M)
        d=re.sub(r'^Vsrc SRC 0 .*$',f'Vsrc SRC 0 {c.get("source_V",0):.17g}',d,flags=re.M)
        d=d.replace('.save V(PIN) V(BNC)','.save V(PIN) V(BNC) V(DAC)')
    return d

def native(c,work,deck=None,timeout=120,bias=None):
    p=work/(c['id']+'.cir');d=deck if deck is not None else net(c)
    if deck is None and not (bias and bias.exists()):
        guides=list((CH1/'S7b/campaign').glob(f's7b_j3_s{c["ix"]:02d}_*mc0_*.bias'))
        if not guides:guides=list((CH1/'S7b/campaign').glob(f's7b_j1_s{c["ix"]:02d}_*mcnom_*biasonly.bias'))
        if not guides:
            guides=list((CH1/'S7b/campaign').glob(f's7b_j3_s{0 if c["ix"]<6 else 6:02d}_*mc0_*.bias'))
            if guides:
                # Reorder only initial recommendations for an equivalent switch branch.
                # No node is imposed after Newton iteration; actual CODE stays in deck.
                initial=guides[0].read_text();tap=c['tap']
                def branch(m):
                    key,n=m[1],int(m[2]);n=tap if n==0 else 0 if n==tap else n
                    return 'xch:xmux:'+key+str(n)
                initial=re.sub(r'xch:xmux:([xdc])([0-7])',branch,initial,flags=re.I)
                initial=re.sub(r'V\(xch:xmux:code\)=[^\s]+',f'V(xch:xmux:code)={tap}',initial,flags=re.I)
                for bit in range(3):initial=re.sub(fr'V\(xch:a{bit}\)=[^\s]+',f'V(xch:a{bit})={4.96 if tap&(1<<bit) else 0}',initial,flags=re.I)
                own=work/f's9_nodeset_s{c["ix"]:02d}.bias';write(own,initial);guides=[own]
        if guides:bias=guides[0]
    if bias and bias.exists():d=d.replace('\n.end\n',f'\n.loadbias "{bias}"\n.end\n')
    if c.get('retry_numeric'):d=d.replace('\n.end\n','\n.options itl4=1000\n.end\n')
    if c['s9_test'] in ['K1','K1SWEEP','K5AC']:d=d.replace('\n.end\n',f'\n.savebias "{p.with_suffix(".bias")}" internal\n.end\n')
    write(p,d)
    for ext in ['.raw','.op.raw','.log','.db']:p.with_suffix(ext).unlink(missing_ok=True)
    t=time.perf_counter();rec=dict(id=c['id'],seconds=0.,returncode=1,errors=[],warnings=[])
    try:
        proc=sb.run_lt(p,work,timeout);vals,err,warn,_=old.s4.s3.prior.old.read_log(p.with_suffix('.log'))
        logtext=p.with_suffix('.log').read_text(errors='replace')
        vals.update({m[1].lower():float(m[2]) for m in re.finditer(r'^([\w]+)=([+\-\d.eE]+)\s',logtext,re.M)})
        rec.update(returncode=proc.returncode,errors=err,warnings=warn)
        expected={x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',d,re.M|re.I)}
        if expected-set(vals):rec['errors'].append('Missing measures '+str(sorted(expected-set(vals))))
        if proc.returncode or rec['errors']:raise RuntimeError(str(rec['errors']))
        raw=old.s4.s3.raw_read(p.with_suffix('.raw'))
    except Exception as e:
        rec['errors'].append(repr(e));rec['returncode']=1;raw=None
    rec['seconds']=time.perf_counter()-t
    write(p.with_suffix('.native.json'),json.dumps(rec))
    with NUMERIC_LOCK:
        with (work/'native_history.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(rec)+'\n')
    if raw is not None:
        for ext in ['.raw','.op.raw','.db']:p.with_suffix(ext).unlink(missing_ok=True)
    return raw,rec

def ac_metrics(raw,c):
    f=raw['frequency'];h=raw['v(pin)']/raw['v(bnc)'];db=20*np.log10(abs(h/h[0]))
    hit=np.flatnonzero(db<=-3)
    if not len(hit):raise ValueError('No -3 dB crossing')
    ix=hit[0];f3=float(np.exp(np.interp(-3,db[ix-1:ix+1][::-1],np.log(f[ix-1:ix+1])[::-1])))
    interp=lambda freq:float(np.interp(np.log(freq),np.log(f),db))
    gd=-np.gradient(np.unwrap(np.angle(h)),2*np.pi*f)*1e9;mask=(f>=1e4)&(f<=1e6)
    alias=interp(2.47e6);tail=np.flatnonzero(f>=2.47e6);j=tail[np.argmax(db[tail])]
    g=float(h[0].real);gn=-.25/c['scale_V_div']
    return dict(minus3_Hz=f3,peak_db=float(db.max()),peak_Hz=float(f[np.argmax(db)]),atten_1p73m_db=-interp(1.73e6),atten_2p47m_db=-alias,rebound_excess_db=max(0,float(db[j]-alias)),rebound_Hz=float(f[j]),gd_min_ns=float(gd[mask].min()),gd_max_ns=float(gd[mask].max()),gd_variation_ns=float(np.ptp(gd[mask])),gain_dc_signed=g,gain_nominal_signed=gn,gain_error_pct=100*(g/gn-1))

def analyze(c,raw,row):
    test=c['s9_test']
    if test in ['K1','K1SWEEP','K5AC']:row.update(ac_metrics(raw,c));return {}
    if test in ['K3','K5NOISE']:
        key=next(k for k in raw if 'onoise' in k and 'total' not in k)
        rms=old.s4.s3.integral_band(raw['frequency'],raw[key].real,10e6)
        row.update(noise_pin_uV=rms*1e6,noise_pct_div=100*rms/.25,noise_with_adc_low_pct=100*np.hypot(rms,.40e-3)/.25,noise_with_adc_high_pct=100*np.hypot(rms,.61e-3)/.25);return {}
    if test=='K6':
        cc=dict(c,phase='K6');extra=sb.analyze(cc,raw,row)
        ok=row['adc_min_V']>=0 and row['adc_max_V']<=3.3 and row['mux_low_margin_V']>=0 and row['mux_high_margin_V']>=0 and row['mux_supply_max_V']<=10
        for r in extra['limits']:
            r['variant']=c['variant'];stage=r['stage'];cur=max(r['plus_current_abs_max_A'],r['minus_current_abs_max_A'])
            if c['variant']=='B' and stage.startswith(('U103','U105')):
                path={'U103A':'x103a','U103B':'x103b','U105A':'x105a:xamp','U105B':'x105b:xamp'}[stage]
                mid=':xselect:xb' if c['mc']<0 else ''
                for side,el in [('plus','rina'),('minus','rinb')]:
                    r[side+'_pin_current_abs_max_A']=float(abs(raw[f'i(xch:{path}{mid}:xcore:{el})']).max())
                cur=max(r['plus_pin_current_abs_max_A'],r['minus_pin_current_abs_max_A'])
            lim=.010 if stage=='OPA810' else .00043 if stage=='OPA836' else .005 if c['variant']=='B' else float('inf')
            diff=8 if c['variant']=='B' else 2
            ok=ok and cur<=lim and (r['differential_abs_max_V']<=diff if stage.startswith(('U103','U105')) else True)
        row['protection_pass']=bool(ok)
        extra['bav99']=[dict(id=c['id'],variant=c['variant'],stage='U103'+stage,diode=diode,current_abs_max_A=float(abs(raw[f'i(xch:xprot{stage.lower()}:{diode.lower()})']).max())) for stage in ['A','B'] for diode in ['DP','DN']]
        for r in extra.get('stress',[]):r['variant']=c['variant']
        return extra
    return old.analyze(c,raw,row)

def op_case(c,work):
    parts=[];records=[];lim=.01*c['scale_V_div']
    guide=work/(case('K5AC',c['variant'],c['ix'],c['mc'])['id']+'.bias')
    for src,dac,label in [(-lim,1.25,'gain_negative'),(0,1.25,'gain_zero'),(lim,1.25,'gain_positive'),(0,.2,'dac_low'),(0,2.3,'dac_high'),(0,1.24,'dac_local')]:
        cc=dict(c,source_V=src,vdac_V=dac,id=c['id']+'_'+label+'_src'+old.s4.number(src)+'_dac'+old.s4.number(dac))
        raw,rec=native(cc,work,timeout=60,bias=guide);records.append(rec)
        if raw is None:raise ValueError('OP failed '+str(rec))
        parts.append(float(raw['v(pin)'][0]))
    low,center,high,dl,dh,local=parts;gain=(high-low)/(2*lim);slope=(center-local)/(.01)
    dac=1.25+(1.25-center)/slope;plus=(dl-1.25)/.25;minus=(1.25-dh)/.25
    row=dict(c,gain_dc_signed=gain,gain_nominal_signed=-.25/c['scale_V_div'],gain_error_pct=100*(gain/(-.25/c['scale_V_div'])-1),center_V=center,offset_uncal_V=center-1.25,dac_center_V=dac,position_plus_div=plus,position_minus_div=minus,offset_compensable=bool(.2<=dac<=2.3),position_pass=bool(.2<=dac<=2.3 and plus>=4.5 and minus>=4.5))
    return row,{},records

def simulate(c,work):
    jsonpath=work/(c['id']+'.json');csvpath=work/(c['id']+'.csv');records=[]
    for attempt in range(2):
        try:
            if c['s9_test']=='K5OP':
                row,extra,recs=op_case(c,work);records+=recs
            elif c['s9_test']=='K6':
                pair={}
                for dr in [-1,1]:
                    cc=dict(c,direction=dr,id=c['id']+('_negative' if dr<0 else '_positive'))
                    raw,rec=native(cc,work,timeout=600);records.append(rec)
                    if raw is None:raise ValueError('Protection child failed')
                    x=raw['v(bnc)']
                    if abs(x[-1]-dr*c['dc_limit_V'])>1e-8:raise ValueError('Wrong protection endpoint')
                    pair[dr]=raw
                raw={k:np.r_[pair[-1][k][::-1],pair[1][k][1:]] for k in pair[-1]}
                row=dict(c);extra=analyze(c,raw,row)
            elif c['s9_test']=='K4':row,extra,recs=sampling(c,work);records+=recs
            else:
                bias=work/(case('K1',c['variant'],c['ix'])['id']+'.bias')
                if c['mc']>=0:
                    own=work/(case('K5AC',c['variant'],c['ix'],c['mc'])['id']+'.bias')
                    if own.exists():bias=own
                raw,rec=native(dict(c,retry_numeric=bool(attempt)),work,timeout=900 if c['s9_test'] in ['K2','K6REC','K8'] else 120,bias=bias if attempt or c['mc']>=0 else None);records.append(rec)
                if raw is None:raise ValueError('Native failed')
                row=dict(c);extra=analyze(c,raw,row)
                if c['s9_test'] in ['K1','K1SWEEP']:
                    write(work/(c['id']+'.response.json'),json.dumps(dict(f=raw['frequency'].tolist(),mag=abs(raw['v(pin)']/raw['v(bnc)']).tolist())))
            row['test']=c['s9_test'];row['returncode']=0
            if c['s9_test']=='K5AC':extra['mc_components']=mc_subcircuits(c)[1]
            csv_write(csvpath,[row],FIELDS)
            write(jsonpath,json.dumps(dict(row=row,extra=extra,records=records),ensure_ascii=False))
            return row,extra,records
        except Exception as e:
            records.append(dict(id=c['id']+f'_analysis_attempt{attempt}',returncode=1,errors=[repr(e)],warnings=[],seconds=0))
    write(work/(c['id']+'.failed.json'),json.dumps(records));return {},{},records

def execute(cases,work,resume=False):
    rows=[];extras={};records=[];pending=[]
    for c in cases:
        p=work/(c['id']+'.json');q=work/(c['id']+'.csv')
        if resume and p.exists() and q.exists():
            try:
                d=json.loads(p.read_text());rr=list(csv.DictReader(q.open()))
                if len(rr)!=1 or rr[0]['returncode']!='0' or list(rr[0])!=FIELDS:raise ValueError('Incomplete CSV')
                if c['s9_test']=='K6' and 'bav99' not in d['extra']:raise ValueError('Missing diode/pin-current audit')
                if c['variant']=='B' and c['s9_test'] in ['K2','K6REC','K8']:
                    deck=(work/(c['id']+'.cir')).read_text()
                    if 'gmin=1e-12' not in deck or 'abstol=1e-10' not in deck:raise ValueError('Transient numerical settings changed')
                rows.append(d['row']);records+=d['records']
                for k,v in d['extra'].items():extras.setdefault(k,[]).extend(v)
                continue
            except (ValueError,KeyError):pass
        pending.append(c)
    print('BATCH',cases[0]['s9_test'] if cases else '',len(pending),'pending',len(rows),'resumed',flush=True)
    with ThreadPoolExecutor(max_workers=10) as pool:
        tasks={pool.submit(simulate,c,work):c for c in pending}
        count=0
        for fut in as_completed(tasks):
            row,ex,rec=fut.result();records+=rec;count+=1
            if row:rows.append(row)
            for k,v in ex.items():extras.setdefault(k,[]).extend(v)
            if not row or count%25==0 or count==len(pending):print('PROGRESS',count,'/',len(pending),'OK' if row else 'FAIL',tasks[fut]['id'],flush=True)
    return rows,extras,records

def protected():
    paths=[p for p in CH1.rglob('*') if p.is_file() and p.suffix.lower() not in ['.raw','.log','.db','.pyc'] and '__pycache__' not in p.parts]
    paths += [p for p in MODELS.rglob('*') if p.is_file()]
    paths += [PROJECT/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    def signature(p):
        if p.is_relative_to(MODELS) or p.suffix.lower() in ['.py','.inc','.md','.lib','.sub']:
            return 'sha256:'+hashlib.sha256(p.read_bytes()).hexdigest()
        stat=p.stat();return f'stat:{stat.st_size}:{stat.st_mtime_ns}'
    return {str(p):signature(p) for p in paths}

def batches(smoke=False,preflight=False):
    inds=[0,6] if smoke or preflight else range(12)
    bs=[[case('K1','A',i) for i in inds]]
    if preflight:return bs
    bs.append([case('K3',v,i) for v in ['A','B'] for i in inds])
    bs.append([sampling_case(s,r,f) for s in (['P'] if smoke else ['P','Z','R']) for r in ([825] if smoke else [400,825,1500]) for f in [.5e6,1e6]])
    n=2 if smoke else 500
    bs.append([case('K5AC',v,i,m) for v in ['A','B'] for i in ([0,6] if smoke else [0,3,6,9]) for m in range(n)])
    bs.append([case('K5NOISE',v,i,m) for v in ['A','B'] for i in [0,6] for m in range(1 if smoke else 100)])
    bs.append([case('K5OP',v,i,m) for v in ['A','B'] for i in ([0,6] if smoke else [0,3,6,9]) for m in range(n)])
    prot=[]
    for v in ['A','B']:
        for rp,rn in ([(4.8,5)] if smoke else [(4.8,4.8),(4.8,5),(5,4.8),(5,5)]):
            for ix,lim,cpl in ([(0,40,0),(6,100,0)] if smoke else [(i,40,0) for i in [0,1,5,6,11]]+[(i,100,cpl) for i in [0,6] for cpl in [0,1]]):
                prot.append(case('K6',v,ix,rail_plus_set_V=rp,rail_minus_set_V=rn,dc_limit_V=lim,CPL=cpl))
    bs.append(prot)
    rec=[]
    for v in ['A','B']:
        for ix,amps in ([(0,[.2,-.2]),(6,[40,-40])] if smoke else [(0,[.2,2,4.5,-.2,-2,-4.5]),(6,[20,40,-20,-40])]):
            rec += [case('K6REC',v,ix,kind='overload',amp=a) for a in amps]
    bs.append(rec)
    bs.append([case('K2',v,i,kind='step',amp=SCALES[i]) for v in ['A','B'] for i in inds])
    bs.append([case('K5OP',v,i) for v in ['A','B'] for i in inds])
    bs.append([case('K8',v,kind='idle') for v in ['A','B']])
    # ENCARGO K0 gate: native LM6172 current/BW disagree with supplied sheet.
    # Preserve earlier B diagnostics; do not qualify the rejected model.
    return [[c for c in batch if c['variant']=='A'] for batch in bs]

def optimize(work,resume):
    # Fixed starting ratio rounded to E96, then local 2-D fine sweep. No remedy search.
    e96=np.array([100,102,105,107,110,113,115,118,121,124,127,130,133,137,140,143,147,150,154,158,162,165,169,174,178,182,187,191,196,200,205,210,215,221,226,232,237,243,249,255,261,267,274,280,287,294,301,309,316,324,332,340,348,357,365,374,383,392,402,412,422,432,442,453,464,475,487,499,511,523,536,549,562,576,590,604,619,634,649,665,681,698,715,732,750,768,787,806,825,845,866,887,909,931,953,976],float)
    candidates=np.r_[e96,e96*10]
    near=lambda val:float(candidates[np.argmin(abs(np.log(candidates/val)))])
    pairs=sorted({(near(2490*f),near(1100*f)) for f in np.linspace(.75,1.25,21)})
    rr,ex,rec=execute([case('K1SWEEP','A',i,F1=a,F2=b) for a,b in pairs for i in [0,6]],work,resume)
    def choose(rows):
        ps=sorted({(r['F1'],r['F2']) for r in rows})
        score=lambda pair:max(abs(np.log(r['minus3_Hz']/1e6)) for r in rows if (r['F1'],r['F2'])==pair)
        return min(ps,key=score)
    best=choose(rr)
    aa=sorted(candidates,key=lambda a:abs(np.log(a/best[0])))[:5];bb=sorted(candidates,key=lambda b:abs(np.log(b/best[1])))[:5]
    r2,e2,re2=execute([case('K1SWEEP','A',i,F1=a,F2=b) for a in aa for b in bb for i in [0,6]],work,resume)
    rr+=r2;rec+=re2;best=choose(rr);FILTERS['A']=FILTERS['B']=best
    # B's historical preflight is retained; no new B run after the K0 gate.
    csv_write(ROOT/'resultados/s9_filtro_barrido.csv',rr,FIELDS)
    write(ROOT/'resultados/s9_filtros.json',json.dumps(FILTERS,indent=2))
    return rec

def sampling_case(state,rsw,target):
    odds=np.arange(1,N//2,2);m=int(odds[np.argmin(abs(odds*FS/N-target))]);f=m*FS/N
    return case('K4','A',kind='sampled',state=state,RSW=rsw,freq_Hz=float(f),M=m,target_Hz=target)

def sampling(c,work):
    # S6 fixed OPA836 and pin, one ADC instead of two. Ideal filter-output stimulus.
    head=[f'* {c["id"]}','.param AMP_S9_SELECT=0',f'.include "{INC}"',f'.include "{MODELS/"OPA836/opa836_a.lib"}"',f'.include "{MODELS/"AD8039/AD8038_ltspice.sub"}"',f'.include "{MODELS/"LM6172/lm6172.lib"}"','.param BUFFER_KIND=810','.options numdgt=15 plotwinsize=0 threads=1 method=gear solver=alt reltol=1e-5 abstol=1e-12 gminsteps=0','VDD VDDA 0 3.3','VREF REF 0 2.5','VDAC DAC 0 1.25','XREF INPUT REFERENCE VDDA REF DAC STAGE_S6']
    head.insert(1,'.subckt AMP_S9 IP IM VP VN OUT params: KIND=0\nXSELECT IP IM VP VN OUT AMP_S9_A\n.ends AMP_S9')
    guide=dict(c,s9_test='K4GUIDE',id=c['id']+'_guide')
    deck='\n'.join(head+['VI INPUT 0 0 AC 1','.save V(REFERENCE) V(INPUT)',f'.ac lin 3 {c["freq_Hz"]*.999:.17g} {c["freq_Hz"]*1.001:.17g}', '.end'])+'\n'
    ar,rec=native(guide,work,deck);records=[rec]
    if ar is None:raise ValueError('ADC AC calibration failed')
    amp=1/float(abs(ar['v(reference)'][1]))
    dr,rec=native(guide|{'id':guide['id']+'_op'},work,'\n'.join(head+['VI INPUT 0 0','.op','.save V(REFERENCE)', '.end'])+'\n');records.append(rec)
    if dr is None:raise ValueError('ADC OP calibration failed')
    gn=-old.NOM['R_F_S4']/old.NOM['R_IN_S4'];dc=(1.25-float(dr['v(reference)'][0]))/gn
    end=START+TS+(FIRST+N)*PERIOD;edge=20e-12;st={'P':0,'Z':1,'R':2}[c['state']]
    deck='\n'.join(head+[f'VI INPUT 0 SINE({dc:.17g} {amp:.17g} {c["freq_Hz"]:.17g})','XLOAD INPUT PIN VDDA REF DAC STAGE_S6',f'VCLK CLK 0 PULSE(0 1 {START-edge/2:.17g} {edge:.17g} {edge:.17g} {TS-edge:.17g} {PERIOD:.17g})','S1 PIN CS CLK 0 SAMPLE','CS CS 0 5p',f'BRESET RESET 0 V=if({st}>0,if(V(CLK)<0.5,1,0),0)',f'VPRE PRE 0 {2.5 if st==2 else 0}','SR PRE CS RESET 0 RESET',f'.model SAMPLE SW(Ron={c["RSW"]} Roff=1e15 Vt=0.5 Vh=0)', '.model RESET SW(Ron=1m Roff=1e15 Vt=0.5 Vh=0)', '.save V(PIN) V(REFERENCE) V(CS) V(CLK)',f'.meas TRAN {c["id"]}_adc_width TRIG V(CLK) VAL=.5 RISE=1 TARG V(CLK) VAL=.5 FALL=1',f'.meas TRAN {c["id"]}_adc_period TRIG V(CLK) VAL=.5 RISE=1 TARG V(CLK) VAL=.5 RISE=2',f'.tran 0 {end:.17g} 0 .5n','.end'])+'\n'
    # Names include actual calibrated stimulus.
    cc=dict(c,id=c['id'].replace('_acalculated_','_a'+old.s4.number(amp)+'_')+'_srcdc'+old.s4.number(dc),amplitude_V=amp)
    deck=deck.replace(c['id'],cc['id'])
    raw,rec=native(cc,work,deck,timeout=900);records.append(rec)
    if raw is None:raise ValueError('ADC transient failed')
    indices=np.arange(FIRST-1,FIRST+N);ts=START+TS+indices/FS;t=raw['time'];clk=raw['v(clk)'];cs=raw['v(cs)'];ys=[];ap=[]
    for when in ts:
        j=int(np.searchsorted(t,when))
        while clk[j-1]<.5:j-=1
        while clk[j]>=.5:j+=1
        l=j-1
        value=cs[l]+(when-t[l])*(cs[l]-cs[l-1])/(t[l]-t[l-1])
        closing=t[l]+(.5-clk[l])*(t[j]-t[l])/(clk[j]-clk[l])
        if abs(closing-when)>1e-12:raise ValueError('Aperture mismatch')
        ys.append(value);ap.append(dict(track_left_time_s=float(t[l]),track_left_clock_V=float(clk[l]),closing_clock_time_s=float(closing),closing_time_error_ps=float((closing-when)*1e12)))
    y=np.array(ys);ref=np.interp(ts,t,raw['v(reference)']);err=y[1:]-ref[1:]
    matrix=np.column_stack([ref[1:],ref[:-1],np.ones(N)]);coeff=np.linalg.lstsq(matrix,err,rcond=None)[0];res=err-matrix@coeff
    h=1+coeff[0]+coeff[1]*np.exp(-2j*np.pi*c['freq_Hz']/FS)
    sf,bins=old.a6.spectrum(y[1:],c['M']);rf,rbin=old.a6.spectrum(ref[1:],c['M'])
    row=dict(c,amplitude_V=amp,sfdr_db=sf['sfdr_db'],reference_sfdr_db=rf['sfdr_db'],fundamental_pp_V=sf['fundamental_pp_V'],residual_rms_LSB=old.a6.rms(res)/old.a6.LSB,residual_max_LSB=float(abs(res).max()/old.a6.LSB),error_max_LSB=float(abs(err).max()/old.a6.LSB),error_rms_LSB=old.a6.rms(err)/old.a6.LSB,gain_delta_db=float(20*np.log10(abs(h))),phase_delta_deg=float(np.angle(h,deg=True)),sample_width_ns=TS*1e9,sample_period_ns=PERIOD*1e9,closing_time_error_ps=max(abs(a['closing_time_error_ps']) for a in ap))
    samples=[dict(id=c['id'],n=i,time_s=float(tt),sample_V=float(vv),reference_V=float(rr),error_V=float(vv-rr),**aa) for i,(tt,vv,rr,aa) in enumerate(zip(ts[1:],y[1:],ref[1:],ap[1:]))]
    br=[dict(id=c['id'],sequence=name,bin=i,freq_Hz=float(i*FS/N),amplitude_V=float(v)) for name,arr in [('loaded',bins),('reference',rbin)] for i,v in enumerate(arr)]
    return row,dict(samples=samples,bins=br),records

def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--preflight',action='store_true');p.add_argument('--optimize',action='store_true');args=p.parse_args()
    profile='preflight' if args.preflight else 'smoke' if args.smoke else 'campaign';work=ROOT/'S9'/profile;work.mkdir(parents=True,exist_ok=True)
    filt=ROOT/'resultados/s9_filtros.json'
    if filt.exists():FILTERS.update(json.loads(filt.read_text()))
    previous_meta=json.loads((work/'s9_meta.json').read_text()) if args.resume and (work/'s9_meta.json').exists() else {}
    before=protected();write(work/'protected_before.json',json.dumps(before));start=time.perf_counter();records=[]
    if args.optimize:records+=optimize(ROOT/'S9'/'optimize',args.resume)
    if args.preflight:
        dist=[dict(mc=n,rail_plus_V=r['rp'],rail_minus_mag_V=r['rn'],vref_V=r['vref'],**r['offsets']) for n in range(10) for r in [sb.realization(n)]]
        csv_write(work/'s9_mc_10.csv',dist,list(dist[0]))
        components=[r for n in range(10) for r in mc_subcircuits(case('K5AC','A',0,n))[1]]
        csv_write(work/'s9_mc_10_components.csv',components,['id','variant','mc','component','nominal_SI','tolerance','draw','factor','value_SI','seed'])
    rows=[];extras={};expected=0
    for batch in batches(args.smoke,args.preflight):
        expected+=len(batch);rr,ex,rec=execute(batch,work,args.resume);rows+=rr;records+=rec
        for k,v in ex.items():extras.setdefault(k,[]).extend(v)
        csv_write(work/'s9_all.csv',rows,FIELDS)
        write(work/'s9_checkpoint.json',json.dumps(dict(rows=rows,extras=extras,records=records)))
    after=protected();changed=[k for k,v in before.items() if after.get(k)!=v];write(work/'protected_after.json',json.dumps(after))
    meta=dict(returncode=int(len(rows)!=expected or bool(changed)),logical_cases=expected,successful=len(rows),simulations=sum(1 for r in records if '_analysis_attempt' not in r['id']),seconds=time.perf_counter()-start+previous_meta.get('seconds',0),workers=10,seed=SEED,profile=profile,protected_count=len(before),protected_changed=changed,filters=FILTERS)
    write(work/'s9_meta.json',json.dumps(meta,indent=2));write(work/'s9_records.json',json.dumps(records,indent=2))
    out=ROOT/'resultados' if profile=='campaign' else work
    csv_write(out/'s9_all.csv',rows,FIELDS)
    for test in sorted({r['test'] for r in rows}):csv_write(out/('s9_'+test.lower()+'.csv'),[r for r in rows if r['test']==test],FIELDS)
    for key,rs in extras.items():
        csv_write(out/f's9_{key}.csv',rs,EXTRA_FIELDS[key])
    print(json.dumps(meta),flush=True);return meta['returncode']
if __name__=='__main__':raise SystemExit(main())
