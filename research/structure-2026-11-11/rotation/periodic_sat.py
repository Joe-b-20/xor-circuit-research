"""Symmetric (equivariant) circuits for Q_m by SAT.

usage: python3 periodic_sat.py m a K [--window] [--out FILE] [--verify M1,M2,...]

A circuit for Q_m is sigma-invariant, sigma(c, j) = (c + a, j + 1), if its set of gate equations is
mapped to itself by sigma (a = 0: the block shift; a = 1: the "screw"; a*m must be 0 mod 4).  Such a
circuit consists of K gate orbits; orbit i has the base gate g_i and the copies sigma^d g_i, d in Z_m
(orbits are free because sigma^d moves every block for 0 < d < m).  The quotient of the dependency
relation must be acyclic, so the orbits can be numbered such that every operand of g_i is an input
or a copy sigma^d g_i' with i' < i.  The four output orbits are represented by o(0,0)..o(3,0), and
after re-basing an orbit (replacing g_i by a copy) we may assume: some base gate equals o(kappa, 0)
for each kappa, and every base gate that is not an output has at least one operand based at d = 0
(an input of block 0 or a copy with d = 0).  The encoding is complete for sigma-invariant circuits
with K orbits (m*K gates) under these normalisations.

--window : instead of all shifts d in Z_m use only d in {-1,0,1} for both operands, inputs of blocks
           {-1,0,1}, and force every base mask to vanish outside blocks {-2..2} (needs m >= 7); a
           solution is then a pattern on the infinite line and gives a circuit for every Q_M.
--verify : unfold the pattern (shifts lifted to (-m/2, m/2]) on Z_M and verify it computes Q_M.
"""
import sys
import time

from pysat.solvers import Solver

import qm


def sig(bitidx, a, d, m):
    c, j = bitidx % 4, bitidx // 4
    return 4 * ((j + d) % m) + ((c + a * d) % 4)


def encode(m, a, K, window=False):
    n = 4 * m
    nv = [0]
    cl = []

    def new():
        nv[0] += 1
        return nv[0]

    shifts = [-1, 0, 1] if window else list(range(m))
    in_blocks = [m - 1, 0, 1] if window else list(range(m))
    val = [[new() for _ in range(n)] for _ in range(K)]
    targets = [qm.rows(m)[kappa] for kappa in range(4)]
    out = [[new() for _ in range(4)] for _ in range(K)]
    src = []
    sel = []
    for i in range(K):
        sources = [("in", c, j) for j in in_blocks for c in range(4)]
        sources += [("g", i2, d) for i2 in range(i) for d in shifts]
        src.append(sources)
        A = [new() for _ in sources]
        B = [new() for _ in sources]
        sel.append((A, B))
        S = len(sources)
        cl.append(A[:S - 1])
        cl.append(B[1:])
        cl.append([-A[S - 1]])
        cl.append([-B[0]])
        for s in range(S):
            for s2 in range(s + 1, S):
                cl.append([-A[s], -A[s2]])
                cl.append([-B[s], -B[s2]])
        for s in range(S):
            for s2 in range(s + 1):
                cl.append([-A[s], -B[s2]])
        pa = [new() for _ in range(n)]
        pb = [new() for _ in range(n)]
        for s, sc in enumerate(sources):
            if sc[0] == "in":
                bidx = 4 * sc[2] + sc[1]
                for b in range(n):
                    cl.append([-A[s], pa[b] if b == bidx else -pa[b]])
                    cl.append([-B[s], pb[b] if b == bidx else -pb[b]])
            else:
                _, i2, d = sc
                for b in range(n):
                    b2 = sig(b, a, d, m)      # bit b of g_i2 moves to bit b2
                    cl.append([-A[s], -val[i2][b], pa[b2]])
                    cl.append([-A[s], val[i2][b], -pa[b2]])
                    cl.append([-B[s], -val[i2][b], pb[b2]])
                    cl.append([-B[s], val[i2][b], -pb[b2]])
        for b in range(n):
            v = val[i][b]
            cl.append([-v, pa[b], pb[b]])
            cl.append([-v, -pa[b], -pb[b]])
            cl.append([v, -pa[b], pb[b]])
            cl.append([v, pa[b], -pb[b]])
        cl.append(val[i][:])
        if window:
            for b in range(n):
                j = b // 4
                if j not in (m - 2, m - 1, 0, 1, 2):
                    cl.append([-val[i][b]])
        # outputs
        for kappa in range(4):
            for b in range(n):
                cl.append([-out[i][kappa], val[i][b] if (targets[kappa] >> b) & 1 else -val[i][b]])
        # non-output orbit: at least one operand based at 0
        based = [s for s, sc in enumerate(sources) if sc[2] == 0]
        cl.append(list(out[i]) + [A[s] for s in based] + [B[s] for s in based])
    for kappa in range(4):
        cl.append([out[i][kappa] for i in range(K)])
    # every orbit is used or is an output
    for i in range(K):
        c2 = list(out[i])
        for i3 in range(i + 1, K):
            for s, sc in enumerate(src[i3]):
                if sc[0] == "g" and sc[1] == i:
                    c2.append(sel[i3][0][s])
                    c2.append(sel[i3][1][s])
        cl.append(c2)
    return cl, val, sel, src, out


def solve(m, a, K, window=False):
    cl, val, sel, src, out = encode(m, a, K, window)
    with Solver(name="cadical153", bootstrap_with=cl) as S:
        if not S.solve():
            return None
        model = set(x for x in S.get_model() if x > 0)
    pattern = []
    for i in range(K):
        A, B = sel[i]
        sa = next(sc for s, sc in enumerate(src[i]) if A[s] in model)
        sb = next(sc for s, sc in enumerate(src[i]) if B[s] in model)
        pattern.append((sa, sb))
    return pattern


def lift(d, m):
    d %= m
    return d if d <= m // 2 else d - m


def unfold(pattern, m, a, M):
    """Circuit on Z_M: gate (i, j) = sigma^j g_i, listed orbit by orbit."""
    K = len(pattern)
    n = 4 * M
    gates = []

    def ref(sc, j):
        if sc[0] == "in":
            c, j0 = sc[1], lift(sc[2], m)
            return 4 * ((j0 + j) % M) + ((c + a * j) % 4)
        _, i2, d = sc
        return n + i2 * M + ((lift(d, m) + j) % M)

    for i in range(K):
        for j in range(M):
            gates.append((ref(pattern[i][0], j), ref(pattern[i][1], j)))
    return n, gates


def fmt(sc, m):
    if sc[0] == "in":
        return f"in({sc[1]},{lift(sc[2], m):+d})"
    return f"g{sc[1]}[{lift(sc[2], m):+d}]"


def main():
    args = sys.argv[1:]
    m, a, K = int(args[0]), int(args[1]), int(args[2])
    assert (a * m) % 4 == 0
    window = "--window" in args
    t0 = time.time()
    pattern = solve(m, a, K, window)
    tag = f"Q_{m}, sigma = (c+{a}, j+1), K = {K} orbits ({m * K} gates)" + (", window" if window else "")
    if pattern is None:
        print(f"{tag}: UNSAT  ({time.time() - t0:.1f} s)")
        return
    print(f"{tag}: SAT  ({time.time() - t0:.1f} s)")
    for i, (sa, sb) in enumerate(pattern):
        print(f"   g{i} = {fmt(sa, m)} + {fmt(sb, m)}")
    Ms = [m]
    if "--verify" in args:
        Ms = [int(x) for x in args[args.index("--verify") + 1].split(",")]
    for M in Ms:
        if (a * M) % 4:
            continue
        n, gates = unfold(pattern, m, a, M)
        ok = qm.computes(n, gates, qm.rows(M))
        print(f"   unfolded on Z_{M}: {len(gates)} gates, computes Q_{M}: {ok}")
        if ok and "--out" in args and M == Ms[0]:
            qm.write_circuit(args[args.index("--out") + 1], n, gates,
                             f"Q_{M}: {len(gates)} gates; sigma-invariant pattern (a = {a}, K = {K}) found by periodic_sat.py\n"
                             + "\n".join(f"g{i} = {fmt(sa, m)} + {fmt(sb, m)}" for i, (sa, sb) in enumerate(pattern)))


if __name__ == "__main__":
    main()
