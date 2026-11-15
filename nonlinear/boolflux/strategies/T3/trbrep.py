#!/usr/bin/env python3
"""T3: repeated trb rebuilds (hub/trb_impl.py) of the region-2 and bottom XOR logic, keep the best
(G, then GD) circuit; optional kernel polish after.
    trbrep.py FILE --cap D --reps 300 --seed 1 [--polish SECONDS --caps A,AD,GD --work DIR] [--out OUT.bfx]"""
import argparse
import random
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from boolflux import core                                      # noqa: E402
from boolflux.hub import trb_impl, ops as O                    # noqa: E402
from boolflux.hub.common import load, metrics, verify          # noqa: E402


def trb_best(c, cap, reps, rng, kinds=('mid', 'bottom', 'random', 'top')):
    best = c; bm = metrics(c)
    for r in range(reps):
        kind = rng.choice(kinds)
        try:
            nc, info = trb_impl.rebuild(best, cap, kind, rng)
        except Exception:
            continue
        m = metrics(nc)
        if m[3] <= cap and (m[2], m[3]) <= (bm[2], bm[3]) and nc is not best:
            best, bm = nc, m
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('files', nargs='+'); ap.add_argument('--cap', type=int, default=30)
    ap.add_argument('--reps', type=int, default=300); ap.add_argument('--seed', type=int, default=1)
    ap.add_argument('--polish', type=float, default=0); ap.add_argument('--caps', default='35,3,26')
    ap.add_argument('--work'); ap.add_argument('--outdir')
    a = ap.parse_args()
    rng = random.Random(a.seed)
    for f in a.files:
        c = load(f); m0 = metrics(c)
        b = trb_best(c, max(a.cap, m0[3]), a.reps, rng)
        line = '%s %s -> trb %s' % (Path(f).name, m0, metrics(b))
        if a.polish:
            A, AD, GD = (None if x == '-' else int(x) for x in a.caps.split(','))
            job = Path(a.work) / (Path(f).stem + '-t%d' % a.seed); job.mkdir(parents=True, exist_ok=True)
            cands, info = O._kernel(b, {'A': A, 'AD': AD, 'GD': GD}, 'cost,gd', a.seed, a.polish, job, a.work)
            if cands:
                b2 = cands[0]; ok, _ = verify(b2)
                line += ' -> polish %s %s' % (metrics(b2), 'ok' if ok else 'FAIL')
                b = b2
        if a.outdir:
            Path(a.outdir).mkdir(parents=True, exist_ok=True)
            (Path(a.outdir) / (Path(f).stem + '-trb.bfx')).write_text(core.to_kernel(b))
        print(line, flush=True)


if __name__ == '__main__':
    main()
