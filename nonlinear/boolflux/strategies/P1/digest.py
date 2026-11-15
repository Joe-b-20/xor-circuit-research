#!/usr/bin/env python3
"""Summarise P1 worker logs: per operator jobs / CPU / best output (G, GD) at the target caps; FRONT events.

    python3 digest.py DATA/runs/w10.jobs.jsonl [...]
"""
import json
import sys
from collections import defaultdict

for f in sys.argv[1:]:
    st = defaultdict(lambda: [0, 0.0, None, defaultdict(int)])
    fronts = []; tgt = None; last = None
    for ln in open(f):
        try: r = json.loads(ln)
        except Exception: continue
        if r.get('event') == 'start':
            a = r['argv']; tgt = a[a.index('--target') + 1]
        if r.get('event') == 'FRONT': fronts.append((r['m'], r['class'], r['file'].split('/')[-1]))
        if 'job' in r and 'op' in r:
            s = st[r['op']]; s[0] += 1; s[1] += r['cpu']; last = r['t']
            for m, adm in r['outs']:
                k = (m[2], m[3], m[1])
                if s[2] is None or k < s[2]: s[2] = k
                s[3][tuple(m)] += 1
    print('==', f, 'target', tgt)
    for op, (n, cpu, best, hist) in sorted(st.items()):
        top = sorted(hist.items(), key=lambda kv: (kv[0][2], kv[0][3]))[:6]
        print('  %-7s jobs %3d cpu %6.0f s  best (G,GD,AD) %s  lowest outs %s' % (op, n, cpu, best,
              ' '.join('%d/%d/%d x%d' % (m[1], m[2], m[3], c) for m, c in top)))
    for fr in fronts: print('  FRONT', fr)
