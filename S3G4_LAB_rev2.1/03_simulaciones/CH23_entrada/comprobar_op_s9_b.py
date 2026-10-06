"""Bounded numerical diagnostics of the existing DAC-high OP; unchanged B circuit."""
import sys
sys.dont_write_bytecode=True
import json,argparse,re
from concurrent.futures import ThreadPoolExecutor
import ejecutar_s9_b as b
s=b.s;ROOT=b.ROOT

def run(mode):
    c=b.bcase('K5OP',0,0)
    work=ROOT/'S9/B_hoja/numerica_op';work.mkdir(parents=True,exist_ok=True)
    campaign=ROOT/'S9/B_hoja/campaign'
    reference=json.loads((campaign/(c['id']+'.json')).read_text())
    base=c['id']+'_dac_high_src0_dac2p3'
    cc=dict(c,source_V=0,vdac_V=2.3,id=base+'_'+mode+'_diagnostico')
    deck=s.net(cc)
    if mode=='stepped':
        lim=.01*c['scale_V_div']
        sources=[-lim,0,lim,0,0,0];dacs=[1.25,1.25,1.25,.2,2.3,1.24]
        tab=lambda values:'table(S9_OP_STATE,'+','.join(f'{i},{v:.17g}' for i,v in enumerate(values))+')'
        deck=re.sub(r'^Vsrc SRC 0 .*$',f'Vsrc SRC 0 {{{tab(sources)}}}',deck,flags=re.M)
        deck=re.sub(r'^VDAC DAC 0 .*$',f'VDAC DAC 0 {{{tab(dacs)}}}',deck,flags=re.M)
        deck=deck.replace('\n.end\n','\n.step param S9_OP_STATE list 0 1 2 3 4 5\n.end\n')
    if mode=='source1':deck=deck.replace('\n.end\n','\n.options srcstepmethod=1\n.end\n')
    if mode=='gminsteps':deck=deck.replace('gminsteps=0','gminsteps=100')
    if mode=='gmin12':deck=deck.replace('gmin=1e-16','gmin=1e-12')
    bias=campaign/(s.case('K5AC','B',0,0)['id']+'.bias')
    raw,rec=s.native(cc,work,deck,60,bias)
    if raw is None:return dict(mode=mode,error=rec)
    if mode=='stepped':
        vals=raw['v(pin)'].tolist()
        if len(vals)!=6:raise RuntimeError('Expected six OP values, found '+str(len(vals)))
        low,center,high,dl,dh,local=vals
        slope=(center-local)/.01
        derived=dict(gain_dc_signed=(high-low)/(2*lim),center_V=center,dac_center_V=1.25+(1.25-center)/slope,position_plus_div=(dl-1.25)/.25,position_minus_div=(1.25-dh)/.25)
        return dict(mode=mode,seconds=rec['seconds'],pins=vals,differences={k:v-reference['row'][k] for k,v in derived.items()})
    expected=1.25-reference['row']['position_minus_div']*.25
    return dict(mode=mode,seconds=rec['seconds'],pin_V=float(raw['v(pin)'][0]),reference_pin_V=expected,difference_V=float(raw['v(pin)'][0])-expected)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['initial','gmin12','stepped'],default='initial');args=ap.parse_args()
    s.FILTERS.update(json.loads((ROOT/'resultados/s9_filtros.json').read_text()))
    with ThreadPoolExecutor(max_workers=2) as pool:rows=list(pool.map(run,[args.mode] if args.mode!='initial' else ['source1','gminsteps']))
    s.write(ROOT/('resultados/s9b_numerica_op'+('_'+args.mode if args.mode!='initial' else '')+'.json'),json.dumps(rows,indent=2));print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
