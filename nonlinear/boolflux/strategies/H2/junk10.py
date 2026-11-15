"""Junk analysis of all 10-member GF(4)-norm layers (relaxed model, v independent, gamma = 0).

For each 10-dim bilinear span S (10200, from enum_s.py) up to the symmetry x -> a x, v -> c v,
and each basis X of S made of members (10 of the 15 members in S): the targets' coefficient
vectors are unique; report J_x = dim span of the targets' x-junk mod (affine + V_N) and
J_v = dim span of their v-junk mod affine(v).
"""
import itertools, pickle, sys, time, os
from h2lib import Basis, gmul, gpow
import relax as RX
import a28parse as AP

t0 = time.time()
M, PI = RX.all_members(with_index=True)
S10 = pickle.load(open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/S10.pkl'), 'rb'))['S']
g = 3; c = gpow(3, 17)
memb = [(m[3], m[4]) for m in M]
act_a = [PI[(gmul(g, A), s)] for (A, s) in memb]
act_c = [PI[(A, gmul(c, s))] for (A, s) in memb]
Sset = {frozenset(s) for s in S10}
seen = set(); orbits = []
for s in S10:
    fs = frozenset(s)
    if fs in seen: continue
    orb = {fs}; stack = [fs]
    while stack:
        u = stack.pop()
        for act in (act_a, act_c):
            v = frozenset(act[i] for i in u)
            if v not in orb: orb.add(v); stack.append(v)
    assert orb <= Sset
    seen |= orb
    orbits.append((sorted(fs), len(orb)))
print('orbits of 10-dim S:', len(orbits), [o[1] for o in orbits], round(time.time() - t0, 1), flush=True)

XF = Basis()
for v in [AP.ONE] + AP.BITS + AP.Ntabs: XF.add(v)
VF = Basis()
VONE = 0xFFFF
vl = [sum(1 << m for m in range(16) if m >> j & 1) for j in range(4)]
for v in [VONE] + vl: VF.add(v)
xj = [XF.full_reduce(m[1])[0] for m in M]
vj = [VF.full_reduce(m[2])[0] for m in M]
T = [RX.target_parts(1 << i, 0) for i in range(8)]
txj = [XF.full_reduce(t[1])[0] for t in T]
tvj = [VF.full_reduce(t[2])[0] for t in T]
assert all(v == 0 for v in txj) and all(v == 0 for v in tvj)

results = []
for oi, (mem, osz) in enumerate(orbits):
    hist = {}
    best = None
    for X in itertools.combinations(mem, 10):
        B = Basis(track=True)
        ok = True
        for j, i in enumerate(X):
            if not B.add(M[i][0], 1 << j): ok = False; break
        if not ok: continue
        XJ = Basis(); VJ = Basis(); XVJ = Basis()
        for t in T:
            r, tag = B.full_reduce(t[0])
            assert r == 0
            a = 0; b = 0
            for j in range(10):
                if tag >> j & 1: a ^= xj[X[j]]; b ^= vj[X[j]]
            XJ.add(a); VJ.add(b); XVJ.add((a << 16) | b)
        key = (XJ.n, VJ.n)
        hist[key] = hist.get(key, 0) + 1
        if best is None or key < best[0]: best = (key, X)
    print('orbit', oi, 'size', osz, 'classes(s):', sorted({RX.trK(0) for _ in [0]}),
          'hist (Jx,Jv):', dict(sorted(hist.items())), 'best', best[0], round(time.time() - t0, 1), flush=True)
    results.append((mem, osz, hist, best))
pickle.dump(results, open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/junk10.pkl'), 'wb'))
