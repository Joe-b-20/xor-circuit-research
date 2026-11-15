#!/usr/bin/env python3
"""T3: level-1 product exchange keeping S1 = span{1, x, level-1 ANDs} exactly: P' = a'b' with a', b'
x-affine and P' = P_i mod (affine + other level-1 ANDs). Exhaustive over all a', b' (256 x 256 up to
complement) [C]. python3 l1swap.py CIRCUIT"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core
from boolflux.hub.common import load, metrics, ONES
from pairs import and_levels
from prodswap import RBasis
c = load(sys.argv[1]); n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
X = core.input_tables(8)
lin = []
for m in range(1, 256):
    v = 0
    for i in range(8):
        if (m >> i) & 1: v ^= X[i]
    lin.append(v)
A1 = [g for g in range(n, NS) if c.gates[g - n][0] == 8 and al[g] == 1]
print(metrics(c), 'level-1 ANDs', len(A1))
for g in A1:
    W = RBasis([ONES] + X + [t[h] for h in A1 if h != g])
    Pr, _ = W.reduce(t[g])
    sols = set()
    for i, u in enumerate(lin):
        for v in lin[i:]:
            if W.reduce(u & v)[0] == Pr: sols.add((u, v))
    op, a, b = c.gates[g - n]
    print('s%d: pairs (a\', b\') of linear forms with the same product class: %d' % (g, len(sols)), flush=True)
