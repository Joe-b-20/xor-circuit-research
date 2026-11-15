"""Exact multiplicative complexity of a small vectorial Boolean function (CHM / Stoffelen
encoding): k ANDs, each operand an affine combination of the inputs and earlier AND outputs,
outputs affine combinations of inputs and AND outputs.  Returns a decoded circuit.

table: list of 2^n output ints; input bit j of row p is (p >> j) & 1 (input j), output bit o is
(y >> o) & 1.
Symmetry breaking (sound): none on operands except that AND i's operand coefficient vectors
are ordered (op0 <= op1 lexicographically) -- swapping the two operands of one AND is a
symmetry.  AND outputs are not reordered (would need care with dependencies).
"""
from __future__ import annotations

import time

from pysat.solvers import Solver


class CNF:
    def __init__(self):
        self.n = 0; self.cl = []
        self.T = self.var(); self.cl.append([self.T])

    def var(self):
        self.n += 1; return self.n

    def and2(self, a, b):
        if a == -self.T or b == -self.T: return -self.T
        if a == self.T: return b
        if b == self.T: return a
        c = self.var()
        self.cl += [[-c, a], [-c, b], [c, -a, -b]]
        return c

    def xor2(self, a, b):
        if a == -self.T: return b
        if b == -self.T: return a
        if a == self.T: return -b
        if b == self.T: return -a
        c = self.var()
        self.cl += [[-c, a, b], [-c, -a, -b], [c, -a, b], [c, a, -b]]
        return c

    def xor_list(self, xs):
        r = -self.T
        for x in xs: r = self.xor2(r, x)
        return r


def lex_le(f, a, b):
    """a <= b as bit vectors (index 0 most significant)"""
    eq = f.T
    for x, y in zip(a, b):
        # if prefix equal then not (x=1 and y=0)
        f.cl.append([-eq, -x, y])
        e2 = f.var()
        # e2 = eq & (x == y)
        f.cl += [[-e2, eq], [-e2, -x, y], [-e2, x, -y], [e2, -eq, x, y], [e2, -eq, -x, -y]]
        eq = e2


def encode(table, n, m, k):
    f = CNF()
    A = [[[f.var() for _ in range(1 + n + i)] for _ in range(2)] for i in range(k)]
    B = [[f.var() for _ in range(1 + n + k)] for _ in range(m)]
    for i in range(k):
        lex_le(f, A[i][0], A[i][1])
    for p in range(1 << n):
        xs = [(p >> j) & 1 for j in range(n)]
        ts = []
        for i in range(k):
            ops = []
            for s in range(2):
                co = A[i][s]
                terms = [co[0]] + [co[1 + j] for j in range(n) if xs[j]] + \
                        [f.and2(co[1 + n + r], ts[r]) for r in range(i)]
                ops.append(f.xor_list(terms))
            ts.append(f.and2(ops[0], ops[1]))
        y = table[p]
        for o in range(m):
            co = B[o]
            terms = [co[0]] + [co[1 + j] for j in range(n) if xs[j]] + \
                    [f.and2(co[1 + n + r], ts[r]) for r in range(k)]
            v = f.xor_list(terms)
            f.cl.append([v] if (y >> o) & 1 else [-v])
    return f, A, B


def solve(table, n, m, k, solver='cadical153'):
    f, A, B = encode(table, n, m, k)
    t0 = time.time()
    with Solver(name=solver, bootstrap_with=f.cl) as s:
        ok = s.solve()
        model = set(l for l in s.get_model() if l > 0) if ok else None
    dt = time.time() - t0
    if not ok: return None, dt, f
    dec = lambda vs: [1 if v in model else 0 for v in vs]
    ands = [(dec(A[i][0]), dec(A[i][1])) for i in range(k)]
    outs = [dec(B[o]) for o in range(m)]
    return (ands, outs), dt, f


def evaluate(circ, n, p):
    ands, outs = circ
    xs = [(p >> j) & 1 for j in range(n)]
    ts = []
    for a0, a1 in ands:
        v = []
        for co in (a0, a1):
            s = co[0]
            for j in range(n): s ^= co[1 + j] & xs[j]
            for r in range(len(ts)): s ^= co[1 + n + r] & ts[r]
            v.append(s)
        ts.append(v[0] & v[1])
    y = 0
    for o, co in enumerate(outs):
        s = co[0]
        for j in range(n): s ^= co[1 + j] & xs[j]
        for r in range(len(ts)): s ^= co[1 + n + r] & ts[r]
        y |= s << o
    return y
