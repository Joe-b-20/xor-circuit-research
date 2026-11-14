"""Subspace cover by rank-2 alternating forms on F_2^8 (stage-1 problems).

Least l such that l products of x-linear forms span (mod affine) a given space U of quadratic
forms. Symmetry breaking (sound for a subspace cover): coefficient matrix c = [I_d | C'] for a
basis of U (GL(d) on the basis, column permutation), lex order on free columns, nonzero products.

  python3 cover.py --l 9 --a28-junk        U = V_N + span(junk residuals of the A28 last layer)
  python3 cover.py --l 9 --forms FILE      U given as JSON list of 28-bit alternating forms
"""
from __future__ import annotations

import argparse
import itertools
import json

import qmc

PAIRS = list(itertools.combinations(range(8), 2))


def encode(l, U):
    d = len(U)
    f = qmc.CNF()
    L = [f.vars(8) for _ in range(l)]; M = [f.vars(8) for _ in range(l)]
    W = [[f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a])) for a, b in PAIRS]
         for j in range(l)]
    C = [[f.var() for _ in range(l)] for _ in range(d)]
    for s in range(d):
        for r in range(28):
            f.fix(f.xor_list([f.and2(C[s][j], W[j][r]) for j in range(l)]), (U[s] >> r) & 1)
    for j in range(l):
        f.cl.append([W[j][r] for r in range(28)])
    for j in range(l - 1):   # c free: products fully interchangeable (sound)
        qmc.lex_le(f, L[j], L[j + 1])
    return f, L, M


def a28_junk_space(gamma='17', g0='hard', member_tabs=None):
    import wsat
    from kj_search import Model, AD5
    from fam_check import gp
    from structure import analyse
    M = Model(None if gamma == 'none' else gp(int(gamma)), g0)
    if member_tabs is None:
        c, ands, outs, tt = analyse(AD5)
        top = max(A['level'] for A in ands)
        member_tabs = [A['tab'] for A in ands if A['level'] == top]
    ok, res, kj, _ = wsat.residuals(M, member_tabs)
    assert ok
    sp = wsat.quad_form_coords(M)
    rho = wsat.to_forms(sp, res); kap = wsat.to_forms(sp, kj)
    Nf = wsat.n_forms()
    # basis of V_N + span(rho)  (kernel junk kap also free: include as optional? keep exact: kap empty
    # case only)
    if kap:
        raise SystemExit('kernel junk nonempty: use wsat.py')
    basis = []; sp2 = qmc.Normal([])
    import gf
    S = gf.Span()
    for v in Nf + rho:
        if S.add(v): basis.append(v)
    return basis


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--a28-junk', action='store_true')
    ap.add_argument('--forms', default=None)
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    if a.a28_junk:
        U = a28_junk_space()
    else:
        U = json.load(open(a.forms))
    f, L, M = encode(a.l, U)
    info = {'l': a.l, 'dimU': len(U), 'vars': f.n, 'clauses': len(f.cl)}
    print(json.dumps(info), flush=True)
    ok, model, dt = qmc.solve(f, a.solver)
    info.update(sat=ok, secs=round(dt, 1))
    if ok:
        val = set(v for v in model if v > 0)
        info['W'] = [[[1 if v in val else 0 for v in L[j]], [1 if v in val else 0 for v in M[j]]]
                     for j in range(a.l)]
    print(json.dumps(info), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps(info))


if __name__ == '__main__':
    main()
