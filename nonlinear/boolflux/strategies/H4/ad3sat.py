"""Joint SAT for the first two AND levels of the GF(4)-norm (AND-depth-3) route.

Model (exact for functions of x, see NOTES.md section AD3):
  L1: k1 products l_j * m_j, l_j, m_j in span(1, x)                       (AND level 1)
  L2: k2 products, operands in span(1, x, N), N = x^17 (4 coordinates)    (AND level 2)
  require  N in span(1, x, L1)  and  T in span(1, x, L1, L2)
  T = coordinates of x^84 (8) and N4 = x^85 (2)   [option --targets]
Level 3 (P * N4^2, P = x^84) is then done with 12 products [bilinear rank 12, P].
Everything modulo E0 = span(1, x, N); products mod E0 depend only on the operand wedge.

usage: ad3sat.py K1 K2 [--targets adj+n4|adj|n4] [--seed S]
"""
from __future__ import annotations

import argparse
import itertools
import json
import time

from pysat.solvers import Solver

import cover1
from chm import CNF, lex_le
from h4lib import pw, ONES

XT = [sum(1 << p for p in range(256) if (p >> a) & 1) for a in range(8)]


def coords_of(fn):
    return [sum(1 << p for p in range(256) if (fn(p) >> k) & 1) for k in range(8)]


NT = coords_of(lambda p: pw(p, 17) if p else 0)
ADJ = coords_of(lambda p: pw(p, 84) if p else 0)
N4T = coords_of(lambda p: pw(p, 85) if p else 0)


def basis_of(vs):
    rows = cover1.rowspace(vs)
    return list(rows.values())


def reduce_mod(v, rows):
    return cover1.reduce(v, rows)


def level_tables(path, level):
    if path.endswith('.json'):
        import json
        ops = json.load(open(path))['l1ops']
        return [int(a, 16) & int(b, 16) for a, b in ops]
    import sys
    sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
    from boolflux import core
    c = core.read_ncff(path); tabs = c.tables(); la = [0] * 8; out = []
    for j, (op, a, b) in enumerate(c.gates):
        l = (1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]); la.append(l)
        if op in core.NONLINEAR_OPS and l == level: out.append(tabs[8 + j])
    return out


def build(targets='adj+n4', fixed=()):
    G = XT + basis_of([t for t in NT if t])          # 12 operand basis functions
    assert len(G) == 12
    E0 = cover1.rowspace([ONES] + XT + [t for t in NT if t] + list(fixed))
    pairs1 = list(itertools.combinations(range(8), 2))
    pairs2 = list(itertools.combinations(range(12), 2))
    im1 = [reduce_mod(XT[a] & XT[b], E0) for a, b in pairs1]
    im2 = [reduce_mod(G[a] & G[b], E0) for a, b in pairs2]
    T = []
    if 'adj' in targets: T += ADJ
    if 'n4' in targets: T += N4T
    T = [reduce_mod(t, E0) for t in T]
    T = basis_of([t for t in T if t])
    # quotient coordinates on span(im1, im2, T)
    allv = im1 + im2 + T
    rows = cover1.rowspace(allv)
    piv = sorted(rows)
    # express each vector in the basis rows (coordinates = which rows are used)
    basis = [rows[h] for h in piv]

    def qc(v):
        c = 0
        for i in range(len(piv) - 1, -1, -1):
            h = piv[i]
            if (v >> h) & 1:
                v ^= basis[i]; c |= 1 << i
        assert v == 0
        return c
    # rows are not mutually reduced; reduce descending works since each row has leading bit h
    q = len(piv)
    return dict(im1=[qc(v) for v in im1], im2=[qc(v) for v in im2], T=[qc(t) for t in T], q=q,
                pairs1=pairs1, pairs2=pairs2,
                Nw=[cover1.form_from_anf(8, cover1.anf_quadratic_part(t, 8)) for t in NT if t])


def encode(k1, k2, P):
    f = CNF()
    pairs1, pairs2 = P['pairs1'], P['pairs2']
    L1 = [([f.var() for _ in range(8)], [f.var() for _ in range(8)]) for _ in range(k1)]
    L2 = [([f.var() for _ in range(12)], [f.var() for _ in range(12)]) for _ in range(k2)]
    for j in range(k1 - 1): lex_le(f, L1[j][0] + L1[j][1], L1[j + 1][0] + L1[j + 1][1])
    for j in range(k2 - 1): lex_le(f, L2[j][0] + L2[j][1], L2[j + 1][0] + L2[j + 1][1])

    def wedge(l, m, pairs):
        return [f.xor2(f.and2(l[a], m[b]), f.and2(l[b], m[a])) for a, b in pairs]
    W1 = [wedge(l, m, pairs1) for l, m in L1]
    W2 = [wedge(l, m, pairs2) for l, m in L2]
    q = P['q']

    def image(w, ims):
        return [f.xor_list([w[i] for i in range(len(ims)) if (ims[i] >> r) & 1]) for r in range(q)]
    I1 = [image(w, P['im1']) for w in W1]
    I2 = [image(w, P['im2']) for w in W2]
    # N in span(L1) as quadratic forms on x (wedge coords, exact)
    for t in P['Nw']:
        c = [f.var() for _ in range(k1)]
        for i in range(len(pairs1)):
            v = f.xor_list([f.and2(c[j], W1[j][i]) for j in range(k1)])
            f.cl.append([v] if (t >> i) & 1 else [-v])
    for t in P['T']:
        c = [f.var() for _ in range(k1 + k2)]
        imgs = I1 + I2
        for r in range(q):
            v = f.xor_list([f.and2(c[j], imgs[j][r]) for j in range(k1 + k2)])
            f.cl.append([v] if (t >> r) & 1 else [-v])
    return f, L1, L2


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('k1', type=int); ap.add_argument('k2', type=int)
    ap.add_argument('--targets', default='adj+n4')
    ap.add_argument('--solver', default='cadical153')
    ap.add_argument('--out', default=None)
    ap.add_argument('--fix-l1', default=None, help='NCFF file: its level-1 ANDs are free (k1 must be 0)')
    a = ap.parse_args()
    fixed = level_tables(a.fix_l1, 1) if a.fix_l1 else []
    if fixed:
        assert a.k1 == 0
        assert all(cover1.reduce(t, cover1.rowspace([ONES] + XT + fixed)) == 0 for t in NT)
    P = build(a.targets, fixed)
    if fixed: P['Nw'] = []
    f, L1, L2 = encode(a.k1, a.k2, P)
    t0 = time.time()
    with Solver(name=a.solver, bootstrap_with=f.cl) as s:
        ok = s.solve()
        model = set(l for l in s.get_model() if l > 0) if ok else None
    dt = time.time() - t0
    res = {'k1': a.k1, 'k2': a.k2, 'targets': a.targets, 'fix_l1': a.fix_l1, 'q': P['q'], 'vars': f.n,
           'clauses': len(f.cl), 'sat': ok, 'secs': round(dt, 1)}
    if ok:
        bits = lambda vs: sum(1 << i for i, v in enumerate(vs) if v in model)
        res['L1'] = [(bits(l), bits(m)) for l, m in L1]
        res['L2'] = [(bits(l), bits(m)) for l, m in L2]
    print(json.dumps(res), flush=True)
    if a.out:
        with open(a.out, 'a') as fh: fh.write(json.dumps(res) + '\n')


if __name__ == '__main__':
    main()
