"""CHECKS (finite, not proofs) for the second review of joint01 Theorem A.
Convention of check_j01.py / REPORT: low nibble = omega (own, w), high nibble = s (free), bit k = index k.
A_i = (E_i | p_i), p_i = u_(i-1) + u_i, X(v) = (v | v).
"""
from itertools import combinations

U = [1, 2, 4, 8]
EVEN = [v for v in range(1, 16) if bin(v).count("1") % 2 == 0]
E = [15 ^ U[i] for i in range(4)]
P = [U[(i - 1) % 4] | U[i] for i in range(4)]
W = list(U)
A = [E[i] | (P[i] << 4) for i in range(4)]
X = lambda v: v | (v << 4)
om = lambda x: x & 15
sp = lambda x: x >> 4


def rank(vs):
    b = []
    for v in vs:
        for c in b:
            v = min(v, v ^ c)
        if v:
            b.append(v)
    return len(b)


def fmt(x):
    return "(%s | %s)" % (format(om(x), "04b")[::-1], format(sp(x), "04b")[::-1])


# 1. the user's example, translated.  User: (own|free), s_0 = u_0 + u_1 (primal / reflected indexing).
#    Under c -> -c the user's A_0 = (E_0 | u_0+u_1) is REPORT's A_0 = (E_0 | u_3+u_0) only after reflection;
#    in REPORT coordinates the analogous aux is h = (E_0 | 1111).
h = E[0] | (15 << 4)
print("h =", fmt(h))
print(" h + w_0 =", fmt(h ^ W[0]), "= X(1111):", h ^ W[0] == X(15))
print(" h + (0|p_0+1111) =", fmt(h ^ ((P[0] ^ 15) << 4)), "= A_0:", h ^ ((P[0] ^ 15) << 4) == A[0])

# 2. for every basis and every possible aux value beta: services with a named partner (F3 count, counting
#    BOTH directions of an R+R' representation) and services with a free partner.
worst = 0
for vs in combinations(EVEN, 3):
    if rank(vs) < 3:
        continue
    Xs = [X(v) for v in vs]
    req = A + Xs
    named = W + req
    for beta in range(256):
        if om(beta) == 0 or beta in named:
            continue
        named_srv = [(R, n) for R in req for n in named if n != R and R ^ n == beta]
        free_srv = [R for R in req if om(R) == om(beta)]       # R = beta + (0 | s) for s = s(R)+s(beta)
        reps = {frozenset((R, n)) for R, n in named_srv}
        assert len(reps) <= 1
        assert len(free_srv) <= 1
        worst = max(worst, len(free_srv) + len(reps))
print("check 2: every aux value has <= 1 named representation and <= 1 required vector in its own fibre;"
      " max total kinds =", worst)

# 3. hand claims used for F3: sums of three distinct required vectors are never (unit | 0); differences of two
#    required vectors are never (unit|0) or (even|0).
for vs in combinations(EVEN, 3):
    if rank(vs) < 3:
        continue
    req = A + [X(v) for v in vs]
    for t in combinations(req, 3):
        s = t[0] ^ t[1] ^ t[2]
        assert not (sp(s) == 0 and om(s) in U)
print("check 3: no three required vectors sum to (unit | 0)")

# 4. p = 3 last sub-case: v_1 = {i, j}, beta_1 = (v_1|0), X_1, k notin v_1, beta_2 = X_1 + w_k = (E_l|v_1),
#    A_l, beta_3 = (E_j | p_i), l = i - 1.  Signals before beta_3: w, beta_1, X_1, beta_2, A_l (+ free).
#    beta_3 must be a first gate (not an entry): a sum of two non-free signals.  Check none works.
cnt = 0
for i in range(4):
    for j in range(4):
        if j == i:
            continue
        v1 = U[i] | U[j]
        l = (i - 1) % 4
        if l == j:
            continue
        k = [x for x in range(4) if x not in (i, j, l)][0]
        b1 = v1
        X1 = X(v1)
        b2 = X1 ^ W[k]
        assert om(b2) == E[l]
        b3 = E[j] | (P[i] << 4)
        sig = W + [b1, X1, b2, A[l]]
        for x, y in combinations(sig, 2):
            assert x ^ y != b3
        cnt += 1
print("check 4: p = 3 last sub-case, %d index choices, beta_3 is no sum of two earlier non-free signals" % cnt)
