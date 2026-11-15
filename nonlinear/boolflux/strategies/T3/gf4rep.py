#!/usr/bin/env python3
"""T3: for GF(4)-point quadruples (gf4search JSON), try all representative scalings of points 2-4
(27 combos: same 12 R functions, different Q pairing = different products and bottom layer), keep
admissible ones, price the bottom (Paar), write a JSON in gf4search format sorted by (region-2 + bottom).
    gf4rep.py SRC SEARCH.json OUT.json [--top 500]"""
import itertools
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import load, _gmul, ONES      # noqa: E402
from pairs import and_levels, Basis                    # noqa: E402
from prodswap import RBasis                            # noqa: E402
from gf4basis import RT, QT                            # noqa: E402
from gf4search import paar                             # noqa: E402

src, sj, oj = sys.argv[1:4]
top = int(sys.argv[5]) if len(sys.argv) > 5 else 500
c = load(src); t = c.tables(); outs = [t[s] for s in c.outputs]
J = json.load(open(sj)); rho = J['rho']; ws = J['ws']
scal = [1, rho, _gmul(rho, rho)]
res = []
seen = set()
for tot, r2, b, a, combo in J['res'][:top]:
    for sc in itertools.product(range(3), repeat=3):
        pts = [combo[0]] + [_gmul(scal[k], p) for k, p in zip(sc, combo[1:])]
        prods = [QT[w] & RT[_gmul(s, l)] for w, s in zip(ws, scal) for l in pts]
        Rb = RBasis([ONES] + prods)
        rows = []; ok = True
        for o in outs:
            rr, m = Rb.reduce(o)
            if rr: ok = False; break
            rows.append(m >> 1)
        if not ok: continue
        bb = paar(rows, 12)
        res.append((r2 + bb, r2, bb, a, pts))
res.sort()
print('combos admissible', len(res))
for x in res[:25]: print(x)
J2 = dict(J); J2['res'] = res[:1000]
Path(oj).write_text(json.dumps(J2))
