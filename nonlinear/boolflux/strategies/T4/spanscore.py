#!/usr/bin/env python3
"""T4: junk sharing through linear dependencies (not only equal residues).

Each output k with rank-2 design d needs its x-junk q_k(d) (sum of 1 or 2 rank-2 forms) in
span(stage-1 + extra junk ANDs).  Choose a basis set B of (output, design) whose constituent rank-2
forms are created as ANDs (cost = number of constituents); every other output whose x-junk lies in
span(S1 + constituents(B)) gets its design for free.  d-junk: pairs whose Y_a Y_b is outside the
front span cost one shared AND each (unless the design's sum is free).
Exhaustive over |B| <= MAXB on the given front.
    python3 spanscore.py FILE [MAXB]"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red  # noqa

DES = [('p3', ((a, b),)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
SAVE = {'p3': 1, 'p2': 2}

if __name__ == '__main__':
    c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
    maxb = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    outs = decompose(c, T, la, ba, 4)
    ys = sorted({y for d in outs for y in d})
    S1 = [qform(T[s]) for s in fa if la[s] == 1]
    pfree = {pr: ((ys[pr[0]] & ys[pr[1]]) in V) for pr in itertools.combinations(range(4), 2)}
    dsum_free = {}
    for di, d in enumerate(DES):
        s = 0
        for a, b in d[1]: s ^= ys[a] & ys[b]
        dsum_free[di] = s in V
    cons = {}; q = {}
    for k in range(8):
        w = [lin(outs[k].get(y, 0)) for y in ys]
        for di, d in enumerate(DES):
            cons[(k, di)] = [wedge(w[a], w[b]) for a, b in d[1]]
            qq = 0
            for x in cons[(k, di)]: qq ^= x
            q[(k, di)] = qq
    items = sorted(q)
    best = []
    for nb in range(1, maxb + 1):
        for B in itertools.combinations(items, nb):
            if len({k for k, _ in B}) < nb: continue
            red = Red(S1 + [x for it in B for x in cons[it]])
            cost = sum(len(cons[it]) for it in B)
            chosen = list(B)
            used = {k for k, _ in B}
            for k in range(8):
                if k in used: continue
                opts = [it for it in items if it[0] == k and red.red(q[it]) == 0]
                if opts:
                    chosen.append(max(opts, key=lambda it: SAVE[DES[it[1]][0]]))
            sav = sum(SAVE[DES[di][0]] for k, di in chosen)
            dp = set()
            for k, di in chosen:
                if dsum_free[di]: continue
                for pr in DES[di][1]:
                    if not pfree[pr]: dp.add(pr)
            net = sav - cost - len(dp)
            best.append((net, [(k, DES[di]) for k, di in chosen], cost, len(dp)))
    best.sort(key=lambda z: -z[0])
    seen = set()
    for z in best[:400]:
        key = json.dumps(sorted(map(str, z[1])))
        if key in seen: continue
        seen.add(key)
        print(json.dumps({'net': z[0], 'A': 48 - z[0], 'choice': z[1], 'xjunk_ands': z[2], 'djunk_ands': z[3]}))
        if len(seen) >= 12: break
