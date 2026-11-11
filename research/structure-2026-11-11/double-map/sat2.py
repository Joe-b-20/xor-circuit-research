"""Exact XOR-gate optimum of a double map with the parity structure given to the solver.

usage: python3 sat2.py "1|0|3|02" [kmin kmax] [--profiles] [--pair]
       python3 sat2.py m2 25 25

A circuit with k gates for a reduced T (zero diagonal, no zero row/column) has 2m odd output gates and
x >= m gates with two odd operands (partition lemma + Lemma A of REPORT.md).  The encoding is the plain
straight-line-program encoding (operand selectors, mask bits) plus one extra mask column carrying the
parity, and the valid redundant constraint  #(odd+odd gates) >= m.  --profiles solves each count profile
(x, y, h) with x + y + h = k - 2m separately and prints which are satisfiable.  --pair restricts to
circuits whose even masks lie in W (final partition = pair partition).
Symmetry breaking: operands ordered; consecutive gates that are independent are in lexicographic order.
"""
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

import dmap
import geom


def encode(rows, n, k, m, x_range=None, y_range=None, pair=False, min_x=None):
    nv = [0]
    cls = []

    def new():
        nv[0] += 1
        return nv[0]

    S = n + k
    C = n + 1                      # mask columns + parity column
    A = [None] * S
    B = [None] * S
    val = [[None] * C for _ in range(S)]
    isx = []
    isy = []
    for g in range(n, S):
        A[g] = [new() for _ in range(g)]
        B[g] = [new() for _ in range(g)]
        for i in range(C):
            val[g][i] = new()
        cls.append(A[g][:g - 1])
        cls.append(B[g][1:])
        cls.append([-A[g][g - 1]])
        cls.append([-B[g][0]])
        for s in range(g):
            for s2 in range(s + 1, g):
                cls.append([-A[g][s], -A[g][s2]])
                cls.append([-B[g][s], -B[g][s2]])
        for s in range(g):
            for s2 in range(s + 1):
                cls.append([-A[g][s], -B[g][s2]])
        pa = [new() for _ in range(C)]
        pb = [new() for _ in range(C)]
        for s in range(g):
            for i in range(C):
                if s < n:
                    bit = (i == s) or (i == n)
                    cls.append([-A[g][s], pa[i] if bit else -pa[i]])
                    cls.append([-B[g][s], pb[i] if bit else -pb[i]])
                else:
                    cls.append([-A[g][s], -val[s][i], pa[i]])
                    cls.append([-A[g][s], val[s][i], -pa[i]])
                    cls.append([-B[g][s], -val[s][i], pb[i]])
                    cls.append([-B[g][s], val[s][i], -pb[i]])
        for i in range(C):
            v = val[g][i]
            cls.append([-v, pa[i], pb[i]])
            cls.append([-v, -pa[i], -pb[i]])
            cls.append([v, -pa[i], pb[i]])
            cls.append([v, pa[i], -pb[i]])
        cls.append([val[g][i] for i in range(n)])
        # parity column consistent with the mask: enforced implicitly (linear), no clause needed
        xg, yg = new(), new()
        cls.append([-xg, pa[n]])
        cls.append([-xg, pb[n]])
        cls.append([xg, -pa[n], -pb[n]])
        cls.append([-yg, -pa[n]])
        cls.append([-yg, -pb[n]])
        cls.append([yg, pa[n], pb[n]])
        isx.append(xg)
        isy.append(yg)
        if pair:
            d = []
            for kk in range(m):
                z = new()
                a, b = val[g][kk], val[g][m + kk]
                cls.append([-z, a, b])
                cls.append([-z, -a, -b])
                cls.append([z, -a, b])
                cls.append([z, a, -b])
                d.append(z)
            for i in range(m):
                for j in range(i + 1, m):
                    cls.append([-d[i], -d[j]])
    out = []
    for r in rows:
        sel = [new() for _ in range(k)]
        out.append(sel)
        cls.append(sel)
        for gi in range(k):
            g = n + gi
            for i in range(n):
                cls.append([-sel[gi], val[g][i] if (r >> i) & 1 else -val[g][i]])
            cls.append([-sel[gi], val[g][n]])
    for g in range(n, S):
        cl = [o[g - n] for o in out]
        for g2 in range(g + 1, S):
            cl.append(A[g2][g])
            cl.append(B[g2][g])
        cls.append(cl)
    for g in range(n, S - 1):
        for s in range(g):
            for s2 in range(s):
                cls.append([-B[g][s], -B[g + 1][s2]])
        eq = new()
        for s in range(g):
            cls.append([-B[g][s], -B[g + 1][s], eq])
        for a in range(g):
            for a2 in range(a + 1):
                cls.append([-eq, -A[g][a], -A[g + 1][a2]])

    def card(lits, lo, hi):
        if lo is not None and lo > 0:
            enc = CardEnc.atleast(lits=lits, bound=lo, top_id=nv[0], encoding=EncType.seqcounter)
            nv[0] = max(nv[0], enc.nv)
            cls.extend(enc.clauses)
        if hi is not None and hi < len(lits):
            enc = CardEnc.atmost(lits=lits, bound=hi, top_id=nv[0], encoding=EncType.seqcounter)
            nv[0] = max(nv[0], enc.nv)
            cls.extend(enc.clauses)

    if x_range is not None:
        card(isx, x_range[0], x_range[1])
    elif min_x:
        card(isx, min_x, None)
    if y_range is not None:
        card(isy, y_range[0], y_range[1])
    return cls, A, B


def solve(rows, n, k, m, **kw):
    cls, A, B = encode(rows, n, k, m, **kw)
    with Solver(name="cadical153", bootstrap_with=cls) as s:
        res = s.solve()
        if not res:
            return False, None
        model = set(l for l in s.get_model() if l > 0)
    circ = []
    for g in range(n, n + k):
        a = next(i for i in range(g) if A[g][i] in model)
        b = next(i for i in range(g) if B[g][i] in model)
        circ.append((a, b))
    assert dmap.check(circ, rows, n)
    return True, circ


def optimum(T, kmin=None, kmax=None, pair=False, verbose=False):
    """For reduced T. Returns (L, circuit)."""
    m = len(T)
    n = 2 * m
    rows = dmap.dmap_rows(T)
    kmin = kmin or 3 * m
    kmax = kmax or 4 * m + 4
    for k in range(kmin, kmax + 1):
        t0 = time.time()
        res, circ = solve(rows, n, k, m, min_x=m, pair=pair)
        if verbose:
            print(f"   k={k}: {'SAT' if res else 'UNSAT'} ({time.time() - t0:.1f}s)", flush=True)
        if res:
            return k, circ
    return None, None


def main():
    arg = sys.argv[1]
    T = geom.m2_T() if arg == "m2" else dmap.parse_t(arg)
    m = len(T)
    n = 2 * m
    nums = [int(a) for a in sys.argv[2:] if not a.startswith("--")]
    kmin = nums[0] if nums else 3 * m
    kmax = nums[1] if len(nums) > 1 else 4 * m + 4
    pair = "--pair" in sys.argv
    rows = dmap.dmap_rows(T)
    if "--profiles" in sys.argv:
        for k in range(kmin, kmax + 1):
            e = k - 3 * m
            anysat = False
            for x in range(m, m + e + 1):
                for y in range(0, m + e - x + 1):
                    h = m + e - x - y
                    t0 = time.time()
                    res, circ = solve(rows, n, k, m, x_range=(x, x), y_range=(y, y), pair=pair)
                    print(f"k={k} (x,y,h)=({x},{y},{h}): {'SAT' if res else 'UNSAT'} ({time.time() - t0:.1f}s)", flush=True)
                    anysat |= res
            if anysat:
                break
        return
    L, circ = optimum(T, kmin, kmax, pair=pair, verbose=True)
    if L is None:
        print(f"no circuit with {kmin}..{kmax} gates" + (" in the pair partition" if pair else ""))
        return
    print("L =", L, "eps =", L - 3 * m)
    x, y, odd, blocks = dmap.profile(circ, n)
    print("profile x,y,h =", x, y, odd - 2 * m, "blocks:", blocks)
    print("circuit:", circ)


if __name__ == "__main__":
    main()
