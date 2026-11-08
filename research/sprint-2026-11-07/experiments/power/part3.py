#!/usr/bin/env python3
"""Part 3 (no solver): the window the sprint's generator would need in order to contain the improvement.
For every anchor (anchors.json) and for every hunt 89->88 pair (pairs.json + samples): M = helpers of the
anchor not in the improvement (identity frame; and the best rotation), and k_gen = |window(order, M)|,
the removed set the sprint generator produces when seeded with all of M (upward closure under the
anchor's any-pair wiring + dead cone + closure repair), with its target count.  Writes part3.json, part3.txt.
"""
import sys, os, json, collections
H = os.path.expanduser("~")
S = H + "/xs-campaigns/2026-11-07-sprint"
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, S + "/sat"); sys.path.insert(0, HERE)
import sat87, run_scopes  # noqa: E402
from anchors import helpers, rotset, TSET, SRC  # noqa: E402


def gen_window(order, vals, imp_vals, s):
    ah = helpers(vals)
    M = ah - rotset(helpers(imp_vals), s)
    W = run_scopes.window(order, sorted(M))
    tw = sum(1 for t in sat87.TARGETS if t in W)
    return len(M), len(W), tw


def q(xs):
    xs = sorted(xs); n = len(xs)
    return "n=%d min=%d q1=%d med=%d q3=%d max=%d" % (n, xs[0], xs[n // 4], xs[n // 2], xs[3 * n // 4], xs[-1]) if xs else "-"


out = {"anchors": [], "pairs": []}
lines = []
anchors = json.load(open(os.path.join(HERE, "anchors.json")))
for a in anchors:
    order = sat87.wiring_from_values(a["values"])
    best = None
    for s in range(4):
        m, kw, tw = gen_window(order, a["values"], a["truth"]["values"], s)
        if best is None or (kw, m) < (best[1], best[0]):
            best = (m, kw, tw, s)
    m0, kw0, tw0 = gen_window(order, a["values"], a["truth"]["values"], 0)
    rec = {"id": a["id"], "kind": a["kind"], "gates": a["gates"], "need0": m0, "kgen0": kw0, "tW0": tw0,
           "need_best": best[0], "kgen_best": best[1], "tW_best": best[2], "rot_best": best[3]}
    out["anchors"].append(rec)
    lines.append("%-28s g=%d need=%2d -> generator window k=%2d (tW=%2d, free=%2d)%s" % (
        a["id"], a["gates"], m0, kw0, tw0, kw0 - 1 - tw0, "" if best[1] == kw0 else "  [rot %d: need %d k=%d]" % (best[3], best[0], best[1])))
# all hunt pairs
samples = {}
for tag, rel, runs, arms in SRC:
    for i, line in enumerate(open(os.path.join(S, rel))):
        r = json.loads(line)
        samples["%s:%d" % (tag, i)] = r["values"]
pairs = json.load(open(os.path.join(HERE, "pairs.json")))
for p in pairs:
    v89, v88 = samples[p["a89"]], samples[p["b88"]]
    order = sat87.wiring_from_values(v89)
    if order is None:
        continue
    m, kw, tw = gen_window(order, v89, v88, 0)
    out["pairs"].append({"a89": p["a89"], "b88": p["b88"], "kind": p["kind"], "need0": m, "kgen0": kw, "tW0": tw})
for kind in ("descent", "excursion"):
    sel = [r for r in out["pairs"] if r["kind"] == kind]
    lines.append("all %s pairs (%d): k_needed %s" % (kind, len(sel), q([r["need0"] for r in sel])))
    lines.append("all %s pairs: generator window k_gen %s" % (kind, q([r["kgen0"] for r in sel])))
    lines.append("all %s pairs: targets in that window %s" % (kind, q([r["tW0"] for r in sel])))
    lines.append("all %s pairs: k_gen <= 10: %d, <= 12: %d, <= 9: %d" % (kind, sum(r["kgen0"] <= 10 for r in sel), sum(r["kgen0"] <= 12 for r in sel), sum(r["kgen0"] <= 9 for r in sel)))
hist = collections.Counter(min(r["kgen0"], 40) for r in out["pairs"])
lines.append("k_gen histogram, all pairs (40 = >= 40): %s" % sorted(hist.items()))
json.dump(out, open(os.path.join(HERE, "part3.json"), "w"))
open(os.path.join(HERE, "part3.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
