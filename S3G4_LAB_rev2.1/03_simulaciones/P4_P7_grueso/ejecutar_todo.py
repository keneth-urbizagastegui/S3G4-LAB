"""Ejecuta los 14 ensayos P4/P7, extrae .meas/.four y evalua C1--C9.

El codigo de salida solo refleja errores de simulacion/medida, nunca criterios fallidos.
Rutas deliberadamente nativas de Windows (el proyecto contiene un espacio).
"""
from __future__ import annotations

import csv
import math
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
LTSPICE = Path(r"C:\Users\Keneth\AppData\Local\Programs\ADI\LTspice\LTspice.exe")
OUT = ROOT / "resultados"

# Tabla unica de umbrales, como exige el contrato.
CRITERIA = {
    "C1": {"zin_nom": 1e6, "tol_rel": .02},
    "C2": {"cin_min": 10e-12, "cin_max": 30e-12, "delta_max": 2e-12},
    "C3": {"gain_tol_rel": .01},
    "C4": {"flat_rel_max": .01, "loss_1m5_db_max": .5, "peak_db_max": .2},
    "C5": {"step_error_pct_max": 1.0},
    "C6": {"noise_div_pct_max": 1.0},
    "C7": {"thd_pct_max": .5, "zin_eff_min": 900e3},
    "C8": {"power_derating": .60, "v0805_max": 150., "v1206_max": 200., "amp_abs_max": 5.5},
    "C9": {"clamp_peak_max": .1, "amp_abs_max": 5.5},
}
NOM_GAIN = {"s5": 50., "s200": 1.25, "s500": .5, "s5v": .05}
SCALE_VDIV = [5e-3, 200e-3, 500e-3]


def lin(token: str) -> float:
    """LTspice imprime resultados AC como (dB,angulo); devolver magnitud lineal."""
    token = token.strip()
    m = re.match(r"\(([-+0-9.eE]+)dB,", token)
    if m:
        return 10 ** (float(m.group(1)) / 20)
    return float(re.match(r"[-+0-9.eE]+", token).group())


def parse_log(path: Path) -> tuple[dict[str, float], dict[str, list[float]], list[float], list[str]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    values: dict[str, float] = {}
    tables: dict[str, list[float]] = {}
    for line in text.splitlines():
        m = re.match(r"^([a-z][a-z0-9_]+):.*?=\s*(\([^\r\n]+?\)|[-+0-9.eE]+)(?:\s+at|\s+FROM|$)", line, re.I)
        if m:
            try: values[m.group(1).lower()] = lin(m.group(2))
            except (ValueError, AttributeError): pass
        elif re.match(r"^[a-z][a-z0-9_]*_f3:", line, re.I):
            mf = re.match(r"^([a-z][a-z0-9_]+):.*\sAT\s+([-+0-9.eE]+)\s*$", line, re.I)
            if mf: values[mf.group(1).lower()] = float(mf.group(2))
    # Tablas de .step: encabezado Measurement y filas numeradas.
    blocks = re.split(r"\nMeasurement:\s*", text)
    for block in blocks[1:]:
        name = block.splitlines()[0].strip().lower()
        vals = []
        for line in block.splitlines()[1:]:
            m = re.match(r"\s*\d+\s+(\([^\r\n]+?\)|[-+0-9.eE]+)(?:\s|$)", line)
            if m: vals.append(lin(m.group(1)))
            elif vals and line.strip(): break
        if vals: tables[name] = vals
    thd = [float(x) for x in re.findall(r"Total Harmonic Distortion:\s*([-+0-9.eE]+)%", text)]
    issues = [x.strip() for x in text.splitlines() if re.search(
        r"Measurement .*FAIL|syntax error|Fatal Error|Unknown subcircuit|Voltage not found|No such function|Time step too small|WARNING:", x, re.I)]
    return values, tables, thd, issues


def peak(v: dict[str, float], stem: str, kind: str) -> float:
    if f"{stem}_{kind}pk" in v:
        return abs(v[f"{stem}_{kind}pk"])
    return max(abs(v[f"{stem}_{kind}max"]), abs(v[f"{stem}_{kind}min"]))


def main() -> int:
    OUT.mkdir(exist_ok=True)
    asc_files = sorted([*ROOT.glob("P4_rele/T*.asc"), *ROOT.glob("P7_sin_rele/T*.asc")])
    allv: dict[str, dict[str, float]] = {"P4": {}, "P7": {}}
    allt: dict[str, dict[str, list[float]]] = {"P4": {}, "P7": {}}
    thds: dict[str, list[float]] = {"P4": [], "P7": []}
    errors: list[str] = []
    warnings: list[str] = []
    runs = []
    reuse = "--reuse" in sys.argv
    for asc in asc_files:
        proc = subprocess.CompletedProcess([], 0, "", "") if reuse else subprocess.run([str(LTSPICE), "-b", str(asc)], capture_output=True, text=True)
        log = asc.with_suffix(".log")
        design = "P4" if "P4_rele" in asc.parts else "P7"
        if not log.exists():
            issues, vals, tabs, four = ["no se genero .log"], {}, {}, []
        else:
            vals, tabs, four, issues = parse_log(log)
        allv[design].update(vals); allt[design].update(tabs)
        if asc.name.startswith("T05"): thds[design] = four
        bad = proc.returncode != 0 or bool(issues)
        if bad: errors.append(f"{asc.relative_to(ROOT)}: exit={proc.returncode}; " + "; ".join(issues))
        # Mensajes de convergencia recuperada se cuentan como advertencia aunque el calculo termine.
        if log.exists():
            txt = log.read_text(encoding="utf-8", errors="replace")
            for line in txt.splitlines():
                if "Direct Newton iteration failed" in line:
                    warnings.append(f"{asc.relative_to(ROOT)}: {line.strip()}")
        runs.append((str(asc.relative_to(ROOT)), proc.returncode, "ERROR" if bad else "OK"))

    rows: list[dict[str, object]] = []
    summary: dict[str, dict[str, tuple[str, bool]]] = {"P4": {}, "P7": {}}

    def result(design: str, crit: str, value: str, passed: bool) -> None:
        summary[design][crit] = (value, passed)
        rows.append({"design": design, "test": crit, "measure": "resumen_criterio", "value": value,
                     "unit": "", "criterion": crit, "pass": "PASS" if passed else "FAIL"})

    for design in ("P4", "P7"):
        d = design.lower(); v = allv[design]; t = allt[design]
        # C1/C2
        positions = ["x1", "d100"] if design == "P4" else ["fina", "gruesa"]
        zins = [v[f"{d}_{p}_zin100"] for p in positions]
        cins = [v[f"{d}_{p}_cin1m"] for p in positions]
        p1 = all(abs(x/CRITERIA['C1']['zin_nom']-1) <= CRITERIA['C1']['tol_rel'] for x in zins)
        result(design, "C1", ", ".join(f"{p}={x/1e6:.4f} Mohm" for p,x in zip(positions,zins)), p1)
        p2 = all(CRITERIA['C2']['cin_min'] <= x <= CRITERIA['C2']['cin_max'] for x in cins) and abs(cins[0]-cins[1]) <= CRITERIA['C2']['delta_max']
        result(design, "C2", ", ".join(f"{p}={x/1e-12:.3f} pF" for p,x in zip(positions,cins)) + f"; delta={abs(cins[0]-cins[1])/1e-12:.3f} pF", p2)
        # C3/C4
        gain_err=[]; flat=[]; loss=[]; pk=[]
        for scale,nom in NOM_GAIN.items():
            g=v[f"{d}_{scale}_g100"]; gain_err.append(100*(g/nom-1))
            flat.append(100*(v[f"{d}_{scale}_gmax"]/v[f"{d}_{scale}_gmin"]-1))
            loss.append(-20*math.log10(v[f"{d}_{scale}_g1m5"]/g))
            pk.append(20*math.log10(v[f"{d}_{scale}_peak"]/g))
        result(design,"C3",f"peor error={max(gain_err,key=abs):+.3f}%",max(map(abs,gain_err))<=100*CRITERIA['C3']['gain_tol_rel'])
        p4=max(flat)<=100*CRITERIA['C4']['flat_rel_max'] and max(loss)<=CRITERIA['C4']['loss_1m5_db_max'] and max(pk)<=CRITERIA['C4']['peak_db_max']
        result(design,"C4",f"peor planitud={max(flat):.3f}%, perdida1.5MHz={max(loss):.3f} dB, pico={max(pk):.3f} dB",p4)
        # C5
        errs=[]
        for scale in ("s5","s500"):
            errs.append(100*abs(v[f"{d}_{scale}_v2us"]/v[f"{d}_{scale}_vsettled"]-1))
        result(design,"C5",f"5mV/div={errs[0]:.3f}%, 500mV/div={errs[1]:.3f}%",max(errs)<=CRITERIA['C5']['step_error_pct_max'])
        # C6: filas SC 1..3 y ganancias correspondientes de T02.
        onoise=t[f"{d}_noise_integrated"]
        scales=("s5","s200","s500")
        ein=[onoise[i]/v[f"{d}_{scales[i]}_g100"] for i in range(3)]
        pct=[100*ein[i]/SCALE_VDIV[i] for i in range(3)]
        result(design,"C6",", ".join(f"{SCALE_VDIV[i]*1e3:g}mV/div={ein[i]*1e6:.2f}uV ({pct[i]:.3f}%)" for i in range(3)),max(pct)<=CRITERIA['C6']['noise_div_pct_max'])
        # C7: orden .four: r50 5,11,20,40; r10k...; probe...
        stem=f"{d}_r50_40"; i_pk=peak(v,stem,"iin"); bnc_pk=peak(v,stem,"bnc")
        zin=bnc_pk/i_pk; thd=thds[design][3]
        result(design,"C7",f"THD={thd:.4f}%, Zin_ef={zin/1e3:.2f} kohm",thd<=CRITERIA['C7']['thd_pct_max'] and zin>=CRITERIA['C7']['zin_eff_min'])
        # C8: los dos estados DC. Potencias medidas totales se reparten por las resistencias fisicas.
        c8_ok=True; c8_bits=[]
        for state in ("low","safe"):
            st=f"{d}_{state}_dc"
            amp=peak(v,st,"pre") if design=="P4" else max(peak(v,st,"fino"),peak(v,st,"grueso"))
            c8_ok &= amp <= CRITERIA['C8']['amp_abs_max']
            if design=="P4":
                rt_v=peak(v,st,"rt_v")/3; rt_p=abs(v[f"{st}_rt_p"])/3
                rs_v=peak(v,st,"rs_v"); rs_p=abs(v[f"{st}_rs_p"])
                c8_ok &= rt_v<=150 and rt_p<=.125*.60 and rs_v<=150 and rs_p<=.125*.60
                # Variante AT: dos 1206 comparten V/P.
                c8_ok &= rs_v/2<=200 and rs_p/2<=.25*.60
                c8_bits.append(f"{state}: Rt={rt_v:.2f}V/{rt_p*1e3:.2f}mW c/u, Rs-base={rs_v:.2f}V/{rs_p*1e3:.2f}mW, VinAmp={amp:.2f}V")
            else:
                vals=[]
                for br in ("rtf","rtg"):
                    rv=peak(v,st,f"{br}_v")/3; rp=abs(v[f"{st}_{br}_p"])/3
                    c8_ok &= rv<=150 and rp<=.125*.60; vals.append(f"{br}={rv:.2f}V/{rp*1e3:.2f}mW c/u")
                c8_bits.append(f"{state}: "+", ".join(vals)+f", VinAmp={amp:.2f}V")
        result(design,"C8","; ".join(c8_bits),c8_ok)
        # C9: red, clamp y entradas de buffer. Energia de cada rama = Pmedia*10s se conserva en CSV/acta.
        clamp=[]; amps=[]
        for state in ("low","safe"):
            st=f"{d}_{state}_ac"
            if design=="P4":
                clamp.append(max(peak(v,st,"dhp"),peak(v,st,"dlp"))); amps.append(peak(v,st,"pre"))
            else:
                clamp.append(max(peak(v,st,"dhf"),peak(v,st,"dlf"))); amps.append(max(peak(v,st,"fino"),peak(v,st,"grueso")))
        result(design,"C9",f"Iclamp_pk peor={max(clamp)*1e3:.2f}mA, VinAmp peor={max(amps):.2f}V",max(clamp)<=CRITERIA['C9']['clamp_peak_max'] and max(amps)<=CRITERIA['C9']['amp_abs_max'])

        # Volcado de todas las medidas primitivas para trazabilidad.
        for name,val in sorted(v.items()):
            rows.append({"design":design,"test":name.split("_")[1].upper() if "_" in name else "", "measure":name,
                         "value":f"{val:.12g}","unit":"SI","criterion":"","pass":""})
        for name,vals in sorted(t.items()):
            for i,val in enumerate(vals,1):
                rows.append({"design":design,"test":"STEP","measure":f"{name}[{i}]","value":f"{val:.12g}","unit":"SI","criterion":"","pass":""})

    with (OUT/"resultados.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=["design","test","measure","value","unit","criterion","pass"]); w.writeheader(); w.writerows(rows)

    lines=["# Resumen automatico P4/P7","",f"- Simulaciones: {len(asc_files)}",f"- Errores: {len(errors)}",f"- Advertencias: {len(warnings)}","",
           "| Criterio | P4 | Estado | P7 | Estado |","|---|---|---|---|---|"]
    for c in CRITERIA:
        a,ap=summary['P4'][c]; b,bp=summary['P7'][c]
        lines.append(f"| {c} | {a} | {'PASA' if ap else 'FALLA'} | {b} | {'PASA' if bp else 'FALLA'} |")
    lines += ["","## Ejecuciones","","| Fichero | exit LTspice | Estado |","|---|---:|---|"]
    lines += [f"| `{f}` | {code} | {state} |" for f,code,state in runs]
    lines += ["","## Errores"] + ([f"- {x}" for x in errors] or ["- Ninguno."])
    lines += ["","## Advertencias"] + ([f"- {x}" for x in warnings] or ["- Ninguna."])
    (OUT/"resumen.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(f"Simulaciones={len(asc_files)} errores={len(errors)} advertencias={len(warnings)}")
    print(f"CSV={OUT/'resultados.csv'}")
    print(f"Resumen={OUT/'resumen.md'}")
    if errors:
        for x in errors: print("ERROR:",x)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
