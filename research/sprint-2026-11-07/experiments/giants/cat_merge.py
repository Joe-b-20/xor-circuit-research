#!/usr/bin/env python3
"""Merge the catalogue shards.  Inputs: hunt/plateaus.json (old state map, products), giants/
resolve.jsonl (giant entries resolved earlier), catalogue/shard_*.jsonl, pl files.  Outputs in
giants/catalogue/:
  plateaus_all.json   {"states": hash -> plateau key | null, "plateaus": key -> {size, radices,
                       factor_value_counts, verified, kind, source}}
  landings_all.json   same format as estimate/landings.json (chains from restart events of
                       hunt/runs and hunt/runsD, as estimate/landings.py), all sampled arms
  landing_table_all.txt  (written by reestimate.py)
then runs reestimate.py on it (Chao2, D2, chain-pair N_eff, alpha fit, HT) -> reestimate_all.out."""
import collections, glob, json, os, subprocess, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants")
import cat_lib as C  # noqa: E402

store = json.load(open(C.HUNT + "/plateaus.json"))
P, H = store["plateaus"], store["states"]
plat = {}


def add_plateau(k, d, source):
    if k in plat:
        return
    fac = d.get("factors", [])
    plat[k] = {"size": d.get("size"), "radices": [len(f["choices"]) for f in fac],
               "factor_value_counts": [len(f["values"]) for f in fac], "core_size": len(d.get("core", [])),
               "verified": (d.get("meta") or {}).get("verified"), "kind": d.get("kind"), "source": source}


for k, v in P.items():
    if v["kind"] == "product":
        add_plateau(k, v["plateau"], "hunt/plateaus.json" + (" (pre-sprint)" if v["first"]["arm"] == "pre" else ""))
for f in glob.glob(C.G + "/pl_*.json"):
    add_plateau(os.path.basename(f)[3:-5], json.load(open(f)), "giants/" + os.path.basename(f))
for f in glob.glob(C.PLDIR + "/*.json"):
    add_plateau(os.path.basename(f)[:-5], json.load(open(f)), "catalogue/pl")

states = {}
for h, k in H.items():
    states[h] = k if (k and P.get(k, {}).get("kind") == "product") else None
# giant entries resolved earlier (their sample hash -> canonical key)
E = {e["key"]: e for e in json.load(open(C.G + "/entries.json"))}
for line in open(C.G + "/resolve.jsonl"):
    r = json.loads(line)
    if r["resolved"]:
        states[E[r["entry"]]["samples"][0][3]] = r["canon"]
nres = collections.Counter()
for h, r in C.done_ids().items():
    nres[(r["kind"], r["resolved"], r["how"].split(";")[0])] += 1
    if r["resolved"]:
        states[h] = r["key"]
    else:
        states.setdefault(h, None)
        if r["kind"] == "giant" or states[h] is None:
            states[h] = None
json.dump({"states": states, "plateaus": plat}, open(C.CAT + "/plateaus_all.json", "w"))

# chains, as estimate/landings.py, over hunt/runs and hunt/runsD
bounds = {}
for root in (C.HUNT + "/runs", C.HUNT + "/runsD"):
    for p in glob.glob(root + "/*/workers/*/events.jsonl"):
        parts = p.split(os.sep)
        arm, w = parts[-4], parts[-2]
        ts = []
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


visits = collections.defaultdict(list)
n88 = collections.Counter()
unmapped = collections.Counter()
for f in C.SAMPLE_FILES:
    for line in open(f):
        r = json.loads(line)
        if r["gates"] != 88:
            continue
        n88[r["arm"]] += 1
        h = r["hash"]
        k = states.get(h)
        if k is None:
            unmapped[r["arm"]] += 1
            k = "unresolved-" + h          # kept as its own (non-product) key, excluded by reestimate
        if (r["arm"], r["worker"]) not in bounds:
            print("WARNING no events for", r["arm"], r["worker"])
        visits[(r["arm"], r["worker"], chain_index(r["arm"], r["worker"], r["t"] or 0))].append((r["t"] or 0, k))
inc = collections.defaultdict(set)
first = collections.Counter()
nsamp = collections.Counter()
for c, seq in visits.items():
    seq.sort()
    first[seq[0][1]] += 1
    for t, k in seq:
        inc[k].add(c)
        nsamp[k] += 1
rows = []
for k in inc:
    pr = k in plat
    rows.append({"key": k, "size": plat[k]["size"] if pr else None, "kind": "product" if pr else "giant",
                 "chains": len(inc[k]), "first_landings": first[k], "workers": len({(a, w) for a, w, _ in inc[k]}),
                 "arms": "".join(sorted({a for a, _, _ in inc[k]})), "samples": nsamp[k],
                 "chain_ids": sorted(f"{a}/{w}/{i}" for a, w, i in inc[k]),
                 "radices": plat[k]["radices"] if pr else []})
rows.sort(key=lambda r: (-r["chains"], -(r["size"] or 0)))
json.dump({"rows": rows, "T_chains": len(visits),
           "chains": {f"{a}/{w}/{i}": [k for _, k in sorted(s)] for (a, w, i), s in visits.items()}},
          open(C.CAT + "/landings_all.json", "w"), indent=0)
print("shard outcomes:", dict(nres))
print(f"88 samples per arm {dict(n88)}; unresolved samples per arm {dict(unmapped)}")
print(f"chains with 88 samples {len(visits)}; plateau rows {len(rows)} "
      f"(product {sum(r['kind'] == 'product' for r in rows)}, unresolved {sum(r['kind'] != 'product' for r in rows)})")
open(C.CAT + "/empty_resolve.jsonl", "w").close()
subprocess.run([sys.executable, C.G + "/reestimate.py", C.CAT + "/landings_all.json", C.CAT + "/empty_resolve.jsonl",
                C.CAT + "/landing_table_all.txt", C.CAT + "/reestimate_all.out"], check=True)
