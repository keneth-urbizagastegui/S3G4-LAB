"""E5: margen de fase con un Cff de out a IN- (inv), sobre los decks de lazo de Codex (copias en C:/s12a/e5).
También mide la ganancia cerrada x10.1 a 20 kHz con Cff (deck AC E1 nominal)."""
import os,sys,re,subprocess,itertools,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
SRC=r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\S12'
LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe';OUT=r'C:\s12a\e5';os.makedirs(OUT,exist_ok=True)
def run(text,name):
    p=os.path.join(OUT,name+'.cir');open(p,'w').write(text)
    subprocess.run([LT,'-b',p],timeout=600,capture_output=True);return leer(p[:-4]+'.raw')
def pm(r):
    f=r['frequency'].real;T=-r['V(inv)']/r['V(test)'];m=np.abs(T);i=np.where((m[:-1]>=1)&(m[1:]<1))[0][0]
    ph=np.unwrap(np.angle(T));p=np.interp(0,-np.log(m[i:i+2]),ph[i:i+2]);fc=np.exp(np.interp(0,-np.log(m[i:i+2]),np.log(f[i:i+2])))
    return 180+np.degrees(p),fc
jobs=[]
for g,ron,cff,cl in itertools.product(('g1','g10d1'),(60,400,520),(0,1,2,3.3,4.7),(10,47)):
    base=open(os.path.join(SRC,f'a0d1_{g}_kloop_i0_m192_qE5_r4d9_x0_s0d006_t23_ron400_u0.cir')).read()
    t=re.sub(r'RTMUX=\S+',f'RTMUX={ron}',base).replace('Cload out vcm 10p',f'Cload out vcm {cl}p')
    t=re.sub(r'^\.meas.*$','',t,flags=re.M).replace('.end',f'Cff out inv {cff}p\n.end')
    jobs.append(((g,ron,cff,cl),t))
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex:
    res=list(ex.map(lambda j:(j[0],pm(run(j[1],'pm_'+'_'.join(map(str,j[0])).replace('.','d')))),jobs))
print('ganancia RTMUX Cff(pF) Cload(pF) -> PM(deg) fc(MHz)')
for k,(p,fc) in res:print(*k,f'{p:.2f}',f'{fc/1e6:.2f}')
# ganancia cerrada x10.1 a 20 kHz con Cff (deck E1 nominal)
ac=[x for x in os.listdir(SRC) if 'g10d1_kac' in x and x.endswith('.cir') and 'qE1' in x][0]
for cff in (0,2,3.3):
    t=re.sub(r'^\.meas.*$','',open(os.path.join(SRC,ac)).read(),flags=re.M).replace('.end',f'Cff out inv {cff}p\n.end')
    r=run(t,f'ac_cff{str(cff).replace(".","d")}');f=r['frequency'].real;v=np.abs(r['V(out)'])
    print('x10.1 AC Cff',cff,'pF: |G| 1kHz',np.interp(1e3,f,v),'20kHz',np.interp(2e4,f,v))
