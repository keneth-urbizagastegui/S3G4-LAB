"""Auditoría Claude S11.4: envolvente de ESD si el GDT NO ceba a tiempo (GDT lento).

Copia los decks T2 de Codex (sólo lectura), pone GDC=GIMP=100 kV (el GDT no ceba nunca)
y los guarda en <salida>; después se ejecutan con LTspice -b y se miden con pulso_esd.py.
Uso: python envolvente_sin_gdt.py <carpeta S11_4> <salida>
"""
import sys
from pathlib import Path
src, out = Path(sys.argv[1]), Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
for p in sorted(src.glob('T2_*gdc420*.cir')):
    if 'p1_b0_r1_' not in p.name: continue          # riel nominal, alimentado: un caso por modo/estímulo/signo
    s = p.read_text(encoding='utf-8', errors='replace')
    s = s.replace('.param GDC=420 GIMP=1000', '.param GDC=100k GIMP=100k')
    assert 'GDC=100k' in s
    (out / p.name.replace('gdc420', 'gdcNOFIRE')).write_text(s, encoding='utf-8')
    print(p.name[:80])
