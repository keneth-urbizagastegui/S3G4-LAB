"""Auditoría S11.3, C6: compliance a 100 uA con el bloqueo BAV199 (base) y con un Schottky
genérico ajustado a VF = 0.24 V a 0.1 mA (máximo de hoja típico de BAT54; modelo supuesto, no de fabricante)."""
import json, numpy as np
from pathlib import Path
src=Path(__file__).with_name('recalcular_raw.py').read_text(encoding='utf-8').split('res = {}')[0]
g={};exec(compile(src,'head','exec'),g)
SCH='.model SCHK D(Is=8.8n N=1 Rs=2 Cjo=10p BV=30)\nDblk bp n2 SCHK'
res={}
for rail in (.98,1,1.02):
    c=g['find'](q='R1',mode='diode',source=.0001,rail=rail)
    for tag,repl in (('BAV199',()),('Schottky',(('Dblk bp n2 BAV199',SCH),))):
        d=g['sim'](f'C6_{tag}_{rail}',c,repl);t=d['time'];vin=d['v(vin)'];i=d['i(vsense)'];m=(t>.002)&(i>=.99e-4)
        res[f'{tag}_rail{rail}']=round(float(np.max(vin[m])),4) if m.any() else None
print(json.dumps(res,indent=1))
