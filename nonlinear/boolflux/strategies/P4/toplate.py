"""P4: for every 2-helper (17-gate) top layer of a circuit, the lateness of each form against the
deadlines of the fixed rest of the circuit (GD cap given)."""
import itertools
import json
import sys

import topenum


def nm(v):
    return '+'.join(f'x{i}' for i in range(8) if v >> i & 1)


path, gd = sys.argv[1], int(sys.argv[2])
H = int(sys.argv[3]) if len(sys.argv) > 3 else 2
gates, s, forms, inj = topenum.top_spec(path, gd)
F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
for hs in itertools.combinations(allv, H):
    S = set(F) | set(hs)
    lv = topenum.closure_levels(S)
    if all(t in lv for t in S):
        late = {nm(t): lv[t] - d for t, d in F.items() if lv[t] > d}
        inj_av = {nm(m): (lv.get(m, 0 if bin(m).count('1') == 1 else None), d) for m, d in inj.items()}
        print(json.dumps(dict(helpers=[nm(h) for h in hs], maxlate=max(late.values()), late=late,
                              injections_available=inj_av)))
