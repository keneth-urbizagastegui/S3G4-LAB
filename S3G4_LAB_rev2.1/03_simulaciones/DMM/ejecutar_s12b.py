"""S12b: isolated derivative of S12; originals read-only, local models only.
10 workers, 900s/case, signed resume, priority groups completed sequentially.
Protection retains S11.4 reduced exposure; buffers use TI transfer plus an
explicit rail +/-0.5V, 1ohm input clamp wrapper (unverified IV assumption).
"""
from pathlib import Path
import importlib.util
import sys

HERE=Path(__file__).resolve().parent
# Load S12 implementation into this module with only output/include names changed.
# This keeps its raw parser/calibration methodology without writing S12 artifacts.
_source=(HERE/'ejecutar_s12.py').read_text(encoding='utf-8')
_source=_source.replace("HERE/'S12'", "HERE/'S12b'").replace('dmm_bloque2.inc','dmm_bloque2b.inc').replace('s12_', 's12b_')
_source=_source.replace("if __name__=='__main__':raise SystemExit(main())", '')
_source=_source.replace("Path(__file__),HERE/", "Path(__file__),HERE/'ejecutar_s12.py',HERE/'ejecutar_s11_4.py',HERE/'gdt_seguimiento/gdt_seguimiento.py',HERE/")
exec(compile(_source,str(HERE/'ejecutar_s12.py'),'exec'),globals())

PRIORITY=('E3','E8','E2','E1','E6','E5','E4','E7','C2','C3','Q0')
_cases=cases; _deck=deck; _audit=audit; _ident=ident
spec=importlib.util.spec_from_file_location('s12b_gdt',HERE/'gdt_seguimiento/gdt_seguimiento.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)

def ident(c):
    # Full S11.4 physical state is encoded in every protection measurement name.
    b=c.get('base')
    d={k:v for k,v in c.items() if k!='base'}
    result=_ident(d)
    if b:result+='_'+protection.name(b)
    return result.lower().replace('.','d').replace('-','m').replace('+','p')

def cases(n=200):
    # The inherited sorter must see its original groups first.
    global PRIORITY
    priority=PRIORITY;PRIORITY=('E4','E1','E2','E3','E5','E6','E7','C2','C3','Q0')
    try:oldcases=_cases(n)
    finally:PRIORITY=priority
    out=[]
    for c in oldcases:
        if c['q']=='E3':
            # Every range at 0, +/-FS, +/-20, +/-50; FS error only meaningful
            # inside declared range; rail legality required for every voltage.
            for amp in sorted(set((0,c['amp'],-c['amp'],20,-20,50,-50))):
                out.append(dict(c,amp=amp,stop=.028,pretime=.020))
        elif c['q']=='E2':
            out.append(dict(c,leak=.85e-9*2**((c['temp']-23)/10),bleak=.85e-9*2**((c['temp']-23)/10),stop=.422,method='plateau'))
        elif c['q']=='E6':
            for tau in (1e-9,1e-7):
                out.append(dict(c,chain='gdtmov',tau=tau))
                out.append(dict(c,q='E8',chain='gdtmov',tau=tau))
        else:out.append(c)
    template=next(c for c in oldcases if c['q']=='E2')
    for amp in (-50,50):out.append(dict(template,q='E8',kind='stress50',amp=amp,sel=2,gain=1,leak=0,stop=.003))
    return sorted(out,key=lambda c:(priority.index(c['q']),0 if c['q']=='E3' and c['amp']==-20 and c['sel']==0 and c['gain']>1 and c.get('charge')==5e-12 else 1))

def deck(c):
    if c['kind']=='protection':return protection_deck(c)
    cc=dict(c)
    if cc['kind']=='stress50':cc['kind']='dc'
    text=_deck(cc)
    text=text.replace('solver=normal','solver=norm')
    if c['kind']=='stress50' or c['q']=='E2':
        if c['kind']=='stress50':
            stimulus=f'PWL(0 0 20u {c["amp"]} {c["stop"]} {c["amp"]})';step='100n'
        else:
            points=['0 0','1m 0']
            for j in range(21):
                value=-c['amp']+j*c['amp']/10
                points += [f'{.001+j*.020+20e-6:.10g} {value:.15g}',f'{.001+(j+1)*.020:.10g} {value:.15g}']
            stimulus='PWL('+' '.join(points)+')';step='5u'
        text=text.replace('Vin vin 0 0',f'Vin vin 0 {stimulus}')
        text=re.sub(r'^\.dc .*$',f'.tran 0 {c["stop"]} 0 {step}',text,flags=re.M)
        text=re.sub(r'^\.meas dc .*$',f'.meas tran {ident(c)}__last FIND V(out) AT={c["stop"]}',text,flags=re.M)
    if c['q']=='E3':
        # Establish extreme inputs by a physical ramp from a solvable zero OP.
        # Allow 20ms (>60 divider time constants) before saved autocero event.
        text=text.replace(f'Vin vin 0 {c["amp"]}',f'Vin vin 0 PWL(0 0 20u {c["amp"]} {c["stop"]} {c["amp"]})')
        text=text.replace(' 0.001002 ', ' 0.021002 ').replace(' 0.001 ', ' 0.021 ')
        text=text.replace(' 1m ', ' 21m ')
        # Keep the complete 0->+/-50V ramp too: legality is checked throughout,
        # while settling is evaluated only at the preconditioned mux event.
        # 1us ceiling yields >=100 samples in the shortest 0.1ms firmware wait;
        # LTspice still reduces its step at control edges/fast amplifier changes.
        text=text.replace(f'.tran 0 {c["stop"]} 0 100n',f'.tran 0 {c["stop"]} 0 1u')
        # A disconnected numerical timing probe imposes100ns breakpoints
        # around switching/charge injection, without changing circuit pieces.
        # Needed because coarse1us alone changed rail verdicts in saturated X0.
        grid=' '.join(f'{.0209+j*1e-7:.10g} {j%2}' for j in range(2001))
        text=text.replace('.end',f'Vtiming timing 0 PWL({grid})\n.end')
    # TI buffers always stay OPA2192, including comparison of A with OPA2188.
    text=text.replace('Xbuf0 bi0 bn0 vp vn bx0 OPAx188','Xbuf0 bi0 bn0 vp vn bx0 OPAx192').replace('Xbuf1 bi1 bn1 vp vn bx1 OPAx188','Xbuf1 bi1 bn1 vp vn bx1 OPAx192')
    if c['model']=='188':text=text.replace('.temp ',f'.include "{MODELS/"OPA2192/OPAx192.LIB"}"\n.temp ',1)
    text=text.replace('X0 ctl0 x0 mux','X0 ctl0 bx0 mux').replace('X1 ctl1 x1 mux','X1 ctl1 bx1 mux')
    text=text.replace('Rsel x0 mux','Rsel bx0 mux').replace('Rsel x1 mux','Rsel bx1 mux')
    text=text.replace('BLEAK=0',f'BLEAK={c.get("bleak",0):.15g}')
    text=text.replace('MLEAK=0',f'MLEAK={1e-9*2**((c["temp"]-23)/10) if c["q"]=="E2" else 0:.15g}')
    if c['q'] in ('E3','E8'):
        text=text.replace('.save V(out)', '.save V(bx0) V(bx1) V(x2) I(Vib0) I(Vib1) I(Vibn0) I(Vibn1) V(out)')
        if c['kind']=='stress50':
            text=text.replace('.end','.save V(bx0) V(bx1) V(x2) I(Vib0) I(Vib1) I(Vibn0) I(Vibn1)\n.end')
        name=ident(c)
        text=text.replace('.end',f'.meas tran {name}__buffer0_i MAX abs(I(Vib0))\n.end')
    return text

def protection_deck(c):
    text=_deck(c)
    # S12's update from 415uA to1mA/channel made the old 3mA residual
    # negative (3mA-2mA-1.1mA-16uA). Remove that unphysical load only
    # here; physical IC loads sum3.116mA, plus2mA for the new buffers.
    text=re.sub(r'^Riqother .*\n','* No negative residual load; IC budget5.116mA at9.8V.\n',text,flags=re.M)
    # Both actual inputs after the existing 100ohm resistors. Remove HC clamps
    # from those nodes and put them on buffer outputs. Keep other reduced loads.
    text=text.replace('Xh0 hx0 rp rn','Xh0 bx0 rp rn').replace('Xh1 hx1 rp rn','Xh1 bx1 rp rn')
    text=text.replace('Rselected hx0 mux','Rselected bx0 mux').replace('Rselected hx1 mux','Rselected bx1 mux')
    text=re.sub(r'^(?:Cgdt|Cgstate|Rgstate|Bgthreshold|Bgstate|Bgdt|\.param GDC)[^\n]*\n','',text,flags=re.M)
    block='\n'.join(study.gdt_block('mov',c['base']['gdc'],c['tau']))+'\n'
    # TI transfer voltages isolated from rails to preserve physical reduced rail
    # accounting; explicit PINOPA supplies common/differential capacitance.
    block+=f'.include "{MODELS/"OPA2192/OPAx192.LIB"}"\n'
    block+='Ebp bvp 0 rp 0 1\nEbn bvn 0 rn 0 1\n'
    for i in (0,1):
        block+=f'Vib{i} hx{i} bi{i} 0\nXbpin{i} bi{i} rp rn PINOPA\nEbi{i} ti{i} 0 bi{i} 0 1\nVibn{i} bx{i} bni{i} 0\nXbuf{i} ti{i} bni{i} bvp bvn bx{i} OPAx192\nCbd{i} bi{i} bx{i} 1.6p\n'
    block+='Riqbuffers rp rn {9.8/.002}\n'
    text=text.replace('.temp 25',block+'.temp 25')
    # Limit save set: no giant internal TI traces, retain physical stress nodes.
    text=re.sub(r'^\.save .*\n','',text,flags=re.M)
    text=re.sub(r'^\.end\s*$',lambda m:'.save V(vin) V(mid1) V(d1) V(mid2) V(d2) V(mid3) V(x1) V(x2) V(c1) V(c2) V(c3) V(rp) V(rn) V(bi0) V(bi1) V(bx0) V(bx1) I(Vib0) I(Vib1) I(Vibn0) I(Vibn1)\n.end',text,flags=re.M)
    # Short physical-state hash keeps filenames below Windows MAX_PATH. Names of
    # .meas retain the complete state; the first comment retains JSON as well.
    return text

def run(c,resume=False):
    # The inherited run uses ident without base for the path; digest preserves all.
    return _run(c,resume)

def duration_above(t,y,limit):
    # Exact duration of piecewise-linear RAW interpolation above threshold.
    dt=np.diff(t);duration=0.
    for sign in (-1,1):
        a=sign*y[:-1]-limit;b=sign*y[1:]-limit
        fraction=np.where((a>0)&(b>0),1.,0.)
        m=(a>0)&(b<=0);fraction[m]=a[m]/(a[m]-b[m])
        m=(a<=0)&(b>0);fraction[m]=b[m]/(b[m]-a[m])
        duration+=float(np.sum(dt*fraction))
    return duration

def audit(c,path):
    if c['kind']=='protection':
        d=raw(path);t=np.abs(np.asarray(d['time']));v=lambda n:np.asarray(d['v('+n+')'])
        r={}
        pieces=[(f'r{i}{s}',a,b,1.5e6,200.) for i,x,y in ((1,'vin','d1'),(2,'d1','d2'),(3,'d2','x1')) for s,a,b in (('a',x,f'mid{i}'),('b',f'mid{i}',y))]
        pieces += [('r910k','x1','x2',910e3,200.),('r100k','x2','0',100e3,200.)]
        pieces += [(f'rc{i}',a,f'c{i}',3300.,None) for i,a in ((1,'vin'),(2,'d1'),(3,'d2'))]
        for part,a,b,res,rating in pieces:
            y=v(a)-(0 if b=='0' else v(b))
            r.update({part+'_peak_V':float(np.max(np.abs(y))),part+'_energy_J':float(np.trapezoid(y*y/res,t))})
            r[part+'_above_work_s']=duration_above(t,y,rating) if rating else None
            # Thresholds reported for unknown antipulse rating, without inventing it.
            if rating is None:
                for threshold in (200,400,1000):r[f'{part}_above_{threshold}V_s']=duration_above(t,y,threshold)
        for i,a,b,cap in ((1,'c1','d1',100e-12),(2,'c2','d2',100e-12),(3,'c3','x1',100e-12),(4,'x1','x2',330e-12),(5,'x2','0',3e-9)):
            y=v(a)-(0 if b=='0' else v(b));r[f'c{i}_peak_V']=float(np.max(np.abs(y)));r[f'c{i}_stored_peak_J']=float(np.max(.5*cap*y*y))
            r[f'c{i}_above_work_s']=duration_above(t,y,2000) if i<=3 else None
        for i in (0,1):
            r[f'buffer{i}_peak_A']=float(np.max(np.abs(d[f'i(vib{i})'])))
            r[f'buffer{i}_n_peak_A']=float(np.max(np.abs(d[f'i(vibn{i})'])))
        r['input_current_pass']=max(r[k] for k in r if k.endswith('_peak_A'))<=.005
        r['vin_peak_V']=float(np.max(np.abs(v('vin'))));return r
    cc=dict(c)
    if cc['kind']=='stress50':cc['kind']='dc'
    r={} if c['q'] in ('E3','E2') or c['kind']=='stress50' else _audit(cc,path)
    if c['q']=='E2':
        d=raw(path);t=np.abs(np.asarray(d['time']));x=[];y=[]
        for j in range(21):
            end=.001+(j+1)*.020;m=(t>=end-.002)&(t<=end)
            x.append(float(np.mean(d['v(vin)'][m])));y.append(float(np.mean(d['v(out)'][m])))
        slope,offset=np.polyfit(x,y,1)
        r.update(slope=float(slope),offset_V=float(offset),DC_method='21_plateaus_20ms_last2ms_mean',DC_fit_residual_V=float(np.max(np.abs(np.asarray(y)-slope*np.asarray(x)-offset))))
    if c['q'] in ('E3','E8'):
        d=raw(path)
        for node in ('bx0','bx1','x2'):r[node+'_peak_V']=float(np.max(np.abs(d['v('+node+')'])))
        r['all_channels_rail_pass']=max(r[n+'_peak_V'] for n in ('bx0','bx1','x2'))<=c['rail']
        for i in (0,1):
            for pin in ('','n'):r[f'buffer{i}_{pin or "p"}_peak_A']=float(np.max(np.abs(d[f'i(vib{pin}{i})'])))
        if c['q']=='E8':r['input_current_pass']=max(r[k] for k in r if k.endswith('_peak_A'))<=.005
        if c['q']=='E3':
            axis=np.abs(np.asarray(d['time']));nodes=('bx0','bx1','x2')
            # During X3/preconditioning all three signal routes are off.
            # From the close command at21.002ms, the requested Yn is selected.
            peaks=[float(np.max(np.abs(d['v('+node+')']))) for i,node in enumerate(nodes) if i!=c['sel']]
            before=axis<.021002
            peaks.append(float(np.max(np.abs(d['v('+nodes[c['sel']]+')'][before]))))
            r['unselected_channels_peak_V']=max(peaks)
            r['unselected_channels_rail_pass']=r['unselected_channels_peak_V']<=c['rail']
            fs=next(x for x in RANGES if x[1]==c['sel'] and x[2]==c['gain'])
            r['in_range']=abs(c['amp'])<=fs[0]
            if r['in_range']:
                t=np.abs(np.asarray(d['time']))-c.get('pretime',0);div=(1,1.01/10.01,.1/10.01)[c['sel']];lsb=fs[3]*div*c['gain'];wait={0:.0001,1:.003,2:.0015}[c['sel']]
                at=float(np.interp(.001+wait,t,d['v(out)']));r['error_at_wait_counts']=(at-c['amp']*div*c['gain'])/lsb
                r['one_count_pass']=abs(r['error_at_wait_counts'])<=1
                expected=c['amp']*div*c['gain'];tail=float(np.mean(d['v(out)'][t>.0078]));r['final_error_counts']=(tail-expected)/lsb
                r['settle_s']=settle(t,d['v(out)'],.001,expected,lsb) if abs(tail-expected)<=lsb else None
    return r

# Obtain inherited run's code object; globals resolve to S12b functions above.
_run_source=_source[_source.index('def run('):_source.index('\ndef dc_budget(')]
_run_source=_run_source.replace('def run(', 'def _run(')
exec(compile(_run_source,str(HERE/'ejecutar_s12b.py'),'exec'),globals())

def dc_budget():
    """Conditional engineering reserve; not production yield certification.
    Source leakage limit at buffer input, COM held .85nA, mux each Yn 1nA.
    Both buffer and A drift .5uV/C (SOIC), Ib20pA, typical TMUX .3nA.
    Buffer low-frequency output impedance bounded by 1ohm (assumption).
    """
    rng=np.random.default_rng(1202);tc=rng.uniform(-25e-6,25e-6,(10000,10));rs=np.array([1.5e6]*6+[910e3,100e3,91e3,10e3]);out=[]
    for fs,sel,g,lsb in RANGES:
        div=(1,1.01/10.01,.1/10.01)[sel];source_lsb=lsb*div
        resistance=(99100,9e6*1.01e6/10.01e6+100,100e3*9.91e6/10.01e6)[sel]
        mux_r=71 if sel<2 else resistance+70
        # X1 buffer remains connected even in X2: its input leakage changes
        # X2 through the divider, with89.91kohm transresistance.
        input_resistance=resistance if sel<2 else 9e6*100e3/10.01e6
        ib_resistance=resistance+mux_r if sel<2 else input_resistance+mux_r
        gains=[]
        for dt in (-5,5):
            rr=rs*(1+tc*dt);ratio=1 if sel==0 else (rr[:,6]+rr[:,7])/np.sum(rr[:,:8],axis=1) if sel==1 else rr[:,7]/np.sum(rr[:,:8],axis=1)
            gg=1 if g==1 else 1+rr[:,8]/rr[:,9]
            gains.append(np.abs(np.asarray(ratio/div*gg/g)-1)*1e6)
        drift=math.sqrt(2)-1
        # In X2 there is no buffer: combined mux1nA + COM.85nA across source.
        fixed=(2.5e-6*(2 if sel<2 else 1)+20e-12*ib_resistance*drift+(.3e-9*91000/g*drift if g>1 else 0)+(.85e-9+1e-9)*mux_r*drift)/source_lsb
        # Unbuffered Y2 also loads X1 when Y1 is selected: reciprocal
        # divider transresistance89.91kohm, with1nA off-channel leakage.
        if sel==1:fixed+=1e-9*(9e6*100e3/10.01e6)*drift/source_lsb
        per=1e-9*input_resistance*drift/source_lsb
        out.append(dict(range_V=fs,gain_p95_ppm=float(np.percentile(np.maximum(*gains),95)),offset_budget_counts=fixed+.85*per,buffer_leak_max_nA=max(0,(4-fixed)/per) if per else None,COM_leak_max_nA=max(0,(4-(fixed-(.85e-9+1e-9)*mux_r*drift/source_lsb+.85*per))/ (1e-9*mux_r*drift/source_lsb)-1),fixed_counts=fixed,population=10000,assumptions='double_per10C;SOIC_drift;Ib20pA;buffer_Rout1ohm;Yn1nA_COM0.85nA'))
    writecsv(RESULTS/'s12b_dc_budget.csv',out);return out

if __name__=='__main__':raise SystemExit(main())
