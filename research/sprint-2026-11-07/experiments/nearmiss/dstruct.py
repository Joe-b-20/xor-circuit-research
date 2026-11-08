"""Structure of candidate D around y19: the dead representative r, its ancestors, and the
window sizes k for singleton seeds (closure under the wiring, and under any pair)."""
import json, os, sys
from common import *
import sat87
order, missing, prof = load_deep("b87_most_exact", 87)
vals = sat87.values_of(order)
par = parents(order); users = sat87.dependents(order); dep = depth_of(order)
tidx = {t: i for i, t in enumerate(TARGETS)}
r = [x["actual"] for x in prof["rows"] if x["residual"]][0]
def nm(v): return ("y%d" % tidx[v]) if v in tidx else ("x%d" % (v.bit_length()-1) if v in INPUTS else "h%08x" % v)
def window(seeds, anypair):
    W = set(seeds) if anypair else sat87.closure_remove(order, seeds)
    W = sat87.private_cone(order, W)
    K = [v for v in vals if v not in W]
    while True:
        if sat87.wiring_from_values(K) is not None: break
        comp = set(sat87.values_of(sat87.wiring_from_values_partial(K)))
        K = [v for v in K if v in comp]
    return set(vals) - set(K)
print("r =", nm(r), "parents", [nm(p) for p in par[r]], "users", [nm(u) for u in users[r]])
anc = []; st = [r]; seen = set()
while st:
    v = st.pop()
    for o in par.get(v, ()):
        if o in par and o not in seen:
            seen.add(o); anc.append(o); st.append(o)
print("ancestors of r:", [(nm(a), dep[a], len(users[a])) for a in anc])
helpers = [v for v in vals if v not in TSET]
rows = []
for h in helpers:
    Wc = window([h, r], False); Wa = window([h, r], True)
    rows.append((len(Wc), len(Wa), h))
rows.sort()
print("singleton windows (with r dropped): k_closure, k_anypair, helper, depth, users, targets in W")
for kc, ka, h in rows:
    Wc = window([h, r], False)
    print("%3d %3d %s d%d u%d tW=%d" % (kc, ka, nm(h), dep[h], len(users[h]), len(Wc & TSET)))
