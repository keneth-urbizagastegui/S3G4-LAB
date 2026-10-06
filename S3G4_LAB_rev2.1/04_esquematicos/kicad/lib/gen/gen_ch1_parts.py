# Uso (desde 04_esquematicos/kicad): python lib/gen/gen_ch1_parts.py
# Genera las huellas y símbolos propios de CH1 (S8, 4 oct 2026) y los integra en la librería s3g4
# sin tocar los demás símbolos (reemplaza sólo los de este script si ya existen).
#
# Fuentes de las cotas (todas en datasheet - componentes/ salvo donde se dice):
#  K101 TQ2SA-5V-Z (C22686): C46047.pdf (serie TQ, ASCTB14E) p.11, "Suggested mounting pad (Top view)" tipo SA:
#       pads 1.0 x 2.94 mm, paso 2.54, 9.56 mm entre centros de fila; esquema en vista superior p.11:
#       fila inferior 1..5 (izq->der), fila superior 10..6; bobina 1(+)/10(-); polo 1: 3 COM, 2 NC, 4 NO;
#       polo 2: 8 COM, 9 NC, 7 NO; 5 y 6 sin función. Cuerpo 14 x 9. Coincide con la huella SamacSys 16574131.
#  SW101 SS23H37L6 (C883267): C883267.pdf (XKB SS23H37): pines a 0/6/10/14 mm, filas a 2.5 mm,
#       anclajes a 18.5 x 6.1 mm con 3.3 mm del primer pin; cuerpo 19.5 x 6.6. Agujeros (no los da el plano):
#       huella EasyEDA de LCSC (uuid 71739f07...): pad 1.5 / taladro 0.9 (contactos), pad 2.0 / taladro 1.3 (anclajes).
#       Numeración propia (CH1_PIEZAS_Y_REDES.md §2.3): polo A 1=T1(0 mm) 2=COM(6) 3=T2(10) 4=T3(14); polo B 5..8 igual.
#  J101 KH-BNC50-3511 (C2837587): C2837587.pdf "PCB": 2 x Ø2.00 a 10.1 mm; 2 x Ø0.90 a 2.5 mm, el central en el eje,
#       fila de señal a 5.05 mm detrás de la de anclaje; cuerpo 14.7 de ancho, frente a 28.5 mm de la fila de anclaje,
#       35.5 de largo. Coincide con la huella EasyEDA (uuid 066bf880...). Pin 1 centro, pin 2 (y anclajes) malla.
#  VC101 SEHWA STC3MA06-T1 (C22468120): C22468120.pdf p.3 (land pattern). La hoja no identifica el rotor.
import os, re
HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.dirname(HERE)
PRETTY = os.path.join(LIB, "s3g4.pretty")
SYM = os.path.join(LIB, "s3g4.kicad_sym")
f = lambda v: ("%.3f" % v).rstrip('0').rstrip('.')

# ---------------------------------------------------------------- huellas
class FP:
    def __init__(s, name, descr, tags, attr):
        s.name = name; s.o = [f'(footprint "{name}"\n\t(version 20260206)\n\t(generator "s3g4_gen_fp")\n\t(layer "F.Cu")',
                               f'\t(descr "{descr}")', f'\t(tags "{tags}")']
        s.attr = attr
    def props(s, yref, yval, ds):
        for p, v, y, lay, hide in (("Reference", "REF**", yref, "F.SilkS", False), ("Value", s.name, yval, "F.Fab", False),
                                   ("Datasheet", ds, 0, "F.Fab", True), ("Description", s.name, 0, "F.Fab", True)):
            s.o.append(f'\t(property "{p}" "{v}" (at 0 {f(y)} 0) (layer "{lay}"){" (hide yes)" if hide else ""} (effects (font (size 1 1) (thickness 0.15))))')
        s.o.append(f'\t(attr {s.attr})')
    def rect(s, x1, y1, x2, y2, lay, w):
        s.o.append(f'\t(fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type solid)) (fill no) (layer "{lay}"))')
    def line(s, x1, y1, x2, y2, lay, w):
        s.o.append(f'\t(fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {w}) (type solid)) (layer "{lay}"))')
    def circ(s, x, y, r, lay, w, fill="no"):
        s.o.append(f'\t(fp_circle (center {f(x)} {f(y)}) (end {f(x+r)} {f(y)}) (stroke (width {w}) (type solid)) (fill {fill}) (layer "{lay}"))')
    def text(s, t, x, y, lay, size=1):
        s.o.append(f'\t(fp_text user "{t}" (at {f(x)} {f(y)} 0) (layer "{lay}") (effects (font (size {size} {size}) (thickness {f(size*0.15)}))))')
    def smd(s, n, x, y, w, h):
        s.o.append(f'\t(pad "{n}" smd roundrect (at {f(x)} {f(y)}) (size {f(w)} {f(h)}) (layers "F.Cu" "F.Mask" "F.Paste") (roundrect_rratio 0.15))')
    def tht(s, n, x, y, d, drill, shape="circle"):
        s.o.append(f'\t(pad "{n}" thru_hole {shape} (at {f(x)} {f(y)}) (size {f(d)} {f(d)}) (drill {f(drill)}) (layers "*.Cu" "*.Mask") (remove_unused_layers no))')
    def save(s):
        s.o.append('\t(embedded_fonts no)\n)')
        open(os.path.join(PRETTY, s.name + ".kicad_mod"), "w", encoding="utf-8", newline="\n").write("\n".join(s.o) + "\n")

DS = "${KIPRJMOD}/../../../datasheet - componentes/"

# K101: relé TQ2SA, origen en el centro del cuerpo
fp = FP("Relay_Panasonic_TQ2SA_SMD", "Rele de senal Panasonic TQ2SA (SMD tipo SA), DPDT. Pads segun C46047.pdf p.11 (vista superior)", "relay TQ2 TQ2SA DPDT signal Panasonic", "smd")
fp.props(-7.6, 7.6, DS + "C46047.pdf")
P, Y = 2.54, 9.56 / 2
fp.rect(-7, -4.5, 7, 4.5, "F.Fab", 0.1)
fp.line(-7, 3.5, -6, 4.5, "F.Fab", 0.1)
for i in range(5):
    fp.smd(i + 1, -5.08 + i * P, Y, 1.0, 2.94)        # 1..5 fila inferior, izq -> der
    fp.smd(10 - i, -5.08 + i * P, -Y, 1.0, 2.94)      # 10..6 fila superior, izq -> der
fp.line(-7.12, -3.0, -7.12, 3.0, "F.SilkS", 0.12); fp.line(7.12, -3.0, 7.12, 3.0, "F.SilkS", 0.12)
fp.circ(-5.08, Y + 2.0, 0.15, "F.SilkS", 0.3, "yes")
fp.rect(-7.5, -Y - 1.72, 7.5, Y + 1.72, "F.CrtYd", 0.05)
fp.text("${REFERENCE}", 0, 0, "F.Fab", 1)
fp.save()

# SW101: conmutador deslizante SS23H37, origen en el centro del cuerpo
X0 = -5.95                                            # pin T1 respecto al centro (anclajes a -3.3 y +15.2 del pin 1)
fp = FP("SW_Slide_DP3T_XKB_SS23H37", "Conmutador deslizante XKB SS23H37 (2 polos x 3 posiciones, recorrido 4 mm). Cotas C883267.pdf; agujeros de la huella EasyEDA de LCSC. Numeracion propia: polo A 1=T1 2=COM 3=T2 4=T3, polo B 5..8", "slide switch DP3T SS23H37 XKB", "through_hole")
fp.props(-4.6, 4.6, DS + "C883267.pdf")
fp.rect(-9.75, -3.3, 9.75, 3.3, "F.Fab", 0.1)
for i, dx in enumerate((0, 6, 10, 14)):
    fp.tht(i + 1, X0 + dx, 1.25, 1.5, 0.9, "rect" if i == 0 else "circle")   # polo A
    fp.tht(i + 5, X0 + dx, -1.25, 1.5, 0.9)                                   # polo B
for x in (X0 - 3.3, X0 + 15.2):
    for y in (-3.05, 3.05):
        fp.tht("", x, y, 2.0, 1.3)                                            # anclajes, sin red
fp.rect(-9.87, -3.42, 9.87, 3.42, "F.SilkS", 0.12)
fp.text("A", X0 - 1.5, 1.25, "F.Fab", 0.8); fp.text("B", X0 - 1.5, -1.25, "F.Fab", 0.8)
fp.rect(-10.1, -4.3, 10.1, 4.3, "F.CrtYd", 0.05)
fp.save()

# J101: BNC acodado Kinghelm, origen en el pin central; la boca apunta hacia +y
fp = FP("BNC_Kinghelm_KH-BNC50-3511_Horizontal", "BNC hembra acodado Kinghelm KH-BNC50-3511 (C2837587). Cotas C2837587.pdf; la boca apunta hacia +y. Pin 1 centro; pin 2 y anclajes = malla", "BNC coaxial right-angle Kinghelm", "through_hole")
fp.props(-3.2, 35.0, DS + "C2837587.pdf")
yM = 5.05
fp.rect(-7.35, yM - 7.0, 7.35, yM + 28.5, "F.Fab", 0.1)
fp.line(-7.35, yM + 28.5 - 21.0, 7.35, yM + 28.5 - 21.0, "F.Fab", 0.1)            # inicio de la rosca (21 mm del frente)
fp.text("boca", 0, yM + 26, "F.Fab", 1)
fp.tht(1, 0, 0, 1.6, 0.9, "rect")
fp.tht(2, 2.5, 0, 1.6, 0.9)
for x in (-5.05, 5.05):
    fp.tht(2, x, yM, 3.0, 2.0)
fp.rect(-7.47, yM - 7.12, 7.47, yM + 6.0, "F.SilkS", 0.12)                       # parte sobre la placa
fp.rect(-7.6, yM - 7.25, 7.6, yM + 28.75, "F.CrtYd", 0.05)
fp.save()

# VC101: trimmer SEHWA STC3MA06, origen en el centro, eje largo vertical.
# Cotas: C22468120.pdf (SEHWA STC3M-SP-15 rev 4.1) p.3, "Land Pattern": pads 1.40 x 1.30, 2.60 entre bordes
# interiores y 5.10 entre exteriores -> centros a +-1.95; cuerpo 3.20 x 4.50. La hoja no identifica el rotor.
fp = FP("C_Trimmer_SEHWA_STC3MA06_3.2x4.5mm", "Trimmer ceramico SEHWA STC3MA06-T1 2-6 pF NP0 100 V (C22468120). Land pattern de C22468120.pdf p.3. La hoja no indica que terminal es el rotor", "trimmer capacitor SEHWA STC3", "smd")
fp.props(-3.3, 3.3, DS + "C22468120.pdf")
fp.rect(-1.6, -2.25, 1.6, 2.25, "F.Fab", 0.1)
fp.circ(0, 0, 1.1, "F.Fab", 0.1)
fp.smd(1, 0, -1.95, 1.4, 1.3); fp.smd(2, 0, 1.95, 1.4, 1.3)
fp.line(-1.72, -0.9, -1.72, 0.9, "F.SilkS", 0.12); fp.line(1.72, -0.9, 1.72, 0.9, "F.SilkS", 0.12)
fp.rect(-1.95, -2.85, 1.95, 2.85, "F.CrtYd", 0.05)
fp.save()

# ---------------------------------------------------------------- símbolos
fx = '(effects (font (size 1.27 1.27)))'
def prop(k, v, x, y, hide=False, just=""):
    j = f' (justify {just})' if just else ''
    return f'\t\t(property "{k}" "{v}" (at {f(x)} {f(y)} 0){" (hide yes)" if hide else ""} (effects (font (size 1.27 1.27)){j}))'
def pin(typ, n, name, x, y, ang, hide=False, length=2.54):
    return f'\t\t\t(pin {typ} line (at {f(x)} {f(y)} {ang}) (length {f(length)}){" (hide yes)" if hide else ""} (name "{name}" {fx}) (number "{n}" {fx}))'
def poly(pts, w=0.254):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return f'\t\t\t(polyline (pts {p}) (stroke (width {f(w)}) (type default)) (fill (type none)))'
def circle(x, y, r):
    return f'\t\t\t(circle (center {f(x)} {f(y)}) (radius {f(r)}) (stroke (width 0.2) (type default)) (fill (type none)))'
def symbol(name, ref, value, fpname, ds, desc, mpn, lcsc, gfx, pins, ytop, ybot):
    return f'''	(symbol "{name}"
		(pin_names (offset 0.508) (hide yes))
		(exclude_from_sim no) (in_bom yes) (on_board yes)
{prop("Reference", ref, 0, ytop + 1.27)}
{prop("Value", value, 0, ybot - 1.27)}
{prop("Footprint", "s3g4:" + fpname, 0, ybot - 3.81, True)}
{prop("Datasheet", ds, 0, 0, True)}
{prop("Description", desc, 0, 0, True)}
{prop("MPN", mpn, 0, 0, True)}
{prop("LCSC", lcsc, 0, 0, True)}
		(symbol "{name}_0_1"
{chr(10).join(gfx)}
		)
		(symbol "{name}_1_1"
{chr(10).join(pins)}
		)
		(embedded_fonts no)
	)'''

def txt(t, x, y, size=1.0):
    return f'			(text "{t}" (at {f(x)} {f(y)} 0) (effects (font (size {f(size)} {f(size)}))))'
W, PL = 7.62, 10.16                                   # medio ancho del cuerpo y posición de los pines

# Relé TQ2SA: bobina a la izquierda, dos polos a la derecha (NC arriba, COM, NO abajo); dibujado en reposo (COM-NC)
g = [f'			(rectangle (start {-W} 12.7) (end {W} -12.7) (stroke (width 0.254) (type default)) (fill (type background)))',
     f'			(rectangle (start -6.35 1.27) (end -3.81 -1.27) (stroke (width 0.254) (type default)) (fill (type none)))',
     poly([(-W, 2.54), (-5.08, 2.54), (-5.08, 1.27)]), poly([(-W, -2.54), (-5.08, -2.54), (-5.08, -1.27)]),
     txt("+", -6.6, 3.6), txt("-", -6.6, -3.6), poly([(-3.81, 0), (-1.27, 0)], 0.15)]
pins = [pin("passive", 1, "+", -PL, 2.54, 0), pin("passive", 10, "-", -PL, -2.54, 0),
        pin("no_connect", 5, "NC", -PL, -10.16, 0, True), pin("no_connect", 6, "NC", -PL, -7.62, 0, True)]
for yc, nc, com, no in ((7.62, 2, 3, 4), (-7.62, 9, 8, 7)):
    g += [poly([(W, yc), (-1.27, yc), (3.3, yc + 2.25)]), circle(-1.27, yc, 0.35),
          poly([(W, yc + 2.54), (3.81, yc + 2.54)]), poly([(W, yc - 2.54), (3.81, yc - 2.54)]),
          txt("NC", 5.7, yc + 3.5), txt("COM", 4.8, yc + 0.95), txt("NO", 5.7, yc - 1.6)]
    pins += [pin("passive", nc, "NC", PL, yc + 2.54, 180), pin("passive", com, "COM", PL, yc, 180),
             pin("passive", no, "NO", PL, yc - 2.54, 180)]
g += [poly([(-1.27, 0), (-1.27, 7.0)], 0.15), poly([(-1.27, 0), (-1.27, -7.0)], 0.15)]   # unión mecánica bobina-contactos
SYMS = {"TQ2SA-5V-Z": symbol("TQ2SA-5V-Z", "K", "TQ2SA-5V-Z", "Relay_Panasonic_TQ2SA_SMD", DS + "C46047.pdf",
        "Rele de senal Panasonic TQ2SA-5V-Z, DPDT monoestable, bobina 5 V 178 ohm con polaridad (1 = +). Dibujado en reposo. Pines 5 y 6 sin funcion",
        "TQ2SA-5V-Z", "C22686", g, pins, 12.7, -12.7)}

# Conmutador SS23H37: dos polos, común a la izquierda, T1/T2/T3 a la derecha (AC, GND, DC en CH1)
g = [f'			(rectangle (start {-W} 10.16) (end {W} -10.16) (stroke (width 0.254) (type default)) (fill (type background)))']
pins = []
for yc, base, pole in ((5.08, 1, "A"), (-5.08, 5, "B")):
    ys = (yc + 2.54, yc, yc - 2.54)                 # T1, T2, T3
    g += [poly([(-W, yc), (-2.54, yc), (2.8, ys[0] - 0.35)]), circle(-2.54, yc, 0.35), txt("COM", -5.3, yc + 0.95)]
    for y, t in zip(ys, ("T1", "T2", "T3")):
        g += [poly([(W, y), (3.81, y)]), circle(3.81, y, 0.35), txt(t, 5.7, y + 0.95)]
    pins += [pin("passive", base + 1, "COM", -PL, yc, 0),
             pin("passive", base, "T1", PL, ys[0], 180), pin("passive", base + 2, "T2", PL, ys[1], 180),
             pin("passive", base + 3, "T3", PL, ys[2], 180)]
g += [poly([(0.6, 4.0), (0.6, -6.6)], 0.15)]
SYMS["SS23H37L6"] = symbol("SS23H37L6", "SW", "SS23H37L6", "SW_Slide_DP3T_XKB_SS23H37", DS + "C883267.pdf",
        "Conmutador deslizante XKB SS23H37L6, 2 polos x 3 posiciones. T1/T2/T3 por orden de recorrido (CH1: AC, GND, DC). Numeracion propia: A 1=T1 2=COM 3=T2 4=T3; B 5..8",
        "SS23H37L6", "C883267", g, pins, 10.16, -10.16)

# Integración: quitar versiones anteriores de estos símbolos y añadir las nuevas
s = open(SYM, encoding="utf-8").read()
def drop(text, name):
    i = text.find(f'(symbol "{name}"')
    if i < 0: return text
    d = 0
    for j in range(i, len(text)):
        if text[j] == '(': d += 1
        elif text[j] == ')':
            d -= 1
            if d == 0: return text[:text.rfind('\n', 0, i) + 1] + text[j + 1:].lstrip('\n')
    raise ValueError("símbolo sin cerrar")
for n in SYMS: s = drop(s, n)
k = s.rstrip().rfind(')')
s = s[:k].rstrip() + "\n" + "\n".join(SYMS.values()) + "\n)\n"
open(SYM, "w", encoding="utf-8", newline="\n").write(s)
print("huellas:", sorted(x for x in os.listdir(PRETTY)))
print("símbolos:", re.findall(r'^\t\(symbol "([^"]+)"', s, re.M))
