* S13 P43, c1. Parameters set by ejecutar_s13.py. Manufacturer TLV2372/SWI1.
* BSS138 generic LTspice model: assumption, not selected-MPN guarantee.
.model B3N VDMOS(Vto=1.3 Kp=1.3 Rs=.5 Rd=.5 Rg=3 Cgdmax=40p Cgdmin=3p Cgs=50p Cjo=20p Is=1p)
.model B3P VDMOS(pchan Rg=3 Vto={VTO} Rd=2.4 Rs=1.8 Rb=3 Kp=.2 Cgdmax={40p*CSCALE} Cgdmin={1p*CSCALE} Cgs={20p*CSCALE} Cjo={10p*CSCALE} Is=2p ksubthres=.1)
Vbref bref 0 2.5
Rben bref ben 10k
Mben ben en 0 0 B3N
Vben en 0 {if(ENABLE,0,3.3)}
Vosa ben aina {VOSA}
Xb1 aina e1 rp rn o1 TLV2372
Rb1 o1 b1 10k
Mb1 cn b1 e1 e1 B3N
Rbref e1 0 {24900*RREF}
Rbset rp cn {4990*RSET}
Rk rp s {RK}
* SWI1 is active low; selected control COM, spare channels at VCC.
* Sense/force stay selected during source OFF: disable reference first.
* INH after settling is a firmware action, not included in this analog test.
Vbon bon 0 0
Ebof boff 0 rp 0 1
Xforce bon s ff rn rp 0 SWI1
Rfr ff f {max(RON-60,.001)}
Xsense bon s ss rn rp 0 SWI1
Rsr ss sn {1000+max(RON-60,0)}
Cbf f 0 {25p*CSCALE}
Cbs sn 0 {33p*CSCALE}
Cbsy s 0 {5p*CSCALE}
Vosb cn ainb {VOSB}
Xb2 ainb sn rp rn ogi TLV2372
Vinj ogi og 0 AC {ACINJ}
Cbcomp og sn 1n
Rbg og gate 1k
Mbpass bp gate f f B3P
Dbblock bp n1 BAT54
Iforce f 0 {LF}
Iborne bor 0 {LB}
