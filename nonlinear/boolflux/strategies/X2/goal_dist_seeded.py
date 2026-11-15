#!/usr/bin/env python3
"""X2: goal distance of seeded hub directories (baseline = the directory's own seed records).

    python3 goal_dist_seeded.py DIR [DIR ...]

Per directory: per goal A-G the best key / tuple of the seeds and of the whole archive, the improvement events
(time, operator, tuple), new stepping-stone tuples, goal-meeting records; CPU-h from runs/*.json.  Use the same
seed list for every directory compared (L1's overnight seed.list)."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import goals as GL     # noqa: E402

for d in map(Path, sys.argv[1:]):
    recs = []
    for f in (d / 'archive').glob('*.json'):
        if f.name == 'cells.json': continue
        try:
            recs.append(json.loads(f.read_text()))
        except Exception:
            pass
    recs.sort(key=lambda r: r['t_admit'])
    tup = lambda r: (r['A'], r['AD'], r['G'], r['GD'])
    seeds = [r for r in recs if r['operator'] in ('seed', 'ingest')]
    made = [r for r in recs if r['operator'] not in ('seed', 'ingest')]
    s0 = GL.state([tup(r) for r in seeds]); s1 = GL.state([tup(r) for r in recs])
    cpu = 0.0; jobs = 0
    for f in (d / 'runs').glob('*.json'):
        try:
            cpu += float(json.loads(f.read_text()).get('cpu_s') or 0); jobs += 1
        except Exception:
            pass
    print('%s: %d seeds, %d hub-made records, %d jobs, %.2f CPU-h; state better than seeds: %s' % (
        d, len(seeds), len(made), jobs, cpu / 3600, GL.state_key(s1) < GL.state_key(s0)))
    seedt = {tup(r) for r in seeds}
    for n in GL.NAMES:
        g = GL.goal(n); cur = s0[n]['key']; ev = []
        for r in made:
            k = GL.key(g, tup(r))
            if cur is None or k < cur:
                cur = k; ev.append('%s %s %s %s' % (time.strftime('%H:%M', time.gmtime(r['t_admit'])), r['operator'], tup(r), k))
        stones = len({tup(r) for r in made if GL.stepping(g, tup(r))} - seedt)
        print('  %s %-28s seeds %s %s -> %s %s | new stone tuples %d | %s' % (
            n, g.note, s0[n]['m'], s0[n]['key'], s1[n]['m'], s1[n]['key'], stones, '; '.join(ev) or 'no improvement'))
    met = sorted({(n, tup(r), r['id']) for r in made for n in GL.met_goals(tup(r))})
    print('  goal-meeting hub-made records: %s' % (met or 'none'))
