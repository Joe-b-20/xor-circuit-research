#!/usr/bin/env python3
"""Descent statistics of the hunt arms from the workers' events.jsonl.

A chain = one root followed until a restart.  Finished chains come from 'restart' events (the
``prev`` block: best, root_s = chain age, stall_s = time since its last improvement,
improvements).  The running chain comes from the last 'epoch' event.  Time from the root to a
gate level is read from the epochs (60 s resolution): first epoch whose chain_best.gates <= G,
minus the chain's start time (only 'improve' events exist for worker-best improvements, so
later chains are invisible there).  Usage: descents.py RUNS_DIR [levels]
"""
import json, os, sys

runs = sys.argv[1]
levels = [int(x) for x in (sys.argv[2].split(",") if len(sys.argv) > 2 else ["90", "89", "88", "87"])]


def chains_of(path):
    chains = {}      # engine_chain -> dict
    order = []
    last_epoch = None
    for line in open(path):
        try:
            e = json.loads(line)
        except Exception:
            continue
        ev = e.get("ev")
        if ev == "epoch":
            c = e.get("engine_chain")
            if c not in chains:
                chains[c] = {"chain": c, "root": e.get("root"), "t0": None, "levels": {}, "best": None,
                             "end": None, "finished": False}
                order.append(c)
            ch = chains[c]
            if ch["t0"] is None:
                # chain start = epoch time minus its age is not in the epoch; use the restart
                # event's time when we see it; else the first epoch time
                ch["t0_epoch"] = e["t"]
            cb = e.get("chain_best") or {}
            g = cb.get("gates")
            if g is not None:
                for L in levels:
                    if g <= L and L not in ch["levels"]:
                        ch["levels"][L] = e["t"]
                if ch["best"] is None or (g, cb.get("depth", 99)) < tuple(ch["best"]):
                    ch["best"] = [g, cb.get("depth")]
            last_epoch = e
        elif ev == "restart":
            prev = e.get("prev") or {}
            c = prev.get("engine_chain")
            if c is None:
                continue
            if c not in chains:
                chains[c] = {"chain": c, "root": prev.get("root"), "t0": None, "levels": {}, "best": None,
                             "end": None, "finished": False}
                order.append(c)
            ch = chains[c]
            ch["finished"] = True
            ch["end"] = e["t"]
            ch["t0"] = e["t"] - prev.get("age_s", prev.get("root_s", 0))
            ch["prev_best"] = prev.get("best")
            ch["root_s"] = prev.get("root_s")
            ch["stall_s"] = prev.get("stall_s")
            ch["improvements"] = prev.get("improvements")
            ch["reason"] = e.get("reason")
            if ch["best"] is None and prev.get("best"):
                ch["best"] = [prev["best"]["gates"], prev["best"]["depth"]]
            # next chain starts now
            nc = e.get("engine_chain")
            if nc is not None and nc not in chains:
                chains[nc] = {"chain": nc, "root": (e.get("root") or {}).get("id"), "t0": e["t"], "levels": {},
                              "best": None, "end": None, "finished": False}
                order.append(nc)
            elif nc is not None:
                chains[nc]["t0"] = e["t"]
    out = []
    for c in order:
        ch = chains[c]
        if ch["t0"] is None:
            ch["t0"] = 0.0 if c == 1 else ch.get("t0_epoch", 0.0)
        # convert level times to time since chain start
        ch["levels"] = {L: max(0.0, t - ch["t0"]) for L, t in ch["levels"].items()}
        if ch["finished"] and ch.get("prev_best"):
            pb = ch["prev_best"]
            for L in levels:
                if pb["gates"] <= L and L not in ch["levels"]:
                    # reached between epochs: bound by the last improvement time
                    ch["levels"][L] = max(0.0, (ch["root_s"] or 0) - (ch["stall_s"] or 0))
        out.append(ch)
    return out, last_epoch


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
        cs, last = chains_of(p)
        for c in cs:
            c["worker"] = w
        allc += cs
        if last is not None:
            hours += last["t"] / 3600
    done = [c for c in allc if c["finished"]]
    print(f"=== {arm}: {len(allc)} chains ({len(done)} finished), {hours:.2f} worker-hours")
    for L in levels:
        reached = [c for c in allc if L in c["levels"]]
        tt = [c["levels"][L] for c in reached]
        rate = len(reached) / hours if hours else 0
        print(f"  <= {L}: {len(reached)} chains ({rate:.2f}/worker-h); time from root: {q(tt)} s")
    at88 = [c for c in done if c["best"] and c["best"][0] <= 88]
    if at88:
        stay = [c["stall_s"] for c in at88 if c.get("stall_s") is not None]
        ages = [c["root_s"] for c in at88 if c.get("root_s") is not None]
        print(f"  finished chains at <= 88: {len(at88)}; stall before restart: {q(stay)} s; chain age: {q(ages)} s")
    not88 = [c for c in done if c["best"] and c["best"][0] > 88]
    if not88:
        ages = [c["root_s"] for c in not88 if c.get("root_s") is not None]
        bests = {}
        for c in not88:
            bests[c["best"][0]] = bests.get(c["best"][0], 0) + 1
        print(f"  finished chains above 88: {len(not88)}; chain age: {q(ages)} s; bests {dict(sorted(bests.items()))}")
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
        reasons[c.get("reason")] = reasons.get(c.get("reason"), 0) + 1
    print(f"  restart reasons: {reasons}")
