"""Lector propio de .raw de LTspice (binario real/complejo, double o float+double tiempo)."""
import numpy as np
def leer(path):
    b=open(path,'rb').read();i=b.find('Binary:\n'.encode('utf-16-le'))
    h=b[:i].decode('utf-16-le');data=b[i+len('Binary:\n'.encode('utf-16-le')):]
    n=int(h.split('No. Variables:')[1].split()[0]);p=int(h.split('No. Points:')[1].split()[0])
    names=[l.split('\t')[2] for l in h.split('Variables:\n')[1].splitlines() if l.startswith('\t')]
    flags=h.split('Flags:')[1].splitlines()[0]
    if 'complex' in flags:a=np.frombuffer(data,np.complex128,n*p).reshape(p,n)
    elif 'double' in flags:a=np.frombuffer(data,np.float64,n*p).reshape(p,n)
    else:
        dt=np.dtype([('t','<f8')]+[(f'v{k}','<f4') for k in range(1,n)]);r=np.frombuffer(data,dt,p)
        a=np.column_stack([r['t']]+[r[f'v{k}'].astype(float) for k in range(1,n)])
    if 'time' in names[0].lower() or names[0]=='time':a=a.copy();a[:,0]=np.abs(a[:,0].real) if not np.iscomplexobj(a) else a[:,0]
    return {nm:a[:,k] for k,nm in enumerate(names)}
