* S4 contract, 2026-10-03. Previous stages remain immutable.
.include "ch1_comun_s3b.inc"
* Verbatim from chequeo_claude/s3b/y_b3_g_s00_pos1_tap0_cpldc_nomi_bipolar_t25.cir.
* LTspice standard.dio, Rohm model; design part is Nexperia BAV99 (C2500).
.model BAV99HY D(Is=10.825E-15 N=0.9242 Rs=896.25E-3 Ikf=1.7426E-6 Cjo=640.32E-15 M=0.0662 Vj=0.6504 Isr=9.7471E-9 Bv=100 Tt=4.5428E-9 Iave=0.215 Vpk=100 mfg=Rohm type=Silicon)
.subckt PROTECT_BAV99 COMMON IP IM params: R_SER=470
RSER COMMON IP {R_SER}
DP IP IM BAV99HY
DN IM IP BAV99HY
.ends PROTECT_BAV99
.param R_IN_S4=10k R_F_S4=10k R_OFF_S4=8.06k
.param RT_MID=10k RB_MID=5.23k VREF_NOM=2.5 VDDA_NOM=3.3
.param A_IN=R_F_S4/R_IN_S4 A_OFF=R_F_S4/R_OFF_S4 NG_S4=1+A_IN+A_OFF
.param VMID_IDEAL=VREF_NOM*RB_MID/(RT_MID+RB_MID)
.param CENTER_IDEAL=NG_S4*VMID_IDEAL-A_OFF*VREF_NOM/2
.param R_ADC_S4=68 C_ADC_S4=470p C_SH_S4=5p C_SUM_S4=1p
* SUPPOSITION required by S4 2.3, not an added physical part.
.model DESD_OPA836 D(Is=1e-15 N=1 Rs=10)
* Order matches TI's SIX-node OPA836: IN+ IN- OUT VCC VEE Vnot_pd.
.subckt OPA836_S4_ESD IP IM OUT VP VN PD
XAMP IP IM OUT VP VN PD OPA836
DP IP IM DESD_OPA836
DN IM IP DESD_OPA836
.ends OPA836_S4_ESD
.subckt OPA836_S4_BARE IP IM OUT VP VN PD
XAMP IP IM OUT VP VN PD OPA836
.ends OPA836_S4_BARE
