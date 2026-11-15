#!/usr/bin/env python3
"""Write an r1enum input for a window (for benchmarks / split runs).
Usage: bench_enum.py CIRCUIT "U" OPS OUTFILE"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import chain  # noqa: E402
from wsat import Base, Span, ONES  # noqa: E402

b = Base(sys.argv[1]); U = {int(t) for t in sys.argv[2].split(',')}
ops = chain.opset(b, sys.argv[3])
n = b.n
R = [k for k in range(b.K) if k not in U]
Rop = [k for k in R if ops is None or k in ops]
W = [ONES] + b.tab[1:1 + n] + [b.andtab[k] for k in R]
Trep = []; ST = Span(W)
for y in b.out:
    if ST.add(y): Trep.append(y)
HT = chain.checks_of(W + Trep)
comp = chain.comp_checks(W, Trep)
Vb = b.tab[1:1 + n] + [b.andtab[k] for k in Rop]
nv = len(Vb)
GH = [chain.Gmat(h, Vb) for h in HT]; GC = [chain.Gmat(h, Vb) for h in comp]
rnd = random.Random(1); nf = min(len(GH), nv + 10); GF = []
for _ in range(nf):
    acc = [0] * nv
    for row in GH:
        if rnd.random() < 0.5: acc = [x ^ y for x, y in zip(acc, row)]
    GF.append(acc)
lines = ['%d %d %d %d' % (nv, len(GH), len(GC), nf)]
for rows in (GF, GH, GC):
    for row in rows: lines.append(' '.join('%x' % w for w in row))
Path(sys.argv[4]).write_text('\n'.join(lines) + '\n')
print('nv', nv, 'nh', len(GH), 'nc', len(GC))
