"""S13 confirmation. Previous scripts/includes are imported read-only.
10 workers, timeout 900 s, deterministic cases, signature-checked resume.
SWI1 plus added resistance spans Ron approximately; actual Ron is reported.
"""
from __future__ import annotations
import argparse, concurrent.futures as cf, hashlib, itertools, json, math, os, re, subprocess, sys, time
from pathlib import Path
import numpy as np
import ejecutar_s11_4 as s4
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/'estudio_bloque3/scripts'))
import rawlt
JOBS=HERE/'S13'; RESULTS=HERE/'resultados'; MODELS=s4.MODELS; LT=s4.LT
RK=[499,4990,49900,420000,1700000]; FS=[2000,20000,200000,2000000,20000000]
SET=2.5*4990/24900
INC=HERE/'comun/dmm_bloque3.inc'
def state(c):
 desc='s13_'+c['q']+'_'+c['kind']+'_'+'_'.join(f'{k}{v:.5g}' if isinstance(v,float) else f'{k}{v}' for k,v in sorted(c.items()) if k not in ('q','kind','base','seq'))
 if 'base' in c:desc+='_'+s4.name(c['base'])
 return re.sub(r'[^a-zA-Z0-9_]','d',desc)
def filename(c):return f"s13_{c['q']}_{c['kind']}_{c['seq']:04d}"
def cases():
 out=[]
 def add(q,kind,**kw):
  c=dict(q=q,kind=kind,k=0,rail=4.9,vto=-2.,ron=95.,cs=1.,ctvs=600e-12,rx=2000.,rref=1.,rset=1.,vosa=0.,vosb=0.,temp=23,enable=1,lf=0.,lb=0.,seq=len(out)); c.update(kw);out.append(c)
 rng=np.random.default_rng(1308)
 for i in range(100):
  add('C2','compliance',rail=float(rng.uniform(4.8,5)),vto=float(rng.uniform(-2,-.8)),ron=float(rng.uniform(60,130)),cs=float(rng.uniform(.5,1.5)),rref=float(rng.uniform(.999,1.001)),rset=float(rng.uniform(.999,1.001)),vosa=float(rng.uniform(-.0045,.0045)),vosb=float(rng.uniform(-.0045,.0045)))
 for k in range(5):
  for vt,ron,cs,rail in itertools.product((-.8,-2.),(60,130),(.5,1.5),(4.8,5.)):
   add('C2','phase',k=k,rx=FS[k],vto=vt,ron=ron,cs=cs,rail=rail)
  for cap in (300e-12,600e-12,900e-12):add('C2','startup',k=k,rx=FS[k],ctvs=cap)
  for temp in (18,23,28):add('C2','thermal',k=k,rx=FS[k],temp=temp)
 for b in s4.cases():
  if b['q']=='T2': add('C1','esd',base=b,enable=int(b['source']>0),rail=4.9*b['rail'],temp=b['temp'])
  elif b['q']=='T4':
   for source in (0,.001):add('C1','fault60',base=dict(b,source=source),enable=int(source>0),rail=4.9*b['rail'],temp=b['temp'])
 for cap,short in itertools.product((300e-12,600e-12,900e-12),(20,40)):
  add('C3','continuity',ctvs=cap,rx=1e12,short=short)
 for k,lf,lb,temp in itertools.product((3,4),(.1e-9,1e-9,10e-9),(.1e-9,1e-9,10e-9),(18,23,28)):
  factor=2**((temp-23)/10);add('C5','leak',k=k,rx=FS[k],lf=lf*factor,lb=lb*factor,lf23=lf,lb23=lb,temp=temp)
 for voltage in (-60,-5,-.02,.02,5,60):
  for gain in (1,10.1):add('C6','external',enable=0,voltage=voltage,gain=gain)
 for voltage,k in ((.65,0),(3.,1),(3.2,1),(3.6,1)):
  add('C7','diode',voltage=voltage,k=k,rail=4.8)
 return sorted(out,key=lambda c:['C2','C1','C3','C5','C6','C7'].index(c['q']))
def p43(c,ac=0):
 return (f'.include "{MODELS / "TLV2372/TLV2372.LIB"}"\n.include "{MODELS / "74HC4051/hc_tnomi.cir"}"\n'+
 f'.param RK={RK[c["k"]]} VTO={c["vto"]} RON={c["ron"]} CSCALE={c["cs"]} RREF={c["rref"]} RSET={c["rset"]} VOSA={c["vosa"]} VOSB={c["vosb"]} ENABLE={c["enable"]} LF={c["lf"]} LB={c["lb"]} ACINJ={ac}\n'+
 f'.include "{INC}"\n'+''.join(f'Rku{i} rp su{i} {rk}\nXfu{i} boff su{i} ff rn rp 0 SWI1\nXse{i} boff su{i} ss rn rp 0 SWI1\n' for i,rk in enumerate(RK) if i!=c['k'])+''.join(f'Xspforce{i} boff 0 ff rn rp 0 SWI1\nXspsense{i} boff 0 ss rn rp 0 SWI1\n' for i in range(3)))
def reading(gain):
 return f''' .include "{MODELS / 'OPA2192/OPAx192.LIB'}"
Rp bor x0p 99k
Cp0 x0p 0 3p
D0p x0p rp BAV199
D0n rn x0p BAV199
Rx0 x0p bi0 10k
Cin bi0 0 9p
Xbuf bi0 bx0 rp rn bx0 OPAx192
Rmux bx0 mux 70
Czm mux 0 28p
Rfg out inv {(gain-1)*10000 if gain>1 else .001}
Rgg inv 0 10k
Xamp mux inv rp rn out OPAx192
Rd1 out pb14 10k
Rd2 pb14 0 10k
Cpb pb14 0 5p
Dpb 0 pb14 BAT54
* X2 buffered route of S12d: 100k / 10.01Meg, A selected separately.
Rtop2 bor x2 9.91Meg
Rbot2 x2 0 100k
Rx2 x2 bi2 10k
Ci2 bi2 0 9p
Xbuf2 bi2 bx2 rp rn bx2 OPAx192
Xax2 bx2 inv2 rp rn out2 OPAx192
Rf2 out2 inv2 {(gain-1)*10000 if gain>1 else .001}
Rg2 inv2 0 10k
'''.lstrip()
def deck(c):
 prefix=state(c)
 if c['q']=='C1':
  b=c['base'];t=s4.deck(b).replace('RON=700','OLD_RON=700')
  # S11.4 reduced exposure model retained for fast ESD. Full P43 is C2.
  t=t.replace('Rohm1 ptin ohmid 1.1k\nRohm2 ohmid n1 1.1k','Rohm1 ptin ohmida 510\nRohm2 ohmida ohmidb 510\nRohm3 ohmidb n1 510')
  t=t.replace('Dblk bp n2 BAT54','Dblk bp n1 BAT54')
  # bor is just an alias for terminal; leakage disabled in C1.
  t='\n'.join(l for l in t.splitlines() if not l.startswith('.meas '))
  t=re.sub(r'(?m)^\.end\s*$',lambda m:f'.meas tran {prefix}__span MAX V(rp,rn)\n.meas tran {prefix}__bat_reverse MAX V(n1,bp)\n.meas tran {prefix}__bss_vds MAX abs(V(bp,msource))\n.end',t)
  # inherited names described obsolete source: relabel every measurement.
  t=re.sub(r'(\.meas\s+tran\s+)\S+?__',lambda m:m[1]+prefix+'__',t)
  return t+'\n'
 bat=next(l for l in s4.old.read_text(s4.STANDARD).splitlines() if re.match(r'^\.model BAT54\s',l,re.I))
 t=f'* {prefix}\n* STATE {json.dumps(c,sort_keys=True)}\n'+bat+'\n'+p43(c,int(c['kind']=='phase'))
 if c['kind']=='external':
  # P34 assumes the commanded OFF state. TI macro does not converge under
  # all disabled conditions; retain pass/body/block device exposure explicitly.
  mos=next(l for l in (HERE/'comun/dmm_bloque1_final.inc').read_text().splitlines() if l.startswith('.model BSS84 '))
  t=f'* {prefix}\n* P34 commanded OFF; gate tied to source rail (ideal control).\n'+bat+'\n'+mos+'\nRk rp f 594\nMoff bp rp f f BSS84\nDbblock bp n1 BAT54\n'
 t+=f'Vp rp 0 {c["rail"]}\nVn rn 0 -{c["rail"]}\n.temp {c["temp"]}\n'
 t+='\n.model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)\n'
 t+=f'Rohm1 n1 ohmida 510\nRohm2 ohmida ohmidb 510\nRohm3 ohmidb bor 510\nCtvs n1 0 {c["ctvs"]}\nBtvs n1 0 I=sgn(V(n1))*max(abs(V(n1))-14.7,0)/.258719339\nCbor bor 0 25p\nRdiv bor 0 10.01Meg\nRs n1 n2 2700\nD2p n2 rp BAV199\nD2n rn n2 BAV199\n'
 if c['kind']=='compliance':t+='Vdut bor 0 0\n.dc Vdut 0 4.5 .01\n'
 elif c['kind'] in ('external','diode'):
  t+=f'Vdut bor 0 {c["voltage"]}\n'+reading(c.get('gain',10.1))+'\n.op\n'
  t=t.replace('Rdiv bor 0 10.01Meg','* Rdiv represented by physical X2 divider')
 else:
  t+=f'Rx bor 0 {c["rx"]}\n'
  if c['kind']=='phase':t+='.ac dec 60 10 200Meg\n'
  elif c['kind']=='continuity':
   t+=reading(10.1)+f'Vctl ctl 0 PULSE(0 1 20u 10n 10n 150u 1)\nSshort bor 0 ctl 0 SHORT\n.model SHORT SW(Ron={c["short"]} Roff=1T Vt=.5)\n'
   t+='Bcmpin cmpin 0 V={.2525-V(pb14)}\nScomp comp 0 cmpin 0 COMP\n.model COMP SW(Ron=1 Roff=1G Vt=0 Vh=.0045)\nRcomp rp comp 10k\n.tran 0 320u 0 .2u\n'
  elif c['kind']=='startup':
   # Zero initial terminal voltage, established rails: electrical settling,
   # not a cold power-on or unverified firmware INH sequence.
   t+='.ic V(bor)=0\n'
   t+=f'.tran 0 {[.001,.001,.005,.04,.12][c["k"]]} 0 {[.1e-6,.2e-6,1e-6,5e-6,10e-6][c["k"]]}\n'
  else:t+='.op\n'
 t+='.options plotwinsize=0 numdgt=15 reltol=.003 abstol=1p solver=alt method=gear threads=1\n.save V(*) I(*)\n'
 if c['enable']:t+='.nodeset V(e1)=2.5 V(cn)=4.4 V(o1)=3.8 V(b1)=3.8 V(s)=4.4 V(f)=4.3 V(sn)=4.4 V(ogi)=1 V(og)=1 V(gate)=1\n'
 else:t+=f'.nodeset V(e1)=0 V(cn)={c["rail"]} V(o1)=0 V(b1)=0 V(s)={c["rail"]} V(f)={c["rail"]} V(sn)={c["rail"]} V(ogi)={c["rail"]} V(og)={c["rail"]} V(gate)={c["rail"]}\n'
 if c['kind'] in ('startup','continuity'):t+=f'.meas tran {prefix}__borne_final FIND V(bor) AT '+str(.00032 if c['kind']=='continuity' else [.001,.001,.005,.04,.12][c['k']])+'\n'
 return t+'.end\n'
def audit(path,c):
 _,d=rawlt.read(str(path));d={k.lower():v for k,v in d.items()}
 def v(x):return np.real(d['v('+x+')'])
 r={}
 if c['q']=='C1':
  # Keep inherited S11 audit with transformed chain, plus new source stresses.
  b=c['base'];r=s4.audit(path,b)
  t=np.abs(d['time']);
  for i,a,z in ((1,'ptin','ohmida'),(2,'ohmida','ohmidb'),(3,'ohmidb','n1')):
   vv=v(a)-v(z);pw=vv*vv/510;r[f'r1_{i}_vpeak_V']=float(np.max(np.abs(vv)));r[f'r1_{i}_Pavg_W']=float(np.trapezoid(pw,t)/(t[-1]-t[0]));r[f'r1_{i}_E_J']=float(np.trapezoid(pw,t));r[f'r1_{i}_Ipeak_A']=float(np.max(np.abs(vv/510)))
  r['bat_reverse_V']=float(np.max(v('n1')-v('bp')));r['bss_vds_V']=float(np.max(np.abs(v('bp')-v('msource'))));return r
 current=v('bor')/c['rx']+v('bor')/10.01e6 if c['kind'] not in ('compliance','diode','external') else None
 r.update(borne_final_V=float(v('bor')[-1]))
 if c['kind']!='external':r.update(vset_V=float((v('rp')-v('cn'))[-1]),force_ron_ohm=float((v('s')[-1]-v('f')[-1])/(float(np.real(d['i(rk)'][-1])) or 1e-30)))
 if current is not None:r['current_A']=float(current[-1]);r['initial_error_pct']=float((current[-1]/(SET/RK[c['k']])-1)*100)
 if c['kind']=='compliance':
  ii=np.real(d['i(vdut)'])+v('bor')/10.01e6
  ok=ii>=.99*SET/RK[0];r['compliance_V']=float(np.max(v('bor')[ok])) if np.any(ok) else 0.;r['margin_V']=r['compliance_V']-(SET/RK[0])*(2000*10.01e6/(2000+10.01e6));r['pass_margin']=r['margin_V']>=.3;r['initial_error_pct']=float((ii[0]/(SET/RK[0])-1)*100)
 elif c['kind']=='phase':
  loop=-d['v(ogi)']/d['v(og)'];mag=np.abs(loop);ph=np.degrees(np.unwrap(np.angle(loop)));ix=np.flatnonzero(mag<1)
  if not len(ix) or ix[0]==0:r.update(pm_deg=None,fc_Hz=None)
  else:
   k=ix[0];a=-np.log10(mag[k-1])/(np.log10(mag[k])-np.log10(mag[k-1]));r['pm_deg']=float(180+ph[k-1]+a*(ph[k]-ph[k-1]));r['fc_Hz']=float(10**(np.log10(np.real(d['frequency'][k-1]))+a*np.log10(np.real(d['frequency'][k]/d['frequency'][k-1]))))
 elif c['kind']=='startup':
  t=np.abs(d['time']);ix=np.flatnonzero(np.abs(v('bor')/v('bor')[-1]-1)>.001);r['settle_s']=float(t[ix[-1]]) if len(ix) else 0.;r['limit_s']=1.5*[.031e-3,.13e-3,1.1e-3,9.4e-3,39e-3][c['k']]
 elif c['kind']=='continuity':
  t=np.abs(d['time']);pb=v('pb14');cmp=v('comp');
  for label,ts,condition in [('close',20e-6,pb<.2525-.0045),('open',170e-6,pb>.2525+.0045)]:
   ix=np.flatnonzero((t>=ts)&condition);r[label+'_s']=float(t[ix[0]]-ts) if len(ix) else None
  mask=(t>20e-6)&(t<320e-6);r['transitions']=int(np.count_nonzero(np.diff(cmp[mask]>.5*c['rail'])));r['pb_min_V']=float(pb.min());r['pb_max_V']=float(pb.max())
 elif c['kind'] in ('external','diode'):
  r.update(x0_out_V=float(v('out')[-1]),x2_out_V=float(v('out2')[-1]),dut_A=float(np.real(d['i(vdut)'][-1])))
 return r
def run(c,args):
 nm=filename(c);p=JOBS/(nm+'.cir');cache=p.with_suffix('.json');txt=deck(c)
 signature=hashlib.sha256((txt+Path(__file__).read_text()+INC.read_text()+s4.DEPENDENCY_SIGNATURE).encode()).hexdigest()
 if args.resume and cache.exists():
  r=json.loads(cache.read_text());
  if r.get('signature')==signature and r.get('status')=='ok':return dict(r,reused=True)
 p.write_text(txt,encoding='utf-8');start=time.perf_counter();r=dict(c,id=nm,signature=signature,reused=False)
 r.pop('base',None)
 try:
  if p.with_suffix('.raw').exists():p.with_suffix('.raw').unlink()
  proc=subprocess.run([str(LT),'-b',str(p)],capture_output=True,timeout=900)
  if proc.returncode!=0:raise RuntimeError(f'LTspice exit {proc.returncode}; see {p.with_suffix(".log")}')
  r.update(audit(p.with_suffix('.raw'),c));r['status']='ok';r['returncode']=proc.returncode
  if c['kind'] in ('startup','continuity'):
   _,d=rawlt.read(str(p.with_suffix('.raw')));stop=.00032 if c['kind']=='continuity' else [.001,.001,.005,.04,.12][c['k']]
   if abs(d['time'][-1])<stop*(1-1e-6):raise RuntimeError('Incomplete transient')
  if c['q']=='C1' and not r.get('raw_complete'):raise RuntimeError('Incomplete C1 transient')
 except Exception as e:r.update(status='error',error=str(e))
 r['elapsed_s']=time.perf_counter()-start;cache.write_text(json.dumps(r,indent=2),encoding='utf-8');return r
def analytical():
 rows=[]
 for fs,k,gain,pct in [(200,0,10.1,.002),(2000,0,1,.002),(20000,1,1,.002),(200000,2,1,.002),(2000000,3,1,.002),(20000000,4,1,.01)]:
  for lsb,level,counts,limit in [(2.1,'typical',40,1),(3.2,'guaranteed',40,1),(None,'calibrated_proxy',10,.85)]:
   x=np.linspace(.1*fs,fs,1001);slope=gain*(SET/RK[k])*(10.01e6/(x+10.01e6))**2
   adc_counts=lsb*5/4096/100e-6 if lsb else 10
   ratio=adc_counts*100e-6/slope/((pct-.0006)*x+counts*fs/20000)
   rows.append(dict(q='C4',range_ohm=fs,level=level,adc_lsb=lsb,adc_counts=adc_counts,worst_pct=float(100*ratio.max()),at_fraction=float(x[np.argmax(ratio)]/fs),limit_pct=limit*100))
 s4.writecsv(RESULTS/'s13_inl.csv',rows)
 # Datasheet-derived RSS drift from 23 C to either endpoint, not full span.
 drift=math.sqrt(125**2+177**2+20**2+4**2)
 s4.writecsv(RESULTS/'s13_analytical.csv',[dict(term='drift_RSS_endpoint',value=drift,unit='ppm'),dict(term='drift_linear_endpoint',value=125+250+20+4,unit='ppm'),dict(term='threshold_uncalibrated',value=.016/(.001*10.1/2),unit='ohm'),dict(term='threshold_calibrated_7mV_assumed',value=.007/(.001*10.1/2),unit='ohm'),dict(term='P34_20mV_signal',value=.02*10.1*100000/10010000/100e-6,unit='ADC_counts')])
def main():
 ap=argparse.ArgumentParser();
 for flag in ('smoke','resume','preflight','build'):ap.add_argument('--'+flag,action='store_true')
 ap.add_argument('--only',nargs='*');ap.add_argument('--workers',type=int,default=10);a=ap.parse_args()
 JOBS.mkdir(exist_ok=True);RESULTS.mkdir(exist_ok=True);cs=cases()
 if a.only:cs=[c for c in cs if c['q'] in a.only]
 if a.preflight:cs=cs[:1]
 elif a.smoke:
  cs=[next(c for c in cs if c['kind']==kind) for kind in dict.fromkeys(c['kind'] for c in cs)]
 if a.build:
  for c in cs:(JOBS/(filename(c)+'.cir')).write_text(deck(c),encoding='utf-8')
  print('built',len(cs));return
 start=time.perf_counter();records=[]
 # Priority groups complete in requested order.
 for q in dict.fromkeys(c['q'] for c in cs):
  group=[c for c in cs if c['q']==q]
  with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
   for f in cf.as_completed([pool.submit(run,c,a) for c in group]):
    r=f.result();records.append(r)
    if len(records)%10==0 or a.smoke or a.preflight or r['status']!='ok':print(f'{len(records)}/{len(cs)} {q} {r["kind"]} {r["status"]} {r["elapsed_s"]:.2f}s',flush=True)
 label='preflight' if a.preflight else 'smoke' if a.smoke else 'campaign';dest=RESULTS/f's13_{label}.csv';s4.writecsv(dest,records);analytical()
 summary=dict(total=len(records),ok=sum(r['status']=='ok' for r in records),reused=sum(r['reused'] for r in records),elapsed_s=time.perf_counter()-start,workers=a.workers,timeout_s=900)
 dest.with_suffix('.json').write_text(json.dumps(summary,indent=2));print(json.dumps(summary),flush=True)
 return int(summary['ok']!=summary['total'])
if __name__=='__main__':raise SystemExit(main())
