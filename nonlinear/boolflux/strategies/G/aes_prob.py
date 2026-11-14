"""AES problem files for nlb.c, built from a published 28-AND circuit.

usage:
  python3 aes_prob.py info FILE
  python3 aes_prob.py ucover FILE K OUT.prob [--level1]    stage-1 replacement: K products (any depth
        unless --level1) spanning U = V_N + junk forced by FILE's inversion + last layer
  python3 aes_prob.py repair FILE DROP OUT.prob [--free SPEC]   FILE's 28 products minus product DROP
        (1-based); remaining operands re-indexed; slots in SPEC free (default all), others fixed
  python3 aes_prob.py scratch K OUT.prob                   K free products, any depth, target S-box

Element layout (nlb): 0 = constant 1, 1..8 = inputs U0..U7, 9.. = products.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / 'C'))
from structure import analyse                      # noqa: E402  (track C, read-only use)
import gf                                          # noqa: E402
from targets import aes_sbox                       # noqa: E402
from nlbprob import Problem, Span, product_tables  # noqa: E402

ONES = (1 << 256) - 1


def sbox_tables():
    sb = aes_sbox()
    return [gf.bit_table(sb, 7 - j) for j in range(8)]


def n_coords():
    N = [gf.power(p, 17) for p in range(256)]
    sp = gf.Span(); basis = []
    for v in gf.SUB16:
        if v and sp.add(v): basis.append(v)
    return gf.coord_tables(N, basis)


def quad_monomials():
    X = gf.X
    return [X[i] & X[j] for i in range(8) for j in range(i + 1, 8)]


def load_circuit(path):
    """products as (L, R) masks over [1, U0..U7, a1..] (structure.py layout = nlb layout), levels"""
    c, ands, outs, tabs = analyse(path)
    ops = [(A['L'], A['R']) for A in ands]
    lev = [A['level'] for A in ands]
    return ops, lev, ands


def check_ops(ops):
    free = [ONES] + list(gf.X)
    tabs = product_tables(free, ops)
    S = Span()
    for j, t in enumerate(tabs): S.add(t, 1 << j)
    return all(S.express(t) is not None for t in sbox_tables())


def u_space(path):
    """U basis (quadratic functions mod affine) that level-1 must span, given FILE's inversion and
    last layer; plus the dimension of span(Z) & span(affine, quadratics)."""
    ops, lev, ands = load_circuit(path)
    Z = [A['tab'] for A in ands if A['level'] > 1]
    Q = [ONES] + list(gf.X) + quad_monomials()
    S = Span()
    for j, t in enumerate(Z): S.add(t, 1 << j)
    nz = len(Z)
    for j, t in enumerate(Q): S.add(t, 1 << (nz + j))
    # intersection span(Z) & span(Q)
    S2 = Span()
    for j, t in enumerate(Q): S2.add(t, 1 << j)
    inter = 0
    for t in Z:
        pass
    # dimension count: dim Z + dim Q - dim(Z+Q)
    dZ = sum(1 for _ in Z)  # Z products independent (checked below)
    SZ = Span(); rz = sum(SZ.add(t, 0) for t in Z)
    rq = len(S2.rows)
    rzq = len(S.rows)
    inter = rz + rq - rzq
    targets = n_coords()
    res = []
    for t in sbox_tables():
        tag = S.express(t)
        assert tag is not None, 'output not in span(Z, quadratics)'
        r = 0
        for j in range(len(Q)):
            if (tag >> (nz + j)) & 1: r ^= Q[j]
        res.append(r)
    # basis of U mod affine
    A = Span()
    for t in [ONES] + list(gf.X): A.add(t, 0)
    base_aff = len(A.rows)
    U = []
    for t in targets + res:
        if A.add(t, 0): U.append(t)
    return {'U': U, 'dimU': len(U), 'inter': inter, 'rankZ': rz, 'nZ': nz}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd')
    ap.add_argument('args', nargs='*')
    ap.add_argument('--level1', action='store_true')
    ap.add_argument('--free', default=None)
    a = ap.parse_args()
    if a.cmd == 'info':
        ops, lev, ands = load_circuit(a.args[0])
        from collections import Counter
        print('levels', sorted(Counter(lev).items()), 'valid', check_ops(ops))
        u = u_space(a.args[0])
        print('dimU', u['dimU'], 'intersection dim', u['inter'], 'rankZ', u['rankZ'], 'nZ', u['nZ'])
    elif a.cmd == 'ucover':
        path, K, out = a.args[0], int(a.args[1]), a.args[2]
        u = u_space(path)
        assert u['inter'] == 0, 'span(Z) meets the quadratics: addends needed'
        P = Problem(8)
        for _ in range(K): P.add_slot(allow=P.x_mask() if a.level1 else None)
        P.add_group(u['U'])
        P.write(out)
        print(json.dumps({'out': out, 'dimU': u['dimU'], 'K': K, 'level1': a.level1}))
    elif a.cmd == 'repair':
        path, drop, out = a.args[0], int(a.args[1]) - 1, a.args[2]
        ops, lev, ands = load_circuit(path)
        base = 9
        e_drop = base + drop
        new = []
        for k, (L, R) in enumerate(ops):
            if k == drop: continue
            def fix(m):
                lo = m & ((1 << e_drop) - 1)
                hi = m >> (e_drop + 1)
                return lo | (hi << e_drop)
            new.append((fix(L), fix(R)))
        free = set(range(len(new)))
        if a.free:
            free = set()
            for part in a.free.split(','):
                if '-' in part:
                    x, y = part.split('-'); free |= set(range(int(x) - 1, int(y)))
                else: free.add(int(part) - 1)
        P = Problem(8)
        for k, (L, R) in enumerate(new):
            P.add_slot(allow=None, a=L, b=R, fixed=0 if k in free else 1)
        P.add_group(sbox_tables())
        P.write(out)
        print(json.dumps({'out': out, 'dropped': drop + 1, 'K': len(new), 'free': len(free)}))
    elif a.cmd == 'scratch':
        K, out = int(a.args[0]), a.args[1]
        P = Problem(8)
        for _ in range(K): P.add_slot()
        P.add_group(sbox_tables())
        P.write(out)
    else:
        raise SystemExit('unknown command')


if __name__ == '__main__':
    main()
