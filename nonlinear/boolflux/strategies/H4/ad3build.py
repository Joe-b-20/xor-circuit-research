"""Build and verify an AD3 GF(4)-norm-route circuit:
  level 1 = the level-1 ANDs of L1FILE (or explicit operand pairs), level 2 = members/N-products
  (a state from ad3fix.py / ad3mem.py), level 3 = x^84 * N4^2 by GF(4)-scalar Karatsuba (12).
usage: ad3build.py JSONL_LINE_FILE INDEX OUT.circ.txt
"""
from __future__ import annotations

import json
import sys

import ad3mem as A
from ad3sat import XT, NT, ADJ, N4T
from h4lib import Circ, Tower, smul, check_inverse, save, Q, ONES
sys.path.insert(0, '/home/joebachir20/xcr-boolflux/nonlinear')
from boolflux import core


class Solver:
    """express truth tables as XOR combinations of the circuit's wires"""
    def __init__(self, C):
        self.C = C; self.rows = {}; self.n = 0
        self.sync()

    def sync(self):
        while self.n < len(self.C.tab):
            self.add(self.C.tab[self.n], 1 << self.n); self.n += 1

    def add(self, v, tag):
        for h in sorted(self.rows, reverse=True):
            if (v >> h) & 1: v ^= self.rows[h][0]; tag ^= self.rows[h][1]
        if v: self.rows[v.bit_length() - 1] = (v, tag)

    def bundle(self, t):
        self.sync()
        tag = 0; v = t
        for h in sorted(self.rows, reverse=True):
            if (v >> h) & 1: v ^= self.rows[h][0]; tag ^= self.rows[h][1]
        if v: raise ValueError('not in span')
        return {w: 1 for w in range(self.n) if (tag >> w) & 1}


def level1_operands(path):
    if path.endswith('.json'):
        return [(int(a, 16), int(b, 16)) for a, b in json.load(open(path))['l1ops']]
    c = core.read_ncff(path); tabs = c.tables(); la = [0] * 8; out = []
    for j, (op, a, b) in enumerate(c.gates):
        l = (1 if op in core.NONLINEAR_OPS else 0) + max(la[a], la[b]); la.append(l)
        if op in core.NONLINEAR_OPS and l == 1:
            assert op == 8, 'only AND at level 1 supported'
            out.append((tabs[a], tabs[b]))
    return out


def build(l1, state, out, comment):
    C = Circ(); S = Solver(C)
    for ta, tb in l1:
        C.AND(S.bundle(ta), S.bundle(tb))
    Ntab = [S.bundle(t) for t in A.Nb]           # N basis functions as bundles
    def nform(bits):
        b = {}
        for i in range(4):
            if (bits >> i) & 1: b = C.add(b, Ntab[i])
        return b
    for m in state:
        if m[0] == 'x':
            C.AND(S.bundle(A.lin(m[1], XT)), S.bundle(A.lin(m[2], XT)))
    for m in state:
        if m[0] == 'x': continue
        if m[0] == 'n':
            C.AND(nform(m[1]), nform(m[2]))
        else:
            lam, (g0, g1) = m[1], m[2]
            a0, a1 = A.COMP[lam]
            C.AND(C.add(S.bundle(a0), nform(g0)), C.add(S.bundle(a1), nform(g1)))
    l12 = C.ands
    P = {}
    for k in range(8):
        for w in S.bundle(ADJ[k]): P[w] = P.get(w, 0) ^ (1 << k)
    P = {w: c for w, c in P.items() if c}
    N4 = {}
    for k in range(8):
        if N4T[k]:
            for w in S.bundle(N4T[k]): N4[w] = N4.get(w, 0) ^ (1 << k)
    N4 = C.project({w: c for w, c in N4.items() if c}, Q)
    T = Tower(('normal',) * 3)
    y = smul(C, T, P, C.frob(N4, 1), 3, 1)
    ok = check_inverse(C, y)
    m = save(C, y, out, [comment])
    return ok, l12, m


def main():
    lines = open(sys.argv[1]).read().splitlines()
    rec = json.loads(lines[int(sys.argv[2])])
    l1 = level1_operands(rec['l1file'])
    state = [tuple(m) if m[0] == 'n' else (m[0], m[1], tuple(m[2])) for m in rec['state']]
    ok, l12, m = build(l1, state, sys.argv[3], 'H4 AD3 GF(4)-norm route: L1 of %s, L2 %s' % (
        rec['l1file'].split('/')[-1], json.dumps(rec['state'])))
    print('inverse ok', ok, 'levels 1+2 ANDs', l12, 'metrics', m)


if __name__ == '__main__':
    main()
