"""Repeat ONLY B's MC OP cohorts with total LM6172 offset uniform +/-3 mV.

Original campaign and A remain read-only. Six native OP points per board,
same seed, rails, passives and independent draws; only four offset sources shift.
VOS IP IPR {value} SUBTRACTS value at IN+, so cancellation of +2.986 mV
native follower output requires +2.986 mV on the SPICE source parameter.
This is a -2.986 mV shift in effective amplifier offset, as requested.
"""
import sys
sys.dont_write_bytecode = True
import argparse, hashlib, json, re, time
from pathlib import Path
import ejecutar_s9_b as b

s = b.s
ROOT = b.ROOT
SHIFT_V = 2.986e-3  # Explicit auditor/user instruction; K0 measured 2.986006 mV.
KEYS = ('VOA', 'VOB', 'VOFA', 'VOFB')
base_net = s.net


def net(c):
    assert c['variant'] == 'B' and c['s9_test'] == 'K5OP' and c['mc'] >= 0
    deck = base_net(c)
    def shifted(match):
        line = match[0]
        for key in KEYS:
            line, count = re.subn(r'\b' + key + r'=([^\s]+)',
                                  lambda m: key + '=' + format(float(m[1]) + SHIFT_V, '.17g'), line)
            if count != 1:
                raise RuntimeError('Missing or duplicate LM offset ' + key)
        return line
    return re.sub(r'^XCH BNC [^\n]+', shifted, deck, flags=re.M)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--resume', action='store_true')
    ap.add_argument('--smoke', action='store_true')
    args = ap.parse_args()
    gate = json.loads((ROOT/'resultados/s9b_puerta_k0.json').read_text())
    digest = hashlib.sha256(b.MODEL.read_bytes()).hexdigest()
    if not gate['passed'] or gate['model_sha256'] != digest:
        raise RuntimeError('K0/model mismatch')
    s.FILTERS.update(json.loads((ROOT/'resultados/s9_filtros.json').read_text()))
    campaign = ROOT/'S9/B_hoja/campaign'
    work = ROOT/'S9/B_hoja'/('op_corregido_smoke' if args.smoke else 'op_corregido')
    work.mkdir(parents=True, exist_ok=True)
    specification = dict(model_sha256=digest,source_parameter_shift_V=SHIFT_V,effective_offset_shift_V=-SHIFT_V,keys=KEYS,seed=s.SEED,
                         method='Six independent OP states; only LM6172 MC sources shifted')
    lock = work/'s9b_op_corregido_lock.json'
    if lock.exists() and json.loads(lock.read_text()) != json.loads(json.dumps(specification)):
        raise RuntimeError('Resume correction/model specification mismatch')
    s.write(lock,json.dumps(specification,indent=2))
    # Reuse solved campaign recommendations without altering originals.
    for ix in [0,3,6,9]:
        for mc in range(2 if args.smoke else 500):
            bias = campaign/(b.bcase('K5AC',ix,mc)['id']+'.bias')
            target = work/bias.name
            if bias.exists() and not target.exists():
                s.write(target,bias.read_text())
        bias = campaign/(b.bcase('K1',ix)['id']+'.bias')
        if bias.exists() and not (work/bias.name).exists():
            s.write(work/bias.name,bias.read_text())
    before = s.protected() | b.a_guard()
    s.write(work/'protected_before.json',json.dumps(before))
    s.net = net
    start = time.perf_counter()
    rows, records = [], []
    for ix in [0,3,6,9]:
        batch = [b.bcase('K5OP',ix,mc) for mc in range(2 if args.smoke else 500)]
        rr, extras, recs = s.execute(batch,work,args.resume)
        rows += rr
        records += recs
        s.csv_write(work/'s9b_op_corregido_all.csv',rows,s.FIELDS)
        s.write(work/'s9b_op_corregido_checkpoint.json',json.dumps(dict(rows=rows,records=records)))
    after = s.protected() | b.a_guard()
    changed = [k for k,v in before.items() if after.get(k) != v]
    s.write(work/'protected_after.json',json.dumps(after))
    expected = 8 if args.smoke else 2000
    meta = dict(specification,logical_cases=expected,successful=len(rows),
                simulations=sum('_analysis_attempt' not in r['id'] for r in records),
                seconds=time.perf_counter()-start,workers=10,protected_changed=changed,
                returncode=int(len(rows)!=expected or bool(changed)))
    s.write(work/'s9b_op_corregido_meta.json',json.dumps(meta,indent=2))
    if not args.smoke:
        s.csv_write(ROOT/'resultados/s9b_op_corregido.csv',rows,s.FIELDS)
    print(json.dumps(meta),flush=True)
    return meta['returncode']


if __name__ == '__main__':
    raise SystemExit(main())
