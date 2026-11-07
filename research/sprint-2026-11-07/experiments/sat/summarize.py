"""Table of all instances in results.jsonl, plus per-k summary."""
import json, os, collections
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl"))]
print("%-14s %-32s %3s %3s %-8s %8s %7s %8s" % ("circuit", "scope", "k", "tW", "result", "wall_s", "solve_s", "clauses"))
for r in rows:
    print("%-14s %-32s %3d %3d %-8s %8.1f %7s %8s" % (r["circuit"], r["scope"], r["k"], r["targets_in_W"], r["result"],
          r["secs"] or 0, r.get("solve_secs"), r.get("nclauses")))
print()
byk = collections.defaultdict(lambda: collections.Counter())
tk = collections.defaultdict(list)
for r in rows:
    byk[r["k"]][r["result"]] += 1
    if r["result"] == "UNSAT":
        tk[r["k"]].append(r["solve_secs"])
print("k   UNSAT  TIMEOUT  SAT  ERROR   UNSAT solve-time min/median/max (s)")
for k in sorted(byk):
    c = byk[k]
    ts = sorted(tk[k])
    med = ts[len(ts) // 2] if ts else None
    print("%-3d %5d %8d %4d %6d   %s / %s / %s" % (k, c["UNSAT"], c["TIMEOUT"], c["SAT"], c["ERROR"],
          ts[0] if ts else "-", med if ts else "-", ts[-1] if ts else "-"))
print("total instances", len(rows), "total wall s", round(sum(r["secs"] or 0 for r in rows)))
