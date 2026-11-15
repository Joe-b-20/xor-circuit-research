"""Bilinear span dimension of known layers in the tower model."""
from h2lib import Basis
import tsearch as TS
from tower import tab, W, W2
def bil(t):
    # cross part: f(L,R,v) + f(L,R,0) + f(0,0,v) + f(0,0,0) as table over (L,R,v)
    out = 0
    for p in range(4096):
        lr = p & 255; v = p >> 8
        b = ((t >> p) ^ (t >> lr) ^ (t >> (v << 8)) ^ t) & 1
        if b: out |= 1 << p
    return out
A28 = [((1, 2, 2, 3), (3, 0)), ((1, 2, 2, 3), (0, 3)), ((1, 1, 2, 2), (3, 0)), ((0, 0, 1, 1), (0, 1)), ((1, 3, 0, 2), (3, 0)), ((1, 2, 3, 2), (0, 3)), ((1, 3, 2, 1), (1, 2)), ((1, 2, 0, 0), (3, 0)), ((1, 3, 1, 0), (3, 0)), ((0, 1, 0, 2), (2, 3)), ((1, 3, 3, 2), (1, 2)), ((1, 0, 1, 2), (2, 3)), ((0, 1, 2, 3), (2, 3))]
cells = [(1, W2), (W, W2), (W2, 1), (W, 1), (W2, W)]
UMI = [(TS.lin_comb(r, a, t, b), c) for a, b, c in TS.ROWS for r, t in cells]
T = [bil(t) for t in TS.targets(0)]
for name, L in (('A28', A28), ('umizame', UMI)):
    B = Basis()
    for lc, mc in L: B.add(bil(TS.member_table(lc, mc)))
    TB = B.copy()
    print(name, 'k', len(L), 'bil dim d =', B.n, 'T inside:', all(B.contains(t) for t in T))
