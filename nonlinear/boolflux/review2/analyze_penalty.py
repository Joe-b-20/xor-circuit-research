"""Summarise ~/xs-campaigns/2026-11-13-boolflux/bench/rebuild_penalty.json against MECHANICS.md s.5.
    python3 analyze_penalty.py
"""
import json
from collections import defaultdict
from pathlib import Path

rows = json.loads((Path.home() / 'xs-campaigns/2026-11-13-boolflux/bench/rebuild_penalty.json').read_text())
print(len(rows), 'rows')
by = defaultdict(list)
for r in rows: by[(r['start'], r['skel_iters'])].append(r)
print('start | iters | accepted moves | K | ands_kept | unseeded-G0 | seeded-G0')
for (s, it), rs in sorted(by.items()):
    print('%s | %d | %s | %s | %s | %s | %s' % (s[9:30], it, [r['accepted_moves'] for r in rs], [r['K'] for r in rs],
          [r['ands_kept'] for r in rs], [r['G_unseeded'] - r['G0'] for r in rs], [r['G_seeded'] - r['G0'] for r in rs]))
z = [r for r in rows if r['skel_iters'] == 0]
print('iters 0: unseeded penalty', sorted({(r['G0'], r['G_unseeded']) for r in z}), 'seeded penalty', sorted({r['G_seeded'] - r['G0'] for r in z}))
one = [r for r in rows if r['accepted_moves'] == 1]
print('exactly 1 accepted move: seeded penalty', sorted(r['G_seeded'] - r['G0'] for r in one), 'n', len(one))
mid = [r for r in rows if 25 <= r['accepted_moves'] <= 90]
print('25-90 accepted moves: seeded penalty', sorted(r['G_seeded'] - r['G0'] for r in mid), 'n', len(mid))
print('accepted move counts', sorted({r['accepted_moves'] for r in rows}))
print('K changed (K != K at iters 0):', sum(1 for r in rows if r['K'] != by[(r['start'], 0)][0]['K']), 'of', len(rows))
print('seeded > unseeded:', sum(1 for r in rows if r['G_seeded'] > r['G_unseeded']))
