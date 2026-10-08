# Auditoria Claude S12c: opcion (a), buffer OPA192 en X2.
# Divisor S12c reducido (borne a 0 V): 9 Mohm + 3x(100p+3.3k), 910k||330p, 100k||3n.
# 1) DC: fuga del mux (1.85 nA a 23 C, 2.616 nA a 28 C) en el nodo del mux;
#    sin buffer el nodo del mux es X2; con buffer es la salida del buffer (+Ron 70).
# 2) Transitorio: carga de 7.8 pC inyectada en el nodo del mux a t=0 (equivale
#    a la cola observada por Codex, ~259 cuentas iniciales a tau=300 us).
# Salida en cuentas del rango 20 V (1 cuenta = 1 mV en borne = 99.9 uV en X2).
import subprocess, pathlib, re
LT = r"C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe"
LIB = r"C:\Users\Keneth\Desktop\S3G4 LAB\Simulation_LTSpice\models\OPA2192\OPAx192.LIB"
W = pathlib.Path(r"C:\s12c")
LSB = 1e-3 * 100e3 / 10.01e6
def deck(name, buf, analysis):
    mux = "m" if buf else "x2"
    s = f"""* {name}
.include "{LIB}"
Vp vp 0 4.9
Vn vn 0 -4.9
Rtop 0 x1p 9Meg
Ctop 0 x1p 33.3p
Rlow x1p x2 910k
Clow x1p x2 330p
Rbot x2 0 100k
Cbot x2 0 3n
Cp2 x2 0 8p
{"Xb x2 bo vp vn bo OPAx192" if buf else "*"}
{"Ron bo m 70" if buf else "*"}
Cm {mux} 0 28p
Il {mux} 0 {{IL}}
Iq {mux} 0 PWL(0 0 1n {{Q/1n}} 2n 0)
{analysis}
.end
"""
    p = W / f"{name}.cir"; p.write_text(s); return p
def run(p):
    subprocess.run([LT, "-b", str(p)], cwd=W, timeout=300)
    b = p.with_suffix(".log").read_bytes()
    t = b.decode("utf-16-le", "ignore") if b[1:2] == b"\x00" else b.decode("latin-1")
    return dict((k.lower(), float(v)) for k, v in re.findall(r"^(\w+):[^=\n]*=\s*([-\d.eE+]+)", t, re.M))
for buf in (0, 1):
    node = "m" if buf else "x2"
    v = []
    for il in ("1.85n", "2.616n"):
        r = run(deck(f"x2dc_b{buf}_{il}", buf, f".param Q=0 IL={il}\n.op\n.meas op v FIND V({node})"))
        v.append(r["v"])
    print(f"buffer={buf} DC: 23C {v[0]/LSB:.3f} cuentas, 28C {v[1]/LSB:.3f}, deriva {(v[1]-v[0])/LSB:.4f} cuentas")
    tr = ".param IL=0 Q=7.8p\n.tran 0 3.5m 0 1u\n" + "\n".join(
        f".meas tran e{int(t*1e4)} FIND V({node}) AT={t}" for t in (1e-4, 1.5e-3, 3e-3))
    r = run(deck(f"x2tr_b{buf}", buf, tr))
    print(f"buffer={buf} carga 7.8 pC:", {k: round(v / LSB, 4) for k, v in r.items() if k.startswith("e")})
