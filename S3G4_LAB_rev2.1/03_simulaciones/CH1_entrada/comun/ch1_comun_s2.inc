* S2 P4b; DC=0 AC=1 GND=2. Design unchanged from S1b, R1 midpoint.
* Real amplifier capacitance is retained AND contractual CIN_BUF=5p retained.
* See ACTA_S2 for this unresolved double-counting ambiguity.
.param RT1=549k RB=11k RS1=49.9k RS2=49.9k RBIAS=10Meg REQ=10Meg
.param RPROT=1k CAC=1.8n CBNC=3p CX1=2p CTAP=2p
.param COFF_RELE=1p RON_RELE=0.1 CSEL_PAR=3p COFF_SW=0.5p CIN_BUF=5p
.param CJO=1.9002p VJ_D=1.2722 M_D=0.35193
.param CJ_POL=CJO/(1+5/VJ_D)**M_D RS=RS1+RS2 RBP=RB*RBIAS/(RB+RBIAS)
.param C_SEL_EST=2*CJ_POL+CSEL_PAR+CIN_BUF+2*COFF_SW
.param CEQ=C_SEL_EST CX1_TOT=CX1+COFF_RELE+C_SEL_EST CS=RBIAS*CX1_TOT/RS
.param CT1=20p CTRIM_MIN=2p CTRIM_MAX=6p CTRIM_MED=(CTRIM_MIN+CTRIM_MAX)/2
.param CT2F=CT1-CTRIM_MED CTRIM=CTRIM_MED
.param CB=(CT1/2+COFF_RELE)*2*RT1/RBP-(C_SEL_EST+CTAP)
* Nexperia BAV199.txt .MODEL verbatim, without its orphan .ENDS.
.MODEL BAV199 D
+ IS=805.84E-18
+ N=1.0246
+ RS=50.000E-3
+ IKF=362.16E-6
+ CJO=1.9002E-12
+ M=.35193
+ VJ=1.2722
+ ISR=298.95E-15
+ BV=113.30
+ IBV=10
+ TT=1.0230E-6
* Generic rail TVS; RS derived from the two points in the S2 contract.
.param TVS_RS=(10.3-6.67)/(38.8-1m)
.model DTVS D(Is=1p N=1 Rs={TVS_RS} BV=6.67 IBV=1m)
.model DELIVERY D(Ron=1u Roff=1e18 Vfwd=0)
.subckt RAILS_S2 VP VN params: POWER=1 BLEED=0
VPI PP 0 5
RVP PP PDEL 0.5
DVP PDEL PREG DELIVERY
VNI NN 0 -5
RVN NDEL NN 0.5
DVN NREG NDEL DELIVERY
RLOADSWP PREG VP {if(POWER==1,1u,1e18)}
RLOADSWN VN NREG {if(POWER==1,1u,1e18)}
CbulkP VP 0 {if(POWER==1,10u,1u)}
CbulkN VN 0 {if(POWER==1,10u,1u)}
CdecP VP 0 100n
CdecN VN 0 100n
RloadP VP 0 {if(POWER==1,5/42m,1Meg)}
RloadN VN 0 {if(POWER==1,5/39m,1Meg)}
RbleedP VP 0 {if(POWER==1,1e18,if(BLEED==0,1e18,if(BLEED==1,10k,100)))}
RbleedN VN 0 {if(POWER==1,1e18,if(BLEED==0,1e18,if(BLEED==1,10k,100)))}
DtvsP 0 VP DTVS
DtvsN VN 0 DTVS
.ends RAILS_S2
* Wrapper pin order is consistently IN+ IN- V+ V- OUT.
.subckt BUFFER_OPA810 IP IM VP VN OUT
XAMP IP IM OUT VP VN OPA810
.ends BUFFER_OPA810
.subckt BUFFER_AD8065 IP IM VP VN OUT
XAMP IP IM VP VN OUT AD8065
.ends BUFFER_AD8065
* Exposed nodes and sense-source ports facilitate independent audit.
.subckt FRONT_S2 BNC BI VP VN M TAP RSM X1 EQ SEL B T2 params: POS=100 CPL=0
Rt1 BNC M {RT1}
Rt2 M TAP {RT1}
Ct1 BNC M {CT1}
Ct2fixed M TAP {CT2F}
Ct2trim M TAP {CTRIM}
Rb TAP 0 {RB}
Cb TAP 0 {CB}
Ctap TAP 0 {CTAP}
Rs1 BNC RSM {RS1}
Rs2 RSM X1 {RS2}
Cs BNC X1 {CS}
Cx1 X1 0 {CX1}
Cbnc BNC 0 {CBNC}
Rk1a100 TAP SEL {if(POS==100,RON_RELE,1e18)}
Rk1a1 X1 SEL {if(POS==1,RON_RELE,1e18)}
Ck1a1 X1 SEL {if(POS==100,COFF_RELE,0)}
Ck1a100 TAP SEL {if(POS==1,COFF_RELE,0)}
Rk1b X1 EQ {if(POS==100,RON_RELE,1e18)}
Ck1b X1 EQ {if(POS==1,COFF_RELE,0)}
Req EQ 0 {REQ}
Ceq EQ 0 {CEQ}
DHP SEL VP BAV199
DLP VN SEL BAV199
Csel SEL 0 {CSEL_PAR}
CAc SEL T2 {CAC}
RswDC B SEL {if(CPL==0,RON_RELE,1e18)}
RswAC B T2 {if(CPL==1,RON_RELE,1e18)}
RswGND B 0 {if(CPL==2,RON_RELE,1e18)}
CswDC B SEL {if(CPL==0,0,COFF_SW)}
CswAC B T2 {if(CPL==1,0,COFF_SW)}
CswGND B 0 {if(CPL==2,0,COFF_SW)}
Rbias B 0 {RBIAS}
Rprot B BI {RPROT}
Cin BI 0 {CIN_BUF}
.ends FRONT_S2
