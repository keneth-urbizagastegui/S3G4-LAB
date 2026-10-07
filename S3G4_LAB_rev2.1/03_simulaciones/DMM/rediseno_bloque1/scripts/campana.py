import json, csv
from run1 import one
cases = []
def add(name, **kw): cases.append((name, kw))
# O0 referencia (PTC 200 + TVS + Rs a rieles)
add('O0_ptc200_rs330', opt='O0', rptc=200., rs=330.)
add('O0_ptc200_rs330_zen', opt='O0', rptc=200., rs=330., zener=True)
# O1: proteccion a COM + bloqueo de cuerpo
for ph in (0, 90):
    for rp_ in (200., 250.):
        for rs in (330., 1000.):
            add(f'O1_ptc{int(rp_)}_rs{int(rs)}_ph{ph}', opt='O1', rptc=rp_, rs=rs, ph=ph)
add('O1_hot35k_rs330', opt='O1', rptc=35e3, rs=330.)
# O2: limitador bidireccional de deplexion
for il in (1.5e-3, 2.5e-3, 5e-3, 10e-3):
    for ph in (0, 90):
        add(f'O2_ilim{il*1e3:g}mA_rs100_ph{ph}', opt='O2', ilim=il, ron_lim=700., rs=100., ph=ph)
# O3: estilo 121GW: PTC 570 + 1630 = 2.2k
for rs, op in ((3300., 'O0'), (1000., 'O1')):
    for ph in (0, 90):
        add(f'O3_{op}_ptc570_r1630_rs{int(rs)}_ph{ph}', opt=op, rptc=570., rser=1630., rs=rs, ph=ph)
add('O3_O0_rs3300_zen', opt='O0', rptc=570., rser=1630., rs=3300., zener=True)
add('O3_hot35k_O0_rs3300', opt='O0', rptc=35e3, rser=1630., rs=3300.)
# O4 dato: 60 V sin PTC (R fija 2.2k), solo R + TVS + Rs a rieles
add('O4_60Vdc_pos', opt='O0', rptc=1e-3, rser=2200., rs=3300., grid='dc', vdc=60)
add('O4_60Vdc_neg', opt='O0', rptc=1e-3, rser=2200., rs=3300., grid='dc', vdc=-60)
add('O4_60Vpk_ac', opt='O0', rptc=1e-3, rser=2200., rs=3300., vac=60.)
rows = []
for n, kw in cases:
    kw2 = dict(kw)
    try:
        r = one(n, **kw2)
    except Exception as e:
        r = {'name': n, 'error': str(e)}
    rows.append(r); print(n, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k in ('I_pk_A','I_rms_A','P_tvs_avg_W','span_max_V','I_body_pk_A','I_cut_1ms_after_zc_A','P_lim_pk_W','error')}, flush=True)
json.dump(rows, open('campana1.json', 'w'), indent=1)
