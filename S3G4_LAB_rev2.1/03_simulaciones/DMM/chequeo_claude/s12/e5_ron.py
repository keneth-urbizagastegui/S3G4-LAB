"""E5 x1: PM frente a RTMUX y a la C de IN- (Ctm), con Cload 10 pF."""
import os,sys,re,subprocess,itertools,numpy as np
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)));from leer_raw import leer
SRC=r'C:\Users\Keneth\Desktop\S3G4 LAB\S3G4_LAB_rev2.1\03_simulaciones\DMM\S12'
LT=r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe';OUT=r'C:\s12a\e5r';os.makedirs(OUT,exist_ok=True)
def run(text,name):
    p=os.path.join(OUT,name+'.cir');open(p,'w').write(text);subprocess.run([LT,'-b',p],timeout=600,capture_output=True);return leer(p[:-4]+'.raw')
def pm(r):
    f=r['frequency'].real;T=-r['V(inv)']/r['V(test)'];m=np.abs(T);i=np.where((m[:-1]>=1)&(m[1:]<1))[0][0]
    ph=np.unwrap(np.angle(T));return 180+np.degrees(np.interp(0,-np.log(m[i:i+2]),ph[i:i+2]))
base=open(os.path.join(SRC,'a0d1_g1_kloop_i0_m192_qE5_r4d9_x0_s0d006_t23_ron400_u0.cir')).read()
base=re.sub(r'^\.meas.*$','',base,flags=re.M)
jobs=[(ron,ct) for ron in (60,100,150,200,250,300,400) for ct in (5,10,15)]
def one(j):
    ron,ct=j;t=re.sub(r'RTMUX=\S+',f'RTMUX={ron}',base).replace('Ctm inv 0 10p',f'Ctm inv 0 {ct}p')
    return j,pm(run(t,f'r{ron}_c{ct}'))
from concurrent.futures import ThreadPoolExecutor
with ThreadPoolExecutor(8) as ex:res=list(ex.map(one,jobs))
print('RTMUX(ohm) Ctm(pF) PM(deg)  [ruta = RTMUX+1 ohm]')
for (ron,ct),p in res:print(ron,ct,f'{p:.2f}')
