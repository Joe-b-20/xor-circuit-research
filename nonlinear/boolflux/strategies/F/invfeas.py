#!/usr/bin/env python3
"""Which extra level-0 linear inputs make the inversion targets depth-3 computable (track F)."""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from invsyn import X, Y, M   # noqa: E402

combos = []
for r in (2, 3, 4):
    for ks in itertools.combinations(range(4), r):
        v = 0
        for k in ks: v ^= X[k]
        combos.append(('^'.join(map(str, ks)), v))


def reach(base, d):
    S = set(base)
    for _ in range(d):
        L = list(S); new = set()
        for i, a in enumerate(L):
            new.add(a ^ M)
            for b in L[i:]:
                new.add(a & b); new.add(a ^ b); new.add(a ^ b ^ M)
        S |= new
    return S


y0, y1, y2, y3 = Y
T = [y0, y1, y2, y3, y0 ^ y2, y1 ^ y3]
R2 = None
for k in range(0, 3):
    for sub in itertools.combinations(combos, k):
        base = list(X) + [v for nm, v in sub]
        S2 = reach(base, 2)
        # depth 3: op(a, b) with a, b in S2
        L = list(S2); S2s = S2
        ok = []
        for t in T:
            found = (t ^ M) in S2s or t in S2s
            if not found:
                for a in L:
                    if (t ^ a) in S2s or (t ^ a ^ M) in S2s: found = True; break
            if not found:
                sup = [a for a in L if a & t == t]
                for i, a in enumerate(sup):
                    for b in sup[i:]:
                        if a & b == t: found = True; break
                    if found: break
            ok.append(found)
        if any(ok):
            print('extra', [nm for nm, v in sub], 'depth-3 targets reachable:', ok, 'R2 size', len(S2), flush=True)
