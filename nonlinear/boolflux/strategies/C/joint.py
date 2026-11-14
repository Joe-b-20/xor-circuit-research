"""Joint exact SAT: l level-1 products (any x-linear forms) + k last-layer GF(4)-norm members,
with the GF(16) inversion fixed (the 5 inversion ANDs of the AD5 file, as functions of N).

(a) N's 4 quadratic forms lie in span of the level-1 wedges (mod affine);
(b) every bit of x^-1 lies in span(level-1 products, members) + E_min,
    E_min = span(1, x, N coords, n coords, inversion ANDs).
Given (a), (b) is exactly the circuit condition (inversion operands are functions of N in E).
Symmetry breaking: lex order of level-1 first operands, lex order of member first operands
(both sound: products within a group are interchangeable; c is free).
A SAT answer with l + k = 22 is a 27-AND circuit (l + 5 + k), built by build27.py.

usage: python3 joint.py --l 9 --k 13 [--gamma 17|none] [--out FILE] [--a28-check]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import qmc
from exp_stage3 import tables_of
from fam_sat import build_O
from fam_check import gp
from structure import analyse

AD5 = '/home/joebachir20/xcr-boolflux/nonlinear/nist/aes-sbox/aes-sbox-a28-ad5-g124-gd27-xx96-26.circ.txt'
PAIRS8 = list(itertools.combinations(range(8), 2))


def setup(gamma):
    O, omega = build_O(gamma, False)        # X (8) + w coords (4)
    N = [gf.power(p, 17) for p in range(256)]
    n = [gf.INV[v] for v in N]
    sp = gf.Span(); kb = []
    for v in gf.SUB16:
        if v and sp.add(v): kb.append(v)
    Nt = gf.coord_tables(N, kb); nt = gf.coord_tables(n, kb)
    _, inv = tables_of(AD5)
    Emin = [gf.ONES] + gf.X + Nt + nt + inv
    T = [gf.bit_table(gf.INV, kk) for kk in range(8)]
    Nforms = [gf.anf_quadratic_part(t) for t in Nt]
    return O, omega, Emin, T, Nforms


def encode(l, k, gamma, fix_members=None, fix_l1=None):
    O, omega, Emin, T, Nforms = setup(gamma)
    pairs, phic, tco, q, Ef = qmc.build_phi(O, Emin, T)
    d = len(O)
    f = qmc.CNF()
    Z = qmc._zero(f)
    # level-1: x part free, w part zero
    L1 = []; M1 = []
    for _ in range(l):
        a = f.vars(8); b = f.vars(8)
        L1.append(a + [Z] * (d - 8)); M1.append(b + [Z] * (d - 8))
    L2 = [f.vars(d) for _ in range(k)]
    M2 = [[f.xor_list([L2[j][c] for c in range(d) if omega[b][c]]) or Z for b in range(d)]
          for j in range(k)]
    L = L1 + L2; M = M1 + M2
    P = l + k
    Wx = []
    Y = []
    for j in range(P):
        w = {}
        for (a, b) in pairs:
            if j < l and (a >= 8 or b >= 8): continue
            w[(a, b)] = f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a]))
        if j < l:
            Wx.append([w[pq] for pq in PAIRS8])
        yj = []
        for r in range(q):
            terms = [w[pq] for pq, col in zip(pairs, phic) if (col >> r) & 1 and pq in w]
            yj.append(f.xor_list(terms))
        Y.append(yj)
    C = [[f.var() for _ in range(P)] for _ in T]
    for o in range(len(T)):
        for r in range(q):
            zs = [f.and2(C[o][j], Y[j][r]) for j in range(P) if Y[j][r] is not None]
            f.fix(f.xor_list(zs), (tco[o] >> r) & 1)
    # (a)
    Ec = [[f.var() for _ in range(l)] for _ in range(4)]
    for s in range(4):
        for r in range(28):
            f.fix(f.xor_list([f.and2(Ec[s][j], Wx[j][r]) for j in range(l)]), (Nforms[s] >> r) & 1)
    for j in range(l):
        f.cl.append(Wx[j])
    if fix_l1 is None:
        for j in range(l - 1): qmc.lex_le(f, L1[j][:8], L1[j + 1][:8])
    if fix_members is None:
        for j in range(k - 1): qmc.lex_le(f, L2[j], L2[j + 1])
    if fix_members:
        for j, vec in enumerate(fix_members):
            for b in range(d): f.fix(L2[j][b], vec[b])
    if fix_l1:
        for j, (va, vb) in enumerate(fix_l1):
            for b in range(8): f.fix(L1[j][b], va[b]); f.fix(M1[j][b], vb[b])
    meta = dict(l=l, k=k, d=d, q=q, vars=f.n, clauses=len(f.cl))
    return f, (L1, M1, L2, C), meta, O


def a28_fixings(O):
    """member first operands and level-1 operands of the AD5 file in the O basis"""
    from exp_stage3 import coords
    c, ands, outs, tt = analyse(AD5)
    top = max(A['level'] for A in ands)
    mem = []
    for A in ands:
        if A['level'] != top: continue
        co = coords([gf.ONES] + O, A['Ltab'])[1:]
        mem.append(co)
    l1 = []
    for A in ands:
        if A['level'] != 1: continue
        l1.append((coords([gf.ONES] + O, A['Ltab'])[1:9], coords([gf.ONES] + O, A['Rtab'])[1:9]))
    return mem, l1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--k', type=int, default=13)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    ap.add_argument('--a28-check', default=None, help='fix "members", "l1" or "both" to AD5 values')
    a = ap.parse_args()
    gamma = None if a.gamma == 'none' else gp(int(a.gamma))
    fm = fl = None
    if a.a28_check:
        O0, _, _, _, _ = setup(gamma)
        mem, l1 = a28_fixings(O0)
        if a.a28_check in ('members', 'both'): fm = mem
        if a.a28_check in ('l1', 'both'): fl = l1
    t0 = time.time()
    f, (L1, M1, L2, C), meta, O = encode(a.l, a.k, gamma, fm, fl)
    meta['encode_s'] = round(time.time() - t0, 1); meta['a28_check'] = a.a28_check
    meta['gamma'] = a.gamma
    print(json.dumps(meta), flush=True)
    ok, model, dt = qmc.solve(f, a.solver)
    meta['sat'] = ok; meta['secs'] = round(dt, 1)
    if ok:
        val = set(v for v in model if v > 0)
        bit = lambda v: 1 if v in val else 0
        meta['l1'] = [[[bit(v) for v in L1[j][:8]], [bit(v) for v in M1[j][:8]]] for j in range(a.l)]
        meta['members'] = [[bit(v) for v in L2[j]] for j in range(a.k)]
        meta['c'] = [[bit(v) for v in row] for row in C]
    print(json.dumps(meta), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps(meta))


if __name__ == '__main__':
    main()
