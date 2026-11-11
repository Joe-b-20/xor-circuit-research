"""The four outputs of one sheet as a stand-alone 8-input map: [b: E_c] + [a: s_c], c = 0..3, nothing free.

usage: python3 sheet_alone.py KLO KHI [--units-only]
  Least K with a K-gate circuit over the 8 inputs (complete SAT encoding of rotation/scheme_sat.py).
  K <= 9 is impossible by Lemma 3.4 (free vectors only help).
"""
import os
import sys
import time

from pysat.solvers import Solver

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import scheme_sat as ss  # noqa: E402


def main():
    klo, khi = int(sys.argv[1]), int(sys.argv[2])
    base = [1 << i for i in range(8)]
    targets = ss.targets_out()
    for k in range(klo, khi + 1):
        t0 = time.time()
        cl, A, B = ss.encode(base, targets, k)
        with Solver(name="cadical153", bootstrap_with=cl) as S:
            res = S.solve()
            print(f"sheet alone, K = {k}: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
            if res:
                model = set(x for x in S.get_model() if x > 0)
                vals = list(base)
                for g in range(8, 8 + k):
                    a = next(i for i in range(g) if A[g][i] in model)
                    b = next(i for i in range(g) if B[g][i] in model)
                    vals.append(vals[a] ^ vals[b])
                    nm = lambda i: f"{'ab'[i // 4]}{i % 4}" if i < 8 else f"g{i - 8}"
                    print(f"   g{g - 8} = {nm(a)} + {nm(b)}   [{ss.describe(vals[g])}]" + ("  = OUT" if vals[g] in targets else ""))
                break


if __name__ == "__main__":
    main()
