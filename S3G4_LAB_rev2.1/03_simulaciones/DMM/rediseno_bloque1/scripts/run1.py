import sys, json, os
from gen import *
from rdlib import *
def one(name, **kw):
    opt = kw.pop('opt')
    cir = f'c1_{name}.cir'
    open(cir, 'w').write(build(opt, title=name, **kw))
    raw, log = run(cir)
    d = read_raw(raw)
    r = metrics(d, opt, 0.0500, 0.0667, kw.get('rptc', 200.), kw.get('rs', 330.))
    r['name'] = name
    return r
if __name__ == '__main__':
    r = one('smoke_O0', opt='O0', rptc=200., rs=330.)
    print(json.dumps(r, indent=1))
