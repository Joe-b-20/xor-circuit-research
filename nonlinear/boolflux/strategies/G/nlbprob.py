"""Problem files for nlb.c (track G) and solution -> circuit.

Elements: free wires first (element 0 = constant 1, then the n inputs, then optional extra free
wires), then products p_0..p_{K-1}.  Operand masks are bit masks over element indices.

Problem file:  NW npts / NF / NF tables / K / K lines 'fixed allow opA opB' (hex) / NG /
per group 'w nt na' + nt target tables + na addend tables.  Tables: NW hex words, word 0 first
(bit x of the truth table = value at input integer x, as core.py).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))         # nonlinear/boolflux
from core import input_tables, tables_from_values, Circuit, write_ncff, NONLINEAR_OPS  # noqa: E402


def words(t, nw):
    return ' '.join('%x' % ((t >> (64 * i)) & ((1 << 64) - 1)) for i in range(nw))


class Problem:
    def __init__(self, n, free_extra=()):
        self.n = n
        self.npts = 1 << n
        self.nw = max(1, self.npts // 64)
        self.ones = (1 << self.npts) - 1
        self.free = [self.ones] + input_tables(n) + list(free_extra)
        self.slots = []          # (fixed, allow, a, b)
        self.groups = []         # (w, targets, addends)

    @property
    def NF(self):
        return len(self.free)

    def x_mask(self):
        """allowed mask for level-1 operands: constant + inputs"""
        return (1 << (1 + self.n)) - 1

    def add_slot(self, allow=None, a=0, b=0, fixed=0):
        e = self.NF + len(self.slots)
        if allow is None: allow = (1 << e) - 1          # any earlier element
        self.slots.append((fixed, allow, a, b))
        return e

    def add_group(self, targets, addends=(), w=1.0):
        self.groups.append((w, list(targets), list(addends)))

    def text(self):
        L = ['%d %d' % (self.nw, self.npts), str(self.NF)]
        L += [words(t, self.nw) for t in self.free]
        L.append(str(len(self.slots)))
        for f, al, a, b in self.slots: L.append('%d %x %x %x' % (f, al, a, b))
        L.append(str(len(self.groups)))
        for w, T, Z in self.groups:
            L.append('%g %d %d' % (w, len(T), len(Z)))
            L += [words(t, self.nw) for t in T] + [words(t, self.nw) for t in Z]
        return '\n'.join(L) + '\n'

    def write(self, path):
        Path(path).write_text(self.text(), encoding='utf-8', newline='\n')


def read_state(path):
    lines = Path(path).read_text().split('\n')
    head = lines[0].split()
    K = int(head[head.index('K') + 1])
    ops = [tuple(int(v, 16) for v in lines[1 + k].split()) for k in range(K)]
    return float(head[2]), ops


def product_tables(free, ops):
    tabs = list(free)
    for a, b in ops:
        ta = tb = 0
        for j in range(len(tabs)):
            if (a >> j) & 1: ta ^= tabs[j]
            if (b >> j) & 1: tb ^= tabs[j]
        tabs.append(ta & tb)
    return tabs


class Span:
    """GF(2) span of ints with tags (which basis elements make each vector)."""
    def __init__(self):
        self.rows = {}     # pivot -> (vec, tag)

    def reduce(self, v, tag=0):
        while v:
            p = v.bit_length() - 1
            if p not in self.rows: break
            r, t = self.rows[p]; v ^= r; tag ^= t
        return v, tag

    def add(self, v, tag):
        v, tag = self.reduce(v, tag)
        if v: self.rows[v.bit_length() - 1] = (v, tag); return True
        return False

    def express(self, v):
        """tag such that v = XOR of tagged elements, or None"""
        # full reduction (rows are not reduced against each other: iterate)
        tag = 0
        while v:
            p = v.bit_length() - 1
            if p not in self.rows: return None
            r, t = self.rows[p]; v ^= r; tag ^= t
        return tag


def circuit_from_basis(n, m, free_names, free, ops, out_tables, name='nlb'):
    """XOR-chain circuit: free wires must be 1 + inputs only (others not realisable here)."""
    assert len(free) == 1 + n, 'extra free wires need their own sub-circuit'
    gates = []
    sig_of = {}          # element index -> signal (None for constant)
    for i in range(n): sig_of[1 + i] = i
    tabs = list(free)

    def nsig():
        return n + len(gates) - 1

    def xor_chain(mask, want_not=False):
        idx = [j for j in range(mask.bit_length()) if (mask >> j) & 1]
        neg = 0 in idx
        idx = [j for j in idx if j != 0]
        if not idx: raise ValueError('constant operand')
        cur = sig_of[idx[0]]
        for j in idx[1:]:
            gates.append((6, cur, sig_of[j])); cur = nsig()
        return cur, neg
    for k, (a, b) in enumerate(ops):
        sa, na = xor_chain(a); sb, nb = xor_chain(b)
        # AND with complemented inputs via op code: f(a,b) = (a^na)&(b^nb)
        op = 0
        for x in (0, 1):
            for y in (0, 1):
                if (x ^ na) & (y ^ nb): op |= 1 << ((x << 1) | y)
        gates.append((op, sa, sb))
        sig_of[1 + n + k] = nsig()
    alltabs = product_tables(free, ops)
    S = Span()
    for j, t in enumerate(alltabs): S.add(t, 1 << j)
    outs = []
    for t in out_tables:
        tag = S.express(t)
        if tag is None: raise ValueError('output not in span')
        cur, neg = xor_chain(tag)
        if neg:
            gates.append((3, cur, cur)); cur = nsig()
        outs.append(cur)
    c = Circuit(n, m, gates, outs, name)
    return c.live()


def canon_gates(c):
    """replace op codes not in the NCFF library by library ops (2 -> ANDN swapped etc.)"""
    from core import canonical
    g2 = []
    for op, a, b in c.gates:
        if op in (8, 4, 2, 1, 6, 9, 3, 14, 13, 11, 7):
            op, a, b = canonical(op, a, b)
        g2.append((op, a, b))
    c.gates = g2
    return c
