#!/usr/bin/env python3
"""Which Y*Y products (y_i y_j, and s*t for Y-forms s, t) lie in the span of a front's existing signals?
If s*t is in span(front signals of AND level <= 3) the Y*Y part of a packed product (A+s)(B+t) can be
cancelled by XORs of existing signals instead of other products.   yyspan.py REF FRONT"""
import sys
from itertools import combinations
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL  # noqa

rc, Yt = FL.ref_basis(sys.argv[1])
c = BT.load(sys.argv[2])
T = c.tables(); la, lg = BT.and_levels(c)
AD = max(la[s] for s in c.outputs)
B = BT.Basis()
B.add(BT.ONES, '1')
sigs = [s for s in range(c.n + len(c.gates)) if la[s] <= AD - 1]
for s in sigs: B.add(T[s], s)
print('front signals', len(sigs), 'span dim', len(B.names))
forms = {}
for u in range(1, 16):
    t = 0
    for i in range(4):
        if u >> i & 1: t ^= Yt[i]
    forms[u] = t
n_in = 0; tot = 0
for u, v in combinations(range(1, 16), 2):
    p = forms[u] & forms[v]
    cb = B.coords(p)
    tot += 1
    if cb is not None:
        n_in += 1
        used = [B.names[k] for k in range(len(B.names)) if cb >> k & 1]
        print(len(used), 'y-form %2d * %2d in span, via %s' % (u, v, used))
print('pairs in span: %d of %d' % (n_in, tot))
