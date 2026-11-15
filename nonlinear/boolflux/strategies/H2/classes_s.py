"""Which bilinear spans S (d = 10..13) are spanned by members of at most 3 (or 4) classes?"""
import itertools, pickle, os, sys, time
from h2lib import Basis, gmul
import relax as RX

M = RX.all_members()
w = RX.w; w2 = RX.w2
K = [k for k in RX.KSET if k]
classes = []
seen = set()
for s in K:
    if s in seen: continue
    cl = {s, gmul(w, s), gmul(w2, s)}; seen |= cl; classes.append(min(cl))
cls_of_s = {}
for i, c in enumerate(classes):
    for s in (c, gmul(w, c), gmul(w2, c)): cls_of_s[s] = i
mcls = [cls_of_s[m[4]] for m in M]
pickle.dump(mcls, open(os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/mcls.pkl'), 'wb'))
D = os.path.expanduser('~/xs-campaigns/2026-11-15-study/H2/')
for d in map(int, sys.argv[1:]):
    t0 = time.time()
    Sl = pickle.load(open(D + 'S%d.list.pkl' % d, 'rb'))
    comp = {}; tri = {}; quad = {}
    for S in Sl:
        cc = [0] * 5
        for i in S: cc[mcls[i]] += 1
        comp[tuple(cc)] = comp.get(tuple(cc), 0) + 1
        for r in (3, 4):
            for sub in itertools.combinations(range(5), r):
                B = Basis()
                for i in S:
                    if mcls[i] in sub: B.add(M[i][0])
                if B.n == d:
                    dd = tri if r == 3 else quad
                    dd[sub] = dd.get(sub, 0) + 1
    print('d', d, 'class compositions', dict(list(comp.items())[:6]), '... #', len(comp))
    print('   spanned by 3 classes:', tri, ' by 4 classes:', sum(quad.values()), round(time.time() - t0, 1), flush=True)
