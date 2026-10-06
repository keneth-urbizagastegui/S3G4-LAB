"""Revisión de Claude (3 oct 2026): recalcula las cifras del canal CH1 desde los valores decididos."""
import numpy as np
from math import pi, sqrt, log, log10
from scipy import optimize
P=print
k=1.380649e-23; T=300
# --- entrada (ch1_comun_s2b.inc) ---
RT1=549e3; RB=11e3; RS=2*49.9e3; RBIAS=10e6; REQ=10e6; RPROT=1e3; CAC=1.8e-9
CBNC=3e-12; CX1=2e-12; CTAP=2e-12; COFF=1e-12; CSELP=3e-12; COFFSW=0.5e-12; CBUF=2.5e-12
CJO=1.9002e-12; VJ=1.2722; M=0.35193
CJ=CJO/(1+5/VJ)**M
CSEL=2*CJ+CSELP+CBUF+2*COFFSW
RBP=RB*RBIAS/(RB+RBIAS)
CT1=20e-12; CB=(CT1/2+COFF)*2*RT1/RBP-(CSEL+CTAP)
ratio100=RBP/(2*RT1+RBP); ratio1=RBIAS/(RS+RBIAS)
Zin100=1/(1/(2*RT1+RBP)+1/(RS+REQ)); Zin1=1/(1/(2*RT1+RBP)+1/(RS+RBIAS))
CX1T=CX1+COFF+CSEL; CS=RBIAS*CX1T/RS
P('== Entrada')
P(f'CJ BAV199 a 5 V = {CJ*1e12:.3f} pF; C_SEL_EST = {CSEL*1e12:.2f} pF')
P(f'÷100: relación = 1/{1/ratio100:.3f}; ×1: relación = {ratio1:.5f} ({(ratio1-1)*100:+.3f} %)')
P(f'Zin ÷100 = {Zin100/1e3:.2f} kΩ; Zin ×1 = {Zin1/1e3:.2f} kΩ')
P(f'Cb calculado = {CB*1e12:.1f} pF; C_S calculado = {CS*1e9:.3f} nF (elegido 1.5 nF)')
P(f'τ arriba ÷100 = {2*RT1*(CT1/2+COFF)*1e6:.3f} µs; τ abajo = {RBP*(CB+CSEL+CTAP)*1e6:.3f} µs')
P(f'corte AC = {1/(2*pi*RBIAS*CAC):.2f} Hz')
for V in (50,100):
    I=(V-5.6)/RS; P(f'{V} V en ×1: corriente a sujeciones {I*1e3:.3f} mA; P por R_S de 49.9 k = {I*I*49.9e3*1e3:.1f} mW; V por 549 k en ÷100 = {V*RT1/(2*RT1+RBP):.1f} V')
P(f'offset de OPA810 por Ib 2 pA en R_BIAS: {2e-12*RBIAS*1e6:.1f} µV')
# --- escalera ---
RL=[499,249,150,49.9,24.9,24.9]; tot=sum(RL)
taps=[1]+[sum(RL[i:])/tot for i in range(1,6)]
P('== Escalera'); P('tomas reales:',[round(t,6) for t in taps],' total',tot,'Ω')
ideal=[1,1/2,1/4,1/10,1/20,1/40]; P('error frente a ideal %:',[round((a/b-1)*100,3) for a,b in zip(taps,ideal)])
P(f'peor impedancia de toma: {max(sum(RL[:i])*sum(RL[i:])/tot for i in range(1,6)):.1f} Ω')
# --- ganancia ---
G1=1+1000/249; G2=1+2260/249; AOL=10**(70/20)
G1r=G1/(1+G1/AOL); G2r=G2/(1+G2/AOL)
P('== Ganancia'); P(f'ideal ×{G1:.4f} · ×{G2:.4f} = ×{G1*G2:.3f}; con A_OL 70 dB: ×{G1r*G2r:.3f} ({(G1r*G2r/(G1*G2)-1)*100:+.2f} %)')
# --- escalas ---
P('== Escalas (S4 = −1)')
scales=[(5e-3,1,0),(10e-3,1,1),(20e-3,1,2),(50e-3,1,3),(100e-3,1,4),(200e-3,1,5),(0.5,100,0),(1,100,1),(2,100,2),(5,100,3),(10,100,4),(20,100,5)]
for vd,pos,t in scales:
    c=ratio1 if pos==1 else ratio100
    g=c*taps[t]*G1r*G2r
    P(f'{vd*1e3:8.1f} mV/div  ×{"1  " if pos==1 else "÷100"} toma {ideal[t]:.4f}: V en ADC por div = {-g*vd:.4f} V ({(g*vd/0.25-1)*100:+.2f} % frente a 0.25)')
# --- filtro TR reescalado ---
def sk(R,C1,C2): return 1/(2*pi*R*sqrt(C1*C2)), 0.5*sqrt(C1/C2)
s1=sk(1110,56e-12,47e-12); s2=sk(499,220e-12,56e-12)
P('== Filtro'); P(f'sección 1: f0 {s1[0]/1e6:.3f} MHz, Q {s1[1]:.3f}; sección 2: f0 {s2[0]/1e6:.3f} MHz, Q {s2[1]:.3f}')
fRC=1/(2*pi*68*470e-12)
def H(f):
    s=2j*pi*f; h=1
    for f0,Q in (s1,s2):
        w=2*pi*f0; h*=w*w/(s*s+s*w/Q+w*w)
    for fp in (fRC,10.8e6): h*=1/(1+s/(2*pi*fp))
    return h
f3=optimize.brentq(lambda f:20*log10(abs(H(f)))+3,5e5,5e6)
P(f'ideal −3 dB {f3/1e6:.3f} MHz (simulado en cadena: 2.011); A(4.5 MHz) {-20*log10(abs(H(4.5e6))):.1f} dB; polo del RC {fRC/1e6:.2f} MHz')
# --- S4 ---
RIN=RF=10e3; ROFF=8.06e3; vref=2.5; vmid=vref*5.23/15.23
kk=RF/ROFF
P('== S4'); P(f'VMID {vmid:.4f} V; V_ADC = {1+RF/RIN+kk:.4f}·VMID − V_in − {kk:.4f}·V_DAC; centro con V_DAC 1.25: {(2+kk)*vmid-1.25*kk:.4f} V')
P(f'offset: V_DAC 0.2 → {(-(0.2-1.25)*kk)/0.25:+.2f} div; 2.3 → {(-(2.3-1.25)*kk)/0.25:+.2f} div (salida mínima ≈ 0.02 V)')
P(f'carga del DAC {ROFF/1e3:.2f} kΩ (≥ 5 kΩ: {ROFF>=5e3}); corriente de VREF+ por 3 divisores = {3*vref/15.23e3*1e3:.3f} mA (REF3325 ±5 mA)')
P(f'ganancia de ruido {1+RF/(RIN*ROFF/(RIN+ROFF)):.3f}; polo C_F {1/(2*pi*RF*1e-12)/1e6:.1f} MHz')
P(f'offset por Ib del OPA836 (650 nA) en el divisor: {650e-9*(10e3*5.23e3/15.23e3)*1e3:.2f} mV en VMID → ×3.24 = {650e-9*(10e3*5.23e3/15.23e3)*3.24e3:.2f} mV en ADC')
# --- ADC ---
LSB=2.5/4096; P('== ADC'); P(f'LSB {LSB*1e3:.4f} mV; códigos por div {0.25/LSB:.1f}; pantalla 0.25–2.25 V = códigos {0.25/LSB:.0f}–{2.25/LSB:.0f}')
for snr in (66.9,63.2):
    vn=2.5/(2*sqrt(2))/10**(snr/20); P(f'ruido ADC con SNR {snr} dB: {vn*1e3:.3f} mV rms = {vn/0.25*100:.3f} % div')
an=0.38; P(f'ruido total (AFE {an} % ⊕ ADC 0.16–0.24 %): {sqrt(an**2+0.16**2):.2f}–{sqrt(an**2+0.24**2):.2f} % div = {sqrt(an**2+0.24**2)/100*410:.2f} códigos rms en el peor caso')
# --- ancho de banda requerido de U103/filtro: SR ---
P('== Slew rate'); P(f'2 Vpp a 2 MHz exige {2*pi*2e6*1/1e6:.1f} V/µs; AD8039 425; OPA836 560; OPA810 {"≥ 200 (hoja)"}')
# --- consumo por canal (hoja) ---
P('== Consumo por canal (hoja)')
I5=3.7+4*1.0; I33=1.0; P(f'±5 V: OPA810 3.7 + 4 × AD8039 1.0 = {I5:.1f} mA por riel; 3.3 V: OPA836 {I33} mA + VMID 0.164 mA (VREF+)')
P(f'tres canales iguales: ±5 V {3*I5:.1f} mA por riel (G.3 suponía 10 × 3.9 = 39 mA); 3.3 V {3*I33:.1f} mA (G.3: 11.7 mA)')
P(f'potencia AFE de los 3 canales: {3*I5*1e-3*10*1e3:.0f} mW en ±5 V + {3*I33*3.3:.0f} mW en 3.3 V')
# --- 4051 ---
P('== 74HC4051'); 
for v in (5.0,5.04,5.08): P(f'rieles ±{v:.2f} V → VCC−VEE = {2*v:.2f} V (recomendado ≤ 10.0, máx. absoluto 11)')
