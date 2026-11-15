"""Level-1 quadratic complexity by SAT.

Instance: operand space = F_2^d (the variables v_0..v_{d-1}; constants are irrelevant),
targets t_1..t_r = quadratic forms given as alternating matrices (wedge coordinates, a<b),
free space E (optional list of wedge vectors that may be added for free, e.g. forms that are
available anyway).  Question: do k products l_j * m_j (l_j, m_j linear forms) exist with every
t_o in span(l_j ^ m_j) + E ?  (Modulo linear terms, l*m has alternating part l ^ m, and the
diagonal x_a^2 = x_a is linear, so this is exact for one AND level over affine operands.)

Soundness of symmetry breaking: products are sorted lexicographically by (l_j || m_j) (any
solution can be permuted into this order).  The output combination c is free.

usage as module: solve(d, targets, k, E=()) -> (prods or None, secs)
"""
from __future__ import annotations

import itertools
import time

from pysat.solvers import Solver

from chm import CNF, lex_le


def wedge_index(d):
    return {p: i for i, p in enumerate(itertools.combinations(range(d), 2))}


def form_from_anf(d, quad_monos):
    """quad_monos: iterable of (a, b) a != b monomials x_a x_b -> wedge vector (int)"""
    wi = wedge_index(d); v = 0
    for a, b in quad_monos:
        if a == b: continue
        v ^= 1 << wi[(min(a, b), max(a, b))]
    return v


def anf_quadratic_part(tt, n):
    """truth table (int over 2^n points, bit p = value at p, var j = bit j of p) ->
    set of (a,b) quadratic monomials; asserts degree <= 2."""
    N = 1 << n
    f = [(tt >> p) & 1 for p in range(N)]
    # Moebius transform
    for j in range(n):
        for p in range(N):
            if p & (1 << j): f[p] ^= f[p ^ (1 << j)]
    mons = []
    for p in range(N):
        if f[p]:
            w = bin(p).count('1')
            assert w <= 2, 'degree > 2'
            if w == 2:
                a, b = [j for j in range(n) if (p >> j) & 1]
                mons.append((a, b))
    return mons


def solve(d, targets, k, E=(), solver='cadical153', budget=None):
    f = CNF()
    pairs = list(itertools.combinations(range(d), 2))
    L = [[f.var() for _ in range(d)] for _ in range(k)]
    M = [[f.var() for _ in range(d)] for _ in range(k)]
    for j in range(k - 1):
        lex_le(f, L[j] + M[j], L[j + 1] + M[j + 1])
    Wd = []
    for j in range(k):
        w = []
        for a, b in pairs:
            w.append(f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a])))
        Wd.append(w)
    # work in the quotient Lambda^2 / span(E): coordinates = images of the wedge basis vectors
    Erows = rowspace(list(E))
    npairs = len(pairs)
    imgs = [reduce(1 << i, Erows) for i in range(npairs)]
    tq = [reduce(t, Erows) for t in targets]
    rows = rowspace(imgs + tq)
    piv = sorted(rows); basis = [rows[h] for h in piv]

    def qc(v):
        c = 0
        for i in range(len(piv) - 1, -1, -1):
            if (v >> piv[i]) & 1: v ^= basis[i]; c |= 1 << i
        assert v == 0
        return c
    qi = [qc(v) for v in imgs]; qt = [qc(v) for v in tq]
    q = len(piv)
    I = [[f.xor_list([Wd[j][i] for i in range(npairs) if (qi[i] >> r) & 1]) for r in range(q)]
         for j in range(k)]
    for t in qt:
        c = [f.var() for _ in range(k)]
        for r in range(q):
            v = f.xor_list([f.and2(c[j], I[j][r]) for j in range(k)])
            f.cl.append([v] if (t >> r) & 1 else [-v])
    t0 = time.time()
    with Solver(name=solver, bootstrap_with=f.cl) as s:
        ok = s.solve()
        model = set(l for l in s.get_model() if l > 0) if ok else None
    dt = time.time() - t0
    if not ok: return None, dt
    prods = [(sum(1 << a for a in range(d) if L[j][a] in model),
              sum(1 << a for a in range(d) if M[j][a] in model)) for j in range(k)]
    return prods, dt


def check(d, targets, prods, E=()):
    """exact GF(2) check of a returned cover"""
    pairs = list(itertools.combinations(range(d), 2))
    vecs = []
    for l, m in prods:
        v = 0
        for i, (a, b) in enumerate(pairs):
            if ((l >> a) & (m >> b) & 1) ^ ((l >> b) & (m >> a) & 1): v |= 1 << i
        vecs.append(v)
    span = rowspace(vecs + list(E))
    return all(reduce(t, span) == 0 for t in targets)


def rowspace(vecs):
    rows = {}
    for v in vecs:
        v = reduce(v, rows)
        if v: rows[v.bit_length() - 1] = v
    return rows


def reduce(v, rows):
    while v:
        h = v.bit_length() - 1
        if h in rows: v ^= rows[h]
        else: break
    # full reduction
    for h in sorted(rows, reverse=True):
        if (v >> h) & 1: v ^= rows[h]
    return v
