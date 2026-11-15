"""X3 bil.py: the x(x)n bilinear part of ANY product with operands in span(1, x, N, n).
Tensor = 4x8 GF(2) matrix (n-form index j, x-bit i) <-> function sum t_ji x_i n_j.  A product
(l + lam + ..)(l' + lam' + ..) has x(x)n-part l(x)lam' + l'(x)lam, of rank <= 2.  The four cyclotomic classes
of x^(2^i) n^(2^j) (127, 15, 47, 111) are disjoint from all classes of the other parts (x*x, n*n, x*N, n*N,
N*N, affine), so the x(x)n-part of a function in the span is well defined, and the outputs' parts span T_b
(8-dim, every nonzero element of rank 4).
Computes: (1) max number of rank<=2 tensors in a coset j + T_b  (m = 9 possible iff some coset has 9
affinely spanning ones); (2) all 10-dim S = T_b + J spanned by rank<=2 tensors (optional, arg '10')."""
import sys, pickle, os
from collections import defaultdict
from gfinv import gmul, gpow
n = 8
inv = [gpow(x, 254, 8) for x in range(256)]
nn = [gpow(x, 238, 8) for x in range(256)]
def tt(f): return sum((f(x) & 1) << x for x in range(256))
X = [tt(lambda x, i=i: x >> i) for i in range(8)]
Y = [tt(lambda x, i=i: inv[x] >> i) for i in range(8)]
# 4 independent coordinates of n
ncand = [tt(lambda x, i=i: nn[x] >> i) for i in range(8)]
def reduce(basis, v):
    for p, b in basis:
        if (v >> p) & 1: v ^= b
    return v
NB = []; bas = []
for c in ncand:
    r = reduce(bas, c)
    if r:
        p = r.bit_length() - 1; bas = [(q, b ^ (r if (b >> p) & 1 else 0)) for q, b in bas] + [(p, r)]; NB.append(c)
assert len(NB) == 4
# functions x_i n_j, tensor bit index j*8+i
F = [(NB[j] & X[i], 1 << (j * 8 + i)) for j in range(4) for i in range(8)]
# express outputs: gaussian elimination with tracking
ech = []
for f, tag in F:
    for p, b, t in ech:
        if (f >> p) & 1: f ^= b; tag ^= t
    assert f, 'x_i n_j dependent'
    ech.append((f.bit_length() - 1, f, tag))
Tb = []
for y in Y:
    tag = 0
    for p, b, t in ech:
        if (y >> p) & 1: y ^= b; tag ^= t
    assert y == 0, 'output not bilinear in (x, n)'
    Tb.append(tag)
# echelon of T_b for class reduction
TE = []
for t in Tb:
    for p, b in TE:
        if (t >> p) & 1: t ^= b
    assert t
    p = t.bit_length() - 1
    TE = [(q, b ^ (t if (b >> p) & 1 else 0)) for q, b in TE] + [(p, t)]
def cls(t):
    for p, b in TE:
        if (t >> p) & 1: t ^= b
    return t
def rank(t):
    rows = [(t >> (8 * j)) & 255 for j in range(4)]
    r = 0; bs = []
    for v in rows:
        for b in bs: v = min(v, v ^ b)
        if v: bs.append(v); r += 1
    return r
import itertools
print('ranks in T_b:', sorted(set(rank(sum(Tb[i] for i in range(8) if (m >> i) & 1) if 0 else
      __import__('functools').reduce(lambda a, b: a ^ b, [Tb[i] for i in range(8) if (m >> i) & 1], 0)) for m in range(1, 256))))
# all rank<=2 tensors: rows = lam-coefficients: tensor rows j: l1 if lam1_j, l2 if lam2_j
R = set()
planes = [(a, b) for a in range(1, 16) for b in range(a + 1, 16) if (a ^ b) > b]
for a, b in planes:
    ja = [j for j in range(4) if (a >> j) & 1]; jb = [j for j in range(4) if (b >> j) & 1]
    for l1 in range(256):
        ta = sum(l1 << (8 * j) for j in ja)
        for l2 in range(256):
            R.add(ta ^ sum(l2 << (8 * j) for j in jb))
R.discard(0)
print('rank<=2 tensors', len(R))
by = defaultdict(list)
for t in R: by[cls(t)].append(t)
assert 0 not in by
hist = defaultdict(int)
for c, v in by.items(): hist[len(v)] += 1
print('cosets with rank<=2 tensors:', len(by), 'size histogram', sorted(hist.items()))
pickle.dump((Tb, TE, dict(by)), open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/bil.pkl'), 'wb'))
