"""Small memory-mapped audit of LTspice raw, including aborted prefixes.
Never labels prefix energy as energy over the requested 10 seconds.
"""
from pathlib import Path
import re
import numpy as np
from scipy.integrate import cumulative_trapezoid

def audit_raw(path, stop, frequency=60, case=None):
    path=Path(path)
    if not path.exists(): return {}
    with path.open('rb') as f: header=f.read(16000)
    enc='utf-16-le' if b'\x00' in header[:80] else 'utf-8'
    mark='Binary:\n'.encode(enc); end=header.find(mark)
    if end<0: return {}
    text=header[:end].decode(enc,errors='replace')
    if 'Transient Analysis' not in text: return {'raw_plot':'not_transient'}
    nv=int(re.search(r'No. Variables:\s*(\d+)',text)[1])
    np_decl=int(re.search(r'No. Points:\s*(\d+)',text)[1])
    names=[m[1].lower() for m in re.findall(r'^\s*(\d+)\s+(\S+)\s+\S+',text,re.M)]
    offset=end+len(mark)
    if 'double' in text:
        count=min(np_decl,(path.stat().st_size-offset)//(nv*8))
        data=np.memmap(path,dtype='<f8',mode='r',offset=offset,shape=(count,nv))
        get=lambda name: data[:,names.index(name.lower())]
    else:
        dtype=np.dtype([('time','<f8'),('v','<f4',(nv-1,))])
        count=min(np_decl,(path.stat().st_size-offset)//dtype.itemsize)
        data=np.memmap(path,dtype=dtype,mode='r',offset=offset,shape=(count,))
        get=lambda name: data['time'] if names.index(name.lower())==0 else data['v'][:,names.index(name.lower())-1]
    if count<2: return {}
    t=np.abs(np.asarray(get('time')))
    last=float(t[-1]); r=dict(observed_stop_s=last,raw_points=count,
        raw_complete=last>=stop-max(1e-9,stop*1e-7),
        raw_endpoint_exact=abs(last-stop)<=max(1e-9,stop*1e-7),
        requested_stop_s=stop,raw_overrun_s=max(last-stop,0),
        observed_maxstep_s=float(np.max(np.diff(t))))
    for n in ('vin','ain','x0','x1','x2','x5','n1','n2','rp','rn','shunt','theta'):
        if f'v({n})' in names:
            v=get(f'v({n})'); r[f'observed_{n}_max']=float(np.max(v)); r[f'observed_{n}_min']=float(np.min(v))
    span=get('v(rp)')-get('v(rn)'); r['observed_span_max']=float(np.max(span))
    if 'v(ms)' in names: r['observed_pass_vds']=float(np.max(np.abs(get('v(n2)')-get('v(ms)'))))
    theta=get('v(theta)'); ix=np.flatnonzero(theta>=1)
    if len(ix):
        i=int(ix[0]); r['observed_trip_s']=float(t[i] if i==0 else t[i-1]+(1-theta[i-1])/(theta[i]-theta[i-1])*(t[i]-t[i-1]))
    r['theta_final']=float(theta[-1])
    if case:
        r['ptc_resistance_final_ohm']=case['rcold']*np.exp(np.log(1e6/case['rcold'])*np.clip((theta[-1]-1)/.4,0,1))
    parts={'rprot1':('vin','p1'),'rprot2':('p1','p2'),'rprot3':('p2','x0'),
           'rdiv1':('vin','d1'),'rdiv2':('d1','d2'),'rdiv3':('d2','x1'),
           'rdiv4':('x1','x2'),'rdiv5':('x2','0'),'rc1':('vin','c1'),
           'rc2':('d1','c2'),'rc3':('d2','c3'),'rs':('n1','n2'),
           'rwarn':('ain','x5'),'rshunt':('shunt','0'),'ptc':('pt','n1')}
    powers={}
    for part,(a,b) in parts.items():
        cur='i(vptc)' if part=='ptc' else f'i({part})'
        if cur in names:
            voltage=get(f'v({a})')-(0 if b=='0' else get(f'v({b})'))
            powers[part]=voltage*get(cur)
            r[f'observed_{part}_v']=float(np.max(np.abs(voltage)))
    if 'i(btvs)' in names: powers['tvs']=get('v(n1)')*get('i(btvs)')
    for n,node in (('0','x0'),('1','x1'),('2','n2'),('5','x5')):
        powers['bav'+n]=np.maximum((get(f'v({node})')-get('v(rp)'))*get(f'i(d{n}p)'),0)+np.maximum((get('v(rn)')-get(f'v({node})'))*get(f'i(d{n}n)'),0)
    # Integrate exact real time. An aborted prefix is never extrapolated.
    long=case and case['p'] in ('P2','P3','P4','P5') and stop>=1
    a=last-5/frequency; mid=last-3/frequency
    periodic_errors=[]
    for part,power in powers.items():
        integral=cumulative_trapezoid(power,t,initial=0)
        r[f'{part}_energy_simulated_J']=float(integral[-1])
        r[f'observed_{part}_peak_W']=float(np.max(power))
        if long and a>=0 and r['raw_complete']:
            e0=float(np.interp(a,t,integral)); em=float(np.interp(mid,t,integral))
            avg=float((integral[-1]-e0)/(last-a))
            pfirst=(em-e0)/(mid-a); plast=(integral[-1]-em)/(last-mid)
            variation=abs(plast-pfirst)/max(abs(avg),1e-12)
            periodic_errors.append(variation)
            r[f'{part}_periodic_W']=avg
            r[f'{part}_energy_extrapolated_J']=avg*(10-last)
            r[f'{part}_energy_total_estimate_J']=float(integral[-1])+avg*(10-last)
    if long:
        r['energy_simulated_duration_s']=last
        r['energy_extrapolated_duration_s']=10-last
        r['periodic_power_relative_change_max']=max(periodic_errors,default=float('inf'))
        rail_drift=max(abs(float(np.interp(a,t,get('v('+n+')')))-float(get('v('+n+')')[-1])) for n in ('rp','rn')) if a>=0 else float('inf')
        r['periodic_rail_drift_V']=rail_drift
        ptc_ok=not case['relay'] or case['opening']<100 or r.get('ptc_resistance_final_ohm',0)>=.99e6
        r['extrapolation_valid']=bool(r['raw_complete'] and max(periodic_errors,default=1)<.05 and rail_drift<.01 and ptc_ok)
        r['extrapolation_basis']='last_5_cycles; hot_PTC_required_if_never_open; estimates_invalid_unless_extrapolation_valid'
    if case and case['p']=='P7' and r['raw_complete']:
        # Recovery relative to final post-removal steady value; 10 µV smallest V count.
        for node in ('x0','n2'):
            voltage=get(f'v({node})'); reference=float(voltage[-1])
            bad=np.flatnonzero((t>=case['remove']) & (np.abs(voltage-reference)>10e-6))
            r[node+'_recovery_s']=float(t[bad[-1]]-case['remove']) if len(bad) else 0.
        r['recovery_exposure_s']=case['remove']
    for n in ('Vptc','Vsense','D0p','D0n','D1p','D1n','D2p','D2n','Dbr1','Dbr2','Dbr3','Dbr4'):
        key=f'i({n.lower()})'
        if key in names:
            cur=get(key); r[f'observed_{n.lower()}_peak']=float(np.max(np.abs(cur)))
            if n.startswith('Dbr'):
                r[f'observed_{n.lower()}_i2t']=float(np.trapezoid(cur*cur,t))
                lim=t<=.0083
                if np.count_nonzero(lim)>1: r[f'observed_{n.lower()}_i2t_8p3ms']=float(np.trapezoid(cur[lim]*cur[lim],t[lim]))
    if 'i(btvs)' in names:
        power=get('v(n1)')*get('i(btvs)')
        energy=cumulative_trapezoid(power,t,initial=0)
        r.update(observed_tvs_e_J=float(energy[-1]),observed_tvs_peak_W=float(np.max(power)))
        half=1/(2*frequency)
        edges=np.arange(0,last+half/2,half); edges=edges[edges<=last]
        if len(edges)>1:
            halves=np.diff(np.interp(edges,t,energy))
            r['observed_tvs_semicycle_max_J']=float(np.max(halves))
    del data
    return r
