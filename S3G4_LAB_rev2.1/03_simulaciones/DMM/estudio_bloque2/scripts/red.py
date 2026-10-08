# -*- coding: utf-8 -*-
"""Modelo lineal del frontal de tensión (bloque 2): R_PROT, divisor compensado, capacidades del mux y del amplificador.
Análisis nodal complejo; sin dependencias salvo numpy/scipy."""
import numpy as np
from scipy.optimize import least_squares

# --- valores nominales (bloque 1 cerrado) ---
NOM = dict(Rprot=99e3, Rs100=100.0, Ron=100.0,
           Rt=3e6, Ct=100e-12, Rd=3.3e3, R2=900e3, C2=330e-12, R3=100e3, C3=3.0e-9,
           # capacidades parásitas (suposiciones salvo las del 4051 y la OPA2188, que son de hoja/modelo)
           C_bav=4e-12,      # BAV199 en el nodo (2 diodos, ~2 pF cada uno a 0 V; hoja BAV199)
           C_ypin=5e-12,     # pata Yn del 74HC4051 (hoja Nexperia: 5 pF)
           C_pcb_pre=3e-12,  # pistas/pads antes del 100 ohm (suposición)
           C_z=25e-12,       # pata común Z del 74HC4051 (hoja: 25 pF)
           C_pcb_com=3e-12,  # nodo común hasta la entrada del amplificador (suposición)
           C_amp=9.5e-12,    # OPA2188: modo común 9.5 pF por entrada (hoja/modelo TI)
           gbw=2e6)

def par(**kw):
    p = dict(NOM); p.update(kw); return p

def _solve(Y, I):
    return np.linalg.solve(Y, I)

def h_x0(f, p):
    """V(com)/Vin en el camino X0: Rprot -> nodo (BAV199+Yn+pcb) -> 100 ohm + Ron -> COM (Z + pcb + amp)."""
    s = 2j*np.pi*np.asarray(f)
    Cpre = p['C_bav']+p['C_ypin']+p['C_pcb_pre']
    Ccom = p['C_z']+p['C_pcb_com']+p['C_amp']
    Rsw = p['Rs100']+p['Ron']
    out = []
    for si in np.atleast_1d(s):
        Y = np.array([[1/p['Rprot']+si*Cpre+1/Rsw, -1/Rsw],
                      [-1/Rsw, 1/Rsw+si*Ccom]])
        I = np.array([1/p['Rprot'], 0])
        out.append(_solve(Y, I)[1])
    return np.array(out)

def h_div(f, p, sel):
    """Divisor completo; sel = 1 (X1, ÷10) o 2 (X2, ÷100). Devuelve V(com)/Vin."""
    s = 2j*np.pi*np.atleast_1d(np.asarray(f, dtype=float))
    Rsw1 = p['Rs100']+p['Ron']          # X1 lleva 100 ohm; X2 no
    Rsw2 = p['Ron']
    Cpre1 = p['C_bav']+p['C_ypin']+p['C_pcb_pre']   # X1 siempre carga el nodo ÷10 con BAV199+pata+pcb
    Cpre2 = p['C_ypin']+p['C_pcb_pre']              # X2: pata + pcb (sin BAV199)
    Ccom = p['C_z']+p['C_pcb_com']+p['C_amp']
    out = []
    for si in s:
        Ysec = 1/p['Rt'] + 1/(p['Rd']+1/(si*p['Ct']))
        # nodos: a, b, t1, t2, c (COM)
        # fuente Vin=1 -> sección1 -> a -> sección2 -> b -> sección3 -> t1 -> (R2||C2) -> t2 -> (R3||C3) -> gnd
        Y2 = 1/p['R2']+si*p['C2']; Y3 = 1/p['R3']+si*p['C3']
        n = 5
        Y = np.zeros((n, n), complex); I = np.zeros(n, complex)
        # 0:a 1:b 2:t1 3:t2 4:c
        def add(i, j, y):
            if i is not None: Y[i, i] += y
            if j is not None: Y[j, j] += y
            if i is not None and j is not None: Y[i, j] -= y; Y[j, i] -= y
        add(0, None, Ysec); I[0] += Ysec*1            # sección1 desde Vin (Norton)
        add(0, 1, Ysec); add(1, 2, Ysec)
        add(2, 3, Y2); add(3, None, Y3)
        # cargas fijas del nodo no seleccionado
        if sel == 1:
            add(2, 4, 1/Rsw1); add(2, None, si*Cpre1); add(3, None, si*Cpre2)
        else:
            add(3, 4, 1/Rsw2); add(3, None, si*Cpre2); add(2, None, si*Cpre1)
        add(4, None, si*Ccom)
        out.append(_solve(Y, I)[4])
    return np.array(out)

def amp_pole(f, G, gbw):
    return 1/(1+1j*np.asarray(f)/(gbw/G))

def dc(h_fn, p, *a):
    return h_fn(np.array([1e-3]), p, *a)[0].real

def err_pct(h, h0):
    return (np.abs(h)/abs(h0)-1)*100

if __name__ == '__main__':
    f = np.array([40, 100, 300, 1e3, 3e3, 10e3, 20e3])
    p = par()
    h0 = h_x0(np.array([1e-3]), p)[0]
    print('X0 error %:', np.round(err_pct(h_x0(f, p), h0), 2))
    for sel in (1, 2):
        h0 = h_div(np.array([1e-3]), p, sel)[0]
        print('X%d DC %.5f  error %%:' % (sel, abs(h0)), np.round(err_pct(h_div(f, p, sel), h0), 2))

# ---------- variante con buffers antes del mux (X0 y X1 con OPA2192 de entrada RRIO) ----------
def h_x0_buf(f, p, Cbuf=6e-12):
    s = 2j*np.pi*np.atleast_1d(np.asarray(f, dtype=float))
    C = p['C_bav']+p['C_pcb_pre']+Cbuf
    R = p['Rprot']+p['Rs100']
    return 1/(1+s*R*C)

def h_div_buf(f, p, sel, Cbuf=6e-12, buf2=False):
    """sel=1: X1 con buffer (la toma ÷10 ve siempre la misma carga). sel=2: X2 (con o sin buffer)."""
    s = 2j*np.pi*np.atleast_1d(np.asarray(f, dtype=float))
    Cpre1 = p['C_bav']+p['C_pcb_pre']+Cbuf
    Cpre2 = p['C_pcb_pre']+(Cbuf if buf2 else p['C_ypin'])
    Ccom = p['C_z']+p['C_pcb_com']+p['C_amp']
    out = []
    for si in s:
        Ysec = 1/p['Rt'] + 1/(p['Rd']+1/(si*p['Ct']))
        Y2 = 1/p['R2']+si*p['C2']; Y3 = 1/p['R3']+si*p['C3']
        Y = np.zeros((5, 5), complex); I = np.zeros(5, complex)
        def add(i, j, y):
            if i is not None: Y[i, i] += y
            if j is not None: Y[j, j] += y
            if i is not None and j is not None: Y[i, j] -= y; Y[j, i] -= y
        add(0, None, Ysec); I[0] += Ysec
        add(0, 1, Ysec); add(1, 2, Ysec); add(2, 3, Y2); add(3, None, Y3)
        add(2, None, si*Cpre1); add(3, None, si*Cpre2)
        if sel == 2 and not buf2:
            add(3, 4, 1/p['Ron']); add(4, None, si*Ccom)
        else:
            add(4, None, 1e-9)     # nodo inactivo
        out.append(np.linalg.solve(Y, I)[3 if sel == 2 else 2])
    return np.array(out)
