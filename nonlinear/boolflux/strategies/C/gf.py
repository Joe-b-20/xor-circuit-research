"""GF(2^8) (AES polynomial) helpers and GF(2) linear algebra on 256-point truth tables.

Truth table convention (as core.py): an int whose bit p is the function value at input byte p.
Input wire U_i (file input i) is bit 7-i of the byte.
"""
from __future__ import annotations

ONES = (1 << 256) - 1


def mul(a, b, poly=0x11B):
    r = 0
    while b:
        if b & 1: r ^= a
        b >>= 1; a <<= 1
        if a & 0x100: a ^= poly
    return r


def power(a, e):
    r = 1
    while e:
        if e & 1: r = mul(r, a)
        a = mul(a, a); e >>= 1
    return r


INV = [0] + [power(a, 254) for a in range(1, 256)]
SUB16 = sorted({power(a, 17) for a in range(256)})      # GF(16) inside GF(256)
assert len(SUB16) == 16


def bit_table(f, k):
    """truth table of bit k (0 = lsb) of the byte function f: list/ callable"""
    t = 0
    for p in range(256):
        v = f[p] if not callable(f) else f(p)
        if (v >> k) & 1: t |= 1 << p
    return t


def coord_tables(f, basis=None):
    """Truth tables of coordinates of f (values in GF(256)).  basis: list of GF(2^8) elements
    spanning the value set; coordinates are taken w.r.t. the dual via solving.  Default: 8 bits."""
    if basis is None:
        return [bit_table(f, k) for k in range(8)]
    # express each value in the basis
    idx = coords_in_basis(basis)
    out = [0] * len(basis)
    for p in range(256):
        v = f[p] if not callable(f) else f(p)
        c = idx[v]
        for i in range(len(basis)):
            if (c >> i) & 1: out[i] |= 1 << p
    return out


def coords_in_basis(basis):
    idx = {}
    k = len(basis)
    for c in range(1 << k):
        v = 0
        for i in range(k):
            if (c >> i) & 1: v ^= basis[i]
        idx[v] = c
    return idx


def input_tables():
    tabs = []
    for i in range(8):
        bit = 7 - i; t = 0
        for p in range(256):
            if (p >> bit) & 1: t |= 1 << p
        tabs.append(t)
    return tabs


X = input_tables()


class Span:
    """Incremental GF(2) row space of ints (pivot = highest bit)."""
    def __init__(self, vecs=()):
        self.piv = {}            # pivot bit -> (vec, tag)
        for v in vecs: self.add(v)

    def reduce(self, v, tag=0):
        while v:
            h = v.bit_length() - 1
            if h not in self.piv: return v, tag
            pv, pt = self.piv[h]
            v ^= pv; tag ^= pt
        return 0, tag

    def add(self, v, tag=0):
        r, t = self.reduce(v, tag)
        if r:
            self.piv[r.bit_length() - 1] = (r, t); return True
        return False

    def contains(self, v):
        return self.reduce(v)[0] == 0

    def dim(self):
        return len(self.piv)


def affine_x():
    return [ONES] + X


def anf_quadratic_part(t):
    """Alternating-form (quadratic ANF part) of a truth table, as 28-bit int over pairs i<j of
    input wires U_i U_j; raises if degree > 2."""
    # Moebius transform
    a = [(t >> p) & 1 for p in range(256)]
    for i in range(8):
        s = 1 << i
        for p in range(256):
            if p & s: a[p] ^= a[p ^ s]
    q = 0; k = 0
    for p in range(256):
        if a[p] and bin(p).count('1') > 2:
            raise ValueError('degree > 2')
    # pair index: monomial with byte bits b1,b2 -> wires 7-b
    pairs = [(i, j) for i in range(8) for j in range(i + 1, 8)]
    for n, (i, j) in enumerate(pairs):
        p = (1 << (7 - i)) | (1 << (7 - j))
        if a[p]: q |= 1 << n
    return q


def anf(t):
    a = [(t >> p) & 1 for p in range(256)]
    for i in range(8):
        s = 1 << i
        for p in range(256):
            if p & s: a[p] ^= a[p ^ s]
    return a


def degree(t):
    a = anf(t)
    return max((bin(p).count('1') for p in range(256) if a[p]), default=-1)
