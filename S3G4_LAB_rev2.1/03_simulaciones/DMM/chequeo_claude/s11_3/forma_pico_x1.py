"""Forma del pico de corriente en el diodo interno de X1 (proxy ICHC): anchura y carga, para separar físico de artefacto."""
import numpy as np, glob, os
from pathlib import Path
src=Path(__file__).with_name('recalcular_raw.py').read_text(encoding='utf-8').split('def find')[0]
g={};exec(src,g)
for f in sorted(x for x in glob.glob(r'C:/s113/claude/X1_*.raw') if not x.endswith('.op.raw')):
    d=g['readraw'](Path(f));t=d['time']
    i=sum(np.abs(d[k]) for k in d if k.startswith('i(xh1:d'))
    k=int(np.argmax(i));pk=i[k];dt=np.diff(t)
    w50=float(np.sum(dt[(i[:-1]>pk/2)]));w2=float(np.sum(dt[(i[:-1]>2e-3)]))
    q=float(np.trapezoid(i,t))
    print(os.path.basename(f)[:28],f"pk={pk*1e3:.2f}mA t={t[k]*1e9:.2f}ns ancho50%={w50*1e9:.3f}ns t>2mA={w2*1e9:.2f}ns Q={q*1e9:.3f}nC paso_local={dt[max(k-1,0)]*1e12:.1f}ps")
# Pico "sostenido": máximo del mínimo móvil sobre 20 ns (descarta picos de una sola muestra).
print('--- pico sostenido >=20 ns (X0 y X1) ---')
for f in sorted(x for x in glob.glob(r'C:/s113/claude/X*.raw') if not x.endswith('.op.raw')):
    d=g['readraw'](Path(f));t=d['time']
    for pin in ('xh0','xh1'):
        i=sum(np.abs(d[k]) for k in d if k.startswith(f'i({pin}:d'))
        n=20; s=np.lib.stride_tricks.sliding_window_view(i,n).min(axis=1) if len(i)>n else i
        print(os.path.basename(f)[:30],pin,f"bruto={i.max()*1e3:.2f}mA sostenido20ns={s.max()*1e3:.2f}mA")
