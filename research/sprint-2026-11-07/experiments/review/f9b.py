#!/usr/bin/env python3
"""Review check for F9: rank correlation of the pre-registered rules A and B (crossmap/predict.csv)
with the realised gains of pt1/pt2 (gates below 'current' at the cap after 4 worker-hours)."""
import csv, math
pred = {r["map"]: r for r in csv.DictReader(open("/home/joebachir20/xs-campaigns/2026-11-07-sprint/crossmap/predict.csv"))}
real = {"ss17-8x8-gf16": 161, "klsw17-m-8x8-gf256-inv": 330, "skop15-8x8-gf16": 146, "skop15-4x4-gf256-inv": 88,
        "anubis-clefia-m0": 91, "khazad": 340, "fox-mu8": 500}


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
    return num / den


maps = list(real)
gain = [int(pred[m]["current"]) - real[m] for m in maps]
rel = [(int(pred[m]["current"]) - real[m]) / int(pred[m]["current"]) for m in maps]
predg = [int(pred[m]["pred_gain"]) for m in maps]
rA = [-int(pred[m]["rankA"]) for m in maps]
rB = [-int(pred[m]["rankB"]) for m in maps]
k = [int(pred[m]["k"]) for m in maps]
for m, g, r_ in zip(maps, gain, rel):
    print(f"  {m:26s} current {pred[m]['current']:>4s} after {real[m]:>4d} gain {g:2d} ({100*r_:.1f} %) predA {pred[m]['pred_gain']:>2s} rankA {pred[m]['rankA']:>2s} rankB {pred[m]['rankB']:>2s} k {pred[m]['k']}")
print(f"Spearman with absolute gain: rule A (-rank) {spearman(rA, gain):+.2f}, rule B (-rank) {spearman(rB, gain):+.2f}, "
      f"predicted gain {spearman(predg, gain):+.2f}, k {spearman(k, gain):+.2f}")
print(f"Spearman with relative gain: rule A {spearman(rA, rel):+.2f}, rule B {spearman(rB, rel):+.2f}, "
      f"predicted gain {spearman(predg, rel):+.2f}, k {spearman(k, rel):+.2f}")
