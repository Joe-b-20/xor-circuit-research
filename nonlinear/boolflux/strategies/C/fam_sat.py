"""Stage-3 search restricted to the GF(4)-norm family (NOTES.md section 4):
products  (Tr(Ax) + Tr_K(s w) [+ Tr_K(t N)]) * (Tr(wA x) + Tr_K(w^2 s w) [+ Tr_K(w^2 t N)])
with w = omega (GF(4) generator), w-function = n + gamma*N (default gamma = g^17 as in A28),
or (--wfree) independent n- and N-parts.

E = 1, x, level-1 ANDs of --stage1, middle ANDs of --inv (default: same file), plus --extra-l1
files' level-1 ANDs.  Targets: the 8 bits of x^-1.

usage: python3 fam_sat.py --stage1 F [--inv F] --k K [--gamma E|none] [--wfree]
"""
from __future__ import annotations

import argparse
import json
import time

import gf
import qmc
from exp_stage3 import tables_of
from fam_check import tr_tab, trK, OMEGA, gp
from spectral import TRF

N = [gf.power(p, 17) for p in range(256)]
n = [gf.INV[v] for v in N]
KSTAR = [v for v in gf.SUB16 if v]


def kbasis():
    sp = gf.Span(); kb = []
    for v in gf.SUB16:
        if v and sp.add(v): kb.append(v)
    return kb


def coords(B, t):
    sp = gf.Span()
    for i, b in enumerate(B): sp.add(b, 1 << i)
    r, tag = sp.reduce(t, 0)
    if r: return None
    return [(tag >> i) & 1 for i in range(len(B))]


def build_O(gamma, wfree):
    kb = kbasis()
    O = list(gf.X); kinds = [('x', None)] * 8
    funcs = []
    if wfree:
        funcs = [n, N]
    else:
        w = [n[p] ^ (gf.mul(gamma, N[p]) if gamma else 0) for p in range(256)]
        funcs = [w]
    for fv in funcs:
        tabs = gf.coord_tables(fv, kb)
        for t in tabs:
            # find s with Tr_K(s f) == t
            s = next(s for s in gf.SUB16 if trK(s, fv) == t)
            O.append(t); kinds.append(('k', (s, fv)))
    w2 = gf.mul(OMEGA, OMEGA)
    d = len(O)
    omega = [[0] * d for _ in range(d)]   # omega[b][c]: coefficient of O_c... we need M = Om L
    for c in range(d):
        kind, data = kinds[c]
        if kind == 'x':
            A = TRF[O[c]]
            img = tr_tab(gf.mul(OMEGA, A))
        else:
            s, fv = data
            img = trK(gf.mul(w2, s), fv)
        co = coords(O, img)
        assert co is not None
        for b in range(d): omega[b][c] = co[b]
    return O, omega


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--stage1', required=True)
    ap.add_argument('--inv', default=None)
    ap.add_argument('--k', type=int, required=True)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--wfree', action='store_true')
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    l1, mid = tables_of(a.stage1)
    if a.inv: _, mid = tables_of(a.inv)
    gamma = None if a.gamma == 'none' else gp(int(a.gamma))
    O, omega = build_O(gamma, a.wfree)
    E = [gf.ONES] + gf.X + l1 + mid
    T = [gf.bit_table(gf.INV, kk) for kk in range(8)]
    t0 = time.time()
    f, LMC, meta = qmc.encode(O, E, T, a.k, symbreak=True, omega=omega)
    info = dict(stage1=a.stage1, inv=a.inv, k=a.k, gamma=a.gamma, wfree=a.wfree, n_l1=len(l1),
                n_mid=len(mid), **meta)
    print(json.dumps(info), flush=True)
    ok, model, dt = qmc.solve(f, a.solver)
    info['sat'] = ok; info['solve_s'] = round(dt, 1)
    if ok:
        prods, cmat = qmc.decode(model, LMC, O)
        info['verified'] = qmc.check(prods, cmat, O, E, T)
        info['prods'] = [[''.join(map(str, l)), ''.join(map(str, m))] for l, m in prods]
        info['c'] = [''.join(map(str, r)) for r in cmat]
    print(json.dumps(info), flush=True)
    if a.out:
        open(a.out, 'w').write(json.dumps(info))


if __name__ == '__main__':
    main()
