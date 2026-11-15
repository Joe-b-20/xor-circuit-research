"""Triples to drop from a 14-member last layer with d = 2 (11 + 2 = 13 candidates; agent H1)."""
import sys, itertools, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf
for f in sys.argv[1:]:
    c, a, o, T = xag.parse(f)
    r = [(xag.role(A), A["tab"]) for A in a]
    pre = [t for ro, t in r if ro in ("S1", "MID")]; last = [t for ro, t in r if ro not in ("S1", "MID")]
    out = []
    for tr in itertools.combinations(range(len(last)), 3):
        S = xag.span([gf.ONES], gf.X, pre, [t for k, t in enumerate(last) if k not in tr]); d0 = S.dim()
        for t in T: S.add(t)
        if S.dim() - d0 <= 2: out.append((tr, S.dim() - d0))
    print(json.dumps({"file": Path(f).name, "triples_d<=2": out}))
