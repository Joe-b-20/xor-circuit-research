"""Gate-cost pricing and any-level re-basing (ops/rebase_lib/gprice.py, idea 06).

    python3 -m unittest boolflux.tests.test_gprice      (from search/nonlinear/)

The identity basis reproduces the parent (skeleton, price = G, gbuild = the parent's tuple); the generic
skeleton bound equals gbasis's Kraft test on top classes; every gbuild and patch build verifies on all 256
inputs (forward and inverse); patch builds keep A; classes below the top level exist on AD4/AD5 circuits.
"""
import random
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
PKG = HERE.parent
REPO = PKG.parents[2]
OPS = PKG / 'ops'
sys.path.insert(0, str(PKG.parent)); sys.path.insert(0, str(OPS)); sys.path.insert(0, str(OPS / 'rebase_lib'))

from boolflux import aesfn                              # noqa: E402
from boolflux.hub.common import verify, metrics, load    # noqa: E402

FWD = REPO / 'circuits' / 'aes-sbox'
INV = REPO / 'circuits' / 'aes-invsbox'
F32 = FWD / 'aes-sbox-a32-ad4-g117-gd17-xx85-35.circ.txt'
F28 = FWD / 'aes-sbox-a28-ad5-g133-gd18-xx105-51.circ.txt'
F35 = FWD / 'aes-sbox-a35-ad3-g155-gd15-xx120-56.circ.txt'
I32 = INV / 'aes-invsbox-a32-ad5-g109-gd20-xx77-28.circ.txt'


class TestGprice(unittest.TestCase):
    def setUp(self):
        import gprice
        self.GP = gprice

    def tearDown(self):
        aesfn.use('aes-sbox')

    def _id(self, path, func):
        aesfn.use(func)
        c = load(path); m = metrics(c); P = self.GP.Parent(c)
        for deep in (False, True):
            cls = self.GP.find_classes(P, deep=deep)
            st = self.GP.skeleton_of(P, cls, self.GP.identity(cls))
            self.assertEqual(st['removed'], set()); self.assertEqual(st['changed'], set())
            self.assertEqual(self.GP.price(P, st)[0], m[2])
            nc, _ = self.GP.gbuild(P, st, m[3])
            self.assertTrue(verify(nc)[0]); self.assertEqual(metrics(nc), m)
        return c, m, P

    def test_identity_forward_inverse(self):
        self._id(F32, 'aes-sbox')
        self._id(I32, 'aes-invsbox')

    def test_bound_matches_gbasis_on_top_classes(self):
        import gbasis as GB
        c, m, P = self._id(F35, 'aes-sbox')
        for cap in (m[3], m[3] - 1):
            res = GB.analyse(c, cap)
            cls = self.GP.gb_classes(res)
            for cb in GB.feasible_combos(res, maxn=20, rng=random.Random(1))[:20]:
                st = self.GP.skeleton_of(P, cls, cb)
                self.assertLessEqual(st['bound'], cap)

    def test_priced_builds_verify(self):
        c, m, P = self._id(F32, 'aes-sbox')
        cls = self.GP.find_classes(P, deep=True)
        self.assertTrue(any(not pc['top'] for pc in cls))          # classes below the top AND level
        rc = self.GP.ranked_combos(P, cls, m[3], random.Random(1), pool=12)
        self.assertTrue(rc)
        self.assertEqual([x[0] for x in rc], sorted(x[0] for x in rc))
        for pr, bd, cb, st in rc[:6]:
            nc, _ = self.GP.gbuild(P, st, m[3])
            self.assertTrue(verify(nc)[0])
            mm = metrics(nc); self.assertEqual(mm[0], m[0]); self.assertLessEqual(mm[3], m[3])

    def test_patch_builds_verify(self):
        for path, func in ((F28, 'aes-sbox'), (I32, 'aes-invsbox')):
            aesfn.use(func)
            c = load(path); m = metrics(c)
            vs, cls = self.GP.patch_variants(c, deep=True, max_single=4, max_pairs=4, rng=random.Random(2))
            self.assertTrue(vs)
            for nc, desc in vs:
                self.assertTrue(verify(nc)[0])
                self.assertEqual(metrics(nc)[0], m[0])


if __name__ == '__main__':
    unittest.main()
