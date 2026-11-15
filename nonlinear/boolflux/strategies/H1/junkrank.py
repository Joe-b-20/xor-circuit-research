"""Ranks inside U = V_N + junk (agent H1): for every nonzero class j of junk mod V_N, the rank
distribution of the alternating forms j + v (v in V_N), and how many rank-2 forms U contains.
usage: python3 junkrank.py FILE ..."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, deps, NC


def qform(t):
    return gf.anf_quadratic_part(t)


PAIRS = [(i, j) for i in range(8) for j in range(i + 1, 8)]


def rank_alt(q):
    rows = [0] * 8
    for n, (i, j) in enumerate(PAIRS):
        if q >> n & 1: rows[i] |= 1 << j; rows[j] |= 1 << i
    r = 0
    rows = rows[:]
    for c in range(8):
        piv = next((k for k in range(r, 8) if rows[k] >> c & 1), None)
        if piv is None: continue
        rows[r], rows[piv] = rows[piv], rows[r]
        for k in range(8):
            if k != r and rows[k] >> c & 1: rows[k] ^= rows[r]
        r += 1
    return r


def basis(vs):
    S = gf.Span(); b = []
    for v in vs:
        if S.add(v): b.append(v)
    return b


for f in sys.argv[1:]:
    c, ands, outs, ot = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    parts = []
    for o in outs:
        t = 0
        for k in deps(o):
            if roles[k] == 'S1': t ^= ands[k]['tab']
        parts.append(qform(t))
    VN = basis([qform(t) for t in NC])
    Sv = gf.Span(VN)
    J = []
    SU = gf.Span(VN)
    for p in parts:
        if SU.add(p): J.append(p)       # independent of V_N + earlier junk
    Ub = VN + J
    allU = []
    for m in range(1, 1 << len(Ub)):
        q = 0
        for i in range(len(Ub)):
            if m >> i & 1: q ^= Ub[i]
        allU.append((m, q))
    hist = {}
    for m, q in allU:
        r = rank_alt(q); hist[r] = hist.get(r, 0) + 1
    per = []
    for mj in range(1, 1 << len(J)):
        rs = []
        for mv in range(1 << len(VN)):
            q = 0
            for i in range(len(J)):
                if mj >> i & 1: q ^= J[i]
            for i in range(len(VN)):
                if mv >> i & 1: q ^= VN[i]
            rs.append(rank_alt(q))
        per.append(min(rs))
    s1 = [qform(ands[k]['tab']) for k in range(len(ands)) if roles[k] == 'S1']
    print(Path(f).name[9:45], 'dimU %d  rank hist of U\\0 %s  min rank per junk class %s  '
          'S1 products inside U: %d/%d' % (
              len(Ub), dict(sorted(hist.items())), per,
              sum(1 for q in s1 if gf.Span(Ub).contains(q)), len(s1)))
