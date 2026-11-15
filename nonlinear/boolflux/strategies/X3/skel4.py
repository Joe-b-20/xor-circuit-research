"""X3: GF(16) analogue of the three-stage skeleton, exact.
Model: stage 1 = l products of x-linear forms whose span (with 1, x) contains the 2 coordinates of the
norm N = x^5 (GF(16) -> GF(4)); GF(4) inversion is linear (free); last layer = m PARALLEL products with
operands in span(1, x, stage-1 products) (superset of span(1, x, N, N^-1)); outputs in the total span.
Prints, for l = 3, 4: number of stage-1 sets and the least m (m = 4, 5, 6 tested)."""
import itertools, sys
from gfinv import inv_table, pow_table
n = 4; NP = 16; ONE = (1 << NP) - 1
X = [sum(((x >> j) & 1) << x for x in range(NP)) for j in range(n)]
def tt(tab, o): return sum(((tab[x] >> o) & 1) << x for x in range(NP))
T = [tt(inv_table(4), o) for o in range(4)]
Nc = [t for t in (tt(pow_table(4, 5), o) for o in range(4)) if t]
class Span:
    def __init__(s, vs=()):
        s.b = {}
        for v in vs: s.add(v)
    def red(s, v):
        while v:
            h = v.bit_length() - 1
            if h not in s.b: return v
            v ^= s.b[h]
        return 0
    def add(s, v):
        v = s.red(v)
        if v: s.b[v.bit_length() - 1] = v; return True
        return False
    def copy(s):
        c = Span(); c.b = dict(s.b); return c
    def __len__(s): return len(s.b)
def lin(mask, gens):
    v = 0
    for j, g in enumerate(gens):
        if (mask >> j) & 1: v ^= g
    return v
def subspaces2(d):
    for a in range(1, 1 << d):
        for b in range(a + 1, 1 << d):
            if (a ^ b) > b: yield a, b
A0 = Span([ONE] + X)
quad = {}
for a, b in subspaces2(4):
    p = lin(a, X) & lin(b, X); quad[A0.red(p)] = (a, b)
quads = list(quad)   # 35 rank-2 classes
print('rank-2 quadratic classes', len(quads))
def minlayer(gens):
    V = Span([ONE] + gens)
    VT = V.copy(); [VT.add(t) for t in T]
    cls = set()
    for a, b in subspaces2(len(gens)):
        c = V.red(lin(a, gens) & lin(b, gens))
        if c: cls.add(c)
    cls = list(cls)
    inT = [c for c in cls if VT.red(c) == 0]
    S = V.copy(); [S.add(c) for c in inT]
    if all(S.red(t) == 0 for t in T): return 4, len(cls)
    # m = 5: one junk direction
    seen = set()
    for p in cls:
        r = VT.red(p)
        if not r or r in seen: continue
        seen.add(r)
        VJ = VT.copy(); VJ.add(p)
        S = V.copy(); [S.add(c) for c in cls if VJ.red(c) == 0]
        if all(S.red(t) == 0 for t in T): return 5, len(cls)
    if MAXM < 6: return 6, len(cls)
    out = [c for c in cls if VT.red(c)]
    for p, q in itertools.combinations(out, 2):
        VJ = VT.copy(); VJ.add(p); VJ.add(q)
        S = V.copy(); [S.add(c) for c in cls if VJ.red(c) == 0]
        if all(S.red(t) == 0 for t in T) and len(S) - len(V) <= 6: return 6, len(cls)
    return 7, len(cls)
MAXM = int(sys.argv[2]) if len(sys.argv) > 2 else 6
for l in [int(t) for t in sys.argv[1].split(",")]:
    res = {}; cnt = 0; cntN = 0
    for comb in itertools.combinations(quads, l):
        S = Span([ONE] + X + list(comb))
        hasN = all(S.red(c) == 0 for c in Nc)
        if l >= 3 and not hasN: continue
        cnt += 1
        m, nc = minlayer(X + list(comb))
        res[(hasN, m)] = res.get((hasN, m), 0) + 1
    print('l', l, 'stage-1 sets', cnt, '(hasN, least parallel m): count', sorted(res.items()), flush=True)
