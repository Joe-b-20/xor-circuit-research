#!/usr/bin/env python3
"""Exhaustive front/back joins (hub join.py) over all ordered pairs of A28 circuits.

    python3 alljoin.py OUTDIR [--extra DIR ...]

Circuits: hub archive records with A = 28 (any AD, G <= 145) + .bfx files of the --extra dirs with A = 28.
For every ordered pair (X, Y) and every cut level: join_all(X, Y).  Results with A <= 28 are tallied per
(AD, G, GD); those with goal excess <= 4 for B or C are verified and written to OUTDIR/cand/ (deduplicated).
Summary: OUTDIR/summary.json (Pareto per AD of all join results, pair count, time).
"""
import hashlib, json, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub import join as J                       # noqa: E402
from boolflux.hub.common import core, metrics, verify    # noqa: E402

HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19)}


def exc(m, g):
    if m[0] > g[0] or m[1] > g[1]: return 99
    return max(0, m[2] - g[2]) + max(0, m[3] - g[3])


out = Path(sys.argv[1]); (out / 'cand').mkdir(parents=True, exist_ok=True)
extra = sys.argv[2:]
circs = {}
for f in HUBAR.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text())
    if r['A'] == 28 and r['G'] <= 145:
        circs[r['id']] = core.from_kernel((HUBAR / (r['id'] + '.bfx')).read_text(), r['id'])
for d in extra:
    for p in Path(d).glob('*.bfx'):
        c = core.from_kernel(p.read_text(), p.stem)
        if metrics(c)[0] == 28: circs[p.stem] = c
ids = sorted(circs)
print('circuits', len(ids), flush=True)
P = {i: J.Prepared(circs[i], i) for i in ids}
t0 = time.time(); pairs = 0; res = {}; kept = {}; seen = set()
for x in ids:
    for y in ids:
        if x == y: continue
        pairs += 1
        for c, LX, LY, nint in J.join_all(P[x], P[y]):
            m = metrics(c)
            if m[0] > 28: continue
            k = (m[1], m[2], m[3]); res[k] = res.get(k, 0) + 1
            e = min(exc(m, g) for g in GOALS.values())
            if e <= 4:
                kt = core.to_kernel(c); h = hashlib.sha1(kt.encode()).hexdigest()[:12]
                if h in seen: continue
                seen.add(h)
                ok, info = verify(c)
                if not ok: continue
                (out / 'cand' / ('%d-%d-%d-%d-%s.bfx' % (m + (h,)))).write_text(kt)
                kept[h] = {'m': m, 'front': x, 'back': y, 'LX': LX, 'LY': LY, 'nint': nint}
    if pairs % 2000 < len(ids):
        print('pairs', pairs, 'kept', len(kept), round(time.time() - t0), 's', flush=True)
summ = {'circuits': len(ids), 'pairs': pairs, 'seconds': round(time.time() - t0, 1), 'kept': kept}
for ad in sorted({k[0] for k in res}):
    pts = sorted({k[1:] for k in res if k[0] == ad})
    summ['front_ad%d' % ad] = [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]
    print('AD', ad, 'join front', summ['front_ad%d' % ad])
(out / 'summary.json').write_text(json.dumps(summ, indent=1))
print('done', pairs, 'pairs', len(kept), 'kept', round(time.time() - t0), 's')
