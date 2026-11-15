#!/usr/bin/env python3
"""T4: after the 44 plan (junk ANDs of outputs 1,2,3,5 p2 (0,2)(1,3) + AND(Y0,Y2)), can output 0 (or
any output) use a 3-product design with free x-forms whose junk lies in the enlarged span?
    python3 chain44.py FRONT"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red, designs, solve_design  # noqa
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
outs = decompose(c, T, la, ba, 4)
ys = sorted({y for d in outs for y in d}); nY = 4
red = Red([qform(T[s]) for s in fa if la[s] == 1])
for k in (1, 2, 3, 5):
    w = [lin(outs[k].get(y, 0)) for y in ys]
    red.add(wedge(w[0], w[2])); red.add(wedge(w[1], w[3]))
V.add(ys[0] & ys[2])
print('enlarged S1 dim', len(red.p))
E = list(itertools.combinations(range(nY), 2))
dsum_ok = {}
for r in range(0, len(E) + 1):
    for sub in itertools.combinations(E, r):
        s = 0
        for a, b in sub: s ^= ys[a] & ys[b]
        dsum_ok[frozenset(sub)] = (s in V)
from collections import Counter
D = designs(nY)
for k in range(8):
    w = [lin(outs[k].get(y, 0)) for y in ys]
    found = []
    for combo in D:
        edges = [s for kind, s in combo if kind == 'e']
        cnt = Counter(edges)
        es = frozenset(e for e, m in cnt.items() if m % 2)
        if not dsum_ok.get(es, False): continue
        x = solve_design(combo, w, red, True)
        if x is not None: found.append((len(combo), str(combo)))
    found.sort()
    print(json.dumps({'out': k, 'best_products': found[0][0] if found else 4, 'n': len(found), 'ex': found[:3]}), flush=True)
