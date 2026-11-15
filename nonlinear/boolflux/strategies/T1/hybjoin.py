#!/usr/bin/env python3
"""Hybrid joins: every circuit in the given dirs (new-AND-space circuits: found/newspace, h2pol pools) x every
A28 hub archive circuit (G <= 145), both roles, all cut levels (hub join.join_all).  A28 results are kept per
(role, AD, G, GD) up to 3 distinct structures, verified, and written to OUTDIR/ (name role-A-AD-G-GD-id.bfx);
summary lines per input circuit in OUTDIR/hybjoin.jsonl.

    python3 hybjoin.py OUTDIR DIR...
"""
import hashlib, json, sys, time
from pathlib import Path
PKG = Path('/home/joebachir20/xcr-boolflux/nonlinear/boolflux')
sys.path.insert(0, str(PKG.parent))
from boolflux.hub import join as J                       # noqa: E402
from boolflux.hub.common import core, metrics, verify    # noqa: E402
HUBAR = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/archive')
out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
log = open(out / 'hybjoin.jsonl', 'a')
A28 = {}
for f in HUBAR.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text())
    if r['A'] == 28 and r['G'] <= 145:
        A28[r['id']] = J.Prepared(core.from_kernel((HUBAR / (r['id'] + '.bfx')).read_text(), r['id']), r['id'])
ins = []
for d in sys.argv[2:]:
    for p in Path(d).glob('*.bfx'):
        c = core.from_kernel(p.read_text(), p.stem)
        m = metrics(c)
        if m[0] == 28 and m[2] <= 175: ins.append((p, c, m))
print('inputs', len(ins), 'partners', len(A28), flush=True)
kept = {}
for p, c, m in ins:
    X = J.Prepared(c, p.stem); t0 = time.time(); n = 0; best = {}
    for P in A28.values():
        for F, B, role in ((X, P, 'nsfront'), (P, X, 'nsback')):
            for jc, LX, LY, nint in J.join_all(F, B):
                n += 1; mj = metrics(jc)
                if mj[0] > 28: continue
                key = (role,) + mj
                if key not in best or mj[2] < best[key]: best[key] = mj[2]
                if len(kept.setdefault(key, [])) >= 3: continue
                h = hashlib.sha1(core.to_kernel(jc).encode()).hexdigest()[:12]
                if h in kept[key]: continue
                if not verify(jc)[0]: continue
                kept[key].append(h)
                (out / ('%s-%d-%d-%d-%d-%s.bfx' % (key + (h,)))).write_text(core.to_kernel(jc))
    fr = {}
    for k in best:
        fr.setdefault(k[0], set()).add(k[1:])
    fr = {r: sorted(q for q in v if not any(o != q and all(a <= b for a, b in zip(o, q)) for o in v)) for r, v in fr.items()}
    log.write(json.dumps({'input': str(p), 'm': m, 'joins': n, 'secs': round(time.time() - t0), 'front': fr}) + '\n'); log.flush()
    print(p.name, m, n, 'joins', fr, flush=True)
