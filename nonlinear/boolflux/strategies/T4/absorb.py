#!/usr/bin/env python3
"""T4: can stage 1 (9 x-linear products spanning N = x^17 mod affine) absorb bottom x-junk?

Rank-2 bottom product (Y_i + w_j)(Y_j + w_i) = Y_i w_i + Y_j w_j + Y_i Y_j + w_i w_j replaces two
rank-1 products when Y_i Y_j is free (in V, the front span) and the x-junk w_i w_j (a product of
two x-linear forms) is one of the 9 stage-1 products.  This asks, exactly (SAT, C's qmc model):
for a set of such x-junk products t_1..t_s, are there 9 - s further x-linear products with
N's coordinates in span(1, x, t's, products)?
    python3 absorb.py FILE single|greedy [--solver cadical153]
"""
import sys, json, time, itertools
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'C')); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
import qmc  # noqa
from boolflux import core  # noqa

def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11b
        b >>= 1
    return r
def gpow(a, e):
    r = 1
    while e:
        if e & 1: r = gmul(r, a)
        a = gmul(a, a); e >>= 1
    return r

def N_tables():
    Nv = [gpow(x, 17) for x in range(256)]
    return [sum(((Nv[x] >> j) & 1) << x for x in range(256)) for j in range(8)]

def setup(f):
    c = load(f); T, lg, la, fa, ba, V, X = analyse(c)
    AD = max(la[o] for o in c.outputs)
    outs = decompose(c, T, la, ba, AD)
    ys = sorted({y for d in outs for y in d})
    free = [(i, j) for i, j in itertools.combinations(range(len(ys)), 2) if (ys[i] & ys[j]) in V]
    targets = []   # (output k, pair, table, dfree)
    for k, d in enumerate(outs):
        ws = [d.get(y, 0) for y in ys]
        for i, j in itertools.combinations(range(len(ys)), 2):
            targets.append((k, (i, j), ws[i] & ws[j], (i, j) in free))
    return c, T, V, ys, free, outs, targets

def test(ts, solver, k=None):
    O = core.input_tables(8)
    E = [ONES] + O + list(ts)
    TT = N_tables()
    k = 9 - len(ts) if k is None else k
    f, LMC, meta = qmc.encode(O, E, TT, k)
    ok, model, dt = qmc.solve(f, solver)
    sol = None
    if ok:
        prods, cm = qmc.decode(model, LMC, O)
        assert qmc.check(prods, cm, O, E, TT)
        sol = prods
    return ok, dt, sol, meta

if __name__ == '__main__':
    f = sys.argv[1]; mode = sys.argv[2]
    solver = 'cadical153'
    c, T, V, ys, free, outs, targets = setup(f)
    print(json.dumps({'Y': len(ys), 'free_pairs': free}), flush=True)
    if mode == 'single':
        only_free = '--all' not in sys.argv
        for (k, p, t, df) in targets:
            if only_free and not df: continue
            ok, dt, sol, meta = test([t], solver)
            print(json.dumps({'out': k, 'pair': p, 'dfree': df, 'sat': ok, 'secs': round(dt, 1), 'q': meta['q']}), flush=True)
    elif mode == 'greedy':
        # targets passed as list of out:pair
        pass
