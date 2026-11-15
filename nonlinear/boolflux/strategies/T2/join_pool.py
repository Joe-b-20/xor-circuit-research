#!/usr/bin/env python3
"""All-pairs joins (hub/join.py: front of X, back of Y, linear interface) over a pool of circuits, keeping
every distinct product with (A, AD, G, GD) <= --max.  Output: OUT/j-a..-ad..-g..-gd..-<sha>.bfx and
OUT/joins.jsonl (front, back, LX, LY, interface gates, metrics).

  join_pool.py --archive DIR --ids ID ... [--files F ...] --max 32,6,108,34 --out OUT [--seconds T]
"""
import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux.hub.common import core, metrics  # noqa: E402
from boolflux.hub import join as J  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--archive'); ap.add_argument('--ids', nargs='*', default=[])
    ap.add_argument('--files', nargs='*', default=[])
    ap.add_argument('--max', required=True); ap.add_argument('--out', required=True)
    ap.add_argument('--seconds', type=float, default=1e9)
    a = ap.parse_args()
    mx = tuple(int(x) for x in a.max.split(','))
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    pool = []
    for i in a.ids:
        pool.append((i, core.from_kernel((Path(a.archive) / 'archive' / (i + '.bfx')).read_text(), i)))
    for f in a.files:
        p = Path(f)
        pool.append((p.name, core.from_kernel(p.read_text()) if p.suffix == '.bfx' else core.read_ncff(str(p))))
    P = [J.Prepared(c, n) for n, c in pool]
    log = open(out / 'joins.jsonl', 'a'); seen = set(); t0 = time.time(); tried = 0; kept = 0
    best = {}
    for X in P:
        for Y in P:
            if X is Y: continue
            if time.time() - t0 > a.seconds: break
            for c, LX, LY, nint in J.join_all(X, Y):
                tried += 1
                m = metrics(c)
                if not all(v <= w for v, w in zip(m, mx)): continue
                k = core.to_kernel(c); h = hashlib.sha1(k.encode()).hexdigest()[:12]
                if h in seen: continue
                seen.add(h); kept += 1
                (out / ('j-a%d-ad%d-g%d-gd%d-%s.bfx' % (m + (h,)))).write_text(k)
                log.write(json.dumps({'id': h, 'm': m, 'front': X.id, 'back': Y.id, 'LX': LX, 'LY': LY, 'nint': nint}) + '\n')
                key = (m[1], m[3]);
                if key not in best or m[2] < best[key][0]: best[key] = (m[2], h)
        log.flush()
    print('tried', tried, 'kept', kept, 'secs', round(time.time() - t0, 1))
    for k in sorted(best): print('AD %d GD %d  G %d  %s' % (k + best[k]))


main()
