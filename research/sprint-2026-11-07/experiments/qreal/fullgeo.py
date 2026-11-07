#!/usr/bin/env python3
"""Geometry of full values (exact, branch and bound; no full enumeration):
  per value: number of triples containing an output (a full HELPER needs >= 2: Lemma O1), outputs in supp(f)
  overlap histogram of supports over compatible pairs
  C(m) = max cover(S) over jointly independent m-sets of ADMISSIBLE full values (>= 2 output triples), B&B with the
         bound cover + sum of the (m-k) largest |supp(g) \\ current| over remaining compatible g
  mflow = largest m admitting an independent m-set with flow(S) >= 2m (hereditary; DFS restricted to flow-feasible
         sets, node-capped: if capped, the value is a lower bound and is NOT used as a row)
usage: python3 fullgeo.py ORI [time_cap_per_m_seconds] [flow_node_cap]
"""
import sys, time, itertools, json
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'))
from fullsets2 import setup, Basis
from fullsets import maxflow_outputs, popcount
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

def main(ori, tcap, fcap):
    t0 = time.time()
    B, trip, fulls, line, supp = setup(ori)
    out_mask = sum(1 << i for i in range(32, 64))
    ntri_out = {f: sum(1 for T in trip[f] if T & out_mask) for f in fulls}
    print(f'{ori}: {len(fulls)} full values; triples containing an output per value: {dict(sorted(Counter(ntri_out.values()).items()))}; '
          f'outputs in supp: {dict(sorted(Counter(popcount(supp[f] & out_mask) for f in fulls).items()))}; weight-3 values: {sum(1 for f in fulls if popcount(f)==3)}', flush=True)
    adm = [f for f in fulls if ntri_out[f] >= 2]
    print(f'{ori}: admissible full values (>= 2 output triples, Lemma O1): {len(adm)} of {len(fulls)}', flush=True)
    N = len(adm)
    comp = {}
    ov = Counter()
    for i, j in itertools.combinations(range(N), 2):
        bs = Basis(); ok = all(bs.add(v) for v in line[adm[i]] + line[adm[j]])
        comp[(i, j)] = comp[(j, i)] = ok
        if ok: ov[popcount(supp[adm[i]] & supp[adm[j]])] += 1
    print(f'{ori}: support overlap histogram over compatible admissible pairs: {dict(sorted(ov.items()))}', flush=True)
    # ---- C(m) by branch and bound
    C = {}; Cstatus = {}
    for m in range(1, 15):
        best = [0]; nodes = [0]; deadline = time.time() + tcap; timed = [False]
        def rec(start, bs, k, cur, cands):
            nodes[0] += 1
            if time.time() > deadline: timed[0] = True; return
            cov = popcount(cur)
            if k == m:
                if cov > best[0]: best[0] = cov
                return
            gains = sorted((popcount(supp[adm[i]] & ~cur) for i in cands), reverse=True)[:m - k]
            if len(gains) < m - k or cov + sum(gains) <= best[0]: return
            for idx, i in enumerate(cands):
                t = bs.copy()
                if t.add(line[adm[i]][0]) and t.add(line[adm[i]][1]):
                    newc = [j for j in cands[idx + 1:] if comp[(i, j)]]
                    rec(i + 1, t, k + 1, cur | supp[adm[i]], newc)
                    if timed[0]: return
        rec(0, Basis(), 0, 0, list(range(N)))
        if best[0] == 0: break
        C[m] = best[0]; Cstatus[m] = 'exact' if not timed[0] else 'TIMED OUT (lower bound only)'
        print(f'{ori}: C({m}) = {best[0]} [{Cstatus[m]}], nodes {nodes[0]}, {time.time()-t0:.0f}s', flush=True)
    # ---- flow-feasible sets (hereditary)
    mflow = [0]; nflow = Counter(); nodes = [0]; capped = [False]
    def rec_flow(start, bs, chosen, cands):
        nodes[0] += 1
        if nodes[0] > fcap: capped[0] = True; return
        m = len(chosen); mflow[0] = max(mflow[0], m); nflow[m] += 1
        for idx, i in enumerate(cands):
            t = bs.copy()
            if t.add(line[adm[i]][0]) and t.add(line[adm[i]][1]):
                S = [adm[j] for j in chosen + [i]]
                if maxflow_outputs(S, trip, out_mask) >= 2 * len(S):
                    rec_flow(i + 1, t, chosen + [i], [j for j in cands[idx + 1:] if comp[(i, j)]])
                    if capped[0]: return
    rec_flow(0, Basis(), [], list(range(N)))
    print(f'{ori}: flow-feasible independent sets by size {dict(sorted(nflow.items()))}; largest m with flow >= 2m: {mflow[0]} '
          f'[{"CAPPED: lower bound only" if capped[0] else "exact"}]; nodes {nodes[0]}; {time.time()-t0:.0f}s', flush=True)
    per_m = {m: dict(C=C[m], Cstatus=Cstatus[m], flow_ok=int(m <= mflow[0])) for m in C}
    json.dump(dict(ori=ori, complete=all(s == 'exact' for s in Cstatus.values()) and not capped[0], admissible=len(adm),
                   ntri_out=dict(Counter(ntri_out.values())), per_m=per_m, mflow=mflow[0], flow_exact=not capped[0]),
              open(OUT/f'fullsets_{ori}.json', 'w'))

if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 60.0, int(sys.argv[3]) if len(sys.argv) > 3 else 200000)
