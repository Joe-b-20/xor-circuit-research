#!/usr/bin/env python3
"""Print a circuit's bottom decomposition (qflip coordinates) in readable form.  showdec.py REF FILE"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parents[2]))
import bottom as BT, flip as FL, qflip as QF  # noqa


def fs(f):
    t = []
    if f & 1: t.append('1')
    t += ['x%d' % (k - 1) for k in range(1, 9) if f >> k & 1]
    t += ['y%d' % (k - 9) for k in range(9, 13) if f >> k & 1]
    return '+'.join(t) or '0'


rc, Yt = FL.ref_basis(sys.argv[1])
c = BT.load(sys.argv[2])
free, fixed, lin = QF.decompose(c, Yt)
for L, R, w in sorted(free, key=lambda t: (-(t[0] >> 9 and t[0] & 0x1FF and 1 or 0), t)):
    print('%-28s * %-34s w=%s' % (fs(L), fs(R), format(w, '08b')[::-1]))
for L, R, w in fixed:
    if w: print('fixed %-22s * %-34s w=%s' % (fs(L), fs(R), format(w, '08b')[::-1]))
for o in range(8):
    if lin[o]: print('lin S%d: %s' % (o, fs(lin[o])))
