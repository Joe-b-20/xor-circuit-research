#!/usr/bin/env python3
"""How an AND-depth-3 AES circuit is built (track F).

For a circuit C (AD3) and the reference interface of NIST 116 (GF(2^4) inversion inputs N0..N3
and inversion outputs y0..y3, see invspec.py):
  - span checks: are N's bits in span{1, x, AND-level-1 outputs of C}?  are y's in
    span{1, x, ANDs of level <= 2}?
  - the A2 / A3 operands of C described by their algebraic degree (as functions of x) and by
    whether they lie in span{N-linear}, span{N-quadratic}, span{N-linear x x-linear} ...
    (checked against bases built from 116's N).
    python3 ad3study.py AD3.circ.txt [REF.circ.txt]
"""
import itertools
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2])); sys.path.insert(0, str(HERE))
from boolflux import core   # noqa: E402
from depth import analyse   # noqa: E402
from invspec import spec   # noqa: E402

ONES = (1 << 256) - 1


class Span:
    def __init__(self, vecs=()):
        self.rows = {}
        for v in vecs: self.add(v)

    def reduce(self, v):
        for p in sorted(self.rows, reverse=True):
            if (v >> p) & 1: v ^= self.rows[p]
        return v

    def add(self, v):
        v = self.reduce(v)
        if v:
            p = v.bit_length() - 1
            for q in list(self.rows):
                if (self.rows[q] >> p) & 1: self.rows[q] ^= v
            self.rows[p] = v
            return True
        return False

    def contains(self, v):
        return self.reduce(v) == 0

    def dim(self):
        return len(self.rows)


def degree(t):
    """Algebraic degree of a 256-bit truth table (Moebius transform)."""
    a = [(t >> x) & 1 for x in range(256)]
    for i in range(8):
        for x in range(256):
            if x >> i & 1: a[x] ^= a[x ^ (1 << i)]
    return max((bin(x).count('1') for x in range(256) if a[x]), default=0)


def main():
    c = core.read_ncff(sys.argv[1])
    ref = core.read_ncff(sys.argv[2] if len(sys.argv) > 2 else str(HERE.parents[2] / 'nist/aes-sbox/aes-sbox-a33-ad4-g116-gd15-xx83-7.circ.txt'))
    ins, outs, rt, _ = spec(ref)
    N = [rt[s] for s in ins[:4]]
    Y = [rt[s] for s in outs]
    X = core.input_tables(8)
    t = c.tables(); n = c.n
    lv, al, req, GD, D, region, fo = analyse(c, 99)
    base = [ONES] + X
    for k in (1, 2, 3):
        ands = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == k]
        print('AND level %d: %d ANDs; output degrees %s' % (k, len(ands), sorted(degree(t[s]) for s in ands)))
        ops = []
        for s in ands:
            for x in c.gates[s - n][1:]: ops.append(x)
        print('   operand degrees: %s' % sorted(degree(t[x]) for x in ops))
    S1 = Span(base + [t[s] for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == 1])
    print('dim span{1,x,A1} =', S1.dim(), '; N bits in it:', [S1.contains(v) for v in N])
    # N-quadratic and N-linear x x-linear spaces
    NL = Span([ONES] + N)
    NQ = Span([ONES] + N + [a & b for a, b in itertools.combinations(N, 2)])
    NX = Span([a & x for a in [ONES] + N for x in [ONES] + X])
    S2 = Span(base + [t[s] for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] <= 2])
    print('dim span{1,x,A1,A2} =', S2.dim(), '; y in it:', [S2.contains(v) for v in Y])
    a2 = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == 2]
    a3 = [s for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == 3]
    S1N = Span(base + [t[s] for s in range(n, n + len(c.gates)) if c.gates[s - n][0] == 8 and al[s] == 1])
    def kind(v):
        r = []
        if NL.contains(v): r.append('N-lin')
        if NQ.contains(v): r.append('N-quad')
        if NX.contains(v): r.append('N-lin*x-lin')
        if S1N.contains(v): r.append('in span(1,x,A1)')
        return ','.join(r) or '-'
    for lab, ands in (('A2', a2), ('A3', a3)):
        print('%s operands:' % lab)
        for s in ands:
            a, b = c.gates[s - n][1:]
            print('   AND(%s | %s) -> deg %d' % (kind(t[a]), kind(t[b]), degree(t[s])))


if __name__ == '__main__':
    main()
