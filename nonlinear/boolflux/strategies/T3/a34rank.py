#!/usr/bin/env python3
"""T3: can the junk N-quadratic form of the mixed level-2 products (tau1 tau2, supported on the T-plane)
replace one of the 3 pure-N level-2 ANDs? The 3 Q forms Tr_{4/2}(v N^5) (v in GF(4)*) are realised as
p_a + p_b with 3 rank-2 forms; with tau1 tau2 as one of them, the other two would be Q_v + tau1 tau2:
we compute the symplectic rank of Q_v + tau1 tau2 (mod linear terms) for all v and all choices of the
T-plane basis. Computation on GF(16) = {x^17} inside GF(256) (poly 0x11B)."""
import itertools, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import _gmul, _gpow
G16 = sorted({_gpow(x, 17) for x in range(256)})        # 16 elements
assert len(G16) == 16
G4 = sorted({_gpow(x, 85) for x in range(256)})
def tr(z, k):   # trace from GF(2^k) subfield... use absolute trace of GF(256) scaled: Tr_{256/2}
    t = 0; y = z
    for _ in range(8): t ^= y; y = _gmul(y, y)
    return t & 1
# basis of GF(16) over GF(2)
basis = []
def span(b):
    s = {0}
    for v in b: s |= {x ^ v for x in s}
    return s
for z in G16:
    if z and z not in span(basis): basis.append(z)
assert len(basis) == 4
def coord(N):     # N as 4-bit vector over basis
    for m in range(16):
        v = 0
        for i in range(4):
            if (m >> i) & 1: v ^= basis[i]
        if v == N: return m
elems = {coord(N): N for N in G16}
def form_table(f):     # f: GF(16) element -> bit ; returns table over 16 coords
    return [f(elems[m]) for m in range(16)]
def symp_rank(tab):
    # B(x,y) = q(x+y)+q(x)+q(y)+q(0) on F2^4 ; matrix B_ij = B(e_i, e_j)
    q = tab
    M = [[q[(1 << i) ^ (1 << j)] ^ q[1 << i] ^ q[1 << j] ^ q[0] if i != j else 0 for j in range(4)] for i in range(4)]
    rows = [sum(M[i][j] << j for j in range(4)) for i in range(4)]
    r = 0
    for col in range(4):
        p = next((k for k in range(r, 4) if (rows[k] >> col) & 1), None)
        if p is None: continue
        rows[r], rows[p] = rows[p], rows[r]
        for k in range(4):
            if k != r and (rows[k] >> col) & 1: rows[k] ^= rows[r]
        r += 1
    return r
# Q_v(N) = Tr_{256/2}(w N^5) for w ranging (functionals of N^5 in GF(4)); collect distinct tables
Qs = {}
for w in range(1, 256):
    tab = tuple(form_table(lambda N, w=w: tr(_gmul(w, _gpow(N, 5)), 8)))
    if any(tab): Qs[tab] = w
Qs = [list(t) for t in Qs]
print('distinct Q forms', len(Qs), 'ranks', [symp_rank(q) for q in Qs])
# T-plane functionals: N -> Tr(u (N + N^4)), u any; distinct nonzero
Ts = {}
for u in range(1, 256):
    tab = tuple(form_table(lambda N, u=u: tr(_gmul(u, N ^ _gpow(N, 4)), 8)))
    if any(tab): Ts[tab] = u
Ts = [list(t) for t in Ts]
print('distinct T functionals', len(Ts))
t1, t2 = Ts[0], [t for t in Ts if t != Ts[0]][0]
rho = [a & b for a, b in zip(t1, t2)]
print('rank of tau1 tau2:', symp_rank(rho))
for q in Qs:
    s = [a ^ b for a, b in zip(q, rho)]
    print('rank(Q + tau1 tau2) =', symp_rank(s))
