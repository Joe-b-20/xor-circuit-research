#!/usr/bin/env python3
"""Compare the product spans (modulo affine functions) of two circuits, per AND level.
    python3 cmp_spans.py FILE1 FILE2"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import x1lib as X
from boolflux.hub.common import load, metrics
from boolflux import core

ONES = (1 << 256) - 1
AFF = [ONES] + core.input_tables(8)


class Sp:
    def __init__(self, vs=()):
        self.piv = []
        for v in vs: self.add(v)

    def red(self, t):
        for p, r in self.piv:
            if (t >> p) & 1: t ^= r
        return t

    def add(self, t):
        t = self.red(t)
        if t: self.piv.append((t.bit_length() - 1, t)); return True
        return False

    @property
    def dim(self): return len(self.piv)


def info(f):
    c = load(f); p = X.extract(c); T, ft = p.tables(); lv = p.and_levels()
    return c, p, T, lv


def span_of(tabs):
    s = Sp(AFF)
    for t in tabs: s.add(t)
    return s


def inter_dim(ta, tb):
    sa, sb = span_of(ta), span_of(tb); su = span_of(list(ta) + list(tb))
    return sa.dim - 9, sb.dim - 9, sa.dim + sb.dim - su.dim - 9


f1, f2 = sys.argv[1], sys.argv[2]
c1, p1, T1, l1 = info(f1); c2, p2, T2, l2 = info(f2)
print(Path(f1).name, metrics(c1)); print(Path(f2).name, metrics(c2))
print('all products: dim1 %d dim2 %d intersection %d' % inter_dim([T1[k] for k in p1.ands], [T2[k] for k in p2.ands]))
for L in range(1, max(max(l1.values()), max(l2.values())) + 1):
    a = [T1[k] for k in p1.ands if l1[k] <= L]; b = [T2[k] for k in p2.ands if l2[k] <= L]
    print('levels <= %d: n1 %d n2 %d | dim1 %d dim2 %d intersection %d' % ((L, len(a), len(b)) + inter_dim(a, b)))
# which products of circuit 1 lie in the full span of circuit 2 (and vice versa)
s2 = span_of([T2[k] for k in p2.ands]); s1 = span_of([T1[k] for k in p1.ands])
print('products of 1 inside span 2 by level:', sorted((l1[k]) for k in p1.ands if s2.red(T1[k]) == 0))
print('products of 2 inside span 1 by level:', sorted((l2[k]) for k in p2.ands if s1.red(T2[k]) == 0))
