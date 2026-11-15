#!/usr/bin/env python3
"""T4: rank-2 bottom products for a fixed AD4 front (exact span tests on 256-point truth tables).

Front = all signals of AND level <= 3.  V = span(1, x, front ANDs).  Y-forms = the AND-level-3 sides
of the bottom products.  Each output currently is S_k = sum_i Y_i w_ik (rank-1 products).
A rank-2 product (Y_a + w_b)(Y_b + w_a) = Y_a w_a + Y_b w_b + [Y_a Y_b + w_a w_b] carries two
rank-1 terms; the bracket (junk) must be supplied: in V (free), or by extra ANDs.
Reports, per output and pairing, whether the junk of the 2-product design lies in V, in
V + span(x-quadratics w_a w_b) (one extra level-1 AND each), etc.
    python3 rank2.py FILE
"""
import sys, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core  # noqa

ONES = (1 << 256) - 1

class Span:
    def __init__(self, vecs=()):
        self.piv = {}   # pivot bit -> vector
        for v in vecs: self.add(v)
    def reduce(self, v):
        while v:
            h = v.bit_length() - 1
            if h in self.piv: v ^= self.piv[h]
            else: return v
        return 0
    def add(self, v):
        r = self.reduce(v)
        if r: self.piv[r.bit_length() - 1] = r; return True
        return False
    def __contains__(self, v): return self.reduce(v) == 0
    def copy(self):
        s = Span(); s.piv = dict(self.piv); return s
    def dim(self): return len(self.piv)

def load(f):
    return core.read_ncff(f) if f.endswith('.txt') else core.from_kernel(open(f).read())

def analyse(c):
    n = c.n; T = c.tables(); S = n + len(c.gates)
    lg = [0]*n; la = [0]*n
    for op, a, b in c.gates:
        lg.append(1+max(lg[a], lg[b])); la.append((op in core.NONLINEAR_OPS) + max(la[a], la[b]))
    AD = max(la[o] for o in c.outputs)
    front_and = [n+j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS and la[n+j] < AD]
    bot_and = [n+j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS and la[n+j] == AD]
    V = Span([ONES] + [T[i] for i in range(n)] + [T[s] for s in front_and])
    X = Span([ONES] + [T[i] for i in range(n)])
    return T, lg, la, front_and, bot_and, V, X

def main(f):
    c = load(f); n = c.n
    T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    print('front ANDs %d, bottom ANDs %d, dim V %d' % (len(fa), len(ba), V.dim()))
    # Y-forms: bottom AND operands of AND level AD-1 (functions), reduced to distinct classes mod V
    ysides = {}
    for s in ba:
        op, a, b = c.gates[s - n]
        for u, v in ((a, b), (b, a)):
            if la[u] == AD - 1 and la[v] < AD - 1:
                ysides.setdefault(T[u], []).append((s, T[v], lg[u], lg[v]))
    print('distinct Y-side functions:', len(ysides), 'levels', sorted({lg_ for L in ysides.values() for (_, _, lg_, _) in L}))
    # independence of Y-sides mod V
    W = V.copy(); yb = []
    for y in ysides:
        if W.add(y): yb.append(y)
    print('Y-sides independent mod V:', len(yb))
    # A1 products span (quadratic junk absorption)
    Q = Span([ONES] + [T[i] for i in range(n)] + [T[s] for s in fa if la[s] == 1])
    # per output: express as sum_i Y_i * w_i (+ V) using the given products
    from collections import defaultdict
    for k, o in enumerate(c.outputs):
        # find bottom ANDs feeding output k (by XOR cone)
        cone = set(); st = [o]
        while st:
            s = st.pop()
            if s < n or s in cone: continue
            cone.add(s)
            op, a, b = c.gates[s - n]
            if op in core.NONLINEAR_OPS and la[s] == AD: continue
            if op in core.NONLINEAR_OPS: continue
            st += [a, b]
        prods = [s for s in cone if s in ba]
        terms = []
        for s in prods:
            op, a, b = c.gates[s - n]
            y, w = (a, b) if la[a] == AD - 1 else (b, a)
            terms.append((T[y], T[w]))
        # rank-2 pairings
        res = []
        idx = range(len(terms))
        if len(terms) == 4:
            for pairing in (((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))):
                junk_d = 0; junk_x = 0
                for i, j in pairing:
                    junk_d ^= terms[i][0] & terms[j][0]
                    junk_x ^= terms[i][1] & terms[j][1]
                J = junk_d ^ junk_x
                inV = J in V
                dV = junk_d in V; xQ = junk_x in Q
                # extra-AND options: x-junk as 1-2 new level-1 ANDs (always possible, rank<=4), d-junk in V?
                res.append('pair%s: junk in V %s | d-junk in V %s | x-junk in A1span %s' % (pairing, inV, dV, xQ))
        print('S%d: %d products, levels %s' % (k, len(prods), sorted(lg[s] for s in prods)))
        for r in res: print('    ' + r)
    # d-junk: products of Y-side pairs, mod V
    ys = list(ysides)
    print('Y_a*Y_b in V:', [(i, j) for i in range(len(ys)) for j in range(i+1, len(ys)) if (ys[i] & ys[j]) in V])
    VY = V.copy()
    for i in range(len(ys)):
        for j in range(i+1, len(ys)): VY.add(ys[i] & ys[j])
    print('dim V + {Y_aY_b}:', VY.dim(), 'vs dim V', V.dim())
if __name__ == "__main__":
    main(sys.argv[1])
