"""Print the last-layer products of an A28 file in coordinates (const | x 8 | N 4 | n 4) and the
grade content of the pure-x quadratic part alpha ^ alpha'."""
import sys

import gf
from structure import analyse
from exp_stage3 import coords

N = [gf.power(p, 17) for p in range(256)]
n = [gf.INV[v] for v in N]
sp = gf.Span(); basis = []
for v in gf.SUB16:
    if v and sp.add(v): basis.append(v)
Nt = gf.coord_tables(N, basis); nt = gf.coord_tables(n, basis)
B = [gf.ONES] + gf.X + Nt + nt

# grade classes of quadratic x-forms: Tr(c x^3), Tr(c x^5), Tr(c x^9), N
def trace_fn(e, c):
    out = 0
    for p in range(256):
        v = gf.mul(c, gf.power(p, e)); t = 0
        for i in range(8): t ^= gf.power(v, 1 << i)
        if t & 1: out |= 1 << p
    return out

cls = {}
for e in (3, 5, 9, 17):
    sp2 = gf.Span(); vs = []
    for c in range(1, 256):
        t = gf.anf_quadratic_part(trace_fn(e, c))
        if sp2.add(t): vs.append(t)
    cls[e] = vs
allq = []; tags = []
for e in (3, 5, 9, 17):
    for v in cls[e]: allq.append(v); tags.append(e)
SQ = gf.Span()
for i, v in enumerate(allq): SQ.add(v, 1 << i)
print('class dims', {e: len(v) for e, v in cls.items()})


def grade_content(q):
    r, t = SQ.reduce(q, 0)
    assert r == 0
    out = {}
    for i in range(len(allq)):
        if (t >> i) & 1: out[tags[i]] = out.get(tags[i], 0) + 1
    return out


def wedge_x(a, b):
    import itertools
    w = 0
    for k, (i, j) in enumerate(itertools.combinations(range(8), 2)):
        if (a[i] & b[j]) ^ (a[j] & b[i]): w |= 1 << k
    return w


c, ands, outs, tabs = analyse(sys.argv[1])
top = max(A['level'] for A in ands)
print('level-1 products grade content:')
for k, A in enumerate(ands):
    if A['level'] == 1:
        print('  a%d' % (k + 1), grade_content(gf.anf_quadratic_part(A['tab'])))
for k, A in enumerate(ands):
    if A['level'] != top: continue
    L = coords(B, A['Ltab']); R = coords(B, A['Rtab'])
    f = lambda v: '%d|%s|%s|%s' % (v[0], ''.join(map(str, v[1:9])), ''.join(map(str, v[9:13])), ''.join(map(str, v[13:17])))
    q = wedge_x(L[1:9], R[1:9])
    print('a%-2d %s * %s   x-wedge grades %s' % (k + 1, f(L), f(R), grade_content(q) if q else '-'))
