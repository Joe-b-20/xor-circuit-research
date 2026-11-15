#!/usr/bin/env python3
"""T4: emit build46 'cx' plans for output K: every 3-product design (chain.py design graphs, free
x-forms) whose junk lies in the 44-plan's enlarged span.   python3 cxplan.py FRONT K [MAX]"""
import sys, itertools, json
from pathlib import Path
from collections import Counter
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import load, analyse  # noqa
from xjunk import decompose  # noqa
from chain import lin, wedge, qform, Red, designs, WT  # noqa
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
K = int(sys.argv[2]); MAX = int(sys.argv[3]) if len(sys.argv) > 3 else 5
import os
BASIS = [int(x) for x in os.environ.get('T4_BASIS', '1,2,3,5').split(',')]
PAIR = [tuple(int(ch) for ch in p) for p in os.environ.get('T4_PAIR', '02-13').split('-')]
MAXP = int(os.environ.get('T4_MAXP', '3'))
outs = decompose(c, T, la, ba, 4)
ys = sorted({y for d in outs for y in d})
red = Red([qform(T[s]) for s in fa if la[s] == 1])
for k in BASIS:
    w = [lin(outs[k].get(y, 0)) for y in ys]
    for a, b in PAIR: red.add(wedge(w[a], w[b]))
for a, b in PAIR:
    if (ys[a] & ys[b]) not in V: V.add(ys[a] & ys[b])
w = [lin(outs[K].get(y, 0)) for y in ys]
nfound = 0
for combo in sorted(designs(4), key=len):
    if len(combo) > MAXP: continue
    edges = [s for kind, s in combo if kind == 'e']
    cnt = Counter(edges)
    es = [e for e, m in cnt.items() if m % 2]
    s = 0
    for a, b in es: s ^= ys[a] & ys[b]
    if s not in V: continue
    slots = []
    for t, (kind, sv) in enumerate(combo):
        for v in sv: slots.append((v, t))
    byv = {}
    for idx, (v, t) in enumerate(slots): byv.setdefault(v, []).append(idx)
    free = [i for v, L in byv.items() for i in L[:-1]]
    if len(free) > 2: continue
    for vals in itertools.product(range(256), repeat=len(free)):
        x = [None] * len(slots)
        for i, val in zip(free, vals): x[i] = val
        for v, L in byv.items():
            sacc = w[v]
            for i in L[:-1]: sacc ^= x[i]
            x[L[-1]] = sacc
        j = 0; groups = []
        for t, (kind, sv) in enumerate(combo):
            ia = [i for i, (v, tt) in enumerate(slots) if tt == t]
            if kind == 'e':
                a, b = sv
                sa = x[[i for i in ia if slots[i][0] == a][0]]; sb = x[[i for i in ia if slots[i][0] == b][0]]
                j ^= WT[sa][sb]
                # product (Y_a + slot_b)(Y_b + slot_a): bilinear Y_a*slot_a + Y_b*slot_b
                groups.append('%d %d %x %x' % (a, b, sb, sa))
            else:
                a = sv[0]; groups.append('%d - %x' % (a, x[ia[0]]))
        if red.red(j) == 0:
            print('%d:cx %s' % (K, ' | '.join(groups))); nfound += 1
            per = globals().get('_per', 0) + 1; globals()['_per'] = per
            if per >= int(os.environ.get('T4_PERDESIGN', '1')) or nfound >= MAX:
                globals()['_per'] = 0
                break
    if nfound >= MAX: break
