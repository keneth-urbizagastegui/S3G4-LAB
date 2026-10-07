"""Utilidades comunes: lector .raw (binario LTspice) y ejecucion de LTspice. Claude, 7 oct 2026."""
import subprocess, os, numpy as np
LT = r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe'

def read_raw(path):
    data = open(path, 'rb').read()
    key = 'Binary:\n'.encode('utf-16-le')
    i = data.find(key)
    hdr = data[:i].decode('utf-16-le'); body = data[i + len(key):]
    lines = hdr.splitlines()
    nv = int(next(l for l in lines if l.startswith('No. Variables')).split(':')[1])
    npnt = int(next(l for l in lines if l.startswith('No. Points')).split(':')[1])
    k = lines.index('Variables:')
    names = [lines[k + 1 + j].split('\t')[2] for j in range(nv)]
    # time es double (8 B); el resto float32 (4 B) salvo si se uso .options numdgt=15
    flags = next(l for l in lines if l.startswith('Flags')).lower()
    dbl = 'double' in flags or True
    # LTspice: con numdgt>=7 todo double. Se fuerza numdgt=15 en los decks.
    arr = np.frombuffer(body[:npnt * nv * 8], dtype='<f8').reshape(npnt, nv)
    d = {n.lower(): arr[:, j] for j, n in enumerate(names)}
    d['time'] = np.abs(d['time']) if 'time' in d else None
    return d

def run(cir):
    cir = os.path.abspath(cir)
    r = subprocess.run([LT, '-b', cir], capture_output=True, text=True, timeout=1800)
    return os.path.splitext(cir)[0] + '.raw', os.path.splitext(cir)[0] + '.log'

def integ(t, y):
    return float(np.trapezoid(y, t))
