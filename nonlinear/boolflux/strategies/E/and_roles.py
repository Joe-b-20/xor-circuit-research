"""Roles of the ANDs of a circuit: level, which later ANDs' operand forms use it, whether outputs use it,
and the GF(2^4) interface content (dimension of N/N^-1/u span within the prefix up to each AND)."""
import sys
from common import *
import skeleton_e as skeleton

VN = fn_tables(lambda x: gpow(x, 17))
c = load(sys.argv[1]); n = c.n
sk = skeleton.extract(c)
K = len(sk['ands'])
lvl = []
for k, (L, R) in enumerate(sk['ands']):
    deps = [j for j in range(k) if ((L | R) >> (1 + n + j)) & 1]
    lvl.append(1 + max([lvl[j] for j in deps], default=0))
users = {k: [] for k in range(K)}
for k, (L, R) in enumerate(sk['ands']):
    for j in range(k):
        if ((L | R) >> (1 + n + j)) & 1: users[j].append(k)
outuse = {k: sum(1 for o in sk['outputs'] if (o >> (1 + n + k)) & 1) for k in range(K)}
# truth tables of the ANDs
tabs = c.tables(); andsig = [c.n + j for j, g in enumerate(c.gates) if g[0] in core.NONLINEAR_OPS]
# minimal set of level-1 ANDs whose span (with x) contains N
spN = Span(VN)
for k in range(K):
    L, R = sk['ands'][k]
    xin = lambda f: f & ((1 << (1 + n)) - 1) == f
    print('AND %2d lvl %d  L%s R%s  used by %s  outputs %d' % (k, lvl[k], 'x' if xin(L) else '*', 'x' if xin(R) else '*', users[k], outuse[k]))
# which level-1 ANDs matter for N: N bits as forms over basis
from itertools import combinations
basis_tabs = []
ones = ONES
it = core.input_tables(n)
def form_table(f, andt):
    t = 0
    if f & 1: t ^= ones
    for i in range(n):
        if (f >> (1 + i)) & 1: t ^= it[i]
    for k in range(K):
        if (f >> (1 + n + k)) & 1: t ^= andt[k]
    return t
andt = []
for k, (L, R) in enumerate(sk['ands']):
    andt.append(form_table(L, andt) & form_table(R, andt))
# express each N bit in span of inputs + level-1 ANDs
l1 = [k for k in range(K) if lvl[k] == 1]
rows = []
for k in l1: rows.append((andt[k], 1 << k))
for i in range(n): rows.append((it[i], 0))
rows.append((ones, 0))
def express(t):
    # gaussian elimination with tracking
    piv = {}
    for tt, tag in rows:
        for p in sorted(piv, reverse=True):
            if (tt >> p) & 1: tt ^= piv[p][0]; tag ^= piv[p][1]
        if tt: piv[tt.bit_length() - 1] = (tt, tag)
    for p in sorted(piv, reverse=True):
        if (t >> p) & 1: t ^= piv[p][0]
    return t == 0
need = set()
for b in VN:
    if b == 0: continue
    # which level-1 ANDs are needed: drop one at a time
    pass
for drop in l1:
    sub = [r for r in rows if r[1] != (1 << drop)]
    piv = {}
    for tt, tag in sub:
        for p in sorted(piv, reverse=True):
            if (tt >> p) & 1: tt ^= piv[p]
        if tt: piv[tt.bit_length() - 1] = tt
    ok = True
    for b in VN:
        t = b
        for p in sorted(piv, reverse=True):
            if (t >> p) & 1: t ^= piv[p]
        if t: ok = False
    print('N spanned without level-1 AND %d: %s' % (drop, ok))
