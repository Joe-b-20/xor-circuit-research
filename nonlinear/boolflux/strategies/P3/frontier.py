#!/usr/bin/env python3
"""Collect the (G, GD) Pareto set of all circuits in certified P3 runs (runs whose command.txt uses
the repair_keep kernel P3/bin/bfx-4dc199db and whose start is certified) plus found/, and print the
run files of frontier points not yet in found/ (to be recorded with record.py --keep-other).
    frontier.py [--record]"""
import json, subprocess, sys
from pathlib import Path
from boolflux_path import *  # noqa  (sets sys.path)
from boolflux import core  # noqa

P3 = Path.home() / 'xs-campaigns/2026-11-15-targets/P3'
MODEL = core.Model.load('nist')
pts = {}
def add(p, src, cert):
    c = core.read_ncff(str(p)); m = c.metrics(MODEL)
    if m['A'] > 32 or m['AD'] > 4: return
    k = (m['G'], m['GD'])
    if k not in pts or (cert and not pts[k][2]): pts[k] = (p, src, cert)
for j in sorted((P3 / 'found').glob('*.json')):
    d = json.loads(j.read_text())
    add(j.with_suffix('').with_suffix('.circ.txt'), 'found', d.get('path_certified') is True)
for run in sorted((P3 / 'runs').glob('rk*')):
    cmd = run / 'command.txt'
    if not cmd.exists() or 'bfx-4dc199db' not in cmd.read_text(): continue
    for p in sorted((run / 'pareto').glob('*.circ.txt')):
        add(p, run.name, True)
front = []
for k, v in sorted(pts.items()):
    if v[2] and not any(g <= k[0] and d <= k[1] and (g, d) != k and pts[(g, d)][2] for g, d in pts):
        front.append((k, v))
for (G, GD), (p, src, cert) in front:
    print(G, GD, src, p)
if '--record' in sys.argv:
    for (G, GD), (p, src, cert) in front:
        if src == 'found': continue
        run = p.parent.parent
        cmdtxt = (run / 'command.txt').read_text().strip()
        start = cmdtxt.split('--start ')[1].split()[0]
        r = subprocess.run([sys.executable, str(Path(__file__).parent / 'record.py'), '--keep-other', '--circ', str(p),
                            '--start', start, '--tag', run.name, '--method',
                            'pdrive mode from command.txt, repair_keep 1, kernel bfx-4dc199db (run Pareto set, frontier pass)',
                            '--command', cmdtxt, '--seed', cmdtxt.split('--seed ')[1].split()[0],
                            '--kernel', str(P3 / 'bin/bfx-4dc199db'), '--path-certified', 'true'],
                           capture_output=True, text=True)
        print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-300:])
