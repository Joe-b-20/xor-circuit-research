"""Sanity checks of topenum: the reference's own helper triple must be feasible at GD 32; without a
depth cap, two-helper sets must exist (XORFlux found 17-gate tops)."""
import itertools
import sys

import topenum

path = sys.argv[1]
for gd in (32, 99):
    gates, s, forms, inj = topenum.top_spec(path, gd)
    F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
    trip = (0b10010, 0b100001, 0b101000)   # x1+x4, x0+x5, x3+x5
    S = set(F) | set(trip)
    lv = topenum.closure_levels(S)
    ok = all(t in lv for t in S) and all(lv[t] <= d for t, d in F.items())
    print('gd', gd, 'reference triple feasible:', ok, 'max form level', max(lv[t] for t in F) if ok else None)
gates, s, forms, inj = topenum.top_spec(path, 99)
F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
n = 0
for hs in itertools.combinations(allv, 2):
    S = set(F) | set(hs)
    lv = topenum.closure_levels(S)
    if all(t in lv for t in S):
        n += 1
        if n <= 3:
            print('no-cap 2-helper example', [bin(h) for h in hs], 'depth', max(lv[t] for t in F))
print('no-cap feasible 2-helper sets', n)
