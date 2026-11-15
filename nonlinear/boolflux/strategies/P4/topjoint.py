"""P4: joint top + pre-inversion test.

For every top layer with (#forms + H) gates (every value a form or one of H helpers; exact by the
closure argument of topenum.py) that meets the form deadlines of the reference at GD cap, compute
Avail = inputs + forms + helpers and the 4-injection bases ('good sets', preinj.py) of the
pre-inversion targets.  A triple with a good set is a candidate for pre = 10 + 4 = 14 gates.

    python3 topjoint.py CIRC H GD [--targets t30,t31,t32,t33] > out.jsonl
"""
import argparse
import itertools
import json
import sys
import time

import circ
import preinj
import topenum


def good_sets(X, avail, ntg=4, k=4):
    out = []
    for B in itertools.combinations(range(1, 1 << ntg), k):
        if preinj.rank(list(B)) < ntg:
            continue
        S = preinj.solve_basis(list(B), X, ntg)
        if S is not None and all(v in avail for v in S):
            out.append((B, S))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('circ')
    ap.add_argument('H', type=int)
    ap.add_argument('gd', type=int)
    ap.add_argument('--targets', default='t30,t31,t32,t33')
    a = ap.parse_args()
    gates, s, forms, inj = topenum.top_spec(a.circ, a.gd)
    F = {m: d for m, d in forms.items() if bin(m).count('1') > 1}
    names = a.targets.split(',')
    xm = lambda atoms: sum(1 << int(t[1:]) for t in atoms if t[0] == 'x')
    X = [xm(s[n][0]) for n in names]
    allv = [v for v in range(1, 256) if bin(v).count('1') > 1 and v not in F]
    inputs = {1 << i for i in range(8)}
    t0 = time.time()
    nfeas = 0
    ncand = 0
    for hs in itertools.combinations(allv, a.H):
        S = set(F) | set(hs)
        lv = topenum.closure_levels(S)
        if not (all(t in lv for t in S) and all(lv[t] <= d for t, d in F.items())):
            continue
        nfeas += 1
        avail = inputs | set(F) | set(hs)
        g = good_sets(X, avail)
        if g:
            ncand += 1
            print(json.dumps(dict(helpers=list(hs), levels={str(k): v for k, v in lv.items()},
                                  good=[[list(B), S] for B, S in g])), flush=True)
    print(json.dumps(dict(done=True, H=a.H, feasible=nfeas, candidates=ncand, elapsed=round(time.time() - t0, 1))),
          flush=True)


if __name__ == '__main__':
    main()
