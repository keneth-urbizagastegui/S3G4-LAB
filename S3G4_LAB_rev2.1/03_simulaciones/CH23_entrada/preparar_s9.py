"""Generate reviewable copies of the fixed CH1 topology, never edit CH1/models."""
import sys
sys.dont_write_bytecode=True
from pathlib import Path
import re
ROOT=Path(__file__).resolve().parent
CH1=ROOT.parent/'CH1_entrada'
sys.path.insert(0,str(CH1))
import ejecutar_s7b as sb
def main():
    text=sb.TEXT
    sk='\n'.join(sb.extract(text,'SK_S7B','SK_S9'))
    sk=sk.replace('VOS=0','VOS=0 AMP=0')
    sk=sk.replace('XAMP IPR IM VPP VNN OUT AD8038','XAMP IPR IM VPP VNN OUT AMP_S9 KIND={AMP}')
    chan='\n'.join(sb.extract(text,'CHANNEL_S7B','CHANNEL_S9'))
    chan=chan.replace('VO836=0','VO836=0 AMP=0 F1=2.49k F2=1.10k')
    chan=chan.replace('AD8038','AMP_S9 KIND={AMP}').replace('SK_S7B','SK_S9').replace('{RFILT1_S7}','{F1}').replace('{RFILT2_S7}','{F2}')
    chan=chan.replace('VOS={VOFA}','VOS={VOFA} AMP={AMP}').replace('VOS={VOFB}','VOS={VOFB} AMP={AMP}')
    wrapper='''* Pin order is symbolic, not SOIC package pin numbers.
.subckt LM6172_W IP IM VP VN OUT
XCORE IP IM VP VN OUT LM6172/NS
.ends LM6172_W
.subckt AMP_S9_A IP IM VP VN OUT
XA IP IM VP VN OUT AD8038
.ends AMP_S9_A
.subckt AMP_S9_B IP IM VP VN OUT
XB IP IM VP VN OUT LM6172_W
.ends AMP_S9_B
* AMP_S9 is bound by the deck generator from AMP_S9_SELECT (0=A,1=B).
* Exactly one manufacturer instance, never two inactive loaded amplifiers.
'''
    sb.write(ROOT/'comun/ch23_comun_s9.inc','* S9: immutable S7b included verbatim; only filter/amp/ADC timing changed.\n.include "../../CH1_entrada/comun/ch1_comun_s7b.inc"\n'+wrapper+sk+'\n'+chan+'\n')
    native=(sb.MODELS/'LM6172/lm6172.lib').read_text().replace('LM6172/NS','LM6172_S9_CORE')
    lines=[]
    for line in native.splitlines():
        if re.match(r'^R\w*\s',line):line+=' noiseless'
        lines.append(line)
    k=1.380649e-23;t=273.15+25;en=11e-9;inoise=1e-12
    noise=f'''
* Sheet SNOS792E table 5.6 p8, +/-5 V: en=11n, in=1p at10kHz.
* White approximation 1Hz..10MHz; no verified 1/f curve.
.subckt LM6172/NS IP IM VP VN OUT
REN NE 0 {en**2/(4*k*t):.17g}
EEN IPN IP NE 0 1
RINP NP 0 {4*k*t/inoise**2:.17g}
RINM NM 0 {4*k*t/inoise**2:.17g}
GINP IP 0 NP 0 {inoise**2/(4*k*t):.17g}
GINM IM 0 NM 0 {inoise**2/(4*k*t):.17g}
XCORE IPN IM VP VN OUT LM6172_S9_CORE
.ends LM6172/NS
'''
    sb.write(ROOT/'comun/lm6172_s9_ruido_hoja.lib','* Copy for NOISE ONLY: internal resistors noiseless, sheet sources added.\n'+'\n'.join(lines)+'\n'+noise)
    sb.write(ROOT/'comun/lm6172_s9_sin_ruido_interno.lib','* Diagnostic core, native resistor noise disabled.\n'+'\n'.join(lines).replace('LM6172_S9_CORE','LM6172/NS')+'\n')
if __name__=='__main__':main()
