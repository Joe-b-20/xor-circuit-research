"""v-junk of GF(4)-norm members per class zeta, pulled back to functions of N via v = n + gamma N.

Member (A, s): v-junk = Tr_K(s v) Tr_K(w^2 s v) (depends on s up to GF(4)*, i.e. class zeta = s^3).
For each gamma in K and each parity vector pi in F_2^5 over the classes: is
sum_zeta pi_zeta junk_zeta(n + gamma N) in span(1, N, n) (free), in a 5-AND-achievable class
(one extra middle dimension), or neither?
"""
import sys, json
from pathlib import Path
from h2lib import Basis, gmul, gpow, INV
import relax as RX
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'G'))

K = [k for k in RX.KSET if k]
# classes: s up to GF(4)* multiples
w = RX.w; w2 = RX.w2
classes = []
seen = set()
for s in K:
    if s in seen: continue
    cl = {s, gmul(w, s), gmul(w2, s)}
    seen |= cl
    classes.append(min(cl))
assert len(classes) == 5

# index N by 4-bit mask in KB coords
Nval = [RX.vval(m) for m in range(16)]
idx_of = {v: m for m, v in enumerate(Nval)}
INP = [sum(1 << m for m in range(16) if m >> j & 1) for j in range(4)]
ONES = 0xFFFF
ntab = [sum(1 << m for m in range(16) if idx_of[INV[Nval[m]]] >> j & 1) for j in range(4)]


def jz(s, gamma):
    t = 0
    for m in range(16):
        N = Nval[m]; v = INV[N] ^ gmul(gamma, N)
        if RX.trK(gmul(s, v)) & RX.trK(gmul(gmul(w2, s), v)): t |= 1 << m
    return t


base = Basis()
for v in [ONES] + INP + ntab: base.add(v)
assert base.n == 9


def achievable_set():
    import exact_mid as EM
    EM.INP = INP
    comp = []
    sp = base.copy()
    for x in range(1 << 16):
        if sp.add(x): comp.append(x)
        if len(comp) == 7: break
    ok = set()
    for c in range(1, 128):
        v = 0
        for i in range(7):
            if (c >> i) & 1: v ^= comp[i]
        if EM.search(ntab + [v]): ok.add(base.full_reduce(v)[0])
    return ok


if __name__ == '__main__':
    ACH = achievable_set()
    print('achievable extra classes for a 5-AND middle:', len(ACH))
    out = {}
    for gamma in [0] + K:
        J = [base.full_reduce(jz(s, gamma))[0] for s in classes]
        free = []; ach = []
        for pi in range(1, 32):
            f = 0
            for z in range(5):
                if pi >> z & 1: f ^= J[z]
            if f == 0: free.append(pi)
            elif f in ACH: ach.append(pi)
        rk = Basis()
        for j in J: rk.add(j)
        print('gamma %3d  rank(junk_zeta) %d  free parity vectors %s  achievable %s' % (gamma, rk.n, free, ach))
        out[gamma] = {'free': free, 'ach': ach}
    json.dump({'classes': classes, 'P': out, 'ACH': sorted(ACH)},
              open(str(Path('~/xs-campaigns/2026-11-15-study/H2/vjunk.json').expanduser()), 'w'))
