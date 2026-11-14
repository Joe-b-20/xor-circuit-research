#!/usr/bin/env python3
"""Plan for the track-F A/B: modes on equal CPU time from the same start.
    python3 plan_ab.py START CAP ROUNDS SECONDS OUT.json
Arms: gate-old (kernel snapshot 7c53f2e4), gate-new (kernel 0659eb9, lex cost,gd), osc, trb, mix
(osc/trb/mix use the old kernel).  Round r uses seed r for every arm."""
import json
import sys
from pathlib import Path

start, cap, rounds, secs, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), float(sys.argv[4]), sys.argv[5]
NEW = str(Path.home() / 'xs-campaigns/2026-11-13-aes/F/snap-new/boolflux/kernel/bfx')
arms = [('gate-old', 'gate', {}, ['--stage-iters', '200000']),
        ('gate-new', 'gate', {'F_BFX': NEW, 'F_LEX': 'cost,gd'}, ['--stage-iters', '200000']),
        ('osc', 'osc', {}, ['--stage-iters', '200000', '--repair-iters', '200000']),
        ('trb', 'trb', {}, ['--stage-iters', '200000']),
        ('mix', 'mix', {}, ['--stage-iters', '200000', '--repair-iters', '200000'])]
jobs = []
for r in range(1, rounds + 1):
    for name, mode, env, args in arms:
        jobs.append({'name': 'r%d-%s' % (r, name), 'start': start, 'cap': cap, 'mode': mode,
                     'seconds': secs, 'seed': r, 'env': env, 'args': args})
Path(out).write_text(json.dumps({'jobs': jobs}, indent=1) + '\n')
print(len(jobs), 'jobs')
