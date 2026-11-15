#!/usr/bin/env python3
"""T4: all output pairs x all rank-2 designs (p3 a b, p2 pairing): x-junk of the two outputs equal
modulo the front span V (then the junk ANDs are shared).  Also d-junk status.
    python3 pairscan.py FILE"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
AD = max(la[o] for o in c.outputs)
outs = decompose(c, T, la, ba, AD)
ys = sorted({y for d in outs for y in d})
DES = [('p3', (a, b)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
def pairs_of(d): return [d[1]] if d[0] == 'p3' else list(d[1])
def xj(k, d):
    w = [outs[k].get(y, 0) for y in ys]; r = 0
    for a, b in pairs_of(d): r ^= w[a] & w[b]
    return r
def dfree(d):
    s = 0
    for a, b in pairs_of(d): s ^= ys[a] & ys[b]
    return s in V
import os
extra = os.environ.get('T4_EXTRA', '')     # e.g. "x:1:0:2,x:1:1:3,y:0:2"  (x-junk of output k pair a b; d-junk pair)
for item in [e for e in extra.split(',') if e]:
    parts = item.split(':')
    if parts[0] == 'x':
        k, a, b = map(int, parts[1:]); w = [outs[k].get(y, 0) for y in ys]; V.add(w[a] & w[b])
    else:
        a, b = map(int, parts[1:]); V.add(ys[a] & ys[b])
for k in range(8):
    for d in DES:
        if xj(k, d) in V:
            print(json.dumps({'single': k, 'd': d, 'dfree': dfree(d)}))
hits = []
for k, l in itertools.combinations(range(8), 2):
    for dk in DES:
        for dl in DES:
            if (xj(k, dk) ^ xj(l, dl)) in V:
                sav = (1 if dk[0] == 'p3' else 2) + (1 if dl[0] == 'p3' else 2)
                xcost = len(pairs_of(dk))
                h = {'k': k, 'l': l, 'dk': dk, 'dl': dl, 'saved_products': sav, 'xjunk_ands': xcost,
                     'dfree_k': dfree(dk), 'dfree_l': dfree(dl)}
                hits.append(h); print(json.dumps(h))
print('d-free designs:', [d for d in DES if dfree(d)])
