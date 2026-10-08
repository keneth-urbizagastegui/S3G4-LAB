# Auditoria Claude S12c, E3: corriente que la entrada del buffer X0 (OPA192 TI)
# inyecta por sus pinzas internas cuando X0 esta sujeto por BAV199 a ~5.5 V.
# Variantes: R serie 100/1k/10k ante el buffer y Schottky a los rieles en x0p.
# Barrido DC del borne 0..50 V. Trabaja en C:\s12c. Uso: python e3_pinza_x0.py
import subprocess, pathlib, re
LT = r"C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\OPA2192\OPAx192.LIB"
W = pathlib.Path(r"C:\s12c"); W.mkdir(exist_ok=True)
BAV = ".model BAV199 D(IS=805.84E-18 N=1.0246 RS=.05 IKF=362.16E-6 CJO=1.9002E-12 M=.35193 VJ=1.2722 ISR=298.95E-15 BV=113.30 IBV=10 TT=1.0230E-6)"
# Schottky generica tipo BAT54 (aproximada, no modelo de fabricante)
SCH = ".model SCH D(IS=2e-7 N=1.04 RS=2.4 CJO=10p BV=30)"
def deck(name, rser, schottky):
    s = f"""* {name}
.include "{LIB}"
{BAV}
{SCH}
Vp vp 0 4.9
Vn vn 0 -4.9
Vin vin 0 0
Rp vin x0p 99k
D0p x0p vp BAV199
D0n vn x0p BAV199
{"Dsp x0p vp SCH" if schottky else "*"}
{"Dsn vn x0p SCH" if schottky else "*"}
Rx0 x0p x0 {rser}
Vib0 x0 bi0 0
Xb bi0 bx0 vp vn bx0 OPAx192
Rl bx0 0 1Meg
.dc Vin 0 50 5
.meas dc ib20 FIND I(Vib0) AT=20
.meas dc ib50 FIND I(Vib0) AT=50
.meas dc v20 FIND V(bi0) AT=20
.meas dc v50 FIND V(bi0) AT=50
.meas dc x50 FIND V(x0p) AT=50
.end
"""
    p = W / f"{name}.cir"; p.write_text(s); return p
rows = []
for name, r, sch in (("r100", 100, 0), ("r1k", 1000, 0), ("r10k", 10000, 0), ("r100_sch", 100, 1), ("r10k_sch", 10000, 1)):
    p = deck(name, r, sch)
    subprocess.run([LT, "-b", str(p)], cwd=W, timeout=300)
    log = p.with_suffix(".log").read_text(encoding="utf-16-le", errors="ignore") if b"\x00" in p.with_suffix(".log").read_bytes()[:200] else p.with_suffix(".log").read_text(errors="ignore")
    m = dict(re.findall(r"(\w+):\s*\S+\(?.*?\)?=\s*([-\d.eE+]+)", log))
    vals = {k: m.get(k) for k in ("ib20", "ib50", "v20", "v50", "x50")}
    print(name, vals)
