"""Local LM6172 validation. Original manufacturer model is read only."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import os,json,subprocess,time
from concurrent.futures import ThreadPoolExecutor
import numpy as np
ROOT=Path(__file__).resolve().parent
CH1=ROOT.parent/'CH1_entrada'
sys.path.insert(0,str(CH1))
import ejecutar_s7b as sb
MODELS=Path(os.environ.get('S3G4_MODELS',str(sb.MODELS)))
LT=sb.LT
def run(item):
    name,mode,gain,vin,rail=item
    work=ROOT/'S9'/'K0';work.mkdir(parents=True,exist_ok=True)
    ident=f'k0_b_{name}_g{gain}_vin{sb.old.s4.number(vin)}_rail{rail}'
    p=work/(ident+'.cir')
    feedback=['RFB OUT IM 900','RG IM 0 100'] if gain==10 else ['VFB OUT IM 0']
    model=ROOT/'comun/lm6172_s9_sin_ruido_interno.lib' if name=='silent' else ROOT/'comun/lm6172_s9_ruido_hoja.lib' if name=='sheet' else MODELS/'LM6172/lm6172.lib'
    deck='\n'.join([f'* {ident}',f'.include "{model}"','.options gmin=1e-16 numdgt=15 plotwinsize=0 threads=1',f'VP VP 0 {rail}',f'VN VN 0 {-rail}',f'VI IN 0 {vin} AC 1','VIP IN IP 0','VIM IM IMR 0','XLM IP IMR VP VN OUT LM6172/NS','RL OUT 0 1k']+feedback+(['.op','.save V(OUT) I(VP) I(VN) I(VIP) I(VIM)'] if mode=='op' else ['.ac dec 300 1 1G','.save V(OUT) V(IN)'] if mode=='ac' else ['.noise V(OUT) VI dec 300 1 10Meg',f'.meas NOISE {ident}_en100k FIND V(inoise) AT=100k',f'.meas NOISE {ident}_en1m FIND V(inoise) AT=1Meg'])+['.end'])+'\n'
    if name.startswith('gmin12'):deck=deck.replace('gmin=1e-16','gmin=1e-12')
    sb.write(p,deck);start=time.perf_counter();proc=sb.run_lt(p,work,120)
    log=p.with_suffix('.log').read_text(errors='replace')
    raw=sb.old.s4.s3.raw_read(p.with_suffix('.raw'))
    row=dict(id=ident,mode=mode,gain=gain,vin=vin,rail=rail,returncode=proc.returncode,seconds=time.perf_counter()-start)
    if mode=='op': row.update(out_V=float(raw['v(out)'][0]),ip_A=float(raw['i(vip)'][0]),im_A=float(raw['i(vim)'][0]),supply_plus_A=float(-raw['i(vp)'][0]),supply_minus_A=float(raw['i(vn)'][0]))
    elif mode=='ac':
        f=raw['frequency'];h=raw['v(out)']/raw['v(in)'];db=20*np.log10(abs(h/h[0]));ix=np.flatnonzero(db<=-3)[0];row.update(gain_dc=float(h[0].real),minus3_Hz=float(np.exp(np.interp(-3,db[ix-1:ix+1][::-1],np.log(f[ix-1:ix+1])[::-1]))),peak_db=float(db.max()))
    else:
        f=raw['frequency'];k=next(k for k in raw if 'inoise' in k and 'total' not in k);row.update(en100k_nV=float(np.interp(1e5,f,raw[k].real)*1e9),en1m_nV=float(np.interp(1e6,f,raw[k].real)*1e9))
    return row
def main():
    jobs=[(f'op{i}','op',1,v,r) for i,(v,r) in enumerate([(0,4.9),(.1,4.9),(-.1,4.9),(4,5),(-4,5),(0,15)])]+[('ac','ac',g,0,4.9) for g in [1,10]]+[('noise','noise',1,0,4.9),('silent','noise',1,0,4.9),('sheet','noise',1,0,4.9)]+[('gmin12_'+str(i),'op',1,v,4.9) for i,v in enumerate([0,.1,-.1])]
    with ThreadPoolExecutor(max_workers=10) as p: rows=list(p.map(run,jobs))
    sb.write(ROOT/'resultados/s9_k0.json',json.dumps(rows,indent=2))
    sb.csv_write(ROOT/'resultados/s9_k0.csv',rows,['id','mode','gain','vin','rail','returncode','out_V','ip_A','im_A','supply_plus_A','supply_minus_A','gain_dc','minus3_Hz','peak_db','en100k_nV','en1m_nV'])
    print('K0',len(rows),'validaciones, códigos',sorted(set(r['returncode'] for r in rows)))
if __name__=='__main__':main()
