"""Validation designs: plain tower inversion over various bases.
  naive: x^-1 = x^16 * (N^4 * (N^5)^2)  (9 + 9 + 18 = 36)
  kinv5: x^-1 = x^16 * kinv5(N)         (9 + 5 + 18 = 32, BP structure)
"""
import itertools
import sys

import blocks
from h4lib import Circ, Tower, norm, finv, smul, check_inverse, save

out = sys.argv[1] if len(sys.argv) > 1 else '/tmp/h4'
res = []
for kinds in itertools.product(('normal', 'poly'), repeat=3):
    T = Tower(kinds)
    for mode in ('naive', 'kinv5'):
        C = Circ()
        if mode == 'naive':
            y = finv(C, T, C.x, 3)
        else:
            y = finv(C, T, C.x, 3, kinv=blocks.kinv_plug)
        ok = check_inverse(C, y)
        res.append((kinds, mode, C.ands, ok))
        print(kinds, mode, 'ANDs', C.ands, 'ok', ok, flush=True)
        if kinds == ('normal',) * 3:
            m = save(C, y, '%s-tower-%s.circ.txt' % (out, mode), ['H4 tower %s %s' % (kinds, mode)])
            print(m)
