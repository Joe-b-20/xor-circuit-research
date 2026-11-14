"""Exact multiplicative complexity of a small vectorial function by SAT (Courtois-Hulme-Mourouzis
encoding as in Stoffelen 2016, sec. 3.2): k ANDs, each operand an affine combination of inputs
and earlier AND outputs, outputs affine combinations of inputs and AND outputs.

usage: python3 mc_small.py inv16 K       (x -> x^14 in GF(16) = GF(2)[t]/(t^4+t+1))
"""
from __future__ import annotations

import json
import sys
import time

import qmc


def gf16_inv_table():
    def mul(a, b):
        r = 0
        while b:
            if b & 1: r ^= a
            b >>= 1; a <<= 1
            if a & 16: a ^= 0x13
        return r
    inv = [0] * 16
    for a in range(1, 16):
        for b in range(1, 16):
            if mul(a, b) == 1: inv[a] = b
    return inv


def encode(table, n, m, k):
    f = qmc.CNF()
    T = qmc._zero(f)
    one = -T
    A = []   # operand coefficient vars: for AND i, side s: [const, x_0..x_{n-1}, t_0..t_{i-1}]
    for i in range(k):
        A.append([f.vars(1 + n + i) for _ in range(2)])
    B = [f.vars(1 + n + k) for _ in range(m)]
    # symmetry: operand 0 lex <= operand 1 is not needed; keep it simple
    for p in range(1 << n):
        xs = [(p >> (n - 1 - j)) & 1 for j in range(n)]
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
            f.fix(f.xor_list(terms), (y >> (m - 1 - o)) & 1)
    return f


def main():
    which, k = sys.argv[1], int(sys.argv[2])
    if which == 'inv16':
        table, n, m = gf16_inv_table(), 4, 4
    else:
        raise SystemExit('unknown')
    f = encode(table, n, m, k)
    ok, model, dt = qmc.solve(f, sys.argv[3] if len(sys.argv) > 3 else 'cadical153')
    print(json.dumps({'fn': which, 'k': k, 'sat': ok, 'secs': round(dt, 1), 'vars': f.n,
                      'clauses': len(f.cl)}), flush=True)


if __name__ == '__main__':
    main()
