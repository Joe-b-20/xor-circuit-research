#!/usr/bin/env python3
"""P2: bottom anatomy in model M: for every AND of the circuit, is it a bilinear (u, x) form
(+ affine)? rank? which alpha(s)?   python3 botanat.py FILE"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil   # noqa: E402
from boolflux import core   # noqa: E402

c = core.read_ncff(sys.argv[1]) if sys.argv[1].endswith('.txt') else core.from_kernel(open(sys.argv[1]).read())
T = c.tables(); n = c.n
lg = [0] * n; la = [0] * n
for op, a, b in c.gates:
    lg.append(1 + max(lg[a], lg[b])); la.append((1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]))
k = 0
for j, (op, a, b) in enumerate(c.gates):
    s = n + j
    if op not in core.NONLINEAR_OPS: continue
    d = bil.decompose(T[s])
    info = 'not bilinear'
    if d is not None:
        Mx, lin, cc = d
        r = bil.rank(Mx)
        # column space of alpha side: rows used
        info = 'rank %d lin %02x c %d rows %s' % (r, lin, cc, [sum(Mx[p][q] << q for q in range(8)) for p in range(4)])
    da = bil.decompose(T[a]); db = bil.decompose(T[b])
    def opd(d):
        if d is None: return 'non-bil'
        Mx, lin, cc = d
        if any(any(r) for r in Mx): return 'bil(r%d)+%02x' % (bil.rank(Mx), lin)
        return 'lin %02x' % lin
    print('a%-2d AL%d GL%-2d %s | L %s R %s' % (k, la[s], lg[s], info, opd(da), opd(db)))
    k += 1
