#!/usr/bin/env python3
"""P2: rank-P bottom decomposition with a FIXED alpha profile (model M, rank-1 products), by SAT.

With alpha_j fixed, the Brent equations  sum_j alpha_j[p] g_j[q] c_j[k] = M_k[p][q]  are quadratic
in (g, c).  Kraft per output at depth D: sum_j c_j[k] * 2^(lev(alpha_j) - minlev) <= 2^(D-1-minlev).

    python3 bsat2.py FRONT D OUT.jsonl [--profiles N] [--seconds-each T] [--seed S] [--profile a,a,a,...]
Random profiles: multisets of P alphas, weight-minimal-ish, satisfying the necessary coverage
condition: for every nonzero u-direction s, #{j : <alpha_j, s> = 1} >= 8 (rank of u -> u*z is 8).
"""
import argparse
import json
import random
import sys
import threading
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402
from pysat.formula import IDPool, CNF   # noqa: E402
from pysat.card import CardEnc, EncType   # noqa: E402
from pysat.solvers import Solver   # noqa: E402

POP = [bin(i).count('1') for i in range(256)]


def coverage_ok(vs):
    for s in range(1, 16):
        if sum(1 for v in vs if POP[v & s] & 1) < 8: return False
    return True


def solve(vs, W, budget, seconds, solver='cd19'):
    P = len(vs)
    pool = IDPool(); cnf = CNF()
    b = [[pool.id(('b', j, q)) for q in range(8)] for j in range(P)]
    c = [[pool.id(('c', j, k)) for k in range(8)] for j in range(P)]
    for j in range(P): cnf.append(b[j]); cnf.append(c[j])
    t = [[[None] * 8 for _ in range(8)] for _ in range(P)]
    for j in range(P):
        for q in range(8):
            for k in range(8):
                v = pool.id(('t', j, q, k)); t[j][q][k] = v
                cnf.extend([[-v, b[j][q]], [-v, c[j][k]], [v, -b[j][q], -c[j][k]]])
    for p in range(4):
        js = [j for j in range(P) if (vs[j] >> p) & 1]
        for q in range(8):
            for k in range(8):
                lits = [t[j][q][k] for j in js]
                rhs = bil.M[k][p][q]
                if not lits:
                    if rhs: return 'UNSAT-trivial', None
                    continue
                acc = lits[0]
                for i in range(1, len(lits)):
                    y = pool.id(('x', p, q, k, i)); x1, x2 = acc, lits[i]
                    cnf.extend([[-y, x1, x2], [-y, -x1, -x2], [y, -x1, x2], [y, x1, -x2]]); acc = y
                cnf.append([acc] if rhs else [-acc])
    for k in range(8):
        lits = []
        for j in range(P):
            for r in range(W[j]):
                if r == 0: lits.append(c[j][k])
                else:
                    e = pool.id(('e', j, k, r)); cnf.extend([[-e, c[j][k]], [e, -c[j][k]]]); lits.append(e)
        cnf.extend(CardEnc.atmost(lits=lits, bound=budget, vpool=pool, encoding=EncType.seqcounter).clauses)
    # symmetry: products with equal alpha ordered by c (lex, k=0 first)
    for j in range(P - 1):
        if vs[j] != vs[j + 1]: continue
        eq = None
        for k in range(8):
            x, y = c[j][k], c[j + 1][k]
            if eq is None:
                cnf.append([x, -y]); e = pool.id(('eq', j, k)); cnf.extend([[-e, -x, y], [-e, x, -y]]); eq = e
            else:
                cnf.append([-eq, x, -y]); e = pool.id(('eq', j, k))
                cnf.extend([[-e, eq], [-e, -x, y], [-e, x, -y]]); eq = e
    with Solver(name=solver, bootstrap_with=cnf.clauses) as S:
        tm = threading.Timer(seconds, lambda: S.interrupt()); tm.start()
        r = S.solve_limited(expect_interrupt=True)
        tm.cancel()
        if r is None: return 'TIMEOUT', None
        if r is False: return 'UNSAT', None
        ms = set(l for l in S.get_model() if l > 0)
        dec = []
        for j in range(P):
            g = sum(bil.GMASK[q] for q in range(8) if b[j][q] in ms)
            cv = sum(1 << (7 - k) for k in range(8) if c[j][k] in ms)
            dec.append((bil.ALPHA[vs[j]], g, O.w_of(cv)))
        return 'SAT', dec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('out')
    ap.add_argument('--P', type=int, default=18); ap.add_argument('--profiles', type=int, default=50)
    ap.add_argument('--seconds-each', type=float, default=60); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--profile', default=None, help='comma list of alpha field elements')
    ap.add_argument('--maxw', type=float, default=None, help='max sum of weights (units) of a profile')
    a = ap.parse_args()
    rng = random.Random(a.seed)
    F = ylev.front(ylev.load(a.front))
    lev = {v: F['levels'][v][0] for v in range(1, 16)}
    minlev = min(lev.values()); budget = 2 ** (a.D - 1 - minlev)
    Wv = {v: 2 ** (lev[v] - minlev) for v in lev}
    print('levels', sorted((lev[v], bil.ALPHA[v]) for v in lev), 'budget', budget, flush=True)
    out = open(a.out, 'a')
    tried = set()
    profs = []
    if a.profile:
        profs = [sorted(bil.AIDX[int(x)] for x in a.profile.split(','))]
    T0 = time.time(); n = 0
    while n < a.profiles:
        if profs:
            vs = profs.pop()
        else:
            # random profile biased to light alphas
            cand = [v for v in lev if Wv[v] < budget]
            wts = [1.0 / Wv[v] ** 1.5 for v in cand]
            vs = sorted(rng.choices(cand, weights=wts, k=a.P))
            if a.maxw is not None and sum(Wv[v] for v in vs) > a.maxw: continue
        key = tuple(vs)
        if key in tried or not coverage_ok(vs): continue
        tried.add(key); n += 1
        st, dec = solve(vs, [Wv[v] for v in vs], budget, a.seconds_each)
        rec = {'D': a.D, 'P': a.P, 'profile': [bil.ALPHA[v] for v in vs], 'wsum': sum(Wv[v] for v in vs),
               'status': st, 't': round(time.time() - T0, 1)}
        if dec is not None:
            rec['check'] = O.check(dec); rec['dec'] = dec; rec['front'] = a.front
        print(json.dumps({k: rec[k] for k in rec if k != 'dec'}), flush=True)
        out.write(json.dumps(rec) + '\n'); out.flush()


if __name__ == '__main__':
    main()
