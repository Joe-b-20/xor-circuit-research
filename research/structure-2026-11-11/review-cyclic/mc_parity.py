"""Parity invariance for MixColumns re-encodings: all 64 boundary vectors odd => parity(phi(v)) = parity(v)."""
import os, random
P = os.path.expanduser('~/xor-circuit-research/lower-bound-proofs/mixcolumns-lb75/source/matrix.txt')
rows = [l.strip() for l in open(P) if l.strip()]
n = len(rows)
M = [sum(1 << i for i, ch in enumerate(r) if ch == '1') for r in rows]
MT = [sum(((M[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
w = lambda v: bin(v).count('1')
print("n =", n, " row weights", sorted(set(map(w, M))), " column weights", sorted(set(map(w, MT))))
def solve_basis(I):
    # phi with phi(I[k]) = e_k : return function via inverse of matrix with rows I
    rows_ = [(I[k], 1 << k) for k in range(n)]
    piv = {}
    for a, b in rows_:
        for h, (pa, pb) in piv.items():
            if (a >> h) & 1: a ^= pa; b ^= pb
        if a == 0: return None
        h = a.bit_length() - 1
        for hh in list(piv):
            pa, pb = piv[hh]
            if (pa >> h) & 1: piv[hh] = (pa ^ a, pb ^ b)
        piv[h] = (a, b)
    # coordinates: v = sum over pivots; phi(v) = xor of pb for pivots used
    def phi(v):
        out = 0
        for h in sorted(piv, reverse=True):
            if (v >> h) & 1:
                v ^= piv[h][0]; out ^= piv[h][1]
        assert v == 0
        return out
    return phi
B = [1 << i for i in range(n)] + M
rng = random.Random(1)
ok = 0; tried = 0
for t in range(300):
    I = rng.sample(B, n)
    phi = solve_basis(I)
    if phi is None: continue
    tried += 1
    good = all(w(phi(v)) % 2 == w(v) % 2 for v in [rng.randrange(1, 1 << n) for _ in range(200)])
    MI = [phi(b) for b in B if b not in I]
    MIT = [sum(((MI[i] >> j) & 1) << i for i in range(n)) for j in range(n)]
    good = good and all(w(r) % 2 for r in MI + MIT)
    ok += good
print("random information sets:", tried, " parity preserved and M_I rows/columns odd in all:", ok == tried)
phi = solve_basis(M)  # inverse
Minv = [phi(1 << i) for i in range(n)]
print("InvMC rows odd:", all(w(r) % 2 for r in Minv), " InvMC row weights", sorted(set(map(w, Minv))))
