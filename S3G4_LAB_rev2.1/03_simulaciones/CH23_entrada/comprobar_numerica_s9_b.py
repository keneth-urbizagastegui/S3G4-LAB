"""Same completed B cases, numerical sensitivity only; never a circuit remedy."""
import sys
sys.dont_write_bytecode=True
import json,time
import argparse
from concurrent.futures import ThreadPoolExecutor
import ejecutar_s9_b as b
s=b.s;ROOT=b.ROOT

MODE='gmin12'
def run(mc):
    c=b.bcase('K5AC',0,mc)
    campaign=ROOT/'S9/B_hoja/campaign'
    reference=json.loads((campaign/(c['id']+'.json')).read_text())
    ident=c['id']+'_'+MODE+'_diagnostico';cc=dict(c,id=ident)
    deck=s.net(cc)
    if MODE=='gmin12':deck=deck.replace('gmin=1e-16','gmin=1e-12')
    work=ROOT/'S9/B_hoja/numerica';work.mkdir(parents=True,exist_ok=True)
    bias=campaign/(s.case('K1','B',0)['id']+'.bias')
    if MODE=='biasmc':
        mapped=work/'s9b_nominal_to_mc.bias'
        s.write(mapped,bias.read_text().replace(':xselect:xb',''))
        bias=mapped
    raw,rec=s.native(cc,work,deck,120,bias)
    if raw is None:return dict(mc=mc,error=rec)
    row=s.ac_metrics(raw,c)
    before=reference['row']
    differences={k:row[k]-before[k] for k in ['minus3_Hz','peak_db','atten_1p73m_db','atten_2p47m_db','gain_dc_signed']}
    return dict(mc=mc,mode=MODE,original_seconds=reference['records'][0]['seconds'],regularized_seconds=rec['seconds'],differences=differences)

def main():
    global MODE
    ap=argparse.ArgumentParser();ap.add_argument('--mode',choices=['gmin12','biasmc'],default='gmin12');MODE=ap.parse_args().mode
    s.FILTERS.update(json.loads((ROOT/'resultados/s9_filtros.json').read_text()))
    with ThreadPoolExecutor(max_workers=2) as pool: rows=list(pool.map(run,[0,200]))
    s.write(ROOT/('resultados/s9b_numerica'+('_biasmc' if MODE=='biasmc' else '')+'.json'),json.dumps(rows,indent=2))
    print(json.dumps(rows,indent=2))
if __name__=='__main__':main()
