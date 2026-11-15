#!/usr/bin/env python3
"""T3: two-point neighbourhood built from the best one-point changes (nbscan JSONL): for index pairs
i < j combine the K best replacement points at i and at j; build keep2; emit the best.
    python3 nb2.py SRC NB.jsonl OUT.jsonl --k 8 [--emit DIR --emit-max 20]"""
import argparse
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import load, metrics, cid, _gmul   # noqa: E402
from pairs import Basis                                     # noqa: E402
from gf4build import build                                  # noqa: E402
from nbscan import current_points                           # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('src'); ap.add_argument('nb'); ap.add_argument('out'); ap.add_argument('--k', type=int, default=8)
ap.add_argument('--emit'); ap.add_argument('--emit-max', type=int, default=20)
a = ap.parse_args()
c = load(a.src); pts0 = current_points(c); G0 = metrics(c)[2]
rows = [json.loads(l) for l in open(a.nb)]
best = {i: [] for i in range(4)}
for r in rows:
    if r['G'] <= G0 + 1: continue          # same R set (scalings of the current point)
    if len(best[r['i']]) < a.k: best[r['i']].append(r['p'])
res = []; seen = set()
for i in range(4):
    for j in range(i + 1, 4):
        for p in best[i]:
            for q in best[j]:
                pts = list(pts0); pts[i] = p; pts[j] = q
                B = Basis([])
                if not all(B.add(_gmul(s, x)) for x in pts for s in (1, 188)): continue
                try:
                    nc = build(c, pts, keep2=True)
                except AssertionError:
                    continue
                m = metrics(nc); k = cid(nc)
                if k in seen: continue
                seen.add(k); res.append((m[2], m[3], pts, k, nc))
res.sort(key=lambda x: (x[0], x[1]))
with open(a.out, 'w') as f:
    for g, gd, pts, k, nc in res: f.write(json.dumps({'G': g, 'GD': gd, 'points': pts, 'id': k}) + '\n')
print('built', len(res), 'best', [(x[0], x[1]) for x in res[:15]])
if a.emit:
    d = Path(a.emit); d.mkdir(parents=True, exist_ok=True)
    for g, gd, pts, k, nc in res[:a.emit_max]:
        (d / ('a35-ad3-g%d-gd%d-%s.bfx' % (g, gd, k))).write_text(core.to_kernel(nc))
