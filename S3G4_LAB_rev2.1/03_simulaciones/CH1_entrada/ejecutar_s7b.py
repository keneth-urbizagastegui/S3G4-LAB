"""S7b contract. Ten LTspice workers from preflight onwards.

Only new files are written. Exit 0 means complete execution, not electrical pass.
Replay: copy CH1_entrada and set S3G4_MODELS to immutable manufacturer models.
"""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import argparse, csv, hashlib, json, re, subprocess, time, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import numpy as np
import ejecutar_s7 as old

ROOT = Path(__file__).resolve().parent
MODELS, LT = old.MODELS, old.LT
PROJECT = ROOT.parents[2] if (ROOT.parents[2]/'ai-context').exists() else MODELS.parents[1]
SEED = 2026100371
SIM_TIMEOUT = 120
NUMERIC_RETRY = False
BIAS_LOCKS = [threading.Lock() for _ in range(12)]
DIV = old.DIV
SCALES = old.SCALES
NOM = dict(old.NOM, CS=1.20e-9, CEQ=8.67e-12)
INC = ROOT/'comun/ch1_comun_s7b.inc'
TEXT = INC.read_text(encoding='utf-8')
BASE = old.BASE + ['phase','ix','CPL','rail_plus_set_V','rail_minus_set_V','dc_limit_V']
METRICS = old.METRICS + ['offset_uncal_V','offset_uncal_div','dac_center_V','position_plus_div','position_minus_div','offset_compensable','position_pass','trimmer_required_pF','trimmer_used_pF','trimmer_pass','mux_low_margin_V','mux_high_margin_V','mux_supply_max_V','rail_plus_min_V','rail_plus_max_V','rail_minus_min_V','rail_minus_max_V']
FIELDS = BASE + METRICS
write, csv_write, table = old.write, old.csv_write, old.table

def run_lt(path,work,timeout=SIM_TIMEOUT):
    # LTspice can retain inherited pipe handles on an error dialog. Do not
    # communicate through pipes; on timeout terminate the entire process tree.
    proc=subprocess.Popen([str(LT),'-b',str(path)],cwd=work,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15)
        proc.wait(timeout=15)
        raise
    return proc

def checkpoint_write(path,text):
    temporary=path.with_suffix('.tmp')
    write(temporary,text)
    for attempt in range(20):
        try:
            temporary.replace(path)
            return
        except PermissionError:
            if attempt==19:raise
            time.sleep(.1)

def extract(text, name, newname=None):
    s = re.search(r'^\.subckt '+name+r'\b[\s\S]*?^\.ends[^\n]*',text,re.M|re.I)[0]
    return s.replace(name,newname or name).splitlines()

def nominal_value(expr):
    expr = expr.strip('{}')
    expr = re.sub(r'(?i)(?<![\w.])(\d+(?:\.\d*)?|\.\d+)(meg|[kmunpf])\b',lambda m:str(float(m[1])*{'meg':1e6,'k':1e3,'m':1e-3,'u':1e-6,'n':1e-9,'p':1e-12,'f':1e-15}[m[2].lower()]),expr)
    return float(eval(expr, {'__builtins__':{}},dict(NOM,CS_S7B=NOM['CS'],CEQ_S7B=NOM['CEQ'])))

@lru_cache(maxsize=500)
def realization(n):
    """Same physical board in all four scales and all analyses, fixed seed.

    Trimmer is adjusted, not randomly toleranced. Its 2..6 pF range is physical.
    Track parasitics 1/3 pF use 50%; other explicit capacitances use 5%.
    No variation of ideal contact resistances or internal model components.
    """
    rng = np.random.default_rng(np.random.SeedSequence([SEED,n]))
    rec=[]; values={}
    def draw(name, nominal, tolerance, unit='factor'):
        d=float(rng.uniform(-1,1));factor=1+tolerance*d
        value=nominal*factor if unit=='factor' else tolerance*d
        values[name]=value
        rec.append(dict(mc=n,component=name,nominal_SI=nominal,tolerance=tolerance,draw=d,factor=factor if unit=='factor' else '',value_SI=value,seed=SEED))
        return value
    # Supplies/offset are drawn first, then passive instances in circuit order.
    rp=draw('RAIL_PLUS',4.90,.02);rn=draw('RAIL_MINUS_MAG',4.90,.02)
    vref=draw('VREF',2.5,.002)
    offsets={k:draw(k,0,t,'offset') for k,t in [('VO101',715e-6),('VOA',3e-3),('VOB',3e-3),('VOFA',3e-3),('VOFB',3e-3),('VO836',400e-6)]}
    specs=[('FRONT_S7B','FRONT_S7_MC','XFE',TEXT),
           ('LADDER_S3','LADDER_S7_MC','XLAD',(ROOT/'comun/ch1_comun_s3.inc').read_text(encoding='utf-8')),
           ('SK_S7B','SK_S7_MCA','X105A',TEXT),('SK_S7B','SK_S7_MCB','X105B',TEXT),
           ('CHANNEL_S7B','CHANNEL_S7_MC','XCH',TEXT)]
    blocks=[]
    for name,new,prefix,text in specs:
        lines=extract(text,name,new)
        for j,line in enumerate(lines):
            if not re.match(r'^[RC]\w*\s',line,re.I): continue
            el,a,b,expr=line.split(None,3)
            if el.lower().startswith(('rk','rsw')) or el.lower() in ['cin','ct2trim']: continue
            tol=.01 if el[0].upper()=='R' else .05
            if prefix=='XFE' and el.lower() in ['rt1','rt2','rb']:tol=.001
            if el[0].upper()=='C' and el.lower() in ['cpcb','cma','cmb','csel','cbnc','csum']:tol=.50
            # CF=1 pF is a C0G component, not track parasitic.
            if prefix in ['X105A','X105B']:
                params={'RA':NOM['RFILT1_S7' if prefix=='X105A' else 'RFILT2_S7'],
                        'RB':NOM['RFILT1_S7' if prefix=='X105A' else 'RFILT2_S7'],
                        'CF':NOM['CFILT1_S7' if prefix=='X105A' else 'CFILT2_S7'],
                        'CG':NOM['CGILT1_S7' if prefix=='X105A' else 'CGILT2_S7']}
                nominal=params.get(expr.strip('{}'),NOM.get(expr.strip('{}'),0))
            elif expr.startswith('{if('):
                nominal=NOM['COFF_RELE'] if el.lower().startswith('ck') else NOM['COFF_SW']
            else:nominal=nominal_value(expr)
            val=draw(prefix+':'+el,nominal,tol)
            if expr.startswith('{if('):
                lines[j]=f'{el} {a} {b} '+'{('+expr.strip('{}')+f')*{val/nominal:.17g}'+'}'
            else:lines[j]=f'{el} {a} {b} {val:.17g}'
        if prefix=='XCH':
            for j,line in enumerate(lines):
                lines[j]=line.replace('FRONT_S7B','FRONT_S7_MC').replace('LADDER_S3','LADDER_S7_MC')
                if line.startswith('X105A'):lines[j]=lines[j].replace('SK_S7B','SK_S7_MCA')
                if line.startswith('X105B'):lines[j]=lines[j].replace('SK_S7B','SK_S7_MCB')
                if line.startswith(('XPROTA','XPROTB')):
                    val=draw(line.split()[0]+':RSER',NOM['R_SER_S7'],.01)
                    lines[j]=lines[j].replace('{R_SER_S7}',str(val))
        blocks.append(lines)
    # S2b tau formula with realized physical components and diode capacitance.
    cj=lambda rail:1.9002e-12/(1+rail/1.2722)**.35193
    rbp=values['XFE:Rb']*values['XFE:Rbias']/(values['XFE:Rb']+values['XFE:Rbias'])
    rtop=values['XFE:Rt1']+values['XFE:Rt2']
    c1=values['XFE:Ct1'];cf=values['XFE:Ct2fixed']
    # Sum two OFF coupling-switch capacitors really connected in DC mode.
    csel=cj(rp)+cj(rn)+values['XFE:Csel']+2.5e-12+values['XFE:CswAC']+values['XFE:CswGND']
    ctop_needed=rbp*(values['XFE:Cb']+csel+values['XFE:Ctap'])/rtop-values['XFE:Ck1a1']
    required=c1*ctop_needed/(c1-ctop_needed)-cf
    used=float(np.clip(required,2e-12,6e-12))
    for j,line in enumerate(blocks[0]):
        if line.startswith('Ct2trim '):blocks[0][j]=f'Ct2trim M TAP {used:.17g}'
    values['TRIM_REQUIRED']=required;values['TRIM_USED']=used
    rec.extend([dict(mc=n,component=k,nominal_SI='',tolerance='',draw='',factor='',value_SI=values[k],seed=SEED) for k in ['TRIM_REQUIRED','TRIM_USED']])
    return dict(lines=sum(blocks,[]),records=rec,values=values,rp=rp,rn=rn,vref=vref,offsets=offsets,required=required,used=used,trimmer_pass=bool(2e-12<=required<=6e-12))

def mc_subcircuits(c):
    if c['mc']<0:return [],[]
    r=realization(c['mc']);return r['lines'],[dict(x,id=c['id']) for x in r['records']]

# Reuse S7's tested deck/analysis utilities in memory; no previous file writes.
old.mc_subcircuits=mc_subcircuits

def case(test,ix=0,mc=-1,phase='K1',**kw):
    c=old.case(test,ix,mc,**kw);c.update(phase=phase,CPL=0,rail_plus_set_V=4.90,rail_minus_set_V=4.90,dc_limit_V=40.)
    c['id']='s7b_'+c['id']+'_'+phase.lower()+'_rp4p9_rn4p9_cpldc'
    if phase=='K2DC':c['id']=c['id'].replace('dac1p25','dacsweep0p2to2p3')
    if mc>=0:
        r=realization(mc);c.update(rail_plus_set_V=r['rp'],rail_minus_set_V=r['rn'])
        c['id']=c['id'].replace('_rp4p9_rn4p9',f'_rp{old.s4.number(r["rp"])}_rn{old.s4.number(r["rn"])}')
    return c

def net(c,source_amp=None):
    deck=old.net(c,source_amp).replace(str(ROOT/'comun/ch1_comun_s7.inc'),str(INC))
    deck=deck.replace('RAILS_S2B POWER=1','RAILS_S7B POWER=1').replace('RAILS_S7_MC POWER=1','RAILS_S7B POWER=1')
    deck=deck.replace('CHANNEL_S7 POS=', 'CHANNEL_S7B POS=')
    r=realization(c['mc']) if c['mc']>=0 else None
    rp,rn=(r['rp'],r['rn']) if r else (c['rail_plus_set_V'],c['rail_minus_set_V'])
    deck=deck.replace('RAILS_S7B POWER=1',f'RAILS_S7B POWER=1 RP={rp:.17g} RN={rn:.17g}')
    if r:deck=deck.replace('VREF VREF 0 {VREF_NOM}',f'VREF VREF 0 {r["vref"]:.17g}')
    lines=deck.splitlines()
    for j,line in enumerate(lines):
        if line.startswith('XCH BNC '):
            lines[j]=line+f' CPL={c["CPL"]}'+(' '+' '.join(f'{k}={x:.17g}' for k,x in r['offsets'].items()) if r else '')
    deck='\n'.join(lines)+'\n'
    if c.get('phase')=='K2DC':
        lim=.01*c['scale_V_div']
        sweep=c.get('k2_sweep','gainplus')
        dc=(f'.dc Vsrc 0 {lim:.17g} {lim:.17g}' if sweep=='gainplus' else
            f'.dc Vsrc 0 {-lim:.17g} {-lim:.17g}' if sweep=='gainminus' else
            '.dc VDAC 1.25 .2 -.005' if sweep=='dacminus' else '.dc VDAC 1.25 2.3 .005')
        deck=re.sub(r'^\.dc .*$',dc,deck,flags=re.M)
        deck=re.sub(r'^\.meas DC .*$',old.meas(c,'DC','adc_min_V','MIN V(PIN)'),deck,flags=re.M)
        deck=deck.replace('.save V(PIN) V(BNC)','.save V(PIN) V(BNC) V(DAC)')
    if c['test']=='J5':
        lim=c['dc_limit_V']
        direction=c.get('dc_direction')
        dc=f'.dc Vsrc 0 {lim*direction:.17g} {.001*direction:.17g}' if direction else f'.dc Vsrc {-lim:.17g} {lim:.17g} .05'
        deck=re.sub(r'^\.dc .*$',dc,deck,flags=re.M)
        extra=['V(XCH:'+n+')' for n in ['bo','y1','y2','y3','y4','y5','y7','common','m','tap','rsm','x1','eq','b','sel','rawin']]+['V(DAC)']
        deck=re.sub(r'^(\.save .*?)$',lambda m:m[0]+' '+' '.join(extra),deck,flags=re.M)
    return deck

def analyze(c,raw,row):
    if c['test']=='J8' and c.get('dc_retry'):
        if not np.isclose(raw['v(dac)'][-1],c['vdac_V'],atol=1e-9) or np.max(abs(raw['v(bnc)']))>1e-12:
            raise ValueError('Offset continuation did not reach the requested state')
        center=float(raw['v(pin)'][-1])
        row.update(center_V=center,adc_min_V=center,adc_max_V=center)
        return {}
    if c['phase']=='K2DC':
        x,y,d=raw['v(bnc)'],raw['v(pin)'],raw['v(dac)']
        centers=[];gains=[]
        for dac in [.2,1.25,2.3]:
            mask=np.isclose(d,dac,atol=1e-9)
            if dac==1.25:
                if len(np.unique(x[mask]))!=3:raise ValueError('K2DC requires three distinct source points at DAC center')
                gain,center=np.polyfit(x[mask],y[mask],1)
            else:
                if not mask.any():raise ValueError('Missing DAC endpoint')
                gain=0.;center=float(y[mask].mean())
            centers.append(float(center));gains.append(float(gain))
        slope=(centers[1]-centers[0])/(1.25-.2)
        dac_center=1.25+(1.25-centers[1])/slope
        row.update(gain_dc_signed=gains[1],gain_nominal_signed=-DIV/c['scale_V_div'],
                   gain_error_pct=100*(gains[1]/(-DIV/c['scale_V_div'])-1),center_V=centers[1],
                   offset_uncal_V=centers[1]-1.25,offset_uncal_div=(centers[1]-1.25)/DIV,
                   dac_center_V=dac_center,position_plus_div=(centers[0]-1.25)/DIV,
                   position_minus_div=(1.25-centers[2])/DIV,
                   offset_compensable=bool(.2<=dac_center<=2.3),
                   position_pass=bool(.2<=dac_center<=2.3 and centers[0]>=1.25+4.5*DIV and centers[2]<=1.25-4.5*DIV))
        r=realization(c['mc']);row.update(trimmer_required_pF=r['required']*1e12,trimmer_used_pF=r['used']*1e12,trimmer_pass=r['trimmer_pass'])
        return {}
    if c['test']=='J5':
        # Preserve S7 stage analysis with exact sweep endpoints mapped to ±40.
        lim=c['dc_limit_V'];fake=dict(raw);fake['v(bnc)']=raw['v(bnc)']*40/lim
        extra=old.analyze(c,fake,row)
        for r in extra['limits']:
            for key in ['differential_at_bnc_V','plus_current_at_bnc_V','minus_current_at_bnc_V']:r[key]*=lim/40
            r.update(phase=c['phase'],POS=c['POS'],CPL=c['CPL'],dc_limit_V=lim,rail_plus_set_V=c['rail_plus_set_V'],rail_minus_set_V=c['rail_minus_set_V'])
        lo,hi=raw['v(vn)'],raw['v(vp)']
        mux=[raw['v(xch:'+n+')'] for n in ['bo','y1','y2','y3','y4','y5','y7','common']]+[np.zeros(len(lo))]
        row.update(mux_low_margin_V=min(float((x-lo).min()) for x in mux),
                   mux_high_margin_V=min(float((hi-x).min()) for x in mux),mux_supply_max_V=float((hi-lo).max()),
                   rail_plus_min_V=float(hi.min()),rail_plus_max_V=float(hi.max()),rail_minus_min_V=float(lo.min()),rail_minus_max_V=float(lo.max()))
        # Front-end component stress (DC), inherited 200 V parts.
        pairs={'Rt1':('bnc','m',NOM['RT1']), 'Rt2':('m','tap',NOM['RT1']),
               'Rb':('tap','0',NOM['RB']),'Rs1':('bnc','rsm',NOM['RS1']),
               'Rs2':('rsm','x1',NOM['RS2']),'Req':('eq','0',NOM['REQ']),
               'Cs':('bnc','x1',None),'Ceq':('eq','0',None),'Ct1':('bnc','m',None),'Ct2':('m','tap',None),
               'Ctrimmer':('m','tap',None),'Cb':('tap','0',None),'CAc':('sel','xch:xfe:t2',None)}
        def node(n):return raw['v(bnc)'] if n=='bnc' else np.zeros(len(lo)) if n=='0' else raw['v('+n+')'] if n.startswith('xch:') else raw['v(xch:'+n+')']
        # C_AC stress needs its actual second terminal, saved separately.
        pairs.pop('CAc')
        extra['stress']=[dict(id=c['id'],part=k,voltage_V=float(abs(node(a)-node(b)).max()),power_W=float(((node(a)-node(b))**2/R).max()) if R else '',dc_limit_V=lim) for k,(a,b,R) in pairs.items()]
        return extra
    return old.analyze(c,raw,row)

def protected():
    files=[p for p in ROOT.rglob('*') if p.is_file() and not p.is_relative_to(ROOT/'S7b') and not p.name.startswith('s7b_') and p.name not in ['ejecutar_s7b.py','ch1_comun_s7b.inc','ACTA_S7b.md','RESPUESTA_FINAL_S7b.md'] and p.suffix.lower() not in ['.log','.raw','.db','.pyc'] and '__pycache__' not in p.parts]
    files += [p for p in MODELS.rglob('*') if p.is_file()]
    files += [PROJECT/'ai-context'/n for n in ['STATE.md','DECISIONS.md']]
    return {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.exists()}

def simulate(c,work,source_amp=None):
    if (NUMERIC_RETRY or c.get('retry_request')) and c['test'] in ['J2','J8','J5'] and not c.get('retry_child') and not c.get('dc_direction'):
        children=[]
        ac=case('J1',c['ix']);ac['id']+='_biasonly'
        bias=work/(ac['id']+'.bias')
        with BIAS_LOCKS[c['ix']]:
            if not bias.exists():
                _,_,rec=simulate(ac,work);children.append(rec)
                if rec['errors'] or rec['returncode']:
                    bias.unlink(missing_ok=True)
                    return {},{},dict(id=c['id'],returncode=1,errors=rec['errors'],warnings=rec['warnings'],simulations=rec['simulations'],children=children)
        if c['test']=='J5':
            guide=case('J1',c['ix'],phase='K3GUIDE')
            guide.update(rail_plus_set_V=c['rail_plus_set_V'],rail_minus_set_V=c['rail_minus_set_V'],CPL=c['CPL'],bias_path=str(bias),dc_iteration_limit=1000)
            guide['id']=guide['id'].replace('_rp4p9_rn4p9',f'_rp{old.s4.number(c["rail_plus_set_V"])}_rn{old.s4.number(c["rail_minus_set_V"])}').replace('_cpldc','_cplac' if c['CPL'] else '_cpldc')
            exact=work/(guide['id']+'.bias')
            with BIAS_LOCKS[c['ix']]:
                if not exact.exists():
                    _,_,rec=simulate(guide,work);children.append(rec)
                    if rec['errors'] or rec['returncode']:
                        exact.unlink(missing_ok=True)
                        return {},{},dict(id=c['id'],returncode=1,errors=rec['errors'],warnings=rec['warnings'],simulations=sum(r['simulations'] for r in children),children=children)
            bias=exact
        child=dict(c,retry_child=True,bias_path=str(bias),iteration_limit=1000 if c['test']=='J2' else None,dc_retry=c['test']=='J8',dc_iteration_limit=1000 if c['test']=='J5' else None)
        child['id']+='_retry_bias_itl4_1000' if c['test']=='J2' else '_retry_dacfrom1p25_maxstep5m' if c['test']=='J8' else '_retry_bias_exactrails'
        row,extra,rec=simulate(child,work,source_amp);children.append(rec)
        record=dict(id=c['id'],returncode=rec['returncode'],errors=[x for r in children for x in r['errors']],warnings=[x for r in children for x in r['warnings']],simulations=sum(r['simulations'] for r in children),children=children)
        if row:
            row['id']=c['id']
            for rr in extra.values():
                for r in rr:
                    if isinstance(r,dict) and r.get('id')==child['id']:r['id']=c['id']
        return row,extra,record
    if c['phase']=='K2DC' and not c.get('dac_point'):
        parts=[];children=[]
        ac=case('J3',c['ix'],c['mc'],phase='K2')
        bias=work/(ac['id']+'.bias')
        if not bias.exists():
            _,_,rec=simulate(ac,work);children.append(rec)
            if rec['errors'] or rec['returncode']:return {},{},rec
        for sweep in ['gainplus','gainminus','dacminus','dacplus']:
            child=dict(c,vdac_V=1.25,dac_point=True,k2_sweep=sweep,bias_path=str(bias))
            child['id']=c['id'].replace('dacsweep0p2to2p3',sweep+'_dacstart1p25')
            lim=old.s4.number(.01*c['scale_V_div'])
            state='src0top'+lim if sweep=='gainplus' else 'src0ton'+lim if sweep=='gainminus' else 'srczero_dac1p25to0p2_step5m' if sweep=='dacminus' else 'srczero_dac1p25to2p3_step5m'
            child['id']=re.sub(r'_sweep[^_]+_', '_'+state+'_',child['id'])
            _,ex,rec=simulate(child,work);children.append(rec)
            if rec['errors'] or rec['returncode']:break
            parts.append(ex['_raw'])
        record=dict(id=c['id'],returncode=int(len(parts)!=4),errors=[x for r in children for x in r['errors']],warnings=[x for r in children for x in r['warnings']],simulations=sum(r['simulations'] for r in children),children=children)
        if len(parts)!=4:return {},{},record
        raw={k:np.concatenate([p[k] for p in parts]) for k in ['v(bnc)','v(pin)','v(dac)']}
        row=dict(c);return row,analyze(c,raw,row),record
    # All DC sweeps start at zero and walk to each endpoint to avoid branch jumps.
    if c['test']=='J5' and not c.get('dc_direction'):
        data={};children=[]
        for direction in [-1,1]:
            child=dict(c,dc_direction=direction)
            sweep=('sweep0n' if direction<0 else 'sweep0p')+old.s4.number(c['dc_limit_V'])+'_step1m'
            child['id']=re.sub(r'sweepn(?:40p40|100p100)',sweep,c['id'])
            _,ex,record=simulate(child,work);children.append(record)
            if record['errors'] or record['returncode']:break
            data[direction]=ex['_raw']
        record=dict(id=c['id'],returncode=int(len(data)!=2),errors=[x for r in children for x in r['errors']],warnings=[x for r in children for x in r['warnings']],simulations=len(children),children=children)
        if len(data)!=2:
            if not c.get('retry_child'):return retry_numerical(c,work,source_amp,record)
            return {},{},record
        raw={k:np.r_[data[-1][k][::-1],data[1][k][1:]] for k in data[-1]}
        row=dict(c);return row,analyze(c,raw,row),record
    if c['phase'] in ['K2','K2NOISE'] and not c.get('bias_path'):
        ac=case('J3',c['ix'],c['mc'],phase='K2')
        own=work/(ac['id']+'.bias')
        smoke=ROOT/'S7b'/'smoke'/(case('J3',c['ix'],0,phase='K2')['id']+'.bias')
        seed=own if own.exists() else smoke if smoke.exists() else None
        if seed:
            c=dict(c,bias_path=str(seed),dc_iteration_limit=1000)
    path=work/(c['id']+'.cir');deck=net(c,source_amp)
    if c['phase']=='K2' or c['test']=='J1':deck=deck.replace('\n.end\n',f'\n.savebias "{path.with_suffix(".bias")}" internal\n.end\n')
    if c.get('bias_path'):deck=deck.replace('\n.end\n',f'\n.loadbias "{c["bias_path"]}"\n.end\n')
    if c.get('iteration_limit'):deck=deck.replace('\n.end\n',f'\n.options itl4={c["iteration_limit"]}\n.end\n')
    if c.get('dc_iteration_limit'):deck=deck.replace('\n.end\n',f'\n.options itl1={c["dc_iteration_limit"]} itl2={c["dc_iteration_limit"]}\n.end\n')
    if c.get('dc_retry'):
        target=c['vdac_V'];delta=target-1.25
        step=delta/max(1,int(np.ceil(abs(delta)/.005))) if delta else .005
        deck=re.sub(r'^VDAC DAC 0 .*$', 'VDAC DAC 0 1.25',deck,flags=re.M)
        deck=re.sub(r'^\.dc .*$',f'.dc VDAC 1.25 {target:.17g} {step:.17g}',deck,flags=re.M)
        deck=re.sub(r'^\.meas DC .*$',old.meas(c,'DC','center_V',f'FIND V(PIN) AT={target:.17g}'),deck,flags=re.M)
        deck=deck.replace('.save V(PIN) V(BNC)','.save V(PIN) V(BNC) V(DAC)')
    write(path,deck)
    for ext in ['.raw','.op.raw','.log','.db']:path.with_suffix(ext).unlink(missing_ok=True)
    row=dict(c);record=dict(id=c['id'],returncode=0,errors=[],warnings=[],simulations=1)
    try:
        timeout=600 if c['test']=='J5' else 900 if c['test'] in ['J2','J6','J9'] else SIM_TIMEOUT
        record['timeout_s']=timeout
        started=time.perf_counter()
        proc=run_lt(path,work,timeout)
        record['seconds']=time.perf_counter()-started
        vals,errs,warns,_=old.s4.s3.prior.old.read_log(path.with_suffix('.log'))
        expected={x.lower() for x in re.findall(r'^\.meas\s+\w+\s+(\w+)',deck,re.M|re.I)}
        if expected-set(vals):errs.append('Missing measures '+str(expected-set(vals)))
        record.update(returncode=proc.returncode,errors=errs,warnings=warns)
        if errs or proc.returncode:
            if c['test'] in ['J2','J8'] and not c.get('retry_child'):return retry_numerical(c,work,source_amp,record)
            return {},{},record
        raw=old.s4.s3.raw_read(path.with_suffix('.raw'))
        row.update({k[len(c['id'])+1:]:v for k,v in vals.items() if k in expected})
        if c.get('dac_point'):
            expected_n=2 if c['k2_sweep'].startswith('gain') else 211
            if len(raw['v(bnc)'])!=expected_n:raise ValueError('Incomplete DAC continuation')
            for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
            return row,{'_raw':raw},record
        if c.get('dc_direction'):
            x=raw['v(bnc)'];lim=c['dc_limit_V'];direction=c['dc_direction']
            if len(x)!=round(lim/.001)+1 or abs(x[0])>1e-8 or abs(x[-1]-lim*direction)>1e-8:raise ValueError('Incomplete DC continuation')
            for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
            return row,{'_raw':raw},record
        extra=analyze(c,raw,row)
        if c['test']=='J3':extra['mc_components']=mc_subcircuits(c)[1]
        if c['test']=='J1':write(path.with_suffix('.response.json'),json.dumps(dict(f=raw['frequency'].tolist(),mag=abs(raw['v(pin)']/raw['v(bnc)']).tolist())))
        for ext in ['.raw','.op.raw','.db']:path.with_suffix(ext).unlink(missing_ok=True)
        return row,extra,record
    except Exception as e:
        record['errors'].append(repr(e))
        if c['test'] in ['J2','J8'] and not c.get('retry_child'):return retry_numerical(c,work,source_amp,record)
        return {},{},record

def retry_numerical(c,work,source_amp,record):
    row,extra,retry=simulate(dict(c,retry_request=True),work,source_amp)
    combined=dict(id=c['id'],returncode=retry['returncode'],errors=retry['errors'],warnings=record['warnings']+retry['warnings'],simulations=record['simulations']+retry['simulations'],children=[record,retry])
    return row,extra,combined

def execute(cases,work,amps=None,on_progress=None):
    rows=[];extras={};records=[]
    with ThreadPoolExecutor(max_workers=10) as pool:
        fs={pool.submit(simulate,c,work,(amps or {}).get(c['id'])):c for c in cases}
        for fut in as_completed(fs):
            r,e,rec=fut.result();records.append(rec)
            if r:rows.append(r)
            for k,rr in e.items():extras.setdefault(k,[]).extend(rr)
            write(work/'s7b_progress.json',json.dumps(dict(completed=len(records),total=len(cases),phase=rec['id'],errors=sum(bool(x['errors'] or x['returncode']) for x in records))))
            if on_progress and len(records)%50==0:on_progress(rows,extras,records)
            if rec['errors']:print('ERROR',rec['id'],rec['errors'],flush=True)
            elif len(records)%25==0 or len(cases)<10:print('PROGRESS',len(records),'/',len(cases),flush=True)
    return rows,extras,records

def jobs(smoke=False,preflight=False):
    ix=[0,6] if smoke or preflight else range(12)
    cs=[case('J1',j) for j in ix]+[case('J1DC',j,kind='dc') for j in ix]
    cs += [case('J2',j,kind=k,amp=SCALES[j]*(1 if k=='step' else 3)) for j in ix for k in ['step','square']]
    cs += [case('J4',j,kind='noise') for j in ix]
    cs += [case('J8',j,kind='offset',vdac=float(x)) for j in ix for x in np.linspace(.2,2.3,9)]
    if preflight:return cs
    combos=[(p,n) for p in [4.80,5.00] for n in [4.80,5.00]]
    for rp,rn in combos:
        for j in ([0] if smoke else [0,1,5,6,11]):
            c=case('J5',j,phase='K3',kind='dc');c.update(rail_plus_set_V=rp,rail_minus_set_V=rn)
            c['id']=c['id'].replace('_rp4p9_rn4p9',f'_rp{old.s4.number(rp)}_rn{old.s4.number(rn)}');cs.append(c)
        for j in [0,6]:
            for cpl in ([0] if smoke else [0,1]):
                c=case('J5',j,phase='K3E5',kind='dc');c.update(CPL=cpl,dc_limit_V=100.,rail_plus_set_V=rp,rail_minus_set_V=rn)
                c['id']=c['id'].replace('sweepn40p40','sweepn100p100').replace('_rp4p9_rn4p9_cpldc',f'_rp{old.s4.number(rp)}_rn{old.s4.number(rn)}_cpl'+('ac' if cpl else 'dc'));cs.append(c)
    count=3 if smoke else 500
    for j in [0,3,6,9]:
        cs += [case('J3',j,n,phase='K2') for n in range(count)]
        cs += [case('J1DC',j,n,phase='K2DC',kind='dc') for n in range(count)]
    for j in [0,6]:cs += [case('J4',j,n,phase='K2NOISE',kind='noise') for n in range(2 if smoke else 100)]
    cs += [case('J6',j,phase='K4',kind='pulse',amp=sgn*a) for j,aa in [(0,[.2,2,4.5]),(6,[20,40])] for a in aa for sgn in [-1,1]]
    cs += [case('J9',phase='K1',kind='idle'),case('J9',phase='K1',kind='sine',target=2e6)]
    return cs

def criterion_rows(rows,extra,smoke):
    ac=[r for r in rows if r['test'] in ['J1','J3']];mc=[r for r in rows if r['test']=='J3']
    noise=[r for r in rows if r['test']=='J4'];dc=[r for r in rows if r['phase']=='K2DC'];recovery=[r for r in rows if r['test']=='J6' and not r['bav199_conducts']]
    out=[]
    def add(k,rr,pred,scope):
        success=sum(bool(pred(r)) for r in rr);n=len(rr);fraction=success/n if n else 0
        out.append(dict(criterion=f'S7b-C{k}',scope=scope,N=n,pass_count=success,fraction=fraction,status='PASA' if n and fraction>=.95 else 'FALLA'))
    for j in sorted({r['ix'] for r in ac}):
        for nominal in [True,False]:
            rr=[r for r in ac if r['ix']==j and (r['mc']<0)==nominal]
            if not rr:continue
            scope=f'{SCALES[j]} V/div '+('nominal' if nominal else 'MC')
            add(1,rr,lambda r:1.7e6<=r['minus3_Hz']<=2.3e6,scope)
            add(2,rr,lambda r:r['peak_db']<=1,scope)
    for j in sorted({r['ix'] for r in noise}):
        for nominal in [True,False]:
            rr=[r for r in noise if r['ix']==j and (r['mc']<0)==nominal]
            if rr:add(3,rr,lambda r:r['noise_pct_div']<=.5,f'{SCALES[j]} V/div '+('nominal' if nominal else 'MC'))
    for j in [0,3,6,9]:add(4,[r for r in dc if r['ix']==j],lambda r:abs(r['gain_error_pct'])<=5,f'{SCALES[j]} V/div')
    boards={r['mc']:r for r in dc};add(5,list(boards.values()),lambda r:r['trimmer_pass'],'placas únicas')
    limits={}
    for r in extra.get('limits',[]):limits.setdefault(r['id'],[]).append(r)
    def protection(r):
        return r['adc_min_V']>=0 and r['adc_max_V']<=3.3 and r['mux_low_margin_V']>=0 and r['mux_high_margin_V']>=0 and r['mux_supply_max_V']<=10 and all(max(s['plus_current_abs_max_A'],s['minus_current_abs_max_A']) <=(.010 if s['stage']=='OPA810' else .00043) if s['stage'] in ['OPA810','OPA836'] else s['differential_abs_max_V']<=2 for s in limits.get(r['id'],[]))
    add(6,[r for r in rows if r['test']=='J5'],protection,'casos deterministas K3; no estimador de placas')
    add(7,recovery,lambda r:r['recovery_us'] is not None and r['recovery_us']<=1,'casos nominales K4; no estimador de placas')
    for j in [0,3,6,9]:add(8,[r for r in dc if r['ix']==j],lambda r:r['position_pass'],f'{SCALES[j]} V/div')
    return out

def save_results(rows,extra,records,meta,profile):
    latest={r['id']:r for r in records}
    meta.update(final_error_cases=sum(bool(r['returncode'] or r['errors']) for r in latest.values()),
                final_warning_cases=sum(bool(r.get('warnings')) for r in latest.values()),
                final_warning_messages=sum(len(r.get('warnings',[])) for r in latest.values()),
                historical_unsuccessful_attempts=sum(bool(r['returncode'] or r['errors']) for r in records))
    out=ROOT/'resultados' if profile=='campaign' else ROOT/'S7b'/profile/'resultados'
    out.mkdir(parents=True,exist_ok=True)
    rows=sorted(rows,key=lambda r:r['id'])
    for r in rows:
        if r['test']=='J8' and r.get('dc_retry'):
            child_id=r['id']+'_retry_dacfrom1p25_maxstep5m'
            log=ROOT/'S7b'/profile/(child_id+'.log')
            vals,errs,_,_=old.s4.s3.prior.old.read_log(log)
            if errs:raise ValueError('Invalid native endpoint measure '+str(log))
            center=vals[child_id.lower()+'_center_v']
            r.update(center_V=center,adc_min_V=center,adc_max_V=center,endpoint_native_log=str(log))
    extra={key:sorted(rr,key=lambda r:(r['id'],str(r.get('stage','')),str(r.get('component','')),str(r.get('part','')))) for key,rr in extra.items()}
    centers={r['ix']:r['center_V'] for r in rows if r['phase']=='K1' and r['test']=='J1DC'}
    gains={(r['ix'],r['mc']):r['gain_dc_signed'] for r in rows if r['test']=='J1DC'}
    for r in rows:
        if r['test']=='J8':r['offset_div']=(r['center_V']-centers.get(r['ix'],1.25))/DIV
        if r['test']=='J4':r['noise_bnc_uV']=r['noise_pin_uV']/abs(gains.get((r['ix'],r['mc']),-DIV/r['scale_V_div']))
    for name,pred in [('k1',lambda r:r['phase']=='K1'),('k2',lambda r:r['phase']=='K2'),('k2_dc_offset',lambda r:r['phase']=='K2DC'),('k2_noise',lambda r:r['phase']=='K2NOISE'),('k3',lambda r:r['test']=='J5'),('k4',lambda r:r['test']=='J6')]:
        csv_write(out/f's7b_{name}.csv',[r for r in rows if pred(r)],FIELDS)
    for key,fields in [('limits',old.LIMIT_FIELDS+['phase','POS','CPL','dc_limit_V','rail_plus_set_V','rail_minus_set_V']),('consumption',old.CON_FIELDS),('mc_components',['id','mc','component','nominal_SI','tolerance','draw','factor','value_SI','seed']),('stress',['id','part','voltage_V','power_W','dc_limit_V'])]:csv_write(out/f's7b_{key}.csv',extra.get(key,[]),fields)
    criteria=criterion_rows(rows,extra,meta['smoke']);csv_write(out/'s7b_criterios.csv',criteria,['criterion','scope','N','pass_count','fraction','status'])
    cal=[dict(escala_V_div=r['scale_V_div'],rele=r['POS'],toma=r['tap'],ganancia_medida=r['gain_dc_signed'],ganancia_nominal=-DIV/r['scale_V_div'],signo=int(np.sign(r['gain_dc_signed']))) for r in rows if r['phase']=='K1' and r['test']=='J1DC']
    csv_write(out/'s7b_tabla_calibracion.csv',cal,['escala_V_div','rele','toma','ganancia_medida','ganancia_nominal','signo'])
    nominal=[]
    for j in sorted({r['ix'] for r in rows if r['test']=='J1'}):
        r=dict(next(r for r in rows if r['test']=='J1' and r['ix']==j))
        for test,metric in [('J1DC','gain_dc_signed'),('J4','noise_pct_div'),('J2','rise_ns')]:
            rr=[x for x in rows if x['test']==test and x['ix']==j and x['mc']==-1 and (test!='J2' or x['kind']=='step')]
            if rr:r[metric]=rr[0][metric]
        nominal.append(r)
    csv_write(out/'s7b_k1_por_escala.csv',nominal,FIELDS)
    stats=[]
    for j in [0,3,6,9]:
        for phase,keys in [('K2',['minus3_Hz','peak_db','atten_4p5m_db']),('K2DC',['gain_dc_signed','gain_error_pct','offset_uncal_V','dac_center_V','position_plus_div','position_minus_div']),('K2NOISE',['noise_pct_div'])]:
            rr=[r for r in rows if r['ix']==j and r['phase']==phase]
            for key in keys:
                if not rr:continue
                x=np.array([r[key] for r in rr]);stats.append(dict(scale_V_div=SCALES[j],metric=key,N=len(x),min=float(x.min()),p2p5=float(np.percentile(x,2.5)),median=float(np.median(x)),p97p5=float(np.percentile(x,97.5)),max=float(x.max())))
    csv_write(out/'s7b_montecarlo_resumen.csv',stats,['scale_V_div','metric','N','min','p2p5','median','p97p5','max'])
    trims=[dict(mc=n,required_pF=realization(n)['required']*1e12,used_pF=realization(n)['used']*1e12,in_range=realization(n)['trimmer_pass']) for n in sorted({r['mc'] for r in rows if r['test']=='J3'})]
    csv_write(out/'s7b_trimmer.csv',trims,['mc','required_pF','used_pF','in_range'])
    doc='# S7b — CH1, tolerancias reales\n\n'+json.dumps(meta,ensure_ascii=False)+'\n\n'+table(criteria,['criterion','scope','N','pass_count','fraction','status'])
    doc+='\n## K1 por escala\n\n'+table(nominal,['scale_V_div','minus3_Hz','peak_db','gain_dc_signed','rise_ns','noise_pct_div','atten_4p5m_db'])
    doc+='\n## Monte Carlo\n\n'+table(stats,['scale_V_div','metric','N','min','p2p5','median','p97p5','max'])
    doc+='\n## Recuperación\n\n'+table([r for r in rows if r['test']=='J6'],['scale_V_div','amplitude_V','recovery_us','bav199_conducts'])
    doc+='\n## Offset nominal\n\n'+table([r for r in rows if r['test']=='J8'],['scale_V_div','vdac_V','center_V','offset_div'])
    doc+='\n## Protecciones en extremos\n\n'+table([r for r in rows if r['test']=='J5'],['scale_V_div','POS','CPL','dc_limit_V','rail_plus_set_V','rail_minus_set_V','adc_min_V','adc_max_V','mux_low_margin_V','mux_high_margin_V','mux_supply_max_V'])
    doc+='\n## Consumo\n\n'+table(extra.get('consumption',[]),old.CON_FIELDS)
    doc+='\n## Método y dudas\n\n'+METHOD
    if meta['final_warning_messages']:
        doc+='\nAdvertencia nativa conservada: J2 cuadrada, 50 mV/div, 69 mensajes de relajación automática de convergencia al inicio (t ≈1.16e−14 s). No se modificaron tolerancias en el netlist; el solver actuó internamente. El caso final tiene todas sus medidas y ninguna excepción; se conserva esta limitación numérica en el registro.\n'
    write(out/'s7b_resumen.md',doc)
    if profile=='campaign':
        write(ROOT/'ACTA_S7b.md',doc)
        final_response(rows,extra,meta,criteria,nominal,stats,trims)
    return rows

def final_response(rows,extra,meta,criteria,nominal,stats,trims):
    doc='# Respuesta final — S7b\n\n'
    doc+='Ficheros: `comun/ch1_comun_s7b.inc`, `ejecutar_s7b.py`, bancos, soluciones iniciales y registros en `S7b/`, `resultados/s7b_*.csv` (incluida tabla de calibración), `ACTA_S7b.md`, este resumen y diario `ai-context/journal/2026-10-04-codex-s7b-reanudacion.md`; diario inicial conservado.\n\n'
    doc+=f'Código **{meta["returncode"]}**; **{meta["simulations"]} ejecuciones nativas**, **{meta["successful"]}/{meta["logical_cases"]} casos lógicos**, **{meta["seconds"]:.1f} s ({meta["seconds"]/60:.2f} min) de tiempo acumulado registrado**, 10 trabajadores. {meta["protected_count"]} archivos protegidos, {len(meta["protected_changed"])} cambios. Código 0 significa campaña ejecutada, no aceptación eléctrica. Las ejecuciones incluyen intentos fallidos y repetidos; las pruebas de diagnóstico y smoke tienen registros separados.\n\n'
    doc+=f'Errores finales: {meta["final_error_cases"]}; advertencias finales: {meta["final_warning_messages"]} mensajes en {meta["final_warning_cases"]} caso. Historial: {meta["historical_unsuccessful_attempts"]} intentos lógicos fallidos o sin medición durable, todos recuperados; incluye los 18 preservados durante el reinicio. Auditoría: `S7b/campaign/s7b_auditoria_cierre.json`.\n\n'
    compact=[]
    for k in range(1,9):
        rr=[r for r in criteria if r['criterion']==f'S7b-C{k}' and (k not in [1,2,3] or 'MC' in r['scope'])]
        desc='; '.join(f'{r["scope"]}: {r["pass_count"]}/{r["N"]} ({100*r["fraction"]:.1f} %)' for r in rr)
        compact.append(dict(criterio=f'S7b-C{k}',fraccion=desc,resultado='PASA' if rr and all(r['status']=='PASA' for r in rr) else 'FALLA'))
    doc+=table(compact,['criterio','fraccion','resultado'])
    doc+='\nC1–C4/C8: fracciones por escala de las mismas 500 placas; C3 usa las primeras 100 por escala. C5 cuenta placas únicas. C6/C7 son fracciones de casos deterministas y no estiman la fracción de placas. Criterios nominales completos: `s7b_criterios.csv`.\n\n'
    paired_dc={n:[r for r in rows if r['phase']=='K2DC' and r['mc']==n] for n in range(500)}
    complete=[rr for rr in paired_dc.values() if len(rr)==4]
    if len(complete)==500:
        gain_all=sum(all(abs(r['gain_error_pct'])<=5 for r in rr) for rr in complete)
        pos_all=sum(all(r['position_pass'] for r in rr) for rr in complete)
        doc+=f'Emparejamiento: ganancia C4 en las cuatro escalas simultáneamente {gain_all}/500 ({gain_all/5:.1f} %); margen C8 en las cuatro escalas simultáneamente {pos_all}/500 ({pos_all/5:.1f} %).\n\n'
    nr=[dict(escala=r['scale_V_div'],MHz=r['minus3_Hz']/1e6,pico_dB=r['peak_db'],G_DC=r['gain_dc_signed'],subida_ns=r.get('rise_ns',''),ruido_pct_div=r.get('noise_pct_div',''),A45_dB=r['atten_4p5m_db']) for r in nominal]
    doc+='## K1 por escala\n\n'+table(nr,['escala','MHz','pico_dB','G_DC','subida_ns','ruido_pct_div','A45_dB'])
    sr=[]
    for r in stats:
        if r['metric'] not in ['minus3_Hz','peak_db','noise_pct_div','gain_dc_signed']:continue
        factor=1e-6 if r['metric']=='minus3_Hz' else 1
        sr.append(dict(escala=r['scale_V_div'],magnitud='−3 dB (MHz)' if factor!=1 else r['metric'],N=r['N'],min=r['min']*factor,p2p5=r['p2p5']*factor,p97p5=r['p97p5']*factor,max=r['max']*factor))
    doc+='\n## Monte Carlo\n\nSemilla '+str(SEED)+', 500 placas emparejadas en cuatro escalas.\n\n'+table(sr,['escala','magnitud','N','min','p2p5','p97p5','max'])
    required=np.array([r['required_pF'] for r in trims]);pct=np.percentile(required,[2.5,97.5])
    doc+=f'\nTrimmer requerido: {required.min():.6f}…{required.max():.6f} pF; P2.5/P97.5: {pct[0]:.6f}/{pct[1]:.6f} pF. Rango 2–6 pF suficiente en {sum(r["in_range"] for r in trims)}/{len(trims)} placas. Se aplica recorte físico en las demás.\n'
    bounds=[]
    for stage in old.STAGES:
        rr=[r for r in extra['limits'] if r['stage']==stage]
        bounds.append(dict(etapa=stage,diferencial_max_V=max(r['differential_abs_max_V'] for r in rr),I_entrada_max_mA=1000*max(max(r['plus_current_abs_max_A'],r['minus_current_abs_max_A']) for r in rr)))
    prot=[r for r in rows if r['test']=='J5']
    doc+='\n## Protecciones con rieles extremos\n\nCombinaciones independientes 4.80/5.00 V; ±40 V en cinco escalas y ±100 V en POS1/100, acoplo DC/AC.\n\n'+table(bounds,['etapa','diferencial_max_V','I_entrada_max_mA'])
    doc+=f'\nADC: {min(r["adc_min_V"] for r in prot):.6f}…{max(r["adc_max_V"] for r in prot):.6f} V. 4051: margen inferior mínimo {min(r["mux_low_margin_V"] for r in prot):.6f} V, superior {min(r["mux_high_margin_V"] for r in prot):.6f} V; alimentación máxima real {max(r["mux_supply_max_V"] for r in prot):.6f} V. Límites: OPA810 10 mA, OPA836 0.43 mA, U103/U105 2 V, ADC 0…3.3 V, 4051 dentro de VEE…VCC y suministro ≤10 V. Detalle por escala/riel: `s7b_limits.csv`, `s7b_k3.csv`.\n'
    fast=[r for r in rows if r['test']=='J6' and not r['bav199_conducts']]
    times=[r['recovery_us'] for r in fast if r['recovery_us'] is not None]
    totals={r['kind']:r['power_mW'] for r in extra['consumption'] if r['stage']=='TOTAL_CHANNEL'}
    doc+=f'\nRecuperación: {len(fast)} casos sin conducción directa BAV199; máximo medido {max(times):.6f} µs. Consumo total simulado: reposo {totals["idle"]:.6f} mW, seno {totals["sine"]:.6f} mW. Consumo por etapa y riel: `s7b_consumption.csv`; calibración: `s7b_tabla_calibracion.csv`.\n'
    doc+='\n## Método y dudas\n\n'+METHOD
    if meta['final_warning_messages']:
        doc+='\nJ2 cuadrada en 50 mV/div conserva 69 advertencias nativas de relajación automática de convergencia al arranque (t ≈1.16e−14 s), sin cambio explícito de tolerancias en el netlist. Sus medidas finales son válidas; se declara la advertencia numérica y se conserva el log.\n'
    write(ROOT/'RESPUESTA_FINAL_S7b.md',doc)

METHOD='''- Cambios nominales únicos: AFE ±4.90 V; C_S fijo 1.20 nF. El circuito recuperado fija C_EQ=8.67 pF; el contrato cita 8.7 pF seleccionado y 8.67 pF nominal. Se conserva esta discrepancia de redondeo sin modificar el circuito durante la reparación numérica. Rieles regulados conservan 0.5 Ω, carga 5/42 mA y 5/39 mA, TVS y todos los valores previos. El 4051 usa los mismos ocho SWI1; niveles altos del decodificador siguen el riel real. No se simulan cambios dinámicos de toma.
- Monte Carlo: semilla 2026100371, 500 placas emparejadas en cuatro escalas; offsets independientes, pasivos independientes por instancia; uniformes, factores guardados. R ±1 %, divisor ±0.1 %; C ±5 %, pistas explícitas de 1/3 pF ±50 %. El trimmer no recibe tolerancia adicional: se ajusta y recorta a 2..6 pF. Réplica C_EQ recibe ±5 % tal como manda §2 aunque la selección en prueba podría reducirlo. CMID y condensadores internos/rieles no se dispersan: §2 especifica C0G y no asigna dispersión a esos otros modelos.
- Trimmer: Rtop=Rt1+Rt2; Rbp=Rb||Rbias; Csel=Cj(V+)+Cj(|V−|)+Csel_pista+2.5 pF+CswAC+CswGND; Ctop=Rbp*(Cb+Csel+Ctap)/Rtop−Coff; Ct2=Ct1*Ctop/(Ct1−Ctop); trimmer=Ct2−Ct2fixed. Cb no se reajusta por placa: el contrato pide dispersarlo ±5 % y ajustar el trimmer. La sonda ×10 motivó el ajuste en S1b; la igualdad de tau se calcula sin sustituir la transferencia BNC→PIN por la de punta de sonda.
- Offset OPA836 ±400 µV: hoja local opa836.pdf, SLOS712J, pp. 10/12, máximo a 25 °C; a −40..125 °C llega a 1080 µV (p.12). Fuentes adicionales en serie con IN+ para los seis amplificadores; no se suprime el offset propio del macromodelo (incertidumbre de doble contabilización de su típico). OPA810 ±715 µV y AD8039 ±3 mV según contrato.
- K2 DC: ganancia medida en tres puntos distintos de entrada (−0.01/0/+0.01 div) con DAC 1.25 V, mediante dos recorridos desde cero. DAC recorrido desde 1.25 hacia 0.2 y 2.3 V, paso 5 mV, entrada cero; se miden centros y extremos, sin sustituir DC por AC. La solución AC de la misma placa/escala se guarda con .savebias internal y se carga como recomendación .nodeset; no impone tensiones permanentes, componentes o tolerancias nuevos. Offset referido a centro ADC 1.25 V; DAC de centrado inferido con pendiente medida entre los dos primeros ajustes; posición restante comprobada con los extremos reales, incluido recorte. ±4.5 div exige llegar a 0.125 y 2.375 V. Esto juzga desplazamiento de traza en entrada cero, no amplitud de señal adicional a esa posición.
- K2 AC/ruido puede reutilizar su propio punto guardado o el punto de mc0 del smoke en la misma escala como recomendación inicial; siempre resuelve nuevamente todos los nodos con los valores y offsets de la placa actual. Se conservan semilla, realizaciones, tolerancias y todos los componentes; itl1/itl2=1000 amplía sólo el número máximo de iteraciones.
- Cada proceso tiene tiempo límite: 120 s AC/DC/ruido, 600 s K3 y 900 s transitorios. Popen sin pipes y taskkill /T /F al vencer, para evitar procesos o manejadores heredados colgados. Las cuatro ejecuciones nativas de cada K2DC se registran como hijas con su estado real en el nombre .meas. CSV y extras se ordenan por claves fijas.
- Si J2 falla numéricamente, reintento automático con la solución AC nominal de la misma escala como guía y itl4=1000; no cambia flancos, amplitudes, paso máximo ni tolerancias. --resume --retry-numerical aplica directamente ese método a los pendientes. El registro conserva los intentos fallidos como hijos/historia, y el resultado final se evalúa por el último intento de cada caso.
- Si J8 falla o agota el tiempo, reintento con la misma guía AC nominal y continuación desde DAC 1.25 V al valor solicitado, paso ≤5 mV calculado para alcanzar exactamente el extremo. Entrada cero; medida en el extremo real solicitado. No se cambia la tensión objetivo.
- Si K3 falla en su punto inicial, reintento con guía AC recalculada en la misma escala, acoplo y combinación de rieles que el caso; itl1/itl2=1000 como presupuesto numérico. Los barridos de protección mantienen extremos y paso de 1 mV; las recomendaciones de nodo se liberan al resolver el circuito.
- K1/J8 conserva definición relativa al centro nominal del S7. J2 conserva flancos y amplitudes S7; K4 conserva final de flanco a 11.02 µs y banda ±0.1 div. Conducción BAV199: polarización directa >0.4 V, no corriente capacitiva.
- K3: cuatro combinaciones de magnitud de riel 4.80/5.00 V, barridos iniciados en 0 y continuados con paso 1 mV a ambos extremos; J5 ±40 V en cinco escalas, E5b ±100 V en POS1/100, DC y AC. No incluye seno 100 Vpk ni ESD: S7b pide E5b en continua. Se guarda cada polaridad real en el nombre .meas. La señal del 4051 se comprueba en los ocho Y y Z, incluso la toma no seleccionada. La corriente OPA810 es del pin de entrada, no la corriente de carga de salida. Corrientes de U103 incluyen su red de protección, cota conservadora.
- C6 y C7 son barridos deterministas, no fracciones poblacionales de placas; se reporta la fracción de casos y se declara que no hay Monte Carlo de sobrecarga/recuperación. C1..C4/C8 se juzgan por escala, no sólo agregando placas. Las muestras de ruido son los primeros 100 casos de las mismas 500 placas. No se presenta 2000 realizaciones emparejadas como 2000 placas independientes.
- No se dispersan GBW, I_B, ganancia abierta, ruido intrínseco ni temperatura: el contrato S7b §2 no los exige, aunque la decisión permanente es más amplia. Ruido sólo AFE de 1 Hz a 3.15 MHz con AD8038_ltspice_ruido_hoja.sub; sin ruido, cuantización, jitter ni desajuste del ADC. SWI1 está declarado para transitorio por Nexperia; uso AC/DC conserva limitación histórica. OPA836 ESD es supuesto externo; BAV99HY Rohm representa BAV99 Nexperia. TVS genérica y absorción de rieles pendientes de placa.
- Contradicción: ±2 % de 4.90 implica 4.802..4.998, y dos rieles máximos suman 9.996 V en la fuente ideal, no 9.95 V. K3 exige extremos redondeados 4.80/5.00: suma de fuente 10.0 V, margen nulo en ese extremo; se informa tensión real tras resistencia/consumo.
- Consumo de macromodelo OPA810 ≈1.9 mA frente a 3.7 mA típico de hoja: reportar simulado no revisa G.3 ni certifica autonomía. Sin carga ficticia U103B. No se eligieron remedios ni se modificaron entregables previos, modelos, STATE, DECISIONS o chequeo_claude. No hay nueva evidencia física.
'''

def main():
    global NUMERIC_RETRY
    parser=argparse.ArgumentParser();parser.add_argument('--smoke',action='store_true');parser.add_argument('--preflight',action='store_true');parser.add_argument('--resume',action='store_true');parser.add_argument('--reports-only',action='store_true');parser.add_argument('--retry-numerical',action='store_true');args=parser.parse_args()
    NUMERIC_RETRY=args.retry_numerical
    profile='preflight' if args.preflight else 'smoke' if args.smoke else 'campaign'
    work=ROOT/'S7b'/profile;work.mkdir(parents=True,exist_ok=True)
    checkpoint=work/'s7b_checkpoint.json'
    if args.reports_only:
        d=json.loads(checkpoint.read_text(encoding='utf-8'));d['rows']=save_results(d['rows'],d['extras'],d['records'],d['meta'],profile)
        checkpoint_write(checkpoint,json.dumps(d,ensure_ascii=False));return d['meta']['returncode']
    start=time.perf_counter();before=protected();write(work/'s7b_protected_before.json',json.dumps(before))
    cs=jobs(args.smoke,args.preflight);rows=[];extras={};records=[];previous_seconds=0
    if args.resume and checkpoint.exists():
        d=json.loads(checkpoint.read_text(encoding='utf-8'));rows=d['rows'];extras=d['extras'];records=d['records'];previous_seconds=d.get('meta',{}).get('seconds',0)
    meta=dict(returncode=1,simulations=sum(r.get('simulations',1) for r in records),logical_cases=len(cs),successful=len(rows),seconds=previous_seconds,workers=10,smoke=args.smoke,preflight=args.preflight,seed=SEED,protected_changed=[])
    def signature(c):
        rails=(c['rail_plus_set_V'],c['rail_minus_set_V']) if c['mc']<0 else ('MC',c['mc'])
        return (c['test'],c['phase'],c['ix'],c['mc'],c['kind'],c['vdac_V'],c['CPL'],c['dc_limit_V'],rails,
                'calculated' if c['test']=='J9' and c['kind']=='sine' else c['amplitude_V'])
    done={signature(r) for r in rows}
    for phase,test in [('K1','J1'),('K1','J1DC'),('K1','J2'),('K1','J4'),('K1','J8'),('K1','J9'),('K3','J5'),('K3E5','J5'),('K2','J3'),('K2NOISE','J4'),('K2DC','J1DC'),('K4','J6')]:
        batch=[c for c in cs if c['phase']==phase and c['test']==test and signature(c) not in done];amps={}
        if not batch:continue
        if test=='J9':
            ac={r['ix']:r for r in rows if r['test']=='J1'}
            for c in batch:
                if c['kind']=='sine':
                    response=json.loads((work/(ac[c['ix']]['id']+'.response.json')).read_text())
                    gain=np.interp(np.log(c['freq_Hz']),np.log(response['f']),response['mag']);c['amplitude_V']=float(4*DIV/gain)
                    c['id']=c['id'].replace('_a0_',f'_a{old.s4.number(c["amplitude_V"])}_');amps[c['id']]=c['amplitude_V']
        print('START',phase,test,len(batch),flush=True)
        def partial(rr,ee,recs):
            merged={k:list(x) for k,x in extras.items()}
            for k,x in ee.items():merged.setdefault(k,[]).extend(x)
            pm=dict(meta,seconds=previous_seconds+time.perf_counter()-start,successful=len(rows)+len(rr),simulations=sum(r.get('simulations',1) for r in records+recs))
            checkpoint_write(checkpoint,json.dumps(dict(rows=rows+rr,extras=merged,records=records+recs,meta=pm),ensure_ascii=False))
        rr,ee,recs=execute(batch,work,amps,on_progress=partial);rows+=rr;records+=recs
        for k,x in ee.items():extras.setdefault(k,[]).extend(x)
        meta=dict(returncode=int(len(rows)!=len(cs)),simulations=sum(r.get('simulations',1) for r in records),logical_cases=len(cs),successful=len(rows),seconds=previous_seconds+time.perf_counter()-start,workers=10,smoke=args.smoke,preflight=args.preflight,seed=SEED,protected_changed=[])
        checkpoint_write(checkpoint,json.dumps(dict(rows=rows,extras=extras,records=records,meta=meta),ensure_ascii=False))
    after=protected();changed=[k for k,v in before.items() if after.get(k)!=v];write(work/'s7b_protected_after.json',json.dumps(after))
    latest={r['id']:r for r in records}
    code=int(len(rows)!=len(cs) or bool(changed) or any(r['returncode'] or r['errors'] for r in latest.values()))
    meta.update(returncode=code,protected_changed=changed,protected_count=len(before),seconds=previous_seconds+time.perf_counter()-start)
    rows=save_results(rows,extras,records,meta,profile)
    checkpoint_write(checkpoint,json.dumps(dict(rows=rows,extras=extras,records=records,meta=meta),ensure_ascii=False))
    write(work/'s7b_registro.json',json.dumps(sorted(records,key=lambda r:r['id']),ensure_ascii=False,indent=2))
    if args.preflight:
        mc=[realization(n) for n in range(10)]
        distribution=[dict(mc=n,rail_plus_V=r['rp'],rail_minus_mag_V=r['rn'],VREF_V=r['vref'],trimmer_required_pF=r['required']*1e12,trimmer_used_pF=r['used']*1e12,trimmer_pass=r['trimmer_pass'],**r['offsets']) for n,r in enumerate(mc)]
        csv_write(work/'s7b_mc_10.csv',distribution,list(distribution[0]))
        csv_write(work/'s7b_mc_10_components.csv',[dict(x,id=f'mc{n}') for n,r in enumerate(mc) for x in r['records']],['id','mc','component','nominal_SI','tolerance','draw','factor','value_SI','seed'])
        print('PREFLIGHT',json.dumps(distribution),flush=True)
    print(json.dumps(meta,ensure_ascii=False),flush=True);return code

if __name__=='__main__':raise SystemExit(main())
