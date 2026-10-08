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
V=[]
for x,amp,exp in (('x1',20,20*1.01/10.01),('x2',50,50*.1/10.01)):
    b=prep(x,amp)
    V+=[(x,'base',b,exp),
        (x,'X0 aislado (Y de X0 a 0 V)',b.replace('X0 ctl0 x0 mux','X0 ctl0 0 mux'),exp),
        (x,'X0 y X1 aislados',b.replace('X0 ctl0 x0 mux','X0 ctl0 0 mux').replace('X1 ctl1 x1 mux','X1 ctl1 0 mux') if x=='x2' else None,exp),
        (x,'pinza X0/X1 a +4.4 V (0.5 V bajo VCC)',b.replace('D0p x0p vp','D0p x0p vcl').replace('D1p x1p vp','D1p x1p vcl').replace('\n.op\n','\nVcl vcl 0 4.4\n.op\n'),exp)]
def go(v):
    x,n,t,exp=v
    if t is None:return None
    p=os.path.join(OUT,(x+'_'+re.sub(r'\W+','_',n))[:40]+'.cir');open(p,'w').write(t)
    subprocess.run([LT,'-b',p],timeout=600,capture_output=True);r=leer(p[:-4]+'.raw')
    return x,n,exp,{k:float(r[k][0].real) for k in r if k.startswith(('V(','I('))}
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex:res=[z for z in ex.map(go,V) if z]
for x,n,exp,d in res:
    lsb=2/20000 if x=='x1' else 0.5/50000*10  # ver acta: cuenta en X; se informa error en V
    print(f'{x} {n}: Vout={d["V(out)"]:.5f} V (esperado {exp:.5f}); V(x0)={d["V(x0)"]:.3f} V(x1)={d["V(x1)"]:.3f} V(mux)={d["V(mux)"]:.4f}; I(Rx0)={d["I(Rx0)"]*1e6:.2f} uA I(Rx1)={d["I(Rx1)"]*1e6:.3f} uA')
