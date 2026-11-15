#!/usr/bin/env python3
"""X2 retrospective: which operator moved circuits toward which goal in a finished hub campaign.

    python3 retro.py CAMPAIGN_DIR [--json OUT]

For every job (runs/*.json): CPU s; for every goal, the step from the job's target to each admitted candidate
(goals.step_gain of the keys, summed) and whether a candidate improved the archive's best key for that goal at
admission time (records walked in t_admit order, starting from the records admitted before the campaign's first
job).  Output per (goal, operator): jobs, CPU h, step reward per CPU h, best-key improvements, and per goal the
improvement events (time, op, tuple).  [H] descriptive, generic-scheduler data (targets were not chosen by goal)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import goals as GL     # noqa: E402

d = Path(sys.argv[1]); jout = sys.argv[sys.argv.index('--json') + 1] if '--json' in sys.argv else None
runs = []
for f in (d / 'runs').glob('*.json'):
    try:
        runs.append(json.loads(f.read_text()))
    except Exception:
        pass
recs = []
for f in (d / 'archive').glob('*.json'):
    if f.name == 'cells.json': continue
    try:
        recs.append(json.loads(f.read_text()))
    except Exception:
        pass
recs.sort(key=lambda r: r['t_admit'])
op_of_run = {r['run_id']: r['operator'] for r in runs}
best = {n: None for n in GL.NAMES}
imp = {n: [] for n in GL.NAMES}
first_job = None
for r in recs:
    m = (r['A'], r['AD'], r['G'], r['GD'])
    for g in GL.GOALS:
        k = GL.key(g, m)
        if best[g.name] is None or k < best[g.name]:
            if best[g.name] is not None and r.get('run_id'):
                imp[g.name].append({'t': r['t_admit'], 'op': r['operator'], 'm': m, 'from': best[g.name], 'to': k,
                                    'run_id': r.get('run_id')})
            elif best[g.name] is not None and r['operator'] == 'ingest':
                imp[g.name].append({'t': r['t_admit'], 'op': 'ingest', 'm': m, 'from': best[g.name], 'to': k})
            best[g.name] = k
tab = {}
for run in runs:
    op = run['operator']; cpu = float(run.get('cpu_s') or 0); tm = tuple(run['target_metrics'])
    for g in GL.GOALS:
        kt = GL.key(g, tm); rew = 0.0; moved = 0
        for o in run.get('outcome') or []:
            if o.get('status') != 'admitted': continue
            s = GL.step_gain(kt, GL.key(g, tuple(o['metrics'])))
            rew += s; moved += s > 0
        t = tab.setdefault((g.name, op), {'jobs': 0, 'cpu_s': 0.0, 'rew': 0.0, 'moved': 0, 'near_jobs': 0, 'near_cpu': 0.0, 'near_rew': 0.0})
        t['jobs'] += 1; t['cpu_s'] += cpu; t['rew'] += rew; t['moved'] += moved
        if GL.scalar(g, tm) <= 10 or GL.stepping(g, tm):      # jobs whose target was near this goal
            t['near_jobs'] += 1; t['near_cpu'] += cpu; t['near_rew'] += rew
nimp = {}
for n in GL.NAMES:
    for e in imp[n]: nimp[(n, e['op'])] = nimp.get((n, e['op']), 0) + 1
print('campaign %s: %d runs, %d records' % (d, len(runs), len(recs)))
print('goal op       jobs  CPU-h  step/CPU-h  near-jobs near-CPU-h near-step/CPU-h  best-improvements')
for n in GL.NAMES:
    for op in sorted({o for (g, o) in tab if g == n}):
        t = tab[(n, op)]
        print('%s    %-9s %5d %6.2f %9.2f %9d %9.2f %12.2f %6d' % (
            n, op, t['jobs'], t['cpu_s'] / 3600, t['rew'] / max(t['cpu_s'] / 3600, 1e-9), t['near_jobs'],
            t['near_cpu'] / 3600, t['near_rew'] / max(t['near_cpu'] / 3600, 1e-9), nimp.get((n, op), 0)))
print('\nbest-key improvement events per goal (time UTC, op, tuple, key from -> to):')
import time as _t
for n in GL.NAMES:
    print(n, GL.goal(n).note)
    for e in imp[n]:
        print('   %s %-9s %s %s -> %s' % (_t.strftime('%m-%d %H:%M', _t.gmtime(e['t'])), e['op'], e['m'], e['from'], e['to']))
if jout:
    Path(jout).write_text(json.dumps({'table': {'%s|%s' % k: v for k, v in tab.items()}, 'improvements': imp}, indent=1, default=str))
