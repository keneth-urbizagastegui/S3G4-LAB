"""S6 coherent sample analysis; no quantization, no FFT window."""
from __future__ import annotations
import numpy as np

FCLK=52e6
FS=FCLK/8
TS=3.5/FCLK
PERIOD=16/FCLK
SHIFT=8/FCLK
START=1e-6
N=1024
FIRST=256
LSB=2.5/4096

def coherent(target):
    odds=np.arange(1,N//2,2)
    m=int(odds[np.argmin(abs(odds*FS/N-target))])
    return m,m*FS/N

def rms(x):return float(np.sqrt(np.mean(np.square(x))))

def spectrum(y,m):
    a=2*abs(np.fft.rfft(y-y.mean()))/len(y)
    fund=a[m]
    eligible=a.copy();eligible[0]=eligible[m]=0
    k=int(np.argmax(eligible))
    # Harmonics 2..9 folded into Nyquist, unique bins.
    harmonics=sorted({min((j*m)%N,N-(j*m)%N) for j in range(2,10)}-{0,m})
    spur=N//2-m
    return dict(sfdr_db=float(20*np.log10(fund/max(eligible[k],1e-300))),
                sfdr_bin=k,thd_pct=float(100*np.linalg.norm(a[harmonics])/fund),
                interleave_dbc=float(20*np.log10(max(a[spur],1e-300)/fund)),
                interleave_bin=spur,fundamental_pp_V=float(2*fund),mean_V=float(y.mean())),a

def samples(raw,count=N,first=FIRST):
    indices=np.arange(first-2,first+count)
    times=START+TS+indices/FS
    t=raw['time']
    if t[-1]<times[-1]:raise ValueError('Incomplete transient')
    # Evaluate the LEFT limit at the falling switch threshold. A Z/R reset
    # has a 5fs time constant; interpolating across that discontinuity mixes
    # track and reset values and is not an ADC sample.
    ref=np.interp(times,t,raw['v(reference)'])
    y=[];apertures=[]
    for n,when in zip(indices,times):
        adc=int(n%2+1);clk=raw[f'v(clk{adc})'];cs=raw[f'v(cs{adc})']
        j=int(np.searchsorted(t,when))
        while clk[j-1]<.5:j-=1
        while clk[j]>=.5:j+=1
        left=j-1
        if clk[left-1]<.5:raise ValueError('No two tracking points at aperture')
        value=cs[left]+(when-t[left])*(cs[left]-cs[left-1])/(t[left]-t[left-1])
        closing=t[left]+(.5-clk[left])*(t[j]-t[left])/(clk[j]-clk[left])
        if abs(closing-when)>1e-12:raise ValueError('Aperture clock mismatch')
        y.append(float(value));apertures.append(dict(track_left_time_s=float(t[left]),track_left_clock_V=float(clk[left]),
            closing_clock_time_s=float(closing),closing_time_error_ps=float((closing-when)*1e12)))
    return indices,times,np.array(y),ref,apertures

def analyze(raw,c):
    count=64 if c['test']=='H1' else N
    indices,times,y,ref,apertures=samples(raw,count)
    output=[]
    for adc in [1,2]:
        mask=np.arange(2,len(y))[(indices[2:]%2)==adc-1]
        e=y[mask]-ref[mask]
        r=dict(c,adc=adc,samples=len(mask),reference_mean_V=float(ref[mask].mean()),
               error_max_mV=float(abs(e).max()*1e3),error_rms_mV=rms(e)*1e3,
               error_max_LSB=float(abs(e).max()/LSB),error_rms_LSB=rms(e)/LSB,
               error_mean_mV=float(e.mean()*1e3))
        if c['test']!='H1':
            matrix=np.column_stack([ref[mask],ref[mask-2],np.ones(len(mask))])
            a,b,dc=np.linalg.lstsq(matrix,e,rcond=None)[0]
            residual=e-matrix@np.array([a,b,dc])
            h=1+a+b*np.exp(-2j*np.pi*c['freq_Hz']*2/FS)
            r.update(a=float(a),b=float(b),c_V=float(dc),residual_rms_mV=rms(residual)*1e3,
                     residual_max_mV=float(abs(residual).max()*1e3),residual_rms_LSB=rms(residual)/LSB,
                     residual_max_LSB=float(abs(residual).max()/LSB),gain_delta_db=float(20*np.log10(abs(h))),
                     phase_delta_deg=float(np.angle(h,deg=True)))
        # Consecutive equal-size blocks reveal unsettled drift.
        r['block_rms_delta_mV']=abs(rms(e[:len(e)//2])-rms(e[len(e)//2:]))*1e3
        output.append(r)
    sample_rows=[dict(id=c['id'],n=int(n),adc=int(n%2+1),time_s=float(t),sample_V=float(v),reference_V=float(vr),error_V=float(v-vr))
                 |ap for n,t,v,vr,ap in zip(indices[2:]-indices[2],times[2:],y[2:],ref[2:],apertures[2:])]
    fft_rows=[];bins=[]
    if c['test']!='H1':
        for name,seq in [('loaded',y[2:]),('reference',ref[2:])]:
            r,amp=spectrum(seq,c['M']);fft_rows.append(dict(c,sequence=name,**r))
            bins += [dict(id=c['id'],sequence=name,bin=k,freq_Hz=float(k*FS/N),amplitude_V=float(v)) for k,v in enumerate(amp)]
    return output,sample_rows,fft_rows,bins

def loop_metrics(raw):
    f=raw['frequency'];t=-raw['v(ret)']/raw['v(inj)']
    db=20*np.log10(abs(t));phase=np.unwrap(np.angle(t))*180/np.pi
    # Negative-feedback return ratio starts positive. Keep branch near 0 degrees.
    phase-=360*round(phase[0]/360)
    idx=np.flatnonzero((db[:-1]>=0)&(db[1:]<0))
    out=[]
    for i in idx:
        z=-db[i]/(db[i+1]-db[i]);fc=float(np.exp(np.log(f[i])+z*np.log(f[i+1]/f[i])))
        ph=float(phase[i]+z*(phase[i+1]-phase[i]))
        out.append(dict(crossover_Hz=fc,phase_margin_deg=180+ph))
    if not out:raise ValueError('No unity-loop crossing')
    return out,t
