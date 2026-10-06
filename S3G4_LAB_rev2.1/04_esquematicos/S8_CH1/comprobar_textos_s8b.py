"""Busca textos que se pisan en la hoja de CH1 (S8b).

Uso:  python comprobar_textos_s8b.py [s3g4.kicad_sch] [kicad-cli.exe]

Exporta la hoja a SVG con kicad-cli (que escribe cada cadena una segunda vez,
invisible, con x, y, textLength y font-size), construye la caja de cada texto
y comunica:
  - pares de textos cuyas cajas se solapan;
  - textos atravesados por un cable (se ignoran los extremos del cable y los
    textos de pin, que van pegados a su cable por diseño).
Sale con código 1 si encuentra algún solape.
"""
import math
import os
import re
import subprocess
import sys
import tempfile

AQUI = os.path.dirname(os.path.abspath(__file__))
SCH = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, '..', 'kicad', 's3g4.kicad_sch')
CLI = sys.argv[2] if len(sys.argv) > 2 else r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'

tmp = tempfile.mkdtemp()
subprocess.run([CLI, 'sch', 'export', 'svg', '-o', tmp, SCH], check=True,
               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
svg = open(os.path.join(tmp, os.path.splitext(os.path.basename(SCH))[0] + '.svg'),
           encoding='utf-8').read()

TXT = re.compile(r'(?:<g transform="rotate\((-?[\d.]+) ([\d.\-]+) ([\d.\-]+)\)">\s*)?'
                 r'<text x="([\d.\-]+)" y="([\d.\-]+)"\s*textLength="([\d.]+)" font-size="([\d.]+)"'
                 r'[^>]*text-anchor="(\w+)"[^>]*>([^<]*)</text>')


def caja(m):
    ang = float(m.group(1) or 0)
    x, y, L, fs = (float(m.group(i)) for i in (4, 5, 6, 7))
    anc = m.group(8)
    x0 = {'start': x, 'middle': x - L / 2, 'end': x - L}[anc]
    h_arriba, h_abajo = fs * 0.62, fs * 0.15
    pts = [(x0, y - h_arriba), (x0 + L, y - h_arriba), (x0 + L, y + h_abajo), (x0, y + h_abajo)]
    if ang:
        cx, cy = float(m.group(2)), float(m.group(3))
        c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        pts = [(cx + (px - cx) * c - (py - cy) * s, cy + (px - cx) * s + (py - cy) * c)
               for px, py in pts]
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


textos = []
for m in TXT.finditer(svg):
    t = m.group(9).strip()
    if t:
        c = caja(m)
        if not any(t == u and all(abs(a - b) < 0.01 for a, b in zip(c, d)) for u, d in textos):
            textos.append((t, c))

sch = open(SCH, encoding='utf-8').read()
cables = [tuple(map(float, g)) for g in re.findall(
    r'\(wire\s+\(pts\s+\(xy ([\d.\-]+) ([\d.\-]+)\)\s+\(xy ([\d.\-]+) ([\d.\-]+)\)\s*\)', sch)]


def solapa(a, b, m=0.05):
    return a[0] < b[2] - m and b[0] < a[2] - m and a[1] < b[3] - m and b[1] < a[3] - m


def cruza(c, b, margen=0.15):
    x1, y1, x2, y2 = c
    bx0, by0, bx1, by1 = b[0] + margen, b[1] + margen, b[2] - margen, b[3] - margen
    if bx0 >= bx1 or by0 >= by1:
        return False
    if abs(y1 - y2) < 1e-6:          # horizontal
        return by0 < y1 < by1 and min(x1, x2) < bx1 and max(x1, x2) > bx0 \
            and not (min(x1, x2) >= bx0 and max(x1, x2) <= bx1 and False)
    if abs(x1 - x2) < 1e-6:          # vertical
        return bx0 < x1 < bx1 and min(y1, y2) < by1 and max(y1, y2) > by0
    return False


n = 0
print(f'{len(textos)} textos, {len(cables)} cables')
for i in range(len(textos)):
    for j in range(i + 1, len(textos)):
        if solapa(textos[i][1], textos[j][1]):
            n += 1
            ci = ((textos[i][1][0] + textos[i][1][2]) / 2, (textos[i][1][1] + textos[i][1][3]) / 2)
            print(f'TEXTO/TEXTO  {textos[i][0]!r} x {textos[j][0]!r}  cerca de ({ci[0]:.1f}, {ci[1]:.1f})')
for t, b in textos:
    if re.fullmatch(r'\d{1,2}|[A-Z]\d?|~|\+|-', t):   # números/nombres cortos de pin
        continue
    for c in cables:
        if cruza(c, b):
            n += 1
            print(f'TEXTO/CABLE  {t!r} cerca de ({(b[0] + b[2]) / 2:.1f}, {(b[1] + b[3]) / 2:.1f}) '
                  f'cable ({c[0]:.2f},{c[1]:.2f})-({c[2]:.2f},{c[3]:.2f})')
            break
print(f'{n} solapes')
sys.exit(1 if n else 0)
