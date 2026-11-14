#!/usr/bin/env python3
"""Reachability at depth 3 of each y-combo for extra-input sets (track F); combined with the
early sets that make 116's bottom meet cap 14 (fastset.py output), list feasible (early, extras)."""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from invsyn import X, Y, M   # noqa: E402

y0, y1, y2, y3 = Y
COMBO = {'y0': y0, 'y1': y1, 'y2': y2, 'y3': y3, 'y0^y2': y0 ^ y2, 'y1^y3': y1 ^ y3,
         'y0^y1': y0 ^ y1, 'y2^y3': y2 ^ y3, 'y0123': y0 ^ y1 ^ y2 ^ y3}
FEAS = ['0^1', '0^2', '0^3', '1^3', '2^3', '0^2^3', '0^1^2^3']
EARLY = [l.split(':', 1)[1].strip() for l in open(sys.argv[1]) if l.startswith('feasible with earlier')]
EARLY = [eval(e) for e in EARLY]


def val(e):
    v = 0
    for k in e.split('^'): v ^= X[int(k)]
    return v


def reach2(base):
    S = set(base)
    for _ in range(2):
        L = list(S); new = set()
        for i, a in enumerate(L):
            new.add(a ^ M)
            for b in L[i:]:
                new.add(a & b); new.add(a ^ b); new.add(a ^ b ^ M)
        S |= new
    return S


def d3(t, S2, L):
    if t in S2 or (t ^ M) in S2: return True
    for a in L:
        if (t ^ a) in S2 or (t ^ a ^ M) in S2: return True
    sup = [a for a in L if a & t == t]
    for i, a in enumerate(sup):
        for b in sup[i:]:
            if a & b == t: return True
    return False


for k in (0, 1, 2):
    for ex in itertools.combinations(FEAS, k):
        S2 = reach2(list(X) + [val(e) for e in ex]); L = list(S2)
        ok = {nm: d3(t, S2, L) for nm, t in COMBO.items()}
        for early in EARLY:
            if all(ok[e] for e in early):
                print('extras', list(ex), 'early', early, flush=True)
