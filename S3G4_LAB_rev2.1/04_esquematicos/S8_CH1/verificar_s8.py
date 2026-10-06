"""Verifica la netlist de S8 (CH1) contra CH1_PIEZAS_Y_REDES.md.

Uso:  python verificar_s8.py [tabla.md] [netlist.net] [bom.csv]
      (por defecto, los ficheros de esta carpeta)

Lo que se espera se calcula leyendo las tablas del .md; ningún recuento está
escrito a mano. Comprueba, pin a pin, que cada pieza está en su red, que no
sobran ni faltan piezas, pines ni redes, que los no-connect lo son, y que el
campo LCSC coincide con CH1_BOM_precios.csv. Sale con código 1 si hay
alguna diferencia.

Suposiciones (las únicas que no salen del .md, porque la tabla no da el número
de pin; se imprimen al ejecutar):
  - J101: centro = pin 1, cuerpo = pin 2 (Connector:Conn_Coaxial).
  - D104 (1N4148W, SOD-123): cátodo = pin 1, ánodo = pin 2 (Diode:1N4148W).
En las piezas de dos terminales (R, C) el orden de los pines no importa: se
compara el par de redes.
"""
import csv
import os
import re
import sys
from collections import defaultdict

AQUI = os.path.dirname(os.path.abspath(__file__))
MD = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'CH1_PIEZAS_Y_REDES.md')
NET = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, 's8_ch1.net')
BOM = sys.argv[3] if len(sys.argv) > 3 else os.path.join(AQUI, 'CH1_BOM_precios.csv')

SUPOSICIONES = {('J101', 'centro'): '1', ('J101', 'cuerpo'): '2',
                ('D104', 'cátodo'): '1', ('D104', 'ánodo'): '2'}
REF = re.compile(r'\b([A-Z]{1,2}\d{3})\b')
BT = re.compile(r'`([^`]+)`')


def norm(s):
    """Unifica signos y espacios del texto de la tabla."""
    return (s.replace('−', '-').replace('̅', '').replace(' ', ' ')
            .replace('**', '').strip())


texto = norm(open(MD, encoding='utf8').read())
lineas = texto.splitlines()

# ---------------------------------------------------------------- esperado
dos = {}                         # ref -> par de redes (piezas de 2 terminales)
pines = defaultdict(dict)        # ref -> {pin: red}  (None = no-connect)
errores_tabla = []
sw_resumen, sw_tabla = {}, {}    # SW101: (polo, función) -> red, de la fila resumen y de la tabla de pines


def poner(ref, pin, red):
    if pin in pines[ref] and pines[ref][pin] != red:
        errores_tabla.append(f'{ref}.{pin}: la tabla da dos redes ({pines[ref][pin]} y {red})')
    pines[ref][pin] = red


def pinout(ancla):
    """Lee 'N NOMBRE, N NOMBRE, ...' que sigue a `ancla` hasta el primer punto o paréntesis de cierre."""
    i = texto.index(ancla) + len(ancla)
    trozo = re.split(r'\.\s|\.$|\)', texto[i:], maxsplit=1)[0]
    m = {}
    for num, nombre in re.findall(r'(\d+)\s+([^,]+?)\s*(?:,|$)', trozo):
        m[nombre.strip()] = num
    if not m:
        raise SystemExit(f'No se pudo leer el pinout tras «{ancla}»')
    return m


PIN_OPA810 = pinout('tabla 5-1):')
PIN_4051 = pinout('p. 4, tabla 2):')
PIN_AD8039 = pinout('p. 1, figura 3):')
PIN_OPA836 = pinout('tabla 6-1):')
PIN_2N7002 = pinout('Pinout SOT-23 del 2N7002 (')
m = re.search(r'BAV199\.pdf, tabla 2 \(([^)]*)\)', texto)
PIN_BAV199 = {k.strip(): v for v, k in re.findall(r'(\d)\s*=\s*([^,]+)', m.group(1))}


def tablas():
    """Devuelve (sección, cabecera, filas) de cada tabla Markdown."""
    sec, i = '', 0
    while i < len(lineas):
        l = lineas[i]
        if l.startswith('#'):
            sec = l.lstrip('#').strip()
        if l.startswith('|') and i + 1 < len(lineas) and re.match(r'^\|[-| :]+\|$', lineas[i + 1]):
            cab = [c.strip() for c in l.strip('|').split('|')]
            filas, j = [], i + 2
            while j < len(lineas) and lineas[j].startswith('|'):
                filas.append([c.strip() for c in lineas[j].strip('|').split('|')])
                j += 1
            yield sec, cab, filas
            i = j
            continue
        i += 1


def expandir(nombres, redes):
    """'Y1…Y5' con '`CH1_LAD1` … `CH1_LAD5`' y '`CH1_SENSEL_A` / `_B`'."""
    if '…' in nombres:
        a, b = [x.strip() for x in nombres.split('…')]
        pa, na = re.match(r'(\D+)(\d+)', a).groups()
        nb = re.match(r'\D+(\d+)', b).group(1)
        nombres_l = [f'{pa}{k}' for k in range(int(na), int(nb) + 1)]
        ra, rb = redes
        pr, kr = re.match(r'(.*?)(\d+)$', ra).groups()
        redes_l = [f'{pr}{k}' for k in range(int(kr), int(re.search(r'(\d+)$', rb).group(1)) + 1)]
        return list(zip(nombres_l, redes_l))
    nombres_l = [x.strip() for x in re.split(r'\s+y\s+|\s*/\s*', nombres) if x.strip()]
    base = redes[0]
    redes_l = [base if k == 0 else (base.rsplit('_', 1)[0] + r if r.startswith('_') else r)
               for k, r in enumerate(redes)]
    if len(redes_l) == 1:
        redes_l = redes_l * len(nombres_l)
    if len(redes_l) != len(nombres_l):
        raise ValueError(f'no cuadran nombres {nombres_l} y redes {redes_l}')
    return list(zip(nombres_l, redes_l))


for sec, cab, filas in tablas():
    c0 = cab[0].lower()
    if c0 == 'ref' and cab[-1].startswith('Pin'):
        for f in filas:
            refs = REF.findall(f[0])
            col = f[-1]
            if not refs:
                continue
            ref0 = refs[0]
            if any('ver la tabla de pines' in c for c in f):   # SW101: resumen por función
                for polo, cuerpo in re.findall(r'Polo ([AB]):\s*(.+?)(?=Polo [AB]:|$)', col):
                    for funcion, resto in re.findall(r'(común|DC|AC|GND) → ([^;.]+)', cuerpo):
                        red = BT.findall(resto)
                        sw_resumen[(polo, funcion)] = red[0] if red else None
                continue
            if 'centro' in col and 'cuerpo' in col:      # J101
                for parte in col.split(';'):
                    clave = 'centro' if 'centro' in parte else 'cuerpo'
                    poner(ref0, SUPOSICIONES[(ref0, clave)], BT.findall(parte)[0])
                continue
            if 'ánodo de D1' in col:                      # D101, BAV199
                for parte in col.split(';'):
                    red = BT.findall(parte)[0]
                    if 'ánodo de D1' in parte:
                        poner(ref0, PIN_BAV199['A1'], red)
                    elif 'cátodo de D2' in parte:
                        poner(ref0, PIN_BAV199['K2'], red)
                    elif 'punto común' in parte:
                        poner(ref0, PIN_BAV199['K1/A2'], red)
                continue
            if re.search(r'\bpin(es)?\s+\d', col):       # D102 / D103
                for nums, red in re.findall(r'pin(?:es)?\s+([\d y]+?)\s*(?:\([^)]*\))?\s*→\s*`([^`]+)`', col):
                    for n in re.findall(r'\d+', nums):
                        poner(ref0, n, red)
                for red, nums in re.findall(r'`([^`]+)`\s*\(pin(?:es)?\s+([\d y]+)\)', col):
                    for n in re.findall(r'\d+', nums):
                        poner(ref0, n, red)
                continue
            if re.search(r'\b[DGS] → ', col):            # Q101
                for letra, red in re.findall(r'\b([DGS]) → `([^`]+)`', col):
                    poner(ref0, PIN_2N7002[letra], red)
                continue
            if 'ánodo →' in col:                          # D104
                for parte in col.split(';'):
                    clave = 'ánodo' if 'ánodo' in parte else 'cátodo'
                    poner(ref0, SUPOSICIONES[(ref0, clave)], BT.findall(parte)[0])
                continue
            if re.search(r'\b[A-Z]{1,2}\d{3}:', col):     # pareja en serie
                for parte in col.split(';'):
                    r = REF.search(parte).group(1)
                    a, b = BT.findall(parte)[:2]
                    dos[r] = tuple(sorted((a, b)))
                continue
            redes = BT.findall(col)
            if len(redes) >= 2 and '–' in col:          # dos terminales (una o varias piezas)
                for r in refs:
                    dos[r] = tuple(sorted(redes[:2]))
                continue
            errores_tabla.append(f'Fila sin interpretar en «{sec}»: {f}')
    elif c0 == 'pin' and len(cab) == 3 and 'Función' in cab[1]:     # K101
        for f in filas:
            nums = re.findall(r'\d+', f[0])
            red = BT.findall(f[2])
            for n in nums:
                poner('K101', n, red[0] if red else None)
    elif c0 == 'pin' and 'Polo A' in cab:                            # SW101
        for f in filas:
            nums = re.findall(r'\d+', f[0])
            if len(nums) != 2:
                continue                       # patas MP: sin conexión eléctrica en el esquema
            funcion = 'común' if 'común' in f[1] else f[1].split('=')[-1].strip()
            for n, celda, polo in zip(nums, (f[2], f[3]), 'AB'):
                red = BT.findall(celda)
                poner('SW101', n, red[0] if red else None)
                sw_tabla[(polo, funcion)] = red[0] if red else None
    elif c0 == 'pin' and len(cab) == 2:                              # U101 / U102
        es_mux = any(f[0].startswith('Y') for f in filas)
        ref, mapa = ('U102', PIN_4051) if es_mux else ('U101', PIN_OPA810)
        for f in filas:
            for nombre, red in expandir(f[0], BT.findall(f[1])):
                poner(ref, mapa[nombre], red)

if sw_resumen != sw_tabla:
    errores_tabla.append(f'SW101: la fila resumen {sw_resumen} no coincide con la tabla de pines {sw_tabla}')

# Frases de U103, U105 y U106
for ref in ('U103', 'U105'):
    for unidad in 'AB':
        m = re.search(ref + unidad + r':\s*(.+?)\s*(?:\(×[^)]*\))?\.(?:\s|$)', texto)
        for item in m.group(1).split(','):
            redes = BT.findall(item)
            nombres = BT.sub('', item).strip()
            for nombre in re.split(r'\s+y\s+', nombres):
                poner(ref, PIN_AD8039[f'{nombre.strip()} {unidad}'], redes[0])
    m = re.search(ref + r'B:.*?V\+ / V- → `([^`]+)` / `([^`]+)`', texto, re.S)
    poner(ref, PIN_AD8039['V+'], m.group(1))
    poner(ref, PIN_AD8039['V-'], m.group(2))
m = re.search(r'U106:\s*(.+?)\s*\(tabla 6-1', texto)
for item in m.group(1).split(','):
    red = BT.findall(item)[0]
    nombre = BT.sub('', item).replace('→', '').strip()
    poner('U106', PIN_OPA836[nombre], red)

# K101: los pines 5 y 6 «sin función» y el 7 marcado no-connect ya están como None.

esperado_refs = set(dos) | set(pines)
redes_esperadas = set(r for par in dos.values() for r in par) | \
    set(r for d in pines.values() for r in d.values() if r)

# §3: lista de redes propias declarada en el .md
sec3 = texto[texto.index('## 3. Cuenta'):texto.index('## 4.')]
redes_sec3 = set()
for red in BT.findall(sec3.split('más las globales')[0]):
    if '…' in red:
        continue
    redes_sec3.add(red)
for pref, a, b in re.findall(r'`(CH1_[A-Z]+?)(\d+)`…`CH1_[A-Z]+?(\d+)`', sec3):
    for k in range(int(a), int(b) + 1):
        redes_sec3.add(f'{pref}{k}')
globales = set(BT.findall(texto[texto.index('## 1.'):texto.index('## 2.')].split('| Etiqueta')[1]))
globales = {g for g in globales if re.match(r'^[+\-A-Z0-9_]+$', g) and not g.startswith('_')}
# '`CH1_SENSEL_A`, `_B`, `_C`' en el §1
for base in re.findall(r'`(CH1_[A-Z]+)_A`, `_B`, `_C`', texto):
    globales |= {f'{base}_A', f'{base}_B', f'{base}_C'}

# ----------------------------------------------------------------- netlist
TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')


def parse(ts, i=0):
    out = []
    while i < len(ts):
        t = ts[i]
        if t == '(':
            sub, i = parse(ts, i + 1)
            out.append(sub)
        elif t == ')':
            return out, i + 1
        else:
            out.append(t[1:-1] if t.startswith('"') else t)
            i += 1
    return out, i


arbol = parse(TOK.findall(open(NET, encoding='utf8').read()))[0][0]


def hijo(n, k):
    return [x for x in n if isinstance(x, list) and x and x[0] == k]


real = defaultdict(dict)
campos = {}
for comp in hijo(hijo(arbol, 'components')[0], 'comp'):
    ref = hijo(comp, 'ref')[0][1]
    f = {}
    for fs in hijo(comp, 'fields'):
        for fl in hijo(fs, 'field'):
            nombre = [x for x in fl if isinstance(x, list) and x[0] == 'name'][0][1]
            f[nombre] = fl[-1] if isinstance(fl[-1], str) else ''
    campos[ref] = f
for net in hijo(hijo(arbol, 'nets')[0], 'net'):
    nombre = hijo(net, 'name')[0][1].lstrip('/')
    for nodo in hijo(net, 'node'):
        ref, pin = hijo(nodo, 'ref')[0][1], hijo(nodo, 'pin')[0][1]
        real[ref][pin] = None if nombre.startswith('unconnected-') else nombre
refs_reales = set(campos)

# ---------------------------------------------------------------- comparar
dif = []
for e in errores_tabla:
    dif.append('TABLA: ' + e)
for r in sorted(esperado_refs - refs_reales):
    dif.append(f'Falta la pieza {r}')
for r in sorted(refs_reales - esperado_refs):
    dif.append(f'Pieza de más: {r}')
for r in sorted(esperado_refs & refs_reales):
    if r in dos:
        pr = real[r]
        if set(pr) != {'1', '2'}:
            dif.append(f'{r}: pines {sorted(pr)} (se esperaban 1 y 2)')
            continue
        par = tuple(sorted((pr['1'] or 'NC', pr['2'] or 'NC')))
        if par != dos[r]:
            dif.append(f'{r}: redes {par}, la tabla da {dos[r]}')
    else:
        for pin in sorted(set(pines[r]) | set(real[r]), key=lambda p: int(p) if p.isdigit() else 999):
            esp = pines[r].get(pin, 'SIN TABLA')
            act = real[r].get(pin, 'SIN PIN')
            if esp != act:
                dif.append(f'{r}.{pin}: en la netlist {act or "no-connect"}, la tabla da {esp or "no-connect"}')
redes_reales = set(v for d in real.values() for v in d.values() if v)
for n in sorted(redes_esperadas - redes_reales):
    dif.append(f'Falta la red {n}')
for n in sorted(redes_reales - redes_esperadas):
    dif.append(f'Red de más: {n}')
locales_tabla = {n for n in redes_esperadas if n not in globales}
for n in sorted(locales_tabla ^ redes_sec3):
    dif.append(f'§3 del .md y las tablas no coinciden en la red {n}')
for n in sorted({x for x in redes_esperadas if x in globales} - globales):
    dif.append(f'Global sin declarar en §1: {n}')

lcsc = {}
with open(BOM, encoding='utf8') as fh:
    for fila in csv.DictReader(fh):
        for r in fila['refs'].split():
            lcsc[r] = fila['lcsc']
for r in sorted(refs_reales):
    if lcsc.get(r, '') != campos[r].get('LCSC', ''):
        dif.append(f'{r}: LCSC «{campos[r].get("LCSC", "")}», el CSV da «{lcsc.get(r, "")}»')

# ---------------------------------------------------------------- informe
n_pines = sum(2 for _ in dos) + sum(len(d) for d in pines.values())
print(f'Tabla: {MD}')
print(f'Netlist: {NET}')
print('Suposiciones de numeración (la tabla no da el número):')
for (r, k), v in SUPOSICIONES.items():
    print(f'  {r} {k} = pin {v}')
print(f'Esperado según la tabla: {len(esperado_refs)} piezas ({len(dos)} de dos terminales), '
      f'{n_pines} pines, {len(redes_esperadas)} redes '
      f'({len(locales_tabla)} propias de CH1, {len(redes_esperadas) - len(locales_tabla)} globales), '
      f'{sum(1 for d in pines.values() for v in d.values() if v is None)} no-connect')
print(f'Netlist: {len(refs_reales)} piezas, {len(redes_reales)} redes')
if dif:
    print(f'\n{len(dif)} DIFERENCIAS:')
    for d in dif:
        print('  -', d)
    sys.exit(1)
print('\nSin diferencias: cada pin de cada pieza está en la red que da la tabla.')
sys.exit(0)
