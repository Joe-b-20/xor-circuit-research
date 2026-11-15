#!/usr/bin/env python3
"""T4: earliest gate level of every Y-form Tr(alpha N^-1) (+c) in a circuit's front span
(unique representation over const, x, front ANDs; Huffman over skeleton-bound arrivals).
    python3 ylevels.py FILE"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import inv6 as I, invdesign as D  # noqa
from rank2 import load, analyse, ONES  # noqa
from coversearch import TSpan, bound, huff  # noqa
from boolflux import core, skeleton  # noqa
c = load(sys.argv[1]); n = 8
T, lg, la, fa, ba, V, X = analyse(c)
sk = skeleton.extract(c); b, arr, ol = bound(sk, n)
sig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
ts = TSpan()
basis = [ONES] + [T[i] for i in range(n)]
pos = list(range(1 + n))
for k, s in enumerate(sig):
    if la[s] < 4: basis.append(T[s]); pos.append(1 + n + k)
for i, v in enumerate(basis): ts.add(v, 1 << i)
Nx = [I.p256(x, 17) for x in range(256)]
res = []
for al in I.SUB:
    if not al: continue
    t16 = I.tab(lambda z: I.tr16(I.m256(al, D.inv(z))))
    t = sum(((t16 >> I.IDX[Nx[x]]) & 1) << x for x in range(256))
    best = None
    for tt in (t, t ^ ONES):
        tag = ts.express(tt)
        if tag is None: continue
        terms = [arr[pos[i]] for i in range(1, len(basis)) if (tag >> i) & 1]
        lv = huff(terms, tag & 1)
        best = lv if best is None else min(best, lv)
    res.append((best, al))
res.sort()
print('Y-form levels (level, alpha):', res)
print('front ANDs', sum(1 for s in sig if la[s] < 4))
