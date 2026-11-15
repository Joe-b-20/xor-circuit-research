#!/usr/bin/env python3
"""Write the r1enum input for 'window U -> |U| - 1 parallel ANDs with the FULL operand space'
(operands in V = span(inputs, all kept ANDs)), exactly as H3's chain.solve_window does for its
first enumeration (H3 code imported read-only).  For a parallel (equal-usage) pair U = {i, j}
(rank of outputs mod W = 1) a hit = one product replacing both = a 27 from a 28.

usage: pairgen.py CIRCUIT "i,j" OUT.txt [all|nosinks]  (nosinks: operands from x + ANDs that have consumers; W always = span(1, x, all kept ANDs))  -> prints nv, nh, nc, rank r, the r1enum command"""
import sys, os
sys.path.insert(0, os.path.expanduser('~/xcr-boolflux/nonlinear/boolflux/strategies/H3'))
import chain
from wsat import Base, Span, ONES

b = Base(sys.argv[1]); U = {int(t) for t in sys.argv[2].split(',')}
assert b.closure(U) == U, 'window not closed under consumers'
n = b.n
R = [k for k in range(b.K) if k not in U]
W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
Trep = []; ST = Span(W)
for y in b.out:
    if ST.add(y): Trep.append(y)
HT = chain.checks_of(W + Trep); comp = chain.comp_checks(W, Trep)
OPS = sys.argv[4] if len(sys.argv) > 4 else "all"
Rop = [k for k in R if (OPS == "all" or b.cons[k])]
Vb = b.tab[1:1 + n] + [b.andtab[k] for k in Rop]
nv = len(Vb)
import random
GH = [chain.Gmat(h, Vb) for h in HT]
GC = [chain.Gmat(h, Vb) for h in comp]
rnd = random.Random(1)
nf = min(len(GH), nv + 10)
GF = []
for _ in range(nf):
    acc = [0] * nv
    for row in GH:
        if rnd.random() < 0.5: acc = [x ^ y for x, y in zip(acc, row)]
    GF.append(acc)
lines = ['%d %d %d %d' % (nv, len(GH), len(GC), nf)]
for rows in (GF, GH, GC):
    for row in rows: lines.append(' '.join('%x' % w for w in row))
open(sys.argv[3], 'w').write('\n'.join(lines) + '\n')
print('file', os.path.basename(sys.argv[1]), 'U', sorted(U), 'nv', nv, 'nh', len(GH), 'nc', len(GC),
      'rank r', len(Trep), 'full range hi = %x' % (1 << (nv - 1)))
