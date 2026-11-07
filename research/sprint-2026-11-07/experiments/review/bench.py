#!/usr/bin/env python3
"""Review check for F8: recompute the section-12 statistics from variants_r12.csv and look at
censoring. Usage: bench.py CSV BASE_CONFIG OTHER_CONFIG"""
import csv, sys, statistics
from math import comb

rows = list(csv.DictReader(open(sys.argv[1])))
base, other = sys.argv[2], sys.argv[3]
INF = float("inf")


def arm(cfg):
    d = {}
    for r in rows:
        if r["config"] == cfg:
            it = int(r["it_c0"]) if r["it_c0"] else INF
            d[(r["instance"], r["seed"])] = (it, int(r["iters"]), float(r["wall_s"]), r["early_stop"])
    return d


A, B = arm(base), arm(other)


def sign_p(f, m):
    n = f + m
    return min(1.0, 2 * sum(comb(n, i) for i in range(0, min(f, m) + 1)) / 2 ** n) if n else 1.0


for mp in sorted({k[0] for k in A}):
    ks = sorted(k for k in A if k[0] == mp and k in B)
    a = [A[k][0] for k in ks]
    b = [B[k][0] for k in ks]
    pa = sum(x < INF for x in a) / len(ks)
    pb = sum(x < INF for x in b) / len(ks)
    ma, mb = statistics.median(a), statistics.median(b)
    fewer = sum(1 for k in ks if B[k][0] < A[k][0])
    more = sum(1 for k in ks if B[k][0] > A[k][0])
    tie = len(ks) - fewer - more
    both_fail = sum(1 for k in ks if A[k][0] == INF and B[k][0] == INF)
    both = [k for k in ks if A[k][0] < INF and B[k][0] < INF]
    ratio_both = statistics.median([B[k][0] / A[k][0] for k in both]) if both else INF
    # censoring budget: total iterations of failed runs (how many iterations a 120 s budget bought)
    failA = [A[k][1] for k in ks if A[k][0] == INF]
    failB = [B[k][1] for k in ks if B[k][0] == INF]
    I = min(failA + failB) if (failA + failB) else INF
    pA_I = sum(1 for k in ks if A[k][0] <= I) / len(ks)
    pB_I = sum(1 for k in ks if B[k][0] <= I) / len(ks)
    print(f"== {mp}: n={len(ks)}")
    print(f"  P success: {base} {pa:.2f}, {other} {pb:.2f}")
    print(f"  median it to ref (fail=inf): {ma:.0f} vs {mb:.0f}, ratio {mb/ma if ma<INF else INF:.2f}; "
          f"rank of median within finite values: base has {sum(x<INF for x in a)} finite of {len(a)}")
    print(f"  seed pairs: {other} fewer {fewer}, more {more}, tie {tie} (both failed {both_fail}); sign p {sign_p(fewer, more):.4f}")
    print(f"  both-success pairs {len(both)}: median per-seed ratio {ratio_both:.2f}")
    print(f"  iterations bought by the 120 s budget in FAILED runs: {base} med {statistics.median(failA) if failA else '-'}"
          f" (n={len(failA)}), {other} med {statistics.median(failB) if failB else '-'} (n={len(failB)})")
    print(f"  P(reach ref within I={I} iterations, the smallest failed budget): {base} {pA_I:.2f}, {other} {pB_I:.2f}")
    # wall-time view
    wa = statistics.median([A[k][2] if A[k][0] < INF else INF for k in ks])
    wb = statistics.median([B[k][2] if B[k][0] < INF else INF for k in ks])
    print(f"  median wall s to ref (fail=inf): {wa:.1f} vs {wb:.1f}")
