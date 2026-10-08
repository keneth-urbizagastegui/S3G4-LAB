"""E3, remedio candidato: pinzas de X0/X1 a carriles ±Vcl por debajo de los ±4.9 V del 4051, con Schottky genérica
(supuesto tipo BAT54: Is=2e-7 N=1.05 Rs=1; no es ficha local). .op con el canal ya conmutado."""
import os,sys,re,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
from e3_inyeccion_base import prep
LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe';OUT=r'C:\s12a\e3s';os.makedirs(OUT,exist_ok=True)
jobs=[]
for x,amp,exp in (('x1',20,20*1.01/10.01),('x2',50,50*.1/10.01)):
    for vcl in (4.0,4.3):
        t=prep(x,amp)
        for a,b in (('D0p x0p vp','D0p x0p vclp'),('D0n vn x0p','D0n vcln x0p'),('D1p x1p vp','D1p x1p vclp'),('D1n vn x1p','D1n vcln x1p')):t=t.replace(a+' BAV199',b+' SCH')
        t=t.replace('\n.op\n',f'\n.model SCH D(Is=2e-7 N=1.05 Rs=1 Cjo=10p)\nVclp vclp 0 {vcl}\nVcln vcln 0 {-vcl}\n.op\n')
        jobs.append((x,vcl,exp,t))
def go(j):
    x,vcl,exp,t=j;p=os.path.join(OUT,f'{x}_vcl{str(vcl).replace(".","d")}.cir');open(p,'w').write(t)
    subprocess.run([LT,'-b',p],timeout=600,capture_output=True);r=leer(p[:-4]+'.raw');return x,vcl,exp,{k:float(r[k][0].real) for k in r}
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(4) as ex:
    for x,vcl,exp,d in ex.map(go,jobs):
        print(f'{x} Vcl=±{vcl}: Vout={d["V(out)"]:.6f} (esperado {exp:.6f}, error {1e3*(d["V(out)"]-exp):+.3f} mV); V(x0)={d["V(x0)"]:.3f} V(x1)={d["V(x1)"]:.3f}')
