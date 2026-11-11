"""Joint local problem of sheets 0 and 1 (see j01_sat.py), case c2:
ten gates zero on block 1 forming a sheet-0 circuit, then eleven gates of which exactly one (z*) is zero on
block 1 and the other ten are nonzero on block 1 and have no operand supported on block 0 alone or block 7 alone.
z* may have any operands (in particular two gates that are nonzero on block 1: an exit).

usage: python3 j01_c2.py
"""
import time

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver


def main():
    KZ, KB = 10, 11
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
    val, A, B, allowed = [None] * S, [None] * S, [None] * S, {}
    isz = {}
    for g in range(nb, S):
        first_layer = g < nb + KZ
        src = [s for s in range(g) if not (8 <= s < 12)] if first_layer else list(range(g))
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
        for s in src:
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
        if first_layer:
            for i in range(8, 12):
                cl.append([-val[g][i]])
            cl.append([val[g][i] for i in range(4, 8)])
        else:
            z = new()
            isz[g] = z
            # z  <=> zero on block 1
            for i in range(8, 12):
                cl.append([-z, -val[g][i]])
            cl.append([z] + [val[g][i] for i in range(8, 12)])
            # z* is nonzero on block 0 and on block 7 (it is used by a gate without pure operands)
            cl.append([-z] + [val[g][i] for i in range(4, 8)])
            cl.append([-z] + [val[g][i] for i in range(0, 4)])
            # a gate that is nonzero on block 1 has no operand among the inputs of blocks 7, 0 and the free vectors,
            # and a first-layer operand must be nonzero on block 7
            for s in src:
                if s < 8 or 12 <= s < nb:
                    cl.append([-A[g][s], z])
                    cl.append([-B[g][s], z])
                elif nb <= s < nb + KZ:
                    cl.append([-A[g][s], z] + [val[s][i] for i in range(4)])
                    cl.append([-B[g][s], z] + [val[s][i] for i in range(4)])
    zs = [isz[g] for g in range(nb + KZ, S)]
    card = CardEnc.equals(lits=zs, bound=1, top_id=nv[0], encoding=EncType.seqcounter)
    cl += card.clauses
    nv[0] = max(nv[0], card.nv)
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
    print(f"mode c2: {KZ} + {KB} gates, {nv[0]} variables, {len(cl)} clauses", flush=True)
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        res = sol.solve()
        print(f"mode c2: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
        if res:
            model = set(x for x in sol.get_model() if x > 0)
            vals = list(base)
            for g in range(nb, S):
                a = next(s for s in allowed[g] if A[g][s] in model)
                b = next(s for s in allowed[g] if B[g][s] in model)
                vals.append(vals[a] ^ vals[b])
                print(f"   g{g - nb} = s{a} + s{b}  mask {vals[g]:012b}" + ("  OUT" if vals[g] in tz + tb else ""))


if __name__ == "__main__":
    main()
