"""Spans of V_N with within-row GF(4) norms N(a_r), N(b_r) and umizame's p's (tower model)."""
import itertools
from h2lib import Basis
import tsearch as TS
from tower import m4, tau, W, W2, norm, tab, VAR, ONE
aff = [ONE] + VAR
VN = [tab(lambda L, R, v, j=j: norm(L, R) >> j & 1) for j in range(4)]
P = TS.early_products()
def Nf(coef): return tab(lambda L, R, v: tau(TS.lam_val(coef, L, R)) & tau(m4(W, TS.lam_val(coef, L, R))))
norms = {}
for r, (a, b, c) in enumerate(TS.ROWS):
    norms['Na%d' % r] = Nf(a); norms['Nb%d' % r] = Nf(b)
def dim(vs):
    B = Basis()
    for v in aff + vs: B.add(v)
    return B.n - 9
print('dim VN', dim(VN), ' dim p-span', dim(P), ' VN in p-span:', dim(P + VN) == dim(P))
for rows in [(0,), (1,), (2,), (0, 1), (0, 2), (1, 2), (0, 1, 2)]:
    ns = [norms['Na%d' % r] for r in rows] + [norms['Nb%d' % r] for r in rows]
    others = [r for r in range(3) if r not in rows]
    ps = [P[3 * r + i] for r in others for i in range(3)]
    print('norm rows', rows, ': dim(VN+norms)', dim(VN + ns), ' dim(VN+norms+p of other rows)', dim(VN + ns + ps),
          ' norms in p-span:', [dim(P + [n]) == dim(P) for n in ns])
