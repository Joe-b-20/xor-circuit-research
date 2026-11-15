#!/usr/bin/env python3
"""Bilinear rank-R decompositions of the bottom tensor T with the multiset of Y-forms fixed.

Necessary conditions on the Y-form multiset (m_u, u in GF(2)^4 \\ 0, sum m_u = R) [C]:
  - for every y != 0 the matrix M(y) = sum_i y_i M_i (8x8, the Y-slice) has rank 8, so
    #{k : u_k . y = 1} >= 8;
  - for every 2-dim V of Y, the restriction of T to V is a pencil; its rank r(V) (computed here by
    SAT on the 2 x 8 x 8 tensor) bounds #{k : u_k not orthogonal to V} >= r(V).
Multisets passing both, with few distinct forms (L3 cost), are tried by SAT with u fixed.

    ufix.py REF --R 17 [--dmax 10] [--mmax 3] [--budget CONFL] [--limit N] [--out DIR]
"""
import itertools, json, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, rank_sat as RS  # noqa
from pysat.solvers import Solver  # noqa


def arg(a, k, d, f=str):
    return f(a[a.index(k) + 1]) if k in a else d


def dot(u, y):
    return bin(u & y).count('1') & 1


def tensor_from_ref(ref):
    rc, Yt = FL.ref_basis(ref)
    ten, const = FL.target_tensor(rc, Yt)
    # ten[o][i] = x-mask; build Tn[o][i][j]
    return [[[ten[o][i] >> j & 1 for j in range(8)] for i in range(4)] for o in range(8)]


def restrict(Tn, ys):
    """Tensor with Y restricted to span(ys): new Y coords = coefficients on ys."""
    return [[[sum(y >> i & 1 and Tn[o][i][j] for i in range(4)) & 1 for j in range(8)] for y in ys] for o in range(8)]


def rank_of(Tn, rmax, budget=None):
    for r in range(1, rmax + 1):
        res, dt, sol, nv, nc = RS.solve(Tn, r, budget)
        if res: return r
        if res is None: return None
    return None


def solve_fixed(Tn, us, budget=None):
    m = len(Tn); ny = 4; nx = 8; R = len(us)
    F = RS.CNF()
    v = [[F.var() for _ in range(nx)] for _ in range(R)]
    w = [[F.var() for _ in range(m)] for _ in range(R)]
    for k in range(R): F.cl += [v[k][:], w[k][:]]
    for o, i, j in itertools.product(range(m), range(ny), range(nx)):
        ks = [k for k in range(R) if us[k] >> i & 1]
        terms = [F.AND(v[k][j], w[k][o]) for k in ks]
        if not terms:
            if Tn[o][i][j]: return False, 0, None
            continue
        acc = terms[0]
        for t in terms[1:]: acc = F.XOR(acc, t)
        F.cl.append([acc] if Tn[o][i][j] else [-acc])
    # symmetry: equal consecutive u's -> v's lex nondecreasing (cheap: first bit order)
    s = Solver(name='cadical153', bootstrap_with=F.cl)
    t0 = time.time()
    if budget: s.conf_budget(budget); r = s.solve_limited()
    else: r = s.solve()
    sol = None
    if r:
        M = set(l for l in s.get_model() if l > 0)
        sol = [{'u': [us[k] >> i & 1 for i in range(4)], 'v': [int(x in M) for x in v[k]], 'w': [int(x in M) for x in w[k]]}
               for k in range(R)]
    return r, time.time() - t0, sol


def main():
    a = sys.argv[1:]
    ref = a[0]; R = arg(a, '--R', 17, int); dmax = arg(a, '--dmax', 10, int); mmax = arg(a, '--mmax', 3, int)
    budget = arg(a, '--budget', 200000, int); limit = arg(a, '--limit', 50, int)
    out = Path(arg(a, '--out', 'ufix')); out.mkdir(parents=True, exist_ok=True)
    Tn = tensor_from_ref(ref)
    U = list(range(1, 16))
    planes = set()
    for y1 in U:
        for y2 in U:
            if y2 > y1: planes.add(tuple(sorted({y1, y2, y1 ^ y2})))
    pr = {}
    t0 = time.time()
    if '--ms' in a:
        ms = json.loads(Path(arg(a, '--ms', '')).read_text())
        us = [int(u) for u, m in sorted(ms.items()) for _ in range(m)]
        r, dt, sol = solve_fixed(Tn, us, budget)
        print('fixed multiset', ms, 'R', len(us), 'res', r, '%.1fs' % dt, flush=True)
        if sol: assert RS.check(Tn, sol); print(sol)
        return
    for P in (sorted(planes) if '--planes' in a else []):
        pr[P] = rank_of(restrict(Tn, [P[0], P[1]]), 14, 100000)
    print('plane ranks', sorted(set(pr.values())), {r: sum(1 for v in pr.values() if v == r) for r in set(pr.values())},
          '%.1fs' % (time.time() - t0), flush=True)
    (out / 'planes.json').write_text(json.dumps({str(k): v for k, v in pr.items()}))
    # enumerate multisets
    cands = []
    for d in range(4, dmax + 1):
        for sup in itertools.combinations(U, d):
            for mult in itertools.product(range(1, mmax + 1), repeat=d):
                if sum(mult) != R: continue
                ms = dict(zip(sup, mult))
                ok = all(sum(m for u, m in ms.items() if dot(u, y)) >= 8 for y in U)
                if not ok: continue
                for P, r in pr.items():
                    if r is None: continue
                    # u not orthogonal to V=span(P) <=> dot(u, y) = 1 for some y in P
                    if sum(m for u, m in ms.items() if any(dot(u, y) for y in P)) < r: ok = False; break
                if ok: cands.append((d, ms))
        print('d', d, 'candidates so far', len(cands), '%.1fs' % (time.time() - t0), flush=True)
        if len(cands) >= limit * 20: break
    print('multisets passing:', len(cands), flush=True)
    log = open(out / 'tries.jsonl', 'a')
    for d, ms in cands[:limit]:
        us = [u for u, m in sorted(ms.items()) for _ in range(m)]
        r, dt, sol = solve_fixed(Tn, us, budget)
        rec = {'d': d, 'ms': {str(k): v for k, v in ms.items()}, 'res': r, 't': round(dt, 1)}
        print(rec, flush=True)
        if sol:
            assert RS.check(Tn, sol); rec['sol'] = sol
        log.write(json.dumps(rec) + '\n'); log.flush()
        if sol: print('FOUND rank', R, flush=True); break


if __name__ == '__main__':
    main()
