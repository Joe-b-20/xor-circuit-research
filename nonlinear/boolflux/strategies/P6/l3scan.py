#!/usr/bin/env python3
"""P6: GF(4)-coordinate one-point neighbourhood (T3 nbscan) priced by the re-basing depth bound.

    python3 l3scan.py SRC --cap 12 --out OUT.jsonl [--emit DIR --emit-max 20]

For every one-point change of the level-3 coordinate choice (T3 gf4build, keep2: levels <= 2 of SRC
kept), the best class re-basing (botbasis) max output Kraft at the cap is computed; the variants
with max Kraft <= 1 are candidates for a depth pull at that cap.  Same case as botbasis [C]: lower
levels fixed, Huffman arrivals.
"""
import sys, json, time, argparse
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent / 'T3')); sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                       # noqa: E402
from boolflux.hub.common import load, metrics, cid, _gmul       # noqa: E402
from pairs import Basis                                         # noqa: E402
from gf4build import build                                      # noqa: E402
from nbscan import current_points                               # noqa: E402
import botbasis as BB                                           # noqa: E402


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('src'); ap.add_argument('--cap', type=int, default=12)
    ap.add_argument('--out', required=True); ap.add_argument('--emit'); ap.add_argument('--emit-max', type=int, default=20)
    a = ap.parse_args()
    c = load(a.src); pts0 = current_points(c)
    print('source', metrics(c), 'points', pts0, flush=True)
    tmp = Path(a.out).with_suffix('.tmp.bfx'); seen = set(); rows = []; t0 = time.time()
    f = open(a.out, 'w')
    for i in range(4):
        for p in range(1, 256):
            pts = list(pts0); pts[i] = p
            B = Basis([])
            if not all(B.add(_gmul(s, q)) for q in pts for s in (1, 188)): continue
            try:
                nc = build(c, pts, keep2=True)
            except AssertionError:
                continue
            k = cid(nc)
            if k in seen: continue
            seen.add(k)
            tmp.write_text(core.to_kernel(nc))
            try:
                res = BB.analyse(str(tmp), a.cap, verbose=False)
            except AssertionError:
                continue
            m = metrics(nc)
            row = {'i': i, 'p': p, 'points': pts, 'G': m[2], 'GD': m[3], 'kraft': res['best'], 'id': k}
            rows.append((res['best'], m[2], row, nc))
            f.write(json.dumps(row) + '\n'); f.flush()
    rows.sort(key=lambda r: (r[0], r[1]))
    print('%d variants in %.0f s; best (kraft, G):' % (len(rows), time.time() - t0), [(round(r[0], 3), r[1]) for r in rows[:15]], flush=True)
    print('max Kraft <= 1:', sum(1 for r in rows if r[0] <= 1 + 1e-9), ' < 1:', sum(1 for r in rows if r[0] < 1 - 1e-9))
    if a.emit:
        d = Path(a.emit); d.mkdir(parents=True, exist_ok=True)
        for kr, g, row, nc in rows[:a.emit_max]:
            if kr <= 1 + 1e-9:
                (d / ('a35-ad3-g%d-gd%d-k%03d-%s.bfx' % (g, row['GD'], int(kr * 100), row['id']))).write_text(core.to_kernel(nc))


if __name__ == '__main__':
    main()
