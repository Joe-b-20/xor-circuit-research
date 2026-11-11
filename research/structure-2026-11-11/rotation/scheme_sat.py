"""Sheet schemes: can one sheet be completed with 10 gates, given three even vectors of the previous block?

usage: python3 scheme_sat.py P O [K]        e.g.  python3 scheme_sat.py s1,d1,t d0,s0,d1
       python3 scheme_sat.py --period1 [TIMEOUT]     tries O = rot^r(P) for every basis P (r = 0..3)

Blocks a (previous, inputs 0..3) and b (own, inputs 4..7).  Base signals: the 8 inputs and the three
vectors of P on block a (given, cost 0).  Question: are there K (default 10) gates computing the four
outputs E_c(b) + s_c(a) and the three vectors of O on block b?  A SAT answer is a "sheet scheme"
P -> O.  Chaining schemes along a cyclic sequence of bases P_0 -> P_1 -> ... -> P_(m-1) -> P_0 gives a
circuit for Q_m with 10m gates (the three vectors of P_j are computed by the gates of sheet j).
Rotation r acts by c -> c + r on both blocks and maps schemes to schemes.
Names: s0..s3 = adjacent pairs {c, c+1}; d0 = {0,2}, d1 = {1,3}; t = all four.
"""
import itertools
import subprocess
import sys
import time

from pysat.solvers import Solver

VEC = {"s0": 0b0011, "s1": 0b0110, "s2": 0b1100, "s3": 0b1001, "d0": 0b0101, "d1": 0b1010, "t": 0b1111}
NAME = {v: k for k, v in VEC.items()}


def rot(v, r):
    r %= 4
    return ((v << r) | (v >> (4 - r))) & 15


def targets_out():
    res = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        sc = (1 << c) | (1 << ((c + 1) % 4))
        res.append((Ec << 4) | sc)
    return res


def encode(base, targets, k, nbits=8):
    nv = [0]
    cl = []

    def new():
        nv[0] += 1
        return nv[0]

    nb = len(base)
    S = nb + k
    A = [None] * S
    B = [None] * S
    val = [None] * S
    for g in range(nb, S):
        A[g] = [new() for _ in range(g)]
        B[g] = [new() for _ in range(g)]
        val[g] = [new() for _ in range(nbits)]
        cl.append(A[g][:g - 1])
        cl.append(B[g][1:])
        cl.append([-A[g][g - 1]])
        cl.append([-B[g][0]])
        for s in range(g):
            for s2 in range(s + 1, g):
                cl.append([-A[g][s], -A[g][s2]])
                cl.append([-B[g][s], -B[g][s2]])
        for s in range(g):
            for s2 in range(s + 1):
                cl.append([-A[g][s], -B[g][s2]])
        pa = [new() for _ in range(nbits)]
        pb = [new() for _ in range(nbits)]
        for s in range(g):
            for i in range(nbits):
                if s < nb:
                    bitv = (base[s] >> i) & 1
                    cl.append([-A[g][s], pa[i] if bitv else -pa[i]])
                    cl.append([-B[g][s], pb[i] if bitv else -pb[i]])
                else:
                    cl.append([-A[g][s], -val[s][i], pa[i]])
                    cl.append([-A[g][s], val[s][i], -pa[i]])
                    cl.append([-B[g][s], -val[s][i], pb[i]])
                    cl.append([-B[g][s], val[s][i], -pb[i]])
        for i in range(nbits):
            v = val[g][i]
            cl.append([-v, pa[i], pb[i]])
            cl.append([-v, -pa[i], -pb[i]])
            cl.append([v, -pa[i], pb[i]])
            cl.append([v, pa[i], -pb[i]])
        cl.append(val[g][:])
    out = []
    for r in targets:
        sel = [new() for _ in range(k)]
        out.append(sel)
        cl.append(sel)
        for gi in range(k):
            g = nb + gi
            for i in range(nbits):
                cl.append([-sel[gi], val[g][i] if (r >> i) & 1 else -val[g][i]])
    for g in range(nb, S):
        c2 = [o[g - nb] for o in out]
        for g2 in range(g + 1, S):
            c2.append(A[g2][g])
            c2.append(B[g2][g])
        cl.append(c2)
    for g in range(nb, S - 1):
        for s in range(g):
            for s2 in range(s):
                cl.append([-B[g][s], -B[g + 1][s2]])
        for s in range(g):
            for a in range(g):
                for a2 in range(a + 1):
                    cl.append([-B[g][s], -B[g + 1][s], -A[g][a], -A[g + 1][a2]])
    return cl, A, B


def solve(P, O, k=10):
    base = [1 << i for i in range(8)] + list(P)          # P on block a = low nibble
    targets = targets_out() + [o << 4 for o in O]        # O on block b = high nibble
    cl, A, B = encode(base, targets, k)
    nb = len(base)
    with Solver(name="cadical153", bootstrap_with=cl) as S:
        if not S.solve():
            return None
        model = set(x for x in S.get_model() if x > 0)
    gates = []
    for g in range(nb, nb + k):
        a = next(i for i in range(g) if A[g][i] in model)
        b = next(i for i in range(g) if B[g][i] in model)
        gates.append((a, b))
    vals = list(base)
    for a, b in gates:
        vals.append(vals[a] ^ vals[b])
    assert all(t in vals[nb:] for t in targets)
    return base, gates, vals


def describe(v):
    lo, hi = v & 15, v >> 4
    names = {**NAME, 1: "e0", 2: "e1", 4: "e2", 8: "e3", 14: "E0", 13: "E1", 11: "E2", 7: "E3"}
    parts = []
    if lo:
        parts.append("a:" + names[lo])
    if hi:
        parts.append("b:" + names[hi])
    return " ".join(parts)


def parse(sx):
    return [VEC[x] for x in sx.split(",")]


def bases():
    res = []
    for tri in itertools.combinations(sorted(VEC.values()), 3):
        if tri[0] ^ tri[1] != tri[2]:
            res.append(tri)
    return res


def main():
    args = sys.argv[1:]
    if args[0] == "--period1":
        tmo = int(args[1]) if len(args) > 1 else 30
        seen = set()
        for P in bases():
            orbit = {tuple(sorted(rot(v, r) for v in P)) for r in range(4)}
            if tuple(sorted(P)) != min(orbit):
                continue
            for r in range(4):
                O = tuple(sorted(rot(v, r) for v in P))
                if (P, O) in seen:
                    continue
                seen.add((P, O))
                ps = ",".join(NAME[v] for v in P)
                os_ = ",".join(NAME[v] for v in O)
                t0 = time.time()
                try:
                    res = subprocess.run([sys.executable, __file__, ps, os_], capture_output=True, text=True, timeout=tmo)
                    first = res.stdout.splitlines()[0] if res.stdout else "?"
                except subprocess.TimeoutExpired:
                    first = "TIMEOUT"
                print(f"P = {ps:<9} O = rot^{r}(P) = {os_:<9}: {first}  ({time.time() - t0:.1f} s)", flush=True)
        return
    P, O = parse(args[0]), parse(args[1])
    k = int(args[2]) if len(args) > 2 else 10
    res = solve(P, O, k)
    if res is None:
        print("UNSAT")
        return
    base, gates, vals = res
    print("SAT")
    nb = len(base)

    def nm(i):
        if i < 8:
            return f"{'ab'[i // 4]}{i % 4}"
        if i < nb:
            return "P:" + NAME[base[i]]
        return f"g{i - nb}"

    touts = targets_out()
    for gi, (a, b) in enumerate(gates):
        v = vals[nb + gi]
        tag = f"  = OUT {touts.index(v)}" if v in touts else ""
        print(f"   g{gi} = {nm(a)} + {nm(b)}   [{describe(v)}]{tag}")


if __name__ == "__main__":
    main()
