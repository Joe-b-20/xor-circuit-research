"""Tables for REPORT.md from results.jsonl, comp_*.json and fac_*.json.  python3 summarize.py"""
import json, os, glob, collections
HERE = os.path.dirname(os.path.abspath(__file__))
NAMES = {"kste:3146": "kste#43 33x3^7", "kste:2229": "kste#34 45x3^4", "kste:1557": "kste#41 108x3^4",
         "sampleA:109": "hunt 2101x15x11x3x3", "sampleA:48": "hunt 18927x15x3x3",
         "sampleA:781": "giant 62856x3", "sampleC:131": "giant 69228x3x3"}
ORDER = list(NAMES)
rows = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
best = {}
for r in rows:
    k = (r["circuit"], tuple(r["W"]), r.get("pool", "full"))
    cur = best.get(k)
    if cur is None or r["result"] in ("UNSAT", "SAT") or (cur["result"] == "TIMEOUT" and r["result"] == "TIMEOUT" and r["limit"] > cur["limit"]):
        best[k] = r
rows = list(best.values())


def ci(c):
    return ORDER.index(c) if c in ORDER else 99


def free(r):
    return r["k"] - 1 - r["targets_in_W"]


print("## Component structures [checked: comp_*.json, fac_*.json]\n")
print("Local fan structure at the member state (satmob's method) and the plateau's coupled factor at that state.\n")
print("| circuit | plateau (radices) | depth | plateau core | local core | local mobile | neutral moves | local components (shapes) | coupled factor: choice size / locally core / local comps touched / roots (targets) | coupled instance (k, tW, free) | whole mobile part (k, tW, free) |")
print("|---|---|---:|---:|---:|---:|---:|---|---|---|---|")
for c in ORDER:
    cp = os.path.join(HERE, "comp_%s.json" % c.replace(":", "_"))
    fp = os.path.join(HERE, "fac_%s.json" % c.replace(":", "_"))
    if not (os.path.exists(cp) and os.path.exists(fp)):
        continue
    d = json.load(open(cp)); f = json.load(open(fp))
    shapes = collections.Counter("%d+%d" % (len(x["mobile"]), len(x["roots"])) for x in d["components"])
    f0 = f["factors"][0]
    wm = d["whole_mobile"]
    print("| %s | %s | %d | %d | %d | %d | %d | %d (%s) | %d / %d / %s / %d (%d) | (%d, %d, %d) | (%d, %d, %d) |" % (
        c, NAMES[c], d["depth"], f["plateau_core"], f["local_core"], f["local_mobile"], d["fan"]["n_neutral"],
        len(d["components"]), ", ".join("%s x%d" % (s, n) for s, n in sorted(shapes.items())),
        len(f0["choice"]), len(f0["choice_locally_core"]), f0["local_components"], len(f0["roots"]), f0["root_targets"],
        f0["k"], f0["tW"], f0["free"], wm["k"], wm["tW"], wm["free"]))

print("\nPer-circuit local components (k, tW, free) in component order, and the plateau's 3-way factors seen locally:\n")
for c in ORDER:
    cp = os.path.join(HERE, "comp_%s.json" % c.replace(":", "_"))
    fp = os.path.join(HERE, "fac_%s.json" % c.replace(":", "_"))
    if not (os.path.exists(cp) and os.path.exists(fp)):
        continue
    d = json.load(open(cp)); f = json.load(open(fp))
    per = " ".join("c%d:%d+%d(%d,%d,%d)" % (w["idx"], len(w["mobile"]), len(w["roots"]), w["k"], w["tW"], w["free"]) for w in d["component_windows"])
    fac = " ".join("f%d:r%d|%d|%s" % (x["idx"], x["radix"], len(x["choice"]), x["local_components"]) for x in f["factors"])
    print("* %s (%s): local %s; plateau factors (radix | choice size | local comps) %s" % (c, NAMES[c], per, fac))

print("\n## Instance table [measured]\n")
print("One row per distinct (circuit, W, pool); best record kept.  free = k - 1 - tW.  F = plateau coupled factor window (fac.py), M = local fan component window (mob2.py, satmob's method).  prior = sat/ campaigns' result on the identical (circuit, W) if any.\n")
print("| circuit | scope | level | k | tW | free | pool | result | wall s | solve s | clauses | prior (sat/) |")
print("|---|---|---|---:|---:|---:|---|---|---:|---:|---:|---|")
for r in sorted(rows, key=lambda r: (r["family"] != "F", ci(r["circuit"]), str(r["level"]), free(r), r["k"], r["scope"])):
    res = r["result"] + ("(%ds)" % r["limit"] if r["result"] == "TIMEOUT" else "")
    pr = r.get("prior_sat_campaign")
    pr = ("%s@%ss" % (pr[0], int(pr[1])) if pr else "-")
    print("| %s | %s | %s | %d | %d | %d | %s | %s | %.1f | %s | %s | %s |" % (
        r["circuit"], r["scope"], r["level"], r["k"], r["targets_in_W"], free(r), r.get("pool", "full"), res,
        r.get("secs") or 0, r.get("solve_secs") if r.get("solve_secs") is not None else "-", r.get("nclauses") or "-", pr))

print("\n## Counts per circuit and level [measured]\n")
print("| circuit | level | pool | instances | UNSAT | SAT | TIMEOUT | max solved free | UNSAT solve-time median / max (s) |")
print("|---|---|---|---:|---:|---:|---:|---:|---|")
groups = collections.defaultdict(list)
for r in rows:
    groups[(r["circuit"], str(r["level"]), r.get("pool", "full"))].append(r)
for key in sorted(groups, key=lambda x: (ci(x[0]), x[1], x[2])):
    g = groups[key]
    cnt = collections.Counter(r["result"] for r in g)
    solved = [r for r in g if r["result"] in ("UNSAT", "SAT")]
    st = sorted((r.get("solve_secs") or 0) for r in solved)
    med = st[len(st) // 2] if st else None
    print("| %s | %s | %s | %d | %d | %d | %d | %s | %s |" % (
        key[0], key[1], key[2], len(g), cnt["UNSAT"], cnt["SAT"], cnt["TIMEOUT"],
        max(free(r) for r in solved) if solved else "-", ("%.1f / %.1f" % (med, st[-1])) if st else "-"))

print("\n## Hardness by free values (full pool) [measured]\n")
print("| free | instances | UNSAT | TIMEOUT | UNSAT solve s min / median / max |")
print("|---:|---:|---:|---:|---|")
byf = collections.defaultdict(list)
for r in rows:
    if r.get("pool", "full") == "full":
        byf[free(r)].append(r)
for fv in sorted(byf):
    g = byf[fv]; cnt = collections.Counter(r["result"] for r in g)
    st = sorted((r.get("solve_secs") or 0) for r in g if r["result"] == "UNSAT")
    print("| %d | %d | %d | %d | %s |" % (fv, len(g), cnt["UNSAT"], cnt["TIMEOUT"], ("%.1f / %.1f / %.1f" % (st[0], st[len(st) // 2], st[-1])) if st else "-"))
tot = collections.Counter(r["result"] for r in rows)
print("\nTotals: %d distinct instances: %s; solver wall %.0f s" % (len(rows), dict(tot), sum(r.get("secs") or 0 for r in rows)))
