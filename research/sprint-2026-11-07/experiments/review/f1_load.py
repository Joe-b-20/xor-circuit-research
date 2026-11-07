#!/usr/bin/env python3
"""Review check for F1/F6/F8: per arm, (a) exact root->89 / root->88 times of the FIRST chain of
every worker from 'improve' events (s_since_root), (b) all-chain arrivals at 88 from restart
'prev' blocks + the running chain's last epoch, per worker-hour and per 1e6 iterations,
(c) iteration rate per wall-clock hour bin (load proxy), (d) UTC span.
Usage: f1_load.py RUNS_DIR"""
import json, os, sys, statistics

runs = sys.argv[1]


def med(xs):
    return statistics.median(xs) if xs else float("nan")


for arm in sorted(os.listdir(runs)):
    wdir = os.path.join(runs, arm, "workers")
    if not os.path.isdir(wdir):
        continue
    first89, first88, first_best = [], [], []
    n_chains = 0
    n88 = 0
    n88_running = 0
    wh = 0.0
    its = 0
    utc0, utc1 = None, None
    rate_bins = {}  # hour bin -> list of it/s
    t88_restart = []  # upper bound: root_s - stall_s for chains whose best is 88
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        if not os.path.exists(p):
            continue
        c1_89 = c1_88 = None
        last_epoch = None
        prev_epoch = None
        stop = None
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            ev = e.get("ev")
            if ev == "start":
                utc0 = min(utc0, e["utc"]) if utc0 else e["utc"]
            if ev == "improve" and e.get("chain", "").endswith("c0001") and e.get("kind") == "gates":
                g = e["after"]["gates"]
                if g <= 89 and c1_89 is None:
                    c1_89 = e["s_since_root"]
                if g <= 88 and c1_88 is None:
                    c1_88 = e["s_since_root"]
            if ev == "epoch":
                if last_epoch is not None:
                    dt = e["t"] - last_epoch["t"]
                    if dt > 0:
                        b = int(e["t"] // 3600)
                        rate_bins.setdefault(b, []).append((e["it"] - last_epoch["it"]) / dt)
                last_epoch = e
            if ev == "restart":
                prev = e.get("prev") or {}
                n_chains += 1
                if prev.get("best", {}).get("gates", 99) <= 88:
                    n88 += 1
                    t88_restart.append(prev["root_s"] - prev["stall_s"])
            if ev == "stop":
                stop = e
                utc1 = max(utc1, e["utc"]) if utc1 else e["utc"]
        # running chain at the end
        if last_epoch is not None:
            n_chains += 1
            if (last_epoch.get("chain_best") or {}).get("gates", 99) <= 88:
                n88 += 1
                n88_running += 1
        if stop is not None:
            wh += stop["wall_s"] / 3600
            its += stop["it"]
        elif last_epoch is not None:
            wh += last_epoch["t"] / 3600
            its += last_epoch["it"]
        first89.append(c1_89)
        first88.append(c1_88)
    print(f"=== arm {arm}: {utc0} .. {utc1}")
    print(f"  first chain per worker, exact from improve events: root->89 s = {[None if x is None else round(x) for x in first89]}")
    print(f"  first chain per worker, exact from improve events: root->88 s = {[None if x is None else round(x) for x in first88]}")
    print(f"  chains {n_chains}, reached 88: {n88} ({n88_running} still running at stop), worker-hours {wh:.2f}, "
          f"iterations {its/1e6:.1f} M")
    print(f"  arrivals at 88: {n88/wh:.2f} per worker-hour, {n88/(its/1e6):.3f} per 1e6 iterations; "
          f"iterations per worker-hour {its/wh/1e6:.2f} M")
    if t88_restart:
        print(f"  finished 88 chains: last-improvement time after root (upper bound on root->88): "
              f"n={len(t88_restart)} min={min(t88_restart):.0f} med={med(t88_restart):.0f} max={max(t88_restart):.0f}")
    print("  iteration rate (it/s per worker, median over epochs) by run hour: " +
          ", ".join(f"h{b}: {med(v):.0f}" for b, v in sorted(rate_bins.items())))
