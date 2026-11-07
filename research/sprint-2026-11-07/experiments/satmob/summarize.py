"""Tables for REPORT.md from results.jsonl and comp_*.json.  python3 summarize.py [md]"""
import json, os, glob, collections, sys
HERE = os.path.dirname(os.path.abspath(__file__))
rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
# best record per (circuit, W, pool): UNSAT/SAT beats TIMEOUT; longer TIMEOUT beats shorter
best = {}
for r in rows:
    k = (r["circuit"], tuple(r["W"]), r.get("pool", "full"))
    cur = best.get(k)
    if cur is None or r["result"] in ("UNSAT", "SAT") or (cur["result"] == "TIMEOUT" and r["result"] == "TIMEOUT" and r["limit"] > cur["limit"]):
        best[k] = r
rows = sorted(best.values(), key=lambda r: (r["circuit"] != "repo", r["circuit"], str(r["level"]), r["k"] - 1 - r["targets_in_W"], r["k"], r["scope"]))

print("## Results table [measured]\n")
print("One row per distinct (circuit, W, pool); best record kept (UNSAT/SAT over TIMEOUT, longest TIMEOUT).  free = k - 1 - tW.  prior = the sat/ campaigns' result for the identical (circuit, W) if any (full pool only).\n")
print("| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |")
print("|---|---|---:|---:|---:|---:|---|---|---:|---:|---:|---|")
for r in rows:
    res = r["result"] + ("(%ds)" % r["limit"] if r["result"] == "TIMEOUT" else "")
    pr = r.get("prior_sat_campaign")
    pr = ("%s@%ss" % (pr[0], int(pr[1])) if pr else "-")
    print("| %s | %s | %s | %d | %d | %d | %s | %s | %.1f | %s | %s | %s |" % (
        r["circuit"], r["scope"], r["level"], r["k"], r["targets_in_W"], r["k"] - 1 - r["targets_in_W"], r.get("pool", "full"), res,
        r.get("secs") or 0, r.get("solve_secs") if r.get("solve_secs") is not None else "-", r.get("nclauses") or "-", pr))

print("\n## Counts per circuit and level [measured]\n")
print("| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | max solved k | UNSAT solve-time median / max (s) |")
print("|---|---|---|---:|---:|---:|---:|---:|---:|---|")
groups = collections.defaultdict(list)
for r in rows:
    groups[(r["circuit"], str(r["level"]), r.get("pool", "full"))].append(r)
for key in sorted(groups, key=lambda x: (x[0] != "repo", x[0], x[1], x[2])):
    g = groups[key]
    c = collections.Counter(r["result"] for r in g)
    solved = [r for r in g if r["result"] in ("UNSAT", "SAT")]
    st = sorted((r.get("solve_secs") or 0) for r in solved)
    med = st[len(st) // 2] if st else None
    print("| %s | %s | %s | %d | %d | %d | %d | %s | %s | %s |" % (
        key[0], key[1], key[2], len(g), c["UNSAT"], c["SAT"], c["TIMEOUT"],
        max((r["k"] - 1 - r["targets_in_W"]) for r in solved) if solved else "-",
        max(r["k"] for r in solved) if solved else "-",
        ("%.1f / %.1f" % (med, st[-1])) if st else "-"))

print("\n## Hardness by free values (all circuits, full pool) [measured]\n")
print("| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |")
print("|---:|---:|---:|---:|---|")
byf = collections.defaultdict(list)
for r in rows:
    if r.get("pool", "full") == "full":
        byf[r["k"] - 1 - r["targets_in_W"]].append(r)
for f in sorted(byf):
    g = byf[f]; c = collections.Counter(r["result"] for r in g)
    st = sorted((r.get("solve_secs") or 0) for r in g if r["result"] == "UNSAT")
    print("| %d | %d | %d | %d | %s |" % (f, len(g), c["UNSAT"], c["TIMEOUT"], ("%.1f / %.1f / %.1f" % (st[0], st[len(st) // 2], st[-1])) if st else "-"))

print("\n## Component statistics per circuit [checked: comp_*.json]\n")
print("| circuit | depth | core | mobile | neutral moves | components | shapes (mobile+roots) | per-component (k, tW, free) | whole mobile part (k, tW, free) | values with >1 split |")
print("|---|---:|---:|---:|---:|---:|---|---|---|---:|")
for p in sorted(glob.glob(os.path.join(HERE, "comp_*.json")), key=lambda x: ("repo" not in x, x)):
    d = json.load(open(p))
    shapes = collections.Counter("%d+%d" % (len(c["mobile"]), len(c["roots"])) for c in d["components"])
    per = " ".join("(%d,%d,%d)" % (w["k"], w["tW"], w["free"]) for w in d["component_windows"])
    wm = d["whole_mobile"]
    print("| %s | %d | %d | %d | %d | %d | %s | %s | (%d,%d,%d) | %d |" % (
        d["circuit"], d["depth"], len(d["fan"]["core"]), len(d["fan"]["mobile"]), d["fan"]["n_neutral"], len(d["components"]),
        ", ".join("%s x%d" % (s, n) for s, n in sorted(shapes.items())), per, wm["k"], wm["tW"], wm["free"], len(d["ambiguous_values"])))
tot = collections.Counter(r["result"] for r in rows)
print("\nTotals: %d distinct instances: %s; solver wall %.0f s" % (len(rows), dict(tot), sum(r.get("secs") or 0 for r in rows)))
