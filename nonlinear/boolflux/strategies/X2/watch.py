#!/usr/bin/env python3
"""X2 watcher: every 60 s, print one line per new archive record in the A/B arm dirs that meets a goal or improves
a goal's best key over the snapshot, and per finish-error / goal-run-error event.  Runs until killed."""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux.hub import goals as GL     # noqa: E402

X2 = Path('/home/joebachir20/xs-campaigns/2026-11-15-study/X2')
snap = {f.name for f in (X2 / 'snap0' / 'archive').glob('*.json')}
base = {}
for f in (X2 / 'snap0' / 'archive').glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text()); m = (r['A'], r['AD'], r['G'], r['GD'])
    for g in GL.GOALS:
        k = GL.key(g, m)
        if g.name not in base or k < base[g.name]: base[g.name] = k
seen = set(); evpos = {}
while True:
    for arm in sorted(X2.glob('*/archive')):
        a = arm.parent.name
        if a in ('snap0',) or a.startswith('smoke'): continue
        best = dict(base)
        for f in arm.glob('*.json'):
            if f.name == 'cells.json' or f.name in snap or (a, f.name) in seen: continue
            seen.add((a, f.name))
            try:
                r = json.loads(f.read_text())
            except Exception:
                seen.discard((a, f.name)); continue
            m = (r['A'], r['AD'], r['G'], r['GD'])
            met = GL.met_goals(m)
            if met: print('GOAL-MET arm %s goals %s m %s id %s op %s' % (a, met, m, r['id'], r['operator']), flush=True)
            for g in GL.GOALS:
                if GL.key(g, m) < base[g.name]:
                    print('closer arm %s goal %s m %s key %s (snapshot %s) op %s' % (a, g.name, m, GL.key(g, m), base[g.name], r['operator']), flush=True)
        ev = arm.parent / 'events.jsonl'
        if ev.exists():
            with open(ev) as fh:
                fh.seek(evpos.get(a, 0))
                for ln in fh:
                    if '"finish-error"' in ln or '"goal-run-error"' in ln or 'Traceback' in ln:
                        print('ERROR arm %s %s' % (a, ln[:300]), flush=True)
                evpos[a] = fh.tell()
        hl = arm.parent / 'hub.log'
        if hl.exists() and 'Traceback' in hl.read_text()[-5000:] and (a, 'tb') not in seen:
            seen.add((a, 'tb')); print('TRACEBACK in %s/hub.log' % a, flush=True)
    time.sleep(60)
