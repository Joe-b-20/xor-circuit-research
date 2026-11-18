"""Which of our circuits is compared with which NIST circuit.

For every NIST circuit that no other NIST circuit of the same function dominates (NIST's own
front in A, AD, G, GD), the paired circuit of ours is, among our circuits that are at least as
good in all four metrics (equal metrics included), the one with the fewest gates (ties: lower gate
depth, then fewer ANDs, then lower AND depth).  NIST circuits that none of ours dominates are
listed without a partner.  Linear maps use G and GD only (A = AD = 0).
"""
from __future__ import annotations


def key(m):
    return (m['A'], m['AD'], m['G'], m['GD'])


def dominates(a, b):
    """a is at least as good as b in every metric and better in one."""
    ka, kb = key(a), key(b)
    return all(x <= y for x, y in zip(ka, kb)) and ka != kb


def front(designs):
    return [d for d in designs if not any(dominates(e.metrics, d.metrics) for e in designs)]


def pair(ours, nist):
    """[(nist design, our design or None)] for NIST's front, per function."""
    out = []
    for fn in sorted({d.function for d in nist}):
        ns = [d for d in nist if d.function == fn]
        os_ = [d for d in ours if d.function == fn]
        for n in sorted(front(ns), key=lambda d: key(d.metrics)):
            better = [o for o in os_ if all(x <= y for x, y in zip(key(o.metrics), key(n.metrics)))]
            best = min(better, key=lambda o: (o.metrics['G'], o.metrics['GD'], o.metrics['A'],
                                              o.metrics['AD'])) if better else None
            out.append((n, best))
    return out
