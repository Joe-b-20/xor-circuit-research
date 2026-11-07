"""Summary of results_batch.jsonl: counts per stage/family and the hardest solved k."""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "results_batch.jsonl"))] if os.path.exists(os.path.join(HERE, "results_batch.jsonl")) else []
by = collections.defaultdict(collections.Counter)
hardest = collections.defaultdict(int)
for r in rows:
    fam = "stage%s/%s" % (r.get("stage", "?"), r["scope"].split(":")[0])
    by[fam][r["result"]] += 1
    if r["result"] == "UNSAT":
        hardest[fam] = max(hardest[fam], r["k"])
print("%-14s %6s %4s %8s %6s  hardest solved k" % ("family", "UNSAT", "SAT", "TIMEOUT", "other"))
for fam in sorted(by):
    c = by[fam]
    other = sum(c.values()) - c["UNSAT"] - c["SAT"] - c["TIMEOUT"]
    print("%-14s %6d %4d %8d %6d  %s" % (fam, c["UNSAT"], c["SAT"], c["TIMEOUT"], other, hardest[fam] or "-"))
tot = collections.Counter(r["result"] for r in rows)
print("total %d instances: UNSAT %d, SAT %d, TIMEOUT %d, wall %.1f h; hardest UNSAT k overall: %s"
      % (len(rows), tot["UNSAT"], tot["SAT"], tot["TIMEOUT"], sum(r["secs"] or 0 for r in rows) / 3600, max(hardest.values()) if hardest else "-"))
if tot["SAT"]:
    print("!!! SAT instances:", [(r["circuit"], r["scope"], r.get("found")) for r in rows if r["result"] == "SAT"])
