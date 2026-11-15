#!/usr/bin/env python3
"""Cross joins A28 x (A29..A33, AD <= 5) in both roles, keeping A <= 28 results (hub join.join).

    python3 crossjoin.py OUTDIR

For a front X (cut LX) and a back Y (cut LY) the result has at most ANDs(X, level <= LX) + ANDs(Y, level > LY)
ANDs (front ANDs that nothing reads die).  Pairs/levels with ANDs(Y, > LY) > 28 or with that sum > 30 are
skipped (filter, recorded).  Results with A <= 28 are tallied per (AD, G, GD); verified near-goal ones
(excess <= 4 for B or C) go to OUTDIR/cand/.
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
A28 = {}; OTH = {}
for f in HUBAR.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text())
    if r['A'] == 28 and r['G'] <= 145: A28[r['id']] = r
    elif 29 <= r['A'] <= 33 and r['AD'] <= 5 and r['G'] <= 150: OTH[r['id']] = r
P = {}
def prep(i):
    if i not in P:
        P[i] = J.Prepared(core.from_kernel((HUBAR / (i + '.bfx')).read_text(), i), i)
        n = P[i].c.n
        P[i].andlv = [P[i].l[n + j] for j, g in enumerate(P[i].c.gates) if g[0] in core.NONLINEAR_OPS]
    return P[i]
print('A28', len(A28), 'partners', len(OTH), flush=True)
t0 = time.time(); pairs = 0; tried = 0; skipped = 0; res = {}; kept = {}; seen = set()
for k, oi in enumerate(sorted(OTH)):
    Q = prep(oi)
    for xi in sorted(A28):
        X = prep(xi)
        for F, B in ((X, Q), (Q, X)):
            pairs += 1
            for LY in range(1, B.AD):
                back = sum(1 for l in B.andlv if l > LY)
                if back > 28: skipped += 1; continue
                for LX in sorted({min(LY, F.AD - 1), F.AD - 1}):
                    if LX < 1: continue
                    if back + sum(1 for l in F.andlv if l <= LX) > 30: skipped += 1; continue
                    tried += 1
                    c, nint = J.join(F.front(LX), B, LY)
                    if c is None: continue
                    m = metrics(c)
                    if m[0] > 28: continue
                    kk = (m[1], m[2], m[3]); res[kk] = res.get(kk, 0) + 1
                    e = min(exc(m, g) for g in GOALS.values())
                    if e <= 4:
                        kt = core.to_kernel(c); h = hashlib.sha1(kt.encode()).hexdigest()[:12]
                        if h in seen: continue
                        seen.add(h)
                        ok, info = verify(c)
                        if not ok: continue
                        (out / 'cand' / ('%d-%d-%d-%d-%s.bfx' % (m + (h,)))).write_text(kt)
                        kept[h] = {'m': m, 'front': F.id, 'back': B.id, 'LX': LX, 'LY': LY, 'nint': nint}
    if k % 20 == 0:
        print('partners', k + 1, 'pairs', pairs, 'tried', tried, 'skipped', skipped, 'A28 results', sum(res.values()),
              'kept', len(kept), round(time.time() - t0), 's', flush=True)
summ = {'a28': len(A28), 'partners': len(OTH), 'pairs': pairs, 'tried': tried, 'skipped': skipped,
        'seconds': round(time.time() - t0, 1), 'kept': kept, 'tally': {'%d,%d,%d' % k: v for k, v in res.items()}}
for ad in sorted({k[0] for k in res}):
    pts = sorted({k[1:] for k in res if k[0] == ad})
    summ['front_ad%d' % ad] = [p for p in pts if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in pts)]
    print('AD', ad, 'A28 join front', summ['front_ad%d' % ad])
(out / 'summary.json').write_text(json.dumps(summ, indent=1))
print('done', pairs, 'pairs', tried, 'joins tried', len(kept), 'kept', round(time.time() - t0), 's')
