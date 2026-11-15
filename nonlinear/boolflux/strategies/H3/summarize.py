#!/usr/bin/env python3
"""Summary table of H3 jsonl logs: per (file, source, ops, window size) counts of results and time."""
import collections
import json
import sys

for f in sys.argv[1:]:
    rows = [json.loads(l) for l in open(f) if l.strip()]
    c = collections.OrderedDict()
    for r in rows:
        res = r.get('result', '?')
        kind = res.split(' ')[0]
        key = (r.get('src', '?')[9:30], r.get('ops', '-'), r.get('k'))
        d = c.setdefault(key, collections.Counter())
        d[kind] += 1; d['_t'] += r.get('time', 0) or 0
    print('==', f, len(rows), 'windows')
    for (src, ops, k), d in c.items():
        t = d.pop('_t')
        print('  %-22s ops=%-8s |U|=%-3s %s  (%.0f s)' % (src, ops, k, dict(d), t))
    for r in rows:
        if not str(r.get('result', '')).startswith(('UNSAT', 'SKIP')):
            print('  !!', r.get('src'), r.get('win', r.get('W')), r.get('result'), r.get('file', ''))
