"""Quadratic junk of a circuit in coset coordinates (agent H1).

Every quadratic Boolean function is  Tr(c3 x^3) + Tr(c5 x^5) + Tr(c9 x^9) + Tr_K(c17 x^17) + affine.
For the S1-parts of the outputs (decomp.py) and for the stage-1 products themselves we report the
(c3, c5, c9) components (the c17 component is V_N) and the dims of the projections.
usage: python3 junk.py FILE ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, deps, span, AFFX, NC
from decomp import name


def comps(tab):
    return tuple(xag.coeff(tab, e) for e in (3, 5, 9, 17))


def rank_vecs(vs):
    S = gf.Span()
    for v in vs:
        x = 0
        for i, c in enumerate(v): x |= c << (8 * i)
        S.add(x)
    return S.dim()


for f in sys.argv[1:]:
    c, ands, outs, ot = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    s1 = [k for k in range(len(ands)) if roles[k] == 'S1']
    parts = []
    for o in outs:
        t = 0
        for k in deps(o):
            if roles[k] == 'S1': t ^= ands[k]['tab']
        parts.append(t)
    J = [comps(t)[:3] for t in parts]
    P = [comps(ands[k]['tab']) for k in s1]
    print(Path(f).name[9:45], 'junk (c3,c5,c9) rank %d; per-class rank c3 %d c5 %d c9 %d' % (
        rank_vecs(J), rank_vecs([(v[0],) for v in J]), rank_vecs([(v[1],) for v in J]),
        rank_vecs([(v[2],) for v in J])),
          '| S1 products: (c3,c5,c9) rank %d, c5-rank %d' % (
              rank_vecs([p[:3] for p in P]), rank_vecs([(p[1],) for p in P])))
