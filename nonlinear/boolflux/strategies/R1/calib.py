#!/usr/bin/env python3
"""Calibration: windows on archive front circuits, one try_window per window, statistics per strategy/mode.

    calib.py ARCHIVE_CAMPAIGN NWIN SEED OUT.jsonl [--K 8] [--maxg 9] [--budget 30000] [--ids id,id]
"""
import argparse, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(next(p for p in HERE.parents if (p / 'boolflux' / 'core.py').exists()))); sys.path.insert(0, str(HERE))
from boolflux.hub.archive import Archive          # noqa: E402
from boolflux.hub.common import metrics           # noqa: E402
import wres as R                                   # noqa: E402
import op_wres as O                                # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('camp'); ap.add_argument('nwin', type=int); ap.add_argument('seed', type=int); ap.add_argument('out')
ap.add_argument('--K', type=int, default=8); ap.add_argument('--maxg', type=int, default=9)
ap.add_argument('--budget', type=int, default=30000); ap.add_argument('--ids')
ap.add_argument('--modes', default='cost,gd'); ap.add_argument('--strategies', default='and,pair,reconv,crit,x')
ap.add_argument('--wseconds', type=float, default=20); ap.add_argument('--no-odc', action='store_true')
a = ap.parse_args()
rng = random.Random(a.seed)
ar = Archive(a.camp)
ids = a.ids.split(',') if a.ids else ar.front_ids()
keys = O.DEFAULT_OBJECTIVE.split(',')
f = open(a.out, 'w')
agg = {}
for w in range(a.nwin):
    i = rng.choice(ids); c = ar.circuit(i); net = R.Net(c)
    mode = rng.choice(a.modes.split(',')); strat = rng.choice(a.strategies.split(','))
    D, DA = net.GD - (mode == 'gd'), net.AD - (mode == 'ad')
    t0 = time.time()
    W = R.pick_window(net, strat, rng, K=a.K, maxg=a.maxg)
    if not W:
        st, det = 'nowindow', {}
    else:
        st, nc, det = O.try_window(c, net, W, D, DA, keys, a.budget, rng, time.time() + a.wseconds, odc=not a.no_odc)
        if nc is not None: det['m_new'] = metrics(nc)
    det.update({'id': i, 'm': metrics(c), 'mode': mode, 'strategy': strat, 'status': st, 'dt_total': round(time.time() - t0, 3)})
    f.write(json.dumps(det) + '\n'); f.flush()
    v = agg.setdefault((strat, mode), {}); v[st] = v.get(st, 0) + 1
for k, v in sorted(agg.items()): print(k, v)
