#!/usr/bin/env python3
"""Staircase = generalized Hamming weights of the output-usage code (Z1, 2026-11-15).

For a circuit whose ANDs g_1..g_A are independent of {1, x} and of each other, every output
combination c has a unique expansion; supp(c) = the ANDs it reads, closure = dependency closure.
E = ANDs in the closure of EVERY nonzero output combination (the common core).
L = the other ANDs.  If no AND of L is an ancestor of another AND of L ("L is a sink layer"), then
closure(supp(C)) = E + union of supp_L(c) for c in C, so

    m_k = |E| + d_k(Code),   Code = row space of the 8 x |L| output-usage matrix M,

d_k = k-th generalized Hamming weight (Wei).  waste = m_8 - m_1 - 7 = |L| - d_1 - 7 (when every L
member is read by some output).  This script checks the identity against staircase.py and prints
the code structure: weight distribution, matroid flats f(r) = max #columns of rank r, parallel
classes, connected components (direct-sum blocks).

Usage: staircode.py FILE...  (json per line)
"""
import sys, json
from itertools import combinations
from pathlib import Path
sys.path.insert(0, '/home/joebachir20/xs-campaigns/2026-11-15-study/staircase')
import staircase as sc


def rank_cols(cols):
    """GF(2) rank of a list of int column vectors."""
    basis = []
    for v in cols:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def core_and_code(path):
    ins, outs, gates = sc.parse(path)
    val, ands = sc.evaluate(ins, outs, gates)
    A = len(ands)
    B = sc.Basis()
    gens = [sc.ALL] + [val[n] for n in ins] + [val[o] for o, _, _ in ands]
    if not all(B.add(v, 1 << i) for i, v in enumerate(gens)):
        raise ValueError('dependent ANDs')

    def gsupp(v):
        r, c = B.reduce(v)
        assert r == 0
        return c >> 9
    out_s = [gsupp(val[o]) for o in outs]
    parents = [gsupp(val[a]) | gsupp(val[b]) for _, a, b in ands]
    anc = [0] * A
    for j in range(A):
        m = 1 << j
        p = parents[j]
        while p:
            i = (p & -p).bit_length() - 1
            p &= p - 1
            m |= anc[i]
        anc[j] = m

    def closure(mask):
        m = 0
        while mask:
            i = (mask & -mask).bit_length() - 1
            mask &= mask - 1
            m |= anc[i]
        return m

    def csupp(c):
        s = 0
        for b in range(8):
            if (c >> b) & 1:
                s ^= out_s[b]
        return s
    core = (1 << A) - 1
    for c in range(1, 256):
        core &= closure(csupp(c))
    Lidx = [j for j in range(A) if not (core >> j) & 1]
    # sink test: no L member is a strict ancestor of another L member
    sink = all(not ((anc[j] >> i) & 1) for j in Lidx for i in Lidx if i != j)
    # M columns: column j = 8-bit vector of outputs reading L member j
    cols = []
    for j in Lidx:
        v = 0
        for b in range(8):
            if (out_s[b] >> j) & 1:
                v |= 1 << b
        cols.append(v)
    # AND levels
    lvl = []
    for j in range(A):
        p = parents[j]
        L = 1
        while p:
            i = (p & -p).bit_length() - 1
            p &= p - 1
            L = max(L, lvl[i] + 1)
        lvl.append(L)
    return dict(A=A, E=bin(core).count('1'), Lidx=Lidx, cols=cols, sink=sink, lvl=lvl,
                ands=ands, out_s=out_s, parents=parents, anc=anc, closure=closure, csupp=csupp,
                val=val, ins=ins, outs=outs)


def code_profile(cols):
    """Generalized Hamming weights, weight distribution, flats, parallel classes, blocks."""
    n = len(cols)
    # codeword of c: bit j set iff <c, col_j> = 1
    def cw(c):
        w = 0
        for j, v in enumerate(cols):
            if bin(c & v).count('1') & 1:
                w |= 1 << j
        return w
    words = {c: cw(c) for c in range(1, 256)}
    wdist = {}
    for c, w in words.items():
        k = bin(w).count('1')
        wdist[k] = wdist.get(k, 0) + 1
    d = []
    for k in range(1, 9):
        best = None
        for basis in sc.subspaces(k):
            u = 0
            for v in basis:
                u |= words[v]
            t = bin(u).count('1')
            if best is None or t < best:
                best = t
        d.append(best)
    # flats: f(r) = n - d_{8-r}  (r = 0..7), f(8) = n
    par = {}
    for j, v in enumerate(cols):
        par.setdefault(v, []).append(j)
    parallel = sorted([len(x) for x in par.values()], reverse=True)
    # connected components of the binary matroid: j ~ j' if some circuit contains both.
    # Use: matroid is a direct sum of blocks B iff rank(cols) = sum rank(B). Greedy refine.
    comps = [[j] for j in range(n)]
    R = rank_cols(cols)
    changed = True
    while changed:
        changed = False
        for a in range(len(comps)):
            for b in range(a + 1, len(comps)):
                ra = rank_cols([cols[j] for j in comps[a]])
                rb = rank_cols([cols[j] for j in comps[b]])
                rab = rank_cols([cols[j] for j in comps[a] + comps[b]])
                if rab < ra + rb:
                    comps[a] = comps[a] + comps[b]
                    del comps[b]
                    changed = True
                    break
            if changed:
                break
    blocks = sorted([(len(cmp), rank_cols([cols[j] for j in cmp])) for cmp in comps], reverse=True)
    return dict(n=n, rank=R, d=d, wdist=dict(sorted(wdist.items())), parallel=parallel,
                blocks=blocks)


def analyse(path):
    r = core_and_code(path)
    prof = code_profile(r['cols'])
    m_pred = [r['E'] + x for x in prof['d']]
    lv = r['lvl']
    per = [sum(1 for x in lv if x == L) for L in range(1, max(lv) + 1)]
    Llv = sorted(set(lv[j] for j in r['Lidx']))
    return dict(file=Path(path).name, A=r['A'], and_levels=per, E=r['E'], nL=len(r['Lidx']),
                L_levels=Llv, sink=r['sink'], m_pred=m_pred, **prof,
                waste=prof['d'][7] - prof['d'][0] - 7)


if __name__ == '__main__':
    args = sys.argv[1:]
    check = False
    if args and args[0] == '--check':
        check = True
        args = args[1:]
    for p in args:
        try:
            out = analyse(p)
            if check:
                m = sc.analyse(p)['m']
                out['m_staircase'] = m
                out['identity_ok'] = (m == out['m_pred'])
        except Exception as e:
            out = dict(file=Path(p).name, error=repr(e))
        print(json.dumps(out), flush=True)
