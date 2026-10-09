import gen_p43 as g
from concurrent.futures import ThreadPoolExecutor
rk = {"1mA":499,"100uA":4990,"10uA":49900,"1uA":499e3,"0.2uA":2.499e6}
rxs = {"1mA":2000,"100uA":20e3,"10uA":200e3,"1uA":2e6,"0.2uA":20e6}
opts = {"A sin comp":(110,""),"B 10k+330p":(10e3,"Cc og sni 330p"),"C 10k+100p":(10e3,"Cc og sni 100p"),"D 1k+1n":(1e3,"Cc og sni 1n"),"E 10k+1n":(10e3,"Cc og sni 1n")}
def job(a):
    on,k,vto = a; rsn,comp = opts[on]
    nm = ("c_"+on+"_"+k+"_"+str(abs(vto))).replace(" ","_").replace("+","").replace(".","p")
    t = g.deck(nm,"MOS",rk[k],rxs[k],rs=500,r1=1000,vto=vto,comp=comp,rsn=rsn)
    p = g.pm(nm,t); return on,k,vto,p
jobs=[(on,k,v) for on in opts for k in ("1mA","100uA","10uA","0.2uA") for v in (-2.0,-0.8)]
with ThreadPoolExecutor(4) as ex:
    for on,k,vto,p in ex.map(job,jobs):
        print(on,k,vto,"fc=%s PM=%s"%(("%.3g"%p["fc"]) if p["fc"] else None,("%.0f"%p["pm"]) if p["pm"] else None))
