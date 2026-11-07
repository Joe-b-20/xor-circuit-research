"""c2c_debug.py: one explicit slot swap on the repo state under the own model."""
import os, sys
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
import c2_plateau as P

def mask(names):
    return sum(1 << int(n[1:]) for n in names.split("+"))

S = frozenset(P.D["repo_helpers"])
U = set(S) | P.TSET
h = mask("x7+x15+x27"); w = mask("x2+x10+x27")
print("h in S", h in S, "w in S", w in S)
V = U - {h}
stuck = P.closed_missing(V)
print("stuck after removing h:", [P.names(v) for v in stuck])
VW = V | P.ISET
print("w buildable (naive):", any((w ^ a) in VW for a in VW))
V2 = V | {w}
lev, un = P.levels(V2)
print("unreachable after add:", [P.names(v) for v in sorted(un)][:20], "count", len(un))
lev0, un0 = P.levels(U)
print("original unreachable:", len(un0), " levels of h, root:", lev0.get(h), lev0.get(mask("x2+x7+x10+x15+x27")))
# which values of U decompose using h?
users = [v for v in U if (v ^ h) in (U | P.ISET)]
print("values with a decomposition using h:", [P.names(v) for v in users])
for v in users:
    alts = [(P.names(a), P.names(v ^ a)) for a in (V | P.ISET) if (v ^ a) in (V | P.ISET) and a < (v ^ a)]
    print("   ", P.names(v), "alternative decompositions without h:", alts[:4])
