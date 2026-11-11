"""Double maps D_T : (u, v) -> (u + T w, v + T w), w = u + v, and exact XOR-gate optima by SAT.

Library; usage from the other scripts in this directory (python3 opt_small.py ..., etc.).

Conventions: T is a tuple of m row masks over w_0..w_(m-1) (bit k of row j = T[j][k]).
Inputs of D_T: u_k = bit k, v_k = bit m + k.  Outputs: o_j = u_j + (T w)_j, o'_j = v_j + (T w)_j.
The diagonal of T is irrelevant up to swapping o_j and o'_j, so T is normalised to zero diagonal.
"""
import itertools
import time

from pysat.solvers import Solver


# ---------------------------------------------------------------- matrices
def zero_diag(T):
    return tuple(r & ~(1 << j) for j, r in enumerate(T))


def dmap_rows(T):
    m = len(T)
    T = zero_diag(T)
    rows = []
    for j in range(m):
        rows.append((1 << j) | T[j] | (T[j] << m))
    for j in range(m):
        rows.append((1 << (m + j)) | T[j] | (T[j] << m))
    return rows


def transpose(T):
    m = len(T)
    return tuple(sum(((T[k] >> j) & 1) << k for k in range(m)) for j in range(m))


def conj(T, perm):
    """Relabel index k -> perm[k]."""
    m = len(T)
    out = [0] * m
    for j in range(m):
        r = 0
        for k in range(m):
            if (T[j] >> k) & 1:
                r |= 1 << perm[k]
        out[perm[j]] = r
    return tuple(out)


def canon(T):
    """Canonical representative under simultaneous permutation and transposition."""
    m = len(T)
    T = zero_diag(T)
    best = None
    for S in (T, transpose(T)):
        for perm in itertools.permutations(range(m)):
            c = conj(S, perm)
            if best is None or c < best:
                best = c
    return best


def reduced(T):
    """Zero diagonal, no zero row, no zero column."""
    T = zero_diag(T)
    return all(T) and all(transpose(T))


def rank_f2(vecs):
    basis = []
    for v in vecs:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)
    return len(basis)


def tstr(T):
    m = len(T)
    T = zero_diag(T)
    parts = []
    for j in range(m):
        ks = [str(k) for k in range(m) if (T[j] >> k) & 1]
        parts.append("".join(ks) if ks else "-")
    return "|".join(parts)


def parse_t(s):
    rows = []
    for part in s.split("|"):
        r = 0
        if part != "-":
            for ch in part:
                r |= 1 << int(ch)
        rows.append(r)
    return tuple(rows)


# ---------------------------------------------------------------- partitions
def set_partitions(n):
    """All set partitions of range(n) as lists of block indices (restricted growth strings)."""
    a = [0] * n

    def rec(i, mx):
        if i == n:
            yield tuple(a)
            return
        for b in range(mx + 2):
            a[i] = b
            yield from rec(i + 1, max(mx, b))

    yield from rec(1, 0)


def valid_partitions(T, min_blocks=1):
    """Partitions of the 2m inputs such that every output row is odd on exactly one block."""
    m = len(T)
    rows = dmap_rows(T)
    n = 2 * m
    out = []
    for rg in set_partitions(n):
        c = max(rg) + 1
        if c < min_blocks:
            continue
        masks = [0] * c
        for i, b in enumerate(rg):
            masks[b] |= 1 << i
        ok = True
        for r in rows:
            odd = 0
            for bm in masks:
                if bin(r & bm).count("1") & 1:
                    odd += 1
                    if odd > 1:
                        break
            if odd != 1:
                ok = False
                break
        if ok:
            out.append(rg)
    return out


# ---------------------------------------------------------------- SAT
class Enc:
    def __init__(self):
        self.nv = 0
        self.clauses = []

    def new(self):
        self.nv += 1
        return self.nv

    def add(self, cl):
        self.clauses.append(cl)


def encode(rows, n, k, pair_m=None, extra=None, break_sym=True):
    """CNF for: a k-gate XOR circuit over n inputs computes every mask in rows.

    pair_m = m : restrict to circuits whose final partition refines to the pair partition, i.e. every
    gate mask has u_k-bit != v_k-bit for at most one k (even masks in W, odd masks on one sheet).
    Returns (Enc, A, B, val, out) for decoding.
    """
    E = Enc()
    S = n + k
    A = [None] * S
    B = [None] * S
    val = [[None] * n for _ in range(S)]
    for g in range(n, S):
        A[g] = [E.new() for _ in range(g)]
        B[g] = [E.new() for _ in range(g)]
        for i in range(n):
            val[g][i] = E.new()
        # exactly one first operand, one second operand, first < second
        E.add(A[g][:g - 1])
        E.add(B[g][1:])
        E.add([-A[g][g - 1]])
        E.add([-B[g][0]])
        for s in range(g):
            for s2 in range(s + 1, g):
                E.add([-A[g][s], -A[g][s2]])
                E.add([-B[g][s], -B[g][s2]])
        # ladder: A index < B index
        for s in range(g):
            for s2 in range(s + 1):
                E.add([-A[g][s], -B[g][s2]])
        pa = [E.new() for _ in range(n)]
        pb = [E.new() for _ in range(n)]
        for s in range(g):
            for i in range(n):
                if s < n:
                    E.add([-A[g][s], pa[i] if i == s else -pa[i]])
                    E.add([-B[g][s], pb[i] if i == s else -pb[i]])
                else:
                    E.add([-A[g][s], -val[s][i], pa[i]])
                    E.add([-A[g][s], val[s][i], -pa[i]])
                    E.add([-B[g][s], -val[s][i], pb[i]])
                    E.add([-B[g][s], val[s][i], -pb[i]])
        for i in range(n):
            v = val[g][i]
            E.add([-v, pa[i], pb[i]])
            E.add([-v, -pa[i], -pb[i]])
            E.add([v, -pa[i], pb[i]])
            E.add([v, pa[i], -pb[i]])
        E.add([val[g][i] for i in range(n)])  # nonzero
    # outputs
    out = []
    for r in rows:
        sel = [E.new() for _ in range(k)]
        out.append(sel)
        E.add(sel)
        for gi in range(k):
            g = n + gi
            for i in range(n):
                E.add([-sel[gi], val[g][i] if (r >> i) & 1 else -val[g][i]])
    # every gate used
    for g in range(n, S):
        cl = [o[g - n] for o in out]
        for g2 in range(g + 1, S):
            cl.append(A[g2][g])
            cl.append(B[g2][g])
        E.add(cl)
    if break_sym:
        for g in range(n, S - 1):
            # B_g <= B_{g+1}
            for s in range(g):
                for s2 in range(s):
                    E.add([-B[g][s], -B[g + 1][s2]])
            eq = E.new()
            for s in range(g):
                E.add([-B[g][s], -B[g + 1][s], eq])
            for a in range(g):
                for a2 in range(a + 1):
                    E.add([-eq, -A[g][a], -A[g + 1][a2]])
    if pair_m is not None:
        m = pair_m
        for g in range(n, S):
            d = []
            for kk in range(m):
                x = E.new()
                a, b = val[g][kk], val[g][m + kk]
                E.add([-x, a, b])
                E.add([-x, -a, -b])
                E.add([x, -a, b])
                E.add([x, a, -b])
                d.append(x)
            for i in range(m):
                for j in range(i + 1, m):
                    E.add([-d[i], -d[j]])
    if extra is not None:
        extra(E, A, B, val, out, n, k)
    return E, A, B, val, out


def solve(rows, n, k, pair_m=None, extra=None, solver="cadical153", break_sym=True, time_limit=None):
    """Returns (status, circuit) with status True/False/None; circuit = list of (a, b) operand indices."""
    E, A, B, val, out = encode(rows, n, k, pair_m=pair_m, extra=extra, break_sym=break_sym)
    with Solver(name=solver, bootstrap_with=E.clauses) as s:
        res = s.solve()
        if not res:
            return res, None
        model = set(l for l in s.get_model() if l > 0)
    circ = []
    for g in range(n, n + k):
        a = next(i for i in range(g) if A[g][i] in model)
        b = next(i for i in range(g) if B[g][i] in model)
        circ.append((a, b))
    return True, circ


def masks_of(circ, n):
    vals = [1 << i for i in range(n)]
    for a, b in circ:
        vals.append(vals[a] ^ vals[b])
    return vals


def check(circ, rows, n):
    vals = masks_of(circ, n)
    return all(r in vals for r in rows)


def optimum(rows, n, lo, hi, pair_m=None, extra=None, verbose=False):
    """Least k in [lo, hi] with a circuit; proves UNSAT below. Returns (k, circuit)."""
    for k in range(lo, hi + 1):
        t0 = time.time()
        res, circ = solve(rows, n, k, pair_m=pair_m, extra=extra)
        if verbose:
            print(f"   k={k}: {res} ({time.time() - t0:.1f}s)", flush=True)
        if res:
            assert check(circ, rows, n)
            return k, circ
    return None, None


# ---------------------------------------------------------------- circuit profile
def profile(circ, n):
    """(x, y, h_plus_outputs) and the final partition of a circuit."""
    vals = masks_of(circ, n)
    par = [bin(v).count("1") & 1 for v in vals]
    x = y = odd = 0
    for gi, (a, b) in enumerate(circ):
        if par[a] and par[b]:
            x += 1
        elif not par[a] and not par[b]:
            y += 1
        else:
            odd += 1
    evens = [v for v, p in zip(vals, par) if not p]
    basis = []
    for v in evens:
        for b in basis:
            v = min(v, v ^ b)
        if v:
            basis.append(v)

    def inspan(v):
        for b in basis:
            v = min(v, v ^ b)
        return v == 0

    blocks, seen = [], set()
    for i in range(n):
        if i in seen:
            continue
        blk = [j for j in range(n) if j == i or inspan((1 << i) ^ (1 << j))]
        seen.update(blk)
        blocks.append(blk)
    return x, y, odd, blocks
