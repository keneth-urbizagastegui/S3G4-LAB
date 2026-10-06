"""Audit generated states, protection endpoints, OP points and single-ADC timing."""
import sys
sys.dont_write_bytecode=True
import argparse,csv,json,re
from pathlib import Path
import numpy as np
import ejecutar_s9 as s
def main():
    p=argparse.ArgumentParser();p.add_argument('--smoke',action='store_true');args=p.parse_args()
    work=s.ROOT/'S9'/('smoke' if args.smoke else 'campaign')
    s.FILTERS.update(json.loads((s.ROOT/'resultados/s9_filtros.json').read_text()))
    expected=[c for b in s.batches(args.smoke) for c in b];wanted={c['id']:c for c in expected};errors=[];decks=0
    op_decks={}
    for f in work.glob('*.cir'):
        match=re.match(r'^(s9_k5op_.+?)_(?:gain_negative|gain_zero|gain_positive|dac_low|dac_high|dac_local)_src',f.stem)
        if match:op_decks.setdefault(match[1],[]).append(f)
    data=json.loads((work/'s9_checkpoint.json').read_text());rows=data['rows'];actual={r['id']:r for r in rows}
    if len(actual)!=len(rows):errors.append('Duplicate result ids')
    missing=set(wanted)-set(actual)
    if missing:errors.append('Missing logical cases: '+str(len(missing)))
    for ident,row in actual.items():
        if ident not in wanted:errors.append('Unexpected logical state '+ident);continue
        c=wanted[ident]
        if c['s9_test']=='K4':
            fs=[f for f in work.glob(ident.replace('_acalculated_','_a*')+'_srcdc*.cir') if '_a0_' not in f.name and '_srcamp' not in f.name]
            if len(fs)!=1:errors.append('Single ADC deck missing/ambiguous '+ident);continue
            text=fs[0].read_text();decks+=1
            pulse=re.search(r'^VCLK CLK 0 PULSE\(0 1 ([^\n]+)\)',text,re.M)
            vals=[float(x) for x in pulse[1].split()]
            if not np.isclose(vals[3]+vals[1],s.TS,rtol=0,atol=1e-18) or not np.isclose(vals[4],s.PERIOD,rtol=0,atol=1e-18):errors.append('ADC timing '+ident)
            if 'S2 ' in text or text.count('CS CS 0 5p')!=1:errors.append('Wrong ADC count '+ident)
            sine=re.search(r'^VI INPUT 0 SINE\(([^)]+)\)',text,re.M);src=[float(x) for x in sine[1].split()]
            if not np.isclose(src[2],c['M']*s.FS/s.N,rtol=0,atol=1e-7) or c['M']%2!=1:errors.append('Incoherent source '+ident)
            if abs(row['closing_time_error_ps'])>1:errors.append('Aperture outside 1ps '+ident)
            measures=re.findall(r'^\.meas \w+ (\S+)',text,re.M)
            if any('_acalculated_' in m or '_a0_' in m for m in measures):errors.append('Wrong measured stimulus label '+ident)
            continue
        if c['s9_test']=='K5OP':
            fs=op_decks.get(ident,[])
            if len(fs)!=6:errors.append('Expected six OP states '+ident)
            for f in fs:
                text=f.read_text();decks+=1
                if '\n.op\n' not in text or '\n.dc ' in text:errors.append('MC DC must be OP '+f.name)
                src=float(re.search(r'^Vsrc SRC 0 ([^\n]+)',text,re.M)[1]);dac=float(re.search(r'^VDAC DAC 0 ([^\n]+)',text,re.M)[1])
                if '_gain_negative_' in f.name and not np.isclose(src,-.01*c['scale_V_div'],rtol=0,atol=1e-12):errors.append('Negative OP input '+f.name)
                if '_gain_positive_' in f.name and not np.isclose(src,.01*c['scale_V_div'],rtol=0,atol=1e-12):errors.append('Positive OP input '+f.name)
                if '_dac_low_' in f.name and dac!=.2 or '_dac_high_' in f.name and dac!=2.3 or '_dac_local_' in f.name and dac!=1.24:errors.append('Wrong DAC state '+f.name)
            continue
        if c['s9_test']=='K6':fs=[work/(ident+x+'.cir') for x in ['_negative','_positive']]
        else:fs=[work/(ident+'.cir')]
        for f in fs:
            if not f.exists():errors.append('Missing deck '+f.name);continue
            text=f.read_text();decks+=1
            for meas in re.findall(r'^\.meas \w+ (\S+)',text,re.M):
                if not meas.startswith(f.stem+'_'):errors.append('Measure state differs from deck '+f.name)
            instance=re.search(r'^XCH BNC [^\n]+',text,re.M)
            if not instance or f'POS={c["POS"]}' not in instance[0] or f'CODE={c["tap"]}' not in instance[0] or f'CPL={c["CPL"]}' not in instance[0]:errors.append('Wrong scale/relay/coupling '+f.name)
            noise=c['s9_test'] in ['K3','K5NOISE']
            if c['variant']=='B' and ('lm6172_s9_ruido_hoja.lib' in text)!=noise:errors.append('Wrong LM noise model '+f.name)
            if ('AD8038_ltspice_ruido_hoja.sub' in text)!=noise:errors.append('Wrong AD noise model '+f.name)
            if c['s9_test']=='K6':
                dr=-1 if f.stem.endswith('_negative') else 1
                sweep=re.search(r'^\.dc Vsrc ([^\n]+)',text,re.M);vals=[float(x) for x in sweep[1].split()]
                if not np.allclose(vals,[0,dr*c['dc_limit_V'],dr*.001],rtol=0,atol=1e-12):errors.append('Wrong overload sweep '+f.name)
                if '_limit'+s.old.s4.number(c['dc_limit_V']) not in f.name:errors.append('Missing overload level label '+f.name)
            if c['mc']>=0:
                rr=s.sb.realization(c['mc'])
                for key,value in rr['offsets'].items():
                    match=re.search(r'\b'+key+r'=([^\s]+)',instance[0])
                    if not match or float(match[1])!=value:errors.append('Wrong realized offset '+key+' '+f.name)
    files=list(work.glob('s9_*.csv'))
    for f in files:
        if f.name in ['s9_mc_10.csv','s9_mc_10_components.csv']:continue
        if f.name in ['s9_all.csv'] or re.fullmatch(r's9_k\w+\.csv',f.name):
            with f.open() as h:
                if next(csv.reader(h))!=s.FIELDS:errors.append('Wrong fixed column order '+f.name)
    report=dict(decks=decks,logical_cases=len(rows),expected=len(wanted),errors=errors,returncode=int(bool(errors)),method='Generated deck states, nominal/MC offsets, six OP points, exact endpoints, one ADC, coherent source, aperture and fixed CSV columns')
    s.write(work/'s9_auditoria_codex.json',json.dumps(report,indent=2));print(json.dumps(report));return report['returncode']
if __name__=='__main__':raise SystemExit(main())
