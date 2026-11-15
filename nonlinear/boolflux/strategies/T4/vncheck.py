#!/usr/bin/env python3
"""T4: are the x-junk coincidences structural (q_k + q_l in span(1, x, N coordinates), i.e. valid
for ANY stage-1 cover)?   python3 vncheck.py FILE"""
import sys, itertools, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from rank2 import Span, load, analyse, ONES  # noqa
from xjunk import decompose  # noqa
from absorb import N_tables  # noqa
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
outs = decompose(c, T, la, ba, 4)
ys = sorted({y for d in outs for y in d})
VN = Span([ONES] + [T[i] for i in range(8)] + N_tables())
DES = [('p3', (a, b)) for a, b in itertools.combinations(range(4), 2)] + \
      [('p2', ((0, 1), (2, 3))), ('p2', ((0, 2), (1, 3))), ('p2', ((0, 3), (1, 2)))]
def pairs_of(d): return [d[1]] if d[0] == 'p3' else list(d[1])
def xj(k, d):
    w = [outs[k].get(y, 0) for y in ys]; r = 0
    for a, b in pairs_of(d): r ^= w[a] & w[b]
    return r
for k, l in itertools.combinations(range(8), 2):
    for dk in DES:
        for dl in DES:
            s = xj(k, dk) ^ xj(l, dl)
            if s in V:
                print(json.dumps({'k': k, 'l': l, 'dk': dk, 'dl': dl, 'in_V': True, 'in_span_1_x_N': s in VN}))
