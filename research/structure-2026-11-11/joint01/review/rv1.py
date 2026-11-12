"""Reviewer checks (no circuit search).
1. MixColumns matrix from GF(2^8) arithmetic: rows of sheets 0 and 1 restricted to blocks 7,0,1, and the
   mirror columns (P and Q) of the J_01 problem.
2. p = 3 last step of Theorem A: for every basis, v1 a pair in the basis, i in v1, k not in v1,
   beta_2 = X_1 + w_k = (E_l | v1), beta_3 = A_i + beta_1: is beta_3 in a target fibre, is beta_2+beta_3
   an X_m, and is beta_3 a sum of two of {w, beta_1, X_1, beta_2, A_l}?
"""
from itertools import combinations

def xt(x):
    x <<= 1
    if x & 0x100:
        x ^= 0x11B
    return x & 0xFF

def mc_col(bs):
    out = []
    for c in range(4):
        b0, b1, b2, b3 = bs[c], bs[(c + 1) % 4], bs[(c + 2) % 4], bs[(c + 3) % 4]
        out.append(xt(b0) ^ xt(b1) ^ b1 ^ b2 ^ b3)
    return out

# row (c, j) as a set of inputs (c', j')
rows = {}
for c in range(4):
    for j in range(8):
        rows[(c, j)] = set()
for cc in range(4):
    for jj in range(8):
        bs = [0, 0, 0, 0]
        bs[cc] = 1 << jj
        o = mc_col(bs)
        for c in range(4):
            for j in range(8):
                if (o[c] >> j) & 1:
                    rows[(c, j)].add((cc, jj))

def blockset(r, blk):
    return frozenset(c for (c, j) in r if j == blk)

E = lambda c: frozenset(x for x in range(4) if x != c)
s = lambda c: frozenset([c, (c + 1) % 4])
for c in range(4):
    r0, r1 = rows[(c, 0)], rows[(c, 1)]
    assert {j for _, j in r0} == {0, 7} and blockset(r0, 0) == E(c) and blockset(r0, 7) == s(c)
    assert {j for _, j in r1} == {0, 1, 7} and blockset(r1, 1) == E(c) and blockset(r1, 0) == s(c) \
        and blockset(r1, 7) == s(c)
print("rows of sheets 0, 1 match (3.1): sheet0 = E_c@0 + s_c@7, sheet1 = E_c@1 + s_c@0 + s_c@7")

# mirror columns: targets t0_c (w_c), t1_c (w'_c); vector = (omega | s) bits omega c, s c
def col(inp):
    om = sum(1 << c for c in range(4) if inp in rows[(c, 0)])
    sp = sum(1 << c for c in range(4) if inp in rows[(c, 1)])
    return om, sp
U = [1, 2, 4, 8]
Ev = [15 ^ u for u in U]
Pv = [U[(i - 1) % 4] | U[i] for i in range(4)]
for k in range(4):
    assert col((k, 0)) == (Ev[k], Pv[k]), "A"
    assert col((k, 1)) == (0, Ev[k]), "B"
    om, sp = col((k, 7))
    assert om == sp == Pv[k], "Q"
print("mirror columns: b_k -> (E_k|p_k), b'_k -> (0|E_k), a_k -> (p_k|p_k): diagonal exports confirmed")

# 2. p = 3 last step
EVEN = [v for v in range(1, 16) if bin(v).count("1") % 2 == 0]
def rank(vs):
    bs = []
    for v in vs:
        for b in bs:
            v = min(v, v ^ b)
        if v:
            bs.append(v)
    return len(bs)
V = lambda om, sp: om | (sp << 4)
A = [V(Ev[i], Pv[i]) for i in range(4)]
W = [V(U[i], 0) for i in range(4)]
cnt = 0
bad = []
for basis in combinations(EVEN, 3):
    if rank(basis) < 3:
        continue
    Xs = [V(v, v) for v in basis]
    for v1 in basis:
        if bin(v1).count("1") != 2:
            continue
        b1 = V(v1, 0); X1 = V(v1, v1)
        for k in range(4):
            if v1 >> k & 1:
                continue
            l = [x for x in range(4) if not (v1 | U[k]) >> x & 1][0]
            b2 = X1 ^ W[k]
            assert b2 == V(Ev[l], v1)
            for i in range(4):
                if not v1 >> i & 1:
                    continue
                b3 = A[i] ^ b1
                om3 = b3 & 15
                if om3 not in Ev:
                    continue  # unit fibre: non-entry duplicate
                if (b2 ^ b3) not in Xs:
                    continue
                cnt += 1
                pool = W + [b1, X1, b2, A[l]]
                if any(x ^ y == b3 for x, y in combinations(pool, 2)):
                    bad.append((basis, v1, k, i))
                # does A_l have a legal label (p_l + v1 must be a basis label)? record only
print("p=3 final configurations reached:", cnt, " failures of 'no two sum to beta_3':", len(bad))
