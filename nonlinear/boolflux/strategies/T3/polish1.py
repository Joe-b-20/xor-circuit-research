#!/usr/bin/env python3
"""T3: one kernel polish of each FILE (hub.ops._kernel), print metrics.
    polish1.py --caps 35,3,26 --objective cost,gd --seconds 120 --seed 1 --work DIR FILE [FILE ...]"""
import argparse
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                      # noqa: E402
from boolflux.hub import ops as O                              # noqa: E402
from boolflux.hub.common import load, metrics, verify          # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument('files', nargs='+'); ap.add_argument('--caps', default='35,3,26')
ap.add_argument('--objective', default='cost,gd'); ap.add_argument('--seconds', type=float, default=120)
ap.add_argument('--seed', type=int, default=1); ap.add_argument('--work', required=True)
a = ap.parse_args()
A, AD, GD = (None if x == '-' else int(x) for x in a.caps.split(','))
for f in a.files:
    c = load(f)
    job = Path(a.work) / (Path(f).stem + '-s%d' % a.seed); job.mkdir(parents=True, exist_ok=True)
    cands, info = O._kernel(c, {'A': A, 'AD': AD, 'GD': GD}, a.objective, a.seed, a.seconds, job, a.work)
    if cands:
        m = metrics(cands[0]); ok, _ = verify(cands[0])
        (job / 'result.bfx').write_text(core.to_kernel(cands[0]))
        print(Path(f).name, metrics(c), '->', m, 'ok' if ok else 'FAIL', 't_last', info.get('t_last_improvement'), flush=True)
    else:
        print(Path(f).name, metrics(c), '-> no result', flush=True)
