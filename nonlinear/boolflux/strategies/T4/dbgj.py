import sys, itertools
sys.path.insert(0, '.'); sys.path.insert(0, '../../..')
import joint44 as J
from rank2 import load, analyse
from xjunk import decompose
from chain import lin, wedge, qform, Red
from boolflux import skeleton
c = load(sys.argv[1]); T, lg, la, fa, ba, V, X = analyse(c)
sk = skeleton.extract(c)
own = [sk['ands'][k] for k, s in enumerate([8 + j for j, g in enumerate(c.gates) if g[0] == 8]) if la[s] == 1]
keys = [frozenset({L >> 1, R >> 1, (L ^ R) >> 1}) for L, R in own]
S1 = Red(J.VN + [wedge(*sorted(k)[:2]) for k in keys])
print('S1 dim', len(S1.p))
basis = [12, 81, 92, 176]
ws = J.wforms(basis)
outs = decompose(c, T, la, ba, 4)
ys = sorted({y for d in outs for y in d})
order48 = [92, 81, 176, 12]
for k in (1, 4):
    w48 = [lin(outs[k].get(y, 0)) for y in ys]
    wj = {a: ws[k][basis.index(a)] for a in basis}
    print('out', k, 'w48', [hex(x) for x in w48], 'wjoint(48 order)', [hex(wj[a]) for a in order48])
def q(wsk, pairs):
    r = 0
    for a, b in pairs: r ^= wedge(wsk[a], wsk[b])
    return r
q1 = q(ws[1], ((0, 2), (1, 3))); q4 = q(ws[4], ((0, 2), (1, 3)))
print('joint residues equal:', S1.red(q1) == S1.red(q4))
w1 = [lin(outs[1].get(y, 0)) for y in ys]; w4 = [lin(outs[4].get(y, 0)) for y in ys]
q1b = q(w1, ((0, 2), (1, 3))); q4b = q(w4, ((0, 2), (1, 3)))
print('48 residues equal:', S1.red(q1b) == S1.red(q4b))
import collections
byres = collections.defaultdict(list)
for k in range(8):
    for di, d in enumerate(J.DES):
        qq = 0
        for a, b in d[1]: qq ^= wedge(ws[k][a], ws[k][b])
        byres[S1.red(qq)].append((k, di))
print([[ (k, J.DES[di]) for k, di in L] for r, L in byres.items() if len({k for k, _ in L}) >= 2])
