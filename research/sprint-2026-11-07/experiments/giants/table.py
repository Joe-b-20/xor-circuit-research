#!/usr/bin/env python3
"""Per-entry table for REPORT.txt: entry, chain, sample t, seed depth, outcome, canonical key, size,
factors, coincidences (other entries / catalogue rows and their chains); appendix with seed values."""
import json, collections
G = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants"
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
L = json.load(open(EST + "/landings.json"))
cat = {r["key"]: r for r in L["rows"] if r["kind"] == "product"}
E = {e["key"]: e for e in json.load(open(G + "/entries.json"))}
R = [json.loads(l) for l in open(G + "/resolve.jsonl")]
by = collections.defaultdict(list)
for r in R:
    if r["resolved"]:
        by[r["canon"]].append(r["entry"])
for i, r in enumerate(R, 1):
    e = E[r["entry"]]
    if r["resolved"]:
        k = r["canon"]
        others = [x[:15] for x in by[k] if x != r["entry"]]
        c = cat.get(k)
        catv = f"catalogue row, chains {c['chain_ids']}" if c else "new (not in catalogue)"
        sz = " x ".join(str(x) for x in r["radices"])
        print(f"{i:2d} {r['entry']:23s} {r['chain']:12s} t={r['t_sample']:6.0f} d={e['seed_depth']:2d}  {r['how'][:22]:22s} "
              f"{k} size {r['size']:,} = {sz}; {catv}; same as entries {others}")
    else:
        fa = r.get("info") or (r.get("first_attempt") or {}).get("info") or {}
        print(f"{i:2d} {r['entry']:23s} {r['chain']:12s} t={r['t_sample']:6.0f} d={e['seed_depth']:2d}  UNRESOLVED: {r['how']}"
              + (f" (fanned {fa['fans']} member states, {fa['restarts']} restarts)" if fa.get("fans") else ""))
print("\nAPPENDIX seed helper values (sorted; the 88-gate state minus the target outputs):")
for r in R:
    e = E[r["entry"]]
    print(f"{r['entry']} sample hash {e['samples'][0][3]} ({e['samples'][0][4]}):")
    print("   " + " ".join(str(v) for v in e["seed"]))
