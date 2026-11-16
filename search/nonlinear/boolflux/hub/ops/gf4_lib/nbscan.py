#!/usr/bin/env python3
"""One-point neighbourhood of the level-3 GF(4)-coordinate choice.
Current points = the c's of the first class of the source circuit. Replace point i (i = 0..3) by any
other GF(4)-point representative p (all 255 nonzero field elements, i.e. every point with its 3
scalings), build (keep2: region <= 2 of the source kept, new R's added, dead gates removed; then the
output layer by Paar), record built metrics. Writes OUT.jsonl sorted later by G.
    python3 nbscan.py SRC OUT.jsonl [--emit DIR --emit-max 40]"""
import argparse
import json
import sys
import time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[3]))
from boolflux import core                                   # noqa: E402
from boolflux.hub.common import load, metrics, cid, _gmul, ONES   # noqa: E402
from pairs import and_levels, Basis                         # noqa: E402
from gf4basis import RT, QT                                 # noqa: E402
from gf4build import build                                  # noqa: E402


def current_points(c):
    n = c.n; t = c.tables(); al = and_levels(c); NS = n + len(c.gates)
    inv = {}
    for k, v in RT.items(): inv[v] = k; inv[v ^ ONES] = k
    invq = {}
    for w, v in QT.items(): invq.setdefault(v, w)
    cur = {}
    for g in range(n, NS):
        op, a, b = c.gates[g - n]
        if op != 8 or al[g] != 3: continue
        q = [s for s in (a, b) if t[s] in invq][0]; r = [s for s in (a, b) if t[s] in inv][0]
        cur.setdefault(invq[t[q]], []).append(inv[t[r]])
    return cur[sorted(cur)[0]]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out'); ap.add_argument('--emit'); ap.add_argument('--emit-max', type=int, default=40)
    ap.add_argument('--fresh', action='store_true')
    a = ap.parse_args()
    c = load(a.src); m0 = metrics(c)
    pts0 = current_points(c)
    print('source', m0, 'points', pts0, flush=True)
    res = []; t0 = time.time()
    seen = set()
    for i in range(4):
        for p in range(1, 256):
            pts = list(pts0); pts[i] = p
            B = Basis([])
            if not all(B.add(_gmul(s, q)) for q in pts for s in (1, 188)): continue
            try:
                nc = build(c, pts, keep2=not a.fresh)
            except AssertionError:
                continue
            m = metrics(nc); k = cid(nc)
            if k in seen: continue
            seen.add(k)
            res.append((m[2], m[3], i, p, pts, k, nc))
    res.sort(key=lambda x: (x[0], x[1]))
    with open(a.out, 'w') as f:
        for g, gd, i, p, pts, k, nc in res:
            f.write(json.dumps({'G': g, 'GD': gd, 'i': i, 'p': p, 'points': pts, 'id': k}) + '\n')
    print('built %d distinct in %.0fs; best G: %s' % (len(res), time.time() - t0, [(x[0], x[1]) for x in res[:20]]), flush=True)
    if a.emit:
        d = Path(a.emit); d.mkdir(parents=True, exist_ok=True)
        for g, gd, i, p, pts, k, nc in res[:a.emit_max]:
            (d / ('a35-ad3-g%d-gd%d-%s.bfx' % (g, gd, k))).write_text(core.to_kernel(nc))


if __name__ == '__main__':
    main()
