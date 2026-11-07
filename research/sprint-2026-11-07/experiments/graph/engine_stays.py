#!/usr/bin/env python3
"""Exact ledger from the engine's 'plateau' events.  NOTE (found 2026-11-07): these events track
the chain's BEST-level plateau only (exit reasons are 'improve'/'restart'), so excursions to 89
are not logged as stays; what the 88 stays do carry is proposals/accepted/neutral_accepts, whose
difference accepted - neutral_accepts counts accepted uphill moves (departures from 88 to 89).
Also: 'followup' events (100-proposal windows after an improvement) give uphill acceptance rates,
and the samples give the share of time spent at 89 after a chain's first 88.
Usage: engine_stays.py HUNT_DIR OUT_DIR"""
import collections, json, os, sys
HUNT, OUT = sys.argv[1], sys.argv[2]


def q(xs, f="{:.0f}"):
    xs = sorted(xs)
    if not xs:
        return "-"
    n = len(xs)
    return ("n={} min=" + f + " q1=" + f + " med=" + f + " q3=" + f + " max=" + f).format(
        n, xs[0], xs[n // 4], xs[n // 2], xs[(3 * n) // 4], xs[-1])


stays = collections.defaultdict(list)
follow = []
below = 0
for arm in sorted(os.listdir(os.path.join(HUNT, "runs"))):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        if not os.path.exists(p):
            continue
        for line in open(p):
            try:
                e = json.loads(line)
            except Exception:
                continue
            ev = e.get("ev")
            if ev == "plateau":
                if e["level"][0] < 88:
                    below += 1
                stays[(arm, w, e["chain"])].append(e)
            elif ev == "followup":
                follow.append((arm, e))
print("engine plateau events with gates < 88:", below)
exits = collections.Counter()
stay_it, stay_s, stay_distinct, up, up_rate, up_frac, neutral_rate = [], [], [], [], [], [], []
per_chain = {}
for ck, ss in stays.items():
    ss.sort(key=lambda e: e["entry_it"])
    s88 = [e for e in ss if e["level"][0] == 88]
    if not s88:
        continue
    above_between = 0
    idx = [i for i, e in enumerate(ss) if e["level"][0] == 88]
    for a, b in zip(idx, idx[1:]):
        if any(e["level"][0] > 88 for e in ss[a + 1:b]):
            above_between += 1
    for e in s88:
        exits[e["exit"]] += 1
        stay_it.append(e["age_it"])
        stay_s.append(e["age_s"])
        stay_distinct.append(e["distinct_states"])
        u = e["accepted"] - e["neutral_accepts"]
        up.append(u)
        if e["age_s"] > 10:
            up_rate.append(u / e["age_s"])
        if e["proposals"] > 1000:
            up_frac.append(u / e["proposals"])
            neutral_rate.append(e["neutral_accepts"] / e["proposals"])
    per_chain[ck] = {"stays88": len(s88), "above_between": above_between, "uphill_accepts": sum(up[-len(s88):])}
print(f"chains with 88 stays: {len(per_chain)} (per arm {dict(collections.Counter(k[0] for k in per_chain))})")
print("exit reasons of 88 stays:", exits.most_common())
print(f"88 stays: {len(stay_it)}; stays above 88 logged between two 88 stays of one chain: {sum(v['above_between'] for v in per_chain.values())}")
print("88 stay length, iterations:", q(stay_it))
print("88 stay length, seconds:", q(stay_s))
print("88 stay distinct states (engine count):", q(stay_distinct))
print("accepted uphill moves per 88 stay (accepted - neutral_accepts):", q(up))
print("  per second (stays > 10 s):", q(up_rate, "{:.1f}"))
print("  per proposal (stays > 1000 proposals):", q(up_frac, "{:.4f}"))
print("  neutral accepts per proposal:", q(neutral_rate, "{:.3f}"))
print(f"  total accepted uphill moves off 88 across all 88 stays: {sum(up)}")
# followup windows while the chain sits at 88
f88 = [(a, e) for a, e in follow if (e.get("chain") or {}).get("gates") == 88 and e.get("proposals")]
print(f"followup windows with chain at 88: {len(f88)}; uphill accepts per 100 proposals: "
      f"{q([100 * e['uphill'] / e['proposals'] for a, e in f88], '{:.1f}')}; neutral: "
      f"{q([100 * e['neutral'] / e['proposals'] for a, e in f88], '{:.1f}')}")
# share of samples at 89 after each chain's first 88 sample
restarts = {}
for arm in sorted(os.listdir(os.path.join(HUNT, "runs"))):
    wdir = os.path.join(HUNT, "runs", arm, "workers")
    if not os.path.isdir(wdir):
        continue
    for w in sorted(os.listdir(wdir)):
        p = os.path.join(wdir, w, "events.jsonl")
        ts = []
        if os.path.exists(p):
            for line in open(p):
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("ev") == "restart":
                    ts.append(e["t"])
        restarts[(arm, w)] = sorted(ts)


def cidx(arm, w, t):
    return sum(1 for x in restarts.get((arm, w), []) if x <= t)


samples = []
for path, arms in ((os.path.join(HUNT, "samples.jsonl"), {"A", "B"}), (os.path.join(HUNT, "samplesC", "samples.jsonl"), {"C"})):
    for line in open(path):
        r = json.loads(line)
        if r["arm"] in arms:
            samples.append(r)
samples.sort(key=lambda r: (r["arm"], r["worker"], r["wall"]))
by_chain = collections.defaultdict(list)
for r in samples:
    by_chain[(r["arm"], r["worker"], cidx(r["arm"], r["worker"], r["t"] or 0))].append(r)
share = collections.defaultdict(lambda: [0, 0])
for ck, rs in by_chain.items():
    seen88 = False
    for r in rs:
        if r["gates"] == 88:
            seen88 = True
        if seen88:
            share[ck[0]][r["gates"] == 89] += 1
for arm in "ABC":
    n88, n89 = share[arm]
    print(f"arm {arm}: samples after first 88: at 88 {n88}, at 89 {n89} -> share of sampled instants at 89: {100 * n89 / (n88 + n89):.0f} %")
json.dump({"stay_it": stay_it, "stay_s": stay_s, "uphill": up,
           "per_chain": {"|".join(map(str, k)): v for k, v in per_chain.items()}}, open(os.path.join(OUT, "engine_stays.json"), "w"))
