* S5 2026-10-03: include S4 unchanged. Two unity-gain SK sections.
.include "ch1_comun_s4.inc"
* R1/R2, C1 feedback to OUT, C2 to ground; 1pF PCB at IN+ only.
* Expose zero-volt sensors for both input currents and supply consumption.
.subckt SK_S5 IN OUT VP VN IP IM params: RA=1k RB=1k CF=100p CG=100p
R1 IN MID {RA}
R2 MID PLUS {RB}
C1 MID OUT {CF}
C2 PLUS 0 {CG}
CPCB PLUS 0 1p
VIP PLUS IP 0
VIM OUT IM 0
VCCP VP VPP 0
VCCN VN VNN 0
XAMP IP IM VPP VNN OUT AD8038
.ends SK_S5
.subckt FILTER_S5 IN OUT VP VN params: R1A=1k R1B=1k C1A=100p C1B=100p R2A=1k R2B=1k C2A=100p C2B=100p
XA IN OA VP VN IPA IMA SK_S5 RA={R1A} RB={R1B} CF={C1A} CG={C1B}
XB OA OUT VP VN IPB IMB SK_S5 RA={R2A} RB={R2B} CF={C2A} CG={C2B}
.ends FILTER_S5
