#!/usr/bin/env python3
"""Part 3b (no solver): the MINIMAL window that contains the improvement: W = M plus only what the kept
set can no longer compute under any pair (run_scopes.window with ANYPAIR, i.e. no wiring closure).
This is the lower bound on k for any value-set window of this kind; the sprint's generators (wiring
closure) give the larger k_gen of part3.  Writes part3b.txt."""
import sys, os, json, collections
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/sat"); sys.path.insert(0, HERE)
import sat87, run_scopes  # noqa: E402
run_scopes.ANYPAIR = True
from anchors import helpers, rotset, TSET, SRC  # noqa: E402


def q(xs):
    xs = sorted(xs); n = len(xs)
    return "n=%d min=%d q1=%d med=%d q3=%d max=%d" % (n, xs[0], xs[n // 4], xs[n // 2], xs[3 * n // 4], xs[-1]) if xs else "-"


def kmin(vals, imp, s=0):
    order = sat87.wiring_from_values(vals)
    M = helpers(vals) - rotset(helpers(imp), s)
    W = run_scopes.window(order, sorted(M))
    return len(M), len(W), sum(1 for t in sat87.TARGETS if t in W)


lines = []
for a in json.load(open(os.path.join(HERE, "anchors.json"))):
    m, kw, tw = kmin(a["values"], a["truth"]["values"], 0)
    lines.append("%-28s g=%d need=%2d -> minimal any-pair window k=%2d (tW=%2d, free=%2d)" % (a["id"], a["gates"], m, kw, tw, kw - 1 - tw))
samples = {}
for tag, rel, runs, arms in SRC:
    for i, line in enumerate(open(os.path.join(S, rel))):
        samples["%s:%d" % (tag, i)] = json.loads(line)["values"]
rows = []
for p in json.load(open(os.path.join(HERE, "pairs.json"))):
    v89, v88 = samples[p["a89"]], samples[p["b88"]]
    if sat87.wiring_from_values(v89) is None:
        continue
    m, kw, tw = kmin(v89, v88)
    rows.append((p["kind"], m, kw, tw))
for kind in ("descent", "excursion"):
    sel = [r for r in rows if r[0] == kind]
    lines.append("all %s pairs (%d): minimal window k_min %s; k_min <= 9: %d, <= 10: %d, <= 12: %d; k_min == k_needed: %d"
                 % (kind, len(sel), q([r[2] for r in sel]), sum(r[2] <= 9 for r in sel), sum(r[2] <= 10 for r in sel), sum(r[2] <= 12 for r in sel), sum(r[2] == r[1] for r in sel)))
    lines.append("all %s pairs: targets in the minimal window %s" % (kind, q([r[3] for r in sel])))
hist = collections.Counter(min(r[2], 30) for r in rows)
lines.append("k_min histogram, all pairs (30 = >= 30): %s" % sorted(hist.items()))
open(os.path.join(HERE, "part3b.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
