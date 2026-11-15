#!/usr/bin/env python3
"""Formal model of the bottom (last AND level) of an AD4 Boyar-Peralta-family AES circuit.

Coordinates: X = the 8 input bits, Y = a basis of the inversion-output space (span of the last-level
AND operands modulo span(1, X)).  Every last-level operand is affine in (Y, X).  Quadratic
functions over (Y, X) are represented by their monomial coefficients; the 1 + 12 + 66 monomials
(1, y_i, x_j, y_i y_j, y_i x_j, x_i x_j) are checked to be linearly independent as truth tables on
the 256 inputs, so formal identities and functional identities agree inside that space.

    bottom.py FILE        prints the bottom: operands as forms, outputs in coordinates
"""
import sys
from pathlib import Path
from itertools import combinations
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core, targets  # noqa

NL = core.NONLINEAR_OPS
ONES = (1 << 256) - 1


def load(f):
    p = Path(f)
    return core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))


def and_levels(c):
    la = [0] * c.n; lg = [0] * c.n
    for op, a, b in c.gates:
        la.append((1 if op in NL else 0) + max(la[a], la[b]))
        lg.append(1 + max(lg[a], lg[b]))
    return la, lg


class Basis:
    """Incremental GF(2) basis over ints (truth tables) with coordinate tracking."""
    def __init__(self):
        self.rows = []   # (pivot_bit, vec, combo)
        self.names = []

    def reduce(self, v):
        combo = 0
        for piv, r, cb in self.rows:
            if v >> piv & 1:
                v ^= r; combo ^= cb
        return v, combo

    def add(self, v, name):
        r, combo = self.reduce(v)
        if r == 0:
            return False
        k = len(self.names); self.names.append(name)
        combo ^= 1 << k
        piv = r.bit_length() - 1
        # keep rows reduced w.r.t. the new pivot
        new = []
        for p2, r2, c2 in self.rows:
            if r2 >> piv & 1:
                r2 ^= r; c2 ^= combo
            new.append((p2, r2, c2))
        new.append((piv, r, combo))
        self.rows = new
        return True

    def coords(self, v):
        r, combo = self.reduce(v)
        return None if r else combo


def analyse(c):
    T = c.tables(); n = c.n
    la, lg = and_levels(c)
    AD = max(la[s] for s in c.outputs)
    last = [j for j, (op, a, b) in enumerate(c.gates) if op in NL and la[n + j] == AD]
    X = [T[i] for i in range(n)]
    # Y space: operands of last-level ANDs modulo span(1, X)
    B = Basis(); B.add(ONES, '1')
    for i in range(n): B.add(X[i], 'x%d' % i)
    Ysig = []
    for j in last:
        op, a, b = c.gates[j]
        for s in (a, b):
            if B.add(T[s], 'y%d' % len(Ysig)):
                Ysig.append(s)
    return T, la, lg, last, Ysig, B


def monomials(Yt, Xt):
    mons = [('1', ONES)]
    mons += [('y%d' % i, t) for i, t in enumerate(Yt)] + [('x%d' % i, t) for i, t in enumerate(Xt)]
    V = [('y%d' % i, t) for i, t in enumerate(Yt)] + [('x%d' % i, t) for i, t in enumerate(Xt)]
    for (na, ta), (nb, tb) in combinations(V, 2):
        mons.append((na + nb, ta & tb))
    return mons


def main():
    c = load(sys.argv[1])
    T, la, lg, last, Ysig, B = analyse(c)
    print('last-level ANDs:', len(last), ' Y dim:', len(Ysig), ' Y signals:', Ysig)
    Yt = [T[s] for s in Ysig]; Xt = [T[i] for i in range(c.n)]
    mons = monomials(Yt, Xt)
    MB = Basis()
    dep = 0
    for nm, t in mons:
        if not MB.add(t, nm): dep += 1
    print('monomials', len(mons), 'dependent', dep)
    nm_ = B.names
    def form(v):
        cb = B.coords(v)
        return '+'.join(nm_[k] for k in range(len(nm_)) if cb >> k & 1) if cb is not None else '?'
    for j in last:
        op, a, b = c.gates[j]
        print('AND g%d lvl%d: (%s) * (%s)   [sig %d lv %d, sig %d lv %d]' % (
            c.n + j, lg[c.n + j], form(T[a]), form(T[b]), a, lg[a], b, lg[b]))
    for o, s in enumerate(c.outputs):
        cb = MB.coords(T[s])
        print('S%d:' % o, '?' if cb is None else ' '.join(MB.names[k] for k in range(len(MB.names)) if cb >> k & 1))


if __name__ == '__main__':
    main()
