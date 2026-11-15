#!/usr/bin/env python3
"""digest of T1 worker job logs: per worker/op jobs, cpu, improvements, best excess; pool fronts"""
import json, sys
from pathlib import Path
from collections import defaultdict

D = Path(sys.argv[1])
GOALS = {'B': (28, 4, 130, 22), 'C': (28, 5, 127, 19)}
for f in sorted(D.glob('*.jobs.jsonl')):
    st = defaultdict(lambda: [0, 0.0, 0, 0]); last = None; errs = 0; best = {}
    for ln in f.read_text().splitlines():
        try: r = json.loads(ln)
        except Exception: continue
        if r.get('event') == 'status': last = r
        if 'op' not in r: continue
        s = st[r['op']]; s[0] += 1; s[1] += r['cpu']; s[2] += r['imp']
        if r.get('err'): errs += 1; s[3] += 1
        for m, res in r['outs']:
            if res: best[tuple(m)] = best.get(tuple(m), 0) + 1
    print('==', f.stem, 'errors', errs)
    for op, s in sorted(st.items()):
        print('  %-7s jobs %4d cpu %7.0f s imp %3d err %d' % (op, *s))
    if last: print('  pool', last['pool'], 'front', last['front'])
    pts = sorted(best)
    print('  admitted points (best 12 by G):', sorted(pts, key=lambda m: (m[2], m[3]))[:12])
sh = D / 'shared'
pts = defaultdict(int)
for j in sh.glob('*.json'):
    r = json.loads(j.read_text()); pts[tuple(r['m'])] += 1
for ad in (4, 5):
    P = sorted({m[2:] for m in pts if m[1] == ad})
    fr = [p for p in P if not any(q != p and q[0] <= p[0] and q[1] <= p[1] for q in P)]
    print('shared AD%d front' % ad, fr)
print('found:', sorted(p.name for p in (D / 'found').glob('*.bfx')))
