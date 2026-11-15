import pickle, sys, os
from h2lib import Basis
P = pickle.load(open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/d13/ad5-g14.txt.pkl'), 'rb'))
A28 = [((1, 2, 2, 3), (3, 0)), ((1, 2, 2, 3), (0, 3)), ((1, 1, 2, 2), (3, 0)), ((0, 0, 1, 1), (0, 1)), ((1, 3, 0, 2), (3, 0)), ((1, 2, 3, 2), (0, 3)), ((1, 3, 2, 1), (1, 2)), ((1, 2, 0, 0), (3, 0)), ((1, 3, 1, 0), (3, 0)), ((0, 1, 0, 2), (2, 3)), ((1, 3, 3, 2), (1, 2)), ((1, 0, 1, 2), (2, 3)), ((0, 1, 2, 3), (2, 3))]
mem = [(tuple(a), tuple(b)) for a, b in P['mem']]
idx = []
for m in A28:
    idx.append(mem.index(m) if m in mem else None)
print('indices', idx)
# linear consistency: combined vectors (b << 128 | j) rank vs b rank
B = Basis(); Bb = Basis()
for i in idx:
    B.add((P['b'][i] << 128) | P['j'][i]); Bb.add(P['b'][i])
print('rank (b,j)', B.n, 'rank b', Bb.n)
# all members consistent with the graph spanned by A28's (b,j)
cons = [i for i in range(len(mem)) if B.contains((P['b'][i] << 128) | P['j'][i]) and Bb.contains(P['b'][i]) and P['b'][i]]
print('consistent members with A28 graph:', len(cons), cons)
pts = {}
for i in cons: pts.setdefault(P['b'][i], []).append(i)
print('points', len(pts), 'multi', {k: v for k, v in pts.items() if len(v) > 1})
