"""Verifica CH2 y CH3 contra CH1, que ya está verificado (S8b).

CH2 y CH3 son copias de CH1 (DECISIONS 6 oct: AD8039 en los tres canales;
S9: solo cambia el filtro). Así que la verdad de CH2/CH3 se deriva de la
netlist de CH1 que `verificar_s8.py` ya dio por buena (`S8_CH1/s8_ch1.net`):

  - referencias 1xx -> N xx  (R123 -> R223 / R323; K101 -> K201 / K301);
  - redes CH1_* -> CHN_*; las demás (rieles, masas, RELAY_COM) no cambian;
  - los cambios del filtro de CH2_PIEZAS_Y_REDES.md §2 (CAMBIOS abajo).

Compara, pieza a pieza: valor, huella, campo LCSC y la red de cada pin.
Con la netlist del proyecto entero comprueba también que CH1 sigue igual
que en S8b (N = 1, sin cambios).

Uso:  python verificar_ch23.py proyecto.net [s8_ch1.net]
Sale con código 1 si hay alguna diferencia.
"""
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
NET = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 's10_ch23.net')
BASE = sys.argv[2] if len(sys.argv) > 2 else os.path.join(AQUI, '..', 'S8_CH1', 's8_ch1.net')

# Filtro de CH2/CH3 a 1 MHz (S9: RFILT1 = 2.37 kΩ, RFILT2 = 1.10 kΩ, mismos condensadores).
# Referencias de CH1; se aplican a CH2 y CH3 tras renumerar. None = la pieza no existe.
CAMBIOS = {
    'R123': ('2.2k', 'C4190'),    # RFILT1 = 2.2 kΩ + 150 Ω = 2.35 kΩ (−0.84 %)
    'R124': ('2.2k', 'C4190'),
    'R148': ('150', 'C22808'),
    'R149': ('150', 'C22808'),
    'R125': ('1.1k', 'C22764'),   # RFILT2 = 1.1 kΩ, una sola pieza
    'R126': ('1.1k', 'C22764'),
    'R138': None,                 # en CH1 iban en paralelo para hacer 499 Ω
    'R139': None,
}


def tokens(texto):
    return re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', texto)


def arbol(toks):
    pila = [[]]
    for t in toks:
        if t == '(':
            pila.append([])
        elif t == ')':
            n = pila.pop()
            pila[-1].append(n)
        else:
            pila[-1].append(t[1:-1] if t.startswith('"') else t)
    return pila[0][0]


def hijos(nodo, nombre):
    return [h for h in nodo[1:] if isinstance(h, list) and h and h[0] == nombre]


def valor(nodo, nombre):
    h = hijos(nodo, nombre)
    return h[0][1] if h and len(h[0]) > 1 else None


def leer(ruta):
    raiz = arbol(tokens(open(ruta, encoding='utf-8').read()))
    piezas, pines = {}, {}
    for c in hijos(hijos(raiz, 'components')[0], 'comp'):
        ref = valor(c, 'ref')
        lcsc = None
        for f in hijos(hijos(c, 'fields')[0], 'field') if hijos(c, 'fields') else []:
            if valor(f, 'name') == 'LCSC':
                lcsc = f[2] if len(f) > 2 and isinstance(f[2], str) else None
        piezas[ref] = (valor(c, 'value'), valor(c, 'footprint'), lcsc)
    for n in hijos(hijos(raiz, 'nets')[0], 'net'):
        nombre = valor(n, 'name')
        for nodo in hijos(n, 'node'):
            pines[(valor(nodo, 'ref'), valor(nodo, 'pin'))] = nombre
    return piezas, pines


def red_corta(nombre):
    """'/CH2/CH2_TAP' -> 'CH2_TAP'; 'unconnected-(K201-Pad5)' -> 'NC'."""
    if nombre.startswith('unconnected-') or nombre.startswith('Net-('):
        return 'NC' if nombre.startswith('unconnected-') else 'SIN_NOMBRE'
    return nombre.rsplit('/', 1)[-1]


def canal(ref):
    m = re.fullmatch(r'([A-Z]+)(\d)(\d\d)', ref)
    return (m.group(1), int(m.group(2)), m.group(3)) if m else None


def esperado(base_piezas, base_pines, n):
    piezas, pines = {}, {}
    for ref, (val, fp, lcsc) in base_piezas.items():
        c = canal(ref)
        if not c or c[1] != 1:
            continue
        if n != 1 and ref in CAMBIOS:
            if CAMBIOS[ref] is None:
                continue
            val, lcsc = CAMBIOS[ref]
        piezas[f'{c[0]}{n}{c[2]}'] = (val, fp, lcsc)
    for (ref, pin), red in base_pines.items():
        c = canal(ref)
        if not c or c[1] != 1 or (n != 1 and CAMBIOS.get(ref, 0) is None):
            continue
        r = red_corta(red)
        r = re.sub(r'^CH1_', f'CH{n}_', r)
        pines[(f'{c[0]}{n}{c[2]}', pin)] = r
    return piezas, pines


def comparar(n, esp, real):
    (ep, epin), (rp, rpin) = esp, real
    rp = {k: v for k, v in rp.items() if canal(k) and canal(k)[1] == n}
    rpin = {k: red_corta(v) for k, v in rpin.items() if canal(k[0]) and canal(k[0])[1] == n}
    err = []
    for ref in sorted(set(ep) | set(rp)):
        if ref not in rp:
            err.append(f'falta {ref}')
        elif ref not in ep:
            err.append(f'sobra {ref}')
        elif ep[ref] != rp[ref]:
            err.append(f'{ref}: esperado {ep[ref]}, hay {rp[ref]}')
    for k in sorted(set(epin) | set(rpin)):
        if k[0] not in rp or k[0] not in ep:
            continue
        if epin.get(k) != rpin.get(k):
            err.append(f'{k[0]} pin {k[1]}: esperado {epin.get(k)}, hay {rpin.get(k)}')
    redes = {r for r in epin.values() if r != 'NC'}
    print(f'CH{n}: {len(ep)} piezas y {len(epin)} pines esperados, {len(redes)} redes; '
          f'{len(rp)} piezas en la netlist; {len(err)} diferencias')
    for e in err[:60]:
        print('   ', e)
    return err


def main():
    base = leer(BASE)
    real = leer(NET)
    canales = sorted({canal(r)[1] for r in real[0] if canal(r)} & {1, 2, 3})
    if not canales:
        print('La netlist no tiene piezas de CH1, CH2 ni CH3')
        return 1
    total = 0
    for n in canales:
        total += len(comparar(n, esperado(*base, n), real))
    for n in (2, 3):
        if n not in canales:
            print(f'CH{n}: no hay piezas en la netlist')
            total += 1
    print('Sin diferencias.' if total == 0 else f'{total} diferencias en total.')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main())
