#!/usr/bin/env python3
"""hub polish/pull jobs: when did the kernel last improve (t_last_improvement) vs the job's seconds;
how often did a polish of an A28 input lower G"""
import json, sys
from pathlib import Path
from collections import Counter
R = Path('/home/joebachir20/xs-campaigns/2026-11-14-hub/long/runs')
fr = []; a28 = Counter()
for f in R.glob('*.json'):
    try: r = json.loads(f.read_text())
    except Exception: continue
    if r.get('operator') not in ('polish', 'pull'): continue
    oi = r.get('op_info') or {}
    t = oi.get('t_last_improvement'); s = (r.get('settings') or {}).get('seconds')
    if t is not None and s: fr.append(t / s)
    tm = r.get('target_metrics')
    if tm and tm[0] == 28: a28[r['operator']] += 1
fr.sort()
n = len(fr)
print('jobs with t_last', n)
for q in (0.25, 0.5, 0.75, 0.9, 0.95):
    print('quantile', q, round(fr[int(q * (n - 1))], 3))
print('share last improvement after 50% of budget', sum(1 for x in fr if x > 0.5) / n)
print('A28-input jobs', dict(a28))
