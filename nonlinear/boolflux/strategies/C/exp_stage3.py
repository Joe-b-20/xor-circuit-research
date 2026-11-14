"""Stage-3 cover experiments: given the signals of a circuit before its last AND layer (E),
find k products of operands in span(O) covering x^-1 modulo E.

usage: python3 exp_stage3.py --e FILE[:levels] [--e2 FILE:ands] --ops xNn|E --k K [--solver S]
  --e  A28 file; E = 1, x, all ANDs below the last AND level
  --stage1 FILE   take level-1 ANDs from this file instead (needs --inv)
  --inv FILE      take the ANDs strictly between level 1 and the last level from this file
"""
from __future__ import annotations

import argparse
import json
import sys
import time

import gf
import qmc
from structure import analyse


def tables_of(path):
    c, ands, outs, tabs = analyse(path)
    top = max(A['level'] for A in ands)
    lvl1 = [A['tab'] for A in ands if A['level'] == 1]
    mid = [A['tab'] for A in ands if 1 < A['level'] < top]
    return lvl1, mid


def coords(B, t):
    sp = gf.Span()
    for i, b in enumerate(B): sp.add(b, 1 << i)
    r, tag = sp.reduce(t, 0)
    assert r == 0
    return [(tag >> i) & 1 for i in range(len(B))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage1', required=True)
    ap.add_argument('--inv', default=None)
    ap.add_argument('--ops', default='xNn')
    ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--nosym', action='store_true')
    ap.add_argument('--fix', type=int, default=0, help='fix this many products to the --stage1 file last-layer ones')
    ap.add_argument('--drop1', type=int, default=-1, help='drop this level-1 AND (0-based)')
    a = ap.parse_args()
    l1, mid = tables_of(a.stage1)
    if a.inv: _, mid = tables_of(a.inv)
    if a.drop1 >= 0: l1 = l1[:a.drop1] + l1[a.drop1 + 1:]
    N = [gf.power(p, 17) for p in range(256)]
    n = [gf.INV[v] for v in N]
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    Nt = gf.coord_tables(N, basis); nt = gf.coord_tables(n, basis)
    T = gf.coord_tables(gf.INV)
    E = [gf.ONES] + gf.X + l1 + mid
    En = qmc.Normal(E)
    info = {'stage1': a.stage1, 'inv': a.inv, 'n_l1': len(l1), 'n_mid': len(mid),
            'dimE': En.dim(), 'N_in_E': [En.nf(t) == 0 for t in Nt],
            'n_in_E': [En.nf(t) == 0 for t in nt]}
    Tq = qmc.Normal([En.nf(t) for t in T])
    info['dim_T_mod_E'] = Tq.dim()
    if a.ops == 'xNn':
        O = gf.X + Nt + nt
    elif a.ops == 'xn':
        O = gf.X + nt
    elif a.ops == 'xN':
        O = gf.X + Nt
    elif a.ops == 'E':
        O = gf.X + l1 + mid
    else:
        raise SystemExit('ops')
    info['ops'] = a.ops; info['d'] = len(O)
    info['O_in_E'] = all(En.nf(t) == 0 for t in O)
    if a.k == 0:
        pairs, phic, tco, q, _ = qmc.build_phi(O, E, T)
        info['q'] = q
        print(json.dumps({k: v for k, v in info.items() if k not in ('stage1', 'inv')}))
        return
    t0 = time.time()
    f, LMC, meta = qmc.encode(O, E, T, a.k, symbreak=not a.nosym and a.fix == 0)
    if a.fix:
        c_, ands_, _, _ = analyse(a.stage1)
        top = max(A['level'] for A in ands_)
        last = [A for A in ands_ if A['level'] == top]
        L, M, C = LMC
        for j, A in enumerate(last[:a.fix]):
            for side, V in (('Ltab', L[j]), ('Rtab', M[j])):
                co = coords([gf.ONES] + O, A[side])[1:]
                for b, v in enumerate(co): f.fix(V[b], v)
    info.update(meta); info['k'] = a.k; info['encode_s'] = round(time.time() - t0, 1)
    print(json.dumps(info), flush=True)
    ok, model, dt = qmc.solve(f, a.solver)
    info['sat'] = ok; info['solve_s'] = round(dt, 1)
    if ok:
        prods, cmat = qmc.decode(model, LMC, O)
        info['verified'] = qmc.check(prods, cmat, O, E, T)
        info['prods'] = [[''.join(map(str, l)), ''.join(map(str, m))] for l, m in prods]
        info['c'] = [''.join(map(str, r)) for r in cmat]
    print(json.dumps(info), flush=True)


if __name__ == '__main__':
    main()
