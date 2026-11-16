#!/usr/bin/env python3
"""Classify the AND-level-4 products of an AD4 tower circuit.

Each operand t is written as F(N) + l(x) + c (F a function of N, l linear) when possible:
'N' (l = 0), 'x' (F constant), 'N+x' (both), '?' (neither).  N = the 4 coordinates read by
AND-level-2 gates.  Also prints, per output, its products and gate levels.

    botclass.py CIRCUIT
"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import signals as L  # noqa: E402
core = L.core


def main():
    c = L.load(sys.argv[1]); n = c.n
    T, lg, la = L.sim(c)
    # N coordinates: span of AL2 operands that have degree 2
    co = []
    for j, (op, a, b) in enumerate(c.gates):
        if op in core.NONLINEAR_OPS and la[n + j] == 2:
            for o in (a, b):
                if L.deg(T[o]) == 2: co.append(T[o])
    key = [tuple((t >> x) & 1 for t in co) for x in range(256)]
    cls = {}
    for x in range(256): cls.setdefault(key[x], []).append(x)
    fibers = list(cls.values())
    print('N fibers:', len(fibers), 'sizes', sorted(set(len(f) for f in fibers)))

    def isN(t):
        return all(len({(t >> x) & 1 for x in f}) == 1 for f in fibers)
    LIN = [L.lin_table(m) for m in range(256)]

    def classify(t):
        if L.deg(t) <= 1: return 'x', None
        for m in range(256):
            if isN(t ^ LIN[m]):
                return ('N' if m == 0 else 'N+x'), m
        return '?', None
    fo = {}
    for j, (op, a, b) in enumerate(c.gates):
        for o in {a, b}: fo.setdefault(o, []).append(n + j)
    stats = {}
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in core.NONLINEAR_OPS and la[s] == 4:
            ca = classify(T[a]); cb = classify(T[b])
            k = '/'.join(sorted([ca[0], cb[0]]))
            stats[k] = stats.get(k, 0) + 1
            print('AND %3d GL%-2d  (%s GL%d, %s GL%d)  fanout %d' % (s, lg[s], ca[0], lg[a], cb[0], lg[b], len(fo.get(s, []))))
    print(stats)


if __name__ == '__main__':
    main()


def outsets(c):
    """for each AND-4 product: the outputs whose XOR form (over AND signals) contains it."""
    from boolflux import skeleton
    sk = skeleton.extract(c); n = c.n
    andsig = [n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
    T, lg, la = L.sim(c)
    res = {}
    for k, s in enumerate(andsig):
        if la[s] != 4: continue
        res[s] = [j for j, F in enumerate(sk['outputs']) if (F >> (1 + n + k)) & 1]
    return res


if __name__ == '__main__' and len(sys.argv) > 2:
    c = L.load(sys.argv[1])
    for s, js in outsets(c).items():
        print(s, js)
