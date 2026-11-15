"""Express each output S1-part (x-junk + N) as a combination of the circuit\x27s own S1 products
modulo V_N: minimal number of S1 products per junk class (agent H1)."""
import sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf, deps, NC
for f in sys.argv[1:]:
    c, ands, outs, ot = xag.parse(f)
    roles = [xag.role(A) for A in ands]
    s1 = [k for k in range(len(ands)) if roles[k] == "S1"]
    q = {k: gf.anf_quadratic_part(ands[k]["tab"]) for k in s1}
    VN = gf.Span([gf.anf_quadratic_part(t) for t in NC])
    parts = []
    for o in outs:
        t = 0
        for k in deps(o):
            if roles[k] == "S1": t ^= q[k]
        parts.append(t)
    # junk classes = span of parts mod V_N
    SU = gf.Span([gf.anf_quadratic_part(t) for t in NC]); J = []
    for p in parts:
        if SU.add(p): J.append(p)       # independent modulo V_N + earlier junk
    res = []
    for m in range(1, 1 << len(J)):
        v = 0
        for i in range(len(J)):
            if m >> i & 1: v ^= J[i]
        best = None
        for r in range(1, len(s1) + 1):
            for sub in itertools.combinations(s1, r):
                w = v
                for k in sub: w ^= q[k]
                if VN.contains(w): best = (r, [k + 1 for k in sub]); break
            if best: break
        res.append(best)
    print(Path(f).name[9:40], "junk classes as sums of S1 products mod V_N:", res)
