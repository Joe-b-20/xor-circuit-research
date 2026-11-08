"""Step 1: collect every InvMC 118@5 record, canonicalise through the engine state at cap 5,
dedupe.  Writes records118.json: {"states": {hk_str: {"hk": [...], "gates", "depth", "files": n,
"sources": {run:worker: n}, "chains": [...], "wiring_file": path}}, "counts": {...}}."""
import glob
import json
import os
import time
from collections import Counter, defaultdict
import common as C
import pes_lib

t0 = time.time()
sp = pes_lib.make_space("inv", 5)
files = []
for g in C.RECORD_GLOBS:
    files += glob.glob(g)
files = sorted(set(files))
print("files", len(files), flush=True)
states = {}
raw_sets = set()
skipped = Counter()
per_run_files = Counter()
for i, f in enumerate(files):
    try:
        d = json.load(open(f))
    except Exception as e:
        skipped["unreadable"] += 1
        continue
    if "gates" not in d or d.get("inputCount", 32) != 32:
        skipped["format"] += 1
        continue
    w = C.wiring_of_record(d)
    if not C.is_inverse(w):
        skipped["not_inverse"] += 1
        continue
    vals = [v for v, _, _ in w]
    raw_sets.add(frozenset(vals))
    helpers = [v for v in vals if v not in sp.tset]
    st = sp.state(helpers)
    g, dep = st.count(), st.depth()
    if g != 118 or dep != 5 or not st.ok():
        skipped[f"g{g}d{dep}ok{st.ok()}"] += 1
        continue
    hk = sp.hkey(st)
    key = ",".join(map(str, hk))
    run = C.run_of(f)
    per_run_files[run] += 1
    e = states.setdefault(key, {"hk": list(hk), "gates": g, "depth": dep, "files": 0,
                                "sources": Counter(), "chains": set(), "wiring_file": f,
                                "raw_gates": d.get("gateCount"), "raw_depth": d.get("depth")})
    e["files"] += 1
    e["sources"][run] += 1
    ch = (d.get("metadata") or {}).get("chain")
    if ch:
        e["chains"].add(run + "/" + str(ch))
    if i % 300 == 0:
        print(i, len(states), round(time.time() - t0, 1), flush=True)
for e in states.values():
    e["sources"] = dict(e["sources"])
    e["chains"] = sorted(e["chains"])
out = {"states": states,
       "counts": {"files": len(files), "skipped": dict(skipped), "raw_value_sets": len(raw_sets),
                  "distinct_states_cap5": len(states), "files_per_run": dict(per_run_files)}}
C.dump("records118.json", out)
print(json.dumps(out["counts"], indent=1))
print("seconds", round(time.time() - t0, 1))
