"""Spectral (fibre) coordinates of the stage-3 products of an A28 file.

Operand l = alpha(x) + g(N) with alpha(x) = Tr(A x) and g a function of N; we report A and the
spectral coefficients g^_e = sum_{v in K*} g(v) v^{-e} at e = 14 (n-part, s) and e = 1 (N-part, t).
Also the product QR spectrum f_e = sum_{x in F*} P(x) x^{-(1+17e)}.
"""
import sys

import gf
from structure import analyse

TR = [0] * 256
for p in range(256):
    t = 0
    for i in range(8): t ^= gf.power(p, 1 << i)
    TR[p] = t & 1
TRF = {}
for A in range(256):
    tab = 0
    for p in range(256):
        if TR[gf.mul(A, p)]: tab |= 1 << p
    TRF[tab] = A
N = [gf.power(p, 17) for p in range(256)]
KSTAR = [v for v in gf.SUB16 if v]
LOG = {}
g = 3  # generator of F*
x = 1
for i in range(255):
    LOG[x] = i; x = gf.mul(x, g)


def inv_pow(x, d):
    return gf.power(x, (255 - (d % 255)) % 255)


def split(tab):
    """tab = alpha(x) + g(N(x))?  returns (A, gtable over K) or None"""
    for atab, A in TRF.items():
        r = tab ^ atab
        # r must be a function of N
        val = {}
        ok = True
        for p in range(256):
            v = (r >> p) & 1
            if val.setdefault(N[p], v) != v: ok = False; break
        if ok: return A, val
    return None


def ghat(val, e):
    s = 0
    for v in KSTAR:
        if val[v]: s ^= inv_pow(v, e)
    return s


def fspec(tab, e):
    s = 0
    for p in range(1, 256):
        if (tab >> p) & 1: s ^= inv_pow(p, 1 + 17 * e)
    return s


def name(v):
    if v == 0: return '0'
    return 'g^%d' % LOG[v]


if __name__ == '__main__':
    c, ands, outs, tabs = analyse(sys.argv[1])
    top = max(A['level'] for A in ands)
    print('ω = g^85 ; K* = <g^17>')
    for k, Ad in enumerate(ands):
        if Ad['level'] != top: continue
        L = split(Ad['Ltab']); R = split(Ad['Rtab'])
        A1, g1 = L; A2, g2 = R
        ratio = gf.mul(A2, gf.INV[A1]) if A1 else None
        print('a%-2d A=%-6s A\'=%-6s A\'/A=%-6s | s=%-6s s\'=%-6s t=%-6s t\'=%-6s | g(0)=%d,%d | other e: %s' % (
            k + 1, name(A1), name(A2), name(ratio) if ratio else '-',
            name(ghat(g1, 14)), name(ghat(g2, 14)), name(ghat(g1, 1)), name(ghat(g2, 1)),
            g1[0], g2[0],
            [e for e in range(15) if e not in (0, 1, 2, 4, 8, 14, 13, 11, 7) and (ghat(g1, e) or ghat(g2, e))]))
        spec = [e for e in range(15) if fspec(Ad['tab'], e)]
        print('     product QR spectrum support:', spec)
    T = [gf.bit_table(gf.INV, kk) for kk in range(8)]
    print('target x^-1 bit0 QR support:', [e for e in range(15) if fspec(T[0], e)])
    for k, Ad in enumerate(ands):
        if Ad['level'] == 1:
            print('L a%d QR support' % (k + 1), [e for e in range(15) if fspec(Ad['tab'], e)])
