* Reduced electrical exposure model, NOT transfer, recovery or failure model.
* OPA2188 SBOS525C p4: rail +/-0.5V, +/-10mA absolute; p5 9.5p common/6p diff;
* p6 415uA/channel. Two channels consume 830uA at 9.8V.
* TLV2372 SLOS270F p8: rail +/-0.2V, +/-10mA; p11 8p common;
* p13 550uA/channel at 5V (750uA at 15V): 550uA assumption at 9.8V.
* HC4051 Rev12 p5: +/-20mA clamp, 25mA switch; p9 16uA max at 10V/25C;
* p10: Yn 5p, Z 25p; p1: Ron 60 ohm typical at 9V.
* Clamp Ron=1ohm is an unverified IV approximation; current is NOT capped.
.model ICOPA D(Ron=1 Roff=1T Vfwd=.5)
.model ICTLV D(Ron=1 Roff=1T Vfwd=.2)
.model ICHC D(Ron=1 Roff=1T Vfwd=.5)
.subckt PINOPA a rp rn
Dhi a rp ICOPA
Dlo rn a ICOPA
Cin a 0 9.5p
.ends
.subckt PINTLV a rp rn
Dhi a rp ICTLV
Dlo rn a ICTLV
Cin a 0 8p
.ends
.subckt PINHC a rp rn
Dhi a rp ICHC
Dlo rn a ICHC
Cin a 0 5p
.ends
Xh0 x0 rp rn PINHC
Xh1 x1 rp rn PINHC
Xh2 x2 rp rn PINHC
Xh3 0 rp rn PINHC
Xh4 shunt rp rn PINHC
Xh5 x5 rp rn PINHC
Xh6 n2 rp rn PINHC
Xh7 0 rp rn PINHC
Xhz mux rp rn PINHC
Chz mux 0 20p
Vamp mux ampin 0
Xopi ampin rp rn PINOPA
Xopn out rp rn PINOPA
Copdiff ampin out 6p
* No amplifier transfer in reduced model: second follower input tied to first.
Rfeedback ampin out 1u
Riqopa rp rn {9.8/(2*415u)}
Riqtlv rp rn {9.8/(2*550u)}
Riqhc rp rn {9.8/16u}
* Residual load preserves total contractual 3mA, without double counting ICs.
Riqother rp rn {9.8/(.003-2*415u-2*550u-16u)}
* P43 retained as abstract compliant current source (not a feedback macro).
Vhead rp ms {.5*POWER*if(ISOURCE>0,1,0)}
Vsense ms msource 0
Bsource msource n2 I={ISOURCE*limit(V(msource,n2)/.1,0,1)*POWER}
* TLV feedback input at source side; reference is tied here because actual
* sense resistor/reference topology is outside block 1. Does not certify TLV loop.
Xtlvi ms rp rn PINTLV
Xtlvn msource rp rn PINTLV
* BSS84 DS30149 p2: Vds -50V, Vgs +/-20V, Id -130mA, pulse -1.2A;
* Ciss 24.6p, Coss 4.7p, Crss 2.8p typical. Gate has NO specified rail diodes:
* do not invent them. Intrinsic PMOS body diode drains to source, no gate load.
Cmosgs ms msource 21.8p
Cmosgd ms n2 2.8p
Cmosds n2 msource 1.9p
Dmosbody n2 msource BODY
* No fictitious 130mA limit or gate clamp; evaluate stress externally.
