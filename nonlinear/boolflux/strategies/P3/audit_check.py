#!/usr/bin/env python3
"""Audit of a replay (pdrive_replay.py): (1) is the replayed result gate-identical to the original
circuit? (2) max A and AD over every accepted kernel state in every traced kernel call.
    audit_check.py REPLAY_DIR ORIGINAL.circ.txt [CIRC_IN_REPLAY (default: best.circ.txt or a pareto file)]"""
import glob, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from boolflux import core  # noqa

d = Path(sys.argv[1]); orig = core.read_ncff(sys.argv[2])
cands = [Path(sys.argv[3])] if len(sys.argv) > 3 else [d / 'best.circ.txt'] + sorted((d / 'pareto').glob('*.circ.txt'))
same = [str(p) for p in cands if p.exists() and core.read_ncff(str(p)).gates == orig.gates and core.read_ncff(str(p)).outputs == orig.outputs]
print('gate-identical replay result:', same or 'NONE')
mA = mAD = 0; n = 0; worst = None
for f in sorted(glob.glob(str(d / 'traces' / '*.trace'))):
    for line in open(f):
        p = line.split()
        if len(p) < 8: continue
        a, ad = int(p[5]), int(p[7]); n += 1
        if a > mA or ad > mAD:
            mA, mAD = max(mA, a), max(mAD, ad)
        if (a > 32 or ad > 4) and worst is None: worst = (f, line.strip())
print('traced states', n, 'max A', mA, 'max AD', mAD, 'first violation', worst)
