#!/usr/bin/env python3
"""P7: simulated annealing over the PRODUCT SET of a rank-1 bottom (bopt.py model).

State: a set P of rank-1 tensors (alpha, w).  Every output tensor B_j must lie in span(P); its
representation is the minimum-cost subset (over the null space of P when P is dependent), subject to
Kraft at the cap.  Moves: swap one product for a candidate, drop one, add one.  Cost = bopt.Model.cost
of the induced choice (+ penalties for unrepresentable / Kraft-infeasible outputs).

    psa.py --init PLAN.json [--iters 50000] [--seed 1] [--T0 1.0] --out PLAN2.json
"""
import argparse, json, math, random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s1lib as L  # noqa: E402
import bopt, bsel  # noqa: E402


def tens(p):
    a, w = p
    return sum(w << (8 * i) for i in range(4) if (a >> i) & 1)


def solve_all(P, B, M):
    """per output: min-cost subset of P summing to B_j (Kraft ok). Returns list or None entries."""
    vec = [tens(p) for p in P]
    # elimination with combination masks
    piv = []   # (vector, combo)
    null = []
    for k, v in enumerate(vec):
        cmb = 1 << k
        for pv, pc in piv:
            if v ^ pv < v: v ^= pv; cmb ^= pc
        if v: piv.append((v, cmb)); piv.sort(key=lambda t: -t[0])
        else: null.append(cmb)
    out = []
    for Bj in B:
        t = sum(Bj[i] << (8 * i) for i in range(4)); cmb = 0
        for pv, pc in piv:
            if t ^ pv < t: t ^= pv; cmb ^= pc
        if t: out.append(None); continue
        best = None
        nn = len(null)
        for bits in range(1 << min(nn, 6)):
            c = cmb
            for q in range(min(nn, 6)):
                if (bits >> q) & 1: c ^= null[q]
            S = [P[k] for k in range(len(P)) if (c >> k) & 1]
            if not M.kraft(S): continue
            key = len(S)
            if best is None or key < best[0]: best = (key, S)
        out.append(best[1] if best else None)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--init', required=True); ap.add_argument('--iters', type=int, default=50000)
    ap.add_argument('--seed', type=int, default=1); ap.add_argument('--T0', type=float, default=1.0)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    plan = json.load(open(a.init))
    c = L.load(plan['circuit']); n = c.n
    T, lg, la, base = bopt.base_front(c)
    Ys = [b[1] for b in base]; Lb = [b[0] for b in base]
    U, C = bsel.decompose_outputs(c, T, Ys)
    B = [tuple(U[j][i] for i in range(4)) for j in range(8)]
    nfront = sum(1 for j, g in enumerate(c.gates) if g[0] in L.core.NONLINEAR_OPS and la[n + j] <= 3)
    M = bopt.Model(B, Lb, plan['cap'], bopt.front_free_forms(c, T, la), plan['amax'] - nfront)
    rng = random.Random(a.seed)
    # candidate pool: products of all Kraft-feasible 4-term decompositions of every output
    pool = set()
    for j in range(8):
        for A in bopt.bases_of(bopt.colspace(B[j])):
            S = bopt.decompose(B[j], A)
            if M.kraft(S): pool.update(S)
    pool = sorted(pool)
    print('candidate pool', len(pool))
    P = sorted({tuple(p) for S in plan['choice'] for p in S})

    def evaluate(P):
        ch = solve_all(P, B, M)
        bad = sum(1 for S in ch if S is None)
        if bad: return (10000 * bad, ), ch
        cc = M.cost(ch)
        return cc, ch
    cur, ch = evaluate(P)
    best = (cur, list(P), ch)
    print('start', cur)
    for it in range(a.iters):
        Tt = a.T0 * (1 - it / a.iters) + 0.02
        Q = list(P); r = rng.random()
        if r < 0.6:
            k = rng.randrange(len(Q)); Q[k] = rng.choice(pool)
        elif r < 0.8 and len(Q) > 18:
            Q.pop(rng.randrange(len(Q)))
        else:
            Q.append(rng.choice(pool))
        Q = sorted(set(Q))
        cc, chq = evaluate(Q)
        # drop unused products
        if cc[0] < 10000:
            used = {p for S in chq for p in S}
            if len(used) < len(Q):
                Q = sorted(used); cc, chq = evaluate(Q)
        if cc[0] <= cur[0] or rng.random() < math.exp(-(cc[0] - cur[0]) / Tt):
            P, cur, ch = Q, cc, chq
            if cc[0] < best[0][0]:
                best = (cc, list(P), chq)
                print('it %d: cost %s' % (it, cc), flush=True)
    cc, P, ch = best
    print('BEST', cc)
    plan2 = dict(plan); plan2['choice'] = [[list(p) for p in S] for S in ch]; plan2['cost'] = cc
    json.dump(plan2, open(a.out, 'w'))


if __name__ == '__main__':
    main()
