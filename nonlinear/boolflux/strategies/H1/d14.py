"""For a 9+5+14 circuit: d(X) for X = last layer minus 1 or 2 products, over E = its own stage 1 +
middle (fixed). d = 0 for a 13-subset = a 27 directly; pairs with d = 1 go to fixk.py (agent H1)."""
import sys, itertools, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import xag
from xag import gf
for f in sys.argv[1:]:
    c, a, o, T = xag.parse(f)
    r = [(xag.role(A), A["tab"]) for A in a]
    pre = [t for ro, t in r if ro in ("S1", "MID")]; last = [t for ro, t in r if ro not in ("S1", "MID")]
    base = xag.span([gf.ONES], gf.X, pre)
    def d(X):
        S = xag.span([gf.ONES], gf.X, pre, X); d0 = S.dim()
        for t in T: S.add(t)
        return S.dim() - d0
    singles = [d(last[:i] + last[i+1:]) for i in range(len(last))]
    pairs = {}
    for i, j in itertools.combinations(range(len(last)), 2):
        dd = d([t for k, t in enumerate(last) if k not in (i, j)])
        pairs.setdefault(dd, []).append((i, j))
    print(json.dumps({"file": Path(f).name, "k": len(last), "pre": len(pre), "d_full": d(last),
                      "d_single": singles, "pairs_by_d": {k: (v if k <= 1 else len(v)) for k, v in sorted(pairs.items())}}))
