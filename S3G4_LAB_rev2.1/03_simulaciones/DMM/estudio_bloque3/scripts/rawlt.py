"""Lector minimo de .raw binario de LTspice (tran float32/time double, AC complex double)."""
import numpy as np
def read(p):
    b=open(p,'rb').read(); enc='utf-16-le'
    i=b.find('Binary:\n'.encode(enc)); h=b[:i].decode(enc); data=b[i+len('Binary:\n'.encode(enc)):]
    lines=h.splitlines(); nv=int([l for l in lines if l.startswith('No. Variables')][0].split(':')[1])
    npt=int([l for l in lines if l.startswith('No. Points')][0].split(':')[1])
    k=lines.index('Variables:'); names=[l.split('\t')[2] for l in lines[k+1:k+1+nv]]
    flags=[l for l in lines if l.startswith('Flags')][0]
    if 'complex' in flags:
        a=np.frombuffer(data,dtype=np.complex128,count=npt*nv).reshape(npt,nv); return names,{n:a[:,j] for j,n in enumerate(names)}
    if 'double' in flags:
        a=np.frombuffer(data,dtype='<f8',count=npt*nv).reshape(npt,nv); out={n:a[:,j] for j,n in enumerate(names)}; out[names[0]]=np.abs(out[names[0]]); return names,out
    dt=np.dtype([('t','<f8')]+[(f'v{j}','<f4') for j in range(1,nv)])
    a=np.frombuffer(data,dtype=dt,count=npt); out={names[0]:np.abs(a['t'])}
    for j in range(1,nv): out[names[j]]=a[f'v{j}'].astype(float)
    return names,out
