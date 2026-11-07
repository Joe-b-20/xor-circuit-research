#!/usr/bin/env python3
"""Review check for F5 coverage: which slice of the hunt the plateau catalogue covers (worker
clock t of catalogued 88 samples vs all 88 samples, per arm), and what the key-None states are.
Usage: f5d.py HUNT_DIR"""
import json, os, sys, collections

HUNT = sys.argv[1]
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p = store["states"]
P = store["plateaus"]

samples = []
for sp_path in (os.path.join(HUNT, "samples.jsonl"), os.path.join(HUNT, "samplesC", "samples.jsonl")):
    if os.path.exists(sp_path):
        for line in open(sp_path):
            r = json.loads(line)
            samples.append((r["arm"], r["worker"], r["t"], r["gates"], r["hash"], len(r["values"]), len(set(r["values"]))))

by_arm = collections.defaultdict(list)
for s in samples:
    if s[3] == 88:
        by_arm[s[0]].append(s)
for arm, lst in sorted(by_arm.items()):
    cat = [s for s in lst if h2p.get(s[4])]
    none = [s for s in lst if s[4] in h2p and h2p[s[4]] is None]
    uncat = [s for s in lst if s[4] not in h2p]
    ts_all = sorted(s[2] for s in lst)
    ts_cat = sorted(s[2] for s in cat)
    print(f"arm {arm}: 88 samples {len(lst)} (distinct hashes {len({s[4] for s in lst})}); catalogued with a key {len(cat)}, "
          f"key None {len(none)}, not in catalogue {len(uncat)}")
    if ts_cat:
        print(f"   worker-clock t of all 88 samples: {ts_all[0]:.0f}..{ts_all[-1]:.0f} s; of catalogued ones: "
              f"{ts_cat[0]:.0f}..{ts_cat[-1]:.0f} s (p90 {ts_cat[int(0.9*len(ts_cat))]:.0f} s)")
    # how many of the None samples have duplicate values or fewer than 88 values
    if none:
        c = collections.Counter((s[5], s[6]) for s in none)
        print(f"   key-None samples: (len(values), distinct values) counts: {dict(c.most_common(5))}")
# None states that are records (not samples)
rec_none = [h for h, k in h2p.items() if k is None and h.startswith("g88")]
samp_none = [h for h, k in h2p.items() if k is None and not h.startswith("g88")]
print(f"key-None entries: {len(rec_none)} record files, {len(samp_none)} sample hashes")
# first-seen wall of hunt plateaus per arm, as worker-hours covered
walls = collections.defaultdict(list)
for k, v in P.items():
    if v["first"]["arm"] != "pre":
        walls[v["first"]["arm"]].append(v["first"]["wall"])
for arm, ws in sorted(walls.items()):
    ws.sort()
    print(f"arm {arm}: plateaus first seen over wall span {(ws[-1]-ws[0])/60:.0f} min")
