#!/usr/bin/env python3
"""P2: depth-constrained rank-1 bottoms in the "one product per class per output" model, by SAT.

Model M (bil.py): output k is the bilinear form M_k = sum_alpha alpha (x) m_{alpha,k} with
m_{alpha,k} an 8-bit x-functional (0 = class alpha unused by output k).  The bottom products are
the distinct pairs (alpha, m) with m != 0; output k uses (alpha, m_{alpha,k}) for each used class.
Restriction (stated case for every UNSAT): an output uses at most one product per alpha class.
Depth D: the product of class alpha sits at gate level 1 + lev(alpha) (front Y-form level table);
per output Kraft  sum_{alpha used by k} 2^(1 + lev(alpha) - D) <= 1.
Count: number of distinct (alpha, m != 0) <= P.

    python3 bsat3.py FRONT D P OUT.jsonl [--seconds T] [--exclude-w W]
"""
import argparse
import json
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


def encode(lev, D, P, outputs=range(8)):
    minlev = min(lev.values()); budget = 2 ** (D - 1 - minlev)
    W = {v: 2 ** (lev[v] - minlev) for v in lev}
    cls = [v for v in range(1, 16) if W[v] <= budget]
    pool = IDPool(); cnf = CNF()
    m = {(v, k, q): pool.id(('m', v, k, q)) for v in cls for k in outputs for q in range(8)}
    used = {}
    for v in cls:
        for k in outputs:
            u = pool.id(('u', v, k)); used[v, k] = u
            bits = [m[v, k, q] for q in range(8)]
            cnf.append([-u] + bits)
            for b in bits: cnf.append([u, -b])
    # linear equations: for each k, p, q: XOR_{v in cls, v[p]} m[v,k,q] = M_k[p][q]
    for k in outputs:
        for p in range(4):
            vs = [v for v in cls if (v >> p) & 1]
            for q in range(8):
                lits = [m[v, k, q] for v in vs]; rhs = bil.M[k][p][q]
                acc = lits[0]
                for i in range(1, len(lits)):
                    y = pool.id(('x', k, p, q, i)); x1, x2 = acc, lits[i]
                    cnf.extend([[-y, x1, x2], [-y, -x1, -x2], [y, -x1, x2], [y, x1, -x2]]); acc = y
                cnf.append([acc] if rhs else [-acc])
    # Kraft per output
    for k in outputs:
        lits = []
        for v in cls:
            for r in range(W[v]):
                if r == 0: lits.append(used[v, k])
                else:
                    e = pool.id(('e', v, k, r)); cnf.extend([[-e, used[v, k]], [e, -used[v, k]]]); lits.append(e)
        cnf.extend(CardEnc.atmost(lits=lits, bound=budget, vpool=pool, encoding=EncType.seqcounter).clauses)
    # distinct products: new[v,k] if used and differs from all earlier outputs' m in class v
    news = []
    ks = list(outputs)
    for v in cls:
        for i, k in enumerate(ks):
            nw = pool.id(('new', v, k)); news.append(nw)
            eqs = []
            for k2 in ks[:i]:
                e = pool.id(('eq', v, k, k2)); eqs.append(e)
                # e -> m[v,k,q] == m[v,k2,q] for all q
                for q in range(8):
                    a, b = m[v, k, q], m[v, k2, q]
                    cnf.extend([[-e, -a, b], [-e, a, -b]])
            # used & not new -> some eq
            cnf.append([-used[v, k], nw] + eqs)
    cnf.extend(CardEnc.atmost(lits=news, bound=P, vpool=pool, encoding=EncType.seqcounter).clauses)
    return pool, cnf, m, used, cls, W, budget


def decode(model, m, used, cls, outputs=range(8)):
    ms = set(l for l in model if l > 0)
    prods = {}   # (alpha, g) -> incidence bits
    for v in cls:
        for k in outputs:
            if used[v, k] not in ms: continue
            g = sum(bil.GMASK[q] for q in range(8) if m[v, k, q] in ms)
            key = (bil.ALPHA[v], g)
            prods[key] = prods.get(key, 0) | (1 << (7 - k))
    return [(al, g, O.w_of(cv)) for (al, g), cv in prods.items()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('P', type=int); ap.add_argument('out')
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--solver', default='cd19')
    a = ap.parse_args()
    F = ylev.front(ylev.load(a.front))
    lev = {v: F['levels'][v][0] for v in range(1, 16)}
    t0 = time.time()
    pool, cnf, m, used, cls, W, budget = encode(lev, a.D, a.P)
    print('levels', sorted((lev[v], bil.ALPHA[v]) for v in lev), 'classes', len(cls), 'budget', budget,
          'vars', pool.top, 'clauses', len(cnf.clauses), flush=True)
    with Solver(name=a.solver, bootstrap_with=cnf.clauses) as S:
        tm = threading.Timer(a.seconds, lambda: S.interrupt()); tm.start()
        r = S.solve_limited(expect_interrupt=True); tm.cancel()
        el = time.time() - t0
        rec = {'front': a.front, 'D': a.D, 'P': a.P, 'elapsed': round(el, 1)}
        if r is None: rec['status'] = 'TIMEOUT'
        elif r is False: rec['status'] = 'UNSAT'
        else:
            dec = decode(S.get_model(), m, used, cls)
            rec.update(status='SAT', nprod=len(dec), check=O.check(dec), dec=dec)
        print(json.dumps({k: v for k, v in rec.items() if k != 'dec'}), flush=True)
        with open(a.out, 'a') as fh: fh.write(json.dumps(rec) + '\n')


if __name__ == '__main__':
    main()
