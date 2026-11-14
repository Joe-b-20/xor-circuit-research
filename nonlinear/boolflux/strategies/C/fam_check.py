"""Numerical check of the GF(4)-family n-block analysis (NOTES.md section 4)."""
import itertools
import random

import gf
from spectral import fspec, TR

g = 3
def gp(e): return gf.power(g, e % 255)
OMEGA = gp(85)
N = [gf.power(p, 17) for p in range(256)]
n = [gf.INV[v] for v in N]


def tr_tab(A):
    t = 0
    for p in range(256):
        if TR[gf.mul(A, p)]: t |= 1 << p
    return t


def trK(s, vals):
    """table of x -> Tr_K(s * vals[x]) (vals in K)"""
    t = 0
    for p in range(256):
        y = gf.mul(s, vals[p]); z = 0
        for i in range(4): z ^= gf.power(y, 1 << i)
        if z & 1: t |= 1 << p
    return t


def member(A, s, w=n):
    l = tr_tab(A) ^ trK(s, w)
    m = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(gf.mul(OMEGA, OMEGA), s), w)
    return l & m


def nvec(tab):
    v = 0
    for i, e in enumerate((14, 13, 11, 7)):
        v |= fspec(tab, e) << (8 * i)
    return v


if __name__ == '__main__':
    mu5 = [gp(51 * i) for i in range(5)]
    cube_root = {}
    for e in range(0, 255, 17):
        s = gp(e); cube_root.setdefault(gf.power(s, 3), s)
    T = [gf.bit_table(gf.INV, k) for k in range(8)]
    Tv = [nvec(t) for t in T]
    print('target n-vectors', [hex(v) for v in Tv])
    random.seed(1)
    for trial in range(20):
        z1, z2 = random.randrange(1, 256), random.randrange(1, 256)
        Z = [z1, z2]
        prods = []
        for zeta in mu5:
            s = cube_root[zeta]
            for z in Z:
                Y = gf.mul(gf.INV[zeta], z)
                A = gf.mul(Y, gf.INV[s])
                prods.append(member(A, s))
        sp = gf.Span([nvec(p) for p in prods])
        ok = all(sp.contains(t) for t in Tv)
        print('trial', trial, 'Z', Z, 'span dim', sp.dim(), 'targets covered:', ok)
        if ok: break
