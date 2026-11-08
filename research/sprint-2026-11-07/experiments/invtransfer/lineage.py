"""Step 5: how many independent discovery events do the 118@5 records trace to?  Reads the
metadata (root, chain, move, ref, timestamps) of every adopt and inv118 118@5 record file and of
the other campaigns' inverse g119-d5 / g120-d5 records (did any other run reach 118/119 independently?).
Also: first-layer overlap of the other runs' 119@5 / 120@5 states with the 118 family's fixed pairs."""
import glob
import json
import os
import re
from collections import Counter, defaultdict
import common as C
import pes_lib

sp = pes_lib.make_space("inv", 5)
HOME = C.HOME
FL = C.load("firstlayer118.json")
fixed = {int(h, 16) for h in FL["pairs_in_all_hex"]}
print("118-family fixed L1 pairs:", len(fixed))

# adopt 118 records: roots and chains
roots = Counter()
chains = Counter()
first = {}
for f in sorted(glob.glob(HOME + "/xs-campaigns/2026-10-31-adopt/runs/adopt/workers/inv-cap5-*/records/g118-d5-*.json")):
    d = json.load(open(f))
    m = d.get("metadata") or {}
    roots[(m.get("root") or "")[:80]] += 1
    chains[m.get("chain")] += 1
    w = f.split("/workers/")[1].split("/")[0]
    ts = m.get("found_at") or m.get("time") or m.get("wall") or m.get("it")
    first.setdefault(w, (ts, m.get("root"), m.get("move")))
print("adopt 118 records by root:", roots.most_common(10))
print("adopt 118 records by chain:", len(chains), "chains;", chains.most_common(8))
print("first record per worker (ts, root, move):")
for w, v in sorted(first.items()):
    print("  ", w, v)
# metadata keys of one record
f = sorted(glob.glob(HOME + "/xs-campaigns/2026-10-31-adopt/runs/adopt/workers/inv-cap5-01/records/g118-d5-*.json"))[0]
print("metadata keys:", sorted((json.load(open(f)).get("metadata") or {}).keys()))

# other campaigns' inverse 119/120 at depth 5
stats = {}
for camp in ("2026-10-31-adopt", "2026-10-31-long", "2026-11-03-waits", "2026-11-04-12h", "2026-11-05-inv-star",
             "2026-11-02-v9b", "2026-11-02-v9c", "2026-11-03-v9e", "2026-11-03-12h", "2026-11-06-w500"):
    for g in (119, 120):
        files = glob.glob(HOME + f"/xs-campaigns/{camp}/**/records/g{g}-d5-*.json", recursive=True)
        if not files:
            continue
        n_inv = 0
        states = set()
        ov = Counter()
        runs = Counter()
        for f in files:
            try:
                d = json.load(open(f))
            except Exception:
                continue
            if "gates" not in d:
                continue
            w = C.wiring_of_record(d)
            if not C.is_inverse(w):
                continue
            n_inv += 1
            vals = frozenset(v for v, _, _ in w)
            if vals in states:
                continue
            states.add(vals)
            l1 = {v for v in vals if bin(v).count("1") == 2}
            best = 0
            for s in sp.shifts:
                l1s = set(sp.rot(tuple(sorted(l1)), s)) if s else l1
                best = max(best, len(l1s & fixed))
            ov[best] += 1
            runs[C.run_of(f).rsplit(":", 1)[0]] += 1
        stats[f"{camp} g{g}"] = {"files": len(files), "inverse_files": n_inv, "distinct_states": len(states),
                                 "overlap_with_118_fixed_L1": dict(sorted(ov.items())), "runs": dict(runs)}
        print(camp, g, stats[f"{camp} g{g}"])
C.dump("lineage118.json", {"adopt_roots": dict(roots), "adopt_chains": dict(chains), "other": stats})
