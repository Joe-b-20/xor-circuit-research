#!/usr/bin/env python3
"""Seed list for a goal-focused hub directory: one circuit per (A, AD, G, GD) tuple of the source archive,
restricted to the classes the user's goals B-G (and the A <= 31 classes next to them) live in.

    python3 mk_focus_seeds.py [--src ARCHIVE_DIR] [--out SEED_LIST] [--per-cell N]

Kept tuples (A, AD, G, GD):
  A <= 32, AD <= 6                       goals B, C, D, E and every A29-A31 class (stepping stones)
  A <= 35, AD <= 3, GD >= 20             goal F window (the AD3 points at GD < 20 are not near any goal)
  A <= 48, AD <= 4, GD <= 13             goal G window
Per (A, AD, GD) cell the N lowest-G tuples are kept (default 3: the cell minimum plus near-front
alternatives as join partners / nursery material); for each tuple the earliest admitted circuit.
Read-only on the source archive.  Output: absolute .bfx paths, one per line (scheduler.py --seed-list).
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

HOME = Path.home()
ap = argparse.ArgumentParser()
ap.add_argument('--src', default=str(HOME / 'xs-campaigns/2026-11-14-hub/long/archive'))
ap.add_argument('--out', default=str(HOME / 'xs-campaigns/2026-11-15-study/L1/focus.seed.list'))
ap.add_argument('--per-cell', type=int, default=3)
args = ap.parse_args()


def keep(A, AD, G, GD):
    return (A <= 32 and AD <= 6) or (A <= 35 and AD <= 3 and GD >= 20) or (A <= 48 and AD <= 4 and GD <= 13)


src = Path(args.src)
first = {}
for f in src.glob('*.json'):
    if f.name == 'cells.json': continue
    r = json.loads(f.read_text())
    m = (r['A'], r['AD'], r['G'], r['GD'])
    if not keep(*m) or not (src / (r['id'] + '.bfx')).exists(): continue
    if m not in first or r['t_admit'] < first[m][0]: first[m] = (r['t_admit'], r['id'])
cells = defaultdict(list)
for m, (t, i) in first.items(): cells[(m[0], m[1], m[3])].append((m[2], i))
out = []
for k, l in sorted(cells.items()):
    for g, i in sorted(l)[:args.per_cell]: out.append(str(src / (i + '.bfx')))
Path(args.out).write_text('\n'.join(out) + '\n')
print('tuples in scope', len(first), 'cells', len(cells), 'seeds written', len(out), '->', args.out)
