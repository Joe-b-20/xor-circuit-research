#!/usr/bin/env python3
"""Plateau-level view of a transition log: the cheap v3 plateau signature (hunt/sig.py: core
and mobile helper sets from the remove1 fan, canonical modulo byte rotation; constant on an
exact product plateau, an upper bound on exact plateaus) of every 88 entry's values.

Usage: plateau_sig.py TRANSLOG.jsonl [SAMPLES.jsonl ARM WORKER]
Prints: distinct plateaus, consecutive runs (how many entries stay on one plateau), hops between
distinct plateaus and their excursion lengths, revisits (a plateau re-entered after others), and
what the 30 s sampler saw of the same hour.  ~35 ms per state.
"""
import json
import statistics as st
import sys
import time
from collections import Counter

sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-05-exit/pes")
import pes_lib  # noqa: E402

sp = pes_lib.make_space("mc", None)
PERIOD = 30.0


def canon(core, mobile):
    best = None
    for s in sp.shifts:
        c = tuple(sorted(sp.rot(tuple(sorted(core)), s))) if s else tuple(sorted(core))
        m = tuple(sorted(sp.rot(tuple(sorted(mobile)), s))) if s else tuple(sorted(mobile))
        k = (c, m)
        if best is None or k < best:
            best = k
    return "%016x" % pes_lib.h64(best)


def sig_of(values):
    helpers = [v for v in values if v not in sp.tset]
    state = sp.state(helpers)
    if state.count() != 88:
        return None, state.count()
    S = frozenset(sp.hkey(state))
    g, d, neutral, downs, binds = pes_lib.fan(sp, S)
    mobile = set()
    for R, A, k, dep in neutral:
        mobile |= R | A
    core = S - mobile
    return canon(core, mobile), (d, len(neutral), len(downs))


def q(xs, p):
    xs = sorted(xs)
    return xs[max(0, min(len(xs) - 1, int(round(p * (len(xs) - 1)))))] if xs else None


def main():
    path = sys.argv[1]
    rows = [json.loads(l) for l in open(path)]
    body = [r for r in rows if r["k"] in ("step", "chain")]
    body.sort(key=lambda r: r["it"])
    close = next((r for r in rows if r["k"] == "close"), None)
    t_end = close["t"] if close else body[-1]["t"]
    # segments at 88 with their exit time
    segs = []
    for i, r in enumerate(body):
        nxt = body[i + 1] if i + 1 < len(body) else None
        if r["g"] == 88 and r.get("v"):
            segs.append({"it0": r["it"], "t0": r["t"], "t1": nxt["t"] if nxt else t_end,
                         "it1": nxt["it"] if nxt else None, "v": r["v"], "c": r["c"], "id": r["id"]})
    t0 = time.perf_counter()
    cache = {}
    downs = 0
    for s in segs:
        key = s["id"]
        if key not in cache:
            cache[key] = sig_of(s["v"])
        s["sig"], info = cache[key]
        if s["sig"] is not None and info[2]:
            downs += 1
    secs = time.perf_counter() - t0
    sigs = [s["sig"] for s in segs]
    span = t_end - body[0]["t"]
    print(f"entries {len(segs)}  signatures computed in {secs:.1f} s ({secs / max(1, len(segs)) * 1e3:.1f} ms each)")
    print(f"states with a remove1 down-exit (an 87 neighbour): {downs}")
    distinct = Counter(sigs)
    print(f"distinct plateau signatures: {len(distinct)}  (span {span:.0f} s -> {len(distinct) / span * 3600:.0f} per hour)")
    # runs of consecutive entries on one plateau
    runs = []
    hops = []          # (excursion seconds, excursion steps, from sig, to sig)
    cur, start = None, None
    for i, s in enumerate(segs):
        if s["sig"] != cur:
            if cur is not None:
                runs.append((cur, start, i - 1))
                prev = segs[i - 1]
                hops.append((s["t0"] - prev["t1"], s["it0"] - prev["it1"], cur, s["sig"]))
            cur, start = s["sig"], i
    runs.append((cur, start, len(segs) - 1))
    run_len = [b - a + 1 for _, a, b in runs]
    run_s = [segs[b]["t1"] - segs[a]["t0"] for _, a, b in runs]
    print(f"plateau visits (runs of consecutive entries on one signature): {len(runs)} "
          f"({len(runs) / span * 3600:.0f} per hour); entries per visit median {q(run_len, .5)} "
          f"(q1 {q(run_len, .25)}, q3 {q(run_len, .75)}, max {max(run_len)}); visit length s median "
          f"{q(run_s, .5):.1f} (q1 {q(run_s, .25):.1f}, q3 {q(run_s, .75):.1f}, max {max(run_s):.0f})")
    if hops:
        hs = [h[0] for h in hops]
        print(f"hops between distinct plateaus: {len(hops)}; excursion s median {q(hs, .5):.2f} "
              f"(q1 {q(hs, .25):.2f}, q3 {q(hs, .75):.2f}, p90 {q(hs, .9):.2f}, max {max(hs):.1f}); "
              f"shorter than 30 s: {sum(1 for h in hs if h < PERIOD) / len(hs):.3f}; "
              f"shorter than 2 s: {sum(1 for h in hs if h < 2) / len(hs):.3f}")
        # ticks every 30 s: a hop is seen by the sampler when a tick falls in its excursion
        ticks = []
        t = body[0]["t"] + PERIOD
        while t < t_end:
            ticks.append(t)
            t += PERIOD
        seen = 0
        for (dt, _, _, _), (prev, nxt) in zip(hops, [(segs[b], segs[b + 1]) for _, a, b in runs[:-1]]):
            if any(prev["t1"] <= tk < nxt["t0"] for tk in ticks):
                seen += 1
        print(f"hops whose 89 excursion contains a 30 s tick: {seen} of {len(hops)} "
              f"({1 - seen / len(hops):.3f} missed)")
        # which plateau visits would a 30 s sampler catch at all
        caught = sum(1 for _, a, b in runs if any(segs[a]["t0"] <= tk < segs[b]["t1"] for tk in ticks))
        print(f"plateau visits containing a 30 s tick: {caught} of {len(runs)}")
    # revisits
    first, revisit, back_and_forth = {}, 0, 0
    order = [r[0] for r in runs]
    for i, sg in enumerate(order):
        if sg in first:
            revisit += 1
            if i >= 2 and order[i - 2] == sg:
                back_and_forth += 1
        else:
            first[sg] = i
    print(f"revisits (a plateau visited again after at least one other): {revisit}, of which "
          f"A-B-A back-and-forth: {back_and_forth}; plateaus visited more than once: "
          f"{sum(1 for n in Counter(order).values() if n > 1)}")
    # sampler pairing
    if len(sys.argv) > 4:
        recs = [json.loads(l) for l in open(sys.argv[2])]
        mine = [r for r in recs if r["arm"] == sys.argv[3] and r["worker"] == sys.argv[4] and r["gates"] == 88]
        ssigs = []
        for r in mine:
            sg, _ = sig_of(r["values"])
            ssigs.append(sg)
        print(f"sampler: {len(mine)} distinct 88 samples -> {len(set(ssigs))} distinct signatures, "
              f"{len(set(ssigs) & set(distinct))} of them among the log's {len(distinct)}; "
              f"sampler-visible hops (consecutive distinct sample signatures): "
              f"{sum(1 for a, b in zip(ssigs, ssigs[1:]) if a != b)}")
    json.dump({"segments": [{k: v for k, v in s.items() if k != "v"} for s in segs],
               "runs": runs, "hops": hops},
              open(path.replace(".jsonl", ".plateaus.json"), "w"))


if __name__ == "__main__":
    main()
