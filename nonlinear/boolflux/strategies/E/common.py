"""Track E shared helpers: circuit loading, truth tables, GF(2^8) interface spaces, metrics."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parents[1]            # nonlinear/boolflux
REPO = PKG.parents[1]
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402

NIST = REPO / 'nonlinear' / 'nist'
ONES = (1 << 256) - 1
MODEL = core.Model.load('nist')
SBOX = targets.aes_sbox()


def published_files():
    fs = sorted(NIST.glob('aes-sbox/*.circ.txt')) + sorted(NIST.glob('sbox/aes-sbox-fwd-*'))
    return fs


def load(path):
    p = Path(path)
    if p.suffix == '.bfx':
        return core.from_kernel(p.read_text(), name=p.stem)
    return core.read_ncff(str(p))


def gmul(a, b):
    r = 0
    while b:
        if b & 1: r ^= a
        a <<= 1
        if a & 0x100: a ^= 0x11B
        b >>= 1
    return r


def gpow(a, e):
    r = 1
    while e:
        if e & 1: r = gmul(r, a)
        a = gmul(a, a); e >>= 1
    return r


def fn_tables(f):
    """Bit tables (8) of a byte function f(x)."""
    ts = [0] * 8
    for x in range(256):
        v = f(x)
        for j in range(8):
            if (v >> j) & 1: ts[j] |= 1 << x
    return ts


def metrics(c):
    m = c.metrics(MODEL)
    return (m['A'], m['AD'], m['G'], m['GD'])


def correct(c):
    return c.value_table() == SBOX


class Span:
    """GF(2) span of 256-bit tables (with the constant 1 optionally), with membership tests."""
    def __init__(self, tabs=(), affine=True):
        self.rows = {}      # pivot bit -> row
        if affine: self.add(ONES)
        for t in tabs: self.add(t)

    def reduce(self, t):
        for p in sorted(self.rows, reverse=True):
            if (t >> p) & 1: t ^= self.rows[p]
        return t

    def add(self, t):
        t = self.reduce(t)
        if t:
            p = t.bit_length() - 1
            # keep rows reduced w.r.t. the new pivot not necessary for membership tests
            self.rows[p] = t
            return True
        return False

    def __contains__(self, t):
        return self.reduce(t) == 0

    def dim(self):
        return len(self.rows)


def levels(c):
    """AND level of every signal."""
    la = [0] * c.n
    for op, a, b in c.gates:
        la.append(max(la[a], la[b]) + (1 if op in core.NONLINEAR_OPS else 0))
    return la
