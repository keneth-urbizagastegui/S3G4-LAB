"""S5 prototype reconstruction and E96/E12 synthesis; no design selection."""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
import csv
import json
import subprocess
from pathlib import Path
import numpy as np
from scipy import signal, optimize

ROOT = Path(__file__).resolve().parent
E96 = np.array([100,102,105,107,110,113,115,118,121,124,127,130,133,137,140,143,
 147,150,154,158,162,165,169,174,178,182,187,191,196,200,205,210,215,221,
 226,232,237,243,249,255,261,267,274,280,287,294,301,309,316,324,332,340,
 348,357,365,374,383,392,402,412,422,432,442,453,464,475,487,499,511,523,
 536,549,562,576,590,604,619,634,649,665,681,698,715,732,750,768,787,806,
 825,845,866,887,909,931,953,976], dtype=float)
E12 = np.array([10,12,15,18,22,27,33,39,47,56,68,82],dtype=float)
RVALUES = np.concatenate([E96,E96*10])
RVALUES = RVALUES[(RVALUES>=499)&(RVALUES<=2490)]
CVALUES = np.concatenate([E12*10.**i for i in range(-1,4)])*1e-12
FIXED = np.array([1/(2*np.pi*68*470e-12),10.8e6])

def ordered(p):
    return sorted([complex(x) for x in p if x.imag>0],key=lambda x:abs(x)/(-2*x.real))

def response(p,f):
    w=2j*np.pi*np.asarray(f)
    h=np.ones(w.shape,dtype=complex)
    for x in p: h*=(-x)/(w-x)
    for x in FIXED:h*=1/(1+w/(2*np.pi*x))
    return h

def prototypes():
    be=signal.besselap(4,norm='mag')[1];bu=signal.buttap(4)[1]
    b=ordered(be);u=ordered(bu)
    tr=[]
    for a,z in zip(b,u):
        x=np.sqrt(abs(a)*abs(z))*np.exp(1j*(np.angle(a)+np.angle(z))/2)
        tr.extend([x,x.conjugate()])
    return {'BE':be,'TR':np.array(tr),'BU':bu}

def synthesize():
    components=[];ideal=[];poles={}
    for candidate,p in prototypes().items():
        scale=optimize.brentq(lambda x:20*np.log10(abs(response(p*x,[2e6])[0]))+3,1e6,1e8)
        p=p*scale;poles[candidate]=p
        den=np.poly(np.r_[p,-2*np.pi*FIXED]).real
        tf=signal.TransferFunction([den[-1]],den)
        t=np.linspace(0,3e-6,30001);t,y=signal.step(tf,T=t)
        t10=np.interp(.1,y[:np.argmax(y)+1],t[:np.argmax(y)+1])
        t90=np.interp(.9,y[:np.argmax(y)+1],t[:np.argmax(y)+1])
        row=dict(candidate=candidate,scale_rad_s=scale,minus3_Hz=2e6,
                 overshoot_pct=max(0,float(y.max()-1)*100),rise_ns=float((t90-t10)*1e9))
        for f in [3.25e6,4.5e6,6.5e6]:row['atten_'+str(f/1e6).replace('.','p')+'m_db']=-20*np.log10(abs(response(p,[f])[0]))
        ideal.append(row)
        for j,x in enumerate(ordered(p),1):
            f0=abs(x)/(2*np.pi);q=abs(x)/(-2*x.real);options=[]
            # E12 C2 in 47..220pF. For each C2 round C1 first, then R.
            # Minimize Q error, then f0 error, then favor larger C2.
            for c2 in CVALUES[(CVALUES>=47e-12*(1-1e-10))&(CVALUES<=220e-12*(1+1e-10))]:
                c1=CVALUES[np.argmin(abs(CVALUES-4*q*q*c2))]
                ri=1/(2*np.pi*f0*np.sqrt(c1*c2))
                if not 499<=ri<=2490:continue
                r=RVALUES[np.argmin(abs(RVALUES-ri))]
                qr=.5*np.sqrt(c1/c2);fr=1/(2*np.pi*r*np.sqrt(c1*c2))
                options.append((abs(qr/q-1),abs(fr/f0-1),-c2,r,c1,c2,fr,qr))
            if not options:raise ValueError('No E96/E12 synthesis in allowed range')
            _,_,_,r,c1,c2,fr,qr=min(options)
            components.append(dict(candidate=candidate,section=j,R1_Ohm=float(r),R2_Ohm=float(r),
                C1_pF=float(c1*1e12),C2_pF=float(c2*1e12),target_f0_Hz=f0,target_Q=q,
                real_f0_Hz=float(fr),real_Q=float(qr),f0_error_pct=float(100*(fr/f0-1)),Q_error_pct=float(100*(qr/q-1))))
    return components,ideal

def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    fields=list(rows[0]) if rows else []
    with path.open('w',encoding='utf-8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def main():
    c,i=synthesize();write_csv(ROOT/'resultados/s5_componentes.csv',c)
    write_csv(ROOT/'resultados/s5_ideal.csv',i)
    print(json.dumps(dict(ideal=i,components=c),indent=2),flush=True)
    # The synthesis deliverable also checks each section in native LTspice;
    # the runner creates six isolated decks with ten workers from the start.
    return subprocess.run([sys.executable,str(ROOT/'ejecutar_s5.py'),'--controls'],cwd=ROOT).returncode

if __name__=='__main__':raise SystemExit(main())
