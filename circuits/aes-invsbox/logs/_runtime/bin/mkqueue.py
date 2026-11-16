#!/usr/bin/env python3
"""Write the conjugation job queue (queue.jsonl) and the hub seed list (seeds.list).

    XS_INVSBOX=1 PYTHONPATH=<camp>/shim python3 mkqueue.py --out DIR [--seconds 1800] [--rounds 10]

Starts: the Pareto front (A, AD, G, GD) of NIST's pinned inverse S-box circuits (metrics recomputed by
the independent verifier, aes_check.published() under invshim).  Rounds, each over all starts in
(A, AD, G, GD) order: conjugates by screen rank (3 per job), the start itself (staged pull, 'id') every
fourth round.  Stage GD caps from the start's GD d: loose first, then tighter.
"""
import argparse
import json
import sys
from pathlib import Path

import invshim
invshim.install()
import aes_check

ap = argparse.ArgumentParser()
ap.add_argument('--out', required=True)
ap.add_argument('--seconds', type=int, default=1800)
ap.add_argument('--rounds', type=int, default=10)
ap.add_argument('--scale', type=float, default=1.0, help='stage-length factor (smoke test)')
a = ap.parse_args()
out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

pub = sorted(aes_check.published())
files = {n: f for f in invshim.inverse_published_files() for n in [f.name]}
dom = lambda u, v: all(x <= y for x, y in zip(u, v)) and u != v
front = [(u, n) for u, n in pub if not any(dom(w, u) for w, _ in pub)]
(out / 'seeds.list').write_text(''.join(str(files[n]) + '\n' for u, n in pub))
(out / 'nist_front.json').write_text(json.dumps([{'tuple': list(u), 'file': n} for u, n in front], indent=1) + '\n')


def sched(d, conj):
    s = lambda x: max(30, int(x * a.scale))
    if conj:
        st = [('g', d + 6, 240), ('m', d + 3, 300), ('m', d + 1, 300), ('m', d, 360), ('m', d - 1, 360), ('m', d - 2, 360)]
    else:
        st = [('g', d + 4, 240), ('m', d + 2, 300), ('m', d, 360), ('m', d - 1, 400), ('m', d - 2, 400)]
    return ','.join('%s:%d:%d' % (m, max(3, D), s(t)) for m, D, t in st)


jobs = []
rank = 1
for r in range(a.rounds):
    ident = (r % 4 == 1)
    for u, n in front:
        if ident:
            conj = 'id'
        else:
            conj = ','.join('rank:%d' % q for q in range(rank, rank + 3))
        jobs.append({'i': len(jobs), 'round': r + 1, 'start': str(files[n]), 'start_tuple': list(u),
                     'conj': conj, 'schedule': sched(u[3], not ident), 'seconds': a.seconds,
                     'seed': 1000 + len(jobs)})
    if not ident:
        rank += 3
with open(out / 'queue.jsonl', 'w') as f:
    for j in jobs:
        f.write(json.dumps(j) + '\n')
print('published inverse circuits %d, NIST front %d, jobs %d -> %s' % (len(pub), len(front), len(jobs), out))
