* S3 extends S2b verbatim, no retuning. Include resolved relative to this file.
.include "ch1_comun_s2b.inc"
.param RL1=499 RL2=249 RL3=150 RL4=49.9 RL5=24.9 RL6=24.9
.param RLTOT=RL1+RL2+RL3+RL4+RL5+RL6
.param TAP0=1 TAP1=(RL2+RL3+RL4+RL5+RL6)/RLTOT
.param TAP2=(RL3+RL4+RL5+RL6)/RLTOT TAP3=(RL4+RL5+RL6)/RLTOT
.param TAP4=(RL5+RL6)/RLTOT TAP5=RL6/RLTOT
.param RF1=1k RG1=249 RF2=2.26k RG2=249 GAIN1=1+RF1/RG1 GAIN2=1+RF2/RG2
.param SWITCH_EDGE=30n BBM=20n CTRL_TAU=SWITCH_EDGE/ln(9)
.subckt LADDER_S3 IN Y1 Y2 Y3 Y4 Y5
RL1 IN Y1 {RL1}
RL2 Y1 Y2 {RL2}
RL3 Y2 Y3 {RL3}
RL4 Y3 Y4 {RL4}
RL5 Y4 Y5 {RL5}
RL6 Y5 0 {RL6}
.ends LADDER_S3
* Nexperia SWI1: control, Y, Z, VEE, VCC, GND. Active LOW.
.subckt MUX_S3 Y0 Y1 Y2 Y3 Y4 Y5 Y6 Y7 Z A0 A1 A2 VP VN params: DYNAMIC=0
* Behavioral binary decoder. Every change opens old immediately; a new
* channel closes only after BBM of stable code. RC gives 30ns 10-90% edges.
Bcode CODE 0 V=if(V(A0)>2.5,1,0)+2*if(V(A1)>2.5,1,0)+4*if(V(A2)>2.5,1,0)
B0 D0 0 V=if(V(CODE)==0,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==0,0,5)),5)
B1 D1 0 V=if(V(CODE)==1,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==1,0,5)),5)
B2 D2 0 V=if(V(CODE)==2,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==2,0,5)),5)
B3 D3 0 V=if(V(CODE)==3,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==3,0,5)),5)
B4 D4 0 V=if(V(CODE)==4,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==4,0,5)),5)
B5 D5 0 V=if(V(CODE)==5,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==5,0,5)),5)
B6 D6 0 V=if(V(CODE)==6,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==6,0,5)),5)
B7 D7 0 V=if(V(CODE)==7,if(DYNAMIC==0,0,if(delay(V(CODE),BBM)==7,0,5)),5)
R0 D0 C0 1
R1 D1 C1 1
R2 D2 C2 1
R3 D3 C3 1
R4 D4 C4 1
R5 D5 C5 1
R6 D6 C6 1
R7 D7 C7 1
C0 C0 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C1 C1 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C2 C2 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C3 C3 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C4 C4 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C5 C5 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C6 C6 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
C7 C7 0 {if(DYNAMIC==1,CTRL_TAU,1f)}
X0 C0 Y0 Z VN VP 0 SWI1
X1 C1 Y1 Z VN VP 0 SWI1
X2 C2 Y2 Z VN VP 0 SWI1
X3 C3 Y3 Z VN VP 0 SWI1
X4 C4 Y4 Z VN VP 0 SWI1
X5 C5 Y5 Z VN VP 0 SWI1
X6 C6 Y6 Z VN VP 0 SWI1
X7 C7 Y7 Z VN VP 0 SWI1
.ends MUX_S3
.subckt AD8039_S3 IP IM VP VN OUT
XAMP IP IM VP VN OUT AD8038
.ends AD8039_S3
