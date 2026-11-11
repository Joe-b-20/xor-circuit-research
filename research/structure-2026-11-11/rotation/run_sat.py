"""Exact optimum of the "run" maps F_l (Q_m restricted to l consecutive blocks) by SAT.

usage: python3 run_sat.py L KLO KHI [--out FILE]
  F_L has 4L inputs (blocks 0..L-1) and the 4L + 4 outputs
     E_c on block 0;   E_c on block j + s_c on block j-1 (1 <= j < L);   s_c on block L-1      (c = 0..3).
  It is Q_m (m >= L + 2) with all inputs outside L consecutive blocks set to 0; F_2 is the map N of the task.
Same complete encoding as slp_sat.py.
"""
import sys
import time

import qm
import slp_sat


def run_targets(L):
    t = []
    for c in range(4):
        t.append(qm.E(c, 0))
    for j in range(1, L):
        for c in range(4):
            t.append(qm.E(c, j) | qm.s(c, j - 1))
    for c in range(4):
        t.append(qm.s(c, L - 1))
    return t


def main():
    args = sys.argv[1:]
    L, klo, khi = int(args[0]), int(args[1]), int(args[2])
    targets = run_targets(L)
    n = 4 * L
    for k in range(klo, khi + 1):
        t0 = time.time()
        res, gates = slp_sat.solve(targets, n, k)
        print(f"F_{L}: k = {k}: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
        if res:
            vals = qm.masks(n, gates)
            for gi, (a, b) in enumerate(gates):
                print(f"   s{n + gi} = s{a} + s{b}   mask {vals[n + gi]:0{n}b}" + ("  *" if vals[n + gi] in targets else ""))
            if "--out" in args:
                qm.write_circuit(args[args.index("--out") + 1], n, gates, f"F_{L}: {k} gates (SAT, slp_sat encoding)")
            break


if __name__ == "__main__":
    main()
