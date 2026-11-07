#!/usr/bin/env python3
"""Review check for F9/F4/F7: (a) outcomes of pt1, pt2, x1a, x1b from workers' status.json;
(b) crossmap table: gain over NIST vs matrix size k, with/without MixColumns, batch maps only.
Usage: f9.py SPRINT_DIR"""
import csv, json, math, os, sys

S = sys.argv[1]
for run in ["predtest/runs/pt1", "predtest/runs/pt2", "x1/runs/x1a", "x1/runs/x1b"]:
    d = os.path.join(S, run, "workers")
    print(f"== {run}")
    for w in sorted(os.listdir(d)):
        p = os.path.join(d, w, "status.json")
        if not os.path.exists(p):
            continue
        st = json.load(open(p))
        b = st.get("best") or {}
        fr = st.get("frontier")
        print(f"  {w:34s} best {b.get('gates')}@{b.get('depth')}  frontier {fr}  steps/s {st.get('steps_per_second', 0):.0f}  t {st.get('t', 0):.0f}")

# (b) crossmap
rows = list(csv.DictReader(open(os.path.join(S, "crossmap", "table.csv"))))


def rank(xs):
    o = sorted(range(len(xs)), key=lambda i: xs[i])
    r = [0.0] * len(xs)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and xs[o[j + 1]] == xs[o[i]]:
            j += 1
        for t in range(i, j + 1):
            r[o[t]] = (i + j) / 2 + 1
        i = j + 1
    return r


def spearman(x, y):
    rx, ry = rank(x), rank(y)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    num = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry))
    return num / den if den else float("nan")


def show(label, sel):
    ks = [int(r["k"]) for r in sel]
    gain = [float(r["gain_any_rel"]) for r in sel]
    logd = [math.log(float(r["direct_xor"])) for r in sel]
    rw = [float(r["rw_max"]) for r in sel]
    byk = {}
    for k, g in zip(ks, gain):
        byk.setdefault(k, []).append(g)
    med = {k: (len(v), round(sorted(v)[len(v) // 2], 3), round(min(v), 3), round(max(v), 3)) for k, v in sorted(byk.items())}
    print(f"  {label}: n={len(sel)}; gain_any_rel by k (n, median, min, max): {med}")
    print(f"     spearman gain~log(direct) {spearman(logd, gain):+.2f}, gain~k {spearman(ks, gain):+.2f}, "
          f"gain~rw_max {spearman(rw, gain):+.2f}; rw_max~log(direct) {spearman(rw, logd):+.2f}")


batch = [r for r in rows if r["protocol"].startswith("batch")]
show("batch maps", batch)
show("batch maps + aes-mixcolumns", batch + [r for r in rows if r["map"] == "aes-mixcolumns"])
show("all 59", rows)
mc = [r for r in rows if r["map"] == "aes-mixcolumns"][0]
print("  aes-mixcolumns row: k", mc["k"], "gain_any_rel", mc["gain_any_rel"], "best_gap_rel", mc["best_gap_rel"], "rw_max", mc["rw_max"], "protocol", mc["protocol"], "worker_hours", mc["worker_hours"])
# 4x4 GF(256) maps vs MC
print("  4x4 GF(2^8) maps (k=4, n_in=32), gain_any_rel:")
for r in rows:
    if r["k"] == "4" and r["n_in"] == "32":
        print(f"     {r['map']:28s} gain {float(r['gain_any_rel']):+.3f} rw_max {r['rw_max']} protocol {r['protocol']} worker_h {r['worker_hours']}")
