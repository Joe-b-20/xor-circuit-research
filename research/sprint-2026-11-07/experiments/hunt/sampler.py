#!/usr/bin/env python3
"""Sample every hunt worker's chain.json every PERIOD seconds and append any state of at most
MAXG gates that has not been seen before (per worker) to samples.jsonl.  Cheap, read-only.
Usage: sampler.py RUNS_DIR OUT.jsonl [period] [maxg]
"""
import hashlib, json, os, sys, time

runs = sys.argv[1]
out = sys.argv[2]
period = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
maxg = int(sys.argv[4]) if len(sys.argv) > 4 else 89
seen = {}
while True:
    now = time.time()
    for arm in sorted(os.listdir(runs)):
        wdir = os.path.join(runs, arm, "workers")
        if not os.path.isdir(wdir):
            continue
        for w in sorted(os.listdir(wdir)):
            p = os.path.join(wdir, w, "chain.json")
            try:
                with open(p) as f:
                    d = json.load(f)
            except Exception:
                continue
            vals = d.get("chain_values") or []
            g = len(vals)
            if not vals or g > maxg:
                continue
            h = hashlib.sha256(json.dumps(sorted(vals)).encode()).hexdigest()[:16]
            key = (arm, w)
            if seen.get(key) == h:
                continue
            seen[key] = h
            rec = {"arm": arm, "worker": w, "wall": now, "t": d.get("t"), "steps": d.get("steps"),
                   "gates": g, "hash": h, "values": sorted(vals)}
            with open(out, "a") as f:
                f.write(json.dumps(rec) + "\n")
    if os.path.exists(os.path.join(os.path.dirname(out), "ALL_DONE")):
        break
    time.sleep(period)
