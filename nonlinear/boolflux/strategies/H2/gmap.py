"""Map a real gamma (element of K in FIPS GF(256)) to the tower-model gamma index."""
import sys
import tbuild as TB
from tower import m4, W, b16, g16
from h2lib import gpow
def tower_gamma(gr):
    L, R = TB.LR(gr)
    assert L == R, (L, R)
    A1, A0 = g16(L)
    return b16((m4(W, A1), m4(W, A0)))
for e in (17, 34, 187, 204):
    print('g^%d ->' % e, tower_gamma(gpow(3, e)))
