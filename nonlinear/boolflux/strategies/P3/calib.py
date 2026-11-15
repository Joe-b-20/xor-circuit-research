#!/usr/bin/env python3
"""Calibration of build.py: decompose a circuit's bottom (qflip.decompose) and rebuild it on its own front.
    calib.py REF FILE [seeds]"""
import random, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF, build as BD  # noqa

ref, f = sys.argv[1], sys.argv[2]
seeds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
rc, Yt = FL.ref_basis(ref)
c = BT.load(f)
free, fixed, lin = QF.decompose(c, Yt)
print('rank', len(free), 'fixed w', [w for _, _, w in fixed], 'lin', lin)
for s in range(seeds):
    cc = BD.build(c, Yt, free, fixed, lin, random.Random(s))
    m = cc.metrics(BD.MODEL)
    print('seed', s, 'ok', cc.value_table() == BD.AES, m['A'], m['AD'], m['G'], m['GD'])
