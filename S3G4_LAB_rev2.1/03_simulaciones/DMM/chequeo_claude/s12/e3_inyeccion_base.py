"""prep() de e3_inyeccion.py, sin ejecución."""
"""E3: ¿por qué X1/X2 no llegan al valor? Punto de trabajo (.op) del deck E3 de Codex con el canal ya conmutado
(Xsel cerrado, X3 abierto) y variantes que aíslan el canal X0 (y X1) sobretensionado no seleccionado."""
import os,sys,re,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
SRC=r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\S12'
LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe';OUT=r'C:\s12a\e3';os.makedirs(OUT,exist_ok=True)
def prep(x,amp):
    t=open(os.path.join(SRC,f'a{amp}_cq0_g1_kzero_i0_m192_qE3_r4d9_{x}_s0d008_t23_ron60_u0.cir')).read()
    sel=int(x[1]);t=re.sub(rf'^Vctl{sel} .*$',f'Vctl{sel} ctl{sel} 0 0',t,flags=re.M)
    t=re.sub(r'^Vctl3 .*$','Vctl3 ctl3 0 4.9',t,flags=re.M)
    t=re.sub(r'^\.(tran|meas|options solver).*$','',t,flags=re.M).replace('.save V(out) V(mux) V(vin) I(Vp) I(Vn)','.op\n.save V(out) V(mux) V(x0) V(x1) V(x2) V(x0p) V(x1p) I(Rx0) I(Rx1)')
    return t
