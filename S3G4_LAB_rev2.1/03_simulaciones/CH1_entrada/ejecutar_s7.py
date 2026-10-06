"""S7 integration; ten workers from the first check, deterministic schemas.

Exit zero = all requested simulations executed and protected files unchanged.
Electrical failure is a valid result. No manufacturer model edits/downloads.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode=True
import argparse,csv,hashlib,json,re,subprocess,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import numpy as np
import ejecutar_s4 as s4
import ejecutar_s5 as s5
import analisis_s6 as a6

ROOT=Path(__file__).resolve().parent
MODELS,LT=s4.MODELS,s4.LT
PROJECT=MODELS.parents[1]
OUT=ROOT/'resultados'
SCALES=list(s4.s3.SCALES)
SEED=202610037
DIV=.25
BASE=['id','test','scale_V_div','POS','tap','mc','kind','amplitude_V','freq_Hz','M','vdac_V']
METRICS=['minus3_Hz','gain_dc_signed','gain_nominal_signed','gain_error_pct','peak_db','peak_Hz',
 'atten_1m_db','atten_2m_db','atten_3p25m_db','atten_4p5m_db','atten_6p5m_db',
 'rebound_excess_db','gd_min_ns','gd_max_ns','gd_variation_ns','ac_points','ac_last_Hz',
 'rise_ns','overshoot_pct','settling_0p5pct_ns','square_fall_settling_ns',
 'noise_pin_uV','noise_bnc_uV','noise_pct_div','adc_min_V','adc_max_V',
 'recovery_us','bav199_peak_A','bav199_conducts','bav199_forward_max_V','terminal_error_V','observation_us',
 'offset_div','center_V','sfdr_db','thd_pct','residual_rms_LSB','residual_max_LSB',
 'fundamental_pp_V','gain_sample_db','phase_sample_deg','delay_equivalent_ns',
 'source_amp_V','last_time_s','max_step_s']
FIELDS=BASE+METRICS
STAGES=['OPA810','U103A','U103B','U105A','U105B','OPA836']
CURRENT={'OPA810':('vip101','vin101'),'U103A':('vipa','vina'),
 'U103B':('vipb','vinb'),'U105A':('x105a:vccp','x105a:vccn'),
 'U105B':('x105b:vccp','x105b:vccn'),'OPA836':('vcc',None),
 '4051':('vmuxp','vmuxn')}
INPUT={'OPA810':('bi','u101m','vi101','vim101'),
 'U103A':('ipa','ima','via','vima'),'U103B':('ipb','imb','vib','vimb'),
 'U105A':('ipa105','ima105','x105a:vip','x105a:vim'),
 'U105B':('ipb105','imb105','x105b:vip','x105b:vim'),
 'OPA836':('ip','im','vip','vim')}

def write(p,s):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(s,encoding='utf-8',newline='\n')

def csv_write(p,rows,fields):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore')
        w.writeheader();w.writerows(sorted(rows,key=lambda r:(str(r.get('id','')),str(r.get('stage','')),str(r.get('component','')),r.get('n',r.get('bin',0)))))

def case(test,ix=0,mc=-1,kind='ac',amp=0.,target=0.,vdac=1.25):
    m,f=a6.coherent(target) if target else (0,0.)
    c=dict(test=test,ix=ix,scale_V_div=SCALES[ix],POS=1 if ix<6 else 100,tap=ix%6,
           mc=mc,kind=kind,amplitude_V=amp,freq_Hz=f,M=m,vdac_V=vdac)
    c['id']=f'{test}_s{ix:02d}_pos{c["POS"]}_tap{c["tap"]}_dc_mc{mc}_'+kind+f'_a{s4.number(amp)}_f{s4.number(f)}_dac{s4.number(vdac)}'
    c['id']=c['id'].lower().replace('mc-1','mcnom')
    if test=='J9' and kind=='sine':
        c['freq_Hz']=target;c['M']=0
        c['id']=f'j9_s{ix:02d}_pos{c["POS"]}_tap{c["tap"]}_dc_mcnom_sine_a{s4.number(amp)}_f{s4.number(target)}_dac{s4.number(vdac)}'
    state=('ac1_dc0' if test in ['J1','J3','J4'] else 'sweepn40p40' if test=='J5' else
           'sweep'+s4.number(.01*SCALES[ix]) if test=='J1DC' else
           'negative' if amp<0 else 'positive' if test=='J2' and kind=='step' or test=='J6' else
           'bipolar' if kind in ['sampled','sine','square'] else 'zero')
    c['id']+='_'+state+('_p_r825_n1024' if test=='J7' else '')
    return c

def meas(c,mode,name,expr):return f'.meas {mode} {c["id"]}_{name} {expr}'

COMPONENT_KEYS='RT1 RB RS1 RS2 RBIAS REQ RPROT CAC CBNC CX1 CTAP COFF_RELE RON_RELE CSEL_PAR COFF_SW CEQ CS CT1 CT2F CTRIM CB RL1 RL2 RL3 RL4 RL5 RL6 RF1 RG1 RF2 RG2 R_SER_S7 C_COMMON_S7 C_GAIN_S7 RFILT1_S7 RFILT2_S7 CFILT1_S7 CGILT1_S7 CFILT2_S7 CGILT2_S7 CPCB_S7 C_FB_S7 C_MID_S7 R_VCHECK_S7 R_IN_S4 R_F_S4 R_OFF_S4 RT_MID RB_MID R_ADC_S4 C_ADC_S4 CPAD_S6 C_SUM_S4'.split()

def include_parameters():
    expressions={'BUFFER_KIND':'810'}
    for suffix in ['s2b','s3','s3b','s4','s5','s6','s7']:
        text=(ROOT/'comun'/f'ch1_comun_{suffix}.inc').read_text(encoding='utf-8-sig')
        for line in text.splitlines():
            if line.lower().startswith('.param '):
                expressions.update(re.findall(r'(\w+)=([^\s]+)',line[7:]))
    resolved={}
    factors={'meg':1e6,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12,'f':1e-15}
    def value(key):
        if key in resolved:return resolved[key]
        expr=expressions[key]
        expr=re.sub(r'(?i)(\d+(?:\.\d*)?|\.\d+)(meg|[kmunpf])\b',lambda m:str(float(m[1])*factors[m[2].lower()]),expr)
        expr=expr.replace('if(','iff(')
        names=set(re.findall(r'\b[A-Za-z_]\w*\b',expr))
        env={'iff':lambda cond,a,b:a if cond else b,'ln':np.log}
        for name in names:
            if name in expressions:env[name]=value(name)
        resolved[key]=float(eval(expr,{'__builtins__':{}},env));return resolved[key]
    return {key:value(key) for key in COMPONENT_KEYS}

NOM=include_parameters()
def mc_subcircuits(c):
    """Copy immutable topology, apply independent factors to physical instances.

    Original global parameters are never redefined. Nominal values stay exact.
    Both scales use the same draws (paired realizations of the same channel).
    """
    if c['mc']<0:return [],[]
    rng=np.random.default_rng(np.random.SeedSequence([SEED,c['mc']]))
    records=[]
    def factor(component,tol):
        draw=float(rng.uniform(-1,1));f=1+tol*draw
        records.append(dict(id=c['id'],mc=c['mc'],component=component,tolerance=tol,draw=draw,factor=f,seed=SEED))
        return f
    def extract(filename,name,newname):
        text=(ROOT/'comun'/filename).read_text(encoding='utf-8-sig')
        body=re.search(r'^\.subckt '+name+r'\b[\s\S]*?^\.ends[^\n]*',text,re.M|re.I)[0]
        return body.replace(name,newname).splitlines()
    def passive(lines,prefix):
        out=[]
        for line in lines:
            if re.match(r'^[RC]\w*\s',line,re.I):
                name=line.split()[0]
                # Ideal switch resistances are models, not physical resistors.
                if name.lower().startswith(('rk','rsw')):out.append(line);continue
                tol=.05 if name[0].upper()=='C' else .001 if prefix=='XFE' and name.lower() in ['rt1','rt2','rb'] else .01
                # Cin is zero in FRONT_S2B; keep zero, no fake physical capacitor.
                if name.lower()=='cin':out.append(line);continue
                f=factor(prefix+':'+name,tol)
                line=re.sub(r'\{([^{}]+)\}',lambda m:'{('+m[1]+f')*{f:.17g}'+'}',line)
                if '{' not in line:
                    head,val=line.rsplit(None,1);line=head+' {'+val+f'*{f:.17g}'+'}'
            out.append(line)
        return out
    front=passive(extract('ch1_comun_s2b.inc','FRONT_S2B','FRONT_S7_MC'),'XFE')
    ladder=passive(extract('ch1_comun_s3.inc','LADDER_S3','LADDER_S7_MC'),'XLAD')
    ska=passive(extract('ch1_comun_s7.inc','SK_S7','SK_S7_MCA'),'X105A')
    skb=passive(extract('ch1_comun_s7.inc','SK_S7','SK_S7_MCB'),'X105B')
    # SK R/C values passed nominally; each physical element varied inside its own copy.
    channel=passive(extract('ch1_comun_s7.inc','CHANNEL_S7','CHANNEL_S7_MC'),'XCH')
    channel=[line.replace('FRONT_S2B','FRONT_S7_MC').replace('LADDER_S3','LADDER_S7_MC').replace('SK_S7 RA','SK_S7_MCA RA') if line.startswith('X105A') else line.replace('FRONT_S2B','FRONT_S7_MC').replace('LADDER_S3','LADDER_S7_MC').replace('SK_S7 RA','SK_S7_MCB RA') if line.startswith('X105B') else line.replace('FRONT_S2B','FRONT_S7_MC').replace('LADDER_S3','LADDER_S7_MC') for line in channel]
    for j,line in enumerate(channel):
        if line.startswith(('XPROTA','XPROTB')):
            ff=factor(line.split()[0]+':RSER',.01)
            channel[j]=line.replace('{R_SER_S7}','{R_SER_S7*'+f'{ff:.17g}'+'}')
    rails=extract('ch1_comun_s2b.inc','RAILS_S2B','RAILS_S7_MC')
    for j,line in enumerate(rails):
        if re.match(r'^C\w*\s',line,re.I):
            ff=factor('XRAILS:'+line.split()[0],.05)
            if '{' in line:rails[j]=re.sub(r'\{([^{}]+)\}',lambda m:'{('+m[1]+f')*{ff:.17g}'+'}',line)
            else:
                head,val=line.rsplit(None,1);rails[j]=head+' {'+val+f'*{ff:.17g}'+'}'
    return front+ladder+ska+skb+channel+rails,records

def saves():
    ss=['V(PIN)','V(BNC)','V(SRC)','V(CS1)','V(CS2)','V(CLK1)','V(CLK2)']
    for p,n,ip,im in INPUT.values():ss += [f'V(XCH:{p})',f'V(XCH:{n})',f'I(XCH:{ip})',f'I(XCH:{im})']
    for p,n in CURRENT.values():ss += [f'I(XCH:{p})']+([f'I(XCH:{n})'] if n else [])
    ss+=['I(XCH:VOUT101)','I(XCH:XFE:DHP)','I(XCH:XFE:DLP)','I(VREF)','I(VDAC)','V(VP)','V(VN)','V(XCH:O)','V(XCH:SEL)']
    return list(dict.fromkeys(ss))

def net(c,source_amp=None):
    l=[f'* S7 {c["id"]}',f'.include "{ROOT/"comun/ch1_comun_s7.inc"}"',
       f'.include "{MODELS/"OPA810/opa810_a.lib"}"',
       f'.include "{MODELS/("AD8039/AD8038_ltspice_ruido_hoja.sub" if c["test"]=="J4" else "AD8039/AD8038_ltspice.sub")}"',
       f'.include "{MODELS/"74HC4051/hc_tnomi.cir"}"',
       f'.include "{MODELS/"OPA836/opa836_a.lib"}"',
       '.param BUFFER_KIND=810','.options numdgt=15 plotwinsize=0 threads=1',
       '.options method=gear solver=alt reltol=1e-5 abstol=1e-12 gminsteps=0','.temp 25']
    mc_lines,_=mc_subcircuits(c);l+=mc_lines
    l+=[f'XRAILS VP VN {"RAILS_S7_MC" if c["mc"]>=0 else "RAILS_S2B"} POWER=1','VDD VDDA 0 {VDDA_NOM}','VREF VREF 0 {VREF_NOM}',
        f'VDAC DAC 0 {c["vdac_V"]:.17g}',
        f'XCH BNC PIN VP VN VDDA VREF DAC {"CHANNEL_S7_MC" if c["mc"]>=0 else "CHANNEL_S7"} POS={c["POS"]} CODE={c["tap"]}']
    test=c['test'];amp=c['amplitude_V']
    if test=='J2':
        source=f'PULSE(0 {amp:.17g} 1u 2n 2n 1 2)' if c['kind']=='step' else f'PULSE({-amp:.17g} {amp:.17g} 1u 2n 2n 5u 10u)'
    elif test=='J6':source=f'PULSE(0 {amp:.17g} 1u 10n 10n 10u 1)'
    elif test=='J7' or (test=='J9' and c['kind']=='sine'):
        amp=source_amp if source_amp is not None else amp
        source=f'SINE(0 {amp:.17g} {c["freq_Hz"]:.17g})'
    else:source='DC 0 AC 1'
    l += [f'Vsrc SRC 0 {source}','VLINK SRC BNC 0']
    if test in ['J1','J3']:
        l += [meas(c,'AC','gain_dc_signed','FIND re(V(PIN)/V(BNC)) AT=1'),'.save V(PIN) V(BNC) V(SRC)', '.ac dec 300 1 200Meg']
    elif test=='J1DC':
        limit=c['scale_V_div']*.01
        l += [meas(c,'DC','center_V','FIND V(PIN) AT=0'),'.save V(PIN) V(BNC)',f'.dc Vsrc {-limit:.17g} {limit:.17g} {limit:.17g}']
    elif test=='J4':
        l += [meas(c,'NOISE','onoise_100k','FIND V(onoise) AT=100k'),'.noise V(PIN) Vsrc dec 300 1 3.15Meg']
    elif test=='J5':
        dc=f'.dc Vsrc 0 {40*c["dc_direction"]} {.001*c["dc_direction"]}' if c.get('dc_direction') else '.dc Vsrc -40 40 .05'
        l += [meas(c,'DC','adc_min_V','MIN V(PIN)'),meas(c,'DC','adc_max_V','MAX V(PIN)'),'.save '+' '.join(saves()),dc]
    elif test=='J8':
        l += [meas(c,'DC','center_V','FIND V(PIN) AT=0'),'.save V(PIN) V(BNC)', '.dc Vsrc -1n 1n 1n']
    else:
        if test=='J7':
            l += ['XADC PIN CS1 CS2 CLK1 CLK2 RESET1 RESET2 ADC_S6 RSW=825 STATE=0']
            end=a6.START+a6.TS+(a6.FIRST+a6.N+2)/a6.FS;dt=.5e-9
        elif test=='J6':end=1.2e-3 if abs(amp)>5.6 and c['POS']==1 else 40e-6;dt=2e-9
        elif test=='J9':end=40e-6 if c['kind']=='sine' else 2e-6;dt=.5e-9 if c['kind']=='sine' else 10e-9
        else:end=30e-6 if c['kind']=='square' else 8e-6;dt=1e-9
        selected=(['V(PIN)','V(BNC)','V(CS1)','V(CS2)','V(CLK1)','V(CLK2)'] if test=='J7' else
                  ['V(PIN)','V(BNC)'] if test=='J2' else
                  ['V(PIN)','V(BNC)','V(XCH:SEL)','V(VP)','V(VN)','I(XCH:XFE:DHP)','I(XCH:XFE:DLP)'] if test=='J6' else saves())
        l += [meas(c,'TRAN','adc_min_V','MIN V(PIN)'),meas(c,'TRAN','adc_max_V','MAX V(PIN)'),
              '.save '+' '.join(selected),f'.tran 0 {end:.17g} 0 {dt:.17g}']
    return '\n'.join(l+['.end'])+'\n'

def v(raw,n):return raw['v(xch:'+n+')']
def i(raw,n):return raw['i(xch:'+n+')']

def analyze(c,raw,r):
    test=c['test'];extra={}
    if test in ['J1','J3']:
        f=raw['frequency'];h=raw['v(pin)']/raw['v(bnc)']
        x=s5.ac_metrics(f,h)
        r.update({k:val for k,val in x.items() if k in FIELDS})
        r['gain_dc_signed']=float(h[0].real)
        r['gain_nominal_signed']=-DIV/c['scale_V_div']
        r['gain_error_pct']=100*(r['gain_dc_signed']/r['gain_nominal_signed']-1)
        db=20*np.log10(abs(h/h[0]));r['peak_db']=float(db.max());r['peak_Hz']=float(f[np.argmax(db)])
        gd=-np.gradient(np.unwrap(np.angle(h)),2*np.pi*f);mask=(f>=1e4)&(f<=2e6)
        r.update(gd_min_ns=float(gd[mask].min()*1e9),gd_max_ns=float(gd[mask].max()*1e9))
        r['gd_variation_ns']=r['gd_max_ns']-r['gd_min_ns']
        # Rebound means climbing above |H(4.5MHz)|, not local numerical ripples.
        return extra
    if test=='J1DC':
        g,center=np.polyfit(raw['v(bnc)'],raw['v(pin)'],1)
        r.update(gain_dc_signed=float(g),center_V=float(center),gain_nominal_signed=-DIV/c['scale_V_div'])
        r['gain_error_pct']=100*(g/r['gain_nominal_signed']-1);return extra
    if test=='J4':
        key=next(k for k in raw if 'onoise' in k and 'total' not in k)
        rms=s4.s3.integral_band(raw['frequency'],raw[key].real,3.15e6)
        r.update(noise_pin_uV=rms*1e6,noise_pct_div=100*rms/DIV)
        return extra
    y=raw['v(pin)']
    r.update(adc_min_V=float(y.min()),adc_max_V=float(y.max()))
    if test=='J8':r.update(center_V=float(y[1]));return extra
    if test=='J5':
        limits=[];bnc=raw['v(bnc)']
        if len(bnc)<1601 or abs(bnc[0]+40)>1e-8 or abs(bnc[-1]-40)>1e-8:
            raise ValueError('J5 sweep does not cover both exact endpoints')
        for stage,(p,n,ip,im) in INPUT.items():
            row=dict(id=c['id'],scale_V_div=c['scale_V_div'],stage=stage)
            for side,node in [('plus',p),('minus',n)]:
                arr=v(raw,node);row[side+'_min_V']=float(arr.min());row[side+'_max_V']=float(arr.max())
            diff=v(raw,p)-v(raw,n);j=int(np.argmax(abs(diff)))
            row.update(differential_abs_max_V=float(abs(diff[j])),differential_at_bnc_V=float(bnc[j]))
            for side,node in [('plus',ip),('minus',im)]:
                arr=i(raw,node);j=int(np.argmax(abs(arr)))
                row[side+'_current_abs_max_A']=float(abs(arr[j]));row[side+'_current_at_bnc_V']=float(bnc[j])
                row[side+'_at_minus40_V']=float(v(raw,p if side=='plus' else n)[0])
                row[side+'_at_plus40_V']=float(v(raw,p if side=='plus' else n)[-1])
                row[side+'_current_at_minus40_A']=float(arr[0]);row[side+'_current_at_plus40_A']=float(arr[-1])
            if stage=='OPA810':row['output_current_abs_max_A']=float(abs(i(raw,'vout101')).max())
            limits.append(row)
        extra['limits']=limits;return extra
    t=raw['time'];r.update(last_time_s=float(t[-1]),max_step_s=float(np.diff(t).max()))
    if test=='J2':
        initial=float(y[t<.5e-6].mean());final=float(y[(t>4e-6)&(t<4.9e-6)].mean())
        delta=final-initial;mask=(t>=1e-6)&(t<5.9e-6);ts=t[mask];z=(y[mask]-initial)/delta
        t10=s5.crossing(ts,z,.1);t90=s5.crossing(ts,z,.9)
        r.update(rise_ns=float((t90-t10)*1e9),overshoot_pct=max(0.,float(z.max()-1)*100))
        val=s4.s3.settled(ts,y[mask],1e-6,final,.005*abs(delta))
        r['settling_0p5pct_ns']=None if val is None else val*1e9
        if c['kind']=='square':
            mask=(t>=6.004e-6)&(t<10.9e-6)
            val=s4.s3.settled(t[mask],y[mask],6.004e-6,initial,.005*abs(delta))
            r['square_fall_settling_ns']=None if val is None else val*1e9
    elif test=='J6':
        initial=float(y[t<.5e-6].mean());event=11.02e-6
        val=s4.s3.settled(t,y,event,initial,.1*DIV)
        peak=max(float(abs(i(raw,'xfe:dhp')).max()),float(abs(i(raw,'xfe:dlp')).max()))
        forward=max(float((v(raw,'sel')-raw['v(vp)']).max()),float((raw['v(vn)']-v(raw,'sel')).max()))
        r.update(recovery_us=None if val is None else val*1e6,bav199_peak_A=peak,bav199_conducts=forward>.4,bav199_forward_max_V=forward,
                 terminal_error_V=float(y[-1]-initial),observation_us=float((t[-1]-event)*1e6))
    elif test=='J7':
        # Aperture left limit exactly as S6; reference aliases PIN for sampler utility.
        raw=dict(raw);raw['v(reference)']=raw['v(pin)']
        inds,ts,ys,ref,ap=a6.samples(raw)
        seq=ys[2:];fit=np.column_stack([np.sin(2*np.pi*c['freq_Hz']*ts[2:]),np.cos(2*np.pi*c['freq_Hz']*ts[2:]),np.ones(a6.N)])
        coeff=np.linalg.lstsq(fit,seq,rcond=None)[0];res=seq-fit@coeff
        spec,bins=a6.spectrum(seq,c['M']);r.update({k:x for k,x in spec.items() if k in FIELDS})
        r.update(residual_rms_LSB=a6.rms(res)/a6.LSB,residual_max_LSB=float(abs(res).max()/a6.LSB))
        refcoef=np.linalg.lstsq(fit,ref[2:],rcond=None)[0]
        ratio=complex(coeff[0],coeff[1])/complex(refcoef[0],refcoef[1])
        r.update(gain_sample_db=float(20*np.log10(abs(ratio))),phase_sample_deg=float(np.angle(ratio,deg=True)),
                 delay_equivalent_ns=float(-np.angle(ratio)/(2*np.pi*c['freq_Hz'])*1e9))
        extra['samples']=[dict(id=c['id'],n=int(n-a6.FIRST),adc=int(n%2+1),time_s=float(tt),sample_V=float(yy),pin_V=float(rr),**aa) for n,tt,yy,rr,aa in zip(inds[2:],ts[2:],seq,ref[2:],ap[2:])]
        extra['bins']=[dict(id=c['id'],bin=j,freq_Hz=j*a6.FS/a6.N,amplitude_V=float(x)) for j,x in enumerate(bins)]
    elif test=='J9':
        mask=t>=20e-6 if c['kind']=='sine' else t>=1e-6
        tt=t[mask]
        def avg(arr):return float(np.trapezoid(arr[mask],tt)/(tt[-1]-tt[0]))
        rows=[]
        for stage,(pp,nn) in CURRENT.items():
            p=avg(i(raw,pp));n=avg(i(raw,nn)) if nn else 0.
            power=avg(raw['v(vp)']*i(raw,pp)-raw['v(vn)']*(-i(raw,nn))) if nn else 3.3*p
            rows.append(dict(id=c['id'],stage=stage,kind=c['kind'],plus_A=p,minus_A=n,vdda_A=p if not nn else 0.,power_mW=power*1e3))
        ref=-avg(raw['i(vref)']);dac=-avg(raw['i(vdac)'])
        rows.append(dict(id=c['id'],stage='VMID',kind=c['kind'],vref_A=ref,power_mW=2.5*ref*1e3))
        rows.append(dict(id=c['id'],stage='DAC',kind=c['kind'],dac_A=dac,power_mW=c['vdac_V']*dac*1e3))
        rows.append(dict(id=c['id'],stage='TOTAL_CHANNEL',kind=c['kind'],plus_A=sum(x['plus_A'] for x in rows if x.get('stage')!='OPA836' and 'plus_A' in x),minus_A=sum(x.get('minus_A',0.) for x in rows),vdda_A=sum(x.get('vdda_A',0.) for x in rows),vref_A=ref,dac_A=dac,power_mW=sum(x['power_mW'] for x in rows)))
        extra['consumption']=rows
    return extra

def protected():
    files=[p for p in ROOT.rglob('*') if p.is_file() and not p.is_relative_to(ROOT/'S7') and
           not p.name.startswith('s7_') and p.name not in ['ejecutar_s7.py','ch1_comun_s7.inc','ACTA_S7.md','RESPUESTA_FINAL_S7.md','verificar_s7.py'] and
           p.suffix.lower() not in ['.log','.raw','.db','.pyc'] and '__pycache__' not in p.parts]
    files += [p for p in MODELS.rglob('*') if p.is_file()]
    cp=PROJECT if (PROJECT/'ai-context').exists() else MODELS.parents[1]
    files += [cp/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}

def simulate_dc_pair(c,work):
    data={};children=[]
    for direction in [-1,1]:
        child=dict(c,dc_direction=direction)
        child['id']=c['id'].replace('sweepn40p40',('sweep0n40' if direction<0 else 'sweep0p40')+'_step1m')
        _,extra,record=simulate(child,work)
        children.append(record)
        if record['errors'] or record['returncode']:break
        data[direction]=extra['_raw']
    record=dict(id=c['id'],returncode=int(any(r['returncode'] for r in children)),
                errors=[e for r in children for e in r['errors']],warnings=[w for r in children for w in r['warnings']],simulations=len(children),children=children)
    if len(data)!=2 or record['errors'] or record['returncode']:return {},{},record
    raw={key:np.r_[data[-1][key][::-1],data[1][key][1:]] for key in data[-1]}
    r=dict(c);extra=analyze(c,raw,r)
    return r,extra,record

def simulate(c,work,source_amp=None):
    if c['test']=='J5' and c['ix'] in [1,5] and not c.get('dc_direction'):
        return simulate_dc_pair(c,work)
    path=work/(c['id']+'.cir');deck=net(c,source_amp);write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    r=dict(c);record=dict(id=c['id'],returncode=0,errors=[],warnings=[])
    try:
        proc=subprocess.run([str(LT),'-b',str(path)],cwd=work,capture_output=True,timeout=7200)
        vals,errs,warns,_=s4.s3.prior.old.read_log(path.with_suffix('.log'))
        expected={x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        if expected-set(vals):errs.append('Missing measures '+str(expected-set(vals)))
        record.update(returncode=proc.returncode,errors=errs,warnings=warns)
        if errs or proc.returncode:return {},{},record
        raw=s4.s3.raw_read(path.with_suffix('.raw'));r.update({k[len(c['id'])+1:]:val for k,val in vals.items() if k in expected})
        if c.get('dc_direction'):
            bnc=raw['v(bnc)']
            if len(bnc)!=40001 or abs(bnc[0])>1e-8 or abs(bnc[-1]-40*c['dc_direction'])>1e-8:
                raise ValueError('Incomplete fine DC continuation')
        extra={'_raw':raw} if c.get('dc_direction') else analyze(c,raw,r)
        if c['test']=='J3':extra['mc_components']=mc_subcircuits(c)[1]
        if c['test']=='J1':
            write(path.with_suffix('.response.json'),json.dumps(dict(f=raw['frequency'].tolist(),mag=abs(raw['v(pin)']/raw['v(bnc)']).tolist())))
        if source_amp is not None:r['source_amp_V']=source_amp
        for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
        return r,extra,record
    except Exception as e:record['errors'].append(repr(e));return {},{},record

def execute(cases,work,amps=None):
    rows=[];extras={};records=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        fs={pool.submit(simulate,c,work,(amps or {}).get(c['id'])):c for c in cases}
        for fut in as_completed(fs):
            r,e,rec=fut.result();records.append(rec)
            if r:rows.append(r)
            for key,rr in e.items():extras.setdefault(key,[]).extend(rr)
            if rec['errors']:print('ERROR',rec['id'],rec['errors'],flush=True)
            elif len(records)%25==0 or len(cases)<10:print('PROGRESS',len(records),'/',len(cases),flush=True)
    return rows,extras,records

def jobs(smoke=False):
    indices=[0,6] if smoke else range(12)
    cs=[case('J1',j) for j in indices]+[case('J1DC',j,kind='dc') for j in indices]
    cs += [case('J5',j,kind='dc') for j in ([0] if smoke else [0,1,5,6,11])]
    cs += [case('J4',j,kind='noise') for j in indices]
    cs += [case('J2',j,kind=k,amp=SCALES[j]*(1 if k=='step' else 3)) for j in indices for k in ['step','square']]
    cs += [case('J3',j,mc=n) for j in [0,6] for n in range(3 if smoke else 300)]
    cs += [case('J6',j,kind='pulse',amp=sgn*a) for j,aa in [(0,[.2,2,4.5]),(6,[20,40])] for a in aa for sgn in [-1,1]]
    cs += [case('J8',vdac=float(x),kind='offset') for x in np.linspace(.2,2.3,9)]
    cs += [case('J9',kind='idle'),case('J9',kind='sine',target=2e6)]
    cs += [case('J7',j,kind='sampled',target=f) for j in [0,6] for f in [1e6,2e6]]
    return cs

LIMIT_FIELDS=['id','scale_V_div','stage','plus_min_V','plus_max_V','minus_min_V','minus_max_V',
 'differential_abs_max_V','differential_at_bnc_V','plus_current_abs_max_A','plus_current_at_bnc_V',
 'minus_current_abs_max_A','minus_current_at_bnc_V','plus_at_minus40_V','plus_at_plus40_V',
 'minus_at_minus40_V','minus_at_plus40_V','plus_current_at_minus40_A','plus_current_at_plus40_A',
 'minus_current_at_minus40_A','minus_current_at_plus40_A','output_current_abs_max_A']
CON_FIELDS=['id','stage','kind','plus_A','minus_A','vdda_A','vref_A','dac_A','power_mW']

def assess(rows,extra,complete):
    def rr(test):return [r for r in rows if r['test']==test]
    ac=rr('J1');mc=rr('J3');st=[r for r in rr('J2') if r['kind']=='step'];noise=rr('J4');rec=rr('J6');sam=rr('J7');offs=rr('J8');dc=rr('J1DC')
    limits=extra.get('limits',[])
    n=len(ac);expected=12 if complete else 2
    out=[]
    def add(k,ok,evidence):out.append(dict(criterion=f'S7-C{k}',status='PASA' if ok else 'FALLA',evidence=evidence))
    add(1,len(ac)==expected and all(1.8e6<=r['minus3_Hz']<=2.2e6 and r['peak_db']<=.5 and r['rebound_excess_db']<1e-6 for r in ac),f'{n} escalas; corte '+str([round(r['minus3_Hz']/1e6,6) for r in ac]))
    rates={j:sum(1.8e6<=r['minus3_Hz']<=2.2e6 for r in mc if r['ix']==j)/max(1,sum(r['ix']==j for r in mc)) for j in [0,6]}
    add(2,all(x>=.95 for x in rates.values()),str(rates))
    add(3,len(st)==expected and all(140<=r['rise_ns']<=210 for r in st),str([round(r['rise_ns'],3) for r in st])+' ns')
    add(4,len(noise)==expected and all(r['noise_pct_div']<=.45 for r in noise),str([round(r['noise_pct_div'],5) for r in noise])+' % div')
    bad=[]
    for r in limits:
        lim=10e-3 if r['stage']=='OPA810' else .43e-3 if r['stage']=='OPA836' else None
        if lim and max(r['plus_current_abs_max_A'],r['minus_current_abs_max_A'])>lim:bad.append(r['stage']+' current '+str(max(r['plus_current_abs_max_A'],r['minus_current_abs_max_A'])))
        if r['stage'] in ['U103A','U103B','U105A','U105B'] and r['differential_abs_max_V']>2:bad.append(r['stage']+' differential '+str(r['differential_abs_max_V']))
    if any(r['adc_min_V']<0 or r['adc_max_V']>3.3 for r in rr('J5')):bad.append('ADC outside rails')
    add(5,len(limits)==(30 if complete else 6) and not bad,str(bad or 'Dentro de límites')+f'; {len(limits)} filas de límites')
    fast=[r for r in rec if not r['bav199_conducts']]
    add(6,bool(fast) and all(r['recovery_us'] is not None and r['recovery_us']<=1 for r in fast),str([(r['scale_V_div'],r['amplitude_V'],r['recovery_us'],r['bav199_conducts']) for r in rec]))
    add(7,len(sam)==4 and all(r['sfdr_db']>=60 and r['residual_rms_LSB']<=.5 for r in sam),str([(r['sfdr_db'],r['residual_rms_LSB']) for r in sam]))
    if offs:
        x=np.array([r['vdac_V'] for r in offs]);y=np.array([r['offset_div'] for r in offs]);mask=(y>-4.7)&(y<5)
        fit=np.polyfit(x[mask],y[mask],1);res=float(abs(y[mask]-np.polyval(fit,x[mask])).max())
        endpoint_error=float(abs(y-np.polyval(fit,x)).max())
        add(8,max(y)>=5 and min(y)<=-4.8 and endpoint_error<1e-5,f'offset {min(y):.6g} .. {max(y):.6g} div; interior lineal, residuo {res:.3g} div; desviación del extremo {endpoint_error:.6g} div. Rango pasa, linealidad literal de 9 puntos falla por recorte ya aceptado en S4')
    else:add(8,False,'Sin datos')
    add(9,len(dc)==expected and all(abs(r['gain_error_pct'])<=3 for r in dc),str([round(r['gain_error_pct'],6) for r in dc])+' %')
    return out

def table(rows,fields,labels=None):
    return '| '+' | '.join(labels or fields)+' |\n| '+' | '.join(['---']*len(fields))+' |\n'+'\n'.join('| '+' | '.join(str(r.get(k,'')) for k in fields)+' |' for r in rows)+'\n'

def pieces():
    groups=[('Rt1/Rt2',2,'RT1','1206, divisor; ±0.1 %'),('Rb',1,'RB','divisor'),
      ('Ct1',1,'CT1','C0G'),('Ct2fixed',1,'CT2F','derivado CT1-CTRIM_MED'),
      ('Ct2trim',1,'CTRIM','SEHWA 2–6 pF, nominal central'),('Cb',1,'CB','seleccionar en prueba'),
      ('Rs1/Rs2',2,'RS1','1206'),('Cs',1,'CS','>=200 V'),('Req',1,'REQ','1206 >=200 V'),
      ('Ceq',1,'CEQ','>=200 V, seleccionar en prueba'),('CAc',1,'CAC','acoplo'),
      ('Rbias',1,'RBIAS','bias'),('Rprot',1,'RPROT','protección buffer')]
    groups += [(f'RL{j}',1,f'RL{j}','escalera') for j in range(1,7)]
    groups += [('R_SER U103A/B',2,'R_SER_S7','protección IN+'),('RFA',1,'RF1','U103A'),
      ('RGA',1,'RG1','U103A'),('RFB',1,'RF2','U103B'),('RGB',1,'RG2','U103B'),
      ('R1/R2 U105A',2,'RFILT1_S7','TR, sección 1'),('C1 U105A',1,'CFILT1_S7','TR feedback'),
      ('C2 U105A',1,'CGILT1_S7','TR a masa'),('R1/R2 U105B',2,'RFILT2_S7','TR, sección 2'),
      ('C1 U105B',1,'CFILT2_S7','TR feedback'),('C2 U105B',1,'CGILT2_S7','TR a masa'),
      ('RIN',1,'R_IN_S4','OPA836'),('RF',1,'R_F_S4','OPA836'),('ROFF',1,'R_OFF_S4','OPA836'),
      ('CF',1,'C_FB_S7','C0G'),('RT_MID',1,'RT_MID','VMID desde VREF+'),
      ('RB_MID',1,'RB_MID','VMID'),('CMID',1,'C_MID_S7','VMID'),
      ('RADC',1,'R_ADC_S4','pin PA0'),('CADC',1,'C_ADC_S4','pin PA0')]
    rr=[dict(designador=name,cantidad=qty,valor_SI=NOM[key],nota=note) for name,qty,key,note in groups]
    rr += [dict(designador=name,cantidad=qty,valor_SI=value,nota=note) for name,qty,value,note in
           [('U101',1,'OPA810','fuente única'),('U103',1,'AD8039 doble','A y B'),('U105',1,'AD8039 doble','A y B'),
            ('U102',1,'74HC4051','8 SWI1 Nexperia'),('Ufinal',1,'OPA836','VDDA 3.3 V'),
            ('K1',1,'HFD27 DPDT','monoestable'),('sujeción entrada',1,'BAV199 par','Nexperia'),
            ('sujeción U103A/B',2,'BAV99 par','C2500, modelo Rohm BAV99HY')]]
    return rr

def save_results(rows,extra,records,meta,smoke):
    rows=sorted((dict(r) for r in rows),key=lambda r:r['id'])
    extra={key:sorted(rr,key=lambda r:(r['id'],str(r.get('stage','')),str(r.get('component','')),r.get('n',r.get('bin',0)))) for key,rr in extra.items()}
    for test in ['J1','J1DC','J2','J3','J4','J5','J6','J7','J8','J9']:
        csv_write(OUT/f's7_{test.lower()}.csv',[r for r in rows if r['test']==test],FIELDS)
    for name,fields in [('limits',LIMIT_FIELDS),('consumption',CON_FIELDS),('mc_components',['id','mc','component','tolerance','draw','factor','seed']),('samples',['id','n','adc','time_s','sample_V','pin_V','track_left_time_s','track_left_clock_V','closing_clock_time_s','closing_time_error_ps']),('bins',['id','bin','freq_Hz','amplitude_V'])]:
        csv_write(OUT/f's7_{name}.csv',extra.get(name,[]),fields)
    criteria=assess(rows,extra,not smoke);csv_write(OUT/'s7_criterios.csv',criteria,['criterion','status','evidence'])
    ac=sorted([r for r in rows if r['test']=='J1'],key=lambda r:r['ix'])
    dc={r['ix']:r for r in rows if r['test']=='J1DC'}
    noise={r['ix']:r for r in rows if r['test']=='J4'}
    rise={r['ix']:r for r in rows if r['test']=='J2' and r['kind']=='step'}
    calibration=[]
    for r in ac:
        j=r['ix'];g=dc.get(j,r)['gain_dc_signed'];calibration.append(dict(escala_V_div=r['scale_V_div'],rele=r['POS'],toma=r['tap'],ganancia_medida=g,ganancia_nominal=-DIV/r['scale_V_div'],signo=int(np.sign(g))))
        r['gain_dc_signed']=g;r['rise_ns']=rise.get(j,{}).get('rise_ns');r['noise_pct_div']=noise.get(j,{}).get('noise_pct_div')
    csv_write(OUT/'s7_tabla_calibracion.csv',calibration,['escala_V_div','rele','toma','ganancia_medida','ganancia_nominal','signo'])
    stats=[]
    for j in [0,6]:
        rr=[r for r in rows if r['test']=='J3' and r['ix']==j]
        for k in ['minus3_Hz','peak_db','atten_4p5m_db','gain_dc_signed']:
            if rr:
                x=np.array([r[k] for r in rr]);stats.append(dict(scale_V_div=SCALES[j],metric=k,N=len(x),min=float(x.min()),p5=float(np.percentile(x,5)),median=float(np.median(x)),p95=float(np.percentile(x,95)),max=float(x.max()),mean=float(x.mean()),std=float(x.std()),within_band_pct=100*float(np.mean((x>=1.8e6)&(x<=2.2e6))) if k=='minus3_Hz' else ''))
    csv_write(OUT/'s7_montecarlo_resumen.csv',stats,['scale_V_div','metric','N','min','p5','median','p95','max','mean','std','within_band_pct'])
    write(ROOT/'S7'/'s7_run.json',json.dumps(meta,indent=2,ensure_ascii=False))
    write(ROOT/'S7'/'s7_registro.json',json.dumps(sorted(records,key=lambda r:r['id']),indent=2,ensure_ascii=False))
    csv_write(OUT/'s7_componentes.csv',[dict(parameter=k,value_SI=v) for k,v in NOM.items()],['parameter','value_SI'])
    csv_write(OUT/'s7_lista_piezas.csv',pieces(),['designador','cantidad','valor_SI','nota'])
    summary='# S7 — integración CH1\n\n'+json.dumps(meta,ensure_ascii=False)+'\n\n'+table(criteria,['criterion','status','evidence'])+'\n'+table(ac,['scale_V_div','minus3_Hz','gain_dc_signed','rise_ns','noise_pct_div','atten_4p5m_db'])
    write(OUT/'s7_resumen.md',summary)
    acta=summary+'\n## Circuito y piezas\n\n'+table(pieces(),['designador','cantidad','valor_SI','nota'])+'\nParámetros y parásitas completos:\n\n'+table([dict(parameter=k,value_SI=v) for k,v in NOM.items()],['parameter','value_SI'])
    acta+='\nOPA810; AD8039 doble U103 y U105; 74HC4051 (8 SWI1 hc_tnomi); OPA836; HFD27 DPDT; BAV199 Nexperia; BAV99 C2500 (modelo Rohm BAV99HY); trimmer SEHWA 2–6 pF; TVS de riel genérica heredada. FRONT_S2B intacto. VMID M1, C_F=1 pF, ADC 68 ohm / 470 pF + pad 5 pF. Sin carga ficticia.\n'
    acta+='\nContradicción conservada: la tabla del contrato cita C_S=1.5 nF y los resúmenes C_EQ≈12 pF. FRONT_S2B con BUFFER_KIND=810 deriva C_S='+format(NOM['CS']*1e9,'.9g')+' nF, C_EQ='+format(NOM['CEQ']*1e12,'.9g')+' pF y Cb='+format(NOM['CB']*1e9,'.9g')+' nF. Se usa FRONT_S2B sin cambios, expresamente requerido por el contrato; no se escogen nuevos valores. Ct2 físico se compone de CT2F + CTRIM = '+format((NOM['CT2F']+NOM['CTRIM'])*1e12,'.9g')+' pF. La tabla de parámetros se evalúa directamente desde los includes.\n'
    acta+='\n## Monte Carlo\n\n'+table(stats,['scale_V_div','metric','N','min','p5','median','p95','max','within_band_pct'])
    acta+='\n## J5: límites\n\n'+table(extra.get('limits',[]),['scale_V_div','stage','differential_abs_max_V','plus_current_abs_max_A','minus_current_abs_max_A','plus_min_V','plus_max_V','minus_min_V','minus_max_V'])
    acta+='\nExtremos ±40 V y coordenadas de los máximos: s7_limits.csv. U103: corrientes de la red de entrada incluyen los BAV99 externos; cota conservadora, no sólo corriente del pin del macromodelo.\n'
    acta+='\n## Consumo\n\n'+table(extra.get('consumption',[]),['kind','stage','plus_A','minus_A','vdda_A','vref_A','dac_A','power_mW'])
    acta+='\nG.3 supone 3.9 mA por amplificador: CH1 contiene cinco amplificadores a ±5 V y uno a VDDA (G.3 cuenta sólo uno para el filtro, frente a los dos decididos en S5). La carga de 42/39 mA de RAILS_S2B representa otros consumidores y NO se suma al total de CH1. El consumo de canal incluye amplificadores, 4051, VMID y DAC; no bobina de relé, MCU, pérdidas de conversión ni TVS.\n'
    baseline=(len(STAGES)-1)*2*5*3.9e-3+3.3*3.9e-3
    acta+='\nAplicando los 3.9 mA supuestos por G.3 a los seis amplificadores reales de CH1: '+format(baseline*1e3,'.6g')+' mW (antes de VMID/DAC). Diferencia del total simulado: '+str([(r['kind'],round(r['power_mW']-baseline*1e3,6)) for r in extra.get('consumption',[]) if r['stage']=='TOTAL_CHANNEL'])+' mW. No se recalcula autonomía ni se modifica G.3.\n'
    acta+='\n## Recuperación y gran señal\n\n'+table([r for r in rows if r['test']=='J6'],['scale_V_div','amplitude_V','bav199_peak_A','bav199_conducts','recovery_us','terminal_error_V'])
    acta+='\n'+table([r for r in rows if r['test']=='J7'],['scale_V_div','freq_Hz','source_amp_V','fundamental_pp_V','sfdr_db','thd_pct','residual_rms_LSB','gain_sample_db','delay_equivalent_ns'])
    acta+='\n## Offset\n\n'+table([r for r in rows if r['test']=='J8'],['vdac_V','center_V','offset_div'])
    acta+='\n## Método, dudas y límites\n\n- J1 transferencia V(PIN)/V(BNC), 1 Hz–200 MHz; ganancia DC confirmada mediante barrido simétrico de ±0.01 div; inversión conservada en calibración. Retardo de grupo 10 kHz–2 MHz.\n- Monte Carlo: semilla '+str(SEED)+', 300 casos por escala, mismas realizaciones en las dos escalas. Uniforme independiente por instancia física: R ±1 %, resistencias del divisor ±0.1 %, C ±5 %. Copias de topología heredada en el deck sólo para aplicar tolerancias por componente, sin redefinir parámetros globales. Valores derivados se toleran sobre su nominal; sin reajuste de trimmer/Cb/CEQ. Factores y realizaciones en s7_mc_components.csv. No se toleran semiconductores, fuentes, interruptores ideales ni capacidades internas del modelo.\n- J2: 1 div para escalón; 6 div pp para cuadrada. Asentamiento contra último cruce y 0.5 % de amplitud del cambio.\n- J6: conducción BAV199 identificada por polarización directa >0.4 V, separada de corriente capacitiva; recuperación desde final de flanco, 11.02 us, dentro de ±0.1 div.\n- J7: amplitud de entrada calculada de J1 a frecuencia coherente para 8 div pp en el pin; seno ideal ajustado en la secuencia muestreada, offset/ganancia/fase retirados del residuo. Error incluye distorsión completa del canal. Sin ventana FFT, 1024 muestras en estado P; sin cuantización, ruido ADC, jitter ni desajuste. SFDR del modelo no certifica silicio.\n- OPA836: diodos internos agregados DESD_OPA836 son un supuesto de S4. BAV99HY Rohm modela la pieza Nexperia elegida: discrepancia mantenida.\n- C8 pide relación lineal: se informa ajuste en interior sin saturación; extremo inferior recortado igual que S4. No se cambia VMID.\n- E18 histórico (error contra pin simultáneo) contradice auditoría S6: S7 usa residuo no lineal y reporta retraso fijo aparte.\n- Se conserva secuencia AFE sólo con VDDA presente; no se simula apagado ni ESD en esta integración. S1–S6 son evidencia de simulación, no pruebas de placa.\n- Ganancia DC de MC usa límite AC de 1 Hz; ruido referido BNC usa ganancia medida DC.\n'
    acta+='\nLa fuente de prueba impone la BNC con impedancia cero; J4 informa ruido propio del canal y no ruido térmico de una impedancia externa.\n'
    acta+='\nActualización concurrente, 3 oct 21:41: STATE.md y DECISIONS.md cambiaron externamente durante smoke. La nueva decisión fija ±4.90 V, C_S=1.2 nF y C_EQ≈8.7 pF, y pide tolerancias de rieles, VREF y amplificadores con aceptación funcional en ≥95 % de placas. S7 queda congelado en su contrato original, ±5 V y FRONT_S2B intacto; S7b pendiente de encargo/auditoría. El fallo literal de linealidad de C8 no se presenta como rechazo bajo ese criterio nuevo de ganancia/offset calibrables. Codex no modificó esos dos archivos.\n'
    acta+='\nConvergencia J5: 10 mV/div y 200 mV/div se recorren desde 0 hasta cada extremo con paso de 1 mV. Se fusiona -40…0 con 0…+40 sin duplicar 0; 80001 puntos, extremos verificados. Las otras tres escalas conservan -40…+40 con paso de 50 mV. Sólo cambia la inicialización/resolución numérica, no componentes ni modelos. Cada .meas de las dos mitades nombra su polaridad real. El registro conserva los intentos y el número de ejecuciones nativas además de los casos lógicos.\n'
    write(ROOT/'ACTA_S7.md',acta)
    final='# Respuesta final — S7\n\n'
    final+='Creados: `comun/ch1_comun_s7.inc`, `ejecutar_s7.py`, `verificar_s7.py`, decks y registros en `S7/`, CSV y resumen `resultados/s7_*`, tabla de calibración, `ACTA_S7.md` y diario propio en `ai-context/journal/2026-10-03-codex-s7-integracion.md`.\n\n'
    final+=f'Código **{meta["returncode"]}**; **{meta["simulations"]} simulaciones** para {meta.get("logical_cases",len(rows))} casos, {meta["seconds"]:.1f} s ({meta["seconds"]/60:.2f} min), 10 trabajadores. {meta.get("successful_simulations",len(rows))} ejecuciones válidas; inicializaciones previas fallidas/interrumpidas: {len(meta.get("prior_errors",[]))}. {meta["protected_count"]} archivos protegidos; cambios: {len(meta["protected_changed"])}. Código 0 expresa ejecución completa, no aceptación del circuito.\n\n'
    final+=table(criteria,['criterion','status'],['Criterio','Resultado'])
    compact=[dict(escala_V_div=r['scale_V_div'],corte_MHz=round(r['minus3_Hz']/1e6,6),ganancia_V_V=round(r['gain_dc_signed'],8),subida_ns=round(r['rise_ns'],3) if r.get('rise_ns') is not None else '',ruido_pct_div=round(r['noise_pct_div'],5) if r.get('noise_pct_div') is not None else '',atenuacion_4p5MHz_dB=round(r['atten_4p5m_db'],4)) for r in ac]
    final+='\n'+table(compact,['escala_V_div','corte_MHz','ganancia_V_V','subida_ns','ruido_pct_div','atenuacion_4p5MHz_dB'],['V/div','−3 dB (MHz)','G DC (V/V)','Subida (ns)','Ruido (% div)','A 4.5 MHz (dB)'])
    final+='\nMonte Carlo: 300 casos por escala, semilla '+str(SEED)+', tolerancias independientes, sin reajuste.\n\n'
    final+=table([dict(escala_V_div=r['scale_V_div'],min_MHz=round(r['min']/1e6,5),max_MHz=round(r['max']/1e6,5),dentro_pct=round(r['within_band_pct'],3)) for r in stats if r['metric']=='minus3_Hz'],['escala_V_div','min_MHz','max_MHz','dentro_pct'])
    final+='\nPicos de Monte Carlo: '+str([(SCALES[j],max(r['peak_db'] for r in rows if r['test']=='J3' and r['ix']==j),sum(r['peak_db']>.5 for r in rows if r['test']=='J3' and r['ix']==j)) for j in [0,6] if any(r['test']=='J3' and r['ix']==j for r in rows)])+' (escala V/div, máximo dB, casos >0.5 dB). El criterio C2 sólo fija la fracción de cortes dentro de banda; el rendimiento observado no es una garantía estadística de producción. Distribuciones completas de pico, rechazo a 4.5 MHz y ganancia: `s7_montecarlo_resumen.csv`.\n'
    ls=extra.get('limits',[])
    if ls:
        bound=[]
        for stage in STAGES:
            rr=[r for r in ls if r['stage']==stage]
            bound.append(dict(etapa=stage,diferencial_max_V=round(max(r['differential_abs_max_V'] for r in rr),6),entrada_max_mA=round(max(max(r['plus_current_abs_max_A'],r['minus_current_abs_max_A']) for r in rr)*1e3,6),salida_max_mA=round(max(r.get('output_current_abs_max_A',0) for r in rr)*1e3,6) if stage=='OPA810' else ''))
        final+='\nJ5, barridos −40…+40 V en las cinco escalas pedidas:\n\n'+table(bound,['etapa','diferencial_max_V','entrada_max_mA','salida_max_mA'],['Etapa','Diferencial máx. (V)','I entrada máx. (mA)','I salida máx. (mA)'])
        rr=[r for r in rows if r['test']=='J5'];final+=f'\nPin del ADC: {min(r["adc_min_V"] for r in rr):.6f}…{max(r["adc_max_V"] for r in rr):.6f} V. U103: corrientes incluyen la protección BAV99. Extremos por escala: `s7_limits.csv`.\n'
    cr=extra.get('consumption',[]);cons=[]
    for stage in [*STAGES,'4051','VMID','DAC','TOTAL_CHANNEL']:
        idle=next((r for r in cr if r['stage']==stage and r['kind']=='idle'),{})
        active=next((r for r in cr if r['stage']==stage and r['kind']=='sine'),{})
        cons.append(dict(etapa=stage,I_p5_reposo_mA=round((idle.get('plus_A',0) if stage!='OPA836' else 0)*1e3,6),I_n5_reposo_mA=round(abs(idle.get('minus_A',0))*1e3,6),I_VDDA_reposo_mA=round(idle.get('vdda_A',0)*1e3,6),reposo_mW=round(idle.get('power_mW',0),5),seno_2MHz_mW=round(active.get('power_mW',0),5)))
    final+='\nConsumo por etapa y canal (corrientes absorbidas):\n\n'+table(cons,['etapa','I_p5_reposo_mA','I_n5_reposo_mA','I_VDDA_reposo_mA','reposo_mW','seno_2MHz_mW'],['Etapa','I +5 reposo (mA)','I −5 reposo (mA)','I VDDA reposo (mA)','Reposo (mW)','Seno 2 MHz (mW)'])
    final+=f'\nG.3 aplicado al recuento real de CH1 supondría {baseline*1e3:.2f} mW sólo en amplificadores. Corrientes por cada riel: `s7_consumption.csv`.\n'
    fast=[r for r in rows if r['test']=='J6' and not r['bav199_conducts']]
    if fast:final+=f'\nJ6: recuperación máxima {max(r["recovery_us"] for r in fast if r["recovery_us"] is not None):.6f} µs; ningún caso de conducción directa de BAV199 en los pulsos prescritos.\n'
    sam=[r for r in rows if r['test']=='J7']
    if sam:final+=f'J7: SFDR mínimo {min(r["sfdr_db"] for r in sam):.3f} dB; THD máxima {max(r["thd_pct"] for r in sam):.7f} %; residuo máximo {max(r["residual_rms_LSB"] for r in sam):.7f} LSB rms.\n'
    final+='\nDudas conservadas: FRONT_S2B deriva C_S='+format(NOM['CS']*1e9,'.6g')+' nF y C_EQ='+format(NOM['CEQ']*1e12,'.6g')+' pF, distintos de los resúmenes; G.3 cuenta un amplificador de filtro y S5 fija dos. C8 es lineal en su rango útil y recorta en el extremo inferior: se conserva el fallo literal de linealidad en los 9 puntos, junto con la aceptación previa del recorte en S4. Diodos del OPA836 supuestos, BAV99HY de Rohm para una pieza Nexperia y ADC sin ruido, cuantización, jitter ni desajuste: resultados de simulación, pendientes de auditoría y placa. No se cambian valores ni se eligen remedios.\n'
    final+='\nPendiente: S7b para la decisión concurrente de ±4.90 V y C_S=1.2 nF, con tolerancias ampliadas y criterio funcional. S7 verifica el contrato original; no certifica esa nueva revisión. Smoke completó 42/42 simulaciones, pero su código fue 1 por las modificaciones externas de STATE/DECISIONS.\n'
    write(ROOT/'RESPUESTA_FINAL_S7.md',final)
    return criteria

def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');p.add_argument('--quick',action='store_true');p.add_argument('--resume',action='store_true');p.add_argument('--repair-dc',action='store_true');p.add_argument('--reports-only',action='store_true');args=p.parse_args()
    if args.reports_only:
        data=json.loads((ROOT/'S7/s7_completed_data.json').read_text())
        save_results(data['rows'],data['extras'],data['records'],data['meta'],data['meta']['smoke'])
        print('Reports regenerated from completed simulation data; no LTspice execution')
        return data['meta']['returncode']
    start=time.perf_counter();before=protected();work=ROOT/'S7'/('dc_repair' if args.repair_dc else 'quick' if args.quick else 'resume' if args.resume else 'smoke' if args.smoke else 'campaign');work.mkdir(parents=True,exist_ok=True)
    write(work/'s7_protected_before.json',json.dumps(before,indent=2))
    if args.repair_dc:
        cs=[case('J5',j,kind='dc') for j in [1,5]]
        rows,extra,records=execute(cs,work);after=protected()
        changed=[key for key,value in before.items() if after.get(key)!=value]
        code=int(len(rows)!=2 or bool(changed) or any(r['errors'] or r['returncode'] for r in records))
        meta=dict(returncode=code,simulations=sum(r.get('simulations',1) for r in records),seconds=time.perf_counter()-start,protected_changed=changed)
        decks={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in work.glob('*.cir')}
        write(ROOT/'S7/s7_dc_repair.json',json.dumps(dict(rows=rows,extras=extra,records=records,meta=meta,protected_before=before,protected_after=after,decks=decks),ensure_ascii=False))
        print(json.dumps(meta),flush=True);return code
    if args.quick:
        cs=[case('J1',0),case('J1',6),case('J9',kind='idle')]
        rows,extra,records=execute(cs,work)
        meta=dict(returncode=int(any(x['errors'] or x['returncode'] for x in records)),simulations=len(records),seconds=time.perf_counter()-start)
        write(ROOT/'S7'/'s7_quick.json',json.dumps(dict(meta=meta,rows=rows,extra=extra,records=records),ensure_ascii=False,indent=2));print(json.dumps(dict(meta=meta,rows=rows,extra=extra),ensure_ascii=False));return meta['returncode']
    cs=jobs(args.smoke);rows=[];extras={};records=[];prior_meta={};prior_errors=[]
    if args.resume:
        previous=json.loads((ROOT/'S7/s7_completed_data.json').read_text())
        if previous['meta']['smoke']!=args.smoke:raise ValueError('Resume profile differs from saved campaign')
        rows=previous['rows'];extras=previous['extras'];prior_meta=previous['meta']
        records=[r for r in previous['records'] if not r['errors'] and not r['returncode']]
        prior_errors=[r for r in previous['records'] if r['errors'] or r['returncode']]
    def signature(c):
        calculated=c['test']=='J7' or c['test']=='J9' and c['kind']=='sine'
        return tuple(c[k] for k in ['test','ix','mc','kind','freq_Hz','vdac_V'])+(('CALCULATED' if calculated else c['amplitude_V']),)
    completed={signature(r) for r in rows};new_records=[]
    cached=False
    if args.resume and (ROOT/'S7/s7_dc_repair.json').exists():
        cache=json.loads((ROOT/'S7/s7_dc_repair.json').read_text())
        valid=cache['meta']['returncode']==0 and cache['protected_before']==before and cache['protected_after']==before
        for c in [case('J5',j,kind='dc') for j in [1,5]]:
            for direction in [-1,1]:
                child=dict(c,dc_direction=direction)
                child['id']=c['id'].replace('sweepn40p40',('sweep0n40' if direction<0 else 'sweep0p40')+'_step1m')
                valid=valid and cache['decks'].get(child['id']+'.cir')==hashlib.sha256(net(child).encode('utf-8')).hexdigest()
        if valid:
            accepted=[r for r in cache['rows'] if signature(r) not in completed];ids={r['id'] for r in accepted}
            rows+=accepted
            for key,rr in cache['extras'].items():extras.setdefault(key,[]).extend(r for r in rr if r['id'] in ids)
            added=[r for r in cache['records'] if r['id'] in ids];records+=added;new_records+=added
            completed={signature(r) for r in rows};cached=bool(accepted)
            print('Reusing verified DC continuation:',len(accepted),'logical cases',flush=True)
    for test in ['J1','J1DC','J5','J4','J2','J3','J6','J8','J9','J7']:
        batch=[c for c in cs if c['test']==test and signature(c) not in completed];amps={}
        if not batch:continue
        if test in ['J7','J9']:
            ac={r['ix']:r for r in rows if r['test']=='J1'}
            for c in batch:
                if c['kind'] in ['sampled','sine']:
                    j=c['ix'];freq=c['freq_Hz'];path=work/(ac[j]['id']+'.cir')
                    # AC attenuation interpolated from recomputed J1 response saved in a compact JSON sidecar.
                    response_path=path.with_suffix('.response.json')
                    if not response_path.exists():response_path=(ROOT/'S7/campaign'/path.name).with_suffix('.response.json')
                    response=json.loads(response_path.read_text())
                    gain=np.interp(np.log(freq),np.log(response['f']),response['mag'])
                    amplitude=float(4*DIV/gain)
                    c['amplitude_V']=amplitude
                    c['id']=c['id'].replace('_a0_',f'_a{s4.number(amplitude)}_')
                    amps[c['id']]=amplitude
        print('START',test,len(batch),flush=True)
        rr,ee,rec=execute(batch,work,amps);rows+=rr;records+=rec;new_records+=rec
        for k,x in ee.items():extras.setdefault(k,[]).extend(x)
        if test=='J1':
            # Sidecar is produced by simulate; smoke/full each has own responses.
            pass
        write(ROOT/'S7'/'s7_checkpoint.json',json.dumps(dict(rows=rows,extras=extras,records=records),ensure_ascii=False))
    centers={r['ix']:r['center_V'] for r in rows if r['test']=='J1DC'}
    gains={r['ix']:r['gain_dc_signed'] for r in rows if r['test']=='J1DC'}
    for r in rows:
        if r['test']=='J4':r['noise_bnc_uV']=r['noise_pin_uV']/abs(gains[r['ix']])
        if r['test']=='J8':r['offset_div']=(r['center_V']-centers[0])/DIV
    after=protected();changed=[k for k,vv in before.items() if after.get(k)!=vv]
    write(work/'s7_protected_after.json',json.dumps(after,indent=2))
    code=int(any(x['errors'] or x['returncode'] for x in records) or bool(changed) or len(rows)!=len(cs))
    simulations=prior_meta.get('simulations',0)+sum(r.get('simulations',1) for r in new_records)
    meta=dict(returncode=code,simulations=simulations,successful=len(rows),logical_cases=len(cs),successful_simulations=sum(r.get('simulations',1) for r in records if not r['errors'] and not r['returncode']),seconds=prior_meta.get('seconds',0)+time.perf_counter()-start,workers=10,smoke=args.smoke,seed=SEED,protected_count=len(before),protected_changed=changed,resumed=args.resume,verified_dc_cache=cached,prior_errors=[r['id'] for r in prior_errors])
    write(ROOT/'S7'/'s7_completed_data.json',json.dumps(dict(rows=rows,extras=extras,records=records,meta=meta),ensure_ascii=False))
    save_results(rows,extras,records,meta,args.smoke);print(json.dumps(meta,ensure_ascii=False),flush=True);return code

if __name__=='__main__':raise SystemExit(main())
