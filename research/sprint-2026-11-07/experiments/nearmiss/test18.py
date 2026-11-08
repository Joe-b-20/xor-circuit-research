import json, os, glob, sys
from common import *
import sat87
P = pairs18()
pv = set((1 << a) | (1 << b) for a, b in P)
BL = os.path.join(ARCH, "AES_Deep_Repair_75_76_Profiles_2026_10_02/aes_deep_repair/results/baselines")
cands = {"repo88@5": sat87.load_repo_circ()}
for f in sorted(glob.glob(BL + "/*.json")):
    try:
        d = json.load(open(f))
        if isinstance(d, dict) and isinstance(d.get("gates"), list) and len(d["gates"]) == 88:
            cands[os.path.basename(f)] = sat87.load_record(f)
    except Exception:
        pass
tidx = {t: i for i, t in enumerate(TARGETS)}
for name, o in cands.items():
    vs = sat87.values_of(o)
    pg = [v for v, a, b in o if a in INPUTS and b in INPUTS]
    if not pv <= set(pg):
        continue
    rich = [v for v in vs if v not in pg]
    K = list(pv) + rich
    comp = set(sat87.values_of(sat87.wiring_from_values_partial(K)))
    miss = [v for v in K if v not in comp]
    print(name, "pairs", len(pg), "rich", len(rich), "regenerated", len(comp), "missing", [("y%d" % tidx[v] if v in tidx else hex(v)) for v in miss])
    # also try dropping (8,16) pair too (19-pair hypothesis: 18 + (1,17) baseline)
    for drop in [v for v in pg if v not in pv]:
        K2 = [v for v in K if v != drop]
        comp2 = set(sat87.values_of(sat87.wiring_from_values_partial(K2)))
        miss2 = [v for v in K2 if v not in comp2]
        print("   also dropping", hex(drop), "regen", len(comp2), "missing", [("y%d" % tidx[v] if v in tidx else hex(v)) for v in miss2])
