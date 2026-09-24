# -*- coding: utf-8 -*-
"""Mini-libreria SVG para esbozos de esquematico (estilo Altium simplificado)."""
import html, math

def esc(t): return html.escape(str(t), quote=True)

class Sch:
    def __init__(s, w, h, title=""):
        s.w, s.h, s.e, s.title = w, h, [], title
    def add(s, x): s.e.append(x)
    # ---------- primitivas ----------
    def wire(s, *p, cls="w"):
        s.add(f'<polyline class="{cls}" points="{" ".join(f"{x},{y}" for x,y in p)}"/>')
    def dot(s, x, y): s.add(f'<circle class="dot" cx="{x}" cy="{y}" r="3.2"/>')
    def text(s, x, y, t, cls="lbl", a="start"):
        s.add(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{a}">{esc(t)}</text>')
    def rect(s, x, y, w, h, cls="blk", r=0):
        s.add(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>')
    def frame(s, x, y, w, h, t):
        s.rect(x, y, w, h, "grp", 6); s.text(x+8, y+15, t, "grp-t")
    # ---------- dos terminales ----------
    def _two(s, p1, p2, body):
        (x1,y1),(x2,y2) = p1,p2
        L = math.hypot(x2-x1, y2-y1); ux, uy = (x2-x1)/L, (y2-y1)/L
        mx, my = (x1+x2)/2, (y1+y2)/2
        a = (mx-ux*body/2, my-uy*body/2); b = (mx+ux*body/2, my+uy*body/2)
        s.wire(p1, a); s.wire(b, p2)
        ang = math.degrees(math.atan2(uy, ux))
        return mx, my, ang, abs(ux) > 0.5
    def _labels(s, mx, my, horiz, name, val, side):
        if horiz:
            dy = -12 if side != "b" else 26
            s.text(mx, my+dy, name, "ref", "middle")
            if val: s.text(mx, my+(22 if side != "b" else 38), val, "val", "middle")
        else:
            if side == "l":
                s.text(mx-14, my-3, name, "ref", "end")
                if val: s.text(mx-14, my+11, val, "val", "end")
            else:
                s.text(mx+14, my-3, name, "ref")
                if val: s.text(mx+14, my+11, val, "val")
    def R(s, p1, p2, name, val="", side="", cls="sym", body=40):
        mx,my,ang,h = s._two(p1,p2,body)
        z = " ".join(f"{-20+i*5},{0 if i in (0,8) else (-6 if i%2 else 6)}" for i in range(9))
        s.add(f'<polyline class="{cls}" points="{z}" transform="translate({mx},{my}) rotate({ang})"/>')
        s._labels(mx,my,h,name,val,side)
    def HDR(s, p1, p2, name):  # cabecera de derivacion 0 ohm
        mx,my,ang,h = s._two(p1,p2,24)
        s.add(f'<rect class="hdr" x="-12" y="-5" width="24" height="10" transform="translate({mx},{my}) rotate({ang})"/>')
        s._labels(mx,my,h,name,"0 Ω · cabecera","")
    def C(s, p1, p2, name, val="", side="", cls="sym", trim=False):
        mx,my,ang,h = s._two(p1,p2,8)
        s.add(f'<g transform="translate({mx},{my}) rotate({ang})"><line class="{cls}" x1="-4" y1="-11" x2="-4" y2="11"/>'
              f'<line class="{cls}" x1="4" y1="-11" x2="4" y2="11"/>'
              + ('<line class="sym" x1="-12" y1="12" x2="12" y2="-12"/><polyline class="sym" points="6,-12 12,-12 12,-6"/>' if trim else '')
              + '</g>')
        s._labels(mx,my,h,name,val,side)
    def D(s, pa, pk, name, val="", side="", kind="d"):
        """Diodo de anodo pa a catodo pk. kind: d, z (zener), s (schottky), tvs (bidireccional)."""
        mx,my,ang,h = s._two(pa,pk,22)
        if kind == "tvs":
            g = ('<polygon class="fillsym" points="-11,-9 -11,9 0,0"/><polygon class="fillsym" points="11,-9 11,9 0,0"/>'
                 '<polyline class="sym" points="-3,-11 0,-9 0,9 3,11"/>')
        else:
            bar = {'d':'<line class="sym" x1="6" y1="-9" x2="6" y2="9"/>',
                   'z':'<polyline class="sym" points="3,-11 6,-9 6,9 9,11"/>',
                   's':'<polyline class="sym" points="9,-6 9,-9 6,-9 6,9 3,9 3,6"/>'}[kind]
            g = '<polygon class="fillsym" points="-7,-9 -7,9 6,0"/>' + bar
        s.add(f'<g transform="translate({mx},{my}) rotate({ang})">{g}</g>')
        s._labels(mx,my,h,name,val,side)
    def L(s, p1, p2, name, val="", side=""):
        mx,my,ang,h = s._two(p1,p2,40)
        arcs = "".join(f'<path class="sym" d="M{-20+i*10},0 a5,5 0 0 1 10,0"/>' for i in range(4))
        s.add(f'<g transform="translate({mx},{my}) rotate({ang})">{arcs}</g>')
        s._labels(mx,my,h,name,val,side)
    def FUSE(s, p1, p2, name, val="", side=""):
        mx,my,ang,h = s._two(p1,p2,36)
        s.add(f'<g transform="translate({mx},{my}) rotate({ang})"><rect class="sym" x="-18" y="-6" width="36" height="12"/><line class="sym" x1="-18" y1="0" x2="18" y2="0"/></g>')
        s._labels(mx,my,h,name,val,side)
    def PTC(s, p1, p2, name, val="", side=""):
        mx,my,ang,h = s._two(p1,p2,36)
        s.add(f'<g transform="translate({mx},{my}) rotate({ang})"><rect class="sym" x="-18" y="-6" width="36" height="12"/><polyline class="sym" points="-16,12 -8,12 12,-12"/></g>')
        s._labels(mx,my,h,name,val,side)
    # ---------- simbolos de nodo ----------
    def gnd(s, x, y, t="AGND"):
        s.wire((x,y),(x,y+8))
        s.add(f'<g class="gnd"><line x1="{x-10}" y1="{y+8}" x2="{x+10}" y2="{y+8}"/><line x1="{x-6}" y1="{y+12}" x2="{x+6}" y2="{y+12}"/><line x1="{x-2}" y1="{y+16}" x2="{x+2}" y2="{y+16}"/></g>')
        if t != "AGND": s.text(x, y+28, t, "rail", "middle")
    def rail(s, x, y, t, up=True):
        d = -1 if up else 1
        s.wire((x,y),(x,y+d*10))
        s.add(f'<line class="railbar" x1="{x-12}" y1="{y+d*10}" x2="{x+12}" y2="{y+d*10}"/>')
        s.text(x, y+d*(16 if up else 24), t, "rail", "middle")
    def net(s, x, y, t, a="start", dy=-5):
        s.text(x + (4 if a=="start" else -4 if a=="end" else 0), y+dy, t, "net", a)
    def port(s, x, y, t, d="r", io="io"):
        """Puerto jerarquico. d='r': el cable llega por la izquierda y la punta mira a la derecha."""
        w = 9 + 6.6*len(t)
        if d == "r":
            pts = f"{x},{y-8} {x+w},{y-8} {x+w+8},{y} {x+w},{y+8} {x},{y+8}"; tx = x+5; a="start"
        else:
            pts = f"{x},{y-8} {x-w},{y-8} {x-w-8},{y} {x-w},{y+8} {x},{y+8}"; tx = x-5; a="end"
        s.add(f'<polygon class="port" points="{pts}"/>')
        s.text(tx, y+4, t, "portt", a)
    def tp(s, x, y, t, a="start"):
        s.add(f'<circle class="tp" cx="{x}" cy="{y}" r="4.5"/>')
        s.text(x + (8 if a=="start" else -8), y+4, t, "tpt", a)
    def note(s, x, y, t, a="start"): s.text(x, y, t, "note", a)
    # ---------- activos ----------
    def opamp(s, x, y, name, val="", inp_top=False, rails=None):
        """Triangulo de x a x+60. Pines: inm/inp en x-10, out en x+70."""
        s.add(f'<polygon class="op" points="{x},{y-32} {x},{y+32} {x+62},{y}"/>')
        top, bot = ("+","−") if inp_top else ("−","+")
        s.text(x+7, y-11, top, "pm"); s.text(x+7, y+21, bot, "pm")
        s.wire((x-10,y-16),(x,y-16)); s.wire((x-10,y+16),(x,y+16)); s.wire((x+62,y),(x+72,y))
        s.text(x+10, y-38, name, "ref");
        if val: s.text(x+10, y+46, val, "val")
        if rails:
            s.wire((x+28,y-19),(x+28,y-30)); s.text(x+32, y-26, rails[0], "railsm")
            s.wire((x+28,y+19),(x+28,y+30)); s.text(x+32, y+32, rails[1], "railsm")
        pins = {"inm": (x-10, y-16), "inp": (x-10, y+16), "out": (x+72, y)}
        if inp_top: pins["inp"], pins["inm"] = pins["inm"], pins["inp"]
        return pins
    def fda(s, x, y, name, val=""):
        s.add(f'<polygon class="op" points="{x},{y-44} {x},{y+44} {x+80},{y}"/>')
        s.text(x+7, y-20, "+", "pm"); s.text(x+7, y+28, "−", "pm")
        s.text(x+44, y-8, "−", "pm"); s.text(x+44, y+18, "+", "pm")
        s.text(x+10, y-50, name, "ref"); s.text(x+86, y+44, val, "val")
        return {"inp": (x, y-24), "inm": (x, y+24), "outn": (x+62, y-12), "outp": (x+62, y+12), "vocm": (x+30, y+28)}
    def box(s, x, y, w, h, name, val="", pins=(), cls="ic"):
        """pins: (lado, pos, etiqueta, clave). lado l/r/t/b; pos = distancia desde arriba/izquierda."""
        s.rect(x, y, w, h, cls, 3)
        s.text(x + w/2, y - 8, name, "ref", "middle")
        if val: s.text(x + w/2, y + h + 15, val, "val", "middle")
        P = {}
        for side, pos, lab, key in pins:
            if side == "l": px, py, ex, ey, tx, a = x, y+pos, x-12, y+pos, x+5, "start"
            elif side == "r": px, py, ex, ey, tx, a = x+w, y+pos, x+w+12, y+pos, x+w-5, "end"
            elif side == "t": px, py, ex, ey, tx, a = x+pos, y, x+pos, y-12, x+pos, "middle"
            else: px, py, ex, ey, tx, a = x+pos, y+h, x+pos, y+h+12, x+pos, "middle"
            s.wire((px,py),(ex,ey))
            ty = py+4 if side in "lr" else (py+13 if side == "t" else py-5)
            s.text(tx, ty, lab, "pin", a)
            P[key] = (ex, ey)
        return P
    def spdt(s, x, y, name, lab_a, lab_b, pos="a", span=26, dx=44, flip=False):
        """Conmutador: COM en (x,y); contacto a arriba (y-span), b abajo (y+span). Devuelve puntos."""
        sx = -1 if flip else 1
        ca, cb = (x+sx*dx, y-span), (x+sx*dx, y+span)
        s.add(f'<circle class="ct" cx="{x}" cy="{y}" r="2.6"/><circle class="ct" cx="{ca[0]}" cy="{ca[1]}" r="2.6"/><circle class="ct" cx="{cb[0]}" cy="{cb[1]}" r="2.6"/>')
        tgt = ca if pos == "a" else cb
        s.add(f'<line class="blade" x1="{x}" y1="{y}" x2="{tgt[0]-sx*4}" y2="{tgt[1]+(5 if pos=="a" else -5)}"/>')
        s.text(ca[0]+sx*6, ca[1]-4, lab_a, "pin", "start" if sx>0 else "end")
        s.text(cb[0]+sx*6, cb[1]+12, lab_b, "pin", "start" if sx>0 else "end")
        if name: s.text(x, y-span-14, name, "ref", "middle")
        return {"com": (x,y), "a": ca, "b": cb}
    def bnc(s, x, y, name, val="", d="r"):
        s.add(f'<circle class="sym" cx="{x}" cy="{y}" r="11"/><circle class="fillsym" cx="{x}" cy="{y}" r="3"/>')
        s.wire((x,y+11),(x,y+20)); s.gnd(x,y+20)
        s.text(x, y-18, name, "ref", "middle")
        if val: s.text(x, y-32, val, "val", "middle")
        return (x+11, y) if d == "r" else (x-11, y)
    def banana(s, x, y, name, col):
        s.add(f'<circle class="ban" cx="{x}" cy="{y}" r="9" style="stroke:{col}"/><circle class="fillsym" cx="{x}" cy="{y}" r="3.5"/>')
        s.text(x-16, y+4, name, "ref", "end")
        return (x+9, y)
    def svg(s, cls="sch"):
        return (f'<svg class="{cls}" viewBox="0 0 {s.w} {s.h}" width="{s.w}" role="img" aria-label="{esc(s.title)}" '
                f'xmlns="http://www.w3.org/2000/svg">' + "".join(s.e) + '</svg>')
