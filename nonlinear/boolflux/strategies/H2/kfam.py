"""Generate Karatsuba-type 9-product covers of V_N in the tower model, deduplicated by span.

Cover kara:a,b,c,d,P1,P2,P3 = the 9 products tau(r ev_P(aL+bR)) tau(r ev_P(cL+dR)), r in GF(4)*,
P in {P1,P2,P3} (3 of the 5 points of P^1(GF(4))).  (aL+bR)(cL+dR) = (ad+bc) LR + linear, so the
span contains D iff ad + bc != 0 and the 3 evaluations reconstruct the product (checked).
usage: kfam.py OUT [max]   -> writes one spec per line (distinct spans mod affine)."""
import sys, itertools, random
from h2lib import Basis
import tsearch as TS
from tower import tab, VAR, ONE, m4, tau, W, MUL, norm, ONE16

CLS = [(0, 1), (W, 0), (W, 1), (W, W), (W, 3)]
AFF = Basis()
for v in [ONE] + VAR: AFF.add(v)
DT = [tab(lambda L, R, v, j=j: norm(L, R) >> j & 1) for j in range(4)]


def cover(a, b, c, d, pts):
    out = []
    for pi in pts:
        c1, c0 = CLS[pi]
        def ev(u, c1=c1, c0=c0):
            A1, A0 = TS.g16(u); return m4(c1, A1) ^ m4(c0, A0)
        for r in (1, W, 3):
            out.append(tab(lambda L, R, v, r=r, ev=ev: tau(m4(r, ev(MUL[a][L] ^ MUL[b][R]))) &
                           tau(m4(r, ev(MUL[c][L] ^ MUL[d][R])))))
    return out


def key(prods):
    B = AFF.copy()
    for p in prods: B.add(p)
    if not all(B.contains(t) for t in DT): return None
    # canonical: reduced row echelon of the span mod affine
    E = Basis()
    for p in prods: E.add(AFF.full_reduce(p)[0])
    rows = sorted(E.rows.values())
    # full reduction for canonical form
    vs = [r[0] for r in rows]
    piv = [v.bit_length() - 1 for v in vs]
    for i in range(len(vs)):
        for j in range(len(vs)):
            if i != j and (vs[j] >> piv[i]) & 1: vs[j] ^= vs[i]
    return tuple(sorted(vs))


if __name__ == '__main__':
    out = sys.argv[1]; mx = int(sys.argv[2]) if len(sys.argv) > 2 else 50
    random.seed(1)
    seen = {}
    specs = []
    cands = [(ONE16, 0, 0, ONE16)] + [(ONE16, b, c, ONE16) for b in range(16) for c in range(16)]
    random.shuffle(cands[1:])
    for a, b, c, d in cands:
        for pts in itertools.combinations(range(5), 3):
            if len(specs) >= mx: break
            # ad + bc != 0
            if (MUL[a][d] ^ MUL[b][c]) == 0: continue
            k = key(cover(a, b, c, d, pts))
            if k is None or k in seen: continue
            seen[k] = 1
            specs.append('kara:%d,%d,%d,%d,%d,%d,%d' % (a, b, c, d) + '' if False else 'kara:%d,%d,%d,%d,%d,%d,%d' % (a, b, c, d, *pts))
            print(specs[-1], flush=True)
        if len(specs) >= mx: break
    open(out, 'w').write('\n'.join(specs) + '\n')
