#!/usr/bin/env python3
"""Landing table for catalogued 88 plateaus (hunt arms A, B, C).
Sampling unit = chain (one root until restart; boundaries from workers' restart events, same
logic as hunt/chains_plateaus.py).  For each catalogued plateau: exact size (or 'unknown' for
closure-truncated giants), number of chains that visited it (incidence), number of chains whose
FIRST catalogued 88 state was on it, arms, samples.  Writes landings.json for the estimators.
"""
import json, os, collections

HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
OUT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
h2p, P = store["states"], store["plateaus"]

bounds = {}
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
        bounds[(arm, w)] = sorted(ts)


def chain_index(arm, w, t):
    ts = bounds.get((arm, w), [])
    i = 0
    while i < len(ts) and ts[i] <= t:
        i += 1
    return i


visits = collections.defaultdict(list)   # chain -> [(t, key)]
n88 = collections.Counter()
for sp in ("samples.jsonl", "samplesC/samples.jsonl"):
    for line in open(os.path.join(HUNT, sp)):
        r = json.loads(line)
        if r["gates"] != 88:
            continue
        n88[r["arm"]] += 1
        key = h2p.get(r["hash"])
        if not key:
            continue
        visits[(r["arm"], r["worker"], chain_index(r["arm"], r["worker"], r["t"] or 0))].append((r["t"], key))

def kind(k):
    v = P[k]
    if v["kind"] == "product":
        return "product"
    return "giant" if k.startswith("giant-") else "closure"

inc = collections.defaultdict(set)      # key -> chains
first = collections.Counter()           # key -> # chains whose first 88 is here
nsamp = collections.Counter()
for c, seq in visits.items():
    seq.sort()
    first[seq[0][1]] += 1
    for t, k in seq:
        inc[k].add(c)
        nsamp[k] += 1

rows = []
for k in inc:
    rows.append({"key": k, "size": P[k]["size"] if kind(k) == "product" else None, "kind": kind(k),
                 "chains": len(inc[k]), "first_landings": first[k],
                 "workers": len({(a, w) for a, w, _ in inc[k]}),
                 "arms": "".join(sorted({a for a, _, _ in inc[k]})), "samples": nsamp[k],
                 "chain_ids": sorted(f"{a}/{w}/{i}" for a, w, i in inc[k]),
                 "radices": P[k]["radices"]})
rows.sort(key=lambda r: (-r["chains"], -(r["size"] or 0)))
json.dump({"rows": rows, "T_chains": len(visits),
           "chains": {f"{a}/{w}/{i}": [k for _, k in sorted(s)] for (a, w, i), s in visits.items()}},
          open(os.path.join(OUT, "landings.json"), "w"), indent=0)

print(f"sampled 88 states per arm (measured): {dict(n88)}")
print(f"catalogued 88 samples: {sum(len(s) for s in visits.values())}; chains with catalogued 88: {len(visits)} "
      f"{dict(collections.Counter(a for a, _, _ in visits))}")
print(f"catalogued plateaus touched by samples: {len(rows)} of {sum(1 for v in P.values() if v['first']['arm'] != 'pre')} sprint plateaus")
print(f"kinds: {dict(collections.Counter(r['kind'] for r in rows))}")
print("incidence frequency counts Q_j (plateaus seen by exactly j chains):",
      dict(sorted(collections.Counter(r['chains'] for r in rows).items())))
print("  same, exact-size (product) plateaus only:",
      dict(sorted(collections.Counter(r['chains'] for r in rows if r['kind'] == 'product').items())))
print("worker-level counts (plateaus seen by exactly j distinct workers):",
      dict(sorted(collections.Counter(r['workers'] for r in rows).items())))
print("first-landing counts:", dict(sorted(collections.Counter(r['first_landings'] for r in rows if r['first_landings']).items())))
print("\nplateaus seen by >1 chain:")
for r in rows:
    if r["chains"] > 1:
        print(f"  {r['key']:24s} size={r['size']} kind={r['kind']} chains={r['chains']} workers={r['workers']} arms={r['arms']} "
              f"first={r['first_landings']} samples={r['samples']} {r['chain_ids']} radices={r['radices']}")
# chain stats
lens = sorted(len(set(k for _, k in s)) for s in visits.values())
print(f"\ndistinct plateaus per chain: min {lens[0]} median {lens[len(lens)//2]} max {lens[-1]}; total incidences {sum(lens)}")
