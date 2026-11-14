#!/usr/bin/env python3
"""Shared functions between two circuits, by region and level (track F).

    python3 overlap.py A.circ.txt B.circ.txt
For every gate of B: is its function (or complement) a signal of A, and at which level in A vs B.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from depth import analyse   # noqa: E402

ONES = (1 << 256) - 1


def main(fa, fb):
    A = core.read_ncff(fa); B = core.read_ncff(fb)
    ta = A.tables(); tb = B.tables()
    lva, ala, _, _, _, rega, _ = analyse(A, 99)
    lvb, alb, _, _, _, regb, _ = analyse(B, 99)
    ia = {}
    for s, t in enumerate(ta):
        if t not in ia or lva[s] < lva[ia[t]]: ia[t] = s
    rows = {}
    for s in range(B.n, len(tb)):
        r = regb(s); t = tb[s]
        hit = ia.get(t); hitc = ia.get(t ^ ONES)
        key = r
        d = rows.setdefault(key, [0, 0, 0, []])
        d[0] += 1
        if hit is not None:
            d[1] += 1; d[3].append('%d/%d' % (lvb[s], lva[hit]))
        elif hitc is not None:
            d[2] += 1; d[3].append('%d/~%d' % (lvb[s], lva[hitc]))
    print('B=%s gates found in A=%s  (levels B/A)' % (Path(fb).name, Path(fa).name))
    for k in sorted(rows, key=lambda k: (k[1:], k[0])):
        d = rows[k]
        print('  %-3s %3d gates: %3d same, %3d complement   %s' % (k, d[0], d[1], d[2], ' '.join(d[3][:40])))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
