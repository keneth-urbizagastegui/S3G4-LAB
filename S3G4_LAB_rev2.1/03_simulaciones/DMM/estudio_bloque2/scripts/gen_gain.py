import subprocess, re, os
LT = r'C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe'
HEAD = '''* ganancia x1/x10, modo {m}
.include "C:/Users/Keneth/Desktop/S3G4 LAB/Simulation_LTSpice/models/OPA2188/OPAx188.LIB"
Vcc vcc 0 4.9
Vee vee 0 -4.9
Vin in 0 {vin}
XU1 in inv vcc vee out OPAx188
'''
def net(m, leak, vin, ron=100):
    s = HEAD.format(m=m, vin=vin)
    if m == 'H_x1':      # llave abierta en Rg; la fuga de la llave sale del nodo g a masa (rail negativo)
        s += f'Rf out inv 900k\nRg inv g 100k\nIlk g 0 {leak}\n'
    elif m == 'H_x10':   # llave cerrada: Ron en serie con Rg
        s += f'Rf out inv 900k\nRg inv g 100k\nRon g 0 {ron}\nIlk inv 0 0\n'
    elif m == 'S_x1':    # escalera siempre conectada; inv a la salida por la llave A (Ron); la fuga de la llave B (abierta) entra a la toma
        s += f'Rf out tap 900k\nRg tap 0 100k\nSA inv out {ron}\nIlk tap 0 {leak}\n'
    elif m == 'S_x10':   # inv a la toma por la llave B; la llave A abierta fuga desde inv
        s += f'Rf out tap 900k\nRg tap 0 100k\nSB inv tap {ron}\nIlk inv 0 {leak}\n'
    elif m == 'S2_x10':  # escalera 10 veces menor (90k/10k)
        s += f'Rf out tap 90k\nRg tap 0 10k\nSB inv tap {ron}\nIlk inv 0 {leak}\n'
    s = s.replace('SA inv out', 'RA inv out').replace('SB inv tap', 'RB inv tap')
    s += '.op\n.meas op vo find v(out) at 0\n.end\n'
    return s
res = {}
for m in ('H_x1', 'H_x10', 'S_x1', 'S_x10', 'S2_x10'):
    for leak in (0, 1e-9):
        for vin in (0.0, 0.2 if m.endswith('x10') else 1.0):
            fn = f'g_{m}_{int(leak*1e9)}_{vin}.cir'.replace('.cir', '').replace('.', 'p') + '.cir'
            open(fn, 'w').write(net(m, leak, vin))
            subprocess.run([LT, '-b', fn], cwd=os.path.dirname(os.path.abspath(__file__)), timeout=60)
            log = open(fn.replace('.cir', '.log'), errors='ignore').read()
            v = float(re.search(r'vo:.*?=([-0-9.eE+]+)', log).group(1))
            res[(m, leak, vin)] = v
for m in ('H_x1', 'H_x10', 'S_x1', 'S_x10', 'S2_x10'):
    vin = 0.2 if m.endswith('x10') else 1.0
    g0 = res[(m, 0, vin)] - res[(m, 0, 0.0)]
    g1 = res[(m, 1e-9, vin)] - res[(m, 1e-9, 0.0)]
    print(f'{m}: Vo(0 V) sin fuga {res[(m,0,0.0)]*1e6:+.1f} uV, con 1 nA {res[(m,1e-9,0.0)]*1e6:+.1f} uV (delta {(res[(m,1e-9,0.0)]-res[(m,0,0.0)])*1e6:+.1f} uV); '
          f'ganancia sin fuga {g0/vin:.5f}, con 1 nA {g1/vin:.5f}')
