#!/usr/bin/env python3
"""Descent statistics of the hunt arms from the workers' events.jsonl.

A chain = one root followed until a restart.  For each chain: start t, root constructor, time
from the root to each gate level (first 'improve' event with after.gates <= G), the best gates
reached and the time spent at the chain's best before the restart.  Per arm: chains started,
chains that reached <= 90 / 89 / 88, time-to-88 quantiles, arrivals at 88 per worker-hour.
Usage: descents.py RUNS_DIR [levels]
"""
import glob, json, os, statistics, sys

runs = sys.argv[1]
levels = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["90", "89", "88", "87"])]


def chains_of(path):
    chains = []
    cur = None
    for line in open(path):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ev = e.get("ev")
        if ev == "improve":
            cid = e.get("chain")
            if cur is None or cur["chain"] != cid:
                if cur is not None:
                    chains.append(cur)
                cur = {"chain": cid, "root": e.get("root"), "t0": e["t"] - (e.get("s_since_root") or 0),
                       "levels": {}, "best": None, "t_best": None, "end": None}
            g = e["after"]["gates"]
            d = e["after"]["depth"]
            for L in levels:
                if g <= L and L not in cur["levels"]:
                    cur["levels"][L] = e["t"] - cur["t0"]
            if cur["best"] is None or (g, d) < tuple(cur["best"]):
                cur["best"] = [g, d]
                cur["t_best"] = e["t"]
        elif ev == "restart" and cur is not None:
            cur["end"] = e["t"]
            cur["restart_reason"] = e.get("reason")
            chains.append(cur)
            cur = None
    if cur is not None:
        chains.append(cur)
    return chains


def q(xs):
    if not xs:
        return "-"
    xs = sorted(xs)
    n = len(xs)
    return f"n={n} min={xs[0]:.0f} med={xs[n // 2]:.0f} max={xs[-1]:.0f}"


for arm in sorted(os.listdir(runs)):
    wdir = os.path.join(runs, arm, "workers")
    if not os.path.isdir(wdir):
        continue
    allc = []
    hours = 0.0
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        if not os.path.exists(p):
            continue
        cs = chains_of(p)
        for c in cs:
            c["worker"] = w
        allc += cs
        try:
            st = json.load(open(os.path.join(wdir, w, "chain.json")))
            hours += (st.get("t") or 0) / 3600
        except Exception:
            pass
    done = [c for c in allc if c["end"] is not None]
    print(f"=== {arm}: {len(allc)} chains ({len(done)} finished), {hours:.2f} worker-hours")
    for L in levels:
        reached = [c for c in allc if L in c["levels"]]
        tt = [c["levels"][L] for c in reached]
        rate = len(reached) / hours if hours else 0
        print(f"  <= {L}: {len(reached)} chains ({rate:.2f}/worker-h); time from root: {q(tt)} s")
    at88 = [c for c in done if c["best"] and c["best"][0] <= 88]
    if at88:
        stay = [c["end"] - c["t_best"] for c in at88]
        print(f"  finished chains at <= 88: {len(at88)}; stay at best before restart: {q(stay)} s")
    depths = {}
    for c in allc:
        if c["best"] and c["best"][0] == 88:
            depths[c["best"][1]] = depths.get(c["best"][1], 0) + 1
    if depths:
        print(f"  depth of 88 chain bests: {dict(sorted(depths.items()))}")
    roots = {}
    for c in allc:
        r = (c["root"] or "?").split("#")[0]
        roots.setdefault(r, [0, 0])
        roots[r][0] += 1
        roots[r][1] += 1 if (88 in c["levels"]) else 0
    print(f"  roots (chains, reached 88): {roots}")
    reasons = {}
    for c in done:
        reasons[c.get("restart_reason")] = reasons.get(c.get("restart_reason"), 0) + 1
    print(f"  restart reasons: {reasons}")
