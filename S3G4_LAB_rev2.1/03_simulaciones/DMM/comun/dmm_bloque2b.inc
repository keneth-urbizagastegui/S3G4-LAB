* S12b, topology fixed by decision 2026-10-08. Includes supplied in deck.
* COM=0; pcb parasitics assumed. MUXAC=1 only for AC/noise, NXP SWI1 transient otherwise.
* TMUX4053 parametric: Ron 60ohm typical, 400ohm corner; leakage supplied.
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
D1p x1p vp BAV199
D1n vn x1p BAV199
Rx1 x1p x1 100
* Two TI followers; zero-volt probes measure BOTH signal input currents.
Vib0 x0 bi0 0
Vib1 x1 bi1 0
Vibn0 bx0 bn0 0
Vibn1 bx1 bn1 0
Xbuf0 bi0 bn0 vp vn bx0 OPAx192
Xbuf1 bi1 bn1 vp vn bx1 OPAx192
Ibl0 x0 0 {BLEAK}
Ibl1 x1 0 {BLEAK}
* Rc1/Rc2/Rc3 3.3k antipulse: reference/rating pending; no value changed.
* BEGIN_MUX: passive AC/noise; replaced by eight SWI1 in transient decks.
Cy0 bx0 0 5p
Cy1 bx1 0 5p
Cy2 x2 0 5p
Cz mux 0 {CZ}
* Selected resistor supplied by executor (X0, X1, X2 or COM).
* END_MUX
Cp0 x0p 0 {CPRE}
Cp1 x1p 0 {CPRE}
Cp2 x2 0 {CPRE}
Cpcb mux 0 {CPCB}
Ileak mux 0 {LEAK}
Imux0 bx0 0 {MLEAK}
Imux1 bx1 0 {MLEAK}
Imux2 x2 0 {MLEAK}
Rfg out tap {RF}
Rgg tap 0 {RG}
Sg1 out g1 gain1 0 S12SW
Sg10 tap g10 gain10 0 S12SW
Rg1 g1 inv {RTMUX}
Rg10 g10 inv {RTMUX}
Ctm inv 0 10p
Itm inv 0 {GTLEAK}
Xamp mux inv vp vn out OPAx192
Vcm vcm 0 1.25
Rload out vcm 10k
Cload out vcm 10p
