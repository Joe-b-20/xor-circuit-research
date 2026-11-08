import json, os, sys
from common import *
import sat87

order, missing, prof = load_deep("b87_most_exact", 87)
vals = sat87.values_of(order)
print("D: gates", len(order), "distinct", len(set(vals)), "missing outputs", missing)
dep = depth_of(order)
tv = [t for t in TARGETS if t in set(vals)]
print("targets present", len(tv), "depth over present targets", max(dep[t] for t in tv), "max depth", max(dep.values()))
print("split_closed(D)", sat87.split_closed(vals))
helpers = [v for v in vals if v not in TSET]
print("helpers", len(helpers))
rep = [r for r in prof["rows"] if r["residual"]][0]
print("y19 target %08x actual-rep %08x residual %08x" % (rep["target"], rep["actual"], rep["residual"]))
par = parents(order)
r = rep["actual"]
print("rep parents %08x %08x" % par[r], "depth", dep[r])
users = sat87.dependents(order)
print("rep users", [hex(u) for u in users[r]])
# ancestors of rep
anc = set(); st = [r]
while st:
    v = st.pop()
    for o in par.get(v, ()):
        if o in par and o not in anc:
            anc.add(o); st.append(o)
print("rep ancestors (non-input)", len(anc), "of which targets", len(anc & TSET))
# pair gates count
pairs = [(v, a, b) for v, a, b in order if a in INPUTS and b in INPUTS]
print("input-pair gates in D", len(pairs))

# ---- 18-pair state
P = pairs18()
print("18 pairs", P)
pv = [(1 << a) | (1 << b) for a, b in P]
# candidate 19-pair 88s
cands = {"repo88@5": sat87.load_repo_circ()}
import glob
BL = os.path.join(ARCH, "AES_Deep_Repair_75_76_Profiles_2026_10_02/aes_deep_repair/results/baselines")
for f in sorted(glob.glob(BL + "/*.json")):
    try:
        d = json.load(open(f))
        if isinstance(d, dict) and "gates" in d and isinstance(d["gates"], list) and len(d["gates"]) == 88:
            cands[os.path.basename(f)] = sat87.load_record(f)
    except Exception as e:
        pass
for name, o in cands.items():
    vs = sat87.values_of(o)
    pg = sorted(v for v, a, b in o if a in INPUTS and b in INPUTS)
    extra = [hex(v) for v in pg if v not in pv]
    have = sum(1 for v in pv if v in pg)
    print(name, "gates", len(o), "pair gates", len(pg), "contains 18 pairs:", have, "extra pairs", extra)
