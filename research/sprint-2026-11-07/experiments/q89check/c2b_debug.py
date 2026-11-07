"""c2b_debug.py: debug the own remove1 model on the repo state (exclude w == h; per-helper statistics)."""
import json, os, sys, time
from collections import Counter
OUT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, OUT)
import c2_plateau as P

S = frozenset(P.D["repo_helpers"])
U = set(S) | P.TSET
g0 = len(U)
lev0, un0 = P.levels(U)
print("repo: gates", g0, "levels max", max(lev0.values()), "unreach", len(un0), "targets max level", max(lev0[t] for t in P.TSET))
stats = Counter(); outcomes = {}
t0 = time.time()
for h in sorted(S):
    V = U - {h}
    stuck = P.closed_missing(V)
    stats[f"stuck={len(stuck)}"] += 1
    if not stuck:
        T = P.trim(V, 4); outcomes[frozenset(T - P.TSET)] = len(T) - g0; stats["free"] += 1; continue
    VW = V | P.ISET
    cands = None
    for s in stuck:
        c = {s ^ a for a in VW} - VW - {0, h}
        cands = c if cands is None else cands & c
    stats["cands_total"] += len(cands)
    for w in cands:
        if not any((w ^ a) in VW for a in VW):
            stats["w not buildable"] += 1; continue
        V2 = V | {w}
        lev, un = P.levels(V2)
        if un:
            stats["unreach after add"] += 1; continue
        if max(lev[t] for t in P.TSET) > 4:
            stats["depth>4"] += 1; continue
        T = P.trim(V2, 4)
        dg = len(T) - g0
        stats[f"outcome dg={dg}"] += 1
        outcomes[frozenset(T - P.TSET)] = dg
print(dict(stats), f"{time.time()-t0:.0f}s")
print("distinct outcomes:", Counter(outcomes.values()))
for K, dg in outcomes.items():
    if K != S:
        print("  dg", dg, "removed", [P.names(v) for v in S - K], "added", [P.names(v) for v in K - S])
