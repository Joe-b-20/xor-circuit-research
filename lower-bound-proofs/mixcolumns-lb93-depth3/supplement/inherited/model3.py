#!/usr/bin/env python3
"""Shared candidate-set construction for the COMPLETE depth-3 model.

Re-derived independently of, and agreeing with, this project's earlier,
unpublished exact depth-3 model.  The two constructions were written from the
structure theorem below without reference to each other and produce the same
candidate sets; that agreement is the reason this file exists.

Structure theorem (depth <= 3, minimal circuit):
  * every target has weight 5 or 7 > 4 = 2^2, so every target sits at level
    exactly 3, and no target can feed another gate (a level-3 gate's parents
    are at level <= 2).  Hence exactly 32 level-3 gates, one per target.
  * level-1 gates have weight exactly 2 ("edges");
  * level-2 gates have weight <= 4; weight <= 2 values are realisable at
    level 1 so WLOG a level-2 gate has weight 3 or 4;
  * a weight-4 level-2 mask is the XOR of two DISJOINT edges;
    a weight-3 level-2 mask is an input XOR a disjoint edge.
  * every level-2 gate feeds only level-3 gates, so it occurs in some target
    decomposition.
  N_depth3 = 32 + min(|L1| + |L2|).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys, itertools
from mcmatrix import TARGETS

pc = lambda m: bin(m).count('1')
BITS = lambda m: [i for i in range(32) if (m >> i) & 1]


def decompositions(t):
    """All unordered pairs (a,b), a^b == t, wt(a),wt(b) <= 4."""
    w = pc(t)
    bits = BITS(t)
    out = []
    if w == 7:
        for c in itertools.combinations(bits, 4):
            a = sum(1 << i for i in c)
            out.append((a, t ^ a))
    elif w == 5:
        for i in bits:                                   # {1,4}
            out.append((1 << i, t ^ (1 << i)))
        for c in itertools.combinations(bits, 2):        # {2,3}
            a = sum(1 << i for i in c)
            out.append((a, t ^ a))
        for c in itertools.combinations(bits, 3):        # {4,3} overlap 1
            a3 = sum(1 << i for i in c)
            for z in range(32):
                if (t >> z) & 1:
                    continue
                a = a3 | (1 << z)
                b = (t ^ a3) | (1 << z)
                assert a ^ b == t and pc(a) == 4 and pc(b) == 3
                out.append((a, b))
    else:
        raise SystemExit('unexpected target weight %d' % w)
    # sanity: unordered, distinct
    return out


def buildings(m):
    """Ways to build a level-2 mask from level-<=1 signals (inputs + edges)."""
    b = BITS(m)
    if len(b) == 4:
        return [((1 << b[0]) | (1 << b[i]), (1 << b[j]) | (1 << b[k]))
                for i, j, k in [(1, 2, 3), (2, 1, 3), (3, 1, 2)]]
    if len(b) == 3:
        return [((1 << b[i]), m ^ (1 << b[i])) for i in range(3)]
    raise SystemExit('bad level-2 weight')


def candidates():
    decomp = {t: decompositions(t) for t in TARGETS}
    L2 = set()
    for t, ds in decomp.items():
        for a, b in ds:
            for v in (a, b):
                if pc(v) >= 3:
                    L2.add(v)
    L2 = sorted(L2)
    edges = set()
    for m in L2:
        for e1, e2 in buildings(m):
            for e in (e1, e2):
                if pc(e) == 2:
                    edges.add(e)
    for t in TARGETS:
        for a, b in decomp[t]:
            for v in (a, b):
                if pc(v) == 2:
                    edges.add(v)
    return decomp, L2, sorted(edges)


if __name__ == '__main__':
    d, L2, E = candidates()
    print('L2 candidates %d  edges %d  decompositions %d'
          % (len(L2), len(E), sum(len(v) for v in d.values())))
    from collections import Counter
    print('L2 weight profile', Counter(pc(m) for m in L2))
