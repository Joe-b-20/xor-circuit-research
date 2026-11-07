#!/usr/bin/env python3
"""Per chain (one root until restart): which 88 plateaus the chain's sampled states belong to,
in time order.  Uses plateaus.json (state hash -> plateau key), samples.jsonl (worker, t, hash)
and the workers' events.jsonl (restart times = chain boundaries).  Prints per arm: chains that
reached 88, plateaus visited per chain, and the number of distinct plateaus first reached by a
chain's FIRST 88 state (independent discoveries) against all plateaus seen.
Usage: chains_plateaus.py HUNT_DIR
"""
import json, os, sys

HUNT = sys.argv[1] if len(sys.argv) > 1 else "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p = store["states"]
P = store["plateaus"]

# chain boundaries from restart events: list of restart times per (arm, worker)
bounds = {}
for arm in sorted(os.listdir(os.path.join(HUNT, "runs"))):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in sorted(os.listdir(wdir)):
        ts = []
        p = os.path.join(wdir, w, "events.jsonl")
        if not os.path.exists(p):
            continue
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            if e.get("ev") == "restart":
                ts.append(e["t"])
        bounds[(arm, w)] = sorted(ts)


def chain_index(arm, w, t):
    ts = bounds.get((arm, w), [])
    i = 0
    while i < len(ts) and ts[i] <= t:
        i += 1
    return i


visits = {}  # (arm, worker, chain) -> list of (t, key)
for line in open(os.path.join(HUNT, "samples.jsonl")):
    r = json.loads(line)
    if r["gates"] != 88:
        continue
    key = h2p.get(r["hash"])
    if not key:
        continue
    c = chain_index(r["arm"], r["worker"], r["t"] or 0)
    visits.setdefault((r["arm"], r["worker"], c), []).append((r["t"], key))

for arm in sorted({k[0] for k in visits}):
    chains = sorted(k for k in visits if k[0] == arm)
    first_keys = []
    all_keys = set()
    print(f"=== {arm}: {len(chains)} chains with sampled 88 states")
    for k in chains:
        seq = sorted(visits[k])
        keys = []
        for t, key in seq:
            if not keys or keys[-1] != key:
                keys.append(key)
        distinct = len(set(keys))
        all_keys |= set(keys)
        first_keys.append(keys[0])
        sizes = [P[x]["size"] for x in dict.fromkeys(keys)]
        print(f"  {k[1]} chain {k[2]}: {len(seq)} samples over {seq[-1][0] - seq[0][0]:.0f} s, "
              f"{distinct} distinct plateaus, {len(keys) - 1} transitions; sizes {sizes[:8]}")
    print(f"  first-88 plateaus: {len(set(first_keys))} distinct of {len(first_keys)} chains; "
          f"all plateaus seen by this arm: {len(all_keys)}")
pre = [k for k, v in P.items() if v.get("also_pre") or v["first"]["arm"] == "pre"]
hits = sum(v["members_seen"] for k, v in P.items() if v.get("also_pre") or v["first"]["arm"] == "pre")
print(f"pre-sprint plateaus in catalogue: {len(pre)}; hunt states that landed on one: {hits}")
