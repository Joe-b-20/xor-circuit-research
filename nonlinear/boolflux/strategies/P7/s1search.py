#!/usr/bin/env python3
"""P7: stage-1 covers with N-coordinates at gate level 4.

Question: the NIST 59@10 stage 1 builds the four N-coordinates f_1..f_4 used by its inversion
as sums of 4-5 disjoint level-1/2 products (17 ANDs).  Which sums of 4 products of affine
operands with <= 2 input variables (so every product at gate level <= 2 and every f_k at gate
level 4 by its own XOR tree) give f_k, and how many products can the four sums share?

    s1search.py CIRCUIT [--stats]

Writes the decompositions per coordinate to P7/runs/s1/decs.json.
"""
import itertools, json, sys
from collections import defaultdict
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402


def coords(c):
    T, lg, la = L.sim(c)
    n = c.n
    seen = []
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in L.core.NONLINEAR_OPS and la[s] == 2:
            for o in (a, b):
                t = T[o]
                if t & 1: t ^= L.ONES       # normalise: f(0) = 0
                if t not in seen: seen.append(t)
    return seen, T, lg, la


def products():
    forms = [m for m in range(1, 256) if bin(m).count('1') <= 2]
    P = []
    for l, m in itertools.combinations(forms, 2):
        w = L.wedge(l, m)
        if w:
            lev = 1 if bin(l).count('1') == 1 and bin(m).count('1') == 1 else 2
            P.append((l, m, w, lev))
    return P


def decomps(q, P, PS):
    out = []
    for i1 in range(len(P)):
        for i2 in range(i1 + 1, len(P)):
            k = q ^ P[i1][2] ^ P[i2][2]
            for (i3, i4) in PS.get(k, ()):
                if i3 > i2:
                    out.append((i1, i2, i3, i4))
    return out


def main():
    c = L.load(sys.argv[1])
    fs, T, lg, la = coords(c)
    print('N-coordinates at AND-level-2 operands:', len(fs), 'degrees', [L.deg(f) for f in fs])
    qs = [L.quad(f) for f in fs]
    P = products()
    print('products with <= 2-variable operands:', len(P))
    PS = defaultdict(list)
    for i1 in range(len(P)):
        for i2 in range(i1 + 1, len(P)):
            PS[P[i1][2] ^ P[i2][2]].append((i1, i2))
    res = {}
    for k, q in enumerate(qs):
        D = decomps(q, P, PS)
        print('f%d: %d four-product decompositions' % (k, len(D)))
        res[k] = D
    # all 15 nonzero combinations (any of them could be a coordinate of an alternative inversion)
    allq = {}
    for mask in range(1, 16):
        q = 0
        for k in range(4):
            if (mask >> k) & 1: q ^= qs[k]
        allq[mask] = q
    out = Path.home() / 'xs-campaigns/2026-11-15-targets/P7/runs/s1'
    out.mkdir(parents=True, exist_ok=True)
    json.dump({'P': P, 'fs': [hex(f) for f in fs], 'qs': qs, 'decs': res}, open(out / 'decs.json', 'w'))
    if '--stats' in sys.argv:
        for mask, q in allq.items():
            print('combo %2d: %d decompositions' % (mask, len(decomps(q, P, PS))))


if __name__ == '__main__':
    main()
