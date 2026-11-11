"""The three-term sheet [b: E_c] + [a: s_c] + [k: s_c]: an explicit 13-gate circuit, and small SAT side checks.

usage: python3 three_term.py                 verifies the 13-gate circuit (REPORT part II, Theorem II.1)
       python3 three_term.py diag [TIMEOUT]  SAT: does a 10-gate sheet circuit (blocks a free, b) exist that also
                                             contains the three "diagonal" gates [a: x] + [b: x], x in X, for a
                                             basis X of the even space?  (one instance per basis up to rotation)

Model of Theorem II.1: base = the 12 inputs of blocks a, k, b and every vector supported on a alone or on k
alone (cost 0); every gate counts.  The 13-gate circuit: three gates D_x = [a: x] + [k: x], x in {s1, d1, t},
then the ten gates of the scheme {s1,d1,t} -> {s0,d0,d1} of rotation/scheme_sat.py with D_x in place of x.
Bits: block a = 0..3, block k = 4..7, block b = 8..11.
"""
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import scheme_sat as ss  # noqa: E402

S = {"s0": 0b0011, "s1": 0b0110, "s2": 0b1100, "s3": 0b1001, "d0": 0b0101, "d1": 0b1010, "t": 0b1111}


def verify13():
    A, K, B = 0, 4, 8
    e = lambda blk, c: 1 << (blk + c)
    gates = []

    def g(x, y):
        gates.append(x ^ y)
        return x ^ y

    D = {x: g(S[x] << A, S[x] << K) for x in ("s1", "d1", "t")}      # three mixed {a,k} gates
    s0b = g(e(B, 0), e(B, 1))
    d0b = g(e(B, 0), e(B, 2))
    d1b = g(e(B, 1), e(B, 3))
    h1 = g(e(B, 3), D["s1"])
    v = g(D["d1"], s0b)
    o1 = g(d0b, h1)
    o2 = g(h1, v)
    h2 = g(D["t"], o1)
    o3 = g(d1b, h2)
    o0 = g(v, h2)
    want = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        sc = (1 << c) | (1 << ((c + 1) % 4))
        want.append((Ec << B) | (sc << K) | (sc << A))
    ok = all(w in gates for w in want) and len(gates) == 13 and len(set(gates)) == 13
    print(f"13-gate circuit for the three-term sheet (pure vectors of a and of k free): verified = {ok}")
    nb = sum(1 for m in gates if m >> B)
    nm = sum(1 for m in gates if not (m >> B) and (m & 15) and ((m >> 4) & 15))
    print(f"   gates nonzero on b: {nb}; gates on a and k only: {nm}")


def diag_one(names, k=10):
    from pysat.solvers import Solver
    X = [S[n] for n in names]
    base = [1 << i for i in range(8)] + [v for v in range(1, 16) if bin(v).count("1") >= 2]
    targets = ss.targets_out() + [x | (x << 4) for x in X]
    cl, A, B = ss.encode(base, targets, k)
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        return sol.solve()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "one":
        print("SAT" if diag_one(sys.argv[2].split(",")) else "UNSAT")
        return
    if len(sys.argv) > 1 and sys.argv[1] == "diag":
        tmo = int(sys.argv[2]) if len(sys.argv) > 2 else 120
        for X in ss.bases():
            orbit = {tuple(sorted(ss.rot(v, r) for v in X)) for r in range(4)}
            if tuple(sorted(X)) != min(orbit):
                continue
            names = ",".join(ss.NAME[v] for v in X)
            t0 = time.time()
            try:
                res = subprocess.run([sys.executable, __file__, "one", names], capture_output=True, text=True, timeout=tmo)
                out = res.stdout.strip() or "?"
            except subprocess.TimeoutExpired:
                out = "TIMEOUT"
            print(f"10-gate sheet containing the diagonal gates of {{{names}}}: {out}  ({time.time() - t0:.1f} s)", flush=True)
        return
    verify13()


if __name__ == "__main__":
    main()
