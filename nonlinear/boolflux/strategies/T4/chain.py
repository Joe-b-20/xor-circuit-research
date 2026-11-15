#!/usr/bin/env python3
"""T4: per output, 3-product (or 2-product) bottom designs with rank-2 products and free junk,
for a FIXED front (exhaustive over the design graphs and the free x-forms, linear parts only).

Output k needs sum_i Y_i w_i (Y_i the level-8 Y-forms, w_i x-linear).  A design is a multiset of
products: rank-2 edge (a,b): (Y_a + u)(Y_b + v) -> bilinear Y_a v + Y_b u, junk Y_aY_b + u v;
rank-1 vertex a: Y_a z.  Coverage equations fix all but f free x-forms.  The design is FREE when
  d-junk (sum of Y_aY_b over edges) in V   and   x-junk (sum u v) in span(1, x, stage-1 products)
(tested on alternating forms, exact).  A free 3-product design saves one AND on that output.
    python3 chain.py FILE
"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from boolflux import core  # noqa

PAIRS = list(itertools.combinations(range(8), 2))
def lin(t, n=8):
    """linear part (8-bit, bit i = input i) of an affine truth table"""
    e = [1 << (n - 1 - i) for i in range(n)]
    c0 = t & 1
    return sum((((t >> e[i]) & 1) ^ c0) << i for i in range(n))
def wedge(l, m):
    w = 0
    for r, (a, b) in enumerate(PAIRS):
        if (((l >> a) & (m >> b)) ^ ((l >> b) & (m >> a))) & 1: w |= 1 << r
    return w
WT = [[0] * 256 for _ in range(256)]
for l in range(256):
    for m in range(l + 1, 256):
        WT[l][m] = WT[m][l] = wedge(l, m)
def qform(t):
    """alternating form of the quadratic part of t (degree <= 2 assumed for the result to mean much)"""
    w = 0; f = lambda x: (t >> x) & 1
    for r, (a, b) in enumerate(PAIRS):
        ea = 1 << (7 - a); eb = 1 << (7 - b)
        if f(0) ^ f(ea) ^ f(eb) ^ f(ea | eb): w |= 1 << r
    return w

class Red:
    def __init__(self, vecs):
        self.p = {}
        for v in vecs: self.add(v)
    def red(self, v):
        for h in sorted(self.p, reverse=True):
            if (v >> h) & 1: v ^= self.p[h]
        return v
    def add(self, v):
        v = self.red(v)
        if v: self.p[v.bit_length() - 1] = v
        return bool(v)

def designs(nY):
    V = range(nY); E = list(itertools.combinations(V, 2))
    out = []
    # 3 products: combinations with repetition of items (edges or vertices)
    items = [('e', e) for e in E] + [('v', (v,)) for v in V]
    for r in (2, 3):
        for combo in itertools.combinations_with_replacement(items, r):
            cov = set()
            for kind, s in combo: cov |= set(s)
            if cov != set(V): continue
            if all(k == 'v' for k, _ in combo): continue
            out.append(combo)
    return out

def solve_design(combo, w, red, dfree_ok):
    """slots: each edge (a,b) has slot (a, v) [x-form multiplying Y_a] and (b, u); vertex a has slot (a, z).
    x-junk: for edge, u*v = slot_b * slot_a.  Coverage: sum of slots at vertex i = w_i."""
    slots = []   # (vertex, product index)
    for t, (kind, s) in enumerate(combo):
        for v in s: slots.append((v, t))
    # per vertex: slots; choose all but last freely, last = w_i + sum others
    byv = {}
    for idx, (v, t) in enumerate(slots): byv.setdefault(v, []).append(idx)
    free = [i for v, L in byv.items() for i in L[:-1]]
    if len(free) > 2: return None
    best = None
    for vals in itertools.product(range(256), repeat=len(free)):
        x = [None] * len(slots)
        for i, val in zip(free, vals): x[i] = val
        for v, L in byv.items():
            s = w[v]
            for i in L[:-1]: s ^= x[i]
            x[L[-1]] = s
        # x-junk
        j = 0; ok = True
        for t, (kind, s) in enumerate(combo):
            if kind == 'e':
                ia = [i for i, (v, tt) in enumerate(slots) if tt == t]
                j ^= WT[x[ia[0]]][x[ia[1]]]
            else:
                pass
        if red.red(j) == 0:
            return x
    return None

if __name__ == '__main__':
    c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    outs = decompose(c, T, la, ba, AD)
    ys = sorted({y for d in outs for y in d}); nY = len(ys)
    red = Red([qform(T[s]) for s in fa if la[s] == 1])
    print('Y-forms', nY, 'stage-1 alternating span dim', len(red.p))
    # d-junk: which edge subsets have sum Y_aY_b in V
    E = list(itertools.combinations(range(nY), 2))
    dsum_ok = {}
    for r in range(0, len(E) + 1):
        for sub in itertools.combinations(E, r):
            s = 0
            for a, b in sub: s ^= ys[a] & ys[b]
            dsum_ok[frozenset(sub)] = (s in V)
    print('edge sets with free d-junk:', [sorted(k) for k, v in dsum_ok.items() if v and k])
    D = designs(nY)
    print('designs', len(D))
    tot = 0
    for k, d in enumerate(outs):
        w = [lin(d.get(y, 0)) for y in ys]
        found = []
        for combo in D:
            edges = [s for kind, s in combo if kind == 'e']
            # d-junk parity: repeated edges cancel
            from collections import Counter
            cnt = Counter(edges)
            es = frozenset(e for e, m in cnt.items() if m % 2)
            if not dsum_ok.get(es, False): continue
            x = solve_design(combo, w, red, True)
            if x is not None: found.append((len(combo), combo))
        found.sort(key=lambda z: z[0])
        bestn = found[0][0] if found else 4
        tot += bestn
        print(json.dumps({'out': k, 'best_products': bestn, 'n_free_designs': len(found),
                          'example': str(found[0][1]) if found else None}), flush=True)
    print('total bottom products (free designs, fixed front):', tot)
