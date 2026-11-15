"""Karatsuba-type 9-product covers of V_N (real 256-point tables), deduplicated by span mod affine.
kara:a,b,c,d,P1,P2,P3 = products tau(r ev_P(aL+bR)) tau(r ev_P(cL+dR)), r in GF(4)*, P in 3 of the
5 points of P^1(GF(4)).  (aL+bR)(cL+dR) = (ad+bc)LR + linear, and D = LR + linear.
Also canonical-form dedupe under the swap L <-> R is NOT applied (cheap to test both).
usage: kfam256.py OUT [max]"""
import sys, itertools, random
from h2lib import Basis
import tsearch as TS, tbuild as TB, a28parse as AP
from tower import m4, tau, W, W2, MUL, norm, ONE16

CLS = [(0, 1), (W, 0), (W, 1), (W, W), (W, 3)]
LRx = [TB.LR(x) for x in range(256)]
AFF = Basis()
for v in [AP.ONE] + AP.BITS: AFF.add(v)
DT = [TB.T256(lambda x, j=j: norm(*LRx[x]) >> j & 1) for j in range(4)]


def cover(a, b, c, d, pts):
    out = []
    for pi in pts:
        c1, c0 = CLS[pi]
        ev = lambda u, c1=c1, c0=c0: m4(c1, TS.g16(u)[0]) ^ m4(c0, TS.g16(u)[1])
        u1 = [ev(MUL[a][L] ^ MUL[b][R]) for L, R in LRx]
        u2 = [ev(MUL[c][L] ^ MUL[d][R]) for L, R in LRx]
        for r in (1, W, W2):
            out.append(TB.T256(lambda x, r=r: tau(m4(r, u1[x])) & tau(m4(r, u2[x]))))
    return out


def key(prods):
    B = AFF.copy()
    for p in prods: B.add(p)
    if B.n - AFF.n != 9 or not all(B.contains(t) for t in DT): return None
    E = Basis()
    for p in prods: E.add(AFF.full_reduce(p)[0])
    vs = [r[0] for r in E.rows.values()]
    piv = [v.bit_length() - 1 for v in vs]
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i != j and (vs[j] >> piv[i]) & 1: vs[j] ^= vs[i]
    return tuple(sorted(vs))


if __name__ == '__main__':
    out = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 10 ** 9
    random.seed(1)
    quads = [(ONE16, 0, 0, ONE16)] + [(ONE16, b, c, ONE16) for b in range(16) for c in range(16) if (b, c) != (0, 0)]
    seen = set(); specs = []
    for a, b, c, d in quads:
        if (MUL[a][d] ^ MUL[b][c]) == 0: continue
        for pts in itertools.combinations(range(5), 3):
            k = key(cover(a, b, c, d, pts))
            if k is None or k in seen: continue
            seen.add(k); specs.append('kara:%d,%d,%d,%d,%d,%d,%d' % (a, b, c, d, *pts))
        if len(specs) >= mx: break
    open(out, 'w').write('\n'.join(specs) + '\n')
    print('distinct covers', len(specs))
