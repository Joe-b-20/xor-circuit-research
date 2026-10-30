#!/usr/bin/env python3
"""Single source of truth for the strengthened depth-3 LP.

build() returns
  rows : list of (list[(var_index, int_coef)], int_rhs, tag)   meaning  >= rhs
  cost : list of int, length nvar   (1 on the x/y variables, 0 elsewhere)
  meta : dict with the index maps

Every row is a valid inequality for the complete depth-3 model, i.e. a
theorem about depth-3 MixColumns circuits; control_lp.py checks all of them
against the verified 97-gate depth-3 circuit.
All coefficients are integers, so an exact rational dual certificate is
possible (certify.py).
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sys, itertools
from mcmatrix import TARGETS
from model3 import candidates, buildings, pc, BITS
import cuts as CUT


def build(use_cuts=True, level=1):
    decomp, L2, E = candidates()
    Eset = set(E)
    xi = {e: i for i, e in enumerate(E)}
    yi = {m: len(E) + i for i, m in enumerate(L2)}
    base = len(E) + len(L2)
    zi, n = {}, 0
    for t in TARGETS:
        for k in range(len(decomp[t])):
            zi[(t, k)] = base + n; n += 1
    wbase = base + n
    wi, nw = {}, 0
    for m in L2:
        if pc(m) == 4:
            for j in range(3):
                wi[(m, j)] = wbase + nw; nw += 1
    nvar = wbase + nw
    rows = []

    def add(terms, rhs, tag):
        rows.append((terms, rhs, tag))

    # ---- exact model -------------------------------------------------
    for t in TARGETS:
        add([(zi[(t, k)], 1) for k in range(len(decomp[t]))], 1, 'cover')
    for t in TARGETS:
        for k, (a, b) in enumerate(decomp[t]):
            for v in (a, b):
                if pc(v) == 1:
                    continue            # a plain input costs nothing
                j = xi[v] if pc(v) == 2 else yi[v]
                add([(j, 1), (zi[(t, k)], -1)], 0, 'zparent')
    for m in L2:
        if pc(m) == 4:
            add([(wi[(m, j)], 1) for j in range(3)] + [(yi[m], -1)], 0, 'wbuild')
            for j, (e1, e2) in enumerate(buildings(m)):
                for e in (e1, e2):
                    add([(xi[e], 1), (wi[(m, j)], -1)], 0, 'wedge')
        else:
            add([(xi[m ^ (1 << b)], 1) for b in BITS(m)] + [(yi[m], -1)], 0, 'build3')
    if not use_cuts:
        return rows, [1] * base + [0] * (nvar - base), dict(
            xi=xi, yi=yi, zi=zi, wi=wi, nvar=nvar, base=base, E=E, L2=L2, decomp=decomp)

    # ---- valid inequalities ------------------------------------------
    for xs, ys, b in CUT.cuts_building(L2):
        add([(xi[e], 1) for e in xs] + [(yi[m], c) for m, c in ys], b, 'C1')
    for xs, ys, b in CUT.cuts_target_l2(decomp, TARGETS):
        add([(yi[m], c) for m, c in ys], b, 'C3')
    for xs, ys, b in CUT.cuts_w7_matching(TARGETS, Eset):
        add([(xi[e], 1) for e in xs], b, 'C4C5')
    for xs, ys, b in CUT.cuts_w5(TARGETS, Eset):
        add([(xi[e], 1) for e in xs], b, 'C6')
    xs, ys, b = CUT.cut_aggregate_degree(decomp, TARGETS)
    add([(yi[m], c) for m, c in ys], b, 'C7')
    for xs, ys, b in CUT.cuts_aggregate_by_weight(decomp, TARGETS):
        add([(yi[m], c) for m, c in ys], b, 'C7b')
    for t in TARGETS:
        if pc(t) != 5:
            continue
        ov = [k for k, (a, b_) in enumerate(decomp[t]) if pc(a) + pc(b_) > pc(t)]
        add([(xi[e], 1) for e in CUT.sub_edges(t) if e in Eset]
            + [(zi[(t, k)], 1) for k in ov], 2, 'C8')
    if level >= 2:
        L2set = set(L2)
        for xs, ys, b in CUT.cuts_w7_bits(TARGETS, L2set):
            add([(yi[m], c) for m, c in ys], b, 'C9C10')
        for xs, ys, b in CUT.cuts_w7_global(TARGETS, L2set, Eset):
            add([(xi[e], 1) for e in xs] + [(yi[m], c) for m, c in ys], b, 'C7cd')
    if level >= 3:
        # ---- weight-5 REGIME cuts -------------------------------------
        # A weight-5 target t is decomposed either
        #   (N) {1,4} or {2,3}: both parents inside t -> >=2 disjoint edges
        #       inside t AND >=1 level-2 mask inside t;   or
        #   (O) {4,3} overlapping in a bit z outside t: BOTH parents are
        #       level-2 masks and BOTH contain z.
        # With S_O = sum_{k in OV} z_{t,k}:
        #   (b) sum_{m subset t} y_m + S_O >= 1
        #   (c) sum_{m in P2(t)} y_m >= 1 + z_{t,k}      for each k in OV
        #   (e) sum_{m: z in m} y_m >= 2 z_{t,k}         for each k in OV, z its
        #                                                overlap bit
        L2set = set(L2)
        by_bit = {}
        for m in L2:
            for i in BITS(m):
                by_bit.setdefault(i, []).append(m)
        for t in TARGETS:
            if pc(t) != 5:
                continue
            ov = [k for k, (a, b_) in enumerate(decomp[t]) if pc(a) + pc(b_) > pc(t)]
            ins = [m for m in (sum(1 << i for i in c)
                               for k in (3, 4)
                               for c in itertools.combinations(BITS(t), k))
                   if m in L2set]
            P2 = sorted({v for a, b_ in decomp[t] for v in (a, b_) if pc(v) >= 3})
            add([(yi[m], 1) for m in ins] + [(zi[(t, k)], 1) for k in ov], 1, 'W5b')
            for k in ov:
                a, b_ = decomp[t][k]
                zbit = BITS(a & b_)[0]
                add([(yi[m], 1) for m in P2] + [(zi[(t, k)], -1)], 1, 'W5c')
                add([(yi[m], 1) for m in by_bit[zbit]] + [(zi[(t, k)], -2)], 0, 'W5e')
    if level >= 4:
        # ---- NO-WASTE constraints (valid at the optimum) ---------------
        # A selected level-2 mask that is not the parent of any chosen target
        # decomposition can be deleted, strictly lowering the cost; likewise a
        # selected edge that neither builds a selected level-2 mask nor is a
        # target parent.  So SOME optimal solution satisfies
        #    y_m  <= sum_{(t,k): m is a parent of decomposition k of t} z_{t,k}
        #    x_e  <= sum_{(m,j): e in matching j of m} w_{m,j}
        #            + sum_{(t,k): e is a parent} z_{t,k}
        #            + sum_{m wt3 : e = m minus one bit} y_m
        # and a lower bound for that solution is a lower bound for all.
        useY = {}
        useX = {}
        for t in TARGETS:
            for k, (a, b_) in enumerate(decomp[t]):
                for v in (a, b_):
                    if pc(v) >= 3:
                        useY.setdefault(v, []).append(zi[(t, k)])
                    elif pc(v) == 2:
                        useX.setdefault(v, []).append(zi[(t, k)])
        for m in L2:
            if pc(m) == 4:
                for j, (e1, e2) in enumerate(buildings(m)):
                    for e in (e1, e2):
                        useX.setdefault(e, []).append(wi[(m, j)])
            else:
                for bb in BITS(m):
                    useX.setdefault(m ^ (1 << bb), []).append(yi[m])
        for m in L2:
            add([(j, 1) for j in useY.get(m, [])] + [(yi[m], -1)], 0, 'NWy')
        for e in E:
            add([(j, 1) for j in useX.get(e, [])] + [(xi[e], -1)], 0, 'NWx')
    cost = [1] * base + [0] * (nvar - base)
    return rows, cost, dict(xi=xi, yi=yi, zi=zi, wi=wi, nvar=nvar, base=base,
                            E=E, L2=L2, decomp=decomp)


def control_point(meta):
    """The verified 97-gate depth-3 circuit as a feasible point of the LP."""
    import json
    from control_primal import masks_and_depths, CIRC
    g = json.load(open(CIRC))['gates']
    sig, dep = masks_and_depths(g)
    p = [0] * meta['nvar']
    X, Y = set(), set()
    for k in range(len(g)):
        m, d = sig[32 + k], dep[32 + k]
        if d == 1:
            X.add(m); p[meta['xi'][m]] = 1
        elif d == 2:
            Y.add(m); p[meta['yi'][m]] = 1
    for (t, k), j in meta['zi'].items():
        a, b = meta['decomp'][t][k]
        ok = all(True if pc(v) == 1 else ((v in X) if pc(v) == 2 else (v in Y)) for v in (a, b))
        if ok:
            p[j] = 1
    for (m, jj), j in meta['wi'].items():
        e1, e2 = buildings(m)[jj]
        if e1 in X and e2 in X:
            p[j] = 1
    return p
