#!/usr/bin/env python3
"""recent T1 jobs since a UTC time (HH:MM), per worker: op, parent tuple -> output tuples; plus v3 op stats"""
import json, sys, time, calendar
from pathlib import Path
from collections import defaultdict
D = Path(sys.argv[1]); hhmm = sys.argv[2]
day = time.strftime('%Y-%m-%d', time.gmtime())
t0 = calendar.timegm(time.strptime(day + ' ' + hhmm, '%Y-%m-%d %H:%M'))
for f in sorted(D.glob('*.jobs.jsonl')):
    st = defaultdict(lambda: [0, 0.0, 0]); lines = []
    for ln in f.read_text().splitlines():
        r = json.loads(ln)
        if 'op' not in r or r['t'] < t0: continue
        s = st[r['op']]; s[0] += 1; s[1] += r['cpu']; s[2] += r['imp']
        lines.append('%s %s/%s/%s/%s -> %s' % (r['op'], *r['pm'], ' '.join('%d/%d/%d/%d%s' % (*m, '*' if res else '') for m, res in r['outs'])))
    print('==', f.stem, {k: [v[0], round(v[1]), v[2]] for k, v in st.items()})
    for l in lines[-int(sys.argv[3]) if len(sys.argv) > 3 else -8:]: print('  ', l)
