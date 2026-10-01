from pathlib import Path

ROOT = Path(__file__).resolve().parent


def write(rel: str, title: str, criteria: str, net: list[str]) -> None:
    p = ROOT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    rows = ["Version 4.1", "SHEET 1 1900 1400",
            f"TEXT 48 32 Left 2 ;{title}", f"TEXT 48 56 Left 2 ;{criteria}"]
    y = 96
    for line in net:
        mark = ";" if line.startswith("*") else "!"
        text = line[1:].lstrip() if mark == ";" else line
        rows.append(f"TEXT 48 {y} Left 2 {mark}{text}")
        y += 24
    p.write_text("\n".join(rows) + "\n", encoding="ascii", errors="replace")


INC = ".include ..\\comun\\rev21_comun.inc"


def source_and_path(design, tag, pos, tap, gfix, rs="50", source="AC 1"):
    front = "FRONT_P4" if design == "P4" else "FRONT_P7"
    return [
        f"V{tag} VS{tag} 0 {source}", f"Rsrc{tag} VS{tag} BNC{tag} {rs}",
        f"Cbnc{tag} BNC{tag} 0 {{CBNC}}", f"XR{tag} VP{tag} VN{tag} RAILS",
        f"XF{tag} BNC{tag} PRE{tag} VP{tag} VN{tag} {front} POS={pos}",
        f"XC{tag} PRE{tag} SAL{tag} SALF{tag} VP{tag} VN{tag} COMMON TAP={tap} GFIX={gfix}",
    ]


def t01_p7():
    n = [INC]
    for tag, pos in [("F", 2), ("G", 200)]:
        n += [f"V{tag} SRC{tag} 0 AC 1", f"BI{tag} SRC{tag} BNC{tag} I=V(SRC{tag},BNC{tag})/1u",
              f"Cbnc{tag} BNC{tag} 0 {{CBNC}}", f"XR{tag} VP{tag} VN{tag} RAILS",
              f"XP7{tag} BNC{tag} OUT{tag} VP{tag} VN{tag} FRONT_P7 POS={pos}"]
    n += [".ac dec 100 10 10Meg",
          ".meas ac p7_fina_zin100 FIND mag(V(BNCF)/I(BIF)) AT=100",
          ".meas ac p7_fina_cin1m FIND abs(im(I(BIF)/V(BNCF)))/(2*pi*1Meg) AT=1Meg",
          ".meas ac p7_gruesa_zin100 FIND mag(V(BNCG)/I(BIG)) AT=100",
          ".meas ac p7_gruesa_cin1m FIND abs(im(I(BIG)/V(BNCG)))/(2*pi*1Meg) AT=1Meg"]
    write("P7_sin_rele/T01_zin.asc", "T01 P7: Zin/Cin con fina y gruesa seleccionadas.",
          "C1: 1Mohm +/-2%. C2: 10..30pF y diferencia <=2pF.", n)


SCALES = {
    "P4": [("s5", 1, 1, 50, 50), ("s200", 1, 40, 50, 1.25),
           ("s500", 100, 1, 50, .5), ("s5v", 100, 10, 50, .05)],
    "P7": [("s5", 2, 1, 100, 50), ("s200", 2, 40, 100, 1.25),
           ("s500", 200, 1, 100, .5), ("s5v", 200, 10, 100, .05)],
}


def t02(design):
    n = [INC]
    for tag, pos, tap, gf, nom in SCALES[design]:
        n += source_and_path(design, tag, pos, tap, gf)
    n += [".ac dec 80 10 100Meg"]
    d = design.lower()
    for tag, pos, tap, gf, nom in SCALES[design]:
        p = f"{d}_{tag}"
        n += [f".meas ac {p}_g100 FIND mag(V(SAL{tag})) AT=100",
              f".meas ac {p}_g100k FIND mag(V(SAL{tag})) AT=100k",
              f".meas ac {p}_g1m5 FIND mag(V(SAL{tag})) AT=1.5Meg",
              f".meas ac {p}_gmax MAX mag(V(SAL{tag})) FROM=10 TO=100k",
              f".meas ac {p}_gmin MIN mag(V(SAL{tag})) FROM=10 TO=100k",
              f".meas ac {p}_peak MAX mag(V(SAL{tag})) FROM=10 TO=100Meg",
              f".meas ac {p}_f3 WHEN mag(V(SAL{tag}))={nom}/sqrt(2) FALL=1"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T02_respuesta.asc",
          f"T02 {design}: cuatro escalas; SAL antes del filtro ideal.",
          "C3: ganancia +/-1%. C4: plana <=1%, perdida1.5MHz<=0.5dB, pico<=0.2dB.", n)


def t03(design):
    n = [INC, ".options noopiter"]
    specs = [("s5", SCALES[design][0], "15m"), ("s500", SCALES[design][2], "1.5")]
    for tag, (_, pos, tap, gf, nom), amp in specs:
        n += source_and_path(design, tag, pos, tap, gf, source=f"PULSE(-{amp} {amp} 1m 10n 10n 490u 1m)")
    n += [".tran 0 2m 0 25n startup"]
    d = design.lower()
    for tag, _, _ in specs:
        p = f"{d}_{tag}"
        n += [f".meas tran {p}_v2us FIND V(SAL{tag}) AT=1.00201m",
              f".meas tran {p}_v20us FIND V(SAL{tag}) AT=1.02001m",
              f".meas tran {p}_v200us FIND V(SAL{tag}) AT=1.20001m",
              f".meas tran {p}_vsettled FIND V(SAL{tag}) AT=1.40001m"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T03_escalon.asc",
          f"T03 {design}: escalon 1kHz/10ns, 5mV/div y 500mV/div.",
          "C5: error respecto a asentado <=1% a 2us.", n)


def t04(design):
    d = design.lower()
    if design == "P4":
        pos = "if(SC==3,100,1)"; tap = "if(SC==2,40,1)"; gf = 50
    else:
        pos = "if(SC==3,200,2)"; tap = "if(SC==2,40,1)"; gf = 100
    n = [INC, ".param SC=1", "Vin VS 0 AC 1", "Rsrc VS BNC 50", "Cbnc BNC 0 {CBNC}",
         "XR VP VN RAILS", f"XF BNC PRE VP VN FRONT_{design} POS={{{pos}}}",
         f"XC PRE SAL SALF VP VN COMMON TAP={{{tap}}} GFIX={gf}",
         ".step param SC list 1 2 3", ".noise V(SALF) Vin dec 80 10 50Meg",
         f".meas noise {d}_noise_integrated INTEG V(onoise)"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T04_ruido.asc",
          f"T04 {design}: SC=1/2/3 corresponde 5mV/200mV/500mV por division.",
          "C6: ruido referido a entrada <=1% de una division; Python divide por ganancia T02.", n)


def t05(design):
    d = design.lower(); n = [INC]
    pos, tap, gf = (100, 10, 50) if design == "P4" else (200, 10, 100)
    # Cin de la misma posicion, expresado a partir de los valores del circuito, no como total manual.
    cinexpr = "CBNC+CT_P4" if design == "P4" else "CBNC+CTF_P7+CTG_P7"
    n += [f".param CPROBE=({cinexpr})/9"]
    nodes = []
    for stype, rs in [("r50", "50"), ("r10k", "10k")]:
        for amp in [5, 11, 20, 40]:
            tag=f"{stype}_{amp}"; nodes.append(tag)
            n += source_and_path(design, tag, pos, tap, gf, rs=rs, source=f"SINE(0 {amp} 1k)")
    for amp_tip in [50, 112, 200, 400]:
        amp=amp_tip//10 if amp_tip != 112 else 11.2; tag=f"probe_{str(amp).replace('.','p')}"; nodes.append(tag)
        n += [f"V{tag} TIP{tag} 0 SINE(0 {amp_tip} 1k)", f"Rp{tag} TIP{tag} BNC{tag} 9Meg",
              f"Cp{tag} TIP{tag} BNC{tag} {{CPROBE}}", f"Cbnc{tag} BNC{tag} 0 {{CBNC}}",
              f"XR{tag} VP{tag} VN{tag} RAILS", f"XF{tag} BNC{tag} PRE{tag} VP{tag} VN{tag} FRONT_{design} POS={pos}",
              f"XC{tag} PRE{tag} SAL{tag} SALF{tag} VP{tag} VN{tag} COMMON TAP={tap} GFIX={gf}"]
    n += [".tran 0 2m 0 2u startup", ".four 1k " + " ".join(f"V(SAL{x})" for x in nodes)]
    for tag in nodes:
        # 1.25 ms es el pico positivo del segundo periodo de 1 kHz.
        n += [f".meas tran {d}_{tag}_salpk FIND V(SAL{tag}) AT=1.25m",
              f".meas tran {d}_{tag}_iinpk FIND I(V{tag}) AT=1.25m",
              f".meas tran {d}_{tag}_bncpk FIND V(BNC{tag}) AT=1.25m"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T05_gran_senal.asc",
          f"T05 {design}: 5V/div; fuentes 50ohm, 10kohm y sonda x10; amplitudes del contrato.",
          "C7: a 50ohm/40V THD<=0.5% y Zin efectiva>=900kohm.", n)


def t06(design):
    d=design.lower(); n=[INC]
    poses=[("low",1 if design=="P4" else 2),("safe",100 if design=="P4" else 200)]
    for state,pos in poses:
        for case,src in [("dc","50"),("ac","SINE(0 353.5533906 50)")]:
            tag=f"{state}_{case}"
            n += [f"V{tag} BNC{tag} 0 {src}", f"Cbnc{tag} BNC{tag} 0 {{CBNC}}",
                  f"VPI{tag} VPI{tag} 0 5", f"RVP{tag} VPI{tag} VP{tag} 1",
                  f"VNI{tag} VNI{tag} 0 -5", f"RVN{tag} VNI{tag} VN{tag} 1"]
            if design=="P4":
                n += [f"Rt{tag} BNC{tag} TAP{tag} {{RT_P4}}", f"Ct{tag} BNC{tag} TAP{tag} {{CT_P4}}",
                      f"Rb{tag} TAP{tag} 0 {{RB_P4}}", f"Cb{tag} TAP{tag} 0 {{CBN_P4}}",
                      f"Rs{tag} BNC{tag} X1{tag} {{RS_P4}}", f"Cs{tag} BNC{tag} X1{tag} {{CS_P4}}",
                      f"VC1{tag} C1{tag} 0 {1 if pos==1 else 0}", f"VC100{tag} C100{tag} 0 {1 if pos==100 else 0}",
                      f"S1{tag} X1{tag} PRE{tag} C1{tag} 0 SRELE", f"S100{tag} TAP{tag} PRE{tag} C100{tag} 0 SRELE",
                      f"CO1{tag} X1{tag} PRE{tag} {{COFF_RELE}}", f"CO100{tag} TAP{tag} PRE{tag} {{COFF_RELE}}",
                      f"Rbias{tag} PRE{tag} 0 {{RBIAS_P4}}", f"Csel{tag} PRE{tag} 0 {{CPAR_SEL}}", f"Ctap{tag} TAP{tag} 0 {{CPAR_TAP}}",
                      f"DHP{tag} PRE{tag} VP{tag} DBAV199", f"DLP{tag} VN{tag} PRE{tag} DBAV199",
                      f"DT1{tag} PRE{tag} TM{tag} DTVS5", f"DT2{tag} 0 TM{tag} DTVS5"]
                n += [f".meas tran {d}_{tag}_rt_vmax MAX V(BNC{tag},TAP{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rt_vmin MIN V(BNC{tag},TAP{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rt_p AVG V(BNC{tag},TAP{tag})*I(Rt{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rs_vmax MAX V(BNC{tag},X1{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rs_vmin MIN V(BNC{tag},X1{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rs_p AVG V(BNC{tag},X1{tag})*I(Rs{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_premax MAX V(PRE{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_premin MIN V(PRE{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rele_x1max MAX V(X1{tag},PRE{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_rele_x1min MIN V(X1{tag},PRE{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_rele_d100max MAX V(TAP{tag},PRE{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_rele_d100min MIN V(TAP{tag},PRE{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_dhpmax MAX I(DHP{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_dhpmin MIN I(DHP{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_dlpmax MAX I(DLP{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_dlpmin MIN I(DLP{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_tvsmax MAX I(DT1{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_tvsmin MIN I(DT1{tag}) FROM=80m TO=100m"]
            else:
                n += [f"RtF{tag} BNC{tag} FINO{tag} {{RTF_P7}}", f"CtF{tag} BNC{tag} FINO{tag} {{CTF_P7}}",
                      f"RbF{tag} FINO{tag} 0 {{RBF_P7}}", f"CbF{tag} FINO{tag} 0 {{CBF_P7}}", f"CFP{tag} FINO{tag} 0 {{CPAR_FINO}}",
                      f"RtG{tag} BNC{tag} GRUESO{tag} {{RTG_P7}}", f"CtG{tag} BNC{tag} GRUESO{tag} {{CTG_P7}}",
                      f"RbG{tag} GRUESO{tag} 0 {{RBG_P7}}", f"CbG{tag} GRUESO{tag} 0 {{CBG_P7}}", f"CGP{tag} GRUESO{tag} 0 {{CPAR_GRUESO}}",
                      f"XBF{tag} FINO{tag} BF{tag} VP{tag} VN{tag} BUF", f"XBG{tag} GRUESO{tag} BG{tag} VP{tag} VN{tag} BUF",
                      f"VC2{tag} C2{tag} 0 {1 if pos==2 else 0}", f"VC200{tag} C200{tag} 0 {1 if pos==200 else 0}",
                      f"SF{tag} BF{tag} PRE{tag} C2{tag} 0 S4053", f"SG{tag} BG{tag} PRE{tag} C200{tag} 0 S4053",
                      f"COF{tag} BF{tag} PRE{tag} {{COFF_4053}}", f"COG{tag} BG{tag} PRE{tag} {{COFF_4053}}", f"COUT{tag} PRE{tag} 0 {{CS_4053}}",
                      f"DHF{tag} FINO{tag} VP{tag} DBAV199", f"DLF{tag} VN{tag} FINO{tag} DBAV199",
                      f"DTF1{tag} FINO{tag} TMF{tag} DTVS5", f"DTF2{tag} 0 TMF{tag} DTVS5"]
                for br,node,res in [("rtf","FINO","RtF"),("rtg","GRUESO","RtG")]:
                    n += [f".meas tran {d}_{tag}_{br}_vmax MAX V(BNC{tag},{node}{tag}) FROM=80m TO=100m",
                          f".meas tran {d}_{tag}_{br}_vmin MIN V(BNC{tag},{node}{tag}) FROM=80m TO=100m",
                          f".meas tran {d}_{tag}_{br}_p AVG V(BNC{tag},{node}{tag})*I({res}{tag}) FROM=80m TO=100m"]
                n += [f".meas tran {d}_{tag}_finomax MAX V(FINO{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_finomin MIN V(FINO{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_gruesomax MAX V(GRUESO{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_gruesomin MIN V(GRUESO{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_dhfmax MAX I(DHF{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_dhfmin MIN I(DHF{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_dlfmax MAX I(DLF{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_dlfmin MIN I(DLF{tag}) FROM=80m TO=100m",
                      f".meas tran {d}_{tag}_tvsmax MAX I(DTF1{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_tvsmin MIN I(DTF1{tag}) FROM=80m TO=100m"]
            n += [f".meas tran {d}_{tag}_railpmax MAX I(RVP{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_railpmin MIN I(RVP{tag}) FROM=80m TO=100m",
                  f".meas tran {d}_{tag}_railnmax MAX I(RVN{tag}) FROM=80m TO=100m", f".meas tran {d}_{tag}_railnmin MIN I(RVN{tag}) FROM=80m TO=100m"]
    n += [".tran 0 100m 0 5u startup"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T06_supervivencia.asc",
          f"T06 {design}: 50Vdc y 250Vrms/50Hz, ambas posiciones; medidas en ultimo ciclo.",
          "C8: DC, P<=60% nominal y V nominal; C9: clamp<=100mA; entrada amp dentro de rail+0.5V.", n)


def t07(design):
    d=design.lower(); pos,tap,gf=(100,1,50) if design=="P4" else (200,1,100)
    n=[INC,".param RUN=0", ".param WC=1+0.05*sin(RUN*12.9898+0.7)",
       ".param WR=1+0.01*sin(RUN*78.233+1.3)",
       ".param WPAR=1+0.60*sin(RUN*39.425+2.1)",
       "Vin VS 0 AC 1", "Rsrc VS BNC {50*WR}", "Cbnc BNC 0 {CBNC*WPAR}", "XR VP VN RAILS",
       f"XF BNC PRE VP VN FRONT_{design} POS={pos}", f"XC PRE SAL SALF VP VN COMMON TAP={tap} GFIX={gf}",
       ".step param RUN 1 200 1", ".ac dec 30 10 10Meg",
       f".meas ac {d}_wc_gdc FIND mag(V(SAL)) AT=100",
       f".meas ac {d}_wc_g100k FIND mag(V(SAL)) AT=100k",
       f".meas ac {d}_wc_g1m5 FIND mag(V(SAL)) AT=1.5Meg",
       f".meas ac {d}_wc_peak MAX mag(V(SAL)) FROM=10 TO=10Meg",
       # Indicador de error inicial derivado de la relacion HF/LF; se declara como limitacion en acta.
       f".meas ac {d}_wc_step2us_proxy PARAM 100*abs({d}_wc_peak/{d}_wc_gdc-1)"]
    write(f"{design.replace('P4','P4_rele').replace('P7','P7_sin_rele')}/T07_robustez.asc",
          f"T07 {design}: 200 extremos deterministas de R/C/parasitarias; escala 500mV/div.",
          "Sin criterio. AC y ganancia DC; step2us_proxy no sustituye T03 y queda como duda explicita.", n)


if __name__ == "__main__":
    t01_p7()
    for design in ("P4", "P7"):
        t02(design); t03(design); t04(design); t05(design); t06(design); t07(design)
