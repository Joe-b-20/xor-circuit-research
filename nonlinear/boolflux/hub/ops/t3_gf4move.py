#!/usr/bin/env python3
"""T3 hub operator gf4move (common hub CLI, see hub/ops.py):

    python3 hub/ops/t3_gf4move.py --archive DIR --in ID --seed S --seconds T --out JOBDIR [--caps A,AD,GD]

For an AND-depth-3 input of the published family (level 3 = 12 products Tr(w x^170) Tr(c x^84), c in
the 3 GF(4)-scalings of 4 GF(4)-points; strategies/T3/NOTES.md 1), replace one GF(4)-point (p 0.7) or
take a random admissible 4-point choice (p 0.3), rebuild the R operands (region 2 kept, new R's added
greedily, dead gates removed) and the output layer (Paar), then polish with the gate kernel for the
remaining time under the caps (default: the input's A and AD, its GD + 2). Inputs without that
structure return no candidates. Every candidate is checked on all 256 inputs here; the hub admits.
Measured (T3 NOTES 6-7, 1 seed each): one-point changes of NIST 139@27 polish to 140@29-30 in 90 s
(the rebuilt published choice: 140@27); new-choice circuits 140@26, 142@22 after chains.
"""
from __future__ import annotations

import random
import sys
import time
from pathlib import Path

OPS_DIR = Path(__file__).resolve().parent
HUBDIR = OPS_DIR.parent
sys.path.insert(0, str(HUBDIR.parents[1]))
sys.path.insert(0, str(HUBDIR.parent / 'strategies' / 'T3'))

from boolflux.hub import ops as HO                       # noqa: E402
from boolflux.hub.common import metrics, sbox, _gmul      # noqa: E402


def op_gf4move(ar, args, rng, out):
    from gf4build import build
    from nbscan import current_points
    from pairs import Basis
    t0 = time.time()
    c = ar.circuit(args.inp); A, AD, G, GD = metrics(c)
    if AD != 3:
        return [], {'skip': 'AD != 3'}
    try:
        pts0 = current_points(c)
    except Exception as e:
        return [], {'skip': 'no GF(4) level-3 structure: %s' % str(e)[:60]}
    nc = None; tried = 0; kind = 'local-best'; pts = None
    if rng.random() < 0.7:
        # targeted one-point move: build every replacement of one index, pick among the 6 cheapest real changes
        i = rng.randrange(4); opts = []
        for p in range(1, 256):
            q = list(pts0); q[i] = p
            B = Basis([])
            if not all(B.add(_gmul(s, x)) for x in q for s in (1, 188)): continue
            try:
                tc = build(c, q, keep2=True)
            except Exception:
                continue
            opts.append((metrics(tc)[2], metrics(tc)[3], q, tc))
        opts.sort(key=lambda o: (o[0], o[1]))
        real = [o for o in opts if opts and o[0] > opts[0][0]]
        if real:
            o = rng.choice(real[:6]); pts, nc = o[2], o[3]; tried = len(opts)
    while nc is None and tried < 200:
        tried += 1
        if rng.random() < 0.7:
            pts = list(pts0); pts[rng.randrange(4)] = rng.randrange(1, 256); kind = 'local'
        else:
            pts = [rng.randrange(1, 256) for _ in range(4)]; kind = 'global'
        B = Basis([])
        if not all(B.add(_gmul(s, q)) for q in pts for s in (1, 188)): continue
        try:
            nc = build(c, pts, keep2=rng.random() < 0.8)
        except Exception:
            nc = None
    if nc is None:
        return [], {'tried': tried}
    built = metrics(nc)
    caps = dict(args.caps or {'A': A, 'AD': AD, 'GD': GD + 2})
    cands, info = HO._kernel(nc, caps, args.objective, args.seed, max(5.0, args.seconds - (time.time() - t0) - 1), out, args.archive)
    cands = [x for x in cands if tuple(x.value_table()) == sbox()]
    return cands, {'points': pts, 'kind': kind, 'built': built, 'caps': caps, 'tries': tried,
                   't_last_improvement': info.get('t_last_improvement')}


HO.OPS.update({'gf4move': op_gf4move})

if __name__ == '__main__':
    sys.exit(HO.main('gf4move'))
