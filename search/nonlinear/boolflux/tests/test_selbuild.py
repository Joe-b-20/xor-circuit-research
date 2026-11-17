"""Tests for ops/selbuild.py (aes-sbox-sel from one S-box or inverse S-box circuit) and the aes-sbox-sel target.

    python3 -m unittest discover -s search/nonlinear/boolflux/tests -t search/nonlinear -p 'test_selbuild.py'
"""
import json
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
sys.path.insert(0, str(PKG.parent))
sys.path.insert(0, str(PKG / 'ops'))

from boolflux import core, targets      # noqa: E402
import selbuild as SB                    # noqa: E402

SEEDS = PKG.parent / 'seeds'
FWD = SEEDS / 'aes-sbox' / 'aes-sbox-a32-ad4-g117-gd19-xx85-6.circ.txt'
INV = SEEDS / 'aes-invsbox' / 'aes-invsbox-a32-ad4-g117-gd21-xx85-10.circ.txt'


class TestSel(unittest.TestCase):
    def test_target_is_nist_table(self):
        n, m, t, _ = targets.load('aes-sbox-sel')
        fj = json.loads((SEEDS / 'aes-sbox-sel' / 'aes-sbox-sel.fn.json').read_text())
        self.assertEqual((n, m), (fj['n_inputs'], fj['n_outputs']))
        self.assertEqual(t, fj['table'])
        self.assertEqual(SB.sel_table(), t)

    def test_min_mux_rank(self):
        for src, best in (('aes-sbox', {(31, 0), (95, 0), (174, 0)}), ('aes-invsbox', {(23, 0), (178, 0), (210, 0)})):
            r = {(l, k): sum(SB.Plan(src, l, k).r) for l in range(1, 256) for k in range(8)}
            self.assertEqual(min(r.values()), 8)
            self.assertEqual({lk for lk, v in r.items() if v == 8}, best)

    def test_builds(self):
        want = SB.sel_table()
        for path, lk in ((FWD, (31, 0)), (INV, (23, 0))):
            F = core.read_ncff(str(path)); A0 = F.metrics()['A']; AD0 = F.metrics()['AD']
            P = SB.Plan('aes-sbox' if path is FWD else 'aes-invsbox', *lk)
            bi = next(SB.bases(P.Din)); bo = next(SB.bases(P.Dout))
            for top, bottom in (('bp', 'wrap'), ('wrap', 'wrap'), ('flat', 'flat'), ('xdelta', 'leafg')):
                c = SB.build(F, P, bi, bo, random.Random(1), 1, top, bottom)
                m = c.metrics()
                self.assertEqual(list(c.value_table()), want, (path.name, top, bottom))
                self.assertEqual((m['A'], m['AD']), (A0 + 8, AD0 + 2), (path.name, top, bottom))


if __name__ == '__main__':
    unittest.main()
