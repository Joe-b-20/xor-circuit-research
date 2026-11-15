"""P4: every 15-gate pre-inversion (10 product-merging gates + 5 injections) of the 103, through the
transposed product-part circuit, and its best timing.

A 10-gate product-part circuit is the transpose of a 5-gate circuit T computing the 9 product
columns (4-bit vectors over the targets t30..t33) from the 4 unit vectors; T's value set is
forced (the 5 non-unit columns), so only a few T realisations exist.  In the transposed
(multi-input XOR) view an injection is one more leaf at some node w, with reach = value(w).
For each T realisation, each top (value set + levels), each 5-injection solution X = R S with S in
Avail (all solutions), every node's XOR tree is arranged optimally for arrival time (join the two
earliest first); the targets' levels are compared with deadlines (required times of t30..t33 in
the reference at the given GD, inversion and bottom fixed).  Exact for 15-gate pre-inversions.

    python3 preT.py CIRC GD [--tops ref|gd32]
"""
import argparse
import heapq
import itertools
import json
import sys

import block
import circ
import preinj
import topenum


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('gd', type=int)
    ap.add_argument('--tops', default='ref')
    a = ap.parse_args()
    ref = circ.read(a.circ)
    s = circ.symbolic(ref)
    xs = {f'x{i}' for i in range(8)}
    xm = lambda at: sum(1 << int(t[1:]) for t in at if t[0] == 'x')
    prod = [f'a{i}' for i in range(1, 10)]
    names = ['t30', 't31', 't32', 't33']
    X = [xm(s[t][0]) for t in names]
    P = [sum(1 << i for i, p in enumerate(prod) if p in s[t][0]) for t in names]
    cols = [sum(1 << j for j in range(4) if (P[j] >> i) & 1) for i in range(9)]
    topn = {o for op, o, ins in ref if op != 'AND' and s[o][0] <= xs}
    pren = {o for op, o, ins in ref if op != 'AND' and o not in topn and s[o][0] <= xs | set(prod)}
    req = block.required([g for g in ref if g[1] not in topn | pren], a.gd)
    dl = [req[t] for t in names]
    # level-1 AND operands (x masks) per product
    ops = {}
    for op, o, ins in ref:
        if o in prod:
            ops[o] = [xm(s[i][0]) for i in ins]
    # tops
    gates, s2, forms, inj = topenum.top_spec(a.circ, 32)
    F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
    tops = []
    if a.tops == 'ref':
        L = block.levels_of(ref)
        lv = {xm(s[o][0]): L[o] for op, o, ins in ref if op != 'AND' and o in topn}
        lv.update({1 << i: 0 for i in range(8)})
        tops.append(('ref', lv))
    else:
        allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
        for hs in itertools.combinations(allv, 3):
            S = set(F) | set(hs)
            lv = topenum.closure_levels(S)
            if all(t in lv for t in S) and (a.tops == "all" or all(lv[t] <= d for t, d in F.items())):
                tops.append((hs, {v: lv[v] for v in S | {1 << i for i in range(8)}}))
    print(json.dumps(dict(deadlines=dl, tops=len(tops))), flush=True)
    units = [1, 2, 4, 8]
    nonunit = sorted({c for c in cols if c & (c - 1)})
    allvals = units + nonunit
    recipes = {v: [(x, v ^ x) for x in allvals if x < (v ^ x) and (v ^ x) in allvals] for v in nonunit}
    reals = []
    for choice in itertools.product(*[recipes[v] for v in nonunit]):
        dep = dict(zip(nonunit, choice))
        # acyclic
        st = {}

        def ok(v):
            if v in units:
                return True
            if st.get(v) == 1:
                return False
            if st.get(v) == 2:
                return True
            st[v] = 1
            r = all(ok(u) for u in dep[v])
            st[v] = 2
            return r
        if all(ok(v) for v in nonunit):
            reals.append(dep)
    print(json.dumps(dict(T_realisations=len(reals))), flush=True)
    best = None
    count = 0
    MINV = [99, 99, 99, 99]
    reach_vals = sorted(set(allvals))
    for tname, lv in tops:
        avail = set(lv)
        arr_a = {p: 1 + max(lv[o] for o in ops[p]) for p in prod}
        av = sorted(avail)
        # all 5-point solutions: multisets of reach values, S in Avail
        sols = []
        for B in itertools.combinations_with_replacement(reach_vals, 5):
            if preinj.rank(list(B)) < 4:
                continue
            basis = []
            for i in range(5):
                if preinj.rank([B[j] for j in basis] + [B[i]]) > len(basis):
                    basis.append(i)
            free = [i for i in range(5) if i not in basis]
            Bb = [B[i] for i in basis]
            s0 = preinj.solve_basis(Bb, list(X), 4)
            if s0 is None:
                continue
            cs = [preinj.solve_basis(Bb, [(B[f] >> j) & 1 for j in range(4)], 4) for f in free]
            for fv in itertools.product(av, repeat=len(free)):
                Sv = [0] * 5
                good = True
                for idx, p in enumerate(basis):
                    v = s0[idx]
                    for c, w in zip(cs, fv):
                        if c[idx]:
                            v ^= w
                    if v not in avail:
                        good = False
                        break
                    Sv[p] = v
                if not good:
                    continue
                for f, w in zip(free, fv):
                    Sv[f] = w
                sols.append((B, Sv))
        for dep in reals:
            readers = {v: [] for v in allvals}
            for v, (x1, x2) in dep.items():
                readers[x1].append(v)
                readers[x2].append(v)
            # T topological order: units first then nonunit by dependency
            order = []
            seen = set()

            def visit(v):
                if v in seen:
                    return
                seen.add(v)
                if v in dep:
                    for u in dep[v]:
                        visit(u)
                order.append(v)
            for v in allvals:
                visit(v)
            atoms_at = {v: [p for i, p in enumerate(prod) if cols[i] == v] for v in allvals}
            for B, Sv in sols:
                inj_at = {v: [] for v in allvals}
                for r, sv in zip(B, Sv):
                    inj_at[r].append(lv[sv])
                Sarr = {}
                for w in reversed(order):        # T consumers first = original producers first
                    inc = [arr_a[p] for p in atoms_at[w]] + inj_at[w] + [Sarr[r] for r in readers[w]]
                    hq = list(inc)
                    heapq.heapify(hq)
                    while len(hq) > 1:
                        x1 = heapq.heappop(hq)
                        x2 = heapq.heappop(hq)
                        heapq.heappush(hq, max(x1, x2) + 1)
                    Sarr[w] = hq[0] if hq else None
                tl = [Sarr[u] for u in units]
                count += 1
                late = max(t - d for t, d in zip(tl, dl))
                MINV[:] = [min(a, b) for a, b in zip(MINV, tl)]
                if best is None or late < best[0]:
                    best = (late, tname if isinstance(tname, str) else list(tname), B, Sv, tl)
    print(json.dumps(dict(elementwise_min_target_levels=MINV)), flush=True)
    print(json.dumps(dict(evaluated=count, best_lateness=best[0] if best else None,
                          best=dict(top=best[1], reach=list(best[2]), inj=best[3], target_levels=best[4]) if best else None,
                          deadlines=dl)), flush=True)


if __name__ == '__main__':
    main()
