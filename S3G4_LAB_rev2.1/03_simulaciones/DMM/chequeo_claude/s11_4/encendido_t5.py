"""Auditoría Claude S11.4, D6: qué pasa al ENCENDER tras el fallo de red con el DMM apagado.

Toma el deck T5 apagado de Codex (sólo lectura), cierra el interruptor de carga y las cargas
de riel en t = 12 s (2 s después de retirar la red) y sigue hasta 12.2 s.
Uso: python encendido_t5.py <deck_T5_p0.cir> <carpeta_salida>
"""
import sys, re
from pathlib import Path
src = Path(sys.argv[1]); out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
s = src.read_text(encoding='utf-8', errors='replace')
s = s.replace('Rloadswp preg rp {if(POWER==1,1u,1e18)}', 'Sonp preg rp pon 0 RELAY')
s = s.replace('Rloadswn rn nreg {if(POWER==1,1u,1e18)}', 'Sonn rn nreg pon 0 RELAY')
s = re.sub(r'^Rloadp rp 0 .*$', 'Sldp rp lp pon 0 RELAY\nRlp lp 0 {4.9/.003}', s, flags=re.M)
s = re.sub(r'^Rloadn rn 0 .*$', 'Sldn rn ln pon 0 RELAY\nRln ln 0 {4.9/.003}', s, flags=re.M)
s = s.replace('.tran 0 12.0 0 5e-05', '.tran 0 12.2 0 5e-05\nVpon pon 0 PWL(0 0 12 0 12.0001 1)')
s = re.sub(r'^\.meas.*$', '', s, flags=re.M)
meas = ['.meas tran n2_pre FIND V(n2) AT 11.999']
for t in ('12.0002', '12.0005', '12.001', '12.002', '12.005', '12.01', '12.05', '12.1', '12.2'):
    meas.append(f'.meas tran n2_{t.replace(".", "d")} FIND V(n2) AT {t}')
meas += ['.meas tran x0_12d2 FIND V(x0) AT 12.2', '.meas tran rp_12d01 FIND V(rp) AT 12.01', '.meas tran rn_12d01 FIND V(rn) AT 12.01']
head, tail = s.rsplit('\n.end', 1)  # el último .end, no un .ends
s = head + '\n' + '\n'.join(meas) + '\n.end' + tail
dst = out / 'T5_encendido.cir'; dst.write_text(s, encoding='utf-8'); print(dst)
