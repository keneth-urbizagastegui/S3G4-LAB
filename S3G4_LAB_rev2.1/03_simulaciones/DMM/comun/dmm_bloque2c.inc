* S12c derivative of S12b: single /100 tap, X1 grounded, one X0 buffer.
* Same dual OPA2192: buffer X0 and amplifier A. Local TI single-channel instances.
.param SEL=0 GAIN=1 MUXAC=1 RON=70 RTMUX=60 LEAK=0 GTLEAK=0 BLEAK=0 MLEAK=0
.param CT1=100p CT2=100p CT3=100p C2=330p C3=3n CPRE=3p CZ=25p CPCB=3p
.param R1A=1.5Meg R1B=1.5Meg R2A=1.5Meg R2B=1.5Meg R3A=1.5Meg R3B=1.5Meg RLOW=910k RBOT=100k RF=91k RG=10k RPROT=99k
.model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)
.model S12SW SW(Ron=1 Roff=1T Vt=.5)
Rp vin x0p {RPROT}
D0p x0p vp BAV199
D0n vn x0p BAV199
Rx0 x0p x0 100
R1a vin d1a {R1A}
R1b d1a d1 {R1B}
R2a d1 d2a {R2A}
R2b d2a d2 {R2B}
R3a d2 d3a {R3A}
R3b d3a x1p {R3B}
Rc1 vin c1 3300
Cc1 c1 d1 {CT1}
Rc2 d1 c2n 3300
Cc2 c2n d2 {CT2}
Rc3 d2 c3n 3300
Cc3 c3n x1p {CT3}
Rlow x1p x2 {RLOW}
Clow x1p x2 {C2}
Rbot x2 0 {RBOT}
Cbot x2 0 {C3}
* x1p is internal divider junction, NOT a mux tap. No clamp, Rx1 or buffer.
Vib0 x0 bi0 0
Vibn0 bx0 bn0 0
Xbuf0 bi0 bn0 vp vn bx0 OPAx192
Ibl0 x0 0 {BLEAK}
* 3x3.3k antipulse >=1.5kV >=25uJ deltaR<=1%; MPN qualification pending.
* BEGIN_MUX
Cy0 bx0 0 5p
Cy1 0 0 5p
Cy2 x2 0 5p
Cz mux 0 {CZ}
* END_MUX
Cp0 x0p 0 {CPRE}
* Internal divider junction retains assumed 3pF pad/pista, not removed hardware.
Cp1 x1p 0 {CPRE}
Cp2 x2 0 {CPRE}
Cpcb mux 0 {CPCB}
Ileak mux 0 {LEAK}
Imux0 bx0 0 {MLEAK}
Imux2 x2 0 {MLEAK}
Rfg out tap {RF}
Rgg tap 0 {RG}
Sg1 out g1 gain1 0 S12SW
Sg10 tap g10 gain10 0 S12SW
Rg1 g1 inv {RTMUX}
Rg10 g10 inv {RTMUX}
* CD(ON)=10pF in pi: 5p on common and 5p on selected source side.
Ctm inv 0 5p
Ctmo1 g1 0 {5p*(GAIN<2)}
Ctmo10 g10 0 {5p*(GAIN>1)}
Itm inv 0 {GTLEAK}
Xamp mux inv vp vn out OPAx192
Vcm vcm 0 1.25
Rload out vcm 10k
Cload out vcm 10p
