#!/usr/bin/env python3
"""T4, bottom-bilinear model at gate depth 11.
Outputs S_k = Tr16(Y * R_k(a)).  An exact 4-term rank decomposition of output k is a GF(2)-basis
A = {alpha_j} of GF(16) with products Tr(alpha_j Y) * Tr(beta_j R_k(a)), {beta_j} the trace-dual basis.
Products of outputs k, l coincide iff alpha equal and Tr(beta R_k) == Tr(beta' R_l) as functions of a,
i.e. beta*theta_k == beta'*theta_l (theta = the AES output functional).  This counts, for every pair
of outputs, the max number of products two exact decompositions can share (exhaustive over all
ordered pairs of bases), and the min total over all 8 outputs is then >= 32 - sum of best sharing
(computed exactly by search below for the one proportional pair)."""
import itertools
# GF(16) = GF(2)[t]/(t^4+t+1)
def m16(a, b):
    r = 0
    for i in range(4):
        if (b >> i) & 1: r ^= a << i
    for i in (7, 6, 5, 4):
        if (r >> i) & 1: r ^= 0b10011 << (i - 4)
    return r
def tr16(z):
    t = 0; s = z
    for _ in range(4): t ^= s; s = m16(s, s)
    return t & 1
els = list(range(1, 16))
def span(v):
    s = {0}
    for x in v: s |= {y ^ x for y in s}
    return s
bases = [b for b in itertools.combinations(els, 4) if len(span(b)) == 16]
print('unordered bases', len(bases))
def dual(b):
    d = []
    for i in range(4):
        cand = [z for z in els if all(tr16(m16(z, b[j])) == (1 if j == i else 0) for j in range(4))]
        assert len(cand) == 1
        d.append(cand[0])
    return d
D = {b: dual(b) for b in bases}
# outputs k, l with theta_l = gamma * theta_k (gamma in GF16*, gamma != 1): product (alpha, beta) of k
# equals product (alpha, beta') of l iff beta = gamma * beta'.  Max sharing over basis pairs, per gamma.
res = {}
for g in range(2, 16):
    best = 0
    for b1 in bases:
        p1 = {(a, d) for a, d in zip(b1, D[b1])}
        for b2 in bases:
            p2 = {(a, m16(g, d)) for a, d in zip(b2, D[b2])}
            s = len(p1 & p2)
            if s > best: best = s
    res[g] = best
print('max shared products for proportional pair, by gamma:', res)
