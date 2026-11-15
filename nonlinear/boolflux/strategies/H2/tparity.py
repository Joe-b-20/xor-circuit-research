"""Tower model: which class-parity vectors have free v-junk, per gamma (BMP middle span)."""
from h2lib import Basis
import tsearch as TS
from tower import m4, tau, W, W2, MUL, INV16
MS = Basis()
for t in TS.middle_span16(): MS.add(t)
CL = [(0, 1), (W, 0), (W, 1), (W, W), (W, W2)]   # first three = umizame rows' c
def vj(mu, gamma):
    return sum(1 << D for D in range(16) if (lambda c: tau(m4(W, c)) & tau(c))(TS.mu_val(mu, INV16[D] ^ MUL[gamma][D])))
for g in range(16):
    J = [vj(mu, g) for mu in CL]
    free = []
    for pi in range(1, 32):
        f = 0
        for z in range(5):
            if pi >> z & 1: f ^= J[z]
        if MS.contains(f): free.append(format(pi, '05b')[::-1])
    print('gamma', g, 'free parity (classes 0..4, rows=0,1,2):', free)
