"""Lector propio de .raw binario LTspice (real double) y metricas de auditoria S11.1.
Uso: python auditar_raw.py P3|P5 ruta.raw [t_apertura_s]
No usa el codigo de Codex."""
import sys, numpy as np

def read_raw(path):
    data = open(path, 'rb').read()
    i = data.find('Binary:\n'.encode('utf-16-le'))
    hdr = data[:i].decode('utf-16-le'); body = data[i + len('Binary:\n'.encode('utf-16-le')):]
    lines = hdr.splitlines()
    nv = int(next(l for l in lines if l.startswith('No. Variables')).split(':')[1])
    npnt = int(next(l for l in lines if l.startswith('No. Points')).split(':')[1])
    k = lines.index('Variables:')
    names = [lines[k + 1 + j].split('\t')[2] for j in range(nv)]
    arr = np.frombuffer(body[:npnt * nv * 8], dtype='<f8').reshape(npnt, nv)
    d = {n: arr[:, j] for j, n in enumerate(names)}
    d['time'] = np.abs(d['time'])
    return d

def integ(t, y, mask=None):
    if mask is not None: t, y = t[mask], y[mask]
    return float(np.trapezoid(y, t))

def at(d, name, t0):
    return float(np.interp(t0, d['time'], d[name]))

def p3(d, topen):
    t = d['time']; V = lambda n: d[f'V({n})']; I = lambda n: d[f'I({n})']
    print(f'puntos {len(t)}, t_final {t[-1]:.6f} s, paso max {np.max(np.diff(t))*1e6:.1f} us')
    vrel = np.abs(V('vin') - V('ptin'))
    early = t < 0.02
    print(f'rele: |V(vin,ptin)| max antes de 20 ms = {vrel[early].max():.3f} V (cerrado => ~I*0.1 ohm)')
    iptc = I('Vptc')
    if topen:
        print(f'I_PTC en la apertura real t={topen:.3f}s: {at(d,"I(Vptc)",topen):.3f} A; V red {at(d,"V(vin)",topen):.1f} V')
        late = t > topen + 1e-3
        print(f'tras apertura: |I_PTC| max {np.abs(iptc[late]).max():.3e} A, |V(vin,ptin)| max {vrel[late].max():.1f} V')
    for tt in (0.023, 0.103):
        if tt < t[-1]: print(f'  I_PTC(t={tt}) = {at(d,"I(Vptc)",tt):.4f} A')
    # ciclo en torno a 23 ms: corriente maxima en el semiciclo
    th = V('theta'); trip = t[np.argmax(th >= 1)] if (th >= 1).any() else None
    print(f'disparo theta>=1: {trip}')
    isrc = I('Vsense')
    print(f'fuente: I(Vsense) a t=1 ms {at(d,"I(Vsense)",1e-3)*1e3:.4f} mA (antes de la red relevante); a t=0: {isrc[0]*1e3:.4f} mA')
    ptv = V('n1') * I('Btvs'); pptc = (V('pt') - V('n1')) * iptc
    print(f'E_TVS total simulada {integ(t, ptv):.4f} J ; E_PTC {integ(t, pptc):.3f} J ; P_TVS pico {np.abs(ptv).max():.1f} W')
    # energia por semiciclo
    hc = np.floor(t * 120).astype(int); es = [integ(t, ptv, hc == k) for k in range(hc.max() + 1)]
    print(f'E_TVS semiciclo max {max(es):.4f} J (semiciclo {int(np.argmax(es))})')
    print(f'pico I_PTC {np.abs(iptc).max():.3f} A ; pico |V(n1)| {np.abs(V("n1")).max():.2f} V')
    irs = I('Rs'); print(f'pico |I(Rs)| {np.abs(irs).max()*1e3:.2f} mA ; pico I(D2p) {I("D2p").max()*1e3:.2f} mA ; pico I(D2n) {I("D2n").max()*1e3:.2f} mA')
    span = V('rp') - V('rn')
    j = np.argmax(span)
    print(f'rp max {V("rp").max():.3f} V, rn min {V("rn").min():.3f} V, span max {span.max():.3f} V a t={t[j]*1e3:.2f} ms')
    # corriente que entra al riel + desde N2: por D2p y por el diodo de cuerpo (Rs - D2p + D2n - Bsource ~)
    ibody_est = irs - I('D2p') + I('D2n') - isrc
    print(f'corriente estimada por el diodo de cuerpo BSS84 (I_Rs - I_D2p + I_D2n - I_fuente, desprecia Xh6/C): pico {ibody_est.max()*1e3:.2f} mA')
    vds = V('n2') - V('ms')
    print(f'VDS BSS84 = V(n2)-V(msource): min {vds.min():.2f} V, max {vds.max():.2f} V')
    # instantes de pico de inyeccion vs span
    k = np.argmax(irs); print(f'  en pico I(Rs) t={t[k]*1e3:.2f} ms: V(n1)={V("n1")[k]:.2f}, V(n2)={V("n2")[k]:.2f}, rp={V("rp")[k]:.2f}, rn={V("rn")[k]:.2f}')

def p5(d):
    t = d['time']; I = lambda n: d[f'I({n})']; V = lambda n: d[f'V({n})']
    i1 = I('Dbr1'); i2 = I('Dbr2'); ish = I('Rshunt')
    m = t <= 8.3e-3
    print(f't_final {t[-1]*1e3:.3f} ms; pico I(Dbr1) {i1.max():.2f} A, pico I(Dbr2) {i2.max():.2f} A; pico I(Rshunt) {np.abs(ish).max():.1f} A')
    print(f'I2t Dbr1 hasta 8.3 ms {integ(t, i1**2, m):.2f} A2s; 10 ms {integ(t, i1**2):.2f}; I2t derivador {integ(t, ish**2):.2f} A2s; E derivador {0.1*integ(t, ish**2):.3f} J')
    itot = ish + i1 + i2  # rama shunt + dos ramas del puente (cada rama 2 diodos en serie)
    print(f'corriente total de falta pico {np.abs(itot).max():.1f} A; I2t total 10 ms {integ(t, itot**2):.1f} A2s')
    for tm in (0.2e-3, 0.5e-3, 1e-3):
        print(f'  I2t Dbr1 en los primeros {tm*1e3:.1f} ms: {integ(t, i1**2, t <= tm):.3f} A2s; I2t total {integ(t, itot**2, t <= tm):.2f} A2s')
    print(f'pico V(shunt) {np.abs(V("shunt")).max():.2f} V')

if __name__ == '__main__':
    d = read_raw(sys.argv[2])
    p3(d, float(sys.argv[3]) if len(sys.argv) > 3 else None) if sys.argv[1] == 'P3' else p5(d)
