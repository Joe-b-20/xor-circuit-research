#!/usr/bin/env python3
"""Prepare the catalogue queue (catalogue/queue.jsonl) and catalogue/products.json.
Queue order: (1) the unresolved giant seeds of giants/resolve.jsonl (time_limit 1800), then
(2) every distinct sampled 88 state (samples.jsonl, samplesC, samplesD) not already mapped to a
product key in hunt/plateaus.json "states", interleaved across chains (1st sample of every chain,
then 2nd, ...) so concurrent shards work on different chains and a chain's later samples can
resolve by lookup.  Items already having a result in a shard file are kept in the queue (workers
skip them).  Clears stale claims (claimed, no result) so an interrupted run resumes.
Usage: cat_prep.py"""
import collections, glob, json, os, sys
sys.path.insert(0, "/home/joebachir20/xs-campaigns/2026-11-07-sprint/giants")
import cat_lib as C  # noqa: E402

os.makedirs(C.PLDIR, exist_ok=True)
os.makedirs(C.CAT + "/claims", exist_ok=True)
store = json.load(open(C.HUNT + "/plateaus.json"))
P, H = store["plateaus"], store["states"]
prod = {k: v["plateau"] for k, v in P.items() if v["kind"] == "product"}
json.dump(prod, open(C.CAT + "/products.json.tmp", "w"))
os.replace(C.CAT + "/products.json.tmp", C.CAT + "/products.json")

queue = []
E = {e["key"]: e for e in json.load(open(C.G + "/entries.json"))}
for line in open(C.G + "/resolve.jsonl"):
    r = json.loads(line)
    if not r["resolved"]:
        e = E[r["entry"]]
        queue.append({"id": e["samples"][0][3], "kind": "giant", "entry": r["entry"], "seed": e["seed"],
                      "time_limit": 1800})
gids = {q["id"] for q in queue}
bychain = collections.defaultdict(list)
seen = set(gids)
n_all = n_known = 0
for f in C.SAMPLE_FILES:
    for line in open(f):
        r = json.loads(line)
        if r["gates"] != 88:
            continue
        n_all += 1
        h = r["hash"]
        if h in seen:
            continue
        seen.add(h)
        k = H.get(h)
        if k and P.get(k, {}).get("kind") == "product":
            n_known += 1
            continue
        bychain[(r["arm"], r["worker"])].append((r["t"] or 0, h, r["values"], r["arm"], r["worker"]))
rest = []
for c in bychain.values():
    c.sort()
mx = max((len(c) for c in bychain.values()), default=0)
for i in range(mx):
    for c in sorted(bychain):
        if i < len(bychain[c]):
            t, h, v, a, w = bychain[c][i]
            rest.append({"id": h, "kind": "sample", "arm": a, "worker": w, "t": t, "values": v, "time_limit": 900})
queue += rest
with open(C.CAT + "/queue.jsonl.tmp", "w") as f:
    for q in queue:
        f.write(json.dumps(q) + "\n")
os.replace(C.CAT + "/queue.jsonl.tmp", C.CAT + "/queue.jsonl")
done = C.done_ids()
stale = 0
for cl in glob.glob(C.CAT + "/claims/*"):
    if os.path.basename(cl) not in done:
        os.remove(cl)
        stale += 1
print(f"88 sample lines {n_all}; distinct states mapped to a product in plateaus.json {n_known}; "
      f"queue {len(queue)} (giants {len(gids)}, samples {len(rest)}); already done {len(done)}; stale claims cleared {stale}")
