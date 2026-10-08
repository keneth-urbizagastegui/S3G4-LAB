* S11.4 final, S11.3 dependencies read-only.
* Rprot: FOJAN FPS1206J333 33k 0.5W, 200V catalog (no local sheet).
* Rohm: Milliohm HoCR2512 1.1k 2W, 250V catalog (no local sheet).
* Cc: CCTC TCC1206COG101J202FT 100p C0G 2kV (no local sheet).
* GDT SMD4532-600NF: catalog DC600V +/-30%, impulse1000V@100V/us,
* 0.5pF. All catalog data assumed until a local manufacturer sheet exists.
* DC corner GDC; GIMP shared by both corners (no impulse tolerance given).
* Linear slope interpolation capped above100V/us is assumed, NOT guaranteed.
* Arc20V plus1ohm, holding10mA, turn-on/off1ns are unverified assumptions.
* State integrates toward1 when threshold crossed or ignition sustained,
* decays toward0 below GHOLD. No damage, thermal or stochastic delay model.
Cgdt vin 0 .5p
Cgstate gstate 0 1n IC=0
Rgstate gstate 0 1T
Bgthreshold gthreshold 0 V={GDC+(GIMP-GDC)*limit(abs(ddt(V(vin)))/100Meg,0,1)}
Bgstate 0 gstate I={1n/GTAU*if(abs(V(vin))>=V(gthreshold),1-V(gstate),if(V(gstate)>1u,if(abs(I(Bgdt))>=GHOLD,1-V(gstate),-V(gstate)),-V(gstate)))}
Bgdt vin 0 I={limit(V(gstate),0,1)*sgn(V(vin))*max(abs(V(vin))-GARC,0)/GRON}
* S11.1 contractual topology. Includes manufacturer models in generated decks.
* O4 has no PTC and no BSS126; no destructive or thermal failure is modeled.
.model RELAY SW(Ron=.1 Roff=1e12 Vt=.5 Vh=0)
.model FUSE_SW SW(Ron=.04 Roff=1e12 Vt=0 Vh=.001)
.model BSS84 VDMOS(pchan Rg=3 Vto=-2.1 Rd=2.4 Rs=1.8 Rb=3 Kp=.2 Cgdmax=.04n Cgdmin=.001n Cgs=.02n Cjo=.01n Is=2p ksubthres=.1)
* GBU808 fit to 1.0 V at 4 A per diode, local DS21227 p2; Rs15m is assumed.
.model GBU808 D(Is=4.543761543852662e-08 N=2 Rs=.015 Cjo=130p BV=800 Ibv=5u)
.model BODY D(Is=1n N=1 Rs=.1)
.model REGSUP D(Ron=1u Roff=1e18 Vfwd=0)
.model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)
Rprot1 vin p1 33k
Rprot2 p1 p2 33k
Rprot3 p2 x0 33k
D0p x0 rp BAV199
D0n rn x0 BAV199
Rdiv1 vin d1 3Meg
Rdiv2 d1 d2 3Meg
Rdiv3 d2 x1 3Meg
Rc1 vin c1 3.3k
Cc1 c1 d1 100p
Rc2 d1 c2 3.3k
Cc2 c2 d2 100p
Rc3 d2 c3 3.3k
Cc3 c3 x1 100p
Rdiv4 x1 x2 900k
Cdiv4 x1 x2 330p
Rdiv5 x2 0 100k
Cdiv5 x2 0 3n
D1p x1 rp BAV199
D1n rn x1 BAV199
Srelay vin ptin rc 0 RELAY
Coff vin ptin 1p
* TVS linear avalanche through VBRmax/IT and VCmax/IPP, p3.
Rs n1 n2 {RSER}
D2p n2 rp BAV199
D2n rn n2 BAV199
* P43 pass MOS source 0.5 V below rail; feedback forces current only when compliant.
Vhead rp ms {.5*POWER*if(ISOURCE>0,1,0)}
Vsense ms msource 0
Ccontrol ctrl 0 {max(ISOURCE*1m,1n)} IC={if(ISOURCE==0,0,2.1)}
Rcontrol ctrl 0 1T
Berror 0 ctrl I=if(ISOURCE==0,-V(ctrl)/1k,ISOURCE-I(Vsense)-max(V(ctrl)-4.5,0)/1k+max(-V(ctrl),0)/1k)
Bgate gate 0 V=if(ISOURCE==0,V(ms),V(ms)-limit(V(ctrl),0,4.5))
Mpass bp gate msource msource BSS84
Dblk bp n2 BAT54
Bfctl fc 0 V=6.7*ARC-V(qfus)-.001
Cqfus qfus 0 1 IC=0
Bqfus 0 qfus I=I(Vfs)**2
Vfs ain af 0
Sfuse af shunt fc 0 FUSE_SW
Rshunt shunt 0 .1
Dbr1 shunt bridge GBU808
Dbr2 0 bridge GBU808
Dbr3 bridge shunt GBU808
Dbr4 bridge 0 GBU808
Rwarn ain x5 10Meg
D5p x5 rp BAV199
D5n rn x5 BAV199
* Local rails: one-way source, external typical load plus macro consumption.
Vregp regp 0 {4.9*RAIL}
Vregn regn 0 {-4.9*RAIL}
Rdeliverp regp regpf .5
Rdelivern regnf regn .5
Dregp regpf preg REGSUP
Dregn nreg regnf REGSUP
Rloadswp preg rp {if(POWER==1,1u,1e18)}
Rloadswn rn nreg {if(POWER==1,1u,1e18)}
Rloadp rp 0 {if(POWER==1,4.9/.003,1e18)}
Rloadn rn 0 {if(POWER==1,4.9/.003,1e18)}
Crp rp 0 1u
Crn rn 0 1u
* Principal rails use the CH1 acta loads 42/39 mA, not ideal sinks.
Dmainp regp mainp REGSUP
Dmainn mainn regn REGSUP
Rmainp mainp 0 {4.9/.042}
Rmainn mainn 0 {4.9/.039}
Cmp mainp 0 10u
Cmn mainn 0 10u
* BODYCASE=0 uses an open switch in series with each diode.
Vbody bc 0 {BODYCASE}
Sbp rp bpp bc 0 RELAY
Dbp bpp mainp BODY
Sbn bnn rn bc 0 RELAY
Dbn mainn bnn BODY
Bsel0 ct0 0 V=if(TAP==0,0,V(rp))
Bsel1 ct1 0 V=if(TAP==1,0,V(rp))
Bsel2 ct2 0 V=if(TAP==2,0,V(rp))
Bsel3 ct3 0 V=if(TAP==3,0,V(rp))
Bsel4 ct4 0 V=if(TAP==4,0,V(rp))
Bsel5 ct5 0 V=if(TAP==5,0,V(rp))
Bsel6 ct6 0 V=if(TAP==6,0,V(rp))
Bsel7 ct7 0 V=if(TAP==7,0,V(rp))
Rx0 x0 hx0 100
Rx1 x1 hx1 100
* RX2 absent: X2 wired directly to the mux.
Xm0 ct0 hx0 mux rn rp 0 SWI1
Xm1 ct1 hx1 mux rn rp 0 SWI1
Xm2 ct2 x2 mux rn rp 0 SWI1
Xm3 ct3 0 mux rn rp 0 SWI1
Rb shunt bin 10k
Xm4 ct4 bin mux rn rp 0 SWI1
Xm5 ct5 x5 mux rn rp 0 SWI1
* Channel6 removed from N2; spare grounded.
Xm6 ct6 0 mux rn rp 0 SWI1
Xm7 ct7 0 mux rn rp 0 SWI1
Vamp mux ampin 0
* Macro supply voltages buffered: the contractual 3mA load already includes ICs.
Eampp amprp 0 rp 0 1
Eampn amprn 0 rn 0 1
* Manufacturer transfer model has a voltage interface; physical input ESD and
* capacitances exposed separately. Avoid assigning ALL input displacement
* current to a supply rail. This wrapper is an approximation, explicitly audited.
Ecalc calcinput 0 ampin 0 1
Xamp calcinput calcoutput amprp amprn calcoutput OPAx188
Eout out 0 calcoutput 0 1
Xphysical ampin out rp rn ESD_IN_OPAx188
Cphysicalp ampin 0 9.5p
Cphysicaln out 0 9.5p
Cphysicaldiff ampin out 6p
Rohm1 ptin ohmid 1.1k
Rohm2 ohmid n1 1.1k
* SMAJ12CA pp2-3; S11.1 linear avalanche and leakage approximation.
Btvs n1 0 I={V(n1)*TVLEAK/12+sgn(V(n1))*max(abs(V(n1))-TVKNEE,0)/TVRD}
* BZT52C5V6 approximate sink, no local sheet found: 5.6V at5mA, Rd40ohm.
.model Z56 D(Is=1n N=1.5 BV={ZBV} Ibv=5m Rs=40 Cjo=100p)
Dzp 0 rp Z56
Dzn rn 0 Z56
