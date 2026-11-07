#!/usr/bin/env python3
"""Review check for F5 'zero repeats': per catalogued plateau, the set of distinct chains
(arm, worker, chain index) whose sampled 88 states landed on it. Usage: f5e.py HUNT_DIR"""
import json, os, sys, collections

HUNT = sys.argv[1]
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p, P = store["states"], store["plateaus"]
bounds = {}
for arm in os.listdir(os.path.join(HUNT, "runs")):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in os.listdir(wdir):
        ts = []
        p = os.path.join(wdir, w, "events.jsonl")
        if os.path.exists(p):
            for line in open(p):
                if '"ev":"restart"' in line:
                    try:
                        ts.append(json.loads(line)["t"])
                    except Exception:
                        pass
        bounds[(arm, w)] = sorted(ts)
visitors = collections.defaultdict(set)
first88 = {}
for sp_path in (os.path.join(HUNT, "samples.jsonl"), os.path.join(HUNT, "samplesC", "samples.jsonl")):
    if os.path.exists(sp_path):
        for line in open(sp_path):
            r = json.loads(line)
            if r["gates"] != 88:
                continue
            k = h2p.get(r["hash"])
            if not k:
                continue
            ci = sum(1 for x in bounds.get((r["arm"], r["worker"]), []) if x <= r["t"])
            ch = (r["arm"], r["worker"], ci)
            visitors[k].add(ch)
            if ch not in first88 or first88[ch][0] > r["t"]:
                first88[ch] = (r["t"], k)
multi = {k: v for k, v in visitors.items() if len(v) > 1}
print(f"plateaus visited by sampled states: {len(visitors)}; by >= 2 distinct chains: {len(multi)}; "
      f"by >= 2 arms: {sum(1 for v in multi.values() if len({c[0] for c in v}) > 1)}")
for k, v in multi.items():
    print(f"   {k} size {P[k]['size']} kind {P[k]['kind']} chains {sorted(v)}")
fk = collections.Counter(k for _, k in first88.values())
print(f"chains with a catalogued first-88 state: {len(first88)}; distinct first-88 plateaus: {len(fk)}; "
      f"first-88 plateaus shared by two chains: {[(k, n) for k, n in fk.items() if n > 1]}")
