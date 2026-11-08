#!/usr/bin/env python3
"""qjoint/qj_pairs.py -- joint finite search over PAIRS (and triangles) of hubs that meet the same full helpers.

Setting (REPORT.md section 2).  Hub k: value h_k, r_k represented triples R_k, witness full set S_k subset of N(h_k)
(one full helper per full-met missing label of the hub, Lemma 4.6 / C1(a)).  Two hubs k, k' interact only through
  (i)  a common full helper f in S_k n S_k' -- at the SAME full-met label (then P(h_k+f) and P(h_k'+f) share f's end c,
       so h_k + h_k' in PV; the hubs share that missing label and by Lemma 4.6 no other) or at DIFFERENT labels of f;
  (ii) a shared hub-only missing label (h_k + h_k' in PV; mixed vector H_k + H_k' + P(h_k + h_k')).
Hubs with r + m = 1 carry a single vector private in their coordinate H_k and never create a dependence, so only hubs
with r + m >= 2 are enumerated: r = 0 with cap_0 >= 2, r = 1 with cap_1 >= 1, r = 2 with cap_2 >= 1 (tables of
qhub/hub2_{ori}.json, finite fact H2).  For every full value f, every pair of such hubs with f in both witness sets, and
every maximal (R, S ∋ f) choice of each hub, the joint family is tested; the achievable joint classes (r_1 + m_1,
r_2 + m_2) are tabulated by sharing mode.  Separately: the graph on the r = 2 hub values (cap_2 >= 1) with
XOR in PV and jointly independent with the hub-only mixed vector, and its triangles (three (2,2,0) hubs pairwise
sharing one hub-only label, the shape of the q = 4 M^T survivors).
usage: python3 qj_pairs.py [M,Mt]
"""
import sys, json, time, itertools
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/qjoint'))
from qj_geo import Geo, Basis, FULLC, HUBC, independent, rank  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qjoint'

def hub_configs(G, h, r, cap):
    """all (R, S) with |R| = r, S subset of N(h), F(h,R,S) independent, |S| = cap (maximal) -- plus all S of size
    cap-1 >= 1 when cap >= 2 (sub-maximal configurations also matter: a hub at r + m = 2)."""
    reps = G.trip.get(h, [])
    out = []
    for R in (itertools.combinations(reps, r) if r else [()]):
        base = [T | HUBC(0) for T in R]
        for m in range(max(1, cap - 1), cap + 1):
            for S in itertools.combinations(G.N[h], m):
                vs = list(base)
                for f in S: vs += G.full_vectors(f); vs.append(HUBC(0) | FULLC(G.fidx[f]) | G.pairmask[h ^ f])
                if independent(vs): out.append((R, S))
    return out

def relabel(vs, k):
    """move hub coordinate 0 to k"""
    return [(v ^ HUBC(0) ^ HUBC(k)) if v & HUBC(0) else v for v in vs]

def main(ori):
    t0 = time.time()
    G = Geo(ori); cap = G.load_cap()
    cand = []   # (h, r, cap_r)
    for r, tab in cap.items():
        for h, c in tab.items():
            if r + c >= 2 and c >= 1: cand.append((h, r, c))
    print(f'{ori}: candidate hubs with r + cap >= 2: {Counter((r, c) for _, r, c in cand)}; {time.time()-t0:.0f}s', flush=True)
    # per hub: configurations (R, S) with |S| in {cap-1, cap}
    cfg = {}
    byf = defaultdict(list)       # f -> list of (h, r, cfg index) with f in S
    for h, r, c in cand:
        cs = hub_configs(G, h, r, c)
        cfg[(h, r)] = cs
        for ci, (R, S) in enumerate(cs):
            for f in S: byf[f].append((h, r, ci))
    print(f'{ori}: {sum(len(v) for v in cfg.values())} hub configurations; per-f lists: {sum(len(v) for v in byf.values())} incidences; {time.time()-t0:.0f}s', flush=True)
    # pairs sharing f
    stat = Counter(); pairs_seen = set(); examples = {}
    nt = 0
    for f, lst in byf.items():
        for (h1, r1, c1), (h2, r2, c2) in itertools.combinations(lst, 2):
            if h1 == h2: continue
            R1, S1 = cfg[(h1, r1)][c1]; R2, S2 = cfg[(h2, r2)][c2]
            k1 = r1 + len(S1); k2 = r2 + len(S2)
            cls = tuple(sorted(((r1, len(S1)), (r2, len(S2)))))
            # sharing mode at f: same label iff the pairs P(h1+f), P(h2+f) intersect
            same = bool(G.pairmask[h1 ^ f] & G.pairmask[h2 ^ f])
            common = set(S1) & set(S2)
            # by Lemma 4.6 two hubs share at most one missing label: at most one common f with 'same label'
            nsame = sum(1 for g in common if G.pairmask[h1 ^ g] & G.pairmask[h2 ^ g])
            if nsame > 1: stat[('4.6-excluded', cls)] += 1; continue
            vs = [v for g in sorted(set(S1) | set(S2)) for v in G.full_vectors(g)]
            vs += relabel([T | HUBC(0) for T in R1] + [HUBC(0) | FULLC(G.fidx[g]) | G.pairmask[h1 ^ g] for g in S1], 1)
            vs += relabel([T | HUBC(0) for T in R2] + [HUBC(0) | FULLC(G.fidx[g]) | G.pairmask[h2 ^ g] for g in S2], 2)
            nt += 1
            ok = independent(vs)
            mode = 'same-label' if nsame == 1 else 'diff-labels'
            stat[(mode, cls, ok)] += 1
            if ok and (mode, cls) not in examples: examples[(mode, cls)] = dict(h1=hex(h1), r1=r1, S1=[hex(g) for g in S1], h2=hex(h2), r2=r2, S2=[hex(g) for g in S2], f=hex(f))
            # additionally a shared hub-only label (only if no shared full-met label, Lemma 4.6) when h1 + h2 in PV
            if nsame == 0 and (h1 ^ h2) in G.pairmask:
                ok2 = independent(vs + [HUBC(1) | HUBC(2) | G.pairmask[h1 ^ h2]])
                stat[('diff-labels+hub-only', cls, ok2)] += 1
    print(f'{ori}: {nt} joint pair tests; {time.time()-t0:.0f}s', flush=True)
    # summary by class: for each (mode, cls) the number of independent / dependent pairs
    rows = defaultdict(lambda: [0, 0])
    for key, n in stat.items():
        if key[0] == '4.6-excluded': continue
        mode, cls, ok = key; rows[(mode, cls)][0 if ok else 1] += n
    print(f'{ori}: joint pair results (mode, ((r1,m1),(r2,m2))): independent / dependent')
    for key in sorted(rows): print(f'   {key}: {rows[key][0]} / {rows[key][1]}')
    # the limit classes: both hubs at r + m = 3
    lim = {k: v for k, v in rows.items() if all(r + m == 3 for r, m in k[1])}
    print(f'{ori}: pairs with BOTH hubs at the H2 limit (r + m = 3) sharing a full helper: ' + '; '.join(f'{k}: {v[0]} indep / {v[1]} dep' for k, v in sorted(lim.items())))
    # r = 2 hubs (cap_2 >= 1): PV-adjacency graph with the hub-only mixed vector; triangles
    r2 = sorted(h for h, r, c in cand if r == 2)
    adj = defaultdict(set); edge_info = {}
    for h1, h2 in itertools.combinations(r2, 2):
        if (h1 ^ h2) not in G.pairmask: continue
        okany = False
        for (R1, S1) in cfg[(h1, 2)]:
            for (R2, S2) in cfg[(h2, 2)]:
                if len(S1) != 1 or len(S2) != 1: continue
                vs = [v for g in sorted(set(S1) | set(S2)) for v in G.full_vectors(g)]
                vs += relabel([T | HUBC(0) for T in R1] + [HUBC(0) | FULLC(G.fidx[g]) | G.pairmask[h1 ^ g] for g in S1], 1)
                vs += relabel([T | HUBC(0) for T in R2] + [HUBC(0) | FULLC(G.fidx[g]) | G.pairmask[h2 ^ g] for g in S2], 2)
                vs.append(HUBC(1) | HUBC(2) | G.pairmask[h1 ^ h2])
                if independent(vs): okany = True; break
            if okany: break
        edge_info[(h1, h2)] = okany
        if okany: adj[h1].add(h2); adj[h2].add(h1)
    npv = sum(1 for (h1, h2) in edge_info)
    nok = sum(1 for v in edge_info.values() if v)
    tri = [(a, b, c) for a, b, c in itertools.combinations(r2, 3) if b in adj[a] and c in adj[a] and c in adj[b]]
    print(f'{ori}: r = 2 hub values (cap_2 >= 1): {len(r2)}; pairs with XOR in PV: {npv}; of them jointly independent with a shared hub-only label: {nok}; triangles: {len(tri)}')
    # also: r=2 hubs sharing a full-met label with each other (same f, same label): from stat
    json.dump(dict(ori=ori, stat={str(k): v for k, v in stat.items()}, rows={str(k): v for k, v in rows.items()}, examples={str(k): v for k, v in examples.items()},
                   r2_values=[hex(h) for h in r2], r2_pv_pairs=npv, r2_pv_indep=nok, r2_triangles=[[hex(a), hex(b), hex(c)] for a, b, c in tri]),
              open(OUT/f'pairs_{ori}.json', 'w'), indent=1)
    print(f'{ori}: done {time.time()-t0:.0f}s', flush=True)

if __name__ == '__main__':
    oris = sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']
    for o in oris: main(o)
