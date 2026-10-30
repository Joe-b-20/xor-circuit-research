#!/usr/bin/env python3
"""Valid inequalities for the COMPLETE depth-3 model (model3.py).

Every inequality here is a THEOREM about depth-3 MixColumns circuits, so
adding them cannot raise the integer optimum; they only tighten the LP
relaxation (and hence the dual bound that we cite as the lower bound).
Each is justified in its docstring and each is checked against the verified
97-gate depth-3 circuit by control_cuts.py -- a cut violated by a real
depth-3 circuit would be UNSOUND and the bound VACUOUS.

Variables: x_e (e an edge = weight-2 mask), y_m (m a level-2 mask, wt 3 or 4).
A cut is returned as (list_of_x_edges, list_of_y_masks, rhs, kind) meaning
   sum_{e in list} x_e + sum_{m in list} y_m  >=  rhs        (kind='ge')
or with y-coefficients given explicitly for the 'agg' kind.
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import itertools
from model3 import pc, BITS

def sub_edges(m):
    b = BITS(m)
    return [ (1 << i) | (1 << j) for i, j in itertools.combinations(b, 2) ]


def cuts_building(L2):
    """C1/C2 -- a level-2 mask forces edges INSIDE it.

    wt(m)=4: m is the disjoint union of two selected edges e1,e2 subset m.
             Hence for every bit b of m, some selected edge inside m contains
             b:  sum_{e subset m, b in e} x_e  >=  y_m.
    wt(m)=3: m = input ^ edge with the edge inside m:
             sum_{e subset m} x_e  >=  y_m.
    """
    out = []
    for m in L2:
        es = sub_edges(m)
        if pc(m) == 4:
            for b in BITS(m):
                out.append(([e for e in es if (e >> b) & 1], [(m, -1)], 0))
        else:
            out.append((es, [(m, -1)], 0))
    return out


def cuts_target_l2(decomp, TARGETS):
    """C3 -- every target needs a level-2 parent; a weight-7 target needs two.

    Both parents of a target have weight <= 4 so two weight-<=2 parents give a
    value of weight <= 4 < 5 <= wt(t): at least one parent is a level-2 gate.
    For wt(t)=7 the split is forced to be {4,3} with both parts inside t, so
    BOTH parents are level-2 gates and they are distinct.
    """
    out = []
    for t in TARGETS:
        ms = set()
        for a, b in decomp[t]:
            for v in (a, b):
                if pc(v) >= 3:
                    ms.add(v)
        out.append(([], [(m, 1) for m in sorted(ms)], 2 if pc(t) == 7 else 1))
    return out


def cuts_w7_matching(TARGETS, edgeset):
    """C4/C5 -- a weight-7 target forces a 3-edge MATCHING inside itself.

    t = m4 ^ m3 with m4,m3 disjoint, inside t, of weights 4 and 3.
    m4 = e1 ^ e2 (disjoint edges inside m4 inside t); m3 = input ^ e3 with
    e3 inside m3 inside t.  e1,e2,e3 are pairwise disjoint and cover 6 of the
    7 bits of t.  Therefore for EVERY subset U of t,
        sum_{e subset t, e meets U} x_e  >=  ceil((|U|-1)/2)
    (the matching covers all but one bit of t, each of its edges meets U in at
    most 2 bits).  |U| = 7 gives the plain floor of 3.
    """
    out = []
    for t in TARGETS:
        if pc(t) != 7:
            continue
        inside = [e for e in sub_edges(t) if e in edgeset]
        for u in (2, 4, 6, 7):
            for U in itertools.combinations(BITS(t), u):
                Um = sum(1 << i for i in U)
                rhs = (u - 1 + 1) // 2
                out.append(([e for e in inside if e & Um], [], rhs))
    return out


def cuts_w5(TARGETS, edgeset):
    """C6 -- weight-5 targets.

    Decompositions of a weight-5 target t are {1,4}, {2,3} (both parents
    inside t) or {4,3} overlapping in one bit z outside t.
      - {1,4}: the weight-4 parent is two disjoint edges inside t.
      - {2,3}: an edge inside t plus a weight-3 mask inside t whose edge is
        also inside t -- two disjoint edges inside t.
      - {4,3} with z outside t: the weight-4 parent a = a3 | z splits into an
        edge {z, alpha} (alpha in t) and an edge inside t; so >= 1 edge inside
        t AND >= 1 edge with exactly one endpoint in t.
    Hence  A := sum_{e subset t} x_e  >= 1   and   A + B >= 2 where
    B := sum_{|e cap t| = 1} x_e.
    """
    out = []
    for t in TARGETS:
        if pc(t) != 5:
            continue
        A = [e for e in sub_edges(t) if e in edgeset]
        B = [e for e in edgeset if pc(e & t) == 1]
        out.append((A, [], 1))
        out.append((A + B, [], 2))
    return out


def cuts_aggregate_by_weight(decomp, TARGETS):
    """C7b -- C7 disaggregated over the two target weights.

    The 12 weight-7 targets need 24 level-2 parents, and a level-2 mask can
    parent at most deg7(m) of them; likewise the 20 weight-5 targets need 20.
    """
    from collections import defaultdict
    d7, d5 = defaultdict(set), defaultdict(set)
    for t in TARGETS:
        tgt = d7 if pc(t) == 7 else d5
        for a, b in decomp[t]:
            for v in (a, b):
                if pc(v) >= 3:
                    tgt[v].add(t)
    return [([], [(m, len(s)) for m, s in sorted(d7.items())], 24),
            ([], [(m, len(s)) for m, s in sorted(d5.items())], 20)]


def cut_aggregate_degree(decomp, TARGETS):
    """C7 -- aggregate level-2 demand.

    Each target needs 1 level-2 parent (2 if wt 7): 32 + 12 = 44 demands.
    A selected level-2 mask m can satisfy at most deg(m) of them, where
    deg(m) = #targets for which m occurs as a parent in some decomposition.
    Hence  sum_m deg(m) y_m >= 44.
    """
    from collections import defaultdict
    dg = defaultdict(set)
    for t in TARGETS:
        for a, b in decomp[t]:
            for v in (a, b):
                if pc(v) >= 3:
                    dg[v].add(t)
    return ([], [(m, len(s)) for m, s in sorted(dg.items())], 44)


# ---------------------------------------------------------------- level 2 --

def cuts_w7_bits(TARGETS, L2set):
    """C9/C10 -- bit-level demand inside a weight-7 target.

    Both parents of a weight-7 target are level-2 masks CONTAINED in t and
    they partition t (weights 4 and 3, disjoint).  Hence
      * for every bit i of t:  sum_{m subset t, i in m} y_m >= 1
      * summing over the 7 bits: sum_{m subset t} wt(m) y_m >= 7.
    """
    out = []
    for t in TARGETS:
        if pc(t) != 7:
            continue
        ins = [m for m in (sum(1 << i for i in c)
                           for k in (3, 4)
                           for c in itertools.combinations(BITS(t), k))
               if m in L2set]
        for i in BITS(t):
            out.append(([], [(m, 1) for m in ins if (m >> i) & 1], 1))
        out.append(([], [(m, pc(m)) for m in ins], 7))
    return out


def cuts_w7_global(TARGETS, L2set, edgeset):
    """C7c/C7d -- global Chvatal-Gomory counts driven by the weight-7 targets.

    24 level-2-parent demands, each satisfiable by a mask contained in at most
    n7(m) <= 2 weight-7 targets;  36 edge-slot demands (3 disjoint edges per
    weight-7 target), each satisfiable by an edge inside at most n7(e) <= 3
    weight-7 targets.  Hence
      sum_m n7(m) y_m >= 24  and  sum_m y_m >= 12   (over masks inside a wt-7 target)
      sum_e n7(e) x_e >= 36  and  sum_e x_e >= 12   (over edges inside a wt-7 target)
    """
    from collections import Counter
    n7m, n7e = Counter(), Counter()
    for t in TARGETS:
        if pc(t) != 7:
            continue
        for k in (2, 3, 4):
            for c in itertools.combinations(BITS(t), k):
                m = sum(1 << i for i in c)
                if k == 2:
                    if m in edgeset:
                        n7e[m] += 1
                elif m in L2set:
                    n7m[m] += 1
    out = [([], [(m, v) for m, v in sorted(n7m.items())], 24),
           ([], [(m, 1) for m in sorted(n7m)], 12),
           ([e for e, v in sorted(n7e.items()) for _ in range(v)], [], 36),
           (sorted(n7e), [], 12)]
    return out
