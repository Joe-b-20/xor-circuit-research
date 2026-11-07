#!/usr/bin/env python3
"""Step 1: list the 18 non-product keys (giant-* and closure) with seeds, chains, samples."""
import json, os, collections
HUNT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/hunt"
EST = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/estimate"
OUT = "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants"
store = json.load(open(os.path.join(HUNT, "plateaus.json")))
P, H = store["plateaus"], store["states"]
L = json.load(open(os.path.join(EST, "landings.json")))
rows = {r["key"]: r for r in L["rows"]}
keys = [k for k, v in P.items() if v["kind"] != "product" and v["first"]["arm"] != "pre"]
print("non-product sprint keys in plateaus.json:", len(keys), "; in landing rows:", sum(k in rows for k in keys))
# samples by hash
samp = collections.defaultdict(list)
for f in ("samples.jsonl", "samplesC/samples.jsonl"):
    for line in open(os.path.join(HUNT, f)):
        r = json.loads(line)
        if r["gates"] == 88 and H.get(r["hash"]) in keys:
            samp[H[r["hash"]]].append((r["arm"], r["worker"], r["t"], r["hash"], f))
out = []
for k in keys:
    v = P[k]; m = v["plateau"].get("meta", {})
    seed = m.get("seed")
    nst = len(v["plateau"].get("states") or [])
    rec = {"key": k, "kind": v["kind"], "stored_size": v["size"], "stored_states": nst, "verified": m.get("verified"),
           "seed": seed, "seed_depth": m.get("seed_depth"), "first": v["first"], "members_seen": v["members_seen"],
           "arms": v["arms"], "chains": rows.get(k, {}).get("chain_ids"), "samples": samp[k],
           "compress_seconds": m.get("compress_seconds"), "fans": m.get("fans")}
    out.append(rec)
    print(k, v["kind"], "size", v["size"], "states", nst, m.get("verified"), "depth", m.get("seed_depth"),
          "sec", m.get("compress_seconds"), "chains", rec["chains"], "samples", [(a, w, round(t or 0), h) for a, w, t, h, _ in samp[k]],
          "seedlen", len(seed or []))
# chain sequences of the giant chains
for c, seq in L["chains"].items():
    if any(x in keys for x in seq):
        print(c, " ".join(("G:" + x[6:14]) if x.startswith("giant") else ("C:" + x[1:9]) if x in keys else "." for x in seq))
json.dump(out, open(os.path.join(OUT, "entries.json"), "w"), indent=1)
