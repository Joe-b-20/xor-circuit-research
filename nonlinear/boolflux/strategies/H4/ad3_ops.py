"""Decompose the level-2 and level-3 operands of an AD3 GF(4)-norm circuit.
Level 2: operand = const + a(x) + b(N): print a as an F-element functional and b as K-functional,
and test the GF(4)-norm-member shape (x-parts and N-parts Q-proportional).
usage: ad3_ops.py FILE"""
import sys

import cover1
from ad3sat import XT, NT, ADJ, N4T, basis_of, level_tables
from h4lib import ONES, mul, pw, W, K, Q
import blocks
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core


def solve_coords(v, basis):
    """coordinates of v in the list basis (assumed independent), or None"""
    rows = {}
    for i, b in enumerate(basis):
        t = 1 << i
        for h in sorted(rows, reverse=True):
            if (b >> h) & 1: b ^= rows[h][0]; t ^= rows[h][1]
        if b: rows[b.bit_length() - 1] = (b, t)
    tag = 0
    for h in sorted(rows, reverse=True):
        if (v >> h) & 1: v ^= rows[h][0]; tag ^= rows[h][1]
    return tag if v == 0 else None


def functional_elem(coef_bits, nbits, field_basis):
    """GF(2)-linear functional f(y) = sum coef_i y_i on coordinates y_i w.r.t. field_basis ->
    the element c with f(y) = Tr(c y)  (searched)"""
    pass


def main(path):
    c = core.read_ncff(path); tabs = c.tables(); la = [0] * 8
    Nb = basis_of([t for t in NT if t])
    base = [ONES] + XT + Nb
    lv = {}
    for j, (op, a, b) in enumerate(c.gates):
        l = (1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]); la.append(l)
        if op in core.NONLINEAR_OPS: lv.setdefault(l, []).append((tabs[a], tabs[b], tabs[8 + j]))
    # x-parts as functionals: x bit i = XT[i]; express the x-part a(x) = sum a_i x_i as Tr(alpha x)
    tr = lambda z: bin(z).count('1') & 1  # placeholder (not field trace)
    def trF(z):
        s = 0; y = z
        for _ in range(8): s ^= y; y = mul(y, y)
        return s & 1
    alphas = {}
    for al in range(256):
        bits = 0
        for i in range(8):
            if trF(mul(al, 1 << i)): bits |= 1 << i
        alphas[bits] = al
    print('level sizes', {k: len(v) for k, v in lv.items()})
    for l in (2,):
        for (ta, tb, tp) in lv[l]:
            ca = solve_coords(ta, base); cb = solve_coords(tb, base)
            xa, na = (ca >> 1) & 255, ca >> 9
            xb, nb = (cb >> 1) & 255, cb >> 9
            A, B = alphas[xa], alphas[xb]
            ratio = mul(B, pw(A, 254)) if A else None
            print('L2  x-parts Tr(%3d x), Tr(%3d x)  ratio %s  N-parts %s %s' % (
                A, B, ratio if ratio is not None else '-', bin(na), bin(nb)),
                'ratio in Q' if ratio in Q else '')


if __name__ == '__main__':
    main(sys.argv[1])
