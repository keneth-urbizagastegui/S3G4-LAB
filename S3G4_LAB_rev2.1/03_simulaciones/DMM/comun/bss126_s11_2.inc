* BSS126 engineering approximation, NOT manufacturer model.
* Infineon rev2.1 pp1-3: IDSS>=7mA (NO max), threshold at8uA,
* Vth -2.7/-2/-1.6V; Ron320typ/700max at3mA, BV600V; RthJA250.
* p6 graphical approximations: threshold -3.7mV/K; Ron ratio
* exp(.0055*(T-25)); neither is a guaranteed temperature bound.
* p3 constant caps: Cgs20p Cgd1p Cds1.4p at25V; ESD unvalidated.
* IDSS=21mA sensitivity must NOT be called guaranteed maximum.
.subckt BSS126_EST d g s params: IDS=7m VP=1.6 RON=700 TC=25
.param VT0={VP/(1-sqrt(8u/IDS))}
.param VPT={VT0+.0037*(TC-25)}
.param KPT={2*IDS/VT0**2*exp(-.0055*(TC-25))*VT0/VPT}
.param CORE={VT0/(2*IDS)*(2/(1+sqrt(1-3m/IDS)))}
Rd d di {max(RON-CORE,0)*exp(.0055*(TC-25))}
M1 di g s s DM
.model DM NMOS(Level=1 Vto={-VPT} Kp={KPT} Lambda=0 Tnom={TC})
Cgs g s 20p
Cgd g di 1p
Cds di s 1.4p
Dbody s di DB126
.model DB126 D(Is=2n N=2 Rs=1 Tt=160n)
* Avalanching only enables stress estimates, no avalanche energy rating exists.
Dava s di DA126
.model DA126 D(Is=1e-30 N=2 BV=600 Ibv=250u Rs=10)
.ends BSS126_EST
