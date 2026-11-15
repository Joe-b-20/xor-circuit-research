#!/usr/bin/env python3
"""T3: distribution of the bottom-layer price (Paar greedy, 8 outputs from the 12 level-3 products) over
random admissible GF(4)-point quadruples (aligned class bases), and the region-2 entry price of the
best ones.  python3 bottomscan.py CIRCUIT N SEED [OUT.json]"""
import json
import random
import sys
from collections import Counter
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, _gmul, ONES      # noqa: E402
from pairs import and_levels, Basis                    # noqa: E402
from prodswap import RBasis                            # noqa: E402
from gf4basis import RT, QT                            # noqa: E402
from gf4search import paar                             # noqa: E402

c = load(sys.argv[1]); N = int(sys.argv[2]); rng = random.Random(int(sys.argv[3]))
t = c.tables(); outs = [t[s] for s in c.outputs]
ws = [2, 32, 34]; rho = 188
scal = [1, rho, _gmul(rho, rho)]
hist = Counter(); best = []
for _ in range(N):
    pts = [rng.randrange(1, 256) for _ in range(4)]
    B = Basis([])
    if not all(B.add(_gmul(s, p)) for p in pts for s in (1, rho)): continue
    prods = [QT[w] & RT[_gmul(s, l)] for w, s in zip(ws, scal) for l in pts]
    Rb = RBasis([ONES] + prods); rows = []; ok = True
    for o in outs:
        r, m = Rb.reduce(o)
        if r: ok = False; break
        rows.append(m >> 1)
    if not ok: hist['inadmissible'] += 1; continue
    b = paar(rows, 12); hist[b] += 1
    best.append((b, pts))
best.sort()
print(sorted(hist.items(), key=lambda x: str(x[0])))
print(best[:20])
if len(sys.argv) > 4:
    Path(sys.argv[4]).write_text(json.dumps({'rho': rho, 'ws': ws, 'res': [(b, 0, b, 0, p) for b, p in best[:2000]]}))
