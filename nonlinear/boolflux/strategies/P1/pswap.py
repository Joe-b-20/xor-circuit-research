#!/usr/bin/env python3
"""P1 last-layer basis swap ("polarisation swap") of final-level AND products.

For a product z = AND(p, q) whose readers are all linear, the same quadratic part is carried by
  z1 = AND(p, p^q) = z ^ p        z2 = AND(p^q, q) = z ^ q
  z3 = AND(~p, q)  = z ^ q        z4 = AND(p, ~q)  = z ^ p        z5 = AND(~p, ~q) = z ^ p ^ q ^ 1
(over GF(2): p(1+p+q) = p + pq, (1+p)(1+q) = 1 + p + q + pq).  Replacing z by z_k and the linear
correction (p, q, or p^q^1) folded into the readers changes one AND operand form and the bottom
linear layer, keeps A and AD (the new operand is linear in the old operands' AND level), and is
outside the gate kernel's single-gate resubstitution neighbourhood.  The folded correction is
then re-synthesised by a timing-driven rebuild of the bottom linear region (hub trb_impl), so the
new bottom is not the old one plus a patch; the gate kernel polishes afterwards (p1run op pswap).
Complemented operands use an XNOR with a constant-free partner when available, else a NOT.

    python3 pswap.py FILE --k 2 --seed 1 --cap D
"""
import random
import sys
from pathlib import Path

PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux import core, targets   # noqa: E402
from boolflux.hub import trb_impl    # noqa: E402

AND, XOR, XNOR, NOT = 8, 6, 9, 3


def final_products(c):
    n = c.n; S = n + len(c.gates)
    al = [0] * S; fo = [[] for _ in range(S)]
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        al[s] = (1 if op == AND else 0) + max(al[a], al[b])
        fo[a].append(s)
        if b != a: fo[b].append(s)
    # a product whose transitive fan-out has no AND
    hasand = [False] * S
    for s in range(S - 1, n - 1, -1):
        hasand[s] = any(c.gates[y - n][0] == AND or hasand[y] for y in fo[s])
    return [s for s in range(n, S) if c.gates[s - n][0] == AND and not hasand[s]]


def swap(c, targets_, rng):
    """targets_: list of (signal of an AND, variant 1..5).  Returns a new circuit (same function)."""
    n = c.n
    tv = dict(targets_)
    gates = []; new = list(range(n))

    def g(op, a, b):
        gates.append((op, a, b)); return n + len(gates) - 1
    for j, (op, a, b) in enumerate(c.gates):
        s = n + j
        A_, B_ = new[a], new[b]
        if s in tv:
            v = tv[s]; p, q = A_, B_
            if v == 1:
                x = g(XOR, p, q); z = g(AND, p, x); corr = g(XOR, z, p)
            elif v == 2:
                x = g(XOR, p, q); z = g(AND, x, q); corr = g(XOR, z, q)
            elif v == 3:
                np_ = g(NOT, p, p); z = g(AND, np_, q); corr = g(XOR, z, q)
            elif v == 4:
                nq = g(NOT, q, q); z = g(AND, p, nq); corr = g(XOR, z, p)
            else:
                np_ = g(NOT, p, p); nq = g(NOT, q, q); z = g(AND, np_, nq)
                t = g(XNOR, p, q); corr = g(XOR, z, t)
            new.append(corr)
        else:
            new.append(g(op, A_, B_))
    return core.Circuit(n, c.m, gates, [new[o] for o in c.outputs], c.name).live()


def kick(c, k, rng, D=None, rebuild=True):
    fp = final_products(c)
    if not fp: return None, {}
    picks = rng.sample(fp, min(k, len(fp)))
    tv = [(s, rng.choice([1, 2, 1, 2, 3, 4, 5])) for s in picks]
    x = swap(c, tv, rng)
    info = {'swaps': [(s, v) for s, v in tv]}
    assert tuple(x.value_table()) == tuple(targets.aes_sbox())
    if rebuild:
        M = core.Model.load('nist'); gd = x.metrics(M)['GD']
        Dr = max(gd, D or 0)
        for kind in ('bottom', 'bottom'):
            y, inf = trb_impl.rebuild(x, Dr, kind, rng)
            if y is not x and tuple(y.value_table()) == tuple(targets.aes_sbox()):
                x = y; info['trb'] = 'bottom'
                break
    return x, info


if __name__ == '__main__':
    import argparse
    ap = argparse.ArgumentParser(); ap.add_argument('file'); ap.add_argument('--k', type=int, default=2)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--cap', type=int, default=None)
    a = ap.parse_args()
    t = Path(a.file).read_text()
    c = core.from_kernel(t) if a.file.endswith('.bfx') else core.read_ncff(t)
    M = core.Model.load('nist'); rng = random.Random(a.seed)
    print('start', [c.metrics(M)[k] for k in ('A', 'AD', 'G', 'GD')], 'final products', len(final_products(c)))
    for i in range(5):
        x, info = kick(c, a.k, rng, a.cap)
        print('kick', [x.metrics(M)[k] for k in ('A', 'AD', 'G', 'GD')], info)
