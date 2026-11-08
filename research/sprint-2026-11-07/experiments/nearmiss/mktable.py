"""Print the instance tables (markdown) from results.jsonl, grouped by family prefix."""
import json, sys, collections
from common import *
tidx = {t: i for i, t in enumerate(TARGETS)}
def nm(v): return ("y%d" % tidx[v]) if v in tidx else ("x%d" % (v.bit_length()-1) if v in INPUTS else "%08x" % v)
rows = [json.loads(l) for l in open("results.jsonl")]
groups = collections.OrderedDict()
for r in rows:
    g = r["name"].split(":")[0]
    groups.setdefault(g, []).append(r)
for g, L in groups.items():
    print("\n### %s (%d instances)\n" % (g, len(L)))
    print("| instance | K | k | m | targets needed | result | wall s | clauses |")
    print("|---|---|---:|---:|---|---|---:|---:|")
    for r in L:
        W = ",".join(nm(v) for v in r["W"]) if r["W"] else "-"
        if len(W) > 70: W = W[:67] + "..."
        tn = ",".join("y%d" % t for t in r["targets_needed"])
        print("| %s | %s minus {%s} (%d) | %d | %d | %s | %s | %.1f | %s |" % (
            r["name"], r["family"], W, r["nK"], r["k"], r["m"], tn, r["result"] + ("" if r["result"] != "TIMEOUT" else " @%ds" % r["limit"]), r["secs"], r.get("nclauses") or ""))
tot = sum(r["secs"] for r in rows)
c = collections.Counter(r["result"] for r in rows)
print("\nTotal: %d instances, %.0f s solver wall; %s" % (len(rows), tot, dict(c)))
