"""Audit corrected B OP against original decks, without running any simulation."""
import sys
sys.dont_write_bytecode=True
import json,re,hashlib
from pathlib import Path
import ejecutar_s9_b_op_corregido as c

s=c.s; ROOT=c.ROOT


def main():
    work=ROOT/'S9/B_hoja/op_corregido'
    original=ROOT/'S9/B_hoja/campaign'
    data=json.loads((work/'s9b_op_corregido_checkpoint.json').read_text())
    rows=data['rows']; errors=[]; decks=0
    wanted={(ix,mc) for ix in [0,3,6,9] for mc in range(500)}
    if {(r['ix'],r['mc']) for r in rows}!=wanted or len(rows)!=2000:
        errors.append('Missing/duplicate OP boards')
    digest=hashlib.sha256(c.b.MODEL.read_bytes()).hexdigest()
    lock=json.loads((work/'s9b_op_corregido_lock.json').read_text())
    if lock['model_sha256']!=digest or lock['source_parameter_shift_V']!=c.SHIFT_V:
        errors.append('Model/correction mismatch')
    def normalized(deck):
        return re.sub(r'^\.loadbias .*\n','',deck,flags=re.M)
    states={'gain_negative','gain_zero','gain_positive','dac_low','dac_high','dac_local'}
    by_case={row['id']:{} for row in rows}
    pattern=re.compile(r'^(.+)_(gain_negative|gain_zero|gain_positive|dac_low|dac_high|dac_local)_src')
    # Enumerate the directory once, rather than once for each of 2,000 boards.
    for path in work.glob('*.cir'):
        match=pattern.match(path.name)
        if not match or match[1] not in by_case:
            errors.append('Unexpected OP deck '+path.name)
            continue
        if match[2] in by_case[match[1]]:
            errors.append('Duplicate OP state '+path.name)
        by_case[match[1]][match[2]]=path
    for row in rows:
        indexed=by_case[row['id']]
        fs=list(indexed.values())
        if set(indexed)!=states: errors.append('Six OP states missing '+row['id'])
        for path in fs:
            decks+=1
            text=path.read_text(); old=(original/path.name).read_text()
            if '\n.op\n' not in text or '\n.dc ' in text:
                errors.append('Non-OP deck '+path.name)
            instance=re.search(r'^XCH BNC [^\n]+',text,re.M)[0]
            offsets=s.sb.realization(row['mc'])['offsets']
            for key,value in offsets.items():
                actual=float(re.search(r'\b'+key+r'=([^\s]+)',instance)[1])
                expected=value+c.SHIFT_V if key in c.KEYS else value
                if actual!=expected: errors.append('Offset '+key+' '+path.name)
            # Restore only four sources; all remaining deck bytes must match,
            # apart from the path of the copied Newton recommendation.
            def restore(match):
                line=match[0]
                for key in c.KEYS:
                    line=re.sub(r'\b'+key+r'=([^\s]+)',key+'='+format(offsets[key],'.17g'),line)
                return line
            restored=re.sub(r'^XCH BNC [^\n]+',restore,text,flags=re.M)
            if normalized(restored)!=normalized(old):
                errors.append('Unexpected circuit/stimulus/settings change '+path.name)
            native=json.loads(path.with_suffix('.native.json').read_text())
            if native['returncode'] or native['errors']:
                errors.append('Native failure '+path.name)
    report=dict(returncode=int(bool(errors)),logical_cases=len(rows),expected=2000,
                decks=decks,model_sha256=digest,source_parameter_shift_V=c.SHIFT_V,effective_offset_shift_V=-c.SHIFT_V,errors=errors,
                method='All six OP decks paired byte-for-byte with original after restoring four offset sources; loadbias path excluded')
    s.write(work/'s9b_op_corregido_auditoria.json',json.dumps(report,indent=2))
    print(json.dumps(report));return report['returncode']


if __name__=='__main__':raise SystemExit(main())
