#!/usr/bin/env python3
"""P2: the bsat3 model (one product per alpha class per output) in OR-tools CP-SAT with table
constraints instead of XOR chains.

For output k and x-coordinate q, v_{k,q} in GF(2)^15 (bit per alpha class) must satisfy
sum_alpha v[alpha] * alpha = column q of M_k: an affine space of 2^11 vectors -> AllowedAssignments.
m_{alpha,k} = (v_{k,q}[alpha])_q; used_{alpha,k} = OR_q; Kraft per output (integers);
products = distinct (alpha, m != 0); minimise (or bound) the number of products.

    python3 cp3.py FRONT D OUT.jsonl [--P P] [--seconds T] [--workers 1] [--classes-maxw W]
"""
import argparse
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bil    # noqa: E402
import ylev   # noqa: E402
import orbit as O   # noqa: E402
from ortools.sat.python import cp_model   # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('front'); ap.add_argument('D', type=int); ap.add_argument('out')
    ap.add_argument('--P', type=int, default=None, help='hard bound on products (else minimise)')
    ap.add_argument('--seconds', type=float, default=600); ap.add_argument('--workers', type=int, default=1)
    ap.add_argument('--maxw', type=int, default=None)
    a = ap.parse_args()
    F = ylev.front(ylev.load(a.front))
    lev = {v: F['levels'][v][0] for v in range(1, 16)}
    minlev = min(lev.values()); budget = 2 ** (a.D - 1 - minlev)
    W = {v: 2 ** (lev[v] - minlev) for v in lev}
    cls = [v for v in range(1, 16) if W[v] <= (a.maxw or budget)]
    print('levels', sorted((lev[v], bil.ALPHA[v]) for v in lev), 'budget', budget, 'classes', len(cls), flush=True)
    # solutions table per column vector (4 bits)
    sols = {c: [] for c in range(16)}
    for msk in range(1 << len(cls)):
        x = 0
        for i, v in enumerate(cls):
            if (msk >> i) & 1: x ^= v
        sols[x].append([(msk >> i) & 1 for i in range(len(cls))])
    md = cp_model.CpModel()
    v = {}
    for k in range(8):
        for q in range(8):
            col = sum(bil.M[k][p][q] << p for p in range(4))
            vs = [md.NewBoolVar('v%d_%d_%d' % (k, q, i)) for i in range(len(cls))]
            md.AddAllowedAssignments(vs, sols[col])
            for i in range(len(cls)): v[k, q, i] = vs[i]
    used = {}
    for k in range(8):
        for i in range(len(cls)):
            u = md.NewBoolVar('u%d_%d' % (k, i)); used[k, i] = u
            md.AddMaxEquality(u, [v[k, q, i] for q in range(8)])
        md.Add(sum(W[cls[i]] * used[k, i] for i in range(len(cls))) <= budget)
    # distinct products: new[k,i] = used and differs from all earlier k' in class i
    news = []
    for i in range(len(cls)):
        for k in range(8):
            nw = md.NewBoolVar('n%d_%d' % (k, i)); news.append(nw)
            eqs = []
            for k2 in range(k):
                e = md.NewBoolVar('e%d_%d_%d' % (k, k2, i)); eqs.append(e)
                for q in range(8):
                    md.Add(v[k, q, i] == v[k2, q, i]).OnlyEnforceIf(e)
            # used and not new -> some eq
            md.AddBoolOr(eqs + [nw, used[k, i].Not()])
            md.AddImplication(nw, used[k, i])
    tot = sum(news)
    if a.P is not None: md.Add(tot <= a.P)
    else: md.Minimize(tot)
    s = cp_model.CpSolver()
    s.parameters.max_time_in_seconds = a.seconds
    s.parameters.num_search_workers = a.workers
    s.parameters.log_search_progress = False

    class CB(cp_model.CpSolverSolutionCallback):
        def __init__(self):
            super().__init__(); self.t0 = time.time()
        def on_solution_callback(self):
            print('%.1fs solution products %d bound %.0f' % (time.time() - self.t0, self.ObjectiveValue() if a.P is None else -1,
                                                          self.BestObjectiveBound() if a.P is None else -1), flush=True)
    t0 = time.time()
    st = s.Solve(md, CB())
    rec = {'front': a.front, 'D': a.D, 'P': a.P, 'status': s.StatusName(st), 'elapsed': round(time.time() - t0, 1),
           'model': 'one product per alpha class per output; classes %d' % len(cls)}
    if st in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        prods = {}
        for k in range(8):
            for i in range(len(cls)):
                if s.Value(used[k, i]):
                    g = sum(bil.GMASK[q] for q in range(8) if s.Value(v[k, q, i]))
                    key = (bil.ALPHA[cls[i]], g); prods[key] = prods.get(key, 0) | (1 << (7 - k))
        dec = [(al, g, O.w_of(cv)) for (al, g), cv in prods.items()]
        rec.update(nprod=len(dec), check=O.check(dec), dec=dec)
        if a.P is None: rec['bound'] = s.BestObjectiveBound()
    elif a.P is None:
        rec['bound'] = s.BestObjectiveBound()
    print(json.dumps({k: x for k, x in rec.items() if k != 'dec'}), flush=True)
    with open(a.out, 'a') as fh: fh.write(json.dumps(rec) + '\n')


if __name__ == '__main__':
    main()
