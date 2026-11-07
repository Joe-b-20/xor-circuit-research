"""Summary of a batch: python3 batch_summary.py [batch|batch2]  (default batch).
batch  -> results_batch.jsonl;  batch2 -> results_batch2.shard*.jsonl (+ results_batch2.jsonl) merged.
Prints counts per stage/family (UNSAT/SAT/TIMEOUT), the hardest solved k, and any SAT instance."""
import json, os, sys, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
which = sys.argv[1] if len(sys.argv) > 1 else "batch"
files = [os.path.join(HERE, "results_batch.jsonl")] if which == "batch" else \
    [os.path.join(HERE, "results_batch2.jsonl")] + sorted(glob.glob(os.path.join(HERE, "results_batch2.shard*.jsonl")))
rows = [json.loads(l) for f in files if os.path.exists(f) for l in open(f) if l.strip()]
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
    print("%-14s %6d %4d %8d %6d  %s" % (fam, c["UNSAT"], c["SAT"], c["TIMEOUT"],
          sum(c.values()) - c["UNSAT"] - c["SAT"] - c["TIMEOUT"], hardest[fam] or "-"))
tot = collections.Counter(r["result"] for r in rows)
print("total %d instances: UNSAT %d, SAT %d, TIMEOUT %d, solver wall %.1f h; hardest UNSAT k overall: %s"
      % (len(rows), tot["UNSAT"], tot["SAT"], tot["TIMEOUT"], sum(r["secs"] or 0 for r in rows) / 3600,
         max(hardest.values()) if hardest else "-"))
if tot["SAT"]:
    print("!!! SAT instances:", [(r["circuit"], r["scope"], r.get("found")) for r in rows if r["result"] == "SAT"])
