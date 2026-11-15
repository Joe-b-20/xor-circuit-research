"""X3b x3b_drop.py FILE...: for a 9 + 5 + 14 (or any three-stage) circuit, drop each top product m and ask
  (a) fixed prefix:  d_a = dim(T + E + X_m) - dim(E + X_m),  E = span(1, x, stage-1, middle products)
  (b) stage 1 free:  d_b = same with E replaced by span(1, x, N, n, middle products, ALL x-quadratics)
      (necessary for a 9 + 5 + 13 with this middle and these 13 products; H1 cond27 R2 with the real middle)
  (c) for d_b = 0: U_m = V_N + quadratic parts of the outputs (unique iff Quad cap (A + X_m) adds nothing
      mod V_N, reported), dim U_m, whether U_m lies in the file's own stage-1 span, and the
      tensor test (T_b in the span of the 13 tensors).
Also every pair (m1, m2) for (a)/(b) counts: d after dropping 2 (how far a 12 is)."""
import sys, itertools
from pathlib import Path
S = Path.home() / 'xcr-boolflux/nonlinear/boolflux/strategies'
for d in ('G', 'C', 'H1'):
    sys.path.insert(0, str(S / d))
import xag, gf
from xag import ONES, AFFX, NC, nC
QUAD = [gf.X[i] & gf.X[j] for i in range(8) for j in range(i + 1, 8)]
T = [gf.bit_table(gf.INV, k) for k in range(8)]

def ech(vs):
    b = {}
    for v in vs:
        while v:
            h = v.bit_length() - 1
            if h in b: v ^= b[h]
            else: b[h] = v; break
    return b
def dim(vs): return len(ech(vs))

for f in sys.argv[1:]:
    c, ands, outs, otabs = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    s1 = [A['tab'] for A, r in zip(ands, roles) if r == 'S1']
    mid = [A['tab'] for A, r in zip(ands, roles) if r == 'MID']
    top = [k for k, r in enumerate(roles) if r not in ('S1', 'MID')]
    tops = [ands[k]['tab'] for k in top]
    assert dim(list(AFFX) + s1 + mid + tops + T) == dim(list(AFFX) + s1 + mid + tops), 'control: outputs not in span'
    E = list(AFFX) + s1 + mid
    Eb = list(AFFX) + list(NC) + list(nC) + mid + QUAD
    print('%s: S1 %d MID %d top %d' % (Path(f).name, len(s1), len(mid), len(top)))
    def d(base, X):
        return dim(base + X + T) - dim(base + X)
    print('  full layer: d_a %d d_b %d' % (d(E, tops), d(Eb, tops)))
    rowa = []; rowb = []
    for i in range(len(tops)):
        X = tops[:i] + tops[i + 1:]
        da, db = d(E, X), d(Eb, X)
        rowa.append(da); rowb.append(db)
        extra = ''
        if db == 0:
            # quadratic parts of the outputs over (A + X) then Quad
            base = list(AFFX) + list(NC) + list(nC) + mid + X
            B = {}
            tagged = [(v, 0) for v in base] + [(q, 1 << j) for j, q in enumerate(QUAD)]
            for v, tg in tagged:
                while v:
                    h = v.bit_length() - 1
                    if h in B: v ^= B[h][0]; tg ^= B[h][1]
                    else: B[h] = (v, tg); break
            qs = []
            for t in T:
                v, tg = t, 0
                while v:
                    h = v.bit_length() - 1
                    v ^= B[h][0]; tg ^= B[h][1]
                q = 0
                for j in range(28):
                    if tg >> j & 1: q ^= QUAD[j]
                qs.append(q)
            U = list(AFFX) + list(NC) + qs
            dU = dim(U) - 9
            inS1 = dim(list(AFFX) + s1 + U) == dim(list(AFFX) + s1)
            capD = dim(list(AFFX) + QUAD) + dim(base) - dim(base + QUAD) - (dim(list(AFFX) + list(NC)))
            extra = ' -> dim U %d, U in own stage 1: %s, dim(Quad cap A+X) mod V_N %d' % (dU, inS1, capD)
        print('  drop top AND %2d: d_a %d d_b %d%s' % (top[i], da, db, extra))
    pa = {}; pb = {}
    for i, j in itertools.combinations(range(len(tops)), 2):
        X = [t for k, t in enumerate(tops) if k not in (i, j)]
        a_, b_ = d(E, X), d(Eb, X)
        pa[a_] = pa.get(a_, 0) + 1; pb[b_] = pb.get(b_, 0) + 1
        if a_ <= 1 or b_ <= 1:
            print('  slack-1 pair: top-list indices (%d, %d) = AND %d, %d: d_a %d d_b %d' % (i, j, top[i], top[j], a_, b_))
    print('  drop pairs: d_a histogram %s, d_b histogram %s' % (dict(sorted(pa.items())), dict(sorted(pb.items()))))
