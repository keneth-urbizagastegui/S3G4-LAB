"""Lee una netlist de KiCad y escribe las piezas por hoja y las redes de cada pieza.
Uso: python kinet.py netlist.net salida.txt"""
import sys, re, collections
sys.stdout.reconfigure(encoding='utf-8')
TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')

def tree(txt):
    st = [[]]
    for t in TOK.findall(txt):
        if t == '(':
            st.append([])
        elif t == ')':
            n = st.pop(); st[-1].append(n)
        else:
            st[-1].append(t[1:-1] if t.startswith('"') else t)
    return st[0][0]

def ch(n, name): return [h for h in n[1:] if isinstance(h, list) and h and h[0] == name]
def val(n, name):
    h = ch(n, name); return h[0][1] if h and len(h[0]) > 1 else None

root = tree(open(sys.argv[1], encoding='utf-8').read())
pins = collections.defaultdict(list)
for net in ch(ch(root, 'nets')[0], 'net'):
    name = val(net, 'name')
    for nd in ch(net, 'node'):
        pins[val(nd, 'ref')].append((val(nd, 'pin'), val(nd, 'pinfunction') or '', name))
by = collections.defaultdict(list)
for c in ch(ch(root, 'components')[0], 'comp'):
    sp = ch(c, 'sheetpath'); sheet = val(sp[0], 'names') if sp else '?'
    fields = {}
    for f in (ch(ch(c, 'fields')[0], 'field') if ch(c, 'fields') else []):
        if len(f) > 2 and isinstance(f[2], str): fields[val(f, 'name')] = f[2]
    extra = ' '.join(f'{k}={v}' for k, v in fields.items()
                     if k not in ('Footprint', 'Datasheet', 'Description') and v and v != '~')[:70]
    fp = (val(c, 'footprint') or '').split(':')[-1][:26]
    by[sheet].append((val(c, 'ref'), val(c, 'value'), fp, extra))
def key(r): return (re.sub(r'\d', '', r[0]), int(re.sub(r'\D', '', r[0]) or 0))
out = []
for sh, L in by.items():
    out.append(f'\n=== {sh} ({len(L)})')
    for r in sorted(L, key=key):
        nets = '; '.join(f"{p}{('/'+fn) if fn else ''}={n.split('/')[-1]}" for p, fn, n in sorted(pins[r[0]]))
        out.append(f'{r[0]:6s} {str(r[1])[:26]:26s} {r[2]:26s} | {nets[:150]} | {r[3]}')
open(sys.argv[2], 'w', encoding='utf-8').write('\n'.join(out))
print({k: len(v) for k, v in by.items()})
