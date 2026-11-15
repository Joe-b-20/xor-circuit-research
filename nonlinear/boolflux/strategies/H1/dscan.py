"""d(X) for X = own last layer minus 1 or 2 members, over E = own stage 1 + a 5-AND middle of
another file (agent H1). Lists the subsets with |X| + d = 13 (27-relevant)."""
import sys, itertools
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf
def roles(f):
    c, a, o, ot = xag.parse(f); return [(xag.role(A), A["tab"]) for A in a], ot
for L in sys.argv[1].split(","):
    rL, T = roles(L)
    s1 = [t for r, t in rL if r == "S1"]; last = [t for r, t in rL if r not in ("S1", "MID")]
    if len(s1) != 9: print(Path(L).name, "stage 1 has", len(s1)); continue
    for M in sys.argv[2].split(","):
        rM, _ = roles(M); mid = [t for r, t in rM if r == "MID"]
        hits = []
        for r in (1, 2):
            for drop in itertools.combinations(range(len(last)), r):
                X = [t for i, t in enumerate(last) if i not in drop]
                S = xag.span([gf.ONES], gf.X, s1, mid, X); d0 = S.dim()
                for t in T: S.add(t)
                d = S.dim() - d0
                if len(X) + d <= 13: hits.append((drop, d))
        print(Path(L).name[9:36], "mid", Path(M).name[9:30], "subsets with |X|+d<=13:", hits)
