#!/usr/bin/env python3
"""Review check for F1: epoch-based first-88 time of the first chain per worker (what
descents.py sees), kinds of improve events, and the fraction of all chains reaching <= 89 within
180 s (UNDERSTANDING's 'under 3 minutes'). Usage: f1b.py RUNS_DIR"""
import json, os, sys, collections

runs = sys.argv[1]
for arm in sorted(os.listdir(runs)):
    wdir = os.path.join(runs, arm, "workers")
    if not os.path.isdir(wdir):
        continue
    kinds = collections.Counter()
    first88_epoch = []
    t89 = []
    t88 = []
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        t0 = {1: 0.0}
        seen89, seen88 = {}, {}
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            ev = e.get("ev")
            if ev == "improve":
                kinds[(e.get("kind"), e.get("chain", "").endswith("c0001"))] += 1
            elif ev == "restart":
                t0[e["engine_chain"]] = e["t"]
            elif ev == "epoch":
                c = e["engine_chain"]
                g = (e.get("chain_best") or {}).get("gates", 99)
                if g <= 89 and c not in seen89:
                    seen89[c] = e["t"] - t0.get(c, 0.0)
                if g <= 88 and c not in seen88:
                    seen88[c] = e["t"] - t0.get(c, 0.0)
        first88_epoch.append(round(seen88.get(1, -1)))
        t89 += list(seen89.values())
        t88 += list(seen88.values())
    t89.sort()
    t88.sort()
    print(f"=== {arm}: improve events by (kind, first chain): {dict(kinds)}")
    print(f"  first chain per worker, epoch-based root->88: {first88_epoch}")
    n = len(t89)
    print(f"  all chains with an epoch at <= 89: {n}; within 180 s: {sum(1 for x in t89 if x <= 180)} "
          f"({100*sum(1 for x in t89 if x <= 180)/n:.0f} %); within 300 s: {sum(1 for x in t89 if x <= 300)}; "
          f"p90 {t89[int(0.9*n)]:.0f} s; max {t89[-1]:.0f} s")
    n = len(t88)
    print(f"  chains with an epoch at <= 88: {n}; within 300 s: {sum(1 for x in t88 if x <= 300)}; within 600 s: "
          f"{sum(1 for x in t88 if x <= 600)}; median {t88[n//2]:.0f}; p90 {t88[int(0.9*n)]:.0f}; max {t88[-1]:.0f} s")
