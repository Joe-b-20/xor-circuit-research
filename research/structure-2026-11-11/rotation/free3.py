"""Cost of a sheet with one extra term when every vector of each of the two previous blocks is free.

usage: python3 free3.py K

Blocks a (bits 0..3), k (bits 4..7), b (bits 8..11).  Base signals: the 12 inputs, the 11 vectors of
weight >= 2 supported on block a, and the 11 vectors of weight >= 2 supported on block k (cost 0; vectors
meeting both a and k are NOT free).  Question: do K gates compute the four outputs
E_c(b) + s_c(a) + s_c(k)?  (For K <= 9 the answer is no by restriction to k = 0 and free_prev.py --odd.)
Complete SAT encoding (scheme_sat.encode).
"""
import sys
import time

from pysat.solvers import Solver

import scheme_sat as ss


def main():
    K = int(sys.argv[1])
    pure = [v for v in range(1, 16) if bin(v).count("1") >= 2]
    base = [1 << i for i in range(12)] + pure + [v << 4 for v in pure]
    targets = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        sc = (1 << c) | (1 << ((c + 1) % 4))
        targets.append((Ec << 8) | (sc << 4) | sc)
    t0 = time.time()
    cl, A, B = ss.encode(base, targets, K, nbits=12)
    nb = len(base)
    with Solver(name="cadical153", bootstrap_with=cl) as S:
        res = S.solve()
        if not res:
            print(f"extra-term sheet, K = {K}: UNSAT  ({time.time() - t0:.1f} s)")
            return
        model = set(x for x in S.get_model() if x > 0)
    print(f"extra-term sheet, K = {K}: SAT  ({time.time() - t0:.1f} s)")
    vals = list(base)
    names = {0b0011: "s0", 0b0110: "s1", 0b1100: "s2", 0b1001: "s3", 0b0101: "d0", 0b1010: "d1", 0b1111: "t",
             1: "e0", 2: "e1", 4: "e2", 8: "e3", 14: "E0", 13: "E1", 11: "E2", 7: "E3"}

    def desc(v):
        return " ".join(f"{blk}:{names[(v >> sh) & 15]}" for blk, sh in (("a", 0), ("k", 4), ("b", 8)) if (v >> sh) & 15)

    for g in range(nb, nb + K):
        a = next(i for i in range(g) if A[g][i] in model)
        b = next(i for i in range(g) if B[g][i] in model)
        vals.append(vals[a] ^ vals[b])
        nm = lambda i: f"[{desc(vals[i])}]" if i < nb else f"g{i - nb}"
        print(f"   g{g - nb} = {nm(a)} + {nm(b)}   [{desc(vals[g])}]" + ("  = OUT" if vals[g] in targets else ""))
    assert all(t in vals[nb:] for t in targets)


if __name__ == "__main__":
    main()
