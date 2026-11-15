"""Level 2 of the GF(4)-norm (AD3) route with a bounded quadratic junk space.

Model (exact for functions, NOTES.md section 4): k2 products with operands in span(1, x, N);
J free x-quadratic forms j_1..j_J ("junk", to be produced by level 1 together with V_N);
require  T in span(L2) + span(j) + span(1, x, N)   (T = x^84 and N4 = x^85 coordinates).
Then level 1 must cover U = V_N + span(j): l1 = cover(U) (computed afterwards, cover1.py).
Products sorted lexicographically; junk vectors free (only their span matters).

usage: ad3j.py K2 J [--targets adj+n4] [--out FILE] [--cover] [--seed S]
"""
from __future__ import annotations

import argparse
import itertools
import json
import random
import time

from pysat.solvers import Solver

import cover1
from chm import CNF, lex_le
import ad3sat


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('k2', type=int); ap.add_argument('J', type=int)
    ap.add_argument('--targets', default='adj+n4')
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    ap.add_argument('--cover', action='store_true', help='then compute cover(V_N + junk) for k1 = 9..12')
    ap.add_argument('--block', default=None, help='jsonl of earlier solutions whose junk spaces are blocked (not used)')
    a = ap.parse_args()
    P = ad3sat.build(a.targets)
    q = P['q']
    f = CNF()
    k2, J = a.k2, a.J
    pairs1, pairs2 = P['pairs1'], P['pairs2']
    L2 = [([f.var() for _ in range(12)], [f.var() for _ in range(12)]) for _ in range(k2)]
    for j in range(k2 - 1): lex_le(f, L2[j][0] + L2[j][1], L2[j + 1][0] + L2[j + 1][1])
    W2 = [[f.xor2(f.and2(l[x], m[y]), f.and2(l[y], m[x])) for x, y in pairs2] for l, m in L2]
    Jv = [[f.var() for _ in range(len(pairs1))] for _ in range(J)]

    def image(w, ims):
        return [f.xor_list([w[i] for i in range(len(ims)) if (ims[i] >> r) & 1]) for r in range(q)]
    imgs = [image(w, P['im2']) for w in W2] + [image(w, P['im1']) for w in Jv]
    for t in P['T']:
        c = [f.var() for _ in range(len(imgs))]
        for r in range(q):
            v = f.xor_list([f.and2(c[j], imgs[j][r]) for j in range(len(imgs))])
            f.cl.append([v] if (t >> r) & 1 else [-v])
    t0 = time.time()
    with Solver(name=a.solver, bootstrap_with=f.cl) as s:
        ok = s.solve()
        model = set(l for l in s.get_model() if l > 0) if ok else None
    dt = time.time() - t0
    res = {'k2': k2, 'J': J, 'targets': a.targets, 'q': q, 'sat': ok, 'secs': round(dt, 1)}
    if ok:
        bits = lambda vs: sum(1 << i for i, v in enumerate(vs) if v in model)
        res['L2'] = [(bits(l), bits(m)) for l, m in L2]
        res['junk'] = [bits(v) for v in Jv]
        # junk wedge vectors in Lambda^2(8) coordinates = exactly the bit vectors (pairs1 order)
        U = [w for w in P['Nw']] + res['junk']
        res['dimU'] = len(cover1.rowspace(U))
        if a.cover:
            Ub = list(cover1.rowspace(U).values())
            for k1 in range(9, 13):
                prods, dt1 = cover1.solve(8, Ub, k1)
                res['cover%d' % k1] = (prods is not None, round(dt1, 1))
                if prods is not None:
                    res['L1'] = prods; break
    print(json.dumps(res), flush=True)
    if a.out:
        with open(a.out, 'a') as fh: fh.write(json.dumps(res) + '\n')


if __name__ == '__main__':
    main()
