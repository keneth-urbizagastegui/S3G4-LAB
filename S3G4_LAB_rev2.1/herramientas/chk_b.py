# -*- coding: utf-8 -*-
import sch
FS={"ref":11,"val":10,"net":10,"pin":9.5,"rail":10.5,"railsm":9,"portt":10.5,"tpt":9.5,"note":10.5,"grp-t":10.5,"pm":15}
T=[];W=[]
_t,_w=sch.Sch.text,sch.Sch.wire
def text(s,x,y,t,cls="lbl",a="start"):
    fs=FS.get(cls,10);w=len(str(t))*fs*0.6
    x0=x if a=="start" else (x-w/2 if a=="middle" else x-w)
    if str(t).strip() and cls!="pm":T.append((x0,y-fs*0.8,x0+w,y+fs*0.2,str(t)))
    _t(s,x,y,t,cls,a)
def wire(s,*p,cls="w"):
    for a,b in zip(p,p[1:]):W.append((a,b))
    _w(s,*p,cls=cls)
sch.Sch.text,sch.Sch.wire=text,wire
import draw_black_scope as draw_c
def hit(b,a,c):
    (x1,y1),(x2,y2)=a,c
    if x1==x2: return b[0]+1<x1<b[2]-1 and min(y1,y2)<b[3]-1 and max(y1,y2)>b[1]+1
    if y1==y2: return b[1]+1<y1<b[3]-1 and min(x1,x2)<b[2]-1 and max(x1,x2)>b[0]+1
    return False
for n,f in (("afe",draw_c.afe),):
    T.clear();W.clear();f();iss=[]
    for i,a in enumerate(T):
        for b in T[i+1:]:
            if a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]: iss.append(f"TXT {a[4]!r} x {b[4]!r}")
        for w in W:
            if hit(a,*w): iss.append(f"WIRE {a[4]!r} {w}")
        if a[2]>1300 or a[0]<0: iss.append(f"FUERA {a[4]!r}")
    print(n,len(iss));[print("  ",x) for x in iss]
