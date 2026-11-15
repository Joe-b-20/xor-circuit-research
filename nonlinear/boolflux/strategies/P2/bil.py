#!/usr/bin/env python3
"""P2: the AES S-box bottom as a bilinear map (model M, rank-1 bottom products).

x^-1 = u * z with u = N^-1 = (x^17)^-1 in GF(16) (subfield of GF(256), AES polynomial) and
z = x^16.  A rank-1 product is Y_alpha(x) * g(x) with Y_alpha = Tr16(alpha * u) (alpha in the
subfield, a GF(2)-functional on u) and g a GF(2)-linear functional of x (8-bit mask over x0..x7,
x0 = msb).  Each AES output bit k (minus its constant) is a bilinear form M_k (4 x 8 matrix in the
bases below).  Truth-table index t = field element (core.input_tables: x0 = msb).

Functions:
  alpha_basis, tab_Y(alpha), tab_g(mask), f(alpha, mask)  truth tables (256-bit ints)
  M[k]  4x8 0/1 matrix of output k in (alpha_basis, unit masks)
  decompose(tt)  -> (matrix 4x8, affine part mask, const) if tt is bilinear + affine, else None
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE.parent / 'T4'))
import inv6 as I   # noqa: E402
from boolflux import targets   # noqa: E402

ONES = (1 << 256) - 1
SBOX = targets.aes_sbox()


def inv(z): return I.p256(z, 254) if z else 0


U = [inv(I.p256(x, 17)) for x in range(256)]           # u(x) = N^-1 in GF(16)


def tab_Y(alpha):
    return sum((I.tr16(I.m256(alpha, U[x])) & 1) << x for x in range(256))


def tab_g(mask):
    return sum((bin(mask & x).count('1') & 1) << x for x in range(256))


def f(alpha, mask):
    return tab_Y(alpha) & tab_g(mask)


# GF(2)-basis of the subfield (functionals on u): first 4 independent SUB elements
def _basis():
    B = []; span = {0}
    for a in I.SUB:
        if a and a not in span:
            B.append(a); span = span | {s ^ a for s in span}
        if len(B) == 4: break
    return B


ALPHA_B = _basis()
ALPHA = [0] * 16                      # coordinate vector (4 bits) -> subfield element
for v in range(16):
    a = 0
    for p in range(4):
        if (v >> p) & 1: a ^= ALPHA_B[p]
    ALPHA[v] = a
AIDX = {a: v for v, a in enumerate(ALPHA)}
GMASK = [1 << (7 - q) for q in range(8)]   # q -> mask of input x_q (x_q = bit 7-q of t)

# linear algebra basis: 32 bilinear functions + 8 linear + const
_BASIS = []
for p in range(4):
    for q in range(8):
        _BASIS.append(('B', p, q, f(ALPHA_B[p], GMASK[q])))
for q in range(8):
    _BASIS.append(('L', q, None, tab_g(GMASK[q])))
_BASIS.append(('C', None, None, ONES))


class _Elim:
    def __init__(self, vecs):
        self.rows = []                # (pivot bit, vec, tag)
        for i, v in enumerate(vecs):
            t = 1 << i
            for pb, rv, rt in self.rows:
                if (v >> pb) & 1: v ^= rv; t ^= rt
            if v == 0: raise ValueError('dependent basis')
            pb = v.bit_length() - 1
            self.rows.append((pb, v, t))

    def express(self, v):
        t = 0
        for pb, rv, rt in self.rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        return None if v else t


EL = _Elim([b[3] for b in _BASIS])


def decompose(tt):
    tag = EL.express(tt)
    if tag is None: return None
    Mx = [[0] * 8 for _ in range(4)]; lin = 0; c = 0
    for i, b in enumerate(_BASIS):
        if (tag >> i) & 1:
            if b[0] == 'B': Mx[b[1]][b[2]] = 1
            elif b[0] == 'L': lin |= GMASK[b[1]]
            else: c = 1
    return Mx, lin, c


def out_tab(k):
    return sum(((SBOX[x] >> (7 - k)) & 1) << x for x in range(256))


M = []
for k in range(8):
    d = decompose(out_tab(k))
    assert d is not None and d[1] == 0, ('output not bilinear', k, d)
    M.append(d[0])


def rank(Mx):
    rows = [sum(b << q for q, b in enumerate(r)) for r in Mx]
    r = 0
    for bit in range(8):
        piv = next((i for i in range(r, len(rows)) if (rows[i] >> bit) & 1), None)
        if piv is None: continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for i in range(len(rows)):
            if i != r and (rows[i] >> bit) & 1: rows[i] ^= rows[r]
        r += 1
    return r


if __name__ == '__main__':
    print('alpha basis', ALPHA_B)
    for k in range(8):
        print('y%d rank %d' % (k, rank(M[k])), M[k])
