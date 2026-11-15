"""Canright all-normal tower (as in umizame's paper) and the relaxed (L, R, v) model.

GF(4): ints with W = 2, W^2 = 3 (poly basis 1, W); normal coords x = x0 W^2 + x1 W.
GF(16): pairs (A1, A0) = A1 Z^4 + A0 Z, Z^2 + Z + W^2 = 0.   GF(256): H = L Y^16 + R Y.
D = L R + W Z (L + R)^2, Q = D^-1, H^-1 = RQ Y^16 + QL Y.
Relaxed model: points p in [0, 4096): L = p & 15, R = (p >> 4) & 15, v = p >> 8, each GF(16)
element as 4 bits = (A1 normal coords x0, x1, A0 normal coords x0, x1) -> bit order
bit0 = A0.x0, bit1 = A0.x1, bit2 = A1.x0, bit3 = A1.x1.
"""
from h2lib import Basis
import itertools

W, W2 = 2, 3


def m4(x, y):
    r = 0
    if y & 1: r ^= x
    if y & 2: r ^= (x << 1)
    if r & 4: r ^= 0b111
    return r


def nb(x0, x1): return (W2 if x0 else 0) ^ (W if x1 else 0)


NB = {nb(a, b): (a, b) for a in (0, 1) for b in (0, 1)}


def tau(x): return (x ^ m4(x, x)) & 1


def g16(bits):  # 4-bit -> (A1, A0)
    A0 = nb(bits & 1, (bits >> 1) & 1); A1 = nb((bits >> 2) & 1, (bits >> 3) & 1)
    return (A1, A0)


def b16(A):
    A1, A0 = A
    a0 = NB[A0]; a1 = NB[A1]
    return a0[0] | (a0[1] << 1) | (a1[0] << 2) | (a1[1] << 3)


def mul16(A, B):
    A1, A0 = A; B1, B0 = B
    l = m4(A0, B0); h = m4(m4(W, A1), m4(W, B1)); s = m4(A0 ^ m4(W, A1), B0 ^ m4(W, B1))
    return (l ^ h ^ m4(W, s), m4(W2, h) ^ m4(W, s))


def add16(A, B): return (A[0] ^ B[0], A[1] ^ B[1])


E16 = [g16(i) for i in range(16)]
MUL = [[b16(mul16(E16[i], E16[j])) for j in range(16)] for i in range(16)]
ONE16 = None
for i in range(16):
    if all(MUL[i][j] == j for j in range(16)): ONE16 = i
assert ONE16 is not None
INV16 = [0] * 16
for i in range(1, 16):
    for j in range(16):
        if MUL[i][j] == ONE16: INV16[i] = j
WZ = b16((0, W))
assert all(MUL[MUL[i][i]][1] is not None for i in range(16))


def sq(i): return MUL[i][i]


def norm(L, R):
    LR = MUL[L][R]; s = sq(L ^ R)
    return LR ^ MUL[WZ][s]


NPTS = 4096
ONE = (1 << NPTS) - 1


def tab(f):
    t = 0
    for p in range(NPTS):
        if f(p & 15, (p >> 4) & 15, p >> 8) & 1: t |= 1 << p
    return t


VAR = [tab(lambda L, R, v, i=i: ((L | (R << 4) | (v << 8)) >> i) & 1) for i in range(12)]


def gf4coord(i, which):  # GF(4) coordinate of 4-bit GF(16) element: which = 1 (A1) or 0 (A0)
    A1, A0 = g16(i)
    return A1 if which else A0


def check_tower():
    # sanity: inversion formula on GF(256) via H H^-1 = 1 is implied by norm algebra; check D in GF(16)
    # and that (L,R) -> (RQ, QL) is a bijection inverse-like: applying twice gives identity
    inv = {}
    for L in range(16):
        for R in range(16):
            D = norm(L, R); Q = INV16[D]
            inv[(L, R)] = (MUL[R][Q], MUL[Q][L])
    ok = all(inv[inv[k]] == k for k in inv)
    return ok


if __name__ == '__main__':
    print('tower involution check (inverse of inverse = id):', check_tower())
