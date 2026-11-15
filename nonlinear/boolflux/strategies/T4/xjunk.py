#!/usr/bin/env python3
"""T4: x-junk structure for rank-2 bottom products on a fixed front (see rank2.py).
For each output k the x-forms w_ik (coefficient of Y-form i) and the x-junk q_kij = w_ik*w_jk.
Prints dims of span{q} mod V, pairwise intersections of per-output junk spaces mod V, and which
q's lie in V.   python3 xjunk.py FILE"""
import sys, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from boolflux import core  # noqa

def decompose(c, T, la, ba, AD):
    """per output: dict Yfunc -> xform (XOR of the x-operands of its products with that Y-side)"""
    n = c.n; outs = []
    for o in c.outputs:
        cone = set(); st = [o]; prods = []
        while st:
            s = st.pop()
            if s < n or s in cone: continue
            cone.add(s)
            op, a, b = c.gates[s - n]
            if op in core.NONLINEAR_OPS:
                if la[s] == AD: prods.append(s)
                continue
            st += [a, b]
        d = {}
        for s in prods:
            op, a, b = c.gates[s - n]
            y, w = (a, b) if la[a] == AD - 1 else (b, a)
            d[T[y]] = d.get(T[y], 0) ^ T[w]
        outs.append(d)
    return outs

if __name__ == '__main__':
    c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    outs = decompose(c, T, la, ba, AD)
    ys = sorted({y for d in outs for y in d})
    print('Y-forms', len(ys))
    allq = Span(); Vq = V.copy()
    per = []
    for k, d in enumerate(outs):
        ws = [d.get(y, 0) for y in ys]
        qs = {}
        for i, j in itertools.combinations(range(len(ys)), 2):
            q = ws[i] & ws[j]
            qs[(i, j)] = q
        inV = [p for p, q in qs.items() if q in V]
        sp = V.copy(); add = 0
        for q in qs.values(): add += sp.add(q)
        per.append((sp, qs))
        print('S%d: q in V for pairs %s; dim(V+Q_k)-dim V = %d' % (k, inV, add))
        for q in qs.values(): Vq.add(q)
    print('dim(V + all q) - dim V =', Vq.dim() - V.dim())
    # pairwise intersections of Q_k (mod V)
    for k, l in itertools.combinations(range(len(outs)), 2):
        s = per[k][0].copy(); a = s.dim()
        for q in per[l][1].values(): s.add(q)
        inter = (per[k][0].dim() - V.dim()) + (per[l][0].dim() - V.dim()) - (s.dim() - V.dim())
        if inter: print('  Q_%d and Q_%d intersect mod V in dim %d' % (k, l, inter))
