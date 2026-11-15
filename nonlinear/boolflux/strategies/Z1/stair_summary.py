#!/usr/bin/env python3
"""Summarise staircode.py output by (A, AND levels, E, K, d-hierarchy); add the Wei-dual hierarchy
d_perp (flats of the image arrangement in V/(T + free), dim K - 8).
usage: stair_summary.py JSONL"""
import sys, json
from collections import defaultdict

rows = [json.loads(l) for l in open(sys.argv[1]) if l.strip()]
bad = [r for r in rows if 'error' in r]
ok = [r for r in rows if 'error' not in r]
print('files', len(rows), 'errors', len(bad), 'identity m_k = E + d_k holds:',
      sum(1 for r in ok if r.get('identity_ok')), 'sink layer:', sum(1 for r in ok if r['sink']))
for r in bad:
    print('  ERR', r['file'], r['error'][:100])
grp = defaultdict(list)
for r in ok:
    key = (r['A'], tuple(r['and_levels']), r['E'], r['nL'], tuple(r['d']), r['sink'], r.get('identity_ok'))
    grp[key].append(r)


def dual(d, n):
    k = len(d)
    comp = sorted(set(range(1, n + 1)) - set(d))
    return sorted(n + 1 - x for x in comp)


print('%-4s %-18s %-3s %-3s %-28s %-22s %-5s %-5s %-5s %s' % ('A', 'levels', 'E', 'K', 'd_k (code)', 'd_perp (images)', 'waste', 'sink', 'id', 'count'))
for key in sorted(grp, key=lambda k: (k[0], k[1], k[4])):
    A, lv, E, K, d, sink, idok = key
    rs = grp[key]
    dp = dual(list(d), K) if len(d) == 8 and d[-1] == K else None
    print('%-4d %-18s %-3d %-3d %-28s %-22s %-5d %-5s %-5s %d' % (A, '-'.join(map(str, lv)), E, K, ','.join(map(str, d)),
          ','.join(map(str, dp)) if dp else '-', d[-1] - d[0] - 7, sink, idok, len(rs)))
