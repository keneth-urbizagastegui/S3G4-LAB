"""S12c from S12b, isolated outputs; 10 workers, signed resume, 900s/case.
Manufacturer files/previous campaigns read-only. No downloads.
"""
from pathlib import Path
HERE=Path(__file__).resolve().parent
_b=(HERE/'ejecutar_s12b.py').read_text(encoding='utf-8')
_b=_b.replace('S12b','S12c').replace('s12b_','s12c_').replace('dmm_bloque2b.inc','dmm_bloque2c.inc')
_b=_b.replace("\nif __name__=='__main__':raise SystemExit(main())",'')
exec(compile(_b,str(HERE/'ejecutar_s12b.py'),'exec'),globals())

RANGES=((.2,0,10.1,10e-6),(2,0,1,100e-6),(20,2,10.1,1e-3),(50,2,1,.01))
_bdeck=deck;_baudit=audit;_bmain=main;_bprotection=protection_deck
_basecases=_cases

def ident(c):
    d={k:v for k,v in c.items() if k not in ('base','params')}
    result=_ident(d)
    if c.get('base'):
        b=dict(c['base'],rx1='none')
        result+='_'+protection.name(b).replace('rx100_100_none','rx100_none_none')
    return result.lower().replace('.','d').replace('-','m').replace('+','p')

def cases(n=200):
    global PRIORITY
    priority=PRIORITY;PRIORITY=('E4','E1','E2','E3','E5','E6','E7','C2','C3','Q0')
    try:old=_basecases(n)
    finally:PRIORITY=priority
    out=[]
    for c in old:
        if c['q']=='E3':
            for amp in sorted(set((0,c['amp'],-c['amp'],20,-20,50,-50))):
                out.append(dict(c,amp=amp,stop=.028,pretime=.020))
        elif c['q']=='E2':
            factor=2**((c['temp']-23)/10)
            out.append(dict(c,leak=.85e-9*factor,bleak=.6e-9*factor,stop=.422,method='plateau'))
        elif c['q']=='E6':
            for tau in (1e-9,1e-7):
                out.append(dict(c,chain='gdtmov',tau=tau))
                out.append(dict(c,q='E8',chain='gdtmov',tau=tau))
        elif c['q']=='C2' and c['sel']==1:
            out.append(dict(c,sel=2,gain=10.1))
        else:out.append(c)
    template=next(c for c in old if c['q']=='E2')
    for amp in (-50,50):out.append(dict(template,q='E8',kind='stress50',amp=amp,sel=2,gain=1,leak=0,stop=.003))
    # Full-signal RMS check with transient NXP mux, every range, 40/100/1k/20k.
    # Covers 50Vrms=70.7107Vpk explicitly, all routes remain connected.
    for fs,sel,g,lsb in RANGES:
        for f in (40,100,1000,20000):
            out.append(dict(template,q='E1',kind='fullac',sel=sel,gain=g,amp=fs*math.sqrt(2),rms=fs,freq=f,leak=0,bleak=0,temp=23,stop=max(.004,6/f)))
    # E3 AC checks for every selected range at 50Vrms; rail qualification only.
    for fs,sel,g,lsb in RANGES:
        for f in (40,20000):
            out.append(dict(template,q='E3',kind='railac',sel=sel,gain=g,amp=50*math.sqrt(2),rms=50,freq=f,leak=0,bleak=0,temp=23,stop=max(.004,6/f)))
    return sorted(out,key=lambda c:priority.index(c['q']))

def deck(c):
    if c['kind']=='protection':return protection_deck(c)
    if c['kind'] in ('fullac','railac'):
        cc=dict(c,kind='sine',q='AC_TRANSIENT');text=_bdeck(cc)
        text=text.replace(f'SINE(0 {c["amp"]} 20k)',f'SINE(0 {c["amp"]} {c["freq"]})')
        step=min(1e-6,1/(c['freq']*300))
        text=text.replace(f'.tran 0 {c["stop"]} 0 100n',f'.tran 0 {c["stop"]} 0 {step:.12g} uic')
        text=re.sub(r'^\.meas tran .*__rms .*$',f'.meas tran {ident(c)}__rms RMS V(out) FROM={c["stop"]-2/c["freq"]} TO={c["stop"]}',text,flags=re.M)
        text=text.replace('.end','.options solver=norm method=trap reltol=.003\n.end')
    else:text=_bdeck(c)
    # X1 at COM for both AC selected path and all transient eight-channel models.
    text=text.replace('X1 ctl1 bx1 mux','X1 ctl1 0 mux').replace('Rsel bx1 mux','Rsel 0 mux')
    if c['kind']=='recover' and c['model']=='188':
        # External DC initialization constraints, released for transient;
        # the original4V OP and UIC are numerically pathological for TI188.
        initial_out=3.4 if c['gain']==1 else 4.78
        initial_inv=initial_out/c['gain']
        text=text.replace('.end',f'.ic V(out)={initial_out} V(mux)=4 V(bx0)=4 V(inv)={initial_inv} V(bi0)=4 V(bn0)=4\n.options solver=norm method=trap reltol=.003 gminsteps=0 srcsteps=0\n.end')
    if c['kind'] in ('zero','recover','gain','sine') and not (c['kind']=='recover' and c['model']=='188'):
        # SWI1 is specified for transient only; avoid pathological DC source
        # stepping. Keep the physical preconditioning interval before metrics.
        text=re.sub(r'(?m)^(\.tran [^\n]*?)(?: uic)?$',r'\1 uic',text)
    if c['kind']!='loop':
        # S12c requests CD(ON) repartition for loop cases only. Keep the S12b
        # transient/calibration model intact for comparisons and gain switches.
        text=text.replace('Ctm inv 0 5p','Ctm inv 0 10p')
        text=re.sub(r'(?m)^Ctmo(?:1|10) .*\n','',text)
    text=re.sub(r'\b(?:V\(bx1\)|I\(Vib1\)|I\(Vibn1\))[ \t]*','',text,flags=re.I)
    # Prefixes reflect actual S12c state, even when constructed by inherited CC.
    text=re.sub(r'(?m)^(\.meas\s+\w+\s+)\S+?__',lambda m:m[1]+ident(c)+'__',text)
    if c['q'] in ('E3','E8') or c['kind']=='fullac':
        text=re.sub(r'(?m)^\.end\s*$', '.save V(bx0) V(x2) V(bi0) V(bn0) V(vp) V(vn) I(Vib0) I(Vibn0)\n.end', text)
    return text

def protection_deck(c):
    # Reuse S12b builder unchanged first, then remove its entire X1 exposure.
    text=_bprotection(c)
    text=re.sub(r'(?m)^(?:D1p|D1n|Rx1|Vib1|Vibn1|Xbpin1|Ebi1|Xbuf1|Cbd1|Xh1|Cin1)\s[^\n]*\n','',text)
    text=text.replace('Rselected bx1 mux','Rselected 0 mux')
    # Any reduced capacitive load on hx1 is gone with the removed tap.
    text=re.sub(r'(?m)^\w[^\n]*\bhx1\b[^\n]*\n','',text)
    text=re.sub(r'\b(?:V\(bi1\)|V\(bx1\)|I\(Vib1\)|I\(Vibn1\))[ \t]*','',text,flags=re.I)
    text=text.replace('Riqbuffers rp rn {9.8/.002}','Riqbuffers rp rn {9.8/.001}')
    text=text.replace('IC budget5.116mA','IC budget4.116mA')
    text=re.sub(r'(?m)^\.end\s*$', '.save V(bni0) I(Xbpin0:Dhi) I(Xbpin0:Dlo)\n.end', text)
    return text

def audit(c,path):
    if c['kind']=='protection':
        # S12b impulse audit independent of discarded buffer1 traces.
        d=raw(path);t=np.abs(np.asarray(d['time']));v=lambda n:np.asarray(d['v('+n+')'])
        r={}
        pieces=[(f'r{i}{s}',a,b,1.5e6,200.) for i,x,y in ((1,'vin','d1'),(2,'d1','d2'),(3,'d2','x1')) for s,a,b in (('a',x,f'mid{i}'),('b',f'mid{i}',y))]
        pieces += [('r910k','x1','x2',910e3,200.),('r100k','x2','0',100e3,200.)]
        pieces += [(f'rc{i}',a,f'c{i}',3300.,None) for i,a in ((1,'vin'),(2,'d1'),(3,'d2'))]
        for part,a,b,res,rating in pieces:
            y=v(a)-(0 if b=='0' else v(b))
            r[part+'_peak_V']=float(np.max(np.abs(y)));r[part+'_energy_J']=float(np.trapezoid(y*y/res,t))
            r[part+'_above_work_s']=duration_above(t,y,rating) if rating else None
            if rating is None:
                for threshold in (200,400,1000,1500):r[f'{part}_above_{threshold}V_s']=duration_above(t,y,threshold)
        for i,a,b,cap in ((1,'c1','d1',100e-12),(2,'c2','d2',100e-12),(3,'c3','x1',100e-12),(4,'x1','x2',330e-12),(5,'x2','0',3e-9)):
            y=v(a)-(0 if b=='0' else v(b));r[f'c{i}_peak_V']=float(np.max(np.abs(y)));r[f'c{i}_stored_peak_J']=float(np.max(.5*cap*y*y))
        hi=np.asarray(d['i(xbpin0:dhi)']);lo=np.asarray(d['i(xbpin0:dlo)'])
        r['buffer0_clamp_peak_A']=float(max(np.max(np.abs(hi)),np.max(np.abs(lo))))
        r['buffer0_total_peak_A']=float(np.max(np.abs(d['i(vib0)'])))
        r['buffer0_capacitive_peak_A']=float(np.max(np.abs(np.asarray(d['i(vib0)'])-(hi-lo))))
        r['input_current_pass']=r['buffer0_clamp_peak_A']<=.005
        r['vin_peak_V']=float(np.max(np.abs(v('vin'))));return r
    if c['q']=='E2':return _baudit(c,path)
    if c['q'] in ('E3','E8') or c['kind']=='fullac':
        d=raw(path);t=np.abs(np.asarray(d['time']));r={}
        for node in ('bx0','x2','bi0','bn0'):
            r[node+'_peak_V']=float(np.max(np.abs(d['v('+node+')'])))
        r['all_channels_rail_pass']=max(r['bx0_peak_V'],r['x2_peak_V'])<=c['rail']
        r['buffer_input_cm_pass']=r['bi0_peak_V']<=c['rail']
        r['buffer0_total_peak_A']=float(np.max(np.abs(d['i(vib0)'])))
        # TI model includes input conduction. Separately report excess beyond
        # +/-0.5V clamp threshold, inferred IV (same assumption as S12b).
        bi=np.asarray(d['v(bi0)']);vp=np.asarray(d['v(vp)']);vn=np.asarray(d['v(vn)'])
        clamp=np.maximum(bi-vp-.5,0)-np.maximum(vn-bi-.5,0)
        r['buffer0_clamp_inferred_peak_A']=float(np.max(np.abs(clamp)))
        if c['kind']=='stress50':
            # PINOPA's 0.5V/1ohm IV is NOT the TI ESD IV. Subtract TI's
            # actual 6.4p/1.6p displacement at internal ESDP/ESDN, after its
            # 100ohm input resistors. MID is constant with fixed +/- rails.
            tt,ix=np.unique(t,return_index=True)
            ip=np.asarray(d['i(vib0)'])[ix];inn=np.asarray(d['i(vibn0)'])[ix]
            ep=bi[ix]-100*ip;en=np.asarray(d['v(bn0)'])[ix]-100*inn
            capacitive=6.4e-12*np.gradient(ep,tt)+1.6e-12*np.gradient(ep-en,tt)
            r['buffer0_clamp_peak_A']=float(np.max(np.abs(ip-capacitive)))
            r['buffer0_clamp_method']='TI_input_R100_Ccm6.4p_Cdiff1.6p_subtraction;constant_MID;Ib_included'
            r['invalid_PINOPA_IV_inference_A']=r.pop('buffer0_clamp_inferred_peak_A')
            switches=[f'i(xbuf0:x_u5:s{i})' for i in (1,2,3,4)]
            if all(k in d for k in switches):
                r['buffer0_TI_direct_clamp_peak_A']=float(max(np.max(np.abs(d[k])) for k in switches))
                r['TI_decomposition_delta_A']=abs(r['buffer0_TI_direct_clamp_peak_A']-r['buffer0_clamp_peak_A'])
                r['buffer0_clamp_peak_A']=r['buffer0_TI_direct_clamp_peak_A']
            r['input_current_pass']=r['buffer0_clamp_peak_A']<=.005
        if c['kind'] in ('fullac','railac'):
            f=c['freq'];grid=np.linspace(c['stop']-2/f,c['stop'],12000,endpoint=False)
            wave=np.interp(grid,t,d['v(out)']);inp=np.interp(grid,t,d['v(vin)'])
            r['rms_V']=float(np.sqrt(np.mean(wave**2)));r['input_rms_V']=float(np.sqrt(np.mean(inp**2)))
            wave-=np.mean(wave);spec=np.abs(np.fft.rfft(wave));r['thd_pct']=float(np.sqrt(sum(spec[2*j]**2 for j in range(2,10)))/spec[2]*100)
            r['transfer_rms']=r['rms_V']/r['input_rms_V']
            return r
        if c['q']=='E3':
            selnode='bx0' if c['sel']==0 else 'x2';other='x2' if c['sel']==0 else 'bx0'
            before=t<.021002
            r['unselected_channels_peak_V']=max(r[other+'_peak_V'],float(np.max(np.abs(d['v('+selnode+')'][before]))))
            r['unselected_channels_rail_pass']=r['unselected_channels_peak_V']<=c['rail']
            fs=next(x for x in RANGES if x[1]==c['sel'] and x[2]==c['gain'])
            r['in_range']=abs(c['amp'])<=fs[0]
            if r['in_range']:
                div=1 if c['sel']==0 else .1/10.01;lsb=fs[3]*div*c['gain'];expected=c['amp']*div*c['gain']
                tt=t-c.get('pretime',0);wait=.0001 if c['sel']==0 else .0015
                r['error_at_wait_counts']=(float(np.interp(.001+wait,tt,d['v(out)']))-expected)/lsb
                r['error_at_3ms_counts']=(float(np.interp(.004,tt,d['v(out)']))-expected)/lsb
                r['one_count_pass']=abs(r['error_at_wait_counts'])<=1
                tail=float(np.mean(d['v(out)'][tt>.0078]));r['final_error_counts']=(tail-expected)/lsb
                r['settle_s']=settle(tt,d['v(out)'],.001,expected,lsb) if abs(tail-expected)<=lsb else None
        return r
    r=_audit(c,path)
    if c['kind']=='loop':
        d=raw(path);f=np.real(d['frequency']);loop=-d['v(out)'] if c['q']=='Q0' else -d['v(inv)']/d['v(test)']
        mag=np.abs(loop);phase=np.unwrap(np.angle(loop))*180/np.pi
        crossings=np.flatnonzero((mag[:-1]>1)&(mag[1:]<=1))
        if not len(crossings):raise ValueError('unity crossing missing')
        i=int(crossings[0]);x=-np.log(mag[i])/(np.log(mag[i+1])-np.log(mag[i]))
        r['pm_grid_deg']=r['pm_deg'];r['pm_deg']=float(180+phase[i]+x*(phase[i+1]-phase[i]))
        r['unity_hz']=float(np.exp(np.log(f[i])+x*(np.log(f[i+1])-np.log(f[i]))))
    if c['q']=='E7':
        fs=next(x for x in RANGES if x[1]==c['sel'] and x[2]==c['gain']);div=1 if c['sel']==0 else .1/10.01
        r['noise_counts']=r['noise_rms_V']/(fs[3]*div*c['gain']);r['noise_autozero_counts']=math.sqrt(2)*r['noise_counts']
    return r

def dc_budget():
    rng=np.random.default_rng(1202);tc=rng.uniform(-25e-6,25e-6,(10000,10));rs=np.array([1.5e6]*6+[910e3,100e3,91e3,10e3]);out=[]
    drift=math.sqrt(2)-1
    for fs,sel,g,lsb in RANGES:
        div=1 if sel==0 else .1/10.01;input_lsb=lsb*div
        source=99100 if sel==0 else 100e3*9.91e6/10.01e6
        mux_r=71 if sel==0 else source+70
        gains=[]
        for dt in (-5,5):
            rr=rs*(1+tc*dt);ratio=1 if sel==0 else rr[:,7]/np.sum(rr[:,:8],axis=1)
            gg=1 if g==1 else 1+rr[:,8]/rr[:,9]
            gains.append(np.abs(np.asarray(ratio/div*gg/g)-1)*1e6)
        fixed=(2.5e-6*(2 if sel==0 else 1)+20e-12*(source+mux_r if sel==0 else mux_r)*drift+(.3e-9*91000/g*drift if g>1 else 0))/input_lsb
        # X0: existing COM .85nA plus Yn1nA see buffer output. X2: solve
        # aggregate allowable source leakage, including Yn/COM/PCB, not buffer1.
        per=1e-9*(source if sel==0 else mux_r)*drift/input_lsb
        if sel==0:fixed+=1.85e-9*mux_r*drift/input_lsb;used=.6
        else:used=1.85
        out.append(dict(range_V=fs,gain_p95_ppm=float(np.percentile(np.maximum(*gains),95)),offset_budget_counts=fixed+used*per,leak_max_nA=max(0,(4-fixed)/per),fixed_counts=fixed,assumed_leak_nA=used,leak_node='X0_total_external_plus_Ib_reserve' if sel==0 else 'X2_aggregate_Yn_COM_PCB',population=10000,assumptions='23C_cal;18_28C;double_per10C;SOIC_drift;Ib20pA;TMUX0.3nA'))
    writecsv(RESULTS/'s12c_dc_budget.csv',out);return out

# Short filenames contain a hash of complete state; .meas keeps full identity.
# Include all inherited source files and manufacturer dependencies in resume.
def signature(content):
    deps=[Path(__file__),HERE/'ejecutar_s12b.py',HERE/'ejecutar_s12.py',HERE/'comun/dmm_bloque2c.inc',HERE/'gdt_seguimiento/gdt_seguimiento.py']
    deps += [HERE/f'ejecutar_s11_{i}.py' for i in (1,2,3,4)]
    deps += list((HERE/'comun').glob('*s11*.inc'))+[HERE/'comun/dmm_bloque1_final.inc']
    deps += [MODELS/'OPA2192/OPAx192.LIB',MODELS/'OPA2188/OPAx188.LIB',MODELS/'74HC4051/hc_tnomi.cir',protection.STANDARD]
    return hashlib.sha256(content.encode()+b''.join(p.read_bytes() for p in deps)).hexdigest()

def run(c,resume=False):
    content=deck(c);name=c['q'].lower()+'_'+hashlib.sha256(ident(c).encode()).hexdigest()[:20]
    p=JOBS/(name+'.cir');stamp=p.with_suffix('.json');digest=signature(content)
    if resume and stamp.exists():
        r=json.loads(stamp.read_text())
        if r.get('signature')==digest and r.get('status')=='ok' and p.read_text(encoding='utf-8')==content:return dict(r,reused=True)
    p.write_text(content,encoding='utf-8');start=time.perf_counter();r={k:v for k,v in c.items() if k not in ('params',)}
    r.update(id=name,physical_state=ident(c),signature=digest,status='ok')
    try:
        proc=subprocess.Popen([str(LT),'-b',str(p)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
        try:r['returncode']=proc.wait(timeout=900)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],capture_output=True);raise TimeoutError('900s')
        vals,log=parse_log(p.with_suffix('.log'))
        if 'rms' in c and 'rms' in vals:vals['out_rms_V']=vals.pop('rms')
        r.update(vals)
        if r['returncode'] or 'Fatal Error' in log or not vals:raise RuntimeError(log[-800:])
        r.update(audit(c,p.with_suffix('.raw')))
    except Exception as e:r.update(status='error',error=str(e))
    r['elapsed_s']=time.perf_counter()-start;stamp.write_text(json.dumps(r,indent=2),encoding='utf-8');return r

def collect(n=200):
    """Reaudit identical decks; explicitly rerun invalid/changed decks only.
    Preserve previous signatures and original campaign timings/reuse evidence.
    """
    start=time.perf_counter();cs=cases(n);rows=[];repair=[]
    oldrows={r['id']:r for r in csv.DictReader((RESULTS/'s12c_campaign.csv').open(encoding='utf-8-sig'))}
    for c in cs:
        name=c['q'].lower()+'_'+hashlib.sha256(ident(c).encode()).hexdigest()[:20]
        p=JOBS/(name+'.cir');stamp=p.with_suffix('.json');content=deck(c)
        if not stamp.exists() or p.read_text(encoding='utf-8')!=content:
            repair.append(c);continue
        r=json.loads(stamp.read_text())
        if r['status']!='ok':repair.append(c);continue
        old=r['signature'];r['signature']=signature(content)
        if r['signature']!=old:r.setdefault('signature_history',[]).append(dict(signature=old,reason='exact_saved_deck_proof;source_audit_revision'))
        if c['kind']=='stress50':r.update(audit(c,p.with_suffix('.raw')))
        if 'rms' in c:
            if r.get('rms')!=c['rms']:r['out_rms_V']=r.get('rms')
            r['rms']=c['rms']
        r['reaudited_exact_deck']=True
        stamp.write_text(json.dumps(r,indent=2),encoding='utf-8')
        rows.append(dict(r,reused=oldrows[name].get('reused')=='True'))
    with cf.ThreadPoolExecutor(max_workers=10) as pool:
        for fut in cf.as_completed([pool.submit(run,c,False) for c in repair]):rows.append(fut.result())
    writecsv(RESULTS/'s12c_campaign.csv',rows)
    # Update smoke records, retaining the measured smoke timing metadata.
    smoke=RESULTS/'s12c_smoke.csv';smokeids=[r['id'] for r in csv.DictReader(smoke.open(encoding='utf-8-sig'))]
    current={r['id']:r for r in rows};writecsv(smoke,[dict(current[i],reused=False) for i in smokeids])
    summary=json.loads((RESULTS/'s12c_campaign.json').read_text(encoding='utf-8'))
    if 'collect_elapsed_s' in summary:
        summary.setdefault('collect_history',[]).append({k:summary[k] for k in ('collect_elapsed_s','collect_reexecuted','ok')})
    summary['ok_before_collect']=summary['ok'];summary['ok']=sum(r['status']=='ok' for r in rows)
    summary['collect_elapsed_s']=time.perf_counter()-start;summary['collect_reexecuted']=len(repair)
    summary['reaudited_exact_deck']=len(rows)-len(repair);summary['audit_source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    (RESULTS/'s12c_campaign.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');dc_budget();print(json.dumps(summary),flush=True)
    for r in rows:
        if r['status']!='ok':print('ERROR',r['id'],r.get('error','')[:300],flush=True)
    return int(summary['ok']!=len(rows))

def main():
    ap=argparse.ArgumentParser()
    for flag in ('smoke','resume','build','collect'):ap.add_argument('--'+flag,action='store_true')
    ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10);ap.add_argument('--n',type=int,default=200)
    a=ap.parse_args();JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True);cs=cases(a.n)
    if a.collect:return collect(a.n)
    if a.only:cs=[c for c in cs if c['q'] in a.only]
    if a.smoke:
        selected=[next(c for c in cs if c['q']==q) for q in PRIORITY if any(c['q']==q for c in cs)]
        predicates=[lambda c:c['kind']=='fullac' and c['rms']==50 and c['freq']==20000,
                    lambda c:c['kind']=='railac' and c['sel']==2 and c['gain']==1 and c['freq']==40,
                    lambda c:c['q']=='E5' and c['kind']=='loop' and c['tmux']==400,
                    lambda c:c['q']=='E3' and c['kind']=='zero' and c['sel']==2 and c['gain']>1 and c['amp']==20]
        for pred in predicates:
            found=next((c for c in cs if pred(c)),None)
            if found is not None and found not in selected:selected.append(found)
        cs=selected
    if a.build:
        for c in cs:
            name=c['q'].lower()+'_'+hashlib.sha256(ident(c).encode()).hexdigest()[:20]
            (JOBS/(name+'.cir')).write_text(deck(c),encoding='utf-8')
        print(json.dumps({'built':len(cs)}));return 0
    start=time.perf_counter();rows=[]
    with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
        for q in PRIORITY:
            group=[c for c in cs if c['q']==q]
            for fut in cf.as_completed([pool.submit(run,c,a.resume) for c in group]):
                r=fut.result();rows.append(r)
                if r['status']!='ok':print('ERROR',r['id'],r['error'][:300],flush=True)
            if group:print(q,len(group),'ok',sum(r['status']=='ok' for r in rows if r['q']==q),flush=True)
    dest=RESULTS/f's12c_{"smoke" if a.smoke else "campaign"}.csv';writecsv(dest,rows)
    summary=dict(total=len(rows),ok=sum(r['status']=='ok' for r in rows),elapsed_s=time.perf_counter()-start,reused=sum(r.get('reused',False) for r in rows),workers=a.workers,timeout_s=900,n_population=a.n,started_local=time.strftime('%Y-%m-%dT%H:%M:%S%z',time.localtime(time.time()-(time.perf_counter()-start))))
    dest.with_suffix('.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');dc_budget();print(json.dumps(summary),flush=True)
    return int(summary['total']!=summary['ok'])

if __name__=='__main__':raise SystemExit(main())
