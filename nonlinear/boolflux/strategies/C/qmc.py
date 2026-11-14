"""One-layer product cover problem ("quadratic MC modulo a free space"), exact SAT model.

Given
  O : list of truth tables (operand basis; operands are GF(2) combinations of O, constants
      are irrelevant when every O element and 1 lie in E),
  E : free space (truth tables that are available by XOR),
  T : target truth tables,
find k products P_j = l_j * m_j (l_j, m_j in span O) and c with
  T_o + sum_j c_oj P_j  in  span E     for every o.

Math (see NOTES.md, section "one-layer cover"): when span O + <1> lies in E, the map
(l, m) -> l*m mod E is GF(2)-bilinear and alternating, so P_j mod E = Phi(l_j ^ m_j) with
Phi : Lambda^2(span O) -> F_2^256 / E linear.  The model is exact for this formulation.
"""
from __future__ import annotations

import itertools
import time

import gf


class Normal:
    """Canonical projection modulo a span (reduced echelon, highest-bit pivots)."""
    def __init__(self, vecs):
        rows = {}
        for v in vecs:
            for h in sorted(rows, reverse=True):
                if (v >> h) & 1: v ^= rows[h]
            if v:
                h = v.bit_length() - 1
                # reduce existing rows by the new one
                for g in list(rows):
                    if (rows[g] >> h) & 1: rows[g] ^= v
                rows[h] = v
        self.rows = rows
        self.order = sorted(rows, reverse=True)

    def nf(self, v):
        for h in self.order:
            if (v >> h) & 1: v ^= self.rows[h]
        return v

    def dim(self):
        return len(self.rows)


def quotient_coords(vecs):
    """Coordinates of the given vectors w.r.t. a basis of their span (list of ints)."""
    sp = gf.Span(); n = 0; out = []
    base_tags = []
    for v in vecs:
        r, t = sp.reduce(v, 0)
        if r:
            sp.piv[r.bit_length() - 1] = (r, t ^ (1 << n)); n += 1
            r2, t2 = sp.reduce(v, 0)
            out.append(t2)
        else:
            out.append(t)
    return out, n


def build_phi(O, E, T):
    """Returns (pairs, phi_cols, tcoords, q): phi_cols[(b,b')] = int over quotient coords."""
    Ef = Normal(list(E))
    d = len(O)
    pairs = list(itertools.combinations(range(d), 2))
    rem = [Ef.nf(O[a] & O[b]) for a, b in pairs]
    trem = [Ef.nf(t) for t in T]
    coords, q = quotient_coords(rem + trem)
    return pairs, coords[:len(pairs)], coords[len(pairs):], q, Ef


class CNF:
    def __init__(self):
        self.n = 0; self.cl = []

    def var(self):
        self.n += 1; return self.n

    def vars(self, k):
        return [self.var() for _ in range(k)]

    def and2(self, a, b):
        p = self.var()
        self.cl += [[-p, a], [-p, b], [p, -a, -b]]
        return p

    def xor2(self, a, b):
        p = self.var()
        self.cl += [[-p, a, b], [-p, -a, -b], [p, -a, b], [p, a, -b]]
        return p

    def xor_list(self, xs):
        """returns literal equal to XOR(xs) (None for empty)"""
        if not xs: return None
        acc = xs[0]
        for x in xs[1:]: acc = self.xor2(acc, x)
        return acc

    def fix(self, lit, val):
        if lit is None:
            if val: self.cl.append([])            # unsat
            return
        self.cl.append([lit] if val else [-lit])


def encode(O, E, T, k, symbreak=True, fixed_c=None, omega=None, free_bits=None):
    pairs, phic, tco, q, Ef = build_phi(O, E, T)
    d = len(O)
    f = CNF()
    if free_bits is None:
        L = [f.vars(d) for _ in range(k)]
    else:
        # L_j = sum_i lam_i * free_bits[i] (free_bits: list of d-bit 0/1 lists spanning a subspace)
        L = []
        for _ in range(k):
            lam = f.vars(len(free_bits))
            L.append([f.xor_list([lam[i] for i in range(len(free_bits)) if free_bits[i][b]]) or 0
                      for b in range(d)])
        L = [[(v if v else _zero(f)) for v in row] for row in L]
    if omega is None:
        M = [f.vars(d) for _ in range(k)]
    else:
        M = [[f.xor_list([L[j][c] for c in range(d) if omega[b][c]]) or _zero(f)
              for b in range(d)] for j in range(k)]
    C = [[f.var() for _ in range(k)] for _ in T]
    # wedge coordinates per product
    Y = []
    for j in range(k):
        w = {}
        for (a, b) in pairs:
            w[(a, b)] = f.xor2(f.and2(L[j][a], M[j][b]), f.and2(L[j][b], M[j][a]))
        yj = []
        for r in range(q):
            terms = [w[pq] for pq, col in zip(pairs, phic) if (col >> r) & 1]
            yj.append(f.xor_list(terms))
        Y.append(yj)
    for o in range(len(T)):
        for r in range(q):
            zs = []
            for j in range(k):
                if Y[j][r] is not None: zs.append(f.and2(C[o][j], Y[j][r]))
            f.fix(f.xor_list(zs), (tco[o] >> r) & 1)
    if symbreak:
        # products ordered by their y vectors? cheap version: order by first operand as integer
        # (lexicographic L_j <= L_{j+1} on bit vectors), and operand l < m within a product.
        for j in range(k - 1):
            lex_le(f, L[j], L[j + 1])
        for j in range(k):
            lex_lt(f, M[j], L[j]) if False else None
    meta = dict(d=d, q=q, pairs=len(pairs), vars=f.n, clauses=len(f.cl))
    return f, (L, M, C), meta


_Z = {}


def _zero(f):
    if id(f) not in _Z:
        z = f.var(); f.cl.append([-z]); _Z[id(f)] = z
    return _Z[id(f)]


def lex_le(f, a, b):
    """a <= b lexicographically, a[0] most significant"""
    # eq_i: prefix equal so far
    eq = None
    for i in range(len(a)):
        # if prefix equal then a_i <= b_i
        if eq is None:
            f.cl.append([-a[i], b[i]])
        else:
            f.cl.append([-eq, -a[i], b[i]])
        e = f.var()   # e <-> (prefix eq and a_i == b_i)
        x = f.xor2(a[i], b[i])
        if eq is None:
            f.cl += [[-e, -x], [e, x]]
        else:
            f.cl += [[-e, eq], [-e, -x], [e, -eq, x]]
        eq = e


def lex_lt(f, a, b):
    lex_le(f, a, b)


def solve(f, solver='cadical153', time_limit=None):
    from pysat.solvers import Solver
    t0 = time.time()
    with Solver(name=solver, bootstrap_with=f.cl) as s:
        ok = s.solve()
        model = s.get_model() if ok else None
    return ok, model, time.time() - t0


def decode(model, LMC, O):
    L, M, C = LMC
    val = set(v for v in model if v > 0)
    prods = []
    for lj, mj in zip(L, M):
        lv = [1 if v in val else 0 for v in lj]; mv = [1 if v in val else 0 for v in mj]
        prods.append((lv, mv))
    cmat = [[1 if v in val else 0 for v in row] for row in C]
    return prods, cmat


def check(prods, cmat, O, E, T):
    Ef = Normal(list(E))
    P = []
    for lv, mv in prods:
        l = 0; m = 0
        for b, (x, y) in enumerate(zip(lv, mv)):
            if x: l ^= O[b]
            if y: m ^= O[b]
        P.append(l & m)
    for o, t in enumerate(T):
        v = t
        for j, p in enumerate(P):
            if cmat[o][j]: v ^= p
        if Ef.nf(v) != 0: return False
    return True
