"""Can an optimal sheet circuit lend a three-term neighbour everything it needs?  (necessary condition, SAT)

usage: python3 qa_sat.py K MAXU [MINDIM]

Blocks a (free, bits 0..3) and b (bits 4..7); base = 8 inputs and the 11 vectors of weight >= 2 on a.
Question: is there a K-gate circuit computing the four sheet outputs [b: E_c] + [a: s_c] together with a set U
of at most MAXU of its gates, each nonzero on both blocks, such that the span of U contains
   MINDIM = 3 (default): the three diagonal vectors [a: s_c] + [b: s_c], c = 0, 1, 2 (the whole diagonal space D);
   MINDIM = 2          : two independent diagonal vectors (all seven 2-dimensional subspaces of D are tried).
REPORT part II, Lemma II.6: if sheets 0 and 1 of MixColumns are computed jointly with 20 gates (block 7 free,
block-monotone), sheet 0's ten gates satisfy this with K = 10, MAXU = 4, MINDIM = 3.
"""
import itertools
import sys
import time

from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

S_VEC = [0b0011, 0b0110, 0b1100, 0b1001]


def encode(base, targets, k, nbits=8):
    nv = [0]
    cl = []

    def new():
        nv[0] += 1
        return nv[0]

    nb = len(base)
    S = nb + k
    A, B, val = [None] * S, [None] * S, [None] * S
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
                    bit = (base[s] >> i) & 1
                    cl.append([-A[g][s], pa[i] if bit else -pa[i]])
                    cl.append([-B[g][s], pb[i] if bit else -pb[i]])
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
    for g in range(nb, S):            # every gate is an ancestor of an output: used by a later gate or an output
        c2 = [o[g - nb] for o in out]
        for g2 in range(g + 1, S):
            c2 += [A[g2][g], B[g2][g]]
        cl.append(c2)
    for g in range(nb, S - 1):
        for s in range(g):
            for s2 in range(s):
                cl.append([-B[g][s], -B[g + 1][s2]])
        for s in range(g):
            for a in range(g):
                for a2 in range(a + 1):
                    cl.append([-B[g][s], -B[g + 1][s], -A[g][a], -A[g + 1][a2]])
    return cl, val, nv


def run(k, maxu, diag_targets):
    base = [1 << i for i in range(8)] + [v for v in range(1, 16) if bin(v).count("1") >= 2]
    targets = []
    for c in range(4):
        Ec = 15 ^ (1 << c)
        targets.append((Ec << 4) | S_VEC[c])
    cl, val, nv = encode(base, targets, k)
    nb = len(base)

    def new():
        nv[0] += 1
        return nv[0]

    gates = list(range(nb, nb + k))
    u = {g: new() for g in gates}
    for g in gates:
        cl.append([-u[g]] + val[g][0:4])
        cl.append([-u[g]] + val[g][4:8])
    card = CardEnc.atmost(lits=list(u.values()), bound=maxu, top_id=nv[0], encoding=EncType.seqcounter)
    cl += card.clauses
    nv[0] = max(nv[0], card.nv)
    for d in diag_targets:
        lam = {g: new() for g in gates}
        for g in gates:
            cl.append([-lam[g], u[g]])
        for i in range(8):
            terms = []
            for g in gates:
                t = new()
                cl.append([-t, lam[g]])
                cl.append([-t, val[g][i]])
                cl.append([t, -lam[g], -val[g][i]])
                terms.append(t)
            acc = terms[0]
            for t in terms[1:]:
                x = new()
                cl.append([-x, acc, t])
                cl.append([-x, -acc, -t])
                cl.append([x, -acc, t])
                cl.append([x, acc, -t])
                acc = x
            cl.append([acc] if (d >> i) & 1 else [-acc])
    with Solver(name="cadical153", bootstrap_with=cl) as sol:
        return sol.solve()


def main():
    k, maxu = int(sys.argv[1]), int(sys.argv[2])
    mindim = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    diag = lambda s: s | (s << 4)
    if mindim == 3:
        t0 = time.time()
        res = run(k, maxu, [diag(S_VEC[0]), diag(S_VEC[1]), diag(S_VEC[2])])
        print(f"K = {k}, |U| <= {maxu}, span(U) contains D: {'SAT' if res else 'UNSAT'}  ({time.time() - t0:.1f} s)", flush=True)
    else:
        evens = [0b0011, 0b0110, 0b1100, 0b1001, 0b0101, 0b1010, 0b1111]
        seen = set()
        for x, y in itertools.combinations(evens, 2):
            sub = frozenset([x, y, x ^ y])
            if sub in seen:
                continue
            seen.add(sub)
            t0 = time.time()
            res = run(k, maxu, [diag(x), diag(y)])
            print(f"K = {k}, |U| <= {maxu}, span(U) contains the diagonals of {sorted(sub)}: {'SAT' if res else 'UNSAT'}"
                  f"  ({time.time() - t0:.1f} s)", flush=True)


if __name__ == "__main__":
    main()
