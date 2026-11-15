#!/usr/bin/env python3
"""P2: bottom decompositions (model M, rank-1 products) x symmetry orbit x fronts -> depth-feasible
designs.

A rank-1 bottom is a list of (alpha_j, g_j, w_j) with  sum_j Tr16(alpha_j N^-1) g_j(x) w_j = x^-1
(alpha_j in the GF(16) subfield, g_j an 8-bit input mask, w_j in GF(256)); output k uses product j
iff l_k(w_j) = 1 where l_k(w) = bit 7-k of A(w) (A = AES affine linear part).

Symmetries (exact): b in GF(256)*:  alpha -> alpha b^-17, g -> g o (x -> b x), w -> b w;
a in GF(16)*: alpha -> a alpha, w -> a^-1 w;  Frobenius: alpha -> alpha^8, g -> g o (x -> x^2),
w -> w^128 (all powers).

    python3 orbit.py extract FILE...            print/collect decompositions of rank-1 bottoms
    python3 orbit.py search D OUT.json --fronts F1 F2 ... --bottoms B1 B2 ...
"""
import itertools
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import inv6 as I   # noqa: E402
from boolflux import core   # noqa: E402

m256, p256 = I.m256, I.p256
SB = bil.SBOX
SINV = [0] * 256
for x in range(256): SINV[SB[x]] = x


def inv(z): return p256(z, 254) if z else 0


def lvec(w):                 # 8-bit vector, bit 7-k = l_k(w)
    return SB[inv(w)] ^ 0x63


def w_of(cvec):              # inverse of lvec
    return inv(SINV[cvec ^ 0x63])


assert all(w_of(lvec(w)) == w for w in range(256))
SUBSET = set(I.SUB)


def alpha_of_tt(tt):
    for al in I.SUB:
        if al and (bil.tab_Y(al) == tt or bil.tab_Y(al) == tt ^ bil.ONES): return al
    return None


YT = {al: bil.tab_Y(al) for al in I.SUB if al}
GT = {g: bil.tab_g(g) for g in range(256)}


def extract(c):
    """rank-1 products of the bottom (AND level 4 ANDs) whose XOR combinations give the outputs."""
    T = c.tables(); n = c.n
    la = [0] * n
    for op, a, b in c.gates:
        la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
    prods = []
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op not in core.NONLINEAR_OPS or la[s] != 4: continue
        d = bil.decompose(T[s])
        if d is None or d[1] or bil.rank(d[0]) != 1: return None
        Mx = d[0]
        rows = [sum(Mx[p][q] << q for q in range(8)) for p in range(4)]
        gq = next(r for r in rows if r)
        av = sum(1 << p for p in range(4) if rows[p])
        g = sum(bil.GMASK[q] for q in range(8) if (gq >> q) & 1)
        prods.append([bil.ALPHA[av], g, s])
    # incidence: express outputs over the product tables
    tabs = [bil.f(al, g) for al, g, s in prods]
    rows = []
    for i, v in enumerate(tabs):
        t = 1 << i
        for pb, rv, rt in rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        if v == 0: return None
        rows.append((v.bit_length() - 1, v, t))
    cvec = [0] * len(prods)
    for k in range(8):
        v = bil.out_tab(k); t = 0
        for pb, rv, rt in rows:
            if (v >> pb) & 1: v ^= rv; t ^= rt
        if v:
            v = bil.out_tab(k) ^ bil.ONES; t = 0
            for pb, rv, rt in rows:
                if (v >> pb) & 1: v ^= rv; t ^= rt
            if v: return None
        for j in range(len(prods)):
            if (t >> j) & 1: cvec[j] |= 1 << (7 - k)
    return [(al, g, w_of(cv)) for (al, g, s), cv in zip(prods, cvec)]


def check(dec):
    for x in range(256):
        N = p256(x, 17); u = inv(N); acc = 0
        for al, g, w in dec:
            if I.tr16(m256(al, u)) & bin(g & x).count('1') & 1: acc ^= w
        if acc != inv(x): return False
    return True


def gmap(g, fn):
    """g o fn as a mask: functional x -> parity(g & fn(x)) is linear; find its mask."""
    m = 0
    for q in range(8):
        e = 1 << (7 - q)
        if bin(g & fn(e)).count('1') & 1: m |= e
    return m


def transforms():
    """yield (a, b, f) and the function mapping a decomposition."""
    G16 = [z for z in I.SUB if z]
    for f in range(8):
        for b in range(1, 256):
            for a in G16:
                yield a, b, f


def apply(dec, a, b, f):
    b17i = inv(p256(b, 17))
    out = []
    for al, g, w in dec:
        al2 = m256(m256(al, b17i), a); g2 = gmap(g, lambda x, b=b: m256(b, x)); w2 = m256(m256(w, b), inv(a))
        for _ in range(f):
            al2 = p256(al2, 8); g2 = gmap(g2, lambda x: m256(x, x)); w2 = p256(w2, 128)
        out.append((al2, g2, w2))
    return out


def units(dec, lev, D):
    """per-output Kraft sums sum 2^(1+lev-D) (as floats) and max."""
    ks = [0.0] * 8
    for al, g, w in dec:
        lv = lvec(w); L = lev[al]
        for k in range(8):
            if (lv >> (7 - k)) & 1: ks[k] += 2.0 ** (1 + L - D)
    return ks


if __name__ == '__main__':
    if sys.argv[1] == 'extract':
        for f in sys.argv[2:]:
            c = ylev.load(f); d = extract(c)
            print(Path(f).name, None if d is None else (len(d), check(d)), d)
