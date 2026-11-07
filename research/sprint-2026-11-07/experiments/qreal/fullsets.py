#!/usr/bin/env python3
"""Finite facts about SETS of full helpers (Task a / e geometry).

For a set S of full values that can be the full helpers of one phase (Lemma 4.4: the 3|S| relations H_f + T are
independent; equivalently the 2|S| six-set differences are independent), define, with supp(f) = union of the
three (pairwise disjoint) triples of f (9 boundary elements) and mult_S(v) = #{(f,T): f in S, v in T}:
  cover(S) = |union_f supp(f)|,            X(S) = sum_v (mult_S(v) - 2)_+,
  flow(S)  = max number of (f, triple)-> output assignments with distinct outputs, at most 2 per f, the output
             lying in that triple  (chronology: see Lemma O1 in REPORT.md).
Why.  Every full helper f gives one H-B edge f-a_j and one B-B edge b_j-c_j per triple T_j = {a_j,b_j,c_j}; these
6|S| edges are pairwise distinct (N1), so the boundary degree d_v >= mult_S(v) for all v in B and
      sum_{v in B} max(1, mult_S(v)) <= sum_B d_v = 2(x+y-q) + R + U = 2(x+y-q) + 32 + h - y + q - z   (BD)
      E_B = sum_B (d_v - 2)_+ >= X(S)                                                                    (BX)
      flow(S) >= 2|S|  (every full helper defines >= 2 distinct outputs through its non-defining represented edges)  (O1)
This script enumerates all independent sets (DFS, exact if it completes) and reports per size m:
  count, C(m) = max cover, X_min(m), the joint table of (cover, X) and whether flow >= 2m is ever satisfied.
usage: python3 fullsets.py [M|Mt] [node_cap]
"""
import sys, json, itertools, time
from collections import Counter, defaultdict
from pathlib import Path
sys.path.insert(0, str(Path.home()/'xs-campaigns/2026-11-07-sprint/lb76/pkg_copy/source/lower_bounds/checks'))
from stress import BOUNDARY  # noqa: E402
OUT = Path.home()/'xs-campaigns/2026-11-07-sprint/qreal'

class Basis:
    __slots__ = ('piv',)
    def __init__(self, piv=None): self.piv = dict(piv) if piv else {}
    def add(self, v):
        while v:
            hb = v.bit_length() - 1
            if hb in self.piv: v ^= self.piv[hb]
            else: self.piv[hb] = v; return True
        return False
    def copy(self): return Basis(self.piv)

def popcount(x): return bin(x).count('1')

def maxflow_outputs(S, trip_masks, out_mask):
    """max assignment (f, triple) -> output in triple, distinct outputs, <= 2 per f.  Small Ford-Fulkerson."""
    # nodes: src=0, f-nodes 1..n, triple nodes n+1.., output nodes, sink
    n = len(S); tri = [(i, T) for i, f in enumerate(S) for T in trip_masks[f]]
    outs = sorted({b for _, T in tri for b in range(64) if (T >> b) & 1 and (out_mask >> b) & 1})
    oidx = {b: k for k, b in enumerate(outs)}
    N = 1 + n + len(tri) + len(outs) + 1; snk = N - 1
    cap = defaultdict(int)
    for i in range(n): cap[(0, 1 + i)] = 2
    for k, (i, T) in enumerate(tri):
        cap[(1 + i, 1 + n + k)] = 1
        for b in outs:
            if (T >> b) & 1: cap[(1 + n + k, 1 + n + len(tri) + oidx[b])] = 1
    for b in outs: cap[(1 + n + len(tri) + oidx[b], snk)] = 1
    adj = defaultdict(set)
    for (a, b) in list(cap): adj[a].add(b); adj[b].add(a)
    flow = 0
    while True:
        prev = {0: None}; stack = [0]; found = False
        while stack and not found:
            u = stack.pop()
            for w in adj[u]:
                if w not in prev and cap[(u, w)] > 0:
                    prev[w] = u; stack.append(w)
                    if w == snk: found = True; break
        if not found: return flow
        w = snk
        while prev[w] is not None:
            u = prev[w]; cap[(u, w)] -= 1; cap[(w, u)] += 1; w = u
        flow += 1

def analyse(ori, node_cap):
    t0 = time.time()
    B = BOUNDARY[ori]
    out_mask = sum(1 << i for i in range(32, 64))
    trip = defaultdict(list)
    for i, j, k in itertools.combinations(range(64), 3):
        trip[B[i] ^ B[j] ^ B[k]].append((1 << i) | (1 << j) | (1 << k))
    fulls = sorted(v for v, ts in trip.items() if len(ts) == 3)
    line = {f: (trip[f][0] ^ trip[f][1], trip[f][0] ^ trip[f][2]) for f in fulls}
    supp = {f: trip[f][0] | trip[f][1] | trip[f][2] for f in fulls}
    assert all(popcount(supp[f]) == 9 for f in fulls)
    n_out_in_supp = Counter(popcount(supp[f] & out_mask) for f in fulls)
    w3 = sum(1 for f in fulls if popcount(f) == 3)
    print(f'{ori}: {len(fulls)} full values; outputs in supp(f) histogram {dict(sorted(n_out_in_supp.items()))}; weight-3 values {w3}; '
          f'per-value flow (outputs assignable, <=2): {dict(sorted(Counter(maxflow_outputs([f], trip, out_mask) for f in fulls).items()))}')
    # boundary element usage over all full triples
    use = Counter()
    for f in fulls:
        for T in trip[f]:
            for b in range(64):
                if (T >> b) & 1: use[b] += 1
    print(f'{ori}: boundary elements by number of full triples containing them: inputs {sorted(use[b] for b in range(32))}; outputs {sorted(use[b] for b in range(32, 64))}')
    # pairwise support overlaps of compatible pairs
    ov = Counter()
    for f, g in itertools.combinations(fulls, 2):
        bs = Basis(); ok = all(bs.add(v) for v in line[f] + line[g])
        if ok: ov[popcount(supp[f] & supp[g])] += 1
    print(f'{ori}: support overlap histogram over compatible pairs: {dict(sorted(ov.items()))}')
    # DFS over independent sets
    N = len(fulls); stats = defaultdict(Counter); count = Counter(); nodes = [0]; capped = [False]
    best_cover = defaultdict(int); min_X = defaultdict(lambda: 10 ** 9)
    mult = [0] * 64
    def rec(start, bs, chosen):
        nodes[0] += 1
        if nodes[0] > node_cap: capped[0] = True; return
        m = len(chosen)
        if m:
            cov = sum(1 for v in range(64) if mult[v]); X = sum(max(0, mult[v] - 2) for v in range(64))
            count[m] += 1
            best_cover[m] = max(best_cover[m], cov); min_X[m] = min(min_X[m], X)
            if m >= 5:
                fl = maxflow_outputs([fulls[i] for i in chosen], trip, out_mask)
                stats[m][(cov, X, fl >= 2 * m)] += 1
        for i in range(start, N):
            f = fulls[i]; t = bs.copy()
            if t.add(line[f][0]) and t.add(line[f][1]):
                for T in trip[f]:
                    for v in range(64):
                        if (T >> v) & 1: mult[v] += 1
                rec(i + 1, t, chosen + [i])
                for T in trip[f]:
                    for v in range(64):
                        if (T >> v) & 1: mult[v] -= 1
                if capped[0]: return
    rec(0, Basis(), [])
    status = 'CAPPED (lower bounds on counts only)' if capped[0] else 'COMPLETE'
    print(f'{ori}: DFS {status}, {nodes[0]} nodes, {time.time()-t0:.0f}s')
    res = {}
    for m in sorted(count):
        res[m] = dict(count=count[m], C=best_cover[m], Xmin=min_X[m])
        line_ = f'{ori}: m={m:2d}: independent sets {count[m]:9d}, max cover C(m) = {best_cover[m]:2d}, min excess X = {min_X[m]}'
        if m in stats:
            st = stats[m]
            ok = sum(c for (cov, X, fl), c in st.items() if fl)
            cov_ok = sorted({cov for (cov, X, fl) in st if fl}, reverse=True)[:1]
            # the best (max cover) among flow-feasible sets, and min X among flow-feasible with cover >= c
            line_ += f'; sets with flow >= 2m: {ok}; max cover among them {cov_ok}'
            res[m]['flow_ok'] = ok
            res[m]['table'] = {f'{cov},{X},{int(fl)}': c for (cov, X, fl), c in st.items()}
        print(line_, flush=True)
    json.dump(dict(ori=ori, complete=not capped[0], per_m=res), open(OUT/f'fullsets_{ori}.json', 'w'))
    return res

if __name__ == '__main__':
    oris = sys.argv[1].split(',') if len(sys.argv) > 1 else ['M', 'Mt']
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 3_000_000
    for o in oris: analyse(o, cap)
