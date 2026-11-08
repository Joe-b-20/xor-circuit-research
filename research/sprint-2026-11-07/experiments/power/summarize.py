#!/usr/bin/env python3
"""Tables for REPORT.md from anchors.json, windows.json, part3.json, results.jsonl.  Prints Markdown."""
import os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
anchors = json.load(open(os.path.join(HERE, "anchors.json")))
windows = json.load(open(os.path.join(HERE, "windows.json")))
p3 = {r["id"]: r for r in json.load(open(os.path.join(HERE, "part3.json")))["anchors"]}
p3b = {}
for line in open(os.path.join(HERE, "part3b.txt")):
    if "minimal any-pair window k=" in line:
        aid = line.split()[0]
        p3b[aid] = int(line.split("window k=")[1].split()[0])
res = []
if os.path.exists(os.path.join(HERE, "results.jsonl")):
    res = [json.loads(l) for l in open(os.path.join(HERE, "results.jsonl")) if l.strip()]
byA = collections.defaultdict(list)
for r in res:
    byA[r["anchor"]].append(r)
wByA = collections.defaultdict(list)
for w in windows:
    wByA[w["anchor"]].append(w)

print("## Anchor table\n")
print("| anchor | kind | G | improvement | need | symdiff | k_gen | k_min | windows A/C/B (k<=10/12/9) | contained | run: SAT/UNSAT/TO (A, C, B) | SAT found |")
print("|---|---|---:|---|---:|---:|---:|---:|---|---:|---|---|")
for a in anchors:
    aid = a["id"]
    ws = wByA[aid]
    nA = sum(w["fam"] == "A" for w in ws); nC = sum(w["fam"] == "C" for w in ws); nB = sum(w["fam"] == "B" for w in ws)
    rs = byA.get(aid, [])
    def cnt(fam):
        c = collections.Counter(r["result"] for r in rs if r["fam"] == fam)
        return "%d/%d/%d" % (c["SAT"], c["UNSAT"], c["TIMEOUT"])
    found = collections.Counter(("=truth" if r.get("found_equals_truth") else "other<=G-1") for r in rs if r["result"] == "SAT")
    imp = a["truth"]["id"]
    if a["kind"].startswith("hunt"):
        imp = "next 88 in chain (%s, +%ss)" % (a["truth"]["id"], a.get("gap_wall"))
    elif a["kind"] == "p2":
        imp = "nearest 89@4 (" + a["imp_note"].split("(")[1]
    else:
        imp = "nearest of %d: %s" % (a.get("n_imps", 0), a["truth"]["id"][:28])
    kg = p3.get(aid, {}).get("kgen0", "-")
    print("| %s | %s | %d | %s | %d | %d | %s | %s | %d/%d/%d | %d | %s, %s, %s | %s |" % (
        aid, a["kind"], a["gates"], imp, a["dist"]["need0"], a["dist"]["sd0"], kg, p3b.get(aid, "-"), nA, nC, nB,
        a["n_contained_truth"], cnt("A"), cnt("C"), cnt("B"), dict(found) if found else "-"))

print("\n## Run totals\n")
tot = collections.Counter(r["result"] for r in res)
print("instances run: %d; SAT %d, UNSAT %d, TIMEOUT %d, ERROR %d; solver wall %.1f min; budget-truncated instances: %d"
      % (len(res), tot["SAT"], tot["UNSAT"], tot["TIMEOUT"], tot["ERROR"], sum(r["secs"] or 0 for r in res) / 60, sum(1 for r in res if r["budget_truncated"])))
print("\n| class | instances | SAT | UNSAT | TIMEOUT |")
print("|---|---:|---:|---:|---:|")
for cls, name in ((0, "P0 kept set contained in the known improvement"), (1, "P1 contained in another known smaller circuit"),
                  (2, "P2 one-seed windows k<=8 (60 s)"), (3, "P3 output blocks k<=12 (1800/900 s)"), (4, "P4 one-seed windows k=9-10 (900 s)"), (5, "P5 two-seed windows k<=9 (900 s)")):
    rr = [r for r in res if r["priority"] == cls]
    c = collections.Counter(r["result"] for r in rr)
    print("| %s | %d | %d | %d | %d |" % (name, len(rr), c["SAT"], c["UNSAT"], c["TIMEOUT"]))
print("\nper anchor kind (non-contained windows only):\n")
print("| kind | anchors | instances | SAT | UNSAT | TIMEOUT | k range | anchors with a SAT |")
print("|---|---:|---:|---:|---:|---:|---|---:|")
for kind in ("hunt-descent", "hunt-excursion", "repo", "seed", "p2"):
    rr = [r for r in res if r["kind"] == kind and not r["contained_truth"] and not r["n_contained_corpus"]]
    c = collections.Counter(r["result"] for r in rr)
    ks = [r["k"] for r in rr]
    print("| %s | %d | %d | %d | %d | %d | %s | %d |" % (kind, sum(a["kind"] == kind for a in anchors), len(rr), c["SAT"], c["UNSAT"], c["TIMEOUT"],
          ("%d-%d" % (min(ks), max(ks))) if ks else "-", len({r["anchor"] for r in rr if r["result"] == "SAT"})))
print("\nk histogram of the run (all classes): %s" % sorted(collections.Counter(r["k"] for r in res).items()))
sats = [r for r in res if r["result"] == "SAT"]
print("\nSAT instances not contained in the known improvement (unexpected finds): %d" % sum(1 for r in sats if not r["contained_truth"]))
for r in sats:
    if not r["contained_truth"]:
        print("  ", r["anchor"], r["scope"], "k=%d" % r["k"], "found", r.get("found"), "eq_truth", r.get("found_equals_truth"), "new outside truth", r.get("found_n_new_outside_truth"))
print("\nsolve-time medians (UNSAT) per (fam, k):")
d = collections.defaultdict(list)
for r in res:
    if r["result"] == "UNSAT":
        d[(r["fam"], r["k"])].append(r["secs"])
for key in sorted(d):
    xs = sorted(d[key])
    print("  %s k=%d: n=%d med=%.1fs max=%.1fs" % (key[0], key[1], len(xs), xs[len(xs) // 2], xs[-1]))
