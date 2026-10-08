"""E3 X2: ¿la fuga del canal X1 apagado depende de pasar VCC o es la Roff del modelo SWI1?
Barrido de Vin con X0 aislado; y pinza Schottky ±4.3 V solo en X0 (X1 con BAV199 a ±4.9 como en el bloque 1)."""
import os,sys,re,subprocess
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
from e3_inyeccion_base import prep
LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe';OUT=r'C:\s12a\e3u';os.makedirs(OUT,exist_ok=True)
jobs=[]
for vin in (20,30,40,45,48,50):
    t=prep('x2',50).replace('Vin vin 0 50',f'Vin vin 0 {vin}').replace('X0 ctl0 x0 mux','X0 ctl0 0 mux');jobs.append((f'X0 aislado Vin={vin}',vin,t))
for vin in (45,50):
    t=prep('x2',50).replace('Vin vin 0 50',f'Vin vin 0 {vin}').replace('D0p x0p vp BAV199','D0p x0p vclp SCH').replace('D0n vn x0p BAV199','D0n vcln x0p SCH')
    t=t.replace('\n.op\n','\n.model SCH D(Is=2e-7 N=1.05 Rs=1 Cjo=10p)\nVclp vclp 0 4.3\nVcln vcln 0 -4.3\n.op\n');jobs.append((f'Schottky X0 a ±4.3 V, Vin={vin}',vin,t))
def go(j):
    n,vin,t=j;p=os.path.join(OUT,re.sub(r'\W+','_',n)+'.cir');open(p,'w').write(t)
    subprocess.run([LT,'-b',p],timeout=600,capture_output=True);r=leer(p[:-4]+'.raw');return n,vin,{k:float(r[k][0].real) for k in r}
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex:
    for n,vin,d in ex.map(go,jobs):
        exp=vin*.1/10.01;print(f'{n}: Vout={d["V(out)"]:.6f} esperado {exp:.6f} error {1e3*(d["V(out)"]-exp):+.3f} mV ({(d["V(out)"]-exp)/1e-5:+.0f} cuentas de 10 uV en X2); V(x0)={d["V(x0)"]:.3f} V(x1)={d["V(x1)"]:.3f}')
