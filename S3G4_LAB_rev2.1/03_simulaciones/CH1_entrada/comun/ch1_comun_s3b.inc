* S3b: include immutable S3, add only R_SER and antiparallel diodes.
.include "ch1_comun_s3.inc"
* Verbatim BAT54 from installed LTspice standard.dio, Vishay metadata.
.model BAT54 D(Is=.1u Rs=2.2 N=1 Cjo=12p M=.3 Eg=.69 Xti=2 Iave=300m Vpk=30 mfg=Vishay type=Schottky)
.subckt PROTECT_BAT54 COMMON IP IM params: R_SER=470
RSER COMMON IP {R_SER}
DP IP IM BAT54
DN IM IP BAT54
.ends PROTECT_BAT54
.subckt PROTECT_BAV199 COMMON IP IM params: R_SER=470
RSER COMMON IP {R_SER}
DP IP IM BAV199
DN IM IP BAV199
.ends PROTECT_BAV199
