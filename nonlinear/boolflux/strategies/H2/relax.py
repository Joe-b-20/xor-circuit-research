"""Relaxed GF(4)-norm-member model in real coordinates.

x in F = GF(256) (FIPS polynomial, 0x11B), v in K = GF(16) subfield, independent.  A member
(A, s) is the product  [Tr(Ax) + Tr_K(s v)] * [Tr(wAx) + Tr_K(w^2 s v)],  w = g^85.
Quadratic function f(x, v) (mod affine) = (bilinear part, x-part, v-part):
  bil[i][j] = coefficient of x_i v_j (x_i = bit i of x, v_j = j-th coordinate in basis KB of K),
  xpart = f(x, 0) (256-point table), vpart = f(0, v) (16-point table over the basis coords).
Target b (gamma fixed): Tr(b x^16 v) + Tr(b gamma x^33)   [x^-1 = x^16 n, n = v + gamma N].
"""
from h2lib import gmul, gpow, tr8, Basis
import itertools

G = 3
w = gpow(G, 85)
w2 = gmul(w, w)
KSET = sorted({gpow(y, 17) for y in range(256)})
# GF(2) basis of K
KB = []
_b = Basis()
for y in KSET:
    if y and _b.add(y): KB.append(y)
assert len(KB) == 4


def trK(z):
    """Tr_{K/2}(z) for z in K."""
    t = z
    y = z
    for _ in range(3):
        y = gmul(y, y); t ^= y
    assert t in (0, 1)
    return t


def vval(j_mask):
    v = 0
    for j in range(4):
        if j_mask >> j & 1: v ^= KB[j]
    return v


VPTS = [vval(m) for m in range(16)]   # v at coordinate mask m


def member_parts(A, s):
    """bil as 32-bit int (bit 4*i + j), xpart 256-table, vpart 16-table."""
    wA = gmul(w, A); w2s = gmul(w2, s)
    def f(x, v):
        return (tr8(gmul(A, x)) ^ trK(gmul(s, v))) & (tr8(gmul(wA, x)) ^ trK(gmul(w2s, v)))
    return parts(f)


def parts(f):
    f00 = f(0, 0)
    bil = 0
    for i in range(8):
        fi0 = f(1 << i, 0)
        for j in range(4):
            if f(1 << i, KB[j]) ^ fi0 ^ f(0, KB[j]) ^ f00:
                bil |= 1 << (4 * i + j)
    xp = 0
    for x in range(256):
        if f(x, 0): xp |= 1 << x
    vp = 0
    for m in range(16):
        if f(0, VPTS[m]): vp |= 1 << m
    return bil, xp, vp


def target_parts(b, gamma):
    x16 = [gpow(x, 16) for x in range(256)]
    x33 = [gpow(x, 33) for x in range(256)]
    gb = gmul(b, gamma)
    def f(x, v):
        return tr8(gmul(b, gmul(x16[x], v))) ^ tr8(gmul(gb, x33[x]))
    return parts(f)


_CACHE = {}


def all_members(with_index=False):
    """Distinct members by bilinear part; returns list of (bil, xpart, vpart, A, s)
    (and, with_index, a dict (A, s) -> member index).  Cached on disk."""
    import pickle, os
    fn = os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/members.pkl')
    if os.path.exists(fn):
        out, pair = pickle.load(open(fn, 'rb'))
    else:
        out = {}; pair = {}
        for A in range(1, 256):
            for s in KSET:
                if s == 0: continue
                bil, xp, vp = member_parts(A, s)
                if bil not in out: out[bil] = (bil, xp, vp, A, s)
                pair[(A, s)] = bil
        pickle.dump((out, pair), open(fn, 'wb'))
    lst = list(out.values())
    if not with_index: return lst
    idx = {m[0]: i for i, m in enumerate(lst)}
    return lst, {k: idx[b] for k, b in pair.items()}


if __name__ == '__main__':
    import time
    t0 = time.time()
    M = all_members()
    print('distinct member bilinear parts', len(M), time.time() - t0)
