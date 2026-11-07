#!/usr/bin/env python3
"""Exact branch-and-bound versions of the fullsets.py quantities (no full enumeration needed):
  count(m)      number of jointly independent m-sets of full values (plain DFS count, cheap: no per-node work)
  C(m)          max cover(S) over independent m-sets (B&B: prune when cover + 9*(m - |S|) <= best)
  Xmin(m)       min X(S) over independent m-sets (B&B: X is monotone nondecreasing in S, prune when X >= best)
  Xmin_c(m, c)  min X(S) over independent m-sets with cover(S) >= c  (for the two-phase check)
  mflow         largest m with an independent m-set S having flow(S) >= 2m (flow-feasibility is hereditary:
                a subset of a flow-feasible set is flow-feasible, so the DFS is restricted to flow-feasible sets)
usage: python3 fullsets2.py [M|Mt]
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'))
from fullsets import Basis, popcount, maxflow_outputs  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

def setup(ori):
    B = BOUNDARY[ori]
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    fulls = sorted(v for v, ts in trip.items() if len(ts) == 3)
    line = {f: (trip[f][0] ^ trip[f][1], trip[f][0] ^ trip[f][2]) for f in fulls}
    supp = {f: trip[f][0] | trip[f][1] | trip[f][2] for f in fulls}
    return B, trip, fulls, line, supp

def main(ori):
    t0 = time.time()
    B, trip, fulls, line, supp = setup(ori)
    out_mask = sum(1 << i for i in range(32, 64))
    N = len(fulls)
    # pairwise compatibility matrix (speeds up DFS)
    comp = [[False] * N for _ in range(N)]
    for i, j in itertools.combinations(range(N), 2):
        bs = Basis(); ok = all(bs.add(v) for v in line[fulls[i]] + line[fulls[j]])
        comp[i][j] = comp[j][i] = ok
    # 1. counts
    count = Counter(); nodes = [0]
    def rec_count(start, bs, m):
        nodes[0] += 1
        for i in range(start, N):
            t = bs.copy()
            if t.add(line[fulls[i]][0]) and t.add(line[fulls[i]][1]):
                count[m + 1] += 1; rec_count(i + 1, t, m + 1)
    rec_count(0, Basis(), 0)
    print(f'{ori}: independent sets by size: {dict(sorted(count.items()))}; DFS nodes {nodes[0]}; {time.time()-t0:.0f}s', flush=True)
    maxm = max(count)
    # 2. C(m) by branch and bound, for each m
    mult = [0] * 64
    def add(f, sgn):
        for T in trip[f]:
            v = T
            while v:
                b = (v & -v).bit_length() - 1; mult[b] += sgn; v &= v - 1
    C = {}
    for m in range(1, maxm + 1):
        best = [0]
        def rec(start, bs, k):
            cov = sum(1 for v in mult if v)
            if k == m:
                best[0] = max(best[0], cov); return
            if cov + 9 * (m - k) <= best[0]: return
            if N - start < m - k: return
            for i in range(start, N):
                t = bs.copy()
                if t.add(line[fulls[i]][0]) and t.add(line[fulls[i]][1]):
                    add(fulls[i], 1); rec(i + 1, t, k + 1); add(fulls[i], -1)
        rec(0, Basis(), 0); C[m] = best[0]
    print(f'{ori}: C(m) = max cover: {C}; {time.time()-t0:.0f}s', flush=True)
    # 3. Xmin(m): X is monotone nondecreasing in S, so prune when X >= best
    Xmin = {}; Xc = {}
    for m in range(1, maxm + 1):
        best = [10 ** 9]
        def rec(start, bs, k):
            X = sum(max(0, v - 2) for v in mult)
            if X >= best[0]: return
            if k == m:
                best[0] = X; return
            if N - start < m - k: return
            for i in range(start, N):
                t = bs.copy()
                if t.add(line[fulls[i]][0]) and t.add(line[fulls[i]][1]):
                    add(fulls[i], 1); rec(i + 1, t, k + 1); add(fulls[i], -1)
        rec(0, Basis(), 0); Xmin[m] = best[0]
    print(f"{ori}: Xmin(m) = min boundary excess of the full helpers alone: {Xmin}; {time.time()-t0:.0f}s", flush=True)
    # 4. flow-feasible sets (hereditary): largest m
    mflow = [0]; nflow = Counter()
    def rec_flow(start, bs, chosen):
        m = len(chosen)
        if m > mflow[0]: mflow[0] = m
        nflow[m] += 1
        for i in range(start, N):
            t = bs.copy()
            if t.add(line[fulls[i]][0]) and t.add(line[fulls[i]][1]):
                S = [fulls[j] for j in chosen + [i]]
                if maxflow_outputs(S, trip, out_mask) >= 2 * len(S):
                    rec_flow(i + 1, t, chosen + [i])
    rec_flow(0, Basis(), [])
    print(f'{ori}: flow-feasible independent sets by size: {dict(sorted(nflow.items()))}; largest m with flow >= 2m: {mflow[0]}; {time.time()-t0:.0f}s', flush=True)
    per_m = {m: dict(count=count[m], C=C[m], Xmin=Xmin[m], flow_ok=int(m <= mflow[0]), Xc=(Xc.get(m) or {})) for m in range(1, maxm + 1)}
    json.dump(dict(ori=ori, complete=True, per_m=per_m, mflow=mflow[0]), open(OUT/f'fullsets_{ori}.json', 'w'))

if __name__ == '__main__':
    for o in (sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']): main(o)
