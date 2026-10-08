"""Auditoría S11.3: corriente en los diodos internos del HC4051 (proxy ICHC) en los peores casos de ESD
según el CSV de Codex, con RX0/RX1/RX2 variados. Reutiliza recalcular_raw (sin volver a ejecutar su bloque)."""
import json, runpy, sys
from pathlib import Path
import numpy as np
src = Path(__file__).with_name('recalcular_raw.py').read_text(encoding='utf-8').split('res = {}')[0]
g = {}; exec(compile(src, 'recalcular_raw_head', 'exec'), g)
find, sim = g['find'], g['sim']
def clamp(d, pin):
    return 1e3*max(float(np.max(np.abs(d[k]))) for k in d if k.startswith(f'i({pin}:') and ('dhi' in k or 'dlo' in k))
res = {}
casos = {  # peores de s11_3_campaign_audited.csv
  'X0_aire_sinRX': dict(q='R6', amplitude=-8000, mode='v', power=0, body=0, rail=1, rx0=1e-6),
  'X0_contacto_sinRX': dict(q='R6', amplitude=-4000, mode='v', power=1, body=0, rail=1.02, rx0=1e-6),
  'X1_aire_RX100': dict(q='R6', amplitude=8000, mode='v', power=1, body=0, rail=1.02, rx0=100),
  'X1_contacto_RX100': dict(q='R6', amplitude=4000, mode='v', power=1, body=0, rail=1, rx0=100),
}
for tag, kw in casos.items():
    c = g['find'](**kw)
    variantes = [('base', ())]
    if 'X1' in tag: variantes += [(f'RX1_{v}', (('Rx1 x1 hx1 100', f'Rx1 x1 hx1 {v}'),)) for v in (150, 220)]
    else: variantes += [('RX0_100', (('.param RX0=1e-06', '.param RX0=100'),))]
    for vt, repl in variantes:
        d = sim(f'{tag}_{vt}', c, repl)
        res[f'{tag}_{vt}'] = {p+'_mA': round(clamp(d, p), 3) for p in ('xh0', 'xh1', 'xh2', 'xopi')}
print(json.dumps(res, indent=1))
Path(r'C:/s113/claude/inyeccion.json').write_text(json.dumps(res, indent=1))
