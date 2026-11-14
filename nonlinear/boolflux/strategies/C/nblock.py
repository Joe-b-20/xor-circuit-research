"""n-block bound (NOTES.md section 4): least k such that k matrices of rank <= 2 in
M_{8x4}(GF(2)) span a space containing S = { y -> b*y : b in GF(256) }, y in GF(16) (the maps
K -> F of multiplication by b).  Exact SAT model, symmetry breaking: coefficient matrix
c = [I_8 | C'] (GL(8) on the target basis + column permutation), lex order on free columns.

Also usable for the variant where each product contributes a rank<=1 matrix (--rank 1),
which is the bilinear rank of the F x K -> F multiplication tensor.

usage: python3 nblock.py K [--rank 1|2] [--solver NAME]
"""
from __future__ import annotations

import argparse
import json
import time

import gf
import qmc


def target_mats():
    sp = gf.Span(); kb = []
    for v in gf.SUB16:
        if v and sp.add(v): kb.append(v)
    mats = []
    for i in range(8):
        b = 1 << i
        # matrix rows = 8 bits of F, cols = 4 basis elements of K
        cols = [gf.mul(b, y) for y in kb]
        mats.append([[(cols[c] >> r) & 1 for c in range(4)] for r in range(8)])
    return mats


def encode(k, rank=2, rows=8, cols=4, targets=None):
    T = targets or target_mats()
    m = len(T)
    f = qmc.CNF()
    terms = []
    for j in range(k):
        rk = []
        for _ in range(rank):
            rk.append((f.vars(rows), f.vars(cols)))
        terms.append(rk)
    C = [[f.var() for _ in range(k)] for _ in range(m)]
    # entries of Q_j
    Q = []
    for j in range(k):
        q = [[f.xor_list([f.and2(a[r], u[c]) for a, u in terms[j]]) for c in range(cols)]
             for r in range(rows)]
        Q.append(q)
    for o in range(m):
        for j in range(min(m, k)):
            f.fix(C[o][j], 1 if o == j else 0)
    for o in range(m):
        for r in range(rows):
            for c in range(cols):
                zs = [f.and2(C[o][j], Q[j][r][c]) for j in range(k)]
                f.fix(f.xor_list(zs), T[o][r][c])
    for j in range(m, k - 1):
        qmc.lex_le(f, terms[j][0][0] + terms[j][0][1], terms[j + 1][0][0] + terms[j + 1][0][1])
    return f


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('k', type=int)
    ap.add_argument('--rank', type=int, default=2)
    ap.add_argument('--solver', default='cadical153')
    a = ap.parse_args()
    f = encode(a.k, a.rank)
    ok, model, dt = qmc.solve(f, a.solver)
    print(json.dumps({'k': a.k, 'rank': a.rank, 'sat': ok, 'secs': round(dt, 1), 'vars': f.n,
                      'clauses': len(f.cl)}), flush=True)


if __name__ == '__main__':
    main()
