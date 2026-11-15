#!/usr/bin/env python3
"""P2: depth-constrained rank-P bottom decompositions (model M, rank-1 products) by SAT.

Find P products (alpha_j, g_j) and output incidence c_j in {0,1}^8 with
    sum_j c_j[k] * (alpha_j (x) g_j) = M_k     (Brent equations over GF(2), bil.M)
and, per output k, the Kraft condition of an XOR tree of depth D over its products, where the
product of alpha has gate level 1 + lev(alpha) (lev from the front's Y-form levels, ylev.py):
    sum_{j: c_j[k]} 2^(1 + lev(alpha_j) - D) <= 1.

    python3 bsat.py FRONT_FILE D P OUT.json [--seconds T] [--solver cd19] [--maxlev L]

Every solution is checked exactly (truth tables) before it is written.
"""
import argparse
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil   # noqa: E402
import ylev  # noqa: E402
from pysat.formula import IDPool, CNF   # noqa: E402
from pysat.card import CardEnc, EncType   # noqa: E402
from pysat.solvers import Solver   # noqa: E402


def build(levels, D, P, maxlev=None, sym=True):
    pool = IDPool(); cnf = CNF()
    a = [[pool.id(('a', j, p)) for p in range(4)] for j in range(P)]
    b = [[pool.id(('b', j, q)) for q in range(8)] for j in range(P)]
    c = [[pool.id(('c', j, k)) for k in range(8)] for j in range(P)]
    for j in range(P):
        cnf.append(a[j]); cnf.append(b[j]); cnf.append(c[j])       # nonzero
    # alpha value indicators
    lev = {v: levels[v][0] for v in range(1, 16)}
    minlev = min(lev.values())
    budget = 2 ** (D - 1 - minlev)
    assert budget >= 1
    W = {v: 2 ** (lev[v] - minlev) for v in lev}          # weight units
    hv = [[None] * 16 for _ in range(P)]
    for j in range(P):
        for v in range(1, 16):
            h = pool.id(('h', j, v)); hv[j][v] = h
            # h <-> (a_j == v)
            lits = [a[j][p] if (v >> p) & 1 else -a[j][p] for p in range(4)]
            for l in lits: cnf.append([-h, l])
            cnf.append([h] + [-l for l in lits])
            if W[v] > budget or (maxlev is not None and lev[v] > maxlev):
                cnf.append([-h])
    # t = a & b ; s = t & c ; XOR over j
    for p in range(4):
        for q in range(8):
            t = []
            for j in range(P):
                v = pool.id(('t', j, p, q)); t.append(v)
                cnf.extend([[-v, a[j][p]], [-v, b[j][q]], [v, -a[j][p], -b[j][q]]])
            for k in range(8):
                s = []
                for j in range(P):
                    v = pool.id(('s', j, p, q, k)); s.append(v)
                    cnf.extend([[-v, t[j]], [-v, c[j][k]], [v, -t[j], -c[j][k]]])
                # XOR chain of s == M_k[p][q]
                acc = s[0]
                for j in range(1, P):
                    y = pool.id(('x', p, q, k, j))
                    x1, x2 = acc, s[j]
                    cnf.extend([[-y, x1, x2], [-y, -x1, -x2], [y, -x1, x2], [y, x1, -x2]])
                    acc = y
                cnf.append([acc] if bil.M[k][p][q] else [-acc])
    # Kraft per output
    for k in range(8):
        lits = []
        for j in range(P):
            for v in range(1, 16):
                if W[v] > budget: continue
                # e = c_j[k] & h_jv, counted W[v] times (W copies)
                for r in range(W[v]):
                    e = pool.id(('e', j, v, k, r))
                    cnf.extend([[-e, c[j][k]], [-e, hv[j][v]], [e, -c[j][k], -hv[j][v]]])
                    lits.append(e)
        enc = CardEnc.atmost(lits=lits, bound=budget, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(enc.clauses)
    if sym:
        # products ordered by their (c) incidence value as an integer, nonincreasing: lex order on c
        for j in range(P - 1):
            # c_j >= c_{j+1} lexicographically (k = 0 most significant): standard lex encoding
            eq_prev = None
            for k in range(8):
                x, y = c[j][k], c[j + 1][k]
                if eq_prev is None:
                    cnf.append([x, -y])            # not (x=0 & y=1)
                    e = pool.id(('eq', j, k)); cnf.extend([[-e, -x, y], [-e, x, -y]]); eq_prev = e
                else:
                    cnf.append([-eq_prev, x, -y])
                    e = pool.id(('eq', j, k))
                    cnf.extend([[-e, eq_prev], [-e, -x, y], [-e, x, -y]]); eq_prev = e
    return pool, cnf, a, b, c, W, budget


def decode(model, a, b, c):
    ms = set(l for l in model if l > 0)
    prods = []
    for j in range(len(a)):
        av = sum(1 << p for p in range(4) if a[j][p] in ms)
        bv = sum(bil.GMASK[q] for q in range(8) if b[j][q] in ms)
        cv = [k for k in range(8) if c[j][k] in ms]
        prods.append((av, bv, cv))
    return prods


def check(prods):
    tabs = [bil.f(bil.ALPHA[av], bv) for av, bv, cv in prods]
    for k in range(8):
        t = 0
        for (av, bv, cv), tt in zip(prods, tabs):
            if k in cv: t ^= tt
        o = bil.out_tab(k)
        if t != o and t != o ^ bil.ONES: return False
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('P', type=int); ap.add_argument('out')
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--solver', default='cd19')
    ap.add_argument('--maxlev', type=int, default=None); ap.add_argument('--nosym', action='store_true')
    ap.add_argument('--count', type=int, default=1, help='number of solutions to enumerate (blocking c/a/b)')
    a_ = ap.parse_args()
    F = ylev.front(ylev.load(a_.front))
    levels = F['levels']
    print('Y levels', sorted((levels[v][0], bil.ALPHA[v]) for v in range(1, 16)), flush=True)
    t0 = time.time()
    pool, cnf, a, b, c, W, budget = build(levels, a_.D, a_.P, a_.maxlev, not a_.nosym)
    print('vars %d clauses %d budget %d build %.1fs' % (pool.top, len(cnf.clauses), budget, time.time() - t0), flush=True)
    sols = []
    with Solver(name=a_.solver, bootstrap_with=cnf.clauses) as S:
        import threading
        timer = threading.Timer(a_.seconds, lambda: S.interrupt()); timer.start()
        while len(sols) < a_.count:
            r = S.solve_limited(expect_interrupt=True)
            if r is None:
                print('TIMEOUT after %.1fs' % (time.time() - t0), flush=True); break
            if r is False:
                print('UNSAT after %.1fs (case: rank-1 products, %d products, depth %d, these Y-levels)' % (time.time() - t0, a_.P, a_.D), flush=True); break
            prods = decode(S.get_model(), a, b, c)
            ok = check(prods)
            kr = []
            for k in range(8):
                kr.append(sum(W[av] for av, bv, cv in prods if k in cv))
            print('SAT %.1fs check %s kraft-units %s / %d' % (time.time() - t0, ok, kr, budget), flush=True)
            sols.append({'prods': prods, 'kraft': kr, 'check': ok})
            # block this incidence/alpha assignment
            V = set(v for row in a + b + c for v in row)
            S.add_clause([-x for x in S.get_model() if abs(x) in V])
        timer.cancel()
    json.dump({'front': a_.front, 'D': a_.D, 'P': a_.P, 'levels': {str(v): levels[v][0] for v in levels},
               'solutions': sols}, open(a_.out, 'w'))


if __name__ == '__main__':
    main()
