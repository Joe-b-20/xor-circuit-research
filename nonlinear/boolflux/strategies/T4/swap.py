#!/usr/bin/env python3
"""T4: does the rest of an AD4 circuit use stage 1 only through N (then any 9-cover can replace it)?
For every skeleton form above stage 1 (operands of AND level >= 2, outputs) the stage-1 part
(XOR of the referenced level-1 products) is tested for membership in span(1, x, N coordinates).
    python3 swap.py FILE..."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from absorb import N_tables  # noqa
from boolflux import core, skeleton  # noqa

def check(f):
    c = load(f); T, lg, la, fa, ba, V, X = analyse(c)
    n = c.n
    sk = skeleton.extract(c)
    ands = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    tab = [ONES] + [T[i] for i in range(n)] + [T[s] for s in ands]
    lvl1 = [k for k, s in enumerate(ands) if la[s] == 1]
    NX = Span([ONES] + [T[i] for i in range(n)] + N_tables())
    bad = []; tot = 0
    forms = []
    for k, (L, R) in enumerate(sk['ands']):
        if la[ands[k]] >= 2: forms += [('a%d.L' % k, L), ('a%d.R' % k, R)]
    forms += [('y%d' % j, F) for j, F in enumerate(sk['outputs'])]
    for name, F in forms:
        part = 0; used = False
        for k in lvl1:
            if (F >> (1 + n + k)) & 1: part ^= T[ands[k]]; used = True
        if not used: continue
        tot += 1
        if part not in NX: bad.append(name)
    print('%s: stage-1 products %d; forms using stage 1: %d; NOT in span(1,x,N): %d %s' % (
        Path(f).name, len(lvl1), tot, len(bad), bad[:12]))

for f in sys.argv[1:]: check(f)
