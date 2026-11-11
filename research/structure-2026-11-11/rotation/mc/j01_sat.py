"""Joint local problem of sheets 0 and 1 of MixColumns (blocks 7, 0, 1; every vector of block 7 free): SAT cases.

usage: python3 j01_sat.py MODE
  MODE a  : 10 gates zero on block 1 (a sheet-0 circuit), then 10 gates nonzero on block 1 none of which has an
            operand supported on block 0 alone or on block 7 alone            (the case |Z| = |B| = 10)
  MODE b  : 10 gates zero on block 1 (a sheet-0 circuit), then 11 gates nonzero on block 1, any operands
                                                                               (the case |Z| = 10, |B| = 11)
  MODE c1 : 11 gates zero on block 1, each an ancestor of a sheet-0 output, then 10 gates as in MODE a
                                                                               (|Z| = 11 closed, |B| = 10)
Outputs: sheet 0  [0: E_c] + [7: s_c];  sheet 1  [1: E_c] + [0: s_c] + [7: s_c].
Bits: block 7 = 0..3, block 0 = 4..7, block 1 = 8..11.  Base: the 12 inputs and the 11 vectors of weight >= 2 on
block 7.  By REPORT part II (Lemma II.4) a block-monotone local circuit with fewer than 22 gates falls into one of
the cases a, b, c1, c2; each MODE is a complete encoding of its case (c2 is not implemented).
"""
import sys
import time

from pysat.solvers import Solver


def main():
    mode = sys.argv[1]
    KZ = 11 if mode == "c1" else 10
    KB = 11 if mode == "b" else 10
    restricted = mode in ("a", "c1")
    NB = 12
    base = [1 << i for i in range(12)] + [v for v in range(1, 16) if bin(v).count("1") >= 2]
    nb = len(base)
    tz, tb = [], []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        sc = (1 << c) | (1 << ((c + 1) % 4))
        tz.append((Ec << 4) | sc)
        tb.append((Ec << 8) | (sc << 4) | sc)
    nv = [0]
    cl = []

    def new():
        nv[0] += 1
        return nv[0]

    S = nb + KZ + KB
    val = [None] * S
    A = [None] * S
    B = [None] * S
    isZ = lambda g: nb <= g < nb + KZ
    allowed = {}
    for g in range(nb, S):
        if isZ(g):
            src = [s for s in range(g) if not (s < 12 and s >= 8)]          # no block-1 inputs
        else:
            src = list(range(g))
            if restricted:
                src = [s for s in src if (8 <= s < 12) or s >= nb]          # block-1 inputs and gates only
        allowed[g] = src
        A[g] = {s: new() for s in src}
        B[g] = {s: new() for s in src}
        val[g] = [new() for _ in range(NB)]
        cl.append(list(A[g].values()))
        cl.append(list(B[g].values()))
        for i, s in enumerate(src):
            for s2 in src[i + 1:]:
                cl.append([-A[g][s], -A[g][s2]])
                cl.append([-B[g][s], -B[g][s2]])
        for s in src:                     # A index < B index
            for s2 in src:
                if s2 <= s:
                    cl.append([-A[g][s], -B[g][s2]])
        pa = [new() for _ in range(NB)]
        pb = [new() for _ in range(NB)]
        for s in src:
            for i in range(NB):
                if s < nb:
                    bit = (base[s] >> i) & 1
                    cl.append([-A[g][s], pa[i] if bit else -pa[i]])
                    cl.append([-B[g][s], pb[i] if bit else -pb[i]])
                else:
                    cl.append([-A[g][s], -val[s][i], pa[i]])
                    cl.append([-A[g][s], val[s][i], -pa[i]])
                    cl.append([-B[g][s], -val[s][i], pb[i]])
                    cl.append([-B[g][s], val[s][i], -pb[i]])
        for i in range(NB):
            v = val[g][i]
            cl.append([-v, pa[i], pb[i]])
            cl.append([-v, -pa[i], -pb[i]])
            cl.append([v, -pa[i], pb[i]])
            cl.append([v, pa[i], -pb[i]])
        if isZ(g):
            for i in range(8, 12):
                cl.append([-val[g][i]])
            cl.append([val[g][i] for i in range(4, 8)])          # nonzero on block 0 (pure block-7 gates are free)
        else:
            cl.append([val[g][i] for i in range(8, 12)])         # nonzero on block 1
    # restricted: a Z gate used by a B gate must be nonzero on block 7 (it is nonzero on block 0 already)
    if restricted:
        for g in range(nb + KZ, S):
            for s in allowed[g]:
                if isZ(s):
                    cl.append([-A[g][s]] + [val[s][i] for i in range(4)])
                    cl.append([-B[g][s]] + [val[s][i] for i in range(4)])
    # targets
    selz = [[new() for _ in range(KZ)] for _ in tz]
    selb = [[new() for _ in range(KB)] for _ in tb]
    for sel, t in zip(selz, tz):
        cl.append(sel)
        for k in range(KZ):
            g = nb + k
            for i in range(NB):
                cl.append([-sel[k], val[g][i] if (t >> i) & 1 else -val[g][i]])
    for sel, t in zip(selb, tb):
        cl.append(sel)
        for k in range(KB):
            g = nb + KZ + k
            for i in range(NB):
                cl.append([-sel[k], val[g][i] if (t >> i) & 1 else -val[g][i]])
    # every Z gate is used by a later Z gate or is a sheet-0 output (it is an ancestor of sheet 0);
    # every B gate is used by a later B gate or is a sheet-1 output
    for g in range(nb, nb + KZ):
        c2 = [sel[g - nb] for sel in selz]
        for g2 in range(g + 1, nb + KZ):
            c2 += [A[g2][g], B[g2][g]]
        cl.append(c2)
    for g in range(nb + KZ, S):
        c2 = [sel[g - nb - KZ] for sel in selb]
        for g2 in range(g + 1, S):
            c2 += [A[g2][g], B[g2][g]]
        cl.append(c2)
    # ordering inside each layer: (larger operand, smaller operand) strictly increasing
    for lo, hi in ((nb, nb + KZ), (nb + KZ, S)):
        for g in range(lo, hi - 1):
            for s in allowed[g]:
                for s2 in allowed[g + 1]:
                    if s2 < s:
                        cl.append([-B[g][s], -B[g + 1][s2]])
                if s in B[g + 1]:
                    for a in allowed[g]:
                        for a2 in allowed[g + 1]:
                            if a2 <= a:
                                cl.append([-B[g][s], -B[g + 1][s], -A[g][a], -A[g + 1][a2]])
    t0 = time.time()
    print(f"mode {mode}: {KZ} + {KB} gates, {nv[0]} variables, {len(cl)} clauses", flush=True)
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        res = sol.solve()
        print(f"mode {mode}: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
        if res:
            model = set(x for x in sol.get_model() if x > 0)
            vals = list(base)
            for g in range(nb, S):
                a = next(s for s in allowed[g] if A[g][s] in model)
                b = next(s for s in allowed[g] if B[g][s] in model)
                vals.append(vals[a] ^ vals[b])
                print(f"   g{g - nb} = s{a} + s{b}  mask {vals[g]:012b}" + ("  OUT" if vals[g] in tz + tb else ""))
            assert all(t in vals[nb:] for t in tz + tb)


if __name__ == "__main__":
    main()
