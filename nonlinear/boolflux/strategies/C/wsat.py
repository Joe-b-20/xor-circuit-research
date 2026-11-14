"""Given a last-layer member set S (default: the 13 last-layer ANDs of the AD5 file), decide by SAT
whether l level-1 products exist whose span (a) contains N's 4 quadratic forms and (b) absorbs
the x-quadratic junk of S, i.e. each output residual r_o lies in span(W) + junk(K0) + V_N + E_min.
If SAT for l = 9 with the 5-AND inversion of E_min and G0 treated hard, a 9 + 5 + |S| circuit
exists (built and checked by build27.py).

usage: python3 wsat.py --l 9 [--members FILE.json] [--g0 hard]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

import gf
import qmc
from kj_search import Model, a28_members, AD5
from structure import analyse

PAIRS = list(itertools.combinations(range(8), 2))


def quad_form_coords(M):
    """Span over E_min (tag 0) + JX monomials (tag bit i) to read x-quadratic forms."""
    sp = gf.Span()
    for e in M.Emin: sp.add(e, 0)
    for i, q in enumerate(M.JX): sp.add(q, 1 << i)
    return sp


def residuals(M, tabs):
    """tabs: truth tables of S. Returns (feasible, residual tables, kernel junk tables)."""
    H = [M.hard.nf(t) for t in tabs]
    k = len(tabs)
    piv = {}; kernel = []
    for j in range(k):
        v, tag = H[j], 1 << j
        while v:
            h = v.bit_length() - 1
            if h not in piv: break
            pv, pt = piv[h]; v ^= pv; tag ^= pt
        if v: piv[v.bit_length() - 1] = (v, tag)
        else: kernel.append(tag)
    res = []; combos = []
    for o in range(8):
        v, tag = M.hT[o], 0
        while v:
            h = v.bit_length() - 1
            if h not in piv: break
            pv, pt = piv[h]; v ^= pv; tag ^= pt
        if v: return False, None, None, None
        r = M.T[o]
        for j in range(k):
            if (tag >> j) & 1: r ^= tabs[j]
        res.append(r); combos.append(tag)
    kj = []
    for tag in kernel:
        r = 0
        for j in range(k):
            if (tag >> j) & 1: r ^= tabs[j]
        kj.append(r)
    return True, res, kj, (combos, kernel)


def to_forms(sp, tabs):
    out = []
    for t in tabs:
        r, tag = sp.reduce(t, 0)
        assert r == 0, 'residual not in E_min + JX'
        out.append(tag)            # 28-bit, bit i <-> PAIRS[i] (JX built in that order)
    return out


def n_forms():
    N = [gf.power(p, 17) for p in range(256)]
    sp = gf.Span(); kb = []
    for v in gf.SUB16:
        if v and sp.add(v): kb.append(v)
    return [gf.anf_quadratic_part(t) for t in gf.coord_tables(N, kb)]


def encode(l, Nf, rho, free):
    f = qmc.CNF()
    L = [f.vars(8) for _ in range(l)]; Mv = [f.vars(8) for _ in range(l)]
    W = [[f.xor2(f.and2(L[j][a], Mv[j][b]), f.and2(L[j][b], Mv[j][a])) for a, b in PAIRS]
         for j in range(l)]
    # (a) N forms, c = [I_4 | C']
    C = [[f.var() for _ in range(l)] for _ in range(4)]
    for s in range(4):
        for j in range(min(4, l)): f.fix(C[s][j], 1 if s == j else 0)
        for r in range(28):
            f.fix(f.xor_list([f.and2(C[s][j], W[j][r]) for j in range(l)]), (Nf[s] >> r) & 1)
    # (b) residuals modulo span(free + N forms)
    Pn = qmc.Normal(list(free) + list(Nf))
    img = [Pn.nf(1 << r) for r in range(28)]
    PW = [[f.xor_list([W[j][r] for r in range(28) if (img[r] >> b) & 1]) for b in range(28)]
          for j in range(l)]
    rho_n = [Pn.nf(x) for x in rho]
    for o, x in enumerate(rho_n):
        D = [f.var() for _ in range(l)]
        for b in range(28):
            terms = [f.and2(D[j], PW[j][b]) for j in range(l) if PW[j][b] is not None]
            f.fix(f.xor_list(terms), (x >> b) & 1)
    for j in range(l):
        f.cl.append([W[j][r] for r in range(28)])
    for j in range(4, l - 1):
        qmc.lex_le(f, L[j], L[j + 1])
    return f, L, Mv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--l', type=int, default=9)
    ap.add_argument('--gamma', default='17')
    ap.add_argument('--g0', default='hard')
    ap.add_argument('--members', default=None, help='JSON list of [kind, A, s(, t)]')
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    from fam_check import gp
    gamma = None if a.gamma == 'none' else gp(int(a.gamma))
    M = Model(gamma, a.g0)
    if a.members:
        mem = json.load(open(a.members))
        tabs = []
        for m in mem:
            w2 = None
            if m[0] == 'gf4':
                tabs.append(member_table(M, m[1], m[2]))
            else:
                tabs.append(member_table(M, m[1], m[2], m[3]))
    else:
        c, ands, outs, tt = analyse(AD5)
        top = max(A['level'] for A in ands)
        tabs = [A['tab'] for A in ands if A['level'] == top]
    ok, res, kj, combos = residuals(M, tabs)
    info = {'k': len(tabs), 'g0': a.g0, 'feasible': ok, 'l': a.l}
    if not ok:
        print(json.dumps(info)); return
    sp = quad_form_coords(M)
    rho = to_forms(sp, res); kap = to_forms(sp, kj)
    Nf = n_forms()
    Pn = qmc.Normal(kap + Nf)
    J = qmc.Normal([Pn.nf(x) for x in rho]).dim()
    info['J'] = J; info['kernel'] = len(kj)
    print(json.dumps(info), flush=True)
    f, L, Mv = encode(a.l, Nf, rho, kap)
    info['vars'] = f.n; info['clauses'] = len(f.cl)
    print(json.dumps(info), flush=True)
    ok2, model, dt = qmc.solve(f, a.solver)
    info['sat'] = ok2; info['secs'] = round(dt, 1)
    if ok2:
        val = set(v for v in model if v > 0)
        info['W'] = [[[1 if v in val else 0 for v in L[j]], [1 if v in val else 0 for v in Mv[j]]]
                     for j in range(a.l)]
    print(json.dumps(info), flush=True)
    if a.out: open(a.out, 'w').write(json.dumps(info))


def member_table(M, A, s, t=None):
    from fam_check import tr_tab, trK, OMEGA
    w2 = gf.mul(OMEGA, OMEGA)
    if t is None:
        l = tr_tab(A) ^ trK(s, M.w)
        m = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(w2, s), M.w)
    else:
        from kj_search import n as nn, N as NN
        l = tr_tab(A) ^ trK(s, nn) ^ trK(t, NN)
        m = tr_tab(gf.mul(OMEGA, A)) ^ trK(gf.mul(w2, s), nn) ^ trK(gf.mul(w2, t), NN)
    return l & m


if __name__ == '__main__':
    main()
