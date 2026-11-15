r"""X3 semi.py: algebraic type of the rank<=2 tensors that share a T_b-coset (sizes 2, 3, 5).
Tensor = l1 (x) lam1 + l2 (x) lam2, l(x) = Tr_F(A x), lam(n) = Tr_K(e n).  Reports per coset size the
distribution of (rank, class of A1/A2, class of e1/e2) with classes: Q* = GF(4) \ {0,1}, K = GF(16) \ GF(4), F = other,
and the K-lines (c K, identified by c^15) of the differences inside a coset."""
import os, sys
from collections import Counter
from gfinv import gmul, gpow
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/X3/')
def tr(z, n=8):
    s = 0
    for _ in range(8): s ^= z; z = gmul(z, z, 8)
    return s & 1
inv = [gpow(x, 254, 8) for x in range(256)]
nn = [gpow(x, 238, 8) for x in range(256)]
Kset = sorted(set(nn)); assert len(Kset) == 16
Q = {x for x in Kset if gpow(x, 4, 8) == x}
# x-form mask u (bit i <-> x_i) -> A with Tr(A x) = parity(u & x)
A_of = {}
for A in range(256):
    u = sum(tr(gmul(A, 1 << i, 8)) << i for i in range(8)); A_of[u] = A
# n-forms: same coordinates as bil_tb.py: first 4 independent bits of n
def tt(f): return sum((f(x) & 1) << x for x in range(256))
cand = [tt(lambda x, i=i: nn[x] >> i) for i in range(8)]
NBidx = []; bas = []
for i, c in enumerate(cand):
    r = c
    for b in bas: r = min(r, r ^ b)
    if r: bas.append(r); bas.sort(reverse=True); NBidx.append(i)
e_of = {}
for e in Kset:   # form n -> Tr_K(e n) = Tr_F(e' n)?  use Tr_F(E n) restricted to K, E in F; find mask over NB bits
    pass
# lam mask m (bit j <-> bit NBidx[j] of n) ; find E in F with Tr_F(E k) = lam(k) for all k in K ; identify by values on K
def lam_vals(m): return tuple(bin(m & sum(((k >> NBidx[j]) & 1) << j for j in range(4))).count('1') & 1 for k in Kset)
val2m = {lam_vals(m): m for m in range(16)}
E_of = {}
for E in range(256):
    v = tuple(tr(gmul(E, k, 8)) for k in Kset)
    if v in val2m and val2m[v] not in E_of: E_of[val2m[v]] = E   # E defined mod ker; ratio classes need K-valued rep
# K-valued representative: Tr_F(E k) = Tr_K(Tr_{F/K}(E) k); e = E + E^16
e_of = {m: E ^ gpow(E, 16, 8) for m, E in E_of.items()}
def cls(r):
    if r in Q: return 'Q*' if r > 1 else '1'
    if r in Kset: return 'K'
    return 'F'
def decomp(t):
    rows = [(t >> (8 * j)) & 255 for j in range(4)]
    # row space basis
    bs = []
    for v in rows:
        r = v
        for b in bs: r = min(r, r ^ b)
        if r: bs.append(r)
    if len(bs) == 1:
        l = bs[0]; lam = sum(1 << j for j in range(4) if rows[j] == l)
        return 1, None, None
    l1, l2 = bs[0], bs[1]
    # rows[j] = a_j l1 + b_j l2
    lam1 = lam2 = 0
    for j, v in enumerate(rows):
        for a, b in ((0, 0), (1, 0), (0, 1), (1, 1)):
            if (l1 if a else 0) ^ (l2 if b else 0) == v: lam1 |= a << j; lam2 |= b << j; break
        else: return 3, None, None
    rA = gmul(A_of[l1], gpow(A_of[l2], 254, 8), 8); re = gmul(e_of[lam1], gpow(e_of[lam2], 254, 8), 8)
    # ratio classes are basis dependent only within {r, r+1, 1/r, ...}: class membership in Q/K/F is invariant
    return 2, cls(rA), cls(re)
# dual basis for outputs: T_b element <-> c
stat = {}
for ln in open(D + 'bil_cosets2.txt'):
    p = ln.split(); sz = int(p[2]); ts = [int(z, 16) for z in p[3:]]
    key = tuple(sorted(Counter(decomp(t) for t in ts).items()))
    stat.setdefault(sz, Counter())[key] += 1
for sz in sorted(stat):
    print('coset size', sz)
    for k, v in stat[sz].most_common(): print('   ', v, 'cosets:', k)
