"""P4: every minimum (25-gate) bottom of the 103, through its transposed circuit, and the best
achievable output timing for the 103's product arrival times.

Transposed circuit T: inputs e_0..e_7 (one per output y_j), its node values must be exactly the 14
non-unit columns + the unique helper (see NOTES 2.3); each T-gate value v = a ^ b for a pair of
earlier values.  The original (transpose of T): for each T-node w, S_w = XOR of the products whose
column is w and of S_r for every T-gate r reading w; y_j = S_{e_j}.  A node with f incoming
signals costs f - 1 XOR gates, arranged as any binary tree; for a minimum arrival time the
optimal tree repeatedly joins the two earliest signals (Huffman with max-plus, unit delay).
Every 25-gate bottom arises this way (transposition is a bijection on XOR circuits without dead
nodes), so the minimum over T realisations of the latest output is exact for 25-gate bottoms.

    python3 bottomT.py CIRC [--write OUT.circ.txt]   (writes the best re-timed full circuit)
"""
import argparse
import heapq
import itertools
import json
import sys

import block
import circ


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('--write', default=None)
    ap.add_argument('--gd', type=int, default=32)
    a = ap.parse_args()
    ref = circ.read(a.circ)
    s = circ.symbolic(ref)
    used = set()
    for op, o, ins in ref:
        if op == 'AND':
            for i in ins:
                used |= s[i][0]
    outprod = [o for op, o, ins in ref if op == 'AND' and o not in used]
    ys = [f'y{j}' for j in range(8)]
    col = {p: sum(1 << j for j, y in enumerate(ys) if p in s[y][0]) for p in outprod}
    L = block.levels_of(ref)
    arr = {p: L[p] for p in outprod}
    values = sorted({c for c in col.values() if c & (c - 1)})
    units = [1 << j for j in range(8)]
    # helper(s): minimal value sets = values + H helpers; find all helper sets with H = 1
    def closed(S):
        have = set(units)
        prog = True
        while prog:
            prog = False
            for t in S:
                if t not in have and any((t ^ x) in have for x in have):
                    have.add(t)
                    prog = True
        return set(S) <= have
    helpers = [h for h in range(1, 256) if h & (h - 1) and h not in values and closed(values + [h])]
    print(json.dumps(dict(values=len(values), helper_sets=[[h] for h in helpers])), flush=True)
    best = None
    nreal = 0
    for h in helpers:
        V = values + [h]
        allv = units + V
        # recipes per value
        rec = {v: [(x, v ^ x) for x in allv if x < (v ^ x) and (v ^ x) in allv] for v in V}
        order_vals = V
        for choice in itertools.product(*[rec[v] for v in order_vals]):
            dep = {v: set(p) for v, p in zip(order_vals, choice)}
            # acyclic?
            state = {}
            ok = True

            def visit(v):
                if v in units:
                    return True
                st = state.get(v)
                if st == 1:
                    return False
                if st == 2:
                    return True
                state[v] = 1
                for u in dep[v]:
                    if not visit(u):
                        return False
                state[v] = 2
                return True
            for v in V:
                if not visit(v):
                    ok = False
                    break
            if not ok:
                continue
            nreal += 1
            # reverse topological order of T (consumers first)
            topo = []
            seen = set()

            def topo_visit(v):
                if v in seen:
                    return
                seen.add(v)
                if v not in units:
                    for u in dep[v]:
                        topo_visit(u)
                topo.append(v)
            for v in V:
                topo_visit(v)
            for u in units:
                if u not in seen:
                    topo.append(u)
            readers = {x: [] for x in allv}
            for v in V:
                for u in dep[v]:
                    readers[u].append(v)
            prods_at = {x: [p for p in outprod if col[p] == x] for x in allv}
            S = {}
            for w in reversed(topo):     # consumers (late in T) first
                inc = [arr[p] for p in prods_at[w]] + [S[r] for r in readers[w]]
                if not inc:
                    S[w] = None
                    continue
                hq = list(inc)
                heapq.heapify(hq)
                while len(hq) > 1:
                    x1 = heapq.heappop(hq)
                    x2 = heapq.heappop(hq)
                    heapq.heappush(hq, max(x1, x2) + 1)
                S[w] = hq[0]
            outl = [S[1 << j] for j in range(8)]
            m = max(outl)
            if best is None or m < best[0]:
                best = (m, choice, outl, h)
    print(json.dumps(dict(realisations=nreal, best_max_output_level=best[0] if best else None,
                          best_output_levels=best[2] if best else None, ref_output_levels=[L[y] for y in ys])), flush=True)


if __name__ == '__main__':
    main()
