"""Auditoría Claude S11.4, D5: tensión disponible a 100 µA (riel -2 %) recalculada desde el .raw del barrido T1.
Uso: python d5_raw.py <T1_..._r0d98_i0d0001_..._sweep_...raw>"""
import sys
from pathlib import Path
import numpy as np
exec(open(Path(__file__).with_name('pulso_esd.py'), encoding='utf-8').read().split('d = Path')[0])
x = raw(Path(sys.argv[1])); v = x['v(vin)']; isrc = np.abs(x['i(vsense)']); idut = np.abs(x['i(vdut)'])
ok = isrc >= 0.99 * 100e-6; print('V máx con I_fuente >= 99 uA:', round(float(v[ok].max()), 6))
k = np.argmin(np.abs(v - 3.5)); print('a 3.5 V: I_fuente', round(isrc[k] * 1e6, 3), 'uA; I_DUT', round(idut[k] * 1e6, 3), 'uA')
