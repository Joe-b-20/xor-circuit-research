#!/usr/bin/env python3
"""Per-AND-level gate census of circuits: for each AND level k, #AND at level k and #linear gates at level k
(a linear gate's level = max AND level of its operands).  Also level-0 linear gates that feed only level-0
signals vs ANDs, and outputs' levels.   regions.py FILE|ARCHIVE_ID ... [--archive DIR]"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import core, metrics  # noqa
from boolflux.hub.join import levels  # noqa


def census(c):
    l = levels(c); n = c.n
    A = {}; L = {}
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        if op in core.NONLINEAR_OPS: A[l[s]] = A.get(l[s], 0) + 1
        else: L[l[s]] = L.get(l[s], 0) + 1
    return A, L


def main():
    args = sys.argv[1:]; ar = None
    if '--archive' in args:
        i = args.index('--archive'); ar = Path(args[i + 1]); del args[i:i + 2]
    for f in args:
        p = Path(f)
        if p.exists():
            c = core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))
        else:
            c = core.from_kernel((ar / 'archive' / (f + '.bfx')).read_text())
        A, L = census(c)
        m = metrics(c)
        K = max(list(A) + list(L))
        print('%-60s %s  AND/lvl %s  LIN/lvl %s' % (p.name[:60], m, [A.get(k, 0) for k in range(1, K + 1)],
                                                   [L.get(k, 0) for k in range(0, K + 1)]))


main()
