"""Auditoria Claude S11.2: recalcula desde el .raw (lector propio) un caso Q3, Q5, Q6 y Q1.
Uso: python recalcular_raw.py <carpeta con los .raw del smoke reejecutado (C:\\s112\\...\\S11_2)>
No usa el codigo de Codex."""
import sys, glob, os, numpy as np

def read_raw(path):
    data = open(path, 'rb').read()
    i = data.find('Binary:\n'.encode('utf-16-le'))
    hdr = data[:i].decode('utf-16-le'); body = data[i + len('Binary:\n'.encode('utf-16-le')):]
    lines = hdr.splitlines()
    nv = int(next(l for l in lines if l.startswith('No. Variables')).split(':')[1])
    npnt = int(next(l for l in lines if l.startswith('No. Points')).split(':')[1])
    k = lines.index('Variables:')
    names = [lines[k + 1 + j].split('\t')[2].lower() for j in range(nv)]
    arr = np.frombuffer(body[:npnt * nv * 8], dtype='<f8').reshape(npnt, nv)
    d = {n: arr[:, j].copy() for j, n in enumerate(names)}
    d['time'] = np.abs(d['time'])
    return d

def get(d, n):
    return d.get(n.lower(), np.zeros_like(d['time']))

def find(folder, pref):
    return [p for p in glob.glob(os.path.join(folder, pref + '*.raw')) if not p.endswith('.op.raw')][0]

def q3(d, ta=0.0, stop=1.0):
    t = d['time']; V = lambda n: get(d, f'v({n})'); I = lambda n: get(d, f'i({n})')
    print(f'[Q3] puntos {len(t)} t_final {t[-1]:.4f}s')
    print(f'  rele: |V(vin)-V(ptin)| max {np.max(np.abs(V("vin")-V("ptin"))):.4e} V (cerrado si ~I*0.1)')
    i1 = I('vlf1'); print(f'  |I(Vlf1)| pico {np.max(np.abs(i1))*1e3:.4f} mA; Vin pico {np.max(V("vin")):.2f} V')
    for k, (a, b, g) in enumerate((('ld1', 's1', 's2'), ('ld2', 's2', 's1')), 1):
        p = (V(a) - V(b)) * (i1 if k == 1 else I('vlf2'))
        m = t >= stop - 5 / 60
        pm = np.trapezoid(p[m], t[m]) / (t[m][-1] - t[m][0])
        e1 = np.trapezoid(p, t); e10 = e1 + pm * (10 - stop)
        print(f'  FET{k}: Pmed ult.5 ciclos {pm:.6f} W, E1s {e1:.6f} J, E10 {e10:.6f} J, '
              f'Tj(RthJA250, P media 10 s) {ta + 250 * e10 / 10:.3f} C, VDS max {np.max(np.abs(V(a)-V(b))):.2f} V, '
              f'VGS min {np.min(V(g)-V(b)):.3f} V')
    vpk = 230 * 2 ** .5; il = np.max(np.abs(i1))
    print(f'  a mano: Vpk*Ilim/pi = {vpk*il/np.pi:.6f} W por FET')
    print(f'  span max {np.max(V("rp")-V("rn")):.3f} V; rp max {np.max(V("rp")):.3f}; rn min {np.min(V("rn")):.3f}')
    for n in ('d2p', 'd2n', 'dzp', 'dzn', 'dblk', 'rs'):
        y = I(n); print(f'  I({n}) max {y.max()*1e3:.4f} mA min {y.min()*1e3:.4f} mA')

def q5(d):
    t = d['time']; V = lambda n: get(d, f'v({n})'); I = lambda n: get(d, f'i({n})')
    ifs = I('vfs'); q = np.concatenate([[0], np.cumsum(0.5 * (ifs[1:]**2 + ifs[:-1]**2) * np.diff(t))])
    j = np.argmax(q >= 6.7) if (q >= 6.7).any() else None
    print(f'[Q5] pico |I_fus| {np.max(np.abs(ifs)):.3f} A; I2t fus total {q[-1]:.4f} A2s; '
          f'cruce 6.7 A2s en t={t[j]*1e6 if j is not None else float("nan"):.2f} us; V(qfus) final {V("qfus")[-1]:.4f}')
    if j is not None:
        late = t > t[j] + 2e-6; print(f'  |I_fus| max tras apertura+2us {np.max(np.abs(ifs[late])):.3e} A')
    for n in ('dbr1', 'dbr2', 'dbr3', 'dbr4'):
        y = I(n); print(f'  {n}: pico {np.max(np.abs(y)):.3f} A, I2t {np.trapezoid(y*y, t):.4f} A2s')
    print(f'  pico V(bin) {np.max(V("bin")):.4f} V; E Rshunt {np.trapezoid(V("shunt")*I("rshunt"), t):.5f} J')
    tc = t[j] if j is not None else t[-1]
    print(f'  duracion de conduccion hasta apertura {tc*1e3:.4f} ms -> I2t con pulso equivalente; '
          f'Ipk^2*tc/2 aprox {np.max(np.abs(ifs))**2*tc/2:.3f} A2s')

def q6(d):
    t = d['time']; V = lambda n: get(d, f'v({n})'); I = lambda n: get(d, f'i({n})')
    vds1 = V('ld1') - V('s1'); vgs1 = V('s2') - V('s1'); vds2 = V('ld2') - V('s2'); vgs2 = V('s1') - V('s2')
    for nm, y in (('VDS1', vds1), ('VGS1', vgs1), ('VDS2', vds2), ('VGS2', vgs2)):
        j = np.argmax(np.abs(y)); print(f'[Q6] |{nm}| max {abs(y[j]):.2f} V en t={t[j]*1e9:.1f} ns')
    j = np.argmax(np.abs(vds1))
    ilim = (V('s1') - V('s2')) / 700
    print(f'  en ese instante: I(Vlf1) {I("vlf1")[j]:.4f} A, I_Rlim {ilim[j]:.4f} A, I(Vlf2) {I("vlf2")[j]:.4f} A, '
          f'I(Rs) {I("rs")[j]:.4f} A, V(vin) {V("vin")[j]:.1f}, V(ptin) {V("ptin")[j]:.1f}, V(n1) {V("n1")[j]:.2f}, V(n2) {V("n2")[j]:.2f}')
    for n in ('vlf1', 'rs', 'd2p', 'd2n', 'rprot1', 'rdiv1', 'rc1', 'dzp', 'dzn'):
        y = I(n); print(f'  I({n}) pico {np.max(np.abs(y)):.4f} A, carga {np.trapezoid(np.abs(y), t)*1e9:.2f} nC')
    for k in [k for k in d if k.startswith('i(xh') or k.startswith('i(xop') or k.startswith('i(xtlv')]:
        y = d[k]
        if np.max(np.abs(y)) > 1e-3: print(f'  {k} pico {np.max(np.abs(y))*1e3:.1f} mA')
    print(f'  span max {np.max(V("rp")-V("rn")):.3f} V; V(x0) max/min {V("x0").max():.3f}/{V("x0").min():.3f}; '
          f'V(x1) {V("x1").max():.3f}/{V("x1").min():.3f}; rp {V("rp").max():.3f} rn {V("rn").min():.3f}')

def q1(d):
    t = d['time']; V = lambda n: get(d, f'v({n})'); I = lambda n: get(d, f'i({n})')
    j = len(t) - 1
    print(f'[Q1] final: V(vin) {V("vin")[j]:.4f}, V(ptin) {V("ptin")[j]:.4f}, V(n1) {V("n1")[j]:.4f}, '
          f'V(n2) {V("n2")[j]:.4f}, V(bp) {V("bp")[j]:.4f}, V(msource) {V("msource")[j]:.4f}, rp {V("rp")[j]:.4f}')
    print(f'  I(Vlf1) {I("vlf1")[j]*1e3:.4f} mA, I(Vsense) {I("vsense")[j]*1e3:.4f} mA')
    print(f'  caidas: Dblk {V("bp")[j]-V("n2")[j]:.4f} V; Rs {V("n2")[j]-V("n1")[j]:.4f} V; par O2 (n1->ptin) '
          f'{V("n1")[j]-V("ptin")[j]:.4f} V [FET2 {V("n1")[j]-V("s2")[j]:.4f}, Rlim {V("s2")[j]-V("s1")[j]:.4f}, FET1 {V("s1")[j]-V("ld1")[j]:.4f}]; '
          f'cabeza fuente rp-msource {V("rp")[j]-V("msource")[j]:.4f}; BSS84 {V("msource")[j]-V("bp")[j]:.4f}')
    print(f'  V(vin) max en el barrido {V("vin").max():.4f} V')

if __name__ == '__main__':
    f = sys.argv[1]
    q3(read_raw(find(f, 'Q3_')), ta=0.0)
    q5(read_raw(find(f, 'Q5_')))
    q6(read_raw(find(f, 'Q6_')))
    q1(read_raw(find(f, 'Q1_')))

def q1_compliance(d, vc):
    """Cadena de caidas en el instante en que V(vin)=vc (compliancia a 99 %)."""
    t = d['time']; V = lambda n: get(d, f'v({n})'); I = lambda n: get(d, f'i({n})')
    j = int(np.argmin(np.abs(V('vin') - vc)))
    f = lambda n: V(n)[j]
    print(f'[Q1 a V(vin)={f("vin"):.4f}] I(Vlf1) {I("vlf1")[j]*1e3:.4f} mA; rp {f("rp"):.4f}')
    print(f'  rp-msource {f("rp")-f("msource"):.4f}; BSS84 msource-bp {f("msource")-f("bp"):.4f}; Dblk {f("bp")-f("n2"):.4f}; '
          f'Rs {f("n2")-f("n1"):.4f}; FET2 n1-s2 {f("n1")-f("s2"):.4f} (VGS2 {f("s1")-f("s2"):.4f}); '
          f'Rlim s2-s1 {f("s2")-f("s1"):.4f}; FET1 s1-ptin {f("s1")-f("ptin"):.4f} (VGS1 {f("s2")-f("s1"):.4f}); rele {f("ptin")-f("vin"):.5f}')
