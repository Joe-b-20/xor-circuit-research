#!/usr/bin/env python3
"""X2: one line per finished job of a campaign dir (goal, op, target, caps, cpu, admitted, reward)."""
import json
import sys
from pathlib import Path

d = Path(sys.argv[1])
for f in sorted((d / 'runs').glob('*.json')):
    r = json.loads(f.read_text())
    print(r['run_id'], r.get('goal', '-'), r['target_metrics'], r.get('goal_caps'), 'rc', r['returncode'],
          'cpu', r['cpu_s'], 'cand', r['candidates'], 'adm', r['admitted'], 'gain', round(r['gain'], 3),
          'rew', r.get('goal_reward'), 'prog', r.get('goal_progress') or '')
for ln in (d / 'events.jsonl').read_text().splitlines():
    e = json.loads(ln)
    if e['ev'] in ('finish-error', 'goal-run-error', 'GOAL-MET', 'goal-progress', 'control-error', 'goal-control-error'):
        print('EVENT', ln[:400])
