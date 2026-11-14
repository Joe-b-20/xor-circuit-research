#!/usr/bin/env python3
"""Summarise fdrive A/B jobs: per job start G, best G and time of each new best, stage counts,
osc repair success, trb kick sizes.   python3 abstat.py DIR [DIR ...]"""
import json
import sys
from pathlib import Path

rows = []
for d in sys.argv[1:]:
    for jd in sorted(Path(d).glob('*/log.jsonl')):
        recs = [json.loads(l) for l in jd.read_text().splitlines() if l.strip()]
        if not recs: continue
        st = recs[0]; name = jd.parent.name
        bests = [(r['t'], r['G'], r['GD']) for r in recs if r['kind'] == 'best']
        rep = [r for r in recs if r['kind'] == 'osc-repaired']
        rep_ok = sum(1 for r in rep if r['GD'] <= st['cap'])
        trb = [r for r in recs if r['kind'] == 'trb']
        kick = [r['G'] - r.get('G_before', r['G']) for r in trb if 'G_before' in r]
        end = [r for r in recs if r['kind'] == 'end']
        rows.append((name, st['G'], min([b[1] for b in bests if b[2] <= st['cap']] or [st['G']]),
                     ['%d@%.0fs' % (g, t) for t, g, gd in bests if gd <= st['cap']],
                     '%d/%d' % (rep_ok, len(rep)) if rep else '-',
                     ('%d kicks, mean +%.1f' % (len(kick), sum(kick) / len(kick))) if kick else '-',
                     'done' if end else 'running'))
print('| job | start G | best G | improvements (G@time) | osc repairs feasible | trb kicks | state |')
print('|---|---|---|---|---|---|---|')
for r in rows:
    print('| %s | %d | %d | %s | %s | %s | %s |' % (r[0], r[1], r[2], ' '.join(r[3]) or '-', r[4], r[5], r[6]))
