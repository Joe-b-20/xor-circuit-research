"""Cost of one sheet when every even vector of the previous block is free.

usage: python3 free_prev.py [--odd] one O K      same question for one list O (e.g. s0,s1,s2,s3 = last block of a run)
       (--odd: the four odd vectors E_c of block a are free too, i.e. every vector of block a)
       python3 free_prev.py outputs KLO KHI      least K such that K gates compute the four outputs
                                                 E_c(b) + s_c(a), given the 8 inputs and all seven
                                                 nonzero even vectors of block a at no cost
       python3 free_prev.py basis K [TIMEOUT]    for every basis O of the even space of block b (up to
                                                 rotation): can K gates compute the four outputs AND the
                                                 three vectors of O, with the same free signals?
Complete SAT encoding (scheme_sat.encode).
"""
import subprocess
import sys
import time

from pysat.solvers import Solver

import scheme_sat as ss


ODD_TOO = False     # --odd : the four odd vectors E_c of block a are free as well


def solve(O, k):
    base = [1 << i for i in range(8)] + sorted(ss.VEC.values())
    if ODD_TOO:
        base += [15 ^ (1 << c) for c in range(4)]
    targets = ss.targets_out() + [o << 4 for o in O]
    cl, A, B = ss.encode(base, targets, k)
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


def show(res):
    base, gates, vals = res
    nb = len(base)

    def nm(i):
        if i < 8:
            return f"{'ab'[i // 4]}{i % 4}"
        if i < nb:
            return "a:" + ss.NAME.get(base[i], f"E{[14, 13, 11, 7].index(base[i]) if base[i] in (14, 13, 11, 7) else '?'}")
        return f"g{i - nb}"

    touts = ss.targets_out()
    for gi, (a, b) in enumerate(gates):
        v = vals[nb + gi]
        tag = f"  = OUT {touts.index(v)}" if v in touts else ""
        print(f"   g{gi} = {nm(a)} + {nm(b)}   [{ss.describe(v)}]{tag}")


def main():
    global ODD_TOO
    args = sys.argv[1:]
    if "--odd" in args:
        ODD_TOO = True
        args.remove("--odd")
    if args[0] == "outputs":
        for k in range(int(args[1]), int(args[2]) + 1):
            t0 = time.time()
            res = solve([], k)
            print(f"outputs only, K = {k}: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
            if res:
                show(res)
                break
    elif args[0] == "one":
        O = ss.parse(args[1])
        res = solve(O, int(args[2]))
        print("SAT" if res else "UNSAT")
        if res:
            show(res)
    else:
        k = int(args[1])
        tmo = int(args[2]) if len(args) > 2 else 60
        for O in ss.bases():
            orbit = {tuple(sorted(ss.rot(v, r) for v in O)) for r in range(4)}
            if tuple(sorted(O)) != min(orbit):
                continue
            os_ = ",".join(ss.NAME[v] for v in O)
            t0 = time.time()
            try:
                res = subprocess.run([sys.executable, __file__, "one", os_, str(k)], capture_output=True, text=True, timeout=tmo)
                first = res.stdout.splitlines()[0] if res.stdout else "?"
            except subprocess.TimeoutExpired:
                first = "TIMEOUT"
            print(f"O = {os_:<9} K = {k}: {first}  ({time.time() - t0:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
