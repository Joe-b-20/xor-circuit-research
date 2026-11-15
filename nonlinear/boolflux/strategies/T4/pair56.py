#!/usr/bin/env python3
"""T4: shared x-junk between the GF(16)-proportional outputs y5, y6 (NIST order) for 2-product
(rank-2) designs on a fixed front: is q5(pairing) == q6(pairing') modulo the front span V?
    python3 pair56.py FILE"""
import sys, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
AD = max(la[o] for o in c.outputs)
outs = decompose(c, T, la, ba, AD)
ys = sorted({y for d in outs for y in d})
PAIRINGS = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]
def q(k, pi):
    w = [outs[k].get(y, 0) for y in ys]
    r = 0
    for a, b in pi: r ^= w[a] & w[b]
    return r
for k, l in [(5, 6)] + [(a, b) for a, b in itertools.combinations(range(8), 2) if (a, b) != (5, 6)]:
    for p1 in PAIRINGS:
        for p2 in PAIRINGS:
            d = q(k, p1) ^ q(l, p2)
            if d in V:
                print('outputs', k, l, 'pairings', p1, p2, ': x-junk equal mod V')
    # one-product (rank-2 pair) junk equal?
    for a, b in itertools.combinations(range(4), 2):
        for e, f in itertools.combinations(range(4), 2):
            wk = [outs[k].get(y, 0) for y in ys]; wl = [outs[l].get(y, 0) for y in ys]
            if ((wk[a] & wk[b]) ^ (wl[e] & wl[f])) in V:
                print('outputs', k, l, 'single pairs', (a, b), (e, f), ': rank-2 x-junk equal mod V')
print('dY free pairs', [(i, j) for i, j in itertools.combinations(range(4), 2) if (ys[i] & ys[j]) in V])
