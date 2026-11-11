"""Exact XOR-gate optimum of a small linear map by SAT (pysat, CaDiCaL 1.5.3).

usage: python3 slp_sat.py m KLO KHI [--T rows] [--out FILE] [--tlimit SECONDS]
  m            the rotation model Q_m (n = 4m inputs), or with --T j:k,j:k,... extra entries T[j][k]=1
               added to the shift (Q_T).
  KLO KHI      tries k = KLO..KHI gates in increasing order; UNSAT for k and SAT for k+1 proves L = k+1.
The encoding is complete for circuits in the model of PROOF.md section 0 (any fan-out, any depth,
cancellation); the only symmetry breaking is the ordering of gates by (larger operand, smaller operand),
which every circuit admits after renumbering its gates (see REPORT.md, section 2).
"""
import sys
import time

from pysat.solvers import Solver

import qm


class Enc:
    def __init__(self):
        self.nv = 0
        self.clauses = []

    def new(self):
        self.nv += 1
        return self.nv

    def add(self, cl):
        self.clauses.append(cl)


def encode(targets, n, k, distinct=True):
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
        E.add(A[g][:g - 1])
        E.add(B[g][1:])
        E.add([-A[g][g - 1]])
        E.add([-B[g][0]])
        for s in range(g):
            for s2 in range(s + 1, g):
                E.add([-A[g][s], -A[g][s2]])
                E.add([-B[g][s], -B[g][s2]])
        for s in range(g):          # A index < B index
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
        # weight >= 2 (a minimum circuit has no zero gate and no gate equal to an input)
        for i in range(n):
            E.add([-val[g][i]] + [val[g][i2] for i2 in range(n) if i2 != i])
        E.add([val[g][i] for i in range(n)])
    out = []
    for r in targets:
        sel = [E.new() for _ in range(k)]
        out.append(sel)
        E.add(sel)
        for gi in range(k):
            g = n + gi
            for i in range(n):
                E.add([-sel[gi], val[g][i] if (r >> i) & 1 else -val[g][i]])
    for g in range(n, S):           # every gate is used or is an output
        cl = [o[g - n] for o in out]
        for g2 in range(g + 1, S):
            cl.append(A[g2][g])
            cl.append(B[g2][g])
        E.add(cl)
    for g in range(n, S - 1):       # (B_g, A_g) strictly increasing lexicographically
        for s in range(g):
            for s2 in range(s):
                E.add([-B[g][s], -B[g + 1][s2]])
        for s in range(g):
            for a in range(g):
                for a2 in range(a + 1):
                    E.add([-B[g][s], -B[g + 1][s], -A[g][a], -A[g + 1][a2]])
    return E, A, B, val, out


def solve(targets, n, k, tlimit=None, solver="cadical153"):
    E, A, B, val, out = encode(targets, n, k)
    with Solver(name=solver, bootstrap_with=E.clauses) as s:
        res = s.solve()
        if not res:
            return res, None
        model = set(l for l in s.get_model() if l > 0)
    gates = []
    for g in range(n, n + k):
        a = next(i for i in range(g) if A[g][i] in model)
        b = next(i for i in range(g) if B[g][i] in model)
        gates.append((a, b))
    assert qm.computes(n, gates, targets)
    return True, gates


def main():
    args = sys.argv[1:]
    m, klo, khi = int(args[0]), int(args[1]), int(args[2])
    T = qm.shift_T(m)
    tag = f"Q_{m}"
    if "--T" in args:
        spec = args[args.index("--T") + 1]
        for item in spec.split(","):
            j, kk = map(int, item.split(":"))
            T[j] ^= 1 << kk
        tag += f" + T[{spec}]"
    targets = qm.rows_T(T)
    n = 4 * m
    outfile = args[args.index("--out") + 1] if "--out" in args else None
    for k in range(klo, khi + 1):
        t0 = time.time()
        res, gates = solve(targets, n, k)
        print(f"{tag}: k = {k}: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
        if res:
            print("   profile:", {a: b for a, b in qm.profile(n, gates, targets).items()})
            if outfile:
                qm.write_circuit(outfile, n, gates, f"{tag}: {k} gates, found by slp_sat.py (SAT), verified by qm.computes")
            break


if __name__ == "__main__":
    main()
